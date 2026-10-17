# -*- coding: utf-8 -*-
"""
物理科普 · 第 01 集  黑洞：连光都逃不出的地方

渲染：
    PYTHONPATH=../common manim -ql --disable_caching scene.py Video    # 预览
    python ../common/build.py 01_黑洞                                    # 成品

单位约定：凡涉及黑洞几何处，均以史瓦西半径 rₛ = 1 为单位计算，再乘以屏幕比例尺。
"""
import sys
from style import *

# style.py 在导入时把分辨率强制设为 1080p30，会覆盖命令行的 -ql。
# 这里在预览模式下恢复低画质，保证预览渲染够快（成品 -qh 不受影响）。
_argv = " ".join(sys.argv)
if "-ql" in sys.argv or "--quality l" in _argv or "-q l" in _argv or "--quality=l" in _argv:
    config.pixel_width = 854
    config.pixel_height = 480
    config.frame_rate = 15

RNG = np.random.default_rng(7)


# ====================================================================== 通用小工具
def heat(x):
    """黑体/吸积盘风格的热色表，x ∈ [0,1]"""
    stops = ["#2a0802", "#8f2d08", "#e0701c", "#ffc35a", "#fff3d6"]
    x = float(np.clip(x, 0, 1)) * (len(stops) - 1)
    i = min(int(x), len(stops) - 2)
    return interpolate_color(ManimColor(stops[i]), ManimColor(stops[i + 1]), x - i)


def starfield(n=170, seed=3):
    rng = np.random.default_rng(seed)
    g = VGroup()
    for _ in range(n):
        d = Dot([rng.uniform(-7.2, 7.2), rng.uniform(-4.1, 4.1), 0],
                radius=rng.uniform(0.006, 0.02), color=WHITE)
        d.set_opacity(rng.uniform(0.12, 0.6))
        g.add(d)
    g.set_z_index(-10)
    return g


def label(text, size=26, color=C_WHITE, **kw):
    return T(text, size=size, color=color, **kw)


def ring_segments(center, a, b, n, bright_fn, width=8, keep=None, rot=0.0):
    """把椭圆 (a,b) 切成 n 段，每段按 bright_fn(θ) 着色；keep(θ) 决定保留哪些段"""
    g = VGroup()
    c = np.array(center)
    for k in range(n):
        t0, t1 = TAU * k / n, TAU * (k + 1) / n
        tm = 0.5 * (t0 + t1)
        if keep is not None and not keep(tm):
            continue
        p0 = c + np.array([a * np.cos(t0 + rot), b * np.sin(t0 + rot), 0])
        p1 = c + np.array([a * np.cos(t1 + rot), b * np.sin(t1 + rot), 0])
        br = bright_fn(tm)
        ln = Line(p0, p1, stroke_width=width, color=heat(br))
        ln.set_stroke(opacity=0.25 + 0.75 * br)
        g.add(ln)
    return g


def black_hole_icon(center=ORIGIN, R=1.15):
    """片头/片尾用的黑洞意象：阴影 + 光子环 + 吸积盘（远侧被透镜折到上方）"""
    c = np.array(center)
    back, front, lens, low = VGroup(), VGroup(), VGroup(), VGroup()
    radii = np.linspace(1.55, 3.3, 9)
    for a in radii:
        rad_fall = (1.55 / a) ** 1.1

        def br(t, rf=rad_fall):  # 左侧（θ≈π）朝向我们运动 → 更亮
            return float(np.clip(rf * (0.22 + 0.78 * ((1 - np.cos(t)) / 2) ** 2), 0, 1))
        back.add(ring_segments(c, a * R, 0.2 * a * R, 44, br, 9, keep=lambda t: np.sin(t) > 0))
        front.add(ring_segments(c, a * R, 0.2 * a * R, 44, br, 9, keep=lambda t: np.sin(t) <= 0))
    for a in np.linspace(1.12, 1.62, 6):   # 透镜像：盘的远侧出现在阴影上方
        rf = (1.12 / a) ** 1.5

        def br2(t, rf=rf):
            return float(np.clip(rf * (0.25 + 0.75 * ((1 - np.cos(t)) / 2) ** 2), 0, 1))
        lens.add(ring_segments(c, a * R, a * R * 0.93, 40, br2, 8, keep=lambda t: np.sin(t) > -0.05))
    for a in np.linspace(1.05, 1.16, 3):   # 次级像：阴影下方细弧
        low.add(ring_segments(c, a * R, a * R * 0.97, 40, lambda t: 0.35 * ((1 - np.cos(t)) / 2 + 0.3), 4,
                              keep=lambda t: np.sin(t) < 0))
    shadow = Circle(radius=R, color=BLACK, fill_color=BLACK, fill_opacity=1, stroke_width=0).move_to(c)
    pring = VGroup(
        Circle(radius=R * 1.03, stroke_color=C_GOLD, stroke_width=14, stroke_opacity=0.18),
        Circle(radius=R * 1.03, stroke_color="#ffe6b0", stroke_width=3, stroke_opacity=0.95),
    ).move_to(c)
    return VGroup(back, lens, low, shadow, pring, front)


# ====================================================================== 物理积分
def null_geodesic(p0, v0, rs=1.0, dl=0.01, nmax=6000, rmax=30.0, box=None):
    """史瓦西零测地线的轨道形状：r̈ = −(3/2) rₛ L² r/r⁵（与 u'' + u = (3/2) rₛ u² 等价）。
    返回 (点列, 是否被捕获)。"""
    p = np.array(p0, float)
    v = np.array(v0, float)
    v /= np.linalg.norm(v)
    L2 = (p[0] * v[1] - p[1] * v[0]) ** 2

    def acc(q):
        r = np.hypot(*q)
        return -1.5 * rs * L2 * q / r ** 5

    pts = [p.copy()]
    for _ in range(nmax):
        k1v = acc(p); k1p = v
        k2v = acc(p + 0.5 * dl * k1p); k2p = v + 0.5 * dl * k1v
        k3v = acc(p + 0.5 * dl * k2p); k3p = v + 0.5 * dl * k2v
        k4v = acc(p + dl * k3p); k4p = v + dl * k3v
        p = p + dl / 6 * (k1p + 2 * k2p + 2 * k3p + k4p)
        v = v + dl / 6 * (k1v + 2 * k2v + 2 * k3v + k4v)
        r = np.hypot(*p)
        if r < rs:
            pts.append(p * rs / r)
            return np.array(pts), True
        pts.append(p.copy())
        if r > rmax:
            break
        if box is not None and not (box[0] < p[0] < box[1] and box[2] < p[1] < box[3]):
            break
    return np.array(pts), False


def newton_traj(p0, v0, GM, Rp, dt=0.004, nmax=40000, box=(-7.6, 7.6, -3.2, 4.6)):
    p = np.array(p0, float)
    v = np.array(v0, float)
    pts = [p.copy()]
    for i in range(nmax):
        def a(q):
            return -GM * q / np.linalg.norm(q) ** 3
        k1v = a(p); k1p = v
        k2v = a(p + 0.5 * dt * k1p); k2p = v + 0.5 * dt * k1v
        k3v = a(p + 0.5 * dt * k2p); k3p = v + 0.5 * dt * k2v
        k4v = a(p + dt * k3p); k4p = v + dt * k3v
        p = p + dt / 6 * (k1p + 2 * k2p + 2 * k3p + k4p)
        v = v + dt / 6 * (k1v + 2 * k2v + 2 * k3v + k4v)
        if np.linalg.norm(p) < Rp and i > 10:
            pts.append(p / np.linalg.norm(p) * Rp)
            return np.array(pts), True
        pts.append(p.copy())
        if not (box[0] < p[0] < box[1] and box[2] < p[1] < box[3]):
            break
    return np.array(pts), False


def path_from(pts, center=ORIGIN, scale=1.0, step=1, **style):
    pts = np.asarray(pts)[::step]
    P = np.column_stack([pts[:, 0] * scale, pts[:, 1] * scale, np.zeros(len(pts))]) + np.array(center)
    m = VMobject(**style)
    m.set_points_as_corners(P)
    return m


def kepler_pos(t, a, e, P, ang, M0=0.0):
    M = TAU * t / P + M0
    E = M
    for _ in range(8):
        E = E - (E - e * np.sin(E) - M) / (1 - e * np.cos(E))
    x = a * (np.cos(E) - e)
    y = a * np.sqrt(1 - e * e) * np.sin(E)
    c, s = np.cos(ang), np.sin(ang)
    return np.array([c * x - s * y, s * x + c * y, 0])


# ====================================================================== 场景
class Video(Explainer):
    def construct(self):
        self.stars = starfield()
        self.add(self.stars)
        self.title_card("黑洞", "连光都逃不出的地方")
        self.intro()
        self.chapter("第一章", "逃逸速度与“暗星”")
        self.ch_escape()
        self.chapter("第二章", "事件视界")
        self.ch_horizon()
        self.chapter("第三章", "弯曲的光与轨道")
        self.ch_light()
        self.chapter("第四章", "冻结的时间，撕裂的潮汐")
        self.ch_time_tide()
        self.chapter("第五章", "诞生与证据")
        self.ch_evidence()
        self.chapter("第六章", "霍金辐射与奇点")
        self.ch_hawking()
        self.fade_all(keep=(self.stars,))
        self.end_card([
            "史瓦西半径 2GM/c²：太阳约 3 公里",
            "事件视界是单向边界，不是实体表面",
            "光子球 1.5 倍、最内稳定轨道 3 倍史瓦西半径",
            "远看下落者冻结变红，它自己照常穿过视界",
            "证据：恒星轨道、EHT 图像、引力波",
        ])

    def clean(self, run_time=0.6):
        self.fade_all(run_time=run_time, keep=(self.stars,))

    # ------------------------------------------------------------------ 片头
    def intro(self):
        bh = black_hole_icon(center=[0, 0.75, 0], R=1.05)
        self.say("宇宙中有一种地方，掉进去就再也出不来，连光也不例外。",
                 FadeIn(bh, scale=0.85), run_time=2.5)
        self.play(FadeOut(bh, scale=1.1), run_time=0.7)

    # ------------------------------------------------------------------ 第一章
    def ch_escape(self):
        Pc = np.array([-4.3, -1.55, 0])
        Rp = 0.85
        planet = VGroup(
            Circle(radius=Rp, fill_color="#2f6f9f", fill_opacity=1, stroke_color=C_BLUE, stroke_width=3),
            Arc(radius=Rp * 0.7, start_angle=0.4, angle=1.3, color="#7fc4e8", stroke_width=3).shift(LEFT * 0.1),
        ).move_to(Pc)
        GM = 0.5 * Rp          # 取逃逸速度 v_esc = √(2GM/R) = 1
        ang = np.deg2rad(52)
        speeds = [0.62, 0.8, 0.93, 1.07, 1.3]
        cols = [C_RED, C_PINK, C_GOLD, C_GREEN, C_TEAL]
        paths, dots = [], []
        for vv, col in zip(speeds, cols):
            pts, _ = newton_traj([0, Rp], [vv * np.cos(ang), vv * np.sin(ang)], GM, Rp,
                                 box=(-7.5 - Pc[0], 7.5 - Pc[0], -0.9 - Pc[1], 5.4 - Pc[1]))
            p = path_from(pts, Pc, step=3, stroke_color=col, stroke_width=3.5)
            paths.append(p)
            d = Dot(radius=0.06, color=col)
            d.add_updater(lambda m, p=p: m.move_to(p.get_end()))
            dots.append(d)
        legend = VGroup(
            VGroup(Line(ORIGIN, RIGHT * 0.5, color=C_RED, stroke_width=4), label("低于逃逸速度：落回", 24)).arrange(RIGHT, buff=0.2),
            VGroup(Line(ORIGIN, RIGHT * 0.5, color=C_GREEN, stroke_width=4), label("高于逃逸速度：飞离", 24)).arrange(RIGHT, buff=0.2),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.18).to_corner(UL, buff=0.5)
        self.say("要多快，石头才能一去不回？", FadeIn(planet), FadeIn(legend))
        self.add(*dots)
        self.say("慢了会落回；超过逃逸速度，就能永远飞离。",
                 LaggedStart(*[Create(p, rate_func=linear) for p in paths], lag_ratio=0.18), run_time=4.8)
        for d in dots:
            d.clear_updaters()
        f = eq(r"v_{\rm esc}=\sqrt{\frac{2GM}{r}}", 60).move_to([3.6, 2.6, 0])
        earth = VGroup(label("地球表面：", 28), eq(r"v_{\rm esc}\approx 11.2\ \mathrm{km/s}", 40)).arrange(RIGHT, buff=0.15)
        earth.next_to(f, DOWN, buff=0.45)
        self.say("逃逸速度取决于质量和半径，地球表面约 11.2 公里每秒。",
                 Write(f), FadeIn(earth, shift=UP * 0.2), run_time=2)
        self.play(*[FadeOut(m) for m in paths + dots + [planet, legend, earth]],
                  f.animate.move_to([-0.2, 3.2, 0]).scale(0.8), run_time=0.7)

        # --- 压缩星球：质量不变，半径缩小，逃逸速度上升
        rs_vis = 0.32
        R = ValueTracker(2.1)
        C1 = np.array([-3.6, 0.6, 0])
        star = always_redraw(lambda: Circle(
            radius=R.get_value(), stroke_color=C_GOLD, stroke_width=3,
            fill_color=interpolate_color(ManimColor("#f0a040"), ManimColor("#200800"),
                                         float(np.clip((rs_vis / R.get_value()) ** 3, 0, 1))),
            fill_opacity=1).move_to(C1))
        mass_lbl = label("质量 M 不变", 26, C_GREY).move_to([-3.6, -2.15, 0])
        base_y, Hbar, bx = -2.0, 4.0, 3.6

        def vfrac():
            return min(1.0, np.sqrt(rs_vis / R.get_value()))
        bar = always_redraw(lambda: Rectangle(
            width=0.8, height=max(0.01, Hbar * vfrac()), stroke_width=0,
            fill_color=interpolate_color(ManimColor(C_TEAL), ManimColor(C_RED), vfrac() ** 4),
            fill_opacity=0.9).move_to([bx, base_y + Hbar * vfrac() / 2, 0]))
        cline = DashedLine([bx - 1.0, base_y + Hbar, 0], [bx + 1.0, base_y + Hbar, 0], color=C_YELLOW)
        clab = label("光速 c", 26, C_YELLOW).next_to(cline, RIGHT, buff=0.15)
        axis = Line([bx - 1.0, base_y, 0], [bx + 1.0, base_y, 0], color=C_GREY)
        vlab = label("逃逸速度", 26).next_to(axis, DOWN, buff=0.15)
        num = always_redraw(lambda: VGroup(eq(r"v/c=", 34), DecimalNumber(vfrac(), num_decimal_places=2, font_size=34))
                            .arrange(RIGHT, buff=0.1).move_to([bx - 2.1, base_y + Hbar * vfrac(), 0]))
        self.say("把星球越压越小，逃逸速度就越来越大。",
                 Succession(AnimationGroup(FadeIn(star), FadeIn(mass_lbl), Create(axis), FadeIn(vlab), Create(cline),
                                           FadeIn(clab), FadeIn(bar), FadeIn(num), run_time=1.0),
                            R.animate(run_time=2.6).set_value(0.75)), run_time=3.6)
        rlab = eq(r"r=\frac{2GM}{c^2}", 48, C_YELLOW).next_to(C1 + np.array([0, -rs_vis, 0]), DOWN, buff=0.45)
        self.say("达到光速时，半径正好是 2GM/c²。",
                 Succession(R.animate(run_time=2.2).set_value(rs_vis), Write(rlab, run_time=0.8)), run_time=3.0)

        # --- 暗星：牛顿光微粒飞出又落回
        star.clear_updaters()
        dark = VGroup(star, rlab)
        self.play(*[FadeOut(m) for m in (bar, num, cline, clab, axis, vlab, mass_lbl, f)],
                  dark.animate.shift(RIGHT * 0.6), run_time=0.7)
        c0 = C1 + RIGHT * 0.6
        corp = VGroup()
        anims = []
        for k in range(10):
            th = TAU * k / 10 + 0.3
            u = np.array([np.cos(th), np.sin(th), 0])
            d = Dot(c0 + u * rs_vis, radius=0.05, color=C_YELLOW)
            corp.add(d)
            anims.append(d.animate(rate_func=there_and_back).move_to(c0 + u * (rs_vis + 1.3)))
        cards = VGroup(
            VGroup(label("米歇尔", 34, C_BLUE), label("1783", 30, C_GREY)).arrange(RIGHT, buff=0.3),
            VGroup(label("拉普拉斯", 34, C_BLUE), label("1796", 30, C_GREY)).arrange(RIGHT, buff=0.3),
            label("“暗星”：引力强到光也逃不掉", 30, C_WHITE),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.35).move_to([3.3, 1.5, 0])
        note = label("牛顿图像：光被当作普通粒子，先飞出，再落回", 24, C_GREY).move_to([-2.4, -2.15, 0])
        self.add(corp)
        self.say("1783 年米歇尔、1796 年拉普拉斯，都设想过这种“暗星”。",
                 LaggedStart(*[FadeIn(c, shift=RIGHT * 0.2) for c in cards], lag_ratio=0.4),
                 AnimationGroup(*anims), FadeIn(note), run_time=3)
        gr = VGroup(label("广义相对论：", 30, C_TEAL), label("不是“光飞不动”，而是时空本身被弯曲", 26, C_TEAL)
                    ).arrange(DOWN, aligned_edge=LEFT, buff=0.15).move_to([3.3, -0.6, 0])
        self.say("但这只是牛顿式类比；真正的黑洞属于广义相对论。",
                 FadeIn(gr, shift=UP * 0.2), AnimationGroup(*[
                     d.animate(rate_func=there_and_back).move_to(c0 + (d.get_center() - c0) * 4.0) for d in corp]),
                 run_time=3)
        self.clean()

    # ------------------------------------------------------------------ 第二章
    def ch_horizon(self):
        metric = eq(r"ds^2=-\Big(1-\frac{r_s}{r}\Big)c^2dt^2+\Big(1-\frac{r_s}{r}\Big)^{-1}dr^2+r^2d\Omega^2", 46)
        metric.move_to([0, 2.7, 0])
        who = label("卡尔·史瓦西  1916", 28, C_GREY).next_to(metric, DOWN, buff=0.35)
        self.say("1916 年，史瓦西解出了球对称天体外的时空。",
                 Write(metric), FadeIn(who), run_time=2.5)
        rs = eq(r"r_s=\frac{2GM}{c^2}", 64, C_YELLOW).move_to([0, 0.9, 0])
        sun = Circle(radius=1.0, fill_color="#f4b740", fill_opacity=1, stroke_color=C_GOLD).move_to([-3.6, -1.0, 0])
        earth = Circle(radius=0.6, fill_color="#2f6f9f", fill_opacity=1, stroke_color=C_BLUE).move_to([3.6, -1.0, 0])
        sl = label("太阳", 28).move_to([-3.6, 0.35, 0])
        el = label("地球", 28).move_to([3.6, 0.35, 0])
        sv = eq(r"r_s\approx 2.95\ \mathrm{km}", 40, C_GOLD).move_to([-3.6, -1.75, 0])
        ev = eq(r"r_s\approx 8.9\ \mathrm{mm}", 40, C_BLUE).move_to([3.6, -1.75, 0])
        nts = label("（示意，不按比例）", 22, C_GREY).move_to([0, -2.2, 0])
        self.say("其中的史瓦西半径：太阳约 3 公里，地球约 9 毫米。",
                 Succession(AnimationGroup(FadeOut(who), Write(rs), FadeIn(sun), FadeIn(earth), FadeIn(sl), FadeIn(el),
                                           run_time=1.2),
                            AnimationGroup(sun.animate.scale(0.05).set_fill(BLACK).set_stroke(C_GOLD, 2),
                                           earth.animate.scale(0.05).set_fill(BLACK).set_stroke(C_BLUE, 2),
                                           FadeIn(sv), FadeIn(ev), FadeIn(nts), run_time=2.2)), run_time=3.4)
        self.clean(0.5)

        # --- 事件视界：单向边界
        Ch = np.array([0, 0.6, 0])
        hz = DashedVMobject(Circle(radius=1.7, color=C_YELLOW, stroke_width=3), num_dashes=48).move_to(Ch)
        inside = Circle(radius=1.7, fill_color=BLACK, fill_opacity=1, stroke_width=0).move_to(Ch)
        hl = label("事件视界", 28, C_YELLOW).move_to(Ch + np.array([0, 2.15, 0]))
        a_in = Arrow(Ch + np.array([-4.6, 0.6, 0]), Ch + np.array([-0.7, 0.2, 0]), color=C_GREEN, buff=0, stroke_width=6)
        a_out = Arrow(Ch + np.array([0.5, -0.3, 0]), Ch + np.array([1.6, -0.6, 0]), color=C_RED, buff=0, stroke_width=6)
        cross = Cross(scale_factor=0.22, stroke_color=C_RED).move_to(Ch + np.array([1.85, -0.66, 0]))
        lin = label("可以进去", 26, C_GREEN).next_to(a_in, UP, buff=0.1)
        lout = label("出不来", 26, C_RED).move_to(Ch + np.array([3.0, -0.75, 0]))
        nomat = label("不是实体表面，这里空无一物", 24, C_GREY).move_to(Ch + np.array([3.7, 1.5, 0]))
        self.say("这个球面叫事件视界：不是实体表面，而是单向边界。",
                 FadeIn(inside), Create(hz), FadeIn(hl), GrowArrow(a_in), FadeIn(lin),
                 GrowArrow(a_out), Create(cross), FadeIn(lout), FadeIn(nomat), run_time=2.5)
        self.clean(0.5)

        # --- 时空图与光锥（入射爱丁顿–芬克尔斯坦坐标）
        X0, Y0, sx, sy = -5.7, -2.25, 2.2, 0.95
        rmax, tmax = 5.6, 6.2

        def P(r, t):
            return np.array([X0 + r * sx, Y0 + t * sy, 0])
        axr = Arrow(P(0, 0), P(rmax + 0.1, 0), buff=0, color=C_GREY, stroke_width=3, max_tip_length_to_length_ratio=0.03)
        axt = Arrow(P(0, 0), P(0, tmax), buff=0, color=C_GREY, stroke_width=3, max_tip_length_to_length_ratio=0.04)
        lr = label("到中心的距离 r", 24, C_GREY).next_to(P(rmax, 0), UP, buff=0.12).shift(LEFT * 0.6)
        lt = label("时间", 24, C_GREY).next_to(P(0, tmax), RIGHT, buff=0.15)
        sing = VMobject(stroke_color=C_RED, stroke_width=3)
        sing.set_points_as_corners([P(0.04 * ((-1) ** k), t) for k, t in enumerate(np.linspace(0, tmax - 0.4, 40))])
        hline = DashedLine(P(1, 0), P(1, tmax - 0.3), color=C_YELLOW, stroke_width=3)
        hlab = label("视界", 24, C_YELLOW).next_to(P(1, tmax - 0.3), UP, buff=0.08)
        coord = label("坐标：入射爱丁顿–芬克尔斯坦", 20, C_GREY).move_to([4.9, 3.72, 0])
        rays = VGroup()
        for C in np.arange(-3.0, 9.0, 1.2):     # 真实出射光线 t* = r + 2 ln|r−1| + C
            for side in (0, 1):
                rr = np.linspace(1.004, rmax, 300) if side == 0 else np.linspace(0.001, 0.996, 300)
                tt = rr + 2 * np.log(np.abs(rr - 1)) + C
                ok = (tt >= 0) & (tt <= tmax - 0.35)
                if ok.sum() < 3:
                    continue
                m = VMobject(stroke_color=C_GOLD, stroke_width=1.6, stroke_opacity=0.45)
                m.set_points_as_corners([P(r, t) for r, t in zip(rr[ok], tt[ok])])
                rays.add(m)
        for C in np.arange(0.6, 12, 1.2):       # 入射光线 t* = −r + C
            r1 = max(0, C - (tmax - 0.35))
            r2 = min(rmax, C)
            if r2 - r1 > 0.05:
                rays.add(Line(P(r2, C - r2), P(r1, C - r1), stroke_color=C_BLUE, stroke_width=1.4, stroke_opacity=0.3))

        def cone(r, t, L=0.62, alpha=0.4):
            ap = P(r, t)
            vin = np.array([-sx, sy, 0]); vin /= np.linalg.norm(vin)
            vout = np.array([(r - 1) * sx, (r + 1) * sy, 0]); vout /= np.linalg.norm(vout)
            tri = Polygon(ap, ap + L * vin, ap + L * vout, stroke_width=0, fill_color=C_TEAL, fill_opacity=alpha)
            e1 = Line(ap, ap + L * vin, color=C_BLUE, stroke_width=3)
            e2 = Line(ap, ap + L * vout, color=C_GOLD, stroke_width=3)
            return VGroup(tri, e1, e2, Dot(ap, radius=0.035, color=WHITE))

        t_live, t_stat = 3.4, 1.2
        rv = ValueTracker(4.6)
        live = always_redraw(lambda: cone(rv.get_value(), t_live, L=0.85, alpha=0.6))
        lgd = VGroup(
            VGroup(Line(ORIGIN, RIGHT * 0.45, color=C_GOLD, stroke_width=4), label("向外的光", 22)).arrange(RIGHT, buff=0.15),
            VGroup(Line(ORIGIN, RIGHT * 0.45, color=C_BLUE, stroke_width=4), label("向内的光", 22)).arrange(RIGHT, buff=0.15),
            VGroup(Square(0.3, fill_color=C_TEAL, fill_opacity=0.5, stroke_width=0), label("物体可走的未来", 22)).arrange(RIGHT, buff=0.15),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
        lgd.add_background_rectangle(color=BG, opacity=0.85, buff=0.12).move_to([5.25, 2.85, 0])
        lgd.set_z_index(20)
        self.say("时空图中，光的方向构成“光锥”，物体只能在锥内运动。",
                 GrowArrow(axr), GrowArrow(axt), FadeIn(lr), FadeIn(lt), Create(hline), FadeIn(hlab),
                 Create(sing), FadeIn(coord), FadeIn(rays), FadeIn(live), FadeIn(lgd), run_time=2.5)
        statics = VGroup(*[cone(r, t_stat) for r in (4.6, 3.2, 2.2, 1.5)])
        self.say("越靠近视界，光锥越向黑洞倾斜。",
                 rv.animate.set_value(1.25), LaggedStart(*[FadeIn(s) for s in statics], lag_ratio=0.3),
                 run_time=3.7)
        hc = cone(1.0, t_stat)
        hnote = label("向外的光：r 不变", 22, C_GOLD).next_to(P(1, t_live + 0.55), RIGHT, buff=0.15)
        self.say("在视界上，“向外”的光只能停在原地。",
                 rv.animate.set_value(1.0), FadeIn(hc), FadeIn(hnote), Indicate(hline, color=C_YELLOW), run_time=2.5)
        ic = cone(0.55, t_stat)
        shade = Rectangle(width=sx * 1.0, height=(tmax - 0.3) * sy, stroke_width=0,
                          fill_color=C_RED, fill_opacity=0.10).move_to(P(0.5, (tmax - 0.3) / 2))
        inote = label("视界内：一切未来都指向更小的 r", 22, C_RED).next_to(P(1.1, 0.3), RIGHT, buff=0.1)
        self.say("视界以内，一切未来都指向更小的半径，就像明天必然到来。",
                 rv.animate.set_value(0.5), FadeIn(ic), FadeIn(shade), FadeIn(inote), run_time=3.5)
        live.clear_updaters()
        self.clean()

    # ------------------------------------------------------------------ 第三章
    def ch_light(self):
        Cb = np.array([0.4, 0.65, 0])
        S = 0.55
        note = label("* 本章数值针对不旋转黑洞", 20, C_GREY).to_corner(UR, buff=0.3)
        hole = Circle(radius=S, fill_color=BLACK, fill_opacity=1, stroke_color=C_GREY, stroke_width=2).move_to(Cb)
        hole.set_z_index(5)
        rays, caps = VGroup(), []
        bs = [-4.6, -3.7, -3.0, -2.5, -2.0, -1.5, -1.0, -0.5, 0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 2.75, 3.0, 3.7, 4.6]
        xl = (-7.4 - Cb[0]) / S
        box = (xl - 0.5, (7.6 - Cb[0]) / S, (-2.55 - Cb[1]) / S, (3.95 - Cb[1]) / S)
        for b in bs:
            pts, cap = null_geodesic([xl, b], [1, 0], dl=0.02, nmax=4000, rmax=60, box=box)
            col = "#b05050" if cap else C_BLUE
            rays.add(path_from(pts, Cb, S, step=2, stroke_color=col, stroke_width=2.2,
                               stroke_opacity=0.85 if cap else 0.9))
            caps.append(cap)
        self.say("视界之外，光线被引力弯曲：这些是广义相对论算出的光路。",
                 FadeIn(hole), FadeIn(note), LaggedStart(*[Create(r, rate_func=linear) for r in rays], lag_ratio=0.04),
                 run_time=4)
        bc = 1.5 * np.sqrt(3)
        bcirc = DashedVMobject(Circle(radius=bc * S, color=C_YELLOW, stroke_width=2.5), num_dashes=40).move_to(Cb)
        bx = -5.6
        bline = DoubleArrow([bx, Cb[1], 0], [bx, Cb[1] + bc * S, 0], buff=0, color=C_YELLOW, stroke_width=3,
                            tip_length=0.15)
        blab = eq(r"b_c=\tfrac{3\sqrt3}{2}\,r_s\approx 2.6\,r_s", 34, C_YELLOW)
        blab.add_background_rectangle(color=BG, opacity=0.85, buff=0.08).move_to([-5.2, 2.75, 0])
        bname = label("瞄准距离 b", 22, C_YELLOW).next_to(bline, RIGHT, buff=0.1)
        bname.add_background_rectangle(color=BG, opacity=0.85, buff=0.05)
        guide = DashedLine([bx, Cb[1] + bc * S, 0], [Cb[0], Cb[1] + bc * S, 0], color=C_YELLOW, stroke_width=1.5, stroke_opacity=0.6)
        capg = VGroup(*[r for r, c in zip(rays, caps) if c])
        self.say("瞄准距离小于约 2.6 倍史瓦西半径的光，会被吞没。",
                 Create(bcirc), GrowFromCenter(bline), Create(guide), Write(blab), FadeIn(bname),
                 *[Indicate(r, color=C_RED, scale_factor=1.0) for r in capg], run_time=2.5)

        # --- 放大：光子球
        S2 = 1.0
        self.play(FadeOut(rays), FadeOut(bcirc), FadeOut(bline), FadeOut(blab), FadeOut(guide), FadeOut(bname),
                  hole.animate.scale(S2 / S), run_time=0.8)
        ps = DashedVMobject(Circle(radius=1.5 * S2, color=C_GOLD, stroke_width=2.5), num_dashes=50).move_to(Cb)
        psl = eq(r"1.5\,r_s", 34, C_GOLD).move_to(Cb + np.array([1.6, 1.3, 0]))
        psn = label("光子球", 26, C_GOLD).next_to(psl, RIGHT, buff=0.15)
        ang = ValueTracker(0)
        ph = always_redraw(lambda: Dot(Cb + 1.5 * S2 * np.array([np.cos(ang.get_value()), np.sin(ang.get_value()), 0]),
                                       radius=0.07, color=C_YELLOW))
        trail = TracedPath(ph.get_center, dissipating_time=0.5, stroke_color=C_YELLOW, stroke_width=4)
        hl = label("视界", 22, C_GREY).move_to(Cb).set_z_index(6)
        self.add(trail)
        self.say("在 1.5 倍史瓦西半径处，光能绕黑洞转圈：光子球。",
                 Create(ps), FadeIn(psl), FadeIn(psn), FadeIn(ph), FadeIn(hl),
                 ang.animate(rate_func=linear).set_value(2 * TAU), run_time=4)
        self.remove(trail)
        ph.clear_updaters()
        p_in, _ = null_geodesic([1.5, 0], [-0.012, 1], dl=0.01, nmax=6000, rmax=12)
        p_out, _ = null_geodesic([1.5, 0], [0.012, 1], dl=0.01, nmax=6000, rmax=12,
                                 box=(-7.0 - Cb[0], 7.0 - Cb[0], -2.5 - Cb[1], 3.9 - Cb[1]))
        pin = path_from(p_in, Cb, S2, step=2, stroke_color=C_RED, stroke_width=3)
        pout = path_from(p_out, Cb, S2, step=2, stroke_color=C_TEAL, stroke_width=3)
        d1 = Dot(radius=0.06, color=C_RED); d1.add_updater(lambda m: m.move_to(pin.get_end()))
        d2 = Dot(radius=0.06, color=C_TEAL); d2.add_updater(lambda m: m.move_to(pout.get_end()))
        self.remove(ph)
        self.add(d1, d2)
        ul = VGroup(label("稍偏向内 → 坠入", 24, C_RED), label("稍偏向外 → 逃离", 24, C_TEAL)).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
        ul.to_corner(UL, buff=0.5)
        self.say("但这个轨道不稳定，稍有偏离，光就会坠入或逃离。",
                 Create(pin, rate_func=linear), Create(pout, rate_func=linear), FadeIn(ul), run_time=4)
        d1.clear_updaters(); d2.clear_updaters()
        self.play(FadeOut(pin), FadeOut(pout), FadeOut(d1), FadeOut(d2), FadeOut(ul), run_time=0.5)

        # --- ISCO 与吸积盘
        isco = Circle(radius=3 * S2, color=C_GREEN, stroke_width=3).move_to(Cb)
        il = eq(r"3\,r_s", 34, C_GREEN).move_to(Cb + np.array([2.9, 2.4, 0]))
        iln = label("最内稳定圆轨道", 24, C_GREEN).next_to(il, RIGHT, buff=0.15)
        om = ValueTracker(0)
        mo = ValueTracker(0)
        movers = VGroup()
        for k, rr in enumerate([3.0, 3.6, 4.3, 5.0, 5.7]):
            for j in range(3):
                ph0 = TAU * j / 3 + k
                w = rr ** -1.5 * 6
                d = Dot(radius=0.05, color="#ffe0a0")
                d.add_updater(lambda m, rr=rr, ph0=ph0, w=w: m.move_to(
                    Cb + np.array([rr * np.cos(ph0 + w * om.get_value()), 0.3 * rr * np.sin(ph0 + w * om.get_value()), 0]))
                    .set_opacity(mo.get_value()))
                movers.add(d)
        radii = np.linspace(3.0, 5.9, 9)

        def dop(t, a):   # 左侧（θ≈π）朝向观众运动：多普勒提升
            return float(np.clip((3.0 / a) ** 0.8 * (0.12 + 0.88 * ((1 - np.cos(t)) / 2) ** 2.2), 0, 1))

        def build(fn, keepf):
            return VGroup(*[ring_segments(Cb, a, 0.3 * a, 56, (lambda t, a=a: fn(t, a)), 9, keep=keepf) for a in radii])
        back_u = build(lambda t, a: 0.5 * (3.0 / a) ** 0.8, lambda t: np.sin(t) > 0)
        front_u = build(lambda t, a: 0.5 * (3.0 / a) ** 0.8, lambda t: np.sin(t) <= 0)
        back_d = build(dop, lambda t: np.sin(t) > 0)
        front_d = build(dop, lambda t: np.sin(t) <= 0)
        back_u.set_z_index(1); front_u.set_z_index(8); back_d.set_z_index(1); front_d.set_z_index(8)
        movers.set_z_index(9)
        self.add(movers)
        self.say("物质的最内稳定圆轨道在 3 倍处，大致是吸积盘的内边缘。",
                 Succession(
                     AnimationGroup(Create(isco), FadeIn(il), FadeIn(iln), run_time=1.3),
                     Wait(0.8),
                     AnimationGroup(isco.animate.stretch(0.3, 1), FadeOut(il), FadeOut(iln), FadeOut(ps), FadeOut(psl),
                                    FadeOut(psn), FadeOut(hl), run_time=1.1),
                     AnimationGroup(FadeIn(back_u), FadeIn(front_u), FadeOut(isco), mo.animate.set_value(1),
                                    om.animate(rate_func=linear).set_value(1.6), run_time=1.8)),
                 run_time=5.0)
        l1 = label("朝我们运动 · 更亮", 24, "#ffd27a").move_to(Cb + np.array([-3.7, 2.4, 0]))
        l2 = label("远离我们 · 更暗", 24, "#c06030").move_to(Cb + np.array([3.7, 2.4, 0]))
        v1 = Arrow(Cb + np.array([-4.6, 1.5, 0]), Cb + np.array([-4.6, 0.5, 0]), buff=0, color="#ffd27a", stroke_width=4)
        v2 = Arrow(Cb + np.array([4.6, 0.5, 0]), Cb + np.array([4.6, 1.5, 0]), buff=0, color="#c06030", stroke_width=4)
        self.say("盘中朝我们运动的一侧，因相对论聚束而更亮。",
                 Transform(back_u, back_d), Transform(front_u, front_d), FadeIn(l1), FadeIn(l2),
                 om.animate(rate_func=linear).set_value(4.5), run_time=4)
        for m in movers:
            m.clear_updaters()
        self.clean()

    # ------------------------------------------------------------------ 第四章
    def ch_time_tide(self):
        # --- 三只钟
        bh = Circle(radius=2.4, fill_color=BLACK, fill_opacity=1, stroke_color=C_YELLOW, stroke_width=2).move_to([-8.3, 0.6, 0])
        bhl = label("黑洞", 24, C_GREY).move_to([-6.4, 3.0, 0])
        specs = [(-4.6, 1.05, C_RED), (-0.9, 2.0, C_GOLD), (3.9, 10.0, C_BLUE)]
        tt = ValueTracker(0)
        clocks = VGroup()
        waves = VGroup()
        Rc = 0.8
        for x, r, col in specs:
            rate = np.sqrt(1 - 1 / r)
            c = np.array([x, 1.05, 0])
            face = Circle(radius=Rc, color=C_WHITE, stroke_width=3).move_to(c)
            ticks = VGroup(*[Line(c + (Rc - 0.12) * np.array([np.cos(a), np.sin(a), 0]), c + Rc * np.array([np.cos(a), np.sin(a), 0]),
                                  stroke_width=2, color=C_GREY) for a in np.arange(0, TAU, TAU / 12)])
            hand = always_redraw(lambda c=c, rate=rate, col=col: Line(
                c, c + 0.65 * np.array([np.cos(PI / 2 - rate * tt.get_value()), np.sin(PI / 2 - rate * tt.get_value()), 0]),
                color=col, stroke_width=5))
            hub = Dot(c, radius=0.05, color=col)
            rl = eq(r"r=%s\,r_s" % (f"{r:g}"), 32).next_to(face, DOWN, buff=0.15)
            rt = eq(r"\times %.2f" % rate, 34, col).next_to(face, RIGHT, buff=0.2)
            clocks.add(VGroup(face, ticks, hand, hub, rl, rt))
            lam = 0.38 / rate
            w = FunctionGraph(lambda X, lam=lam, x=x: -1.6 + 0.22 * np.sin(TAU * (X - x) / lam),
                              x_range=[x - 1.3, x + 1.3, 0.02], color=col, stroke_width=3)
            waves.add(w)
        f = eq(r"\frac{d\tau}{dt}=\sqrt{1-\frac{r_s}{r}}", 48).move_to([1.3, 3.2, 0])
        self.say("越深入引力场，时间越慢：视界旁悬停的钟，远看几乎停住。",
                 FadeIn(bh), FadeIn(bhl), FadeIn(clocks), Write(f), tt.animate(rate_func=linear).set_value(9), run_time=5)
        wl = label("同样的光，传到远处时的波长", 22, C_GREY).move_to([1.3, -2.2, 0])
        self.say("那里发出的光波长被拉长，变红变暗：引力红移。",
                 LaggedStart(*[Create(w) for w in waves], lag_ratio=0.25), FadeIn(wl),
                 tt.animate(rate_func=linear).set_value(16), run_time=4)
        for c in clocks:
            c[2].clear_updaters()
        self.clean(0.5)

        # --- 远处看 vs 飞船自己
        def ship():
            nose = Polygon([-0.2, 0, 0], [0.05, 0.13, 0], [0.05, -0.13, 0], fill_color=C_WHITE, fill_opacity=1, stroke_width=0)
            body = Rectangle(width=0.36, height=0.18, fill_color=C_WHITE, fill_opacity=1, stroke_width=0).move_to([0.23, 0, 0])
            fin = Polygon([0.3, 0.09, 0], [0.42, 0.2, 0], [0.42, 0.09, 0], fill_color=C_WHITE, fill_opacity=1, stroke_width=0)
            fin2 = fin.copy().flip(RIGHT, about_point=ORIGIN)
            return VGroup(nose, body, fin, fin2)
        rows = []
        for y, txt in ((1.9, "远处的人看到的"), (-0.9, "飞船自己经历的")):
            hz = DashedLine([-3.2, y - 1.0, 0], [-3.2, y + 1.0, 0], color=C_YELLOW)
            dark = VGroup(*[Rectangle(width=0.6, height=2.0, stroke_width=0, fill_color=BLACK,
                                      fill_opacity=0.25 + 0.12 * k).move_to([-3.5 - 0.6 * k, y, 0]) for k in range(7)])
            lt = label(txt, 26, C_TEAL).move_to([3.2, y + 0.8, 0])
            hzl = label("视界", 20, C_YELLOW).next_to(hz, UP, buff=0.05)
            bhn = label("黑洞", 22, C_GREY).move_to([-5.6, y + 0.75, 0])
            rows.append(VGroup(dark, hz, lt, hzl, bhn))
        eye = label("观察者", 22, C_GREY).move_to([6.3, 1.9 - 0.45, 0])
        eyed = Dot([6.3, 1.9, 0], color=C_GREY)
        s1t = ValueTracker(0)

        def ship1():
            s = s1t.get_value()
            m = ship().move_to([-2.85 + 7.0 * np.exp(-3.6 * s), 1.9, 0])
            m.set_fill(interpolate_color(ManimColor(C_WHITE), ManimColor(C_RED), min(1, 1.3 * s)),
                       opacity=max(0.0, 1 - s ** 1.6))
            return m
        sh1 = always_redraw(ship1)
        self.say("远处的人看到下落的飞船越来越慢、越红，最后淡出。",
                 FadeIn(rows[0]), FadeIn(eye), FadeIn(eyed), FadeIn(sh1),
                 s1t.animate(rate_func=linear).set_value(1), run_time=5)
        s2t = ValueTracker(0)
        sh2 = always_redraw(lambda: ship().move_to([4.3 - 9.0 * s2t.get_value() ** 1.7, -0.9, 0]))
        tau = always_redraw(lambda: VGroup(label("飞船的钟", 22, C_GREY), DecimalNumber(3.0 * s2t.get_value(), num_decimal_places=2,
                                                                                        font_size=30)).arrange(RIGHT, buff=0.15).move_to([3.2, -1.75, 0]))
        cross = label("越过视界的那一刻：本地看并无特别之处", 22, C_GREY).move_to([-2.0, -2.25, 0])
        self.say("但飞船自己会在有限时间内穿过视界。",
                 FadeIn(rows[1]), FadeIn(sh2), FadeIn(tau), s2t.animate(rate_func=linear).set_value(1),
                 Succession(Wait(2.6), FadeIn(cross, run_time=0.8)), run_time=4)
        sh1.clear_updaters(); sh2.clear_updaters(); tau.clear_updaters()
        self.clean(0.5)

        # --- 潮汐：面条化
        Cb = np.array([-5.0, 0.6, 0])
        hole = Circle(radius=0.5, fill_color=BLACK, fill_opacity=1, stroke_color=C_YELLOW, stroke_width=2).move_to(Cb)
        glow = Circle(radius=0.62, stroke_color=C_GOLD, stroke_width=8, stroke_opacity=0.25).move_to(Cb)
        base = VGroup(Circle(radius=0.38, fill_color=C_TEAL, fill_opacity=0.85, stroke_color=WHITE, stroke_width=2),
                      Line(LEFT * 0.38, RIGHT * 0.38, color=WHITE, stroke_width=2),
                      Line(UP * 0.38, DOWN * 0.38, color=WHITE, stroke_width=2))
        dd = ValueTracker(9.0)

        def body():
            d = dd.get_value()
            s = min(1 + 9.0 / d ** 3, 6.0)
            return base.copy().stretch(s, 0).stretch(1 / np.sqrt(s), 1).move_to(Cb + np.array([d, 0, 0]))
        obj = always_redraw(body)
        p = Cb + np.array([5.5, 0, 0])
        arrs = VGroup(
            Arrow(p + LEFT * 0.42, p + LEFT * 1.25, buff=0, color=C_RED, stroke_width=5),
            Arrow(p + RIGHT * 0.42, p + RIGHT * 0.85, buff=0, color=C_RED, stroke_width=5),
            Arrow(p + UP * 0.95, p + UP * 0.45, buff=0, color=C_BLUE, stroke_width=5),
            Arrow(p + DOWN * 0.95, p + DOWN * 0.45, buff=0, color=C_BLUE, stroke_width=5),
        )
        tl = VGroup(label("纵向：被拉长", 26, C_RED), label("横向：被挤压", 26, C_BLUE)).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
        tl.move_to([3.6, 2.6, 0])
        self.play(FadeIn(hole), FadeIn(glow), FadeIn(obj), run_time=0.6)
        self.say("潮汐力：近端引力更强，物体被纵向拉长、横向挤压。",
                 Succession(dd.animate(run_time=1.0).set_value(5.5),
                            AnimationGroup(LaggedStart(*[GrowArrow(a) for a in arrs], lag_ratio=0.15), FadeIn(tl), run_time=1.3),
                            Wait(0.4),
                            AnimationGroup(FadeOut(arrs), dd.animate(rate_func=rate_functions.ease_in_quad).set_value(0.78),
                                           run_time=2.5)), run_time=5.2)
        obj.clear_updaters()
        self.clean(0.5)

        # --- 小黑洞 vs 超大质量黑洞（视界处的潮汐）
        f = eq(r"\Delta a\approx\frac{2GM\,L}{r^3}\;\;\Rightarrow\;\;\Delta a(r_s)\propto\frac{1}{M^2}", 42).move_to([0, 3.2, 0])
        lc = np.array([-3.6, 0.5, 0])
        small = VGroup(Circle(radius=0.35, fill_color=BLACK, fill_opacity=1, stroke_color=C_YELLOW, stroke_width=2).move_to(lc + LEFT * 1.2),
                       base.copy().stretch(4.5, 0).stretch(0.47, 1).move_to(lc + RIGHT * 0.9))
        hz2 = ArcBetweenPoints([2.2, -0.6, 0], [2.2, 1.6, 0], angle=-0.25, color=C_YELLOW, stroke_width=3)
        big = VGroup(hz2, base.copy().move_to([3.6, 0.5, 0]))
        hz2l = label("视界（几乎是平的）", 20, C_YELLOW).next_to(hz2, DOWN, buff=0.1)
        hdr1 = label("10 倍太阳质量", 28, C_GOLD).move_to([-3.6, 1.9, 0])
        hdr2 = label("400 万倍太阳质量", 28, C_GOLD).move_to([3.6, 1.9, 0])
        v1 = VGroup(eq(r"\approx 2\times10^{8}\ \mathrm{m/s^2}", 34), label("约两千万倍重力加速度", 24, C_RED)).arrange(DOWN, buff=0.12).move_to([-3.6, -1.4, 0])
        v2 = VGroup(eq(r"\approx 1\times10^{-3}\ \mathrm{m/s^2}", 34), label("约万分之一倍重力加速度", 24, C_GREEN)).arrange(DOWN, buff=0.12).move_to([3.6, -1.4, 0])
        cap = label("视界处，2 米长物体两端的加速度差", 22, C_GREY).move_to([0, 2.45, 0])
        sep = DashedLine([0, 1.8, 0], [0, -2.0, 0], color=C_GREY, stroke_opacity=0.5)
        self.say("黑洞越小，视界处潮汐越强；超大质量黑洞的视界处几乎无感。",
                 Write(f), FadeIn(cap), FadeIn(small), FadeIn(big), FadeIn(hz2l), FadeIn(hdr1), FadeIn(hdr2),
                 FadeIn(v1), FadeIn(v2), Create(sep), run_time=2.5)
        self.clean(0.5)

        # --- 不会“吸”：太阳换成同质量黑洞，地球轨道不变
        Cs = np.array([0, 0.6, 0])
        sun = Circle(radius=0.55, fill_color="#f4b740", fill_opacity=1, stroke_color=C_GOLD).move_to(Cs)
        orbit = DashedVMobject(Circle(radius=2.6, color=C_GREY, stroke_width=2), num_dashes=60).move_to(Cs)
        th = ValueTracker(0)
        earth = always_redraw(lambda: Dot(Cs + 2.6 * np.array([np.cos(th.get_value()), np.sin(th.get_value()), 0]),
                                          radius=0.12, color=C_BLUE))
        fl = eq(r"F=\frac{GMm}{r^2}", 44).move_to([4.8, 2.9, 0])
        fn = label("只取决于质量 M", 24, C_GREY).next_to(fl, DOWN, buff=0.15)
        bhl = label("同质量的黑洞", 24, C_YELLOW).move_to(Cs + np.array([0, -0.55, 0]))
        same = label("地球轨道：不变", 26, C_GREEN).move_to([-4.6, 2.9, 0])
        self.say("在远处，黑洞的引力和同质量恒星一样，它并不会“吸”东西。",
                 Succession(AnimationGroup(FadeIn(sun), Create(orbit), FadeIn(earth), FadeIn(fl), FadeIn(fn), run_time=1.3),
                            Wait(0.5),
                            AnimationGroup(sun.animate.scale(0.09).set_fill(BLACK).set_stroke(C_YELLOW, 3), FadeIn(bhl),
                                           FadeIn(same), run_time=1.8)),
                 th.animate.set_value(TAU * 1.15), run_time=6, rate_func=linear)
        earth.clear_updaters()
        self.clean()

    # ------------------------------------------------------------------ 第五章
    def ch_evidence(self):
        # --- 恒星坍缩
        Cs = np.array([-3.6, 0.6, 0])
        layers = [(2.3, "#c0392b", "H"), (1.85, "#e67e22", "He"), (1.45, "#f1c40f", "C"),
                  (1.1, "#7fb069", "O"), (0.78, "#5dade2", "Si"), (0.45, "#9b9b9b", "Fe")]
        onion = VGroup(*[Circle(radius=r, fill_color=c, fill_opacity=0.9, stroke_color=BLACK, stroke_width=1).move_to(Cs)
                         for r, c, _ in layers])
        tags = VGroup(*[label(n, 20, BLACK if n != "Fe" else WHITE).move_to(Cs + np.array([0, r - 0.17 if n != "Fe" else 0, 0]))
                        for (r, c, n) in layers])
        core = onion[-1]
        flash = Circle(radius=0.2, stroke_color=WHITE, stroke_width=6).move_to(Cs)
        bhole = VGroup(Circle(radius=0.16, fill_color=BLACK, fill_opacity=1, stroke_color=C_GOLD, stroke_width=2),
                       Circle(radius=0.24, stroke_color=C_GOLD, stroke_width=6, stroke_opacity=0.3)).move_to(Cs)
        self.add(flash.set_stroke(opacity=0))
        self.say("大质量恒星燃尽后，核心在自身引力下坍缩。",
                 Succession(AnimationGroup(FadeIn(onion), FadeIn(tags), run_time=0.8),
                            AnimationGroup(core.animate.scale(0.12).set_fill(WHITE), FadeOut(tags[-1]), run_time=1.3),
                            AnimationGroup(*[m.animate.scale(2.4).set_opacity(0) for m in list(onion[:-1]) + list(tags[:-1])],
                                           flash.animate.set_stroke(opacity=1).scale(16).set_stroke(opacity=0),
                                           FadeOut(core), FadeIn(bhole), run_time=1.7)), run_time=3.8)
        # 残骸质量数轴
        nl = NumberLine(x_range=[0, 4.5, 1], length=7.0, include_numbers=False, color=C_GREY).move_to([3.0, -0.6, 0])
        nums = VGroup(*[eq(str(k), 30, C_GREY).next_to(nl.n2p(k), DOWN, buff=0.15) for k in range(5)])
        unit = label("核心质量（太阳质量）", 22, C_GREY).next_to(nums, DOWN, buff=0.15)

        def band(a, b, col, op):
            return Rectangle(width=nl.n2p(b)[0] - nl.n2p(a)[0], height=0.5, stroke_width=0, fill_color=col,
                             fill_opacity=op).move_to([(nl.n2p(a)[0] + nl.n2p(b)[0]) / 2, nl.get_center()[1] + 0.35, 0])
        ns = band(1.1, 2.0, C_TEAL, 0.7)
        unc = band(2.0, 3.0, C_GREY, 0.45)
        bhb = band(3.0, 4.5, C_PURPLE, 0.75)
        l_ns = label("中子星", 26, C_TEAL).next_to(ns, UP, buff=0.15)
        l_unc = label("上限所在", 22, C_WHITE).move_to(unc)
        l_bh = label("黑洞", 26, C_PURPLE).next_to(bhb, UP, buff=0.15)
        hdr = label("中子星质量上限 ≈ 2–3 个太阳质量", 28, C_WHITE).move_to([3.0, 1.6, 0])
        self.say("若核心超过中子星的质量上限，约 2 到 3 个太阳质量，就成为黑洞。",
                 Create(nl), FadeIn(nums), FadeIn(unit), FadeIn(hdr), FadeIn(ns), FadeIn(l_ns), FadeIn(unc), FadeIn(l_unc),
                 FadeIn(bhb), FadeIn(l_bh), run_time=2.5)
        self.clean(0.5)

        # --- 星系中心的超大质量黑洞
        Cg = np.array([-0.6, 0.6, 0])
        rng = np.random.default_rng(11)
        gal = VGroup()
        for arm in range(2):
            for i in range(200):
                t = rng.uniform(0.2, 3.3)
                r = 0.6 * np.exp(0.5 * t) + rng.normal(0, 0.15)
                a = t + arm * PI + rng.normal(0, 0.16)
                pt_ = Cg + np.array([r * np.cos(a), 0.5 * r * np.sin(a), 0])
                d = Dot(pt_, radius=rng.uniform(0.012, 0.032), color=interpolate_color(ManimColor(C_BLUE), WHITE, rng.uniform(0, 1)))
                d.set_opacity(rng.uniform(0.3, 0.9))
                gal.add(d)
        gal.rotate(0.25, about_point=Cg)
        bulge = VGroup(*[Ellipse(width=0.9 * k, height=0.5 * k, stroke_width=0, fill_color="#ffe9b0", fill_opacity=0.12).move_to(Cg)
                         for k in (1, 1.6, 2.3)])
        cdot = Dot(Cg, radius=0.07, color=BLACK).set_stroke(C_YELLOW, 2)
        smbh = VGroup(label("超大质量黑洞", 26, C_YELLOW), eq(r"10^{6}\sim10^{10}\,M_\odot", 34, C_YELLOW)).arrange(DOWN, buff=0.1)
        smbh.move_to([5.0, 3.0, 0])
        pt = Line(smbh.get_bottom() + DOWN * 0.05, Cg + np.array([0.12, 0.08, 0]), color=C_YELLOW, stroke_width=2)
        self.say("星系中心还有百万到数十亿倍太阳质量的超大质量黑洞。",
                 FadeIn(gal, lag_ratio=0.002), FadeIn(bulge), FadeIn(cdot), FadeIn(smbh), Create(pt), run_time=2)
        self.clean(0.5)

        # --- 人马座 A*：S 星轨道
        Ca = np.array([0.6, 0.6, 0])
        stars = [  # a, e, 方向, 周期(年), 初相
            (2.0, 0.88, np.deg2rad(165), 16.0, 2.6, C_YELLOW),
            (1.35, 0.55, np.deg2rad(55), 16.0 * (1.35 / 2.0) ** 1.5, 1.0, C_BLUE),
            (1.65, 0.72, np.deg2rad(255), 16.0 * (1.65 / 2.0) ** 1.5, 4.0, C_TEAL),
            (0.95, 0.4, np.deg2rad(320), 16.0 * (0.95 / 2.0) ** 1.5, 0.5, C_PINK),
            (2.15, 0.35, np.deg2rad(110), 16.0 * (2.15 / 2.0) ** 1.5, 3.3, C_PURPLE),
        ]
        yr = ValueTracker(0)
        orbits, sdots = VGroup(), VGroup()
        for a, e, ang, P, M0, col in stars:
            ell = ParametricFunction(lambda s, a=a, e=e, ang=ang, P=P: Ca + kepler_pos(s * P, a, e, P, ang),
                                     t_range=[0, 1, 0.005], color=col, stroke_width=1.5, stroke_opacity=0.45)
            orbits.add(DashedVMobject(ell, num_dashes=70))
            d = Dot(radius=0.07, color=col)
            d.add_updater(lambda m, a=a, e=e, ang=ang, P=P, M0=M0: m.move_to(Ca + kepler_pos(yr.get_value(), a, e, P, ang, M0)))
            sdots.add(d)
        s2l = label("S2", 22, C_YELLOW)
        s2l.add_updater(lambda m: m.next_to(sdots[0], UR, buff=0.04))
        center = VGroup(Line(LEFT * 0.12, RIGHT * 0.12, color=C_WHITE), Line(UP * 0.12, DOWN * 0.12, color=C_WHITE)).move_to(Ca)
        cl = label("看不见的中心", 22, C_GREY).next_to(center, DOWN, buff=0.2)
        cnt = always_redraw(lambda: VGroup(DecimalNumber(1995 + yr.get_value(), num_decimal_places=0, group_with_commas=False,
                                                         font_size=34), label("年", 26)).arrange(RIGHT, buff=0.1).move_to([-5.6, 3.3, 0]))
        p2 = label("S2 绕行一周约 16 年", 22, C_GREY).move_to([-5.0, 2.7, 0])
        self.say("银河系中心的恒星，都绕着一个看不见的点转。",
                 FadeIn(orbits), FadeIn(sdots), FadeIn(s2l), FadeIn(center), FadeIn(cl), FadeIn(cnt), FadeIn(p2),
                 yr.animate(rate_func=linear).set_value(10), run_time=4.5)
        mass = VGroup(label("人马座 A*", 30, C_YELLOW), eq(r"M\approx 4\times10^{6}\,M_\odot", 40, C_YELLOW)).arrange(DOWN, buff=0.12)
        mass.move_to([4.9, 2.8, 0])
        nob = VGroup(label("2020 年诺贝尔物理学奖", 26, C_GOLD),
                     label("根策尔、盖兹（与彭罗斯共享）", 22, C_GREY)).arrange(DOWN, buff=0.1).move_to([4.6, -1.75, 0])
        self.say("由轨道推算，那里有约 400 万个太阳质量的人马座 A*。",
                 FadeIn(mass), FadeOut(cl), Succession(Wait(2.0), FadeIn(nob, shift=UP * 0.2, run_time=1.0)),
                 yr.animate(rate_func=linear).set_value(22), run_time=5.5)
        for d in sdots:
            d.clear_updaters()
        s2l.clear_updaters(); cnt.clear_updaters()
        self.clean(0.5)

        # --- EHT 图像（示意）
        def eht(center, kind):
            g = VGroup()
            rr = 1.45
            for k, dr in enumerate(np.linspace(-0.42, 0.42, 9)):
                prof = np.exp(-(dr / 0.24) ** 2)

                def br(t, prof=prof):
                    if kind == "m87":
                        ang = 0.35 + 0.65 * ((1 - np.sin(t + 0.3)) / 2) ** 1.6
                    else:
                        ang = 0.35 + 0.65 * max(np.cos(1.5 * (t - 0.4)) ** 8, np.cos(1.5 * (t - 2.5)) ** 8 * 0.9, 0.2)
                    return float(np.clip(prof * ang, 0, 1))
                g.add(ring_segments(center, rr + dr, rr + dr, 60, br, 12))
            return g
        L = np.array([-3.4, 0.75, 0]); R = np.array([3.4, 0.75, 0])
        img1, img2 = eht(L, "m87"), eht(R, "sgr")
        t1 = VGroup(label("M87*", 30, C_GOLD), label("2019", 24, C_GREY)).arrange(RIGHT, buff=0.25).next_to(img1, DOWN, buff=0.25)
        t2 = VGroup(label("人马座 A*", 30, C_GOLD), label("2022", 24, C_GREY)).arrange(RIGHT, buff=0.25).next_to(img2, DOWN, buff=0.25)
        sch = label("事件视界望远镜（EHT）图像 · 示意", 22, C_GREY).move_to([0, 3.5, 0])
        self.say("2019 年和 2022 年，事件视界望远镜拍下了 M87* 和人马座 A*。",
                 FadeIn(img1), FadeIn(img2), FadeIn(t1), FadeIn(t2), FadeIn(sch), run_time=2)
        hz = DashedVMobject(Circle(radius=1.45 / 2.6, color=C_WHITE, stroke_width=2), num_dashes=24).move_to(L)
        hzl = label("视界", 20, C_WHITE).move_to(L)
        arr = Arrow(L, L + 1.45 * np.array([np.cos(0.6), np.sin(0.6), 0]) * 0.92, buff=0, color=C_YELLOW, stroke_width=3,
                    max_tip_length_to_length_ratio=0.12)
        al = VGroup(label("阴影半径", 22, C_YELLOW), eq(r"\approx 2.6\,r_s", 30, C_YELLOW)).arrange(RIGHT, buff=0.1)
        al.move_to(L + np.array([0.3, 2.35, 0]))
        self.say("中间的暗区是“阴影”，半径约为视界的 2.6 倍。",
                 Create(hz), FadeIn(hzl), GrowArrow(arr), FadeIn(al), run_time=1.8)
        self.clean(0.5)

        # --- GW150914
        tmin, tmax_ = -0.2, 0.03
        tc_end = -0.001

        def f_of(tau):
            return 35 * (0.2 / tau) ** 0.375

        def phase(tau):  # Φ(τ) = ∫2πf dt
            return TAU * 35 * 0.2 ** 0.375 * tau ** 0.625 / 0.625
        x0, x1, yc, amp = -6.2, 6.2, -0.85, 1.25

        def c2p(t, h):
            return np.array([x0 + (t - tmin) / (tmax_ - tmin) * (x1 - x0), yc + amp * h, 0])
        base = Arrow(c2p(tmin, 0) + LEFT * 0.1, c2p(tmax_, 0) + RIGHT * 0.3, buff=0, color=C_GREY, stroke_width=2,
                     max_tip_length_to_length_ratio=0.02)
        ts = np.linspace(tmin, tmax_, 1600)
        hs = []
        Ph0 = phase(0.2)
        for t in ts:
            tau = -t
            if tau > -tc_end:
                hs.append((f_of(tau) / 250) ** 0.667 * np.cos(Ph0 - phase(tau)))
            else:
                tau0 = -tc_end
                hs.append((f_of(tau0) / 250) ** 0.667 * np.exp(-(t - tc_end) / 0.004) *
                          np.cos(Ph0 - phase(tau0) + TAU * 250 * (t - tc_end)))
        wave = VMobject(stroke_color=C_TEAL, stroke_width=3)
        wave.set_points_as_corners([c2p(t, h) for t, h in zip(ts, hs)])
        xlab = label("时间（全程约 0.2 秒）", 22, C_GREY).move_to([4.9, yc - 1.45, 0])
        ylab = label("引力波应变", 22, C_GREY).move_to([-5.4, yc + 1.5, 0])
        flab = eq(r"35\ \mathrm{Hz}\ \to\ 250\ \mathrm{Hz}", 30, C_TEAL).move_to([-1.0, yc + 1.55, 0])
        tt = ValueTracker(tmin)
        Cbin = np.array([0, 2.35, 0])

        def sep(t):
            tau = max(-t, 1e-3)
            return 1.5 * (tau / 0.2) ** 0.25

        def oang(t):
            tau = max(-t, 1e-3)
            return 0.5 * (Ph0 - phase(tau))
        m1, m2 = 36 / 65, 29 / 65

        def binary():
            t = tt.get_value()
            if t >= tc_end:
                return VGroup(Circle(radius=0.3, fill_color=BLACK, fill_opacity=1, stroke_color=C_GOLD, stroke_width=3).move_to(Cbin))
            d, a = sep(t), oang(t)
            u = np.array([np.cos(a), 0.45 * np.sin(a), 0])
            return VGroup(
                Circle(radius=0.22, fill_color=BLACK, fill_opacity=1, stroke_color=C_GOLD, stroke_width=3).move_to(Cbin + u * d * m2),
                Circle(radius=0.19, fill_color=BLACK, fill_opacity=1, stroke_color=C_GOLD, stroke_width=3).move_to(Cbin - u * d * m1))
        bins = always_redraw(binary)
        name = VGroup(label("GW150914", 30, C_WHITE), label("LIGO · 2015 年 9 月 14 日", 22, C_GREY)).arrange(DOWN, aligned_edge=LEFT, buff=0.1)
        name.move_to([-5.0, 3.15, 0])
        mm = eq(r"36\,M_\odot+29\,M_\odot\to 62\,M_\odot", 34, C_GOLD).move_to([4.4, 3.3, 0])
        rad = label("约 3 个太阳质量的能量化为引力波", 22, C_GREY).next_to(mm, DOWN, buff=0.15)
        self.say("2015 年，LIGO 首次直接探测到引力波，来自双黑洞并合。",
                 FadeIn(name), GrowArrow(base), FadeIn(xlab), FadeIn(ylab), FadeIn(bins), run_time=1.5)
        self.say("两黑洞约 36 和 29 倍太阳质量，波形与理论吻合。",
                 FadeIn(mm), FadeIn(rad), FadeIn(flab), Create(wave), tt.animate.set_value(tmax_),
                 run_time=6, rate_func=linear)
        bins.clear_updaters()
        self.clean()

    # ------------------------------------------------------------------ 第六章
    def ch_hawking(self):
        Cc = np.array([-10.6, 0.6, 0])
        Rh = 6.6
        hole = Circle(radius=Rh, fill_color=BLACK, fill_opacity=1, stroke_color=C_YELLOW, stroke_width=3).move_to(Cc)
        hl = label("视界", 24, C_YELLOW).move_to([-3.4, 3.2, 0])
        pairs = []
        for k, a in enumerate([0.22, -0.05, 0.12, -0.2]):
            u = np.array([np.cos(a), np.sin(a), 0])
            p = Cc + u * (Rh + 0.18)
            d_in = Dot(p, radius=0.07, color=C_RED)
            d_out = Dot(p, radius=0.07, color=C_BLUE)
            wv = FunctionGraph(lambda x: 0.12 * np.sin(14 * x), x_range=[0, 1.6, 0.02], color=C_BLUE, stroke_width=3)
            wv.rotate(a, about_point=ORIGIN).shift(p + u * 1.0)
            pairs.append(Succession(
                AnimationGroup(FadeIn(d_in, scale=0.3), FadeIn(d_out, scale=0.3), run_time=0.4),
                AnimationGroup(d_in.animate.move_to(Cc + u * (Rh - 0.9)).set_opacity(0),
                               d_out.animate.move_to(p + u * 1.0), run_time=1.0),
                AnimationGroup(FadeOut(d_out), Create(wv), run_time=0.6),
            ))
        meta = label("（“粒子对”只是一种启发式的比喻）", 22, C_GREY).move_to([0.2, -2.15, 0])
        th = eq(r"T_H=\frac{\hbar c^3}{8\pi G M k_B}", 54).move_to([3.6, 2.4, 0])
        self.say("1974 年，霍金指出：计入量子效应，黑洞会发出微弱热辐射。",
                 Succession(AnimationGroup(FadeIn(hole), FadeIn(hl), run_time=0.7),
                            AnimationGroup(LaggedStart(*pairs, lag_ratio=0.35), FadeIn(meta), Write(th), run_time=3.8)),
                 run_time=4.5)
        tv = eq(r"\approx 6\times10^{-8}\,\mathrm{K}\times\frac{M_\odot}{M}", 44, C_TEAL).next_to(th, DOWN, buff=0.4)
        inv = label("质量越小，温度越高", 24, C_TEAL).next_to(tv, DOWN, buff=0.2)
        cmb = VGroup(eq(r"T_{\rm CMB}\approx 2.7\,\mathrm{K}", 40, C_RED), label("宇宙微波背景：高出约四千万倍", 22, C_RED)).arrange(DOWN, buff=0.12)
        cmb.next_to(inv, DOWN, buff=0.35)
        never = label("天文观测中从未探测到", 24, C_GREY).next_to(cmb, DOWN, buff=0.3)
        self.say("温度与质量成反比；太阳质量黑洞仅约一亿分之六开，从未被观测到。",
                 Succession(AnimationGroup(FadeIn(tv, shift=UP * 0.2), FadeIn(inv), run_time=1.5),
                            AnimationGroup(FadeIn(cmb, shift=UP * 0.2), FadeIn(never), run_time=1.5)), run_time=3.0)
        self.clean(0.5)

        # --- 奇点
        Cs = np.array([-2.8, 0.6, 0])
        hz = DashedVMobject(Circle(radius=2.3, color=C_YELLOW, stroke_width=3), num_dashes=56).move_to(Cs)
        inner = Circle(radius=2.3, fill_color=BLACK, fill_opacity=1, stroke_width=0).move_to(Cs)
        core = Dot(Cs, radius=0.08, color=WHITE)
        glow = VGroup(*[Circle(radius=0.1 * k, stroke_width=0, fill_color=C_PURPLE, fill_opacity=0.12).move_to(Cs) for k in (2, 3, 4.5)])
        q = label("?", 40, C_PURPLE).move_to(Cs + np.array([0.45, 0.4, 0]))
        r0 = eq(r"r=0", 32, C_GREY).move_to(Cs + np.array([0, -0.45, 0]))
        hzl = label("视界", 22, C_YELLOW).next_to(hz, UP, buff=0.1)
        txt = VGroup(label("经典理论：曲率 → 无穷大", 28, C_WHITE),
                     label("实际含义：广义相对论在此失效", 28, C_RED),
                     label("需要：量子引力理论", 28, C_PURPLE),
                     label("（视界内，r = 0 是一个“时刻”而非地点）", 20, C_GREY)).arrange(DOWN, aligned_edge=LEFT, buff=0.32)
        txt.move_to([3.4, 0.6, 0])
        self.say("中心的“奇点”，更可能意味着广义相对论在那里失效。",
                 FadeIn(inner), Create(hz), FadeIn(hzl), FadeIn(core), FadeIn(glow), FadeIn(q), FadeIn(r0),
                 LaggedStart(*[FadeIn(t, shift=RIGHT * 0.2) for t in txt], lag_ratio=0.35),
                 Succession(Wait(2.0), AnimationGroup(*[g.animate(rate_func=there_and_back).scale(1.6) for g in glow], run_time=1.5)),
                 run_time=3.5)
        self.clean(0.5)
        bh = black_hole_icon(center=[0, 0.75, 0], R=1.05)
        self.say("黑洞，是检验时空观念的终极实验室。", FadeIn(bh, scale=0.9), run_time=2)
