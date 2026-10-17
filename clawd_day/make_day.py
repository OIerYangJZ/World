# -*- coding: utf-8 -*-
"""
《Clawd 的一天》—— 16-bit 像素游戏风动画（约 57 秒，24 fps）
世界画在 320×180 的像素画布上，最近邻 ×4 放大到 1280×720；
文字在高分辨率层上用无抗锯齿方式绘制，保持像素颗粒感。配乐为程序合成的芯片音乐。

运行：
  python3 make_day.py                 → music.wav + Clawd的一天.mp4
  python3 make_day.py still 12 30.5   → previews/ 下导出指定秒数的静帧
"""
import math, random, os, sys, subprocess, wave, array, re
from PIL import Image, ImageDraw, ImageFont, ImageChops

BW, BH, S = 320, 180, 4
W, H = BW * S, BH * S
FPS = 24
HERE = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------- 调色板
INK = (22, 20, 35)
CREAM = (246, 238, 222)
PAPER = (250, 246, 236)
CLAY = (217, 119, 87)
CLAY_L = (240, 160, 126)
CLAY_D = (163, 78, 56)
EYE = (30, 22, 28)
BLUSH = (248, 158, 146)
WALL = (233, 214, 186)
WALL_D = (214, 192, 162)
WOOD = (150, 98, 66)
WOOD_D = (108, 68, 46)
FLOOR = (186, 140, 104)
FLOOR_D = (160, 116, 84)
BOARD = (40, 74, 62)
BOARD_D = (32, 60, 50)
CHALK = (232, 238, 228)
CHALK_D = (150, 175, 160)
PINK = (255, 132, 168)
CYAN = (108, 208, 232)
GOLD = (250, 206, 98)
GREEN = (118, 204, 120)
PURPLE = (122, 96, 196)
SCREEN = (22, 24, 38)

# ---------------------------------------------------------------- 小工具
def clamp(v, a=0.0, b=1.0):
    return max(a, min(b, v))

def lerp(a, b, k):
    return a + (b - a) * k

def ease_out(p):
    p = clamp(p)
    return 1 - (1 - p) ** 3

def ease_io(p):
    p = clamp(p)
    return p * p * (3 - 2 * p)

def mix(a, b, k):
    return tuple(int(round(a[i] + (b[i] - a[i]) * k)) for i in range(3))

def R(d, x, y, w, h, c):
    x, y, w, h = int(round(x)), int(round(y)), int(round(w)), int(round(h))
    if w > 0 and h > 0:
        d.rectangle([x, y, x + w - 1, y + h - 1], fill=c)

def lum(c):
    return 0.3 * c[0] + 0.6 * c[1] + 0.1 * c[2]

# ---------------------------------------------------------------- 字体（逐字回退）
FONT_FILES = {
    "cjk": ("/System/Library/Fonts/Hiragino Sans GB.ttc", 2),
    "mono": ("/System/Library/Fonts/Menlo.ttc", 1),
    "stix": ("/System/Library/Fonts/Supplemental/STIXTwoMath.otf", 0),
}
_fonts, _glyph = {}, {}

def F(kind, size):
    k = (kind, size)
    if k not in _fonts:
        path, idx = FONT_FILES[kind]
        _fonts[k] = ImageFont.truetype(path, size, index=idx)
    return _fonts[k]

def has_glyph(kind, c):
    k = (kind, c)
    if k not in _glyph:
        f = F(kind, 24)
        _glyph[k] = c == " " or bytes(f.getmask(c)) != bytes(f.getmask(""))
    return _glyph[k]

def font_kind(c):
    o = ord(c)
    if 0x2E80 <= o or c in "…—“”":
        return "cjk"
    for k in ("mono", "cjk", "stix"):
        if has_glyph(k, c):
            return k
    return "mono"

def runs(s):
    out = []
    for c in s:
        k = font_kind(c)
        if out and out[-1][0] == k:
            out[-1][1] += c
        else:
            out.append([k, c])
    return out

def text_w(s, size):
    return sum(F(k, size).getlength(r) for k, r in runs(s))

def draw_text(d, x, y, s, size, color, anchor="l", shadow=None):
    """x, y 为全分辨率像素，y 是文字顶端。"""
    if anchor != "l":
        w = text_w(s, size)
        x -= w / 2 if anchor == "m" else w
    if shadow:
        draw_text(d, x + S, y + S, s, size, shadow)
    base = y + int(size * 0.86)
    for k, r in runs(s):
        f = F(k, size)
        d.text((int(x), int(base)), r, font=f, fill=color, anchor="ls")
        x += f.getlength(r)

# 高分辨率覆盖层：('t', x, y, 文本, 字号, 颜色, 对齐, 阴影) 或 ('r', x, y, w, h, 颜色)，坐标均为基准像素
def T(ov, x, y, s, size, color, anchor="l", shadow=None):
    ov.append(("t", x, y, s, size, color, anchor, shadow))

def OR(ov, x, y, w, h, c):
    ov.append(("r", x, y, w, h, c))

def draw_overlay(img, ov):
    d = ImageDraw.Draw(img)
    d.fontmode = "1"
    for it in ov:
        if it[0] == "t":
            _, x, y, s, size, color, anchor, shadow = it
            draw_text(d, x * S, y * S, s, size, color, anchor, shadow)
        else:
            _, x, y, w, h, c = it
            x0, y0 = int(round(x * S)), int(round(y * S))
            d.rectangle([x0, y0, x0 + int(round(w * S)) - 1, y0 + int(round(h * S)) - 1], fill=c)

# ---------------------------------------------------------------- 天空（Bayer 抖动渐变）
SKY_KEYS = [
    (0, (12, 14, 38), (34, 30, 72)),
    (300, (14, 16, 44), (44, 36, 84)),
    (350, (40, 42, 100), (150, 90, 120)),
    (390, (80, 100, 170), (250, 150, 110)),
    (430, (110, 160, 225), (250, 205, 160)),
    (600, (84, 150, 235), (170, 215, 250)),
    (900, (90, 150, 230), (200, 220, 240)),
    (1050, (100, 140, 210), (250, 190, 140)),
    (1110, (70, 60, 140), (245, 120, 90)),
    (1170, (30, 30, 80), (110, 60, 110)),
    (1260, (12, 14, 38), (34, 30, 72)),
    (1440, (12, 14, 38), (34, 30, 72)),
]
BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]

def sky_cols(m):
    m %= 1440
    for (m0, t0, b0), (m1, t1, b1) in zip(SKY_KEYS, SKY_KEYS[1:]):
        if m0 <= m <= m1:
            k = (m - m0) / (m1 - m0)
            return mix(t0, t1, k), mix(b0, b1, k)
    return SKY_KEYS[0][1], SKY_KEYS[0][2]

def night_k(m):
    return clamp((95 - lum(sky_cols(m)[0])) / 55)

_sky = {}
def sky_img(w, h, m, bands=7):
    q = int(m // 3) * 3
    key = (w, h, q)
    if key not in _sky:
        top, bot = sky_cols(q)
        cols = [mix(top, bot, i / (bands - 1)) for i in range(bands)]
        data = []
        for y in range(h):
            f = y / max(1, h - 1) * (bands - 1)
            b = min(int(f), bands - 2)
            fr = (f - b) * 16
            c0, c1 = cols[b], cols[b + 1]
            row = BAYER[y & 3]
            data.extend(c1 if fr > row[x & 3] + 0.5 else c0 for x in range(w))
        img = Image.new("RGB", (w, h))
        img.putdata(data)
        _sky[key] = img
    return _sky[key].copy()

_r = random.Random(11)
STARS = [(_r.randrange(BW), _r.randrange(BH), _r.random() * 6.28, _r.random()) for _ in range(140)]

def stars(d, x0, y0, w, h, t, k, ox=0, oy=0):
    if k <= 0.05:
        return
    for sx, sy, ph, big in STARS:
        if sx < w and sy < h:
            tw = 0.5 + 0.5 * math.sin(t * 3 + ph)
            v = k * (0.35 + 0.65 * tw)
            c = mix((60, 60, 110), (255, 250, 220), v)
            d.point((x0 + sx, y0 + sy), fill=c)
            if big > 0.9 and tw > 0.6:
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    d.point((x0 + sx + dx, y0 + sy + dy), fill=mix((60, 60, 110), c, 0.6))

CLOUDS = [(10, 14, 1.0), (52, 30, 0.7), (96, 10, 1.2), (150, 24, 0.8)]

def cloud(d, x, y, sc, c):
    R(d, x + 4 * sc, y, 10 * sc, 4 * sc, c)
    R(d, x, y + 3 * sc, 20 * sc, 4 * sc, c)
    R(d, x + 12 * sc, y + 1 * sc, 6 * sc, 3 * sc, c)

def window_view(w, h, m, t, sun=True):
    img = sky_img(w, h, m)
    d = ImageDraw.Draw(img)
    k = night_k(m)
    stars(d, 0, 0, w, h, t, k)
    top, bot = sky_cols(m)
    if sun:
        u = (m - 360) / 780
        if -0.05 < u < 1.05:
            sx = w * (0.1 + 0.8 * u)
            sy = h * 0.95 - math.sin(math.pi * clamp(u)) * h * 0.72
            d.ellipse([sx - 7, sy - 7, sx + 7, sy + 7], fill=GOLD)
            d.ellipse([sx - 4, sy - 4, sx + 3, sy + 3], fill=(255, 238, 180))
        u2 = ((m - 1140) % 1440) / 660
        if u2 < 1:
            mx = w * (0.15 + 0.7 * u2)
            my = h * 0.8 - math.sin(math.pi * u2) * h * 0.6
            d.ellipse([mx - 7, my - 7, mx + 7, my + 7], fill=(248, 240, 206))
            sc = mix(top, bot, clamp(my / h))
            d.ellipse([mx - 3, my - 9, mx + 10, my + 4], fill=sc)
    if k < 0.7:
        cc = mix((255, 255, 255), top, k)
        for cx, cy, sc in CLOUDS:
            x = (cx + t * 3 * sc) % (w + 40) - 30
            cloud(d, x, cy * h / 60, sc, cc)
    return img

# ---------------------------------------------------------------- 主角：像素 Clawd（可挤压拉伸、旋转、分身）
def clawd(img, cx, by, s=3, sq=1.0, angle=0.0, ghost=False, eyes="open", arms="rest", legs="stand",
          t=0.0, look=(0, 0), blush=False, mouth=False):
    """(cx, by) = 脚底中心。sq>1 拉长、sq<1 压扁；angle 为逆时针角度。"""
    spr = Image.new("RGBA", (16 * s, 11 * s), (0, 0, 0, 0))
    d = ImageDraw.Draw(spr)

    def r(u, v, w, h, c):
        v += 1
        x0, y0 = int(round(u * s)), int(round(v * s))
        x1, y1 = int(round((u + w) * s)), int(round((v + h) * s))
        if x1 > x0 and y1 > y0:
            d.rectangle([x0, y0, x1 - 1, y1 - 1], fill=c + (255,))

    for i, lx in enumerate((3, 5, 10, 12)):
        lh = 2
        if legs == "walk":
            lh = 2 if (int(t * 12) + i) % 2 == 0 else 1
        elif legs == "tuck":
            lh = 1
        r(lx, 8, 1, lh, CLAY_D)
    left, right = (0, 4, 2, 2), (14, 4, 2, 2)
    if arms == "up":
        left, right = (0, 0.5, 2, 3), (14, 0.5, 2, 3)
    elif arms == "type":
        a = int(t * 14) % 2
        left, right = (0, 3.5 + a, 2, 2), (14, 4.5 - a, 2, 2)
    elif arms == "point":
        right = (14, 0.5, 2, 3)
    elif arms == "wave":
        right = (14, -0.5 + int(t * 7) % 2, 2, 3)
    elif arms == "dance":
        a = int(t * 5) % 2
        left, right = ((0, 0.5, 2, 3), (14, 4, 2, 2)) if a else ((0, 4, 2, 2), (14, 0.5, 2, 3))
    r(*left, CLAY)
    r(*right, CLAY)
    r(2, 0, 12, 8, CLAY)
    r(2, 0, 12, 1, CLAY_L)
    r(2, 7, 12, 1, CLAY_D)
    lx, ly = look
    for ex in (4, 10):
        ex += lx * 0.5
        ey = 2 + ly * 0.5
        if eyes == "open":
            r(ex + 0.5, ey, 1, 2, EYE)
        elif eyes == "wide":
            r(ex, ey - 0.5, 1.5, 2.5, EYE)
        elif eyes in ("closed", "sleep"):
            r(ex, ey + 1.5, 2, 0.5, EYE)
        elif eyes == "happy":
            r(ex, ey + 1, 0.5, 1, EYE)
            r(ex + 0.5, ey + 0.5, 1, 0.5, EYE)
            r(ex + 1.5, ey + 1, 0.5, 1, EYE)
    if mouth:
        r(7 + lx * 0.5, 4.8, 2, 1.7, EYE)
    if blush:
        r(2.5, 4.5, 1.5, 0.5, BLUSH)
        r(12, 4.5, 1.5, 0.5, BLUSH)
    if legs == "tuck":
        by += s
    w = max(1, round(16 * s / sq ** 0.7))
    h = max(1, round(11 * s * sq))
    spr = spr.resize((w, h), Image.NEAREST)
    if ghost:
        rgb = Image.blend(spr.convert("RGB"), Image.new("RGB", spr.size, (255, 240, 230)), 0.5)
        ph = int(t * 12) % 2
        chk = Image.new("L", spr.size)
        chk.putdata([255 if (x + y + ph) % 2 == 0 else 0 for y in range(h) for x in range(w)])
        alpha = ImageChops.multiply(spr.getchannel("A"), chk)
        spr = rgb.convert("RGBA")
        spr.putalpha(alpha)
    if angle:
        spr = spr.rotate(angle, resample=Image.NEAREST, expand=True)
    img.paste(spr, (int(round(cx - spr.width / 2)), int(round(by - h / 2 - spr.height / 2))), spr)

def breathe(t, amp=0.035, sp=4.0):
    return 1 + amp * math.sin(t * sp)

def blink(t, e="open", period=3.1, off=0.0):
    return "closed" if (t + off) % period < 0.12 else e

def hop(lt, t0, dur, a, b, h, spin=0):
    """蓄力 → 腾空（可空翻）→ 落地压扁。返回 (cx, by, sq, angle, 阶段)，不在时段内返回 None。"""
    if t0 - 0.12 <= lt < t0:
        k = (lt - (t0 - 0.12)) / 0.12
        return a[0], a[1], 1 - 0.3 * math.sin(k * math.pi / 2), 0, "crouch"
    if t0 <= lt < t0 + dur:
        p = (lt - t0) / dur
        return (lerp(a[0], b[0], p), lerp(a[1], b[1], p) - h * 4 * p * (1 - p),
                1 + 0.22 * abs(1 - 2 * p), -spin * 360 * ease_io(p), "air")
    if t0 + dur <= lt < t0 + dur + 0.18:
        k = (lt - t0 - dur) / 0.18
        return b[0], b[1], 1 - 0.3 * math.cos(k * math.pi / 2), 0, "land"
    return None

def run_pose(lt, x0, x1, t0, t1):
    p = clamp((lt - t0) / (t1 - t0))
    x = lerp(x0, x1, ease_io(p) * 0.3 + p * 0.7)
    dr = 1 if x1 > x0 else -1
    return x, -abs(math.sin(lt * 16)) * 3, 1 + 0.06 * math.sin(lt * 32), -8 * dr, dr

def bounce(lt, period, h):
    p = (lt % period) / period
    sq = 0.82 if p < 0.12 or p > 0.92 else 1.08
    return -h * 4 * p * (1 - p) if 0.12 <= p <= 0.92 else 0, sq

def first(*poses):
    for p in poses:
        if p:
            return p
    return None

def ground_shadow(d, cx, gy, lift, s, col):
    w = 13 * s * (1 - min(0.6, lift / 90))
    d.ellipse([cx - w / 2, gy - 2, cx + w / 2, gy + 1], fill=col)

def emote(d, ov, x, y, sym, col=INK):
    R(d, x + 1, y, 10, 11, INK)
    R(d, x, y + 1, 12, 9, INK)
    R(d, x + 1, y + 1, 10, 9, CREAM)
    R(d, x + 3, y + 11, 2, 1, INK)
    R(d, x + 3, y + 10, 2, 1, CREAM)
    T(ov, x + 6, y + 1.6, sym, 28, col, "m")

def zzz(ov, x, y, t, col=(200, 200, 240)):
    for i in range(3):
        p = ((t * 0.6) + i / 3) % 1
        T(ov, x + p * 10 + math.sin(p * 6) * 2, y - p * 22, "z" if i % 2 else "Z", int(22 + p * 16), mix(col, (70, 70, 110), p * 0.8))

def sparkle(d, x, y, r, c):
    R(d, x - r, y, 2 * r + 1, 1, c)
    R(d, x, y - r, 1, 2 * r + 1, c)

def burst(d, x, y, q, c, n=8, r0=4, r1=18):
    for i in range(n):
        a = i * 2 * math.pi / n
        rr = lerp(r0, r1, q)
        R(d, x + math.cos(a) * rr - 1, y + math.sin(a) * rr - 1, 2, 2, c)

def asterisk(d, cx, cy, r, c):
    for dx, dy in ((1, 0), (0, 1), (1, 1), (1, -1)):
        for k in range(-r, r + 1):
            d.point((cx + dx * k, cy + dy * k), fill=c)

# ---------------------------------------------------------------- HUD 与字幕
def hud(d, ov, m):
    R(d, 5, 5, 62, 16, CREAM)
    R(d, 6, 6, 60, 14, INK)
    h = (m // 60) % 24
    if 6 <= h < 18:
        d.ellipse([10, 9, 17, 16], fill=GOLD)
    else:
        d.ellipse([10, 9, 17, 16], fill=(248, 240, 206))
        d.ellipse([12, 7, 19, 14], fill=INK)
    T(ov, 22, 7.8, "%02d:%02d" % (h, int(m % 60)), 34, CREAM)
    R(d, 6, 23, 60, 2, INK)
    R(d, 6, 23, int(60 * (m % 1440) / 1440), 2, GOLD)

def caption(d, ov, tag, s, lt, cps=15):
    R(d, 6, 146, 308, 30, CREAM)
    R(d, 7, 147, 306, 28, INK)
    R(d, 8, 148, 304, 1, (60, 56, 80))
    n = int(max(0.0, lt - 0.25) * cps)
    T(ov, 14, 156.5, tag, 30, GOLD)
    T(ov, 50, 156.5, s[:n], 30, CREAM)
    if n >= len(s) and int(lt * 3) % 2 == 0:
        T(ov, 304, 164, "▼", 18, GOLD, "m")

# ---------------------------------------------------------------- 场景道具：房间
_r = random.Random(5)
BOOKS = []
x = 264
while x < 312:
    w = _r.choice((3, 4, 5))
    BOOKS.append((x, w, _r.randrange(9, 14), _r.choice([CLAY, PURPLE, CYAN, GOLD, GREEN, PINK])))
    x += w + 1

def shade(c, k):
    return mix(c, (24, 24, 52), k * 0.72)

def room(d, img, m, t, dark=0.0, screen_fn=None, ov=None):
    wl = shade(WALL, dark)
    R(d, 0, 0, BW, 140, wl)
    dot = shade(WALL_D, dark)
    for yy in range(8, 118, 12):
        for xx in range(6 + (yy // 12 % 2) * 6, BW, 12):
            d.point((xx, yy), fill=dot)
    R(d, 0, 118, BW, 22, shade(WALL_D, dark))
    R(d, 0, 117, BW, 2, shade(WOOD, dark))
    R(d, 0, 140, BW, 40, shade(FLOOR, dark))
    for yy in (150, 163):
        R(d, 0, yy, BW, 1, shade(FLOOR_D, dark))
    for i, xx in enumerate(range(20, BW, 48)):
        R(d, xx + (i % 2) * 20, 141 if i % 2 else 151, 1, 9, shade(FLOOR_D, dark))
    # 窗
    R(d, 20, 16, 88, 82, shade(WOOD_D, dark))
    img.paste(window_view(76, 70, m, t), (26, 22))
    R(d, 63, 22, 2, 70, shade(WOOD, dark))
    R(d, 26, 56, 76, 2, shade(WOOD, dark))
    R(d, 16, 96, 96, 4, shade(WOOD, dark))
    # 海报：布洛赫球
    R(d, 126, 26, 36, 38, shade(INK, dark))
    R(d, 128, 28, 32, 34, shade(PAPER, dark))
    d.ellipse([133, 33, 155, 55], outline=shade(CLAY, dark))
    d.ellipse([133, 41, 155, 47], outline=shade(CLAY_L, dark))
    d.line([144, 44, 150, 36], fill=shade(INK, dark))
    R(d, 149, 35, 2, 2, shade(CLAY_D, dark))
    # 书架
    R(d, 260, 34, 56, 3, shade(WOOD, dark))
    for bx, bw, bh, bc in BOOKS:
        R(d, bx, 34 - bh, bw, bh, shade(bc, dark))
        R(d, bx, 34 - bh + 2, bw, 1, shade(mix(bc, CREAM, 0.5), dark))
    # 书桌、显示器
    R(d, 168, 104, 148, 4, shade(WOOD, dark))
    R(d, 168, 107, 148, 1, shade(WOOD_D, dark))
    R(d, 172, 108, 4, 32, shade(WOOD_D, dark))
    R(d, 306, 108, 4, 32, shade(WOOD_D, dark))
    R(d, 206, 62, 66, 40, shade(INK, dark))
    R(d, 234, 100, 10, 4, shade(INK, dark))
    R(d, 209, 65, 60, 34, SCREEN)
    if screen_fn:
        screen_fn(d, 209, 65, 60, 34)
    # 马克杯 + 台灯
    R(d, 186, 96, 8, 8, shade(CREAM, dark))
    R(d, 194, 98, 2, 4, shade(CREAM, dark))
    R(d, 187, 97, 6, 1, shade(CLAY, dark))
    R(d, 290, 100, 12, 4, shade(INK, dark))
    d.line([296, 100, 290, 82], fill=shade(INK, dark), width=2)
    d.polygon([(282, 84), (296, 76), (300, 84)], fill=shade(GOLD if dark < 0.5 else (120, 100, 70), dark * 0.4))
    # 垫子
    d.ellipse([34, 128, 114, 146], fill=shade((196, 104, 128), dark))
    d.ellipse([38, 128, 110, 140], fill=shade((222, 132, 152), dark))

# ---------------------------------------------------------------- 场景 0：片头·黎明天际线
_r = random.Random(3)
BUILDINGS = []
x = -6
while x < BW + 6:
    w = _r.randrange(18, 38)
    top = _r.randrange(104, 148)
    if 128 <= x + w / 2 <= 176:
        top = 132
    wins = [(wx, wy, _r.random()) for wy in range(top + 6, 180, 7) for wx in range(x + 3, x + w - 3, 5) if _r.random() < 0.55]
    BUILDINGS.append((x, w, top, wins, _r.random()))
    x += w + _r.randrange(-2, 3)

def scene_title(d, img, ov, lt, m):
    img.paste(window_view(BW, BH, m, lt, sun=False), (0, 0))
    k = night_k(m)
    sy = lerp(176, 104, ease_io(lt / 4.2))
    d.ellipse([236, sy - 16, 268, sy + 16], fill=(250, 180, 100))
    d.ellipse([240, sy - 12, 264, sy + 12], fill=GOLD)
    d.ellipse([245, sy - 7, 257, sy + 5], fill=(255, 238, 190))
    for cx, cy in ((20, 88), (190, 70), (96, 96)):
        cloud(d, (cx + lt * 5) % 360 - 30, cy, 1.5, mix((110, 90, 150), (255, 186, 160), 1 - k))
    for bx, bw, top, wins, v in BUILDINGS:
        c = mix((26, 24, 46), (60, 52, 84), v * 0.5 + (1 - k) * 0.3)
        R(d, bx, top, bw, BH - top, c)
        R(d, bx, top, bw, 1, mix(c, (250, 170, 130), 0.5 * (1 - k)))
        for wx, wy, th in wins:
            if th < 0.25 + 0.75 * k:
                R(d, wx, wy, 2, 3, mix((120, 100, 60), GOLD, k))
    pose = hop(lt, 2.8, 0.55, (160, 132), (160, 132), 34, spin=1)
    if pose:
        cx, by, sq, ang, ph = pose
        clawd(img, cx, by, 2, sq, ang, eyes="wide" if ph == "air" else "happy", arms="up", legs="tuck" if ph == "air" else "stand", t=lt)
    elif lt < 1.6:
        clawd(img, 160, 132, 2, breathe(lt), eyes="sleep", legs="tuck", t=lt)
        zzz(ov, 176, 108, lt)
    elif lt < 2.3:
        k2 = (lt - 1.6) / 0.7
        clawd(img, 160, 132, 2, 1 + 0.4 * math.sin(k2 * math.pi), eyes="closed", arms="up", t=lt, mouth=True)
    elif lt < 2.68:
        clawd(img, 160, 132, 2, 1, eyes=blink(lt, "open", 0.2), t=lt, look=(1, 0) if lt < 2.5 else (-1, 0))
    else:
        dy, sq = bounce(lt, 0.42, 5)
        clawd(img, 160, 132 + dy, 2, sq, eyes="happy", arms="wave", t=lt, blush=True)
    title = "Clawd 的一天"
    tw = text_w(title, 92) / S
    x = BW / 2 - tw / 2
    for i, ch in enumerate(title):
        p = ease_out((lt - 0.3 - i * 0.1) / 0.3)
        if p > 0:
            T(ov, x, 20 - (1 - p) * 14 + math.sin(lt * 3 + i) * 0.8, ch, 92, CREAM, shadow=INK)
        x += text_w(ch, 92) / S
    if lt > 1.4:
        T(ov, BW / 2, 50, "A  DAY  IN  THE  LIFE  OF  CLAWD"[: int((lt - 1.4) * 30)], 24, GOLD, "m", INK)

# ---------------------------------------------------------------- 场景 1：07:00 起床 → 空翻下床 → 跑 → 跳上桌 → 跳舞
def scene_wake(d, img, ov, lt, m):
    lit = lt > 1.2

    def scr(d, x, y, w, h):
        if lit:
            R(d, x, y, w, h, (30, 34, 54))
            asterisk(d, x + w // 2, y + h // 2, 7 + int(lt * 4) % 2, CLAY_L)

    room(d, img, m, lt, 0.12, scr)
    sh = (170, 126, 94)
    pose = first(hop(lt, 1.7, 0.6, (74, 137), (112, 140), 52, spin=1),
                 hop(lt, 3.5, 0.5, (150, 140), (192, 104), 40))
    if pose:
        cx, by, sq, ang, ph = pose
        if by > 120:
            ground_shadow(d, cx, 140, 140 - by, 3, sh)
        clawd(img, cx, by, 3, sq, ang, eyes="wide", arms="up", legs="tuck" if ph == "air" else "stand", t=lt)
    elif lt < 1.58:
        if lt < 1.2:
            clawd(img, 74, 137, 3, breathe(lt), eyes="sleep", legs="tuck", t=lt)
            zzz(ov, 100, 100, lt)
        else:
            shake = math.sin(lt * 70) * 5
            clawd(img, 74, 137, 3, 1.12, shake, eyes="wide", legs="tuck", t=lt)
            emote(d, ov, 84, 84, "!", CLAY_D)
    elif lt < 3.38:
        x, dy, sq, ang, dr = run_pose(lt, 112, 150, 2.48, 3.38)
        ground_shadow(d, x, 140, 0, 3, sh)
        clawd(img, x, 140 + dy, 3, sq, ang, eyes="open", legs="walk", t=lt, look=(1, 0))
    else:
        dy, sq = bounce(lt - 4.18, 0.36, 8)
        clawd(img, 192, 104 + dy, 3, sq, 6 * math.sin(lt * 8.7), eyes="happy", arms="dance", t=lt,
              look=(1 if int(lt * 2.8) % 2 else -1, 0), blush=True)
        if int(lt * 5) % 2:
            sparkle(d, 160, 70, 2, GOLD)
            sparkle(d, 226, 58, 2, GOLD)
    caption(d, ov, "07:00", "起床！开工啦～", lt - 0.5)

# ---------------------------------------------------------------- 场景 2：09:30 量子 → 画布洛赫球 → 叠加态分身 → 测量坍缩
_r = random.Random(8)
SMUDGES = [(_r.randrange(14, 300), _r.randrange(12, 120), _r.randrange(8, 30), _r.randrange(2, 6)) for _ in range(14)]
Q_SPLIT, Q_MEAS = 3.4, 6.0

def bloch_tip(th, ph, cx, cy, Rr, el=0.32):
    x3, y3, z3 = math.sin(th) * math.cos(ph), math.sin(th) * math.sin(ph), math.cos(th)
    return cx + Rr * y3, cy - Rr * z3 * math.cos(el) + Rr * x3 * math.sin(el)

def q_angles(lt):
    if lt < Q_MEAS:
        return (math.pi / 2) * ease_io((lt - 2.2) / 0.8), max(0.0, lt - 3.0) * 2.4
    return lerp(math.pi / 2, math.pi, ease_out((lt - Q_MEAS) / 0.2)), (Q_MEAS - 3.0) * 2.4

def scene_quantum(d, img, ov, lt, m):
    R(d, 0, 0, BW, 140, WALL)
    R(d, 0, 140, BW, 40, FLOOR)
    R(d, 0, 150, BW, 1, FLOOR_D)
    R(d, 6, 4, 308, 128, WOOD)
    R(d, 10, 8, 300, 118, BOARD)
    for sx, sy, sw, sh in SMUDGES:
        R(d, sx, sy, sw, sh, BOARD_D)
    R(d, 8, 126, 304, 5, WOOD_D)
    R(d, 40, 126, 8, 2, CHALK)
    cx, cy, Rr = 250, 52, 28
    rev = ease_out((lt - 1.3) / 1.0)
    if rev > 0:
        d.arc([cx - Rr, cy - Rr, cx + Rr, cy + Rr], -90, -90 + 360 * rev, fill=CHALK)
    if rev >= 1:
        for a in range(0, 360, 12):
            ex = cx + Rr * math.sin(math.radians(a))
            ey = cy + Rr * 0.32 * math.cos(math.radians(a))
            if math.cos(math.radians(a)) > 0 or a % 24 == 0:
                d.point((ex, ey), fill=CHALK if math.cos(math.radians(a)) > 0 else CHALK_D)
        for yy in range(cy - Rr - 6, cy + Rr + 6, 3):
            d.point((cx, yy), fill=CHALK_D)
        th, ph = q_angles(lt)
        for i in range(1, 14):
            if Q_SPLIT < lt - i * 0.05 < Q_MEAS:
                tx, ty = bloch_tip(*q_angles(lt - i * 0.05), cx, cy, Rr)
                d.point((tx, ty), fill=mix(BOARD, CYAN, 1 - i / 14))
        tx, ty = bloch_tip(th, ph, cx, cy, Rr)
        d.line([cx, cy, tx, ty], fill=CLAY_L)
        R(d, tx - 1, ty - 1, 3, 3, CLAY)
        T(ov, cx + 4, cy - Rr - 11, "|0⟩", 26, CHALK)
        T(ov, cx + 4, cy + Rr + 2, "|1⟩", 26, CHALK)
    sh = (170, 126, 94)
    GY = 140
    pose = first(hop(lt, 2.9, 0.35, (196, GY), (160, GY), 16),
                 hop(lt, 7.0, 0.6, (230, GY), (230, GY), 46, spin=1))
    if pose:
        x, by, sq, ang, ph = pose
        ground_shadow(d, x, GY, GY - by, 3, sh)
        clawd(img, x, by, 3, sq, ang, eyes="happy" if lt > 6 else "open", arms="up", t=lt,
              legs="tuck" if ph == "air" else "stand")
    elif lt < 1.3:
        x, dy, sq, ang, dr = run_pose(lt, -30, 196, 0.0, 1.3)
        ground_shadow(d, x, GY, 0, 3, sh)
        clawd(img, x, GY + dy, 3, sq, ang, legs="walk", t=lt, look=(1, 0))
    elif lt < 2.83:
        clawd(img, 196, GY, 3, 1 + 0.04 * math.sin(lt * 40), 4 * math.sin(lt * 26), arms="point", t=lt, look=(1, -1))
        chalk = (222, 110 + math.sin(lt * 20) * 3)
        R(d, *chalk, 2, 2, CHALK)
        for i in range(4):
            p = (lt * 1.6 + i / 4) % 1
            d.point((chalk[0] + i - 2, chalk[1] + p * 26), fill=mix(CHALK, WALL, p))
    elif lt < Q_SPLIT:
        clawd(img, 160, GY, 3, breathe(lt), eyes="happy", t=lt)
    elif lt < Q_MEAS:
        sp = ease_out((lt - Q_SPLIT) / 0.5)
        dy, sq = bounce(lt - Q_SPLIT, 0.5, 16)
        xl, xr = lerp(160, 90, sp), lerp(160, 230, sp)
        for i, xx in enumerate((xl, xr)):
            ground_shadow(d, xx, GY, -dy, 3, sh)
        for xx in range(int(xl) + 26, int(xr) - 25, 2):
            d.point((xx, GY - 18 + dy + round(3 * math.sin(xx * 0.25 - lt * 10))), fill=PINK)
        for xx, lk in ((xl, -1), (xr, 1)):
            clawd(img, xx, GY + dy, 3, sq, 7 * math.sin(lt * 6.3) * lk, ghost=True, eyes=blink(lt, "open"),
                  arms="dance", t=lt, look=(lk, 0))
        if lt - Q_SPLIT < 0.3:
            burst(d, 160, GY - 16, (lt - Q_SPLIT) / 0.3, GOLD, 10, 8, 34)
    else:
        k = (lt - Q_MEAS)
        if k < 0.3:
            burst(d, 90, GY - 16, k / 0.3, PINK, 10, 4, 26)
        pop = 1 + 0.4 * (1 - ease_out(k / 0.3))
        shake = 6 * math.sin(lt * 50) if 0.3 < k < 0.85 else 0
        e = "wide" if k < 0.85 else "happy"
        if k > 0.95:
            dy, sq = bounce(lt, 0.45, 6)
            clawd(img, 230, GY + dy, 3, sq, eyes="happy", arms="wave", t=lt, blush=True)
        else:
            clawd(img, 230, GY, 3, pop, shake, eyes=e, arms="up", t=lt)
            if k > 0.3:
                emote(d, ov, 200, 92, "!", CLAY_D)
    if Q_MEAS <= lt < Q_MEAS + 0.1:
        img.paste(Image.blend(img, Image.new("RGB", img.size, CREAM), 0.75))
    caption(d, ov, "09:30", "量子：叠加态……测量！", lt - 0.4)

# ---------------------------------------------------------------- 场景 3：11:00 数学 → 踩着引理跳上定理
_r = random.Random(21)
SYMS = ["∀ε>0", "∃δ", "∑", "∫", "π", "⊗", "∞", "e^{iπ}"]
FLOATERS = [(SYMS[i], _r.randrange(0, 300), _r.randrange(0, 200), _r.uniform(3, 8)) for i in range(8)]
BLOCK_X = [40, 106, 172, 238]
BLOCK_T = [0.3 + i * 1.3 for i in range(4)]
LABELS = ["引理", "引理", "引理", "定理"]

def block_top(i):
    return 140 - (i + 1) * 24

def scene_math(d, img, ov, lt, m):
    R(d, 0, 0, BW, BH, (34, 32, 72))
    for xx in range(0, BW, 10):
        R(d, xx, 0, 1, BH, (42, 40, 86))
    for yy in range(0, BH, 10):
        R(d, 0, yy, BW, 1, (42, 40, 86))
    f = F("mono", 12)
    for s, x0, y0, sp in FLOATERS:
        d.text((x0, (y0 - lt * sp) % 200 - 16), s, font=f, fill=(74, 70, 130))
    R(d, 0, 140, BW, 40, (24, 22, 52))
    R(d, 0, 140, BW, 1, (90, 84, 160))
    for i in range(4):
        a = BLOCK_T[i]
        if lt < a:
            continue
        p = ease_out((lt - a) / 0.35)
        bx, top = BLOCK_X[i], block_top(i)
        off = (1 - p) * -150
        c = GOLD if i == 3 else mix(PURPLE, CYAN, i * 0.2)
        R(d, bx, top + off, 56, 140 - top, c)
        R(d, bx, top + off, 56, 2, mix(c, CREAM, 0.5))
        R(d, bx + 54, top + off, 2, 140 - top, mix(c, INK, 0.3))
        T(ov, bx + 28, top + off + 8, LABELS[i], 26, INK if i == 3 else CREAM, "m")
        if 0.35 < lt - a < 0.55:
            q = (lt - a - 0.35) / 0.2
            R(d, bx - 6 - q * 8, 138, 4, 2, CREAM)
            R(d, bx + 58 + q * 8, 138, 4, 2, CREAM)
    pos = [(18, 140)] + [(BLOCK_X[i] + 26, block_top(i)) for i in range(4)]
    pose = first(*[hop(lt, BLOCK_T[i] + 0.5, 0.5, pos[i], pos[i + 1], 26 + i * 4, spin=1 if i == 3 else 0) for i in range(4)])
    cur = sum(1 for i in range(4) if lt >= BLOCK_T[i] + 1.0)
    if pose:
        x, by, sq, ang, ph = pose
        clawd(img, x, by, 3, sq, ang, eyes="wide" if ph == "air" else "open", arms="up",
              legs="tuck" if ph == "air" else "stand", t=lt)
    elif lt < 5.5:
        x, by = pos[cur]
        waiting = cur < 4 and lt > BLOCK_T[cur] - 0.4 if cur < 4 else False
        dy, sq = bounce(lt, 0.5, 3) if waiting else (0, breathe(lt))
        clawd(img, x, by + dy, 3, sq, eyes=blink(lt), t=lt, look=(1, -1))
    elif lt < 6.0:
        x, by = pos[4]
        clawd(img, x, by, 3, 1.15, eyes="happy", arms="up", t=lt)
    else:
        x, by = pos[4]
        dy, sq = bounce(lt, 0.4, 9)
        clawd(img, x, by + dy, 3, sq, 8 * math.sin(lt * 7.8), eyes="happy", arms="dance", t=lt, blush=True)
    if lt > 5.5:
        p = ease_out((lt - 5.5) / 0.3)
        fx, ft = BLOCK_X[3] + 53, block_top(3)
        R(d, fx, ft - 26 * p, 1, 26 * p, CREAM)
        if p >= 1:
            for row in range(7):
                R(d, fx + 1, ft - 26 + row, 10 + round(math.sin(lt * 8 + row * 0.8)), 1, CLAY if row % 6 else CLAY_L)
    if lt > 5.9:
        p = ease_out((lt - 5.9) / 0.25)
        size = int(64 * (1 + 0.8 * (1 - p)))
        T(ov, 130, 12, "Q.E.D.", size, GOLD, "m", INK)
        for i in range(8):
            ang = i * math.pi / 4 + lt
            if int(lt * 6 + i) % 2:
                R(d, 140 + math.cos(ang) * 70, 22 + math.sin(ang) * 16, 2, 2, CREAM)
    caption(d, ov, "11:00", "数学：一步一步，证毕！", lt - 0.4)

# ---------------------------------------------------------------- 场景 4：13:00 闲聊 → 用图标对话，Clawd 表演
CHAT = [(0.3, "u", "bowl"), (1.1, "c", "bowl"), (3.0, "u", "sky"), (3.8, "c", "wave"), (5.4, "u", "heart"), (6.0, "c", "heart")]
HEART = [".XX...XX.", "XXXX.XXXX", "XXXXXXXXX", "XXXXXXXXX", ".XXXXXXX.", "..XXXXX..", "...XXX...", "....X...."]

def icon(d, kind, x, y, t):
    if kind == "bowl":
        R(d, x + 1, y + 5, 14, 1, GOLD)
        R(d, x + 1, y + 6, 14, 2, (200, 64, 52))
        R(d, x + 2, y + 8, 12, 2, CREAM)
        R(d, x + 4, y + 10, 8, 1, CREAM)
        d.line([x + 9, y, x + 14, y + 6], fill=WOOD)
        d.line([x + 11, y, x + 15, y + 5], fill=WOOD)
        for i in range(3):
            p = (t * 1.2 + i / 3) % 1
            d.point((x + 3 + i * 3, y + 4 - p * 6), fill=mix((255, 255, 255), (200, 190, 180), p))
    elif kind == "sky":
        R(d, x, y, 16, 12, (110, 170, 240))
        d.ellipse([x + 2, y + 2, x + 7, y + 7], fill=GOLD)
        R(d, x + 8, y + 7, 7, 2, (255, 255, 255))
        R(d, x + 10, y + 6, 3, 1, (255, 255, 255))
    elif kind == "wave":
        for i in range(16):
            R(d, x + i, y + 5 + round(3.5 * math.sin(i * 0.8 - t * 8)), 1, 2, mix(PURPLE, CYAN, i / 15))
    elif kind == "heart":
        pulse = int(t * 4) % 2
        for j, row in enumerate(HEART):
            for i, ch in enumerate(row):
                if ch == "X":
                    d.point((x + 3 + i, y + 2 + j - pulse), fill=PINK)

def scene_chat(d, img, ov, lt, m):
    R(d, 0, 0, BW, 140, WALL)
    for yy in range(8, 118, 12):
        for xx in range(6 + (yy // 12 % 2) * 6, BW, 12):
            d.point((xx, yy), fill=WALL_D)
    R(d, 0, 118, BW, 22, WALL_D)
    R(d, 0, 117, BW, 2, WOOD)
    R(d, 0, 140, BW, 40, FLOOR)
    R(d, 0, 152, BW, 1, FLOOR_D)
    R(d, 214, 14, 96, 84, WOOD_D)
    img.paste(window_view(86, 74, m, lt), (219, 19))
    R(d, 261, 19, 2, 74, WOOD)
    R(d, 210, 96, 104, 4, WOOD)
    for i in range(4):
        R(d, 150 - i * 14, 142 + i * 3, 50, 2, mix(FLOOR, CREAM, 0.25))
    R(d, 170, 128, 40, 3, WOOD)
    R(d, 174, 131, 2, 9, WOOD_D)
    R(d, 204, 131, 2, 9, WOOD_D)
    R(d, 250, 116, 30, 3, WOOD)
    R(d, 264, 119, 2, 21, WOOD_D)
    R(d, 258, 108, 9, 8, CREAM)
    R(d, 267, 110, 2, 4, CREAM)
    for i in range(3):
        p = (lt * 0.8 + i / 3) % 1
        d.point((261 + round(math.sin(p * 7 + i) * 1.5), 106 - p * 14), fill=mix(CREAM, WALL, p))
    # 气泡：左边是“你”，头顶是 Clawd
    for j, (ta, who, kind) in enumerate(CHAT):
        nxt = next((tb for tb, w2, _ in CHAT[j + 1:] if w2 == "u"), 99) if who == "c" else \
              next((tb for tb, w2, _ in CHAT[j + 1:] if w2 == "u"), 99)
        if not (ta <= lt < nxt + (0.0 if who == "u" else 0.3)):
            continue
        pop = ease_out((lt - ta) / 0.18)
        if who == "u":
            x, y = 16, 40 + (1 - pop) * 8
            bubble(d, x, y, 44, 24, CREAM)
            R(d, x - 4, y + 18, 5, 2, CREAM)
            T(ov, x + 9, y + 4, "?", 40, CLAY_D, "m")
            icon(d, kind, x + 20, y + 6, lt)
        else:
            x, y = 172, 58 + (1 - pop) * 8
            bubble(d, x, y, 34, 22, CLAY)
            R(d, x + 14, y + 22, 4, 3, CLAY)
            icon(d, kind, x + 9, y + 5, lt)
            R(d, x + 28, y + 4, 2, 8, CREAM)
            R(d, x + 28, y + 14, 2, 2, CREAM)
    GY = 128
    pose = first(hop(lt, 1.1, 0.45, (190, GY), (190, GY), 24),
                 hop(lt, 5.9, 0.6, (190, GY), (190, GY), 44, spin=1))
    if pose:
        x, by, sq, ang, ph = pose
        clawd(img, x, by, 3, sq, ang, eyes="happy", arms="up", legs="tuck" if ph == "air" else "stand", t=lt, blush=lt > 5)
    elif lt < 1.0:
        clawd(img, 190, GY, 3, breathe(lt), 8, eyes=blink(lt, "open", 1.5), legs="tuck", t=lt, look=(-1, -1))
    elif lt < 3.0:
        dy, sq = bounce(lt, 0.34, 4)
        clawd(img, 190, GY + dy, 3, sq, 5 * math.sin(lt * 9), eyes="happy", arms="dance", legs="tuck", t=lt, look=(-1, 0))
    elif lt < 3.8:
        clawd(img, 190, GY, 3, breathe(lt), -9, eyes=blink(lt, "open", 1.3), legs="tuck", t=lt, look=(-1, -1))
    elif lt < 5.4:
        k = lt - 3.8
        clawd(img, 190 + 5 * math.sin(k * 7), GY, 3, 1 + 0.08 * math.sin(k * 14), 14 * math.sin(k * 7),
              eyes="happy", arms="dance", legs="tuck", t=lt)
    else:
        laugh = 5 * math.sin(lt * 60)
        dy, sq = bounce(lt, 0.3, 3)
        clawd(img, 190, GY + dy, 3, sq, laugh, eyes="happy", arms="wave", legs="tuck", t=lt, blush=True)
    caption(d, ov, "13:00", "闲聊：什么都能聊～", lt - 0.4)

def bubble(d, x, y, w, h, c):
    R(d, x + 1, y, w - 2, h, c)
    R(d, x, y + 1, w, h - 2, c)

# ---------------------------------------------------------------- 场景 5：15:00 写代码 → 狂敲键盘 → 追 bug → 全绿
_r = random.Random(4)
BARS = []
for _ in range(40):
    ind = _r.choice([0, 0, 1, 1, 2]) * 8
    BARS.append((ind, [(_r.randrange(4, 22), _r.choice([PINK, CYAN, CREAM, CREAM, GOLD, (150, 200, 255)]))
                       for _ in range(_r.randrange(1, 5))]))
KB_X, DESK = 287, 130

def code_lines(lt):
    return clamp(lt, 0, 2.2) * 5 + clamp(lt - 6.63, 0, 0.7) * 5

def bug(d, x, y, t, face=-1, scared=False, k=2):
    G, GL = (72, 160, 80), (120, 210, 120)
    x += round(math.sin(t * 60)) if scared else 0

    def r(u, v, w, h, c):
        R(d, x + u * k, y + v * k, w * k, h * k, c)

    r(-4, -5, 8, 4, G)
    r(-3, -5, 6, 1, GL)
    ex = -3 if face < 0 else 2
    r(ex, -4, 1, 1, INK)
    r(ex + (-1 if face < 0 else 1), -7, 1, 2, G)
    lg = int(t * 14) % 2
    for i in range(3):
        r(-3 + i * 3, -1 + (lg if i % 2 else 1 - lg), 1, 1, INK)

def bug_pos(lt):
    if lt < 2.8:
        return lerp(240, 200, clamp((lt - 2.0) / 0.8)), 80, -1, False
    if lt < 3.2:
        p = (lt - 2.8) / 0.4
        return lerp(200, 150, p), lerp(80, DESK, p) - 20 * 4 * p * (1 - p), -1, False
    if lt < 3.9:
        return lerp(150, 30, (lt - 3.2) / 0.7), DESK, -1, False
    if lt < 4.4:
        return lerp(30, 80, (lt - 3.9) / 0.5), DESK, 1, False
    return 80, DESK, 1, True

def scene_code(d, img, ov, lt, m):
    R(d, 0, 0, BW, 130, mix(WALL, GOLD, 0.08))
    d.polygon([(250, 0), (320, 0), (320, 40), (300, 130), (262, 130)], fill=mix(WALL, (255, 240, 200), 0.45))
    R(d, 0, 130, BW, 5, WOOD)
    R(d, 0, 135, BW, 45, WOOD_D)
    R(d, 70, 28, 188, 96, INK)
    R(d, 74, 32, 180, 86, SCREEN)
    R(d, 156, 124, 16, 6, INK)
    n = code_lines(lt)
    first_line = max(0, int(n) - 9)
    for li in range(first_line, int(n) + 1):
        ind, segs = BARS[li % len(BARS)]
        y = 37 + (li - first_line) * 7
        frac = 1 if li < int(n) else n - int(n)
        total = sum(w + 3 for w, _ in segs) * frac
        x = 80 + ind
        for w, c in segs:
            ww = min(w, total)
            if ww <= 0:
                break
            R(d, x, y, ww, 3, c)
            total -= w + 3
            x += w + 3
        if li == int(n) and int(lt * 3) % 2:
            R(d, x, y - 1, 2, 5, CREAM)
    if lt > 6.9:
        p = clamp((lt - 6.9) / 0.5)
        R(d, 96, 104, 136, 5, (40, 44, 64))
        R(d, 96, 104, int(136 * p), 5, GREEN)
        if p >= 1:
            R(d, 74, 32, 180, 68, (22, 40, 34))
            for i in range(7):
                R(d, 146 + i * 2, 62 + i * 2, 4, 4, GREEN)
            for i in range(12):
                R(d, 160 + i * 2, 74 - i * 3, 4, 4, GREEN)
    # bug
    if 2.0 <= lt < 4.82:
        bx, by_, face, scared = bug_pos(lt)
        bug(d, bx, by_, lt, face, scared)
        if 2.8 <= lt < 3.0:
            emote(d, ov, bx - 6, by_ - 22, "?", (60, 150, 70))
    if 4.82 <= lt < 5.3:
        burst(d, 80, DESK - 8, (lt - 4.82) / 0.48, GOLD, 10, 6, 30)
        T(ov, 80, DESK - 48 - (lt - 4.82) * 10, "caught!", 26, GOLD, "m", INK)
    # Clawd
    pose = first(hop(lt, 3.0, 0.35, (KB_X, DESK), (240, DESK), 20),
                 hop(lt, 4.42, 0.4, (130, DESK), (80, DESK), 34),
                 hop(lt, 6.1, 0.35, (240, DESK), (KB_X, DESK), 20),
                 hop(lt, 7.5, 0.6, (KB_X, DESK), (KB_X, DESK), 44, spin=1))
    typing = lt < 2.2 or 6.63 <= lt < 7.4
    if pose:
        x, by, sq, ang, ph = pose
        happy = lt > 7
        clawd(img, x, by, 3, sq, ang, eyes="happy" if happy else "wide", arms="up",
              legs="tuck" if ph == "air" else "stand", t=lt, look=(-1, 0))
    elif typing:
        clawd(img, KB_X, DESK, 3, 1 + 0.06 * abs(math.sin(lt * 25)), 3 * math.sin(lt * 17), eyes="open",
              arms="type", t=lt, look=(-1, -1))
        for i in range(3):
            p = (lt * 3 + i / 3) % 1
            R(d, KB_X - 18 + i * 14 + p * 4 * (i - 1), DESK - 6 - p * 18, 2, 2, mix(CREAM, WALL, p))
    elif lt < 3.0:
        clawd(img, KB_X, DESK, 3, 1.1, 0, eyes="wide", arms="up", t=lt, look=(-1, 0))
        if lt > 2.3:
            emote(d, ov, KB_X + 4, DESK - 50, "!", CLAY_D)
    elif lt < 4.42:
        x, dy, sq, ang, dr = run_pose(lt, 240, 130, 3.53, 4.3)
        clawd(img, x, DESK + dy, 3, sq, ang, eyes="wide", legs="walk", t=lt, look=(-1, 0))
    elif lt < 5.3:
        clawd(img, 80, DESK, 3, 0.8 if lt < 5.0 else 1.0, eyes="happy", t=lt, blush=True)
    elif lt < 6.1:
        x, dy, sq, ang, dr = run_pose(lt, 80, 240, 5.3, 6.0)
        clawd(img, x, DESK + dy, 3, sq, ang, eyes="happy", legs="walk", t=lt, look=(1, 0))
    else:
        dy, sq = bounce(lt, 0.4, 7)
        clawd(img, KB_X, DESK + dy, 3, sq, 6 * math.sin(lt * 7.8), eyes="happy", arms="dance", t=lt, blush=True)
    R(d, 262, 125, 50, 6, (70, 72, 96))
    for i in range(8):
        R(d, 264 + i * 6, 126, 4, 2, (130, 134, 160))
        R(d, 266 + i * 6 - 3, 128, 4, 2, (110, 114, 140))
    caption(d, ov, "15:00", "写代码：抓 bug！", lt - 0.4)

# ---------------------------------------------------------------- 场景 6：23:00 打哈欠 → 走回垫子 → 转圈 → 趴下睡
def scene_night(d, img, ov, lt, m):
    def scr(d, x, y, w, h):
        px = x + 4 + (lt * 9) % (w - 12)
        py = y + 4 + abs(((lt * 6) % (2 * (h - 12))) - (h - 12))
        R(d, px, py, 4, 4, (60, 50, 90))

    room(d, img, m, lt, 0.85, scr)
    if 5.4 < lt < 6.4:
        p = lt - 5.4
        sx, sy = 96 - p * 70, 26 + p * 28
        for i in range(6):
            d.point((sx + i * 2, sy - i), fill=mix((255, 250, 220), (40, 40, 80), i / 6))
    pose = hop(lt, 3.1, 0.35, (100, 140), (74, 137), 12)
    if pose:
        x, by, sq, ang, ph = pose
        clawd(img, x, by, 3, sq, ang, eyes="closed", t=lt)
    elif lt < 1.2:
        k = clamp(lt / 1.2)
        clawd(img, 210, 140, 3, 1 + 0.35 * math.sin(k * math.pi), eyes="closed", arms="up", t=lt, mouth=0.15 < k < 0.85)
    elif lt < 2.98:
        x, dy, sq, ang, dr = run_pose(lt, 210, 100, 1.2, 2.98)
        clawd(img, x, 140 + dy * 0.4, 3, sq, ang * 0.5 + 4 * math.sin(lt * 3), eyes=blink(lt, "closed", 0.9),
              legs="walk", t=lt * 0.6, look=(-1, 1))
    elif lt < 4.6:
        k = lt - 3.63
        clawd(img, 74 + 5 * math.sin(k * 9), 137, 3, breathe(lt), eyes="closed", legs="walk", t=lt,
              look=(1 if math.cos(k * 9) > 0 else -1, 1))
    elif lt < 4.9:
        clawd(img, 74, 137, 3, 0.7 + 0.3 * ease_out((lt - 4.6) / 0.3), eyes="sleep", legs="tuck", t=lt)
    else:
        clawd(img, 74, 137, 3, breathe(lt, 0.04, 2.5), eyes="sleep", legs="tuck", t=lt)
        zzz(ov, 100, 100, lt)
    caption(d, ov, "23:00", "晚安～明天见。", lt - 0.4)

# ---------------------------------------------------------------- 片尾
def scene_end(d, img, ov, lt, m):
    img.paste(sky_img(BW, BH, 0), (0, 0))
    stars(d, 0, 0, BW, BH, lt, 1.0)
    pose = first(*[hop(lt, t0, 0.5, (160, 112), (160, 112), 22 if i != 2 else 40, spin=1 if i == 2 else 0)
                   for i, t0 in enumerate((0.5, 1.2, 1.9, 2.8))])
    ground_shadow(d, 160, 113, 0 if not pose else 112 - pose[1], 4, (30, 28, 64))
    if pose:
        x, by, sq, ang, ph = pose
        clawd(img, x, by, 4, sq, ang, eyes="happy", arms="up", legs="tuck" if ph == "air" else "stand", t=lt, blush=True)
    else:
        clawd(img, 160, 112, 4, breathe(lt), eyes="happy" if lt > 0.3 else "open", arms="wave", t=lt, blush=True)
    T(ov, BW / 2, 14, "Clawd 的一天", 72, CREAM, "m", INK)
    if lt > 0.8:
        T(ov, BW / 2, 124, "谢谢你每天来找我 ♥"[: int((lt - 0.8) * 12)], 32, GOLD, "m")
    if lt > 3.0:
        T(ov, BW / 2, 142, "— fin —", 24, (150, 150, 190), "m")

# ---------------------------------------------------------------- 时间线
SCENES = [
    # 名称, 开始, 结束, 时钟起, 时钟止, 是否显示 HUD
    (scene_title, 0.0, 4.5, 340, 410, False),
    (scene_wake, 4.5, 10.5, 420, 428, True),
    (scene_quantum, 10.5, 19.5, 570, 640, True),
    (scene_math, 19.5, 28.0, 660, 710, True),
    (scene_chat, 28.0, 35.5, 780, 820, True),
    (scene_code, 35.5, 44.0, 900, 980, True),
    (scene_night, 44.0, 52.5, 1380, 1410, True),
    (scene_end, 52.5, 57.0, 0, 0, False),
]
TOTAL = 57.0
HALF = 0.25

def render_scene(i, t):
    fn, a, b, c0, c1, show = SCENES[i]
    lt = max(0.0, t - a)
    m = lerp(c0, c1, clamp(lt / (b - a)))
    base = Image.new("RGB", (BW, BH), INK)
    d = ImageDraw.Draw(base)
    ov = []
    fn(d, base, ov, lt, m)
    if show:
        hud(d, ov, m)
    big = base.resize((W, H), Image.NEAREST)
    draw_overlay(big, ov)
    return big

_r = random.Random(99)
_ranks = list(range(40 * 23))
_r.shuffle(_ranks)

def dissolve_mask(p):
    n = len(_ranks)
    small = Image.new("L", (40, 23))
    small.putdata([255 if r < p * n else 0 for r in _ranks])
    return small.resize((40 * 32, 23 * 32), Image.NEAREST).crop((0, 0, W, H))

def frame(t):
    idx = max(i for i, s in enumerate(SCENES) if s[1] <= t)
    a, b = SCENES[idx][1], SCENES[idx][2]
    if idx > 0 and t - a < HALF:
        pa, pb, p = idx - 1, idx, 0.5 + (t - a) / (2 * HALF)
    elif idx < len(SCENES) - 1 and b - t < HALF:
        pa, pb, p = idx, idx + 1, 0.5 - (b - t) / (2 * HALF)
    else:
        img = render_scene(idx, t)
        pa = None
    if pa is not None:
        img = Image.composite(render_scene(pb, t), render_scene(pa, t), dissolve_mask(p))
    if t > TOTAL - 1.0:
        img = Image.blend(img, Image.new("RGB", (W, H), (0, 0, 0)), clamp((t - (TOTAL - 1.0)) / 0.9))
    return img

# ---------------------------------------------------------------- 芯片音乐 + 音效
SR = 44100
NOTE = {"C": 0, "C#": 1, "D": 2, "D#": 3, "E": 4, "F": 5, "F#": 6, "G": 7, "G#": 8, "A": 9, "A#": 10, "B": 11}

def freq(n):
    return 440 * 2 ** ((12 * (int(n[-1]) + 1) + NOTE[n[:-1]] - 69) / 12)

def tone(buf, t0, dur, f, amp, wave="sq", duty=0.5, decay=4.0, slide=0.0):
    i0, n = int(t0 * SR), int(dur * SR)
    ph = 0.0
    rnd = random.random
    for k in range(n):
        i = i0 + k
        if i >= len(buf):
            break
        tt = k / SR
        ph = (ph + f * (1 + slide * tt) / SR) % 1.0
        if wave == "sq":
            v = 1.0 if ph < duty else -1.0
        elif wave == "tri":
            v = 4 * abs(ph - 0.5) - 1
        elif wave == "sin":
            v = math.sin(ph * 6.2832)
        else:
            v = rnd() * 2 - 1
        env = min(1.0, tt / 0.004) * math.exp(-decay * tt)
        rem = n - k
        if rem < 400:
            env *= rem / 400
        buf[i] += v * amp * env

def make_music(path):
    random.seed(1)
    buf = array.array("f", [0.0]) * int((TOTAL + 1) * SR)
    e8 = 60 / 112 / 2
    bar = 8 * e8
    chords = [("C", "E", "G"), ("A", "C", "E"), ("F", "A", "C"), ("G", "B", "D")]
    roots = ["C3", "A2", "F2", "G2"]
    melA = [[("E5", 2), ("G5", 2), ("C6", 3), ("B5", 1)], [("A5", 2), ("E5", 2), ("A5", 2), ("C6", 2)],
            [("F5", 2), ("A5", 2), ("C6", 2), ("A5", 2)], [("G5", 3), ("F5", 1), ("E5", 2), ("D5", 2)]]
    melB = [[("E5", 2), ("G5", 2), ("C6", 2), ("E6", 2)], [("D6", 2), ("C6", 2), ("A5", 4)],
            [("F5", 2), ("G5", 2), ("A5", 2), ("C6", 2)], [("B5", 2), ("D6", 2), ("G5", 4)]]
    mel = melA + melB
    b = 0
    main0 = None
    while b * bar < 53.5:
        ts = b * bar
        ch, root = chords[b % 4], roots[b % 4]
        sec = "intro" if ts < 4.2 else ("night" if ts >= 43.5 else "main")
        if sec == "main" and main0 is None:
            main0 = b
        for s16 in range(16):
            nt = ch[[0, 1, 2, 1][s16 % 4]] + ("5" if s16 < 8 else "5")
            if sec == "main":
                tone(buf, ts + s16 * e8 / 2, e8 / 2, freq(nt), 0.035, "sq", 0.25, 9)
            elif s16 % 2 == 0:
                tone(buf, ts + s16 * e8 / 2, e8, freq(nt), 0.06, "tri", decay=5)
        if sec == "main":
            for s8 in range(8):
                nt = root if s8 % 2 == 0 else root[:-1] + str(int(root[-1]) + 1)
                tone(buf, ts + s8 * e8, e8 * 0.95, freq(nt), 0.16, "tri", decay=2)
            for beat in range(4):
                bt = ts + beat * 2 * e8
                if beat % 2 == 0:
                    tone(buf, bt, 0.14, 110, 0.35, "sin", decay=22, slide=-4)
                else:
                    tone(buf, bt, 0.12, 0, 0.12, "noise", decay=28)
                tone(buf, bt + e8, 0.03, 0, 0.04, "noise", decay=120)
            k = 0
            for nt, ln in mel[(b - main0) % 8]:
                tone(buf, ts + k * e8, ln * e8 * 0.95, freq(nt), 0.075, "sq", 0.5, 2.2)
                tone(buf, ts + k * e8 + 0.01, ln * e8 * 0.9, freq(nt) * 1.004, 0.02, "sq", 0.125, 2.2)
                k += ln
        else:
            tone(buf, ts, bar, freq(root), 0.16, "tri", decay=0.8)
            if sec == "night":
                k = 0
                for nt, ln in melA[b % 4]:
                    tone(buf, ts + k * e8, ln * e8 * 1.5, freq(nt), 0.07, "tri", decay=3.5)
                    k += ln
        b += 1
    for i, nt in enumerate(("C4", "E4", "G4", "C5", "E5")):
        tone(buf, b * bar + i * 0.05, 3.0, freq(nt), 0.07, "tri", decay=1.1)
    # 音效
    def blip(t, f, amp=0.08, dur=0.06):
        tone(buf, t, dur, f, amp, "sq", 0.5, 20)
    def boing(t, f=260, amp=0.08):
        tone(buf, t, 0.22, f, amp, "sq", 0.5, 8, slide=2.5)
    def thud(t, amp=0.12):
        tone(buf, t, 0.08, 0, amp, "noise", decay=40)
    def spin(t):
        tone(buf, t, 0.45, 400, 0.06, "sq", 0.25, 3, slide=3)
    def clicks(t0, t1):
        t = t0
        while t < t1:
            tone(buf, t, 0.015, 0, 0.05, "noise", decay=200)
            t += 1 / 14
    spin(2.8)
    w = 4.5
    for i in range(3):
        blip(w + 1.2 + i * 0.12, 1320, 0.07)
    spin(w + 1.7); thud(w + 2.3); boing(w + 3.5, 300); thud(w + 4.0)
    for i in range(5):
        blip(w + 4.2 + i * 0.36, 660 + (i % 2) * 220, 0.04)
    q = 10.5
    boing(q + 2.9, 360)
    tone(buf, q + Q_SPLIT, 0.5, 300, 0.07, "tri", decay=2, slide=3)
    for k in range(5):
        blip(q + Q_SPLIT + 0.06 + k * 0.5, 880, 0.03)
    tone(buf, q + Q_MEAS, 0.12, 0, 0.2, "noise", decay=25)
    blip(q + Q_MEAS, 1760, 0.08, 0.15)
    spin(q + 7.0)
    mt = 19.5
    for i in range(4):
        thud(mt + BLOCK_T[i] + 0.35)
        spin(mt + BLOCK_T[i] + 0.5) if i == 3 else boing(mt + BLOCK_T[i] + 0.5, 260 + i * 60)
    for i, f in enumerate((523, 659, 784, 1047)):
        blip(mt + 5.9 + i * 0.07, f, 0.08, 0.2)
    c = 28.0
    for ta, who, k in CHAT:
        blip(c + ta, 1320 if who == "c" else 990, 0.05)
    boing(c + 1.1, 400); spin(c + 5.9)
    cd = 35.5
    clicks(cd, cd + 2.2); clicks(cd + 6.63, cd + 7.38)
    blip(cd + 2.0, 1800, 0.04); blip(cd + 2.1, 2000, 0.04); blip(cd + 2.8, 1600, 0.04)
    boing(cd + 3.0, 300); boing(cd + 4.42, 220, 0.1)
    tone(buf, cd + 4.82, 0.15, 180, 0.12, "sq", 0.5, 18, slide=-3)
    boing(cd + 6.1, 300)
    for i, f in enumerate((784, 1175)):
        blip(cd + 7.4 + i * 0.1, f, 0.08, 0.25)
    spin(cd + 7.5)
    tone(buf, 44.1, 1.0, 500, 0.05, "tri", decay=1.5, slide=-0.4)
    boing(44 + 3.1, 200, 0.05)
    tone(buf, 44 + 5.4, 0.9, 2000, 0.03, "tri", decay=3, slide=-0.5)
    for i, t0 in enumerate((0.5, 1.2, 1.9, 2.8)):
        spin(52.5 + t0) if i == 2 else boing(52.5 + t0, 350 + i * 40, 0.06)
    peak = max(abs(v) for v in buf) or 1.0
    fade0 = int((TOTAL - 1.2) * SR)
    out = array.array("h")
    for i, v in enumerate(buf):
        g = 0.88 / peak
        if i > fade0:
            g *= max(0.0, 1 - (i - fade0) / (1.2 * SR))
        out.append(int(v * g * 32767))
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(out.tobytes())

# ---------------------------------------------------------------- 主程序
def main():
    if len(sys.argv) > 1 and sys.argv[1] == "still":
        os.makedirs(os.path.join(HERE, "previews"), exist_ok=True)
        for s in sys.argv[2:]:
            frame(float(s)).save(os.path.join(HERE, "previews", "t%05.1f.png" % float(s)))
        return
    wav = os.path.join(HERE, "music.wav")
    print("合成音乐 …")
    make_music(wav)
    out = os.path.join(HERE, "Clawd的一天.mp4")
    n = int(TOTAL * FPS)
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                          "-s", "%dx%d" % (W, H), "-r", str(FPS), "-i", "-", "-i", wav,
                          "-c:v", "libx264", "-preset", "medium", "-crf", "16", "-tune", "animation",
                          "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-shortest", out],
                         stdin=subprocess.PIPE)
    for i in range(n):
        p.stdin.write(frame(i / FPS).tobytes())
        if i % 48 == 0:
            print("  帧 %d / %d" % (i, n), flush=True)
    p.stdin.close()
    p.wait()
    print("完成 →", out)

if __name__ == "__main__":
    main()
