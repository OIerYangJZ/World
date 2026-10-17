# -*- coding: utf-8 -*-
"""
吉伊 / 小八 / 乌萨奇：直接用参考图抠出来的贴图（sprites/*.png）。
只有换表情时才在眼睛、嘴巴的位置贴一小块底色，再画上新表情；其余保持原图。
接口与 chiikawa.draw_buddy 相同：draw_buddy(pen, st)。
"""
import math, os
from PIL import Image, ImageDraw
from lib import Pen, Xf, ell, teardrop, lerp, SS, SWEAT, GLOOM, WHITE, mixc
from chiikawa import _eye_b, _mouth, INKB, TEAR

HERE = os.path.dirname(os.path.abspath(__file__))

# 原图里量出来的五官位置（贴图像素坐标）
SPEC = {   # 正面图（sprites/*_front.png）里量出来的五官：眼睛 (x, y, 半宽, 半高)、嘴、头顶参考点
    "chii": dict(file="chii_front", h=250, col=(250, 250, 250), eyes=[(107, 133, 20, 18), (205, 135, 19, 18)],
                 mouth=(155, 178, 19, 21), f=1.7, tilt=0.02, top=(160, 12), sweat=(245, 67)),
    "hachi": dict(file="hachi_front", h=265, col=(254, 254, 254), eyes=[(106, 155, 20, 19), (204, 162, 20, 19)],
                  mouth=(151, 201, 20, 17), f=1.75, tilt=0.07, top=(156, 37), sweat=(251, 107)),
    "usagi": dict(file="usagi_front", h=335, col=(251, 239, 207), eyes=[(112, 235, 16, 16), (204, 238, 16, 15)],
                  mouth=(152, 279, 20, 18), f=1.5, tilt=0.03, top=(162, 127), sweat=(259, 197)),
}
PRE = 1.3        # 预缩放留的余量（最大放大倍数）
_CACHE = {}


def _load(kind):
    if kind in _CACHE:
        return _CACHE[kind]
    sp = SPEC[kind]
    im = Image.open(os.path.join(HERE, "sprites", f"{sp['file']}.png")).convert("RGBA")
    a = im.getchannel("A")
    w, h = im.size
    # 脚底锚点：最下面 24 行不透明像素的平均 x
    bb = a.point(lambda v: 255 if v > 128 else 0).getbbox()
    ys = range(max(0, bb[3] - 24), bb[3])
    xs = [x for y in ys for x in range(w) if a.getpixel((x, y)) > 128]
    anchor = (sum(xs) / max(1, len(xs)), bb[3] - 4)
    s = sp["h"] * SS * PRE / h            # 预缩放到 2× 层上最大用得到的尺寸
    im = im.resize((max(1, int(w * s)), max(1, int(h * s))), Image.LANCZOS)
    _CACHE[kind] = (im, s, anchor)
    return _CACHE[kind]


def _overlay(kind, st, im, s):
    """在预缩放后的贴图上改表情（坐标：原贴图像素 × s）"""
    sp = SPEC[kind]
    eyes, m = st.get("eyes", "dot"), st.get("mouth", 0.0)
    tears, fountain, sweat, gloom = st.get("tears", 0.0), st.get("fountain"), st.get("sweat"), st.get("gloom", 0.0)
    if eyes == "dot" and m < 0.05 and tears < 0.01 and sweat is None and gloom < 0.01:
        return im
    im = im.copy()
    pen = Pen(im, oy=0, s=1)
    col = sp["col"]
    f = sp["f"] * s
    lw = 5.0 * 0.62 * f / 1.0 * 0.62
    tilt = sp["tilt"]
    if eyes != "dot":
        for j, (ex, ey, rx, ry) in enumerate(sp["eyes"]):
            pen.poly(ell(ex * s, ey * s, rx * s * 1.35, ry * s * 1.35, tilt, 28), fill=col)
            side = -1 if j == 0 else 1
            _eye_b(pen, Xf(ex * s, ey * s, f, rot=tilt), 0, 0, eyes, 4.0, side)
    if m >= 0.05:
        mx, my, mrx, mry = sp["mouth"]
        pen.poly(ell(mx * s, my * s, mrx * s * 1.3, mry * s * 1.5, tilt, 24), fill=col)
        _mouth(pen, Xf(mx * s, (my - mry * 0.4) * s, f, rot=tilt), 0, 0, m, 4.0, 1.15 if kind == "usagi" else 1.0)
    if tears > 0.01:
        for (ex, ey, rx, ry) in sp["eyes"]:
            X = Xf(ex * s, ey * s, f, rot=tilt)
            wv = 7 * tears
            pl, pr = [], []
            for i in range(9):
                u = i / 8
                yy = 10 + u * 110
                xx = 3 * math.sin(u * 9 + st.get("t", 0) * 14)
                pl.append((xx - wv, yy))
                pr.append((xx + wv, yy))
            pen.poly(X.pts(pl + pr[::-1]), fill=TEAR, ol=INKB, w=0.4 * 5 * 0.85 * f)
    tx, ty = sp["top"]
    if gloom > 0.01:
        X = Xf(tx * s, ty * s, f)
        for xx in (-30, -10, 10, 30):
            pen.line(X.pts([(xx, 34 + abs(xx) * 0.3), (xx, 60 + abs(xx) * 0.3)]), mixc(col, GLOOM, gloom), 3.5 * f)
    if sweat is not None:
        swx, swy = sp["sweat"]
        X = Xf(swx * s, swy * s, f)
        pen.poly(X.pts(teardrop(0, 24 * sweat, 30, 11, -math.pi / 2)), fill=SWEAT, ol=INKB, w=2.6 * f / 1.7)
    return im


def draw_buddy(pen, st):
    kind = st["kind"]
    sp = SPEC[kind]
    base, s, anchor = _load(kind)
    im = _overlay(kind, st, base, s)
    kk = st.get("k", 0.85) / 0.85 / PRE           # 相对预缩放的倍数
    sx, sy = st.get("sx", 1.0), st.get("sy", 1.0)
    rot = st.get("rot", 0.0) + 0.25 * st.get("ears", 0.0)
    walk = st.get("walk", 0.0)
    y = st["y"]
    if walk:
        rot += 0.05 * math.sin(st.get("step", 0.0)) * walk
    w, h = im.size
    nw, nh = max(1, int(w * kk * sx)), max(1, int(h * kk * sy))
    im = im.resize((nw, nh), Image.BICUBIC)
    ax, ay = anchor[0] * s * kk * sx, anchor[1] * s * kk * sy
    if st.get("flip"):
        im = im.transpose(Image.FLIP_LEFT_RIGHT)
        ax = nw - ax
    if abs(rot) > 0.002:
        pad = int(max(nw, nh) * 0.6)
        canvas = Image.new("RGBA", (nw + 2 * pad, nh + 2 * pad), (0, 0, 0, 0))
        canvas.paste(im, (pad, pad))
        im = canvas.rotate(-math.degrees(rot), resample=Image.BICUBIC, center=(ax + pad, ay + pad))
        ax, ay = ax + pad, ay + pad
    px, py = pen.P(st["x"], y)
    from lib import paste
    paste(pen.img, im, px - ax, py - ay)
    if st.get("fountain"):               # 喷泉泪：画在画面上，不受贴图边界限制
        t = st.get("t", 0.0)
        for j0 in range(2):
            ex, ey = feature(st, "eye%d" % j0)
            side = -1 if j0 == 0 else 1
            for j in range(12):
                p = (t * 2.4 + j / 12) % 1
                x = ex + side * (10 + 230 * p)
                yy = ey - 6 - 160 * p + 300 * p * p
                r = 8 * (1 - 0.35 * p)
                pen.poly(ell(x, yy, r, r * 1.15, n=12), fill=TEAR, ol=INKB, w=2.0)
    # 返回一个“旧设计坐标 → 画面坐标”的变换，给道具定位用（头顶约等于 head_local）
    old_h = {"chii": 262, "hachi": 300, "usagi": 420}[kind]
    unit = sp["h"] * st.get("k", 0.85) / 0.85 / old_h
    return Xf(st["x"], y, unit, sx, sy, rot)


def feature(st, name):
    """角色某个部位在画面上的位置（mouth / top）"""
    kind = st["kind"]
    sp = SPEC[kind]
    base, s, anchor = _load(kind)
    kk = st.get("k", 0.85) / 0.85
    scale = sp["h"] / (Image.open(os.path.join(HERE, "sprites", f"{sp['file']}.png")).height) * kk
    if name.startswith("eye"):
        fx, fy = sp["eyes"][int(name[3])][:2]
    else:
        fx, fy = sp["mouth"][:2] if name == "mouth" else sp["top"]
    return st["x"] + (fx - anchor[0]) * scale, st["y"] + (fy - anchor[1]) * scale
