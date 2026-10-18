# -*- coding: utf-8 -*-
"""第 02 集 · 量子场：万物底层的“场”"""
import sys
from style import *
import style as _st

# ---------------------------------------------------------------- 兼容性修正（不改 common/style.py）
# 1) style.py 在导入时强制写死 1920x1080@30，导致 -ql 预览也按 1080p 渲染；这里恢复低清预览。
if "-ql" in sys.argv or "--quality=l" in sys.argv:
    config.pixel_width = 854
    config.pixel_height = 480
    config.frame_rate = 15

# 2) style.wrap_sub 会把“——”从中间劈开（两个破折号分到两行）。换一个不拆破折号的版本。
_BREAK = "，、；：。？！,;:"


def _wrap(text, maxc=_st.SUB_MAX_CHARS):
    if len(text) <= maxc or "\n" in text:
        return text
    mid = len(text) / 2
    best, best_d = None, 1e9
    for i, ch in enumerate(text[:-1]):
        nxt = text[i + 1]
        ok = ch in _BREAK or (ch == "—" and nxt != "—")
        if ok and nxt not in _BREAK + "”）":
            d = abs(i + 1 - mid)
            if d < best_d and max(i + 1, len(text) - i - 1) <= maxc + 4:
                best, best_d = i + 1, d
    if best is None:
        best = int(round(mid))
    return text[:best] + "\n" + text[best:]


_st.wrap_sub = _wrap

rng = np.random.default_rng(7)


# ---------------------------------------------------------------- 绘图小工具
def make_palette(stops, n=64):
    cs = [ManimColor(s) for s in stops]
    out = []
    for i in range(n):
        t = i / (n - 1) * (len(cs) - 1)
        j = min(int(t), len(cs) - 2)
        out.append(interpolate_color(cs[j], cs[j + 1], t - j))
    return out


PAL_SHEET = make_palette(["#0e1424", "#1b3556", C_BLUE, "#eafcff"])
PAL_TEMP = make_palette(["#2b3f93", C_BLUE, C_TEAL, C_YELLOW, C_GOLD, C_RED])
PAL_DIV = make_palette([C_BLUE, "#16203a", "#16203a", C_RED])


class FieldGrid(VGroup):
    """方格场：每个小方块的颜色 = 该点的场值"""

    def __init__(self, nx, ny, size, center, palette, gap=0.035):
        super().__init__()
        self.palette = palette
        xs = (np.arange(nx) - (nx - 1) / 2) * size + center[0]
        ys = (np.arange(ny) - (ny - 1) / 2) * size + center[1]
        self.X, self.Y = np.meshgrid(xs, ys)
        for j in range(ny):
            for i in range(nx):
                self.add(Square(size - gap, stroke_width=0, fill_opacity=1,
                                fill_color=palette[0]).move_to([xs[i], ys[j], 0]))

    def paint(self, vals):
        n = len(self.palette)
        idx = np.clip((np.asarray(vals) * (n - 1)).astype(int), 0, n - 1).ravel()
        for sq, k in zip(self.submobjects, idx):
            sq.set_fill(self.palette[k])
        return self


def poly(pts, color=C_BLUE, sw=4):
    m = VMobject(stroke_color=color, stroke_width=sw)
    m.set_points_as_corners(pts)
    return m


def xy(xs, ys):
    return np.stack([xs, ys, np.zeros_like(xs)], 1)


def zigzag(p1, p2, n=7, amp=0.09, color=C_GREY, sw=2.5):
    p1 = np.array(p1, float)
    p2 = np.array(p2, float)
    d = p2 - p1
    L = np.linalg.norm(d)
    if L < 1e-6:
        return poly([p1, p2], color, sw)
    u = d / L
    nrm = np.array([-u[1], u[0], 0])
    pts = [p1]
    for i in range(1, 2 * n):
        pts.append(p1 + d * i / (2 * n) + nrm * amp * (1 if i % 2 else -1))
    pts.append(p2)
    return poly(pts, color, sw)


def wavy(p1, p2, amp=0.12, waves=5, color=C_YELLOW, sw=4, n=140):
    p1 = np.array(p1, float)
    p2 = np.array(p2, float)
    d = p2 - p1
    u = d / np.linalg.norm(d)
    nrm = np.array([-u[1], u[0], 0])
    ts = np.linspace(0, 1, n)
    pts = [p1 + d * t + nrm * amp * np.sin(2 * PI * waves * t) for t in ts]
    return poly(pts, color, sw)


def fline(p1, p2, color=C_BLUE, sw=4):
    p1 = np.array(p1, float)
    p2 = np.array(p2, float)
    ln = Line(p1, p2, color=color, stroke_width=sw)
    tri = Triangle(color=color, fill_opacity=1, stroke_width=0).scale(0.13)
    tri.rotate(angle_of_vector(p2 - p1) - PI / 2).move_to((p1 + p2) / 2)
    return VGroup(ln, tri)


def packet(xs, c, A, s=0.5, k=7.5):
    return A * np.exp(-(xs - c) ** 2 / (2 * s * s)) * np.cos(k * (xs - c))


def smoothstep(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


def ball(tex, color, r=0.42, size=40):
    c = Circle(r, color=color, fill_opacity=0.9, stroke_width=0)
    lab = eq(tex, size, BG).move_to(c)
    return VGroup(c, lab)


def chip(tex, color, r=0.3, size=34):
    c = Circle(r, color=color, fill_opacity=0.22, stroke_width=3)
    lab = eq(tex, size, color).move_to(c)
    return VGroup(c, lab)


class Tween(Animation):
    """ValueTracker 补间：起点在动画开始时读取（避免 .animate 构建器共享 target 的问题）"""

    def __init__(self, tracker, value, **kw):
        self.v1 = value
        kw.setdefault("rate_func", linear)
        super().__init__(tracker, **kw)

    def begin(self):
        self.v0 = self.mobject.get_value()
        super().begin()

    def interpolate_mobject(self, alpha):
        self.mobject.set_value(self.v0 + (self.v1 - self.v0) * self.rate_func(alpha))


class Lazy:
    """延迟构建的动画（播放时才创建）"""

    def __init__(self, fn):
        self.fn = fn


class Video(Explainer):
    # ------------------------------------------------------------ 节拍工具
    def beat(self, text, *steps):
        """字幕 + 依次播放若干步；最后补足阅读时间。步骤可为动画、动画元组、秒数或函数。"""
        self._set_sub(text)
        need = reading_time(text)
        t0 = self._now()
        for s in steps:
            if isinstance(s, Lazy):
                s = s.fn()
            if isinstance(s, (int, float)):
                self.wait(s)
            elif isinstance(s, (list, tuple)):
                self.play(*s)
            elif isinstance(s, Animation) or hasattr(s, "build"):
                self.play(s)
            elif callable(s):
                s()
        rest = need - (self._now() - t0)
        if rest > 0.05:
            self.wait(rest)

    def clock(self, speed=1.0):
        clk = ValueTracker(0)
        clk.add_updater(lambda m, dt: m.increment_value(dt * speed))
        self.add(clk)
        self._clocks.append(clk)
        return clk

    def drive(self, fn):
        """每帧调用 fn(None) 的隐形驱动器（clean 时自动移除）"""
        tk = Mobject()
        tk.add_updater(lambda m: fn(None))
        self.add(tk)
        self._clocks.append(tk)
        return tk

    def clean(self, run_time=0.6):
        for c in self._clocks:
            c.clear_updaters()
            self.remove(c)
        self._clocks = []
        self.fade_all(run_time=run_time)

    # ------------------------------------------------------------ 主线
    def construct(self):
        self._clocks = []
        self.title_card("量子场", "万物底层的“场”")
        self.intro()
        self.chapter("第一章", "什么是场")
        self.ch1()
        self.chapter("第二章", "弹簧网与波")
        self.ch2()
        self.chapter("第三章", "粒子从哪里来")
        self.ch3()
        self.chapter("第四章", "真空并不空")
        self.ch4()
        self.chapter("第五章", "场与场的耦合")
        self.ch5()
        self.chapter("第六章", "标准模型的场清单")
        self.ch6()
        self.end_card([
            "场：给时空每一点指定一个值",
            "场像耦合振子网，每个模式的能量量子化",
            "粒子 = 场的一份激发",
            "真空是所有场的基态，并非空无",
            "相互作用 = 场与场的耦合",
            "希格斯场给基本粒子质量；质子质量主要来自强作用",
        ])

    # ------------------------------------------------------------ 片头
    def intro(self):
        pos = [np.array([-4.0, 1.0, 0]), np.array([0.0, 2.0, 0]), np.array([4.0, 0.4, 0])]
        balls = VGroup(ball(r"e^-", C_BLUE).move_to(pos[0]),
                       ball(r"\gamma", C_YELLOW).move_to(pos[1]),
                       ball(r"q", C_RED).move_to(pos[2]))
        self.beat("电子、光子、夸克……我们习惯把它们想成一颗颗小球。",
                  LaggedStart(*[GrowFromCenter(b) for b in balls], lag_ratio=0.35, run_time=1.8))

        grid = FieldGrid(28, 14, 0.45, (0, 0.7), PAL_SHEET)
        clk = ValueTracker(0)

        def val(t):
            v = 0.1 + 0.04 * np.sin(0.8 * grid.X + 0.6 * grid.Y - 1.3 * t)
            for k, p in enumerate(pos):
                cx = p[0] + 0.5 * np.sin(0.7 * t + k)
                cy = p[1] + 0.3 * np.cos(0.5 * t + 2 * k)
                r2 = (grid.X - cx) ** 2 + (grid.Y - cy) ** 2
                v = v + (0.8 + 0.1 * np.sin(2 * t + k)) * np.exp(-r2 / 0.7)
            return v

        grid.paint(val(0))
        grid.set_z_index(-1)
        title = T("场", 40, C_BLUE, weight=BOLD).move_to([0, 3.62, 0])
        self.beat("但现代物理说：更底层的不是小球，而是铺满宇宙的“场”。",
                  (FadeIn(grid, run_time=1.5), balls.animate(run_time=1.5).scale(0.25).set_opacity(0)),
                  lambda: (clk.add_updater(lambda m, dt: m.increment_value(dt)), self.add(clk),
                           grid.add_updater(lambda m: m.paint(val(clk.get_value())))),
                  FadeIn(title, run_time=0.6))
        self.remove(balls)
        clk.clear_updaters()
        self.remove(clk)
        grid.clear_updaters()
        self.clean()

    # ------------------------------------------------------------ 第一章
    def ch1(self):
        plane = NumberPlane(x_range=[-7, 7, 1], y_range=[-3, 3, 1],
                            background_line_style={"stroke_color": C_BLUE, "stroke_width": 1,
                                                   "stroke_opacity": 0.3},
                            axis_config={"stroke_opacity": 0.5}).shift(UP * 0.7)
        f = lambda x, y: np.sin(0.6 * x) * np.cos(0.5 * y) * 0.5 + 0.5
        dots = VGroup()
        for x in range(-6, 7):
            for y in range(-2, 4):
                c = PAL_TEMP[int(f(x, y) * 63)]
                dots.add(Dot(plane.c2p(x, y - 0.7 + 0.7), radius=0.09, color=c))
        p = Dot(plane.c2p(2, 1), radius=0.13, color=C_YELLOW)
        lab = VGroup(eq(r"(x,\,y,\,t)\ \mapsto", 40, C_YELLOW), T("一个值", 32, C_YELLOW)).arrange(RIGHT, buff=0.2)
        lab.next_to(p, UR, buff=0.15)
        bg = BackgroundRectangle(lab, color=BG, fill_opacity=0.85, buff=0.1)
        self.beat("场，就是给空间每一点、每一时刻都指定一个值。",
                  (Create(plane, run_time=1.2),),
                  (GrowFromCenter(p), FadeIn(bg), FadeIn(lab, shift=UP * 0.2)),
                  LaggedStart(*[FadeIn(d, scale=0.3) for d in dots], lag_ratio=0.01, run_time=1.5))
        self.play(FadeOut(VGroup(plane, dots, p, lab, bg)), run_time=0.6)

        # --- 标量场：气温
        grid = FieldGrid(24, 12, 0.42, (-0.8, 0.75), PAL_TEMP)
        clk = self.clock()

        def temp(X, Y, t):
            return 18 + 9 * (0.6 * np.sin(0.55 * X + 0.35 * t) * np.cos(0.45 * Y - 0.25 * t)
                             + 0.4 * np.cos(0.3 * X - 0.6 * Y + 0.5 * t))

        norm = lambda T_: (T_ - 9) / 18
        grid.paint(norm(temp(grid.X, grid.Y, 0)))
        bar = VGroup(*[Rectangle(width=0.35, height=4.6 / 30, stroke_width=0, fill_opacity=1,
                                 fill_color=PAL_TEMP[int(i / 29 * 63)]) for i in range(30)])
        bar.arrange(UP, buff=0).move_to([5.3, 0.75, 0])
        bl = T("9°C", 24).next_to(bar, DOWN, buff=0.12)
        bh = T("27°C", 24).next_to(bar, UP, buff=0.12)
        head = VGroup(T("气温：标量场", 30), eq(r"T(x,y,t)", 38, C_YELLOW)).arrange(RIGHT, buff=0.35)
        head.move_to([-0.8, 3.62, 0])
        probe = Dot(radius=0.1, color=WHITE)
        num = DecimalNumber(20.0, num_decimal_places=1, font_size=32)
        unit = T("°C", 26)
        tag = VGroup(num, unit)
        tagbg = BackgroundRectangle(tag, color=BG, fill_opacity=0.8, buff=0.08)

        def ppos(t):
            return np.array([-0.8 + 3.6 * np.sin(0.45 * t), 0.75 + 1.6 * np.sin(0.7 * t + 1), 0])

        def upd_probe(m):
            t = clk.get_value()
            q = ppos(t)
            probe.move_to(q)
            num.set_value(float(temp(q[0], q[1], t)))
            unit.next_to(num, RIGHT, buff=0.06)
            tag.next_to(probe, UR, buff=0.08)
            tagbg.surround(tag, buff=0.08)

        upd_probe(None)
        grid.add_updater(lambda m: m.paint(norm(temp(m.X, m.Y, clk.get_value()))))
        probe.add_updater(upd_probe)
        self.beat("气温图就是一个场：每处一个数，叫标量场。",
                  (FadeIn(grid), FadeIn(bar), FadeIn(bl), FadeIn(bh), FadeIn(head, shift=DOWN * 0.2)),
                  (FadeIn(probe), FadeIn(tagbg), FadeIn(tag)))
        self.clean(0.6)

        # --- 矢量场：风
        tt = ValueTracker(0)

        def wind(p):
            t = tt.get_value()
            x, y = p[0] + 0.8, p[1] - 0.75
            r2 = x * x + y * y
            vort = np.array([-y, x, 0]) * np.exp(-r2 / 7) * 0.9
            flow = np.array([0.7 + 0.35 * np.sin(0.5 * p[1] + t), 0.3 * np.cos(0.45 * p[0] - t), 0])
            return vort + flow

        field = always_redraw(lambda: ArrowVectorField(
            wind, x_range=[-5.6, 4.0, 0.75], y_range=[-1.6, 1.9, 0.7],
            length_func=lambda n: 0.6 * np.tanh(n), min_color_scheme_value=0.3,
            max_color_scheme_value=1.6, colors=[C_TEAL, C_YELLOW, C_RED]))
        head = VGroup(T("风：矢量场", 30), eq(r"\vec v(x,y,t)", 38, C_YELLOW)).arrange(RIGHT, buff=0.35)
        head.move_to([-0.8, 3.62, 0])
        self.add(field)
        self.remove(field)
        self.beat("风场在每处放一个箭头，有大小也有方向：矢量场。",
                  (FadeIn(field), FadeIn(head, shift=DOWN * 0.2)),
                  Tween(tt, 3.0, run_time=5.0))
        field.clear_updaters()
        self.clean(0.6)

        # --- 电磁场：电荷的 E，电流的 B
        qc = np.array([-3.4, 0.8, 0])
        wc = np.array([3.4, 0.8, 0])
        charge = VGroup(Circle(0.3, color=C_RED, fill_opacity=0.9, stroke_width=0).move_to(qc),
                        eq("+", 40, BG).move_to(qc))
        wire = VGroup(Circle(0.3, color=C_BLUE, stroke_width=4).move_to(wc),
                      Dot(wc, radius=0.08, color=C_BLUE))
        earr = VGroup()
        barr = VGroup()
        for r, L in ((1.0, 0.65), (1.9, 0.38)):
            for k in range(12):
                a = k * TAU / 12 + (0.26 if r > 1.5 else 0)
                u = np.array([np.cos(a), np.sin(a), 0])
                tvec = np.array([-np.sin(a), np.cos(a), 0])
                earr.add(Arrow(qc + u * r, qc + u * (r + L), buff=0, color=C_YELLOW,
                               stroke_width=4, max_tip_length_to_length_ratio=0.35))
                Lb = 0.42 if r < 1.5 else L
                barr.add(Arrow(wc + u * r - tvec * Lb / 2, wc + u * r + tvec * Lb / 2, buff=0,
                               color=C_BLUE, stroke_width=4, max_tip_length_to_length_ratio=0.35))
        le = VGroup(T("电荷 → 电场", 28), eq(r"\vec E", 40, C_YELLOW)).arrange(RIGHT, buff=0.2).move_to([-3.4, -1.75, 0])
        lb = VGroup(T("电流 → 磁场", 28), eq(r"\vec B", 40, C_BLUE)).arrange(RIGHT, buff=0.2).move_to([3.4, -1.75, 0])
        em_static = VGroup(charge, wire, earr, barr, le, lb)
        EMTEXT = "电磁场每点都有电场和磁场，而且真实存在：阳光的能量和动量就靠它送来。"
        self._set_sub(EMTEXT)
        t_em = self._now()
        self.play(GrowFromCenter(charge), GrowFromCenter(wire))
        self.play(LaggedStart(*[GrowArrow(a) for a in earr], lag_ratio=0.03),
                  LaggedStart(*[GrowArrow(a) for a in barr], lag_ratio=0.03),
                  FadeIn(le), FadeIn(lb))
        self.wait(0.6)
        self.play(FadeOut(em_static), run_time=0.5)

        # --- 阳光：电磁波携带能量
        sun = VGroup(*[Circle(0.8 + 0.18 * i, stroke_width=0, fill_color=C_GOLD,
                              fill_opacity=0.9 if i == 0 else 0.12) for i in range(4)]).move_to([-5.7, 1.0, 0])
        earth = Circle(0.36, stroke_width=0, fill_color="#3a7bd5", fill_opacity=1).move_to([5.9, 1.0, 0])
        halo = Circle(0.62, stroke_width=0, fill_color=C_YELLOW, fill_opacity=0).move_to(earth)
        lsun = T("太阳", 26, C_GOLD).next_to(sun, DOWN, buff=0.1)
        lear = T("地球", 26, C_BLUE).next_to(earth, DOWN, buff=0.35)
        clk = ValueTracker(0)
        y0, xa, xb = 1.0, -4.5, 5.2
        xs = np.linspace(xa, xb, 34)
        dB = np.array([0.62, -0.5, 0])
        k, w = 2.0, 4.0

        def front(t):
            return xa + 3.2 * t

        def amp(x, t):
            return np.where(x < front(t), 1.0, 0.0) * np.sin(k * x - w * t)

        elines = VGroup(*[Line(ORIGIN, UP * 0.01, color=C_YELLOW, stroke_width=3) for _ in xs])
        blines = VGroup(*[Line(ORIGIN, UP * 0.01, color=C_BLUE, stroke_width=3) for _ in xs])
        ecur = VMobject(stroke_color=C_YELLOW, stroke_width=4)
        bcur = VMobject(stroke_color=C_BLUE, stroke_width=4)
        axis = Line([xa, y0, 0], [xb, y0, 0], color=C_GREY, stroke_width=2)

        def upd_wave(m):
            t = clk.get_value()
            a = amp(xs, t)
            for x, ai, el, blm in zip(xs, a, elines, blines):
                base = np.array([x, y0, 0])
                el.set_points_as_corners([base, base + UP * 1.1 * ai])
                blm.set_points_as_corners([base, base + dB * ai])
            xf = np.linspace(xa, xb, 200)
            af = amp(xf, t)
            ecur.set_points_as_corners(xy(xf, y0 + 1.1 * af))
            bcur.set_points_as_corners(xy(xf + dB[0] * af, y0 + dB[1] * af))
            halo.set_fill(opacity=0.35 * smoothstep((front(t) - xb) / 1.5))

        upd_wave(None)
        wave = VGroup(axis, blines, bcur, elines, ecur)
        wave.add_updater(upd_wave)
        le = eq(r"\vec E", 36, C_YELLOW).move_to([-3.6, 2.6, 0])
        lb = eq(r"\vec B", 36, C_BLUE).move_to([-3.2, -0.2, 0])
        u = eq(r"u=\tfrac{\varepsilon_0}{2}\left(E^2+c^2B^2\right)", 42).move_to([-0.6, -1.65, 0])
        ul = T("能量密度", 28, C_GREY).next_to(u, RIGHT, buff=0.4)
        self.add(wave)
        clk.add_updater(lambda m, dt: m.increment_value(dt))
        self.add(clk)
        self._clocks.append(clk)
        self.play(FadeIn(sun), FadeIn(earth), FadeIn(halo), FadeIn(lsun), FadeIn(lear))
        self.play(FadeIn(le), FadeIn(lb), Write(u), FadeIn(ul))
        self.wait(max(2.0, reading_time(EMTEXT) - (self._now() - t_em)))
        wave.clear_updaters()
        self.clean()

    # ------------------------------------------------------------ 第二章
    def ch2(self):
        y0 = 0.8

        def chain(N, disp, r, springs=True, x0=-6.0, x1=6.0):
            xs = np.linspace(x0, x1, N)
            ys = y0 + disp(xs)
            g = VGroup()
            if springs:
                for i in range(N - 1):
                    a = np.array([xs[i], ys[i], 0])
                    b = np.array([xs[i + 1], ys[i + 1], 0])
                    u = (b - a) / np.linalg.norm(b - a)
                    g.add(zigzag(a + u * r, b - u * r, n=max(2, int(7 * 12 / N)),
                                 amp=0.09 * min(1, 24 / N), sw=2.5 if N < 30 else 1.5))
            for x, yv in zip(xs, ys):
                g.add(Dot([x, yv, 0], radius=r, color=C_BLUE))
            return g

        c = ValueTracker(-6.0)
        pulse = lambda xs: 1.1 * np.exp(-(xs - c.get_value()) ** 2 / (2 * 0.75 ** 2))
        ch = always_redraw(lambda: chain(12, pulse, 0.17))
        base = DashedLine([-6.6, y0, 0], [6.6, y0, 0], color=C_GREY, stroke_width=1.5, dash_length=0.1)
        self.beat("想象一串用弹簧相连的小球：拨动一端，扰动沿链条传开——这就是波。",
                  (FadeIn(base), FadeIn(ch)),
                  Tween(c, 8.5, run_time=5.5))
        ch.clear_updaters()
        self.remove(ch)

        sw = lambda xs: 0.75 * np.sin(0.9 * xs + 0.6)
        c12 = chain(12, sw, 0.17)
        c24 = chain(24, sw, 0.12)
        c48 = chain(48, sw, 0.075)
        xf = np.linspace(-6, 6, 240)
        cur = poly(xy(xf, y0 + sw(xf)), C_BLUE, 5)
        xp = (1.5 * PI - 0.6) / 0.9
        yp = y0 + float(sw(np.array([xp]))[0])
        stick = Line([xp, y0, 0], [xp, yp, 0], color=C_YELLOW, stroke_width=4)
        phl = eq(r"\varphi(x,t)", 44, C_YELLOW).next_to(stick, DOWN, buff=0.15)
        lab = T("场值 = 每一点的位移", 28, C_GREY).move_to([0, -1.6, 0])
        self.add(c12)
        self.beat("小球排得越来越密，链条就变成一根连续的弦：一个一维的场。",
                  FadeTransform(c12, c24, run_time=1.1),
                  FadeTransform(c24, c48, run_time=1.1),
                  FadeTransform(c48, cur, run_time=1.1),
                  (Create(stick), FadeIn(phl), FadeIn(lab)))
        self.clean(0.6)

        # --- 简正模式
        x0, x1 = -5.8, -1.7
        ys = [2.7, 1.25, -0.2]
        A = 0.42
        w1 = 2.2
        clk = self.clock()
        xm = np.linspace(x0, x1, 120)
        sm = (xm - x0) / (x1 - x0)
        modes, icons, labs = VGroup(), VGroup(), VGroup()
        cols = [C_TEAL, C_YELLOW, C_RED]
        for n in (1, 2, 3):
            yc = ys[n - 1]
            m = VMobject(stroke_color=cols[n - 1], stroke_width=4)

            def um(m, n=n, yc=yc):
                t = clk.get_value()
                m.set_points_as_corners(xy(xm, yc + A * np.sin(n * PI * sm) * np.cos(n * w1 * t)))

            um(m)
            m.add_updater(um)
            pins = VGroup(Dot([x0, yc, 0], radius=0.06, color=C_GREY), Dot([x1, yc, 0], radius=0.06, color=C_GREY))
            modes.add(VGroup(m, pins))
            labs.add(eq(rf"\omega_{n}", 38, cols[n - 1]).move_to([-6.45, yc, 0]))
            top = np.array([-0.7, yc + 0.6, 0])
            blk = Square(0.26, color=cols[n - 1], fill_opacity=0.9, stroke_width=0)
            spr = VMobject()
            ceil = Line(top + LEFT * 0.3, top + RIGHT * 0.3, color=C_GREY, stroke_width=3)

            def ui(g, n=n, yc=yc, top=top):
                t = clk.get_value()
                yb = yc - 0.2 + 0.22 * np.cos(n * w1 * t)
                g[1].move_to([top[0], yb, 0])
                g[0].become(zigzag(top, [top[0], yb + 0.13, 0], n=5, amp=0.08))

            icon = VGroup(spr, blk, ceil)
            icon_g = VGroup(spr, blk)
            ui(icon_g)
            icon_g.add_updater(ui)
            icons.add(VGroup(icon_g, ceil))
        hm = T("简正模式", 28, C_GREY).move_to([-3.75, 3.6, 0])
        hi = T("谐振子", 28, C_GREY).move_to([-0.7, 3.6, 0])
        xs2 = np.linspace(1.0, 6.4, 200)
        s2 = (xs2 - 1.0) / 5.4
        sum_c = VMobject(stroke_color=C_WHITE, stroke_width=5)

        def us(m):
            t = clk.get_value()
            y = (0.55 * np.sin(PI * s2) * np.cos(w1 * t) + 0.32 * np.sin(2 * PI * s2) * np.cos(2 * w1 * t + 1)
                 + 0.22 * np.sin(3 * PI * s2) * np.cos(3 * w1 * t + 2))
            m.set_points_as_corners(xy(xs2, 1.25 + 1.15 * y))

        us(sum_c)
        sum_c.add_updater(us)
        pins2 = VGroup(Dot([1.0, 1.25, 0], radius=0.06, color=C_GREY), Dot([6.4, 1.25, 0], radius=0.06, color=C_GREY))
        hs = T("叠加 = 任意复杂的振动", 28, C_GREY).move_to([3.7, 3.0, 0])
        arr = Arrow([0.0, 1.25, 0], [0.85, 1.25, 0], buff=0, color=C_GREY, stroke_width=3)
        self.beat("任何振动都能拆成简正模式的叠加，每个模式就像一个独立的谐振子。",
                  (FadeIn(sum_c), FadeIn(pins2), FadeIn(hs)),
                  (LaggedStart(*[FadeIn(m) for m in modes], lag_ratio=0.4), FadeIn(labs), FadeIn(hm), FadeIn(arr)),
                  (FadeIn(icons), FadeIn(hi)))
        self.clean()

    # ------------------------------------------------------------ 第三章
    def ch3(self):
        ax = Axes(x_range=[-2.4, 2.4, 1], y_range=[0, 5.6, 1], x_length=5.0, y_length=5.2,
                  tips=False, axis_config={"include_ticks": False, "stroke_opacity": 0.6}).move_to([-3.4, 0.55, 0])
        Vf = lambda x: 0.95 * x * x
        par = ax.plot(Vf, x_range=[-2.4, 2.4], color=C_BLUE, stroke_width=4)
        rungs, nl = VGroup(), VGroup()
        for n in range(5):
            E = n + 0.5
            xr = np.sqrt(E / 0.95)
            rungs.add(Line(ax.c2p(-xr, E), ax.c2p(xr, E), color=C_WHITE, stroke_width=3))
            nl.add(eq(rf"n={n}", 30, C_GREY).next_to(ax.c2p(xr, E), RIGHT, buff=0.2))
        dot = Dot(ax.c2p(0, 0.5), radius=0.13, color=C_YELLOW)
        f1 = eq(r"E_n=\left(n+\tfrac12\right)\hbar\omega", 62).move_to([3.4, 2.2, 0])
        f2 = eq(r"\Delta E=\hbar\omega", 50, C_YELLOW).move_to([3.4, 0.8, 0])
        jumps = []
        for n in range(3):
            a = ax.c2p(-0.45, n + 0.5)
            b = ax.c2p(-0.45, n + 1.5)
            ar = Arrow(a, b, buff=0.05, color=C_YELLOW, stroke_width=4)
            hl = eq(r"\hbar\omega", 30, C_YELLOW).next_to(ar, LEFT, buff=0.1)
            jumps.append((ar, hl))
        steps = [(Create(ax), Create(par)), (LaggedStart(*[Create(r) for r in rungs], lag_ratio=0.2), FadeIn(nl), Write(f1)),
                 FadeIn(dot, scale=0.5)]
        for n, (ar, hl) in enumerate(jumps):
            steps.append(Lazy(lambda n=n, ar=ar, hl=hl: (GrowArrow(ar), FadeIn(hl), dot.animate.move_to(ax.c2p(0, n + 1.5)),
                                                          rungs[n + 1].animate.set_color(C_YELLOW))))
        steps.insert(3, FadeIn(f2))
        self.beat("量子力学说：谐振子的能量只能是 (n+½)ħω，一级一级，每级相差 ħω。", *steps)
        self.clean(0.6)

        # --- 场 = 许多模式，每个模式一个梯子
        xsL = [-5.0, -2.5, 0.0, 2.5, 5.0]
        ladders, dots, waves, klab = VGroup(), VGroup(), VGroup(), VGroup()
        for i, x in enumerate(xsL):
            rs = VGroup(*[Line([x - 0.5, -1.2 + 0.32 * n, 0], [x + 0.5, -1.2 + 0.32 * n, 0],
                               color=C_GREY, stroke_width=3) for n in range(5)])
            ladders.add(rs)
            dots.add(Dot([x, -1.2, 0], radius=0.09, color=C_YELLOW))
            kk = 2.2 + 1.1 * i
            xw = np.linspace(x - 0.9, x + 0.9, 80)
            waves.add(poly(xy(xw, 2.55 + 0.2 * np.sin(kk * (xw - x))), C_BLUE, 3))
            klab.add(eq(rf"k_{i + 1}", 34, C_GREY).move_to([x, 3.3, 0]))
        nlab = VGroup(T("占据数 n", 24, C_GREY)).move_to([0, -2.05, 0])
        self.play(LaggedStart(*[Create(w) for w in waves], lag_ratio=0.15), FadeIn(klab),
                  LaggedStart(*[FadeIn(l) for l in ladders], lag_ratio=0.15), FadeIn(dots), FadeIn(nlab), run_time=1.4)

        ann = VGroup(T("1 个粒子", 32, C_YELLOW),
                     eq(r"E=\hbar\omega_k,\quad p=\hbar k", 36)).arrange(DOWN, buff=0.15).move_to([0, 1.25, 0])
        self.beat("把每个模式都量子化，就是量子场论：模式升高一级，就多出一个“粒子”。",
                  0.8,
                  (dots[2].animate.move_to([0, -0.88, 0]), ladders[2][1].animate.set_color(C_YELLOW),
                   waves[2].animate.set_color(C_YELLOW).set_stroke(width=5)),
                  Flash([0, -0.88, 0], color=C_YELLOW, flash_radius=0.4),
                  FadeIn(ann, shift=UP * 0.2))
        self.clean(0.6)

        # --- 两种场、两种量子
        clk = self.clock()
        yE, ye = 2.8, 1.05
        xl = np.linspace(-4.3, 6.6, 260)
        lE = VGroup(T("电磁场", 30, C_YELLOW)).move_to([-5.6, yE, 0])
        le = VGroup(T("电子场", 30, C_BLUE)).move_to([-5.6, ye, 0])
        cE = VMobject(stroke_color=C_YELLOW, stroke_width=4)
        ce = VMobject(stroke_color=C_BLUE, stroke_width=4)
        tg = eq(r"\gamma", 40, C_YELLOW)
        tm = eq(r"e^-", 40, C_BLUE)
        tp = eq(r"e^+", 40, C_TEAL)
        span = 10.9

        def cpos(t, v, start):
            return -4.3 + ((start + v * t) % span)

        def upd(m):
            t = clk.get_value()
            g = cpos(t, 2.4, 1.0)
            a = cpos(t, 1.0, 1.5)
            b = -4.3 + ((9.0 - 1.1 * t) % span)
            cE.set_points_as_corners(xy(xl, yE + packet(xl, g, 0.55)))
            ce.set_points_as_corners(xy(xl, ye + packet(xl, a, 0.5, k=6) + packet(xl, b, 0.5, k=6)))
            tg.move_to([g, yE + 0.8, 0])
            tm.move_to([a, ye + 0.8, 0])
            tp.move_to([b, ye + 0.8, 0])

        upd(None)
        self.drive(upd)
        self.beat("电磁场的量子是光子；电子场的量子是电子和正电子。",
                  (FadeIn(lE), FadeIn(cE), FadeIn(tg)),
                  (FadeIn(le), FadeIn(ce), FadeIn(tm), FadeIn(tp)))

        # 玻色子 vs 费米子
        bx = Rectangle(width=2.8, height=1.1, color=C_YELLOW, stroke_width=3).move_to([-3.3, -1.45, 0])
        fx = Rectangle(width=2.8, height=1.1, color=C_BLUE, stroke_width=3).move_to([3.3, -1.45, 0])
        bt = T("玻色子模式：可容纳任意多份", 26, C_YELLOW).move_to([-3.3, -0.45, 0])
        ft = T("费米子模式：最多一份", 26, C_BLUE).move_to([3.3, -0.45, 0])
        bd = VGroup(*[Dot([-4.2 + 0.6 * i, -1.45, 0], radius=0.14, color=C_YELLOW) for i in range(4)])
        fd = Dot([3.3, -1.45, 0], radius=0.14, color=C_BLUE)
        fd2 = Dot([6.2, -1.45, 0], radius=0.14, color=C_BLUE)
        cross = Cross(scale_factor=0.22, stroke_color=C_RED, stroke_width=6).move_to([4.15, -1.45, 0])
        self.beat("电子场是费米子场：每个模式最多容纳一份——泡利不相容原理。",
                  (Create(bx), Create(fx), FadeIn(bt), FadeIn(ft)),
                  (LaggedStart(*[FadeIn(d, scale=0.3) for d in bd], lag_ratio=0.3), FadeIn(fd, scale=0.3)),
                  FadeIn(fd2),
                  Lazy(lambda: fd2.animate(run_time=0.7).move_to([4.15, -1.45, 0])),
                  Lazy(lambda: (Create(cross), fd2.animate(run_time=0.6).move_to([5.9, -1.45, 0]).set_opacity(0.3))))
        self.clean()

        # --- 全同性：同一张电子场上的相同涟漪
        grid = FieldGrid(30, 12, 0.4, (0, 0.9), PAL_SHEET)
        clk = self.clock()
        P0 = [(-4.0, 2.0, 0.9, -0.5), (-1.0, 0.0, -0.6, 0.6), (2.5, 2.4, 0.5, 0.45), (4.5, -0.4, -0.8, -0.3)]
        tags = VGroup(*[eq(r"e^-", 32, WHITE) for _ in P0])

        def bpos(i, t):
            x0, y0, vx, vy = P0[i]
            # 在网格内来回反弹
            def refl(v, lo, hi):
                L = hi - lo
                u = (v - lo) % (2 * L)
                return lo + (u if u < L else 2 * L - u)
            return refl(x0 + vx * t, -5.4, 5.4), refl(y0 + vy * t, -0.8, 2.6)

        def gval(t):
            v = 0.08 + 0.03 * np.sin(0.9 * grid.X - 0.7 * grid.Y + t)
            for i in range(len(P0)):
                bx_, by_ = bpos(i, t)
                v = v + 0.85 * np.exp(-((grid.X - bx_) ** 2 + (grid.Y - by_) ** 2) / 0.35)
            return v

        def ugrid(m):
            t = clk.get_value()
            m.paint(gval(t))
            for i, tgm in enumerate(tags):
                bx_, by_ = bpos(i, t)
                tgm.move_to([bx_, by_ + 0.62, 0])

        ugrid(grid)
        head = T("同一个电子场", 30, C_BLUE).move_to([0, 3.62, 0])
        props = T("每一个：质量 0.511 MeV · 电荷 −e · 自旋 1/2", 28).move_to([0, -1.85, 0])
        self.beat("全宇宙只有一个电子场，所以每个电子都严格相同。",
                  (FadeIn(grid), FadeIn(head), FadeIn(tags)),
                  lambda: grid.add_updater(ugrid),
                  FadeIn(props, shift=UP * 0.2))
        grid.clear_updaters()
        self.clean()

        # --- 波包
        clk = self.clock()
        ks = [3.0 + 0.35 * j for j in range(-3, 4)]
        wts = [np.exp(-j * j / (2 * 1.5 ** 2)) for j in range(-3, 4)]
        S = sum(wts)
        xw = np.linspace(-6.2, 6.2, 320)
        v, c0 = 1.2, -3.9
        comps = VGroup(*[VMobject(stroke_color=C_BLUE, stroke_width=2.5, stroke_opacity=0.5 + 0.5 * wts[i])
                         for i in range(7)])
        ycs = [3.5 - 0.38 * i for i in range(7)]
        tot = VMobject(stroke_color=C_YELLOW, stroke_width=5)
        pdot = Dot(radius=0.12, color=C_WHITE)
        plab = T("“粒子”", 26).set_color(C_WHITE)
        ysum = -0.8

        def uw(m):
            t = clk.get_value()
            yt = np.zeros_like(xw)
            for i in range(7):
                ph = ks[i] * (xw - c0 - v * t)
                comps[i].set_points_as_corners(xy(xw, ycs[i] + 0.14 * np.cos(ph)))
                yt += wts[i] * np.cos(ph)
            tot.set_points_as_corners(xy(xw, ysum + 1.15 * yt / S))
            cx = c0 + v * t
            pdot.move_to([cx, ysum + 1.5, 0])
            plab.next_to(pdot, UP, buff=0.1)

        uw(None)
        sig = eq(r"\sum", 48, C_GREY).move_to([-6.65, 0.15, 0])
        arr = Arrow([-6.65, 0.95, 0], [-6.65, 0.55, 0], buff=0, color=C_GREY, stroke_width=3,
                    max_tip_length_to_length_ratio=0.5)
        self.drive(uw)
        self.beat("许多模式叠加成局部的波包，看起来就像一颗粒子在运动。",
                  LaggedStart(*[FadeIn(c) for c in comps], lag_ratio=0.2, run_time=1.2),
                  (FadeIn(tot), FadeIn(sig), FadeIn(arr)),
                  (FadeIn(pdot), FadeIn(plab)))
        self.clean()

        # --- 产生与湮灭
        ye, yg = 1.6, -0.8
        xl = np.linspace(-6.5, 6.5, 320)
        s = ValueTracker(0)
        le = T("电子场", 28, C_BLUE).move_to([-5.7, ye + 0.85, 0])
        lg = T("电磁场", 28, C_YELLOW).move_to([-5.7, yg + 0.85, 0])
        ce = VMobject(stroke_color=C_BLUE, stroke_width=4)
        cg = VMobject(stroke_color=C_YELLOW, stroke_width=4)
        tm, tp = eq(r"e^-", 38, C_BLUE), eq(r"e^+", 38, C_TEAL)
        g1, g2 = eq(r"\gamma", 38, C_YELLOW), eq(r"\gamma", 38, C_YELLOW)
        A = 0.5
        mode = {"rev": False}

        def ua(m):
            sv = s.get_value()
            if not mode["rev"]:
                d = 4.2 * min(sv / 0.5, 1)
                ae = A * (1 - smoothstep((sv - 0.42) / 0.14))
                ag = A * smoothstep((sv - 0.47) / 0.14)
                xe1, xe2 = -4.2 + d, 4.2 - d
                dg = 4.6 * max(0, (sv - 0.5) / 0.5)
                xg1, xg2 = -dg, dg
                ce.set_points_as_corners(xy(xl, ye + packet(xl, xe1, ae, k=6) + packet(xl, xe2, ae, k=6)))
                cg.set_points_as_corners(xy(xl, yg + packet(xl, xg1, ag, k=9) + packet(xl, xg2, ag, k=9)))
            else:
                dg = 4.6 * min(sv / 0.5, 1)
                ag = A * (1 - smoothstep((sv - 0.42) / 0.14))
                ae = A * smoothstep((sv - 0.47) / 0.14)
                xg1 = xg2 = -4.6 + dg
                d = 4.2 * max(0, (sv - 0.5) / 0.5)
                xe1, xe2 = d, -d
                ce.set_points_as_corners(xy(xl, ye + packet(xl, xe1, ae, k=6) + packet(xl, xe2, ae, k=6)))
                cg.set_points_as_corners(xy(xl, yg + packet(xl, xg1, ag, k=9)))
            tm.move_to([xe1, ye + 0.85, 0]).set_opacity(ae / A)
            tp.move_to([xe2, ye + 0.85, 0]).set_opacity(ae / A)
            g1.move_to([xg1, yg + 0.85, 0]).set_opacity(ag / A)
            g2.move_to([xg2, yg + 0.85, 0]).set_opacity(0 if mode["rev"] else ag / A)

        ua(None)
        drv = VGroup(ce, cg)
        drv.add_updater(ua)
        r1 = eq(r"e^-+e^+\ \to\ \gamma+\gamma", 48).move_to([0, 3.35, 0])
        link = DashedLine([0, ye - 0.3, 0], [0, yg + 0.3, 0], color=C_WHITE, stroke_width=2)
        self.add(drv, tm, tp, g1, g2)
        self.remove(drv, tm, tp, g1, g2)
        self.beat("粒子数并不固定：电子与正电子相遇，可以湮灭成两个光子。",
                  (FadeIn(le), FadeIn(lg), FadeIn(drv), FadeIn(tm), FadeIn(tp), FadeIn(g1), FadeIn(g2), Write(r1)),
                  Tween(s, 0.5, run_time=2.0),
                  (Flash([0, ye, 0], color=C_WHITE, flash_radius=0.5), Create(link),
                   Tween(s, 1.0, run_time=2.2)))
        mode["rev"] = True
        s.set_value(0)
        ua(None)
        nuc = VGroup(Dot([0, 0.4, 0], radius=0.16, color=C_GREY),
                     T("原子核", 24, C_GREY).move_to([0.75, 0.4, 0]))
        r2 = eq(r"\gamma\ \to\ e^-+e^+\qquad (E_\gamma\geq 2m_ec^2\approx 1.022\ \mathrm{MeV})", 40).move_to([0, 3.35, 0])
        self.beat("反过来，高能光子在原子核附近，也能变成一对电子和正电子。",
                  (FadeOut(r1), FadeIn(r2), FadeIn(nuc), FadeOut(link)),
                  Tween(s, 0.5, run_time=2.0),
                  (Flash([0, ye, 0], color=C_WHITE, flash_radius=0.5),
                   Tween(s, 1.0, run_time=2.2)))
        drv.clear_updaters()
        self.clean()

    # ------------------------------------------------------------ 第四章
    def ch4(self):
        clk = self.clock()
        grid = FieldGrid(22, 9, 0.38, (-2.4, 2.0), PAL_DIV)
        rr = np.random.default_rng(3)
        waves = [(rr.uniform(-3, 3), rr.uniform(-3, 3), rr.uniform(3, 7), rr.uniform(0, TAU)) for _ in range(7)]

        def nval(t):
            v = np.zeros_like(grid.X)
            for kx, ky, w, ph in waves:
                v += np.sin(kx * grid.X + ky * grid.Y - w * t + ph)
            return 0.5 + 0.11 * v

        xl = np.linspace(-6.6, 1.8, 260)
        sl = (xl + 6.6) / 8.4
        jl = VMobject(stroke_color=C_BLUE, stroke_width=4)
        nm = [(n, rr.uniform(0, TAU), rr.uniform(0.5, 1.0)) for n in range(1, 13)]

        def upd(m):
            t = clk.get_value()
            grid.paint(nval(t))
            y = np.zeros_like(xl)
            for n, ph, a in nm:
                y += a / np.sqrt(n) * np.sin(n * PI * sl) * np.cos(2.3 * np.sqrt(n) * 2.2 * t + ph)
            jl.set_points_as_corners(xy(xl, -1.0 + 0.16 * y))

        upd(None)
        drv = VGroup(grid, jl)
        base = DashedLine([-6.6, -1.0, 0], [1.8, -1.0, 0], color=C_GREY, stroke_width=1.5)
        head = T("真空 = 所有场的基态", 30).move_to([4.4, 3.1, 0])
        self.beat("真空是所有场的最低能态，但它不是“什么都没有”。",
                  (FadeIn(grid), FadeIn(jl), FadeIn(base), FadeIn(head)),
                  lambda: self.drive(upd))

        # 梯子：零点能
        ax = Axes(x_range=[-1.6, 1.6, 1], y_range=[0, 3.2, 1], x_length=2.6, y_length=3.0, tips=False,
                  axis_config={"include_ticks": False, "stroke_opacity": 0.5}).move_to([4.4, -0.75, 0])
        par = ax.plot(lambda x: 1.2 * x * x, x_range=[-1.6, 1.6], color=C_BLUE, stroke_width=3)
        rungs = VGroup(*[Line(ax.c2p(-np.sqrt((n + 0.5) * 0.5 / 1.2), (n + 0.5) * 0.5),
                              ax.c2p(np.sqrt((n + 0.5) * 0.5 / 1.2), (n + 0.5) * 0.5),
                              color=C_YELLOW if n == 0 else C_GREY, stroke_width=3) for n in range(5)])
        zd = Dot(ax.c2p(0, 0.25), radius=0.09, color=C_YELLOW)
        zd.add_updater(lambda m: m.move_to(ax.c2p(0.12 * np.sin(13 * clk.get_value()) * np.cos(5.3 * clk.get_value()), 0.25)))
        e0 = eq(r"E_0=\tfrac12\hbar\omega\neq 0", 40, C_YELLOW).move_to([4.4, 1.25, 0])
        fl = eq(r"\langle\varphi\rangle=0,\quad \Delta\varphi\neq 0", 40).move_to([4.4, 2.3, 0])
        self.beat("每个模式仍有 ½ħω 的零点能：场值不是确定的零，而有量子涨落。",
                  (Create(ax), Create(par), Create(rungs), FadeIn(zd)),
                  (Write(e0),),
                  (Write(fl),))
        self.clean()

        # --- 卡西米尔
        clk = self.clock()
        d = ValueTracker(1.1)
        plates = VGroup(*[Rectangle(width=0.22, height=4.4, stroke_width=0, fill_color="#9aa4b5",
                                    fill_opacity=0.95) for _ in range(2)])

        def uplates(m):
            m[0].move_to([-d.get_value(), 0.3, 0])
            m[1].move_to([d.get_value(), 0.3, 0])

        uplates(plates)
        plates.add_updater(uplates)
        inner = VGroup(*[VMobject(stroke_color=c, stroke_width=4) for c in (C_TEAL, C_YELLOW, C_RED)])
        iy = [1.65, 0.3, -1.05]
        outer = VGroup(*[VMobject(stroke_color=C_BLUE, stroke_width=2.5, stroke_opacity=0.55) for _ in range(8)])
        oy = [1.75, 0.85, -0.05, -0.95]
        oks = [(3.1, 1.3), (5.3, 2.1), (2.2, 0.4), (6.8, 1.7), (4.1, 2.9), (2.7, 0.9), (7.6, 0.2), (3.7, 1.1)]

        def ucas(m):
            t = clk.get_value()
            dv = d.get_value() - 0.11
            xi = np.linspace(-dv, dv, 120)
            si = (xi + dv) / (2 * dv)
            for n in (1, 2, 3):
                inner[n - 1].set_points_as_corners(xy(xi, iy[n - 1] + 0.32 * np.sin(n * PI * si) * np.cos(2.5 * n * t)))
            for j in range(8):
                k, ph = oks[j]
                left = j < 4
                xo = np.linspace(-6.6, -d.get_value() - 0.11, 140) if left else np.linspace(d.get_value() + 0.11, 6.6, 140)
                outer[j].set_points_as_corners(xy(xo, oy[j % 4] + 0.24 * np.sin(k * xo - 1.8 * k * t * (1 if left else -1) + ph)))

        drv = VGroup(inner, outer)
        ucas(drv)
        self.drive(ucas)
        lin = T("板间：模式受限", 26, C_YELLOW).move_to([0, 2.88, 0])
        lol = T("板外：任意波长", 26, C_GREY).move_to([-4.0, 2.88, 0])
        lor = T("板外：任意波长", 26, C_GREY).move_to([4.0, 2.88, 0])
        self.beat("两块平行金属板之间只容得下特定模式，板外则不受限制。",
                  (FadeIn(plates), FadeIn(outer)),
                  (LaggedStart(*[Create(c) for c in inner], lag_ratio=0.3), FadeIn(lin), FadeIn(lol), FadeIn(lor)))
        fa = Arrow([-2.7, 0.3, 0], [-1.3, 0.3, 0], buff=0, color=C_RED, stroke_width=7)
        fb = Arrow([2.7, 0.3, 0], [1.3, 0.3, 0], buff=0, color=C_RED, stroke_width=7)
        fa.add_updater(lambda m: m.put_start_and_end_on([-d.get_value() - 1.45, 0.3, 0], [-d.get_value() - 0.15, 0.3, 0]))
        fb.add_updater(lambda m: m.put_start_and_end_on([d.get_value() + 1.45, 0.3, 0], [d.get_value() + 0.15, 0.3, 0]))
        ff = eq(r"\frac{F}{A}=-\frac{\pi^2\hbar c}{240\,d^4}", 44).move_to([0, 3.48, 0])
        fbg = BackgroundRectangle(ff, color=BG, fill_opacity=0.9, buff=0.08)
        self.beat("零点能之差把两板推向彼此——这就是卡西米尔效应。",
                  (GrowArrow(fa), GrowArrow(fb), FadeOut(lin), FadeIn(fbg), Write(ff)),
                  Tween(d, 0.98, run_time=2.0, rate_func=smooth))
        t1 = T("1948 · 卡西米尔 预言", 26, C_GOLD).move_to([-4.0, 2.88, 0])
        t2 = T("1997 · 拉莫罗测得（误差约 5%）", 26, C_GOLD).move_to([4.1, 2.88, 0])
        self.beat("1948年卡西米尔预言，1997年拉莫罗测得，与理论吻合，误差约5%。",
                  (FadeOut(lol), FadeOut(lor)),
                  (FadeIn(t1, shift=DOWN * 0.2), FadeIn(t2, shift=DOWN * 0.2)))
        for m in (plates, fa, fb):
            m.clear_updaters()
        self.clean()

        # --- “虚粒子”
        bub = DashedVMobject(Circle(1.25, color=C_GREY, stroke_width=3), num_dashes=28).move_to([-4.3, 0.8, 0])
        pe = ball(r"e^-", C_BLUE, r=0.32, size=30).move_to([-4.75, 0.8, 0])
        pp = ball(r"e^+", C_TEAL, r=0.32, size=30).move_to([-3.85, 0.8, 0])
        vlab = T("“虚粒子”", 32).move_to([-4.3, 2.6, 0])
        vmeta = T("直观比喻", 28, C_GREY).move_to([-4.3, -0.9, 0])
        arr = Arrow([-2.6, 0.8, 0], [-1.2, 0.8, 0], buff=0, color=C_GREY, stroke_width=4)
        lc = np.array([2.4, 0.8, 0])
        ph1 = wavy([-0.8, 0.8, 0], lc + LEFT * 0.9, amp=0.13, waves=4)
        ph2 = wavy(lc + RIGHT * 0.9, [5.6, 0.8, 0], amp=0.13, waves=4)
        loop = Circle(0.9, color=C_BLUE, stroke_width=4).move_to(lc)
        t_up = Triangle(color=C_BLUE, fill_opacity=1, stroke_width=0).scale(0.13).rotate(-PI / 2).move_to(lc + UP * 0.9)
        t_dn = Triangle(color=C_BLUE, fill_opacity=1, stroke_width=0).scale(0.13).rotate(PI / 2).move_to(lc + DOWN * 0.9)
        v1 = Dot(lc + LEFT * 0.9, radius=0.08)
        v2 = Dot(lc + RIGHT * 0.9, radius=0.08)
        fey = VGroup(ph1, ph2, loop, t_up, t_dn, v1, v2)
        flab = T("费曼图内线：微扰展开中的一项", 28).move_to([2.4, -0.9, 0])
        fsub = T("不是探测器能捕捉的粒子", 26, C_GREY).move_to([2.4, -1.55, 0])
        self.beat("“虚粒子冒出又消失”只是比喻：它指的是微扰计算里的中间项。",
                  (Create(bub), FadeIn(pe, scale=0.3), FadeIn(pp, scale=0.3), FadeIn(vlab)),
                  (FadeIn(vmeta), GrowArrow(arr)),
                  (Create(fey, run_time=1.5), FadeIn(flab)),
                  FadeIn(fsub))
        self.clean()

    # ------------------------------------------------------------ 第五章
    def ch5(self):
        ye, yg = 2.0, -0.2
        xl = np.linspace(-4.6, 6.6, 300)
        bands = VGroup(Rectangle(width=11.2, height=1.2, stroke_width=0, fill_color=C_BLUE, fill_opacity=0.07).move_to([1.0, ye, 0]),
                       Rectangle(width=11.2, height=1.2, stroke_width=0, fill_color=C_YELLOW, fill_opacity=0.06).move_to([1.0, yg, 0]))
        le = T("电子场", 28, C_BLUE).move_to([-5.7, ye, 0])
        lg = T("电磁场", 28, C_YELLOW).move_to([-5.7, yg, 0])
        lps = eq(r"\psi", 40, C_BLUE).next_to(le, DOWN, buff=0.12)
        lA = eq(r"A_\mu", 40, C_YELLOW).next_to(lg, DOWN, buff=0.12)
        springs = VGroup(*[zigzag([x, ye - 0.65, 0], [x, yg + 0.65, 0], n=4, amp=0.08, color=C_TEAL, sw=2)
                           for x in np.arange(-4.0, 6.6, 1.3)]).set_opacity(0.6)
        lint = eq(r"\mathcal{L}_{\mathrm{int}}=-e\,\bar\psi\gamma^\mu\psi\,A_\mu", 46).move_to([0.8, 3.45, 0])
        alpha = eq(r"\alpha=\frac{e^2}{4\pi\varepsilon_0\hbar c}\approx\frac{1}{137}", 42).move_to([1.0, -1.78, 0])
        s = ValueTracker(0)
        ce = VMobject(stroke_color=C_BLUE, stroke_width=4)
        cg = VMobject(stroke_color=C_YELLOW, stroke_width=4)
        t1, t2 = eq(r"e^-", 36, C_BLUE), eq(r"e^-", 36, C_BLUE)
        tg = eq(r"\gamma", 36, C_YELLOW)
        xA, xB = -1.4, 2.6

        def u5(m):
            sv = s.get_value()
            if sv < 0.35:
                c1 = -3.8 + (xA + 3.8) * sv / 0.35
            else:
                c1 = xA + 1.6 * (sv - 0.35)
            if sv < 0.7:
                c2 = xB
            else:
                c2 = xB + 2.8 * (sv - 0.7) / 0.3
            cgp = xA + (xB - xA) * np.clip((sv - 0.35) / 0.35, 0, 1)
            ag = 0.45 * smoothstep((sv - 0.33) / 0.06) * (1 - smoothstep((sv - 0.68) / 0.05))
            ce.set_points_as_corners(xy(xl, ye + packet(xl, c1, 0.45, s=0.45, k=6) + packet(xl, c2, 0.45, s=0.45, k=6)))
            cg.set_points_as_corners(xy(xl, yg + packet(xl, cgp, ag, s=0.4, k=9)))
            t1.move_to([c1, ye + 0.85, 0])
            t2.move_to([c2, ye + 0.85, 0])
            tg.move_to([cgp, yg - 0.72, 0]).set_opacity(ag / 0.45)

        u5(None)
        drv = VGroup(ce, cg)
        drv.add_updater(u5)
        self.add(drv, t1, t2, tg)
        self.remove(drv, t1, t2, tg)
        self.beat("场与场之间的耦合就是相互作用，例如电子场与电磁场，强度 α≈1/137。",
                  (FadeIn(bands), FadeIn(le), FadeIn(lg), FadeIn(lps), FadeIn(lA), FadeIn(drv), FadeIn(t1), FadeIn(t2), FadeIn(tg)),
                  (LaggedStart(*[Create(z) for z in springs], lag_ratio=0.1), Write(lint)),
                  Write(alpha))
        self.beat("电子场的涟漪激发电磁场，放出光子；光子又能被别处的电子吸收。",
                  Tween(s, 0.35, run_time=2.0),
                  (Flash([xA, ye - 0.3, 0], color=C_WHITE, flash_radius=0.45),
                   Tween(s, 0.7, run_time=2.0)),
                  (Flash([xB, ye - 0.3, 0], color=C_WHITE, flash_radius=0.45),
                   Tween(s, 1.0, run_time=1.8)))
        drv.clear_updaters()
        self.clean()

        # --- 费曼图 + 电子磁矩：单圈顶点修正图（给出 g/2 的首项修正 α/2π）
        S_, P1 = np.array([-6.0, -1.3, 0]), np.array([-4.9, -0.35, 0])
        V_, P2 = np.array([-3.6, 0.8, 0]), np.array([-2.3, -0.35, 0])
        E_ = np.array([-1.2, -1.3, 0])
        e1 = VGroup(fline(S_, P1), fline(P1, V_), fline(V_, P2), fline(P2, E_))
        ext = wavy(V_, [-3.6, 2.85, 0], amp=0.12, waves=4)
        loop = wavy(P1, P2, amp=0.13, waves=5)
        vs = VGroup(*[Dot(p, radius=0.09) for p in (P1, V_, P2)])
        la = VGroup(eq(r"e^-", 34, C_BLUE).move_to([-6.25, -0.95, 0]), eq(r"e^-", 34, C_BLUE).move_to([-0.95, -0.95, 0]),
                    T("外磁场 γ", 24, C_YELLOW).move_to([-2.65, 2.6, 0]),
                    T("虚光子（圈）", 22, C_YELLOW).move_to([-3.6, -0.85, 0]))
        cap = T("单圈“顶点修正”图", 26, C_GREY).move_to([-3.6, 3.4, 0])
        vl = T("顶点 ∝ e", 24, C_GREY).next_to(V_, RIGHT, buff=0.3)
        tl = VGroup(Arrow([-6.0, -2.15, 0], [-1.2, -2.15, 0], buff=0, color=C_GREY, stroke_width=2),
                    T("时间", 22, C_GREY).move_to([-0.8, -2.15, 0]))
        hd = T("电子磁矩", 32, C_YELLOW).move_to([3.6, 2.7, 0])
        gv = eq(r"\tfrac{g}{2}=1.001\,159\,652\,180\,59\,(13)", 44).move_to([3.6, 1.75, 0])
        gs = T("实验值（2023）", 24, C_GREY).move_to([3.6, 1.0, 0])
        qd = T("QED 理论值与之吻合", 30).move_to([3.6, 0.0, 0])
        dv = VGroup(T("相对偏差", 28), eq(r"<10^{-9}", 40, C_TEAL)).arrange(RIGHT, buff=0.2).move_to([3.6, -0.75, 0])
        sch = VGroup(eq(r"\tfrac{g}{2}=1+\tfrac{\alpha}{2\pi}+\cdots", 38),
                     T("← 左图贡献首项修正（施温格，1948）", 20, C_GREY)).arrange(DOWN, buff=0.12).move_to([3.6, -1.75, 0])
        self.beat("费曼图是这些过程的记账法；由此算出的电子磁矩与实验吻合到十亿分之一。",
                  (Create(e1), FadeIn(tl), FadeIn(cap)),
                  (Create(ext), Create(loop), FadeIn(vs), FadeIn(la), FadeIn(vl)),
                  (FadeIn(hd), Write(gv), FadeIn(gs)),
                  (FadeIn(qd), FadeIn(dv), FadeIn(sch)))
        self.clean()

    # ------------------------------------------------------------ 第六章
    def make_stack(self, ys, h, gravity=False):
        groups = [
            ("夸克场 ×6", C_PURPLE, [r"u", r"d", r"c", r"s", r"t", r"b"]),
            ("轻子场 ×6", C_GREEN, [r"e", r"\mu", r"\tau", r"\nu_e", r"\nu_\mu", r"\nu_\tau"]),
            ("规范场", C_RED, [r"\gamma", r"g", r"W^\pm", r"Z"]),
            ("希格斯场", C_GOLD, [r"H"]),
        ]
        if gravity:
            groups = [("引力？", C_GREY, [r"?"])] + groups
        sheets = []
        cx, hw, sk = 0.9, 4.6, 0.35
        for (name, col, items), y in zip(groups, ys):
            pts = [[cx - hw + sk, y + h / 2, 0], [cx + hw + sk, y + h / 2, 0],
                   [cx + hw - sk, y - h / 2, 0], [cx - hw - sk, y - h / 2, 0]]
            if name == "引力？":
                sh = DashedVMobject(Polygon(*pts, color=col, stroke_width=3), num_dashes=40)
            else:
                sh = Polygon(*pts, color=col, stroke_width=2.5, fill_color=col, fill_opacity=0.12)
            lab = T(name, 28, col).move_to([-5.35, y, 0])
            n = len(items)
            xs = [cx] if n == 1 else np.linspace(cx - 3.6, cx + 3.6, n)
            chips = VGroup(*[chip(it, col, r=0.32 * h / 1.0 + 0.02, size=int(34 * min(1, h + 0.1))).move_to([x, y, 0])
                             for it, x in zip(items, xs)])
            extra = VGroup()
            if name == "规范场":
                extra.add(T("×8", 22, col).next_to(chips[1], RIGHT, buff=0.08))
            sheets.append(VGroup(sh, lab, chips, extra))
        return sheets

    def ch6(self):
        st = self.make_stack([2.9, 1.55, 0.2, -1.15], 1.0)
        self.beat("标准模型的物质场：六种夸克场，六种轻子场——含电子和三种中微子。",
                  (FadeIn(st[0][0]), FadeIn(st[0][1]), LaggedStart(*[FadeIn(c, scale=0.5) for c in st[0][2]], lag_ratio=0.15)),
                  (FadeIn(st[1][0]), FadeIn(st[1][1]), LaggedStart(*[FadeIn(c, scale=0.5) for c in st[1][2]], lag_ratio=0.15)))
        self.beat("规范场传递力：光子对应电磁力，八种胶子对应强力，W和Z对应弱力。",
                  (FadeIn(st[2][0]), FadeIn(st[2][1]), FadeIn(st[2][3]),
                   LaggedStart(*[FadeIn(c, scale=0.5) for c in st[2][2]], lag_ratio=0.25)))

        # --- 墨西哥帽
        ax = Axes(x_range=[-1.75, 1.75, 1], y_range=[0, 2.4, 1], x_length=6.0, y_length=3.9, tips=False,
                  axis_config={"include_ticks": False, "stroke_opacity": 0.6}).move_to([-3.3, 0.55, 0])
        Vh = lambda p: 0.55 * (p * p - 1) ** 2
        hat = ax.plot(Vh, x_range=[-1.75, 1.75], color=C_GOLD, stroke_width=5)
        ring = DashedVMobject(Ellipse(width=ax.c2p(1, 0)[0] - ax.c2p(-1, 0)[0], height=0.6, color=C_GOLD,
                                      stroke_width=2.5), num_dashes=40).move_to(ax.c2p(0, 0))
        rim = Ellipse(width=ax.c2p(1.75, 0)[0] - ax.c2p(-1.75, 0)[0], height=0.85, color=C_GOLD,
                      stroke_width=1.5, stroke_opacity=0.4).move_to(ax.c2p(0, Vh(1.75)))
        lphi = eq(r"\varphi", 38).next_to(ax.x_axis, RIGHT, buff=0.15)
        lV = eq(r"V(\varphi)", 38).next_to(ax.y_axis, UP, buff=0.12)
        pb = ValueTracker(0.03)
        hb = Dot(radius=0.15, color=C_WHITE)
        hb.add_updater(lambda m: m.move_to(ax.c2p(pb.get_value(), Vh(pb.get_value())) + UP * 0.16))
        fV = eq(r"V(\varphi)=-\mu^2|\varphi|^2+\lambda|\varphi|^4", 42).move_to([3.4, 3.1, 0])
        sheetH = st[3]
        vl = VGroup(eq(r"v\approx 246\ \mathrm{GeV}", 36, C_YELLOW)).next_to(ax.c2p(1, 0), DOWN, buff=0.45)
        self.beat("希格斯场的势能像墨西哥草帽：中心不是最低点，真空中的场停在 v≈246 GeV。",
                  (FadeIn(sheetH[0]), FadeIn(sheetH[1]), FadeIn(sheetH[2], scale=0.5)),
                  0.6,
                  FadeOut(VGroup(*[m for g in st for m in g])),
                  (Create(ax), Create(hat), FadeIn(lphi), FadeIn(lV)),
                  (Create(rim), Create(ring), FadeIn(hb), Write(fV)),
                  Tween(pb, 1.0, run_time=3.0, rate_func=lambda t: 1 - np.exp(-5 * t) * np.cos(7 * t) if t < 1 else 1),
                  FadeIn(vl, shift=UP * 0.2))
        hb.clear_updaters()

        data = [(r"t", 172.6, C_PURPLE, "172.6 GeV"), (r"Z", 91.19, C_RED, "91.2 GeV"), (r"W", 80.37, C_RED, "80.4 GeV"),
                (r"b", 4.18, C_PURPLE, "4.18 GeV"), (r"\tau", 1.777, C_GREEN, "1.78 GeV"), (r"c", 1.27, C_PURPLE, "1.27 GeV"),
                (r"\mu", 0.1057, C_GREEN, "106 MeV"), (r"e", 0.000511, C_GREEN, "0.511 MeV")]
        rows = VGroup()
        for i, (tx, m, col, txt) in enumerate(data):
            y = 2.15 - 0.5 * i
            L = (np.log10(m) + 4) / (np.log10(200) + 4) * 3.4
            lab = eq(tx, 34, col).move_to([1.15, y, 0])
            bar = Rectangle(width=L, height=0.3, stroke_width=0, fill_color=col, fill_opacity=0.75)
            bar.move_to([1.55 + L / 2, y, 0])
            val = T(txt, 22, C_GREY).next_to(bar, RIGHT, buff=0.15)
            rows.add(VGroup(lab, bar, val))
        cap = T("质量（对数刻度）· 中微子质量来源仍未确定", 22, C_GREY).move_to([3.7, -1.95, 0])
        self.beat("W、Z玻色子与夸克、带电轻子，都靠与这个背景值耦合获得质量。",
                  LaggedStart(*[AnimationGroup(FadeIn(r[0]), GrowFromEdge(r[1], LEFT), FadeIn(r[2])) for r in rows],
                              lag_ratio=0.18, run_time=2.6),
                  FadeIn(cap))
        self.clean()

        # --- 质子质量
        pc = np.array([-5.0, 2.45, 0])
        prot = VGroup(Circle(0.95, color=C_BLUE, stroke_width=3, fill_color=C_BLUE, fill_opacity=0.1).move_to(pc))
        qs = [pc + np.array([-0.4, 0.3, 0]), pc + np.array([0.42, 0.25, 0]), pc + np.array([0.0, -0.45, 0])]
        for a, b in ((0, 1), (1, 2), (2, 0)):
            prot.add(wavy(qs[a], qs[b], amp=0.06, waves=4, color=C_GREEN, sw=2.5))
        for q, tx in zip(qs, ["u", "u", "d"]):
            prot.add(ball(tx, C_RED, r=0.2, size=26).move_to(q))
        plab = T("质子", 26).next_to(prot, RIGHT, buff=0.2)
        bar = Rectangle(width=11.0, height=0.8, stroke_width=0, fill_color=C_BLUE, fill_opacity=0.55).move_to([0, 0.0, 0])
        sl = Rectangle(width=11.0 * 9 / 938.3, height=0.8, stroke_width=0, fill_color=C_GOLD, fill_opacity=1)
        sl.align_to(bar, LEFT).align_to(bar, DOWN)
        rest = Rectangle(width=11.0 - sl.width, height=0.8).align_to(bar, RIGHT).align_to(bar, DOWN)
        br = Brace(rest, UP, color=C_BLUE)
        brl = T("强相互作用能（夸克动能、胶子场能量…）≈ 99%", 26, C_BLUE).next_to(br, UP, buff=0.15)
        brl.shift(RIGHT * 0.6)
        tot = T("质子质量 938.3 MeV", 28).move_to([3.6, -0.8, 0])
        qa = Arrow([-4.6, -1.35, 0], sl.get_bottom() + DOWN * 0.05, buff=0.05, color=C_GOLD, stroke_width=4)
        ql = T("三个价夸克的质量 ≈ 9 MeV（约 1%）", 26, C_GOLD).move_to([-2.0, -1.6, 0])
        self.beat("但质子质量大多不来自希格斯：价夸克质量只占约1%，其余主要是强相互作用能。",
                  (FadeIn(prot), FadeIn(plab)),
                  (GrowFromEdge(bar, LEFT), FadeIn(tot)),
                  (FadeIn(sl), GrowArrow(qa), FadeIn(ql)),
                  (GrowFromCenter(br), FadeIn(brl)))
        self.clean()

        # --- 2012：希格斯玻色子（示意）
        ax = Axes(x_range=[100, 160, 10], y_range=[0, 1.25, 0.25], x_length=9.0, y_length=4.0, tips=False,
                  axis_config={"stroke_opacity": 0.7, "include_ticks": True},
                  x_axis_config={"numbers_to_include": list(range(100, 161, 10)), "font_size": 26}).move_to([0.3, 0.75, 0])
        bk = lambda m: 1.05 * np.exp(-(m - 100) / 38)
        sg = lambda m: 0.2 * np.exp(-(m - 125) ** 2 / (2 * 1.7 ** 2))
        ms = np.arange(101, 160, 2.0)
        rr = np.random.default_rng(11)
        pts = VGroup(*[Dot(ax.c2p(m, bk(m) + sg(m) + rr.normal(0, 0.018)), radius=0.06, color=C_WHITE) for m in ms])
        fit = ax.plot(lambda m: bk(m) + sg(m), x_range=[100, 160], color=C_RED, stroke_width=4)
        bkc = ax.plot(bk, x_range=[100, 160], color=C_RED, stroke_width=2.5, stroke_opacity=0.5)
        bkc = DashedVMobject(bkc, num_dashes=40)
        xl = eq(r"m_{\gamma\gamma}\ (\mathrm{GeV})", 32, C_GREY).move_to([3.8, -2.05, 0])
        hd = T("2012 · ATLAS 与 CMS", 30, C_GOLD).move_to([-3.6, 3.45, 0])
        note = T("示意图（非真实数据）", 24, C_GREY).move_to([4.2, 3.45, 0])
        pk = ax.c2p(125, bk(125) + sg(125))
        pa = Arrow(pk + UP * 1.05 + RIGHT * 0.6, pk + UP * 0.18, buff=0, color=C_YELLOW, stroke_width=4)
        pl = eq(r"125\ \mathrm{GeV}", 36, C_YELLOW).next_to(pa.get_start(), UP, buff=0.08)
        self.beat("2012年，LHC发现了希格斯场的量子：约125 GeV的希格斯玻色子。",
                  (Create(ax), FadeIn(hd), FadeIn(note), FadeIn(xl)),
                  (LaggedStart(*[FadeIn(p, scale=0.3) for p in pts], lag_ratio=0.03, run_time=1.4), Create(bkc)),
                  (Create(fit), GrowArrow(pa), FadeIn(pl)))
        self.clean()

        # --- 引力：尚未纳入
        st = self.make_stack([3.3, 2.25, 1.2, 0.15, -0.9], 0.8, gravity=True)
        rest = VGroup(*[VGroup(*g) for g in st[1:]])
        gl = T("低能下：有效场论可用 · 普朗克尺度：完整理论未知", 24, C_GREY).move_to([0.9, -1.75, 0])
        self.beat("引力在低能下可作为有效场论，但完整的量子引力理论仍未找到。",
                  FadeIn(rest, lag_ratio=0.1, run_time=1.2),
                  (Create(st[0][0]), FadeIn(st[0][1]), FadeIn(st[0][2])),
                  FadeIn(gl))
        self.clean()

        # --- 结尾：一道涟漪
        clk = self.clock()
        grid = FieldGrid(30, 12, 0.4, (0, 0.9), PAL_SHEET)

        def gfin(t):
            cx = -4.5 + 1.0 * t
            r2 = (grid.X - cx) ** 2 + (grid.Y - 0.9) ** 2
            return 0.06 + 1.0 * np.exp(-r2 / 0.6) * (0.75 + 0.25 * np.cos(4 * np.sqrt(r2) - 6 * t))

        tag = eq(r"e^-", 38)

        def ufin(m):
            t = clk.get_value()
            m.paint(gfin(t))
            tag.move_to([-4.5 + 1.0 * t, 0.9 + 0.75, 0])

        ufin(grid)
        self.beat("一个电子不是一颗小球，而是电子场上的一道涟漪。",
                  (FadeIn(grid), FadeIn(tag)),
                  lambda: grid.add_updater(ufin))
        grid.clear_updaters()
        self.clean(0.6)
