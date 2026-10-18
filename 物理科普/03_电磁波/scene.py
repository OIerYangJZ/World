# -*- coding: utf-8 -*-
"""
物理科普 · 第 03 集　电磁波：光是怎样传播的

渲染：
    PYTHONPATH=../common manim -ql --disable_caching scene.py Video     # 预览
    python ../common/build.py 03_电磁波                                 # 成品
"""
import sys
from style import *

# style.py 在 import 时把分辨率写死为 1080p30，会覆盖命令行 -ql。
# 这里在预览模式下恢复 480p15（不影响 build.py 的 -qh 成品渲染）。
if any(a in ("-ql", "--quality=l") for a in sys.argv[1:]):
    config.pixel_width = 854
    config.pixel_height = 480
    config.frame_rate = 15

E_COL = C_YELLOW      # 电场
B_COL = C_BLUE        # 磁场
S_COL = C_GOLD        # 能流 / 光
K_COL = C_RED         # 辐射“折痕”
YMIN, YMAX, XLIM = -2.5, 3.9, 7.15

RNG = np.random.default_rng(7)


# ====================================================================== 小工具
def vline(color, width=3.0, opacity=1.0):
    m = VMobject()
    m.set_stroke(color, width, opacity)
    m.set_fill(opacity=0)
    m.set_points_as_corners([ORIGIN, RIGHT * 1e-3])
    return m


def vtip(color, opacity=1.0):
    m = VMobject()
    m.set_fill(color, opacity)
    m.set_stroke(width=0)
    m.set_points_as_corners([ORIGIN, RIGHT * 1e-3, UP * 1e-3, ORIGIN])
    return m


def set_arrow(line, tip, a, b, tip_len=0.16):
    d = b - a
    L = float(np.hypot(d[0], d[1]))
    if L < 1e-3:
        line.set_points_as_corners([a, a + RIGHT * 1e-4])
        tip.set_points_as_corners([b, b + RIGHT * 1e-4, b + UP * 1e-4, b])
        return
    u = d / L
    n = np.array([-u[1], u[0], 0.0])
    s = min(tip_len, 0.4 * L)
    base = b - u * s
    line.set_points_as_corners([a, base])
    tip.set_points_as_corners([b, base + n * s * 0.5, base - n * s * 0.5, b])


def charge(sign=1, r=0.22):
    c = Circle(r).set_fill(C_RED if sign > 0 else C_BLUE, 1).set_stroke(WHITE, 2)
    s = MathTex("+" if sign > 0 else "-", font_size=40, color=WHITE).move_to(c)
    g = VGroup(c, s)
    g.set_z_index(20)
    return g


def osym(center, col, s):
    """垂直屏幕朝外的符号 ⊙"""
    return VGroup(Circle(s).set_stroke(col, 2.5).move_to(center),
                  Dot(center, radius=max(0.02, s * 0.33), color=col))


def in_box(P):
    return (P[:, 1] >= YMIN) & (P[:, 1] <= YMAX) & (np.abs(P[:, 0]) <= XLIM)


def polylines(P, labels, styles, group):
    """把折线按“标签 + 是否在画面内”切段，分别着色加入 group。"""
    ok = in_box(P)
    n = len(P)
    i = 0
    while i < n - 1:
        key = (ok[i] and ok[i + 1], labels[i])
        j = i
        while j < n - 1 and (ok[j] and ok[j + 1], labels[j]) == key:
            j += 1
        if key[0] and j > i:
            col, w, op = styles[key[1]]
            m = VMobject().set_stroke(col, w, op)
            m.set_points_as_corners(P[i:j + 1])
            group.add(m)
        i = j if j > i else i + 1


def dashed_circle(center, r, color=C_GREY, width=2, n=72, opacity=0.8):
    g = VGroup()
    ang = np.linspace(0, TAU, 2 * n + 1)
    for k in range(n):
        a0, a1 = ang[2 * k], ang[2 * k + 1]
        P = np.array([center + r * np.array([np.cos(a), np.sin(a), 0]) for a in (a0, a1)])
        if in_box(P).all():
            g.add(Line(P[0], P[1]).set_stroke(color, width, opacity))
    return g


def wl_color(nm):
    """可见光波长 → 近似 RGB"""
    if nm < 380 or nm > 780:
        return C_GREY
    if nm < 440:
        r, g, b = -(nm - 440) / 60, 0, 1
    elif nm < 490:
        r, g, b = 0, (nm - 440) / 50, 1
    elif nm < 510:
        r, g, b = 0, 1, -(nm - 510) / 20
    elif nm < 580:
        r, g, b = (nm - 510) / 70, 1, 0
    elif nm < 645:
        r, g, b = 1, -(nm - 645) / 65, 0
    else:
        r, g, b = 1, 0, 0
    f = 1.0
    if nm < 420:
        f = 0.35 + 0.65 * (nm - 380) / 40
    elif nm > 700:
        f = 0.35 + 0.65 * (780 - nm) / 80
    return rgb_to_color([float(min(1.0, (r * f) ** 0.8)), float(min(1.0, (g * f) ** 0.8)), float(min(1.0, (b * f) ** 0.8))])


def fmt_num(v):
    if v >= 100:
        return f"{int(round(v, -1)) if v >= 1000 else int(round(v))}"
    if v >= 10:
        return f"{int(round(v))}"
    s = f"{v:.1f}"
    return s[:-2] if s.endswith(".0") else s


def fmt_len(m):
    for u, n in [(1e3, "km"), (1, "m"), (1e-2, "cm"), (1e-3, "mm"), (1e-6, "μm"), (1e-9, "nm")]:
        if m >= u * 0.999:
            return f"{fmt_num(m / u)} {n}"
    return f"{fmt_num(m / 1e-12)} pm"


def fmt_freq(f):
    for u, n in [(1e18, "EHz"), (1e15, "PHz"), (1e12, "THz"), (1e9, "GHz"), (1e6, "MHz"), (1e3, "kHz")]:
        if f >= u * 0.999:
            return f"{fmt_num(f / u)} {n}"
    return f"{fmt_num(f)} Hz"


class Proj:
    """简单的正交“伪三维”投影：x 为传播轴，y 竖直，z 指向观众。"""

    def __init__(self, origin=(0, 0.6, 0), az=-0.55, el=0.30, scale=1.0):
        self.o = np.array(origin, dtype=float)
        self.az = ValueTracker(az)
        self.el = ValueTracker(el)
        self.s = scale

    def __call__(self, P):
        P = np.atleast_2d(np.asarray(P, dtype=float))
        a, e = self.az.get_value(), self.el.get_value()
        x, y, z = P[:, 0], P[:, 1], P[:, 2]
        x1 = x * np.cos(a) + z * np.sin(a)
        z1 = -x * np.sin(a) + z * np.cos(a)
        y2 = y * np.cos(e) - z1 * np.sin(e)
        return np.stack([x1, y2, np.zeros_like(x1)], 1) * self.s + self.o

    def pt(self, p):
        return self(p)[0]


class WaveRig(VGroup):
    """沿 x 轴传播的电磁波：E、B 箭头 + 包络线 + 传播轴，每帧按 efun/bfun 刷新。"""

    def __init__(self, proj, efun, bfun=None, x0=-6.0, x1=6.0, n=37,
                 ecol=E_COL, bcol=B_COL, axis=True, env=True, width=2.6):
        super().__init__()
        self.proj, self.x0, self.x1 = proj, x0, x1
        self.xs = np.linspace(x0, x1, n)
        self.xf = np.linspace(x0, x1, 220)
        z = np.zeros_like(self.xs)
        self.base = np.stack([self.xs, z, z], 1)
        zf = np.zeros_like(self.xf)
        self.basef = np.stack([self.xf, zf, zf], 1)
        self.axis = axis
        if axis:
            self.ax, self.axt = vline(GREY_B, 2), vtip(GREY_B)
            self.add(self.ax, self.axt)
        self.parts = []
        for fun, col in ((efun, ecol), (bfun, bcol)):
            if fun is None:
                continue
            ls = [vline(col, width) for _ in self.xs]
            ts = [vtip(col) for _ in self.xs]
            ev = vline(col, 3.2, 0.9) if env else None
            self.parts.append((fun, ls, ts, ev))
            self.add(*ls, *ts)
            if ev is not None:
                self.add(ev)
        self.refresh()
        self.add_updater(lambda m: m.refresh())

    def refresh(self):
        pr = self.proj
        if self.axis:
            a = pr([[self.x0 - 0.6, 0, 0], [self.x1 + 1.0, 0, 0]])
            set_arrow(self.ax, self.axt, a[0], a[1], tip_len=0.25)
        P0 = pr(self.base)
        for fun, ls, ts, ev in self.parts:
            P1 = pr(self.base + fun(self.xs))
            for i in range(len(ls)):
                set_arrow(ls[i], ts[i], P0[i], P1[i])
            if ev is not None:
                ev.set_points_as_corners(pr(self.basef + fun(self.xf)))
        return self


class Reveal(Animation):
    """依次点亮 group 中的子物体（用于光子逐个落屏）"""

    def __init__(self, group, **kw):
        super().__init__(group, **kw)
        self.k = 0

    def interpolate_mobject(self, alpha):
        subs = self.mobject.submobjects
        k = int(alpha * len(subs))
        for i in range(self.k, k):
            subs[i].set_opacity(1)
        self.k = max(self.k, k)


# ====================================================================== 场景
class Video(Explainer):
    def construct(self):
        self.clock = ValueTracker(0.0)
        self.speed = 1.0
        self.driver = Mobject()
        self.driver.add_updater(lambda m, dt: self.clock.increment_value(dt * self.speed))
        self.add(self.driver)

        self.title_card("电磁波", "光是怎样传播的")
        self.intro()
        self.ch1()
        self.ch2()
        self.ch3()
        self.ch4()
        self.ch5()
        self.ch6()
        self.ch7()
        self.end_card([
            "变化的电场与磁场相互激发，以光速传播",
            "横波：E ⊥ B ⊥ 传播方向，E = cB",
            "加速运动的电荷才辐射",
            "从无线电到γ射线，只差波长",
            "光子 E = hf；不需要以太",
        ])

    # ------------------------------------------------------------------ 通用
    def clear_all(self, rt=0.5):
        mobs = [m for m in self.mobjects if m is not self._sub and m is not self.driver]
        for m in mobs:
            m.clear_updaters()
        if mobs:
            self.play(*[FadeOut(m) for m in mobs], run_time=rt)
        self.speed = 1.0

    def tag(self, s, corner=UL):
        return T(s, 28, C_GOLD).to_corner(corner, buff=0.45)

    def plane_wave(self, proj, amp=1.5, lam=4.0, c=1.0, B=True, **kw):
        k = TAU / lam
        clk = self.clock

        def ef(xs):
            v = amp * np.sin(k * (xs - c * clk.get_value()))
            return np.stack([0 * v, v, 0 * v], 1)

        def bf(xs):
            v = amp * np.sin(k * (xs - c * clk.get_value()))
            return np.stack([0 * v, 0 * v, v], 1)

        return WaveRig(proj, ef, bf if B else None, **kw)

    # ------------------------------------------------------------------ 片头
    def intro(self):
        sun_c = np.array([-5.4, 0.7, 0])
        sun = VGroup(*[Circle(0.75 + 0.18 * i).set_fill(S_COL, 0.16 - 0.04 * i).set_stroke(width=0)
                       for i in range(4)],
                     Circle(0.75).set_fill(S_COL, 1).set_stroke(C_YELLOW, 2)).move_to(sun_c)
        eye_c = np.array([5.4, 0.7, 0])
        lid = VGroup(ArcBetweenPoints(eye_c + LEFT * 0.8, eye_c + RIGHT * 0.8, angle=-1.6),
                     ArcBetweenPoints(eye_c + LEFT * 0.8, eye_c + RIGHT * 0.8, angle=1.6)).set_stroke(C_WHITE, 3)
        iris = VGroup(Circle(0.3).set_fill(C_BLUE, 1).set_stroke(width=0),
                      Circle(0.13).set_fill(BLACK, 1).set_stroke(width=0)).move_to(eye_c)
        eye = VGroup(lid, iris)
        ray = FunctionGraph(lambda x: 0.7 + 0.35 * np.sin(3.0 * x), x_range=[-4.4, 4.4, 0.02]).set_stroke(S_COL, 3)
        vac = T("真空", 26, C_GREY).move_to([0, 2.0, 0])
        q = T("？", 60, C_YELLOW).move_to([0, -1.2, 0])
        self.play(FadeIn(sun, scale=0.8), FadeIn(eye), run_time=0.6)
        self.say("光是什么？它怎样穿过真空，来到你眼前？",
                 Create(ray, rate_func=linear), FadeIn(vac), FadeIn(q, scale=1.4), run_time=3.0)
        self.clear_all()

    # ------------------------------------------------------------------ 第一章
    def ch1(self):
        self.chapter("第一章", "电与磁")
        # --- 电荷与电场线
        q0 = np.array([-3.2, 0.6, 0])
        q = charge(+1).move_to(q0)
        dirs = [np.array([np.cos(a), np.sin(a), 0]) for a in np.arange(16) / 16 * TAU]
        lines = VGroup(*[Arrow(q0 + 0.32 * u, q0 + 2.75 * u, buff=0, stroke_width=3, color=E_COL,
                               max_tip_length_to_length_ratio=0.08) for u in dirs])
        coul = eq(r"E=\frac{q}{4\pi\varepsilon_0\, r^2}", 60).move_to([3.4, 0.9, 0])
        lab = T("库仑定律", 30, C_GREY).next_to(coul, UP, buff=0.5)
        note = T("黄色线：电场线", 24, E_COL).next_to(coul, DOWN, buff=0.6)
        self.play(GrowFromCenter(q), run_time=0.6)
        self.say("电荷在周围产生电场，强度与距离平方成反比。",
                 LaggedStart(*[GrowArrow(a) for a in lines], lag_ratio=0.08),
                 FadeIn(lab), Write(coul), FadeIn(note), run_time=2.6)
        self.clear_all()

        # --- 奥斯特：电流的磁场
        w0 = np.array([-3.0, 0.6, 0])
        wire = VGroup(Circle(0.26).set_fill(BLACK, 1).set_stroke(C_GREY, 4),
                      Dot(radius=0.08, color=WHITE)).move_to(w0)
        wire.set_z_index(5)
        needles = VGroup()
        rots = []
        for i in range(8):
            phi = (i + 0.5) / 8 * TAU
            c = w0 + 1.35 * np.array([np.cos(phi), np.sin(phi), 0])
            nd = VGroup(Polygon(c + UP * 0.3, c + RIGHT * 0.07, c + LEFT * 0.07).set_fill(C_RED, 1).set_stroke(width=0),
                        Polygon(c + DOWN * 0.3, c + RIGHT * 0.07, c + LEFT * 0.07).set_fill(GREY_B, 1).set_stroke(width=0),
                        Dot(c, radius=0.03, color=BLACK))
            needles.add(nd)
            ang = (phi + PI) % TAU - PI
            rots.append(Rotate(nd, angle=ang, about_point=c))
        tg = self.tag("1820 · 奥斯特")
        wl = T("导线截面：电流垂直屏幕朝外", 26, C_GREY).move_to([3.4, 2.3, 0])
        beq = eq(r"B=\frac{\mu_0 I}{2\pi r}", 60).move_to([3.4, 0.6, 0])
        rh = T("方向：右手定则", 24, C_GREY).next_to(beq, DOWN, buff=0.5)
        self.play(FadeIn(tg), FadeIn(wire), FadeIn(needles), FadeIn(wl), run_time=0.9)
        self.say("1820年，奥斯特发现电流能让磁针偏转。",
                 Flash(w0, color=C_WHITE, line_length=0.25, flash_radius=0.4),
                 AnimationGroup(*rots, lag_ratio=0.05), run_time=2.4)
        circles = VGroup(*[Arc(radius=r, start_angle=0.35, angle=TAU - 0.35, arc_center=w0)
                           .set_stroke(B_COL, 3).add_tip(tip_length=0.2, tip_width=0.2)
                           for r in (0.75, 1.95, 2.6)])
        for c in circles:
            c.get_tip().set_fill(B_COL, 1).set_stroke(B_COL)
        self.say("电流产生磁场：磁感线一圈圈环绕着导线。",
                 LaggedStart(*[Create(c) for c in circles], lag_ratio=0.3),
                 Write(beq), FadeIn(rh), run_time=2.6)
        self.clear_all()

        # --- 法拉第 / 麦克斯韦 双面板
        L = np.array([-3.5, 1.2, 0])
        R = np.array([3.5, 1.2, 0])
        offs = [np.array([x, y, 0]) for x in (-0.5, 0, 0.5) for y in (-0.5, 0, 0.5)]
        bt, et = ValueTracker(0.12), ValueTracker(0.12)
        self.brate, self.erate = 0.0, 0.0
        drv = Mobject()

        def grow(m, dt):
            bt.increment_value(dt * self.brate)
            et.increment_value(dt * self.erate)
        drv.add_updater(grow)
        self.add(drv)

        loop = Circle(1.12).move_to(L).set_stroke(C_GOLD, 6)
        bsyms = always_redraw(lambda: VGroup(*[osym(L + o, B_COL, 0.05 + 0.13 * bt.get_value()) for o in offs]))
        labB = T("线圈中的磁场 B（朝外）增强", 24, B_COL).move_to(L + [0, 1.85, 0])
        tgF = T("1831 · 法拉第", 28, C_GOLD).move_to([L[0], 3.5, 0])
        earcs = VGroup(*[Arc(radius=1.45, start_angle=s, angle=-1.15, arc_center=L)
                         .set_stroke(E_COL, 4).add_tip(tip_length=0.22, tip_width=0.22)
                         for s in (PI / 2 + 0.2, 0.2, -PI / 2 + 0.2, PI + 0.2)])
        for a in earcs:
            a.get_tip().set_fill(E_COL, 1).set_stroke(E_COL)
        labE = T("感应（涡旋）电场 E", 24, E_COL).move_to(L + [0, -1.8, 0])
        eqF = MathTex(r"\nabla\times\mathbf{E}", "=", r"-\frac{\partial\mathbf{B}}{\partial t}",
                      font_size=44).move_to(L + [0, -2.65, 0])

        self.play(FadeIn(tgF), Create(loop), FadeIn(bsyms), FadeIn(labB), run_time=1.0)
        self.brate = 0.045
        self.say("1831年，法拉第发现：磁场一变，线圈里就有电流。",
                 LaggedStart(*[Create(a) for a in earcs], lag_ratio=0.2), run_time=2.5)
        dloop = DashedVMobject(loop.copy().set_stroke(C_GOLD, 3, 0.5), num_dashes=40)
        self.say("也就是说：变化的磁场激发涡旋电场，无需导线。",
                 FadeOut(loop), FadeIn(dloop), FadeIn(labE), Write(eqF), run_time=2.5)

        plate = Circle(1.0).move_to(R).set_fill(GREY, 0.2).set_stroke(GREY_B, 2)
        esyms = always_redraw(lambda: VGroup(*[osym(R + o, E_COL, 0.05 + 0.13 * et.get_value()) for o in offs]))
        labE2 = T("电容器极板间的电场 E（朝外）增强", 24, E_COL).move_to(R + [0, 1.85, 0])
        tgM = T("1861–1865 · 麦克斯韦", 28, C_GOLD).move_to([R[0], 3.5, 0])
        barcs = VGroup(*[Arc(radius=1.45, start_angle=s, angle=1.15, arc_center=R)
                         .set_stroke(B_COL, 4).add_tip(tip_length=0.22, tip_width=0.22)
                         for s in (PI / 2 - 0.2, -0.2, -PI / 2 - 0.2, PI - 0.2)])
        for a in barcs:
            a.get_tip().set_fill(B_COL, 1).set_stroke(B_COL)
        eqM = MathTex(r"\nabla\times\mathbf{B}", "=", r"\mu_0\mathbf{J}", "+",
                      r"\mu_0\varepsilon_0\frac{\partial\mathbf{E}}{\partial t}",
                      font_size=44).move_to(R + [0, -2.65, 0])
        self.play(FadeIn(plate), FadeIn(esyms), FadeIn(labE2), FadeIn(tgM), run_time=0.6)
        self.erate = 0.045
        self.say("麦克斯韦补上另一半：变化的电场也激发磁场。",
                 LaggedStart(*[Create(a) for a in barcs], lag_ratio=0.2), Write(eqM), run_time=2.6)
        box = SurroundingRectangle(eqM[4], color=C_TEAL, buff=0.08)
        dlab = T("位移电流（极板间 J = 0）", 24, C_TEAL).move_to(R + [0, -1.8, 0])
        self.say("这一项叫位移电流，没有它，方程会违背电荷守恒。",
                 Create(box), FadeIn(dlab), run_time=1.5)
        self.remove(drv)
        self.clear_all()

    # ------------------------------------------------------------------ 第二章
    def ch2(self):
        self.chapter("第二章", "麦克斯韦的预言")
        y0 = 0.9
        Es = [Ellipse(width=0.9, height=2.2).set_stroke(E_COL, 4).move_to([x, y0, 0]) for x in range(-6, 7, 2)]
        Bs = [Ellipse(width=2.3, height=0.8).set_stroke(B_COL, 4).move_to([x, y0, 0]) for x in range(-5, 6, 2)]
        loops = sorted(Es + Bs, key=lambda m: abs(m.get_center()[0]))
        chain = VGroup(*loops)
        src = charge(+1, 0.18).move_to([0, y0, 0])
        arL = Arrow([-1.5, -1.0, 0], [-4.5, -1.0, 0], buff=0, color=C_WHITE, stroke_width=4)
        arR = Arrow([1.5, -1.0, 0], [4.5, -1.0, 0], buff=0, color=C_WHITE, stroke_width=4)
        cL = MathTex("c", font_size=44).next_to(arL, UP, buff=0.12)
        cR = MathTex("c", font_size=44).next_to(arR, UP, buff=0.12)
        leg = VGroup(T("黄：电场环", 24, E_COL), T("蓝：磁场环", 24, B_COL)).arrange(RIGHT, buff=0.6).move_to([0, 3.35, 0])
        self.play(FadeIn(src), FadeIn(leg), run_time=0.6)
        self.say("于是电与磁的变化彼此咬合，扰动能脱离电荷向外传播。",
                 Succession(LaggedStart(*[Create(m) for m in loops], lag_ratio=0.18, run_time=4.0)),
                 FadeOut(src, run_time=2.0), GrowArrow(arL), GrowArrow(arR), FadeIn(cL), FadeIn(cR),
                 run_time=4.0)
        e1 = MathTex(r"\nabla\times\mathbf{E}=-\frac{\partial\mathbf{B}}{\partial t}", font_size=44, color=E_COL)
        e2 = MathTex(r"\nabla\times\mathbf{B}=\mu_0\varepsilon_0\frac{\partial\mathbf{E}}{\partial t}", font_size=44, color=B_COL)
        mid = T("同时成立", 30, C_TEAL)
        row = VGroup(e1, mid, e2).arrange(RIGHT, buff=0.7).move_to([0, -1.25, 0])
        self.say("但这并非“谁生谁”的接力，而是必须同时满足的方程。",
                 chain.animate.set_stroke(opacity=0.25), FadeOut(VGroup(arL, arR, cL, cR)),
                 FadeIn(row, shift=UP * 0.3), run_time=1.8)
        # 波动方程
        w1 = MathTex(r"\nabla^2\mathbf{E}", "=", r"\mu_0\varepsilon_0", r"\frac{\partial^2\mathbf{E}}{\partial t^2}", font_size=58)
        w2 = MathTex(r"\nabla^2 f", "=", r"\frac{1}{v^2}", r"\frac{\partial^2 f}{\partial t^2}", font_size=58)
        w1.move_to([0.8, 1.55, 0])
        w2.move_to([0.8, 0.1, 0])
        l1 = T("真空中的电场：", 26, C_GREY).next_to(w1, LEFT, buff=0.5)
        l2 = T("一般波动方程：", 26, C_GREY).next_to(w2, LEFT, buff=0.5)
        w1[2].set_color(C_TEAL)
        w2[2].set_color(C_TEAL)
        vres = eq(r"v=\frac{1}{\sqrt{\mu_0\varepsilon_0}}", 62, C_YELLOW).move_to([0, -1.5, 0])
        vbox = SurroundingRectangle(vres, color=C_YELLOW, buff=0.18)
        self.play(FadeOut(chain), FadeOut(leg), row.animate.move_to([0, 3.2, 0]).scale(0.85), run_time=1.0)
        self.say("在真空中联立它们，得到波动方程，波速只由两个常数决定。",
                 Succession(AnimationGroup(FadeIn(l1), Write(w1), run_time=1.6),
                            AnimationGroup(FadeIn(l2), FadeIn(w2), run_time=1.2),
                            AnimationGroup(Write(vres), Create(vbox), run_time=1.4)))
        # 代入数值
        self.play(FadeOut(VGroup(row, w1, w2, l1, l2)), VGroup(vres, vbox).animate.move_to([0, 2.7, 0]), run_time=0.9)
        n1 = eq(r"\varepsilon_0\approx 8.854\times10^{-12}\ \mathrm{F/m}", 40).move_to([-3.4, 1.15, 0])
        n2 = eq(r"\mu_0\approx 1.2566\times10^{-6}\ \mathrm{N/A^2}", 40).move_to([3.4, 1.15, 0])
        res = eq(r"v\approx 2.998\times10^{8}\ \mathrm{m/s}", 64, C_YELLOW).move_to([0, -0.15, 0])
        cmp_ = VGroup(T("实测光速", 32, C_GREEN), eq(r"c\approx 2.998\times10^{8}\ \mathrm{m/s}", 46, C_GREEN),
                      eq(r"\checkmark", 56, C_GREEN)).arrange(RIGHT, buff=0.35).move_to([0, -1.55, 0])
        self.say("代入实测的 ε₀ 和 μ₀：波速约每秒3亿米，正是光速！",
                 Succession(AnimationGroup(FadeIn(n1, shift=DOWN * 0.2), FadeIn(n2, shift=DOWN * 0.2), run_time=1.0),
                            Write(res, run_time=1.2), FadeIn(cmp_, shift=UP * 0.2, run_time=0.9)))
        self.clear_all()
        big = VGroup(T("光", 96, S_COL, weight=BOLD), T("=", 96), T("电磁波", 96, weight=BOLD)).arrange(RIGHT, buff=0.5)
        big.move_to([0, 1.0, 0])
        who = T("詹姆斯·克拉克·麦克斯韦　1862 – 1865", 32, C_GREY).move_to([0, -0.6, 0])
        self.say("1862–1865年，麦克斯韦由此断言：光就是电磁波。",
                 FadeIn(big, scale=1.1), FadeIn(who, shift=UP * 0.2), run_time=1.6)
        self.clear_all()

        # 赫兹实验
        tx = np.array([-4.6, 0.6, 0])
        rx = np.array([4.6, 0.6, 0])
        gap = 0.16
        rods = VGroup(Line(tx + UP * gap, tx + UP * 1.7), Line(tx + DOWN * gap, tx + DOWN * 1.7)).set_stroke(GREY_B, 6)
        balls = VGroup(Dot(tx + UP * 1.8, radius=0.2, color=GREY_B), Dot(tx + DOWN * 1.8, radius=0.2, color=GREY_B),
                       Dot(tx + UP * gap, radius=0.06, color=GREY_B), Dot(tx + DOWN * gap, radius=0.06, color=GREY_B))
        ring = Arc(radius=0.9, start_angle=0.14, angle=TAU - 0.28, arc_center=rx).set_stroke(GREY_B, 5)
        rballs = VGroup(Dot(ring.get_start(), radius=0.06, color=GREY_B), Dot(ring.get_end(), radius=0.06, color=GREY_B))
        tl = T("火花振荡器（发射）", 24, C_GREY).move_to(tx + DOWN * 2.45 + RIGHT * 0.3)
        rl = T("接收环", 24, C_GREY).move_to(rx + DOWN * 1.35)
        tg = self.tag("1887 · 赫兹")
        hz = ValueTracker(0.0)
        vw = 2.0

        def zig(a, b, seed, amp=0.08, n=6):
            rng = np.random.default_rng(seed)
            pts = [a + (b - a) * i / n for i in range(n + 1)]
            d = b - a
            nrm = np.array([-d[1], d[0], 0]) / (np.linalg.norm(d) + 1e-9)
            for i in range(1, n):
                pts[i] = pts[i] + nrm * rng.uniform(-amp, amp)
            return VMobject().set_points_as_corners(pts).set_stroke(WHITE, 3)

        def sparks():
            p = hz.get_value()
            g = VGroup()
            if p > 0.01 and (p * 4) % 1 < 0.55:
                g.add(zig(tx + UP * gap, tx + DOWN * gap, int(p * 40)).set_stroke(C_YELLOW, 4))
            if p * vw > 9.2 - 0.9 and (p * 4 + 0.3) % 1 < 0.5:
                g.add(zig(ring.get_start(), ring.get_end(), int(p * 40) + 3, amp=0.05).set_stroke(C_YELLOW, 4))
            return g

        def waves():
            p = hz.get_value()
            g = VGroup()
            front = p * vw
            k = 0
            while front - k * 1.4 > 0:
                r = front - k * 1.4
                if 0.3 < r < 9.6:
                    g.add(Arc(radius=r, start_angle=-0.3, angle=0.6, arc_center=tx)
                          .set_stroke(S_COL, 3, max(0.15, 0.9 - r / 13)))
                k += 1
            return g

        wv = always_redraw(waves)
        sp = always_redraw(sparks)
        self.play(FadeIn(VGroup(rods, balls, ring, rballs, tl, rl, tg)), run_time=0.6)
        self.add(wv, sp)
        self.say("1887年前后，赫兹在实验室里发射并接收到了电磁波。",
                 hz.animate(rate_func=linear).set_value(6.3), run_time=6.3)
        self.clear_all()

    # ------------------------------------------------------------------ 第三章
    def ch3(self):
        self.chapter("第三章", "电磁波的样子")
        # 视角选择：从略低于传播平面处看，z 轴（B 方向）在屏幕上朝右上、与传播轴接近垂直，
        # 这样 B 的正半周与 E 的正半周落在同一侧、同一位置，一眼可见二者同相。
        pr = Proj(origin=(0, 0.3, 0), az=0.15, el=-0.30)
        self.clock.set_value(0)
        self.speed = 1.0
        wave = self.plane_wave(pr, amp=1.5, lam=4.0, c=1.0)
        leg = VGroup(VGroup(Line(ORIGIN, RIGHT * 0.5).set_stroke(E_COL, 4), T("电场 E", 26, E_COL)).arrange(RIGHT, buff=0.2),
                     VGroup(Line(ORIGIN, RIGHT * 0.5).set_stroke(B_COL, 4), T("磁场 B", 26, B_COL)).arrange(RIGHT, buff=0.2)
                     ).arrange(DOWN, aligned_edge=LEFT, buff=0.2).to_corner(UR, buff=0.45)
        clab = always_redraw(lambda: T("传播方向", 24, C_GREY).next_to(pr.pt([6.4, 0, 0]), DOWN, buff=0.3))
        self.play(FadeIn(wave), FadeIn(leg), run_time=1.0)
        self.add(clab)
        self.say("这是一列平面电磁波：黄色是电场，蓝色是磁场。",
                 pr.az.animate.set_value(0.55), pr.el.animate.set_value(-0.85), run_time=4.0,
                 rate_func=smooth)
        # 三轴小坐标架
        tri = Proj(origin=(-5.2, -1.9, 0), az=0.4, el=-0.7, scale=0.75)
        o = tri.pt([0, 0, 0])
        axes = VGroup()
        for v, col, txt in (([1.2, 0, 0], C_WHITE, "c"), ([0, 1.0, 0], E_COL, "E"), ([0, 0, 1.2], B_COL, "B")):
            p = tri.pt(v)
            ar = Arrow(o, p, buff=0, color=col, stroke_width=4, max_tip_length_to_length_ratio=0.25)
            lb = MathTex(txt, font_size=36, color=col).move_to(p + (p - o) / np.linalg.norm(p - o) * 0.3)
            axes.add(ar, lb)
        perp = T("E ⊥ B ⊥ 传播方向", 28).move_to([0, 3.45, 0])
        self.say("电场、磁场、传播方向两两垂直：电磁波是横波。",
                 pr.az.animate.set_value(0.4), pr.el.animate.set_value(-0.7),
                 FadeIn(axes), FadeIn(perp), run_time=2.5)
        # 冻结，标出同相
        self.speed = 0.0
        t0 = self.clock.get_value()
        lam = 4.0
        xc = t0 + lam / 4
        while xc > 1.0:
            xc -= lam
        while xc < -1.0:
            xc += lam
        pE, pB, p0 = pr.pt([xc, 1.5, 0]), pr.pt([xc, 0, 1.5]), pr.pt([xc, 0, 0])
        xz = xc + lam / 4
        pz = pr.pt([xz, 0, 0])
        d1 = DashedLine(pE, p0, color=C_WHITE, stroke_width=2)
        d2 = DashedLine(pB, p0, color=C_WHITE, stroke_width=2)
        rings = VGroup(Circle(0.17).move_to(pE).set_stroke(E_COL, 3), Circle(0.17).move_to(pB).set_stroke(B_COL, 3))
        mx = T("同时最大", 24).next_to(pE, UP, buff=0.22)
        zr = VGroup(Dot(pz, radius=0.09, color=C_WHITE), T("同时为零", 24).next_to(pz, DOWN, buff=1.3).shift(RIGHT * 1.2),
                   Line(pz + DOWN * 0.15 + RIGHT * 0.1, pz + DOWN * 1.15 + RIGHT * 0.9, stroke_width=1.5, color=C_GREY))
        ecb = VGroup(eq(r"E=cB", 54), T("（画面按 c = 1 的单位等长绘制）", 20, C_GREY)).arrange(DOWN, buff=0.15)
        ecb.next_to(leg, DOWN, buff=0.35).align_to(leg, RIGHT)
        self.say("两者同步起伏，同时最大、同时为零；真空中 E = cB。",
                 Succession(AnimationGroup(Create(d1), Create(d2), Create(rings), FadeIn(mx), FadeIn(zr), run_time=1.5),
                            Write(ecb, run_time=1.2)))
        self.play(FadeOut(VGroup(d1, d2, rings, mx, zr)), run_time=0.5)
        self.speed = 1.0
        self.wait(0.6)
        # 波长
        self.speed = 0.0
        t0 = self.clock.get_value()
        xc = t0 + lam / 4
        while xc > -3.0:
            xc -= lam
        while xc < -5.0:
            xc += lam
        a, b = pr.pt([xc, 1.5, 0]), pr.pt([xc + lam, 1.5, 0])
        br = BraceBetweenPoints(a + UP * 0.15, b + UP * 0.15, direction=UP, color=C_WHITE)
        bl = MathTex(r"\lambda", font_size=48).next_to(br.get_center(), UP, buff=0.35)
        clf = eq(r"c=\lambda f", 54).next_to(ecb, DOWN, buff=0.35).align_to(leg, RIGHT)
        self.say("相邻波峰的距离是波长λ，乘以频率f，就是光速。",
                 Succession(AnimationGroup(GrowFromCenter(br), FadeIn(bl), FadeOut(perp), run_time=1.0),
                            Wait(1.2), Write(clf, run_time=1.0)))
        self.play(FadeOut(br), FadeOut(bl), run_time=0.5)
        self.speed = 1.0
        self.wait(0.5)
        self.clear_all()

    # ------------------------------------------------------------------ 第四章
    def field_group(self, T_, traj, center, c=2.0, n=20, R=8.0, m=110, tau=None, col=E_COL):
        ang = (np.arange(n) + 0.5) / n * TAU
        r = np.linspace(0.24, R, m)
        tr = T_ - r / c
        p, v = traj(tr)
        rs = 0.5 * (r[1:] + r[:-1])
        if tau is not None:
            rin, rout = c * max(T_ - tau, 0), c * max(T_, 0)
            labels = np.where(rs <= rin, 0, np.where(rs <= rout, 1, 2))
        else:
            labels = np.zeros(m - 1, dtype=int)
        styles = {0: (col, 2.6, 0.9), 1: (K_COL, 4.5, 1.0), 2: (col, 2.6, 0.9)}
        g = VGroup()
        for a in ang:
            u = np.array([np.cos(a), np.sin(a), 0])
            P = center + p + v * (r / c)[:, None] + r[:, None] * u
            polylines(P, labels, styles, g)
        return g

    def ch4(self):
        self.chapter("第四章", "电磁波从哪里来")
        c = 2.0
        Tt = ValueTracker(0.0)
        # --- 静止 → 匀速
        c0 = np.array([-3.4, 0.6, 0])
        vel = 0.75
        mode = {"v": 0.0}

        def traj_u(t):
            z = np.zeros_like(t)
            x = mode["v"] * t
            return np.stack([x, z, z], 1), np.stack([z + mode["v"], z, z], 1)

        fl = always_redraw(lambda: self.field_group(Tt.get_value(), traj_u, c0, c=c, n=16, R=11.5, m=60))
        q = charge(+1).move_to(c0)
        q.add_updater(lambda m: m.move_to(c0 + RIGHT * mode["v"] * Tt.get_value()))
        self.add(fl)
        self.play(FadeIn(q), run_time=0.6)
        lab = T("静止", 28, C_GREY).move_to([-3.4, 3.4, 0])
        self.add(lab)
        self.wait(0.6)
        mode["v"] = vel
        lab2 = always_redraw(lambda: T("匀速运动 →", 28, C_GREY).move_to(c0 + RIGHT * vel * Tt.get_value() + UP * 2.8))
        self.say("静止或匀速运动的电荷，场线笔直，不辐射。",
                 FadeOut(lab), FadeIn(lab2), Tt.animate(rate_func=linear).set_value(6.0), run_time=5.0)
        q.clear_updaters()
        self.clear_all(0.6)

        # --- 猛推一下
        c1 = np.array([0.0, 0.25, 0])
        tau, v1 = 0.3, 0.75
        acc = v1 / tau

        def traj_k(t):
            z = np.zeros_like(t)
            y = np.where(t < 0, 0, np.where(t < tau, 0.5 * acc * t ** 2, 0.5 * acc * tau ** 2 + v1 * (t - tau)))
            vy = np.where(t < 0, 0, np.where(t < tau, acc * t, v1))
            return np.stack([z, y, z], 1), np.stack([z, vy, z], 1)

        Tk = ValueTracker(-0.4)
        fk = always_redraw(lambda: self.field_group(Tk.get_value(), traj_k, c1, c=c, n=20, R=8.0, m=130, tau=tau))
        qk = always_redraw(lambda: charge(+1).move_to(c1 + traj_k(np.array([Tk.get_value()]))[0][0]))
        shell = always_redraw(lambda: dashed_circle(c1, max(c * Tk.get_value(), 0.01), C_WHITE, 2, n=90, opacity=0.6)
                              if Tk.get_value() > 0.05 else VMobject())
        self.add(fk, qk, shell)
        self.wait(0.6)
        self.say("猛推一下电荷：“它动了”的消息以光速向外扩散。",
                 Tk.animate(rate_func=linear).set_value(1.55), run_time=4.0)
        ghost = DashedVMobject(Circle(0.22).move_to(c1).set_stroke(C_GREY, 2), num_dashes=12)
        gl = T("旧位置", 24, C_GREY).next_to(c1, LEFT, buff=0.35)
        gl.add_background_rectangle(color=BG, opacity=0.85, buff=0.06)
        pnew = c1 + traj_k(np.array([1.55]))[0][0]
        nl = T("新位置", 24, C_WHITE).next_to(pnew, LEFT, buff=0.35)
        nl.add_background_rectangle(color=BG, opacity=0.85, buff=0.06)
        sl = T("以光速扩张的球壳", 24, C_WHITE).move_to(c1 + RIGHT * (c * 1.55) + RIGHT * 1.45 + UP * 0.35)
        sl.add_background_rectangle(color=BG, opacity=0.85, buff=0.06)
        self.say("球壳外，场线仍指向旧位置；球壳内，已指向新位置。",
                 FadeIn(ghost), FadeIn(gl), FadeIn(nl), FadeIn(sl), run_time=1.0)
        kl = T("折痕 = 辐射场", 26, K_COL)
        kl.add_background_rectangle(color=BG, opacity=0.85, buff=0.08)
        kl.move_to([4.6, 2.9, 0])
        self.say("中间的“折痕”，就是以光速飞离的辐射场。",
                 FadeOut(sl), FadeOut(nl), FadeIn(kl),
                 Tk.animate(rate_func=linear).set_value(3.1), run_time=3.6)
        self.clear_all(0.6)

        # --- 振荡偶极子
        c2 = np.array([0.0, 0.6, 0])
        A, per = 0.1, 1.6
        w = TAU / per

        def traj_o(t):
            z = np.zeros_like(t)
            return np.stack([z, A * np.sin(w * t), z], 1), np.stack([z, A * w * np.cos(w * t), z], 1)

        To = ValueTracker(0.0)
        drv = Mobject()
        drv.add_updater(lambda m, dt: To.increment_value(dt * 0.55))
        fo = always_redraw(lambda: self.field_group(To.get_value(), traj_o, c2, c=c, n=20, R=8.6, m=150))
        qo = always_redraw(lambda: charge(+1, 0.18).move_to(c2 + traj_o(np.array([To.get_value()]))[0][0]))
        ant = Line(c2 + DOWN * 0.55, c2 + UP * 0.55).set_stroke(GREY_B, 5)
        self.add(drv)
        self.add(fo, qo)
        self.play(FadeIn(ant), run_time=0.6)
        self.say("让电荷来回振荡，折痕接连发出——这就是天线。", extra=1.0)
        lobe = ParametricFunction(lambda s: c2 + 2.3 * np.sin(s) ** 2 * np.array([np.sin(s), np.cos(s), 0]),
                                  t_range=[0, TAU, 0.02]).set_stroke(S_COL, 4)
        strong = VGroup(*[T("最强", 26, S_COL).move_to(c2 + d * 5.7 + UP * 0.55) for d in (LEFT, RIGHT)])
        zero = T("为零", 26, S_COL).move_to(c2 + UP * 2.85 + RIGHT * 0.9)
        for m in [*strong, zero]:
            m.add_background_rectangle(color=BG, opacity=0.85, buff=0.06)
        eqp = eq(r"\propto\sin^2\theta", 40, S_COL).move_to([5.3, -1.9, 0])
        eqp.add_background_rectangle(color=BG, opacity=0.85, buff=0.08)
        self.say("辐射在垂直于振荡方向最强，沿振荡方向为零。",
                 Create(lobe), FadeIn(strong), FadeIn(zero), FadeIn(eqp), run_time=1.8, extra=0.8)
        self.remove(drv)
        self.clear_all()

    # ------------------------------------------------------------------ 第五章
    def ch5(self):
        self.chapter("第五章", "电磁波谱")
        X = lambda L: -6 + 0.8 * (3 - L)
        yb, hb = 0.3, 0.55
        bands = [(3, 0, "无线电", "#3f4f9a"), (0, -3, "微波", "#2f7a80"), (-3, -6.125, "红外", "#8a3a3a"),
                 (-6.42, -8, "紫外", "#6a3f9a"), (-8, -11, "X射线", "#3f6a9a"), (-11, -12, "γ射线", "#2f8a5f")]
        bar = VGroup()
        for hi, lo, name, col in bands:
            r = Rectangle(width=X(lo) - X(hi), height=hb).set_fill(col, 0.85).set_stroke(width=0)
            r.move_to([(X(hi) + X(lo)) / 2, yb, 0])
            t = T(name, 22 if name != "γ射线" else 20, C_WHITE).move_to(r)
            bar.add(r, t)
        vis = VGroup()
        nv = 10
        for i in range(nv):
            L0 = -6.125 - (0.295) * i / nv
            L1 = -6.125 - (0.295) * (i + 1) / nv
            nm = 10 ** ((L0 + L1) / 2) * 1e9
            vis.add(Rectangle(width=X(L1) - X(L0), height=hb).set_fill(wl_color(nm), 1).set_stroke(width=0)
                    .move_to([(X(L0) + X(L1)) / 2, yb, 0]))
        bar.add(vis)
        frame = Rectangle(width=12, height=hb).move_to([0, yb, 0]).set_stroke(GREY_B, 1.5)
        ticks = VGroup()
        for L, s in ((3, "1 km"), (0, "1 m"), (-3, "1 mm"), (-9, "1 nm"), (-12, "1 pm")):
            ticks.add(Line([X(L), yb - hb / 2, 0], [X(L), yb - hb / 2 - 0.15, 0]).set_stroke(GREY_B, 2),
                      T(s, 22, C_GREY).move_to([X(L), yb - hb / 2 - 0.38, 0]))
        axl = T("波长（对数刻度）", 22, C_GREY).move_to([-4.8, -0.75, 0])
        Lt = ValueTracker(2.6)

        def vcol(L):
            nm = 10 ** L * 1e9
            return wl_color(nm) if 380 <= nm <= 750 else C_TEAL

        def wave():
            L = Lt.get_value()
            lam_s = 10 ** (0.317 + 0.095 * L)
            xs = np.linspace(-6, 6, 1400)
            P = np.stack([xs, 2.45 + 0.55 * np.sin(TAU * xs / lam_s), 0 * xs], 1)
            return VMobject().set_points_as_corners(P).set_stroke(vcol(L), 3)

        def pointer():
            L = Lt.get_value()
            x = X(L)
            return Triangle().scale(0.14).rotate(PI).move_to([x, yb + hb / 2 + 0.2, 0]).set_fill(C_WHITE, 1).set_stroke(width=0)

        def name_of(L):
            if L > 0: return "无线电"
            if L > -3: return "微波"
            if L > -6.125: return "红外"
            if L > -6.42: return "可见光"
            if L > -8: return "紫外"
            if L > -11: return "X射线"
            return "γ射线"

        def readout():
            L = Lt.get_value()
            lam = 10 ** L
            f = 299792458.0 / lam
            s = f"λ ≈ {fmt_len(lam)}      f ≈ {fmt_freq(f)}      {name_of(L)}"
            return T(s, 30, C_WHITE).move_to([0, 1.35, 0])

        wv = always_redraw(wave)
        pt = always_redraw(pointer)
        ro = always_redraw(readout)
        self.play(FadeIn(bar), Create(frame), FadeIn(ticks), FadeIn(axl), FadeIn(wv), FadeIn(pt), FadeIn(ro), run_time=1.0)
        self.say("振荡越快，频率越高，波长越短。",
                 Lt.animate(rate_func=smooth).set_value(-1.5), run_time=3.5)
        self.say("从无线电到γ射线，本质相同，只是波长不同。",
                 Lt.animate(rate_func=linear).set_value(-11.6), run_time=6.0)
        # 放大可见光
        rb = VGroup()
        n = 70
        for i in range(n):
            nm = 750 - (750 - 380) * (i + 0.5) / n
            rb.add(Rectangle(width=8 / n + 0.005, height=0.45).set_fill(wl_color(nm), 1).set_stroke(width=0)
                   .move_to([-4 + 8 * (i + 0.5) / n, -1.6, 0]))
        z1 = DashedLine([X(-6.125), yb - hb / 2, 0], [-4, -1.375, 0], color=GREY_B, stroke_width=1.5)
        z2 = DashedLine([X(-6.42), yb - hb / 2, 0], [4, -1.375, 0], color=GREY_B, stroke_width=1.5)
        e1 = T("750 nm", 22, C_GREY).next_to(rb, LEFT, buff=0.2)
        e2 = T("380 nm", 22, C_GREY).next_to(rb, RIGHT, buff=0.2)
        vl = T("人眼可见：约 380 – 750 nm", 24, C_WHITE).move_to([0, -2.2, 0])
        self.say("人眼只看得见约380到750纳米这窄窄一段。",
                 Lt.animate(rate_func=smooth).set_value(np.log10(560e-9)),
                 Create(z1), Create(z2), FadeIn(rb, lag_ratio=0.02), FadeIn(e1), FadeIn(e2), FadeIn(vl),
                 run_time=3.0, extra=0.3)
        self.clear_all()

    # ------------------------------------------------------------------ 第六章
    def ch6(self):
        self.chapter("第六章", "偏振与光压")
        pr = Proj(origin=(0, 0.45, 0), az=-0.8, el=0.28, scale=0.92)
        lam, A, cw = 2.6, 1.5, 1.2
        k = TAU / lam
        st = {"unpol": True, "on": False}
        alpha = ValueTracker(0.0)
        clk = self.clock
        self.clock.set_value(0)

        def rnd(n):
            return (np.sin(n * 12.9898 + 4.1) * 43758.5453) % 1.0

        def ef(xs):
            u = xs - cw * clk.get_value()
            amp = A * np.sin(k * u)
            phi = rnd(np.floor(u / (lam / 2))) * PI if st["unpol"] else np.zeros_like(u)
            E = np.stack([0 * u, amp * np.cos(phi), amp * np.sin(phi)], 1)
            if st["on"]:
                a = alpha.get_value()
                ad = np.array([0, np.cos(a), np.sin(a)])
                comp = E @ ad
                mask = xs > 0
                E[mask] = comp[mask, None] * ad[None, :]
            return E

        wave = WaveRig(pr, ef, None, x0=-6.5, x1=6.5, n=53, env=False)
        lab = T("自然光：偏振方向杂乱无章", 26, E_COL).move_to([-3.6, 3.35, 0])
        self.play(FadeIn(wave), FadeIn(lab), run_time=0.6)
        self.say("电场振动的方向叫偏振。自然光的偏振杂乱无章。")
        # 偏振片
        sv = np.linspace(0, TAU, 80)

        def disk():
            P = pr(np.stack([0 * sv, 1.9 * np.cos(sv), 1.9 * np.sin(sv)], 1))
            d = VMobject().set_points_as_corners(P).set_fill(GREY_B, 0.18).set_stroke(GREY_A, 2)
            a = alpha.get_value()
            ad = np.array([0, np.cos(a), np.sin(a)])
            ax = DashedLine(pr.pt(-2.2 * ad), pr.pt(2.2 * ad), color=S_COL, stroke_width=3)
            return VGroup(d, ax)

        dk = always_redraw(disk)
        dl = T("偏振片", 26, C_WHITE).move_to(pr.pt([0, 2.3, 0]) + UP * 0.3)
        tl = T("金色虚线：透振方向", 22, S_COL).move_to([0.2, -2.15, 0])
        lab2 = T("线偏振光", 26, E_COL).move_to([4.2, 3.35, 0])
        self.play(FadeIn(dk), FadeIn(dl), run_time=0.6)
        st["on"] = True
        self.say("偏振片只放行沿透振方向的电场分量。",
                 FadeIn(tl), FadeIn(lab2), run_time=1.0)
        # 马吕斯
        lab3 = T("入射：竖直线偏振光", 26, E_COL).move_to(lab)
        mal = eq(r"I=I_0\cos^2\theta", 48).move_to([4.3, 2.55, 0])
        th = VGroup(MathTex(r"\theta=", font_size=40), DecimalNumber(0, num_decimal_places=0, font_size=40,
                    unit=r"^\circ")).arrange(RIGHT, buff=0.12).next_to(mal, DOWN, buff=0.3)
        th[1].add_updater(lambda m: m.set_value(alpha.get_value() * 180 / PI))
        st["unpol"] = False
        self.play(FadeOut(lab), FadeIn(lab3), FadeOut(lab2), FadeIn(mal), FadeIn(th), run_time=0.7)
        self.say("透射光强按 cos²θ 变化（马吕斯定律），90°时全挡住。",
                 alpha.animate(rate_func=smooth).set_value(PI / 2), run_time=5.0)
        th[1].clear_updaters()
        self.clear_all()

        # 能量：坡印廷矢量
        pr2 = Proj(origin=(0, 0.1, 0), az=0.4, el=-0.7)
        self.clock.set_value(0)
        w2 = self.plane_wave(pr2, amp=1.4, lam=4.0, c=1.0, x0=-6, x1=5.5)
        Sv = Arrow(pr2.pt([-1.0, 0, 0]), pr2.pt([4.0, 0, 0]), buff=0, color=S_COL, stroke_width=10,
                   max_tip_length_to_length_ratio=0.12)
        Sv.set_z_index(10)
        Sl = MathTex(r"\mathbf{S}", font_size=48, color=S_COL).next_to(Sv.get_end(), UP, buff=0.25)
        Seq = eq(r"\mathbf{S}=\frac{1}{\mu_0}\,\mathbf{E}\times\mathbf{B}", 48).to_corner(UR, buff=0.5)
        sun = VGroup(T("太阳常数（大气层外）", 24, C_GREY), eq(r"\approx 1361\ \mathrm{W/m^2}", 44, S_COL)
                     ).arrange(DOWN, buff=0.15).to_corner(UL, buff=0.5)
        self.play(FadeIn(w2), run_time=0.6)
        self.say("电磁波携带能量：大气层外，阳光每平方米约1361瓦。",
                 GrowArrow(Sv), FadeIn(Sl), Write(Seq), FadeIn(sun), run_time=2.5)
        self.clear_all()

        # 动量：太阳帆
        sp = ValueTracker(0.0)
        xs0, vph = 2.4, 4.0
        xsail = lambda s: xs0 + 0.012 * s ** 2
        sail = always_redraw(lambda: VGroup(
            Rectangle(width=0.1, height=3.6).set_fill(GREY_A, 1).set_stroke(WHITE, 1).move_to([xsail(sp.get_value()), 0.6, 0]),
            Line([xsail(sp.get_value()), 2.4, 0], [xsail(sp.get_value()) + 1.3, 0.6, 0]).set_stroke(GREY_B, 1.5),
            Line([xsail(sp.get_value()), -1.2, 0], [xsail(sp.get_value()) + 1.3, 0.6, 0]).set_stroke(GREY_B, 1.5),
            Square(0.28).set_fill(GREY_B, 1).set_stroke(width=0).move_to([xsail(sp.get_value()) + 1.4, 0.6, 0]),
        ))
        ys = RNG.uniform(-0.9, 2.1, 14)
        offs = RNG.uniform(0, 4.0, 14)

        def photons():
            s = sp.get_value()
            xsl = xsail(s)
            g = VGroup()
            per = 2 * (xsl + 7.5) / vph + 0.5
            for y, o in zip(ys, offs):
                d = ((s - o) % per) * vph if s > o else -1
                if d < 0:
                    continue
                x = -7.5 + d
                dirn = 1
                if x > xsl - 0.08:
                    x = 2 * (xsl - 0.08) - x
                    dirn = -1
                if x < -7.3:
                    continue
                tail = Line([x, y, 0], [x - dirn * 0.45, y, 0]).set_stroke(S_COL, 3, 0.6)
                g.add(tail, Dot([x, y, 0], radius=0.07, color=S_COL))
            return g

        ph = always_redraw(photons)
        push = always_redraw(lambda: VGroup(
            Arrow([xsail(sp.get_value()) + 0.1, -1.75, 0], [xsail(sp.get_value()) + 1.5, -1.75, 0], buff=0,
                  color=K_COL, stroke_width=6),
            MathTex(r"2p", font_size=36, color=K_COL).move_to([xsail(sp.get_value()) + 2.0, -1.75, 0])))
        slab = T("全反射帆", 24, C_WHITE).move_to([xs0 + 0.6, 2.85, 0])
        peq = eq(r"P=\frac{2I}{c}\approx 9\ \mu\mathrm{Pa}", 48).move_to([-3.6, 3.15, 0])
        ik = T("IKAROS（JAXA，2010）", 22, C_GREY).move_to([4.9, -2.2, 0])
        self.play(FadeIn(sail), FadeIn(slab), run_time=0.6)
        self.add(ph)
        self.say("它还携带动量：全反射帆受到的光压约9微帕。",
                 sp.animate(rate_func=linear).set_value(4.5), FadeIn(push), Write(peq), run_time=5.0)
        self.say("2010年，日本“伊卡洛斯”号首次在行星际验证了太阳帆。",
                 sp.animate(rate_func=linear).set_value(9.5), FadeIn(ik), FadeOut(slab), run_time=5.0)
        self.clear_all()

    # ------------------------------------------------------------------ 第七章
    def ch7(self):
        self.chapter("第七章", "光子与以太")
        hc = 1239.84
        packs = VGroup()
        labs = VGroup()
        for cx, nm in ((-4.2, 700), (0, 530), (4.2, 400)):
            lam_s = 0.7 * nm / 700
            xs = np.linspace(-1.4, 1.4, 300)
            P = np.stack([cx + xs, 2.0 + 0.6 * np.exp(-(xs / 0.6) ** 2) * np.sin(TAU * xs / lam_s), 0 * xs], 1)
            packs.add(VMobject().set_points_as_corners(P).set_stroke(wl_color(nm), 4))
            labs.add(VGroup(T(f"{nm} nm", 24, C_GREY),
                            eq(rf"\approx {hc / nm:.1f}\ \mathrm{{eV}}", 40, wl_color(nm))).arrange(DOWN, buff=0.15)
                     .move_to([cx, 0.55, 0]))
        hf = eq(r"E=hf", 72).move_to([0, -1.0, 0])
        hv = eq(r"h=6.626\times10^{-34}\ \mathrm{J\cdot s}", 34, C_GREY).move_to([0, -2.05, 0])
        self.say("光的能量一份一份地交换：每份是一个光子，E = hf。",
                 Succession(LaggedStart(*[FadeIn(p, shift=RIGHT * 0.8) for p in packs], lag_ratio=0.35, run_time=2.2),
                            AnimationGroup(LaggedStart(*[FadeIn(l) for l in labs], lag_ratio=0.3), Write(hf), FadeIn(hv),
                                           run_time=2.0)), extra=0.3)
        self.clear_all()

        # 单光子双缝
        y0 = 0.7
        xb, xsN = -2.5, 2.6
        barrier = VGroup(Line([xb, -2.4, 0], [xb, y0 - 0.56, 0]), Line([xb, y0 - 0.36, 0], [xb, y0 + 0.36, 0]),
                         Line([xb, y0 + 0.56, 0], [xb, 3.8, 0])).set_stroke(GREY_B, 6)
        screen = Line([xsN, -2.4, 0], [xsN, 3.8, 0]).set_stroke(GREY_A, 3)
        src = VGroup(Dot([-6.2, y0, 0], radius=0.12, color=S_COL),
                     *[Arc(radius=r, start_angle=-0.5, angle=1.0, arc_center=[-6.2, y0, 0]).set_stroke(S_COL, 2, 0.5)
                       for r in (0.8, 1.6, 2.4, 3.2)])
        I = lambda y: np.cos(PI * (y - y0) / 0.85) ** 2 * np.exp(-((y - y0) / 1.7) ** 2)
        pts = []
        while len(pts) < 700:
            y = RNG.uniform(-2.35, 3.75)
            if RNG.uniform() < I(y):
                pts.append(y)
        dots = VGroup(*[Dot([xsN + 0.08 + RNG.uniform(0, 0.38), y, 0], radius=0.028, color=C_WHITE).set_opacity(0)
                        for y in pts])
        curve = ParametricFunction(lambda y: np.array([xsN + 0.65 + 2.6 * I(y), y, 0]), t_range=[-2.4, 3.8, 0.01]).set_stroke(C_TEAL, 3)
        cl = T("波动理论的强度分布", 22, C_TEAL).move_to([5.3, 3.55, 0])
        sl = T("探测屏", 22, C_GREY).move_to([xsN - 0.75, 3.55, 0])
        bl = T("双缝", 22, C_GREY).move_to([xb - 0.6, 3.55, 0])
        self.play(FadeIn(barrier), FadeIn(screen), FadeIn(src), FadeIn(sl), FadeIn(bl), run_time=0.6)
        self.add(dots)
        self.say("单个光子落点随机，大量累积就重现波的强度分布。",
                 Succession(Reveal(dots, run_time=5.0, rate_func=lambda t: t ** 2.2),
                            AnimationGroup(Create(curve), FadeIn(cl), run_time=1.2)))
        self.clear_all()

        # 以太
        lattice = VGroup(*[Dot([x, y, 0], radius=0.025, color=GREY_B) for x in np.arange(-6.6, 6.7, 0.55)
                           for y in np.arange(-2.2, 3.7, 0.55)])
        sw = FunctionGraph(lambda x: 0.7 + 0.8 * np.sin(1.6 * x), x_range=[-6.5, 6.5, 0.02]).set_stroke(E_COL, 4)
        aq = T("以太？", 40, C_GREY)
        aq.add_background_rectangle(color=BG, opacity=0.9, buff=0.12)
        aq.move_to([0, 3.2, 0])
        self.say("波总要有介质吧？人们假想光在“以太”中传播。",
                 FadeIn(lattice, lag_ratio=0.002), Create(sw), FadeIn(aq), run_time=2.5)
        # 迈克耳孙—莫雷
        Bp = np.array([0, 0.7, 0])
        S = Bp + LEFT * 3.4
        M1 = Bp + RIGHT * 2.6
        M2 = Bp + UP * 2.6
        D = Bp + DOWN * 2.0
        beams = VGroup(Line(S, Bp), Line(Bp, M1), Line(Bp, M2), Line(Bp, D)).set_stroke(S_COL, 3)
        app = VGroup(beams,
                     Line(Bp + np.array([-0.4, -0.4, 0]), Bp + np.array([0.4, 0.4, 0])).set_stroke(C_BLUE, 5),
                     Line(M1 + DOWN * 0.45, M1 + UP * 0.45).set_stroke(GREY_A, 7),
                     Line(M2 + LEFT * 0.45, M2 + RIGHT * 0.45).set_stroke(GREY_A, 7),
                     Dot(S, radius=0.14, color=S_COL),
                     Square(0.4).move_to(D).set_fill(GREY_B, 1).set_stroke(width=0))
        fr = VGroup(*[Rectangle(width=0.2, height=0.7).set_fill(S_COL, 0.15 + 0.85 * np.cos(PI * i / 2) ** 2)
                      .set_stroke(width=0).move_to([4.0 + 0.2 * i, -1.6, 0]) for i in range(-3, 4)])
        frl = T("干涉条纹", 22, C_GREY).next_to(fr, UP, buff=0.18)
        wind = VGroup(*[Arrow([6.6, y, 0], [4.9, y, 0], buff=0, color=C_GREY, stroke_width=3) for y in (2.3, 2.75, 3.2)])
        wl = T("以太风？", 24, C_GREY).next_to(wind, LEFT, buff=0.2)
        tg = self.tag("1887 · 迈克耳孙 & 莫雷")
        self.play(FadeOut(sw), FadeOut(aq), lattice.animate.set_opacity(0.25), FadeIn(app), FadeIn(fr), FadeIn(frl),
                  FadeIn(wind), FadeIn(wl), FadeIn(tg), run_time=1.0)
        null = T("零结果", 36, K_COL, weight=BOLD).move_to([5.0, 0.4, 0])
        self.say("1887年，迈克耳孙和莫雷寻找“以太风”，一无所获。",
                 Succession(Rotate(app, angle=PI / 4, about_point=Bp, rate_func=there_and_back, run_time=3.0),
                            FadeIn(null, scale=1.3, run_time=0.6)))
        self.clear_all()

        pr = Proj(origin=(0, 0.6, 0), az=0.4, el=-0.7, scale=0.95)
        self.clock.set_value(0)
        wave = self.plane_wave(pr, amp=1.3, lam=4.0, c=1.0, x0=-6, x1=5.5)
        tg2 = self.tag("1905 · 爱因斯坦 · 狭义相对论")
        vac = T("真空：不需要任何介质", 26, C_GREY).to_corner(UR, buff=0.5)
        self.play(FadeIn(wave), run_time=0.6)
        self.say("1905年，狭义相对论表明：以太是多余的。",
                 FadeIn(tg2), FadeIn(vac), run_time=1.5)

        def ship(p, d, txt):
            tri = Triangle().scale(0.22).rotate(-PI / 2 if d > 0 else PI / 2).set_fill(GREY_A, 1).set_stroke(width=0).move_to(p)
            ar = Arrow(p + RIGHT * d * 0.3, p + RIGHT * d * 1.3, buff=0, color=C_GREY, stroke_width=4)
            vt = MathTex(txt, font_size=32, color=C_GREY).next_to(ar, UP, buff=0.08)
            lab = VGroup(T("测得", 24), MathTex("c", font_size=36)).arrange(RIGHT, buff=0.12)
            lab.next_to(tri, LEFT if d > 0 else RIGHT, buff=0.3)
            return VGroup(tri, ar, vt, lab)

        s1 = ship(np.array([-3.6, -1.7, 0]), 1, "v_1")
        s2 = ship(np.array([3.4, -1.7, 0]), -1, "v_2")
        self.say("真空光速对所有惯性观察者都相同：时空观将被改写。",
                 FadeIn(s1, shift=RIGHT * 0.4), FadeIn(s2, shift=LEFT * 0.4), run_time=1.5, extra=0.3)
        self.clear_all()
