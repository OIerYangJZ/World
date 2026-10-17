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
from PIL import Image, ImageDraw, ImageFont

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

# ---------------------------------------------------------------- 主角：像素 Clawd
def clawd(d, x, y, s=2, eyes="open", arms="rest", legs="stand", t=0.0, look=(0, 0), blush=False):
    """(x, y) 为左上角；身体 16×10 个单位，每单位 s 像素。"""
    x, y = int(round(x)), int(round(y))

    def r(u, v, w, h, c):
        x0, y0 = x + int(round(u * s)), y + int(round(v * s))
        x1, y1 = x + int(round((u + w) * s)), y + int(round((v + h) * s))
        if x1 > x0 and y1 > y0:
            d.rectangle([x0, y0, x1 - 1, y1 - 1], fill=c)

    for i, lx in enumerate((3, 5, 10, 12)):
        lh = 2
        if legs == "walk":
            lh = 2 if (int(t * 10) + i) % 2 == 0 else 1
        elif legs == "tuck":
            lh = 1
        r(lx, 8, 1, lh, CLAY_D)
    left, right = (0, 4, 2, 2), (14, 4, 2, 2)
    if arms == "up":
        left, right = (0, 1, 2, 3), (14, 1, 2, 3)
    elif arms == "type":
        a = int(t * 12) % 2
        left, right = (0, 4 + a * 0.5, 2, 2), (14, 4.5 - a * 0.5, 2, 2)
    elif arms == "point":
        right = (14, 1, 2, 3)
    elif arms == "wave":
        wv = int(t * 6) % 2
        right = (14, 0.5 + wv, 2, 3)
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
    if blush:
        r(2.5, 4.5, 1.5, 0.5, BLUSH)
        r(12, 4.5, 1.5, 0.5, BLUSH)

def blink(t, e="open", period=3.1, off=0.0):
    return "closed" if (t + off) % period < 0.12 else e

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
        T(ov, x + p * 10 + math.sin(p * 6) * 2, y - p * 22, "z" if i % 2 else "Z", int(20 + p * 14), mix(col, (70, 70, 110), p * 0.8))

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
    for i, (cx, cy) in enumerate(((20, 88), (190, 70), (96, 96))):
        cloud(d, (cx + lt * 5) % 360 - 30, cy, 1.5, mix((110, 90, 150), (255, 186, 160), 1 - k))
    for bx, bw, top, wins, v in BUILDINGS:
        c = mix((26, 24, 46), (60, 52, 84), v * 0.5 + (1 - k) * 0.3)
        R(d, bx, top, bw, BH - top, c)
        R(d, bx, top, bw, 1, mix(c, (250, 170, 130), 0.5 * (1 - k)))
        for wx, wy, th in wins:
            if th < 0.25 + 0.75 * k:
                R(d, wx, wy, 2, 3, mix((120, 100, 60), GOLD, k))
    e = "sleep" if lt < 2.5 else ("happy" if lt > 3.3 else blink(lt, "open", 0.8, 0.3))
    clawd(d, 144, 112, 2, eyes=e, arms="wave" if lt > 3.3 else "rest", legs="tuck" if lt < 2.5 else "stand", t=lt)
    if lt < 2.5:
        zzz(ov, 176, 110, lt)
    title = "Clawd 的一天"
    tw = text_w(title, 92) / S
    x = BW / 2 - tw / 2
    for i, ch in enumerate(title):
        p = ease_out((lt - 0.3 - i * 0.1) / 0.3)
        if p > 0:
            T(ov, x, 20 - (1 - p) * 14, ch, 92, CREAM, shadow=INK)
        x += text_w(ch, 92) / S
    sub = "A  DAY  IN  THE  LIFE  OF  CLAWD"
    if lt > 1.4:
        T(ov, BW / 2, 50, sub[: int((lt - 1.4) * 30)], 24, GOLD, "m", INK)
    if lt > 2.2:
        T(ov, BW / 2, 60, "量子 · 数学 · 闲聊 · 代码", 30, CREAM, "m", INK)

# ---------------------------------------------------------------- 场景 1：07:00 起床
def scene_wake(d, img, ov, lt, m):
    def scr(d, x, y, w, h):
        if lt > 1.6:
            R(d, x, y, w, h, (30, 34, 54))
            R(d, x, y, w, 3, CLAY)

    room(d, img, m, lt, 0.12, scr)
    if lt > 1.6:
        T(ov, 212, 72, "> claude", 22, GREEN)
        if int(lt * 3) % 2:
            OR(ov, 212, 80, 3, 5, CREAM)
        if lt > 2.2:
            T(ov, 212, 86, "hi ✻", 22, CLAY_L)
    if lt < 2.4:
        bob = 1 if int(lt * 1.5) % 2 else 0
        clawd(d, 58, 118 + bob, 2, eyes="sleep", legs="tuck", t=lt)
        if lt < 2.0:
            zzz(ov, 90, 116, lt)
        if lt > 2.0:
            emote(d, ov, 70, 102, "!", CLAY_D)
    elif lt < 2.9:
        p = (lt - 2.4) / 0.5
        clawd(d, lerp(58, 72, p), lerp(118, 120, p) - 26 * 4 * p * (1 - p), 2, eyes="wide", arms="up", t=lt)
    elif lt < 3.3:
        clawd(d, 72, 120, 2, eyes="wide", arms="up", t=lt)
    elif lt < 5.2:
        p = (lt - 3.3) / 1.9
        bob = -1 if int(lt * 10) % 2 else 0
        clawd(d, lerp(72, 180, ease_io(p)), 120 + bob, 2, eyes=blink(lt), legs="walk", t=lt, look=(1, 0))
    else:
        clawd(d, 180, 120, 2, eyes="happy", arms="wave", t=lt, look=(1, -1))
    caption(d, ov, "07:00", "早安！终端亮了，新的一天开始啦。", lt - 0.5)

# ---------------------------------------------------------------- 场景 2：09:30 量子
_r = random.Random(8)
SMUDGES = [(_r.randrange(14, 300), _r.randrange(12, 120), _r.randrange(8, 30), _r.randrange(2, 6)) for _ in range(14)]

def bloch_tip(lt, cx, cy, Rr, el=0.32):
    th = (math.pi / 2) * ease_io((lt - 1.0) / 1.4)
    ph = max(0.0, lt - 2.4) * 1.7
    x3, y3, z3 = math.sin(th) * math.cos(ph), math.sin(th) * math.sin(ph), math.cos(th)
    return cx + Rr * y3, cy - Rr * z3 * math.cos(el) + Rr * x3 * math.sin(el)

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
    R(d, 260, 126, 6, 2, PINK)
    # 布洛赫球
    cx, cy, Rr = 74, 64, 34
    rev = ease_out(lt / 0.8)
    if rev > 0:
        d.arc([cx - Rr, cy - Rr, cx + Rr, cy + Rr], -90, -90 + 360 * rev, fill=CHALK)
    if lt > 0.5:
        for a in range(0, 360, 12):
            ex = cx + Rr * math.sin(math.radians(a))
            ey = cy + Rr * 0.32 * math.cos(math.radians(a))
            front = math.cos(math.radians(a)) > 0
            if front or a % 24 == 0:
                d.point((ex, ey), fill=CHALK if front else CHALK_D)
        for yy in range(cy - Rr - 6, cy + Rr + 6, 3):
            d.point((cx, yy), fill=CHALK_D)
        for i in range(1, 16):
            tx, ty = bloch_tip(lt - i * 0.06, cx, cy, Rr)
            if lt - i * 0.06 > 2.4:
                d.point((tx, ty), fill=mix(BOARD, CYAN, 1 - i / 16))
        tx, ty = bloch_tip(lt, cx, cy, Rr)
        d.line([cx, cy, tx, ty], fill=CLAY_L, width=1)
        R(d, tx - 1, ty - 1, 3, 3, CLAY)
        R(d, cx - 1, cy - 1, 2, 2, CHALK)
        T(ov, cx + 4, cy - Rr - 11, "|0⟩", 26, CHALK)
        T(ov, cx + 4, cy + Rr + 3, "|1⟩", 26, CHALK)
        T(ov, cx + Rr + 3, cy - 3, "y", 22, CHALK_D)
    # 线路：H + CNOT + 测量
    y0, y1, xa, xb = 36, 60, 176, 298
    wl = int((xb - xa) * ease_out(lt / 0.8))
    R(d, xa, y0, wl, 1, CHALK)
    R(d, xa, y1, wl, 1, CHALK)
    T(ov, 152, y0 - 3.5, "|0⟩", 24, CHALK)
    T(ov, 152, y1 - 3.5, "|0⟩", 24, CHALK)
    if lt > 0.4:
        R(d, 194, 29, 15, 15, BOARD)
        d.rectangle([194, 29, 208, 43], outline=CHALK)
        T(ov, 201.5, 32.5, "H", 26, CHALK, "m")
    if lt > 0.9:
        d.ellipse([228, 34, 232, 38], fill=CHALK)
        R(d, 230, 36, 1, 24, CHALK)
        d.ellipse([224, 54, 236, 66], outline=CHALK)
        R(d, 225, 60, 11, 1, CHALK)
    if lt > 1.4:
        for yy in (y0, y1):
            R(d, 262, yy - 7, 17, 15, BOARD)
            d.rectangle([262, yy - 7, 278, yy + 7], outline=CHALK)
            d.arc([265, yy - 3, 275, yy + 7], 180, 360, fill=CHALK)
            d.line([270, yy + 2, 275, yy - 4], fill=CHALK)
    if lt > 1.6:
        for off in (0.0, 0.5):
            px = xa + ((lt - 1.6) * 0.37 + off) % 1 * 84
            c0 = CHALK if px < 201 else (CYAN if px < 230 else PINK)
            c1 = CHALK if px < 230 else PINK
            if not (192 < px < 210 or 260 < px < 280):
                R(d, px - 1, y0 - 1, 3, 3, c0)
            if not 260 < px < 280:
                R(d, px - 1, y1 - 1, 3, 3, c1)
            if px >= 230:
                for yy in range(y0 + 3, y1 - 2, 2):
                    d.point((px + round(math.sin(yy * 0.6 + lt * 12)), yy), fill=PINK)
    f1 = "|Φ⁺⟩ = (|00⟩ + |11⟩) / √2"
    if lt > 2.6:
        T(ov, 156, 80, f1[: int((lt - 2.6) * 16)], 28, CHALK)
    if lt > 4.6:
        T(ov, 156, 96, "⟨ZZ⟩ = ⟨XX⟩ = 1"[: int((lt - 4.6) * 16)], 28, GOLD)
    if lt > 5.8:
        for i, (sx, sy) in enumerate(((290, 82), (300, 100), (282, 108))):
            if int(lt * 4 + i) % 2:
                R(d, sx, sy - 2, 1, 5, GOLD)
                R(d, sx - 2, sy, 5, 1, GOLD)
    look = (-1, -1) if lt < 2.6 else (1, -1)
    e = "happy" if lt > 6.0 else blink(lt, "open")
    clawd(d, 120, 120, 2, eyes=e, arms="point", t=lt, look=look, blush=lt > 6.0)
    R(d, 150, 118, 2, 2, CHALK)
    if 5.8 < lt < 7.4:
        emote(d, ov, 140, 102, "!", CLAY_D)
    caption(d, ov, "09:30", "量子：把 Bell 态和纠缠一起推导清楚。", lt - 0.4)

# ---------------------------------------------------------------- 场景 3：11:00 数学
_r = random.Random(21)
SYMS = ["∀ε>0", "∃δ>0", "∑1/n²=π²/6", "e^{iπ}+1=0", "∫e^{-x²}dx=√π", "⇒", "≤", "∇·E", "ℤ", "⊗", "Tr ρ = 1", "∞"]
FLOATERS = [(SYMS[i % len(SYMS)], _r.randrange(0, 300), _r.randrange(0, 200), _r.uniform(3, 8)) for i in range(16)]
BLOCK_X = [40, 106, 172, 238]
BLOCK_T = [0.3 + i * 1.3 for i in range(4)]
LABELS = ["引理 1", "引理 2", "引理 3", "定 理"]

def block_top(i):
    return 140 - (i + 1) * 24

def scene_math(d, img, ov, lt, m):
    R(d, 0, 0, BW, BH, (34, 32, 72))
    for xx in range(0, BW, 10):
        R(d, xx, 0, 1, BH, (42, 40, 86))
    for yy in range(0, BH, 10):
        R(d, 0, yy, BW, 1, (42, 40, 86))
    f = F("mono", 11)
    for s, x0, y0, sp in FLOATERS:
        y = (y0 - lt * sp) % 200 - 16
        d.text((x0, y), s, font=f, fill=(78, 74, 138))
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
        R(d, bx, top + off + 22, 56, 1, mix(c, INK, 0.25))
        T(ov, bx + 28, top + off + 7, LABELS[i], 26, INK if i == 3 else CREAM, "m")
        if i > 0 and p >= 1:
            d.text((bx - 8, top + 4), "⇒", font=F("mono", 10), fill=GOLD)
    # Clawd 跳台阶
    pos = [(6, 120)] + [(BLOCK_X[i] + 12, block_top(i) - 20) for i in range(4)]
    cur, jump = 0, None
    for i in range(4):
        js = BLOCK_T[i] + 0.45
        if lt >= js + 0.5:
            cur = i + 1
        elif lt >= js:
            jump = (i, (lt - js) / 0.5)
    if jump:
        i, p = jump
        (xa, ya), (xb, yb) = pos[i], pos[i + 1]
        clawd(d, lerp(xa, xb, p), lerp(ya, yb, p) - 22 * 4 * p * (1 - p), 2, eyes="wide", arms="up", legs="tuck", t=lt)
    else:
        x, y = pos[cur]
        done = lt > 5.8
        clawd(d, x, y, 2, eyes="happy" if done else blink(lt), arms="wave" if done else "rest", t=lt, look=(1, -1), blush=done)
    # 旗子与 Q.E.D.
    if lt > 5.4:
        p = ease_out((lt - 5.4) / 0.3)
        fx, ft = BLOCK_X[3] + 50, block_top(3)
        R(d, fx, ft - 24 * p, 1, 24 * p, CREAM)
        if p >= 1:
            for row in range(7):
                wv = round(math.sin(lt * 8 + row * 0.8))
                R(d, fx + 1, ft - 24 + row, 10 + wv, 1, CLAY if row % 6 else CLAY_L)
    if lt > 5.8:
        p = ease_out((lt - 5.8) / 0.25)
        size = int(64 * (1 + 0.8 * (1 - p)))
        T(ov, 150, 10, "Q.E.D.", size, GOLD, "m", INK)
        sq = 9 * (1 + 0.8 * (1 - p))
        wq = text_w("Q.E.D.", size) / S
        R(d, 150 + wq / 2 + 4, 13 + (size / S) * 0.55 - sq / 2, sq, sq, GOLD)
        for i in range(8):
            ang = i * math.pi / 4 + lt
            rr = 36 + 10 * p
            sx, sy = 160 + math.cos(ang) * rr * 1.8, 20 + math.sin(ang) * rr * 0.4
            if int(lt * 6 + i) % 2:
                R(d, sx, sy, 2, 2, CREAM)
    caption(d, ov, "11:00", "数学：引理一块块垒上去——证毕 ∎", lt - 0.4)

# ---------------------------------------------------------------- 场景 4：13:00 闲聊
CHAT = [
    (0.5, "u", "午饭吃什么好？"),
    (2.0, "c", "楼下那家拉面？今天适合喝点热汤。"),
    (3.3, "u", "好主意！对了，天为什么是蓝的？"),
    (4.9, "c", "瑞利散射：强度 ∝ 1/λ⁴，蓝光散得最多～"),
    (6.3, "u", "懂了，谢谢 Clawd！"),
]

def bubble(d, x, y, w, h, c):
    R(d, x + 1, y, w - 2, h, c)
    R(d, x, y + 1, w, h - 2, c)

def scene_chat(d, img, ov, lt, m):
    R(d, 0, 0, BW, 140, WALL)
    for yy in range(8, 118, 12):
        for xx in range(6 + (yy // 12 % 2) * 6, BW, 12):
            d.point((xx, yy), fill=WALL_D)
    R(d, 0, 118, BW, 22, WALL_D)
    R(d, 0, 117, BW, 2, WOOD)
    R(d, 0, 140, BW, 40, FLOOR)
    R(d, 0, 152, BW, 1, FLOOR_D)
    R(d, 210, 14, 100, 84, WOOD_D)
    img.paste(window_view(90, 74, m, lt), (215, 19))
    R(d, 259, 19, 2, 74, WOOD)
    R(d, 206, 96, 108, 4, WOOD)
    # 光斑
    for i in range(4):
        R(d, 200 - i * 14, 140 + i * 3, 40, 2, mix(FLOOR, CREAM, 0.25))
    # 凳子、小桌、茶
    R(d, 232, 128, 32, 3, WOOD)
    R(d, 235, 131, 2, 9, WOOD_D)
    R(d, 259, 131, 2, 9, WOOD_D)
    R(d, 272, 116, 30, 3, WOOD)
    R(d, 286, 119, 2, 21, WOOD_D)
    R(d, 280, 108, 9, 8, CREAM)
    R(d, 289, 110, 2, 4, CREAM)
    R(d, 281, 109, 7, 1, (170, 120, 70))
    for i in range(3):
        p = (lt * 0.8 + i / 3) % 1
        d.point((283 + round(math.sin(p * 7 + i) * 1.5), 106 - p * 14), fill=mix(CREAM, WALL, p))
    # 聊天窗口
    R(d, 9, 30, 196, 112, INK)
    R(d, 10, 31, 194, 10, CLAY)
    for i in range(3):
        R(d, 14 + i * 5, 35, 2, 2, CREAM)
    T(ov, 107, 32.3, "chat · Clawd", 22, CREAM, "m")
    R(d, 10, 41, 194, 100, PAPER)
    slots = [(ta - (0.9 if who == "c" else 0), ta, who, s) for ta, who, s in CHAT]
    vis = [sl for sl in slots if lt >= sl[0]]
    for k, (ts, ta, who, s) in enumerate(vis):
        up = sum(ease_out((lt - vis[j][0]) / 0.2) for j in range(k + 1, len(vis)))
        pop = ease_out((lt - ts) / 0.15)
        typing = lt < ta
        w = 26 if typing else text_w(s, 24) / S + 9
        h = 12
        y = 134 - up * 17 - h + (1 - pop) * 4
        if y < 44:
            continue
        x = 15 if who == "u" else 199 - w
        col = (228, 222, 208) if who == "u" else CLAY
        bubble(d, x, y, w, h, col)
        R(d, x + (2 if who == "u" else w - 4), y + h - 1, 2, 2, col)
        if typing:
            for i in range(3):
                R(d, x + 7 + i * 5, y + 5 - (1 if int(lt * 8) % 3 == i else 0), 2, 2, CREAM)
        else:
            T(ov, x + 4.5, y + 2.6, s, 24, INK if who == "u" else CREAM)
    replying = any(ts <= lt < ta + 0.7 for ts, ta, who, s in slots if who == "c")
    done = lt > 6.5
    e = "happy" if (replying and any(ta <= lt < ta + 0.7 for ts, ta, who, s in slots if who == "c")) or done else blink(lt, "open")
    clawd(d, 232, 110, 2, eyes=e, arms="wave" if done else "rest", legs="tuck", t=lt, look=(-1, 0), blush=done)
    if done:
        emote(d, ov, 250, 94, "♥", PINK)
    caption(d, ov, "13:00", "闲聊：午饭吃什么、天为什么是蓝的，都能聊。", lt - 0.4)

# ---------------------------------------------------------------- 场景 5：15:00 写代码
CODE = [
    "import numpy as np",
    "",
    "def bell_state():",
    "    psi = np.zeros(4)",
    "    psi[[0, 3]] = 1 / np.sqrt(3)",
    "    return psi",
    "",
    "def fidelity(a, b):",
    "    return abs(np.vdot(a, b))**2",
]
KW = {"import", "as", "def", "return"}
CODE_SIZE, CODE_LH, CODE_X, CODE_Y = 24, 7.5, 110, 14
BUG_COL = len("    psi[[0, 3]] = 1 / np.sqrt(")
FIX_T, CPS, TYPE0 = 4.1, 34, 0.3

def tok_color(tok, prev):
    if tok in KW:
        return PINK
    if prev == "def":
        return CYAN
    if tok.isdigit():
        return GOLD
    if tok in ("np", "abs"):
        return (150, 200, 255)
    if re.match(r"[^\w\s]", tok):
        return (170, 170, 200)
    return CREAM

def scene_code(d, img, ov, lt, m):
    R(d, 0, 0, BW, 130, mix(WALL, GOLD, 0.08))
    d.polygon([(0, 20), (60, 0), (84, 0), (40, 130), (0, 130)], fill=mix(WALL, (255, 240, 200), 0.45))
    R(d, 0, 130, BW, 5, WOOD)
    R(d, 0, 135, BW, 45, WOOD_D)
    R(d, 88, 8, 222, 116, INK)
    R(d, 92, 12, 214, 106, SCREEN)
    R(d, 190, 124, 18, 6, INK)
    R(d, 94, 84, 210, 32, (14, 15, 24))
    R(d, 94, 84, 210, 1, (60, 62, 90))
    cw = F("mono", CODE_SIZE).getlength("0") / S
    fixed = lt >= FIX_T
    bx = CODE_X + (BUG_COL + 0.5) * cw
    by = CODE_Y + 4 * CODE_LH + 3
    if FIX_T <= lt < FIX_T + 1.2:
        OR(ov, CODE_X + BUG_COL * cw - 0.5, CODE_Y + 4 * CODE_LH - 0.5, cw + 1, 7.5, (120, 96, 30))
    n = int(max(0.0, lt - TYPE0) * CPS)
    for li, line in enumerate(CODE):
        if li == 4 and fixed:
            line = line.replace("sqrt(3)", "sqrt(2)")
        y = CODE_Y + li * CODE_LH
        if n <= 0:
            break
        T(ov, CODE_X - 3, y, str(li + 1), CODE_SIZE, (80, 84, 120), "r")
        x, prev = CODE_X, ""
        for tok in re.findall(r"\s+|\w+|[^\w\s]", line):
            if n <= 0:
                break
            part = tok[:n]
            n -= len(tok)
            if part.strip():
                T(ov, x, y, part, CODE_SIZE, tok_color(tok, prev))
                prev = tok
            x += len(part) * cw
        n -= 1
        if n <= 0 and int(lt * 3) % 2:
            OR(ov, x + 0.5, y + 0.5, 2, 6.5, CREAM)
    # bug 爬过来
    if 1.8 <= lt < FIX_T:
        p = ease_io((lt - 1.8) / 1.6)
        gx = lerp(302, bx, p)
        gy = by - 3 + (round(math.sin(lt * 20)) if p < 1 else 0)
        OR(ov, gx - 3, gy - 2, 7, 5, (72, 160, 80))
        OR(ov, gx - 2, gy - 2, 5, 1, (120, 210, 120))
        OR(ov, gx - 3, gy - 4, 1, 2, (72, 160, 80))
        OR(ov, gx + 3, gy - 4, 1, 2, (72, 160, 80))
        lg = int(lt * 12) % 2
        for i in range(3):
            OR(ov, gx - 3 + i * 3, gy + 3 + lg * (i % 2), 1, 1, INK)
        OR(ov, gx - 2, gy - 1, 1, 1, INK)
        OR(ov, gx + 2, gy - 1, 1, 1, INK)
    if FIX_T <= lt < FIX_T + 0.5:
        q = (lt - FIX_T) / 0.5
        for i in range(8):
            a = i * math.pi / 4
            OR(ov, bx + math.cos(a) * (4 + q * 12), by - 3 + math.sin(a) * (4 + q * 10), 2, 2, GOLD)
        T(ov, bx + 8, by - 16 - q * 4, "fixed!", 22, GOLD)
    # 终端
    if lt > 4.7:
        T(ov, 98, 87, "$ pytest -q"[: int((lt - 4.7) * 20)], 22, CREAM)
    if lt > 5.3:
        p = clamp((lt - 5.3) / 1.1)
        R(d, 98, 98, 140, 4, (40, 44, 64))
        R(d, 98, 98, int(140 * p), 4, GREEN)
        T(ov, 244, 96, "%3d%%" % int(p * 100), 20, GREEN)
    if lt > 6.5:
        T(ov, 98, 106, "✓ 128 passed in 0.42s", 22, GREEN)
    # Clawd 在键盘后
    if lt < 3.5:
        e, arms = blink(lt, "open"), "type"
        look = (1, 0) if lt < 2.2 else (1, -1)
    elif lt < FIX_T:
        e, arms, look = "wide", "up", (1, -1)
    elif lt < FIX_T + 0.8 or lt > 6.5:
        e, arms, look = "happy", "wave" if lt > 6.5 else "rest", (1, 0)
    else:
        e, arms, look = blink(lt), "type", (1, 0)
    typing = arms == "type" and lt < TYPE0 + sum(len(l) + 1 for l in CODE) / CPS + 0.3
    clawd(d, 34, 110, 2, eyes=e, arms=arms if (arms != "type" or typing) else "rest", t=lt, look=look, blush=lt > 6.5)
    R(d, 24, 125, 56, 6, (70, 72, 96))
    for i in range(9):
        R(d, 26 + i * 6, 126, 4, 2, (130, 134, 160))
        R(d, 28 + i * 6 - 3, 128, 4, 2, (110, 114, 140))
    if 3.5 <= lt < FIX_T:
        emote(d, ov, 60, 92, "!", CLAY_D)
    elif lt > 6.6:
        emote(d, ov, 60, 92, "✓", (60, 150, 70))
    caption(d, ov, "15:00", "写代码：抓住 bug，跑测试——全绿通过！", lt - 0.4)

# ---------------------------------------------------------------- 场景 6：23:00 晚安
LOG = [("ψ  纠缠态", "×1"), ("∎  定理", "×1"), ("✓  bug 修复", "×1"), ("♥  闲聊", "×∞")]

def scene_night(d, img, ov, lt, m):
    def scr(d, x, y, w, h):
        px = x + 4 + (lt * 9) % (w - 12)
        py = y + 4 + abs(((lt * 6) % (2 * (h - 12))) - (h - 12))
        R(d, px, py, 4, 4, (60, 50, 90))

    room(d, img, m, lt, 0.85, scr)
    if 5.2 < lt < 6.2:
        p = (lt - 5.2)
        sx, sy = 96 - p * 70, 26 + p * 28
        for i in range(6):
            d.point((sx + i * 2, sy - i), fill=mix((255, 250, 220), (40, 40, 80), i / 6))
    clawd(d, 58, 118 + (1 if int(lt * 1.5) % 2 else 0), 2, eyes="sleep", legs="tuck", t=lt)
    zzz(ov, 90, 116, lt)
    if lt > 1.0:
        p = ease_out((lt - 1.0) / 0.5)
        oy = (1 - p) * -70
        R(d, 116, 8 + oy, 136, 58, INK)
        R(d, 117, 9 + oy, 134, 56, (238, 230, 210))
        R(d, 181, 6 + oy, 6, 5, CLAY)
        T(ov, 184, 13 + oy, "今日日志", 26, CLAY_D, "m")
        for i, (a, b) in enumerate(LOG):
            if lt > 1.8 + i * 0.5:
                y = 25 + i * 9.5 + oy
                T(ov, 124, y, a, 24, INK)
                T(ov, 244, y, b, 24, CLAY_D, "r")
    caption(d, ov, "23:00", "晚安。明天见——继续一起探索。", lt - 0.4)

# ---------------------------------------------------------------- 片尾
def scene_end(d, img, ov, lt, m):
    img.paste(sky_img(BW, BH, 0), (0, 0))
    stars(d, 0, 0, BW, BH, lt, 1.0)
    clawd(d, 128, 64, 4, eyes="happy" if lt > 1.2 else blink(lt, "open", 1.0, 0.6), arms="wave" if lt > 1.2 else "rest", t=lt, blush=True)
    R(d, 132, 108, 56, 2, (30, 28, 60))
    T(ov, BW / 2, 16, "Clawd 的一天", 72, CREAM, "m", INK)
    if lt > 0.8:
        T(ov, BW / 2, 122, "谢谢你每天来找我：算量子、证定理、写代码、随便聊聊。"[: int((lt - 0.8) * 22)], 28, GOLD, "m")
    if lt > 3.0:
        T(ov, BW / 2, 140, "— fin —", 24, (150, 150, 190), "m")

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
    tone(buf, 4.5 + 2.0, 0.12, 880, 0.08, "sq", 0.5, 10, slide=1.5)
    tone(buf, 4.5 + 2.4, 0.25, 300, 0.09, "sq", 0.5, 6, slide=3)
    for i in range(4):
        tone(buf, 19.5 + BLOCK_T[i] + 0.3, 0.08, 0, 0.12, "noise", decay=40)
        tone(buf, 19.5 + BLOCK_T[i] + 0.45, 0.22, 260 + i * 60, 0.08, "sq", 0.5, 8, slide=2.5)
    for i, f in enumerate((523, 659, 784, 1047)):
        blip(19.5 + 5.8 + i * 0.07, f, 0.08, 0.2)
    for ta, who, s in CHAT:
        blip(28.0 + ta, 1320 if who == "c" else 990, 0.05)
    t = 35.5 + TYPE0
    end = 35.5 + TYPE0 + sum(len(l) + 1 for l in CODE) / CPS
    while t < end:
        if not (35.5 + 3.5 < t < 35.5 + FIX_T + 0.8):
            tone(buf, t, 0.015, 0, 0.05, "noise", decay=200)
        t += 1 / 11
    tone(buf, 35.5 + FIX_T, 0.15, 180, 0.12, "sq", 0.5, 18, slide=-3)
    for i, f in enumerate((784, 1175)):
        blip(35.5 + 6.5 + i * 0.1, f, 0.08, 0.25)
    tone(buf, 44 + 5.2, 0.9, 2000, 0.03, "tri", decay=3, slide=-0.5)
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
