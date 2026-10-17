# -*- coding: utf-8 -*-
"""
《慢科研倡议》—— 吉伊 / 小八 / 乌萨奇 + 像素 Clawd 的抽象小短剧（竖屏 1080×1920，75 秒，24 fps）

① 天降倡议  ② 作者列表（联名不叫挂名）  ③ 吉伊的慢科研  ④ 隔壁卷王
⑤ 推免面试（零也是一个数量）  ⑥ 灵魂一问（推免截止日期也能慢慢来吗）  片尾

运行：
  python3 slow.py                 → slow_music.wav + 慢科研倡议.mp4
  python3 slow.py still 5 20.5    → previews/ 下导出静帧
  python3 slow.py music           → 只合成配乐
"""
import math, os, sys, random, subprocess
from lib import *
from sprite_buddy import draw_buddy, feature      # 直接用参考图抠出来的角色贴图

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "慢科研倡议.mp4")
WAV = os.path.join(HERE, "slow_music.wav")
DUR = 75.0
GY = 1360            # 室外地面
GYI = 1400           # 室内地面
KB = 0.85            # 角色缩放

S1, S2, S3, S4, S5, S6, SE = 0.0, 6.0, 21.5, 33.0, 40.0, 61.0, 71.0
CUTS = [S2, S3, S4, S5, S6, SE]

PAPER = (255, 250, 236)
PAPER_D = (226, 212, 186)
WOOD = (190, 136, 88)
WOOD_D = (150, 100, 64)
RED = (224, 72, 68)
GOLD = (236, 184, 72)
GRAY_T = (176, 162, 150)
KEY = (206, 210, 220)
HILITE = (255, 222, 80, 120)

POS = {"chii": 300, "hachi": 540, "usagi": 790}


# ================================================================ 台词
# (开始, 结束, 说话者, 文本, 气泡中心, 尾巴指向, 样式)
LINES = [
    (2.4, 4.3, "hachi", "哇！教授们终于懂我们了！", (540, 1030), (540, 1135), "say"),
    (6.2, 8.0, "hachi", "『一篇被你吃透的论文，", (540, 1040), (540, 1135), "say"),
    (8.0, 9.8, "hachi", "远比十篇你只挂了名字的\n论文更有说服力。』", (540, 1020), (540, 1135), "say"),
    (14.8, 16.4, "clawd", "哔。\n（这个author list比我投的论文还长）", (470, 650), (170, 790), "say"),
    (16.5, 18.1, "hachi", "那……挂名的这一百位是？", (600, 500), (640, 600), "say"),
    (18.2, 19.7, "scroll", "这叫联名。不叫挂名。", (540, 520), (540, 400), "chorus"),
    (27.6, 28.8, "chii", "万一第101次不一样呢……", (500, 880), (470, 1000), "think"),
    (30.7, 31.3, "hachi", "恭喜！", (820, 1050), (820, 1130), "say"),
    (35.4, 37.0, "scroll", "灌水式产出，是减分项！", (720, 800), (380, 860), "chorus"),
    (41.9, 43.6, "scroll", "放心，我们不看论文数量。", (650, 470), (800, 640), "chorus"),
    (44.3, 46.2, "scroll", "那么，请介绍一下你的论文。", (650, 470), (800, 640), "chorus"),
    (46.2, 47.4, "chii", "我、我在慢科研……", (330, 1010), (330, 1170), "say"),
    (50.4, 52.0, "scroll", "嗯……我们确实不看数量。", (650, 470), (800, 640), "chorus"),
    (52.0, 54.2, "scroll", "……但是，\n零，它也是一个数量。", (650, 450), (800, 640), "chorus"),
    (55.8, 56.6, "scroll", "下一位。", (620, 470), (800, 640), "chorus"),
    (58.4, 59.0, "scroll", "……", (660, 470), (800, 640), "chorus"),
    (61.2, 63.4, "hachi", "那个……倡议说\n『慢慢来，才能走得远』……", (540, 1010), (540, 1135), "say"),
    (63.6, 65.6, "hachi", "那推免截止日期，\n也能慢慢来吗？", (540, 1010), (540, 1135), "say"),
    (65.8, 66.8, "scroll", "……", (760, 470), (640, 540), "chorus"),
    (69.0, 70.9, "hachi", "……总会有办法的吧？", (520, 1030), (480, 1135), "say"),
]
# 头顶大字（画在角色层，跟镜头一起缩放）
STAMPS = [
    (4.3, 5.8, "呀哈——！", 820, 930, 110, -0.08),
    (13.6, 14.6, "哈？", 900, 540, 110, 0.1),
    (20.5, 21.4, "乌拉！", 900, 470, 110, -0.1),
    (21.6, 22.6, "嗯！", 720, 960, 100, 0.08),
    (32.4, 33.0, "呜……", 600, 960, 80, 0.0),
    (38.0, 39.4, "噗噜噜噜", 330, 1000, 90, -0.06),
    (54.2, 55.8, "呜哇——！！", 360, 1000, 110, 0.0),
    (59.0, 59.6, "哈？", 640, 1000, 100, 0.1),
    (67.2, 68.3, "乌拉——！！", 790, 900, 110, -0.08),
]
PUNCT = set("…，。！？～、 \n（）『』()：:")

def syllables():
    out = []
    for (a, b, who, s, *_r) in LINES:
        chars = [c for c in s if c not in PUNCT and not c.isascii()]
        if not chars:
            continue
        step = min(0.13, (b - a - 0.25) / len(chars))
        for j, c in enumerate(chars):
            out.append((a + 0.06 + step * j, who, j == len(chars) - 1 and "？" in s))
    return out

SYL = syllables()

def talk(who, t):
    m = 0.0
    for (ts, w, _) in SYL:
        if w == who and 0 <= t - ts < 0.12:
            m = max(m, math.sin(math.pi * (t - ts) / 0.12))
    return m


# ================================================================ 小工具
def hop(t, t0, dur, h):
    return -h * arc01((t - t0) / dur) if t0 <= t < t0 + dur else 0.0

def base(kind, x, y, t, face=0.0):
    st = dict(kind=kind, x=x, y=y, k=KB, face=face, t=t)
    br = math.sin(2 * math.pi * 0.8 * t + {"chii": 0, "hachi": 2, "usagi": 4}[kind])
    st["sx"], st["sy"] = 1 + 0.012 * br, 1 - 0.012 * br
    ph = (t + {"chii": 0.3, "hachi": 1.4, "usagi": 2.2}[kind]) % 3.3
    st["eyes"] = "closed" if ph < 0.11 else "dot"
    st["mouth"] = talk(kind, t)
    return st

def walk_to(st, t, t0, t1, x0, x1):
    u = ramp(t, t0, t1)
    st["x"] = lerp(x0, x1, ease_io(u))
    if 0 < u < 1:
        st["walk"], st["step"] = 1.0, (t - t0) * 14
        st["y"] -= abs(math.sin((t - t0) * 14)) * 8
    return st


# ================================================================ 卷轴
SW = 660
ROW0, ROWH = 520, 44
ROD_Y = 380
OFFMAX = ROD_Y + 10 + ROW0 + 100 * ROWH + ROWH / 2 - 790     # 第 101 行停在 y≈790
_CONTENT = None

def _scribble(d, x0, y, w, rnd, amp=8.0):
    f1, ph = rnd.uniform(0.17, 0.3), rnd.uniform(0, 6)
    pts = [(x0 + u + 7 * math.cos(u * f1 + ph), y + amp * math.sin(u * f1 + ph) * (0.6 + 0.4 * math.sin(u * 0.05 + ph)))
           for u in range(0, int(w), 3)]
    d.line(pts, fill=(98, 76, 70), width=2, joint="curve")

def _bars(d, y, n, w=SW):
    for i in range(n):
        d.rounded_rectangle((40, y + i * 30, w - 40 - (90 if i == n - 1 else 0), y + i * 30 + 10), radius=5, fill=(228, 218, 200))

def scroll_content():
    global _CONTENT
    if _CONTENT is None:
        h = ROW0 + 102 * ROWH + 200
        im = Image.new("RGBA", (SW, h), PAPER + (255,))
        d = ImageDraw.Draw(im)
        d.text((SW / 2, 56), "本科生慢科研倡议", font=font(52), fill=INK, anchor="mm")
        _bars(d, 112, 2)
        d.text((40, 186), "一篇被你吃透的论文，", font=font(30), fill=INK)
        d.text((40, 232), "远比十篇你只挂了名字的论文更有说服力。", font=font(30), fill=INK)
        _bars(d, 298, 3)
        d.text((40, 396), "慢慢来，才能走得远。", font=font(30), fill=INK)
        d.text((40, 458), "联合发起人：", font=font(30), fill=INK)
        rnd = random.Random(11)
        for i in range(100):
            y = ROW0 + i * ROWH + ROWH / 2
            d.text((70, y), str(i + 1), font=font(20), fill=GRAY_T, anchor="rm")
            _scribble(d, 96, y, rnd.uniform(120, 170), rnd)
            _scribble(d, 300, y, rnd.uniform(200, 290), rnd, 6)
        _CONTENT = im
    return _CONTENT

def draw_scroll(fr, cx, rod_y, w, L, t, off=0.0, big=True, eyes=False, roll=True, look=0.0):
    d = ImageDraw.Draw(fr, "RGBA")
    x0, x1 = cx - w / 2, cx + w / 2
    if L > 2:
        if big:
            c = scroll_content()
            fr.alpha_composite(c.crop((0, int(off), w, int(off + L))), (int(x0), int(rod_y + 10)))
        else:
            d.rectangle((x0, rod_y + 10, x1, rod_y + 10 + L), fill=PAPER)
            if L > 120:
                d.text((cx, rod_y + 150), "倡议", font=font(int(w * 0.16)), fill=INK, anchor="mm")
                for i in range(int((L - 180) / 34)):
                    yy = rod_y + 200 + i * 34
                    d.rounded_rectangle((x0 + 30, yy, x1 - 30 - (60 if i % 3 == 2 else 0), yy + 10), radius=5, fill=(228, 218, 200))
        d.rectangle((x0, rod_y + 10, x1, rod_y + 10 + L), outline=INK, width=3)
        if roll:
            by = rod_y + 10 + L
            d.rounded_rectangle((x0 - 12, by - 14, x1 + 12, by + 14), radius=14, fill=PAPER_D, outline=INK, width=3)
    d.rounded_rectangle((x0 - 36, rod_y - 16, x1 + 36, rod_y + 16), radius=16, fill=WOOD, outline=INK, width=3)
    for ex in (x0 - 36, x1 + 36):
        d.ellipse((ex - 20, rod_y - 20, ex + 20, rod_y + 20), fill=WOOD_D, outline=INK, width=3)
    if eyes and L > 60:          # 卷轴的小眼睛
        blink = (t * 0.9) % 2.6 < 0.1
        for s in (-1, 1):
            ex, ey = cx + s * w * 0.2 + look * 10, rod_y + 70
            if blink:
                d.line((ex - 10, ey, ex + 10, ey), fill=INK, width=4)
            else:
                d.ellipse((ex - 9, ey - 12, ex + 9, ey + 12), fill=INK)
                d.ellipse((ex - 5, ey - 8, ex, ey - 3), fill=WHITE)

def row101_y():
    return ROD_Y + 10 + ROW0 + 100 * ROWH + ROWH / 2 - OFFMAX

def pile_top(x, Hp):
    u = (x - 540) / 690
    h = Hp * math.sqrt(max(0.0, 1 - u * u))
    h += (14 * math.sin(x * 0.031 + 1) + 9 * math.sin(x * 0.07)) * min(1.0, Hp / 200)
    return GY + 30 - h

def draw_pile(pen, Hp):
    if Hp < 2:
        return
    pts = [(540 - 700 + i * 1400 / 70, pile_top(540 - 700 + i * 1400 / 70, Hp)) for i in range(71)]
    pen.poly(pts + [(1260, H + 40), (-180, H + 40)], fill=PAPER, ol=INK, w=3.5)
    rnd = random.Random(5)
    for j in range(80):
        x = rnd.uniform(0, W)
        v = rnd.uniform(0.05, 0.9)
        top = pile_top(x, Hp)
        y = lerp(H - 40, top + 30, v)
        if y < top + 26:
            continue
        if j % 2:
            a = rnd.uniform(-0.5, 0.5)
            L = rnd.uniform(30, 80)
            pen.line([(x, y), (x + L * math.cos(a), y + L * math.sin(a))], (214, 200, 174), 2.4)
        else:
            pts = [(x + u * 3, y + 6 * math.sin(u * 0.7 + j)) for u in range(14)]
            pen.line(pts, (150, 126, 116), 1.8)

def draw_sheet(pen, x, y, ang, s=1.0):
    ca, sa = math.cos(ang), math.sin(ang)
    pts = [(x + dx * ca - dy * sa, y + dx * sa + dy * ca) for dx, dy in ((-34 * s, -24 * s), (34 * s, -24 * s), (34 * s, 24 * s), (-34 * s, 24 * s))]
    pen.poly(pts, fill=PAPER, ol=INK, w=2.2)


# ================================================================ 道具
def rect_poly(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]

def draw_desk(pen, cx, top, w, ground):
    for s in (-1, 1):
        pen.poly(rect_poly(cx + s * (w / 2 - 30) - 12, top + 10, cx + s * (w / 2 - 30) + 12, ground), fill=WOOD_D, ol=INK, w=3)
    pen.poly(chaikin(rect_poly(cx - w / 2, top, cx + w / 2, top + 30), 1), fill=WOOD, ol=INK, w=3.2)

def draw_book(pen, lay, cx, y):
    for s in (-1, 1):
        pts = [(cx, y - 4), (cx + s * 150, y - 16), (cx + s * 156, y + 70), (cx, y + 80)]
        pen.poly(pts, fill=PAPER, ol=INK, w=3)
        for i in range(4):
            yy = y + 8 + i * 15
            pen.line([(cx + s * 22, yy + 2), (cx + s * 120, yy - 6)], (200, 190, 172), 2.5, caps=False)
    px, py = pen.P(cx + 80, y + 54)
    stamp(lay.img, text_tile("P.1", 48, RED, 4, WHITE), px, py)

def draw_laptop(pen, lay, cx, y, n, t):
    pen.poly(rect_poly(cx - 120, y - 160, cx + 120, y), fill=(70, 74, 92), ol=INK, w=3.2)
    pen.poly(rect_poly(cx - 106, y - 148, cx + 106, y - 12), fill=(36, 40, 56))
    pen.poly([(cx - 140, y), (cx + 140, y), (cx + 160, y + 26), (cx - 160, y + 26)], fill=(186, 190, 204), ol=INK, w=3)
    for (s, yy, sz, col) in ((f"第 {n} 次", y - 110, 76, (200, 230, 210)), ("结果 0.731", y - 46, 64, (255, 226, 120))):
        px, py = pen.P(cx, yy)
        stamp(lay.img, text_tile(s, sz, col), px, py)

def draw_outbox(pen, lay, cx, y):
    pen.poly([(cx - 110, y - 90), (cx + 110, y - 90), (cx + 90, y), (cx - 90, y)], fill=(214, 200, 176), ol=INK, w=3.2)
    for (x0, y0, ang) in ((cx - 100, y - 88, 0.5), (cx + 100, y - 88, math.pi - 0.5)):     # 蜘蛛网
        for r in (24, 44, 64):
            pts = [(x0 + math.cos(ang + a) * r, y0 + math.sin(ang + a) * r) for a in (-0.7, -0.35, 0, 0.35, 0.7)]
            pen.line(pts, (160, 150, 150), 1.6, caps=False)
        for a in (-0.7, 0, 0.7):
            pen.line([(x0, y0), (x0 + math.cos(ang + a) * 70, y0 + math.sin(ang + a) * 70)], (160, 150, 150), 1.6, caps=False)
    px, py = pen.P(cx, y - 44)
    stamp(lay.img, text_tile("产出", 64, INK), px, py)

def draw_keyboard(pen, x, y, ang):
    ca, sa = math.cos(ang), math.sin(ang)
    P = lambda dx, dy: (x + dx * ca - dy * sa, y + dx * sa + dy * ca)
    pen.poly([P(-50, -14), P(50, -14), P(50, 14), P(-50, 14)], fill=KEY, ol=INK, w=2.6)
    for i in range(7):
        for j in range(2):
            px, py = P(-38 + i * 12.6, -5 + j * 10)
            pen.circle(px, py, 2.4, (140, 146, 160))

def draw_printer(pen, x, ground):
    pen.poly(chaikin(rect_poly(x - 90, ground - 140, x + 90, ground), 1), fill=(220, 222, 230), ol=INK, w=3.2)
    pen.poly(rect_poly(x - 60, ground - 110, x + 60, ground - 96), fill=(80, 84, 100))
    pen.circle(x + 62, ground - 40, 7, (120, 220, 140))

def draw_crow(pen, x, y, t):
    flap = math.sin(t * 16) * 0.6
    pen.poly(ell(x, y, 40, 22, 0, 24), fill=(48, 44, 52), ol=INK, w=2)
    pen.poly(ell(x - 38, y - 10, 18, 16, 0, 18), fill=(48, 44, 52))
    pen.poly([(x - 54, y - 12), (x - 74, y - 6), (x - 54, y - 2)], fill=(236, 190, 70))
    for s in (-1, 1):
        pen.poly([(x - 10, y - 6), (x + 20, y - 6), (x + 6 + 10 * s, y - 50 * math.cos(flap) * (1 if s > 0 else 0.7))],
                 fill=(48, 44, 52), ol=INK, w=2)
    pen.circle(x - 42, y - 14, 3, WHITE)

def draw_pencil(pen, x, y, ang):
    ca, sa = math.cos(ang), math.sin(ang)
    P = lambda dx, dy: (x + dx * ca - dy * sa, y + dx * sa + dy * ca)
    pen.poly([P(0, -9), P(120, -9), P(120, 9), P(0, 9)], fill=(250, 210, 80), ol=INK, w=2.6)
    pen.poly([P(0, -9), P(-30, 0), P(0, 9)], fill=(240, 214, 170), ol=INK, w=2.6)
    pen.poly([P(-20, -3), P(-30, 0), P(-20, 3)], fill=INK)
    pen.poly([P(120, -9), P(140, -9), P(140, 9), P(120, 9)], fill=(240, 150, 160), ol=INK, w=2.6)


# ================================================================ 背景
_BG = {}
def meadow():
    if "m" not in _BG:
        _BG["m"] = Meadow(-120, 120, seed=8)
    return _BG["m"]

def room():
    if "r" not in _BG:
        im = Image.new("RGBA", (W, H), (248, 238, 226, 255))
        d = ImageDraw.Draw(im)
        for x in range(0, W, 120):                     # 墙纸竖条
            d.rectangle((x, 0, x + 60, 1180), fill=(244, 232, 218))
        d.rectangle((0, 1180, W, H), fill=(226, 198, 160))
        for y in range(1220, H, 80):
            d.line((0, y, W, y), fill=(206, 176, 138), width=3)
            off = (y // 80) % 2 * 160
            for x in range(off, W, 320):
                d.line((x, y, x, y + 80), fill=(206, 176, 138), width=3)
        d.rectangle((0, 1160, W, 1196), fill=(214, 186, 150), outline=INK, width=3)
        # 盆栽
        d.rounded_rectangle((940, 1250, 1060, 1400), radius=16, fill=(206, 120, 90), outline=INK, width=3)
        for (cx, cy, r) in ((970, 1170, 60), (1030, 1130, 58), (1000, 1080, 50)):
            d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(110, 176, 104), outline=INK, width=3)
        _BG["r"] = im
    return _BG["r"]

def draw_calendar(fr, t):
    d = ImageDraw.Draw(fr, "RGBA")
    x0, y0, x1, y1 = 80, 370, 300, 630
    d.rounded_rectangle((x0, y0, x1, y1), radius=14, fill=WHITE, outline=INK, width=4)
    d.rectangle((x0 + 2, y0 + 2, x1 - 2, y0 + 56), fill=RED)
    for rx in (x0 + 60, x1 - 60):
        d.ellipse((rx - 9, y0 - 14, rx + 9, y0 + 4), fill=(120, 120, 130), outline=INK, width=2)
    if t < S5 + 0.5:
        d.text(((x0 + x1) / 2, 500), "8月", font=font(84), fill=INK, anchor="mm")
        u = ramp(t, S5 + 0.25, S5 + 0.5)
        if u > 0:   # 翻页
            d.rectangle((x0 + 4, y0 + 58, x1 - 4, y0 + 58 + (y1 - y0 - 62) * (1 - u)), fill=(250, 248, 244), outline=INK, width=2)
    else:
        d.text(((x0 + x1) / 2, 480), "9月", font=font(84), fill=INK, anchor="mm")
        d.text(((x0 + x1) / 2, 580), "推免季", font=font(44), fill=RED, anchor="mm")


# ================================================================ 气泡
def bubble_tile(s, style, size=44):
    key = ("bub", s, style, size)
    if key in lib_tiles():
        return lib_tiles()[key]
    lines = s.split("\n")
    f = font(size)
    ws = [f.getbbox(l)[2] - f.getbbox(l)[0] for l in lines]
    lh = int(size * 1.32)
    pw, ph = max(ws) + 76, len(lines) * lh + 46
    im = Image.new("RGBA", (pw + 10, ph + 10), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    bg = (255, 246, 222, 248) if style == "chorus" else (255, 254, 250, 248)
    rad = ph // 2 if style == "think" else 36
    d.rounded_rectangle((5, 5, 5 + pw, 5 + ph), radius=min(rad, ph // 2), fill=bg, outline=INK, width=4)
    for i, l in enumerate(lines):
        cx, cy = 5 + pw / 2, 5 + 23 + (i + 0.5) * lh
        if style == "chorus":       # 一百个声音叠在一起
            for dx, dy, a in ((-5, -3, 80), (5, 3, 80), (3, -5, 60), (-4, 5, 60)):
                d.text((cx + dx, cy + dy), l, font=f, fill=INK + (a,), anchor="mm")
        d.text((cx, cy), l, font=f, fill=INK, anchor="mm")
    lib_tiles()[key] = im
    return im

def lib_tiles():
    import lib
    return lib._TILES

def draw_bubbles(fr, t):
    d = ImageDraw.Draw(fr, "RGBA")
    for (a, b, who, s, (bx, by), (tx, ty), style) in LINES:
        if not a <= t < b:
            continue
        tile = bubble_tile(s, style)
        sc = back_out(ramp(t, a, a + 0.18)) * (1 - ease_io(ramp(t, b - 0.12, b)))
        if sc < 0.03:
            continue
        hw = tile.width * sc / 2
        bx = clamp(bx, 24 + hw, W - 24 - hw)
        if style == "think":
            for j, r in enumerate((16, 11, 7)):
                u = (j + 1) / 4
                x, y = lerp(bx, tx, u + 0.15), lerp(by + tile.height * sc / 2, ty, u + 0.15)
                d.ellipse((x - r * sc, y - r * sc, x + r * sc, y + r * sc), fill=WHITE, outline=INK, width=3)
        else:
            ex = by + (tile.height / 2 - 8) * sc * (1 if ty > by else -1)
            d.polygon([(bx - 22 * sc, ex), (bx + 22 * sc, ex), (lerp(bx, tx, 0.85), lerp(ex, ty, 0.85))],
                      fill=(255, 246, 222) if style == "chorus" else (255, 254, 250), outline=INK, width=4)
        stamp(fr, tile, bx, by, sc)


# ================================================================ 镜头
ZOOMS = [   # (淡入起, 淡入止, 淡出起, 淡出止, 倍数, 焦点 x, 焦点 y)
    (6.0, 6.6, 9.4, 9.9, 1.28, 540, 640),
    (20.7, 20.95, 21.45, 21.5, 1.3, 540, 790),
    (S3 - 0.001, S3, S5 - 0.001, S5, 1.22, 540, 1120),      # ③④ 近一点看桌子
    (S5 - 0.001, S5, S6 - 0.001, S6, 1.12, 560, 1010),     # ⑤ 室内整体近一点
    (S5 - 0.01, S5, 41.2, 41.9, 1.7, 190, 500),
    (52.3, 52.6, 54.1, 54.2, 1.2, 800, 760),
    (54.2, 54.35, 55.6, 55.8, 1.25, 330, 1220),
]
SHAKES = [(10.0, 13.2, 4), (S5 + 0.5, 41.8, 6), (57.2, 57.9, 24), (59.6, 60.0, 6), (66.8, 67.4, 4)]
FOCUS = [(20.5, 21.0, 540, 790), (52.6, 53.4, 800, 760), (54.2, 54.9, 330, 1220)]

def view(t):
    z, fx, fy = 1.0, W / 2, H / 2
    for (a, b, c, d_, zz, x, y) in ZOOMS:
        k = window(t, a, b, c, d_) if b > a else (1 - ease_io(ramp(t, c, d_)) if a <= t < d_ else 0)
        if k > 0:
            z, fx, fy = lerp(z, zz, k), lerp(fx, x, k), lerp(fy, y, k)
    amp = 0.0
    for (a, b, A) in SHAKES:
        if a <= t < b:
            amp = max(amp, A * (1 - ramp(t, a, b)) if A > 10 else A)
    dx, dy = amp * (2 * hsh(int(t * 48), 1) - 1), amp * (2 * hsh(int(t * 48), 2) - 1)
    z = max(z, W / (W - 2 * amp - 2))
    return z, fx, fy, dx, dy

def apply_view(fr, t):
    z, fx, fy, dx, dy = view(t)
    if z < 1.0005:
        return fr
    cw, ch = W / z, H / z
    cx = clamp(clamp(fx, cw / 2, W - cw / 2) + dx, cw / 2, W - cw / 2)
    cy = clamp(clamp(fy, ch / 2, H - ch / 2) + dy, ch / 2, H - ch / 2)
    return fr.resize((W, H), Image.BICUBIC, box=(cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2))

def focus_lines(fr, t):
    for (a, b, cx, cy) in FOCUS:
        if not a <= t < b:
            continue
        k = 1 - ramp(t, b - 0.25, b)
        rnd = random.Random(int(t * 12))
        ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(ov)
        for _ in range(90):
            ang = rnd.uniform(0, 2 * math.pi)
            r0, w, R = rnd.uniform(380, 560), rnd.uniform(3, 10), 1700
            p0 = (cx + math.cos(ang) * r0, cy + math.sin(ang) * r0)
            pl = (cx + math.cos(ang - w / R) * R, cy + math.sin(ang - w / R) * R)
            pr = (cx + math.cos(ang + w / R) * R, cy + math.sin(ang + w / R) * R)
            d.polygon([p0, pl, pr], fill=INK + (int(170 * k),))
        fr.alpha_composite(ov)

def draw_stamps(lay, t):
    for (a, b, s, x, y, size, rot) in STAMPS:
        if a <= t < b:
            sc = back_out(ramp(t, a, a + 0.2)) * (1 - ease_io(ramp(t, b - 0.12, b)))
            wob = rot + 0.06 * math.sin((t - a) * 18) * math.exp(-(t - a) * 3)
            px, py = lay.pen.P(x, y)
            stamp(lay.img, text_tile(s, size * 2, INK, 14, WHITE), px, py, sc, 1.0, wob)


# ================================================================ ① 天降倡议
def scene1(t, fr, lay):
    pen = lay.pen
    rod = lerp(-80, ROD_Y, back_out(ramp(t, 0.6, 1.4), 1.4))
    L = 540 * ease_out(ramp(t, 1.4, 2.2))
    if t > 1.0:                                    # 金光
        a = ramp(t, 1.0, 1.6) * 0.5
        ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(ov)
        for i in range(14):
            ang = t * 0.3 + i * math.pi / 7
            p = [(540, 650), (540 + math.cos(ang - 0.08) * 900, 650 + math.sin(ang - 0.08) * 900),
                 (540 + math.cos(ang + 0.08) * 900, 650 + math.sin(ang + 0.08) * 900)]
            d.polygon(p, fill=(255, 236, 150, int(90 * a)))
        fr.alpha_composite(ov)
    draw_scroll(fr, 540, rod, SW, L, t, roll=True)
    if 0.5 < t < 1.3:
        pen.poly(star4(540, 300, 40 * arc01(ramp(t, 0.5, 1.3)), t), fill=STAR, ol=INK, w=2.5)
    for kind in ("chii", "hachi", "usagi"):
        st = base(kind, POS[kind], GY, t)
        st["rot"] = -0.03 * ease_io(ramp(t, 0.7, 1.2)) * (1 if kind != "usagi" else -1)
        if t > 2.3 and kind == "chii":
            st["eyes"], st["al"], st["ar"] = "sparkle", 0.5, 0.5
        if kind == "hachi" and 2.4 <= t < 4.3:
            st["ar"] = 1.0
            st["eyes"] = "sparkle"
        if kind == "usagi" and 4.3 <= t < 5.8:
            st["y"] += hop(t, 4.3, 0.55, 130)
            st["mouth"], st["al"], st["ar"] = 1.5, 1.3, 1.3
            st["ears"] = 0.25 * math.sin(t * 22)
        draw_buddy(pen, st)

# ================================================================ ② 作者列表
def s2_pile(t):
    return 560 * ease_io(ramp(t, 10.0, 13.2))

def scene2(t, fr, lay):
    pen = lay.pen
    off = OFFMAX * ease_io(ramp(t, 9.8, 13.2))
    L = 540 if t < 9.8 else GY + 40 - ROD_Y - 10
    draw_scroll(fr, 540, ROD_Y, SW, L, t, off=off, roll=t < 9.8)
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    if 6.4 <= t < 9.8:                             # 荧光笔划过引文
        u1 = ease_io(ramp(t, 6.4, 7.6))
        u2 = ease_io(ramp(t, 8.0, 9.3))
        y1 = ROD_Y + 10 + 186
        d.rectangle((540 - SW / 2 + 34, y1 - 2, 540 - SW / 2 + 34 + 300 * u1, y1 + 38), fill=HILITE)
        d.rectangle((540 - SW / 2 + 34, y1 + 44, 540 - SW / 2 + 34 + 575 * u2, y1 + 84), fill=HILITE)
    if t >= 20.1:                                  # 乌萨奇签下第 101 个名字
        y = row101_y()
        u = ramp(t, 20.1, 20.5)
        if t >= 20.7:
            d.rectangle((540 - SW / 2 + 20, y - 22, 540 - SW / 2 + 20 + 480 * ease_io(ramp(t, 20.7, 21.0)), y + 22), fill=HILITE)
        fr.alpha_composite(ov)
        ov = None
        tile = text_tile("101  乌萨奇　本科生", 34, RED)
        cw = int(tile.width * u)
        if cw > 2:
            fr.alpha_composite(tile.crop((0, 0, cw, tile.height)), (int(540 - SW / 2 + 40), int(y - tile.height / 2)))
    if ov is not None:
        fr.alpha_composite(ov)

    Hp = s2_pile(t)
    alarm = t >= 10.0
    for kind in ("chii", "hachi", "usagi"):
        st = base(kind, POS[kind], GY, t)
        if alarm:
            st["eyes"], st["sweat"], st["al"], st["ar"] = "shock", 0.5, 1.2, 1.2
            st["x"] += 3 * math.sin(t * 50)
        draw_buddy(pen, st)

    # 纸片乱飞
    if 9.8 <= t < 13.4:
        for j in range(26):
            p = ((t - 9.8) * 1.3 + j / 26) % 1
            sx = 540 + (hsh(j, 1) - 0.5) * 600
            x = sx + (hsh(j, 2) - 0.5) * 500 * p
            y = 900 + 700 * p * p - 200 * p
            draw_sheet(pen, x, y, p * 6 + j, 0.8)
    draw_pile(pen, Hp)

    # 从纸堆里钻出来
    if t >= 13.5:
        st = base("usagi", 800, pile_top(800, Hp), t)
        st["y"] += hop(t, 13.5, 0.45, 160)
        if 13.6 <= t < 14.6:
            st["mouth"], st["eyes"] = 0.5, "dot"
        if t >= 19.7:     # 拿铅笔跳上去签名
            hy = -110 * ease_out(ramp(t, 19.7, 20.05)) * (1 - ease_io(ramp(t, 20.5, 20.8)))
            st["y"] += hy + (4 * math.sin(t * 60) if 20.05 <= t < 20.5 else 0)
            st["al"] = 0.9
            st["mouth"] = 1.4 if 20.5 <= t < 21.3 else 0.3
            st["ears"] = 0.2 * math.sin(t * 20)
            draw_buddy(pen, st)
        else:
            draw_buddy(pen, st)
    if t >= 14.6:
        y = pile_top(150, Hp) + hop(t, 14.6, 0.4, 120)
        draw_clawd(pen, 150, y, 13, eyes="blink" if 15.8 < t < 15.9 else "open")
    if t >= 16.2:
        st = base("hachi", 640, pile_top(640, Hp), t)
        st["y"] += hop(t, 16.2, 0.42, 140)
        if 16.5 <= t < 18.1:
            st["ar"] = 0.8
        if 18.2 <= t < 19.7:
            st["eyes"] = "blank"
        draw_buddy(pen, st)
    if 18.2 <= t < 19.7:
        pen.poly(teardrop(890, 440, 40, 15, -math.pi / 2), fill=SWEAT, ol=INK, w=2.5)
    if 19.9 <= t < 20.6:                          # 铅笔最后画，别被挡住
        u = ramp(t, 20.1, 20.5)
        draw_pencil(pen, lerp(330, 660, u), row101_y() - 6 + 5 * math.sin(t * 50), -0.8)

# ================================================================ ③ 吉伊的慢科研
SEASONS = [("3月", (255, 214, 226)), ("6月", (255, 236, 160)), ("9月", (250, 196, 130)), ("12月", (236, 244, 255))]

def scene3(t, fr, lay):
    pen = lay.pen
    lt = t - S3
    si = int((t - 22.8) / 0.8) if 22.8 <= t < 26.0 else -1
    if si >= 0:
        ov = Image.new("RGBA", (W, H), SEASONS[si][1] + (70,))
        if si == 3:
            ImageDraw.Draw(ov).rectangle((0, 1150, W, H), fill=(250, 252, 255, 150))
        fr.alpha_composite(ov)
        if si == 1:
            pen.circle(900, 330, 90, (255, 214, 90))
    if t < 26.0:
        cx, chx = 540, 540
    else:
        cx, chx = 540, 440
    st = base("chii", chx, 1268, t)
    if lt < 1.3:
        st["brow"], st["al"] = "angry", 1.2 if lt > 0.1 else 0.0
    elif t < 26.0:
        st["eyes"] = "blank" if (t * 0.5) % 2.0 > 0.1 else "closed"
        if si == 3:
            st["x"] += 2.5 * math.sin(t * 60)
    elif t < 28.8:
        if t >= 27.6:
            st["x"] += 3 * math.sin(t * 55)
            st["sweat"], st["eyes"], st["brow"] = ramp(t, 27.6, 28.8), "shock", "worry"
    else:
        st["eyes"], st["brow"] = ("teary", "worry")
        st["gloom"] = ramp(t, 29.0, 29.5)
        if t >= 31.3:
            st["al"] = st["ar"] = 0.9
        if t >= 32.4:
            st["eyes"], st["tears"], st["mouth"] = "cry", 0.6, 0.5
    draw_buddy(pen, st)
    draw_desk(pen, cx, 1250, 520, GY)
    if t < 26.0:
        draw_book(pen, lay, cx, 1196)
    elif t < 28.8:
        n = 1 + int(99 * ease_io(ramp(t, 26.2, 27.6)))
        draw_laptop(pen, lay, 700, 1250, n, t)
    else:
        draw_outbox(pen, lay, 700, 1250)
        if t >= 31.3:
            draw_sheet(pen, 440, 1190, 0.0, 1.6)
    if si == 0:
        for j in range(18):
            p = ((t - 22.8) * 0.7 + j / 18) % 1
            pen.poly(ell(hsh(j, 3) * W + 60 * math.sin(p * 6 + j), p * 1500 + 300, 9, 5, p * 8, 12), fill=(248, 182, 202))
    if si == 2:
        for j in range(16):
            p = ((t - 24.4) * 0.7 + j / 16) % 1
            pen.poly(ell(hsh(j, 4) * W + 80 * math.sin(p * 5 + j), p * 1500 + 300, 13, 6, p * 7, 14), fill=(236, 142, 70), ol=INK, w=1.5)
    if si == 3:
        for j in range(40):
            p = ((t - 25.2) * 0.4 + j / 40) % 1
            pen.circle(hsh(j, 5) * W + 30 * math.sin(p * 8 + j), p * 1600 + 280, 5 + 3 * hsh(j, 6), WHITE)
    # 小八拿着奖状走进来
    if t >= 29.8:
        hs = base("hachi", 1200, GY, t, face=-0.6)
        walk_to(hs, t, 29.8, 30.6, 1200, 820)
        hs["al"] = 0.7 if t < 31.3 else 0.2
        if 30.6 <= t < 31.3:
            hs["eyes"] = "happy"
        draw_buddy(pen, hs)
        if t < 31.3:
            draw_sheet(pen, hs["x"] - 110, hs["y"] - 110, -0.2, 1.1)

# ================================================================ ④ 隔壁卷王
def s4_count(t):
    n = sum(1 for k in range(47) if t >= 33.3 + k * 0.047 + 0.5)
    return n - (1 if t >= 38.4 else 0)

def scene4(t, fr, lay):
    pen = lay.pen
    draw_printer(pen, 900, GY)
    landed = sum(1 for k in range(47) if t >= 33.3 + k * 0.047 + 0.5)
    shown = landed - (1 if t >= 38.0 else 0)
    for i in range(shown):                         # 论文堆
        y = GY - 8 - i * 6.5
        pen.poly(rect_poly(170 - 70 + 4 * math.sin(i * 1.7), y - 6, 170 + 70 + 4 * math.sin(i * 1.7), y), fill=PAPER, ol=INK, w=1.6)
    for k in range(47):                            # 打印机喷论文
        u = (t - 33.3 - k * 0.047) / 0.5
        if 0 <= u < 1:
            x = lerp(900, 170, u)
            y = lerp(GY - 110, GY - 10 - landed * 6.5, u) - 380 * arc01(u)
            draw_sheet(pen, x, y, u * 9 + k, 0.8)
    draw_desk(pen, 540, 1250, 460, GY)
    kb = [(370, 1236, -0.25), (390, 1205, -0.1), (350, 1176, 0.15), (380, 1148, -0.3),
          (710, 1236, 0.25), (690, 1205, 0.1), (730, 1176, -0.15), (700, 1148, 0.3)]
    for (x, y, a) in kb:
        draw_keyboard(pen, x, y + (3 * math.sin(t * 40 + x) if t < 35.6 else 0), a)
    typing = t < 35.6
    draw_clawd(pen, 540, 1252, 13, eyes="blink" if 39.0 < t < 39.12 else "open", step=int(t * 20) % 2 if typing else None)
    if typing:                                     # 手速快到出残影
        s = pen.s
        for j in range(3):
            off = (int(t * 24) + j) % 3
            for side in (-1, 1):
                x0 = 540 + side * (8 * 13 + 10 + off * 18)
                pen.d.rectangle((round((x0 - 13) * s), round((1252 - 13 * 5 - pen.oy) * s),
                                 round((x0 + 13) * s), round((1252 - 13 * 3 - pen.oy) * s)), fill=CLAWD + (120,))
    if 35.4 <= t < 37.2:
        fr_scroll.append((250, 840, 240, 200, t))
    # 乌萨奇冲过来叼走一篇
    if t >= 37.0:
        st = base("usagi", -150, GY, t)
        u = ramp(t, 37.0, 37.8)
        st["x"] = lerp(-150, 300, ease_out(u))
        if u < 1:
            st["walk"], st["step"] = 1.0, t * 30
            for j in range(4):
                pen.line([(st["x"] - 130 - 40 * j, GY - 120 - 40 * j), (st["x"] - 260 - 40 * j, GY - 120 - 40 * j)], INK, 3)
        if t >= 38.0:
            st["mouth"] = 0.6 * abs(math.sin(t * 22))
            st["eyes"] = "happy"
        draw_buddy(pen, st)
        if t >= 38.0:
            px, py = feature(st, "mouth")
            draw_sheet(pen, px, py + 6, 0.15 * math.sin(t * 22), 0.9)

fr_scroll = []

# ================================================================ ⑤ 推免面试
def scene5(t, fr, lay):
    pen = lay.pen
    draw_calendar(fr, t)
    talking = any(a <= t < b and who == "scroll" for (a, b, who, *_r) in LINES)
    bob = 6 * math.sin(t * 14) if talking else 0
    look = -1.0 if 56.6 <= t < 59.6 else 0.0
    draw_scroll(fr, 830, 610 + bob, 320, 560, t, big=False, eyes=True, roll=False, look=look)
    d = ImageDraw.Draw(fr)                          # 面试桌
    d.rectangle((610, 1150, 1060, 1186), fill=WOOD, outline=INK, width=4)
    d.rectangle((630, 1186, 1040, GYI + 10), fill=WOOD_D, outline=INK, width=4)
    d.rectangle((660, 1220, 1010, 1330), outline=(124, 82, 52), width=4)
    d.text((835, 1275), "评审席", font=font(52), fill=(255, 236, 200), anchor="mm")
    # 吉伊
    st = base("chii", 330, GYI, t, face=0.3)
    if t < 41.9:
        st["eyes"], st["sweat"] = "shock", ramp(t, S5 + 0.5, 41.8)
    elif 43.6 <= t < 44.3:
        st["eyes"], st["mouth"] = "happy", 0.2
    elif 46.2 <= t < 50.4:
        st["eyes"], st["sweat"] = ("shock", ramp(t, 46.2, 48.0))
    elif 50.4 <= t < 54.2:
        st["eyes"] = "blank"
    elif 54.2 <= t < 55.8:
        st["eyes"], st["mouth"], st["fountain"], st["tears"] = "cry", 1.0, True, 1.0
        st["y"] += 6 * math.sin(t * 40)
    elif t >= 55.8:
        walk_to(st, t, 55.8, 56.5, 330, 120)
        st["eyes"], st["tears"], st["mouth"] = "cry", 0.8, 0.4
    if 43.6 <= t < 44.3:
        u = ramp(t, 43.6, 44.3)
        pen.circle(330 + 90 + 60 * u, GYI - 150 - 20 * u, 18 + 14 * u, (240, 240, 250, int(200 * (1 - u))))
    if 46.6 <= t < 47.6:
        st["ar"] = 1.0
    draw_buddy(pen, st)
    # Clawd 扛着论文塔进门
    if t >= 56.6:
        x = lerp(-200, 360, ease_out(ramp(t, 56.6, 57.2)))
        top = GYI - 7 * 13
        n = int(top / 8) + 4
        for i in range(n):
            y = top - i * 8
            wob = math.sin(i * 0.08 + t * 3) * 14 * (i / n) * (1 if t < 57.2 else math.exp(-(t - 57.2) * 2))
            pen.poly(rect_poly(x - 80 + wob, y - 8, x + 80 + wob, y), fill=PAPER, ol=INK, w=1.4)
        draw_clawd(pen, x, GYI, 13, step=int(t * 10) % 2 if t < 57.2 else None)
        if 57.2 <= t < 58.0:
            u = ramp(t, 57.2, 58.0)
            for j in range(6):
                pen.circle(x - 120 + 48 * j, 40 + 60 * u, 30 + 30 * u, (250, 246, 236, int(220 * (1 - u))))
    # 乌萨奇举着「呀哈」简历
    if t >= 57.6:
        us = base("usagi", -200, GYI, t)
        walk_to(us, t, 57.6, 58.2, -200, 600)
        us["al"] = us["ar"] = 1.3
        if t >= 59.0:
            us["mouth"] = 0.5
        draw_buddy(pen, us)
        px, py = feature(us, "top")
        py -= 210
        pen.poly(rect_poly(px - 130, py - 85, px + 130, py + 85), fill=WHITE, ol=INK, w=3)
        sx, sy = pen.P(px, py)
        stamp(lay.img, text_tile("呀哈", 150, INK), sx, sy)
    if 49.0 <= t < 50.6:
        draw_crow(pen, lerp(1250, -200, ramp(t, 49.0, 50.6)), 540, t)
    if 49.4 <= t < 50.2:
        sx, sy = pen.P(lerp(1250, -200, ramp(t, 49.0, 50.6)) + 40, 440)
        stamp(lay.img, text_tile("嘎", 120, INK, 10, WHITE), sx, sy)

# ================================================================ ⑥ 灵魂一问
def scene6(t, fr, lay):
    pen = lay.pen
    bob = 10 * math.sin(t * 1.6)
    if t < 66.8:
        draw_scroll(fr, 540, 520 + bob, 340, 300, t, big=False, eyes=True, roll=True,
                    look=0.8 * math.sin(t * 6) if t >= 65.8 else 0)
        if t >= 65.8:
            pen.poly(teardrop(760, 560, 46, 17, -math.pi / 2), fill=SWEAT, ol=INK, w=2.5)
    else:
        L = 300 * (1 - ease_io(ramp(t, 66.8, 67.1)))
        y = lerp(520 + bob, -400, ease_io(ramp(t, 67.1, 67.5)))
        if y > -60:
            draw_scroll(fr, 540, y, 340, L, t, big=False, eyes=True, roll=L > 10)
        if 67.1 <= t < 67.6:
            for j in range(5):
                pen.line([(400 + 70 * j, y + 120 + 30 * j), (400 + 70 * j, y + 360 + 30 * j)], INK, 3)
    if 67.6 <= t < 68.3:
        pen.poly(star4(540, 140, 34 * arc01(ramp(t, 67.6, 68.3)), t * 2), fill=STAR, ol=INK, w=2.5)
    cs = base("chii", 280, GY, t)
    if 63.6 <= t < 65.8:
        cs["eyes"] = "dot"
    if t >= 68.2:
        cs["eyes"], cs["tears"], cs["mouth"] = "cry", 1.0, 0.5 + 0.2 * math.sin(t * 9)
    hs = base("hachi", 540, GY, t)
    if 61.0 <= t < 65.6:
        hs["ar"] = 1.4 if t < 61.8 else 1.0
    if 65.8 <= t < 68.2:
        hs["eyes"] = "blank"
    if t >= 68.2:
        walk_to(hs, t, 68.2, 68.9, 540, 480)
        hs["face"] = -0.6
        if t >= 68.9:
            hs["al"] = 1.05 + 0.18 * math.sin(t * 12)
    us = base("usagi", 790, GY, t)
    if t >= 67.2:
        us["y"] -= 2600 * ease_io(ramp(t, 67.35, 68.1)) ** 2
        us["mouth"], us["al"], us["ar"] = 1.5, 1.3, 1.3
        us["ears"] = 0.3 * math.sin(t * 24)
    for st in (cs, hs, us):
        draw_buddy(pen, st)
    if t >= 68.2:
        for j in range(8):
            p = ((t - 68.2) * 0.5 + j / 8) % 1
            pen.poly(ell(1150 - p * 1300, 1000 + 200 * hsh(j, 7) + 40 * math.sin(p * 9 + j), 12, 5, p * 9, 14),
                     fill=(150, 200, 110), ol=INK, w=1.5)

# ================================================================ 片尾
def endcard(t):
    if "end" not in _BG:
        bg = meadow().compose(0, SE)
        meadow().foreground(bg, 0)
        bg = bg.filter(ImageFilter.GaussianBlur(5))
        bg.alpha_composite(Image.new("RGBA", (W, H), (255, 252, 244, 60)))
        _BG["end"] = bg
    fr = _BG["end"].copy()
    lay = Layer(780, 1420)
    te = t - SE
    beat = 60 / 120
    for j, (kind, x) in enumerate((("chii", 200), ("hachi", 420), ("usagi", 650))):
        st = base(kind, x, 1330, t)
        st["y"] += -26 * arc01(((te + j * beat / 3) % beat) / beat)
        st["eyes"] = "happy" if kind != "chii" else "teary"
        draw_buddy(lay.pen, st)
    hy = 30 * arc01(((te + 0.25) % beat) / beat)
    draw_clawd(lay.pen, 880, 1330 - hy, 12)
    lay.onto(fr)
    fr = grain(fr.convert("RGB"), t).convert("RGBA")
    stamp(fr, text_tile("你觉得本科生", 92, (255, 233, 150), 8, INK), W / 2, 420, back_out(ramp(te, 0.3, 0.7)))
    stamp(fr, text_tile("慢得起来吗？", 92, (255, 233, 150), 8, INK), W / 2, 540, back_out(ramp(te, 0.5, 0.9)))
    stamp(fr, pill_tile("评论区聊聊～", 54), W / 2, 680, back_out(ramp(te, 0.9, 1.3)))
    stamp(fr, pill_tile("点个关注", 56), W / 2, 1480, back_out(ramp(te, 1.3, 1.7)))
    return fr

# ================================================================ 叠加层（不随镜头缩放）
def overlays(fr, t):
    if 0.3 <= t < SE:
        stamp(fr, pill_tile("教授喊你慢下来，然后呢？", 44, bg=(255, 236, 160, 240)), W / 2, 200, back_out(ramp(t, 0.3, 0.6)))
    if 9.6 <= t < S3:
        n = 101 if t >= 20.7 else int(round(100 * ease_io(ramp(t, 9.8, 13.0))))
        sc = 1 + 0.25 * arc01(ramp(t, 20.7, 21.0))
        stamp(fr, pill_tile(f"联合发起人：{n} 位", 46, bg=(255, 253, 246, 240), fg=RED if n > 100 else INK), W / 2, 300, sc)
    banners = [(22.8, 26.0, "倡议①：读透经典工作"), (26.0, 28.8, "倡议②：反复验证与怀疑"),
               (28.8, 31.3, "倡议③：忍受长期的“没有产出”")]
    for (a, b, s) in banners:
        if a <= t < b:
            stamp(fr, pill_tile(s, 46), W / 2, 360, back_out(ramp(t, a, a + 0.25)))
    if 22.8 <= t < 26.0:
        si = int((t - 22.8) / 0.8)
        stamp(fr, pill_tile(SEASONS[si][0], 50, bg=(255, 255, 255, 230)), W / 2, 470, back_out(ramp(t, 22.8 + si * 0.8, 23.0 + si * 0.8)))
    if S4 + 0.2 <= t < S5:
        n = s4_count(t)
        sc = 1 + 0.2 * arc01(ramp(t, 38.4, 38.7))
        stamp(fr, pill_tile(f"本学期：{n} 篇", 54), W / 2, 360, sc)
        if 38.4 <= t < 39.4:
            stamp(fr, text_tile("-1", 90, RED, 7, WHITE), 830, 330, back_out(ramp(t, 38.4, 38.6)))
        if 38.6 <= t < S5:
            stamp(fr, pill_tile("（减分完成）", 46), W / 2, 480, back_out(ramp(t, 38.6, 38.9)))
    if S5 + 0.5 <= t < 41.8:                       # 推免季警报
        a = 0.5 + 0.5 * math.sin((t - S5) * 18)
        fr.alpha_composite(Image.new("RGBA", (W, H), (230, 40, 40, int(70 * a))))
        stamp(fr, text_tile("推免季！！", 130, RED, 10, WHITE), W / 2 + 6 * math.sin(t * 50), 960, back_out(ramp(t, S5 + 0.5, S5 + 0.8)))
    if 31.3 <= t < 32.5:                            # 奖状
        draw_doc(fr, t, 31.3, 32.5, "奖  状", [("慢科研认证", 76, INK), ("零产出", 110, RED)], seal=True)
    if 47.4 <= t < 49.2:                            # 简历
        draw_doc(fr, t, 47.4, 49.2, "个人简历", [("姓名：吉伊", 50, INK), ("", 260, INK),
                                                ("科研成果：已读懂经典工作 1 篇", 30, GRAY_T)])
    if 59.6 <= t < S6:                              # 计分板
        u = back_out(ramp(t, 59.6, 59.9))
        board = Image.new("RGBA", (900, 520), (0, 0, 0, 0))
        d = ImageDraw.Draw(board)
        d.rounded_rectangle((4, 4, 896, 516), radius=36, fill=(44, 48, 74, 245), outline=INK, width=5)
        d.text((450, 70), "推免计分板", font=font(56), fill=(255, 233, 150), anchor="mm")
        for j, (name, score) in enumerate((("吉伊", "0"), ("Clawd", "46"), ("乌萨奇", "呀哈"))):
            x = 150 + j * 300
            d.text((x, 200), name, font=font(50), fill=WHITE, anchor="mm")
            d.text((x, 340), score, font=font(110 if j < 2 else 80), fill=(255, 210, 90) if j else (255, 140, 140), anchor="mm")
        d.line((300, 150, 300, 460), fill=(90, 96, 130), width=3)
        d.line((600, 150, 600, 460), fill=(90, 96, 130), width=3)
        stamp(fr, board, W / 2, 900, u)

def draw_doc(fr, t, a, b, title, rows, seal=False):
    y = lerp(H + 500, 960, ease_out(ramp(t, a, a + 0.3))) + lerp(0, H, ease_io(ramp(t, b - 0.25, b)))
    im = Image.new("RGBA", (640, 860), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((4, 4, 636, 856), radius=20, fill=(255, 252, 240), outline=INK, width=5)
    if seal:
        d.rounded_rectangle((26, 26, 614, 834), radius=14, outline=GOLD, width=8)
    d.text((320, 120), title, font=font(80), fill=INK, anchor="mm")
    yy = 260
    for (s, size, col) in rows:
        if s:
            d.text((320, yy + size / 2), s, font=font(size), fill=col, anchor="mm")
        yy += size + 50
    if seal:
        d.ellipse((410, 610, 590, 790), outline=RED, width=8)
        d.text((500, 700), "倡议", font=font(52), fill=RED, anchor="mm")
    stamp(fr, im, W / 2, y, 1.0, 1.0, -0.03)


# ================================================================ 一帧
SCENES = [(S1, scene1, "m"), (S2, scene2, "m"), (S3, scene3, "m"), (S4, scene4, "m"), (S5, scene5, "r"), (S6, scene6, "m")]

def draw_frame(t, clean=False):
    """clean=True：不画字幕气泡、头顶大字和叠加层（做封面用）"""
    if t >= SE:
        fr = endcard(t)
        fr = fr.convert("RGB")
    else:
        sc = [s for s in SCENES if t >= s[0]][-1]
        global KB
        KB = 1.08 if sc[1] is scene5 else 0.85
        fr = (meadow().compose(0, t) if sc[2] == "m" else room().copy())
        lay = Layer(0, H)
        fr_scroll.clear()
        sc[1](t, fr, lay)
        for (cx, ry, w, L, tt) in fr_scroll:          # 浮在空中的小卷轴（先画在背景上）
            draw_scroll(fr, cx, ry + 8 * math.sin(tt * 3), w, L, tt, big=False, eyes=True)
        if not clean:
            draw_stamps(lay, t)
        lay.onto(fr)
        if sc[2] == "m":
            meadow().foreground(fr, 0)
        if not clean:
            draw_bubbles(fr, t)
        fr = apply_view(fr, t)
        focus_lines(fr, t)
        fr = grain(fr.convert("RGB"), t).convert("RGBA")
        if not clean:
            overlays(fr, t)
        fr = fr.convert("RGB")
    for c in CUTS:                                   # 转场：一闪
        k = 1 - abs(t - c) / 0.08
        if k > 0:
            fr = Image.blend(fr, Image.new("RGB", (W, H), CREAM), 0.7 * k)
    fade = 1 - ramp(t, DUR - 0.5, DUR)
    if fade < 1:
        fr = Image.blend(Image.new("RGB", (W, H), CREAM), fr, fade)
    return fr


# ================================================================ 配乐
THEME = [("E5", 1), ("G5", 1), ("C6", 1), ("G5", 1), ("A5", 1), ("G5", 1), ("E5", 2),
         ("F5", 1), ("E5", 1), ("D5", 1), ("E5", 1), ("C5", 4),
         ("E5", 1), ("G5", 1), ("C6", 1), ("D6", 1), ("E6", 1), ("D6", 1), ("C6", 1), ("A5", 1),
         ("G5", 1), ("E5", 1), ("D5", 1), ("G5", 1), ("C5", 4)]
CHORDS = ["C", "C", "F", "G", "C", "Am", "F", "C"]
CHORD = {"C": ["E4", "G4", "C5"], "F": ["F4", "A4", "C5"], "G": ["D4", "G4", "B4"], "Am": ["E4", "A4", "C5"]}
ROOT = {"C": "C2", "F": "F2", "G": "G2", "Am": "A2"}

def play_theme(mx, t0, t1, bpm=120, full=True, gain=1.0):
    beat = 60 / bpm
    loop = 16 * beat
    k = 0
    while t0 + k * loop < t1:
        base_t = t0 + k * loop
        tt = base_t
        for n, d in THEME:
            if tt >= t1:
                break
            mx.add(tt, marimba(note_freq(n), 0.8), 0.22 * gain, 0.1, cut=t1)
            tt += d * beat / 2
        for h, ch in enumerate(CHORDS):
            hb = base_t + h * 2 * beat
            if hb >= t1:
                break
            mx.add(hb, bass(note_freq(ROOT[ch]), 0.45), 0.28 * gain, -0.1, cut=t1)
            for q, nn in enumerate(CHORD[ch]):
                mx.add(hb + beat + q * 0.012, celesta(note_freq(nn), 0.45), 0.045 * gain, -0.3, cut=t1)
        if full:
            for e in range(32):
                te = base_t + e * beat / 2
                if te < t1:
                    mx.add(te, noise(0.05, 0.9, 0.35, seed=e, attack=0.002), (0.028 if e % 2 else 0.016) * gain, 0.4)
        k += 1

def trombone(f, dur, vib=0.0):
    """悲伤长号：锯齿味的谐波 + 末尾颤音"""
    def mk():
        n = int(dur * SR)
        ph, out = 0.0, []
        for i in range(n):
            tt = i / SR
            ff = f * (1 + vib * 0.03 * math.sin(2 * math.pi * 6 * tt) * min(1, tt / 0.3))
            ph += 2 * math.pi * ff / SR
            v = sum(math.sin(h * ph) / h for h in range(1, 7))
            out.append(0.5 * v * min(1, tt / 0.04) * min(1, (dur - tt) / 0.08))
        return out
    return lib_cached(("trb", f, dur, vib), mk)

def lib_cached(key, fn):
    import lib
    return lib._cached(key, fn)

def trill(f, dur, rate=28):
    n = int(dur * SR)
    return [math.sin(2 * math.pi * f * i / SR) * (0.5 + 0.5 * math.sin(2 * math.pi * rate * i / SR)) * min(1, (n - i) / 2000)
            for i in range(n)]

VOICE = {"chii": (1700, 0.14), "hachi": (1250, 0.16), "usagi": (1900, 0.18)}

def make_music(path):
    mx = Mix(DUR)
    rnd = random.Random(3)
    mx.add(0.0, noise(DUR, 0.03, 0.004, seed=99, attack=0.5), 0.28, 0.0)        # 微风底噪

    # ① 天降倡议
    play_theme(mx, 0.0, 9.8, full=False, gain=0.8)
    mx.add(0.6, celesta(note_freq("E6"), 1.2), 0.1, 0.0)
    mx.add(0.75, celesta(note_freq("B6"), 1.2), 0.08, 0.0)
    for j, n in enumerate(("C5", "E5", "G5", "C6", "E6", "G6")):           # 圣光
        mx.add(1.4 + 0.06 * j, celesta(note_freq(n), 1.4), 0.07, 0.0)
    mx.add(1.4, sweep(90, 60, 0.3, 10, harm=0.4), 0.3, 0.0)
    mx.add(1.4, noise(0.8, 0.4, 0.06, seed=4, grains=40, attack=0.02), 0.12, 0.0)
    # ② 纸张雪崩
    mx.add(9.8, noise(3.5, 0.5, 0.08, seed=5, grains=60, attack=0.1), 0.35, 0.0)
    for j in range(40):
        mx.add(9.8 + j * 0.08, celesta(note_freq("C5") * 2 ** ((j % 14) / 12 * 2), 0.3), 0.04, -0.4 + 0.02 * j)
    for j in range(100):
        mx.add(9.8 + 3.2 * ease_io(j / 100), sweep(1600, 1600, 0.02, 0, square=True), 0.02, 0.0)
    for (tp, f0) in ((13.5, 400), (14.6, 520), (16.2, 460)):
        mx.add(tp, sweep(f0, f0 * 3, 0.13, 10, square=True), 0.12, 0.0)
        mx.add(tp, noise(0.3, 0.6, 0.1, seed=int(tp * 10), attack=0.003), 0.12, 0.0)
    mx.add(14.8, sweep(880, 880, 0.3, 0, square=True), 0.08, -0.3)
    for j in range(6):                                # 签名沙沙 + 乌拉
        mx.add(20.05 + 0.07 * j, noise(0.06, 0.7, 0.2, seed=40 + j, attack=0.002), 0.12, 0.2)
    mx.add(20.7, celesta(note_freq("C6"), 1.0), 0.1, 0.0)
    mx.add(20.78, celesta(note_freq("G6"), 1.0), 0.1, 0.0)
    # ③ 吉伊的慢科研
    play_theme(mx, 21.5, 27.6, bpm=96, gain=0.8)
    mx.add(21.6, sweep(500, 900, 0.12, 8, harm=0.3), 0.15, 0.0)
    for j in range(4):
        mx.add(22.8 + 0.8 * j, celesta(note_freq(("C6", "E6", "G5", "C5")[j]), 0.9), 0.08, 0.0)
    for j in range(6):
        mx.add(23.6 + j * 0.12, chirp(4200, 0.08, 1.05, 0.95), 0.03, 0.5)          # 知了
    for j in range(60):
        mx.add(26.2 + 1.4 * ease_io(j / 60), sweep(1200, 1200, 0.015, 0, square=True), 0.025, 0.3)
    for j, n in enumerate(("E5", "C5", "A4", "F4")):                           # 零产出
        mx.add(28.9 + 0.5 * j, celesta(note_freq(n), 1.2), 0.07, 0.0)
    for j, n in enumerate(("C5", "E5", "G5", "C6")):                           # 恭喜
        mx.add(30.7 + 0.07 * j, celesta(note_freq(n), 0.8), 0.08, 0.2)
    # ④ 隔壁卷王
    play_theme(mx, S4, 38.0, bpm=200, gain=0.9)
    for k in range(47):
        mx.add(33.3 + k * 0.047, sweep(700, 300, 0.05, 20, square=True), 0.03, 0.4)
    for j in range(int(2.3 * 30)):
        mx.add(S4 + j / 30, noise(0.015, 0.9, 0.4, seed=200 + j, attack=0.001), 0.06, rnd.uniform(-0.3, 0.3))
    mx.add(37.0, noise(0.6, 0.3, 0.05, seed=77, attack=0.05), 0.12, -0.4)
    mx.add(38.0, trill(500, 1.3), 0.12, -0.3)
    mx.add(38.4, sweep(600, 300, 0.2, 6, square=True), 0.1, 0.3)
    # ⑤ 推免面试
    for j in range(3):
        mx.add(S5 + 0.5 + j * 0.44, sweep(620, 940, 0.22, 0, square=True), 0.1, 0.0)
        mx.add(S5 + 0.72 + j * 0.44, sweep(940, 620, 0.22, 0, square=True), 0.1, 0.0)
    mx.add(S5 + 0.25, noise(0.25, 0.4, 0.06, seed=88, attack=0.02), 0.1, -0.5)
    for j in range(int((54.2 - 41.9) / 0.62)):                                 # 心跳
        mx.add(41.9 + j * 0.62, sweep(70, 50, 0.18, 14, harm=0.3), 0.22, 0.0)
        mx.add(41.9 + j * 0.62 + 0.16, sweep(66, 48, 0.14, 16, harm=0.3), 0.14, 0.0)
    mx.add(43.7, noise(0.5, 0.2, 0.05, seed=90, attack=0.1), 0.08, -0.3)
    mx.add(47.4, noise(0.3, 0.5, 0.08, seed=91, attack=0.02), 0.1, 0.0)
    mx.add(49.4, sweep(700, 520, 0.25, 6, harm=0.6), 0.12, 0.3)
    mx.add(49.65, sweep(680, 500, 0.25, 6, harm=0.6), 0.1, 0.1)
    mx.add(52.6, sweep(120, 40, 0.9, 3, harm=0.4), 0.45, 0.0)
    for j, (n, d) in enumerate((("Bb3", 0.42), ("A3", 0.42), ("Ab3", 0.42), ("G3", 1.3))):   # 悲伤长号
        mx.add(54.2 + 0.45 * j, trombone(note_freq(n), d, vib=1.0 if j == 3 else 0.0), 0.12, 0.0)
    for j in range(6):
        mx.add(56.6 + j * 0.1, sweep(300, 300, 0.05, 20, square=True), 0.05, -0.5)
    mx.add(57.2, sweep(110, 34, 1.0, 3.2, harm=0.45), 0.6, 0.0)
    mx.add(57.2, noise(0.9, 0.07, 0.004, seed=56, attack=0.002), 0.9, 0.0)
    for j, n in enumerate(("C5", "E5", "G5", "C6", "E6")):                   # 计分板
        mx.add(59.6 + 0.06 * j, celesta(note_freq(n), 1.0), 0.08, 0.0)
    mx.add(59.6, sweep(200, 100, 0.3, 8, harm=0.4), 0.2, 0.0)
    # ⑥ 灵魂一问
    for j, n in enumerate(("E5", "D5", "C5", "D5", "E5", "E5", "E5", "D5", "D5", "D5", "E5", "G5")):
        if 61.0 + j * 0.4 < 65.8:
            mx.add(61.0 + j * 0.4, celesta(note_freq(n), 0.9), 0.06, 0.1)
    mx.add(66.8, noise(0.7, 0.4, 0.05, seed=92, attack=0.05), 0.16, 0.0)
    mx.add(67.1, sweep(400, 2400, 0.4, 2), 0.1, 0.0)
    mx.add(67.6, celesta(note_freq("B6"), 0.8), 0.08, 0.0)
    for j, n in enumerate(("C5", "B4", "A4", "G4", "E4")):
        mx.add(68.3 + 0.5 * j, celesta(note_freq(n), 1.2), 0.06, -0.1)
    # 片尾
    play_theme(mx, SE, DUR, gain=0.9)

    # 角色的声音
    for (ts, who, q) in SYL:
        if who == "scroll":                         # 一百个低沉声音的合唱
            for v in range(9):
                f = rnd.uniform(220, 520)
                mx.add(ts + rnd.uniform(0, 0.03), chirp(f, 0.11, 1.15, 1.0), 0.035, rnd.uniform(-0.6, 0.6))
        elif who == "clawd":
            mx.add(ts, sweep(880, 880, 0.1, 0, square=True), 0.06, -0.3)
        else:
            f0, g = VOICE[who]
            f = f0 * rnd.choice((0.9, 1.0, 1.1, 1.2))
            mx.add(ts, chirp(f * (1.15 if q else 1), 0.1, 1.45 if q else 1.3, 1.5 if q else 1.1), g, 0.0)
    for (a, b, s, x, y, size, rot) in STAMPS:
        pan = clamp((x - W / 2) / W * 1.4, -0.8, 0.8)
        if "呀哈" in s:
            mx.add(a, chirp(1900, 0.18, 1.4, 1.3), 0.2, pan)
            mx.add(a + 0.2, chirp(2300, 0.4, 1.3, 0.9), 0.2, pan)
        elif "乌拉" in s:
            mx.add(a, sweep(900, 2600, 0.6, 1.5, harm=0.3), 0.16, pan)
        elif "哈" in s:
            mx.add(a, chirp(1300, 0.16, 1.6, 1.7), 0.18, pan)
        elif "呜" in s:
            mx.add(a, sweep(1500, 900, 0.9 if "哇" in s else 0.5, 1.0, harm=0.2), 0.14, pan)
        elif "嗯" in s:
            mx.add(a, chirp(1500, 0.14, 1.2, 1.25), 0.14, pan)
        elif "嘎" in s:
            pass
    mx.reverb(0.14)
    mx.write(path, fade_out=0.8)


# ================================================================ 入口
def make_covers(t=54.75):
    """小红书封面：3:4（1080×1440）和 9:16（1080×1920）两版"""
    fr = draw_frame(t, clean=True).convert("RGBA")
    title1 = text_tile("零，", 150, (255, 233, 150), 14, INK)
    title2 = text_tile("它也是一个数量", 130, (255, 233, 150), 14, INK)
    sub = pill_tile("本科生慢科研倡议 · 推免季篇", 48, bg=(255, 253, 246, 240))
    tag = pill_tile("教授喊你慢下来，然后呢？", 44, bg=(255, 236, 160, 240))
    # 9:16
    full = fr.copy()
    full.alpha_composite(Image.new("RGBA", (W, 760), (255, 248, 236, 0)), (0, 0))
    stamp(full, tag, W / 2, 1600)
    stamp(full, title1, W / 2 - 300, 420, 1.0, 1.0, -0.06)
    stamp(full, title2, W / 2, 590, 1.0, 1.0, -0.03)
    stamp(full, sub, W / 2, 1700)
    full.convert("RGB").save(os.path.join(HERE, "封面_慢科研_9x16.png"))
    # 3:4：裁中间偏下，保住吉伊的脸
    y0 = 300
    crop = fr.crop((0, y0, W, y0 + 1440))
    stamp(crop, title1, W / 2 - 300, 170, 1.0, 1.0, -0.06)
    stamp(crop, title2, W / 2, 340, 1.0, 1.0, -0.03)
    stamp(crop, sub, W / 2, 1330)
    crop.convert("RGB").save(os.path.join(HERE, "封面_慢科研_3x4.png"))
    print("saved covers")


def render_bytes(i):
    return draw_frame(i / FPS).tobytes()

def main():
    os.makedirs(os.path.join(HERE, "previews"), exist_ok=True)
    arg = sys.argv[1] if len(sys.argv) > 1 else ""
    if arg == "cover":
        make_covers()
        return
    if arg == "still":
        for s in sys.argv[2:]:
            draw_frame(float(s)).save(os.path.join(HERE, "previews", f"slow_{float(s):05.2f}.png"))
        return
    if arg == "music" or not os.path.exists(WAV) or "--remusic" in sys.argv:
        print("合成配乐 …", flush=True)
        make_music(WAV)
        if arg == "music":
            return
    encode(render_bytes, int(DUR * FPS), WAV, OUT)
    # 响度标准化到短视频平台常用的 -14 LUFS（视频流直接复制）
    tmp = OUT + ".tmp.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", OUT, "-map", "0:v", "-map", "0:a", "-c:v", "copy",
                    "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", tmp], check=True)
    os.replace(tmp, OUT)
    print("done →", OUT)


if __name__ == "__main__":
    main()
