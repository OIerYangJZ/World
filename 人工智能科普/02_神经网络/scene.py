# -*- coding: utf-8 -*-
"""
第 02 集《神经网络：一层一层的小开关》

时间全部对齐 bars.py 的 BPM 小节网格（96 BPM，130 小节）。字幕由 build.py 烧录。
    ~/.venvs/manim/bin/python ../common/build.py 02_神经网络 [--preview]
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "common"))
from style import *  # noqa: E402,F401
import digits  # noqa: E402

SEVEN = digits.digit(7)
rng = np.random.default_rng(2)


def _rgba(rgb):
    return np.dstack([rgb, np.full(rgb.shape[:2], 255, np.uint8)])


def pix_image(arr, height):
    img = ImageMobject(_rgba(digits.to_rgb(arr)))
    img.set_resampling_algorithm(RESAMPLING_ALGORITHMS["nearest"])
    img.scale_to_fit_height(height)
    return img


def rgb_image(rgb, height):
    img = ImageMobject(_rgba(rgb))
    img.set_resampling_algorithm(RESAMPLING_ALGORITHMS["nearest"])
    img.scale_to_fit_height(height)
    return img


def pixel_grid(arr, size=0.13):
    n = arr.shape[0]
    g = VGroup()
    for r in range(n):
        for c in range(n):
            v = float(arr[r, c])
            sq = Square(side_length=size, stroke_width=0.6, stroke_color="#1d2230",
                        fill_color=interpolate_color(ManimColor("#0f121a"), ManimColor(C_WHITE), v),
                        fill_opacity=1)
            sq.move_to([(c - n / 2 + 0.5) * size, -(r - n / 2 + 0.5) * size, 0])
            g.add(sq)
    return g


# 输入列只画 16 个代表（上 8 + 下 8），取“7”里亮暗不同的像素
_flat = SEVEN.flatten()
_bright = [i for i in range(784) if _flat[i] > 0.6]
_dark = [i for i in range(784) if _flat[i] < 0.05]
IN_IDX = sorted(list(rng.choice(_bright, 7, replace=False)) + list(rng.choice(_dark, 9, replace=False)))


class Net(VGroup):
    """784-16-16-10 网络示意：输入列画 16 个代表 + 省略号"""

    def __init__(self, xs=(-4.6, -1.6, 1.4, 4.4), yc=0.3, seed=5, **kw):
        super().__init__(**kw)
        r = np.random.default_rng(seed)
        self.layers = VGroup()
        cols = []
        # 输入
        inp = VGroup()
        for i in range(16):
            y = yc + (7.5 - i) * 0.26 + (0.22 if i < 8 else -0.22)
            inp.add(Circle(radius=0.09, stroke_color=C_WHITE, stroke_width=1.5,
                           fill_color=C_BLUE, fill_opacity=0).move_to([xs[0], y, 0]))
        dots = T("⋮", size=30, color=C_GREY).move_to([xs[0], yc, 0])
        cols.append(inp)
        for x, n, sp, rad in ((xs[1], 16, 0.28, 0.115), (xs[2], 16, 0.28, 0.115), (xs[3], 10, 0.44, 0.15)):
            col = VGroup()
            for i in range(n):
                y = yc + ((n - 1) / 2 - i) * sp
                col.add(Circle(radius=rad, stroke_color=C_WHITE, stroke_width=1.6,
                               fill_color=C_WHITE, fill_opacity=0).move_to([x, y, 0]))
            cols.append(col)
        self.edges = VGroup()
        for a, b in zip(cols[:-1], cols[1:]):
            eg = VGroup()
            for na in a:
                for nb in b:
                    w = r.normal()
                    eg.add(Line(na.get_center(), nb.get_center(),
                                stroke_color=C_YELLOW if w > 0 else C_BLUE,
                                stroke_width=0.4 + 0.9 * min(abs(w), 1.6), stroke_opacity=0.32))
            self.edges.add(eg)
        self.layers = VGroup(*cols)
        self.out_labels = VGroup(*[T(str(k), size=24, color=C_GREY).next_to(cols[3][k], RIGHT, buff=0.18)
                                   for k in range(10)])
        self.dots = dots
        self.add(self.edges, self.layers, dots, self.out_labels)

    def set_acts(self, layer, values):
        color = C_BLUE if layer == 0 else C_WHITE
        for n, v in zip(self.layers[layer], values):
            n.set_fill(color, opacity=float(v))
        return self

    def act_anims(self, layer, values):
        col = self.layers[layer]
        color = C_BLUE if layer == 0 else C_WHITE
        return [n.animate.set_fill(color, opacity=float(v)) for n, v in zip(col, values)]


IN_ACT = [_flat[i] for i in IN_IDX]
H1_ACT = np.clip(rng.normal(0.45, 0.3, 16), 0, 1)
H2_ACT = np.clip(rng.normal(0.4, 0.3, 16), 0, 1)
OUT_TRAINED = [0.04, 0.12, 0.1, 0.18, 0.06, 0.08, 0.03, 0.95, 0.14, 0.28]
OUT_RANDOM = list(np.clip(rng.normal(0.45, 0.08, 10), 0, 1))


class Video(BeatScene):
    EP_DIR = os.path.dirname(os.path.abspath(__file__))

    def construct(self):
        self.counter = None
        self.intro()          # 1–4
        self.verse1()         # 5–20
        self.hook(21)         # 21–30
        self.verse2()         # 31–50
        self.inst1()          # 51–54
        self.hook(55)         # 55–64
        self.verse3()         # 65–84
        self.bridge()         # 85–92
        self.verse4()         # 93–108
        self.inst2()          # 109–112
        self.hook(113)        # 113–122
        self.outro()          # 123–130
        self.finish()

    # ------------------------------------------------------------ 公共
    def forward(self, net, out_values, bars_each=0.5):
        """光脉冲逐层传过去，各层依次亮起"""
        acts = [IN_ACT, H1_ACT, H2_ACT, out_values]
        self.play_bars(*net.act_anims(0, acts[0]), bars=bars_each)
        for k in range(3):
            flashes = [ShowPassingFlash(e.copy().set_stroke(C_GOLD, width=2.2, opacity=0.9), time_width=0.5)
                       for e in net.edges[k][::3]]
            self.play_bars(LaggedStart(*flashes, lag_ratio=0.002), *net.act_anims(k + 1, acts[k + 1]),
                           bars=bars_each)

    # ------------------------------------------------------------ 前奏 1–4
    def intro(self):
        card = title_card("第 02 集", "神经网络", "一层一层的小开关")
        s, e, t, line, st = card
        self.play_bars(FadeIn(s, shift=DOWN * 0.2), FadeIn(e, shift=DOWN * 0.2), bars=0.75)
        self.play_bars(Write(t), bars=1)
        self.play_bars(GrowFromCenter(line), FadeIn(st, shift=UP * 0.2), bars=0.75)
        self.at_bar(3.5)
        self.set_counter("2", bars=0.5)
        self.at_bar(4.5)
        self.play_bars(FadeOut(card), bars=0.5)

    # ------------------------------------------------------------ 主歌一 5–20
    def verse1(self):
        self.at_bar(5)
        self.tag("回顾第 01 集")
        ax = Axes(x_range=[0, 10], y_range=[0, 10], x_length=5, y_length=3.4, tips=False,
                  axis_config=dict(color=C_GREY, stroke_width=2)).move_to([-2.2, 0.3, 0])
        pts = [(1, 2.1), (2, 2.4), (3, 3.9), (4, 4.1), (5, 5.6), (6, 5.7), (7, 7.2), (8, 7.6), (9, 8.9)]
        dots = VGroup(*[Dot(ax.c2p(x, y), radius=0.07, color=C_BLUE) for x, y in pts])
        w, b = ValueTracker(0.5), ValueTracker(3.0)
        line = always_redraw(lambda: Line(ax.c2p(0, b.get_value()), ax.c2p(10, b.get_value() + 10 * w.get_value()),
                                          color=C_YELLOW, stroke_width=4))
        kw = Knob("w", w, 0, 1.5, radius=0.45).move_to([3.0, 0.6, 0])
        kb = Knob("b", b, -2, 5, radius=0.45).move_to([4.8, 0.6, 0])
        recap = VGroup(ax, dots, kw, kb)
        self.play_bars(FadeIn(recap), Create(line), bars=0.75)
        self.play_bars(w.animate.set_value(0.85), b.animate.set_value(1.2), bars=1)
        # 7–8 手写数字
        self.at_bar(7)
        self.play_bars(FadeOut(recap), FadeOut(line), bars=0.5)
        img = pix_image(SEVEN, 3.64).move_to([0, 0.3, 0])
        q = T("手写的数字？", size=34, color=C_WHITE).next_to(img, RIGHT, buff=0.8)
        self.tag("任务：认手写数字", bars=0.25)
        self.play_bars(FadeIn(img, scale=0.9), bars=0.75)
        self.play_bars(FadeIn(q), bars=0.5)
        # 9–10 28×28 网格
        self.at_bar(9)
        grid = pixel_grid(SEVEN).move_to(img)
        self.play_bars(FadeOut(q), FadeIn(grid), FadeOut(img), bars=0.75)
        bt = Brace(grid, UP, color=C_GREY)
        bl = Brace(grid, LEFT, color=C_GREY)
        tt = T("28", size=28, color=C_GREY).next_to(bt, UP, buff=0.1)
        tl = T("28", size=28, color=C_GREY).next_to(bl, LEFT, buff=0.1)
        self.play_bars(GrowFromCenter(bt), GrowFromCenter(bl), FadeIn(tt), FadeIn(tl), bars=0.75)
        tot = T("28 × 28 = 784 个格子", size=30, color=C_BLUE).next_to(grid, RIGHT, buff=0.8)
        self.play_bars(FadeIn(tot), bars=0.5)
        # 11–12 放大看数值
        self.at_bar(11)
        r0, c0 = 4, 15                       # “7” 横笔的右端，亮暗交界处
        patch = VGroup(*[grid[r * 28 + c] for r in range(r0, r0 + 5) for c in range(c0, c0 + 5)])
        hl = SurroundingRectangle(patch, color=C_YELLOW, buff=0.02, stroke_width=3)
        big = VGroup()
        for r in range(5):
            for c in range(5):
                v = float(SEVEN[r0 + r, c0 + c])
                sq = Square(side_length=0.62, stroke_width=1.5, stroke_color="#2a2f3d",
                            fill_color=interpolate_color(ManimColor("#0f121a"), ManimColor(C_WHITE), v), fill_opacity=1)
                sq.move_to([c * 0.62, -r * 0.62, 0])
                num = T(f"{v:.1f}", size=20, color=BLACK if v > 0.55 else C_WHITE).move_to(sq)
                big.add(VGroup(sq, num))
        big.move_to([4.1, 0.6, 0])
        link = VGroup(Line(hl.get_corner(UR), big.get_corner(UL), color=C_YELLOW, stroke_width=1.5),
                      Line(hl.get_corner(DR), big.get_corner(DL), color=C_YELLOW, stroke_width=1.5))
        self.play_bars(FadeOut(tot), Create(hl), bars=0.25)
        self.play_bars(Create(link), FadeIn(big, scale=0.6), bars=1)
        legend = VGroup(*[Square(side_length=0.3, stroke_width=0,
                                 fill_color=interpolate_color(ManimColor("#0f121a"), ManimColor(C_WHITE), v), fill_opacity=1)
                          for v in np.linspace(0, 1, 11)]).arrange(RIGHT, buff=0).next_to(big, DOWN, buff=0.5)
        l0 = T("0 = 黑", size=22, color=C_GREY).next_to(legend, LEFT, buff=0.15)
        l1 = T("1 = 白", size=22, color=C_GREY).next_to(legend, RIGHT, buff=0.15)
        self.play_bars(FadeIn(legend), FadeIn(l0), FadeIn(l1), bars=0.5)
        # 13–14 抽丝成一列
        self.at_bar(13)
        self.play_bars(*[FadeOut(m) for m in (hl, link, big, legend, l0, l1, bt, bl, tt, tl)], bars=0.25)
        net = Net()
        inp = net.layers[0]
        picks = VGroup(*[grid[i].copy() for i in IN_IDX])
        self.add(picks)
        targets = VGroup(*[n.copy().set_fill(C_BLUE, opacity=float(_flat[i])) for n, i in zip(inp, IN_IDX)])
        self.play_bars(grid.animate.set_opacity(0.12).shift(LEFT * 1.6),
                       LaggedStart(*[Transform(p, t) for p, t in zip(picks, targets)], lag_ratio=0.03), bars=1.25)
        lab = T("输入层：784 个数", size=30, color=C_BLUE).next_to(inp, RIGHT, buff=0.6)
        self.play_bars(FadeIn(net.dots), FadeIn(lab), bars=0.5)
        # 15–16 MNIST
        self.at_bar(15)
        self.play_bars(FadeOut(grid), FadeOut(picks), FadeOut(net.dots), FadeOut(lab), bars=0.25)
        wall = Group()
        for j in range(4):
            for k in range(12):
                d = (k + 3 * j) % 10
                wall.add(pix_image(digits.digit(d, seed=100 + 12 * j + k), 0.95))
        wall.arrange_in_grid(rows=4, cols=12, buff=0.08).move_to([0, 0.75, 0])
        self.play_bars(LaggedStart(*[FadeIn(m, scale=0.7) for m in wall], lag_ratio=0.03), bars=1)
        mn = T("MNIST：60,000 张训练 + 10,000 张测试", size=30, color=C_GOLD).next_to(wall, DOWN, buff=0.35)
        note = T("（画面中的数字为程序生成的示意图）", size=20, color=C_GREY).next_to(mn, DOWN, buff=0.12)
        self.play_bars(FadeIn(mn), FadeIn(note), bars=0.5)
        self.at_bar(16.75)
        self.play_bars(FadeOut(wall), FadeOut(mn), FadeOut(note), bars=0.25)
        # 17–18 任务：图 → 黑箱 → 0~9
        self.at_bar(17)
        img2 = pix_image(SEVEN, 1.8).move_to([-4.6, 0.3, 0])
        box = black_box(w=2.6, h=1.9, depth=0.4).move_to([-0.6, 0.3, 0])
        outs = VGroup()
        for k in range(10):
            sq = Square(side_length=0.42, stroke_color=C_GOLD, stroke_width=2)
            outs.add(VGroup(sq, T(str(k), size=24, color=C_GOLD).move_to(sq)))
        outs.arrange(DOWN, buff=0.06).move_to([4.2, 0.3, 0])
        a1 = Arrow(img2.get_right(), box.front.get_left(), buff=0.15, color=C_GREY)
        a2 = Arrow(box.front.get_right() + RIGHT * 0.4, outs.get_left(), buff=0.15, color=C_GREY)
        self.play_bars(FadeIn(img2), GrowArrow(a1), FadeIn(box), GrowArrow(a2),
                       LaggedStart(*[FadeIn(o) for o in outs], lag_ratio=0.08), bars=1.25)
        self.play_bars(Indicate(outs[7], color=C_GOLD, scale_factor=1.3), bars=0.5)
        # 19–20 掀开盖子
        self.at_bar(19)
        mini = Net().scale(0.25).move_to(box.front)
        mini.edges.set_stroke(width=0.35, opacity=0.18)
        mini.set_opacity(0.6)
        self.play_bars(VGroup(box.front, box.q).animate.shift(UP * 0.3).set_opacity(0.12), FadeIn(mini), bars=1)
        self.at_bar(20.5)
        self.fade_rest(0.5)

    # ------------------------------------------------------------ 副歌
    def hook(self, s):
        self.at_bar(s)
        self.tag("一层一层的小开关")
        lamp = Circle(radius=0.6, stroke_color=C_WHITE, stroke_width=4, fill_color=C_GOLD, fill_opacity=0).move_to([1.2, 0.4, 0])
        halo = Circle(radius=1.1, stroke_width=0, fill_color=C_GOLD, fill_opacity=0).move_to(lamp)
        self.play_bars(FadeIn(lamp), bars=0.5)
        self.add(halo)
        self.play_bars(lamp.animate.set_fill(opacity=0.9), halo.animate.set_fill(opacity=0.18), bars=1)
        self.at_bar(s + 2)
        # ② 加权求和，够亮才点明
        ins = VGroup(*[Circle(radius=0.2, stroke_color=C_WHITE, stroke_width=2, fill_color=C_BLUE, fill_opacity=v)
                       .move_to([-3.0, 0.4 + dy, 0]) for v, dy in ((0.9, 1.3), (0.3, 0.0), (0.7, -1.3))])
        lines = VGroup(*[Line(c.get_right(), lamp.get_left(), color=col, stroke_width=wd)
                         for c, col, wd in zip(ins, (C_YELLOW, C_BLUE, C_YELLOW), (5, 2, 4))])
        meter = Rectangle(width=0.35, height=2.4, stroke_color=C_GREY, stroke_width=2).move_to([3.4, 0.4, 0])
        th = DashedLine(meter.get_left() + LEFT * 0.15 + UP * 0.2, meter.get_right() + RIGHT * 0.15 + UP * 0.2,
                        color=C_RED, stroke_width=3)
        lvl = ValueTracker(0.0)
        fill = always_redraw(lambda: Rectangle(width=0.29, height=max(2.34 * lvl.get_value(), 0.01), stroke_width=0,
                                               fill_color=C_GOLD, fill_opacity=0.9)
                             .move_to(meter).align_to(meter, DOWN).shift(UP * 0.03))
        thl = T("门槛", size=22, color=C_RED).next_to(th, RIGHT, buff=0.1)
        self.play_bars(lamp.animate.set_fill(opacity=0), halo.animate.set_fill(opacity=0),
                       FadeIn(ins), Create(lines), FadeIn(meter), Create(th), FadeIn(thl), FadeIn(fill), bars=0.75)
        pulses = [Dot(c.get_right(), radius=0.07, color=C_GOLD) for c in ins]
        self.play_bars(*[MoveAlongPath(p, l) for p, l in zip(pulses, lines)], lvl.animate.set_value(0.8), bars=0.75)
        self.remove(*pulses)
        self.play_bars(lamp.animate.set_fill(opacity=0.9), halo.animate.set_fill(opacity=0.18), bars=0.5)
        # ③ 一层传一层
        self.at_bar(s + 4)
        self.play_bars(*[FadeOut(m) for m in (lamp, halo, ins, lines, meter, th, thl, fill)], bars=0.25)
        sizes = [3, 4, 4, 2]
        xs = [-3.0, -1.0, 1.0, 3.0]
        cols = VGroup()
        for x, n in zip(xs, sizes):
            cols.add(VGroup(*[Circle(radius=0.28, stroke_color=C_WHITE, stroke_width=2.5, fill_color=C_GOLD,
                                     fill_opacity=0).move_to([x, 0.4 + ((n - 1) / 2 - i) * 0.9, 0]) for i in range(n)]))
        eds = VGroup(*[Line(a.get_center(), b.get_center(), stroke_width=1.5, color=C_GREY, stroke_opacity=0.6)
                       for c1, c2 in zip(cols[:-1], cols[1:]) for a in c1 for b in c2])
        self.play_bars(Create(eds), FadeIn(cols), bars=0.75)
        r = np.random.default_rng(s)
        for col in cols:
            self.play_bars(*[n.animate.set_fill(opacity=float(r.uniform(0.25, 1))) for n in col], bars=0.25)
        # ④ 拼出整片风景：灯阵
        self.at_bar(s + 6)
        self.play_bars(FadeOut(cols), FadeOut(eds), bars=0.25)
        lamps = VGroup()
        W, H = 16, 8
        for i in range(H):
            for j in range(W):
                x, y = (j - (W - 1) / 2) * 0.48, 0.4 + ((H - 1) / 2 - i) * 0.48
                u, v = j / (W - 1), 1 - i / (H - 1)
                moon = (u - 0.75) ** 2 + (v - 0.78) ** 2 < 0.018
                mount = v < 0.55 - 0.9 * abs(u - 0.35) or v < 0.38 - 0.7 * abs(u - 0.8)
                val = 1.0 if moon else (0.7 if mount else 0.06)
                col = C_GOLD if moon else (C_TEAL if mount else C_WHITE)
                c = Circle(radius=0.17, stroke_color=C_DARK, stroke_width=1.5, fill_color=col, fill_opacity=0.04)
                c.move_to([x, y, 0])
                c.target_val = val
                lamps.add(c)
        self.play_bars(FadeIn(lamps), bars=0.5)
        self.play_bars(LaggedStart(*[l.animate.set_fill(opacity=l.target_val) for l in lamps], lag_ratio=0.006),
                       bars=1.25)
        # ⑤ 一层一层，把黑箱打开
        self.at_bar(s + 8)
        self.play_bars(FadeOut(lamps), bars=0.25)
        box = black_box(w=3.6, h=2.4, depth=0.5).move_to([0, 0.2, 0])
        mini = Net().set_acts(0, IN_ACT).set_acts(1, H1_ACT).set_acts(2, H2_ACT).set_acts(3, OUT_TRAINED)
        mini.scale(0.33).move_to(box.front)
        mini.edges.set_stroke(width=0.4, opacity=0.22)
        self.play_bars(FadeIn(box), bars=0.25)
        self.play_bars(VGroup(box.front, box.q).animate.shift(UP * 0.3).set_opacity(0.12), FadeIn(mini), bars=0.5)
        slogan = T("一层一层，把黑箱打开", size=40, color=C_YELLOW, weight=BOLD).to_edge(UP, buff=0.3)
        self.play_bars(Write(slogan), bars=0.5)
        self.at_bar(s + 9.5)
        self.fade_rest(0.5)

    # ------------------------------------------------------------ 主歌二 31–50：一个神经元
    def verse2(self):
        self.at_bar(31)
        self.tag("一个神经元")
        vals = [0.9, 0.1, 0.7, 0.0]
        wts = [0.8, -0.5, 0.3, 1.2]
        ys = [1.65, 0.75, -0.15, -1.05]
        ins = VGroup(*[Circle(radius=0.28, stroke_color=C_WHITE, stroke_width=2, fill_color=C_BLUE, fill_opacity=v)
                       .move_to([-5.2, y, 0]) for v, y in zip(vals, ys)])
        inl = VGroup(*[T(f"{v:.1f}", size=22, color=C_BLUE).next_to(c, LEFT, buff=0.15) for v, c in zip(vals, ins)])
        neu = Circle(radius=0.55, stroke_color=C_WHITE, stroke_width=3, fill_color=C_WHITE, fill_opacity=0).move_to([-1.6, 0.3, 0])
        lines = VGroup(*[Line(c.get_right(), neu.get_center() + 0.55 * normalize(c.get_center() - neu.get_center()),
                              color=C_GREY, stroke_width=2) for c in ins])
        self.play_bars(FadeIn(ins), FadeIn(inl), Create(lines), FadeIn(neu), bars=1.25)
        # 33–34 权重
        self.at_bar(33)
        wl = VGroup()
        for ln, w in zip(lines, wts):
            col = C_YELLOW if w > 0 else C_BLUE
            t = T(f"{w:+.1f}", size=22, color=col).move_to(ln.point_from_proportion(0.42) + UP * 0.22)
            wl.add(t)
        self.play_bars(*[ln.animate.set_stroke(C_YELLOW if w > 0 else C_BLUE, width=1.5 + 3 * abs(w))
                         for ln, w in zip(lines, wts)], LaggedStart(*[FadeIn(t) for t in wl], lag_ratio=0.2), bars=1)
        # 35–36 乘积求和
        self.at_bar(35)
        terms = [f"{v:.1f}×{w:.1f}" if w > 0 else f"{v:.1f}×({w:.1f})" for v, w in zip(vals, wts)]
        parts = []
        for i, t in enumerate(terms):
            if i:
                parts.append(T("+", size=28, color=C_WHITE))
            parts.append(T(t, size=28, color=C_WHITE))
        eq = VGroup(*parts).arrange(RIGHT, buff=0.12).move_to([3.3, 2.2, 0])
        if eq.width > 6.4:
            eq.scale_to_fit_width(6.4)
        self.play_bars(LaggedStart(*[FadeIn(p, shift=DOWN * 0.15) for p in parts], lag_ratio=0.15), bars=1.25)
        s1 = T("= 0.88", size=34, color=C_WHITE).next_to(eq, DOWN, buff=0.3).align_to(eq, LEFT)
        self.play_bars(FadeIn(s1), bars=0.5)
        # 37–38 要 / 不
        self.at_bar(37)
        yn = VGroup(*[T("要" if w > 0 else "不", size=26, color=C_YELLOW if w > 0 else C_BLUE)
                      .next_to(c, RIGHT, buff=0.12).shift(UP * 0.28) for c, w in zip(ins, wts)])
        self.play_bars(LaggedStart(*[FadeIn(x, scale=1.4) for x in yn], lag_ratio=0.2), bars=1)
        # 39–40 偏置与门槛
        self.at_bar(39)
        bias = T("+ 偏置 b = −0.3", size=30, color=C_YELLOW).next_to(s1, DOWN, buff=0.3).align_to(eq, LEFT)
        s2 = T("= 0.58", size=34, color=C_GOLD).next_to(bias, DOWN, buff=0.25).align_to(eq, LEFT)
        bl = Line(neu.get_bottom() + DOWN * 0.05, neu.get_bottom() + DOWN * 0.7, color=C_YELLOW, stroke_width=3)
        bt = T("b", size=26, color=C_YELLOW).next_to(bl, DOWN, buff=0.08)
        self.play_bars(FadeOut(yn), FadeIn(bias), Create(bl), FadeIn(bt), bars=0.75)
        self.play_bars(FadeIn(s2), bars=0.5)
        thr = T("偏置像门槛：b 越小，越难亮", size=22, color=C_GREY).next_to(s2, RIGHT, buff=0.4)
        self.play_bars(FadeIn(thr), bars=0.5)
        # 41–42 ReLU
        self.at_bar(41)
        rax = Axes(x_range=[-1, 1, 0.5], y_range=[0, 1, 0.5], x_length=3.0, y_length=1.6, tips=False,
                   axis_config=dict(color=C_GREY, stroke_width=2)).move_to([3.0, -1.35, 0])
        relu = VGroup(Line(rax.c2p(-1, 0), rax.c2p(0, 0)), Line(rax.c2p(0, 0), rax.c2p(1, 1))).set_stroke(C_GREEN, 4)
        rl = T("ReLU：负数 → 0，正数照常", size=22, color=C_GREEN).next_to(rax, UP, buff=0.15)
        z = ValueTracker(0.58)
        zdot = always_redraw(lambda: Dot(rax.c2p(z.get_value(), max(z.get_value(), 0)), radius=0.08, color=C_GOLD))
        zt = always_redraw(lambda: T(f"{z.get_value():+.2f} → {max(z.get_value(), 0):.2f}", size=22, color=C_GOLD)
                           .next_to(rax, RIGHT, buff=0.25))
        self.play_bars(FadeOut(thr), Create(rax), Create(relu), FadeIn(rl), FadeIn(zdot), FadeIn(zt), bars=0.75)
        self.play_bars(z.animate.set_value(-0.4), bars=0.75)
        self.play_bars(z.animate.set_value(0.58), bars=0.5)
        # 43–44 亮度
        self.at_bar(43)
        outv = T("0.58", size=26, color=BLACK, weight=BOLD).move_to(neu)
        glow = Circle(radius=0.95, stroke_width=0, fill_color=C_GOLD, fill_opacity=0).move_to(neu)
        self.add(glow)
        self.play_bars(neu.animate.set_fill(C_GOLD, opacity=0.58), glow.animate.set_fill(opacity=0.12), FadeIn(outv), bars=1)
        # 45–46 sigmoid vs ReLU
        self.at_bar(45)
        rgrp = VGroup(rax, relu)
        self.play_bars(FadeOut(zt), FadeOut(zdot), FadeOut(rl), rgrp.animate.move_to([1.4, -1.35, 0]), bars=0.5)
        sax = rax.copy().move_to([5.0, -1.35, 0])
        sig = sax.plot(lambda x: 1 / (1 + np.exp(-6 * x)), x_range=[-1, 1], color=C_PURPLE, stroke_width=4)
        sl = T("S 形曲线（sigmoid，早期常用）", size=20, color=C_PURPLE).next_to(sax, UP, buff=0.15)
        rl = T("ReLU（现在常用）", size=22, color=C_GREEN).next_to(rax, UP, buff=0.15)
        self.play_bars(Create(sax), Create(sig), FadeIn(sl), FadeIn(rl), bars=0.75)
        self.neuron_parts = Group(ins, inl, neu, lines, wl, eq, s1, bias, s2, bl, bt, rax, relu, rl, outv, glow, sax, sig, sl)
        # 47–48 一个神经元看全部像素
        self.at_bar(47)
        self.play_bars(*[FadeOut(m) for m in self.neuron_parts], bars=0.25)
        self.tag("一层", bars=0.25)
        net = Net().set_acts(0, IN_ACT)
        self.net = net
        inp = net.layers[0]
        n0 = net.layers[1][7].copy().scale(2.2).move_to([-1.6, 0.3, 0])
        fan = VGroup(*[Line(c.get_center(), n0.get_center(), stroke_width=0.9,
                            color=C_YELLOW if i % 3 else C_BLUE, stroke_opacity=0.5) for i, c in enumerate(inp)])
        self.play_bars(FadeIn(inp), FadeIn(net.dots), Create(fan), FadeIn(n0), bars=1)
        fl = T("784 根连线 = 784 个权重（旋钮）", size=26, color=C_YELLOW).move_to([2.6, 2.6, 0])
        self.play_bars(FadeIn(fl), bars=0.5)
        # 49–50 并排 16 个
        self.at_bar(49)
        h1 = net.layers[1]
        self.play_bars(FadeOut(fan), ReplacementTransform(n0, h1[7]),
                       LaggedStart(*[FadeIn(n, scale=0.5) for i, n in enumerate(h1) if i != 7], lag_ratio=0.05),
                       Create(net.edges[0]), bars=1.25)
        ll = T("第一层：16 个神经元", size=26, color=C_WHITE).move_to([2.6, 2.0, 0])
        self.play_bars(FadeIn(ll), bars=0.5)
        self.v2_labels = VGroup(fl, ll)

    # ------------------------------------------------------------ 间奏一 51–54：前向计算
    def inst1(self):
        self.at_bar(51)
        net = self.net
        img = pix_image(SEVEN, 1.3).move_to([-6.3, 0.3, 0])
        self.play_bars(FadeOut(self.v2_labels), FadeIn(img), Create(net.edges[1]), Create(net.edges[2]),
                       FadeIn(net.layers[2]), FadeIn(net.layers[3]), FadeIn(net.out_labels), bars=0.75)
        self.forward(net, OUT_RANDOM, bars_each=0.5)
        self.at_bar(54.5)
        self.fade_rest(0.5)

    # ------------------------------------------------------------ 主歌三 65–84：整个网络
    def verse3(self):
        self.at_bar(65)
        self.tag("整个网络")
        net = Net()
        heads = VGroup(*[T(t, size=26, color=c).next_to(col, UP, buff=0.25)
                         for t, c, col in zip(["784", "16", "16", "10"], [C_BLUE, C_WHITE, C_WHITE, C_GOLD], net.layers)])
        heads[0].shift(UP * 0.05)
        self.play_bars(FadeIn(net), FadeIn(heads), bars=1)
        # 67–68 隐藏层
        self.at_bar(67)
        hid = DashedVMobject(SurroundingRectangle(VGroup(net.layers[1], net.layers[2]), color=C_PURPLE, buff=0.25,
                                                  corner_radius=0.15), num_dashes=60)
        hl = T("隐藏层", size=28, color=C_PURPLE).next_to(hid, DOWN, buff=0.12)
        self.play_bars(Create(hid), FadeIn(hl), bars=1)
        # 69–70 前向传递
        self.at_bar(69)
        self.forward(net, OUT_TRAINED, bars_each=0.4375)
        # 71–72 最亮的就是答案
        self.at_bar(71)
        ring = Circle(radius=0.27, color=C_GOLD, stroke_width=4).move_to(net.layers[3][7])
        ans = T("判为 7", size=30, color=C_GOLD).next_to(net.out_labels[7], RIGHT, buff=0.25)
        demo = T("（示意：假设旋钮已经训练好）", size=20, color=C_GREY).next_to(hl, DOWN, buff=0.12)
        self.play_bars(Create(ring), FadeIn(ans), FadeIn(demo), bars=1)
        self.at_bar(72.5)
        self.play_bars(FadeOut(VGroup(ring, ans, demo, hid, hl)), bars=0.5)
        # 73–74 数旋钮
        self.at_bar(73)
        self.tag("数一数旋钮")
        grp = VGroup(net, heads)
        self.play_bars(grp.animate.scale(0.72).move_to([-2.3, 0.2, 0]), bars=0.5)
        self.play_bars(LaggedStart(*[ShowPassingFlash(e.copy().set_stroke(C_YELLOW, width=2.5, opacity=1), time_width=0.6)
                                     for eg in net.edges for e in eg[::4]], lag_ratio=0.001), bars=0.5)
        self.play_bars(*[Indicate(n, color=C_YELLOW, scale_factor=1.25) for col in net.layers[1:] for n in col], bars=0.5)
        # 75–76 公式
        self.at_bar(75)
        rows = VGroup(
            T("784 × 16 + 16 = 12,560", size=28, color=C_YELLOW),
            T("16 × 16 + 16 = 272", size=28, color=C_YELLOW),
            T("16 × 10 + 10 = 170", size=28, color=C_YELLOW),
        ).arrange(DOWN, aligned_edge=RIGHT, buff=0.3).move_to([4.1, 1.3, 0])
        cap = T("权重 + 偏置", size=22, color=C_GREY).next_to(rows, UP, buff=0.25)
        self.play_bars(FadeIn(cap), FadeIn(rows[0], shift=LEFT * 0.2), bars=0.75)
        self.play_bars(FadeIn(rows[1], shift=LEFT * 0.2), bars=0.5)
        self.play_bars(FadeIn(rows[2], shift=LEFT * 0.2), bars=0.5)
        # 77–78 合计
        self.at_bar(77)
        rule = Line(rows.get_corner(DL) + DOWN * 0.15, rows.get_corner(DR) + DOWN * 0.15, color=C_GREY)
        total = T("合计 13,002", size=40, color=C_YELLOW, weight=BOLD).next_to(rule, DOWN, buff=0.25).align_to(rows, RIGHT)
        self.play_bars(Create(rule), FadeIn(total, scale=1.2), bars=0.75)
        for t in ["30", "500", "4,000", "9,800", "13,002"]:
            self.set_counter(t, bars=0.15)
        # 79–80 ×6500
        self.at_bar(79)
        times = VGroup(T("2", size=40, color=C_YELLOW), T("→", size=40, color=C_GREY),
                       T("13,002", size=40, color=C_YELLOW), T("约 6,500 倍", size=30, color=C_WHITE)
                       ).arrange(RIGHT, buff=0.25)
        if times.width > 4.6:
            times.scale_to_fit_width(4.6)
        times.move_to([4.2, -1.4, 0])
        self.play_bars(FadeIn(times, shift=UP * 0.2), bars=1)
        # 81–82 每盏灯都有开关
        self.at_bar(81)

        def relu_icon(c):
            r_ = c.width / 2
            return VGroup(Line(LEFT * r_ * 0.6, ORIGIN), Line(ORIGIN, (RIGHT + UP) * r_ * 0.6)).set_stroke(C_GREEN, 2.5).move_to(c)

        icons = VGroup(*[relu_icon(n) for col in net.layers[1:] for n in col])
        self.play_bars(FadeOut(VGroup(rows, cap, rule, total, times)),
                       LaggedStart(*[FadeIn(i, scale=1.6) for i in icons], lag_ratio=0.01), bars=1)
        sw = T("每个神经元：加权求和 → 开关", size=24, color=C_GREEN).move_to([4.3, 1.0, 0])
        self.play_bars(FadeIn(sw), bars=0.5)
        # 83–84 拿掉开关？
        self.at_bar(83)
        qm = T("为什么非要开关？", size=36, color=C_WHITE, weight=BOLD).move_to([4.3, -0.4, 0])
        self.play_bars(FadeIn(qm, scale=1.2), bars=0.5)
        self.play_bars(LaggedStart(*[i.animate.set_opacity(0.1) for i in icons], lag_ratio=0.01), bars=0.75)
        self.at_bar(84.5)
        self.fade_rest(0.5)

    # ------------------------------------------------------------ 桥段 85–92：非线性
    def bridge(self):
        self.at_bar(85)
        self.tag("为什么要开关")
        plane = NumberPlane(x_range=[-7, 7, 1], y_range=[-3, 3, 1], x_length=12.4, y_length=5.3,
                            background_line_style=dict(stroke_color=C_BLUE, stroke_opacity=0.35, stroke_width=1.5),
                            axis_config=dict(stroke_color=C_GREY)).move_to([0, 0.3, 0])
        A = np.array([[1.0, 0.7], [0.15, 1.0]])
        B = np.array([[0.85, -0.45], [0.35, 0.9]])
        lab = T("第 1 层（只有加权求和）", size=28, color=C_WHITE)
        lab.add_background_rectangle(color=BG, opacity=0.85, buff=0.1)
        lab.move_to([0, 2.7, 0])
        self.play_bars(Create(plane), FadeIn(lab), bars=0.5)
        self.play_bars(plane.animate.apply_matrix(A, about_point=plane.c2p(0, 0)), bars=0.75)
        lab2 = T("第 2 层（只有加权求和）", size=28, color=C_WHITE)
        lab2.add_background_rectangle(color=BG, opacity=0.85, buff=0.1)
        lab2.move_to(lab)
        self.play_bars(Transform(lab, lab2), plane.animate.apply_matrix(B, about_point=plane.c2p(0, 0)), bars=1)
        lab3 = T("两层 = 一次加权求和：网格线永远笔直", size=28, color=C_YELLOW)
        lab3.add_background_rectangle(color=BG, opacity=0.85, buff=0.1)
        lab3.move_to(lab)
        self.play_bars(Transform(lab, lab3), bars=0.75)
        self.at_bar(88.5)
        self.play_bars(FadeOut(plane), FadeOut(lab), bars=0.5)
        # 89–92 折纸
        self.at_bar(89)
        u = 1.05
        o = np.array([-0.6, 0.25, 0])
        r = np.random.default_rng(9)
        blue, red = [], []
        while len(blue) < 34:
            p = r.uniform(-1, 1, 2)
            if abs(p[0]) + abs(p[1]) < 0.85:
                blue.append(p)
        while len(red) < 46:
            p = r.uniform(-2.1, 2.1, 2)
            if 1.35 < abs(p[0]) + abs(p[1]) < 2.05:
                red.append(p)
        ax = Axes(x_range=[-2.3, 2.3], y_range=[-2.3, 2.3], x_length=4.6 * u, y_length=4.6 * u, tips=False,
                  axis_config=dict(color=C_GREY, stroke_width=1.5)).move_to(o)
        self.fold_ax = ax
        bd = VGroup(*[Dot(ax.c2p(*p), radius=0.07, color=C_BLUE) for p in blue])
        rd = VGroup(*[Dot(ax.c2p(*p), radius=0.07, color=C_RED) for p in red])
        self.play_bars(FadeIn(ax), FadeIn(bd), FadeIn(rd), bars=0.5)
        ln = Line(ax.c2p(-2.3, -1.6), ax.c2p(2.3, 1.2), color=C_YELLOW, stroke_width=4)
        self.play_bars(Create(ln), bars=0.25)
        self.play_bars(Rotate(ln, angle=PI * 0.6, about_point=ax.c2p(0, 0)), bars=0.5)
        nope = T("一条直线分不开", size=26, color=C_YELLOW).move_to([4.3, 1.8, 0])
        self.add(nope)
        crease = DashedLine(ax.c2p(0, -2.3), ax.c2p(0, 2.3), color=C_GREEN, stroke_width=4)
        f1 = T("开关 ①：沿竖线对折", size=26, color=C_GREEN).move_to([4.3, 1.0, 0])
        self.play_bars(FadeOut(ln), Create(crease), FadeIn(f1), bars=0.25)
        moves = [d.animate.move_to(ax.c2p(abs(p[0]), p[1])) for d, p in zip(list(bd) + list(rd), blue + red) if p[0] < 0]
        self.play_bars(*moves, bars=1)
        crease2 = DashedLine(ax.c2p(-2.3, 0), ax.c2p(2.3, 0), color=C_GREEN, stroke_width=4)
        f2 = T("开关 ②：沿横线对折", size=26, color=C_GREEN).move_to([4.3, 0.3, 0])
        self.play_bars(Create(crease2), FadeIn(f2), bars=0.25)
        moves = [d.animate.move_to(ax.c2p(abs(p[0]), abs(p[1]))) for d, p in zip(list(bd) + list(rd), blue + red) if p[1] < 0]
        self.play_bars(*moves, bars=0.75)
        self.fold = VGroup(ax, bd, rd, crease, crease2, nope, f1, f2)

    # ------------------------------------------------------------ 主歌四 93–108
    def verse4(self):
        self.at_bar(93)
        self.tag("折一折，就分开了")
        ax = self.fold_ax
        sep_long = Line(ax.c2p(-0.2, 1.35), ax.c2p(1.35, -0.2), color=C_YELLOW, stroke_width=5)
        ok = T("折两次后：一条直线就分开", size=26, color=C_YELLOW).move_to([4.3, -0.5, 0])
        self.play_bars(Create(sep_long), FadeIn(ok), bars=0.75)
        card = T("|x| = ReLU(x) + ReLU(−x)：对折 = 两个开关", size=22, color=C_GREY).move_to([4.0, -1.4, 0])
        self.play_bars(FadeIn(card), bars=0.5)
        self.at_bar(94.75)
        self.play_bars(FadeOut(VGroup(self.fold, sep_long, ok, card)), bars=0.25)
        # 95–96 万能逼近
        self.at_bar(95)
        self.tag("万能逼近")
        ax2 = Axes(x_range=[-3, 3], y_range=[-1.6, 1.6], x_length=8.4, y_length=4.2, tips=False,
                   axis_config=dict(color=C_GREY, stroke_width=1.5)).move_to([-1.0, 0.3, 0])

        def f(x):
            return 0.9 * np.sin(1.3 * x) + 0.25 * x

        target = DashedVMobject(ax2.plot(f, x_range=[-3, 3], color=C_WHITE, stroke_width=3), num_dashes=70)

        def pl(k):
            xs = np.linspace(-3, 3, k + 1)
            return VMobject(stroke_color=C_GOLD, stroke_width=5).set_points_as_corners([ax2.c2p(x, f(x)) for x in xs])

        approx = pl(2)
        kl = T("2 段折线", size=30, color=C_GOLD).move_to([4.9, 1.6, 0])
        self.play_bars(Create(ax2), Create(target), bars=0.5)
        self.play_bars(Create(approx), FadeIn(kl), bars=0.25)
        for k in (5, 20):
            kl2 = T(f"{k} 段折线", size=30, color=C_GOLD).move_to(kl)
            self.play_bars(Transform(approx, pl(k)), Transform(kl, kl2), bars=0.5)
        # 97–98 定理卡
        self.at_bar(97)
        thm = VGroup(T("万能逼近定理（大白话）", size=30, color=C_YELLOW, weight=BOLD),
                     T("神经元足够多，就存在一个网络能把连续函数逼近得任意好", size=24, color=C_WHITE),
                     T("只保证“存在”：不保证训练得出来，也不保证数据够用", size=24, color=C_RED)
                     ).arrange(DOWN, buff=0.22)
        thm_bg = SurroundingRectangle(thm, color=C_YELLOW, buff=0.3, corner_radius=0.12, fill_color=BG, fill_opacity=0.92)
        VGroup(thm_bg, thm).move_to([0, -1.25, 0])
        self.play_bars(FadeIn(thm_bg), FadeIn(thm, shift=UP * 0.2), bars=1)
        self.at_bar(98.75)
        self.fade_rest(0.25)
        # 99–100 生物神经细胞 vs 人工神经元
        self.at_bar(99)
        self.tag("“神经元”只是个比喻")
        r = np.random.default_rng(4)
        soma_c = np.array([-3.6, 0.4, 0])
        soma = Circle(radius=0.42, stroke_color=C_TEAL, stroke_width=3, fill_color=C_TEAL, fill_opacity=0.25).move_to(soma_c)

        def branches(start, ang, length, depth, width):
            g = VGroup()
            end = start + length * np.array([np.cos(ang), np.sin(ang), 0])
            g.add(Line(start, end, color=C_TEAL, stroke_width=width))
            if depth > 0:
                for da in (-0.45, 0.4):
                    g.add(*branches(end, ang + da + r.uniform(-0.15, 0.15), length * 0.68, depth - 1, width * 0.7))
            return g

        dend = VGroup(*[branches(soma_c + 0.42 * np.array([np.cos(a), np.sin(a), 0]), a, 0.7, 2, 3)
                        for a in np.linspace(PI * 0.55, PI * 1.45, 4)])
        axon = Line(soma_c + RIGHT * 0.42, soma_c + RIGHT * 2.3, color=C_TEAL, stroke_width=3.5)
        term = VGroup(*[Line(axon.get_end(), axon.get_end() + 0.4 * np.array([np.cos(a), np.sin(a), 0]),
                             color=C_TEAL, stroke_width=2) for a in (-0.6, 0, 0.6)])
        bio = VGroup(dend, soma, axon, term)
        bl = T("生物神经细胞（示意）", size=24, color=C_TEAL).move_to([-3.2, -1.7, 0])
        art_n = Circle(radius=0.55, stroke_color=C_WHITE, stroke_width=3).move_to([3.6, 0.4, 0])
        art_in = VGroup(*[Line(art_n.get_center() + np.array([-2.0, dy, 0]), art_n.get_left(), color=C_YELLOW, stroke_width=2)
                          for dy in (-0.9, -0.3, 0.3, 0.9)])
        sig = T("Σ", size=40, color=C_WHITE).move_to(art_n)
        art_out = Arrow(art_n.get_right(), art_n.get_right() + RIGHT * 1.1, buff=0, color=C_GOLD)
        art = VGroup(art_in, art_n, sig, art_out)
        al = T("人工神经元：加权求和 + 开关", size=24, color=C_WHITE).move_to([3.6, -1.7, 0])
        self.play_bars(Create(bio), FadeIn(bl), bars=1)
        self.play_bars(FadeIn(art), FadeIn(al), bars=0.5)
        insp = T("受大脑启发的比喻", size=30, color=C_YELLOW).move_to([0, 2.5, 0])
        self.play_bars(FadeIn(insp), bars=0.25)
        # 101–102 复杂得多
        self.at_bar(101)
        more = VGroup(*[branches(soma_c + 0.42 * np.array([np.cos(a), np.sin(a), 0]), a, 0.55, 3, 2)
                        for a in np.linspace(PI * 0.3, PI * 1.7, 9)])
        self.play_bars(Create(more), bars=1)
        neq = T("≠", size=72, color=C_RED).move_to([0.2, 0.4, 0])
        insp2 = T("受启发的比喻，不是模拟大脑", size=30, color=C_YELLOW).move_to(insp)
        self.play_bars(FadeIn(neq, scale=1.5), Transform(insp, insp2), bars=0.75)
        self.at_bar(102.75)
        self.fade_rest(0.25)
        # 103–104 希望：每个神经元找一种笔画
        self.at_bar(103)
        self.tag("隐藏层在找什么？")
        img = pix_image(SEVEN, 1.9).move_to([-4.6, 0.3, 0])
        strokes = [digits.render([[(7, 6), (21, 6.5)]]), digits.render([[(21, 6.5), (13, 23)]]),
                   digits.render([digits._circle(14, 14, 6, 6)])]
        names = ["横", "斜竖", "圈"]
        hs = Group()
        for k, (st, nm) in enumerate(zip(strokes, names)):
            c = Circle(radius=0.32, stroke_color=C_WHITE, stroke_width=2.5).move_to([-0.8, 1.6 - 1.3 * k, 0])
            im = pix_image(st, 1.0).next_to(c, RIGHT, buff=0.45)
            t = T(nm, size=24, color=C_GREY).next_to(im, RIGHT, buff=0.25)
            hs.add(Group(c, im, t))
        arrs = VGroup(*[Arrow(img.get_right(), g[0].get_left(), buff=0.12, color=C_GREY, stroke_width=2) for g in hs])
        self.play_bars(FadeIn(img), LaggedStart(*[GrowArrow(a) for a in arrs], lag_ratio=0.2),
                       LaggedStart(*[FadeIn(g) for g in hs], lag_ratio=0.2), bars=1.25)
        hope = T("希望：每个隐藏神经元找一种笔画", size=24, color=C_GREEN).move_to([4.4, 2.3, 0])
        self.play_bars(FadeIn(hope), bars=0.5)
        # 105–106 实际：杂乱
        self.at_bar(105)
        r2 = np.random.default_rng(21)
        noisy = []
        for _ in range(3):
            w = r2.normal(0, 1, (28, 28))
            for _ in range(2):
                w = (w + np.roll(w, 1, 0) + np.roll(w, -1, 0) + np.roll(w, 1, 1) + np.roll(w, -1, 1)) / 5
            noisy.append(rgb_image(digits.diverging_rgb(w), 1.0))
        anims = []
        for g, nz in zip(hs, noisy):
            nz.move_to(g[1])
            anims += [FadeOut(g[1]), FadeIn(nz), g[2].animate.set_opacity(0)]
        self.play_bars(*anims, bars=1)
        real = T("实际：学到的权重往往杂乱、不好解释", size=24, color=C_RED).move_to([4.4, 1.6, 0])
        real2 = T("（示意图；黄 = 正权重，蓝 = 负权重）", size=20, color=C_GREY).next_to(real, DOWN, buff=0.12)
        self.play_bars(FadeIn(real), FadeIn(real2), hope.animate.set_opacity(0.35), bars=0.5)
        self.at_bar(106.75)
        self.fade_rest(0.25)
        # 107–108 准确率
        self.at_bar(107)
        self.tag("训练好之后")
        frame = Rectangle(width=8.0, height=0.55, stroke_color=C_GREY, stroke_width=2).move_to([0, 0.6, 0])
        fill = Rectangle(width=0.01, height=0.45, stroke_width=0, fill_color=C_GREEN, fill_opacity=0.9)
        fill.move_to(frame).align_to(frame, LEFT).shift(RIGHT * 0.05)
        fill_t = fill.copy().stretch_to_fit_width(7.9 * 0.96).align_to(fill, LEFT)
        acc = T("测试集准确率 ≈ 96% 以上", size=36, color=C_GREEN, weight=BOLD).next_to(frame, UP, buff=0.35)
        nt = T("具体数值与训练设置有关；“怎么训练”下两集讲", size=22, color=C_GREY).next_to(frame, DOWN, buff=0.3)
        self.play_bars(Create(frame), Transform(fill, fill_t), FadeIn(acc), FadeIn(nt), bars=1.25)
        self.at_bar(108.5)
        self.fade_rest(0.5)

    # ------------------------------------------------------------ 间奏二 109–112：要点
    def inst2(self):
        self.at_bar(109)
        self.tag("本集要点")
        head = T("本集要点", size=46, color=C_YELLOW, weight=BOLD)
        pts = [
            "1. 输入：28×28 的图 = 784 个 0～1 之间的数",
            "2. 神经元：加权求和 + 偏置，再过开关（ReLU）；输出 = 亮度",
            "3. 网络：784 → 16 → 16 → 10，共 13,002 个旋钮",
            "4. 开关让每一层能“折”空间；“神经元”只是受大脑启发的比喻",
        ]
        items = VGroup(*[T(p, size=30) for p in pts]).arrange(DOWN, aligned_edge=LEFT, buff=0.32)
        g = VGroup(head, items).arrange(DOWN, buff=0.5).move_to([0, 0.35, 0])
        self.play_bars(FadeIn(head, shift=DOWN * 0.2), bars=0.25)
        for it in items:
            self.play_bars(FadeIn(it, shift=RIGHT * 0.3), bars=0.5)
        self.at_bar(112.5)
        self.play_bars(FadeOut(g), bars=0.5)

    # ------------------------------------------------------------ 尾声 123–130
    def outro(self):
        self.at_bar(123)
        self.tag("回顾")
        steps = [("加权", C_YELLOW), ("求和", C_WHITE), ("偏置", C_YELLOW), ("开关", C_GREEN), ("下一层", C_BLUE)]
        chips = VGroup()
        for s_, col in steps:
            t = T(s_, size=32, color=col)
            chips.add(VGroup(SurroundingRectangle(t, color=col, buff=0.18, corner_radius=0.12, stroke_width=2.5), t))
        chips.arrange(RIGHT, buff=0.7).move_to([0, 0.6, 0])
        arrows = VGroup(*[Arrow(chips[i].get_right(), chips[i + 1].get_left(), buff=0.08, color=C_GREY, stroke_width=3,
                                max_tip_length_to_length_ratio=0.35) for i in range(4)])
        self.play_bars(FadeIn(chips[0]), bars=0.3)
        for i in range(1, 5):
            self.play_bars(GrowArrow(arrows[i - 1]), FadeIn(chips[i]), bars=0.3)
        # 125–126 整个网络
        self.at_bar(125)
        self.play_bars(FadeOut(chips), FadeOut(arrows), bars=0.25)
        net = Net().scale(0.8).move_to([0.2, 0.25, 0])
        l_in = T("784 进", size=28, color=C_BLUE).next_to(net.layers[0], UP, buff=0.2)
        l_out = T("10 出", size=28, color=C_GOLD).next_to(net.layers[3], UP, buff=0.2)
        self.play_bars(FadeIn(net), FadeIn(l_in), FadeIn(l_out), Indicate(self.counter, color=C_YELLOW), bars=1)
        # 127–128 随机：乱猜
        self.at_bar(127)
        img = pix_image(SEVEN, 1.2).move_to([-5.6, 0.25, 0])
        self.play_bars(FadeIn(img), bars=0.25)
        self.forward(net, OUT_RANDOM, bars_each=0.25)
        bad = T("旋钮全随机：乱猜", size=30, color=C_RED).move_to([0.2, -2.3, 0])
        self.play_bars(FadeIn(bad), bars=0.5)
        self.at_bar(128.75)
        self.fade_rest(0.25)
        # 129–130 下集
        self.at_bar(129)
        ax = Axes(x_range=[-3, 3], y_range=[0, 4], x_length=6, y_length=3, tips=False,
                  axis_config=dict(color=C_GREY, stroke_width=1.5)).move_to([-2.4, 0.2, 0])
        valley = ax.plot(lambda x: 0.35 * x ** 2 + 0.3 * np.sin(2 * x) + 0.4, x_range=[-3, 3], color=C_RED, stroke_width=4)
        x0 = -2.4
        ball = Dot(ax.c2p(x0, 0.35 * x0 ** 2 + 0.3 * np.sin(2 * x0) + 0.4) + UP * 0.13, radius=0.13, color=C_GREEN)
        nxt = VGroup(T("下集", size=30, color=C_GREY), T("梯度下降", size=48, color=C_GREEN, weight=BOLD),
                     T("蒙着眼睛下山", size=32, color=C_GREEN)).arrange(DOWN, buff=0.25).move_to([3.6, 0.4, 0])
        self.play_bars(Create(ax), Create(valley), FadeIn(ball), FadeIn(nxt, shift=UP * 0.2), bars=1)
        self.at_bar(130.25)
        self.play_bars(*[FadeOut(m) for m in self.visible()], bars=0.75)
