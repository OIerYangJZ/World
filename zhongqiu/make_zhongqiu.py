# -*- coding: utf-8 -*-
"""
《Clawd 的中秋》—— 纸片定格动画（25 秒），主角：小螃蟹 Clawd
12 fps，所有纸片逐帧轻微抖动（boiling），模拟手工摆拍。
运行：python3 make_zhongqiu.py  → frames/*.png + music.wav → ffmpeg 合成
"""
import math, random, os, sys, wave, struct
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops, ImageEnhance, ImageOps

W, H, FPS = 1280, 720, 12
TOTAL = 300
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "frames")
FONT_PATH = "/System/Library/Fonts/Hiragino Sans GB.ttc"

CLAY = (217, 119, 87)
CREAM = (244, 236, 219)
INK = (43, 38, 34)
RED = (190, 52, 44)
GOLD = (248, 208, 118)

_fonts = {}
def font(size, bold=True):
    k = (size, bold)
    if k not in _fonts:
        _fonts[k] = ImageFont.truetype(FONT_PATH, size, index=2 if bold else 0)
    return _fonts[k]

def rng(*key):
    return random.Random(hash(key) & 0xFFFFFFFF)

def clamp(v, a=0.0, b=1.0):
    return max(a, min(b, v))

def ease_out(p):
    return 1 - (1 - p) ** 3

def ease_in(p):
    return p ** 2

def darker(c, k=0.75):
    return tuple(int(v * k) for v in c[:3])

def lerp(a, b, t):
    return a + (b - a) * t

def steps(p, n=8):
    return math.floor(clamp(p) * n) / n

# ---------------------------------------------------------------- 纹理
random.seed(9)

def paper_noise(lo, hi, sigma=60, blur=0.8):
    n = Image.effect_noise((W, H), sigma).filter(ImageFilter.GaussianBlur(blur))
    return n.point(lambda v: int(lo + (hi - lo) * v / 255))

# 夜空：上深下浅的藏青纸
sky_grad = Image.linear_gradient("L").resize((W, H))
SKY_TOP, SKY_BOT = Image.new("RGB", (W, H), (14, 18, 42)), Image.new("RGB", (W, H), (38, 44, 82))
SKY = Image.composite(SKY_BOT, SKY_TOP, sky_grad)
BACKGROUNDS = []
for i in range(4):
    n = paper_noise(0, 255, 70, 1.2)
    fibers = Image.effect_noise((W // 4, H // 4), 90).resize((W, H), Image.BICUBIC)
    mix = ImageChops.add(n.point(lambda v: v // 4), fibers.point(lambda v: v // 5))
    light = ImageEnhance.Brightness(SKY).enhance(1.35)
    BACKGROUNDS.append(Image.composite(light, SKY, mix))

OBJ_TEX = [paper_noise(218, 255, 55, 0.6).convert("RGB") for _ in range(3)]

vg = Image.radial_gradient("L").resize((W, H), Image.BICUBIC)
VIGNETTE = vg.point(lambda v: int(clamp((v - 90) / 165) ** 1.6 * 200))
BLACK = Image.new("RGB", (W, H), (6, 6, 12))

# 月光（预计算的柔光）
MOON_X, MOON_Y, MOON_R = 960, 196, 116
_g = Image.new("L", (W // 2, H // 2), 0)
ImageDraw.Draw(_g).ellipse([MOON_X / 2 - 120, MOON_Y / 2 - 120, MOON_X / 2 + 120, MOON_Y / 2 + 120], fill=150)
MOON_GLOW_L = _g.filter(ImageFilter.GaussianBlur(55)).resize((W, H), Image.BICUBIC)
MOON_GLOW = ImageOps.colorize(MOON_GLOW_L, (0, 0, 0), (255, 214, 140))

# 灯笼光晕精灵
_s = Image.new("L", (120, 120), 0)
ImageDraw.Draw(_s).ellipse([30, 30, 90, 90], fill=170)
LANTERN_GLOW = _s.filter(ImageFilter.GaussianBlur(16))

# ---------------------------------------------------------------- 纸片工具
_tile_cache = {}
def tile_img(text, w, h, bg, fg, fs, angle, radius=None):
    a = int(round(angle))
    key = (text, w, h, bg, fg, fs, a, radius)
    if key in _tile_cache:
        return _tile_cache[key]
    img = Image.new("RGBA", (w + 6, h + 6), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    rad = radius if radius is not None else max(2, min(w, h) // 7)
    d.rounded_rectangle([3, 3, w + 2, h + 2], radius=rad,
                        fill=bg + (255,), outline=darker(bg, 0.82) + (255,), width=1)
    if text:
        d.text((3 + w / 2, 3 + h / 2 + fs * 0.04), text, font=font(fs), fill=fg + (255,), anchor="mm")
    if a:
        img = img.rotate(a, resample=Image.BICUBIC, expand=True)
    _tile_cache[key] = img
    return img

def comp(layer, img, cx, cy):
    x, y = int(round(cx - img.width / 2)), int(round(cy - img.height / 2))
    x0, y0 = max(0, -x), max(0, -y)
    x1, y1 = min(img.width, W - x), min(img.height, H - y)
    if x1 <= x0 or y1 <= y0:
        return
    if (x0, y0, x1, y1) != (0, 0, img.width, img.height):
        img = img.crop((x0, y0, x1, y1))
    layer.alpha_composite(img, (x + x0, y + y0))

def boil(f, key, amp=1.2, rot=2.5):
    r = rng("boil", key, f)
    return r.uniform(-amp, amp), r.uniform(-amp, amp), r.uniform(-rot, rot)

def put_tile(ctx, key, text, cx, cy, w, h, bg, fg, fs, angle=0, amp=1.2, rot=2.5, radius=None):
    dx, dy, da = boil(ctx.f, key, amp, rot)
    comp(ctx.obj, tile_img(text, w, h, bg, fg, fs, angle + da, radius), cx + dx, cy + dy)

class Ctx:
    def __init__(self, f):
        self.f = f
        self.obj = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        self.glows = []   # (x, y, 缩放)

# ---------------------------------------------------------------- 星星
def make_stars():
    r = rng("stars")
    out = []
    while len(out) < 70:
        x, y = r.uniform(20, 1260), r.uniform(20, 470)
        if (x - MOON_X) ** 2 + (y - MOON_Y) ** 2 < (MOON_R + 60) ** 2:
            continue
        out.append(dict(x=x, y=y, s=r.choice([3, 4, 4, 5, 6]), t=r.randint(0, 22), ph=r.uniform(0, 6)))
    return out
STARS = make_stars()

def stars(ctx):
    f = ctx.f
    for i, s in enumerate(STARS):
        if f < s["t"]:
            continue
        tw = math.sin(f * 0.35 + s["ph"])
        if tw < -0.85:
            continue
        size = s["s"] + (1 if tw > 0.6 else 0)
        put_tile(ctx, ("star", i), "", s["x"], s["y"], size, size, (250, 240, 200), (250, 240, 200), 6,
                 angle=45, amp=0.4, rot=8, radius=1)

# ---------------------------------------------------------------- 月亮：由“月”字纸片拼成，藏着几只“兔”
MCELL = 22
def build_moon():
    r = rng("moon")
    cells = []
    y = MOON_Y - MOON_R
    while y <= MOON_Y + MOON_R:
        x = MOON_X - MOON_R
        while x <= MOON_X + MOON_R:
            if (x - MOON_X) ** 2 + (y - MOON_Y) ** 2 < (MOON_R - 6) ** 2:
                cells.append((x, y))
            x += MCELL
        y += MCELL
    order = sorted(cells, key=lambda c: -c[1] + r.uniform(-60, 60))
    tiles = []
    shades = [(250, 226, 150), (246, 214, 128), (252, 236, 178)]
    for k, (x, y) in enumerate(order):
        rabbit = abs(x - (MOON_X - 18)) < 30 and abs(y - (MOON_Y + 20)) < 24
        ch = "兔" if rabbit else "月"
        bg = (226, 196, 120) if rabbit else shades[k % 3]
        tiles.append(dict(x=x, y=y, ch=ch, bg=bg, fg=darker(bg, 0.86), t=8 + int(k / len(order) * 26) + r.randint(0, 3),
                          ang=r.uniform(-6, 6), spin=r.uniform(-60, 60), drop=r.uniform(300, 480), id=("moon", k)))
    return tiles
MOON = build_moon()
MOON_DONE = max(t["t"] for t in MOON) + 7

def moon(ctx):
    f = ctx.f
    for tl in MOON:
        if f < tl["t"]:
            continue
        e = ease_out(steps((f - tl["t"]) / 7, 7))
        y = tl["y"] - (1 - e) * tl["drop"]
        ang = tl["ang"] * 0.4 + (1 - e) * tl["spin"]
        put_tile(ctx, tl["id"], tl["ch"], tl["x"], y, MCELL - 1, MCELL - 1, tl["bg"], tl["fg"], 14,
                 angle=ang, amp=0.7, rot=2.5)

def moon_glow_level(f):
    return clamp((f - 10) / (MOON_DONE - 10)) * (0.9 + 0.1 * math.sin(f * 0.2))

# ---------------------------------------------------------------- 屋顶：“瓦”字纸片
def build_roof():
    r = rng("roof")
    tiles = []
    k = 0
    for row, y in enumerate(range(588, 740, 24)):
        for x in range(0, 1300, 24):
            xx = x + (12 if row % 2 else 0)
            bg = (70, 74, 104) if row == 0 else r.choice([(46, 50, 76), (52, 56, 84), (42, 45, 70)])
            tiles.append(dict(x=xx, y=y, bg=bg, fg=darker(bg, 1.35) if row == 0 else darker(bg, 1.3),
                              t=int(x / 1300 * 10) + r.randint(0, 3), ang=r.uniform(-5, 5), id=("roof", k)))
            k += 1
    return tiles
ROOF = build_roof()
ROOF_TOP = 576

def roof(ctx):
    f = ctx.f
    for tl in ROOF:
        if f < tl["t"]:
            continue
        e = ease_out(steps((f - tl["t"]) / 4, 4))
        put_tile(ctx, tl["id"], "瓦", tl["x"], tl["y"] + (1 - e) * 200, 23, 23, tl["bg"],
                 tuple(min(255, v) for v in tl["fg"]), 14, angle=tl["ang"], amp=0.5, rot=1.5)

# ---------------------------------------------------------------- 主角 Clawd
CLAWD = [(c, 0) for c in range(2, 9)] + [(c, 1) for c in range(2, 9)] + \
        [(c, 2) for c in range(0, 11)] + [(c, 3) for c in range(2, 9)]
LEGS = [2, 4, 6, 8]
_cr = rng("clawd-build")
CLAWD_BUILD = {px: 20 + int(k * 14 / len(CLAWD)) for k, px in
               enumerate(sorted(CLAWD, key=lambda c: -c[1] + _cr.uniform(-1.5, 1.5)))}
BLINKS = {52, 53, 132, 133, 214, 215, 276, 277}
CY = ROOF_TOP - 42

# (帧, x, y, 格子, 视线x, 视线y)
CLAWD_KEYS = [(0, 380, CY, 15, 0, 0), (44, 380, CY, 15, 0, 0), (50, 380, CY, 15, 1, -1),
              (60, 380, CY, 15, 0, -1), (112, 380, CY, 15, 0, -1), (126, 548, CY, 15, 1, 0),
              (192, 548, CY, 15, 1, 0), (196, 548, CY, 15, 1, -1), (238, 548, CY, 15, 1, -1),
              (252, 610, CY, 15, 0, 0)]
LANTERN_T = [66, 76, 86, 95, 103, 110]
HOPS = {}
for t in LANTERN_T:
    HOPS.update({t - 2: 6, t - 1: 10, t: 6})
HOPS.update({262: 8, 263: 16, 264: 20, 265: 16, 266: 8, 282: 6, 283: 12, 284: 6})

def clawd_state(f):
    for (f0, *a), (f1, *b) in zip(CLAWD_KEYS, CLAWD_KEYS[1:]):
        if f0 <= f < f1:
            moving = a[:3] != b[:3]
            p = ease_out(steps((f - f0) / (f1 - f0), max(1, (f1 - f0) // 2))) if moving else 0
            x, y, cell = (lerp(u, v, p) for u, v in zip(a[:3], b[:3]))
            if moving:
                lx, ly = (b[3], b[4]) if p > 0.5 else (a[3], a[4])
            else:
                lx, ly = a[3], a[4]
            return x, y, cell, lx, ly, moving
    _, *a = CLAWD_KEYS[-1]
    return a[0], a[1], a[2], a[3], a[4], False

def clawd(ctx):
    f = ctx.f
    x, y, cell, lx, ly, walking = clawd_state(f)
    y -= HOPS.get(f, 0)
    if walking:
        y -= 3 if (f // 2) % 2 else 0
    size = max(4, int(round(cell)) + 1)
    ox, oy = x - 5 * cell, y - 2 * cell
    # 兔耳朵（中秋限定）
    if f >= 200:
        pop = [0.4, 1.2, 1.0][min(2, f - 200)]
        for i, c in enumerate((3, 7)):
            ang = (10 if i == 0 else -10) + (4 * math.sin(f * 0.5 + i) if f > 206 else 0)
            ex, ey = ox + c * cell + (-4 if i == 0 else 4), oy - cell * 1.9
            put_tile(ctx, ("ear", i), "", ex, ey, int(cell * 0.95 * pop), int(cell * 2.7 * pop),
                     CREAM, CREAM, 8, angle=ang, amp=0.5, rot=1.5, radius=6)
            put_tile(ctx, ("ear-in", i), "", ex, ey + 3, max(2, int(cell * 0.4 * pop)), int(cell * 1.8 * pop),
                     (240, 170, 170), (240, 170, 170), 8, angle=ang, amp=0.3, rot=1, radius=3)
    for (c, r) in CLAWD:
        t = CLAWD_BUILD[(c, r)]
        if f < t:
            continue
        drop = (1 - ease_out(steps((f - t) / 5, 5))) * 320
        # 放灯时举起钳子
        lift = 0
        if c in (0, 1, 9, 10) and any(0 <= f - lt + 3 < 6 for lt in LANTERN_T):
            lift = cell * 0.8
        put_tile(ctx, ("clawd", c, r), "", ox + c * cell, oy + r * cell - drop - lift, size, size,
                 CLAY, CLAY, 8, angle=drop * 0.1, amp=0.4, rot=1.2)
    if f >= 32:
        for i, c in enumerate(LEGS):
            lift = cell * 0.4 if walking and (i % 2) == (f // 2) % 2 else 0
            put_tile(ctx, ("leg", i), "", ox + c * cell, oy + 4 * cell - lift, size, size,
                     CLAY, CLAY, 8, amp=0.4, rot=1.2)
    if f >= 36:
        eh = cell * 0.25 if f in BLINKS else cell * 1.5
        for c in (3, 7):
            put_tile(ctx, ("eye", c), "", ox + c * cell + lx * cell * 0.3, oy + cell * 0.8 + ly * cell * 0.3,
                     max(3, int(cell * 0.8)), max(3, int(eh)), INK, INK, 8, amp=0.5, rot=1)
    # 心情小红晕（结尾）
    if f >= 256:
        for c in (1.6, 8.4):
            put_tile(ctx, ("blush", c), "", ox + c * cell, oy + cell * 1.7, int(cell * 1.1), int(cell * 0.55),
                     (236, 150, 130), (236, 150, 130), 8, amp=0.4, rot=1, radius=4)

# ---------------------------------------------------------------- 孔明灯 / 灯笼
LANTERN_CH = ["圆", "安", "乐", "福", "念", "喜"]
_lantern_cache = {}
def lantern_img(ch, scale, angle):
    s, a = round(scale, 2), int(round(angle))
    key = (ch, s, a)
    if key in _lantern_cache:
        return _lantern_cache[key]
    bw, bh = int(46 * s), int(58 * s)
    w, h = bw + 10, bh + int(34 * s)
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cx = w / 2
    top = int(8 * s)
    d.line([(cx, 0), (cx, top)], fill=GOLD + (255,), width=max(1, int(2 * s)))
    d.rounded_rectangle([cx - bw / 2, top + 3 * s, cx + bw / 2, top + bh], radius=int(18 * s),
                        fill=RED + (255,), outline=darker(RED, 0.75) + (255,), width=1)
    for yy in (top, top + bh - 3 * s):
        d.rectangle([cx - 13 * s, yy, cx + 13 * s, yy + 5 * s], fill=GOLD + (255,))
    d.text((cx, top + bh / 2 + 2 * s), ch, font=font(max(8, int(24 * s))), fill=GOLD + (255,), anchor="mm")
    ty = top + bh + 5 * s
    d.line([(cx, ty), (cx, ty + 18 * s)], fill=GOLD + (255,), width=max(1, int(3 * s)))
    d.line([(cx - 3 * s, ty + 18 * s), (cx + 3 * s, ty + 18 * s)], fill=GOLD + (255,), width=max(1, int(3 * s)))
    if a:
        img = img.rotate(a, resample=Image.BICUBIC, expand=True)
    _lantern_cache[key] = img
    return img

def lanterns(ctx):
    f = ctx.f
    for i, t in enumerate(LANTERN_T):
        if f < t:
            continue
        r = rng("lantern", i)
        age = (f - t) // 2 * 2         # 一拍二，定格感
        side = -1 if i % 2 == 0 else 1
        x0, y0 = 380 + side * 80, CY - 40
        y = y0 - 250 * (1 - math.exp(-age / 45)) - 1.5 * age
        drift = r.uniform(0.6, 2.6) * (1 if i % 3 else -0.6)
        x = x0 + drift * age + 14 * math.sin(age * 0.12 + i)
        scale = 1.0 - min(0.45, age / 260)
        ang = 6 * math.sin(age * 0.15 + i * 2)
        pop = [0.5, 1.15][min(1, f - t)] if f - t < 2 else 1.0
        if y < -120:
            continue
        dx, dy, da = boil(f, ("lantern", i), 0.8, 1.2)
        img = lantern_img(LANTERN_CH[i], round(scale * pop * 20) / 20, ang + da)
        comp(ctx.obj, img, x + dx, y + dy)
        ctx.glows.append((x, y, scale * 1.2))

# ---------------------------------------------------------------- 月饼
def make_mooncake(R=64):
    S = R * 2 + 12
    img = Image.new("RGBA", (S * 2, S * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    c = S
    pts = []
    for i in range(240):
        a = i / 240 * math.tau
        rr = (R - 5 + 5 * abs(math.cos(a * 7))) * 2
        pts.append((c + rr * math.cos(a), c + rr * math.sin(a)))
    d.polygon(pts, fill=(200, 136, 64, 255), outline=(150, 92, 40, 255))
    d.ellipse([c - R * 1.45, c - R * 1.45, c + R * 1.45, c + R * 1.45], outline=(160, 100, 44, 255), width=6)
    d.ellipse([c - R * 1.3, c - R * 1.3, c + R * 1.3, c + R * 1.3], fill=(208, 146, 72, 255))
    d.text((c + 3, c + 3), "团圆", font=font(int(R * 0.72)), fill=(236, 186, 110, 255), anchor="mm")
    d.text((c, c), "团圆", font=font(int(R * 0.72)), fill=(128, 76, 30, 255), anchor="mm")
    return img.resize((S, S), Image.LANCZOS)

MOONCAKE = make_mooncake()
MC_X, MC_Y = 712, ROOF_TOP - 60
MC_T, MC_SPLIT, MC_FLY = 114, 156, 166

def mooncake_piece(k, angle):
    key = ("mc", k, int(round(angle)))
    if key in _tile_cache:
        return _tile_cache[key]
    S = MOONCAKE.width
    mask = Image.new("L", (S, S), 0)
    ImageDraw.Draw(mask).pieslice([-4, -4, S + 4, S + 4], k * 90 + 2, k * 90 + 88, fill=255)
    piece = MOONCAKE.copy()
    piece.putalpha(ImageChops.multiply(MOONCAKE.getchannel("A"), mask))
    if key[2]:
        piece = piece.rotate(key[2], resample=Image.BICUBIC)
    _tile_cache[key] = piece
    return piece

# 每块飞向远方：方向（右下起顺时针的象限中点）
PIECE_DIR = [(0.9, -0.6), (-0.9, -0.5), (-0.4, -1.0), (0.5, -1.0)]

def mooncake(ctx):
    f = ctx.f
    if not (MC_T <= f < 196):
        return
    age = f - MC_T
    e = ease_out(steps(age / 8, 8))
    y = MC_Y - (1 - e) * 520
    if 8 <= age < 11:
        y += [5, -6, 0][age - 8]     # 落地弹一下
    if f < MC_SPLIT:
        dx, dy, da = boil(f, "mc", 0.8, 1.5)
        img = MOONCAKE.rotate(da + (1 - e) * 90, resample=Image.BICUBIC)
        comp(ctx.obj, img, MC_X + dx, y + dy)
        return
    gap = ease_out(steps((f - MC_SPLIT) / 6, 6)) * 12
    for k in range(4):
        mid = math.radians(k * 90 + 45)
        px, py = MC_X + math.cos(mid) * gap, MC_Y + math.sin(mid) * gap
        ang = 0
        if f >= MC_FLY + k * 2:
            q = (f - MC_FLY - k * 2)
            dist = 6 * q * q
            vx, vy = PIECE_DIR[k]
            px += vx * dist
            py += vy * dist
            ang = q * 14 * (1 if k % 2 else -1)
            if dist > 1200:
                continue
        dx, dy, da = boil(f, ("mcp", k), 0.8, 1.5)
        comp(ctx.obj, mooncake_piece(k, ang + da), px + dx, py + dy)

# ---------------------------------------------------------------- 标题
TITLE = ["中", "秋", "快", "乐"]
TITLE_X, TITLE_Y = 610, 300

def title(ctx):
    f = ctx.f
    if f < 242:
        return
    for i, t in enumerate(TITLE):
        t0 = 242 + i * 3
        if f < t0:
            continue
        x = TITLE_X + (i - 1.5) * 112
        age = f - t0
        drop = (1 - ease_out(steps(age / 5, 5))) * 420
        pop = 1.0 if age >= 7 else [1, 1, 1, 1, 1, 1.12, 1.04][age]
        put_tile(ctx, ("title", i), t, x, TITLE_Y - drop, int(96 * pop), int(96 * pop), RED, GOLD,
                 int(62 * pop), angle=[-4, 3, -2, 4][i] + drop * 0.08, amp=1.0, rot=2)
    if f >= 258:
        put_tile(ctx, "date", "2026 · 丙午年 · 中秋", TITLE_X, TITLE_Y + 80, 300, 36, CREAM, INK, 20,
                 angle=-1, amp=0.8, rot=1)

# ---------------------------------------------------------------- 字幕
CAPTIONS = [
    (14, 60, "中秋夜，月亮是一年里最圆的。"),
    (64, 112, "给每一个在远方的人，放一盏灯。"),
    (116, 154, "月饼切成好多块，"),
    (154, 194, "每一块，都寄给想念的人。"),
    (198, 242, "但愿人长久，千里共婵娟。"),
    (256, TOTAL, "Clawd 祝你：花好月圆，阖家团圆。"),
]

def caption(ctx):
    f = ctx.f
    for s, e, text in CAPTIONS:
        if s <= f < e:
            n = min(len(text), f - s + 1)
            fs = 28
            tw = int(font(fs, False).getlength(text))
            w, h = tw + 56, 52
            img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            d = ImageDraw.Draw(img)
            r = rng("cap", text)
            pts = [(r.uniform(0, 3), r.uniform(0, 3)), (w - r.uniform(0, 3), r.uniform(0, 3)),
                   (w - r.uniform(0, 3), h - r.uniform(0, 3)), (r.uniform(0, 3), h - r.uniform(0, 3))]
            d.polygon(pts, fill=CREAM + (255,))
            d.text((28, h / 2 + 2), text[:n], font=font(fs, False), fill=INK + (255,), anchor="lm")
            dx, dy, da = boil(f, "cap", 0.8, 0.5)
            img = img.rotate(r.uniform(-1, 1) + da, resample=Image.BICUBIC, expand=True)
            comp(ctx.obj, img, 640 + dx, 664 + dy)

# ---------------------------------------------------------------- 合成一帧
def render(f):
    ctx = Ctx(f)
    stars(ctx)
    moon(ctx)
    lanterns(ctx)
    title(ctx)
    roof(ctx)
    mooncake(ctx)
    clawd(ctx)
    caption(ctx)

    r = rng("frame", f)
    obj = ctx.obj
    rgb = ImageChops.multiply(obj.convert("RGB"), OBJ_TEX[f % 3])
    alpha = obj.getchannel("A")
    obj = Image.merge("RGBA", (*rgb.split(), alpha))

    frame = BACKGROUNDS[r.randrange(4)].copy()
    # 月光 + 灯笼光晕（在纸片后面）
    lvl = moon_glow_level(f)
    if lvl > 0:
        frame = ImageChops.screen(frame, ImageEnhance.Brightness(MOON_GLOW).enhance(lvl))
    if ctx.glows:
        gl = Image.new("L", (W, H), 0)
        for x, y, s in ctx.glows:
            sz = max(8, int(120 * s))
            spr = LANTERN_GLOW.resize((sz, sz))
            gl.paste(spr, (int(x - sz / 2), int(y - sz / 2)), spr)
        frame = ImageChops.screen(frame, ImageOps.colorize(gl, (0, 0, 0), (255, 150, 80)))
    # 纸片投影
    sh = alpha.filter(ImageFilter.GaussianBlur(4)).point(lambda v: int(v * 0.6))
    shadow_mask = Image.new("L", (W, H), 0)
    shadow_mask.paste(sh, (6, 8))
    frame.paste((4, 4, 12), mask=shadow_mask)
    frame.paste(obj, mask=alpha)
    frame = Image.composite(BLACK, frame, VIGNETTE)
    frame = ImageEnhance.Brightness(frame).enhance(1 + r.uniform(-0.035, 0.035))
    # 开头淡入、结尾淡出
    fade = clamp(f / 6) * clamp((TOTAL - 1 - f) / 10)
    if fade < 1:
        frame = Image.blend(BLACK, frame, fade)
    ox, oy = r.randint(-1, 1), r.randint(-1, 1)
    if ox or oy:
        frame = ImageChops.offset(frame, ox, oy)
    return frame

# ---------------------------------------------------------------- 配乐：原创五声音阶拨弦小曲（Karplus-Strong）
def make_music(path):
    SR = 44100
    dur = TOTAL / FPS
    N = int(SR * dur)
    buf = [0.0] * N
    NOTE = {"D3": 146.83, "A2": 110.0, "G2": 98.0, "B2": 123.47, "D4": 293.66, "E4": 329.63, "F#4": 369.99,
            "A4": 440.0, "B4": 493.88, "D5": 587.33, "E5": 659.25, "F#5": 739.99, "A3": 220.0}
    r = random.Random(3)

    def pluck(freq, start, length, amp, decay=0.996):
        p = int(SR / freq)
        ring = [r.uniform(-1, 1) for _ in range(p)]
        s0 = int(start * SR)
        n = min(int(length * SR), N - s0)
        prev = 0.0
        for i in range(n):
            j = i % p
            v = ring[j]
            nv = decay * 0.5 * (v + ring[(j + 1) % p])
            ring[j] = nv
            prev = 0.7 * prev + 0.3 * v      # 柔化高频
            buf[s0 + i] += prev * amp

    beat = 0.66
    t0 = 0.7
    melody = [("A4", 1), ("B4", 1), ("D5", 2), ("B4", 1), ("A4", 1), ("F#4", 2),
              ("E4", 1), ("F#4", 1), ("A4", 1), ("B4", 1), ("A4", 4),
              ("D5", 1), ("E5", 1), ("D5", 1), ("B4", 1), ("A4", 2), ("F#4", 2),
              ("E4", 1), ("F#4", 0.5), ("E4", 0.5), ("D4", 1), ("E4", 1), ("D4", 4)]
    t = t0
    for n, b in melody:
        pluck(NOTE[n], t, b * beat + 1.6, 0.32, 0.997)
        t += b * beat
    bass = ["D3", "A2", "G2", "A2", "B2", "A2", "G2", "D3"]
    for i, n in enumerate(bass):
        pluck(NOTE[n], t0 + i * 4 * beat, 4 * beat + 2, 0.26, 0.998)
        pluck(NOTE[n] * 1.5, t0 + i * 4 * beat + 2 * beat, 2 * beat + 1.5, 0.12, 0.997)
    # 结尾和弦
    for k, n in enumerate(["D4", "F#4", "A4", "D5"]):
        pluck(NOTE[n], t + k * 0.08, 4, 0.22, 0.998)
    # 简易混响
    for delay, g in ((0.043, 0.35), (0.071, 0.28), (0.113, 0.22), (0.167, 0.16)):
        dd = int(delay * SR)
        for i in range(N - 1, dd - 1, -1):
            buf[i] += buf[i - dd] * g
    peak = max(abs(v) for v in buf) or 1
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        fade_n = int(1.2 * SR)
        out = bytearray()
        for i, v in enumerate(buf):
            g = min(1.0, (N - i) / fade_n)
            out += struct.pack("<h", int(v / peak * 0.85 * g * 32767))
        w.writeframes(bytes(out))

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    args = sys.argv[1:]
    if args == ["music"]:
        make_music(os.path.join(HERE, "music.wav"))
        sys.exit()
    only = [int(a) for a in args]
    for f in (only or range(TOTAL)):
        render(f).save(os.path.join(OUT, f"{f:04d}.png"))
        if f % 50 == 0:
            print("frame", f, flush=True)
