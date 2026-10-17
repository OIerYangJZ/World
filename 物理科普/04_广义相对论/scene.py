# -*- coding: utf-8 -*-
"""第 4 集 · 广义相对论：引力就是时空的弯曲"""
import sys
from style import *

# style.py 在导入时把分辨率写死为 1080p30，会覆盖命令行的 -ql。
# 预览时（-ql）恢复为 480p15，正式渲染（-qh）不受影响。
if "-ql" in sys.argv or "--quality=l" in sys.argv or ("-q" in sys.argv and "l" in sys.argv):
    config.pixel_width = 854
    config.pixel_height = 480
    config.frame_rate = 15

FW = 14.222222  # 默认画面宽度（manim 单位）
DIM = "#2b3a55"
PANEL = "#121826"


# ====================================================================== 小部件
def glow(point, r, color, layers=7, strength=0.5, core=True, core_color=None):
    g = VGroup()
    for i in range(layers, 0, -1):
        rr = r * (1 + 1.6 * i / layers)
        g.add(Circle(radius=rr, stroke_width=0, fill_color=color,
                     fill_opacity=strength * 0.22 * (1 - i / (layers + 1)) ** 1.5))
    if core:
        c = Circle(radius=r, stroke_width=0, fill_opacity=1)
        c.set_fill(color=[core_color or WHITE, color], opacity=1)
        c.set_sheen_direction(DR)
        g.add(c)
    return g.move_to(point)


def sun(point, r=0.8):
    return glow(point, r, C_GOLD, core_color="#fff3b0")


def planet_disk(point, r, c1="#3f8fd0", c2="#0b2742"):
    c = Circle(radius=r, stroke_color=C_BLUE, stroke_width=1.5, stroke_opacity=0.6)
    c.set_fill(color=[c1, c2], opacity=1)
    c.set_sheen_direction(DR)
    return c.move_to(point)


def apple(r=0.15):
    body = Circle(radius=r, stroke_width=0, fill_color=C_RED, fill_opacity=1)
    stem = Line(UP * r * 0.8, UP * r * 1.45, stroke_color="#8b5a2b", stroke_width=3)
    leaf = Ellipse(width=r * 0.9, height=r * 0.42, stroke_width=0,
                   fill_color=C_GREEN, fill_opacity=1).rotate(0.5).move_to(UP * r * 1.25 + RIGHT * r * 0.45)
    return VGroup(body, stem, leaf)


def person(s=1.0, color=C_WHITE):
    """火柴人，原点在两脚中点；右手位置 = (0.45s, 1.15s)"""
    kw = dict(stroke_color=color, stroke_width=4)
    head = Circle(radius=0.17 * s, **kw).move_to(UP * 1.62 * s)
    body = Line(UP * 1.45 * s, UP * 0.75 * s, **kw)
    l1 = Line(UP * 0.75 * s, LEFT * 0.22 * s, **kw)
    l2 = Line(UP * 0.75 * s, RIGHT * 0.22 * s, **kw)
    a1 = Line(UP * 1.3 * s, np.array([-0.38, 1.0, 0]) * s, **kw)
    a2 = Line(UP * 1.3 * s, np.array([0.45, 1.15, 0]) * s, **kw)
    return VGroup(head, body, l1, l2, a1, a2)


def make_clock(r=0.35, color=C_WHITE, hand_color=C_YELLOW):
    face = Circle(radius=r, stroke_color=color, stroke_width=3, fill_color="#151a26", fill_opacity=1)
    ticks = VGroup(*[Line(UP * (r - 0.07), UP * (r - 0.01), stroke_width=2, color=color)
                     .rotate(-i * PI / 6, about_point=ORIGIN) for i in range(12)])
    hand = Line(ORIGIN, UP * r * 0.8, stroke_width=4, color=hand_color)
    pin = Dot(ORIGIN, radius=0.03, color=hand_color)
    return VGroup(face, ticks, hand, pin)


def run_clock(clk, rate):
    face, hand = clk[0], clk[2]
    hand.add_updater(lambda m, dt: m.rotate(-rate * dt, about_point=face.get_center()))
    return clk


def cabin(w=2.8, h=3.4, color=C_BLUE):
    return Rectangle(width=w, height=h, stroke_color=color, stroke_width=4,
                     fill_color=PANEL, fill_opacity=1)


def scale_box():
    return Rectangle(width=0.9, height=0.16, stroke_color=C_GREY, stroke_width=2,
                     fill_color="#2a2f3d", fill_opacity=1)


def flame(top_center, w=1.1, h=0.75):
    outer = Polygon(top_center + LEFT * w / 2, top_center + RIGHT * w / 2, top_center + DOWN * h,
                    stroke_width=0, fill_color=C_PINK, fill_opacity=0.9)
    inner = Polygon(top_center + LEFT * w / 4, top_center + RIGHT * w / 4, top_center + DOWN * h * 0.6,
                    stroke_width=0, fill_color=C_YELLOW, fill_opacity=0.95)
    g = VGroup(outer, inner)
    st = {"t": 0.0}

    def flick(m, dt):
        st["t"] += dt
        k = 1 + 0.08 * np.sin(st["t"] * 23) + 0.05 * np.sin(st["t"] * 37)
        m.stretch_to_fit_height(h * k, about_edge=UP)
    g.add_updater(flick)
    return g


def starfield(n=60, seed=3, xr=(-7, 7), yr=(-2.5, 3.9), op=0.6):
    rng = np.random.default_rng(seed)
    return VGroup(*[Dot([rng.uniform(*xr), rng.uniform(*yr), 0], radius=rng.uniform(0.012, 0.03),
                        color=WHITE, fill_opacity=rng.uniform(0.25, op)) for _ in range(n)])


def label_bg(m, op=0.7):
    return VGroup(BackgroundRectangle(m, color=BG, fill_opacity=op, buff=0.08), m)


# ---------------------------------------------------------------- 球面（正交投影）
EL = 24 * DEGREES


def sph(lat, lon, R, c):
    X = np.cos(lat) * np.sin(lon)
    Y = np.sin(lat)
    Z = np.cos(lat) * np.cos(lon)
    Yp = Y * np.cos(EL) - Z * np.sin(EL)
    Zp = Y * np.sin(EL) + Z * np.cos(EL)
    return np.array([c[0] + R * X, c[1] + R * Yp, 0.0]), Zp


def sphere_curve(fn, n, R, c, front_kw, back_kw):
    """fn(s)->(lat,lon), s∈[0,1]; 前半球实线、后半球淡线"""
    out = VGroup()
    seg, vis = [], None
    for s in np.linspace(0, 1, n):
        p, z = sph(*fn(s), R, c)
        v = z >= 0
        if vis is None or v == vis:
            seg.append(p)
        else:
            if len(seg) > 1:
                out.add(VMobject(**(front_kw if vis else back_kw)).set_points_as_corners(seg))
            seg = [seg[-1], p]
        vis = v
    if len(seg) > 1:
        out.add(VMobject(**(front_kw if vis else back_kw)).set_points_as_corners(seg))
    return out


# ---------------------------------------------------------------- 透视网格（橡皮膜）
def sheet_proj(x, y, z, cx=0.0, cy=0.6, el=24 * DEGREES, S=1.1, persp=0.035):
    f = 1 / (1 + persp * y)
    return np.array([cx + S * x * f, cy + S * (y * np.sin(el) + z * np.cos(el)) * f, 0.0])


def well(x, y, k, a=1.4):
    return -k / (1 + (x * x + y * y) / (a * a))


def sheet_grid(k, n=21, L=5.0, samples=56, **pk):
    g = VGroup()
    vals = np.linspace(-L, L, n)
    ts = np.linspace(-L, L, samples)
    for v in vals:
        for horiz in (True, False):
            if horiz:
                pts = [sheet_proj(t, v, well(t, v, k), **pk) for t in ts]
            else:
                pts = [sheet_proj(v, t, well(v, t, k), **pk) for t in ts]
            closeness = np.exp(-(v * v) / 5.0)
            col = interpolate_color(ManimColor(DIM), ManimColor(C_BLUE), 0.25 + 0.75 * closeness)
            ln = VMobject(stroke_color=col, stroke_width=1.6 + 1.2 * closeness,
                          stroke_opacity=0.55 + 0.4 * closeness)
            ln.set_points_smoothly(pts)
            g.add(ln)
    return g


# ====================================================================== 主场景
class Video(Explainer):

    # ---------- 工具：字幕跟随相机（style.py 的字幕固定在世界坐标，相机移动时会跑出画面）
    def _make_sub(self, text):
        g = super()._make_sub(text)
        frame = self.camera.frame
        g._base = g.get_center().copy()
        g._s = 1.0

        def upd(m):
            s = frame.width / FW
            if abs(s - m._s) > 1e-5:
                m.scale(s / m._s)
                m._s = s
            m.move_to(frame.get_center() + s * m._base)
        g.add_updater(upd)
        upd(g)
        return g

    def clean(self, run_time=0.35):
        for m in self.mobjects:
            if m is not self._sub:
                m.clear_updaters()
        self.fade_all(run_time=run_time)

    def construct(self):
        self.title_card("广义相对论", "引力就是时空的弯曲")
        self.ch1()
        self.ch2()
        self.ch3()
        self.ch4()
        self.ch5()
        self.ch6()
        self.ch7()
        self.ch8()
        self.end_card([
            "等效原理：引力与加速度局部等价",
            "引力即时空弯曲，自由物体走测地线",
            "弱引力下，主角是时间的弯曲",
            "物质弯曲时空，时空引导物质",
            "水星、光偏折、GPS、引力波皆吻合",
        ])

    # ================================================================== 第一章
    def ch1(self):
        self.chapter("第一章", "牛顿的难题")
        formula = eq(r"F = G\,\frac{Mm}{r^{2}}", size=58).move_to([0, 3.15, 0])
        S0 = np.array([-3.0, 0.3, 0])
        sn = sun(S0, 0.6)
        orbit = Ellipse(width=7.2, height=4.2, stroke_color=C_GREY, stroke_width=1.5,
                        stroke_opacity=0.5).move_to(S0)
        th = ValueTracker(-2.2)

        def epos():
            return S0 + np.array([3.6 * np.cos(th.get_value()), 2.1 * np.sin(th.get_value()), 0])
        earth = planet_disk(epos(), 0.22)
        earth.add_updater(lambda m: m.move_to(epos()))

        def farrow():
            e = earth.get_center()
            d = sn.get_center() - e
            d = d / np.linalg.norm(d)
            return Arrow(e + d * 0.25, e + d * 1.25, buff=0, color=C_RED, stroke_width=5,
                         max_tip_length_to_length_ratio=0.3)
        fa = always_redraw(farrow)
        # 苹果树
        branch = Line([4.7, 2.75, 0], [6.6, 2.55, 0], stroke_color="#8b5a2b", stroke_width=6)
        ground = Line([4.4, -1.65, 0], [6.9, -1.65, 0], stroke_color=C_GREEN, stroke_width=4)
        ap = apple(0.17).move_to([5.7, 2.35, 0])
        lab_a = T("苹果落地", 24, C_GREY).move_to([5.65, -2.05, 0])
        lab_p = T("行星运转", 24, C_GREY).move_to([-3.0, -2.15, 0])

        self.say("牛顿的引力定律，统一了苹果落地与行星运转。",
                 Succession(AnimationGroup(Write(formula), FadeIn(sn), Create(orbit), FadeIn(earth), FadeIn(fa),
                                           FadeIn(branch), FadeIn(ground), FadeIn(ap), FadeIn(lab_a),
                                           FadeIn(lab_p), run_time=1.2),
                            AnimationGroup(th.animate.set_value(0.25), ap.animate.move_to([5.7, -1.48, 0]),
                                           run_time=2.2, rate_func=rush_into)))
        # 太阳一动，力立刻改变；而光要 8 分 19 秒
        note = label_bg(T("牛顿：地球受力“瞬间”改变", 26, C_YELLOW)).move_to([2.6, 1.85, 0])
        new_sun = S0 + LEFT * 1.1 + UP * 0.7
        rr = ValueTracker(0.0)
        dist = np.linalg.norm(epos() - new_sun)
        shell = always_redraw(lambda: Circle(radius=max(rr.get_value(), 0.01), stroke_color=C_YELLOW,
                                             stroke_width=3, stroke_opacity=0.75 if rr.get_value() > 0.02 else 0)
                              .move_to(new_sun))

        def timer_txt():
            sec = int(round(499 * rr.get_value() / dist))
            return T(f"光从太阳到地球：{sec // 60} 分 {sec % 60:02d} 秒", 28, C_TEAL).move_to(
                [2.6, -1.25, 0]).set_opacity(1 if rr.get_value() > 0.01 else 0)
        timer = always_redraw(timer_txt)
        self.add(shell, timer)
        self.say("但它是瞬时的：太阳一动，地球受力立刻改变，可没有信号能快过光。",
                 Succession(Wait(0.3), sn.animate(run_time=0.5).move_to(new_sun),
                            Flash(earth, color=C_YELLOW, line_length=0.25, run_time=0.5),
                            FadeIn(note, shift=UP * 0.2, run_time=0.5),
                            rr.animate(run_time=3.6, rate_func=linear).set_value(dist),
                            Flash(earth, color=C_TEAL, line_length=0.3, run_time=0.5)))
        shell.clear_updaters()
        timer.clear_updaters()
        self.clean()
        # 引力 = 力？
        a = T("引力", 90, C_WHITE, weight=BOLD)
        b = T("是一种", 60, C_GREY)
        c = T("力", 90, C_WHITE, weight=BOLD)
        row = VGroup(a, b, c).arrange(RIGHT, buff=0.35).move_to([0, 1.2, 0])
        cross = VGroup(Line(c.get_corner(UL) + UL * 0.15, c.get_corner(DR) + DR * 0.15),
                       Line(c.get_corner(DL) + DL * 0.15, c.get_corner(UR) + UR * 0.15)).set_stroke(C_RED, 8)
        tl = NumberLine(x_range=[1905, 1917, 1], length=8, include_numbers=False, color=C_GREY,
                        stroke_width=2).move_to([0, -1.0, 0])
        y1 = T("1907 等效原理", 24, C_YELLOW).next_to(tl.n2p(1907), DOWN, buff=0.3)
        y2 = T("1915 场方程", 24, C_YELLOW).next_to(tl.n2p(1915), DOWN, buff=0.3)
        d1 = Dot(tl.n2p(1907), color=C_YELLOW)
        d2 = Dot(tl.n2p(1915), color=C_YELLOW)
        span = Line(tl.n2p(1907), tl.n2p(1915), stroke_color=C_YELLOW, stroke_width=6)
        self.say("爱因斯坦用了八年找到出路：引力根本不是力。",
                 Succession(FadeIn(row, shift=UP * 0.2),
                            AnimationGroup(Create(tl), FadeIn(d1), FadeIn(y1)),
                            AnimationGroup(Create(span), FadeIn(d2), FadeIn(y2)),
                            Create(cross)), run_time=4.0)
        self.clean()

    # ================================================================== 第二章
    def ch2(self):
        self.chapter("第二章", "最快乐的想法")
        L = np.array([-3.6, 0.5, 0])
        R = np.array([3.6, 0.5, 0])
        floor = -1.2

        def room(c, cable=False):
            box = cabin().move_to(c)
            sc = scale_box().move_to([c[0], floor + 0.08 + 0.01, 0])
            p = person(1.0).move_to([c[0] - 0.05, 0, 0], aligned_edge=DOWN).shift(UP * (floor + 0.17))
            hand = p[5].get_end()
            ap = apple(0.13).move_to(hand + RIGHT * 0.12 + DOWN * 0.05)
            rd = T("70 kg", 24, C_TEAL).move_to([c[0] - 0.92, floor + 0.22, 0])
            g = VGroup(box, sc, p, ap, rd)
            if cable:
                g.add(Line(box.get_top(), [c[0], 4.2, 0], stroke_color=C_GREY, stroke_width=3))
            return g

        left = room(L, cable=True)
        quote = T("“一生最快乐的想法”", 34, C_YELLOW).move_to([3.0, 2.4, 0])
        qy = T("—— 爱因斯坦，1907", 26, C_GREY).next_to(quote, DOWN, buff=0.25).align_to(quote, RIGHT)
        idea = T("自由下落的人\n感觉不到自己的重量", 30, C_WHITE, line_spacing=1.0).move_to([3.0, 0.2, 0])
        self.say("1907年，他有了“一生最快乐的想法”：自由下落的人感觉不到重量。",
                 Succession(FadeIn(left), FadeIn(quote, shift=DOWN * 0.2), FadeIn(qy), FadeIn(idea)),
                 run_time=3.5)
        # 缆绳断开 → 自由下落；右侧 = 深空漂浮
        fall = ValueTracker(0.0)

        def marks():
            g = VGroup()
            off = fall.get_value()
            for side in (-1, 1):
                for i in range(9):
                    y = -1.5 + ((i * 0.62 + off) % 5.6)
                    if y > 3.9:
                        continue
                    x0 = L[0] + side * 1.55
                    g.add(Line([x0, y, 0], [x0 + side * 0.35, y, 0], stroke_color=C_GREY,
                               stroke_width=2, stroke_opacity=0.6))
            return g
        shaft = always_redraw(marks)
        self.add(shaft)
        cable = left[5]
        sp = cable.get_start() + UP * 0.6
        right = room(R)
        right[2].shift(UP * 0.12).rotate(0.06)
        right[3].shift(UP * 0.16 + RIGHT * 0.05)
        right[4].become(T("0 kg", 24, C_RED).move_to(right[4]))
        stars = starfield(28, seed=5, xr=(1.0, 6.9), yr=(-1.7, 3.6))
        rd_l, rd_r = left[4], right[4]
        z_l = T("0 kg", 24, C_RED).move_to(rd_l)
        z_r = T("0 kg", 24, C_RED).move_to(rd_r)
        lab_l = T("自由下落的电梯", 28, C_WHITE).move_to([L[0], -1.95, 0])
        lab_r = T("远离星体的深空", 28, C_WHITE).move_to([R[0], -1.95, 0])
        eqs = T("=", 80, C_YELLOW).move_to([0, 0.5, 0])
        g_arrow = Arrow([L[0] - 2.4, 1.6, 0], [L[0] - 2.4, 0.2, 0], buff=0, color=C_RED, stroke_width=5)
        g_lab = eq(r"g", 36, C_RED).next_to(g_arrow, LEFT, buff=0.1)
        self.say("下落的电梯里体重计归零，苹果飘在手边，就像漂浮在太空中。",
                 Succession(
                     FadeOut(VGroup(quote, qy, idea), run_time=0.4),
                     AnimationGroup(Flash(sp, color=C_YELLOW, line_length=0.3), FadeOut(cable, shift=UP * 0.8),
                                    run_time=0.6),
                     AnimationGroup(fall.animate(rate_func=rush_into).set_value(14.0),
                                    Transform(rd_l, z_l), left[2].animate.shift(UP * 0.12),
                                    left[3].animate.shift(UP * 0.12 + RIGHT * 0.05),
                                    FadeIn(g_arrow), FadeIn(g_lab), FadeIn(lab_l), run_time=2.8),
                     AnimationGroup(FadeIn(stars), FadeIn(right), FadeIn(lab_r), run_time=1.0),
                     AnimationGroup(FadeIn(eqs), fall.animate(rate_func=linear).set_value(24.0), run_time=1.6)))
        shaft.clear_updaters()
        self.clean(0.6)

        # 地面静止 vs 加速火箭
        left = room(L)
        right = room(R)
        ground = Rectangle(width=4.2, height=0.28, stroke_width=0, fill_color="#3b5d3a",
                           fill_opacity=1).move_to([L[0], floor - 0.14, 0])
        g_arrow = Arrow([L[0] - 2.1, 1.6, 0], [L[0] - 2.1, 0.2, 0], buff=0, color=C_RED, stroke_width=5)
        g_lab = eq(r"g", 36, C_RED).next_to(g_arrow, LEFT, buff=0.1)
        nose = Polygon([R[0] - 1.4, 2.2, 0], [R[0] + 1.4, 2.2, 0], [R[0], 3.05, 0], stroke_color=C_BLUE,
                       stroke_width=4, fill_color=PANEL, fill_opacity=1)
        fl = flame(np.array([R[0], floor, 0]), 1.2, 0.65)
        a_arrow = Arrow([R[0] + 2.1, 0.2, 0], [R[0] + 2.1, 1.6, 0], buff=0, color=C_GOLD, stroke_width=5)
        a_lab = eq(r"a = g", 36, C_GOLD).next_to(a_arrow, RIGHT, buff=0.1)
        lab_l = T("静止在地面上", 28).move_to([L[0], -2.15, 0])
        lab_r = T("太空中以 g 加速的火箭", 28).move_to([R[0], -2.15, 0])
        stars = starfield(28, seed=8, xr=(0.8, 6.9), yr=(-2.4, 3.6))
        self.add(stars)
        aps = [left[3], right[3]]
        self.say("而在加速的火箭里，苹果“落”向地板，与在地面上无法区分。",
                 Succession(
                     AnimationGroup(FadeIn(stars), FadeIn(ground), FadeIn(left), FadeIn(right), FadeIn(nose),
                                    FadeIn(fl), FadeIn(g_arrow), FadeIn(g_lab), FadeIn(a_arrow), FadeIn(a_lab),
                                    FadeIn(lab_l), FadeIn(lab_r), run_time=1.2),
                     Wait(0.6),
                     AnimationGroup(*[a.animate.move_to([a.get_center()[0], floor + 0.29, 0]) for a in aps],
                                    run_time=1.1, rate_func=rush_into),
                     Wait(0.4)))
        title = T("等效原理", 44, C_YELLOW, weight=BOLD).move_to([0, 3.45, 0])
        eqs = T("=", 90, C_YELLOW).move_to([0, 0.5, 0])
        loc = T("（在足够小的区域内）", 24, C_GREY).move_to([0, -0.35, 0])
        self.say("这就是等效原理：在足够小的区域内，引力与加速无法区分。",
                 Succession(FadeIn(title, shift=DOWN * 0.2), GrowFromCenter(eqs), FadeIn(loc)),
                 run_time=2.5)
        self.clean()

        # 万物同样下落
        gl = Line([-6.4, -1.75, 0], [-1.6, -1.75, 0], stroke_color=C_GREY, stroke_width=3)
        hammer = VGroup(Rectangle(width=0.7, height=0.28, stroke_width=0, fill_color="#9aa4b5", fill_opacity=1),
                        Rectangle(width=0.1, height=0.8, stroke_width=0, fill_color="#8b5a2b",
                                  fill_opacity=1).shift(DOWN * 0.52)).move_to([-5.0, 2.9, 0])
        feather = VGroup(Ellipse(width=0.32, height=1.15, stroke_width=0, fill_color=C_WHITE, fill_opacity=0.9),
                         Line(DOWN * 0.7, UP * 0.5, stroke_color=C_GREY, stroke_width=2)).rotate(0.25).move_to([-3.0, 2.85, 0])
        vac = T("真空中", 26, C_GREY).move_to([-4.0, 3.55, 0])
        rows_data = [("伽利略（约 1600 年）", None, "同时落地"),
                     ("厄特沃什扭秤（1908–1922）", r"\sim 10^{-9}", None),
                     ("MICROSCOPE 卫星（2022）", r"\sim 10^{-15}", None)]
        rows = VGroup()
        for name, tex, txt in rows_data:
            n = T(name, 26, C_WHITE)
            v = eq(tex, 40, C_TEAL) if tex else T(txt, 26, C_TEAL)
            rows.add(VGroup(n, v))
        head = T("下落加速度的相对差异", 28, C_YELLOW)
        for r in rows:
            r[0].move_to([0, 0, 0], aligned_edge=LEFT)
        tbl = VGroup(head, *rows)
        head.move_to([2.6, 2.4, 0])
        for i, r in enumerate(rows):
            r[0].move_to([-0.6, 1.4 - i * 1.05, 0], aligned_edge=LEFT)
            r[1].move_to([5.6, 1.4 - i * 1.05, 0])
        bars = VGroup(*[Line([-0.6, 1.4 - i * 1.05 - 0.38, 0], [6.6, 1.4 - i * 1.05 - 0.38, 0],
                             stroke_color=DIM, stroke_width=1.5) for i in range(3)])
        self.say("万物下落完全一样，与质量、成分无关，已验证到千万亿分之一。",
                 Succession(AnimationGroup(FadeIn(gl), FadeIn(hammer), FadeIn(feather), FadeIn(vac), run_time=0.6),
                            AnimationGroup(hammer.animate.shift(DOWN * 4.0), feather.animate.shift(DOWN * 4.0),
                                           run_time=1.3, rate_func=rush_into),
                            FadeIn(head),
                            LaggedStart(*[FadeIn(VGroup(r, b), shift=RIGHT * 0.2) for r, b in zip(rows, bars)],
                                        lag_ratio=0.5, run_time=2.4)))
        self.clean()

    # ================================================================== 第三章
    def ch3(self):
        self.chapter("第三章", "光与时间")
        C = np.array([0, 0.6, 0])
        stars = starfield(70, seed=11, op=0.7)
        spd = ValueTracker(0.0)

        def drift(m, dt):
            v = spd.get_value()
            for d in m:
                d.shift(DOWN * v * dt)
                if d.get_y() < -2.55:
                    d.shift(UP * 6.45)
        stars.add_updater(drift)
        box = cabin(6.0, 3.6).move_to(C)
        fl = flame(np.array([0, C[1] - 1.8, 0]), 2.0, 0.6)
        a_arrow = Arrow([3.6, -0.4, 0], [3.6, 1.6, 0], buff=0, color=C_GOLD, stroke_width=6)
        a_lab = eq(r"a", 40, C_GOLD).next_to(a_arrow, RIGHT, buff=0.12)
        self.add(stars)
        u = ValueTracker(0.0)
        x0, y0, drop = -3.0, 2.05, 2.1

        def lp(uu):
            return np.array([x0 + 6 * uu, y0 - drop * uu * uu, 0])
        emitter = Rectangle(width=0.14, height=0.36, stroke_width=0, fill_color=C_YELLOW,
                            fill_opacity=1).move_to([x0 + 0.07, y0, 0])
        straight = DashedLine([x0, y0, 0], [3.0, y0, 0], stroke_color=C_GREY, stroke_width=2, dash_length=0.12)
        st_lab = T("若火箭不加速", 22, C_GREY).move_to([1.6, y0 + 0.22, 0])
        photon = always_redraw(lambda: glow(lp(u.get_value()), 0.07, C_YELLOW, layers=4))
        beam = always_redraw(lambda: ParametricFunction(lp, t_range=[0, max(u.get_value(), 1e-3)],
                                                        stroke_color=C_YELLOW, stroke_width=5))
        self.say("推论一：光横穿加速的火箭时，舱底在上冲，光路看起来向下弯。",
                 Succession(AnimationGroup(FadeIn(box), FadeIn(fl), GrowArrow(a_arrow), FadeIn(a_lab),
                                           spd.animate.set_value(3.0), FadeIn(emitter), run_time=1.2),
                            AnimationGroup(Create(straight), FadeIn(st_lab), run_time=0.8),
                            AnimationGroup(FadeIn(photon), FadeIn(beam), run_time=0.1),
                            u.animate(rate_func=linear, run_time=3.0).set_value(1.0)))
        bend = T("光路下弯（效果夸大）", 24, C_YELLOW).move_to([-0.6, 0.55, 0])
        half = label_bg(T("这只是总偏折的一半；另一半来自空间的弯曲", 28, C_GOLD)).move_to([0, 3.35, 0])
        beam.clear_updaters()
        photon.clear_updaters()
        self.say("所以引力也让光弯曲。但这只是一半，另一半来自空间的弯曲。",
                 Succession(FadeIn(bend), Wait(0.4), FadeIn(half, shift=DOWN * 0.2)), run_time=2.2)
        # 推论二：红移与钟
        ph = ValueTracker(0.0)
        yb, yt = C[1] - 1.55, C[1] + 1.55
        lam0, kk = 0.32, 1.6

        def wave():
            def f(s):
                y = yb + s * (yt - yb)
                q = (y - yb) / (yt - yb)
                phase = TAU * np.log(1 + kk * q) * (yt - yb) / (kk * lam0) - ph.get_value()
                return np.array([0.25 + 0.22 * np.sin(phase), y, 0])
            w = ParametricFunction(f, t_range=[0, 1, 0.004], stroke_width=4)
            w.set_stroke(color=[C_BLUE, C_PURPLE, C_RED], opacity=wo.get_value())
            return w
        wo = ValueTracker(0.0)
        wv = always_redraw(wave)
        src = Dot([0.25, yb - 0.05, 0], color=C_BLUE, radius=0.08)
        det = Rectangle(width=0.7, height=0.1, stroke_width=0, fill_color=C_GREY,
                        fill_opacity=1).move_to([0.25, yt + 0.06, 0])
        l_s = T("发出：波长短", 22, C_BLUE).move_to([1.75, yb + 0.2, 0])
        l_t = T("收到：波长变长", 22, C_RED).move_to([1.85, yt - 0.25, 0])
        self.add(wv)
        ck_b = make_clock(0.36).move_to([-2.4, yb + 0.5, 0])
        ck_t = make_clock(0.36).move_to([-2.4, yt - 0.5, 0])
        lb = T("尾部钟：慢", 22, C_WHITE).next_to(ck_b, RIGHT, buff=0.2)
        lt = T("头部钟：快", 22, C_WHITE).next_to(ck_t, RIGHT, buff=0.2)
        run_clock(ck_b, 1.4)
        run_clock(ck_t, 2.4)
        self.say("推论二：尾部发往头部的光会变红，头部的人发现尾部的钟走得慢。",
                 Succession(FadeOut(VGroup(beam, photon, bend, half, straight, st_lab, emitter), run_time=0.5),
                            AnimationGroup(FadeIn(src), FadeIn(det), FadeIn(l_s), FadeIn(l_t), wo.animate.set_value(1),
                                           ph.animate(rate_func=linear).set_value(2), run_time=0.6),
                            ph.animate(rate_func=linear, run_time=2.4).set_value(8),
                            AnimationGroup(FadeIn(ck_b), FadeIn(ck_t), FadeIn(lb), FadeIn(lt),
                                           ph.animate(rate_func=linear).set_value(9), run_time=0.5),
                            ph.animate(rate_func=linear, run_time=3.0).set_value(16)))
        self.clean()

        # 引力场中：塔上的钟
        gx = np.linspace(-7.2, 7.2, 60)
        gy = -15.9 + np.sqrt(14 ** 2 - gx ** 2)
        earth = Polygon(*[np.array([x, y, 0]) for x, y in zip(gx, gy)], [7.2, -2.5, 0], [-7.2, -2.5, 0],
                        stroke_width=0, fill_color="#16301f", fill_opacity=1)
        earth.add(VMobject(stroke_color=C_GREEN, stroke_width=3).set_points_smoothly(
            [np.array([x, y, 0]) for x, y in zip(gx, gy)]))
        tower = Rectangle(width=0.5, height=4.6, stroke_color=C_GREY, stroke_width=2, fill_color="#1c2230",
                          fill_opacity=1).move_to([-3.2, 0.4, 0])
        hs = [-1.25, 0.55, 2.35]
        rates = [1.0, 1.6, 2.2]
        cks = VGroup()
        labs = VGroup()
        names = ["低处：最慢", "中间", "高处：最快"]
        for h, r, nm in zip(hs, rates, names):
            c = make_clock(0.38).move_to([-3.2, h, 0])
            run_clock(c, r)
            cks.add(c)
            labs.add(T(nm, 24, C_WHITE).next_to(c, RIGHT, buff=0.25))
        g_arrow = Arrow([-5.4, 2.0, 0], [-5.4, 0.3, 0], buff=0, color=C_RED, stroke_width=5)
        g_lab = T("引力", 24, C_RED).next_to(g_arrow, LEFT, buff=0.1)
        exag = T("（钟速差异被极度夸大）", 22, C_GREY).move_to([-3.2, 3.25, 0])
        self.say("放到引力场里：越低处的钟走得越慢，这就是引力时间膨胀。",
                 Succession(AnimationGroup(FadeIn(earth), FadeIn(tower), FadeIn(g_arrow), FadeIn(g_lab), run_time=0.8),
                            AnimationGroup(LaggedStart(*[FadeIn(c) for c in cks], lag_ratio=0.3),
                                           LaggedStart(*[FadeIn(l) for l in labs], lag_ratio=0.3),
                                           FadeIn(exag), run_time=1.5)))
        f1 = eq(r"\frac{\Delta f}{f}\approx\frac{g\,\Delta h}{c^{2}}", 50).move_to([3.4, 2.2, 0])
        f2 = VGroup(eq(r"\approx 1.1\times10^{-16}", 44, C_TEAL), T("每米（地面附近）", 26, C_TEAL)).arrange(RIGHT, buff=0.15)
        f2.move_to([3.4, 0.9, 0])
        oc = T("光钟（2010）：抬高 33 厘米即可测出", 26, C_GOLD).move_to([3.4, -0.3, 0])
        self.say("每升高1米，钟快约一亿亿分之一；光钟已能测出33厘米的差别。",
                 Succession(Write(f1), FadeIn(f2, shift=UP * 0.2), FadeIn(oc, shift=UP * 0.2)), run_time=3.5)
        self.clean()

    # ================================================================== 第四章
    def ch4(self):
        self.chapter("第四章", "引力不是力")
        big = T("引力不是力，而是时空的弯曲", 46, C_WHITE, weight=BOLD).move_to([0, 1.0, 0])
        sub = T("自由物体沿“测地线”运动：时空中最直的路径", 30, C_TEAL).move_to([0, -0.2, 0])
        self.say("引力不是力，而是时空弯曲；自由物体沿“最直”的测地线运动。",
                 Succession(FadeIn(big, shift=UP * 0.2), Wait(1.2), FadeIn(sub, shift=UP * 0.2)), run_time=3.0)

        # 地球仪
        G = np.array([-2.6, 0.45, 0])
        R = 2.75
        disk = Circle(radius=R, stroke_color=C_BLUE, stroke_width=2.5).move_to(G)
        disk.set_fill(color=["#2f6ea3", "#0c1d33"], opacity=1)
        disk.set_sheen_direction(DR)
        rim = Circle(radius=R * 1.02, stroke_color=C_BLUE, stroke_width=8, stroke_opacity=0.15).move_to(G)
        fk = dict(stroke_color=C_WHITE, stroke_width=1.4, stroke_opacity=0.45)
        bk = dict(stroke_color=C_WHITE, stroke_width=1.0, stroke_opacity=0.08)
        lines = VGroup()
        for lon in np.arange(0, 360, 20) * DEGREES:
            lines.add(sphere_curve(lambda s, lo=lon: (-PI / 2 + PI * s, lo), 60, R, G, fk, bk))
        for lat in np.arange(-60, 90, 30) * DEGREES:
            kw = dict(stroke_color=C_YELLOW, stroke_width=2.5, stroke_opacity=0.8) if lat == 0 else fk
            lines.add(sphere_curve(lambda s, la=lat: (la, TAU * s), 100, R, G, kw, bk))
        pole, _ = sph(PI / 2, 0, R, G)
        pole_dot = Dot(pole, color=C_WHITE, radius=0.06)
        pole_lab = T("北极", 24).next_to(pole, UP, buff=0.12)
        globe = VGroup(rim, disk, lines, pole_dot, pole_lab)
        lat_t = ValueTracker(0.0)
        wop = ValueTracker(0.0)
        lons = [-38 * DEGREES, 38 * DEGREES]
        cols = [C_RED, C_TEAL]
        walkers, paths = VGroup(), VGroup()
        for lo, col in zip(lons, cols):
            walkers.add(always_redraw(lambda lo=lo, col=col:
                                      Dot(sph(lat_t.get_value(), lo, R, G)[0], radius=0.11, color=col).set_opacity(wop.get_value())))
            paths.add(always_redraw(lambda lo=lo, col=col: VMobject(stroke_color=col, stroke_width=5)
                                    .set_points_as_corners([sph(a, lo, R, G)[0] for a in
                                                            np.linspace(0, max(lat_t.get_value(), 1e-3), 30)])))
        starts = VGroup()
        for lo, col in zip(lons, cols):
            p0, _ = sph(0, lo, R, G)
            p1, _ = sph(0.33, lo, R, G)
            starts.add(Arrow(p0, p0 + (p1 - p0) * 1.0, buff=0, color=col, stroke_width=5,
                             max_tip_length_to_length_ratio=0.3))
        par = T("起点：方向平行", 24, C_GREY).move_to(G + np.array([0, -1.75, 0]))
        paths.set_z_index(5)
        walkers.set_z_index(6)
        starts.set_z_index(6)
        self.add(paths, walkers)
        frame = self.camera.frame
        txt1 = T("没有任何力拉扯", 32, C_WHITE).move_to([3.7, 1.4, 0])
        txt2 = T("只因球面本身是弯的", 32, C_YELLOW).move_to([3.7, 0.6, 0])
        txt3 = T("球面上的“直线”= 大圆 = 测地线", 24, C_GREY).move_to([3.7, -0.3, 0])
        self.say("就像两人从赤道笔直北行，无需任何力，却在北极相遇：因为球面是弯的。",
                 Succession(AnimationGroup(FadeOut(big), FadeOut(sub), FadeIn(globe), run_time=0.8),
                            AnimationGroup(GrowArrow(starts[0]), GrowArrow(starts[1]), FadeIn(par), wop.animate.set_value(1),
                                           run_time=0.7),
                            AnimationGroup(lat_t.animate(rate_func=linear, run_time=4.4).set_value(PI / 2 - 0.02),
                                           FadeOut(starts), Succession(Wait(0.8), FadeIn(txt1), Wait(0.6),
                                                                       FadeIn(txt2), FadeIn(txt3)), run_time=3.4),
                            frame.animate(run_time=1.0).scale(0.55).move_to(pole + DOWN * 0.6),
                            Flash(pole, color=C_YELLOW, line_length=0.18, run_time=0.5),
                            frame.animate(run_time=1.0).set_width(FW).move_to(ORIGIN)))
        self.clean()

        # 潮汐：两个苹果奔向地心
        E = np.array([-2.0, -1.3, 0])
        er = 1.05
        earth = planet_disk(E, er, "#4a9a6a", "#0f2a1c")
        ctr = Dot(E, radius=0.05, color=C_WHITE)
        a0 = [np.array([-3.5, 3.1, 0]), np.array([-0.5, 3.1, 0])]
        k = ValueTracker(0.0)

        def apos(i):
            d = E - a0[i]
            return a0[i] + d * k.get_value()
        aps = VGroup(*[apple(0.17) for _ in range(2)])
        for i, a in enumerate(aps):
            a.add_updater(lambda m, i=i: m.move_to(apos(i)))
        guides = VGroup(*[DashedLine(a0[i], E, stroke_color=C_GREY, stroke_width=1.5, dash_length=0.1)
                          for i in range(2)])
        sep = always_redraw(lambda: DoubleArrow(apos(0) + DOWN * 0.35, apos(1) + DOWN * 0.35, buff=0.05,
                                                color=C_YELLOW, stroke_width=3, tip_length=0.15,
                                                max_tip_length_to_length_ratio=0.2))
        t1 = T("两个苹果都奔向地心", 30).move_to([3.6, 2.0, 0])
        t2 = T("间距越来越小：潮汐效应", 30, C_YELLOW).move_to([3.6, 1.1, 0])
        t3 = T("自由下落也消除不了它", 26, C_GREY).move_to([3.6, 0.2, 0])
        t4 = T("→ 时空弯曲的真正标志", 30, C_TEAL).move_to([3.6, -0.7, 0])
        self.say("两个同时下落的苹果也会靠近：这种潮汐效应，才是时空弯曲的标志。",
                 Succession(AnimationGroup(FadeIn(earth), FadeIn(ctr), FadeIn(guides), FadeIn(aps), FadeIn(sep),
                                           FadeIn(t1), run_time=0.8),
                            k.animate(rate_func=rush_into, run_time=2.6).set_value(0.62),
                            FadeIn(t2), FadeIn(t3), FadeIn(t4)))
        self.clean()

    # ================================================================== 第五章
    def ch5(self):
        self.chapter("第五章", "弯曲的时间")
        k = 2.0
        grid = sheet_grid(k)
        m0 = sheet_proj(0, 0, -k)
        halo = VGroup(*[Ellipse(width=2.6 * s, height=0.9 * s, stroke_width=0, fill_color=C_BLUE,
                                fill_opacity=0.05).move_to(m0 + UP * 0.15) for s in (1.0, 1.6, 2.3)])
        mass = glow(m0 + UP * 0.38, 0.42, C_GOLD, layers=4, core_color="#fff3b0")
        th = ValueTracker(0.0)

        def mpos():
            t = th.get_value()
            r = 4.2 * (1 - t) + 0.9 * t
            ang = 0.4 + 7.0 * t
            x, y = r * np.cos(ang), r * np.sin(ang)
            return sheet_proj(x, y, well(x, y, k)) + UP * 0.12
        marble = Dot(mpos(), radius=0.13, color=C_TEAL)
        marble.add_updater(lambda m: m.move_to(mpos()))
        warn1 = label_bg(T("小球为何滚向中心？靠的是膜下方的地球重力", 28, C_RED)).move_to([0, 3.4, 0])
        down = Arrow([4.6, 0.2, 0], [4.6, -1.4, 0], buff=0, color=C_RED, stroke_width=6)
        down_l = label_bg(T("重力？", 24, C_RED)).next_to(down, RIGHT, buff=0.1)
        self.say("常见的“橡皮膜”图只是比喻：小球滚进去，靠的恰是膜下的引力。",
                 Succession(AnimationGroup(FadeIn(grid), FadeIn(halo), FadeIn(mass), FadeIn(marble), run_time=1.0),
                            th.animate(rate_func=rush_into, run_time=2.6).set_value(1.0),
                            AnimationGroup(FadeIn(warn1, shift=DOWN * 0.2), GrowArrow(down), FadeIn(down_l))))
        self.clean()
        metric = eq(r"ds^{2}\approx-\Big(1+\frac{2\Phi}{c^{2}}\Big)c^{2}dt^{2}"
                    r"+\Big(1-\frac{2\Phi}{c^{2}}\Big)d\vec{x}^{\,2}", 58).move_to([0, 1.2, 0])
        tpart = metric[0][4:19]
        xpart = metric[0][20:]
        b1 = Brace(tpart, DOWN, color=C_GOLD)
        b2 = Brace(xpart, DOWN, color=C_GREY)
        l1 = T("时间的弯曲\n主导苹果与行星", 24, C_GOLD, line_spacing=0.9).next_to(b1, DOWN, buff=0.15)
        l2 = T("空间的弯曲\n仅对近光速运动显著", 24, C_GREY, line_spacing=0.9).next_to(b2, DOWN, buff=0.15)
        head = T("弱引力场", 30, C_TEAL).move_to([0, 2.7, 0])
        self.say("而对苹果、行星这样的弱引力，主角其实是时间的弯曲。",
                 Succession(FadeIn(head), Write(metric, run_time=1.6),
                            AnimationGroup(GrowFromCenter(b1), FadeIn(l1)),
                            AnimationGroup(GrowFromCenter(b2), FadeIn(l2))))
        self.clean()

        # 时空图：横轴时间，纵轴高度
        O = np.array([-4.2, -1.9, 0])
        TL, HL = 6.6, 4.8
        bands = VGroup()
        nb = 10
        for i in range(nb):
            bands.add(Rectangle(width=TL, height=HL / nb, stroke_width=0, fill_color=C_GOLD,
                                fill_opacity=0.02 + 0.2 * i / nb)
                      .move_to(O + np.array([TL / 2, (i + 0.5) * HL / nb, 0])))
        tax = Arrow(O, O + RIGHT * (TL + 0.3), buff=0, color=C_WHITE, stroke_width=3)
        hax = Arrow(O, O + UP * (HL + 0.2), buff=0, color=C_WHITE, stroke_width=3)
        tlab = T("时间 t", 26).next_to(tax.get_end(), RIGHT, buff=0.15)
        hlab = T("高度 h", 26).next_to(hax.get_end(), RIGHT, buff=0.15)
        cks = VGroup()
        for h, r in zip([0.5, 2.3, 4.1], [0.9, 1.6, 2.3]):
            c = make_clock(0.32).move_to(O + np.array([-1.25, h, 0]))
            run_clock(c, r)
            cks.add(c)
        ck_lab = T("越高越快", 22, C_GOLD).move_to(O + np.array([-1.25, 4.95, 0]))
        # 候选路径 + 走时仪表
        H = ValueTracker(0.02)
        TT = 6.0
        peak_scale = 4.4 / 0.25

        def path_pt(s, hv):
            return O + np.array([0.15 + TT * s, peak_scale * hv * 4 * s * (1 - s), 0])

        def gain(hv):
            return (2 / 3) * hv - (8 / 3) * hv * hv
        Ag = Dot(path_pt(0, 0), radius=0.09, color=C_WHITE)
        Bg = Dot(path_pt(1, 0), radius=0.09, color=C_WHITE)
        Al = T("抛出", 22).next_to(Ag, DOWN, buff=0.15).shift(RIGHT * 0.15)
        Bl = T("落回", 22).next_to(Bg, DOWN, buff=0.15)

        def path_col():
            q = 1 - min(1, abs(H.get_value() - 0.125) / 0.08)
            return interpolate_color(ManimColor(C_WHITE), ManimColor(C_GREEN), q ** 2)
        cand = always_redraw(lambda: ParametricFunction(lambda s: path_pt(s, H.get_value()), t_range=[0, 1, 0.02],
                                                        stroke_color=path_col(), stroke_width=5))
        MX = 5.3
        base_y = O[1]
        mframe = Rectangle(width=0.8, height=3.3, stroke_color=C_GREY, stroke_width=2).move_to(
            [MX, base_y + 1.65, 0])
        mtitle = T("自身钟表\n走过的时间", 22, C_WHITE, line_spacing=0.9).next_to(mframe, UP, buff=0.15)
        maxline = DashedLine([MX - 0.6, base_y + 0.4 + 2.6, 0], [MX + 0.6, base_y + 0.4 + 2.6, 0],
                             stroke_color=C_GREEN, stroke_width=2)
        bar = always_redraw(lambda: Rectangle(width=0.6, height=0.4 + 62.4 * max(gain(H.get_value()), 0.0005),
                                              stroke_width=0, fill_color=path_col(), fill_opacity=0.9)
                            .move_to([MX, base_y, 0], aligned_edge=DOWN))
        self.say("自由运动的规则：在两个事件之间，走让自身钟表读数最大的路径。",
                 Succession(AnimationGroup(GrowArrow(tax), GrowArrow(hax), FadeIn(tlab), FadeIn(hlab), FadeIn(bands),
                                           LaggedStart(*[FadeIn(c) for c in cks], lag_ratio=0.3),
                                           FadeIn(ck_lab), run_time=1.4),
                            Wait(1.0),
                            AnimationGroup(FadeIn(Ag), FadeIn(Bg), FadeIn(Al), FadeIn(Bl), FadeIn(mframe),
                                           FadeIn(mtitle), FadeIn(maxline), FadeIn(cand), FadeIn(bar), run_time=1.0)))
        plus = T("高处钟快：走时 ＋", 24, C_GOLD).move_to([MX - 0.6, 3.45, 0])
        minus = T("速度快：走时 －", 24, C_RED).move_to([MX - 0.6, 2.95, 0])
        best = T("真实世界线 = 牛顿抛物线", 26, C_GREEN).move_to(O + np.array([TT / 2 + 0.15, 2.75, 0]))
        maxl = T("最长", 22, C_GREEN).next_to(maxline, RIGHT, buff=0.1)
        self.say("飞得高钟走得快，但飞得快钟又变慢；权衡的最优解，恰是牛顿的抛物线。",
                 Succession(AnimationGroup(FadeIn(plus), H.animate(run_time=1.4).set_value(0.1)),
                            AnimationGroup(FadeIn(minus), H.animate(run_time=1.4).set_value(0.25)),
                            H.animate(run_time=1.0).set_value(0.05),
                            H.animate(run_time=1.4).set_value(0.125),
                            AnimationGroup(FadeIn(best), FadeIn(maxl), run_time=0.6)))
        cand.clear_updaters()
        bar.clear_updaters()
        s = ValueTracker(0.0)
        ap = apple(0.15)
        ap.add_updater(lambda m: m.move_to(path_pt(s.get_value(), 0.125)))
        proj = always_redraw(lambda: DashedLine(path_pt(s.get_value(), 0.125),
                                                [O[0], path_pt(s.get_value(), 0.125)[1], 0],
                                                stroke_color=C_RED, stroke_width=2, dash_length=0.08))
        self.add(ap, proj)
        self.say("苹果不是被“拉”下来的，它只是在弯曲的时间里走“直线”。",
                 s.animate.set_value(1.0), run_time=3.5, rate_func=linear)
        self.clean()

    # ================================================================== 第六章
    def ch6(self):
        self.chapter("第六章", "场方程")
        pk = dict(cx=0.0, cy=-0.35, el=20 * DEGREES, S=0.95)
        k = ValueTracker(0.0)
        grid = always_redraw(lambda: sheet_grid(k.get_value(), n=15, samples=40, **pk))
        mass = always_redraw(lambda: glow(sheet_proj(0, 0, -k.get_value(), **pk) + UP * 0.35,
                                          0.12 + 0.22 * k.get_value() / 1.8, C_GOLD, layers=4,
                                          core_color="#fff3b0"))
        fe = eq(r"G_{\mu\nu}", 64)
        fr = eq(r"=\frac{8\pi G}{c^{4}}", 64)
        ft = eq(r"T_{\mu\nu}", 64)
        feq = VGroup(fe, fr, ft).arrange(RIGHT, buff=0.15).move_to([0, 3.0, 0])
        b1 = Brace(fe, DOWN, color=C_BLUE, buff=0.1)
        b2 = Brace(ft, DOWN, color=C_GOLD, buff=0.1)
        l1 = T("时空的弯曲", 26, C_BLUE).next_to(b1, DOWN, buff=0.1)
        l2 = T("物质与能量", 26, C_GOLD).next_to(b2, DOWN, buff=0.1)
        lam = T("（1917 年另加宇宙学常数项 Λ）", 20, C_GREY).next_to(feq, RIGHT, buff=0.3)
        self.add(grid)
        self.say("1915年的场方程：左边是时空的弯曲，右边是物质与能量。",
                 Succession(AnimationGroup(FadeIn(grid), FadeIn(mass), Write(feq), run_time=1.4),
                            k.animate(run_time=2.4).set_value(1.8),
                            AnimationGroup(GrowFromCenter(b1), FadeIn(l1), GrowFromCenter(b2), FadeIn(l2),
                                           FadeIn(lam), run_time=1.0)))
        grid.clear_updaters()
        mass.clear_updaters()
        q1 = T("物质告诉时空如何弯曲，", 34, C_GOLD)
        q2 = T("时空告诉物质如何运动。", 34, C_BLUE)
        qa = T("—— 约翰·惠勒", 24, C_GREY)
        quote = VGroup(q1, q2).arrange(DOWN, buff=0.2, aligned_edge=LEFT).move_to([0.6, 2.85, 0])
        qa.next_to(quote, DOWN, buff=0.15).align_to(quote, RIGHT)
        small = VGroup(fe, fr, ft)
        kv = 1.8
        ph = ValueTracker(0.0)

        def ppos():
            a = ph.get_value()
            x, y = 3.0 * np.cos(a), 3.0 * np.sin(a)
            return sheet_proj(x, y, well(x, y, kv), **pk) + UP * 0.1
        orb = VMobject(stroke_color=C_TEAL, stroke_width=2, stroke_opacity=0.6).set_points_smoothly(
            [sheet_proj(3 * np.cos(a), 3 * np.sin(a), well(3 * np.cos(a), 3 * np.sin(a), kv), **pk)
             for a in np.linspace(0, TAU, 80)])
        pl = planet_disk(ppos(), 0.17)
        pl.add_updater(lambda m: m.move_to(ppos()))
        geo = T("测地线", 24, C_TEAL).move_to([4.6, 0.25, 0])
        self.say("惠勒说：物质告诉时空如何弯曲，时空告诉物质如何运动。",
                 Succession(AnimationGroup(FadeOut(VGroup(b1, b2, l1, l2, lam)),
                                           small.animate.scale(0.55).to_corner(UL, buff=0.35), run_time=0.8),
                            AnimationGroup(FadeIn(q1, shift=RIGHT * 0.2), Create(orb), FadeIn(pl), FadeIn(geo),
                                           run_time=0.9),
                            AnimationGroup(Succession(Wait(0.3), FadeIn(q2, shift=RIGHT * 0.2, run_time=0.7),
                                                      FadeIn(qa, run_time=0.5)),
                                           ph.animate(rate_func=linear, run_time=4.6).set_value(TAU * 1.15)))) 
        self.clean()

    # ================================================================== 第七章
    def ch7(self):
        self.chapter("第七章", "实验的检验")
        # ---------- 水星进动
        S = np.array([-3.2, 0.45, 0])
        sn = sun(S, 0.32)
        p, e, dl = 1.55, 0.45, 0.09
        st = {"th": 0.0}

        def rr(th):
            return p / (1 + e * np.cos(th * (1 - dl)))

        def mp(th):
            r = rr(th)
            return S + np.array([r * np.cos(th), r * np.sin(th), 0])
        merc = Dot(mp(0), radius=0.08, color=C_GREY)
        spd = ValueTracker(0.0)

        def adv(m, dt):
            st["th"] += spd.get_value() * dt / rr(st["th"]) ** 2
            m.move_to(mp(st["th"]))
        merc.add_updater(adv)
        trail = TracedPath(merc.get_center, stroke_color=C_BLUE, stroke_width=2, stroke_opacity=0.7)

        def peri_line():
            n = np.floor(st["th"] * (1 - dl) / TAU + 0.5)
            ang = n * TAU / (1 - dl)
            d = np.array([np.cos(ang), np.sin(ang), 0])
            return Line(S, S + d * 1.25, stroke_color=C_YELLOW, stroke_width=3)
        pline = always_redraw(peri_line)
        ex = T("（进动被极度夸大）", 22, C_GREY).move_to([-3.2, -2.25, 0])
        h1 = T("水星近日点进动", 34, C_WHITE, weight=BOLD).move_to([3.4, 2.7, 0])
        r1 = VGroup(T("扣除行星摄动后的剩余：", 26), eq(r"\approx 43''", 42, C_YELLOW), T("/ 世纪", 26)
                    ).arrange(RIGHT, buff=0.12).move_to([3.4, 1.6, 0])
        r2 = T("牛顿理论：无法解释", 26, C_RED).move_to([3.4, 0.7, 0])
        r3 = VGroup(T("广义相对论：", 26, C_GREEN), eq(r"42.98''", 42, C_GREEN)).arrange(RIGHT, buff=0.12
                                                                                        ).move_to([3.4, -0.2, 0])
        self.add(trail, merc, pline)
        self.say("检验一：水星近日点每世纪多转43角秒，牛顿无解，广义相对论恰好算出。",
                 Succession(AnimationGroup(FadeIn(sn), FadeIn(ex), FadeIn(h1), spd.animate.set_value(4.0),
                                           run_time=1.0),
                            AnimationGroup(FadeIn(r1), run_time=1.0), Wait(1.2), FadeIn(r2), Wait(0.8),
                            FadeIn(r3)))
        self.clean()

        # ---------- 光线偏折
        stars = starfield(45, seed=21, op=0.5)
        Sun = np.array([0, 0, 0])
        sn = sun(Sun, 0.75)
        Obs = np.array([-6.0, -0.2, 0])
        P = np.array([0, 1.0, 0])
        St = np.array([6.3, 1.45, 0])
        app_dir = (P - Obs) / np.linalg.norm(P - Obs)
        App = Obs + app_dir * ((St[0] - Obs[0]) / app_dir[0])
        ray = VMobject(stroke_color=C_YELLOW, stroke_width=4)
        ray.set_points_smoothly([St, (St + P) / 2, P + RIGHT * 0.6 + UP * 0.02, P, P + LEFT * 0.6 + DOWN * 0.08,
                                 (P + Obs) / 2, Obs])
        star_true = Star(5, outer_radius=0.17, color=C_WHITE, fill_opacity=1).move_to(St)
        star_app = Star(5, outer_radius=0.17, color=C_YELLOW, fill_opacity=0.5, stroke_opacity=0.6).move_to(App)
        ext = DashedLine(P, App, stroke_color=C_YELLOW, stroke_width=2, dash_length=0.12, stroke_opacity=0.7)
        earth = planet_disk(Obs, 0.22)
        el = T("地球", 22).next_to(earth, DOWN, buff=0.12)
        tl = T("真实位置", 22, C_WHITE).next_to(star_true, DOWN, buff=0.15)
        al = T("看到的位置", 22, C_YELLOW).next_to(star_app, UP, buff=0.12)
        f1 = VGroup(eq(r"\delta=\frac{4GM_\odot}{c^{2}R_\odot}=1.75''", 46, C_WHITE)).move_to([0, 3.1, 0])
        f2 = VGroup(T("= 2 ×“牛顿式”估算", 26, C_GREY), eq(r"0.87''", 40, C_GREY)).arrange(RIGHT, buff=0.12)
        f2.move_to([0, 2.15, 0])
        exg = T("（角度被夸大）", 20, C_GREY).move_to([3.0, -0.7, 0])
        self.add(stars)
        moon = Circle(radius=0.78, stroke_width=0, fill_color="#05060a", fill_opacity=0).move_to([1.4, -0.9, 0])
        corona = Circle(radius=0.95, stroke_color=WHITE, stroke_width=6, stroke_opacity=0.35).move_to(Sun)
        ec = T("1919 年日全食 · 爱丁顿", 26, C_TEAL).move_to([-3.2, -1.6, 0])
        vl = T("如今射电干涉测量：精度达万分之几", 24, C_GREY).move_to([3.4, -1.9, 0])
        self.say("检验二：星光掠过太阳边缘偏折1.75角秒，1919年日食时由爱丁顿测得。",
                 Succession(AnimationGroup(FadeIn(stars), FadeIn(sn), FadeIn(earth), FadeIn(el), FadeIn(star_true),
                                           FadeIn(tl), run_time=0.6),
                            Create(ray, run_time=1.2),
                            AnimationGroup(Create(ext), FadeIn(star_app), FadeIn(al), FadeIn(exg), run_time=0.7),
                            Write(f1, run_time=0.8), FadeIn(f2, run_time=0.5),
                            AnimationGroup(moon.animate.move_to(Sun).set_fill(opacity=1), FadeIn(ec), run_time=1.3),
                            AnimationGroup(FadeIn(corona), FadeIn(vl), run_time=0.6)))
        self.clean()

        # ---------- 红移 + 夏皮罗延迟
        tw = Rectangle(width=0.5, height=3.6, stroke_color=C_GREY, stroke_width=2, fill_color="#1c2230",
                       fill_opacity=1).move_to([-4.2, 0.6, 0])
        gnd = Line([-6.0, -1.2, 0], [-2.4, -1.2, 0], stroke_color=C_GREEN, stroke_width=3)
        q = ValueTracker(0.0)

        def phot():
            def f(s):
                y = -0.9 + 3.0 * s
                ph = TAU * 6 * np.log(1 + 0.8 * s) / 0.8 - q.get_value()
                return np.array([-3.4 + 0.15 * np.sin(ph), y, 0])
            w = ParametricFunction(f, t_range=[0, 1, 0.005], stroke_width=3)
            w.set_stroke(color=[C_BLUE, C_RED])
            return w
        pw = always_redraw(phot)
        rl = T("引力红移", 30, C_WHITE).move_to([-4.0, -1.65, 0])
        rl2 = T("庞德—雷布卡：22.5 米高塔", 22, C_GREY).move_to([-4.0, -2.1, 0])
        E2, S2, C2 = np.array([0.7, 0.0, 0]), np.array([3.8, 0.0, 0]), np.array([6.6, 0.25, 0])
        e2 = planet_disk(E2, 0.2)
        s2 = sun(S2, 0.42)
        cas = Square(0.18, stroke_width=0, fill_color=C_GREY, fill_opacity=1).move_to(C2)
        sig_path = VMobject(stroke_color=C_TEAL, stroke_width=1.5, stroke_opacity=0.5).set_points_smoothly(
            [E2, S2 + UP * 0.62, C2])
        pos = ValueTracker(0.0)
        pulses = VGroup(*[Dot(radius=0.06, color=C_TEAL) for _ in range(4)])

        def pupd(m):
            for i, d in enumerate(m):
                a = (pos.get_value() - i * 0.13) % 1.0
                d.move_to(sig_path.point_from_proportion(a))
                d.set_opacity(1 if 0.02 < a < 0.98 else 0)
        pulses.add_updater(pupd)
        sl = T("夏皮罗延迟", 30, C_WHITE).move_to([3.7, -1.65, 0])
        sl2 = T("卡西尼号（2003）：吻合到十万分之几", 22, C_GREY).move_to([3.7, -2.1, 0])
        slow = T("经过太阳附近：信号被延迟", 22, C_TEAL).move_to([3.8, 1.3, 0])
        self.add(pw, pulses)
        self.say("引力红移、雷达回波的夏皮罗延迟，也都被精确证实。",
                 Succession(AnimationGroup(FadeIn(VGroup(tw, gnd, rl, rl2)), FadeIn(pw),
                                           FadeIn(VGroup(e2, s2, cas, sig_path, sl, sl2)), FadeIn(slow),
                                           q.animate.set_value(3), pos.animate.set_value(0.2), run_time=0.6,
                                           rate_func=linear),
                            AnimationGroup(q.animate.set_value(30), pos.animate.set_value(2.0), run_time=4.6,
                                           rate_func=linear)))
        self.clean()

        # ---------- GPS
        Eg = np.array([-3.3, 0.35, 0])
        earth = planet_disk(Eg, 1.2)
        orbit = Circle(radius=2.45, stroke_color=C_GREY, stroke_width=1.5, stroke_opacity=0.5).move_to(Eg)
        sa = ValueTracker(0.6)

        def spos():
            a = sa.get_value()
            return Eg + 2.45 * np.array([np.cos(a), np.sin(a), 0])
        sat = VGroup(Square(0.22, stroke_width=0, fill_color=C_GREY, fill_opacity=1),
                     Rectangle(width=0.5, height=0.14, stroke_width=0, fill_color=C_BLUE, fill_opacity=1).shift(LEFT * 0.38),
                     Rectangle(width=0.5, height=0.14, stroke_width=0, fill_color=C_BLUE, fill_opacity=1).shift(RIGHT * 0.38))
        sat.add_updater(lambda m: m.move_to(spos()))
        sck = make_clock(0.22)
        sck.add_updater(lambda m: m.move_to(spos() + UP * 0.45))
        gck = make_clock(0.22).move_to(Eg + DOWN * 0.1 + LEFT * 0.0)
        run_clock(sck, 2.6)
        run_clock(gck, 2.0)
        alt = T("轨道高约 20 200 km", 20, C_GREY).move_to(Eg + np.array([0, 1.75, 0]))
        rows = VGroup(
            VGroup(T("引力较弱（高处钟快）", 26), eq(r"+45\,\mu\mathrm{s}", 40, C_GOLD), T("/ 天", 26)),
            VGroup(T("高速运动（狭义相对论）", 26), eq(r"-7\,\mu\mathrm{s}", 40, C_RED), T("/ 天", 26)),
            VGroup(T("净效应", 28, C_WHITE, weight=BOLD), eq(r"+38\,\mu\mathrm{s}", 44, C_YELLOW), T("/ 天", 26)),
        )
        for i, r in enumerate(rows):
            y = 2.3 - i * 1.0 - (0.2 if i == 2 else 0)
            r[0].move_to([0.6, y, 0], aligned_edge=LEFT)
            r[1].move_to([5.3, y, 0], aligned_edge=RIGHT)
            r[2].next_to(r[1], RIGHT, buff=0.1)
        sep = Line([0.6, 0.62, 0], [6.6, 0.62, 0], stroke_color=C_GREY, stroke_width=2)
        warn = VGroup(T("若不修正：测距误差每天累积", 26, C_RED), eq(r"\approx 11\ \mathrm{km}", 40, C_RED)
                      ).arrange(RIGHT, buff=0.15).move_to([3.5, -0.75, 0])
        calc = eq(r"c\times 38\,\mu\mathrm{s}\approx 11.4\ \mathrm{km}", 34, C_GREY).move_to([3.5, -1.55, 0])
        self.add(sat, sck)
        self.say("GPS卫星钟：引力弱，每天快约45微秒；速度快，又慢约7微秒。",
                 Succession(AnimationGroup(FadeIn(earth), Create(orbit), FadeIn(sat), FadeIn(sck), FadeIn(gck),
                                           FadeIn(alt), run_time=1.0),
                            AnimationGroup(FadeIn(rows[0], shift=LEFT * 0.2), sa.animate.set_value(1.8), run_time=2.2),
                            AnimationGroup(FadeIn(rows[1], shift=LEFT * 0.2), sa.animate.set_value(3.0), run_time=2.2)))
        self.say("净快约38微秒；若不修正，测距误差每天累积约11公里。",
                 Succession(AnimationGroup(Create(sep), FadeIn(rows[2]), sa.animate.set_value(4.0), run_time=1.6),
                            AnimationGroup(FadeIn(warn), sa.animate.set_value(5.0), run_time=1.4),
                            AnimationGroup(FadeIn(calc), sa.animate.set_value(5.8), run_time=1.2)))
        self.clean()

        # ---------- 引力透镜 / 爱因斯坦环
        stars = starfield(60, seed=31, op=0.45)
        Lc = np.array([1.6, 0.55, 0])
        thE, rs = 1.55, 0.32
        beta = ValueTracker(2.9)
        lens = VGroup(*[glow(Lc + np.array(o), r, C_GOLD, layers=4, core_color="#fff3b0")
                        for o, r in [((0, 0, 0), 0.22), ((0.35, 0.22, 0), 0.1), ((-0.3, 0.28, 0), 0.08),
                                     ((-0.12, -0.33, 0), 0.09), ((0.28, -0.2, 0), 0.07)]])
        bdir = np.array([np.cos(2.5), np.sin(2.5), 0])

        def src():
            return DashedVMobject(Circle(radius=rs, stroke_color=C_BLUE, stroke_width=2, stroke_opacity=0.6)
                                  .move_to(Lc + bdir * beta.get_value()), num_dashes=14)

        def imgs():
            b = beta.get_value()
            g = VGroup()
            disc = np.sqrt(b * b + 4 * thE * thE)
            tp, tm = (b + disc) / 2, (disc - b) / 2
            ang = np.arctan2(bdir[1], bdir[0])
            w = PI if b <= rs else np.arcsin(min(1.0, rs / b))
            if w >= PI - 1e-6:
                g.add(Circle(radius=thE, stroke_color=C_BLUE, stroke_width=12).move_to(Lc))
                g.add(Circle(radius=thE, stroke_color=WHITE, stroke_width=3, stroke_opacity=0.7).move_to(Lc))
                return g
            for rad, a0, sw in ((tp, ang, 11), (tm, ang + PI, 7)):
                arc = Arc(radius=rad, start_angle=a0 - w, angle=2 * w, arc_center=Lc,
                          stroke_color=C_BLUE, stroke_width=sw)
                core = Arc(radius=rad, start_angle=a0 - w * 0.8, angle=1.6 * w, arc_center=Lc,
                           stroke_color=WHITE, stroke_width=sw * 0.3, stroke_opacity=0.7)
                g.add(arc, core)
            return g
        srcm = always_redraw(src)
        im = always_redraw(imgs)
        t1 = T("前景星系团 = 引力透镜", 28, C_GOLD).move_to([-4.3, 2.6, 0])
        t2 = T("虚线圈：背景星系的真实位置", 24, C_BLUE).move_to([-4.3, 1.8, 0])
        t3 = T("蓝色：我们看到的像", 24, C_WHITE).move_to([-4.3, 1.2, 0])
        ring_l = T("爱因斯坦环", 34, C_YELLOW, weight=BOLD).move_to([-4.3, -0.3, 0])
        ring_n = T("三者精确对齐时，像变成一个环", 24, C_GREY).move_to([-4.3, -0.95, 0])
        self.add(stars, srcm, im)
        self.say("星系团像透镜一样弯折背后星系的光，形成光弧和“爱因斯坦环”。",
                 Succession(AnimationGroup(FadeIn(stars), FadeIn(lens), FadeIn(srcm), FadeIn(im), FadeIn(t1),
                                           FadeIn(t2), FadeIn(t3), run_time=1.0),
                            beta.animate(run_time=3.6, rate_func=smooth).set_value(0.0),
                            AnimationGroup(FadeIn(ring_l), FadeIn(ring_n), run_time=0.8)))
        self.clean()

    # ================================================================== 第八章
    def ch8(self):
        self.chapter("第八章", "时空的涟漪")
        tau = ValueTracker(0.0)
        Bc = np.array([-3.6, 0.6, 0])
        Rc = np.array([3.6, 0.6, 0])
        om = 1.6  # 轨道角频率（引力波频率是它的 2 倍）

        def binary():
            a = om * tau.get_value()
            d = np.array([np.cos(a), np.sin(a), 0]) * 0.42
            g = VGroup()
            for arm in (0, 1):
                for j, op in enumerate((0.9, 0.6, 0.35, 0.15)):
                    s0, s1 = j * 1.5 * PI, (j + 1) * 1.5 * PI

                    def f(s, arm=arm):
                        r = 0.55 + 2.45 * s / (6 * PI)
                        ang = a + arm * PI - s
                        return Bc + r * np.array([np.cos(ang), np.sin(ang), 0])
                    g.add(ParametricFunction(f, t_range=[s0, s1, 0.08], stroke_color=C_PURPLE,
                                             stroke_width=3, stroke_opacity=op))
            for sgn in (1, -1):
                g.add(Circle(radius=0.2, stroke_color=C_GOLD, stroke_width=2.5, fill_color=BLACK,
                             fill_opacity=1).move_to(Bc + sgn * d))
            return g
        bh = always_redraw(binary)
        base = [np.array([np.cos(a), np.sin(a), 0]) * 1.35 for a in np.linspace(0, TAU, 16, endpoint=False)]
        hamp = 0.45

        def mix():
            t = tau.get_value()
            return float(np.clip((t - 10.4) / 1.4, 0, 1))
        ring = VGroup(*[Dot(Rc + b, radius=0.08, color=C_TEAL) for b in base])

        def rupd(m):
            c = np.cos(2 * om * tau.get_value())
            mm = mix()
            for d, b in zip(m, base):
                plus = np.array([b[0] * (1 + hamp / 2 * c), b[1] * (1 - hamp / 2 * c), 0])
                cross = np.array([b[0] + hamp / 2 * c * b[1], b[1] + hamp / 2 * c * b[0], 0])
                d.move_to(Rc + (1 - mm) * plus + mm * cross)
        ring.add_updater(rupd)
        ref = DashedVMobject(Circle(radius=1.35, stroke_color=C_GREY, stroke_width=1.5).move_to(Rc), num_dashes=30)
        lp = T("“+” 偏振", 30, C_TEAL)
        lx = T("“×” 偏振", 30, C_TEAL)
        lp.move_to(Rc + UP * 2.35)
        lx.move_to(Rc + UP * 2.35)
        lp.add_updater(lambda m: m.set_opacity(1 - mix()))
        lx.add_updater(lambda m: m.set_opacity(mix()))
        lx.set_opacity(0)
        hint = T("一圈自由粒子（形变被夸大）", 22, C_GREY).move_to(Rc + DOWN * 2.15)
        bl = T("双黑洞互绕", 24, C_GOLD).move_to(Bc + DOWN * 2.6 + UP * 0.45)
        self.say("加速的质量会激起以光速传播的时空涟漪：引力波。",
                 Succession(AnimationGroup(FadeIn(bh), FadeIn(bl), tau.animate.set_value(0.5), run_time=0.5,
                                           rate_func=linear),
                            tau.animate(run_time=4.9, rate_func=linear).set_value(6.0)))
        self.add(lp, lx)
        self.say("它让横向空间一边拉伸、一边压缩，有“+”和“×”两种偏振。",
                 Succession(AnimationGroup(FadeIn(ref), FadeIn(ring), FadeIn(hint), tau.animate.set_value(6.5),
                                           run_time=0.5, rate_func=linear),
                            tau.animate(run_time=6.1, rate_func=linear).set_value(15.5)))
        self.clean()

        # ---------- LIGO
        Cn = np.array([-5.6, -1.5, 0])
        AL = 3.2
        wob = ValueTracker(0.0)
        amp = ValueTracker(0.0)

        def arms():
            dlt = 0.12 * amp.get_value() * np.sin(wob.get_value())
            hx = Cn + RIGHT * AL * (1 + dlt)
            vy = Cn + UP * AL * (1 - dlt)
            g = VGroup(Line(Cn, hx, stroke_color=C_RED, stroke_width=3),
                       Line(Cn, vy, stroke_color=C_RED, stroke_width=3),
                       Rectangle(width=0.1, height=0.42, stroke_width=0, fill_color=C_WHITE,
                                 fill_opacity=1).move_to(hx),
                       Rectangle(width=0.42, height=0.1, stroke_width=0, fill_color=C_WHITE,
                                 fill_opacity=1).move_to(vy))
            return g
        ar = always_redraw(arms)
        bs = Square(0.26, stroke_color=C_WHITE, stroke_width=2, fill_color=C_GREY, fill_opacity=1
                    ).rotate(PI / 4).move_to(Cn)
        armlab = T("4 km", 24, C_GREY).move_to(Cn + RIGHT * AL / 2 + DOWN * 0.3)
        ligo = T("LIGO 激光干涉仪", 26, C_WHITE).move_to(Cn + np.array([1.6, AL + 0.45, 0]))
        # 啁啾波形
        ts = np.linspace(-1.0, 0.12, 1400)
        ys = []
        x0 = 1.03
        f0 = 5.0
        for t in ts:
            if t < 0:
                x = -t + 0.03
                A = x ** (-0.25)
                ph = TAU * f0 * (x0 ** 0.625 - x ** 0.625) / 0.625
            else:
                x = 0.03
                A = x ** (-0.25) * np.exp(-t / 0.025)
                ph = TAU * f0 * (x0 ** 0.625 - x ** 0.625) / 0.625 + TAU * f0 * x ** (-0.375) * t
            ys.append(A * np.sin(ph))
        ys = np.array(ys)
        ys = ys / np.abs(ys).max() * 1.05
        xs = 0.3 + (ts - ts[0]) / (ts[-1] - ts[0]) * 6.3
        pts = [np.array([x, 0.65 + y, 0]) for x, y in zip(xs, ys)]
        chirp = VMobject(stroke_color=C_TEAL, stroke_width=2.5).set_points_as_corners(pts)
        axl = Line([0.3, 0.65, 0], [6.7, 0.65, 0], stroke_color=DIM, stroke_width=1.5)
        gwn = T("GW150914 · 2015 年 9 月 14 日", 28, C_YELLOW).move_to([3.5, 2.75, 0])
        mass = eq(r"\approx 36\,M_\odot + 29\,M_\odot \;\to\; 62\,M_\odot", 38).move_to([3.5, -0.95, 0])
        dist = T("距离约 13 亿光年", 24, C_GREY).move_to([3.5, -1.65, 0])
        self.add(ar)
        self.say("2015年，LIGO首次探测到引力波：来自13亿光年外的双黑洞合并。",
                 Succession(AnimationGroup(FadeIn(ar), FadeIn(bs), FadeIn(armlab), FadeIn(ligo), FadeIn(gwn),
                                           Create(axl), run_time=1.0),
                            Create(chirp, run_time=2.6, rate_func=linear),
                            AnimationGroup(FadeIn(mass), FadeIn(dist))))
        dl = VGroup(eq(r"\Delta L \approx 4\times10^{-18}\ \mathrm{m}", 38, C_RED)).move_to([-2.6, 0.9, 0])
        dl2 = T("≈ 质子直径的几百分之一", 22, C_GREY).move_to([-2.6, 0.25, 0])
        nob = T("2017 年诺贝尔物理学奖：韦斯、巴里什、索恩", 22, C_GOLD).move_to([3.4, -2.15, 0])
        self.say("4公里长臂只变了质子直径的几百分之一，此发现获2017年诺贝尔奖。",
                 AnimationGroup(Succession(FadeIn(dl), FadeIn(dl2), Wait(1.0), FadeIn(nob)),
                                amp.animate(rate_func=there_and_back, run_time=4.0).set_value(1.0),
                                wob.animate(rate_func=linear, run_time=4.0).set_value(40.0), run_time=5.5))
        self.clean()

        # ---------- 理论的边界
        Bk = np.array([-3.5, 0.9, 0])
        bhole = VGroup(glow(Bk, 0.85, C_GOLD, layers=5, core=False),
                       Circle(radius=0.95, stroke_color=C_GOLD, stroke_width=4),
                       Circle(radius=0.85, stroke_width=0, fill_color=BLACK, fill_opacity=1).move_to(Bk))
        bhole[1].move_to(Bk)
        bb = ValueTracker(0.0)
        Bb = np.array([3.5, 0.9, 0])

        def bang():
            v = bb.get_value()
            g = VGroup()
            for i in range(5):
                r = 0.15 + v * (0.35 + 0.3 * i)
                g.add(Circle(radius=r, stroke_color=C_YELLOW, stroke_width=3, stroke_opacity=max(0, 0.8 - 0.15 * i)).move_to(Bb))
            g.add(glow(Bb, 0.12, C_YELLOW, layers=4, core_color=WHITE))
            return g
        bgm = always_redraw(bang)
        s1 = T("黑洞中心：奇点", 28, C_WHITE).move_to(Bk + DOWN * 1.9)
        s2 = T("大爆炸起点：奇点", 28, C_WHITE).move_to(Bb + DOWN * 1.9)
        qm1 = T("?", 60, C_RED, weight=BOLD).move_to(Bk + UR * 0.9 + RIGHT * 0.4)
        qm2 = T("?", 60, C_RED, weight=BOLD).move_to(Bb + UR * 0.9 + RIGHT * 0.4)
        qg = VGroup(T("广义相对论", 34, C_BLUE), T("+", 40), T("量子力学", 34, C_PURPLE), T("= ?", 40, C_YELLOW)
                    ).arrange(RIGHT, buff=0.3).move_to([0, 3.3, 0])
        self.say("黑洞中心与大爆炸起点出现“奇点”，理论在那里失效；量子引力仍是未解之谜。",
                 Succession(AnimationGroup(FadeIn(bhole), FadeIn(bgm), FadeIn(s1), FadeIn(s2),
                                           bb.animate.set_value(0.2), run_time=0.6),
                            bb.animate(run_time=2.0).set_value(1.6),
                            AnimationGroup(FadeIn(qm1, scale=1.5), FadeIn(qm2, scale=1.5)),
                            Wait(1.0), FadeIn(qg, shift=DOWN * 0.2)))
        bgm.clear_updaters()
        self.clean()

        # 收尾：弯曲时间中的“直线”
        O = np.array([-3.0, -1.7, 0])
        TL, HL = 6.0, 3.8
        bands = VGroup(*[Rectangle(width=TL, height=HL / 8, stroke_width=0, fill_color=C_GOLD,
                                   fill_opacity=0.02 + 0.2 * i / 8).move_to(O + np.array([TL / 2, (i + 0.5) * HL / 8, 0]))
                         for i in range(8)])
        tax = Arrow(O, O + RIGHT * (TL + 0.3), buff=0, color=C_WHITE, stroke_width=3)
        hax = Arrow(O, O + UP * (HL + 0.2), buff=0, color=C_WHITE, stroke_width=3)
        tl = T("时间", 24).next_to(tax.get_end(), DOWN, buff=0.12)
        hl = T("高度", 24).next_to(hax.get_end(), LEFT, buff=0.12)
        wl = ParametricFunction(lambda s: O + np.array([0.2 + 5.6 * s, 3.2 * 4 * s * (1 - s), 0]), t_range=[0, 1],
                                stroke_color=C_GREEN, stroke_width=6)
        ap = apple(0.16).move_to(wl.get_start())
        msg = T("时空——尤其是时间——的弯曲", 32, C_YELLOW).move_to([0, 3.15, 0])
        self.say("苹果下落，是因为时空——尤其是时间——在弯曲。",
                 Succession(AnimationGroup(FadeIn(bands), GrowArrow(tax), GrowArrow(hax), FadeIn(tl), FadeIn(hl),
                                           run_time=0.8),
                            AnimationGroup(Create(wl), MoveAlongPath(ap, wl), run_time=3.0, rate_func=linear),
                            FadeIn(msg, shift=DOWN * 0.2)))
        self.clean()
