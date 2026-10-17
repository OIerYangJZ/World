# -*- coding: utf-8 -*-
"""吉伊 / 小八 / 乌萨奇 的同人画法（照着参考图复刻比例与五官；与 lib.py 共用画笔和表情）"""
import math
from lib import (Xf, ell, arc, chaikin, teardrop, lerp, clamp, mixc, _eye,
                 WHITE, BLUSH, MOUTH, TONGUE, SWEAT, GLOOM)

INKB = (60, 42, 40)              # 参考图的描边更黑更粗
BUDDY_WHITE = (255, 255, 255)
USAGI_C = (255, 243, 206)
HACHI_BLUE = (122, 168, 216)
EAR_PINK = (244, 178, 192)
BLUSH_B = (246, 168, 180)
BLUSH_LINE = (226, 112, 134)
TEAR = (170, 216, 250)

# 身体：中心 y、半宽、半高、下半身收窄程度、眼睛半间距、眼睛高度（相对中心）
SHAPE = {   # 头：中心 hy、半宽 hrx、半高 hry；身子：中心 by、半宽 brx、半高 bry；眼睛半间距 ex、相对头心高度 ey
    "chii":  dict(hy=-146, hrx=116, hry=104, by=-62, brx=96, bry=64, ex=38, ey=10),
    "hachi": dict(hy=-170, hrx=100, hry=94, by=-62, brx=76, bry=64, ex=38, ey=14),
    "usagi": dict(hy=-168, hrx=114, hry=106, by=-70, brx=94, bry=72, ex=40, ey=6),
}


def head_local(kind):
    return {"chii": -262, "hachi": -300, "usagi": -420}[kind]


def _sup(cx, cy, rx, ry, n_top, n_bot, m=72):
    pts = []
    for i in range(m):
        a = 2 * math.pi * i / m
        c, si = math.cos(a), math.sin(a)
        n = n_top if si < 0 else n_bot
        pts.append((cx + rx * math.copysign(abs(c) ** (2 / n), c), cy + ry * math.copysign(abs(si) ** (2 / n), si)))
    return pts


def head_pts(kind):
    s = SHAPE[kind]
    return _sup(0, s["hy"], s["hrx"], s["hry"], 2.0, 2.1)


def body_only_pts(kind):
    s = SHAPE[kind]
    return _sup(0, s["by"], s["brx"], s["bry"], 2.2, 2.6)


def _eye_b(pen, X, cx, cy, kind, lw, side):
    if kind == "cry":
        pen.line(X.pts([(cx - 11 * side, cy - 7), (cx + 9 * side, cy), (cx - 11 * side, cy + 7)]), INKB, lw * 0.95)
        return
    if kind in ("dot", "teary", "blank"):
        rx, ry = (11, 13) if kind != "blank" else (8, 9.5)
        pen.poly(X.pts(ell(cx, cy, rx, ry, n=26)), fill=INKB)
        pen.poly(X.pts(ell(cx + 1.5, cy - ry * 0.32, rx * 0.55, ry * 0.46, n=16)), fill=WHITE)
        if kind != "blank":
            pen.poly(X.pts(ell(cx - 1, cy + ry * 0.55, rx * 0.5, ry * 0.16, n=12)), fill=(120, 110, 120))
        if kind == "teary":
            pen.poly(X.pts(ell(cx, cy + 13, 12, 4.5, n=16)), fill=TEAR, ol=INKB, w=lw * 0.45)
        return
    _eye(pen, X, cx, cy, kind, lw)


def _omega(pen, X, cx, cy, lw, w=1.0, curl=False):
    for s in (-1, 1):
        pen.line(X.pts(arc(cx + s * 5.2 * w, cy, 5.2 * w, 4.6, 0.1, math.pi - 0.1, 8)), INKB, lw * 0.7)
    if curl:                                        # 乌萨奇上翘的嘴角
        for s in (-1, 1):
            pen.line(X.pts(arc(cx + s * (10.4 * w + 3.5), cy - 1, 3.5, 4.5, math.pi if s > 0 else 0, math.pi * 1.6 if s > 0 else -0.6 * math.pi, 6)),
                     INKB, lw * 0.7)


def _mouth(pen, X, cx, cy, m, lw, w=1.0, curl=False):
    if m < 0.05:
        _omega(pen, X, cx, cy, lw, w, curl)
        return
    h = 5 + 20 * m
    ww = (9 + 7 * m) * w
    pen.poly(X.pts(chaikin([(cx - ww, cy - 2), (cx + ww, cy - 2), (cx + ww * 0.55, cy + h), (cx - ww * 0.55, cy + h)], 3)),
             fill=MOUTH, ol=INKB, w=lw * 0.7)
    pen.poly(X.pts(ell(cx, cy + h * 0.68, ww * 0.55, h * 0.27, n=18)), fill=TONGUE)
    _omega(pen, X, cx, cy - 2, lw * 0.9, w * 0.9)


def draw_buddy(pen, st):
    """
    st：kind('chii'/'hachi'/'usagi')、x、y（脚底）、k、sx、sy、rot、face(-1..1)、eyes、mouth、
    al/ar（手臂 0 垂 .. 1 举 .. 1.4 高举）、step/walk、brow(None/'angry'/'worry')、
    ears（乌萨奇耳朵摆动）、tears、fountain、sweat、gloom、t
    """
    kind = st["kind"]
    s = SHAPE[kind]
    k = st.get("k", 0.85)
    X = Xf(st["x"], st["y"], k, st.get("sx", 1.0), st.get("sy", 1.0), st.get("rot", 0.0))
    lw = 5.0 * k
    face = st.get("face", 0.0)
    fx = 18 * face
    bcy, rx, ry = s["hy"], s["hrx"], s["hry"]
    top = bcy - ry
    bot_ry = s["bry"]
    bby, brx = s["by"], s["brx"]
    col = USAGI_C if kind == "usagi" else BUDDY_WHITE

    brx = s["brx"]
    # 小脚
    ph, walk = st.get("step", 0.0), st.get("walk", 0.0)
    for side, sgn in ((-1, 1), (1, -1)):
        lift = max(0.0, sgn * math.sin(ph)) * 11 * walk
        pen.poly(X.pts(ell(side * brx * 0.45 + face * 8, -6 - lift, 20, 12, n=22)), fill=col, ol=INKB, w=lw * 0.8)

    # 耳朵（身体后面）
    if kind == "chii":
        for side in (-1, 1):
            pen.poly(X.pts(ell(fx * 0.3 + side * 54, top + 16, 17, 16, n=24)), fill=col, ol=INKB, w=lw * 0.8)
    elif kind == "hachi":
        for side in (-1, 1):
            bx, by = fx * 0.3 + side * 52, top + 30
            tri = [(bx - side * 34, by + 4), (bx + side * 38, by + 18), (bx + side * 24, by - 62)]
            pen.poly(X.pts(chaikin(tri, 2)), fill=HACHI_BLUE, ol=INKB, w=lw * 0.8)
    else:
        ea = st.get("ears", 0.0)
        for side in (-1, 1):
            a = 0.22 + side * 0.07 + ea
            bx, by = fx * 0.3 + side * 30 + 14, top + 26
            cx, cy = bx + math.sin(a) * 78, by - math.cos(a) * 78
            pen.poly(X.pts(ell(cx, cy, 25, 84, a, 40)), fill=col, ol=INKB, w=lw * 0.85)
            cx2, cy2 = bx + math.sin(a) * 84, by - math.cos(a) * 84
            pen.poly(X.pts(ell(cx2, cy2, 11, 62, a, 30)), fill=EAR_PINK)

    # 头 + 身子：先描两者的粗轮廓，再盖填充，只留下外轮廓（没有下巴线）
    body = head_pts(kind)
    torso = body_only_pts(kind)
    for shp in (torso, body):
        pen.poly(X.pts(shp), fill=INKB, ol=INKB, w=lw * 2)
    for shp in (torso, body):
        pen.poly(X.pts(shp), fill=col)

    # 小八的蓝色头发：下沿是平缓的波浪，正中间微微往上收
    if kind == "hachi":
        cxh = fx * 0.6
        base_y = top + 0.68 * ry

        def yb(x):
            u = abs(x - cxh) / (rx * 0.42)
            return base_y - 16 * max(0.0, 1 - u) ** 1.4 + 7 * math.sin(min(u, 2.2) * 2.4)
        cap = [p for p in body if p[1] < yb(p[0])]
        if len(cap) > 3:
            xs = [lerp(cap[-1][0], cap[0][0], i / 40) for i in range(41)]
            pen.poly(X.pts(cap + [(x, yb(x)) for x in xs]), fill=HACHI_BLUE)
            pen.line(X.pts([(x, yb(x)) for x in xs]), INKB, lw * 0.75)
            pen.line(X.pts(cap), INKB, lw * 0.5)

    g = st.get("gloom", 0.0)
    if g > 0.01:
        for xx in (-30, -10, 10, 30):
            t0 = top + (60 if kind == "hachi" else 20) + abs(xx) * 0.3
            pen.line(X.pts([(fx * 0.5 + xx, t0), (fx * 0.5 + xx, t0 + 26)]), mixc(col, GLOOM, g), lw * 0.7, caps=False)

    ex0, ey = s["ex"], bcy + s["ey"]
    # 腮红：在眼睛外下方
    for side in (-1, 1):
        bx, by = fx * 0.8 + side * (ex0 + 36), ey + 12
        pen.poly(X.pts(ell(bx, by, 25, 15, n=24)), fill=mixc(col, BLUSH_B, 0.85))
        for j in (-1.5, -0.5, 0.5, 1.5):
            pen.line(X.pts([(bx + j * 8 - 3.5, by + 7), (bx + j * 8 + 3.5, by - 7)]), BLUSH_LINE, lw * 0.4)

    # 眼睛 + 眉毛
    eyes = st.get("eyes", "dot")
    brow = st.get("brow")
    for side in (-1, 1):
        ex = fx + side * ex0
        _eye_b(pen, X, ex, ey, eyes, lw, side)
        if kind == "usagi" and brow is None:
            pen.line(X.pts(arc(ex + side * 4, ey - 26, 22, 22, math.pi * 1.12, math.pi * 1.88, 12)), INKB, lw * 0.7)
        elif brow == "angry":
            pen.line(X.pts([(ex + side * 13, ey - 30), (ex - side * 8, ey - 22)]), INKB, lw * 0.75)
        elif kind != "usagi" or brow == "worry":
            # 吉伊、小八标志性的小八字眉（内侧略高）
            yb_ = ey - (28 if brow == "worry" else 25)
            pen.line(X.pts(arc(ex - side * 1, yb_ + (4 if brow != "worry" else 2), 9, 4, math.pi * 1.15, math.pi * 1.85, 6)), INKB, lw * 0.55)

    # 嘴
    _mouth(pen, X, fx, ey + 18, st.get("mouth", 0.0), lw, 1.7 if kind == "usagi" else 1.45, curl=kind == "usagi")

    tears = st.get("tears", 0.0)
    if tears > 0.01:
        for side in (-1, 1):
            ex = fx + side * ex0
            wv = 7 * tears
            pl, pr = [], []
            for i in range(9):
                u = i / 8
                yy = ey + 8 + u * (bby + bot_ry * 0.7 - ey)
                xx = ex + side * 4 * u + 3 * math.sin(u * 9 + st.get("t", 0) * 14)
                pl.append((xx - wv, yy))
                pr.append((xx + wv, yy))
            pen.poly(X.pts(pl + pr[::-1]), fill=TEAR, ol=INKB, w=lw * 0.4)
    if st.get("fountain"):
        t = st.get("t", 0.0)
        for side in (-1, 1):
            ex = fx + side * ex0
            for j in range(12):
                p = (t * 2.4 + j / 12) % 1
                x = ex + side * (14 + 300 * p)
                y = ey - 6 - 210 * p + 380 * p * p
                r = 9 * (1 - 0.35 * p)
                pen.poly(X.pts(ell(x, y, r, r * 1.15, n=12)), fill=TEAR, ol=INKB, w=lw * 0.4)

    # 小手：贴在身体前侧的小短手
    for side, key in ((-1, "al"), (1, "ar")):
        a = st.get(key, 0.0)
        ang = math.radians(lerp(70, -60, a)) if a <= 1 else math.radians(lerp(-60, -100, (a - 1) / 0.4))
        dx, dy = math.cos(ang) * side, math.sin(ang)
        bx0, by0 = side * (brx * 0.9), bby - bot_ry * 0.25
        pen.poly(X.pts(ell(bx0 + dx * 12, by0 + dy * 12, 17, 11, math.atan2(dy, dx), n=24)), fill=col, ol=INKB, w=lw * 0.75)

    sw = st.get("sweat")
    if sw is not None:
        side = 1 if face <= 0 else -1
        pen.poly(X.pts(teardrop(side * (rx + 8), top + 40 + 24 * sw, 32, 12, -math.pi / 2)), fill=SWEAT, ol=INKB, w=lw * 0.6)
    return X
