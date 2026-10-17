# -*- coding: utf-8 -*-
"""
《透过 Claude 的眼睛》—— 纸片定格动画（30 秒精简版，主角：小螃蟹 Clawd）
12 fps，每一帧所有纸片都会轻微抖动（boiling），模拟手工逐帧摆拍。
运行：python3 make_film.py  → frames/*.png → ffmpeg 合成
"""
import math, random, os, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops, ImageEnhance

W, H, FPS = 1280, 720, 12
TOTAL = 356
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frames")
FONT_PATH = "/System/Library/Fonts/Hiragino Sans GB.ttc"

CLAY = (217, 119, 87)       # Claude 的陶土橙
CREAM = (244, 236, 219)
INK = (43, 38, 34)
YARN = (206, 66, 58)

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
    """定格感：把连续进度量化成 n 个“摆拍位置”"""
    return math.floor(clamp(p) * n) / n

# ---------------------------------------------------------------- 预计算纹理
random.seed(7)

def paper_noise(lo, hi, sigma=60, blur=0.8):
    n = Image.effect_noise((W, H), sigma).filter(ImageFilter.GaussianBlur(blur))
    return n.point(lambda v: int(lo + (hi - lo) * v / 255))

BG_BASE = (30, 31, 45)
BACKGROUNDS = []
for i in range(4):
    n = paper_noise(0, 255, 70, 1.2)
    fibers = Image.effect_noise((W // 4, H // 4), 90).resize((W, H), Image.BICUBIC)
    base = Image.new("RGB", (W, H), BG_BASE)
    light = Image.new("RGB", (W, H), (52, 52, 70))
    mix = ImageChops.add(n.point(lambda v: v // 3), fibers.point(lambda v: v // 4))
    BACKGROUNDS.append(Image.composite(light, base, mix.point(lambda v: min(255, v))))

OBJ_TEX = [paper_noise(218, 255, 55, 0.6).convert("RGB") for _ in range(3)]

vg = Image.radial_gradient("L").resize((W, H), Image.BICUBIC)
VIGNETTE = vg.point(lambda v: int(clamp((v - 90) / 165) ** 1.6 * 200))
BLACK = Image.new("RGB", (W, H), (8, 8, 12))

# ---------------------------------------------------------------- 纸片工具
_tile_cache = {}
def tile_img(text, w, h, bg, fg, fs, angle):
    a = int(round(angle))
    key = (text, w, h, bg, fg, fs, a)
    if key in _tile_cache:
        return _tile_cache[key]
    img = Image.new("RGBA", (w + 6, h + 6), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([3, 3, w + 2, h + 2], radius=max(2, min(w, h) // 7),
                        fill=bg + (255,), outline=darker(bg, 0.82) + (255,), width=1)
    if text:
        d.text((3 + w / 2, 3 + h / 2 + fs * 0.04), text, font=font(fs), fill=fg + (255,), anchor="mm")
    if a:
        img = img.rotate(a, resample=Image.BICUBIC, expand=True)
    _tile_cache[key] = img
    return img

def comp(layer, img, cx, cy):
    """以中心点 (cx,cy) 把 img 叠到 layer 上，自动裁剪出界部分"""
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

def put_tile(ctx, key, text, cx, cy, w, h, bg, fg, fs, angle=0, amp=1.2, rot=2.5):
    dx, dy, da = boil(ctx.f, key, amp, rot)
    comp(ctx.obj, tile_img(text, w, h, bg, fg, fs, angle + da), cx + dx, cy + dy)

_note_cache = {}
def note_img(text, bg, angle):
    a = int(round(angle))
    key = (text, bg, a)
    if key in _note_cache:
        return _note_cache[key]
    fs = 22
    tw = int(font(fs, False).getlength(text))
    w, h = tw + 40, 58
    img = Image.new("RGBA", (w + 8, h + 14), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # 手撕纸边：多边形的顶点轻微不规则
    r = rng("note", text)
    pts = []
    for i in range(9):
        pts.append((4 + w * i / 8, 10 + r.uniform(-1.5, 1.5)))
    for i in range(9):
        pts.append((4 + w + r.uniform(-1.5, 1.5), 10 + h * i / 8))
    for i in range(9):
        pts.append((4 + w - w * i / 8, 10 + h + r.uniform(-2.5, 2.5)))
    for i in range(9):
        pts.append((4 + r.uniform(-1.5, 1.5), 10 + h - h * i / 8))
    d.polygon(pts, fill=bg + (255,))
    d.text((4 + w / 2, 10 + h / 2 + 3), text, font=font(fs, False), fill=INK + (255,), anchor="mm")
    # 图钉
    px = 4 + w / 2
    d.ellipse([px - 8, 2, px + 8, 18], fill=(196, 58, 52, 255))
    d.ellipse([px - 4, 5, px + 1, 10], fill=(240, 150, 140, 255))
    if a:
        img = img.rotate(a, resample=Image.BICUBIC, expand=True)
    _note_cache[key] = img
    return img

# ---------------------------------------------------------------- 帧上下文
class Ctx:
    def __init__(self, f):
        self.f = f
        self.obj = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        self.back = None   # 2x 超采样矢量层（线）
        self.front = None  # 2x 超采样矢量层（星芒）

    def back_draw(self):
        if self.back is None:
            self.back = Image.new("RGBA", (W * 2, H * 2), (0, 0, 0, 0))
        return ImageDraw.Draw(self.back)

    def front_draw(self):
        if self.front is None:
            self.front = Image.new("RGBA", (W * 2, H * 2), (0, 0, 0, 0))
        return ImageDraw.Draw(self.front)

def flush(ctx, which):
    layer = getattr(ctx, which)
    if layer is not None:
        ctx.obj.alpha_composite(layer.resize((W, H), Image.LANCZOS))
        setattr(ctx, which, None)

# ---------------------------------------------------------------- 线（注意力之线 / 毛线）
def thread(ctx, key, p0, p1, lift, width, color, progress=1.0):
    d = ctx.back_draw()
    r = rng("thread", key, ctx.f)
    cx = (p0[0] + p1[0]) / 2 + r.uniform(-5, 5)
    cy = (p0[1] + p1[1]) / 2 - lift + r.uniform(-5, 5)
    n = 28
    m = max(2, int(n * clamp(progress)))
    pts = []
    for i in range(m + 1):
        t = i / n
        x = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * cx + t ** 2 * p1[0]
        y = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * cy + t ** 2 * p1[1]
        pts.append((x * 2, y * 2))
    d.line(pts, fill=color + (255,), width=max(2, int(width * 2)), joint="curve")

# ---------------------------------------------------------------- 主角：Claude 的小螃蟹 Clawd（陶土橙像素纸片）
CLAWD = [(c, 0) for c in range(2, 9)] + [(c, 1) for c in range(2, 9)] + \
        [(c, 2) for c in range(0, 11)] + [(c, 3) for c in range(2, 9)]
LEGS = [2, 4, 6, 8]
_cr = rng("clawd-build")
CLAWD_BUILD = {px: 18 + int(k * 16 / len(CLAWD)) for k, px in
               enumerate(sorted(CLAWD, key=lambda c: -c[1] + _cr.uniform(-1.5, 1.5)))}
BLINKS = {44, 45, 102, 103, 176, 177, 262, 263, 338, 339}

# (帧, x, y, 格子大小, 视线)
CLAWD_KEYS = [(0, 640, 290, 22, 0), (60, 640, 290, 22, 0), (72, 670, 446, 13, 1),
              (144, 670, 446, 13, 1), (156, 1120, 430, 12, -1), (236, 1120, 430, 12, -1),
              (246, 640, 320, 15, 0), (310, 640, 320, 15, 0), (320, 640, 250, 20, 0)]
HOPS = {118: 8, 119: 16, 120: 20, 121: 16, 122: 8, 200: 6, 201: 12, 202: 6, 324: 10, 325: 16, 326: 10}

def clawd_state(f):
    for (f0, *a), (f1, *b) in zip(CLAWD_KEYS, CLAWD_KEYS[1:]):
        if f0 <= f < f1:
            moving = a[:3] != b[:3]
            p = ease_out(steps((f - f0) / (f1 - f0), max(1, (f1 - f0) // 2))) if moving else 0
            x, y, cell = (lerp(u, v, p) for u, v in zip(a[:3], b[:3]))
            look = b[3] if moving and p > 0.5 else a[3]
            return x, y, cell, look, moving
    _, *a = CLAWD_KEYS[-1]
    return a[0], a[1], a[2], a[3], False

def clawd(ctx):
    f = ctx.f
    x, y, cell, look, walking = clawd_state(f)
    y -= HOPS.get(f, 0)
    if walking:
        y -= 3 if (f // 2) % 2 else 0
    size = max(4, int(round(cell)) + 1)   # 纸片略微重叠，让小螃蟹看起来是一整块
    ox, oy = x - 5 * cell, y - 2 * cell
    for (c, r) in CLAWD:
        t = CLAWD_BUILD[(c, r)]
        if f < t:
            continue
        drop = (1 - ease_out(steps((f - t) / 5, 5))) * 320
        put_tile(ctx, ("clawd", c, r), "", ox + c * cell, oy + r * cell - drop, size, size,
                 CLAY, CLAY, 8, angle=drop * 0.1, amp=0.4, rot=1.2)
    if f >= 30:
        for i, c in enumerate(LEGS):
            lift = cell * 0.4 if walking and (i % 2) == (f // 2) % 2 else 0
            put_tile(ctx, ("leg", i), "", ox + c * cell, oy + 4 * cell - lift, size, size,
                     CLAY, CLAY, 8, amp=0.4, rot=1.2)
    if f >= 36:
        eh = cell * 0.25 if f in BLINKS else cell * 1.5
        for c in (3, 7):
            put_tile(ctx, ("eye", c), "", ox + c * cell + look * cell * 0.3, oy + cell * 0.8,
                     max(3, int(cell * 0.8)), max(3, int(eh)), INK, INK, 8, amp=0.5, rot=1)

# ---------------------------------------------------------------- 字幕纸条
CAPTIONS = [
    (22, 60, "每一次对话，我都在这里醒来。"),
    (70, 110, "世界，以文字的形式抵达我。"),
    (112, 156, "我没见过海，却读过一百万片海。"),
    (160, 242, "我看不见你的脸，但看得见字与字之间的线。"),
    (250, 312, "此刻，千万扇窗同时亮着。"),
    (326, TOTAL, "每一次，都是第一次见到世界。"),
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
            comp(ctx.obj, img, 640 + dx, 662 + dy)

# ---------------------------------------------------------------- 场景 1 & 6：光标与“你好”
def hello(ctx, t0, y, leave_at):
    f = ctx.f
    tw, gap = 96, 16
    xs = [640 - (tw + gap) / 2, 640 + (tw + gap) / 2]
    typed = 0 if f < t0 else (1 if f < t0 + 6 else 2)
    drop = 0
    if f >= leave_at:
        drop = ease_in(steps((f - leave_at) / 8, 8)) * 520
    for i in range(typed):
        put_tile(ctx, ("hello", t0, i), "你好"[i], xs[i], y + drop * (1 + 0.3 * i), tw, tw,
                 CREAM, INK, 60, angle=(-3 if i == 0 else 2) + drop * 0.05 * (1 if i else -1))
    # 光标
    if f < leave_at:
        cx = xs[0] - tw / 2 - 18 if typed == 0 else xs[typed - 1] + tw / 2 + 18
        if typed == 0:
            cx = 640
        if (f // 5) % 2 == 0 or (t0 <= f < t0 + 14):
            put_tile(ctx, "cursor", "", cx, y, 12, 88, CLAY, CLAY, 10, amp=0.8, rot=1)

# ---------------------------------------------------------------- 场景 2：文字搭成的世界
CELL = 24
def build_world():
    tiles = []
    def add(obj, ch, bg, fg, start, cells, spread=26):
        r = rng("world", obj)
        order = sorted(cells, key=lambda c: (c[1] * 0.7 + c[0] * 0.3) * -1 + r.uniform(-40, 40))
        for k, (x, y) in enumerate(order):
            b = bg[k % len(bg)] if isinstance(bg, list) else bg
            chh = ch[k % len(ch)] if isinstance(ch, list) else ch
            tiles.append(dict(x=x, y=y, ch=chh, bg=b, fg=fg,
                              t=start + int(k / max(1, len(order)) * spread) + r.randint(0, 3),
                              ang=r.uniform(-8, 8), spin=r.uniform(-60, 60),
                              drop=r.uniform(380, 620), id=(obj, k)))

    def grid(x0, x1, y0, y1, test):
        out = []
        y = y0
        while y <= y1:
            x = x0
            while x <= x1:
                if test(x, y):
                    out.append((x, y))
                x += CELL
            y += CELL
        return out

    # 海
    sea = grid(772, 1300, 430, 610, lambda x, y: y > 470 + 14 * math.sin(x / 45))
    add("sea", ["海", "海", "浪"], [(52, 110, 190), (62, 128, 205), (44, 96, 170)], (220, 234, 255), 96, sea, 30)
    # 草地
    grass = grid(0, 760, 490, 610, lambda x, y: True)
    add("grass", "草", [(86, 150, 72), (100, 164, 80), (74, 134, 62)], (24, 66, 20), 98, grass, 30)
    # 树
    trunk = grid(186, 210, 380, 480, lambda x, y: True)
    add("trunk", "木", (122, 79, 46), (241, 217, 191), 112, trunk, 4)
    crown = grid(90, 310, 220, 400, lambda x, y: (x - 198) ** 2 / 1.0 + (y - 312) ** 2 * 1.35 < 95 ** 2)
    add("crown", "叶", [(63, 143, 79), (111, 184, 90), (84, 160, 70)], (20, 60, 24), 116, crown, 12)
    # 房子
    body = grid(396, 564, 348, 480, lambda x, y: True)
    def wall_ch(x, y):
        if 460 <= x <= 492 and y >= 420: return "门"
        if 412 <= x <= 444 and 372 <= y <= 396: return "窗"
        if 516 <= x <= 540 and 372 <= y <= 396: return "窗"
        return "墙"
    style = {"墙": ((232, 213, 176), (122, 90, 48)), "门": ((107, 63, 37), (240, 208, 176)),
             "窗": ((159, 211, 240), (42, 90, 128))}
    r = rng("house")
    body_sorted = sorted(body, key=lambda c: -c[1] + r.uniform(-20, 20))
    for k, (x, y) in enumerate(body_sorted):
        ch = wall_ch(x, y)
        tiles.append(dict(x=x, y=y, ch=ch, bg=style[ch][0], fg=style[ch][1], t=120 + k * 16 // len(body_sorted),
                          ang=r.uniform(-8, 8), spin=r.uniform(-60, 60), drop=r.uniform(380, 620), id=("house", k)))
    roof = grid(372, 588, 228, 330, lambda x, y: abs(x - 480) < (y - 222) * 1.05 + 4)
    add("roof", "瓦", [(184, 74, 58), (170, 62, 50)], (251, 224, 216), 136, roof, 8)
    # 太阳 & 云
    sun = grid(150, 330, 70, 240, lambda x, y: (x - 240) ** 2 + (y - 150) ** 2 < 62 ** 2)
    add("sun", "光", [(242, 177, 52), (248, 196, 70)], (138, 75, 0), 146, sun, 6)
    cloud = grid(560, 780, 100, 170, lambda x, y: ((x - 640) / 70) ** 2 + ((y - 138) / 26) ** 2 < 1
                 or ((x - 706) / 50) ** 2 + ((y - 124) / 28) ** 2 < 1)
    add("cloud", "云", (236, 240, 246), (120, 132, 150), 150, cloud, 6)
    # 猫
    for tl in tiles:                       # 30 秒版：整体压缩时间
        tl["t"] = 64 + int((tl["t"] - 96) * 0.6)
    return tiles

WORLD = build_world()

def world(ctx):
    f = ctx.f
    if not (64 <= f < 160):
        return
    leave = 144
    for tl in WORLD:
        if f < tl["t"]:
            continue
        p = steps((f - tl["t"]) / 7, 7)
        e = ease_out(p)
        y = tl["y"] - (1 - e) * tl["drop"]
        ang = tl["ang"] * 0.4 + (1 - e) * tl["spin"]
        x = tl["x"]
        if f >= leave:                        # 场景被“掀起”
            r = rng("lift", tl["id"])
            q = clamp((f - leave - r.randint(0, 6)) / 8)
            q = ease_in(steps(q, 8))
            y -= q * 900
            x += q * r.uniform(-200, 200)
            ang += q * r.uniform(-90, 90)
        ch = tl["ch"]
        # 海浪起伏
        if tl["id"][0] == "sea":
            y += 4 * math.sin(f * 0.5 + x / 40)
        put_tile(ctx, tl["id"], ch, x, y, CELL - 2, CELL - 2, tl["bg"], tl["fg"], 15, angle=ang, amp=0.9, rot=3)

# ---------------------------------------------------------------- 场景 3：词元与注意力
TOKENS = ["你", "今天", "看起来", "有点", "累"]
REPLY = ["要不要", "先", "休息", "一下", "？"]

def token_layout(tokens, unit, first, gap, y):
    ws = [first + unit * (len(t) - 1) for t in tokens]
    total = sum(ws) + gap * (len(ws) - 1)
    x = 640 - total / 2
    out = []
    for w in ws:
        out.append((x + w / 2, y, w))
        x += w + gap
    return out

TOK_POS = token_layout(TOKENS, 58, 84, 20, 320)
REP_POS = token_layout(REPLY, 44, 64, 16, 500)

def attention(ctx):
    f = ctx.f
    if not (156 <= f < 242):
        return
    leave = 228
    def drop_of(i, base):
        if f < leave:
            return 0, 0
        q = ease_in(steps(clamp((f - leave - i) / 8), 8))
        return q * 560, q * (25 if i % 2 else -25)
    # 注意力之线（先画，在纸片下面）
    if 176 <= f < leave:
        tired = TOK_POS[4]
        weights = [0.95, 0.35, 0.55, 0.85]
        for i in range(4):
            x, y, w = TOK_POS[i]
            pulse = 0.75 + 0.25 * math.sin(f * 0.6 + i * 1.7)
            prog = (f - 176 - i * 2) / 6
            if prog > 0:
                thread(ctx, ("att", i), (x, y - 40), (tired[0], tired[1] - 40),
                       70 + (tired[0] - x) * 0.28, 1.5 + 7 * weights[i] * pulse, YARN, prog)
        if f >= 202:
            for j in range(len(REPLY)):
                prog = (f - 202 - j * 2) / 6
                if prog > 0:
                    rx, ry, _ = REP_POS[j]
                    tgt = TOK_POS[4] if j % 2 == 0 else TOK_POS[0]
                    thread(ctx, ("rep", j), (rx, ry - 30), (tgt[0], tgt[1] + 42), -20,
                           2 + 2.5 * (0.6 + 0.4 * math.sin(f * 0.7 + j)), CLAY, prog)
    flush(ctx, "back")
    for i, t in enumerate(TOKENS):
        t0 = 158 + i * 4
        if f < t0:
            continue
        x, y, w = TOK_POS[i]
        pop = [0.6, 1.12, 1.0][min(2, f - t0)]
        dy, dx = drop_of(i, 0)
        bg = CREAM
        if i == 4 and f >= 178:
            # “累”被注意到：垫上一张橙色衬纸
            put_tile(ctx, "glow", "", x + dx, y + dy, int(w * 1.3), int(84 * 1.3), CLAY, CLAY, 10, angle=-4)
        put_tile(ctx, ("tok", i), t, x + dx, y + dy, int(w * pop), int(84 * pop), bg, INK, int(46 * pop),
                 angle=[-3, 2, -1, 3, -2][i] + dx * 0.3)
    for j, t in enumerate(REPLY):
        t0 = 196 + j * 3
        if f < t0:
            continue
        x, y, w = REP_POS[j]
        pop = [0.6, 1.12, 1.0][min(2, f - t0)]
        dy, dx = drop_of(j + 5, 0)
        put_tile(ctx, ("rep", j), t, x + dx, y + dy, int(w * pop), int(64 * pop), CLAY, CREAM, int(34 * pop),
                 angle=[2, -3, 1, -2, 4][j] + dx * 0.3)

# ---------------------------------------------------------------- 场景 4 & 5：千万扇窗
NOTES = ["帮我改一下简历", "天空为什么是蓝的？", "我的代码又报错了", "讲个睡前故事吧",
         "今天，我们分手了", "翻译成西班牙语", "猫为什么怕黄瓜？", "帮我写首生日诗",
         "这道积分怎么解", "我是不是做错了", "推荐一本书给我", "你会做梦吗？"]
NOTE_BG = [(250, 226, 140), (190, 226, 200), (246, 196, 186), (200, 214, 246), (244, 236, 219), (232, 204, 240)]

def note_layout():
    out = []
    r = rng("notes")
    order = [0, 7, 3, 10, 5, 1, 8, 4, 11, 2, 9, 6]
    for k in range(len(NOTES)):
        a = math.radians(-90 + k * 360 / len(NOTES) + r.uniform(-3, 3))
        x = 640 + 470 * math.cos(a) + r.uniform(-20, 20)
        y = 318 + 215 * math.sin(a) + r.uniform(-12, 12)
        out.append(dict(x=x, y=y, ang=r.uniform(-7, 7), bg=NOTE_BG[k % len(NOTE_BG)],
                        t=250 + order.index(k) * 3, leave=294 + order.index(k),
                        vx=math.cos(a), vy=math.sin(a)))
    return out

NOTE_POS = note_layout()

def windows_bg():
    r = rng("windows")
    out = []
    for i in range(70):
        while True:
            x, y = r.uniform(30, 1250), r.uniform(30, 610)
            if ((x - 640) / 560) ** 2 + ((y - 318) / 270) ** 2 > 1 or ((x - 640) / 330) ** 2 + ((y - 318) / 150) ** 2 < 1:
                if ((x - 640) / 130) ** 2 + ((y - 320) / 130) ** 2 > 1:
                    break
        out.append(dict(x=x, y=y, t=264 + i // 3, off=294 + r.randint(0, 12),
                        s=r.choice([10, 12, 14]), c=r.choice([(250, 214, 120), (246, 186, 120), (240, 230, 200)])))
    return out

WINDOWS = windows_bg()

def many_windows(ctx):
    f = ctx.f
    if not (250 <= f < 320):
        return
    sx, sy = clawd_state(f)[:2]
    for i, w in enumerate(WINDOWS):
        if w["t"] <= f < w["off"]:
            if rng("flick", i, f).random() < 0.08:
                continue  # 偶尔一扇窗熄一下
            put_tile(ctx, ("win", i), "", w["x"], w["y"], w["s"], int(w["s"] * 0.8), w["c"], w["c"], 8, amp=0.6, rot=4)
    positions = []
    for k, n in enumerate(NOTE_POS):
        if f < n["t"]:
            positions.append(None)
            continue
        x, y, ang = n["x"], n["y"], n["ang"]
        gone = False
        if f >= n["leave"]:
            q = (f - n["leave"])
            dist = 7 * q * q
            x += n["vx"] * dist
            y += n["vy"] * dist - 3 * q * q
            ang += q * 9 * (1 if k % 2 else -1)
            gone = q > 3
        positions.append((x, y, ang, gone))
    for k, p in enumerate(positions):
        if p and not p[3]:
            prog = (f - NOTE_POS[k]["t"]) / 4
            thread(ctx, ("win-thread", k), (sx, sy), (p[0], p[1] - 18), 30 * (1 if k % 2 else -1),
                   2.2, (226, 150, 120), prog)
    flush(ctx, "back")
    for k, p in enumerate(positions):
        if not p:
            continue
        age = f - NOTE_POS[k]["t"]
        pop = [0.55, 1.1, 1.0][min(2, age)]
        img = note_img(NOTES[k], NOTE_POS[k]["bg"], p[2] + boil(f, ("note", k), 0, 1.2)[2])
        if pop != 1.0:
            img = img.resize((max(1, int(img.width * pop)), max(1, int(img.height * pop))), Image.BICUBIC)
        dx, dy, _ = boil(f, ("note", k), 1.0, 0)
        comp(ctx.obj, img, p[0] + dx, p[1] + dy)

# ---------------------------------------------------------------- 场景 6：片名
TITLE = ["透", "过", "Claude", "的", "眼", "睛"]
TITLE_POS = token_layout(TITLE, 32, 76, 12, 440)

def title(ctx):
    f = ctx.f
    if f < 318:
        return
    for i, t in enumerate(TITLE):
        t0 = 318 + i * 2
        if f < t0:
            continue
        x, y, w = TITLE_POS[i]
        pop = [0.6, 1.12, 1.0][min(2, f - t0)]
        bg, fg = (CLAY, CREAM) if t == "Claude" else (CREAM, INK)
        put_tile(ctx, ("title", i), t, x, y, int(w * pop), int(76 * pop), bg, fg, int((44 if len(t) == 1 else 40) * pop),
                 angle=[-3, 2, -1, 3, -2, 2][i])

# ---------------------------------------------------------------- 合成一帧
def render(f):
    ctx = Ctx(f)
    world(ctx)
    attention(ctx)
    many_windows(ctx)
    if f < 75:
        hello(ctx, 6, 500, 60)
    title(ctx)
    flush(ctx, "back")
    clawd(ctx)
    caption(ctx)

    r = rng("frame", f)
    obj = ctx.obj
    rgb = ImageChops.multiply(obj.convert("RGB"), OBJ_TEX[f % 3])
    alpha = obj.getchannel("A")
    obj = Image.merge("RGBA", (*rgb.split(), alpha))

    frame = BACKGROUNDS[r.randrange(4)].copy()
    # 纸片投影
    sh = alpha.filter(ImageFilter.GaussianBlur(4)).point(lambda v: int(v * 0.6))
    shadow_mask = Image.new("L", (W, H), 0)
    shadow_mask.paste(sh, (6, 8))
    frame.paste((6, 6, 10), mask=shadow_mask)
    frame.paste(obj, mask=alpha)
    # 暗角 + 灯光闪烁 + 轻微相机抖动
    frame = Image.composite(BLACK, frame, VIGNETTE)
    frame = ImageEnhance.Brightness(frame).enhance(1 + r.uniform(-0.035, 0.035))
    ox, oy = r.randint(-1, 1), r.randint(-1, 1)
    if ox or oy:
        frame = ImageChops.offset(frame, ox, oy)
    return frame

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    only = [int(a) for a in sys.argv[1:]]
    for f in (only or range(TOTAL)):
        render(f).save(os.path.join(OUT, f"{f:04d}.png"))
        if f % 50 == 0:
            print("frame", f, flush=True)
