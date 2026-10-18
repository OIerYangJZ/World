# -*- coding: utf-8 -*-
"""
第 04 集《反向传播：把错误一层层传回去》

时间全部对齐 bars.py 的 BPM 小节网格（95 BPM，130 小节）。字幕由 build.py 烧录。
    ~/.venvs/manim/bin/python ../common/build.py 04_反向传播 [--preview]
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "common"))
from style import *  # noqa: E402,F401
import digits  # noqa: E402

THREE = digits.digit(3)


def _rgba(rgb):
    return np.dstack([rgb, np.full(rgb.shape[:2], 255, np.uint8)])


def pix_image(arr, height):
    img = ImageMobject(_rgba(digits.to_rgb(arr)))
    img.set_resampling_algorithm(RESAMPLING_ALGORITHMS["nearest"])
    img.scale_to_fit_height(height)
    return img


def mini_knob(r=0.13, color=C_YELLOW):
    c = Circle(radius=r, stroke_color=color, stroke_width=2, fill_color=C_DARK, fill_opacity=1)
    p = Line(ORIGIN, UP * r * 0.85, stroke_color=color, stroke_width=2.5)
    return VGroup(c, p)


def gear(r, color, teeth=None, depth=0.14):
    n = teeth or max(6, int(round(r * 11)))
    pts = []
    for k in range(n):
        a0 = TAU * k / n
        da = TAU / n
        for frac, rad in ((0.0, r), (0.15, r + depth), (0.45, r + depth), (0.6, r)):
            a = a0 + frac * da
            pts.append([rad * np.cos(a), rad * np.sin(a), 0])
    pts.append(pts[0])
    g = VMobject(stroke_color=color, stroke_width=3, fill_color=color, fill_opacity=0.15).set_points_as_corners(pts)
    hub = Circle(radius=min(0.12, r * 0.3), stroke_color=color, stroke_width=3)
    spoke = Line(ORIGIN, RIGHT * r * 0.8, stroke_color=color, stroke_width=4)
    return VGroup(g, hub, spoke)


class LayerNet(VGroup):
    """简化的分层网络示意"""

    def __init__(self, sizes, xs, yc=0.3, spacing=None, radius=0.14, seed=1, edge_opacity=0.35, **kw):
        super().__init__(**kw)
        r = np.random.default_rng(seed)
        self.cols = VGroup()
        for x, n in zip(xs, sizes):
            sp = spacing or min(0.5, 4.2 / max(n - 1, 1))
            self.cols.add(VGroup(*[Circle(radius=radius, stroke_color=C_WHITE, stroke_width=2, fill_color=C_WHITE,
                                          fill_opacity=0).move_to([x, yc + ((n - 1) / 2 - i) * sp, 0]) for i in range(n)]))
        self.W = []
        self.edges = VGroup()
        for a, b in zip(self.cols[:-1], self.cols[1:]):
            w = r.normal(0, 1, (len(b), len(a)))
            self.W.append(w)
            eg = VGroup()
            for j, nb in enumerate(b):
                for i, na in enumerate(a):
                    eg.add(Line(na.get_center(), nb.get_center(), stroke_color=C_YELLOW if w[j, i] > 0 else C_BLUE,
                                stroke_width=0.6 + 0.8 * min(abs(w[j, i]), 1.5), stroke_opacity=edge_opacity))
            self.edges.add(eg)
        self.add(self.edges, self.cols)

    def edge(self, k, j, i):
        """第 k 组连线中，后一层第 j 个 ← 前一层第 i 个"""
        return self.edges[k][j * len(self.cols[k]) + i]

    def set_acts(self, k, vals, color=C_WHITE):
        for n, v in zip(self.cols[k], vals):
            n.set_fill(color, opacity=float(v))
        return self

    def back_flash(self, k, color=C_RED, width=3, every=1):
        return [ShowPassingFlash(Line(e.get_end(), e.get_start(), color=color, stroke_width=width), time_width=0.6)
                for e in self.edges[k][::every]]

    def fwd_flash(self, k, color=C_BLUE, width=2.5, every=1):
        return [ShowPassingFlash(e.copy().set_stroke(color, width=width, opacity=1), time_width=0.6)
                for e in self.edges[k][::every]]


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

    # ------------------------------------------------------------ 前奏 1–4
    def intro(self):
        card = title_card("第 04 集", "反向传播", "把错误一层层传回去")
        s, e, t, line, st = card
        self.play_bars(FadeIn(s, shift=DOWN * 0.2), FadeIn(e, shift=DOWN * 0.2), bars=0.75)
        self.play_bars(Write(t), bars=1)
        self.play_bars(GrowFromCenter(line), FadeIn(st, shift=UP * 0.2), bars=0.75)
        self.at_bar(3.5)
        self.set_counter("13,002", bars=0.5)
        self.at_bar(4.5)
        self.play_bars(FadeOut(card), bars=0.5)

    # ------------------------------------------------------------ 主歌一 5–20：笨办法
    def verse1(self):
        self.at_bar(5)
        self.tag("回顾：反着梯度走")
        cen = np.array([0, 0.3, 0])
        ells = VGroup(*[Ellipse(width=2 * r * 1.6, height=2 * r, stroke_width=2.5,
                                stroke_color=interpolate_color(ManimColor(C_TEAL), ManimColor(C_RED), i / 5)).move_to(cen)
                        for i, r in enumerate([0.25, 0.5, 0.75, 1.0, 1.25, 1.5])])
        p0 = cen + np.array([-1.9, 1.05, 0])
        arr = Arrow(p0, p0 + np.array([0.55, -0.9, 0]), buff=0, color=C_GREEN, stroke_width=6)
        self.play_bars(FadeIn(ells), FadeIn(Dot(p0, color=C_WHITE)), bars=0.5)
        self.play_bars(GrowArrow(arr), bars=0.75)
        self.at_bar(6.75)
        self.fade_rest(0.25)
        # 7–8 一万三千个坡度？
        self.at_bar(7)
        self.tag("13,002 个坡度怎么求？")
        grid = VGroup(*[mini_knob(0.11) for _ in range(24 * 12)]).arrange_in_grid(rows=12, cols=24, buff=0.16)
        grid.move_to([0, 0.45, 0])
        qs = VGroup(*[T("?", size=16, color=C_RED).next_to(k, UR, buff=-0.04) for k in grid[::7]])
        self.grid = grid
        self.play_bars(LaggedStart(*[FadeIn(k) for k in grid], lag_ratio=0.002), bars=1)
        self.play_bars(FadeIn(qs), bars=0.5)
        # 9–10 笨办法：拧一个，算一遍
        self.at_bar(9)
        self.tag("笨办法")
        self.play_bars(FadeOut(qs), grid.animate.scale(0.55).move_to([-3.9, 0.6, 0]), bars=0.5)
        k0 = grid[0]
        hl = SurroundingRectangle(k0, color=C_GOLD, buff=0.04)
        net = LayerNet([4, 5, 5, 3], [1.4, 2.8, 4.2, 5.6], yc=0.6, radius=0.13, seed=3)
        self.play_bars(Create(hl), Rotate(k0[1], -0.7, about_point=k0[0].get_center()), FadeIn(net), bars=0.5)
        self.play_bars(*[LaggedStart(*net.fwd_flash(k), lag_ratio=0.02) for k in range(3)], bars=0.5)
        rec = T("记下：损失 +0.3", size=24, color=C_RED).move_to([3.5, -1.7, 0])
        self.play_bars(FadeIn(rec), bars=0.25)
        # 11–12 一万三千遍
        self.at_bar(11)
        cnt = ValueTracker(1)
        num = always_redraw(lambda: T(f"已算 {int(cnt.get_value()):,} 遍", size=34, color=C_GOLD).move_to([3.5, -1.7, 0]))
        self.play_bars(FadeOut(rec), FadeIn(num), bars=0.25)
        flashes = [Indicate(k, color=C_GOLD, scale_factor=1.6) for k in grid[::3]]
        self.play_bars(LaggedStart(*flashes, lag_ratio=0.01), cnt.animate.set_value(13002), hl.animate.move_to(grid[-1]),
                       *[LaggedStart(*net.fwd_flash(k, every=2), lag_ratio=0.01) for k in range(3)],
                       bars=1.5, rate_func=linear)
        self.remove(num)
        num_final = T("已算 13,002 遍", size=34, color=C_GOLD).move_to([3.5, -1.7, 0])
        self.add(num_final)
        # 13–14 每遍都是完整前向
        self.at_bar(13)
        glass = VGroup(Triangle(color=C_GREY, fill_opacity=0.2).scale(0.32).rotate(PI),
                       Triangle(color=C_GREY, fill_opacity=0.2).scale(0.32)).arrange(DOWN, buff=0).move_to([3.5, 2.5, 0])
        each = T("每一遍 = 整个网络从头算一次", size=24, color=C_GREY).next_to(num_final, DOWN, buff=0.2)
        self.play_bars(FadeIn(glass), FadeIn(each), bars=0.5)
        self.play_bars(Rotate(glass, PI), bars=0.75)
        self.play_bars(Rotate(glass, PI), bars=0.75)
        # 15–16 上千亿？崩成灰
        self.at_bar(15)
        big = T("× 1750 亿？（例如 GPT-3）", size=36, color=C_RED, weight=BOLD).move_to([-3.9, -1.9, 0])
        self.play_bars(FadeIn(big, scale=1.3), bars=0.5)
        self.play_bars(grid.animate.set_color(C_GREY).set_opacity(0.3).shift(DOWN * 0.3), bars=0.75)
        self.play_bars(FadeOut(grid, shift=DOWN * 0.6), bars=0.5)
        self.at_bar(16.75)
        self.fade_rest(0.25)
        # 17–18 一次算出全部？
        self.at_bar(17)
        self.tag("有没有更聪明的办法？")
        idea = T("一次算出全部 13,002 个坡度？", size=40, color=C_WHITE, weight=BOLD).move_to([0, 0.6, 0])
        self.play_bars(Write(idea), bars=1)
        self.at_bar(18.75)
        self.play_bars(FadeOut(idea), bars=0.25)
        # 19–20 从错误出发往回摸
        self.at_bar(19)
        net = LayerNet([4, 6, 6, 3], [-4.2, -1.8, 0.6, 3.0], yc=0.4, radius=0.17, seed=5)
        net.set_acts(3, [0.15, 0.9, 0.2])
        x_ = T("✗", size=40, color=C_RED, weight=BOLD).next_to(net.cols[3][1], RIGHT, buff=0.3)
        self.play_bars(FadeIn(net), bars=0.5)
        self.play_bars(net.cols[3][1].animate.set_stroke(C_RED, width=4), FadeIn(x_, scale=1.5), bars=0.5)
        back = Arrow([4.8, -1.4, 0], [-4.8, -1.4, 0], buff=0, color=C_RED, stroke_width=6)
        bl = T("从错误出发，往回走", size=28, color=C_RED).next_to(back, DOWN, buff=0.15)
        self.play_bars(GrowArrow(back), FadeIn(bl), bars=0.5)
        self.at_bar(20.5)
        self.fade_rest(0.5)

    # ------------------------------------------------------------ 副歌
    def hook(self, s):
        self.at_bar(s)
        self.tag("把错误一层层传回去")
        net = LayerNet([3, 4, 4, 3], [-4.2, -2.0, 0.2, 2.4], yc=0.4, spacing=0.9, radius=0.22, seed=s, edge_opacity=0.5)
        net.set_acts(0, [0.8, 0.3, 0.6]).set_acts(1, [0.5, 0.9, 0.2, 0.6]).set_acts(2, [0.7, 0.1, 0.8, 0.4])
        self.play_bars(FadeIn(net), bars=0.5)
        self.play_bars(*[LaggedStart(*net.fwd_flash(k), lag_ratio=0.03) for k in range(3)],
                       net.cols[3][0].animate.set_fill(C_WHITE, 0.9), bars=0.5)
        wrong = T("✗ 答错了", size=30, color=C_RED, weight=BOLD).next_to(net.cols[3][0], RIGHT, buff=0.35)
        self.play_bars(net.cols[3][0].animate.set_stroke(C_RED, width=5), FadeIn(wrong, scale=1.3), bars=0.5)
        # ② 从最后一层往回
        self.at_bar(s + 2)
        self.play_bars(LaggedStart(*net.back_flash(2, width=5), lag_ratio=0.05), bars=1)
        self.play_bars(*[n.animate.set_stroke(C_RED, width=3) for n in net.cols[2]], bars=0.5)
        # ③ 链式法则：齿轮
        self.at_bar(s + 4)
        gA, gB, gC = gear(0.42, C_YELLOW), gear(0.21, C_ORANGE), gear(0.1, C_RED, teeth=6)
        gA.move_to([4.4, -1.4, 0])
        gB.move_to(gA.get_center() + RIGHT * 0.77)
        gC.move_to(gB.get_center() + RIGHT * 0.45)
        gears = VGroup(gA, gB, gC)
        self.play_bars(FadeIn(gears), LaggedStart(*net.back_flash(1, width=5), lag_ratio=0.05), bars=1)
        self.play_bars(Rotate(gA, -PI, about_point=gA.get_center()), Rotate(gB, 2 * PI, about_point=gB.get_center()),
                       Rotate(gC, -6 * PI, about_point=gC.get_center()),
                       LaggedStart(*net.back_flash(0, width=5), lag_ratio=0.05), bars=1, rate_func=linear)
        # ④ 每个旋钮那一份
        self.at_bar(s + 6)
        knobs = VGroup()
        for k in range(3):
            for e in net.edges[k]:
                kn = mini_knob(0.1).move_to(e.point_from_proportion(0.5))
                knobs.add(kn)
        self.play_bars(FadeIn(knobs), bars=0.5)
        r = np.random.default_rng(s + 1)
        self.play_bars(*[Rotate(kn[1], float(r.uniform(-2.2, 2.2)), about_point=kn[0].get_center()) for kn in knobs],
                       bars=1.25)
        # ⑤ 黑箱
        self.at_bar(s + 8)
        self.fade_rest(0.25)
        box = black_box(w=3.2, h=2.2, depth=0.45).move_to([0, 0.2, 0])
        inner = LayerNet([3, 4, 3], [-0.9, 0, 0.9], yc=0.2, spacing=0.45, radius=0.1, seed=2, edge_opacity=0.6)
        inner.move_to(box.front)
        self.play_bars(FadeIn(box), bars=0.25)
        self.play_bars(VGroup(box.front, box.q).animate.shift(UP * 0.3).set_opacity(0.12), FadeIn(inner),
                       *[LaggedStart(*inner.back_flash(k, width=3), lag_ratio=0.05) for k in (1, 0)], bars=0.5)
        slogan = T("一层一层，把黑箱打开", size=40, color=C_YELLOW, weight=BOLD).to_edge(UP, buff=0.3)
        self.play_bars(Write(slogan), bars=0.5)
        self.at_bar(s + 9.5)
        self.fade_rest(0.5)

    # ------------------------------------------------------------ 主歌二 31–50：最后一层
    def verse2(self):
        self.at_bar(31)
        self.tag("看最后一层")
        r = np.random.default_rng(7)
        img = pix_image(THREE, 1.4).move_to([-6.0, 0.3, 0])
        dots = T("⋯", size=40, color=C_GREY).move_to([-4.75, 0.3, 0])
        net = LayerNet([16, 10], [-3.3, 0.5], yc=0.3, radius=0.12, seed=11, edge_opacity=0.3)
        net.cols[1].arrange(DOWN, buff=0.22).move_to([0.5, 0.3, 0])
        # 重新连线（输出层位置改过）
        net.remove(net.edges)
        W = net.W[0]
        eg = VGroup()
        for j, nb in enumerate(net.cols[1]):
            for i, na in enumerate(net.cols[0]):
                eg.add(Line(na.get_center(), nb.get_center(), stroke_color=C_YELLOW if W[j, i] > 0 else C_BLUE,
                            stroke_width=0.6 + 0.8 * min(abs(W[j, i]), 1.5), stroke_opacity=0.3))
        net.edges = VGroup(eg)
        net.add_to_back(net.edges)
        hid = np.clip(r.uniform(0, 1, 16) ** 1.5, 0, 1)
        hid[[2, 6, 11]] = [0.95, 0.9, 0.85]
        out = np.clip(r.uniform(0, 0.25, 10), 0, 1)
        out[8], out[3] = 0.88, 0.18
        net.set_acts(0, hid).set_acts(1, out)
        labs = VGroup(*[T(str(k), size=22, color=C_GREY).next_to(net.cols[1][k], RIGHT, buff=0.15) for k in range(10)])
        self.net, self.hid, self.W = net, hid, W
        self.play_bars(FadeIn(img), FadeIn(dots), FadeIn(net), FadeIn(labs), bars=1)
        x8 = T("✗ 认成了 8", size=26, color=C_RED).next_to(labs[8], RIGHT, buff=0.25)
        self.play_bars(net.cols[1][8].animate.set_stroke(C_RED, width=4), FadeIn(x8), bars=0.5)
        # 33–34 期望：3 亮，其他暗
        self.at_bar(33)
        want = VGroup()
        for k in range(10):
            n_ = net.cols[1][k]
            if k == 3:
                want.add(Arrow(n_.get_center() + RIGHT * 0.65 + DOWN * 0.18, n_.get_center() + RIGHT * 0.65 + UP * 0.22,
                               buff=0, color=C_GREEN, stroke_width=5, max_tip_length_to_length_ratio=0.45))
            else:
                L_ = 0.12 + 0.3 * out[k]
                want.add(Arrow(n_.get_center() + RIGHT * 0.65 + UP * L_, n_.get_center() + RIGHT * 0.65 + DOWN * L_,
                               buff=0, color=C_RED, stroke_width=3, max_tip_length_to_length_ratio=0.45))
        self.play_bars(FadeOut(x8), labs.animate.shift(RIGHT * 0.5), LaggedStart(*[GrowArrow(a) for a in want], lag_ratio=0.05),
                       bars=1)
        wl = VGroup(T("3：该更亮", size=24, color=C_GREEN), T("8 和其他：该更暗", size=24, color=C_RED)).arrange(DOWN, buff=0.15)
        wl.move_to([4.6, 2.2, 0])
        self.play_bars(FadeIn(wl), bars=0.5)
        # 35–36 三条路
        self.at_bar(35)
        self.tag("想让“3”更亮：三条路")
        n3 = net.cols[1][3]
        ring = Circle(radius=0.24, color=C_GREEN, stroke_width=4).move_to(n3)
        roads = VGroup(T("① 调偏置", size=28, color=C_YELLOW), T("② 调权重", size=28, color=C_YELLOW),
                       T("③ 改上一层的亮度", size=28, color=C_WHITE)).arrange(DOWN, aligned_edge=LEFT, buff=0.3)
        roads.move_to([4.6, 0.3, 0])
        self.play_bars(FadeOut(want), FadeOut(wl), Create(ring), bars=0.5)
        self.play_bars(LaggedStart(*[FadeIn(x, shift=LEFT * 0.2) for x in roads], lag_ratio=0.3), bars=1)
        # 37–38 ① 偏置
        self.at_bar(37)
        bt = ValueTracker(0.3)
        bk = Knob("b", bt, 0, 1, radius=0.3).next_to(n3, DOWN, buff=0.1).shift(RIGHT * 0.95)
        bk.scale(0.8)
        self.play_bars(roads[0].animate.set_color(C_GOLD).scale(1.1), FadeIn(bk), bars=0.5)
        self.play_bars(bt.animate.set_value(0.75), n3.animate.set_fill(C_WHITE, 0.4), bars=1)
        # 39–40 ② 权重
        self.at_bar(39)
        e3 = VGroup(*[net.edges[0][3 * 16 + i] for i in range(16)])
        self.play_bars(roads[0].animate.set_color(C_YELLOW).scale(1 / 1.1), roads[1].animate.set_color(C_GOLD).scale(1.1),
                       FadeOut(bk), net.edges[0].animate.set_stroke(opacity=0.08), bars=0.5)
        self.play_bars(*[e.animate.set_stroke(opacity=0.9, width=1 + 2.0 * min(abs(W[3, i]), 1.5)) for i, e in enumerate(e3)],
                       bars=1)
        # 41–42 亮的那几盏
        self.at_bar(41)
        bright = [i for i in range(16) if hid[i] > 0.6]
        rings = VGroup(*[Circle(radius=0.2, color=C_GOLD, stroke_width=3).move_to(net.cols[0][i]) for i in bright])
        self.play_bars(Create(rings), *[e3[i].animate.set_stroke(C_GOLD, width=6, opacity=1) for i in bright],
                       *[e3[i].animate.set_stroke(opacity=0.25) for i in range(16) if i not in bright], bars=1)
        bl_ = T("亮灯连过来的线，效果最大", size=24, color=C_GOLD).move_to([4.4, -1.6, 0])
        self.play_bars(FadeIn(bl_), bars=0.5)
        # 43–44 ③ 上一层亮度
        self.at_bar(43)
        self.play_bars(roads[1].animate.set_color(C_YELLOW).scale(1 / 1.1), roads[2].animate.set_color(C_GOLD).scale(1.1),
                       FadeOut(rings), FadeOut(bl_), bars=0.5)
        arrows = VGroup()
        for i, nd in enumerate(net.cols[0]):
            up = W[3, i] > 0
            L_ = 0.1 + 0.12 * min(abs(W[3, i]), 1.5)
            c0 = nd.get_center() + LEFT * 0.42
            arrows.add(Arrow(c0 + (DOWN if up else UP) * L_, c0 + (UP if up else DOWN) * L_, buff=0,
                             color=C_GREEN if up else C_RED, stroke_width=3, max_tip_length_to_length_ratio=0.45))
        self.play_bars(LaggedStart(*[GrowArrow(a) for a in arrows], lag_ratio=0.04), bars=1)
        # 45–46 没法直接改：上锁，再往前
        self.at_bar(45)
        lock = VGroup(RoundedRectangle(width=0.4, height=0.3, corner_radius=0.05, color=C_GREY, fill_opacity=1).shift(DOWN * 0.08),
                      Arc(radius=0.13, angle=PI, color=C_GREY, stroke_width=4).shift(UP * 0.1)).move_to([-3.3, 2.75, 0])
        lt = T("亮度不能直接改", size=22, color=C_GREY).next_to(lock, RIGHT, buff=0.15)
        further = Arrow([-3.7, -2.25, 0], [-5.3, -2.25, 0], buff=0, color=C_RED, stroke_width=5)
        fl = T("再往前追", size=22, color=C_RED).next_to(further, UP, buff=0.08)
        self.play_bars(FadeIn(lock), FadeIn(lt), bars=0.5)
        self.play_bars(GrowArrow(further), FadeIn(fl), bars=0.75)
        # 47–48 误差信号往回传
        self.at_bar(47)
        self.play_bars(FadeOut(arrows), net.edges[0].animate.set_stroke(opacity=0.3), bars=0.25)
        self.play_bars(LaggedStart(*net.back_flash(0, width=3, every=2), lag_ratio=0.005), bars=1)
        sig = T("往回传的“误差信号”", size=26, color=C_RED).move_to([4.6, -1.6, 0])
        self.play_bars(FadeIn(sig), *[n.animate.set_stroke(C_RED, width=3) for n in net.cols[0]], bars=0.5)
        # 49–50 十个输出各提要求 → Σ
        self.at_bar(49)
        j0 = 6
        tgt = net.cols[0][j0]
        reqs = VGroup()
        for k in range(10):
            col = C_GREEN if k == 3 else C_RED
            reqs.add(Line(net.cols[1][k].get_center(), tgt.get_center(), color=col, stroke_width=3))
        self.play_bars(FadeOut(roads), FadeOut(ring), net.edges[0].animate.set_stroke(opacity=0.06),
                       LaggedStart(*[Create(x) for x in reqs], lag_ratio=0.06), bars=1)
        sigma = T("Σ", size=44, color=C_GOLD, weight=BOLD).next_to(tgt, LEFT, buff=0.55)
        sl = T("10 个要求加在一起", size=24, color=C_GOLD).move_to([4.6, -2.15, 0])
        self.play_bars(FadeIn(sigma, scale=1.5), FadeIn(sl), bars=0.5)
        self.v2_rest = Group(img, dots, labs, lock, lt, further, fl, sig, reqs, sigma, sl)

    # ------------------------------------------------------------ 间奏一 51–54：完整反向传递
    def inst1(self):
        self.at_bar(51)
        self.fade_rest(0.25)
        self.tag("反向传递")
        net = LayerNet([8, 10, 10, 10], [-4.8, -1.8, 1.2, 4.2], yc=0.3, radius=0.13, seed=21)
        net.set_acts(0, np.random.default_rng(1).uniform(0, 1, 8)).set_acts(1, np.random.default_rng(2).uniform(0, 1, 10))
        net.set_acts(2, np.random.default_rng(3).uniform(0, 1, 10))
        r = np.random.default_rng(4)
        knobs = VGroup()
        for k in range(3):
            for idx in r.choice(len(net.edges[k]), 6, replace=False):
                knobs.add(mini_knob(0.12).move_to(net.edges[k][idx].point_from_proportion(0.5)))
        self.play_bars(FadeIn(net), FadeIn(knobs), bars=0.5)
        self.play_bars(*[n.animate.set_stroke(C_RED, width=4) for n in net.cols[3]], bars=0.25)
        for k in (2, 1, 0):
            ks = knobs[k * 6:(k + 1) * 6]
            self.play_bars(LaggedStart(*net.back_flash(k, width=3, every=2), lag_ratio=0.004),
                           *[Rotate(kn[1], float(r.uniform(-2, 2)), about_point=kn[0].get_center()) for kn in ks],
                           *[n.animate.set_stroke(C_RED, width=3) for n in net.cols[k]], bars=0.75)
        self.at_bar(54.5)
        self.fade_rest(0.5)

    # ------------------------------------------------------------ 主歌三 65–84：链式法则
    def verse3(self):
        self.at_bar(65)
        self.tag("链式法则")
        title = T("链式法则 = 齿轮组", size=40, color=C_WHITE, weight=BOLD).move_to([0, 2.6, 0])
        self.play_bars(Write(title), bars=1)
        # 67–68 三个齿轮
        self.at_bar(67)
        gA, gB, gC = gear(1.2, C_YELLOW), gear(0.6, C_ORANGE), gear(0.2, C_RED, teeth=7, depth=0.1)
        gA.move_to([-3.2, 0.1, 0])
        gB.move_to(gA.get_center() + RIGHT * (1.2 + 0.6 + 0.16))
        gC.move_to(gB.get_center() + RIGHT * (0.6 + 0.2 + 0.13))
        la = T("A", size=30, color=C_YELLOW).next_to(gA, DOWN, buff=0.2)
        lb = T("B", size=30, color=C_ORANGE).next_to(gB, DOWN, buff=0.45)
        lc = T("C", size=30, color=C_RED).next_to(gC, DOWN, buff=0.6)
        ta = ValueTracker(0.0)
        cA = always_redraw(lambda: T(f"A：{ta.get_value():.1f} 圈", size=26, color=C_YELLOW).move_to([3.4, 1.3, 0]))
        cB = always_redraw(lambda: T(f"B：{2 * ta.get_value():.1f} 圈", size=26, color=C_ORANGE).move_to([3.4, 0.7, 0]))
        cC = always_redraw(lambda: T(f"C：{6 * ta.get_value():.1f} 圈", size=26, color=C_RED).move_to([3.4, 0.1, 0]))
        self.play_bars(FadeIn(VGroup(gA, gB, gC, la, lb, lc)), FadeIn(cA), FadeIn(cB), FadeIn(cC), bars=0.5)

        def spin(turns_a, bars):
            self.play_bars(Rotate(gA, -TAU * turns_a, about_point=gA.get_center()),
                           Rotate(gB, 2 * TAU * turns_a, about_point=gB.get_center()),
                           Rotate(gC, -6 * TAU * turns_a, about_point=gC.get_center()),
                           ta.animate.set_value(ta.get_value() + turns_a), bars=bars, rate_func=linear)

        spin(1.0, 1.25)
        # 69–70 B 一圈 → C 三圈
        self.at_bar(69)
        bc = T("B 转 1 圈 → C 转 3 圈", size=28, color=C_WHITE).move_to([3.4, -0.9, 0])
        ab = T("A 转 1 圈 → B 转 2 圈", size=28, color=C_WHITE).move_to([3.4, -0.4, 0])
        self.play_bars(FadeIn(ab), FadeIn(bc), bars=0.5)
        qq = T("A 转 1 圈 → C 转几圈？", size=28, color=C_GOLD).move_to([3.4, -1.5, 0])
        self.play_bars(FadeIn(qq), bars=0.5)
        # 71–72 2 × 3 = 6
        self.at_bar(71)
        ta.set_value(0)
        eq = T("2 × 3 = 6", size=48, color=C_GOLD, weight=BOLD).move_to([3.4, -1.5, 0])
        self.play_bars(ReplacementTransform(qq, eq), bars=0.5)
        spin(1.0, 1.25)
        # 73–74 齿轮链 → 网络路径
        self.at_bar(73)
        self.tag("网络 = 一条条齿轮链")
        self.play_bars(FadeOut(VGroup(gA, gB, gC, la, lb, lc, ab, bc, eq, title)), FadeOut(cA), FadeOut(cB), FadeOut(cC),
                       bars=0.5)
        names = ["旋钮 w", "神经元", "神经元", "输出", "损失"]
        cols = [C_YELLOW, C_WHITE, C_WHITE, C_GOLD, C_RED]
        xs = np.linspace(-5.2, 5.2, 5)
        nodes = VGroup()
        for x, nm, col in zip(xs, names, cols):
            c = Circle(radius=0.42, stroke_color=col, stroke_width=3, fill_color=col, fill_opacity=0.12).move_to([x, 0.6, 0])
            nodes.add(VGroup(c, T(nm, size=22, color=col).next_to(c, DOWN, buff=0.18)))
        links = VGroup(*[Arrow(nodes[i][0].get_right(), nodes[i + 1][0].get_left(), buff=0.05, color=C_GREY, stroke_width=3)
                         for i in range(4)])
        ratios = ["× 0.8", "× 1.5", "× 0.6", "× 1.2"]
        rl = VGroup(*[T(rt, size=24, color=C_ORANGE).next_to(links[i], UP, buff=0.12) for i, rt in enumerate(ratios)])
        self.play_bars(LaggedStart(*[FadeIn(n) for n in nodes], lag_ratio=0.15), Create(links), bars=0.75)
        rlh = T("每一节的“传动比”：这一节变一点，下一节跟着变多少", size=22, color=C_ORANGE).move_to([0, 2.3, 0])
        self.play_bars(FadeIn(rl), FadeIn(rlh), bars=0.5)
        # 75–76 从损失往回乘
        self.at_bar(75)
        vals = [1.0]
        for rt in [1.2, 0.6, 1.5, 0.8]:
            vals.append(vals[-1] * rt)
        tags = VGroup()
        t0 = T("1", size=28, color=C_RED).move_to(nodes[4][0])
        self.play_bars(FadeIn(t0), bars=0.25)
        tags.add(t0)
        for i in range(4):
            idx = 3 - i
            v = vals[i + 1]
            t = T(f"{v:.3g}", size=21, color=C_RED).move_to(nodes[idx][0])
            pulse = Line(links[idx].get_end(), links[idx].get_start(), color=C_RED, stroke_width=6)
            self.play_bars(ShowPassingFlash(pulse, time_width=0.8), FadeIn(t), Indicate(rl[idx], color=C_RED), bars=0.375)
            tags.add(t)
        res = T("旋钮 w 的坡度 = 1.2 × 0.6 × 1.5 × 0.8 ≈ 0.86", size=26, color=C_RED).move_to([0, -1.2, 0])
        self.play_bars(FadeIn(res), bars=0.25)
        # 77–78 公式卡
        self.at_bar(77)
        self.tag("一根线的坡度")
        self.fade_rest(0.25, extra_keep=())
        card = VGroup(T("这根线（权重）的坡度", size=34, color=C_YELLOW), T("=", size=34),
                      T("输入有多亮", size=34, color=C_WHITE), T("×", size=34),
                      T("下游误差信号", size=34, color=C_RED)).arrange(RIGHT, buff=0.2).move_to([0, 1.9, 0])
        if card.width > 13:
            card.scale_to_fit_width(13)
        self.play_bars(LaggedStart(*[FadeIn(c, shift=UP * 0.2) for c in card], lag_ratio=0.15), bars=1)
        self.card = card
        # 79–80 两根线对比
        self.at_bar(79)
        a1 = Circle(radius=0.32, stroke_color=C_WHITE, stroke_width=2.5, fill_color=C_WHITE, fill_opacity=0.9).move_to([-3.5, 0.5, 0])
        a2 = Circle(radius=0.32, stroke_color=C_WHITE, stroke_width=2.5, fill_color=C_WHITE, fill_opacity=0.1).move_to([-3.5, -1.3, 0])
        o = Circle(radius=0.36, stroke_color=C_RED, stroke_width=3).move_to([0.5, -0.4, 0])
        l1 = Line(a1.get_right(), o.get_left(), color=C_GREY, stroke_width=2)
        l2 = Line(a2.get_right(), o.get_left(), color=C_GREY, stroke_width=2)
        t1 = T("0.9", size=24, color=C_WHITE).next_to(a1, LEFT, buff=0.15)
        t2 = T("0.1", size=24, color=C_WHITE).next_to(a2, LEFT, buff=0.15)
        td = T("误差信号 0.5", size=24, color=C_RED).next_to(o, RIGHT, buff=0.2)
        self.play_bars(FadeIn(VGroup(a1, a2, o, l1, l2, t1, t2, td)), bars=0.5)
        g1 = T("0.9 × 0.5 = 0.45", size=28, color=C_GOLD).move_to([4.4, 0.4, 0])
        g2 = T("0.1 × 0.5 = 0.05", size=28, color=C_GREY).move_to([4.4, -1.0, 0])
        self.play_bars(l1.animate.set_stroke(C_GOLD, width=9), l2.animate.set_stroke(C_GREY, width=1.5), FadeIn(g1), FadeIn(g2),
                       bars=1)
        # 81–82 谁亮谁背锅：整个网络
        self.at_bar(81)
        self.play_bars(*[FadeOut(m) for m in (a1, a2, o, l1, l2, t1, t2, td, g1, g2)], card.animate.scale(0.7).move_to([0, 2.7, 0]),
                       bars=0.25)
        net = LayerNet([6, 7, 7, 4], [-4.6, -1.6, 1.4, 4.4], yc=0.0, radius=0.15, seed=33, edge_opacity=0.25)
        r = np.random.default_rng(5)
        acts = [r.uniform(0, 1, len(c)) ** 1.5 for c in net.cols]
        for k in range(4):
            net.set_acts(k, acts[k])
        self.play_bars(FadeIn(net), bars=0.5)
        anims = []
        for k in range(3):
            for j in range(len(net.cols[k + 1])):
                for i in range(len(net.cols[k])):
                    e = net.edge(k, j, i)
                    anims.append(e.animate.set_stroke(C_RED, width=0.4 + 7 * acts[k][i] * 0.6, opacity=0.25 + 0.7 * acts[k][i]))
        self.play_bars(*anims, bars=1)
        # 83–84 一趟前向 + 一趟反向
        self.at_bar(83)
        sum_ = T("一趟前向 + 一趟反向 = 全部 13,002 个坡度", size=30, color=C_WHITE, weight=BOLD).move_to([0, -2.2, 0])
        cost = T("（反向的计算量约为前向的 2 倍：不是免费，但和前向同一量级）", size=20, color=C_GREY).next_to(sum_, DOWN, buff=0.1)
        self.play_bars(FadeIn(sum_, shift=UP * 0.2), Indicate(self.counter, color=C_YELLOW), bars=0.75)
        self.play_bars(FadeIn(cost), bars=0.5)
        self.at_bar(84.5)
        self.fade_rest(0.5)

    # ------------------------------------------------------------ 桥段 85–92
    def bridge(self):
        self.at_bar(85)
        self.tag("错误从后往前流")
        net = LayerNet([8, 10, 10, 10, 6], [-5.4, -2.7, 0, 2.7, 5.4], yc=0.3, radius=0.13, seed=41, edge_opacity=0.22)
        self.play_bars(FadeIn(net), bars=0.5)
        self.play_bars(*[n.animate.set_stroke(C_RED, width=4) for n in net.cols[4]], bars=0.25)
        for k in (3, 2, 1, 0):
            self.play_bars(LaggedStart(*net.back_flash(k, width=3, every=2), lag_ratio=0.003),
                           *[n.animate.set_stroke(C_RED, width=3) for n in net.cols[k]], bars=0.75)
        # 89–92 每个旋钮分到一份
        self.at_bar(89)
        r = np.random.default_rng(9)
        knobs = VGroup()
        for k in range(4):
            for idx in r.choice(len(net.edges[k]), 7, replace=False):
                knobs.add(mini_knob(0.12).move_to(net.edges[k][idx].point_from_proportion(0.5)))
        self.play_bars(LaggedStart(*[FadeIn(kn, scale=0.5) for kn in knobs], lag_ratio=0.03), bars=1)
        order = list(range(len(knobs)))[::-1]
        self.play_bars(LaggedStart(*[Rotate(knobs[i][1], float(r.uniform(-2.4, 2.4)), about_point=knobs[i][0].get_center())
                                     for i in order], lag_ratio=0.05), bars=2.5)
        self.fade_rest(0.5)

    # ------------------------------------------------------------ 主歌四 93–108
    def verse4(self):
        self.at_bar(93)
        self.tag("分工")

        def box(t1, t2, col):
            a = T(t1, size=32, color=col, weight=BOLD)
            b = T(t2, size=28, color=C_WHITE)
            g = VGroup(a, b).arrange(DOWN, buff=0.25)
            return VGroup(RoundedRectangle(width=4.6, height=1.8, corner_radius=0.15, color=col).move_to(g), g)

        b1 = box("反向传播", "只负责：算出梯度", C_RED).move_to([-3.2, 0.5, 0])
        b2 = box("梯度下降", "负责：拧旋钮", C_GREEN).move_to([3.2, 0.5, 0])
        ar = Arrow(b1.get_right(), b2.get_left(), buff=0.15, color=C_GREY)
        self.play_bars(FadeIn(b1), bars=0.5)
        self.play_bars(GrowArrow(ar), FadeIn(b2), bars=0.75)
        self.at_bar(94.75)
        self.fade_rest(0.25)
        # 95–98 训练循环
        self.at_bar(95)
        self.tag("训练循环")
        cen = np.array([-2.6, 0.2, 0])
        R = 1.7
        steps = [("① 前向：猜", C_BLUE), ("② 损失：对答案", C_RED), ("③ 反向：分责任", C_RED), ("④ 更新：拧旋钮", C_GREEN)]
        ring_nodes = VGroup()
        for i, (s_, col) in enumerate(steps):
            a = PI / 2 - i * PI / 2
            t = T(s_, size=24, color=col)
            bg = SurroundingRectangle(t, color=col, buff=0.14, corner_radius=0.1, fill_color=BG, fill_opacity=1, stroke_width=2.5)
            ring_nodes.add(VGroup(bg, t).move_to(cen + np.array([1.55 * R * np.cos(a), R * np.sin(a), 0])))
        circ = Circle(radius=1.0, color=C_GREY, stroke_width=2).stretch(1.55 * R, 0).stretch(R, 1).move_to(cen)
        circ.set_z_index(-1)
        nb = T("下一批数据", size=22, color=C_GREY).move_to(cen)
        self.play_bars(Create(circ), FadeIn(ring_nodes[0], scale=0.8), FadeIn(nb), bars=0.75)
        self.play_bars(Indicate(ring_nodes[0], color=C_BLUE), bars=0.75)
        self.at_bar(97)
        for i in (1, 2, 3):
            self.play_bars(FadeIn(ring_nodes[i], scale=0.8), bars=0.5)
        # 99–100 转几圈；准确率上升；认错的数字变对
        self.at_bar(99)
        dot = Dot(color=C_GOLD, radius=0.1)
        dot.move_to(circ.point_from_proportion(0))
        acc_ax = Axes(x_range=[0, 10], y_range=[0, 1], x_length=3.0, y_length=1.5, tips=False,
                      axis_config=dict(color=C_GREY, stroke_width=1.5)).move_to([4.2, 1.6, 0])
        acc_l = T("准确率", size=20, color=C_GREEN).next_to(acc_ax, UP, buff=0.08).align_to(acc_ax, LEFT)
        acc = acc_ax.plot(lambda x: 0.96 - 0.86 * np.exp(-x / 2.0), x_range=[0, 10], color=C_GREEN, stroke_width=3)
        imgs = Group()
        marks = VGroup()
        for k, d in enumerate([3, 8, 5, 1, 9]):
            im = pix_image(digits.digit(d, seed=200 + k), 0.75).move_to([2.9 + 0.8 * k, -0.6, 0])
            imgs.add(im)
            marks.add(T("✗", size=24, color=C_RED).next_to(im, DOWN, buff=0.08))
        self.play_bars(FadeIn(dot), FadeIn(acc_ax), FadeIn(acc_l), FadeIn(imgs), FadeIn(marks), bars=0.25)
        oks = VGroup(*[T("✓", size=24, color=C_GREEN).move_to(m) for m in marks])
        self.play_bars(MoveAlongPath(dot, circ), Create(acc), *[Transform(m, o) for m, o in zip(marks, oks)],
                       bars=1.5, rate_func=linear)
        self.at_bar(100.75)
        self.fade_rest(0.25)
        # 101–104 时间轴
        self.at_bar(101)
        self.tag("历史")
        line = Line([-6, 0.2, 0], [6, 0.2, 0], color=C_GREY, stroke_width=3)
        evs = [(1970, "Linnainmaa", "反向模式\n自动微分", C_WHITE), (1974, "Werbos", "用来训练\n神经网络的设想", C_WHITE),
               (1986, "Rumelhart、Hinton、Williams", "《自然》论文，让它流行开来", C_GOLD)]
        marks = VGroup()
        for yr, who, what, col in evs:
            x = -6 + 12 * (yr - 1965) / 26
            tick = Line([x, 0.05, 0], [x, 0.35, 0], color=col, stroke_width=4)
            y_ = T(str(yr), size=28, color=col, weight=BOLD).next_to(tick, UP, buff=0.12)
            w_ = T(who, size=22, color=col).next_to(tick, DOWN, buff=0.2)
            d_ = T(what, size=20, color=C_GREY, line_spacing=0.85).next_to(w_, DOWN, buff=0.1)
            marks.add(VGroup(tick, y_, w_, d_))
        self.play_bars(Create(line), FadeIn(marks[0]), bars=0.75)
        self.play_bars(FadeIn(marks[1]), bars=0.75)
        self.at_bar(103)
        self.play_bars(FadeIn(marks[2], scale=1.1), bars=0.75)
        hl = SurroundingRectangle(marks[2], color=C_GOLD, buff=0.15, corner_radius=0.1)
        self.play_bars(Create(hl), bars=0.5)
        self.at_bar(104.75)
        self.fade_rest(0.25)
        # 105–106 自动求导
        self.at_bar(105)
        self.tag("自动求导")
        code = VGroup(Text("loss = model(images, labels)", font_size=28, color=C_WHITE, font="DejaVu Sans Mono"),
                      Text("loss.backward()", font_size=28, color=C_RED, font="DejaVu Sans Mono"),
                      Text("optimizer.step()", font_size=28, color=C_GREEN, font="DejaVu Sans Mono")).arrange(DOWN, aligned_edge=LEFT, buff=0.25)
        bg = SurroundingRectangle(code, color=C_GREY, buff=0.35, corner_radius=0.12, fill_color="#121621", fill_opacity=1)
        cg = VGroup(bg, code).move_to([-1.4, 0.4, 0])
        n1 = T("← 反向传播：框架自动算出所有梯度", size=22, color=C_RED).next_to(code[1], RIGHT, buff=0.9)
        n2 = T("← 梯度下降：拧旋钮", size=22, color=C_GREEN).next_to(code[2], RIGHT, buff=0.9)
        note = T("（示意代码，写法与 PyTorch 一类框架相似）", size=20, color=C_GREY).next_to(cg, DOWN, buff=0.3)
        self.play_bars(FadeIn(cg), FadeIn(note), bars=0.5)
        self.play_bars(FadeIn(n1, shift=LEFT * 0.2), bars=0.5)
        self.play_bars(FadeIn(n2, shift=LEFT * 0.2), bars=0.5)
        self.at_bar(106.75)
        self.fade_rest(0.25)
        # 107–108 大脑？
        self.at_bar(107)
        self.tag("大脑也这么学吗？")
        brain = VGroup(Ellipse(width=3.2, height=2.3, color=C_ORANGE, stroke_width=3))
        for k in range(5):
            brain.add(Arc(radius=0.5, start_angle=PI * (0.2 + 0.15 * k), angle=PI * 0.6, color=C_ORANGE, stroke_width=2)
                      .move_to([-0.9 + 0.45 * k, 0.15 * ((-1) ** k), 0]))
        brain.add(Line([0, 1.1, 0], [0, -1.1, 0], color=C_ORANGE, stroke_width=2))
        brain.move_to([-2.0, 0.4, 0])
        q = T("?", size=96, color=C_WHITE, weight=BOLD).next_to(brain, RIGHT, buff=0.6)
        nt = T("大脑是否也用反向传播学习：尚无定论", size=28, color=C_GREY).move_to([0, -1.8, 0])
        self.play_bars(Create(brain), bars=0.5)
        self.play_bars(FadeIn(q, scale=1.4), FadeIn(nt), bars=0.75)
        self.at_bar(108.5)
        self.fade_rest(0.5)

    # ------------------------------------------------------------ 间奏二 109–112：要点
    def inst2(self):
        self.at_bar(109)
        self.tag("本集要点")
        head = T("本集要点", size=46, color=C_YELLOW, weight=BOLD)
        pts = [
            "1. 笨办法：每个旋钮各算一遍，13,002 个旋钮就要 13,002 遍",
            "2. 链式法则：影响沿链条相乘；反向传播从损失出发往回乘",
            "3. 一根线的坡度 = 输入有多亮 × 下游误差信号",
            "4. 反向传播只算梯度，拧旋钮靠梯度下降；反向 ≈ 2 倍前向的计算量",
        ]
        items = VGroup(*[T(p, size=29) for p in pts]).arrange(DOWN, aligned_edge=LEFT, buff=0.32)
        g = VGroup(head, items).arrange(DOWN, buff=0.5).move_to([0, 0.35, 0])
        if g.width > 13.2:
            g.scale_to_fit_width(13.2)
        self.play_bars(FadeIn(head, shift=DOWN * 0.2), bars=0.25)
        for it in items:
            self.play_bars(FadeIn(it, shift=RIGHT * 0.3), bars=0.5)
        self.at_bar(112.5)
        self.play_bars(FadeOut(g), bars=0.5)

    # ------------------------------------------------------------ 尾声 123–130
    def outro(self):
        self.at_bar(123)
        self.tag("第一部分收尾")
        parts = [("神经网络（函数）", C_WHITE), ("损失", C_RED), ("梯度下降", C_GREEN), ("反向传播", C_RED)]
        chips = VGroup()
        for s_, col in parts:
            t = T(s_, size=30, color=col)
            chips.add(VGroup(SurroundingRectangle(t, color=col, buff=0.2, corner_radius=0.12, stroke_width=2.5), t))
        chips.arrange(RIGHT, buff=0.45).move_to([0, 1.2, 0])
        plus = VGroup(*[T("+", size=32, color=C_GREY).move_to((chips[i].get_right() + chips[i + 1].get_left()) / 2) for i in range(3)])
        self.play_bars(LaggedStart(*[FadeIn(c, shift=UP * 0.2) for c in chips[:3]], lag_ratio=0.3), FadeIn(plus[:2]), bars=1.25)
        # 125–126
        self.at_bar(125)
        self.play_bars(FadeIn(chips[3], shift=UP * 0.2), FadeIn(plus[2]), bars=0.5)
        frame = SurroundingRectangle(VGroup(chips, plus), color=C_GOLD, buff=0.3, corner_radius=0.15)
        fl = T("= 学习的全部机关", size=36, color=C_GOLD, weight=BOLD).next_to(frame, DOWN, buff=0.35)
        self.play_bars(Create(frame), FadeIn(fl), bars=0.75)
        # 127–128 文字怎么切
        self.at_bar(127)
        self.play_bars(FadeOut(VGroup(chips, plus, frame, fl)), bars=0.25)
        chars = VGroup(*[T(c, size=72, color=C_BLUE) for c in "床前明月光"]).arrange(RIGHT, buff=0.15).move_to([0, 0.6, 0])
        self.play_bars(FadeIn(chars), bars=0.5)
        cuts = VGroup(*[Line(UP * 0.7 + RIGHT * 0.15, DOWN * 0.7 + LEFT * 0.15, color=C_WHITE, stroke_width=4)
                        .move_to((chars[i].get_right() + chars[i + 1].get_left()) / 2) for i in range(4)])
        self.play_bars(LaggedStart(*[Create(c) for c in cuts], lag_ratio=0.2),
                       *[ch.animate.shift(RIGHT * 0.25 * (i - 2)) for i, ch in enumerate(chars)], bars=0.75)
        # 129–130 下集
        self.at_bar(129)
        nxt = VGroup(T("下集（正片）", size=28, color=C_GREY), T("词向量", size=48, color=C_BLUE, weight=BOLD),
                     T("把文字变成一串数字", size=30, color=C_BLUE)).arrange(DOWN, buff=0.22).move_to([0, -1.0, 0])
        side = T("岔路 · 番外一：卷积网络——AI 怎么看图", size=22, color=C_GREY).next_to(nxt, DOWN, buff=0.25)
        self.play_bars(VGroup(chars, cuts).animate.shift(UP * 1.2), FadeIn(nxt, shift=UP * 0.2), FadeIn(side), bars=0.75)
        self.at_bar(130.25)
        self.play_bars(*[FadeOut(m) for m in self.visible()], bars=0.75)
