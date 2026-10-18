# -*- coding: utf-8 -*-
"""
第 03 集《梯度下降：蒙着眼睛下山》

时间全部对齐 bars.py 的 BPM 小节网格（80 BPM，118 小节）。字幕由 build.py 烧录。
    ~/.venvs/manim/bin/python ../common/build.py 03_梯度下降 [--preview]

三维曲面用自写的正交投影画在普通 Scene 里（不用 ThreeDScene），便于和字幕、二维元素混排。
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "common"))
from style import *  # noqa: E402,F401

# ---------------------------------------------------------------- 第 01 集的冷饮数据（同一随机种子）
_r = np.random.default_rng(7)
TEMPS = np.sort(_r.uniform(12, 34, 20))
SALES = np.clip(8.0 * TEMPS - 60 + _r.normal(0, 14, 20), 5, 250)
XBAR = TEMPS.mean()
XC = TEMPS - XBAR
W_STAR = float(np.polyfit(XC, SALES, 1)[0])
B_STAR = float(SALES.mean())
WS, BS = 8.0, 80.0                       # 显示坐标：u = (w − w*)/8，v = (b − b*)/80


def wb(u, v):
    return W_STAR + WS * u, B_STAR + BS * v


def loss_uv(u, v):
    w, b = wb(u, v)
    return float(np.mean((SALES - w * XC - b) ** 2))


L_MIN = loss_uv(0, 0)
A_U = WS ** 2 * float(np.mean(XC ** 2))  # L = L_min + A_U·u² + B_V·v²（x 已居中，无交叉项）
B_V = BS ** 2
ZS = (loss_uv(1, 1) - L_MIN) / 2.1      # 高度缩放：角上约 2.1


def z_uv(u, v):
    return (loss_uv(u, v) - L_MIN) / ZS


def grad_uv(u, v):
    return 2 * A_U * u, 2 * B_V * v


ETA = 0.25 / B_V                         # v 方向每步缩一半，u 方向每步缩约 0.8
U0, V0 = -0.92, 0.88
GD_PATH = [(U0, V0)]
for _ in range(14):
    u, v = GD_PATH[-1]
    gu, gv = grad_uv(u, v)
    GD_PATH.append((u - ETA * gu, v - ETA * gv))

X0, X1, Y0, Y1 = 10, 36, 0, 260


def clip_line(w, b):
    """y = w (x − x̄) + b 在坐标框内的端点"""
    pts = []
    for x in (X0, X1):
        y = w * (x - XBAR) + b
        if Y0 <= y <= Y1:
            pts.append((x, y))
    if abs(w) > 1e-9:
        for y in (Y0, Y1):
            x = (y - b) / w + XBAR
            if X0 < x < X1:
                pts.append((x, y))
    pts = sorted(set(pts))
    return (pts[0], pts[-1]) if len(pts) >= 2 else None


def proj(u, v, z, th, el, center, s=2.0, zs=1.0):
    x, y = u * s, v * s
    xr = x * np.cos(th) - y * np.sin(th)
    yr = x * np.sin(th) + y * np.cos(th)
    return center + np.array([xr, z * zs * np.cos(el) + yr * np.sin(el), 0])


def wire_surface(zf, th, el, center, s=2.0, zs=1.0, n=15, m=34, zmax=2.4, lo=C_TEAL, hi=C_RED, width=1.6):
    g = VGroup()
    ts = np.linspace(-1, 1, m)
    for k in np.linspace(-1, 1, n):
        for mode in (0, 1):
            pts, zz = [], []
            for t in ts:
                u, v = (t, k) if mode == 0 else (k, t)
                z = zf(u, v)
                zz.append(z)
                pts.append(proj(u, v, z, th, el, center, s, zs))
            col = interpolate_color(ManimColor(lo), ManimColor(hi), float(np.clip(np.mean(zz) / zmax, 0, 1)))
            g.add(VMobject(stroke_color=col, stroke_width=width, stroke_opacity=0.75).set_points_smoothly(pts))
    return g


def make_axes():
    ax = Axes(x_range=[X0, X1, 5], y_range=[Y0, Y1, 50], x_length=5.4, y_length=3.6,
              axis_config=dict(color=C_GREY, stroke_width=2, include_tip=False))
    lab = VGroup(T("气温", size=20, color=C_GREY).next_to(ax.x_axis, DOWN, buff=0.15).align_to(ax.x_axis, RIGHT),
                 T("冷饮", size=20, color=C_GREY).next_to(ax.y_axis, UP, buff=0.1).align_to(ax.y_axis, LEFT))
    return ax, lab


# 雾中山路（一维）
def hill(x):
    return 0.09 * x ** 2 + 0.12 * np.sin(2.2 * x)


def dhill(x):
    return 0.18 * x + 0.264 * np.cos(2.2 * x)


HILL_PATH = [-5.3]
for _ in range(9):
    HILL_PATH.append(HILL_PATH[-1] - 2.6 * dhill(HILL_PATH[-1]))


class Video(BeatScene):
    EP_DIR = os.path.dirname(os.path.abspath(__file__))

    def construct(self):
        self.counter = None
        self.intro()          # 1–4
        self.verse1()         # 5–20
        self.hook(21)         # 21–30
        self.verse2()         # 31–46
        self.inst()           # 47–50
        self.hook(51)         # 51–60
        self.verse3()         # 61–76
        self.bridge()         # 77–84
        self.verse4()         # 85–100
        self.hook(101)        # 101–110
        self.outro()          # 111–118
        self.finish()

    # ------------------------------------------------------------ 公共部件
    def hillside(self, center=np.array([0, -0.3, 0]), sx=1.0, sy=0.8, fog=0.14):
        def P(x):
            return center + np.array([x * sx, hill(x) * sy, 0])
        full = VMobject(stroke_color=C_WHITE, stroke_width=4, stroke_opacity=fog).set_points_smoothly(
            [P(x) for x in np.linspace(-6, 6, 160)])
        return full, P

    def spotlight(self, xt, P, half=0.85):
        def seg():
            x = xt.get_value()
            xs = np.linspace(x - half, x + half, 30)
            return VMobject(stroke_color=C_WHITE, stroke_width=6).set_points_smoothly([P(t) for t in xs])

        def halo():
            return Circle(radius=0.9, stroke_width=0, fill_color=C_GOLD, fill_opacity=0.10).move_to(P(xt.get_value()))

        def ball():
            return Dot(P(xt.get_value()) + UP * 0.16, radius=0.14, color=C_GOLD)

        def arrow():
            x = xt.get_value()
            d = -np.sign(dhill(x)) if abs(dhill(x)) > 1e-3 else 1
            p0 = P(x) + UP * 0.45
            p1 = P(x + 0.7 * d) + UP * 0.45
            return Arrow(p0, p1, buff=0, color=C_GREEN, stroke_width=5, max_tip_length_to_length_ratio=0.35)

        return always_redraw(halo), always_redraw(seg), always_redraw(ball), always_redraw(arrow)

    def contour_panel(self, center=np.array([3.0, 0.2, 0]), s=2.3, levels=(0.1, 0.2, 0.3, 0.4, 0.5, 0.6)):
        """俯视等高线：u ∈ [−1, 1] 映射到 ±s"""
        ratio = np.sqrt(B_V / A_U)

        def c2p(u, v):
            return center + np.array([u * s, v * s, 0])

        ells = VGroup()
        for i, r in enumerate(levels):
            col = interpolate_color(ManimColor(C_TEAL), ManimColor(C_RED), i / (len(levels) - 1))
            ells.add(Ellipse(width=2 * r * ratio * s, height=2 * r * s, stroke_color=col, stroke_width=2.5).move_to(center))
        star = Star(n=5, outer_radius=0.12, color=C_GOLD, fill_opacity=1).move_to(center)
        labs = VGroup(T("w", size=24, color=C_YELLOW).move_to(center + np.array([ratio * 0.62 * s + 0.35, 0, 0])),
                      T("b", size=24, color=C_YELLOW).move_to(center + np.array([0, 0.62 * s + 0.3, 0])))
        return VGroup(ells, star, labs), c2p

    # ------------------------------------------------------------ 前奏 1–4
    def intro(self):
        card = title_card("第 03 集", "梯度下降", "蒙着眼睛下山")
        s, e, t, line, st = card
        self.play_bars(FadeIn(s, shift=DOWN * 0.2), FadeIn(e, shift=DOWN * 0.2), bars=0.75)
        self.play_bars(Write(t), bars=1)
        self.play_bars(GrowFromCenter(line), FadeIn(st, shift=UP * 0.2), bars=0.75)
        self.at_bar(3.5)
        self.set_counter("13,002", bars=0.5)
        self.at_bar(4.5)
        self.play_bars(FadeOut(card), bars=0.5)

    # ------------------------------------------------------------ 主歌一 5–20
    def verse1(self):
        self.at_bar(5)
        self.tag("13,002 个旋钮，往哪边拧？")
        r = np.random.default_rng(3)
        trs = [ValueTracker(r.uniform(0, 1)) for _ in range(40)]
        knobs = VGroup(*[Knob("·", t, 0, 1, radius=0.22) for t in trs])
        for k in knobs:
            k[-1].set_opacity(0)
        knobs.arrange_in_grid(rows=4, cols=10, buff=0.42)
        knobs.scale_to_fit_height(3.6).move_to([0, 0.65, 0])
        more = T("……共 13,002 个，全是随机的", size=28, color=C_GREY).next_to(knobs, DOWN, buff=0.4)
        self.play_bars(FadeIn(knobs), FadeIn(more), bars=0.5)
        self.play_bars(*[t.animate.set_value(r.uniform(0, 1)) for t in trs], bars=0.625)
        self.play_bars(*[t.animate.set_value(r.uniform(0, 1)) for t in trs], bars=0.625)
        # 7–8 回到直线
        self.at_bar(7)
        self.play_bars(FadeOut(knobs), FadeOut(more), bars=0.25)
        self.tag("先回到两个旋钮", bars=0.25)
        ax, lab = make_axes()
        ax.move_to([-3.6, 0.3, 0])
        lab = make_axes()[1]
        lab[0].next_to(ax.x_axis, DOWN, buff=0.15).align_to(ax.x_axis, RIGHT)
        lab[1].next_to(ax.y_axis, UP, buff=0.1).align_to(ax.y_axis, LEFT)
        dots = VGroup(*[Dot(ax.c2p(x, y), radius=0.06, color=C_BLUE) for x, y in zip(TEMPS, SALES)])
        self.u, self.v = ValueTracker(U0), ValueTracker(V0)

        def line_now():
            w, b = wb(self.u.get_value(), self.v.get_value())
            seg = clip_line(w, b)
            if seg is None:
                return VMobject()
            return Line(ax.c2p(*seg[0]), ax.c2p(*seg[1]), color=C_YELLOW, stroke_width=4)

        fit = always_redraw(line_now)
        self.ax, self.axlab, self.dots, self.fit = ax, lab, dots, fit
        self.play_bars(FadeIn(ax), FadeIn(lab), FadeIn(dots), Create(fit), bars=0.75)
        self.set_counter("2", bars=0.5)
        # 9–10 几组 w、b 与损失
        self.at_bar(9)
        rows = VGroup()
        tries = [(0.6, -0.5), (-0.5, 0.7), (0.2, 0.15)]
        head = T("w, b  →  损失", size=26, color=C_GREY).move_to([3.3, 2.4, 0])
        self.play_bars(FadeIn(head), bars=0.25)
        for i, (uu, vv) in enumerate(tries):
            t = T(f"第 {i + 1} 组  →  {loss_uv(uu, vv):,.0f}", size=26, color=C_RED).move_to([3.3, 1.8 - 0.55 * i, 0])
            rows.add(t)
            self.play_bars(self.u.animate.set_value(uu), self.v.animate.set_value(vv), FadeIn(t), bars=0.5)
        # 11–12 曲面
        self.at_bar(11)
        self.tag("损失地形图")
        self.th = ValueTracker(-0.55)
        el = 0.42
        cen = np.array([3.4, -0.6, 0])
        self.surf_cen, self.surf_el = cen, el
        surf = always_redraw(lambda: wire_surface(z_uv, self.th.get_value(), el, cen))
        self.surf = surf
        self.play_bars(FadeOut(rows), FadeOut(head), FadeIn(surf), bars=1)
        wl = always_redraw(lambda: T("w", size=26, color=C_YELLOW).move_to(
            proj(1.25, -1.0, 0, self.th.get_value(), el, cen)))
        bl = always_redraw(lambda: T("b", size=26, color=C_YELLOW).move_to(
            proj(-1.0, 1.25, 0, self.th.get_value(), el, cen)))
        zl = T("高度 = 损失", size=24, color=C_RED).move_to([3.4, 2.6, 0])
        self.surf_labels = VGroup(wl, bl, zl)
        self.play_bars(FadeIn(wl), FadeIn(bl), FadeIn(zl), bars=0.5)
        # 13–14 转一转：像只碗
        self.at_bar(13)
        self.play_bars(self.th.animate.set_value(0.35), bars=1.5)
        bowl = T("像一只碗", size=28, color=C_WHITE).move_to([5.6, 1.9, 0])
        self.play_bars(FadeIn(bowl), bars=0.5)
        # 15–16 碗底 = 最好的直线
        self.at_bar(15)
        bottom = always_redraw(lambda: Star(n=5, outer_radius=0.14, color=C_GOLD, fill_opacity=1).move_to(
            proj(0, 0, 0, self.th.get_value(), el, cen)))
        bt = T("碗底：损失最低", size=26, color=C_GOLD).move_to([3.4, -2.35, 0])
        self.play_bars(FadeOut(bowl), FadeIn(bottom), FadeIn(bt), bars=0.5)
        self.play_bars(self.u.animate.set_value(0), self.v.animate.set_value(0), bars=1)
        self.play_bars(Indicate(fit, color=C_GOLD), bars=0.5)
        # 17–20 小球下滑（梯度下降），直线跟着变
        self.at_bar(17)
        self.u.set_value(U0)
        self.v.set_value(V0)
        ball = always_redraw(lambda: Dot(proj(self.u.get_value(), self.v.get_value(),
                                              z_uv(self.u.get_value(), self.v.get_value()),
                                              self.th.get_value(), el, cen) + UP * 0.12,
                                         radius=0.12, color=C_GREEN))
        self.play_bars(FadeIn(ball), FadeOut(bt), bars=0.25)
        trail = VGroup()
        self.add(trail)
        steps = GD_PATH[1:]
        per = (3.5 - 0.25) / len(steps)
        for (uu, vv) in steps:
            p_prev = proj(self.u.get_value(), self.v.get_value(), z_uv(self.u.get_value(), self.v.get_value()),
                          self.th.get_value(), el, cen) + UP * 0.12
            p_new = proj(uu, vv, z_uv(uu, vv), self.th.get_value(), el, cen) + UP * 0.12
            seg = Line(p_prev, p_new, color=C_GREEN, stroke_width=3)
            trail.add(seg)
            self.play_bars(self.u.animate.set_value(uu), self.v.animate.set_value(vv), Create(seg), bars=per)
        self.at_bar(20.5)
        self.fade_rest(0.5)

    # ------------------------------------------------------------ 副歌：雾中下山
    def hook(self, s):
        self.at_bar(s)
        self.tag("蒙着眼睛下山")
        full, P = self.hillside(center=np.array([-0.8, -0.9, 0]))
        fogs = VGroup(*[Ellipse(width=w, height=h, stroke_width=0, fill_color=C_GREY, fill_opacity=0.07).move_to(p)
                        for w, h, p in ((7, 2.2, [-3, 0.8, 0]), (6, 1.8, [2.5, 1.6, 0]), (8, 2.4, [0, -0.2, 0]))])
        xt = ValueTracker(HILL_PATH[0])
        halo, seg, ball, arrow = self.spotlight(xt, P)
        self.play_bars(FadeIn(full), FadeIn(fogs), FadeIn(halo), FadeIn(seg), FadeIn(ball), bars=0.75)
        q = T("看不见整座山", size=26, color=C_GREY).move_to([-4.2, 2.4, 0])
        self.play_bars(FadeIn(q), fogs.animate.shift(RIGHT * 0.4), bars=1.0)
        # ② 迈一步
        self.at_bar(s + 2)
        self.play_bars(FadeIn(arrow), FadeOut(q), bars=0.5)
        self.play_bars(xt.animate.set_value(HILL_PATH[1]), bars=1)
        # ③ 一步一步
        self.at_bar(s + 4)
        for x in HILL_PATH[2:6]:
            self.play_bars(xt.animate.set_value(x), bars=0.5)
        # ④ 误差越来越小：小图
        self.at_bar(s + 6)
        lax = Axes(x_range=[0, 10], y_range=[0, 3], x_length=2.8, y_length=1.6, tips=False,
                   axis_config=dict(color=C_GREY, stroke_width=1.5)).move_to([4.6, 1.9, 0])
        lt = T("损失", size=20, color=C_RED).next_to(lax, UP, buff=0.08).align_to(lax, LEFT)
        st = T("步数", size=20, color=C_GREY).next_to(lax, DOWN, buff=0.08).align_to(lax, RIGHT)
        vals = [hill(x) + 0.0 for x in HILL_PATH]
        top = max(vals)
        curve = VMobject(stroke_color=C_RED, stroke_width=3).set_points_as_corners(
            [lax.c2p(i, 2.7 * (v - min(vals)) / (top - min(vals)) + 0.15) for i, v in enumerate(vals)])
        self.play_bars(FadeIn(lax), FadeIn(lt), FadeIn(st), bars=0.25)
        self.play_bars(Create(curve), *[xt.animate.set_value(HILL_PATH[-1])], bars=1.25)
        ok = T("够低了", size=22, color=C_GREEN).next_to(curve.get_end(), UP, buff=0.12)
        self.play_bars(FadeIn(ok), bars=0.5)
        # ⑤ 黑箱打开
        self.at_bar(s + 8)
        self.play_bars(*[FadeOut(m) for m in (full, fogs, halo, seg, ball, arrow, lax, lt, st, curve, ok)], bars=0.25)
        box = black_box(w=3.2, h=2.2, depth=0.45).move_to([0, 0.2, 0])
        pax = Axes(x_range=[-1, 1], y_range=[0, 1], x_length=1.8, y_length=1.1, tips=False,
                   axis_config=dict(stroke_width=1.2, color=C_GREY)).move_to(box.front)
        par = pax.plot(lambda x: x * x, color=C_RED, stroke_width=2.5)
        bx = ValueTracker(-0.85)
        bb = always_redraw(lambda: Dot(pax.c2p(bx.get_value(), bx.get_value() ** 2) + UP * 0.06, radius=0.06, color=C_GREEN))
        inner = VGroup(pax, par)
        self.play_bars(FadeIn(box), bars=0.25)
        self.play_bars(VGroup(box.front, box.q).animate.shift(UP * 0.3).set_opacity(0.12), FadeIn(inner), FadeIn(bb), bars=0.5)
        slogan = T("一层一层，把黑箱打开", size=40, color=C_YELLOW, weight=BOLD).to_edge(UP, buff=0.3)
        self.play_bars(Write(slogan), bx.animate.set_value(0.0), bars=0.5)
        self.at_bar(s + 9.5)
        self.fade_rest(0.5)

    # ------------------------------------------------------------ 主歌二 31–46：高维；梯度
    def verse2(self):
        self.at_bar(31)
        self.tag("一万多维的山")
        self.set_counter("13,002", bars=0.25)
        cen = np.array([0, 0.4, 0])
        rays = VGroup()
        labels = ["w₁", "w₂", "w₃", "w₄", "w₅", "w₆", "w₇", "w₈", "…", "…", "w₁₃₀₀₁", "w₁₃₀₀₂"]
        for i, nm in enumerate(labels):
            a = i * TAU / len(labels) + 0.15
            d = np.array([np.cos(a), np.sin(a), 0])
            rays.add(VGroup(Line(cen, cen + 2.0 * d, color=C_YELLOW, stroke_width=2.5),
                            T(nm, size=22, color=C_YELLOW).move_to(cen + 2.35 * d)))
        cant = T("画不出来", size=30, color=C_RED).move_to([4.6, 1.6, 0])
        self.play_bars(LaggedStart(*[Create(r_) for r_ in rays], lag_ratio=0.08), bars=1.0)
        self.play_bars(FadeIn(cant), bars=0.5)
        # 33–34 试不完
        self.at_bar(33)
        combo = VGroup(T("每个旋钮只试 10 个值：", size=30, color=C_WHITE),
                       T("10 × 10 × … × 10 = 10¹³⁰⁰² 种组合", size=34, color=C_RED)).arrange(DOWN, buff=0.3)
        combo.move_to([0, -1.7, 0])
        self.play_bars(rays.animate.scale(0.7).shift(UP * 0.5), FadeOut(cant), FadeIn(combo[0]), bars=0.75)
        self.play_bars(FadeIn(combo[1], scale=1.2), bars=0.75)
        self.at_bar(34.75)
        self.fade_rest(0.25)
        # 35–36 蒙眼站在雾里的山腰
        self.at_bar(35)
        self.tag("只能摸脚下")
        full, P = self.hillside(center=np.array([-0.3, -1.0, 0]), fog=0.1)
        x0 = -3.6
        foot = P(x0)
        person = VGroup(
            Circle(radius=0.22, color=C_WHITE, stroke_width=3).move_to(foot + UP * 1.35),
            Line(foot + UP * 1.13, foot + UP * 0.5, color=C_WHITE, stroke_width=3),
            Line(foot + UP * 0.5, foot + UP * 0.0 + LEFT * 0.2, color=C_WHITE, stroke_width=3),
            Line(foot + UP * 0.5, foot + UP * 0.05 + RIGHT * 0.2, color=C_WHITE, stroke_width=3),
            Line(foot + UP * 0.95 + LEFT * 0.3, foot + UP * 0.95 + RIGHT * 0.3, color=C_WHITE, stroke_width=3),
            Rectangle(width=0.5, height=0.09, stroke_width=0, fill_color=C_RED, fill_opacity=1).move_to(foot + UP * 1.4),
        )
        fogs = VGroup(*[Ellipse(width=w, height=h, stroke_width=0, fill_color=C_GREY, fill_opacity=0.09).move_to(p)
                        for w, h, p in ((7, 2.4, [-2.5, 0.8, 0]), (7, 2.0, [3.0, 1.2, 0]), (9, 2.6, [0.5, -0.4, 0]))])
        self.play_bars(FadeIn(full), FadeIn(fogs), FadeIn(person), bars=1)
        wq = T("往哪走？", size=30, color=C_GREY).next_to(person, UP, buff=0.3)
        self.play_bars(FadeIn(wq), bars=0.5)
        # 37–38 脚下的坡
        self.at_bar(37)
        tang = Line(P(x0 - 0.7), P(x0 + 0.7), color=C_WHITE, stroke_width=6)
        down = Arrow(P(x0) + UP * 0.2 + RIGHT * 0.3, P(x0 + 1.2) + UP * 0.2, buff=0, color=C_GREEN, stroke_width=5)
        dl = T("这边往下", size=26, color=C_GREEN).next_to(down, DOWN, buff=0.15)
        self.play_bars(FadeOut(wq), Create(tang), bars=0.5)
        self.play_bars(GrowArrow(down), FadeIn(dl), bars=0.75)
        self.at_bar(38.75)
        self.fade_rest(0.25)
        # 39–40 每个旋钮试着拧一点
        self.at_bar(39)
        self.tag("每个旋钮的坡度")
        trs = [ValueTracker(0.5) for _ in range(3)]
        ks = VGroup(*[Knob(n, t, 0, 1, radius=0.34) for n, t in zip(["w₁", "w₂", "w₃"], trs)]).arrange(DOWN, buff=0.35)
        ks.move_to([-4.2, 0.55, 0])
        deltas = ["+0.8", "−1.5", "+0.2"]
        dts = VGroup(*[T(f"拧一点 → 损失 {d}", size=26, color=C_RED if d.startswith("+") else C_GREEN)
                       .next_to(k, RIGHT, buff=0.5) for k, d in zip(ks, deltas)])
        self.play_bars(FadeIn(ks), bars=0.25)
        for t, d in zip(trs, dts):
            self.play_bars(t.animate.set_value(0.62), FadeIn(d, shift=RIGHT * 0.2), bars=0.3)
            t.set_value(0.5)
        note = T("（这里只是帮你理解“坡度”；实际不用一个个去试，第 04 集讲怎么一次算出来）",
                 size=19, color=C_GREY).move_to([0, -2.3, 0])
        self.play_bars(FadeIn(note), bars=0.5)
        # 41–42 梯度向量
        self.at_bar(41)
        entries = VGroup(*[T(x, size=28, color=C_WHITE) for x in ["+0.8", "−1.5", "+0.2", "⋮"]]).arrange(DOWN, buff=0.22)
        lb = T("[", size=110, color=C_WHITE).next_to(entries, LEFT, buff=0.1)
        rb = T("]", size=110, color=C_WHITE).next_to(entries, RIGHT, buff=0.1)
        vec = VGroup(lb, entries, rb).move_to([3.0, 0.35, 0])
        gl = T("梯度：上坡最陡的方向", size=30, color=C_RED).next_to(vec, RIGHT, buff=0.4)
        if gl.get_right()[0] > 6.8:
            gl.next_to(vec, UP, buff=0.3)
        cnt = T("一共 13,002 个数", size=22, color=C_GREY).next_to(vec, DOWN, buff=0.3)
        self.play_bars(TransformFromCopy(VGroup(*[d for d in dts]), entries), FadeIn(lb), FadeIn(rb), bars=1)
        self.play_bars(FadeIn(gl), FadeIn(cnt), bars=0.75)
        self.at_bar(42.75)
        self.fade_rest(0.25)
        # 43–44 等高线：梯度 vs 负梯度
        self.at_bar(43)
        self.tag("反着梯度走")
        panel, c2p = self.contour_panel(center=np.array([-1.0, 0.2, 0]))
        pu, pv = -0.55, 0.42
        P0 = c2p(pu, pv)
        # 梯度 ∝ (A·u, B·v) ∝ (u/ratio², v)，显示坐标与 (u, v) 只差同一个缩放
        ratio = np.sqrt(B_V / A_U)
        n_disp = np.array([pu / (ratio ** 2), pv, 0.0])
        n_disp = n_disp / np.linalg.norm(n_disp)
        dot = Dot(P0, radius=0.1, color=C_WHITE)
        up_arr = Arrow(P0, P0 + 1.2 * n_disp, buff=0, color=C_RED, stroke_width=6)
        upl = T("红：梯度（指向上坡）", size=26, color=C_RED).move_to([4.4, 1.0, 0])
        self.play_bars(FadeIn(panel), FadeIn(dot), bars=0.5)
        self.play_bars(GrowArrow(up_arr), FadeIn(upl), bars=0.5)
        dn_arr = Arrow(P0, P0 - 1.2 * n_disp, buff=0, color=C_GREEN, stroke_width=6)
        dnl = T("绿：负梯度（下坡最快）", size=26, color=C_GREEN).move_to([4.4, 0.4, 0])
        self.play_bars(ReplacementTransform(up_arr.copy(), dn_arr), FadeIn(dnl), up_arr.animate.set_opacity(0.3),
                       upl.animate.set_opacity(0.3), bars=0.75)
        # 45–46 负梯度场
        self.at_bar(45)
        field = VGroup()
        for uu in np.linspace(-0.85, 0.85, 7):
            for vv in np.linspace(-0.5, 0.5, 5):
                q_ = c2p(uu, vv)
                nd = np.array([uu / ratio ** 2, vv, 0.0])
                L_ = np.linalg.norm(nd)
                if L_ < 1e-6:
                    continue
                ln = min(0.55, 0.25 + 0.6 * L_)
                field.add(Arrow(q_, q_ - ln * nd / L_, buff=0, color=C_GREEN, stroke_width=3,
                                max_tip_length_to_length_ratio=0.3, stroke_opacity=0.8))
        fl = T("处处垂直于等高线，指向谷底", size=26, color=C_GREEN).move_to([4.4, -0.3, 0])
        self.play_bars(FadeOut(up_arr), FadeOut(upl), LaggedStart(*[GrowArrow(a) for a in field], lag_ratio=0.02),
                       bars=1.25)
        self.play_bars(FadeIn(fl), bars=0.5)
        self.panel, self.c2p, self.field = panel, c2p, field
        self.v2_extra = VGroup(dot, dn_arr, dnl, fl)

    # ------------------------------------------------------------ 间奏 47–50：等高线上的下山路径
    def inst(self):
        self.at_bar(47)
        c2p = self.c2p
        self.play_bars(FadeOut(self.field), FadeOut(self.v2_extra), bars=0.25)
        pts = [c2p(u, v) for u, v in GD_PATH]
        ball = Dot(pts[0], radius=0.11, color=C_GOLD)
        self.play_bars(FadeIn(ball, scale=1.5), bars=0.25)
        per = 3.0 / (len(pts) - 1)
        for p0, p1 in zip(pts[:-1], pts[1:]):
            a = Arrow(p0, p1, buff=0, color=C_GREEN, stroke_width=4, max_tip_length_to_length_ratio=0.3)
            self.play_bars(GrowArrow(a), ball.animate.move_to(p1), bars=per)
        self.at_bar(50.5)
        self.fade_rest(0.5)

    # ------------------------------------------------------------ 主歌三 61–76：学习率
    def verse3(self):
        self.at_bar(61)
        self.tag("学习率 = 步子多大")
        cfg = [("① 太小", 0.93, 14, C_BLUE), ("② 偏大：来回弹", -0.82, 9, C_ORANGE),
               ("③ 太大：飞出去", -1.3, 1, C_RED), ("④ 合适", 0.35, 5, C_GREEN)]
        centers = [np.array([-3.45, 1.15, 0]), np.array([3.45, 1.15, 0]),
                   np.array([-3.45, -1.45, 0]), np.array([3.45, -1.45, 0])]
        panels = []
        for (name, fac, n, col), c in zip(cfg, centers):
            ax = Axes(x_range=[-2.6, 2.6], y_range=[0, 7], x_length=5.6, y_length=2.0, tips=False,
                      axis_config=dict(color=C_GREY, stroke_width=1.5)).move_to(c)
            par = ax.plot(lambda x: x * x, x_range=[-2.6, 2.6], color=C_WHITE, stroke_width=2.5, stroke_opacity=0.7)
            tl = T(name, size=24, color=col).move_to(ax.c2p(-2.6, 6.6), aligned_edge=LEFT)
            ws = [-2.2]
            for _ in range(n):
                ws.append(ws[-1] * fac)
            panels.append(dict(ax=ax, par=par, tl=tl, ws=ws, col=col))
        self.play_bars(*[FadeIn(VGroup(p["ax"], p["par"], p["tl"])) for p in panels], bars=1)
        balls = []
        for p in panels:
            b = Dot(p["ax"].c2p(p["ws"][0], p["ws"][0] ** 2), radius=0.09, color=p["col"])
            balls.append(b)
        self.play_bars(*[FadeIn(b, scale=1.5) for b in balls], bars=0.5)

        def run(i, bars_total):
            p, b = panels[i], balls[i]
            ax, ws = p["ax"], p["ws"]
            per = bars_total / (len(ws) - 1)
            for w0, w1 in zip(ws[:-1], ws[1:]):
                def cp(w):
                    wc = float(np.clip(w, -2.75, 2.75))
                    return ax.c2p(wc, min(w * w, 7.6))
                end = cp(w1)
                seg = Line(cp(w0), end, color=p["col"], stroke_width=2.5)
                self.play_bars(Create(seg), b.animate.move_to(end), bars=per)

        # 63–64 太小
        self.at_bar(63)
        run(0, 1.75)
        # 65–66 偏大：来回弹
        self.at_bar(65)
        run(1, 1.75)
        # 67–68 太大：飞出去
        self.at_bar(67)
        run(2, 1.25)
        fly = T("飞出去了！", size=24, color=C_RED).move_to(panels[2]["ax"].c2p(1.2, 5.2))
        self.play_bars(balls[2].animate.shift(UP * 1.2 + RIGHT * 0.8).set_opacity(0), FadeIn(fly), bars=0.5)
        # 69–70 合适
        self.at_bar(69)
        run(3, 1.25)
        good = T("几步就到谷底", size=24, color=C_GREEN).next_to(panels[3]["ax"].c2p(0, 0), UP, buff=0.35)
        self.play_bars(FadeIn(good), Flash(balls[3], color=C_GREEN), bars=0.5)
        self.at_bar(70.75)
        self.fade_rest(0.25)
        # 71–72 更新公式
        self.at_bar(71)
        self.tag("每一步做什么")
        parts = VGroup(T("新旋钮", size=46, color=C_YELLOW), T("=", size=46), T("旧旋钮", size=46, color=C_YELLOW),
                       T("−", size=46, color=C_GREEN), T("学习率", size=46, color=C_TEAL), T("×", size=46),
                       T("梯度", size=46, color=C_RED)).arrange(RIGHT, buff=0.22).move_to([0, 1.1, 0])
        self.play_bars(LaggedStart(*[FadeIn(p_, shift=UP * 0.2) for p_ in parts], lag_ratio=0.12), bars=0.75)
        n1 = T("减号：反着梯度走（下坡）", size=24, color=C_GREEN).next_to(parts[3], DOWN, buff=0.6)
        n2 = T("学习率：步子多大", size=24, color=C_TEAL).next_to(parts[4], UP, buff=0.5)
        self.play_bars(FadeIn(n1), FadeIn(n2), bars=0.5)
        rep = T("然后重复：再算梯度，再迈一步", size=26, color=C_WHITE).move_to([0, -1.6, 0])
        self.play_bars(FadeIn(rep), bars=0.5)
        # 73–74 上万个旋钮一起动
        self.at_bar(73)
        self.play_bars(FadeOut(VGroup(n1, n2, rep)), parts.animate.scale(0.6).move_to([0, 2.5, 0]), bars=0.5)
        r = np.random.default_rng(8)
        trs = [ValueTracker(r.uniform(0.3, 0.7)) for _ in range(9)]
        row = VGroup(*[Knob(f"w{i + 1}", t, 0, 1, radius=0.38) for i, t in enumerate(trs)]).arrange(RIGHT, buff=0.32)
        if row.width > 11.5:
            row.scale_to_fit_width(11.5)
        row.move_to([0, 0.4, 0])
        dots = T("…… 一共 13,002 个，同时拧", size=26, color=C_GREY).next_to(row, DOWN, buff=0.45)
        self.play_bars(FadeIn(row), FadeIn(dots), bars=0.5)
        self.play_bars(*[t.animate.set_value(t.get_value() + r.uniform(-0.25, 0.25)) for t in trs], bars=1)
        # 75–76 训练曲线
        self.at_bar(75)
        self.play_bars(FadeOut(VGroup(row, dots, parts)), bars=0.25)
        cax = Axes(x_range=[0, 1000, 200], y_range=[0, 1.1], x_length=8, y_length=3.6, tips=False,
                   axis_config=dict(color=C_GREY, stroke_width=2)).move_to([-0.3, 0.2, 0])
        xl = T("训练步数", size=22, color=C_GREY).next_to(cax.x_axis, DOWN, buff=0.15).align_to(cax.x_axis, RIGHT)
        yl = T("损失", size=22, color=C_RED).next_to(cax.y_axis, UP, buff=0.1).align_to(cax.y_axis, LEFT)
        rr = np.random.default_rng(5)
        xs = np.linspace(0, 1000, 120)
        ys = 0.12 + 0.88 * np.exp(-xs / 180) + rr.normal(0, 0.012, xs.size)
        cv = VMobject(stroke_color=C_RED, stroke_width=3).set_points_as_corners([cax.c2p(x, y) for x, y in zip(xs, ys)])
        self.play_bars(FadeIn(cax), FadeIn(xl), FadeIn(yl), bars=0.25)
        self.play_bars(Create(cv), bars=0.75)
        flat = T("越走越平", size=26, color=C_WHITE).next_to(cax.c2p(800, 0.2), UP, buff=0.3)
        self.play_bars(FadeIn(flat), bars=0.25)
        self.at_bar(76.5)
        self.fade_rest(0.5)

    # ------------------------------------------------------------ 桥段 77–84
    def bridge(self):
        self.at_bar(77)
        self.tag("看不清整座山")
        full, P = self.hillside(center=np.array([0, -0.9, 0]), fog=0.05)
        fogs = VGroup(*[Ellipse(width=w, height=h, stroke_width=0, fill_color=C_GREY, fill_opacity=0.12).move_to(p)
                        for w, h, p in ((9, 3.0, [-2.5, 0.6, 0]), (8, 2.6, [3.0, 1.3, 0]), (11, 3.2, [0.5, -0.6, 0]))])
        self.play_bars(FadeIn(full), FadeIn(fogs), bars=1.25)
        self.play_bars(fogs.animate.shift(RIGHT * 0.8), bars=2.5)
        # 81–84 脚下
        self.at_bar(81)
        xt = ValueTracker(-3.4)
        halo, seg, ball, arrow = self.spotlight(xt, P)
        self.play_bars(FadeIn(halo), FadeIn(seg), FadeIn(ball), bars=1)
        self.play_bars(FadeIn(arrow), bars=1)
        self.play_bars(xt.animate.set_value(-2.2), fogs.animate.shift(RIGHT * 0.4), bars=1.5)
        self.fade_rest(0.5)

    # ------------------------------------------------------------ 主歌四 85–100
    def verse4(self):
        self.at_bar(85)
        self.tag("随机梯度下降")
        cells = VGroup(*[Square(side_length=0.2, stroke_width=0.8, stroke_color=C_BLUE, fill_color=C_BLUE, fill_opacity=0.35)
                         for _ in range(300)]).arrange_in_grid(rows=12, cols=25, buff=0.05).move_to([-1.2, 0.5, 0])
        cl = T("训练数据（例如 60,000 张）", size=26, color=C_BLUE).next_to(cells, UP, buff=0.25)
        glass = VGroup(Triangle(color=C_GREY, fill_opacity=0.2).scale(0.3).rotate(PI),
                       Triangle(color=C_GREY, fill_opacity=0.2).scale(0.3)).arrange(DOWN, buff=0).move_to([5.0, 0.5, 0])
        slow = T("每步都全算：太慢", size=26, color=C_RED).next_to(glass, DOWN, buff=0.3)
        self.play_bars(LaggedStart(*[FadeIn(c) for c in cells], lag_ratio=0.002), FadeIn(cl), bars=1)
        self.play_bars(FadeIn(glass), FadeIn(slow), Rotate(glass, PI), bars=0.75)
        # 87–88 小批
        self.at_bar(87)
        r = np.random.default_rng(12)
        pick = sorted(r.choice(300, 8, replace=False))
        batch = VGroup(*[cells[i] for i in pick])
        bx = RoundedRectangle(width=2.6, height=1.0, corner_radius=0.1, color=C_GOLD).move_to([4.7, 1.6, 0])
        bl = T("一小批（例如 32 张）", size=22, color=C_GOLD).next_to(bx, UP, buff=0.12)
        targets = VGroup(*[c.copy().set_fill(C_GOLD, 0.9).set_stroke(C_GOLD) for c in batch]).arrange(RIGHT, buff=0.08).move_to(bx)
        self.play_bars(FadeOut(glass), FadeOut(slow), Create(bx), FadeIn(bl),
                       *[c.animate.set_fill(C_GOLD, 0.9) for c in batch], bars=0.5)
        self.play_bars(TransformFromCopy(batch, targets), bars=0.75)
        sgd = T("随机梯度下降（SGD）", size=28, color=C_GREEN, weight=BOLD).next_to(bx, DOWN, buff=0.4)
        self.play_bars(FadeIn(sgd), bars=0.5)
        self.at_bar(88.75)
        self.fade_rest(0.25)
        # 89–90 抖动的箭头与路径
        self.at_bar(89)
        panel, c2p = self.contour_panel(center=np.array([-0.6, 0.2, 0]))
        ratio = np.sqrt(B_V / A_U)
        pu, pv = -0.6, 0.45
        P0 = c2p(pu, pv)
        nd = -np.array([pu / ratio ** 2, pv, 0.0])
        nd = nd / np.linalg.norm(nd)
        full_arr = Arrow(P0, P0 + 1.3 * nd, buff=0, color=C_WHITE, stroke_width=6)
        rr = np.random.default_rng(4)
        minis = VGroup()
        for _ in range(6):
            a = rr.normal(0, 0.35)
            Rm = np.array([[np.cos(a), -np.sin(a), 0], [np.sin(a), np.cos(a), 0], [0, 0, 1]])
            minis.add(Arrow(P0, P0 + rr.uniform(0.9, 1.5) * (Rm @ nd), buff=0, color=C_GREEN, stroke_width=3,
                            stroke_opacity=0.8))
        lw = T("白：全部数据的方向", size=22, color=C_WHITE).move_to([4.6, 1.9, 0])
        lg = T("绿：各小批的方向（有点抖）", size=22, color=C_GREEN).move_to([4.6, 1.4, 0])
        self.play_bars(FadeIn(panel), GrowArrow(full_arr), FadeIn(lw), bars=0.5)
        self.play_bars(LaggedStart(*[GrowArrow(m) for m in minis], lag_ratio=0.15), FadeIn(lg), bars=0.75)
        # 抖着走到谷底
        u, v = -0.9, 0.85
        pts = [c2p(u, v)]
        for _ in range(16):
            gu, gv = grad_uv(u, v)
            gu *= 1 + rr.normal(0, 0.45)
            gv *= 1 + rr.normal(0, 0.45)
            u, v = u - ETA * gu + rr.normal(0, 0.02), v - ETA * gv + rr.normal(0, 0.03)
            pts.append(c2p(u, v))
        path = VMobject(stroke_color=C_GOLD, stroke_width=3).set_points_as_corners(pts)
        self.play_bars(FadeOut(minis), FadeOut(full_arr), Create(path), bars=0.75)
        # 91–92 “随机”是什么
        self.at_bar(91)
        card = VGroup(T("“随机” = 随机抽哪一批数据", size=28, color=C_GOLD),
                      T("方向 = 这一批数据上的负梯度（不是乱走）", size=26, color=C_GREEN)).arrange(DOWN, buff=0.25)
        card.move_to([4.0, -1.2, 0])
        if card.width > 5.6:
            card.scale_to_fit_width(5.6)
        self.play_bars(FadeIn(card, shift=UP * 0.2), bars=0.75)
        self.at_bar(92.75)
        self.fade_rest(0.25)
        # 93–94 小坑
        self.at_bar(93)
        self.tag("会被困住吗？")

        def gg(x):
            return 0.08 * x ** 2 - 0.45 * np.exp(-((x + 2.2) ** 2) / 0.2)

        cen = np.array([-0.5, -1.3, 0])

        def Pq(x):
            return cen + np.array([x * 1.0, gg(x) * 1.1, 0])

        road = VMobject(stroke_color=C_WHITE, stroke_width=4).set_points_smoothly([Pq(x) for x in np.linspace(-5.5, 5.5, 200)])
        ball = Dot(Pq(-2.2) + UP * 0.14, radius=0.13, color=C_GOLD)
        qq = T("局部最低？出不来？", size=28, color=C_GOLD).next_to(Pq(-2.2), UP, buff=1.0)
        self.play_bars(Create(road), bars=0.75)
        self.play_bars(FadeIn(ball, shift=DOWN * 0.4), FadeIn(qq), bars=0.75)
        self.at_bar(94.75)
        self.fade_rest(0.25)
        # 95–96 马鞍面
        self.at_bar(95)
        self.tag("马鞍面")
        th, el = 0.6, 0.45
        cen3 = np.array([-1.6, -0.5, 0])

        def zs(u, v):
            return 0.9 * (u * u - v * v) + 0.9

        surf = wire_surface(zs, th, el, cen3, s=2.2, zmax=1.8, lo=C_RED, hi=C_TEAL)
        su, sv = ValueTracker(0.95), ValueTracker(0.03)
        ball3 = always_redraw(lambda: Dot(proj(su.get_value(), sv.get_value(), zs(su.get_value(), sv.get_value()),
                                               th, el, cen3, s=2.2) + UP * 0.1, radius=0.11, color=C_GOLD))
        l1 = T("一个方向是谷，另一个方向是脊", size=24, color=C_WHITE).move_to([4.2, 1.6, 0])
        l2 = T("研究观察：高维中这种“鞍点”", size=22, color=C_GREY).move_to([4.2, 0.9, 0])
        l3 = T("比真正的小坑更常见（经验，不是定理）", size=22, color=C_GREY).move_to([4.2, 0.45, 0])
        self.play_bars(Create(surf), FadeIn(ball3), FadeIn(l1), bars=0.75)
        uu, vv = 0.95, 0.03
        traj = []
        for _ in range(10):
            uu, vv = uu * 0.62, vv * 1.6
            traj.append((uu, vv))
        self.play_bars(FadeIn(l2), FadeIn(l3), su.animate.set_value(traj[3][0]), sv.animate.set_value(traj[3][1]), bars=0.5)
        self.play_bars(su.animate.set_value(traj[9][0]), sv.animate.set_value(min(traj[9][1], 1.0)), bars=0.25)
        self.at_bar(96.75)
        self.fade_rest(0.25)
        # 97–98 惯性
        self.at_bar(97)
        self.tag("加点惯性")

        def hp(x):
            # 左边一段下坡 → 很长的近乎平地 → 右边再下坡
            return 0.3 * (1 - np.tanh(1.6 * (x + 3.8))) + 0.9 - 0.9 / (1 + np.exp(-2.5 * (x - 1.8))) - 0.01 * x

        def dhp(x, e=1e-4):
            return (hp(x + e) - hp(x - e)) / (2 * e)

        cen4 = np.array([0, -1.6, 0])

        def P4(x):
            return cen4 + np.array([x * 1.05, hp(x) * 1.4, 0])

        road2 = VMobject(stroke_color=C_WHITE, stroke_width=4).set_points_smoothly([P4(x) for x in np.linspace(-5.5, 5.5, 220)])
        xa, xb, vb = -5.0, -5.0, 0.0
        A, B = [xa], [xb]
        for _ in range(26):
            xa = xa - 2.2 * dhp(xa)
            vb = 0.86 * vb - 2.2 * dhp(xb)
            xb = xb + vb
            A.append(xa)
            B.append(min(xb, 5.3))
        ta, tb = ValueTracker(A[0]), ValueTracker(B[0])
        ba = always_redraw(lambda: Dot(P4(ta.get_value()) + UP * 0.14, radius=0.12, color=C_BLUE))
        bb = always_redraw(lambda: Dot(P4(tb.get_value()) + UP * 0.14, radius=0.12, color=C_GOLD))
        la = T("普通梯度下降：平地上几乎不动", size=22, color=C_BLUE).move_to([-2.6, 1.9, 0])
        lb = T("带惯性（动量 / Adam 一类）：冲过去", size=22, color=C_GOLD).move_to([2.8, 1.9, 0])
        self.play_bars(Create(road2), FadeIn(ba), FadeIn(bb), FadeIn(la), FadeIn(lb), bars=0.5)
        k = len(A)
        self.play_bars(ta.animate.set_value(A[k // 2]), tb.animate.set_value(B[k // 2]), bars=0.5, rate_func=linear)
        self.play_bars(ta.animate.set_value(A[-1]), tb.animate.set_value(B[-1]), bars=0.5, rate_func=linear)
        self.at_bar(98.75)
        self.fade_rest(0.25)
        # 99–100 训练 vs 测试
        self.at_bar(99)
        self.tag("别只看训练损失")
        cax = Axes(x_range=[0, 10], y_range=[0, 1.1], x_length=7.5, y_length=3.6, tips=False,
                   axis_config=dict(color=C_GREY, stroke_width=2)).move_to([-0.8, 0.2, 0])
        xl = T("训练步数", size=22, color=C_GREY).next_to(cax.x_axis, DOWN, buff=0.15).align_to(cax.x_axis, RIGHT)
        tr_c = cax.plot(lambda x: 0.08 + 0.9 * np.exp(-x / 2.2), x_range=[0, 10], color=C_RED, stroke_width=4)
        te_c = cax.plot(lambda x: 0.22 + 0.8 * np.exp(-x / 2.0) + 0.012 * max(x - 4.5, 0) ** 2, x_range=[0, 10],
                        color=C_TEAL, stroke_width=4)
        ltr = T("训练损失", size=24, color=C_RED).next_to(cax.c2p(10, 0.1), RIGHT, buff=0.15)
        lte = T("测试损失", size=24, color=C_TEAL).next_to(cax.c2p(10, 0.52), RIGHT, buff=0.15)
        self.play_bars(FadeIn(cax), FadeIn(xl), Create(tr_c), FadeIn(ltr), bars=0.5)
        self.play_bars(Create(te_c), FadeIn(lte), bars=0.75)
        self.at_bar(100.5)
        self.fade_rest(0.5)

    # ------------------------------------------------------------ 尾声 111–118
    def outro(self):
        self.at_bar(111)
        self.tag("回顾")
        items = [("损失", "= 高度", C_RED), ("旋钮", "= 位置", C_YELLOW), ("梯度", "= 上坡最陡的方向", C_RED)]
        cards = VGroup()
        for a, b, col in items:
            t = VGroup(T(a, size=34, color=col, weight=BOLD), T(b, size=30, color=C_WHITE)).arrange(RIGHT, buff=0.2)
            cards.add(VGroup(SurroundingRectangle(t, color=col, buff=0.2, corner_radius=0.12, stroke_width=2.5), t))
        cards.arrange(RIGHT, buff=0.5).move_to([0, 1.6, 0])
        if cards.width > 13:
            cards.scale_to_fit_width(13)
        self.play_bars(LaggedStart(*[FadeIn(c, shift=UP * 0.2) for c in cards], lag_ratio=0.3), bars=1.5)
        # 113–114
        self.at_bar(113)
        f = VGroup(T("新旋钮", size=34, color=C_YELLOW), T("= 旧旋钮", size=34, color=C_YELLOW),
                   T("− 学习率 × 梯度", size=34, color=C_GREEN), T("，重复", size=34, color=C_WHITE)).arrange(RIGHT, buff=0.15)
        f.move_to([0, 0.2, 0])
        self.play_bars(FadeIn(f, shift=UP * 0.2), bars=0.75)
        panel, c2p = self.contour_panel(center=np.array([0, -1.55, 0]), s=0.75)
        path = VMobject(stroke_color=C_GREEN, stroke_width=3).set_points_as_corners([c2p(u, v) for u, v in GD_PATH])
        self.play_bars(FadeIn(panel[0]), FadeIn(panel[1]), Create(path), bars=1)
        # 115–116 一万多个坡度
        self.at_bar(115)
        self.play_bars(FadeOut(VGroup(cards, f, panel[0], panel[1], path)), bars=0.25)
        r = np.random.default_rng(31)
        grid = VGroup()
        for i in range(30):
            k = Knob("·", ValueTracker(r.uniform(0, 1)), 0, 1, radius=0.2)
            k[-1].set_opacity(0)
            q = T("?", size=22, color=C_RED).next_to(k, UR, buff=-0.05)
            grid.add(VGroup(k, q))
        grid.arrange_in_grid(rows=3, cols=10, buff=0.4).move_to([0, 0.7, 0])
        ql = T("13,002 个坡度，从哪来？", size=34, color=C_WHITE).next_to(grid, DOWN, buff=0.45)
        self.play_bars(LaggedStart(*[FadeIn(g_) for g_ in grid], lag_ratio=0.03), bars=1)
        self.play_bars(FadeIn(ql), bars=0.5)
        # 117–118 下集：误差往回传
        self.at_bar(117)
        self.play_bars(FadeOut(grid), FadeOut(ql), bars=0.25)
        sizes = [4, 6, 6, 3]
        xs = [-5.2, -3.4, -1.6, 0.2]
        cols = VGroup()
        for x, n in zip(xs, sizes):
            cols.add(VGroup(*[Circle(radius=0.17, stroke_color=C_WHITE, stroke_width=2).move_to([x, 0.3 + ((n - 1) / 2 - i) * 0.55, 0])
                              for i in range(n)]))
        eds = VGroup(*[Line(a.get_center(), b.get_center(), stroke_width=1, color=C_GREY, stroke_opacity=0.5)
                       for c1, c2 in zip(cols[:-1], cols[1:]) for a in c1 for b in c2])
        nxt = VGroup(T("下集", size=30, color=C_GREY), T("反向传播", size=48, color=C_RED, weight=BOLD),
                     T("把错误一层层传回去", size=30, color=C_RED)).arrange(DOWN, buff=0.25).move_to([4.2, 0.4, 0])
        self.play_bars(FadeIn(cols), FadeIn(eds), FadeIn(nxt, shift=UP * 0.2), bars=0.5)
        back = [ShowPassingFlash(Line(b.get_center(), a.get_center(), color=C_RED, stroke_width=4), time_width=0.6)
                for c1, c2 in zip(cols[:-1], cols[1:]) for a in c1 for b in c2]
        self.play_bars(LaggedStart(*back[::-1], lag_ratio=0.004), bars=0.5)
        self.at_bar(118.25)
        self.play_bars(*[FadeOut(m) for m in self.visible()], bars=0.75)
