# -*- coding: utf-8 -*-
"""
程序生成的“手写风格”数字（28×28 灰度，0 = 黑，1 = 白），用于示意 MNIST 一类的输入。
不是 MNIST 原图：每个数字由折线笔画 + 随机的倾斜 / 缩放 / 平移 / 笔画粗细生成。
"""
import numpy as np

N = 28


def _circle(cx, cy, rx, ry, a0=0, a1=360, n=40):
    t = np.radians(np.linspace(a0, a1, n))
    return [(cx + rx * np.cos(x), cy + ry * np.sin(x)) for x in t]


# 坐标：x 向右，y 向下，单位 = 像素（0–28）
STROKES = {
    0: [_circle(14, 14, 6, 9)],
    1: [[(11, 8), (14.5, 5), (14.5, 23)]],
    2: [[(8, 9), (10, 6), (14, 5), (18, 6), (20, 9), (19, 12), (8, 23), (21, 23)]],
    3: [[(8, 6.5), (14, 5), (19, 7), (19, 11), (14, 13.5), (19.5, 16), (20, 20), (15, 23), (8, 22)]],
    4: [[(17, 23), (17, 5), (7, 17), (21, 17)]],
    5: [[(20, 5), (9.5, 5), (8.5, 13), (14, 12), (19, 14), (20, 19), (16, 23), (8, 22)]],
    6: [[(18, 5), (12, 8), (9, 14), (9, 19), (12, 23), (17, 23), (20, 19), (19, 15), (14, 13), (9, 16)]],
    7: [[(7, 6), (21, 6.5), (13, 23)]],
    8: [_circle(14, 9, 4.5, 4), _circle(14, 18, 5.5, 5)],
    9: [_circle(14, 10, 5, 5), [(19, 10), (17.5, 23)]],
}


def _dist_to_seg(px, py, a, b):
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    L = dx * dx + dy * dy
    t = np.clip(((px - ax) * dx + (py - ay) * dy) / L, 0, 1)
    return np.hypot(px - (ax + t * dx), py - (ay + t * dy))


def render(strokes, width=1.6, rot=0.0, scale=1.0, shift=(0.0, 0.0), slant=0.0):
    """把笔画栅格化成 28×28 数组（值域 0–1）"""
    ys, xs = np.mgrid[0:N, 0:N] + 0.5
    c = np.cos(rot)
    s = np.sin(rot)
    d = np.full((N, N), 1e9)
    for st in strokes:
        pts = []
        for x, y in st:
            x, y = x - 14, y - 14
            x = x + slant * y
            x, y = scale * (c * x - s * y), scale * (s * x + c * y)
            pts.append((x + 14 + shift[0], y + 14 + shift[1]))
        for a, b in zip(pts[:-1], pts[1:]):
            d = np.minimum(d, _dist_to_seg(xs, ys, a, b))
    return np.clip(1.6 - d / (0.7 * width), 0, 1)


def digit(k, seed=None):
    """数字 k 的一张样本；seed=None 时为“标准”写法"""
    if seed is None:
        return render(STROKES[k])
    r = np.random.default_rng(seed)
    return render(STROKES[k], width=r.uniform(1.2, 2.1), rot=r.uniform(-0.18, 0.18),
                  scale=r.uniform(0.85, 1.05), shift=(r.uniform(-1.5, 1.5), r.uniform(-1, 1)),
                  slant=r.uniform(-0.25, 0.25))


def to_rgb(a, lo=(15, 18, 26), hi=(236, 236, 236)):
    """灰度数组 → uint8 RGB 图像数组"""
    lo, hi = np.array(lo, float), np.array(hi, float)
    img = lo + (hi - lo) * a[..., None]
    return img.astype(np.uint8)


def diverging_rgb(w, neg=(88, 196, 221), pos=(255, 255, 0), mid=(15, 18, 26)):
    """有正有负的权重图：蓝 = 负，黄 = 正"""
    w = w / (np.abs(w).max() + 1e-9)
    neg, pos, mid = (np.array(x, float) for x in (neg, pos, mid))
    out = np.where(w[..., None] >= 0, mid + (pos - mid) * w[..., None], mid + (neg - mid) * (-w[..., None]))
    return out.astype(np.uint8)
