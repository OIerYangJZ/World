# -*- coding: utf-8 -*-
"""
第 01 集《机器怎么“学”：一台会自己拧旋钮的函数》

时间全部对齐 bars.py 的 BPM 小节网格（88 BPM，122 小节）。字幕由 build.py 烧录。
    ~/.venvs/manim/bin/python ../common/build.py 01_机器怎么学 [--preview]
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "common"))
from style import *  # noqa: E402,F401

# ---------------------------------------------------------------- 数据（固定随机种子，可复现）
rng = np.random.default_rng(7)
TEMPS = np.sort(rng.uniform(12, 34, 20))
SALES = np.clip(8.0 * TEMPS - 60 + rng.normal(0, 14, 20), 5, 250)
W_FIT, B_FIT = np.polyfit(TEMPS, SALES, 1)          # 最小二乘最佳直线

# 过拟合演示：8 个训练点 + 5 个新数据点（来自同一条“真实规律” + 噪声）
rng2 = np.random.default_rng(11)
TR_X = np.array([13.0, 16.0, 19.0, 21.5, 24.0, 27.0, 30.0, 33.0])
TR_Y = 8.0 * TR_X - 60 + rng2.normal(0, 16, TR_X.size)
TE_X = np.array([14.5, 17.5, 25.5, 28.5, 31.5])
TE_Y = 8.0 * TE_X - 60 + rng2.normal(0, 16, TE_X.size)
_xs = (TR_X - 23) / 10                               # 标准化后再插值，数值稳定
POLY = np.polyfit(_xs, TR_Y, TR_X.size - 1)          # 7 次多项式：8 个系数 = 8 个旋钮
W_TR, B_TR = np.polyfit(TR_X, TR_Y, 1)


def poly_f(x):
    return np.polyval(POLY, (x - 23) / 10)


X0, X1, Y0, Y1 = 10, 36, 0, 260


def make_axes():
    ax = Axes(x_range=[X0, X1, 5], y_range=[Y0, Y1, 50], x_length=7.0, y_length=4.6,
              axis_config=dict(color=C_GREY, stroke_width=2, include_tip=False))
    nums = VGroup(*[T(str(v), size=20, color=C_GREY).next_to(ax.c2p(v, Y0), DOWN, buff=0.15)
                    for v in (15, 20, 25, 30, 35)],
                  *[T(str(v), size=20, color=C_GREY).next_to(ax.c2p(X0, v), LEFT, buff=0.15)
                    for v in (50, 100, 150, 200, 250)])
    ax.add(nums)
    xl = T("气温 (°C)", size=24, color=C_GREY).next_to(ax.x_axis, DOWN, buff=0.45).align_to(ax.x_axis, RIGHT)
    yl = T("冷饮 (杯)", size=24, color=C_GREY).next_to(ax.y_axis, UP, buff=0.15).align_to(ax.y_axis, LEFT)
    return ax, VGroup(xl, yl)


def clip_line(w, b):
    """y = w x + b 在坐标框 [X0,X1]×[Y0,Y1] 内的线段端点（数据坐标）"""
    pts = []
    for x in (X0, X1):
        y = w * x + b
        if Y0 <= y <= Y1:
            pts.append((x, y))
    if abs(w) > 1e-9:
        for y in (Y0, Y1):
            x = (y - b) / w
            if X0 < x < X1:
                pts.append((x, y))
    pts = sorted(set(pts))
    if len(pts) < 2:
        return None
    return pts[0], pts[-1]


def clipped_curve(ax, f, color, width=5, n=600):
    """只画出 f 落在坐标框内的部分（分段子路径）"""
    xs = np.linspace(X0 + 0.5, X1 - 0.5, n)
    m = VMobject(stroke_color=color, stroke_width=width)
    run = []
    for x in xs:
        y = f(x)
        if Y0 <= y <= Y1:
            run.append(ax.c2p(x, y))
        else:
            if len(run) > 1:
                m.append_vectorized_mobject(VMobject().set_points_as_corners(run))
            run = []
    if len(run) > 1:
        m.append_vectorized_mobject(VMobject().set_points_as_corners(run))
    m.set_stroke(color=color, width=width)
    return m


def make_cat(color=C_GOLD, scale=1.0):
    head = Circle(radius=0.9, stroke_color=color, stroke_width=5, fill_color=color, fill_opacity=0.12)
    ear_l = Polygon([-0.85, 0.35, 0], [-0.6, 1.25, 0], [-0.15, 0.82, 0],
                    stroke_color=color, stroke_width=5, fill_color=color, fill_opacity=0.12)
    ear_r = ear_l.copy().flip(UP, about_point=ORIGIN)
    eye_l = Ellipse(width=0.18, height=0.3, color=color, fill_opacity=1).move_to([-0.33, 0.15, 0])
    eye_r = eye_l.copy().move_to([0.33, 0.15, 0])
    nose = Triangle(color=color, fill_opacity=1).scale(0.08).rotate(PI).move_to([0, -0.15, 0])
    wh = VGroup()
    for s in (-1, 1):
        for k, dy in enumerate((0.05, -0.12, -0.29)):
            wh.add(Line([s * 0.25, -0.2, 0], [s * 1.25, -0.2 + dy + 0.12 * (1 - k), 0],
                        stroke_width=2.5, color=color))
    cat = VGroup(head, ear_l, ear_r, eye_l, eye_r, nose, wh)
    return cat.scale(scale)


def pixel_seven(n=28, size=0.12):
    """28×28 灰度网格，画一个手写风格的“7”"""
    segs = [((7, 6), (21, 6.5)), ((21, 6.5), (13, 23))]

    def dist(p, a, b):
        p, a, b = map(np.array, (p, a, b))
        t = np.clip(np.dot(p - a, b - a) / np.dot(b - a, b - a), 0, 1)
        return np.linalg.norm(p - (a + t * (b - a)))

    g = VGroup()
    for r in range(n):
        for c in range(n):
            d = min(dist((c + 0.5, r + 0.5), *s) for s in segs)
            v = float(np.clip(1.6 - d / 1.1, 0, 1))
            sq = Square(side_length=size, stroke_width=0.6, stroke_color="#1d2230",
                        fill_color=interpolate_color(ManimColor("#0f121a"), ManimColor(C_WHITE), v),
                        fill_opacity=1)
            sq.move_to([(c - n / 2 + 0.5) * size, -(r - n / 2 + 0.5) * size, 0])
            g.add(sq)
    return g


class Video(BeatScene):
    EP_DIR = os.path.dirname(os.path.abspath(__file__))

    # ============================================================ 主流程
    def construct(self):
        self.counter = None
        self.intro()          # 1–4
        self.verse1()         # 5–20
        self.hook(21, 1)      # 21–30
        self.verse2()         # 31–46
        self.inst1()          # 47–50
        self.hook(51, 2)      # 51–60
        self.verse3()         # 61–76
        self.bridge()         # 77–84
        self.verse4()         # 85–100
        self.inst2()          # 101–104
        self.hook(105, 3)     # 105–114
        self.outro()          # 115–122
        self.finish()

    # ------------------------------------------------------------ 计数器
    def set_counter(self, text, bars=0.5):
        new = knob_counter(text)
        if self.counter is None:
            self.counter = new
            self.play_bars(FadeIn(new, shift=LEFT * 0.2), bars=bars)
        else:
            self.play_bars(Transform(self.counter, new), bars=bars)

    def tag(self, text, bars=0.25):
        t = section_tag(text)
        old = getattr(self, "_tag", None)
        anims = [FadeIn(t, shift=RIGHT * 0.2)]
        if old is not None and old in self.mobjects:
            anims.append(FadeOut(old))
        self._tag = t
        self.play_bars(*anims, bars=bars)

    def visible(self):
        return [m for m in self.mobjects if not isinstance(m, ValueTracker)]

    def fade_rest(self, bars=0.5):
        keep = self.keep()
        self.play_bars(*[FadeOut(m) for m in self.visible() if m not in keep], bars=bars)

    def keep(self):
        """清场时保留的常驻元素"""
        k = [m for m in (self.counter, getattr(self, "_tag", None)) if m is not None]
        return k

    # ------------------------------------------------------------ 前奏 1–4
    def intro(self):
        card = title_card("第 01 集", "机器怎么“学”", "一台会自己拧旋钮的函数")
        s, e, t, line, st = card
        self.play_bars(FadeIn(s, shift=DOWN * 0.2), FadeIn(e, shift=DOWN * 0.2), bars=0.75)
        self.play_bars(Write(t), bars=1)
        self.play_bars(GrowFromCenter(line), FadeIn(st, shift=UP * 0.2), bars=0.75)
        self.at_bar(4.5)
        self.play_bars(FadeOut(card), bars=0.5)

    # ------------------------------------------------------------ 主歌一 5–20
    def verse1(self):
        self.at_bar(5)
        box = black_box().move_to([0, 0.4, 0])
        self.box = box
        q = T("床前明月光，疑是地上__", size=34, color=C_BLUE).move_to([-4.3, 2.6, 0])
        self.tag("黑箱", bars=0.25)
        self.play_bars(FadeIn(box, scale=0.9), bars=0.5)
        self.set_counter("?", bars=0.25)
        self.play_bars(FadeIn(q, shift=RIGHT * 0.3), bars=0.5)
        self.play_bars(q.animate.scale(0.4).move_to(box.front.get_left() + RIGHT * 0.3).set_opacity(0),
                       bars=0.5, rate_func=smooth)
        # 7–8 吐出“霜”
        self.at_bar(7)
        ans = T("霜", size=110, color=C_GOLD, weight=BOLD).move_to(box.front.get_right() + LEFT * 0.4)
        ans.set_opacity(0)
        self.play_bars(Wiggle(box.q, scale_value=1.3), box.front.animate.set_stroke(C_GOLD), bars=0.75)
        self.play_bars(ans.animate.set_opacity(1).move_to([4.4, 0.4, 0]),
                       box.front.animate.set_stroke(C_GREY), bars=0.75)
        how = T("它凭什么？", size=36, color=C_GREY).next_to(box, DOWN, buff=0.5)
        self.play_bars(FadeIn(how, shift=UP * 0.2), bars=0.5)
        # 9–10 倒带
        self.at_bar(9)
        rw = T("◀◀ 倒带", size=30, color=C_GREY).to_edge(DOWN, buff=1.6).shift(RIGHT * 4.5)
        q2 = T("床前明月光，疑是地上__", size=34, color=C_BLUE).move_to([-4.3, 2.6, 0])
        self.play_bars(FadeIn(rw), ans.animate.move_to(box.front.get_right()).set_opacity(0),
                       FadeOut(how), bars=0.75)
        self.play_bars(FadeIn(q2, shift=LEFT * 0.5), bars=0.5)
        self.play_bars(FadeOut(q2), FadeOut(box), FadeOut(rw), FadeOut(ans), bars=0.75)
        # 11–14 传统编程
        self.at_bar(11)
        self.tag("传统编程")

        def node(txt, col):
            r = RoundedRectangle(width=2.6, height=1.1, corner_radius=0.15, stroke_color=col,
                                 fill_color=col, fill_opacity=0.12)
            return VGroup(r, T(txt, size=32, color=col))

        n_in = node("输入", C_BLUE).move_to([-4.6, 1.2, 0])
        n_rule = node("规则（人写）", C_YELLOW).move_to([0, 1.2, 0])
        n_rule[0].stretch_to_fit_width(3.4)
        n_out = node("输出", C_GOLD).move_to([4.6, 1.2, 0])
        a1 = Arrow(n_in.get_right(), n_rule.get_left(), color=C_GREY, buff=0.1)
        a2 = Arrow(n_rule.get_right(), n_out.get_left(), color=C_GREY, buff=0.1)
        self.play_bars(LaggedStart(FadeIn(n_in), GrowArrow(a1), FadeIn(n_rule), GrowArrow(a2), FadeIn(n_out),
                                   lag_ratio=0.3), bars=1.25)
        person = VGroup(Circle(radius=0.22, color=C_YELLOW), Line(DOWN * 0.22, DOWN * 0.75, color=C_YELLOW),
                        Line(DOWN * 0.4 + LEFT * 0.3, DOWN * 0.4 + RIGHT * 0.3, color=C_YELLOW)
                        ).next_to(n_rule, UP, buff=0.3)
        self.play_bars(FadeIn(person, shift=DOWN * 0.2), bars=0.5)
        self.at_bar(13)
        code = VGroup(
            T("如果 ……", size=28, color=C_YELLOW),
            T("    那么 ……", size=28, color=C_WHITE),
            T("否则如果 ……", size=28, color=C_YELLOW),
            T("    那么 ……", size=28, color=C_WHITE),
            T("否则 ……", size=28, color=C_YELLOW),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.16).next_to(n_rule, DOWN, buff=0.45)
        frame = SurroundingRectangle(code, color=C_YELLOW, buff=0.25, corner_radius=0.1, stroke_width=2)
        self.play_bars(Create(frame), LaggedStart(*[FadeIn(c, shift=DOWN * 0.15) for c in code], lag_ratio=0.3),
                       bars=1.5)
        self.at_bar(14.75)
        self.play_bars(*[FadeOut(m) for m in (n_in, n_rule, n_out, a1, a2, person, code, frame)], bars=0.25)
        # 15–16 猫
        self.at_bar(15)
        self.tag("规则写得出来吗？")
        cat = make_cat().move_to([0, 0.5, 0])
        qq = T("这是猫吗？", size=40, color=C_WHITE).next_to(cat, RIGHT, buff=1.0)
        self.play_bars(DrawBorderThenFill(cat), bars=1)
        self.play_bars(FadeIn(qq, shift=LEFT * 0.2), bars=0.5)
        # 17–18 千变万化
        self.at_bar(17)
        v1 = make_cat(C_GOLD, 0.55).rotate(25 * DEGREES)
        v2 = make_cat(C_GREY, 0.35)
        v3 = make_cat(C_ORANGE, 0.55)
        v4 = make_cat(C_GOLD, 0.55)
        cover = Rectangle(width=0.75, height=1.6, fill_color=BG, fill_opacity=1, stroke_width=0).move_to(v4.get_right() + LEFT * 0.3)
        v4 = VGroup(v4, cover)
        v5 = make_cat(C_GOLD, 0.55).set_opacity(0.25)
        row = VGroup(v1, v2, v3, v4, v5).arrange(RIGHT, buff=0.75).move_to([0, 0.6, 0])
        labels = VGroup(*[T(s, size=24, color=C_GREY).next_to(v, DOWN, buff=0.35)
                          for s, v in zip(["转了头", "离得远", "换了毛色", "被挡住", "光线暗"], row)])
        self.play_bars(FadeOut(qq), ReplacementTransform(cat, v1), *[FadeIn(v, scale=0.7) for v in row[1:]],
                       bars=1)
        self.play_bars(LaggedStart(*[FadeIn(l) for l in labels], lag_ratio=0.2), bars=0.75)
        # 19–20 规则爆炸
        self.at_bar(19)
        rules = ["如果耳朵是尖的……", "如果有胡须……", "如果侧着脸……", "如果只露半张脸……",
                 "如果光线很暗……", "如果是黑猫……", "如果在睡觉……", "如果是卡通猫……",
                 "如果毛很长……", "如果是背影……", "如果被帽子挡住……", "如果……"]
        cards = VGroup()
        r2 = np.random.default_rng(3)
        for i, s in enumerate(rules):
            c = T(s, size=26, color=C_YELLOW)
            bg = SurroundingRectangle(c, color=C_YELLOW, buff=0.12, fill_color=BG, fill_opacity=0.9,
                                      stroke_width=1.5, corner_radius=0.06)
            card = VGroup(bg, c).move_to([r2.uniform(-5, 5), r2.uniform(-2.0, 2.6), 0])
            card.rotate(r2.uniform(-0.12, 0.12))
            cards.add(card)
        self.play_bars(VGroup(row, labels).animate.set_opacity(0.2),
                       LaggedStart(*[FadeIn(c, scale=0.6) for c in cards], lag_ratio=0.15), bars=1.25)
        cross = VGroup(Line([-3, -2, 0], [3, 2.6, 0]), Line([-3, 2.6, 0], [3, -2, 0])).set_stroke(C_RED, 14)
        self.play_bars(Create(cross), bars=0.25)
        self.at_bar(20.5)
        self.play_bars(*[FadeOut(m) for m in (row, labels, cards, cross)], bars=0.5)

    # ------------------------------------------------------------ 副歌（三次，内容略有变化）
    def hook(self, start, k):
        self.at_bar(start)
        self.tag("学习的循环")
        center = np.array([0, 0.2, 0])
        RX, RY = 3.9, 1.75
        box = black_box(w=2.4, h=1.7, depth=0.35).move_to(center)
        names = [("① 例子", C_BLUE), ("② 猜", C_GOLD), ("③ 量误差", C_RED), ("④ 拧旋钮", C_YELLOW)]
        angs = [180, 90, 0, -90]
        nodes = VGroup()
        for (s, col), a in zip(names, angs):
            p = center + np.array([RX * np.cos(a * DEGREES), RY * np.sin(a * DEGREES), 0])
            t = T(s, size=32, color=col)
            bg = SurroundingRectangle(t, color=col, buff=0.18, corner_radius=0.12, fill_color=BG,
                                      fill_opacity=1, stroke_width=2.5)
            nodes.add(VGroup(bg, t).move_to(p))
        arcs = VGroup(*[
            CurvedArrow(nodes[i].get_center() + 0.0 * UP, nodes[(i + 1) % 4].get_center(), angle=-PI / 3,
                        color=C_GREY, stroke_width=3, tip_length=0.2)
            for i in range(4)
        ])
        for a in arcs:
            a.set_z_index(-1)
        # 箱子内部（k=2,3 时箱里是一条拟合直线，暗示“学会了”）
        inner = VGroup()
        if k >= 2:
            ax = Axes(x_range=[0, 1], y_range=[0, 1], x_length=1.5, y_length=1.0, tips=False,
                      axis_config=dict(stroke_width=1.5, color=C_GREY)).move_to(box.front)
            dots = VGroup(*[Dot(ax.c2p(x, 0.15 + 0.7 * x + 0.08 * np.sin(9 * x)), radius=0.035, color=C_BLUE)
                            for x in np.linspace(0.05, 0.95, 9)])
            ln = Line(ax.c2p(0, 0.15), ax.c2p(1, 0.85), color=C_YELLOW, stroke_width=3)
            inner = VGroup(ax, dots, ln)
        self.play_bars(FadeIn(box), FadeIn(nodes[0], scale=0.8), bars=0.5)
        # ① 例子：数据点飞进黑箱
        pts = VGroup(*[Dot(nodes[0].get_center() + np.array([0.0, 0.0, 0]), radius=0.07, color=C_BLUE)
                       for _ in range(8)])
        self.add(pts)
        self.play_bars(LaggedStart(*[p.animate.move_to(box.front.get_center()).set_opacity(0) for p in pts],
                                   lag_ratio=0.15), Create(arcs[0]), bars=1.25)
        self.remove(pts)
        # ② 猜
        self.at_bar(start + 2)
        guess = T("猜：120 杯？" if k != 1 else "猜一个答案", size=26, color=C_GOLD).next_to(nodes[1], RIGHT, buff=0.3)
        self.play_bars(FadeIn(nodes[1], scale=0.8), Create(arcs[1]), bars=0.75)
        self.play_bars(FadeIn(guess, shift=DOWN * 0.15), Indicate(box.front, color=C_GOLD), bars=0.75)
        # ③ 量误差
        self.at_bar(start + 4)
        bar_bg = Rectangle(width=1.6, height=0.22, stroke_color=C_RED, stroke_width=1.5).next_to(nodes[2], DOWN, buff=0.25)
        err = Rectangle(width=1.5, height=0.16, stroke_width=0, fill_color=C_RED, fill_opacity=0.9)
        err.move_to(bar_bg).align_to(bar_bg, LEFT).shift(RIGHT * 0.05)
        self.play_bars(FadeIn(nodes[2], scale=0.8), Create(arcs[2]), bars=0.75)
        self.play_bars(FadeIn(bar_bg), GrowFromEdge(err, LEFT), bars=0.75)
        # ④ 拧旋钮
        self.at_bar(start + 6)
        tr = ValueTracker(0.2)
        kn = Knob("·", tr, 0, 1, radius=0.38).next_to(nodes[3], RIGHT, buff=0.4)
        kn[-1].set_opacity(0)
        self.play_bars(FadeIn(nodes[3], scale=0.8), Create(arcs[3]), FadeIn(kn), bars=0.75)
        err2 = err.copy().stretch_to_fit_width(0.35).align_to(err, LEFT)
        self.play_bars(tr.animate.set_value(0.8), Transform(err, err2),
                       LaggedStart(*[ShowPassingFlash(a.copy().set_stroke(C_YELLOW, width=7), time_width=0.6)
                                     for a in arcs], lag_ratio=0.25), bars=1.25)
        # ⑤ 一层一层，把黑箱打开
        self.at_bar(start + 8)
        front = box.front
        lid = VGroup(front, box.q)
        if len(inner):
            inner.set_z_index(5)
        self.play_bars(lid.animate.shift(UP * 0.25).set_opacity(0.15),
                       FadeIn(inner) if len(inner) else Indicate(box.q, color=C_YELLOW, scale_factor=1.5),
                       bars=1)
        slogan = T("一层一层，把黑箱打开", size=40, color=C_YELLOW, weight=BOLD).to_edge(UP, buff=0.3)
        self.play_bars(Write(slogan), bars=0.5)
        self.at_bar(start + 9.5)
        self.fade_rest(0.5)

    # ------------------------------------------------------------ 主歌二 31–46
    def verse2(self):
        self.at_bar(31)
        self.tag("从例子里学")
        show = [3, 7, 11, 15, 18]
        head = VGroup(T("气温 (°C)", size=28, color=C_BLUE), T("冷饮 (杯)", size=28, color=C_GOLD)).arrange(RIGHT, buff=0.8)
        rows = VGroup()
        for i in show:
            r = VGroup(T(f"{TEMPS[i]:.0f}", size=30, color=C_BLUE), T(f"{SALES[i]:.0f}", size=30, color=C_GOLD))
            r[0].move_to(head[0], coor_mask=[1, 0, 0])
            r[1].move_to(head[1], coor_mask=[1, 0, 0])
            rows.add(r)
        rows.arrange(DOWN, buff=0.28)
        for r in rows:
            r[0].set_x(head[0].get_x())
            r[1].set_x(head[1].get_x())
        table = VGroup(head, rows).arrange(DOWN, buff=0.35).move_to([-3.3, 0.35, 0])
        hl = Line(head.get_corner(DL) + DOWN * 0.15 + LEFT * 0.2, head.get_corner(DR) + DOWN * 0.15 + RIGHT * 0.2,
                  color=C_GREY, stroke_width=2)
        q_lab = T("题目", size=26, color=C_BLUE).next_to(head[0], UP, buff=0.3)
        a_lab = T("答案", size=26, color=C_GOLD).next_to(head[1], UP, buff=0.3)
        self.play_bars(FadeIn(head), Create(hl), LaggedStart(*[FadeIn(r, shift=UP * 0.1) for r in rows],
                                                             lag_ratio=0.2), bars=1.25)
        sup = T("这种“题目 + 答案”的学法\n叫监督学习（最基础的一种机器学习）", size=22, color=C_GREY,
                line_spacing=0.9)
        sup.next_to(table, DOWN, buff=0.45)
        self.play_bars(FadeIn(q_lab), FadeIn(a_lab), FadeIn(sup), bars=0.5)
        # 33–34 坐标轴
        self.at_bar(33)
        ax, labs = make_axes()
        ax.move_to([2.6, 0.2, 0])
        labs = make_axes()[1]
        labs[0].next_to(ax.x_axis, DOWN, buff=0.45).align_to(ax.x_axis, RIGHT)
        labs[1].next_to(ax.y_axis, UP, buff=0.15).align_to(ax.y_axis, LEFT)
        boxes = VGroup(*[SurroundingRectangle(r, color=C_YELLOW, buff=0.08, stroke_width=2) for r in rows])
        self.play_bars(Create(ax), FadeIn(labs), bars=1)
        self.play_bars(LaggedStart(*[ShowPassingFlash(b, time_width=0.6) for b in boxes], lag_ratio=0.2), bars=1)
        # 35–36 点落到坐标纸上（先把表格里的 5 行变成点，再补齐 20 个）
        self.at_bar(35)
        target_ax = ax.copy().move_to([-1.6, 0.25, 0])
        self.play_bars(FadeOut(VGroup(table, hl, q_lab, a_lab, sup)), ax.animate.move_to(target_ax),
                       labs.animate.shift(target_ax.get_center() - ax.get_center()), bars=0.5)
        dots = VGroup(*[Dot(ax.c2p(x, y), radius=0.075, color=C_BLUE) for x, y in zip(TEMPS, SALES)])
        self.play_bars(LaggedStart(*[FadeIn(d, scale=2.5) for d in dots], lag_ratio=0.12), bars=1.5)
        self.ax, self.labs, self.dots = ax, labs, dots
        # 37–38 趋势
        self.at_bar(37)
        trend = DashedLine(ax.c2p(12, 40), ax.c2p(34, 230), color=C_TEAL, stroke_width=3).add_tip(tip_length=0.25)
        tt = T("越热，卖得越多", size=30, color=C_TEAL).next_to(ax.c2p(20, 220), UP, buff=0.1)
        self.play_bars(Create(trend), FadeIn(tt), bars=1)
        self.at_bar(38.5)
        self.play_bars(FadeOut(trend), FadeOut(tt), bars=0.5)
        # 39–40 直线
        self.at_bar(39)
        self.w = ValueTracker(2.0)
        self.b = ValueTracker(150.0)

        def line_now():
            seg = clip_line(self.w.get_value(), self.b.get_value())
            if seg is None:
                return VMobject()
            (xa, ya), (xb, yb) = seg
            return Line(ax.c2p(xa, ya), ax.c2p(xb, yb), color=C_YELLOW, stroke_width=5)

        self.fit_line = always_redraw(line_now)
        self.play_bars(Create(self.fit_line), bars=0.5)
        self.play_bars(self.w.animate.set_value(6.5), self.b.animate.set_value(-20), bars=1.5)
        # 41–42 公式与旋钮
        self.at_bar(41)
        formula = VGroup(T("y", size=48, color=C_GOLD), T("=", size=48), T("w", size=48, color=C_YELLOW),
                         T("·", size=48), T("x", size=48, color=C_BLUE), T("+", size=48),
                         T("b", size=48, color=C_YELLOW)).arrange(RIGHT, buff=0.15).move_to([4.6, 2.3, 0])
        wl = T("斜率", size=24, color=C_YELLOW).next_to(formula[2], DOWN, buff=0.2)
        bl = T("截距", size=24, color=C_YELLOW).next_to(formula[6], DOWN, buff=0.2)
        kw = Knob("w", self.w, 0, 16).move_to([3.5, 0.0, 0])
        kb = Knob("b", self.b, -200, 100).move_to([5.7, 0.0, 0])
        self.formula = VGroup(formula, wl, bl)
        self.knobs = VGroup(kw, kb)
        self.play_bars(Write(formula), bars=1)
        self.play_bars(FadeIn(wl), FadeIn(bl), FadeIn(self.knobs, shift=UP * 0.2), bars=1)
        # 43–44 分别拧 w、b
        self.at_bar(43)
        third = 1 / 3
        self.play_bars(Indicate(kw.disk, color=C_YELLOW), self.w.animate.set_value(12), bars=third)
        self.play_bars(self.w.animate.set_value(4), bars=third)
        self.play_bars(self.w.animate.set_value(W_FIT), until=44)
        self.play_bars(Indicate(kb.disk, color=C_YELLOW), self.b.animate.set_value(40), bars=third)
        self.play_bars(self.b.animate.set_value(-120), bars=third)
        self.play_bars(self.b.animate.set_value(-30), until=45)
        # 45–46 计数器 = 2
        self.at_bar(45)
        self.set_counter("2", bars=0.75)
        self.play_bars(self.w.animate.set_value(9.5), self.b.animate.set_value(-70), bars=0.75)
        self.play_bars(self.w.animate.set_value(6.0), self.b.animate.set_value(10), bars=0.5)

    # ------------------------------------------------------------ 间奏一 47–50
    def inst1(self):
        self.at_bar(47)
        for w, b in [(13, -170), (3, 70), (10.5, -120), (5.5, 10)]:
            self.play_bars(self.w.animate.set_value(w), self.b.animate.set_value(b), bars=0.875,
                           rate_func=smooth)
        self.plot_group = VGroup(self.ax, self.labs, self.dots, self.formula, self.knobs)
        self.at_bar(50.5)
        self.play_bars(FadeOut(self.plot_group), FadeOut(self.fit_line), bars=0.5)

    # ------------------------------------------------------------ 主歌三 61–76
    def verse3(self):
        self.at_bar(61)
        self.tag("误差与损失")
        ax = self.ax
        self.w.set_value(5.5)
        self.b.set_value(10)
        # 收起公式，让位给损失条
        self.formula.scale(0.7).move_to([4.6, 2.75, 0])
        self.knobs.scale(0.75).move_to([4.6, 1.15, 0])
        self.play_bars(FadeIn(VGroup(ax, self.labs, self.dots, self.formula, self.knobs)),
                       FadeIn(self.fit_line), bars=0.5)
        qbest = T("哪条线最好？", size=34, color=C_WHITE).move_to([4.6, -0.6, 0])
        self.play_bars(FadeIn(qbest, shift=UP * 0.2), bars=0.75)
        # 63–64 误差竖线
        self.at_bar(63)

        def resid():
            w, b = self.w.get_value(), self.b.get_value()
            g = VGroup()
            for x, y in zip(TEMPS, SALES):
                yp = np.clip(w * x + b, Y0, Y1)
                g.add(Line(ax.c2p(x, y), ax.c2p(x, yp), color=C_RED, stroke_width=3))
            return g

        res = always_redraw(resid)
        self.play_bars(FadeOut(qbest), Create(res), bars=1)
        el = T("误差", size=30, color=C_RED).move_to([4.6, -0.6, 0])
        self.play_bars(FadeIn(el), bars=0.5)
        # 65–66 正负 → 平方
        self.at_bar(65)
        w, b = self.w.get_value(), self.b.get_value()
        r = SALES - (w * TEMPS + b)
        ip, im = int(np.argmax(r)), int(np.argmin(r))
        plus = T("+", size=40, color=C_RED, weight=BOLD).next_to(ax.c2p(TEMPS[ip], SALES[ip]), LEFT, buff=0.12)
        minus = T("−", size=40, color=C_RED, weight=BOLD).next_to(ax.c2p(TEMPS[im], SALES[im]), RIGHT, buff=0.12)
        self.play_bars(FadeIn(plus, scale=1.5), FadeIn(minus, scale=1.5), bars=0.75)
        cancel = T("+ 和 − 会互相抵消", size=26, color=C_GREY).next_to(el, DOWN, buff=0.25)
        self.play_bars(FadeIn(cancel), bars=0.5)
        sq_t = T("→ 先平方", size=30, color=C_RED).next_to(cancel, DOWN, buff=0.2)
        self.play_bars(FadeIn(sq_t, shift=RIGHT * 0.2), bars=0.5)
        # 67–68 方块
        self.at_bar(67)

        def squares():
            w, b = self.w.get_value(), self.b.get_value()
            g = VGroup()
            for x, y in zip(TEMPS, SALES):
                yp = np.clip(w * x + b, Y0, Y1)
                p1, p2 = ax.c2p(x, y), ax.c2p(x, yp)
                s = abs(p1[1] - p2[1])
                if s < 1e-3:
                    continue
                sq = Rectangle(width=s, height=s, stroke_color=C_RED, stroke_width=1.5,
                               fill_color=C_RED, fill_opacity=0.22)
                sq.move_to((p1 + p2) / 2 + RIGHT * s / 2)
                g.add(sq)
            return g

        sqs = always_redraw(squares)
        self.play_bars(FadeOut(plus), FadeOut(minus), FadeIn(sqs), bars=1)
        self.at_bar(68)
        self.play_bars(FadeOut(cancel), FadeOut(sq_t), FadeOut(el), bars=0.5)
        # 69–70 损失条
        self.at_bar(69)

        def mse():
            return float(np.mean((SALES - (self.w.get_value() * TEMPS + self.b.get_value())) ** 2))

        m0 = 4500.0
        loss_lab = T("损失 = 平均( 误差² )", size=30, color=C_RED).move_to([4.6, -0.35, 0])
        frame = Rectangle(width=3.6, height=0.36, stroke_color=C_RED, stroke_width=2).next_to(loss_lab, DOWN, buff=0.3)

        def loss_bar():
            v = min(mse() / m0, 1.0)
            r_ = Rectangle(width=max(3.5 * v, 0.02), height=0.28, stroke_width=0, fill_color=C_RED, fill_opacity=0.9)
            return r_.move_to(frame).align_to(frame, LEFT).shift(RIGHT * 0.05)

        lb = always_redraw(loss_bar)
        num = always_redraw(lambda: T(f"{mse():,.0f}", size=28, color=C_RED).next_to(frame, DOWN, buff=0.18))
        self.play_bars(FadeIn(loss_lab), Create(frame), FadeIn(lb), FadeIn(num), bars=1)
        self.loss_ui = VGroup(loss_lab, frame)
        # 71–72 拧到最小
        self.at_bar(71)
        self.play_bars(self.w.animate.set_value(W_FIT), self.b.animate.set_value(B_FIT), bars=1.5, rate_func=smooth)
        best = T("损失最小 ✓", size=28, color=C_GREEN).next_to(num, DOWN, buff=0.15)
        self.play_bars(FadeIn(best, scale=1.2), bars=0.5)
        # 73–74 更多旋钮 → 曲线
        self.at_bar(73)
        note = T("注：直线的最佳 w、b\n其实能用公式直接算出；\n旋钮成千上万时才要一步步调\n（第 03 集）",
                 size=20, color=C_GREY, line_spacing=0.9).move_to([4.45, -1.85, 0])
        cub = np.polyfit(TEMPS, SALES, 3)
        curve = clipped_curve(ax, lambda x: np.polyval(cub, x), C_ORANGE, 5)
        four = VGroup(*[Knob(n, ValueTracker(v), 0, 1, radius=0.28) for n, v in
                        zip(["a", "b", "c", "d"], [0.3, 0.6, 0.45, 0.7])]).arrange(RIGHT, buff=0.22)
        for kn in four:
            kn[-1].scale(0.8)
        four.move_to([4.45, 1.15, 0])
        cl = T("y = a·x³ + b·x² + c·x + d", size=24, color=C_ORANGE).move_to([4.45, 2.75, 0])
        self.play_bars(FadeOut(VGroup(res, sqs, lb, num, best, self.loss_ui)), FadeOut(self.fit_line),
                       FadeOut(self.knobs), FadeOut(self.formula), FadeIn(four), FadeIn(cl), Create(curve),
                       FadeIn(note), bars=1)
        self.set_counter("4", bars=0.5)
        self.at_bar(74.5)
        # 75–76 越多越好？
        self.at_bar(75)
        qm = T("旋钮越多越好？", size=40, color=C_WHITE, weight=BOLD).move_to([4.45, -0.35, 0])
        self.play_bars(FadeIn(qm, scale=1.3), bars=0.75)
        self.at_bar(76.5)
        self.fade_rest(0.5)
        self.curve4 = curve

    # ------------------------------------------------------------ 桥段 77–84
    def bridge(self):
        self.at_bar(77)
        self.tag("学习 = ？")
        tr = ValueTracker(0.1)
        big = Knob("·", tr, 0, 1, radius=1.3).move_to([-2.2, 0.3, 0])
        big[-1].set_opacity(0)
        frame = Rectangle(width=0.7, height=4.0, stroke_color=C_RED, stroke_width=2).move_to([2.2, 0.3, 0])
        lvl = ValueTracker(1.0)
        fill = always_redraw(lambda: Rectangle(width=0.6, height=max(3.9 * lvl.get_value(), 0.02),
                                               stroke_width=0, fill_color=C_RED, fill_opacity=0.9)
                             .move_to(frame).align_to(frame, DOWN).shift(UP * 0.05))
        el = T("误差", size=30, color=C_RED).next_to(frame, DOWN, buff=0.25)
        self.play_bars(FadeIn(big), Create(frame), FadeIn(fill), FadeIn(el), bars=1)
        for i, v in enumerate([0.72, 0.5, 0.32, 0.2, 0.12]):
            self.play_bars(tr.animate.set_value(0.1 + 0.13 * (i + 1)), lvl.animate.set_value(v), bars=0.5)
        self.at_bar(81)
        eq = T("学习 = 拧旋钮，让误差变小", size=52, color=C_GOLD, weight=BOLD).move_to([0, 2.7, 0])
        self.play_bars(Write(eq), bars=1.5)
        self.play_bars(tr.animate.set_value(0.95), lvl.animate.set_value(0.05), bars=2)
        self.fade_rest(0.5)

    # ------------------------------------------------------------ 主歌四 85–100
    def verse4(self):
        self.at_bar(85)
        self.tag("过拟合与泛化")
        ax, labs = make_axes()
        ax.move_to([-1.6, 0.25, 0])
        labs[0].next_to(ax.x_axis, DOWN, buff=0.45).align_to(ax.x_axis, RIGHT)
        labs[1].next_to(ax.y_axis, UP, buff=0.15).align_to(ax.y_axis, LEFT)
        tr = VGroup(*[Dot(ax.c2p(x, y), radius=0.085, color=C_BLUE) for x, y in zip(TR_X, TR_Y)])
        wig = clipped_curve(ax, poly_f, C_ORANGE, 5)
        lab8 = T("8 个旋钮的曲线", size=28, color=C_ORANGE).move_to([4.6, 2.4, 0])
        self.play_bars(FadeIn(ax), FadeIn(labs), LaggedStart(*[FadeIn(d, scale=2) for d in tr], lag_ratio=0.1),
                       bars=0.5)
        self.play_bars(Create(wig), FadeIn(lab8), bars=0.75)
        self.set_counter("8", bars=0.5)
        # 87–88 训练误差 = 0
        self.at_bar(87)
        z = T("训练误差 = 0", size=34, color=C_GREEN).move_to([4.6, 1.4, 0])
        stamp = VGroup(Circle(radius=0.62, color=C_RED, stroke_width=5),
                       T("满分", size=30, color=C_RED, weight=BOLD)).rotate(0.25).move_to([4.6, 0.1, 0])
        self.play_bars(FadeIn(z), bars=0.75)
        self.play_bars(FadeIn(stamp, scale=1.8), bars=0.5)
        # 89–90 新数据
        self.at_bar(89)
        te = VGroup(*[Circle(radius=0.09, color=C_TEAL, stroke_width=4).move_to(ax.c2p(x, y))
                      for x, y in zip(TE_X, TE_Y)])
        te_res = VGroup(*[Line(ax.c2p(x, y), ax.c2p(x, float(np.clip(poly_f(x), Y0, Y1))), color=C_RED,
                               stroke_width=4) for x, y in zip(TE_X, TE_Y)])
        nl = T("新数据：误差很大！", size=32, color=C_RED).move_to([4.6, -1.2, 0])
        self.play_bars(FadeOut(stamp), LaggedStart(*[FadeIn(c, scale=2) for c in te], lag_ratio=0.15), bars=0.75)
        self.play_bars(Create(te_res), FadeIn(nl), bars=1)
        # 91–92 过拟合 vs 直线
        self.at_bar(91)
        of = T("过拟合 = 背答案", size=36, color=C_ORANGE, weight=BOLD).move_to([4.6, 2.4, 0])
        seg = clip_line(W_TR, B_TR)
        st = Line(ax.c2p(*seg[0]), ax.c2p(*seg[1]), color=C_YELLOW, stroke_width=4)
        st_res = VGroup(*[Line(ax.c2p(x, y), ax.c2p(x, W_TR * x + B_TR), color=C_YELLOW, stroke_width=3)
                          for x, y in zip(TE_X, TE_Y)])
        sl = T("2 个旋钮的直线：新数据误差小", size=24, color=C_YELLOW).move_to([4.6, -0.2, 0])
        self.play_bars(ReplacementTransform(lab8, of), FadeOut(z), bars=0.5)
        self.play_bars(Create(st), bars=0.5)
        self.play_bars(FadeOut(te_res), Create(st_res), FadeIn(sl), nl.animate.set_opacity(0.35), bars=0.75)
        self.at_bar(92.75)
        self.play_bars(*[FadeOut(m) for m in (ax, labs, tr, wig, te, st, st_res, sl, nl, of)], bars=0.25)
        # 93–94 训练集 / 测试集
        self.at_bar(93)
        self.set_counter("2", bars=0.25)
        cells = VGroup(*[Square(side_length=0.48, stroke_width=2) for _ in range(20)]).arrange(RIGHT, buff=0.1)
        cells.move_to([0, 0.9, 0])
        for i, c in enumerate(cells):
            if i < 16:
                c.set_stroke(C_BLUE).set_fill(C_BLUE, 0.35)
            else:
                c.set_stroke(C_GREY).set_fill(C_GREY, 0.2)
        locks = VGroup(*[
            VGroup(RoundedRectangle(width=0.22, height=0.16, corner_radius=0.03, color=C_GREY,
                                    fill_opacity=1).shift(DOWN * 0.04),
                   Arc(radius=0.07, angle=PI, color=C_GREY, stroke_width=3).shift(UP * 0.06)).move_to(c)
            for c in cells[16:]])
        b1 = Brace(cells[:16], DOWN, color=C_BLUE)
        t1 = T("训练集：给它看、拿来调旋钮", size=26, color=C_BLUE).next_to(b1, DOWN, buff=0.15)
        b2 = Brace(cells[16:], DOWN, color=C_GREY)
        t2 = T("测试集：藏起来，最后考", size=26, color=C_GREY).next_to(b2, DOWN, buff=0.15).shift(DOWN * 0.75)
        self.play_bars(LaggedStart(*[FadeIn(c, shift=DOWN * 0.2) for c in cells], lag_ratio=0.04), bars=0.75)
        self.play_bars(FadeIn(locks), GrowFromCenter(b1), FadeIn(t1), GrowFromCenter(b2), FadeIn(t2), bars=1)
        # 95–96 考试 → 泛化
        self.at_bar(95)
        checks = VGroup(*[T("✓", size=34, color=C_GREEN, weight=BOLD).move_to(c) for c in cells[16:]])
        self.play_bars(*[c.animate.set_stroke(C_GREEN).set_fill(C_GREEN, 0.25) for c in cells[16:]],
                       FadeOut(locks), LaggedStart(*[FadeIn(k, scale=1.5) for k in checks], lag_ratio=0.2), bars=1)
        gen = T("泛化：没见过的题，也能答对", size=40, color=C_GREEN, weight=BOLD).move_to([0, -1.9, 0])
        self.play_bars(FadeIn(gen, shift=UP * 0.2), bars=0.75)
        self.at_bar(96.75)
        self.play_bars(*[FadeOut(m) for m in (cells, checks, b1, t1, b2, t2, gen)], bars=0.25)
        # 97–98 同心圆
        self.at_bar(97)
        c_ai = Ellipse(width=10.5, height=4.9, color=C_BLUE, stroke_width=4, fill_color=C_BLUE, fill_opacity=0.06).move_to([0, 0.35, 0])
        c_ml = Ellipse(width=7.0, height=3.3, color=C_YELLOW, stroke_width=4, fill_color=C_YELLOW, fill_opacity=0.06).move_to([0, 0.05, 0])
        c_dl = Ellipse(width=3.8, height=1.6, color=C_GOLD, stroke_width=4, fill_color=C_GOLD, fill_opacity=0.1).move_to([0, -0.35, 0])
        l_ai = T("人工智能", size=34, color=C_BLUE).move_to([0, 2.3, 0])
        l_ml = T("机器学习", size=32, color=C_YELLOW).move_to([0, 1.2, 0])
        l_dl = T("深度学习（神经网络）", size=28, color=C_GOLD).move_to(c_dl)
        hist = T("“人工智能”一词出自 1956 年达特茅斯会议的提案", size=22, color=C_GREY).move_to([0, -2.45, 0])
        self.play_bars(DrawBorderThenFill(c_ai), FadeIn(l_ai), FadeIn(hist), bars=0.75)
        self.play_bars(DrawBorderThenFill(c_ml), FadeIn(l_ml), bars=0.75)
        # 99–100 深度学习 → 下集
        self.at_bar(99)
        self.play_bars(DrawBorderThenFill(c_dl), FadeIn(l_dl), bars=0.75)
        nx = T("→ 第 02 集", size=30, color=C_GOLD).next_to(c_dl, RIGHT, buff=0.3)
        self.play_bars(FadeIn(nx, shift=RIGHT * 0.2), Indicate(l_dl, color=C_GOLD), bars=0.75)
        self.at_bar(100.5)
        self.fade_rest(0.5)

    # ------------------------------------------------------------ 间奏二 101–104：要点卡
    def inst2(self):
        self.at_bar(101)
        self.tag("本集要点")
        head = T("本集要点", size=46, color=C_YELLOW, weight=BOLD)
        pts = [
            "1. 机器学习：不写规则，从“题目 + 答案”里找规律",
            "2. 模型 = 带旋钮（参数）的函数；直线 y = w·x + b 只有 2 个旋钮",
            "3. 损失 = 误差平方的平均；学习 = 调旋钮让损失变小",
            "4. 背下训练题不算会，没见过的测试题也答对才算（泛化）",
        ]
        items = VGroup(*[T(p, size=30) for p in pts]).arrange(DOWN, aligned_edge=LEFT, buff=0.32)
        g = VGroup(head, items).arrange(DOWN, buff=0.5).move_to([0, 0.35, 0])
        self.play_bars(FadeIn(head, shift=DOWN * 0.2), bars=0.25)
        for it in items:
            self.play_bars(FadeIn(it, shift=RIGHT * 0.3), bars=0.5)
        self.at_bar(104.5)
        self.play_bars(FadeOut(g), bars=0.5)

    # ------------------------------------------------------------ 尾声 115–122
    def outro(self):
        self.at_bar(115)
        self.tag("回顾")
        steps = [("给例子", C_BLUE), ("猜一猜", C_GOLD), ("量误差", C_RED), ("拧旋钮", C_YELLOW), ("考新题", C_GREEN)]
        chips = VGroup()
        for s, col in steps:
            t = T(s, size=32, color=col)
            chips.add(VGroup(SurroundingRectangle(t, color=col, buff=0.18, corner_radius=0.12, stroke_width=2.5), t))
        chips.arrange(RIGHT, buff=0.7).move_to([0, 0.8, 0])
        arrows = VGroup(*[Arrow(chips[i].get_right(), chips[i + 1].get_left(), buff=0.08, color=C_GREY,
                                stroke_width=3, max_tip_length_to_length_ratio=0.35) for i in range(4)])
        self.play_bars(FadeIn(chips[0]), bars=0.5)
        for i in (1, 2):
            self.play_bars(GrowArrow(arrows[i - 1]), FadeIn(chips[i]), bars=0.5)
        self.at_bar(117)
        for i in (3, 4):
            self.play_bars(GrowArrow(arrows[i - 1]), FadeIn(chips[i]), bars=0.5)
        way = T("= 机器学习的方法", size=40, color=C_WHITE, weight=BOLD).next_to(chips, DOWN, buff=0.6)
        self.play_bars(FadeIn(way, shift=UP * 0.2), bars=0.75)
        self.at_bar(118.75)
        self.play_bars(FadeOut(VGroup(chips, arrows, way)), bars=0.25)
        # 119–120 一张图
        self.at_bar(119)
        grid = pixel_seven().move_to([-2.2, 0.25, 0])
        gl = T("28 × 28 = 784 个像素", size=28, color=C_BLUE).next_to(grid, DOWN, buff=0.25)
        self.play_bars(LaggedStart(*[FadeIn(s) for s in grid], lag_ratio=0.002), bars=1)
        self.play_bars(FadeIn(gl), Wiggle(self.counter, scale_value=1.25), bars=0.75)
        q = T("2 个旋钮？", size=40, color=C_YELLOW).move_to([3.4, 2.3, 0])
        self.play_bars(FadeIn(q), bars=0.25)
        # 121–122 下集
        self.at_bar(121)
        nxt = VGroup(T("下集", size=30, color=C_GREY), T("神经网络", size=48, color=C_GOLD, weight=BOLD),
                     T("一层一层的小开关", size=32, color=C_GOLD)).arrange(DOWN, buff=0.25).move_to([3.4, 0.4, 0])
        self.play_bars(FadeOut(q), FadeIn(nxt, shift=UP * 0.2), bars=0.5)
        for s in ["16", "250", "1,000", "4,700", "9,100", "13,002"]:
            self.set_counter(s, bars=0.125)
        self.play_bars(*[FadeOut(m) for m in self.visible()], bars=0.75)
