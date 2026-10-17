# -*- coding: utf-8 -*-
"""从参考图里把吉伊、小八、乌萨奇抠出来，存成带透明通道的贴图（只需运行一次）"""
import json, os
from PIL import Image, ImageDraw, ImageFilter, ImageChops

HERE = os.path.dirname(os.path.abspath(__file__))
REF = os.path.join(HERE, "sprites", "reference.png")
PANELS = {   # 名字: (面板框, 角色内部的一个点)
    "usagi": ((0, 0, 1093, 1034), (560, 700)),
    "chii": ((0, 1035, 571, 1579), (200, 1250)),
    "hachi": ((573, 1035, 1093, 1579), (830, 1420)),
}
BARRIER = 150          # 比这暗的像素算描边，挡住泛洪


def lum(p):
    return 0.3 * p[0] + 0.59 * p[1] + 0.11 * p[2]


ERASE = {
    "chii": [(0, 30, 40, 100), (300, 458, 548, 482)],
    "hachi": [(0, 446, 374, 466)],
    "usagi": [(280, 40, 362, 125)],
}


def _flood_all_borders(work, value):
    w, h = work.size
    px = work.load()
    for x in range(w):
        for y in (0, h - 1):
            if px[x, y] == 0:
                ImageDraw.floodfill(work, (x, y), value)
    for y in range(h):
        for x in (0, w - 1):
            if px[x, y] == 0:
                ImageDraw.floodfill(work, (x, y), value)


def extract(im, box, inside, close_bottom=False, r=9, shrink=False):  # r：描边断口的修补半径
    x0, y0, x1, y1 = box
    crop = im.crop(box)
    if close_bottom:      # 面板底边把角色截断了：先补一条描边封口
        ImageDraw.Draw(crop).line((0, crop.height - 3, crop.width, crop.height - 3), fill=(60, 42, 40), width=6)
    w, h = crop.size
    dark = crop.convert("L").point(lambda v: 255 if v < BARRIER else 0)
    # 描边有断口：先把描边加粗 r 像素再泛洪，泛洪完再把前景收回 r 像素
    work = dark.filter(ImageFilter.MaxFilter(2 * r + 1))
    _flood_all_borders(work, 128)
    fg = work.point(lambda v: 0 if v == 128 else 255)
    fg = fg.filter(ImageFilter.MinFilter(2 * r - 1))
    # 只保留角色那一块
    ImageDraw.floodfill(fg, (inside[0] - x0, inside[1] - y0), 200)
    mask = fg.point(lambda v: 255 if v == 200 else 0)
    # 切掉只靠细线连着的小碎块（小花、速度线、草叶）：先腐蚀断开细桥，留主体，再膨胀回来
    core = mask.filter(ImageFilter.MinFilter(9))
    ImageDraw.floodfill(core, (inside[0] - x0, inside[1] - y0), 128)
    core = core.point(lambda v: 255 if v == 128 else 0).filter(ImageFilter.MaxFilter(11))
    mask = ImageChops.multiply(mask, core)
    if shrink:      # 白底图：往里收 1 像素，去掉描边外的白边
        mask = mask.filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(0.8))
    else:
        mask = mask.filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.GaussianBlur(1.0))
    # 去掉地上的阴影和草叶（偏绿的像素）
    px = crop.load()
    mp = mask.load()
    for y in range(h):
        for x in range(w):
            if mp[x, y]:
                r_, g_, b_ = px[x, y]
                if g_ > r_ + 12 and g_ > b_ + 6:
                    mp[x, y] = 0
                elif y > h * 0.9 and max(r_, g_, b_) - min(r_, g_, b_) < 22 and 70 < (r_ + g_ + b_) / 3 < 200:
                    mp[x, y] = 0      # 脚下的灰色阴影
    out = crop.convert("RGBA")
    out.putalpha(mask)
    bb = mask.point(lambda v: 255 if v > 8 else 0).getbbox()
    return out.crop(bb), (bb[0] + x0, bb[1] + y0)


# 正面图：三位站成一排，白底
FRONT = os.path.join(HERE, "sprites", "reference_front.png")
FRONT_PANELS = {
    "usagi": ((90, 90, 470, 615), (260, 420)),     # 框互相重叠也没关系：只保留包含内部点的那一块
    "chii": ((430, 90, 815, 615), (620, 420)),
    "hachi": ((780, 90, 1190, 615), (970, 440)),
}


def _dehalo(im):
    """去掉描边外侧残留的白边：贴着透明区、又很亮的像素"""
    px = im.load()
    w, h = im.size
    a = im.getchannel("A").load()
    for y in range(1, h - 1):
        for x in range(1, w - 1):
            r, g, b, al = px[x, y]
            if al and min(a[x - 1, y], a[x + 1, y], a[x, y - 1], a[x, y + 1]) < 128 and r + g + b > 600:
                px[x, y] = (r, g, b, 0)


def main_front():
    im = Image.open(FRONT).convert("RGB")
    meta = {}
    for name, (box, inside) in FRONT_PANELS.items():
        spr, origin = extract(im, box, inside, r=6, shrink=True)
        _dehalo(spr)
        spr.save(os.path.join(HERE, "sprites", f"{name}_front.png"))
        meta[name] = dict(origin=origin, size=spr.size)
        print(name, origin, spr.size)
    json.dump(meta, open(os.path.join(HERE, "sprites", "meta_front.json"), "w"), indent=1)


def main():
    im = Image.open(REF).convert("RGB")
    meta = {}
    for name, (box, inside) in PANELS.items():
        spr, origin = extract(im, box, inside, r=13 if name == "usagi" else 9)
        d = ImageDraw.Draw(spr)
        for rect in ERASE.get(name, ()):        # 手动擦掉剩下的小花、草叶、影子
            d.rectangle(rect, fill=(0, 0, 0, 0))
        spr.save(os.path.join(HERE, "sprites", f"{name}.png"))
        meta[name] = dict(origin=origin, size=spr.size)
        print(name, origin, spr.size)
    json.dump(meta, open(os.path.join(HERE, "sprites", "meta.json"), "w"), indent=1)


if __name__ == "__main__":
    import sys
    main_front() if "front" in sys.argv else main()
