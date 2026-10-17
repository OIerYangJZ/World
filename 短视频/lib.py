# -*- coding: utf-8 -*-
"""
《啾啾日记》系列公用库 —— 软萌手绘风：细棕描边、粉色斜线腮红、背景虚化、纸面颗粒
  Pen / Xf      2× 超采样画笔；角色局部坐标变换（缩放、挤压拉伸、旋转）
  draw_chick    原创主角「啾啾」：圆滚滚的小黄鸡
  draw_clawd    像素小 Clawd（与软萌画风形成反差）
  Meadow        草地背景：分层预渲染 + 视差裁切
  其余          特效、字幕、音频合成、ffmpeg 输出
每一集只需写自己的时间轴（见 ep01.py）。
"""
import math, random, os, glob, array, wave, subprocess
from multiprocessing import Pool
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

W, H = 1080, 1920        # 竖屏 9:16
SS = 2                   # 角色层超采样倍数
FPS = 24
SR = 44100

# ---------------------------------------------------------------- 调色板
INK = (88, 64, 58)               # 描边：暖棕
WHITE = (255, 255, 255)
CREAM = (255, 252, 244)
CHICK = (255, 233, 150)
CHICK_L = (255, 241, 190)
BEAK = (250, 168, 82)
BLUSH = (250, 172, 182)
BLUSH_D = (236, 128, 148)
MOUTH = (156, 62, 70)
TONGUE = (242, 132, 146)
GLOOM = (140, 162, 224)
SWEAT = (184, 224, 250)
CLAWD = (217, 119, 87)           # Clawd 橙
CLAWD_EYE = (38, 28, 26)
HEART = (236, 92, 108)
TUFT = (124, 196, 100)
TUFT_L = (150, 212, 120)
TUFT_D = (86, 156, 78)
SHADOW = (64, 120, 58, 52)
STAR = (255, 238, 150)


# ---------------------------------------------------------------- 小工具
def clamp(v, a=0.0, b=1.0):
    return max(a, min(b, v))

def lerp(a, b, k):
    return a + (b - a) * k

def ease_io(p):
    p = clamp(p)
    return p * p * (3 - 2 * p)

def ease_out(p):
    p = clamp(p)
    return 1 - (1 - p) ** 3

def back_out(p, s=2.2):
    """带回弹的弹出曲线"""
    p = clamp(p) - 1
    return p * p * ((s + 1) * p + s) + 1

def ramp(t, a, b):
    return clamp((t - a) / (b - a)) if b > a else float(t >= a)

def window(t, a, b, c, d):
    return min(ease_io(ramp(t, a, b)), 1 - ease_io(ramp(t, c, d)))

def arc01(u):
    """0→1→0 的抛物线"""
    return 4 * u * (1 - u) if 0 <= u <= 1 else 0.0

def mixc(a, b, k):
    return tuple(int(round(a[i] + (b[i] - a[i]) * k)) for i in range(3))

def hsh(i, salt=0):
    x = math.sin(i * 127.1 + salt * 311.7) * 43758.5453
    return x - math.floor(x)

def smax(a, b, k):
    """平滑的 max"""
    return (a + b + math.sqrt((a - b) ** 2 + k * k)) / 2


# ---------------------------------------------------------------- 形状（局部坐标，y 向下）
def ell(cx, cy, rx, ry, ang=0.0, n=40):
    ca, sa = math.cos(ang), math.sin(ang)
    out = []
    for i in range(n):
        a = 2 * math.pi * i / n
        x, y = math.cos(a) * rx, math.sin(a) * ry
        out.append((cx + x * ca - y * sa, cy + x * sa + y * ca))
    return out

def arc(cx, cy, rx, ry, a0, a1, n=16):
    return [(cx + math.cos(a0 + (a1 - a0) * i / n) * rx, cy + math.sin(a0 + (a1 - a0) * i / n) * ry)
            for i in range(n + 1)]

def blob(cx, cy, rx, ry, n_top=2.1, n_bot=2.8, m=64):
    """上圆下略平的团子形"""
    pts = []
    for i in range(m):
        a = 2 * math.pi * i / m
        c, s = math.cos(a), math.sin(a)
        n = n_bot if s > 0 else n_top
        pts.append((cx + rx * math.copysign(abs(c) ** (2 / n), c),
                    cy + ry * math.copysign(abs(s) ** (2 / n), s)))
    return pts

def teardrop(bx, by, length, width, ang, m=24):
    """圆头在 (bx,by)，尖端朝 ang 方向"""
    ca, sa = math.cos(ang), math.sin(ang)
    out = []
    for i in range(m):
        a = 2 * math.pi * i / m
        x = math.cos(a)
        y = math.sin(a) * math.sin(a / 2) ** 1.2
        X, Y = (1 - x) / 2 * length, y * width
        # x=1 时尖端，此处翻转使 X=length 为尖端
        X = length - X
        out.append((bx + X * ca - Y * sa, by + X * sa + Y * ca))
    return out

def chaikin(pts, it=2, closed=True):
    for _ in range(it):
        out = []
        n = len(pts)
        for i in range(n if closed else n - 1):
            p, q = pts[i], pts[(i + 1) % n]
            out.append((0.75 * p[0] + 0.25 * q[0], 0.75 * p[1] + 0.25 * q[1]))
            out.append((0.25 * p[0] + 0.75 * q[0], 0.25 * p[1] + 0.75 * q[1]))
        if not closed:
            out = [pts[0]] + out + [pts[-1]]
        pts = out
    return pts

def star4(cx, cy, r, rot=0.0, inner=0.3):
    pts = []
    for i in range(8):
        a = rot + i * math.pi / 4 - math.pi / 2
        rr = r if i % 2 == 0 else r * inner
        pts.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr))
    return chaikin(pts, 1)

def qbez(p0, p1, p2, n=10):
    return [((1 - u) ** 2 * p0[0] + 2 * u * (1 - u) * p1[0] + u * u * p2[0],
             (1 - u) ** 2 * p0[1] + 2 * u * (1 - u) * p1[1] + u * u * p2[1])
            for u in (i / n for i in range(n + 1))]


# ---------------------------------------------------------------- 画笔
class Pen:
    """在 2× 图层上作画；输入用 1× 画面坐标，oy 是图层顶端在画面中的 y"""
    def __init__(self, img, oy=0, s=SS):
        self.img, self.oy, self.s = img, oy, s
        self.d = ImageDraw.Draw(img, "RGBA")

    def P(self, x, y):
        return (x * self.s, (y - self.oy) * self.s)

    def Ps(self, pts):
        return [self.P(x, y) for x, y in pts]

    def poly(self, pts, fill=None, ol=None, w=3.0):
        if len(pts) < 3:
            return
        sp = self.Ps(pts)
        if fill is not None:
            self.d.polygon(sp, fill=fill)
        if ol is not None:
            self.d.line(sp + sp[:2], fill=ol, width=max(1, round(w * self.s)), joint="curve")

    def line(self, pts, col, w, caps=True):
        sp = self.Ps(pts)
        ww = max(1, round(w * self.s))
        self.d.line(sp, fill=col, width=ww, joint="curve")
        if caps:
            r = ww / 2
            for x, y in (sp[0], sp[-1]):
                self.d.ellipse((x - r, y - r, x + r, y + r), fill=col)

    def circle(self, cx, cy, r, fill):
        x, y = self.P(cx, cy)
        r *= self.s
        self.d.ellipse((x - r, y - r, x + r, y + r), fill=fill)

    def ellipse(self, cx, cy, rx, ry, fill):
        x, y = self.P(cx, cy)
        self.d.ellipse((x - rx * self.s, y - ry * self.s, x + rx * self.s, y + ry * self.s), fill=fill)


class Xf:
    """角色局部坐标 → 画面坐标。原点在脚底中心；先缩放/挤压，再旋转。"""
    def __init__(self, ox, oy, k=1.0, sx=1.0, sy=1.0, rot=0.0):
        self.ox, self.oy, self.k = ox, oy, k
        self.ax, self.ay = k * sx, k * sy
        self.c, self.s = math.cos(rot), math.sin(rot)

    def __call__(self, x, y):
        x *= self.ax
        y *= self.ay
        return (self.ox + x * self.c - y * self.s, self.oy + x * self.s + y * self.c)

    def pts(self, pts):
        return [self(x, y) for x, y in pts]


# ---------------------------------------------------------------- 角色：啾啾
def _eye(pen, X, cx, cy, kind, lw):
    if kind in ("happy", "laugh"):
        pen.line(X.pts(arc(cx, cy + 5, 12, 10, math.pi * 1.08, math.pi * 1.92, 12)), INK, lw * 1.15)
        return
    if kind == "closed":
        pen.line(X.pts(arc(cx, cy - 2, 11, 6, math.pi * 0.12, math.pi * 0.88, 10)), INK, lw * 1.1)
        return
    if kind == "swirl":      # 晕倒的蚊香眼
        pts = [(cx + math.cos(-a * 0.55) * a * 0.5, cy + math.sin(-a * 0.55) * a * 0.5) for a in range(27)]
        pen.line(X.pts(pts), INK, lw * 0.8)
        return
    if kind == "shock":
        pen.poly(X.pts(ell(cx, cy, 6.5, 8, n=20)), fill=INK)
        pen.poly(X.pts(ell(cx - 1.5, cy - 2.5, 2, 2, n=10)), fill=WHITE)
        return
    big = kind in ("big", "sparkle")
    rx, ry = (14.5, 18) if big else ((8.5, 11) if kind == "blank" else (10.5, 13.5))
    pen.poly(X.pts(ell(cx, cy, rx, ry, n=28)), fill=INK)
    if kind == "sparkle":
        pen.poly(X.pts(star4(cx - 3, cy - 5, 9.5, inner=0.28)), fill=WHITE)
        pen.poly(X.pts(ell(cx + 5, cy + 7, 2.6, 2.6, n=10)), fill=WHITE)
        pen.poly(X.pts(ell(cx - 6, cy + 6, 1.6, 1.6, n=8)), fill=WHITE)
    else:
        r1 = rx * 0.42
        pen.poly(X.pts(ell(cx - rx * 0.3, cy - ry * 0.36, r1, r1, n=14)), fill=WHITE)
        if kind != "blank":
            pen.poly(X.pts(ell(cx + rx * 0.35, cy + ry * 0.38, r1 * 0.42, r1 * 0.42, n=10)), fill=WHITE)


def draw_chick(pen, st):
    """
    st 字段：x, y（脚底，画面坐标）、k 缩放、sx/sy 挤压、rot 旋转、
    face(-1 朝左 .. 1 朝右)、eyes、mouth(0..1 张嘴)、wl/wr(0 垂 .. 1 举)、
    step 步伐相位、walk(0..1)、tuft(0..1 炸毛)、sway 呆毛摆动、gloom(0..1)、sweat(None 或 0..1)
    """
    k = st.get("k", 1.0)
    X = Xf(st["x"], st["y"], k, st.get("sx", 1.0), st.get("sy", 1.0), st.get("rot", 0.0))
    lw = 3.3 * k
    face = st.get("face", 0.0)
    fx = 24 * face

    # 小脚
    ph, walk = st.get("step", 0.0), st.get("walk", 0.0)
    for side, sgn in ((-1, 1), (1, -1)):
        lift = max(0.0, sgn * math.sin(ph)) * 12 * walk
        cx = side * 40 + face * 14
        pen.poly(X.pts(ell(cx, -6 - lift, 25, 12, n=24)), fill=BEAK, ol=INK, w=lw * 0.85)

    # 头顶三根呆毛（画在身体之前，根部被身体盖住）
    tf, sway = st.get("tuft", 0.0), st.get("sway", 0.0)
    for j, a in enumerate((-0.5, 0.0, 0.5)):
        ang = -math.pi / 2 + a * (1 + 0.5 * tf) + sway * (1.2 if j == 1 else 0.8)
        L = (52 + 16 * tf) * (1.0 if j == 1 else 0.78)
        pen.poly(X.pts(teardrop(fx * 0.4 + a * 26, -206, L, 15 - 3 * tf, ang)), fill=CHICK, ol=INK, w=lw * 0.8)

    # 身体
    pen.poly(X.pts(blob(0, -118, 126, 114)), fill=CHICK, ol=INK, w=lw)
    pen.poly(X.pts(ell(fx * 0.5, -54, 70, 34)), fill=CHICK_L)

    # 阴郁竖线
    g = st.get("gloom", 0.0)
    if g > 0.01:
        for j, xx in enumerate((-42, -14, 14, 42)):
            top = -222 + abs(xx) * 0.25
            pen.line(X.pts([(fx * 0.5 + xx, top), (fx * 0.5 + xx, top + 30 - abs(xx) * 0.2)]),
                     mixc(CHICK, GLOOM, g), lw * 0.9, caps=False)

    # 腮红
    for side in (-1, 1):
        bx = fx * 0.75 + side * 76
        by = -112
        pen.poly(X.pts(ell(bx, by, 20, 11, n=24)), fill=mixc(CHICK, BLUSH, 0.85))
        for j in (-1, 0, 1):
            pen.line(X.pts([(bx + j * 8 - 3, by + 4.5), (bx + j * 8 + 3, by - 4.5)]), BLUSH_D, lw * 0.5)

    # 眼睛
    eyes = st.get("eyes", "dot")
    ex = 40 * (1 - 0.1 * abs(face))
    for side in (-1, 1):
        _eye(pen, X, fx + side * ex, -146, eyes, lw)

    # 嘴 + 喙
    m = st.get("mouth", 0.0)
    bx, by = fx, -118
    if m > 0.04:
        oh = 5 + 17 * m
        pen.poly(X.pts(chaikin([(bx - 12 - 3 * m, by), (bx + 12 + 3 * m, by), (bx + 7, by + oh), (bx - 7, by + oh)], 3)),
                 fill=MOUTH, ol=INK, w=lw * 0.75)
        pen.poly(X.pts(ell(bx, by + oh * 0.72, 7 + 2 * m, oh * 0.26, n=18)), fill=TONGUE)
        pen.poly(X.pts(chaikin([(bx - 7, by + oh - 1), (bx + 7, by + oh - 1), (bx, by + oh + 6)], 3)),
                 fill=BEAK, ol=INK, w=lw * 0.7)
    up = 2.5 * m
    pen.poly(X.pts(chaikin([(bx - 13, by - 7 - up), (bx + 13, by - 7 - up), (bx, by + 7 - up)], 3)),
             fill=BEAK, ol=INK, w=lw * 0.8)

    # 小翅膀（像短短的小手）
    for side in (-1, 1):
        a = st.get("wl" if side < 0 else "wr", 0.0)
        ang = math.radians(lerp(64, -50, a))
        dx, dy = math.cos(ang) * side, math.sin(ang)
        bx0, by0 = side * 110, -96
        pen.poly(X.pts(ell(bx0 + dx * 20, by0 + dy * 20, 27, 18, math.atan2(dy, dx), n=28)),
                 fill=CHICK, ol=INK, w=lw * 0.9)

    # 汗珠
    sw = st.get("sweat")
    if sw is not None:
        side = 1 if face <= 0 else -1
        pen.poly(X.pts(teardrop(side * 118, -196 + 26 * sw, 34, 13, -math.pi / 2)), fill=SWEAT, ol=INK, w=lw * 0.7)


# ---------------------------------------------------------------- 角色：像素小 Clawd
CLAWD_ROWS = [
    "..############..",
    "..###E####E###..",
    "#####E####E#####",
    "################",
    "..############..",
    "...A.B....A.B...",
    "...A.B....A.B...",
]

def draw_clawd(pen, x, y, c=10.0, sx=1.0, sy=1.0, eyes="open", step=None):
    """x,y：脚底中心（1× 画面坐标）；c：像素格边长；step：None 站立 / 0、1 迈步相位"""
    s = pen.s
    cw, ch = c * sx * s, c * sy * s
    X0 = x * s - cw * 8
    Y0 = (y - pen.oy) * s - ch * 7
    d = pen.d

    def cell(col, row, colr):
        x0, x1 = round(X0 + col * cw), round(X0 + (col + 1) * cw)
        y0, y1 = round(Y0 + row * ch), round(Y0 + (row + 1) * ch)
        d.rectangle((x0, y0, x1 - 1, y1 - 1), fill=colr)

    for r, row in enumerate(CLAWD_ROWS):
        for col, k in enumerate(row):
            if k == "#":
                cell(col, r, CLAWD)
            elif k == "E":
                dark = eyes == "open" or (eyes == "blink" and r == 2)
                cell(col, r, CLAWD_EYE if dark else CLAWD)
            elif k in "AB":
                lifted = step is not None and ((k == "A") == (step == 0))
                if not (lifted and r == 6):
                    cell(col, r, CLAWD)


ICONS = {
    "!": ["##", "##", "##", "##", "..", "##"],
    "?": [".###.", "#...#", "...#.", "..#..", ".....", "..#.."],
    "heart": [".##.##.", "#######", "#######", ".#####.", "..###..", "...#..."],
}

def draw_pixel_icon(pen, kind, cx, bottom, c=7.0, scale=1.0):
    rows = ICONS[kind]
    c *= scale
    if c < 0.5:
        return
    s = pen.s
    gw, gh = len(rows[0]), len(rows)
    X0 = cx * s - gw * c * s / 2
    Y0 = (bottom - pen.oy) * s - gh * c * s
    filled = {(i, j) for j, r in enumerate(rows) for i, k in enumerate(r) if k == "#"}
    edge = {(i + di, j + dj) for (i, j) in filled for di in (-1, 0, 1) for dj in (-1, 0, 1)} - filled
    col = HEART if kind == "heart" else INK
    for cells, colr in ((edge, WHITE), (filled, col)):
        for (i, j) in cells:
            x0, y0 = round(X0 + i * c * s), round(Y0 + j * c * s)
            x1, y1 = round(X0 + (i + 1) * c * s), round(Y0 + (j + 1) * c * s)
            pen.d.rectangle((x0, y0, x1 - 1, y1 - 1), fill=colr)


# ---------------------------------------------------------------- 道具 / 特效
def draw_tuft(pen, x, y, size=1.0, wob=0.0):
    """草丛（可抖动）"""
    blades = [(-0.66, 0.72), (-0.33, 0.95), (0.0, 1.12), (0.33, 0.95), (0.66, 0.72)]
    for a, L in blades:
        ang = -math.pi / 2 + a + wob * (1 + abs(a))
        length = 64 * L * size
        bx = x + a * 30 * size
        tip = (bx + math.cos(ang) * length, y + math.sin(ang) * length)
        nx, ny = -math.sin(ang), math.cos(ang)
        wd = 11 * size
        mid = ((bx + tip[0]) / 2, (y + tip[1]) / 2)
        left = qbez((bx + nx * wd, y + ny * wd), (mid[0] + nx * wd * 1.3, mid[1] + ny * wd * 1.3), tip, 8)
        right = qbez((bx - nx * wd, y - ny * wd), (mid[0] - nx * wd * 1.3, mid[1] - ny * wd * 1.3), tip, 8)
        pen.poly(left + right[::-1], fill=TUFT, ol=TUFT_D, w=2.4)


def draw_note(pen, x, y, s=1.0, alpha=1.0, rot=0.0):
    """♪ 音符；(x,y) 为音符头"""
    col = INK + (int(230 * alpha),)
    X = Xf(x, y, s, rot=rot)
    pen.poly(X.pts(ell(0, 0, 10, 7, -0.4, 20)), fill=col)
    pen.line(X.pts([(8.5, -2), (8.5, -36)]), col, 3.2 * s, caps=False)
    pen.line(X.pts(qbez((8.5, -36), (22, -30), (19, -15), 6)), col, 3.2 * s)


def draw_burst(pen, cx, cy, u, n=8, r0=28, r1=88, col=WHITE):
    """砰！放射短线；u 0..1"""
    if not 0 <= u < 1:
        return
    a = 1 - u
    d0 = lerp(r0, r1, ease_out(u))
    L = 26 * (1 - u) + 6
    for i in range(n):
        ang = 2 * math.pi * i / n - math.pi / 2 + 0.2
        p0 = (cx + math.cos(ang) * d0, cy + math.sin(ang) * d0)
        p1 = (cx + math.cos(ang) * (d0 + L), cy + math.sin(ang) * (d0 + L))
        pen.line([p0, p1], col + (int(255 * a),), 5 * a + 1.5)


def draw_leaf(pen, x, y, ang, s=1.0):
    pen.poly(ell(x, y, 10 * s, 4.5 * s, ang, 16), fill=TUFT_L, ol=TUFT_D, w=1.8)


# ---------------------------------------------------------------- 文字
_FONT = None
def _font_path():
    c = sorted(glob.glob("/System/Library/AssetsV2/com_apple_MobileAsset_Font*/*/AssetData/Yuanti.ttc"))
    if c:
        return c[0], 2           # 圆体-简 粗体
    return "/System/Library/Fonts/Hiragino Sans GB.ttc", 1

_FC = {}
def font(size):
    global _FONT
    if _FONT is None:
        _FONT = _font_path()
    if size not in _FC:
        _FC[size] = ImageFont.truetype(_FONT[0], size, index=_FONT[1])
    return _FC[size]

_TILES = {}
def text_tile(s, size, fill=INK, stroke=0, stroke_fill=WHITE):
    key = (s, size, fill, stroke, stroke_fill)
    if key not in _TILES:
        f = font(size)
        l, t, r, b = f.getbbox(s, stroke_width=stroke)
        pad = 4 + stroke
        size_ = (r - l + 2 * pad, b - t + 2 * pad)
        mask = Image.new("L", size_, 0)
        ImageDraw.Draw(mask).text((pad - l, pad - t), s, font=f, fill=255)
        im = Image.new("RGBA", size_, (0, 0, 0, 0))
        if stroke:      # 自己做描边：字形外扩再柔化（圆体部分字形的 FreeType 描边会丢失）
            dil = mask.filter(ImageFilter.MaxFilter(2 * int(stroke * 0.8) + 1))
            dil = dil.filter(ImageFilter.GaussianBlur(stroke * 0.3)).point(lambda v: min(255, v * 2))
            im.paste(Image.new("RGBA", size_, stroke_fill + (255,) if len(stroke_fill) == 3 else stroke_fill), (0, 0), dil)
        im.paste(Image.new("RGBA", size_, fill + (255,) if len(fill) == 3 else fill), (0, 0), mask)
        _TILES[key] = im
    return _TILES[key]

def pill_tile(s, size, pad=(34, 18), bg=(255, 253, 246, 236), fg=INK, border=3):
    key = ("pill", s, size, pad, bg, fg, border)
    if key not in _TILES:
        f = font(size)
        l, t, r, b = f.getbbox(s)
        tw, th = r - l, size
        pw, ph = tw + 2 * pad[0], th + 2 * pad[1]
        im = Image.new("RGBA", (pw + 8, ph + 8), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        d.rounded_rectangle((4, 4, 4 + pw, 4 + ph), radius=ph // 2, fill=bg, outline=INK if border else None, width=border)
        d.text((4 + pw / 2, 4 + ph / 2 + size * 0.04), s, font=f, fill=fg, anchor="mm")
        _TILES[key] = im
    return _TILES[key]

def paste(dst, src, x, y):
    """带裁剪的 alpha 合成（允许越界）"""
    x, y = int(round(x)), int(round(y))
    l, t = max(0, -x), max(0, -y)
    r, b = min(src.width, dst.width - x), min(src.height, dst.height - y)
    if r <= l or b <= t:
        return
    if (l, t, r, b) != (0, 0, src.width, src.height):
        src = src.crop((l, t, r, b))
    dst.alpha_composite(src, (x + l, y + t))

def stamp(dst, tile, cx, cy, scale=1.0, alpha=1.0, rot=0.0):
    if scale <= 0.02 or alpha <= 0.01:
        return
    t = tile
    if abs(scale - 1) > 0.01:
        t = t.resize((max(1, int(t.width * scale)), max(1, int(t.height * scale))), Image.BICUBIC)
    if abs(rot) > 0.002:
        t = t.rotate(-math.degrees(rot), resample=Image.BICUBIC, expand=True)
    if alpha < 0.999:
        t = t.copy()
        t.putalpha(t.getchannel("A").point(lambda v: int(v * alpha)))
    paste(dst, t, cx - t.width / 2, cy - t.height / 2)


# ---------------------------------------------------------------- 背景：草地
class Meadow:
    """分层预渲染的草地；cam 为画面中心对应的世界 x"""
    def __init__(self, cam_min, cam_max, seed=3):
        self.cmin, self.cmax = cam_min, cam_max
        rnd = random.Random(seed)
        self.sky = self._sky()
        self.clouds = self._clouds(rnd)
        self.back = [self._hills(rnd), self._trees(rnd), self._far(rnd), self._near(rnd)]
        self.front = [self._fg(rnd)]

    def _strip(self, p, y0, y1):
        w = int(W + p * (self.cmax - self.cmin) + 120)
        L0 = p * self.cmin - W / 2 - 60
        return Image.new("RGBA", (w, y1 - y0), (0, 0, 0, 0)), L0

    def _sky(self):
        keys = [(0, (140, 190, 228)), (520, (184, 214, 236)), (760, (214, 232, 240)), (900, (228, 240, 238))]
        col = Image.new("RGB", (1, H))
        for y in range(H):
            for (y0, c0), (y1, c1) in zip(keys, keys[1:]):
                if y0 <= y <= y1 or y > keys[-1][0]:
                    k = ramp(y, y0, y1)
                    col.putpixel((0, y), tuple(int(lerp(c0[i], c1[i], k)) for i in range(3)))
                    break
        return col.resize((W, H)).convert("RGBA")

    def _clouds(self, rnd):
        out = []
        for (x, y, s, v) in ((-60, 330, 1.0, 7), (700, 190, 1.25, 5), (430, 600, 0.75, 9), (1180, 470, 0.9, 6)):
            w, h = int(520 * s), int(220 * s)
            im = Image.new("RGBA", (w, h), (252, 253, 255, 0))
            d = ImageDraw.Draw(im)
            for (cx, cy, r) in ((0.3, 0.6, 0.22), (0.5, 0.45, 0.28), (0.7, 0.6, 0.2), (0.45, 0.68, 0.2), (0.62, 0.66, 0.2)):
                R = r * w * 0.62
                d.ellipse((cx * w - R, cy * h - R * 0.8, cx * w + R, cy * h + R * 0.8), fill=(252, 253, 255, 235))
            out.append((im.filter(ImageFilter.GaussianBlur(10 * s)), x, y, v))
        return out

    def _hills(self, rnd):
        p, y0, y1 = 0.12, 600, 900
        im, L0 = self._strip(p, y0, y1)
        d = ImageDraw.Draw(im)
        for col, base, a1, a2, f1, f2 in (((186, 214, 206), 712, 28, 12, 380, 150), ((168, 206, 186), 752, 20, 10, 280, 110)):
            pts = [(u, base + a1 * math.sin((u + L0) / f1) + a2 * math.sin((u + L0) / f2 + 2) - y0)
                   for u in range(0, im.width + 20, 20)]
            d.polygon(pts + [(im.width, y1 - y0), (0, y1 - y0)], fill=col)
        return im.filter(ImageFilter.GaussianBlur(2.5)), p, y0, L0

    def _trees(self, rnd):
        p, y0, y1 = 0.3, 640, 920
        im, L0 = self._strip(p, y0, y1)
        d = ImageDraw.Draw(im)
        u = -40
        while u < im.width + 60:      # 后排：更浅更蓝
            r = rnd.uniform(40, 56)
            cy = 812 - y0 + rnd.uniform(-6, 6)
            d.ellipse((u - r, cy - r, u + r, cy + r), fill=(134, 186, 136))
            d.rectangle((u - r, cy, u + r, y1 - y0), fill=(134, 186, 136))
            u += rnd.uniform(52, 76)
        u = -60
        while u < im.width + 80:      # 前排
            r = rnd.uniform(54, 76)
            cy = 832 - y0 + rnd.uniform(-10, 8)
            d.ellipse((u - r, cy - r, u + r, cy + r), fill=(100, 168, 98))
            d.rectangle((u - r * 0.9, cy, u + r * 0.9, y1 - y0), fill=(100, 168, 98))
            hr = r * 0.6
            hx, hy = u - r * 0.16, cy - r * 0.2
            d.ellipse((hx - hr, hy - hr, hx + hr, hy + hr), fill=(128, 190, 114))
            u += rnd.uniform(78, 120)
        return im.filter(ImageFilter.GaussianBlur(2.2)), p, y0, L0

    def _grass(self, im, base, rnd, blotches, stripes, blur):
        w, h = im.size
        g = Image.new("RGB", (w, h), base)
        d = ImageDraw.Draw(g, "RGBA")
        for (yy, hh, dv) in stripes:
            c = tuple(clamp(base[i] + dv, 0, 255) for i in range(3))
            d.rectangle((0, yy, w, yy + hh), fill=tuple(int(v) for v in c) + (255,))
        for _ in range(int(w * h / blotches)):
            x, y = rnd.uniform(0, w), rnd.uniform(0, h)
            rx, ry = rnd.uniform(40, 140), rnd.uniform(14, 46)
            dv = rnd.choice((-9, -6, 6, 9))
            c = tuple(int(clamp(base[i] + dv, 0, 255)) for i in range(3))
            d.ellipse((x - rx, y - ry, x + rx, y + ry), fill=c + (140,))
        return g.filter(ImageFilter.GaussianBlur(blur))

    def _flowers(self, d, w, y_lo, y_hi, n, rmin, rmax, rnd, avoid=None):
        cols = [(252, 252, 246), (252, 252, 246), (248, 196, 212), (252, 234, 150)]
        for _ in range(n):
            x, y = rnd.uniform(0, w), rnd.uniform(y_lo, y_hi)
            if avoid and avoid[0] < y < avoid[1]:
                continue
            r = rnd.uniform(rmin, rmax)
            d.ellipse((x - r, y - r, x + r, y + r), fill=rnd.choice(cols))

    def _feather(self, im, top):
        a = Image.new("L", im.size, 255)
        ad = ImageDraw.Draw(a)
        for y in range(top):
            ad.line((0, y, im.width, y), fill=int(255 * ease_io(y / top)))
        im.putalpha(a)
        return im

    def _far(self, rnd):
        p, y0, y1 = 0.62, 836, 1240
        im, L0 = self._strip(p, y0, y1)
        h = y1 - y0
        g = self._grass(im, (172, 216, 140), rnd, 5000, [(150, 90, 5), (300, 110, -4)], 16)
        # 远处弯弯的小路
        path = Image.new("L", g.size, 0)
        pd = ImageDraw.Draw(path)
        pts_t, pts_b = [], []
        for u in range(0, g.width + 30, 30):
            c = 175 + 46 * math.sin((u + L0) / 520) + 14 * math.sin((u + L0) / 170 + 1)
            wd = 28 + 6 * math.sin((u + L0) / 300)
            pts_t.append((u, c - wd))
            pts_b.append((u, c + wd))
        pd.polygon(pts_t + pts_b[::-1], fill=255)
        path = path.filter(ImageFilter.GaussianBlur(3))
        pc = Image.new("RGB", g.size, (228, 210, 170))
        pdd = ImageDraw.Draw(pc)
        for _ in range(int(g.width * 1.4)):
            x, y = rnd.uniform(0, g.width), rnd.uniform(0, h)
            r = rnd.uniform(1.5, 3.5)
            pdd.ellipse((x - r, y - r * 0.6, x + r, y + r * 0.6), fill=(208, 186, 144))
        g = Image.composite(pc.filter(ImageFilter.GaussianBlur(1)), g, path)
        d = ImageDraw.Draw(g)
        self._flowers(d, g.width, 30, h, int(g.width * h / 9000), 1.6, 2.6, rnd)
        g = g.filter(ImageFilter.GaussianBlur(1.3))
        return self._feather(g.convert("RGBA"), 26), p, y0, L0

    def _near(self, rnd):
        p, y0, y1 = 1.0, 1150, H
        im, L0 = self._strip(p, y0, y1)
        h = y1 - y0
        stripes = [(110, 130, 6), (330, 150, -5), (560, 160, 6)]
        g = self._grass(im, (158, 208, 124), rnd, 6000, stripes, 22)
        d = ImageDraw.Draw(g)
        self._flowers(d, g.width, 40, h, int(g.width * h / 8000), 2.4, 4.2, rnd, avoid=(150, 210))
        g = g.filter(ImageFilter.GaussianBlur(0.7)).convert("RGBA")
        # 清晰的小草丛（避开角色站立的地面线附近）
        pen = Pen(g, oy=0, s=1)
        for _ in range(int(g.width / 70)):
            x = rnd.uniform(0, g.width)
            y = rnd.uniform(270, 700)
            draw_tuft(pen, x, y, rnd.uniform(0.38, 0.6))
        return self._feather(g, 50), p, y0, L0

    def _fg(self, rnd):
        p, y0, y1 = 1.3, 1680, H
        im, L0 = self._strip(p, y0, y1)
        pen = Pen(im, oy=0, s=1)
        u = rnd.uniform(0, 200)
        while u < im.width:
            draw_tuft(pen, u, rnd.uniform(220, 270), rnd.uniform(1.2, 1.7))
            u += rnd.uniform(220, 420)
        return im.filter(ImageFilter.GaussianBlur(5)), p, y0, L0

    def _crop(self, layer, cam):
        im, p, y0, L0 = layer
        u0 = int(round(p * cam - W / 2 - L0))
        return im.crop((u0, 0, u0 + W, im.height)), y0

    def compose(self, cam, t):
        fr = self.sky.copy()
        for im, x, y, v in self.clouds:
            paste(fr, im, x - 0.05 * cam - v * t, y - im.height / 2)
        for layer in self.back:
            c, y0 = self._crop(layer, cam)
            fr.alpha_composite(c, (0, y0))
        return fr

    def foreground(self, fr, cam):
        for layer in self.front:
            c, y0 = self._crop(layer, cam)
            fr.alpha_composite(c, (0, y0))


# ---------------------------------------------------------------- 后期：纸面颗粒
_GRAIN = None
def grain(img, t, amount=0.13):
    global _GRAIN
    if _GRAIN is None:
        _GRAIN = [Image.effect_noise((W, H), 38).convert("RGB") for _ in range(4)]
    g = _GRAIN[int(t * 8) % len(_GRAIN)]
    return Image.blend(img, ImageChops.overlay(img, g), amount)


class Layer:
    """2× 角色层，只覆盖画面的一条横带以省时"""
    def __init__(self, y0, y1):
        self.y0, self.y1 = y0, y1
        self.img = Image.new("RGBA", (W * SS, (y1 - y0) * SS), (0, 0, 0, 0))
        self.pen = Pen(self.img, oy=y0)

    def onto(self, fr):
        bb = self.img.getbbox()
        if not bb:
            return
        l, t, r, b = (bb[0] // 2 * 2, bb[1] // 2 * 2, min(self.img.width, (bb[2] + 1) // 2 * 2),
                      min(self.img.height, (bb[3] + 1) // 2 * 2))
        part = self.img.crop((l, t, r, b)).resize(((r - l) // SS, (b - t) // SS), Image.LANCZOS)
        fr.alpha_composite(part, (l // SS, self.y0 + t // SS))


# ---------------------------------------------------------------- 音频合成
_ACACHE = {}
def _cached(key, fn):
    if key not in _ACACHE:
        _ACACHE[key] = fn()
    return _ACACHE[key]

def note_freq(n):
    names = {"C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3, "E": 4, "F": 5, "F#": 6, "Gb": 6,
             "G": 7, "G#": 8, "Ab": 8, "A": 9, "A#": 10, "Bb": 10, "B": 11}
    name, octv = n[:-1], int(n[-1])
    return 440.0 * 2 ** ((12 * (octv + 1) + names[name] - 69) / 12)

def _edge(i, n, a=0.003, r=0.008):
    return min(1.0, i / (a * SR + 1), (n - i) / (r * SR + 1))

def marimba(f, dur=0.9):
    def mk():
        n = int(dur * SR)
        w1, w4 = 2 * math.pi * f / SR, 2 * math.pi * f * 3.93 / SR
        return [(math.sin(w1 * i) * math.exp(-i / SR * 5.5) + 0.22 * math.sin(w4 * i) * math.exp(-i / SR * 22))
                * _edge(i, n, 0.002) for i in range(n)]
    return _cached(("mar", round(f, 2), dur), mk)

def celesta(f, dur=1.4):
    def mk():
        n = int(dur * SR)
        w = 2 * math.pi * f / SR
        return [(math.sin(w * i) * math.exp(-i / SR * 3.2) + 0.3 * math.sin(2 * w * i) * math.exp(-i / SR * 6.5)
                 + 0.1 * math.sin(5.4 * w * i) * math.exp(-i / SR * 14)) * _edge(i, n, 0.0015) for i in range(n)]
    return _cached(("cel", round(f, 2), dur), mk)

def bass(f, dur=0.5):
    def mk():
        n = int(dur * SR)
        w = 2 * math.pi * f / SR
        return [(math.sin(w * i) + 0.3 * math.sin(2 * w * i)) * math.exp(-i / SR * 4.5) * _edge(i, n, 0.005, 0.03)
                for i in range(n)]
    return _cached(("bas", round(f, 2), dur), mk)

def sweep(f0, f1, dur, decay=8.0, square=False, harm=0.0):
    """音高滑动；square=True 时为像素风方波（奇次谐波叠加）"""
    def mk():
        n = int(dur * SR)
        ph, out = 0.0, []
        for i in range(n):
            u = i / n
            ph += 2 * math.pi * f0 * (f1 / f0) ** u / SR
            if square:
                v = 0.62 * (math.sin(ph) + math.sin(3 * ph) / 3 + math.sin(5 * ph) / 5 + math.sin(7 * ph) / 7)
            else:
                v = math.sin(ph) + harm * math.sin(2 * ph)
            out.append(v * math.exp(-decay * i / SR) * _edge(i, n))
        return out
    return _cached(("swp", f0, f1, dur, decay, square, harm), mk)

def chirp(f, dur=0.09, up=1.38, end=1.12):
    """啾啾的叫声音节"""
    def mk():
        n = int(dur * SR)
        ph, out = 0.0, []
        for i in range(n):
            u = i / n
            k = lerp(1, up, u / 0.4) if u < 0.4 else lerp(up, end, (u - 0.4) / 0.6)
            ph += 2 * math.pi * f * k / SR
            out.append((math.sin(ph) + 0.2 * math.sin(2 * ph)) * (1 - u) ** 0.5 * _edge(i, n, 0.005, 0.01))
        return out
    return _cached(("chp", round(f, 1), dur, up, end), mk)

def noise(dur, lp=0.25, hp=0.02, seed=1, grains=0, attack=0.01):
    """带通噪声；grains>0 时做成沙沙的颗粒"""
    rnd = random.Random(seed)
    n = int(dur * SR)
    a = b = 0.0
    out = []
    gamp, gnext = 1.0, 0
    for i in range(n):
        x = rnd.uniform(-1, 1)
        a += lp * (x - a)
        b += hp * (a - b)
        v = a - b
        if grains:
            if i >= gnext:
                gamp = rnd.uniform(0.15, 1.0)
                gnext = i + int(SR / grains * rnd.uniform(0.5, 1.5))
            v *= gamp
        out.append(v * _edge(i, n, attack, 0.03))
    return out

def boing(f=200, dur=0.8):
    def mk():
        n = int(dur * SR)
        ph, out = 0.0, []
        for i in range(n):
            tt = i / SR
            ph += 2 * math.pi * f * (1 + 0.32 * math.sin(2 * math.pi * 11 * tt) * math.exp(-tt * 2.5)) / SR
            out.append((math.sin(ph) + 0.25 * math.sin(2 * ph)) * math.exp(-tt * 3.4) * _edge(i, n))
        return out
    return _cached(("boing", f, dur), mk)


class Mix:
    def __init__(self, dur):
        self.N = int(dur * SR) + 1
        self.L = array.array("f", bytes(4 * self.N))
        self.R = array.array("f", bytes(4 * self.N))

    def add(self, t0, s, gain=1.0, pan=0.0, cut=None):
        """cut：在该时刻硬切（带 15ms 淡出）"""
        i0 = int(t0 * SR)
        gl, gr = gain * math.sqrt(0.5 * (1 - pan)), gain * math.sqrt(0.5 * (1 + pan))
        n = min(len(s), self.N - i0)
        if cut is not None:
            n = min(n, int((cut - t0) * SR))
        fade = int(0.015 * SR)
        L, R = self.L, self.R
        for j in range(max(0, -i0), max(0, n)):
            v = s[j]
            if cut is not None and j > n - fade:
                v *= (n - j) / fade
            L[i0 + j] += v * gl
            R[i0 + j] += v * gr

    def reverb(self, wet=0.16):
        out = []
        for ch, delays in ((self.L, (1557, 1617, 1491)), (self.R, (1422, 1277, 1356))):
            acc = array.array("f", bytes(4 * self.N))
            for dl in delays:
                buf = array.array("f", bytes(4 * self.N))
                for i in range(self.N):
                    v = ch[i] + (0.74 * buf[i - dl] if i >= dl else 0.0)
                    buf[i] = v
                for i in range(self.N):
                    acc[i] += buf[i]
            out.append(acc)
        for ch, acc in zip((self.L, self.R), out):
            for i in range(self.N):
                ch[i] += acc[i] * wet / 3

    def write(self, path, fade_out=0.6):
        peak = max(max(abs(v) for v in self.L), max(abs(v) for v in self.R)) or 1.0
        g = 0.89 / peak
        fn = int(fade_out * SR)
        frames = array.array("h", [0]) * (2 * self.N)
        for i in range(self.N):
            f = min(1.0, (self.N - i) / fn) if fn else 1.0
            frames[2 * i] = int(clamp(self.L[i] * g * f, -1, 1) * 32767)
            frames[2 * i + 1] = int(clamp(self.R[i] * g * f, -1, 1) * 32767)
        with wave.open(path, "wb") as wf:
            wf.setnchannels(2)
            wf.setsampwidth(2)
            wf.setframerate(SR)
            wf.writeframes(frames.tobytes())


# ---------------------------------------------------------------- 输出
def encode(render_bytes, nframes, wav, out):
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", wav,
           "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-tune", "grain", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    with Pool(max(1, os.cpu_count() - 1)) as pool:
        for i, b in enumerate(pool.imap(render_bytes, range(nframes), chunksize=4)):
            proc.stdin.write(b)
            if i % 96 == 0:
                print(f"frame {i}/{nframes}", flush=True)
    proc.stdin.close()
    proc.wait()
