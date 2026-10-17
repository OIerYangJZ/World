# -*- coding: utf-8 -*-
"""
《鹈鹕骑单车》—— 复古中世纪海报风动画（约 32 秒，30 fps）
扁平色块 + 胶片颗粒；海滨步道从午后骑到入夜，多层视差滚动。
鹈鹕的双腿用两段式 IK 跟随踏板，车轮/曲柄按行驶距离转动，滑行时曲柄停转（飞轮）。
画面以 2× 超采样绘制后缩小抗锯齿；配乐（口哨 + 尤克里里 + 音效）用纯 Python 合成。

运行：
  python3 make_pelican.py                → music.wav + 鹈鹕骑单车.mp4
  python3 make_pelican.py still 5 10.2   → previews/ 下导出指定秒数的静帧
"""
import math, random, os, sys, subprocess, wave, array
from multiprocessing import Pool
from PIL import Image, ImageDraw, ImageFont, ImageChops, ImageFilter

W, H = 1280, 720
SS = 2
FPS = 30
DUR = 32.0
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "鹈鹕骑单车.mp4")

# ---------------------------------------------------------------- 调色板
NAVY = (34, 46, 72)
NAVY_L = (58, 74, 104)
CREAM = (247, 238, 218)
CREAM_D = (226, 212, 186)
CORAL = (226, 86, 68)
CORAL_D = (178, 58, 50)
MUSTARD = (238, 178, 62)
TEAL = (40, 112, 118)
TEAL_D = (28, 84, 92)
SEA = (54, 136, 146)
SEA_D = (38, 108, 122)
SEA_L = (120, 190, 190)
WHITE = (252, 250, 245)
FEATHER = (214, 220, 228)
FEATHER_D = (176, 186, 200)
PRIMARY = (44, 46, 58)
BEAK = (242, 150, 48)
BEAK_D = (214, 108, 40)
BEAK_TIP = (208, 70, 52)
POUCH = (250, 196, 96)
POUCH_D = (232, 160, 70)
LEG = (240, 128, 56)
LEG_D = (196, 96, 44)
ROAD = (212, 188, 156)
ROAD_D = (190, 164, 132)
ROAD_L = (228, 208, 178)
BUSH = (46, 96, 82)
BUSH_D = (32, 72, 64)
BUSH_L = (74, 128, 100)
SILVER = (172, 196, 214)
GREY = (150, 156, 168)


# ---------------------------------------------------------------- 小工具
def clamp(v, a=0.0, b=1.0):
    return max(a, min(b, v))

def lerp(a, b, k):
    return a + (b - a) * k

def mix(a, b, k):
    return tuple(int(round(lerp(a[i], b[i], k))) for i in range(3))

def ease_io(p):
    p = clamp(p)
    return p * p * (3 - 2 * p)

def ease_out(p):
    p = clamp(p)
    return 1 - (1 - p) ** 3

def ease_in(p):
    p = clamp(p)
    return p ** 3

def ramp(t, a, b):
    """t 在 [a,b] 内从 0 平滑到 1"""
    return ease_io((t - a) / (b - a)) if b > a else float(t >= a)

def window(t, a, b, c, d):
    """a→b 淡入，c→d 淡出"""
    return ramp(t, a, b) * (1 - ramp(t, c, d))

def rot(p, ang, c=(0, 0)):
    s, co = math.sin(ang), math.cos(ang)
    x, y = p[0] - c[0], p[1] - c[1]
    return (c[0] + x * co - y * s, c[1] + x * s + y * co)

def bezier(p0, p1, p2, p3, n=16):
    pts = []
    for i in range(n + 1):
        u = i / n
        a = (1 - u) ** 3; b = 3 * u * (1 - u) ** 2; c = 3 * u * u * (1 - u); d = u ** 3
        pts.append((a * p0[0] + b * p1[0] + c * p2[0] + d * p3[0],
                    a * p0[1] + b * p1[1] + c * p2[1] + d * p3[1]))
    return pts

def qbez(p0, p1, p2, n=14):
    pts = []
    for i in range(n + 1):
        u = i / n
        pts.append(((1 - u) ** 2 * p0[0] + 2 * u * (1 - u) * p1[0] + u * u * p2[0],
                    (1 - u) ** 2 * p0[1] + 2 * u * (1 - u) * p1[1] + u * u * p2[1]))
    return pts

def catmull(pts, n=8, closed=True):
    """过控制点的平滑曲线"""
    out = []
    m = len(pts)
    rng = range(m) if closed else range(m - 1)
    for i in rng:
        p0 = pts[(i - 1) % m] if closed else pts[max(i - 1, 0)]
        p1 = pts[i]
        p2 = pts[(i + 1) % m] if closed else pts[i + 1]
        p3 = pts[(i + 2) % m] if closed else pts[min(i + 2, m - 1)]
        for j in range(n):
            u = j / n
            u2, u3 = u * u, u * u * u
            out.append(tuple(0.5 * (2 * p1[k] + (-p0[k] + p2[k]) * u + (2 * p0[k] - 5 * p1[k] + 4 * p2[k] - p3[k]) * u2
                                    + (-p0[k] + 3 * p1[k] - 3 * p2[k] + p3[k]) * u3) for k in range(2)))
    if not closed:
        out.append(pts[-1])
    return out

def ellipse_pts(cx, cy, rx, ry, ang=0.0, n=40, a0=0.0, a1=2 * math.pi):
    pts = []
    for i in range(n + 1):
        a = a0 + (a1 - a0) * i / n
        x, y = rx * math.cos(a), ry * math.sin(a)
        pts.append((cx + x * math.cos(ang) - y * math.sin(ang),
                    cy + x * math.sin(ang) + y * math.cos(ang)))
    return pts

def hsh(i, salt=0):
    """确定性伪随机 [0,1)"""
    x = math.sin(i * 127.1 + salt * 311.7) * 43758.5453
    return x - math.floor(x)

def font(path, size, index=0):
    return ImageFont.truetype(path, size, index=index)

SONG = "/System/Library/Fonts/Supplemental/Songti.ttc"
SYMB = "/System/Library/Fonts/Apple Symbols.ttf"
FUTURA = "/System/Library/Fonts/Supplemental/Futura.ttc"


# ---------------------------------------------------------------- 调色（按时刻整体偏色）
GRADE = [(1.0, 1.0, 1.0), (0, 0, 0)]

def graded(c):
    m, a = GRADE
    return tuple(int(clamp(c[i] * m[i] + a[i], 0, 255)) for i in range(3))

# 一天的时间轴：午后 → 黄金时刻 → 日落 → 黄昏 → 入夜
TOD_KEYS = [
    # t,   天顶,             地平线,           画面乘色,            加色
    (0.0,  (112, 184, 190), (250, 224, 172), (1.00, 1.00, 1.00), (0, 0, 0)),
    (9.0,  (104, 168, 184), (252, 206, 150), (1.00, 0.95, 0.86), (6, 2, 0)),
    (16.0, (84, 118, 160),  (250, 158, 96),  (1.00, 0.82, 0.70), (10, 2, 0)),
    (21.0, (60, 70, 128),   (236, 116, 96),  (0.82, 0.64, 0.66), (4, 0, 10)),
    (25.0, (34, 38, 82),    (150, 84, 112),  (0.56, 0.52, 0.70), (0, 2, 14)),
    (29.0, (16, 22, 52),    (58, 56, 102),   (0.40, 0.42, 0.62), (0, 4, 18)),
]

def tod(t):
    for i in range(len(TOD_KEYS) - 1):
        a, b = TOD_KEYS[i], TOD_KEYS[i + 1]
        if t <= b[0]:
            k = ease_io((t - a[0]) / (b[0] - a[0]))
            return [tuple(lerp(a[j][c], b[j][c], k) for c in range(3)) for j in range(1, 5)]
    return [tuple(float(v) for v in x) for x in TOD_KEYS[-1][1:]]

def night(t):
    return ramp(t, 20.5, 27.0)


# ---------------------------------------------------------------- 运动：速度 → 行驶距离
def speed(t):
    """世界滚动速度（像素/秒，路面层）"""
    v = 190.0
    v += 190.0 * window(t, 12.8, 14.2, 18.0, 19.5)     # 下坡滑行
    v -= 70.0 * ramp(t, 26.5, 30.0)                  # 收尾放慢
    return v

DT = 1.0 / 240
_DIST = [0.0]
for _i in range(int((DUR + 2) / DT) + 2):
    _DIST.append(_DIST[-1] + speed(_i * DT) * DT)

def dist(t):
    f = clamp(t, 0, DUR + 1.9) / DT
    i = int(f)
    return lerp(_DIST[i], _DIST[i + 1], f - i)

def coast(t):
    """双脚离开踏板的程度"""
    return window(t, 13.6, 14.4, 17.6, 18.5)

# 曲柄角 = 行驶距离积分，但滑行时停转
_CRANK = [0.0]
for _i in range(int((DUR + 2) / DT) + 2):
    tt = _i * DT
    _CRANK.append(_CRANK[-1] + speed(tt) * DT / 34.0 * (1 - coast(tt)))

def crank_angle(t):
    f = clamp(t, 0, DUR + 1.9) / DT
    i = int(f)
    return lerp(_CRANK[i], _CRANK[i + 1], f - i)

def bike_x(t):
    """后轮轴在屏幕上的 x"""
    x = lerp(-420, 400, ease_out((t - 0.2) / 3.6))
    x += 18 * math.sin(t * 0.6) * ramp(t, 4, 6)       # 轻微前后浮动
    x += 60 * window(t, 13.0, 15.0, 17.5, 19.5)      # 冲刺时往前窜一点
    x += 1300 * ease_in((t - 26.8) / 4.2)            # 骑出画面
    return x

GROUND = 626        # 车轮着地线
K = 1.22            # 角色整体缩放
WHEEL_R = 62


# ---------------------------------------------------------------- 画笔（2× 超采样，自动调色）
class Pen:
    def __init__(self, img):
        self.img = img
        self.d = ImageDraw.Draw(img, "RGBA")

    def _c(self, c, raw):
        if len(c) == 4:
            g = c[:3] if raw else graded(c[:3])
            return g + (int(c[3]),)
        return c if raw else graded(c)

    def poly(self, pts, c, raw=False):
        if len(pts) >= 3:
            self.d.polygon([(x * SS, y * SS) for x, y in pts], fill=self._c(c, raw))

    def circle(self, cx, cy, r, c, raw=False):
        r *= SS
        self.d.ellipse((cx * SS - r, cy * SS - r, cx * SS + r, cy * SS + r), fill=self._c(c, raw))

    def ellipse(self, cx, cy, rx, ry, c, raw=False):
        self.d.ellipse(((cx - rx) * SS, (cy - ry) * SS, (cx + rx) * SS, (cy + ry) * SS), fill=self._c(c, raw))

    def pill(self, x0, y0, x1, y1, c, raw=False):
        r = (y1 - y0) / 2 * SS
        self.d.rounded_rectangle((x0 * SS, y0 * SS, x1 * SS, y1 * SS), radius=r, fill=self._c(c, raw))

    def rect(self, x0, y0, x1, y1, c, raw=False):
        self.d.rectangle((x0 * SS, y0 * SS, x1 * SS - 1, y1 * SS - 1), fill=self._c(c, raw))

    def line(self, pts, c, w, raw=False, caps=True):
        col = self._c(c, raw)
        sp = [(x * SS, y * SS) for x, y in pts]
        self.d.line(sp, fill=col, width=max(1, int(round(w * SS))), joint="curve")
        if caps and len(col) == 3:
            r = w * SS / 2
            for (x, y) in (sp[0], sp[-1]):
                self.d.ellipse((x - r, y - r, x + r, y + r), fill=col)

    def ring(self, cx, cy, r, w, c, raw=False):
        r *= SS
        self.d.ellipse((cx * SS - r, cy * SS - r, cx * SS + r, cy * SS + r),
                       outline=self._c(c, raw), width=max(1, int(round(w * SS))))

    def tube(self, pts, widths, c, raw=False):
        """粗细可变的圆滑管子：沿路径叠圆"""
        col = self._c(c, raw)
        for i in range(len(pts) - 1):
            (x0, y0), (x1, y1) = pts[i], pts[i + 1]
            w0, w1 = widths[i], widths[i + 1]
            n = max(1, int(math.hypot(x1 - x0, y1 - y0) / 1.5))
            for j in range(n + 1):
                u = j / n
                x, y, r = lerp(x0, x1, u), lerp(y0, y1, u), lerp(w0, w1, u) / 2
                self.d.ellipse(((x - r) * SS, (y - r) * SS, (x + r) * SS, (y + r) * SS), fill=col)

    def text(self, xy, s, f, c, anchor="la", raw=True):
        self.d.text((xy[0] * SS, xy[1] * SS), s, font=f, fill=self._c(c, raw), anchor=anchor)


# ---------------------------------------------------------------- 天空 / 太阳 / 星星 / 月亮
STARS = [(hsh(i, 1) * W, hsh(i, 2) * 360, 0.6 + 1.4 * hsh(i, 3), hsh(i, 4) * 6.28) for i in range(110)]

def sun_pos(t):
    y = lerp(150, 420, ease_io((t - 1.0) / 23.0))
    return 930.0 - 0.02 * dist(t), y

def draw_sky(pen, t):
    top, hor, _, _ = tod(t)
    d = pen.d
    band = 12   # 复古海报感：分段色带而非平滑渐变
    for y in range(0, 400, band):
        k = (y / 400) ** 1.3
        c = mix(top, hor, k)
        d.rectangle((0, y * SS, W * SS, (y + band) * SS), fill=c)
    # 星星
    nk = night(t)
    if nk > 0:
        for (x, y, s, ph) in STARS:
            tw = 0.6 + 0.4 * math.sin(t * 3.0 + ph * 3)
            a = int(255 * nk * tw * clamp((380 - y) / 120))
            if a > 8:
                pen.circle(x, y, s, (255, 248, 220, a), raw=True)
    # 太阳：条纹切割的复古落日
    sx, sy = sun_pos(t)
    sun_c = mix((252, 214, 110), (248, 110, 72), ramp(t, 8, 23))
    glow = int(70 * (1 - night(t)))
    for i, rr in enumerate((150, 120, 96)):
        pen.circle(sx, sy, rr, sun_c + (int(glow * (0.25 + 0.25 * i)),), raw=True)
    pen.circle(sx, sy, 78, sun_c, raw=True)
    for i in range(5):
        yy = sy + 12 + i * 14
        hgt = 2 + i * 1.8
        if yy < sy + 78:
            pen.rect(sx - 90, yy, sx + 90, yy + hgt, mix(top, hor, ((yy) / 400) ** 1.3), raw=True)
    # 月亮
    mk = ramp(t, 23.5, 28.5)
    if mk > 0:
        mx, my = 250 + 30 * mk, lerp(300, 120, mk)
        pen.circle(mx, my, 60, (255, 240, 200, int(40 * mk)), raw=True)
        pen.circle(mx, my, 34, (250, 240, 214, int(255 * mk)), raw=True)
        pen.circle(mx + 14, my - 8, 30, mix(top, hor, (my / 400) ** 1.3) + (int(255 * mk),), raw=True)


CLOUDS = [(hsh(i, 11) * 1800, 60 + hsh(i, 12) * 170, 60 + hsh(i, 13) * 80) for i in range(7)]

def draw_clouds(pen, t):
    top, hor, _, _ = tod(t)
    base = mix(CREAM, hor, 0.35)
    base = mix(base, (70, 70, 120), night(t) * 0.8)
    shade = mix(base, top, 0.35)
    off = 0.05 * dist(t) + 6 * t
    for (x0, y, w) in CLOUDS:
        x = (x0 - off) % 1900 - 300
        h = w * 0.34
        # 扁平"药丸"云
        pen.pill(x - w * 0.95, y + h * 0.05, x + w * 1.0, y + h * 0.75, shade, raw=True)
        pen.ellipse(x - w * 0.3, y, w * 0.42, h * 0.62, base, raw=True)
        pen.ellipse(x + w * 0.22, y - h * 0.22, w * 0.42, h * 0.78, base, raw=True)
        pen.pill(x - w * 0.85, y - h * 0.05, x + w * 0.9, y + h * 0.58, base, raw=True)


# ---------------------------------------------------------------- 远山 / 海 / 灯塔 / 帆船
def ridge(xw, seed, amp):
    return amp * (0.55 * math.sin(xw * 0.004 + seed) + 0.3 * math.sin(xw * 0.011 + seed * 2.3)
                  + 0.15 * math.sin(xw * 0.027 + seed * 4.1))

HORIZON = 398

def lighthouse_x(t):
    return 1500 - 0.09 * (dist(t) - dist(17.0)) - 420

def draw_far(pen, t):
    top, hor, _, _ = tod(t)
    far = mix(mix(hor, top, 0.45), (120, 110, 150), 0.35)
    near = mix(far, TEAL_D, 0.45)
    X = dist(t)
    # 远岛
    pts = [(0, HORIZON)]
    for x in range(0, W + 16, 16):
        h = ridge(x + 0.03 * X, 1.7, 26) + 12
        pts.append((x, HORIZON - max(0, h)))
    pts.append((W, HORIZON))
    pen.poly(pts, far, raw=True)
    # 岬角（带灯塔）
    lx = lighthouse_x(t)
    cape = [(lx - 360, HORIZON), (lx - 220, HORIZON - 18), (lx - 90, HORIZON - 40), (lx - 20, HORIZON - 52),
            (lx + 40, HORIZON - 54), (lx + 110, HORIZON - 34), (lx + 200, HORIZON - 10), (lx + 300, HORIZON)]
    pen.poly(cape, graded(near), raw=True)
    # 灯塔
    bx, by = lx + 10, HORIZON - 52
    tower = [(bx - 9, by), (bx + 9, by), (bx + 6, by - 46), (bx - 6, by - 46)]
    pen.poly(tower, CREAM)
    for i in range(3):
        y0 = by - 8 - i * 14
        pen.poly([(bx - 8.5 + i * 0.9, y0), (bx + 8.5 - i * 0.9, y0),
                  (bx + 8.1 - i * 0.9, y0 - 6), (bx - 8.1 + i * 0.9, y0 - 6)], CORAL)
    pen.rect(bx - 8, by - 56, bx + 8, by - 46, NAVY)
    pen.poly([(bx - 9, by - 56), (bx + 9, by - 56), (bx, by - 64)], CORAL_D)
    nk = night(t)
    lamp = mix(graded(CREAM), (255, 236, 150), nk)
    pen.rect(bx - 5, by - 55, bx + 5, by - 47, lamp, raw=True)
    if nk > 0.02:
        ang = t * 1.6
        reach = 520 * math.cos(ang)
        spread = 26 + 10 * abs(math.sin(ang))
        a = int(90 * nk * (0.35 + 0.65 * abs(math.cos(ang))))
        pen.poly([(bx, by - 51), (bx + reach, by - 51 - spread), (bx + reach, by - 51 + spread)],
                 (255, 236, 170, a), raw=True)
        pen.circle(bx, by - 51, 14, (255, 236, 170, int(120 * nk)), raw=True)


BOATS = [(300, 452, 1.0), (1150, 430, 0.7), (1900, 466, 1.2)]

def draw_sea(pen, t):
    top, hor, mult, add = tod(t)
    sea_top = mix(mix(SEA_L, hor, 0.45), top, 0.15)
    sea_bot = mix(SEA_D, top, 0.3)
    nk = night(t)
    sea_top = mix(sea_top, (40, 50, 96), nk * 0.75)
    sea_bot = mix(sea_bot, (20, 28, 60), nk * 0.75)
    for i, y in enumerate(range(HORIZON, 560, 10)):
        k = (y - HORIZON) / 160
        pen.rect(0, y, W, y + 10, mix(sea_top, sea_bot, k), raw=True)
    X = dist(t)
    # 波光短线
    light = mix(sea_top, CREAM, 0.35)
    for row in range(9):
        y = HORIZON + 10 + row * 16 + row * row * 0.8
        p = 0.12 + row * 0.025
        spacing = 90 + row * 14
        off = (X * p + row * 57) % spacing
        for j in range(-1, int(W / spacing) + 2):
            x = j * spacing - off + 30 * hsh(j + row * 13, 5)
            L = (14 + row * 3) * (0.6 + 0.6 * math.sin(t * 2 + j + row))
            if L > 3:
                pen.rect(x, y, x + L, y + 2 + row * 0.25, light, raw=True)
    # 落日倒影
    sx, sy = sun_pos(t)
    refl = mix((252, 214, 110), (248, 110, 72), ramp(t, 8, 23))
    ra = 1 - ramp(t, 22, 26)
    for i in range(14):
        y = HORIZON + 6 + i * 9
        wv = (70 - i * 3.5) * (0.7 + 0.3 * math.sin(t * 3 + i * 1.7))
        xo = 8 * math.sin(t * 2.2 + i * 0.9)
        if wv > 4 and ra > 0:
            pen.rect(sx - wv / 2 + xo, y, sx + wv / 2 + xo, y + 3, refl + (int(200 * ra),), raw=True)
    # 月亮倒影
    mk = ramp(t, 25, 29)
    for i in range(8):
        y = HORIZON + 8 + i * 12
        wv = 24 - i * 2
        pen.rect(275 - wv / 2 + 5 * math.sin(t * 2 + i), y, 275 + wv / 2 + 5 * math.sin(t * 2 + i), y + 2,
                 (250, 240, 210, int(160 * mk)), raw=True)
    # 帆船
    for (x0, y, s) in BOATS:
        x = (x0 - 0.14 * X + 12 * t) % 2200 - 300
        bob = 2 * math.sin(t * 1.8 + x0)
        hull = [(x - 26 * s, y + bob), (x + 26 * s, y + bob), (x + 18 * s, y + 8 * s + bob), (x - 18 * s, y + 8 * s + bob)]
        pen.poly(hull, NAVY)
        pen.poly([(x - 2 * s, y - 4 + bob), (x - 2 * s, y - 50 * s + bob), (x + 22 * s, y - 4 + bob)], CREAM)
        pen.poly([(x - 5 * s, y - 4 + bob), (x - 5 * s, y - 40 * s + bob), (x - 22 * s, y - 4 + bob)], CORAL)


# ---------------------------------------------------------------- 步道：栏杆 / 路灯 / 路面 / 前景
RAIL_Y = 548
POST_GAP = 52
LAMP_GAP = 624

def lamp_on(t, i):
    return ramp(t, 21.0 + 0.23 * (i % 5), 21.6 + 0.23 * (i % 5))

def draw_promenade(pen, t, gull):
    X = dist(t)
    # 栏杆下的矮墙
    pen.rect(0, RAIL_Y, W, RAIL_Y + 16, CREAM_D)
    pen.rect(0, RAIL_Y + 12, W, RAIL_Y + 16, ROAD_D)
    # 栏杆立柱
    off = X % POST_GAP
    for j in range(-1, int(W / POST_GAP) + 2):
        x = j * POST_GAP - off
        pen.rect(x - 3, RAIL_Y - 52, x + 3, RAIL_Y, CREAM)
        pen.rect(x + 1, RAIL_Y - 52, x + 3, RAIL_Y, CREAM_D)
    pen.rect(0, RAIL_Y - 58, W, RAIL_Y - 50, CREAM)
    pen.rect(0, RAIL_Y - 51, W, RAIL_Y - 49, CREAM_D)
    pen.rect(0, RAIL_Y - 28, W, RAIL_Y - 24, CREAM)
    # 海鸥站在栏杆上
    if gull is not None:
        gull(pen, t)
    # 路灯
    first = int((X - 200) // LAMP_GAP)
    for i in range(first, first + 4):
        x = i * LAMP_GAP - X + 180
        if -80 < x < W + 80:
            draw_lamp(pen, x, t, i)


def draw_lamp(pen, x, t, i):
    base = RAIL_Y + 6
    pen.rect(x - 9, base - 20, x + 9, base + 4, TEAL_D)
    pen.rect(x - 4, base - 250, x + 4, base - 20, TEAL)
    pen.rect(x + 1, base - 250, x + 4, base - 20, TEAL_D)
    # 弯钩灯臂
    arm = qbez((x, base - 250), (x, base - 290), (x + 40, base - 282), 12)
    pen.line(arm, TEAL, 6)
    lx, ly = x + 42, base - 272
    pen.poly([(lx - 14, ly - 8), (lx + 14, ly - 8), (lx + 8, ly - 16), (lx - 8, ly - 16)], TEAL_D)
    on = lamp_on(t, i)
    bulb = mix(graded(CREAM), (255, 232, 150), on)
    pen.poly([(lx - 10, ly - 8), (lx + 10, ly - 8), (lx + 6, ly + 6), (lx - 6, ly + 6)], bulb, raw=True)
    if on > 0.01:
        fl = 1 - 0.04 * math.sin(t * 17 + i)
        for rr, a in ((70, 26), (42, 50), (22, 90)):
            pen.circle(lx, ly, rr * fl, (255, 220, 140, int(a * on)), raw=True)
        pen.poly([(lx - 8, ly + 6), (lx + 8, ly + 6), (lx + 110, GROUND + 18), (lx - 110, GROUND + 18)],
                 (255, 226, 150, int(26 * on)), raw=True)


def draw_road(pen, t):
    X = dist(t)
    pen.rect(0, RAIL_Y + 16, W, 660, ROAD)
    pen.rect(0, RAIL_Y + 16, W, RAIL_Y + 22, ROAD_D)
    # 骑行道虚线
    off = X % 110
    for j in range(-1, int(W / 110) + 2):
        x = j * 110 - off
        pen.rect(x, 644, x + 56, 649, ROAD_L)
    # 路面小石子
    off2 = X % 300
    for j in range(-1, 6):
        for k in range(6):
            x = j * 300 - off2 + hsh(k, j % 7) * 300
            y = 580 + hsh(k, 3 + j % 7) * 70
            pen.rect(x, y, x + 3 + 3 * hsh(k, 9), y + 2, ROAD_D)


FLOWERS = [CORAL, MUSTARD, CREAM, (236, 132, 150)]

def draw_foreground(pen, t):
    X = dist(t) * 1.55
    pen.rect(0, 660, W, H, BUSH_D)
    pen.rect(0, 660, W, 666, BUSH)
    gap = 170
    off = X % gap
    base_i = int(X // gap)
    for j in range(-1, int(W / gap) + 3):
        x = j * gap - off
        idx = base_i + j
        s = 0.7 + 0.6 * hsh(idx, 21)
        # 灌木：三个叠圆
        for dx, dy, r, c in ((-26, 8, 30, BUSH), (18, 4, 34, BUSH_L), (0, -6, 36, BUSH), (40, 14, 24, BUSH_D)):
            pen.circle(x + dx * s, 690 + dy * s, r * s, c)
        # 花
        for k in range(3):
            fx = x + (hsh(idx, 30 + k) - 0.5) * 90 * s
            fy = 668 + hsh(idx, 40 + k) * 16
            fc = FLOWERS[int(hsh(idx, 50 + k) * 4)]
            pen.line([(fx, fy + 20), (fx, fy)], BUSH_D, 2.5, caps=False)
            for a in range(5):
                ang = a * 1.2566 + idx
                pen.circle(fx + 5 * math.cos(ang), fy + 5 * math.sin(ang), 4.2, fc)
            pen.circle(fx, fy, 3, MUSTARD if fc != MUSTARD else CORAL_D)


# ---------------------------------------------------------------- 海鸥
GULL_WX = None   # 在 draw_frame 中根据时间确定

def gull_screen_x(t):
    # 海鸥站在路面层上（随栏杆滚动）；设定在 t=6.2 时位于鹈鹕前方约 380px
    return 820 - (dist(t) - dist(6.2))

def draw_gull(pen, t):
    x = gull_screen_x(t)
    fly = clamp((t - 6.45) / 2.6)
    if x < -80 and fly <= 0:
        return
    y = RAIL_Y - 58
    if fly > 0:
        # 起飞：向上、向后（相对地面基本不动，向左上漂）
        x += -40 * fly + 30 * math.sin(fly * 3)
        y -= 260 * ease_out(fly) + 40 * fly
        if fly >= 1:
            return
    s = 1.0 + 0.2 * fly
    startle = window(t, 6.1, 6.25, 6.4, 6.5)
    hop = 10 * startle
    y -= hop
    # 身体
    body = ellipse_pts(x, y - 14 * s, 18 * s, 10 * s, -0.15, 24)
    if fly > 0:
        flap = math.sin(t * 22) * 0.9
        for side, col in ((1, FEATHER_D), (-1, FEATHER)):
            tip = (x - 6 * s + side * 4, y - 16 * s - 34 * s * flap * side)
            wing = [(x - 12 * s, y - 16 * s), (x + 8 * s, y - 16 * s), tip]
            wing2 = [tip, (tip[0] - 16 * s, tip[1] + 4), (x - 12 * s, y - 16 * s)]
            pen.poly(wing, col)
            pen.poly(wing2, PRIMARY)
    else:
        for side in (-3, 3):
            pen.line([(x + side, y - 6), (x + side, y + 1)], BEAK, 2, caps=False)
    pen.poly(body, WHITE)
    pen.poly([(x - 16 * s, y - 16 * s), (x - 30 * s, y - 20 * s), (x - 28 * s, y - 12 * s)], FEATHER_D)
    if fly == 0:
        pen.poly(ellipse_pts(x - 4, y - 16, 14, 6, -0.2, 16), FEATHER)
        pen.poly([(x - 16, y - 18), (x - 26, y - 16), (x - 10, y - 12)], PRIMARY)
    hx, hy = x + 14 * s, y - 28 * s - 4 * startle
    pen.circle(hx, hy, 8 * s, WHITE)
    pen.poly([(hx + 6 * s, hy - 1), (hx + 18 * s, hy + 1), (hx + 6 * s, hy + 4)], MUSTARD)
    pen.circle(hx + 3 * s, hy - 2, 1.8 * s, NAVY)
    if startle > 0.2:
        for k in range(3):
            a = -1.9 + k * 0.45
            pen.line([(hx + 14 * math.cos(a), hy + 14 * math.sin(a)),
                      (hx + 24 * math.cos(a), hy + 24 * math.sin(a))], NAVY, 2.2)


# ---------------------------------------------------------------- 鱼（跃出海面，被鹈鹕接住）
FISH_T0, FISH_T1 = 9.1, 10.15

def draw_fish(pen, x, y, ang, s, t):
    wig = math.sin(t * 30) * 0.35
    pts = [rot(p, ang, (0, 0)) for p in [(18, 0), (10, -7), (-4, -8), (-14, -3), (-14, 3), (-4, 8), (10, 7)]]
    body = [(x + px * s, y + py * s) for px, py in pts]
    tail = [rot(p, ang + wig, (0, 0)) for p in [(-12, 0), (-26, -10), (-23, 0), (-26, 10)]]
    tail = [(x + px * s, y + py * s) for px, py in tail]
    pen.poly(tail, SEA_D)
    pen.poly(body, SILVER)
    stripe = [rot(p, ang) for p in [(12, 1), (-10, 1), (-10, 4), (10, 4)]]
    pen.poly([(x + px * s, y + py * s) for px, py in stripe], (120, 150, 190))
    ex, ey = rot((10, -2), ang)
    pen.circle(x + ex * s, y + ey * s, 1.8 * s, NAVY)

def splash(pen, x, y, t, t0):
    k = (t - t0) / 0.8
    if 0 <= k <= 1:
        for i in range(9):
            a = -math.pi / 2 + (i - 4) * 0.28
            v = 70 + 30 * hsh(i, 77)
            px = x + math.cos(a) * v * k * 1.2
            py = y + math.sin(a) * v * k * 1.3 + 160 * k * k
            pen.circle(px, py, 4 * (1 - k) + 1, (240, 250, 255, int(230 * (1 - k))), raw=True)
        pen.ellipse(x, y + 4, 20 + 40 * k, 4 + 4 * k, (240, 250, 255, int(160 * (1 - k))), raw=True)


# ---------------------------------------------------------------- 鹈鹕 + 单车
def ik(hip, foot, a, b):
    """两段式 IK，膝盖朝前"""
    dx, dy = foot[0] - hip[0], foot[1] - hip[1]
    d = clamp(math.hypot(dx, dy), abs(a - b) + 0.01, a + b - 0.01)
    base = math.atan2(dy, dx)
    al = math.acos(clamp((a * a + d * d - b * b) / (2 * a * d), -1, 1))
    c1 = (hip[0] + a * math.cos(base - al), hip[1] + a * math.sin(base - al))
    c2 = (hip[0] + a * math.cos(base + al), hip[1] + a * math.sin(base + al))
    return c1 if c1[0] > c2[0] else c2


class Rig:
    """局部坐标：原点 = 后轮轴，y 向下，单位像素（再乘 K）"""
    def __init__(self, ox, oy):
        self.ox, self.oy = ox, oy

    def P(self, x, y):
        return (self.ox + K * x, self.oy + K * y)

    def Ps(self, pts):
        return [self.P(x, y) for x, y in pts]


def rig_state(t):
    st = {}
    st["x"] = bike_x(t)
    X = dist(t)
    st["wheel"] = X / (WHEEL_R * K)
    st["crank"] = crank_angle(t)
    st["coast"] = coast(t)
    ca = st["crank"]
    pedal_bob = (1 - st["coast"]) * 2.2 * math.sin(2 * ca)
    road_bump = 1.2 * math.sin(X * 0.05) * math.sin(X * 0.013)
    st["bob"] = pedal_bob + road_bump
    # 表情 / 动作事件
    st["bell"] = window(t, 5.85, 5.95, 6.35, 6.5)
    look_fish = window(t, 8.9, 9.3, 10.0, 10.35)
    st["head_tilt"] = -0.10 * look_fish + 0.05 * window(t, 13.6, 14.2, 17.8, 18.6)
    st["open"] = window(t, 9.55, 9.95, 10.12, 10.2)
    st["pouch_fish"] = window(t, 10.15, 10.2, 11.75, 12.05)   # 鱼在嗉囊里
    st["gulp"] = clamp((t - 11.75) / 0.9)                    # 喉咙里的鼓包往下走
    st["happy"] = window(t, 12.0, 12.2, 13.2, 13.5) + window(t, 14.0, 14.3, 17.8, 18.3)
    st["wheee"] = window(t, 14.0, 14.4, 17.6, 18.2)
    st["blink"] = 1.0 if (t % 3.7) < 0.12 else 0.0
    st["wind"] = 1 + 1.4 * st["coast"] + 0.6 * window(t, 12.8, 14.0, 18, 19.5)
    st["t"] = t
    return st


def beak_frame(st):
    """头部在局部坐标下的位置和角度（其他部件都从这里算）"""
    t = st["t"]
    bob = st["bob"]
    hx, hy = 150, -206 + bob * 1.6 + 1.5 * math.sin(t * 2.6)
    return (hx, hy), st["head_tilt"] + 0.03 * math.sin(t * 1.9)


def draw_wheel(pen, R, cx, cy, ang, st, front):
    c = R.P(cx, cy)
    r = WHEEL_R * K
    # 挡泥板在后面画
    pen.ring(c[0], c[1], r - 3 * K, 7.5 * K, NAVY)
    pen.ring(c[0], c[1], r - 8 * K, 2.2 * K, (196, 204, 212))
    # 辐条（高速时加运动模糊）
    w_per_frame = speed(st["t"]) / (WHEEL_R * K) / FPS
    ghosts = 1 if w_per_frame < 0.12 else 3
    for g in range(ghosts):
        a0 = ang - g * w_per_frame / ghosts
        alpha = 255 if ghosts == 1 else int(200 / (g + 1))
        for i in range(12):
            a = a0 + i * math.pi / 6
            p0 = (c[0] + 5 * K * math.cos(a + 0.4), c[1] + 5 * K * math.sin(a + 0.4))
            p1 = (c[0] + (r - 9 * K) * math.cos(a), c[1] + (r - 9 * K) * math.sin(a))
            pen.line([p0, p1], (205, 212, 220, alpha), 1.3 * K, caps=False)
    pen.circle(c[0], c[1], 7 * K, (196, 204, 212))
    pen.circle(c[0], c[1], 3.5 * K, NAVY_L)


def fender(pen, R, cx, cy, a0, a1):
    pts = []
    for i in range(21):
        a = a0 + (a1 - a0) * i / 20
        pts.append(R.P(cx + (WHEEL_R + 5) * math.cos(a), cy + (WHEEL_R + 5) * math.sin(a)))
    pen.line(pts, CREAM, 6 * K)


def draw_pelican_bike(pen, t, st):
    R = Rig(st["x"], GROUND - WHEEL_R * K)
    bob = st["bob"]
    BB = (88, 10)
    CR = 24
    ca = st["crank"]
    RW, FW = (0, 0), (206, 0)
    S = (64, -62)
    Ht, Hb = (178, -84), (184, -56)
    grip = (144, -110)

    hipN = (74, -86 + bob)
    hipF = (80, -88 + bob)
    LA, LB = 60, 62

    def pedal(a):
        return (BB[0] + CR * math.cos(a), BB[1] + CR * math.sin(a))

    cst = st["coast"]
    pn, pf = pedal(ca), pedal(ca + math.pi)
    # 滑行时双脚向前伸直抬起
    lift_n = (182, -74 + 4 * math.sin(t * 9))
    lift_f = (174, -64 + 4 * math.sin(t * 9 + 1))
    fn = (lerp(pn[0], lift_n[0], cst), lerp(pn[1], lift_n[1], cst))
    ff = (lerp(pf[0], lift_f[0], cst), lerp(pf[1], lift_f[1], cst))
    kn = ik(hipN, fn, LA, LB)
    kf = ik(hipF, ff, LA, LB)

    # ---- 远侧腿 + 曲柄
    pen.line(R.Ps([BB, pf]), NAVY_L, 5 * K)
    pen.rect(*R.P(pf[0] - 8, pf[1] - 2), *R.P(pf[0] + 8, pf[1] + 3), NAVY_L)
    pen.line(R.Ps([hipF, kf]), LEG_D, 9 * K)
    pen.line(R.Ps([kf, ff]), LEG_D, 6.5 * K)
    draw_foot(pen, R, ff, LEG_D, cst)

    # ---- 车轮
    draw_wheel(pen, R, *RW, st["wheel"], st, False)
    draw_wheel(pen, R, *FW, st["wheel"] + 0.7, st, True)
    fender(pen, R, *RW, math.pi * 0.95, math.pi * 1.62)
    fender(pen, R, *FW, math.pi * 1.2, math.pi * 1.95)

    # ---- 车架（女式弯梁复古车）
    chain = [R.P(*p) for p in ellipse_pts((BB[0] + RW[0]) / 2, 5, 48, 13, 0.06, 30)]
    pen.line(chain, NAVY_L, 2.2 * K, caps=False)
    pen.line(R.Ps(qbez(Hb, (140, 16), BB, 14)), CORAL, 7 * K)
    pen.line(R.Ps(qbez(Ht, (120, -30), (70, -20), 14)), CORAL, 6.5 * K)
    pen.line(R.Ps([BB, S]), CORAL, 7 * K)
    pen.line(R.Ps([BB, RW]), CORAL_D, 5 * K)
    pen.line(R.Ps([S, RW]), CORAL_D, 5 * K)
    pen.line(R.Ps(qbez(Hb, (196, -24), FW, 10)), CORAL, 6 * K)
    pen.line(R.Ps([Ht, Hb]), CORAL_D, 9 * K)
    # 护链罩
    guard = ellipse_pts(50, 6, 44, 10, 0.08, 24, math.pi, 2 * math.pi)
    pen.poly(R.Ps(guard + [(94, 12), (6, 8)]), CREAM)
    # 座杆 + 车座
    pen.line(R.Ps([S, (61, -78)]), (190, 196, 204), 4.5 * K)
    saddle = [(38, -80), (48, -86), (70, -86), (80, -82), (74, -76), (46, -77)]
    pen.poly(R.Ps(saddle), (120, 72, 50))
    # 车把
    stem_top = (174, -104)
    pen.line(R.Ps([Ht, stem_top]), (190, 196, 204), 4.5 * K)
    bar = qbez(stem_top, (166, -114), grip, 10)
    pen.line(R.Ps(bar), (200, 206, 214), 4 * K)

    # ---- 车筐（法棍 + 花）
    draw_basket(pen, R, t)

    # ---- 尾羽、身体
    # 远侧翅膀的黑色飞羽（从身体后面伸向车把）
    pen.poly(R.Ps([(112, -128 + bob), (152, -118), (154, -106), (116, -108 + bob)]), (30, 30, 40))
    # 尾羽
    for k, (dx, dy) in enumerate(((0, 0), (4, 7), (8, -6))):
        tail = [(18 + dx, -118 + dy), (-22 + dx, -126 + dy * 1.6), (-16 + dx, -114 + dy * 1.6), (14 + dx, -106 + dy)]
        pen.poly(R.Ps([(x, y + bob) for x, y in tail]), FEATHER_D if k == 1 else FEATHER)
    body_pts = [(118, -150), (130, -124), (122, -96), (96, -80), (60, -76), (30, -86), (8, -104),
                (12, -130), (32, -154), (62, -170), (96, -166)]
    body = catmull([(x, y + bob) for x, y in body_pts], 8)
    pen.poly(R.Ps(body), (226, 230, 236))
    cx0, cy0 = 72, -122 + bob
    hl = [(cx0 + (x - cx0) * 0.93 - 4, cy0 + (y - cy0) * 0.93 - 5) for x, y in body]
    pen.poly(R.Ps(hl), WHITE)

    # ---- 近侧腿、曲柄、踏板、牙盘
    pen.circle(*R.P(*BB), 16 * K, (200, 206, 214))
    pen.circle(*R.P(*BB), 11 * K, NAVY_L)
    for i in range(5):
        a = ca + i * 2 * math.pi / 5
        pen.circle(*R.P(BB[0] + 7 * math.cos(a), BB[1] + 7 * math.sin(a)), 2.2 * K, (200, 206, 214))
    pen.line(R.Ps([BB, pn]), (208, 214, 222), 5 * K)
    pen.rect(*R.P(pn[0] - 9, pn[1] - 2), *R.P(pn[0] + 9, pn[1] + 3.5), NAVY)
    pen.line(R.Ps([hipN, kn]), LEG, 9.5 * K)
    pen.line(R.Ps([kn, fn]), LEG, 7 * K)
    draw_foot(pen, R, fn, LEG, cst)
    # 大腿根的羽毛
    pen.poly(R.Ps(ellipse_pts(hipN[0], hipN[1] - 4, 17, 10, -0.2, 20)), WHITE)

    # ---- 翅膀（握车把）
    (hx, hy), tilt = beak_frame(st)
    bell = st["bell"]
    gp = (grip[0], grip[1] - 7 * bell * abs(math.sin(t * 40)))
    wing = catmull([(106, -150 + bob), (80, -162 + bob), (46, -154 + bob), (18, -134 + bob), (0, -110 + bob),
                    (28, -106 + bob), (64, -102 + bob), (98, -108 + bob), (114, -124 + bob)], 8)
    pen.poly(R.Ps(wing), FEATHER)
    cov = catmull([(102, -148 + bob), (80, -158 + bob), (52, -150 + bob), (60, -136 + bob), (86, -128 + bob),
                   (108, -130 + bob)], 8)
    pen.poly(R.Ps(cov), (238, 241, 245))
    # 覆羽的扇贝纹
    for k in range(4):
        cx1 = 40 + k * 18
        pen.poly(R.Ps(ellipse_pts(cx1, -118 + bob + k * 1.5, 11, 6, 0.1, 16, 0, math.pi)), FEATHER_D)
    # 翅膀后端的黑色飞羽
    for k in range(5):
        y0 = -128 + k * 4.5 + bob
        x0 = 48 - k * 2
        pen.poly(R.Ps([(x0, y0 - 5), (x0 - 50 + k * 5, y0 + 1 + k * 2.2), (x0 + 2, y0 + 6)]), PRIMARY)
    # "手"：腕部到车把
    hand = catmull([(96, -128 + bob), (122, -126 + bob * 0.5), (gp[0] + 8, gp[1] - 6), (gp[0] + 12, gp[1] + 3),
                    (gp[0] + 2, gp[1] + 9), (122, -104 + bob * 0.5), (98, -106 + bob)], 6)
    pen.poly(R.Ps(hand), PRIMARY)
    for k in range(3):   # 手下缘的羽尖
        x0 = 104 + k * 11
        pen.poly(R.Ps([(x0, -108 + bob * 0.8), (x0 + 3, -98 + bob * 0.8), (x0 + 10, -107 + bob * 0.7)]), PRIMARY)
    for k in range(3):   # 握把的"手指"
        pen.circle(*R.P(gp[0] + 4 + k * 4, gp[1] + 6 - k * 3), 4.2 * K, (58, 60, 74))
    # 车铃
    bc = R.P(160, -114)
    pen.circle(bc[0], bc[1] - 1 * K, 5.5 * K, MUSTARD)
    pen.circle(bc[0], bc[1] - 6.5 * K, 1.8 * K, MUSTARD)
    if bell > 0.05:
        for k in range(3):
            a = -2.4 + k * 0.5
            r0 = 12 * K + 5 * K * math.sin(t * 30 + k)
            pen.line([(bc[0] + r0 * math.cos(a), bc[1] + r0 * math.sin(a)),
                      (bc[0] + (r0 + 10 * K) * math.cos(a), bc[1] + (r0 + 10 * K) * math.sin(a))],
                     NAVY, 2.6 * K)

    # ---- 脖子 + 头 + 喙 + 嗉囊
    draw_neck_head(pen, R, st, bob)


def draw_foot(pen, R, f, col, cst):
    # 蹼足：踩踏板时平放，滑行时脚尖向上翘
    ang = -0.9 * cst
    toes = [(-6, 0), (14, -3), (16, 2), (14, 5), (-4, 4)]
    pen.poly(R.Ps([(f[0] + p[0] * math.cos(ang) - p[1] * math.sin(ang),
                    f[1] - 3 + p[0] * math.sin(ang) + p[1] * math.cos(ang)) for p in toes]), col)


def draw_basket(pen, R, t):
    # 挂在车把前面
    top_y, bot_y = -104, -66
    x0, x1 = 186, 236
    bread = [(196, -104), (212, -142), (220, -140), (208, -102)]
    pen.poly(R.Ps(bread), (214, 150, 80))
    for k in range(3):
        a = (199 + k * 4.5, -112 - k * 9)
        pen.line(R.Ps([a, (a[0] + 5, a[1] + 1)]), (240, 196, 130), 1.8 * K)
    # 花
    sway = 3 * math.sin(t * 3.3)
    stem = qbez((226, -100), (228, -118), (232 + sway, -132), 8)
    pen.line(R.Ps(stem), BUSH, 2.2 * K)
    fc = (232 + sway, -134)
    for a in range(6):
        ang = a * 1.047 + t * 0.4
        pen.circle(*R.P(fc[0] + 5 * math.cos(ang), fc[1] + 5 * math.sin(ang)), 4.2 * K, CORAL)
    pen.circle(*R.P(*fc), 3.2 * K, MUSTARD)
    body = [(x0, top_y), (x1, top_y), (x1 - 6, bot_y), (x0 + 6, bot_y)]
    pen.poly(R.Ps(body), (196, 142, 84))
    for k in range(4):
        y = top_y + 7 + k * 8.5
        pen.line(R.Ps([(x0 + 1 + k * 1.5, y), (x1 - 1 - k * 1.5, y)]), (160, 108, 60), 1.6 * K, caps=False)
    pen.line(R.Ps([(x0 - 2, top_y), (x1 + 2, top_y)]), (150, 100, 58), 4 * K)
    pen.line(R.Ps([(x0 + 4, top_y), (178, -100)]), (190, 196, 204), 2.5 * K)


def draw_neck_head(pen, R, st, bob):
    t = st["t"]
    (hx, hy), tilt = beak_frame(st)
    # 脖子：S 形
    neck = bezier((106, -146 + bob), (130, -166 + bob), (116, -190 + bob), (hx - 4, hy + 8), 18)
    widths = [lerp(38, 26, i / 18) for i in range(19)]
    Pneck = R.Ps(neck)
    pen.tube(Pneck, [w * K for w in widths], WHITE)
    # 吞鱼时，脖子里的鼓包往下走
    g = st["gulp"]
    if 0 < g < 1:
        idx = int(lerp(18, 2, ease_io(g)))
        p = Pneck[idx]
        pen.circle(p[0] - 2 * K, p[1], 15 * K * math.sin(math.pi * g) ** 0.4, WHITE)
        pen.circle(p[0] - 5 * K, p[1] + 3 * K, 6 * K * math.sin(math.pi * g) ** 0.4, (234, 236, 238))

    # ---- 围巾（缠在脖子上，尾巴向后飘）
    draw_scarf(pen, R, st, Pneck, [w * K for w in widths])

    # 头部局部坐标 → 屏幕
    def HP(x, y):
        rx, ry = rot((x, y), tilt)
        return R.P(hx + rx, hy + ry)

    def HPs(pts):
        return [HP(x, y) for x, y in pts]

    op = st["open"]
    hinge = (8, 4)
    upper_ang = -0.34 * op
    L = 104
    # 嗉囊 / 下喙
    sag = 12 + 3 * math.sin(t * 5.3) + 5 * st["wheee"]
    fish_k = st["pouch_fish"]
    lower_top = [(hinge[0] + L * u, hinge[1] + 2 + 12 * u + 1.5 * math.sin(u * 3)) for u in [i / 16 for i in range(17)]]
    lower_bot = []
    for i in range(16, -1, -1):
        u = i / 16
        s = sag * math.sin(math.pi * u) ** 0.8 * (1 - 0.3 * u)
        if fish_k > 0:
            bump = math.exp(-((u - 0.45 - 0.05 * math.sin(t * 9)) / 0.2) ** 2)
            s += fish_k * (26 + 4 * math.sin(t * 14)) * bump
        if 0 < g < 0.3:
            s += (1 - g / 0.3) * 14 * math.exp(-((u - 0.12) / 0.15) ** 2)
        lower_bot.append((hinge[0] + L * u - 6 * u * (1 - u), hinge[1] + 4 + 12 * u + s))
    pen.poly(HPs(lower_top + lower_bot + [(-6, 12)]), POUCH)
    pen.poly(HPs([(hinge[0] + L * u, hinge[1] + 4 + 12 * u) for u in [i / 12 for i in range(13)]] +
                 [(hinge[0] + L, hinge[1] + 9 + 12), (hinge[0], hinge[1] + 9)]), POUCH_D)

    # 头
    pen.poly(HPs(ellipse_pts(0, 0, 23, 20, -0.15, 30)), WHITE)
    # 冠羽
    crest_sway = 3 * math.sin(t * 6) - 4 * st["wind"]
    crest = [(-12, -12), (-30 + crest_sway, -20), (-22 + crest_sway, -12), (-34 + crest_sway, -8), (-16, -2)]
    pen.poly(HPs(crest), (250, 226, 150))
    # 上喙
    def U(p):
        return rot(p, upper_ang, hinge)
    upper = [U((hinge[0] - 2, hinge[1] - 7)), U((hinge[0] + L * 0.5, hinge[1] + 1)),
             U((hinge[0] + L - 4, hinge[1] + 9)), U((hinge[0] + L + 4, hinge[1] + 12)),
             U((hinge[0] + L - 2, hinge[1] + 17)), U((hinge[0] + L - 8, hinge[1] + 13)),
             U((hinge[0] + L * 0.5, hinge[1] + 7)), U((hinge[0] - 2, hinge[1] + 4))]
    pen.poly(HPs(upper), BEAK)
    ridge_l = [U((hinge[0] + 4, hinge[1] - 2)), U((hinge[0] + L * 0.6, hinge[1] + 4)), U((hinge[0] + L - 6, hinge[1] + 10))]
    pen.line(HPs(ridge_l), BEAK_D, 1.8 * K)
    hook = [U((hinge[0] + L - 6, hinge[1] + 9)), U((hinge[0] + L + 4, hinge[1] + 12)),
            U((hinge[0] + L - 2, hinge[1] + 17)), U((hinge[0] + L - 9, hinge[1] + 13))]
    pen.poly(HPs(hook), BEAK_TIP)
    # 鱼尾从喙缝里露出来
    if st["pouch_fish"] > 0.3:
        tip = HP(hinge[0] + L * 0.72, hinge[1] + 10)
        wig = 0.35 * math.sin(t * 22)
        fin = [(-3, 2), (-2, -9), (-11, -20), (-2, -15), (6, -21), (3, -9), (4, 2)]
        pen.poly([(tip[0] + K * rx, tip[1] + K * ry) for rx, ry in (rot(q, wig) for q in fin)], SILVER)
        pen.line([(tip[0] + K * rx, tip[1] + K * ry) for rx, ry in (rot(q, wig) for q in fin[1:6])], SEA_D, 1.6 * K)
    # 眼周裸皮 + 眼睛
    ex, ey = 4, -5
    pen.poly(HPs(ellipse_pts(ex, ey, 8, 6.5, 0, 18)), (250, 206, 170))
    if st["happy"] > 0.5:
        arc = [(ex - 5, ey + 1), (ex - 2, ey - 3), (ex + 2, ey - 3), (ex + 5, ey + 1)]
        pen.line(HPs(arc), NAVY, 2.4 * K)
    elif st["blink"] > 0:
        pen.line(HPs([(ex - 4, ey), (ex + 4, ey)]), NAVY, 2.2 * K)
    else:
        look = (1.2, -1.5) if st["head_tilt"] < -0.03 else (1.4, 0)
        pen.poly(HPs(ellipse_pts(ex + look[0], ey + look[1], 3.6, 3.6, 0, 14)), NAVY)
        pen.poly(HPs(ellipse_pts(ex + look[0] + 1.2, ey + look[1] - 1.3, 1.2, 1.2, 0, 8)), WHITE)
    # 腮红
    pen.poly(HPs(ellipse_pts(-4, 7, 6, 3.5, 0, 14)), (248, 170, 160, 150))


def draw_scarf(pen, R, st, Pneck, widths):
    t = st["t"]
    k0 = Pneck[11]
    knot = (k0[0] - widths[11] * 0.42, k0[1] + 2 * K)
    wind = st["wind"]
    for tail_i, (length, phase, yoff) in enumerate(((20, 0.0, 0), (16, 1.7, 5))):
        pts = []
        for i in range(length + 1):
            u = i / length
            x = knot[0] - (6 + i * 5.2) * K
            flutter = (4 + 7 * u * wind) * math.sin(t * (7 + 3 * wind) - i * 0.55 + phase)
            droop = (1.6 - 0.6 * min(wind, 2)) * 22 * u * u
            y = knot[1] + (yoff + flutter * u + droop - 8 * u * (wind - 1)) * K
            pts.append((x, y))
        for i in range(length):
            w0 = lerp(13, 8, i / length) * K
            (x0, y0), (x1, y1) = pts[i], pts[i + 1]
            col = CORAL if (i // 3) % 2 == 0 else CREAM
            if tail_i == 1:
                col = CORAL_D if col == CORAL else CREAM_D
            quad = [(x0, y0 - w0 / 2), (x1, y1 - w0 / 2), (x1, y1 + w0 / 2), (x0, y0 + w0 / 2)]
            pen.poly(quad, col)
        # 流苏
        ex, ey = pts[-1]
        for k in range(3):
            pen.line([(ex, ey - 3 * K + k * 3 * K), (ex - 7 * K, ey - 3 * K + k * 3.5 * K + 2 * math.sin(t * 20 + k))],
                     CORAL_D, 1.6 * K)
    # 围在脖子上的一圈
    pen.tube(Pneck[8:14], [w + 5 * K for w in widths[8:14]], CORAL)
    for j in (10, 12):
        (x0, y0), (x1, y1) = Pneck[j - 1], Pneck[j + 1]
        L = math.hypot(x1 - x0, y1 - y0) or 1
        nx, ny = -(y1 - y0) / L, (x1 - x0) / L
        cx, cy = Pneck[j]
        hw = widths[j] / 2 + 2.5 * K
        pen.line([(cx - nx * hw, cy - ny * hw), (cx + nx * hw, cy + ny * hw)], CREAM, 3.6 * K, caps=False)
    pen.circle(knot[0], knot[1], 8 * K, CORAL_D)


# ---------------------------------------------------------------- 速度线 / 小装饰
def draw_speedlines(pen, t, st):
    k = st["coast"]
    if k <= 0.02:
        return
    cx = st["x"]
    for i in range(16):
        y = 300 + hsh(i, 61) * 330
        ph = (t * (2.6 + hsh(i, 64)) + hsh(i, 62)) % 1.0
        x = cx + 120 - ph * 900
        L = 80 + 140 * hsh(i, 63)
        pen.line([(x, y), (x + L, y)], (255, 255, 255, int(190 * k * math.sin(math.pi * ph))), 3.5, raw=True, caps=False)


def draw_notes(pen, t, st):
    """开心时头顶冒出音符 / 爱心"""
    (hx, hy), _ = beak_frame(st)
    R = Rig(st["x"], GROUND - WHEEL_R * K)
    base = R.P(hx - 10, hy - 30)
    for i, (t0, sym) in enumerate(((12.05, "♥"), (12.35, "♪"), (14.3, "♪"), (14.9, "♫"), (15.6, "♪"), (16.4, "♥"))):
        k = (t - t0) / 1.2
        if 0 <= k <= 1:
            x = base[0] - 30 * k + 12 * math.sin(k * 9 + i)
            y = base[1] - 70 * k
            a = int(255 * math.sin(math.pi * k))
            f = font(SYMB, int(40 * SS), 0)
            col = CORAL if sym == "♥" else NAVY
            pen.text((x, y), sym, f, col + (a,), anchor="mm", raw=True)


def draw_bell_text(pen, t, st):
    k = (t - 5.95) / 0.8
    if 0 <= k <= 1:
        R = Rig(st["x"], GROUND - WHEEL_R * K)
        (hx, hy), _ = beak_frame(st)
        bx, by = R.P(hx + 70, hy - 40)
        f = font(SONG, int(30 * SS), 0)
        a = int(255 * min(1, 3 * (1 - k)))
        s = ease_out(k * 3)
        pen.text((bx + 20 * s, by - 26 * s), "叮铃铃！", f, NAVY + (a,), anchor="mm")


# ---------------------------------------------------------------- 标题 / 片尾
def draw_titles(pen, t):
    k = window(t, 0.4, 1.2, 3.4, 4.2)
    if k > 0:
        rise = (1 - ease_out((t - 0.4) / 1.0)) * 20
        f1 = font(SONG, int(96 * SS), 0)
        f2 = font(FUTURA, int(22 * SS), 2)
        a = int(255 * k)
        x, y = 90, 44 + rise
        pen.text((x + 5, y + 5), "鹈鹕骑单车", f1, NAVY + (int(a * 0.9),))
        pen.text((x, y), "鹈鹕骑单车", f1, CREAM + (a,))
        pen.rect(x + 2, y + 128, x + 476, y + 132, CORAL + (a,), raw=True)
        pen.text((x + 2, y + 146), "A  PELICAN  RIDES  A  BICYCLE", f2, NAVY + (a,))
    k2 = ramp(t, 28.8, 29.8)
    if k2 > 0:
        a = int(255 * k2)
        f1 = font(SONG, int(84 * SS), 0)
        f2 = font(FUTURA, int(20 * SS), 2)
        pen.text((W / 2 + 4, 150 + 4), "完", f1, (10, 12, 30, int(a * 0.8)), anchor="mm")
        pen.text((W / 2, 150), "完", f1, CREAM + (a,), anchor="mm")
        pen.text((W / 2, 222), "THE  END", f2, (230, 200, 150, a), anchor="mm")


# ---------------------------------------------------------------- 后期：颗粒 + 暗角 + 入场/出场
_GRAIN = None
_VIGNETTE = None

def post_layers():
    global _GRAIN, _VIGNETTE
    if _GRAIN is None:
        random.seed(7)
        _GRAIN = []
        for i in range(6):
            n = Image.effect_noise((W, H), 34).convert("RGB")
            _GRAIN.append(n)
        v = Image.new("L", (W // 4, H // 4), 0)
        vd = ImageDraw.Draw(v)
        for i in range(60):
            k = i / 60
            vd.ellipse((-W // 8 * (1 - k) - 40 + k * 40, -H // 8 * (1 - k) - 40 + k * 30,
                        W // 4 + W // 8 * (1 - k) + 40 - k * 40, H // 4 + H // 8 * (1 - k) + 40 - k * 30),
                       fill=int(255 * ease_io(k)))
        v = v.filter(ImageFilter.GaussianBlur(6)).resize((W, H), Image.BILINEAR)
        _VIGNETTE = v
    return _GRAIN, _VIGNETTE


def draw_frame(t):
    top, hor, mult, add = tod(t)
    GRADE[0], GRADE[1] = mult, add
    img = Image.new("RGB", (W * SS, H * SS), CREAM)
    pen = Pen(img)
    st = rig_state(t)

    draw_sky(pen, t)
    draw_clouds(pen, t)
    draw_far(pen, t)
    draw_sea(pen, t)

    # 鱼从海里跃起（在栏杆之后起跳）
    fish_launch = (st["x"] + 520 - 0.35 * (dist(t) - dist(FISH_T0)), 508)
    splash(pen, *fish_launch, t, FISH_T0 - 0.05)

    draw_promenade(pen, t, draw_gull)
    draw_road(pen, t)

    # 自行车影子
    sx = st["x"]
    pen.ellipse(sx + 110 * K, GROUND + 4, 175 * K, 8, ROAD_D)
    draw_speedlines(pen, t, st)
    draw_pelican_bike(pen, t, st)

    # 鱼的抛物线：从海面飞到张开的嘴里
    if FISH_T0 <= t < FISH_T1 + 0.02:
        k = clamp((t - FISH_T0) / (FISH_T1 - FISH_T0))
        R = Rig(st["x"], GROUND - WHEEL_R * K)
        (hx, hy), tilt = beak_frame(rig_state(FISH_T1))
        mouth = R.P(hx + 60, hy + 12)
        p0 = fish_launch
        p1 = ((p0[0] + mouth[0]) / 2 + 60, min(p0[1], mouth[1]) - 230)
        pts = qbez(p0, p1, mouth, 1)
        u = k
        x = (1 - u) ** 2 * p0[0] + 2 * u * (1 - u) * p1[0] + u * u * mouth[0]
        y = (1 - u) ** 2 * p0[1] + 2 * u * (1 - u) * p1[1] + u * u * mouth[1]
        dx = 2 * (1 - u) * (p1[0] - p0[0]) + 2 * u * (mouth[0] - p1[0])
        dy = 2 * (1 - u) * (p1[1] - p0[1]) + 2 * u * (mouth[1] - p1[1])
        ang = math.atan2(dy, dx) + math.pi
        draw_fish(pen, x, y, ang, 1.7 - 0.4 * k, t)
        for j in range(1, 4):   # 水珠拖尾
            uu = max(0, u - j * 0.04)
            xx = (1 - uu) ** 2 * p0[0] + 2 * uu * (1 - uu) * p1[0] + uu * uu * mouth[0]
            yy = (1 - uu) ** 2 * p0[1] + 2 * uu * (1 - uu) * p1[1] + uu * uu * mouth[1]
            pen.circle(xx, yy, 4 - j, (235, 248, 255, 200 - j * 50), raw=True)

    draw_foreground(pen, t)
    draw_notes(pen, t, st)
    draw_bell_text(pen, t, st)
    draw_titles(pen, t)

    img = img.resize((W, H), Image.LANCZOS)

    grain, vig = post_layers()
    g = grain[int(t * 12) % len(grain)]
    img = Image.blend(img, ImageChops.overlay(img, g), 0.22)
    dark = ImageChops.multiply(img, Image.new("RGB", (W, H), (70, 60, 80)))
    img = Image.composite(img, dark, vig)
    fade = min(ramp(t, 0.0, 0.6), 1 - ramp(t, DUR - 1.2, DUR - 0.1))
    if fade < 1:
        img = Image.blend(Image.new("RGB", (W, H), (12, 14, 28)), img, fade)
    return img


# ---------------------------------------------------------------- 配乐
SR = 44100

def note_freq(n):
    names = {"C": 0, "C#": 1, "D": 2, "D#": 3, "E": 4, "F": 5, "F#": 6, "G": 7, "G#": 8, "A": 9, "A#": 10, "B": 11}
    name, octv = n[:-1], int(n[-1])
    midi = 12 * (octv + 1) + names[name]
    return 440.0 * 2 ** ((midi - 69) / 12)

BPM = 120
BEAT = 60 / BPM

MELODY = [
    # 第 3–6 小节（A）
    ("G4", .5), ("C5", .5), ("E5", 1), ("D5", .5), ("C5", .5), ("G4", 1),
    ("A4", .5), ("C5", .5), ("E5", 1), ("D5", 1), ("C5", 1),
    ("F4", .5), ("A4", .5), ("C5", 1), ("D5", .5), ("C5", .5), ("A4", 1),
    ("G4", 1), ("B4", .5), ("D5", .5), ("G5", 1.5), (None, .5),
    # 第 7–10 小节（A'，滑行段更欢快）
    ("G4", .5), ("C5", .5), ("E5", 1), ("G5", .5), ("E5", .5), ("C5", 1),
    ("A4", .5), ("C5", .5), ("E5", .5), ("A5", .5), ("G5", 1), ("E5", 1),
    ("F5", .5), ("E5", .5), ("D5", .5), ("C5", .5), ("D5", .5), ("E5", .5), ("F5", .5), ("D5", .5),
    ("E5", 1), ("G5", 1), ("C6", 1.5), (None, .5),
    # 第 11–14 小节（B，日落）
    ("A5", 2), ("G5", 1), ("F5", 1),
    ("E5", 2), ("D5", 1), ("C5", 1),
    ("D5", 1.5), ("E5", .5), ("F5", 1), ("A5", 1),
    ("G5", 2), ("F5", .5), ("D5", .5), ("B4", 1),
    # 第 15 小节
    ("C5", 4),
]

CHORDS = ["C", "C", "C", "Am", "F", "G", "C", "Am", "F", "C", "F", "Em", "Dm", "G", "C", "C"]
UKE = {"C": ["G4", "C4", "E4", "C5"], "Am": ["A4", "C4", "E4", "A4"], "F": ["A4", "C4", "F4", "A4"],
       "G": ["G4", "D4", "G4", "B4"], "Em": ["G4", "E4", "G4", "B4"], "Dm": ["A4", "D4", "F4", "A4"]}
ROOT = {"C": ("C2", "G2"), "Am": ("A1", "E2"), "F": ("F1", "C2"), "G": ("G1", "D2"),
        "Em": ("E2", "B1"), "Dm": ("D2", "A1")}

_PLUCK_CACHE = {}

def pluck(freq, dur):
    key = (round(freq, 2), dur)
    if key in _PLUCK_CACHE:
        return _PLUCK_CACHE[key]
    rnd = random.Random(int(freq * 100))
    n = max(2, int(SR / freq))
    buf = [rnd.uniform(-1, 1) for _ in range(n)]
    # 预先低通，让音色更像尼龙弦
    for _ in range(2):
        buf = [(buf[i] + buf[i - 1]) * 0.5 for i in range(n)]
    out = array.array("f", [0.0]) * int(dur * SR)
    idx = 0
    decay = 0.996
    for i in range(len(out)):
        j = idx % n
        nxt = (idx + 1) % n
        v = buf[j]
        out[i] = v
        buf[j] = decay * 0.5 * (v + buf[nxt])
        idx += 1
    _PLUCK_CACHE[key] = out
    return out


def add(buf, start, samples, gain, pan=0.0):
    L, Rr = buf
    s0 = int(start * SR)
    gl = gain * math.cos((pan + 1) * math.pi / 4)
    gr = gain * math.sin((pan + 1) * math.pi / 4)
    n = min(len(samples), len(L) - s0)
    for i in range(max(0, -s0), n):
        v = samples[i]
        L[s0 + i] += v * gl
        Rr[s0 + i] += v * gr


def whistle(freq, dur):
    n = int((dur + 0.08) * SR)
    out = array.array("f", [0.0]) * n
    ph = 0.0
    rnd = random.Random(int(freq))
    lp = 0.0
    for i in range(n):
        tt = i / SR
        env = min(1.0, tt / 0.035) * (1.0 if tt < dur - 0.05 else max(0.0, 1 - (tt - dur + 0.05) / 0.13))
        vib = 1 + 0.006 * math.sin(2 * math.pi * 5.5 * tt) * min(1, tt / 0.25)
        slide = 1 - 0.02 * math.exp(-tt / 0.03)
        ph += 2 * math.pi * freq * vib * slide / SR
        lp += 0.08 * (rnd.uniform(-1, 1) - lp)
        out[i] = env * (math.sin(ph) + 0.06 * math.sin(2 * ph) + 0.35 * lp)
    return out


def bass(freq, dur):
    n = int(dur * SR)
    out = array.array("f", [0.0]) * n
    for i in range(n):
        tt = i / SR
        env = math.exp(-tt * 3.2) * min(1, tt / 0.006)
        ph = 2 * math.pi * freq * tt
        out[i] = env * (math.sin(ph) + 0.35 * math.sin(2 * ph) + 0.12 * math.sin(3 * ph))
    return out


def shaker(dur=0.07, seed=0):
    rnd = random.Random(seed)
    n = int(dur * SR)
    out = array.array("f", [0.0]) * n
    prev = 0.0
    for i in range(n):
        x = rnd.uniform(-1, 1)
        out[i] = (x - prev) * math.exp(-i / SR * 60) * min(1, i / (SR * 0.004))
        prev = x
    return out


def kick():
    n = int(0.25 * SR)
    out = array.array("f", [0.0]) * n
    ph = 0.0
    for i in range(n):
        tt = i / SR
        f = 45 + 80 * math.exp(-tt * 30)
        ph += 2 * math.pi * f / SR
        out[i] = math.sin(ph) * math.exp(-tt * 14)
    return out


def bell_sfx():
    n = int(1.4 * SR)
    out = array.array("f", [0.0]) * n
    parts = [(2350, 1.0, 2.6), (2350 * 2.76, 0.45, 4.5), (2350 * 5.4, 0.2, 7.0), (2350 * 0.5, 0.15, 3.0)]
    for i in range(n):
        tt = i / SR
        v = 0.0
        for f, a, d in parts:
            v += a * math.sin(2 * math.pi * f * tt) * math.exp(-tt * d)
        out[i] = v * min(1, tt / 0.001) * (1 + 0.3 * math.sin(2 * math.pi * 7 * tt))
    return out


def noise_burst(dur, cutoff, decay, seed, attack=0.005):
    rnd = random.Random(seed)
    n = int(dur * SR)
    out = array.array("f", [0.0]) * n
    lp = 0.0
    a = 1 - math.exp(-2 * math.pi * cutoff / SR)
    for i in range(n):
        tt = i / SR
        lp += a * (rnd.uniform(-1, 1) - lp)
        out[i] = lp * math.exp(-tt * decay) * min(1, tt / attack)
    return out


def gulp():
    n = int(0.22 * SR)
    out = array.array("f", [0.0]) * n
    ph = 0.0
    for i in range(n):
        tt = i / SR
        f = 520 * math.exp(-tt * 9) + 110
        ph += 2 * math.pi * f / SR
        out[i] = math.sin(ph) * math.sin(math.pi * tt / 0.22) ** 1.5
    return out


def snap():
    n = int(0.06 * SR)
    out = array.array("f", [0.0]) * n
    for i in range(n):
        tt = i / SR
        out[i] = (math.sin(2 * math.pi * 1300 * tt) * 0.6 + math.sin(2 * math.pi * 760 * tt)) * math.exp(-tt * 90)
    return out


def gull_call():
    n = int(0.42 * SR)
    out = array.array("f", [0.0]) * n
    ph = 0.0
    for i in range(n):
        tt = i / SR
        u = tt / 0.42
        f = 1500 - 700 * u + 250 * math.sin(math.pi * u) + 40 * math.sin(2 * math.pi * 28 * tt)
        ph += 2 * math.pi * f / SR
        v = math.sin(ph) + 0.5 * math.sin(2 * ph) + 0.3 * math.sin(3 * ph)
        out[i] = v * math.sin(math.pi * u) ** 0.7
    return out


def tick():
    n = int(0.012 * SR)
    return array.array("f", [math.sin(2 * math.pi * 4200 * i / SR) * math.exp(-i / SR * 500) for i in range(n)])


def reverb(L, Rr, wet=0.22):
    """简易 Schroeder 混响"""
    outL = array.array("f", L)
    outR = array.array("f", Rr)
    for src, dst, off in ((L, outL, 0), (Rr, outR, 23)):
        n = len(src)
        acc = array.array("f", [0.0]) * n
        for dl, fb in ((1557 + off, 0.80), (1617 + off, 0.79), (1491 + off, 0.78), (1422 + off, 0.77)):
            cb = array.array("f", [0.0]) * n
            for i in range(dl, n):
                cb[i] = src[i - dl] + fb * cb[i - dl]
            for i in range(n):
                acc[i] += cb[i] * 0.25
        for dl, g in ((225, 0.7), (556, 0.7)):
            ap = array.array("f", [0.0]) * n
            for i in range(n):
                x = acc[i]
                y = -g * x + (acc[i - dl] if i >= dl else 0.0) + g * (ap[i - dl] if i >= dl else 0.0)
                ap[i] = y
            acc = ap
        for i in range(n):
            dst[i] = src[i] + wet * acc[i]
    return outL, outR


def make_music(path):
    total = DUR + 1.0
    N = int(total * SR)
    L = array.array("f", [0.0]) * N
    Rr = array.array("f", [0.0]) * N
    buf = (L, Rr)
    bar = 4 * BEAT

    # 尤克里里扫弦
    strum_pat = [(0, 1, 0.9), (1, 1, 0.6), (1.5, -1, 0.45), (2.5, -1, 0.45), (3, 1, 0.6), (3.5, -1, 0.4)]
    for b, ch in enumerate(CHORDS):
        if b >= 15:
            pat = [(0, 1, 0.9)]
        elif b >= 10:
            pat = [(0, 1, 0.8), (2, 1, 0.55), (3, -1, 0.35)]
        else:
            pat = strum_pat
        for (pos, direction, vel) in pat:
            t0 = b * bar + pos * BEAT
            strings = UKE[ch] if direction > 0 else list(reversed(UKE[ch]))
            ring = 2.6 if b >= 14 else 1.1
            for k, nname in enumerate(strings):
                add(buf, t0 + k * 0.014, pluck(note_freq(nname), ring), 0.11 * vel, pan=-0.25)

    # 贝斯
    for b, ch in enumerate(CHORDS):
        r, f5 = ROOT[ch]
        if b >= 15:
            add(buf, b * bar, bass(note_freq(r), 2.5), 0.42)
            continue
        add(buf, b * bar, bass(note_freq(r), 1.0), 0.42)
        add(buf, b * bar + 2 * BEAT, bass(note_freq(f5), 1.0), 0.34)

    # 口哨旋律（从第 3 小节开始）
    t0 = 2 * bar
    for n, d in MELODY:
        if n:
            add(buf, t0, whistle(note_freq(n), d * BEAT * 0.95), 0.16, pan=0.15)
        t0 += d * BEAT

    # 沙锤 + 底鼓
    for b in range(2, 14):
        for e in range(8):
            vel = 0.05 if e % 2 else 0.035
            if 6 <= b <= 9:
                vel *= 1.5
            add(buf, b * bar + e * BEAT / 2, shaker(seed=b * 8 + e), vel, pan=0.4)
        if 6 <= b <= 9:
            for q in (0, 2):
                add(buf, b * bar + q * BEAT, kick(), 0.3)

    # 音效
    bs = bell_sfx()
    add(buf, 5.95, bs, 0.09, pan=0.2)
    add(buf, 6.2, bs, 0.08, pan=0.2)
    add(buf, 6.5, gull_call(), 0.07, pan=0.5)
    add(buf, 6.95, gull_call(), 0.05, pan=0.3)
    add(buf, FISH_T0 - 0.05, noise_burst(0.6, 2500, 7, 3), 0.35, pan=0.5)
    add(buf, FISH_T1 + 0.02, snap(), 0.22, pan=0.1)
    add(buf, 11.8, gulp(), 0.22)
    add(buf, 12.1, gulp(), 0.16)
    # 滑行：风声 + 飞轮棘轮声
    wind = noise_burst(6.5, 900, 0, 11, attack=1.5)
    for i in range(len(wind)):
        tt = i / SR
        wind[i] *= min(1, (6.5 - tt) / 1.5)
    add(buf, 13.3, wind, 0.28)
    tk = tick()
    tt = 13.9
    while tt < 18.3:
        add(buf, tt, tk, 0.035 * coast(tt), pan=-0.1)
        tt += 1 / (14 * speed(tt) / 380)
    add(buf, 29.4, bs, 0.07, pan=0.4)

    L, Rr = reverb(L, Rr)
    peak = max(max(abs(v) for v in L), max(abs(v) for v in Rr)) or 1.0
    g = 0.89 / peak
    fade_n = int(1.2 * SR)
    frames = array.array("h", [0]) * (2 * N)
    for i in range(N):
        f = 1.0
        if i > N - fade_n:
            f = (N - i) / fade_n
        frames[2 * i] = int(clamp(L[i] * g * f, -1, 1) * 32767)
        frames[2 * i + 1] = int(clamp(Rr[i] * g * f, -1, 1) * 32767)
    with wave.open(path, "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes(frames.tobytes())


# ---------------------------------------------------------------- 主程序
def render_bytes(i):
    return draw_frame(i / FPS).tobytes()


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "still":
        os.makedirs(os.path.join(HERE, "previews"), exist_ok=True)
        for s in sys.argv[2:]:
            t = float(s)
            draw_frame(t).save(os.path.join(HERE, "previews", f"still_{t:05.2f}.png"))
            print("saved", t)
        return
    if len(sys.argv) > 1 and sys.argv[1] == "music":
        make_music(os.path.join(HERE, "music.wav"))
        return

    wav = os.path.join(HERE, "music.wav")
    if not os.path.exists(wav) or "--remusic" in sys.argv:
        print("合成配乐 …")
        make_music(wav)
    nframes = int(DUR * FPS)
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", wav,
           "-c:v", "libx264", "-preset", "medium", "-crf", "23", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", OUT]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    with Pool(max(1, os.cpu_count() - 1)) as pool:
        for i, b in enumerate(pool.imap(render_bytes, range(nframes), chunksize=4)):
            proc.stdin.write(b)
            if i % 60 == 0:
                print(f"frame {i}/{nframes}", flush=True)
    proc.stdin.close()
    proc.wait()
    print("done →", OUT)


if __name__ == "__main__":
    main()
