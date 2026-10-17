# -*- coding: utf-8 -*-
"""
《啾啾日记 · 草丛里的小方块》（竖屏 1080×1920，40 秒，24 fps，独立短篇）

小黄鸡啾啾在草地散步，草丛里蹦出一只像素小 Clawd。啾啾邀请它一起散步，
走着走着，身后的 Clawd 越来越多……回头一数：一、二、三……八……八点五？
正要一起回家——地面一震，一只巨型 Clawd 从天而降。「……九？」啾啾当场晕倒。

运行：
  python3 caocong.py                  → music.wav + 啾啾日记_草丛里的小方块.mp4
  python3 caocong.py still 5 20.5     → previews/ 下导出静帧
  python3 caocong.py sheet            → previews/sheet.png 角色表情设定
  python3 caocong.py cover            → 封面.png
  python3 caocong.py music            → 只合成配乐
"""
import math, os, sys
from lib import *

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "啾啾日记_草丛里的小方块.mp4")
DUR = 40.0
GY = 1360                       # 地面线（脚底）
K = 1.2                         # 角色整体缩放

# ================================================================ 啾啾的移动
X0 = -470.0
T_EXIT = 1e9                    # 这一篇里啾啾最后不再走出画面

# 结尾反转：巨型 Clawd
T_RUMBLE = 31.0                 # 地面开始震
T_DROP = 31.3                   # 从天而降
T_LAND = 31.65                  # 落地
T_TURN2 = 32.0                  # 啾啾慢慢回头
T_NINE = 32.5                   # 「……九？」
T_FAINT = 33.8                  # 晕倒
T_END = 35.0                    # 片尾卡
GIANT_C = 62.0

def v_chick(t):
    if t < 2.45: return 225.0
    if t < 3.0:  return 225.0 * (1 - ease_io((t - 2.45) / 0.55))
    if t < 11.0: return 0.0
    if t < 11.5: return 175.0 * ease_io((t - 11.0) / 0.5)
    if t < 16.5: return 175.0
    if t < 17.0: return 175.0 * (1 - ease_io((t - 16.5) / 0.5))
    if t < T_EXIT: return 0.0
    if t < T_EXIT + 0.5: return 175.0 * ease_io((t - T_EXIT) / 0.5)
    return 175.0

_DT = 1 / 480
_XT = [X0]
for _i in range(int((DUR + 1) / _DT)):
    _XT.append(_XT[-1] + v_chick(_i * _DT) * _DT)

def walk_x(t):
    if t <= 0:
        return X0
    f = t / _DT
    i = int(f)
    if i >= len(_XT) - 1:
        return _XT[-1]
    return lerp(_XT[i], _XT[i + 1], f - i)

def chick_x(t):
    return walk_x(t) + 30 * ease_io(ramp(t, 5.0, 5.3))     # 被吓得往后一跳

def moving(t):
    return v_chick(t) > 2

# ================================================================ Clawd 们
XS = chick_x(6.0)
X17 = chick_x(20.0)
N_CL = 9                                         # 8 只 + 1 只迷你
OFF = [250 + 215 * i for i in range(8)] + [250 + 215 * 7 + 170]
LAG = [0.05 + 0.065 * i for i in range(N_CL)]
CELL = [13.0] * 8 + [7.0]
POP = [4.9, 12.4, 13.2, 13.9, 14.5, 15.0, 15.45, 15.85, 16.25]
AIR = [0.42] + [0.4] * 8
HOPH = [270] + [180] * 7 + [130]
L0 = XS - 254
LAND = [L0] + [chick_x(POP[i] + AIR[i] - LAG[i]) - OFF[i] for i in range(1, N_CL)]
TUFTX = [L0 - 170] + [LAND[i] - 60 for i in range(1, N_CL)]
STOP = [17.0 + LAG[i] for i in range(N_CL)]
COUNT = [22.3 + 0.6 * i for i in range(8)] + [27.6]

# ================================================================ 镜头
def cam_walk(t):
    return smax(0.0, chick_x(t) - 240, 150)

CAM0 = cam_walk(11.0)
CAM17 = cam_walk(17.5)

def cam(t):
    if t < 11.0:
        return CAM0
    if t < 21.5:
        return cam_walk(min(t, 17.5))
    if t < 29.0:
        c = CAM17
        for i in range(N_CL):
            a, b = (COUNT[i] - 0.48, COUNT[i] - 0.05) if i < 8 else (COUNT[7] + 0.25, COUNT[8] - 0.1)
            c = lerp(c, X17 - OFF[i], ease_io(ramp(t, a, b)))
        return c
    return CAM17

def sx_of(wx, t):
    return wx - cam(t) + W / 2

# ================================================================ 台词
LINES = [
    (3.5, 4.7, "嗯？"),
    (6.9, 8.75, "你是……小螃蟹吗？"),
    (9.0, 10.8, "要一起散步吗？"),
    (20.3, 22.0, "……变、变多了！？"),
    (27.6, 29.0, "……八点五？"),
    (29.2, 31.0, "哈哈～那就一起回家吧！"),
    (T_NINE, T_NINE + 1.1, "……九？"),
]
NUMS = "一二三四五六七八"
PUNCT = set("…，。！？～、 ")

def syllables():
    out = []
    for (a, b, s) in LINES:
        chars = [c for c in s if c not in PUNCT]
        for j, c in enumerate(chars):
            out.append((a + 0.08 + 0.13 * j, j == len(chars) - 1 and s.endswith("？")))
    for i in range(8):
        out.append((COUNT[i], False))
    return out

SYL = syllables()

def talk(t):
    m = 0.0
    for (ts, _) in SYL:
        if 0 <= t - ts < 0.12:
            m = max(m, math.sin(math.pi * (t - ts) / 0.12))
    return m

# ================================================================ 啾啾的状态
TURNS = [(3.6, 1, -1, 0.35), (10.8, -1, 1, 0.35), (18.9, 1, -1, 0.35), (T_TURN2, -1, 1, 0.5)]
BLINKS = [1.6, 4.4, 6.1, 9.7, 18.5, 19.6, 19.85, 22.8]

def chick_state(t):
    st = dict(x=sx_of(chick_x(t), t), y=GY, k=K)
    face, sy_dip = 1.0, 0.0
    for t0, a, b, td in TURNS:
        if t >= t0:
            u = ramp(t, t0, t0 + td)
            face = lerp(a, b, ease_io(u))
            sy_dip = max(sy_dip, math.sin(math.pi * u) if u < 1 else 0)
    st["face"] = face

    # 走路
    walk = clamp(v_chick(t) / 120)
    ph = math.pi * (walk_x(t) - X0) / 68
    st["step"], st["walk"] = ph, walk
    y = -abs(math.sin(ph)) * 9 * walk
    rot = math.sin(ph) * 0.045 * walk
    sx = 1 + 0.012 * math.sin(2 * math.pi * 0.9 * t)
    sy = 1 - 0.012 * math.sin(2 * math.pi * 0.9 * t) - 0.04 * sy_dip
    st["sway"] = math.sin(ph) * 0.12 * walk + 0.05 * math.sin(t * 2.1)
    wl = wr = 0.0
    if walk > 0:
        wl, wr = 0.14 + 0.1 * math.sin(ph) * walk, 0.14 - 0.1 * math.sin(ph) * walk

    eyes, mouth = "dot", 0.0
    if t < 2.6 or 11.0 <= t < 17.0 or 10.05 <= t < 10.8:
        eyes = "happy"
    # 歪头
    rot += -0.09 * window(t, 3.9, 4.2, 4.6, 4.9) - 0.08 * window(t, 6.8, 7.1, 8.5, 8.8)
    # 被吓一跳
    if 4.95 <= t < 5.6:
        eyes = "big"
        u = ramp(t, 5.0, 5.32)
        y -= 38 * arc01(u)
        wl = wr = 1.0 - ease_io(ramp(t, 5.35, 5.6))
        mouth = 0.65 * (1 - ramp(t, 5.3, 5.6))
    if 6.45 <= t < 8.8:
        eyes = "sparkle"
    # 邀请：伸出靠近 Clawd 的那只翅膀
    if 9.0 <= t < 10.8:
        wl = max(wl, 0.75 * window(t, 9.0, 9.25, 10.4, 10.8) + 0.12 * math.sin(t * 9))
    if 10.05 <= t < 10.8:
        wr = max(wr, 0.35 + 0.2 * math.sin(t * 16))
    # 被 Clawd 撞了一下屁股
    if 17.05 <= t < 17.6:
        e = math.exp(-(t - STOP[0]) * 9)
        st["x"] += 8 * e
        sy *= 1 - 0.06 * e
        eyes = "big"
    if 17.3 <= t < 18.9:
        eyes = "blank"
    if 18.2 <= t < 19.6:
        st["sweat"] = ramp(t, 18.2, 19.6)
    # 变多了！？
    if 20.3 <= t < 22.0:
        eyes = "shock"
        y -= 44 * arc01(ramp(t, 20.3, 20.62))
        wl = wr = 1.0 if t < 20.9 else 0.6 + 0.1 * math.sin(t * 40)
        st["tuft"] = ease_out(ramp(t, 20.3, 20.45))
        st["gloom"] = ramp(t, 20.6, 20.9)
        st["sweat"] = ramp(t, 20.5, 22.0)
        if t > 20.62:
            st["x"] += 2.2 * math.sin(t * 70)
    # 大笑
    if t >= 29.1:
        eyes = "happy"
        if t < 31.0:
            mouth = 0.35
            y -= 7 * abs(math.sin(2 * math.pi * 2.4 * (t - 29.1)))
            wl = wr = 0.8 + 0.2 * math.sin(t * 15)
    # 地面在震……
    if T_RUMBLE <= t < T_LAND:
        eyes, mouth, wl, wr = "blank", 0.0, 0.0, 0.0
        st["x"] += 1.5 * math.sin(t * 80)
    # 咚！
    if T_LAND <= t < T_FAINT:
        eyes = "shock"
        y -= 50 * arc01(ramp(t, T_LAND, T_LAND + 0.32))
        st["tuft"] = 1.0
        st["gloom"] = ramp(t, T_TURN2 + 0.4, T_TURN2 + 0.8)
        st["sweat"] = ramp(t, T_TURN2 + 0.5, T_FAINT)
        wl = wr = 1.0 if t < T_TURN2 else 0.55 + 0.08 * math.sin(t * 40)
        rot -= 0.07 * ease_io(ramp(t, T_TURN2 + 0.35, T_TURN2 + 0.6))      # 仰头看
    # 晕倒（向后仰倒，小脚朝天）
    if t >= T_FAINT:
        u = ramp(t, T_FAINT, T_FAINT + 0.33)
        rot = -1.38 * u * u + (0.08 * math.sin((t - T_FAINT - 0.33) * 22) * math.exp(-(t - T_FAINT - 0.33) * 6)
                               if u >= 1 else 0)
        y -= 105 * u * u                      # 让圆滚滚的身子正好躺在地上
        eyes, mouth, wl, wr = "swirl", 0.35, 0.9, 0.9
        st["tuft"] = 0.0
    for b in BLINKS:
        if b <= t < b + 0.11 and eyes in ("dot", "blank", "sparkle"):
            eyes = "closed"
    st["mouth"] = max(mouth, talk(t) * (0.9 if eyes != "shock" else 1.0))
    st.update(eyes=eyes, rot=rot, sx=sx, sy=sy, wl=wl, wr=wr)
    st["y"] = GY + y
    return st

# ================================================================ Clawd 的状态
def clawd_state(i, t):
    if t < POP[i]:
        return None
    st = dict(c=CELL[i], sx=1.0, sy=1.0, y=0.0, eyes="open", step=None, icon=None)
    tl = t - POP[i]
    if tl < AIR[i]:
        u = tl / AIR[i]
        st["wx"] = lerp(TUFTX[i], LAND[i], u)
        st["y"] = -HOPH[i] * arc01(u)
        st["sx"], st["sy"] = 0.9, 1.15
        return st

    if i == 0 and t < 11.0:
        wx = L0 + 18 * math.sin(2 * math.pi * 3.0 * (t - 8.0)) * window(t, 8.0, 8.1, 8.75, 8.9)
        if 8.0 <= t < 8.9:
            st["step"] = int(t * 12) % 2
    else:
        wx = chick_x(t - LAG[i]) - OFF[i]
        if i == 0:
            wx = max(L0, wx)
        if moving(t - LAG[i]) and (i > 0 or wx > L0):
            st["step"] = int(walk_x(t - LAG[i]) / 18) % 2
            st["y"] -= 3 if st["step"] else 0
        ts = STOP[i]
        if ts < t < ts + 1.0:          # 一个撞一个
            e = math.exp(-(t - ts) * 9)
            wx += 11 * e * math.sin((t - ts) * 24)
            st["sx"], st["sy"] = 1 + 0.22 * e, 1 - 0.18 * e
    st["wx"] = wx

    lt = tl - AIR[i]
    if lt < 0.25:                      # 落地压扁
        e = 1 - ease_out(lt / 0.25)
        st["sx"], st["sy"] = 1 + 0.3 * e, 1 - 0.3 * e

    hops = []
    if i == 0:
        hops += [(10.0, 0.32, 40), (10.4, 0.32, 40)]
    hops.append((COUNT[i], 0.3, 34 if i < 8 else 26))
    if i < 4:
        hops += [(29.7 + 0.12 * i, 0.32, 36), (30.3 + 0.12 * i, 0.32, 30), (T_LAND + 0.02, 0.3, 46)]
    for (h0, hd, hh) in hops:
        u = (t - h0) / hd
        if 0 <= u < 1:
            st["y"] -= hh * arc01(u)
            st["sx"], st["sy"] = 0.92, 1.1
        elif 1 <= u < 1.6:
            e = 1 - (u - 1) / 0.6
            st["sx"], st["sy"] = 1 + 0.18 * e, 1 - 0.16 * e

    blink = (t + hsh(i, 5) * 3.1) % 3.1 < 0.12 and not (19.0 < t < 21.0)
    if blink or 20.0 <= t < 20.13:
        st["eyes"] = "blink"

    if i == 0:
        if 5.55 <= t < 6.4: st["icon"] = ("!", 5.55)
        if 8.0 <= t < 9.0: st["icon"] = ("?", 8.0)
        if 10.05 <= t < 11.0: st["icon"] = ("heart", 10.05)
    if 20.45 + 0.04 * i <= t < 21.6:
        st["icon"] = ("!", 20.45 + 0.04 * i)
    if i == 8 and 27.85 <= t < 28.9:
        st["icon"] = ("heart", 27.85)
    if T_RUMBLE + 0.1 + 0.04 * i <= t < T_TURN2 + 0.3:
        st["icon"] = ("!", T_RUMBLE + 0.1 + 0.04 * i)
    return st

# ================================================================ 特效
NOTE_T = [0.2 + 0.6 * k for k in range(4)] + [11.3 + 0.6 * k for k in range(9)]

def draw_notes(pen, t):
    for k, s in enumerate(NOTE_T):
        age = t - s
        if not 0 <= age < 1.4:
            continue
        wx = chick_x(s) + 30
        x = sx_of(wx, t) - 24 * age + 10 * math.sin(age * 5 + k)
        y = GY - 320 - 110 * age
        a = min(1, age / 0.15) * (1 - age / 1.4)
        draw_note(pen, x, y, 0.9 + 0.15 * hsh(k), a, 0.15 * math.sin(age * 4 + k))

def draw_sparkles(pen, cx, t, spots, base=GY):
    for j, (dx, dy, r) in enumerate(spots):
        tw = abs(math.sin(t * 5 + j * 1.7))
        if tw > 0.4:
            pen.poly(star4(cx + dx, base + dy, r * tw, t * 0.8 + j), fill=STAR, ol=INK, w=2.2)

def draw_leaves(pen, t):
    for i in range(N_CL):
        age = t - POP[i]
        if not 0 <= age < 1.0:
            continue
        for j in range(6):
            vx = (hsh(i * 7 + j, 1) - 0.4) * 300
            vy = -320 - hsh(i * 7 + j, 2) * 260
            wx = TUFTX[i] + vx * age
            y = GY - 36 + vy * age + 900 * age * age
            pen.poly(ell(sx_of(wx, t), y, 10, 4.5, age * 9 + j, 16), fill=TUFT_L + (int(255 * (1 - age)),), ol=None)

def chick_head(st):
    return st["x"] + st["face"] * 24, st["y"] - 250 * K

def draw_world_layer(t, lay):
    pen = lay.pen
    c = cam(t)
    # 草丛（Clawd 的藏身处）
    for i in range(N_CL):
        x = sx_of(TUFTX[i], t)
        if not -120 < x < W + 120:
            continue
        if i == 0:
            amp = 0.1 * window(t, 3.0, 3.3, 4.7, 4.95) * (0.5 + ramp(t, 3.0, 4.8))
        else:
            amp = 0.13 * window(t, POP[i] - 0.45, POP[i] - 0.3, POP[i] - 0.02, POP[i] + 0.05)
        after = t - POP[i]
        if 0 <= after < 0.8:
            amp = 0.2 * math.exp(-after * 6)
        wob = amp * math.sin(t * 46 + i * 2)
        draw_tuft(pen, x, GY + 6, 1.1 if i < 8 else 0.9, wob)

    # 巨型 Clawd（在所有角色后面）
    gs = giant_state(t)
    if gs:
        u = gs["fall"]
        pen.ellipse(gs["x"], GY - 20, 8.6 * GIANT_C * (0.3 + 0.7 * u), 22 * (0.3 + 0.7 * u), (64, 120, 58, int(30 + 50 * u)))
        draw_clawd(pen, gs["x"], GY - 26 + gs["y"], GIANT_C, gs["sx"], gs["sy"], gs["eyes"])
        age = t - T_LAND
        if 0 <= age < 0.8:                 # 落地扬起的尘土
            for j in range(9):
                dx = (j - 4) * 120 + 40 * hsh(j, 3)
                r = lerp(24, 80, ease_out(age / 0.8)) * (0.7 + 0.5 * hsh(j, 4))
                pen.circle(gs["x"] + dx * (1 + age), GY - 20 - r * 0.4, r, (252, 250, 242, int(220 * (1 - age / 0.8))))

    # 影子
    chs = chick_state(t)
    lift = GY - chs["y"]
    pen.ellipse(chs["x"], GY + 2, 104 * K * (1 - lift / 300), 16 * (1 - lift / 300), SHADOW)
    cls = [clawd_state(i, t) for i in range(N_CL)]
    for st in cls:
        if st:
            pen.ellipse(sx_of(st["wx"], t), GY + 2, 8.6 * st["c"] * (1 + st["y"] / 400), 1.2 * st["c"], SHADOW)

    for i in range(N_CL):
        st = cls[i]
        if not st:
            continue
        x = sx_of(st["wx"], t)
        if -120 < x < W + 120:
            draw_clawd(pen, x, GY + st["y"], st["c"], st["sx"], st["sy"], st["eyes"], st["step"])
        draw_burst(pen, sx_of(TUFTX[i], t), GY - 46, (t - POP[i]) / 0.3)
    draw_leaves(pen, t)
    draw_chick(pen, chs)

    # 啾啾头上的小东西
    hx, hy = chick_head(chs)
    draw_notes(pen, t)
    if 6.45 <= t < 8.8:
        draw_sparkles(pen, chs["x"], t, [(-190, -300, 18), (180, -250, 15), (140, -360, 12)])
    if 29.1 <= t < 31.2:
        draw_sparkles(pen, chs["x"], t, [(-200, -280, 18), (195, -300, 17), (-140, -380, 13), (150, -390, 14), (0, -420, 11)])
    if 17.4 <= t < 18.9:
        a = 1 - ramp(t, 18.6, 18.9)
        for j in range(3):
            if t >= 17.4 + 0.35 * j:
                pen.circle(hx - 34 + 34 * j, hy - 40, 8.5, INK + (int(255 * a),))

    # 头顶的问号/感叹号（2× 层上盖章）
    for (a, b, s, dx) in ((3.4, 4.8, "?", -40), (5.0, 5.8, "!", 0), (20.3, 21.8, "!?", 0)):
        if a <= t < b:
            sc = back_out(ramp(t, a, a + 0.22)) * (1 - ease_io(ramp(t, b - 0.15, b)))
            wob = 0.12 * math.sin((t - a) * 9) * math.exp(-(t - a) * 2)
            x, y = pen.P(hx + dx, hy - 90)
            stamp(lay.img, text_tile(s, 230, INK, 14, WHITE), x, y, sc, 1.0, wob)

    # Clawd 头上的像素图标、点数
    for i in range(N_CL):
        st = cls[i]
        if not st:
            continue
        x = sx_of(st["wx"], t)
        top = GY + st["y"] - 7 * st["c"] * st["sy"]
        if st["icon"]:
            kind, t0 = st["icon"]
            draw_pixel_icon(pen, kind, x, top - 18, 8 if i < 8 else 5, back_out(ramp(t, t0, t0 + 0.2)))
        if COUNT[i] <= t < 29.0:
            s = str(i + 1) if i < 8 else "8.5?"
            sc = back_out(ramp(t, COUNT[i], COUNT[i] + 0.25))
            px, py = pen.P(x, top - (100 if i < 8 else 110))
            stamp(lay.img, text_tile(s, 150 if i < 8 else 100, INK, 12, WHITE), px, py, sc)
    if gs:
        top = GY - 26 + gs["y"] - 7 * GIANT_C * gs["sy"]
        if T_NINE <= t < T_NINE + 0.8:
            px, py = pen.P(gs["x"], top - 90)
            stamp(lay.img, text_tile("9", 280, INK, 16, WHITE), px, py, back_out(ramp(t, T_NINE, T_NINE + 0.25)))
        if 33.3 <= t < T_END:
            draw_pixel_icon(pen, "heart", gs["x"], top - 24, 20, back_out(ramp(t, 33.3, 33.55)))
    if t >= T_FAINT + 0.33:                # 晕倒后头上转圈的小星星
        X = Xf(chs["x"], chs["y"], K, rot=chs["rot"])
        hx, hy = X(0, -150)
        for j in range(3):
            a = (t - T_FAINT) * 5 + j * 2.09
            pen.poly(star4(hx + math.cos(a) * 110, hy - 60 + math.sin(a) * 30, 16, a), fill=STAR, ol=INK, w=2.2)
    return chs

def giant_state(t):
    if t < T_DROP:
        return None
    u = ramp(t, T_DROP, T_LAND)
    st = dict(x=sx_of(CAM17 + 20, t), y=-1500 * (1 - u * u), sx=0.94, sy=1.08, eyes="open", fall=u)
    if t >= T_LAND:
        e = math.exp(-(t - T_LAND) * 7)
        st["sx"], st["sy"] = 1 + 0.12 * e, 1 - 0.14 * e
    if 33.0 <= t < 33.15 or 34.4 <= t < 34.55:
        st["eyes"] = "blink"
    return st

# ================================================================ 镜头推拉 / 震动 / 集中线
def view(t):
    z, fx, fy = 1.0, W / 2, H / 2
    k = window(t, 20.3, 20.42, 21.7, 22.15)            # 「变多了！？」猛推近脸
    if k > 0:
        z = 1 + 0.3 * k
        fx, fy = lerp(W / 2, sx_of(chick_x(t), t), k), lerp(H / 2, GY - 160, k)
    k = window(t, T_TURN2 + 0.3, 33.4, T_END, T_END + 0.1)  # 慢慢推向巨型 Clawd
    if k > 0:
        z = 1 + 0.12 * k
        fx, fy = lerp(W / 2, 620, k), lerp(H / 2, 1080, k)
    amp = 5 * window(t, T_RUMBLE, T_RUMBLE + 0.1, T_LAND - 0.05, T_LAND)
    if T_LAND <= t < T_LAND + 1.2:
        amp += 26 * math.exp(-(t - T_LAND) * 5)
    if T_FAINT + 0.33 <= t < T_FAINT + 0.9:
        amp += 8 * math.exp(-(t - T_FAINT - 0.33) * 8)
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
    """漫画式集中线"""
    for (a, b, cx, cy) in ((20.3, 21.0, 690, 1180), (T_LAND, T_LAND + 0.7, 600, 1150)):
        if not a <= t < b:
            continue
        k = 1 - ramp(t, b - 0.25, b)
        rnd = random.Random(int(t * 12))
        ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(ov)
        for _ in range(90):
            ang = rnd.uniform(0, 2 * math.pi)
            r0, w, R = rnd.uniform(430, 620), rnd.uniform(3, 10), 1600
            p0 = (cx + math.cos(ang) * r0, cy + math.sin(ang) * r0)
            pl = (cx + math.cos(ang - w / R) * R, cy + math.sin(ang - w / R) * R)
            pr = (cx + math.cos(ang + w / R) * R, cy + math.sin(ang + w / R) * R)
            d.polygon([p0, pl, pr], fill=INK + (int(170 * k),))
        fr.alpha_composite(ov)

# ================================================================ 片头 / 字幕
def draw_titles(fr, t):
    if t < 3.2:
        a = 1 - ease_io(ramp(t, 2.8, 3.2))
        sc = back_out(ramp(t, 0.05, 0.45))
        stamp(fr, text_tile("啾啾日记", 150, CHICK, 9, INK), W / 2, 400, sc, a)
        stamp(fr, pill_tile("草丛里的小方块", 50), W / 2, 560, back_out(ramp(t, 0.3, 0.7)), a)
    if 0.5 <= t < T_RUMBLE:                # 钩子：让观众边看边数
        a = 1 - ramp(t, T_RUMBLE - 0.3, T_RUMBLE)
        stamp(fr, pill_tile("数一数：一共有几只Clawd？", 44, bg=(255, 236, 160, 240)), W / 2, 250,
              back_out(ramp(t, 0.5, 0.85)), a)

    s, a0, a1 = None, 0, 0
    for (a, b, txt) in LINES:
        if a <= t < b:
            s, a0, a1 = txt, a, b
    if 22.3 <= t < 27.4:
        n = sum(1 for c in COUNT[:8] if t >= c)
        s, a0, a1 = "、".join(NUMS[:n]) + ("……" if n == 8 else ""), 22.3, 27.4
    if s:
        al = min(ramp(t, a0, a0 + 0.12), 1 - ramp(t, a1 - 0.15, a1))
        stamp(fr, pill_tile(s, 58), W / 2, 1490 + 10 * (1 - al), 1.0, al)

# ================================================================ 片尾
_END_BG = None
def endcard(t):
    global _END_BG
    if _END_BG is None:
        bg = meadow().compose(CAM17, 33.0)
        meadow().foreground(bg, CAM17)
        bg = bg.filter(ImageFilter.GaussianBlur(5))
        bg.alpha_composite(Image.new("RGBA", (W, H), (255, 252, 244, 50)))
        _END_BG = bg
    fr = _END_BG.copy()
    gy = 1290
    lay = Layer(gy - 520, gy + 40)
    pen = lay.pen
    te = t - T_END
    beat = 60 / 104
    draw_clawd(pen, 1100, gy, 28, eyes="blink" if te % 2.9 < 0.14 else "open")   # 巨型 Clawd 从右边探头
    for j, x in enumerate((90, 230, 830)):
        u = ((te + (j % 2) * beat) % (2 * beat)) / (0.6 * beat * 2)
        hy = 38 * arc01(u) if u < 1 else 0
        pen.ellipse(x, gy + 2, 90, 13, SHADOW)
        draw_clawd(pen, x, gy - hy, 11, 0.92 if hy > 2 else 1.0, 1.08 if hy > 2 else 1.0,
                   "blink" if (te + j) % 2.7 < 0.12 else "open", int(te * 4 + j) % 2 if hy > 2 else None)
    k = 1.55
    pen.ellipse(540, gy + 4, 165, 20, SHADOW)
    bob = abs(math.sin(math.pi * te / beat)) * 6
    st = dict(x=540, y=gy - bob, k=k, face=0.0, eyes="happy", mouth=0.3, wl=0.1,
              wr=0.75 + 0.25 * math.sin(te * 10), sway=0.06 * math.sin(te * 3))
    draw_chick(pen, st)
    draw_clawd(pen, 540 + 6, gy - bob - 214 * k, 6.5, eyes="blink" if te % 2.2 < 0.12 else "open")
    draw_sparkles(pen, 540, te, [(-250, -380, 20), (260, -410, 17), (-200, -500, 12), (220, -480, 13)], base=gy)
    lay.onto(fr)
    fr = grain(fr.convert("RGB"), t).convert("RGBA")
    stamp(fr, text_tile("啾啾日记", 140, CHICK, 9, INK), W / 2, 400, back_out(ramp(te, 0.4, 0.8)))
    stamp(fr, pill_tile("你数出来几只？评论区告诉我～", 50), W / 2, 570, back_out(ramp(te, 0.7, 1.05)))
    stamp(fr, pill_tile("点个关注，看更多啾啾～", 58), W / 2, 1440, back_out(ramp(te, 1.3, 1.7)))
    return fr

# ================================================================ 一帧
_MEADOW = None
def meadow():
    global _MEADOW
    if _MEADOW is None:
        _MEADOW = Meadow(-950, 1250)
    return _MEADOW

def main_frame(t, titles=True, fx=True):
    c = cam(t)
    fr = meadow().compose(c, t)
    lay = Layer(0 if t >= T_DROP - 0.05 else 780, 1520)
    draw_world_layer(t, lay)
    lay.onto(fr)
    meadow().foreground(fr, c)
    if fx:
        fr = apply_view(fr, t)
        focus_lines(fr, t)
    fr = grain(fr.convert("RGB"), t).convert("RGBA")
    if titles:
        draw_titles(fr, t)
    return fr

def draw_frame(t):
    # 正片 → 淡到奶白 → 片尾
    fr = (main_frame(t) if t < T_END else endcard(t)).convert("RGB")
    dip = window(t, T_END - 0.35, T_END, T_END, T_END + 0.35)
    if dip > 0:
        fr = Image.blend(fr, Image.new("RGB", (W, H), CREAM), dip)
    fade = 1 - ramp(t, DUR - 0.5, DUR)
    if fade < 1:
        fr = Image.blend(Image.new("RGB", (W, H), CREAM), fr, fade)
    return fr

# ================================================================ 配乐
BPM = 104
BEAT = 60 / BPM
THEME = [  # (音, 八分音符数)
    ("C5", 1), ("F5", 1), ("A5", 1), ("F5", 1), ("G5", 2), ("E5", 2),
    ("F5", 2), ("D5", 1), ("C5", 1), ("D5", 4),
    ("C5", 1), ("F5", 1), ("A5", 1), ("C6", 1), ("Bb5", 2), ("G5", 2),
    ("A5", 1), ("G5", 1), ("F5", 1), ("E5", 1), ("F5", 4),
]
HALF_CHORDS = ["F", "F", "Bb", "C", "F", "Dm", "C", "F"]
CHORD = {"F": ["F4", "A4", "C5"], "Bb": ["F4", "Bb4", "D5"], "C": ["E4", "G4", "C5"], "Dm": ["F4", "A4", "D5"]}
ROOT = {"F": "F2", "Bb": "Bb1", "C": "C2", "Dm": "D2"}

def play_theme(mx, t0, t1, full=True):
    bar = 4 * BEAT
    loop = 4 * bar
    k = 0
    while t0 + k * loop < t1:
        base = t0 + k * loop
        tt = base
        for n, d in THEME:
            if tt >= t1:
                break
            mx.add(tt, marimba(note_freq(n), 0.9), 0.24, 0.1, cut=t1)
            if full:
                mx.add(tt, celesta(note_freq(n) * 2, 0.6), 0.035, 0.3, cut=t1)
            tt += d * BEAT / 2
        for h, ch in enumerate(HALF_CHORDS):
            hb = base + h * 2 * BEAT
            if hb >= t1:
                break
            mx.add(hb, bass(note_freq(ROOT[ch]), 0.5), 0.3, -0.1, cut=t1)
            for q, nn in enumerate(CHORD[ch]):
                mx.add(hb + BEAT + q * 0.012, celesta(note_freq(nn), 0.5), 0.05, -0.3, cut=t1)
        if full:
            for e in range(32):
                te = base + e * BEAT / 2
                if te < t1:
                    mx.add(te, noise(0.05, 0.9, 0.35, seed=e, attack=0.002), 0.03 if e % 2 else 0.018, 0.4)
        k += 1

def make_music(path):
    mx = Mix(DUR)
    # 片头散步 → 草丛一响，音乐戛然而止
    play_theme(mx, 0.0, 3.0, full=False)
    # 散步主题 → 啾啾停下时硬切
    play_theme(mx, 11.0, 17.0)
    # 大笑 → 地面一震，音乐硬切
    play_theme(mx, 29.1, T_RUMBLE)
    # 片尾
    play_theme(mx, T_END, DUR)
    for j, n in enumerate(("F5", "A5", "C6", "F6", "A6")):
        mx.add(29.1 + 0.05 * j, celesta(note_freq(n), 1.0), 0.07, 0.2)

    # 草丛沙沙
    mx.add(3.0, noise(1.9, 0.5, 0.08, seed=3, grains=22, attack=0.3), 0.16, -0.3)
    for i in range(1, N_CL):
        mx.add(POP[i] - 0.45, noise(0.45, 0.5, 0.08, seed=10 + i, grains=26, attack=0.05), 0.1,
               clamp((sx_of(TUFTX[i], POP[i]) - W / 2) / W * 1.6, -0.9, 0.9))
    # 蹦出来！（像素方波）
    for i in range(N_CL):
        pan = clamp((sx_of(TUFTX[i], POP[i]) - W / 2) / W * 1.6, -0.9, 0.9)
        f0 = 300 * (1.06 ** i) if i < 8 else 900
        mx.add(POP[i], sweep(f0, f0 * 3, 0.13, 10, square=True), 0.12 if i else 0.16, pan)
        mx.add(POP[i], noise(0.25, 0.6, 0.1, seed=30 + i, attack=0.003), 0.06, pan)
        mx.add(POP[i] + AIR[i], sweep(140, 80, 0.12, 14, harm=0.3), 0.18, pan)
    # 啾啾吓一跳
    mx.add(5.0, chirp(2300, 0.16, 1.3, 1.25), 0.2, 0.1)
    mx.add(5.55, sweep(1200, 1200, 0.06, 0, square=True), 0.07, -0.2)
    mx.add(5.63, sweep(1600, 1600, 0.08, 0, square=True), 0.07, -0.2)
    # 好奇 / 心动
    for j, n in enumerate(("C6", "E6", "G6")):
        mx.add(6.45 + 0.12 * j, celesta(note_freq(n), 1.2), 0.06, 0.3)
    for j in range(8):
        mx.add(8.0 + j / 12 * 1.0, sweep(900 + 200 * (j % 2), 900 + 200 * (j % 2), 0.025, 0, square=True), 0.04, -0.25)
    mx.add(8.05, sweep(700, 1100, 0.12, 0, square=True), 0.06, -0.25)
    for h in (10.0, 10.4):
        mx.add(h, sweep(500, 1300, 0.12, 6, square=True), 0.07, -0.2)
    for j, n in enumerate(("F5", "A5", "C6", "F6")):
        mx.add(10.05 + 0.09 * j, celesta(note_freq(n), 1.2), 0.07, 0.0)
    # 一个撞一个
    for i in range(N_CL):
        f = 520 * (0.95 ** i)
        mx.add(STOP[i], sweep(f, f * 0.8, 0.07, 18, square=True), 0.07, clamp(-0.1 - 0.1 * i, -0.9, 0))
    # 变多了！？
    mx.add(20.3, boing(190, 0.9), 0.25, 0.0)
    mx.add(20.32, chirp(2400, 0.2, 1.25, 1.3), 0.18, 0.1)
    for i in range(5):
        mx.add(20.45 + 0.04 * i, sweep(1500, 1500, 0.05, 0, square=True), 0.04, -0.4 + 0.15 * i)
    # 点数：每数一只升一个音
    scale = ["F4", "G4", "A4", "Bb4", "C5", "D5", "E5", "F5"]
    for i in range(8):
        mx.add(COUNT[i], marimba(note_freq(scale[i]), 0.9), 0.26, 0.0)
        mx.add(COUNT[i] + 0.02, sweep(600, 1200, 0.1, 8, square=True), 0.05, 0.0)
    mx.add(COUNT[8], celesta(note_freq("F6"), 1.0), 0.09, 0.0)
    mx.add(COUNT[8] + 0.02, sweep(1400, 2600, 0.07, 10, square=True), 0.05, 0.0)
    for j, n in enumerate(("C6", "F6")):
        mx.add(27.85 + 0.12 * j, celesta(note_freq(n), 1.0), 0.06, 0.0)
    # 啾啾说话
    rnd = random.Random(5)
    for (ts, q) in SYL:
        f = rnd.choice((1500, 1650, 1800, 1950))
        mx.add(ts, chirp(f * (1.2 if q else 1.0), 0.1, 1.5 if q else 1.35, 1.6 if q else 1.12), 0.16, 0.1)
    # 环境：微风 + 远处的鸟叫，让停顿不至于死寂
    mx.add(0.0, noise(DUR, 0.03, 0.004, seed=99, attack=0.5), 0.32, 0.0)
    for k, tb in enumerate((1.2, 7.6, 13.0, 18.3, 19.4, 24.6, 28.4, 34.2)):
        for j in range(2):
            mx.add(tb + 0.11 * j, chirp(3300 + 400 * hsh(k, j), 0.07, 1.25, 1.0), 0.03, -0.6 if k % 2 else 0.6)
    # 「……」、汗珠、转身
    for j in range(3):
        mx.add(17.4 + 0.35 * j, sweep(880, 880, 0.05, 0, square=True), 0.035, 0.1)
    mx.add(18.2, sweep(1900, 900, 0.09, 12), 0.08, 0.2)
    mx.add(18.9, noise(0.3, 0.35, 0.06, seed=77, attack=0.08), 0.07, 0.0)
    mx.add(3.6, noise(0.3, 0.35, 0.06, seed=78, attack=0.08), 0.05, 0.0)
    # 巨型 Clawd：震动 → 下落哨音 → 咚！
    mx.add(T_RUMBLE, noise(T_LAND - T_RUMBLE + 0.05, 0.02, 0.002, seed=55, attack=0.12), 1.4, 0.0)
    mx.add(T_RUMBLE, sweep(52, 48, T_LAND - T_RUMBLE, 0, harm=0.5), 0.22, 0.0)
    for i in range(4):
        mx.add(T_RUMBLE + 0.1 + 0.04 * i, sweep(1500, 1500, 0.05, 0, square=True), 0.04, -0.5 + 0.12 * i)
    mx.add(T_DROP, sweep(2200, 380, T_LAND - T_DROP, 0), 0.09, 0.0)
    mx.add(T_LAND, sweep(110, 34, 1.1, 3.2, harm=0.45), 0.7, 0.0)
    mx.add(T_LAND, noise(1.0, 0.07, 0.004, seed=56, attack=0.002), 1.0, 0.0)
    mx.add(T_LAND + 0.02, chirp(2500, 0.2, 1.25, 1.3), 0.18, 0.1)
    for i in range(4):
        mx.add(T_LAND + 0.03, sweep(500 + 80 * i, 1200, 0.1, 8, square=True), 0.04, -0.5 + 0.12 * i)
    mx.add(T_TURN2, noise(0.5, 0.3, 0.05, seed=79, attack=0.15), 0.06, 0.0)
    mx.add(33.0, sweep(150, 150, 0.12, 0, square=True), 0.14, 0.0)
    mx.add(33.3, sweep(110, 230, 0.55, 2.5, square=True), 0.2, 0.0)
    # 晕倒：滑哨下行 + 倒地 + 小鸟转圈
    mx.add(T_FAINT, sweep(1500, 260, 0.45, 1.5), 0.13, 0.0)
    mx.add(T_FAINT + 0.33, sweep(130, 60, 0.22, 12, harm=0.3), 0.3, 0.0)
    for j in range(5):
        mx.add(T_FAINT + 0.55 + 0.2 * j, chirp(3000 + 300 * (j % 2), 0.06, 1.2, 1.0), 0.05, -0.4 if j % 2 else 0.4)
    # 片尾 Clawd 们蹦跶
    for j in range(16):
        te = T_END + j * BEAT
        if te < DUR - 0.6:
            mx.add(te, sweep(700 + 100 * (j % 2), 1300, 0.08, 10, square=True), 0.03, -0.5 if j % 2 else 0.5)
    print("混响 …", flush=True)
    mx.reverb(0.16)
    mx.write(path, fade_out=0.8)

# ================================================================ 入口
def render_bytes(i):
    return draw_frame(i / FPS).tobytes()

def sheet():
    """角色设定图：表情一览"""
    fr = meadow().compose(0, 0)
    lay = Layer(0, H)
    kinds = [("dot", 0, 0, 0), ("happy", 0.3, 0, 0), ("big", 0.6, 0, 0), ("sparkle", 0, 0, 0),
             ("shock", 0.8, 1, 1), ("blank", 0, 0, 0), ("closed", 0, 0, 0), ("happy", 0.4, 0, 0)]
    for j, (e, m, tf, g) in enumerate(kinds):
        x, y = 270 + 540 * (j % 2), 420 + 420 * (j // 2)
        st = dict(x=x, y=y, face=(-1, 0, 1, 0.5, 0, -0.5, 0, 1)[j], eyes=e, mouth=m, tuft=tf, gloom=g,
                  wl=0.8 if j == 7 else 0, wr=0.8 if j in (4, 7) else 0, sweat=0.3 if j == 4 else None)
        draw_chick(lay.pen, st)
    for j in range(4):
        draw_clawd(lay.pen, 160 + 250 * j, 1820, 10, eyes="blink" if j == 1 else "open", step=None if j < 2 else j % 2)
    lay.onto(fr)
    fr.convert("RGB").save(os.path.join(HERE, "previews", "sheet.png"))

def main():
    os.makedirs(os.path.join(HERE, "previews"), exist_ok=True)
    arg = sys.argv[1] if len(sys.argv) > 1 else ""
    if arg == "still":
        for s in sys.argv[2:]:
            t = float(s)
            draw_frame(t).save(os.path.join(HERE, "previews", f"still_{t:05.2f}.png"))
            print("saved", t)
        return
    if arg == "sheet":
        sheet()
        return
    if arg == "cover":
        fr = main_frame(21.0, titles=False, fx=False)
        stamp(fr, text_tile("啾啾日记", 150, CHICK, 9, INK), W / 2, 400)
        stamp(fr, pill_tile("数一数：一共有几只Clawd？", 60, bg=(255, 236, 160, 240)), W / 2, 580)
        fr.convert("RGB").save(os.path.join(HERE, "封面.png"))
        return
    wav = os.path.join(HERE, "music.wav")
    if arg == "music" or not os.path.exists(wav) or "--remusic" in sys.argv:
        print("合成配乐 …", flush=True)
        make_music(wav)
        if arg == "music":
            return
    encode(render_bytes, int(DUR * FPS), wav, OUT)
    print("done →", OUT)


if __name__ == "__main__":
    main()
