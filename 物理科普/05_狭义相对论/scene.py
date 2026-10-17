# -*- coding: utf-8 -*-
"""第 05 集 · 狭义相对论：光速不变带来的一切"""
import sys
from style import *

# style.py 在导入时把分辨率/帧率写死为 1080p30，会覆盖 -ql 预览参数；
# 这里在预览模式下恢复 480p15（不影响 build.py 的 -qh 成品渲染）。
_argv = " ".join(sys.argv)
if " -ql" in " " + _argv or "--quality l" in _argv or "-q l" in _argv:
    config.pixel_width, config.pixel_height, config.frame_rate = 854, 480, 15

GLOW = "#FFF6A0"


def mt(*parts, size=44, color=C_WHITE, **kw):
    """多段公式（用于 TransformMatchingTex）"""
    return MathTex(*parts, font_size=size, color=color, **kw)


def tri_wave(t, period):
    """光子在镜间往返的高度比例 0..1（单程用时 period）"""
    ph = (t / period) % 2.0
    return ph if ph <= 1 else 2 - ph


def gam(b):
    return 1.0 / np.sqrt(1.0 - b * b)


def lb(b, x, ct):
    """洛伦兹变换：静止系坐标 → 以 b 运动的参考系坐标"""
    g = gam(b)
    return g * (x - b * ct), g * (ct - b * x)


def clip_seg(p, q, R):
    """Liang–Barsky：把线段裁剪进 [-R,R]^2"""
    x0, y0 = p
    x1, y1 = q
    dx, dy = x1 - x0, y1 - y0
    t0, t1 = 0.0, 1.0
    for pp, qq in ((-dx, x0 + R), (dx, R - x0), (-dy, y0 + R), (dy, R - y0)):
        if abs(pp) < 1e-12:
            if qq < 0:
                return None
        else:
            r = qq / pp
            if pp < 0:
                t0 = max(t0, r)
            else:
                t1 = min(t1, r)
            if t0 > t1:
                return None
    return (x0 + t0 * dx, y0 + t0 * dy), (x0 + t1 * dx, y0 + t1 * dy)


class Video(Explainer):
    # ------------------------------------------------------------------ 工具
    def _make_sub(self, text):
        """字幕跟随相机（style.py 的字幕固定在场景坐标，相机移动时会跑出画面）"""
        g = super()._make_sub(text)
        fr = self.camera.frame
        W0 = config.frame_width
        c0 = g.get_center().copy()
        w0 = g.width
        last = [None]

        def upd(m):
            key = (round(fr.width, 5), *np.round(fr.get_center(), 5))
            if key == last[0]:
                return
            last[0] = key
            s = fr.width / W0
            m.set_width(w0 * s)
            m.move_to(fr.get_center() + s * c0)

        g.add_updater(upd)
        upd(g)
        return g

    def beat(self, text, *steps, extra=0.0):
        """一条字幕下顺序执行多个步骤；数字=等待，可调用=执行，列表=同时播放（末尾可带 run_time）"""
        self._set_sub(text)
        need = reading_time(text) + extra
        t0 = self._now()
        for st in steps:
            if isinstance(st, (int, float)):
                self.wait(st)
            elif callable(st) and not isinstance(st, Animation):
                st()
            elif isinstance(st, (list, tuple)):
                items = list(st)
                kw = {}
                if items and isinstance(items[-1], (int, float)):
                    kw["run_time"] = items.pop()
                self.play(*items, **kw)
            else:
                self.play(st)
        rest = need - (self._now() - t0)
        if rest > 0.05:
            self.wait(rest)

    def clean(self, run_time=0.5):
        """清场：先冻结所有更新器再淡出"""
        mobs = [m for m in self.mobjects if m is not self._sub]
        for m in mobs:
            m.clear_updaters()
        if mobs:
            self.play(*[FadeOut(m) for m in mobs], run_time=run_time)
        self.remove(*mobs)

    # ------------------------------------------------------------------ 主体
    def construct(self):
        self.title_card("狭义相对论", "光速不变带来的一切")
        self.chapter("第一章", "光速之谜")
        self.part_light_puzzle()
        self.chapter("第二章", "时间膨胀")
        self.part_light_clock()
        self.part_gamma()
        self.part_muons()
        self.chapter("第三章", "长度收缩与同时性")
        self.part_length()
        self.part_simultaneity()
        self.chapter("第四章", "时空图与双生子")
        self.part_minkowski()
        self.part_twins()
        self.chapter("第五章", "质能与速度极限")
        self.part_energy()
        self.end_card([
            "光速对所有惯性观察者都相同",
            "运动的钟变慢，运动的尺沿运动方向缩短",
            "同时是相对的，时空间隔是绝对的",
            "双生子：惯性世界线的固有时最长",
            "E = mc²，有质量的物体到不了光速",
        ])

    # ================================================================ 第一章
    def make_train(self):
        body = RoundedRectangle(width=3.6, height=1.0, corner_radius=0.15, stroke_color=C_BLUE,
                                fill_color=C_BLUE, fill_opacity=0.15, stroke_width=3)
        wins = VGroup(*[RoundedRectangle(width=0.5, height=0.36, corner_radius=0.05, stroke_color=C_BLUE,
                                         stroke_width=2) for _ in range(4)]).arrange(RIGHT, buff=0.32)
        wins.move_to(body).shift(UP * 0.12)
        wheels = VGroup(*[Circle(0.17, color=C_GREY, stroke_width=3).move_to(
            body.get_bottom() + RIGHT * dx + DOWN * 0.12) for dx in (-1.2, 0, 1.2)])
        head = Circle(0.12, color=C_WHITE, stroke_width=3).move_to(body.get_top() + UP * 0.55)
        torso = Line(head.get_bottom(), body.get_top(), color=C_WHITE, stroke_width=3)
        arm = Line(torso.get_center(), torso.get_center() + RIGHT * 0.35 + UP * 0.12, color=C_WHITE, stroke_width=3)
        return VGroup(body, wins, wheels, head, torso, arm)

    def part_light_puzzle(self):
        ground_y = -1.5
        ground = Line([-7.2, ground_y, 0], [7.2, ground_y, 0], color=C_GREY, stroke_width=3)
        posts = VGroup(*[Line([x, ground_y, 0], [x, ground_y - 0.25, 0], color=C_GREY, stroke_width=2)
                         for x in np.arange(-7, 7.1, 1.0)])
        plat = T("站台", 24, C_GREY).move_to([6.2, ground_y - 0.5, 0])
        train = self.make_train()
        train.move_to([-4.5, ground_y + 0.17 + 0.12 + 0.5, 0])
        tr = ValueTracker(0)
        x_start = -4.5
        train.add_updater(lambda m: m.move_to([x_start + 1.0 * tr.get_value(), m.get_y(), 0]))
        hand = train[5].get_end().copy()
        ball = Dot(radius=0.11, color=C_GOLD)

        def ball_pos():
            t = tr.get_value()
            return np.array([x_start + 1.0 * t + hand[0] - x_start + 2.0 * t, hand[1], 0])

        ball.add_updater(lambda m: m.move_to(ball_pos()))
        trail = TracedPath(ball.get_center, stroke_color=C_GOLD, stroke_width=2, stroke_opacity=0.5)

        # 三支速度箭头（头尾相接）
        sc = 1.2
        a0 = np.array([-2.4, 2.75, 0])
        av = Arrow(a0, a0 + RIGHT * sc, buff=0, color=C_BLUE, stroke_width=6, max_tip_length_to_length_ratio=0.25)
        au = Arrow(av.get_end(), av.get_end() + RIGHT * 2 * sc, buff=0, color=C_GOLD, stroke_width=6,
                   max_tip_length_to_length_ratio=0.15)
        aw = Arrow(a0 + DOWN * 0.8, a0 + DOWN * 0.8 + RIGHT * 3 * sc, buff=0, color=C_GREEN, stroke_width=6,
                   max_tip_length_to_length_ratio=0.1)
        lv = T("车 10", 24, C_BLUE).next_to(av, UP, buff=0.12)
        lu = T("球相对车 20", 24, C_GOLD).next_to(au, UP, buff=0.12)
        lw = T("站台上看 30 米/秒", 24, C_GREEN).next_to(aw, DOWN, buff=0.12)
        law = eq(r"u = u' + v", 44).move_to([4.6, 2.35, 0])
        note = T("（只在低速下近似成立）", 22, C_GREY).next_to(law, DOWN, buff=0.15)

        self.add(ball, trail)
        self.beat("车速10米/秒，向前扔出20米/秒的球，站台上看球速是30米/秒。",
                  [Create(ground), FadeIn(posts), FadeIn(plat), FadeIn(train), FadeIn(ball), 0.6],
                  [tr.animate(rate_func=linear).set_value(2.7), 3.0],
                  [GrowArrow(av), FadeIn(lv), 0.6],
                  [GrowArrow(au), FadeIn(lu), 0.6],
                  [GrowArrow(aw), FadeIn(lw), Write(law), FadeIn(note), 1.0])
        self.clean()

        # ---- 麦克斯韦：电磁波
        ph = ValueTracker(0)
        x0, x1 = -6.5, 1.2
        axis = Arrow([x0, 0.9, 0], [x1 + 0.4, 0.9, 0], buff=0, color=C_GREY, stroke_width=2,
                     max_tip_length_to_length_ratio=0.03)

        def wave(amp, color, k=2.2):
            return always_redraw(lambda: ParametricFunction(
                lambda x: np.array([x, 0.9 + amp * np.sin(k * (x - x0) - ph.get_value()), 0]),
                t_range=[x0, x1, 0.04], color=color, stroke_width=4))

        ew = wave(1.3, C_YELLOW)
        bw = wave(0.55, C_BLUE)
        bw.set_stroke(opacity=0.7)
        le = T("电场 E", 24, C_YELLOW).move_to([-6.0, 2.6, 0])
        lbm = T("磁场 B", 24, C_BLUE).move_to([-4.6, 2.6, 0])
        ceq = eq(r"c = \frac{1}{\sqrt{\mu_0 \varepsilon_0}}", 56).move_to([4.5, 1.8, 0])
        cval = eq(r"\approx 3\times 10^{8}\ \mathrm{m/s}", 44, C_YELLOW).next_to(ceq, DOWN, buff=0.4)
        cnote = T("约 30 万千米/秒", 26, C_GREY).next_to(cval, DOWN, buff=0.25)
        q = T("相对于谁？", 40, C_RED).move_to([4.5, -1.6, 0])
        self.add(ew, bw)
        self.beat("麦克斯韦方程组却给出：光速是定值c，约30万千米/秒。",
                  [FadeIn(axis), FadeIn(le), FadeIn(lbm), Write(ceq),
                   ph.animate.set_value(6), 2.0],
                  [FadeIn(cval), FadeIn(cnote), ph.animate.set_value(12), 2.0],
                  [FadeIn(q, scale=1.2), ph.animate.set_value(15), 1.0])
        self.clean()

        # ---- 以太风 + 迈克耳孙干涉仪
        rng = np.random.default_rng(3)
        dashes = VGroup()
        for _ in range(16):
            x, y = rng.uniform(-7, 7), rng.uniform(-2.3, 3.6)
            d = Line([x, y, 0], [x + 0.5, y, 0], color=C_GREY, stroke_width=2, stroke_opacity=0.45)
            dashes.add(d)

        def drift(m, dt):
            for d in m:
                d.shift(LEFT * 1.6 * dt)
                if d.get_right()[0] < -7.2:
                    d.shift(RIGHT * 14.4)

        dashes.add_updater(drift)
        wind = T("← “以太风”？", 26, C_GREY).move_to([4.6, -1.6, 0])
        src = Dot([-5.6, -0.4, 0], radius=0.12, color=C_YELLOW)
        lsrc = T("光源", 22, C_GREY).next_to(src, DOWN, buff=0.15)
        bs_c = np.array([-2.6, -0.4, 0])
        bs = Line(bs_c + np.array([-0.35, -0.35, 0]), bs_c + np.array([0.35, 0.35, 0]), color=C_WHITE, stroke_width=4)
        m1 = Line([0.6, -1.0, 0], [0.6, 0.2, 0], color=C_WHITE, stroke_width=7)
        m2 = Line([-3.2, 2.4, 0], [-2.0, 2.4, 0], color=C_WHITE, stroke_width=7)
        det = Square(0.45, color=C_TEAL, stroke_width=3).move_to([-2.6, -2.0, 0])
        ldet = T("探测器", 22, C_TEAL).next_to(det, RIGHT, buff=0.15)
        beams = VGroup(
            Line(src.get_center(), bs_c), Line(bs_c, [0.6, -0.4, 0]), Line(bs_c, [-2.6, 2.4, 0]),
            Line(bs_c, det.get_top())).set_stroke(C_YELLOW, 3, 0.8)
        mm = T("1887 · 迈克耳孙–莫雷干涉仪", 26, C_WHITE).move_to([-2.6, 3.4, 0])
        # 干涉条纹
        fc = np.array([4.6, 1.0, 0])
        frame = Rectangle(width=3.6, height=1.8, color=C_GREY, stroke_width=2).move_to(fc)
        period = 0.6
        bars = VGroup(*[Rectangle(width=0.22, height=1.6, stroke_width=0, fill_color=C_YELLOW,
                                  fill_opacity=0.65).move_to(fc + RIGHT * period * k) for k in range(-2, 3)])
        sh = ValueTracker(0)
        exp_line = always_redraw(lambda: DashedLine(fc + DOWN * 1.0 + RIGHT * sh.get_value(),
                                                    fc + UP * 1.0 + RIGHT * sh.get_value(),
                                                    color=C_RED, stroke_width=4))
        obs_line = Line(fc + DOWN * 1.0, fc + UP * 1.0, color=C_GREEN, stroke_width=4)
        lexp = T("预期：移动约 0.4 条", 24, C_RED).move_to(fc + UP * 1.35)
        lobs = T("实测：几乎不动（< 0.02 条）", 24, C_GREEN).move_to(fc + DOWN * 1.35)
        self.add(dashes)
        self.beat("人们猜想光在“以太”中传播，可1887年迈克耳孙–莫雷实验没测到以太风。",
                  [FadeIn(wind), FadeIn(mm), FadeIn(src), FadeIn(lsrc), Create(bs), Create(m1), Create(m2),
                   Create(det), FadeIn(ldet), 1.0],
                  [Create(beams), FadeIn(frame), FadeIn(bars), 1.0],
                  [FadeIn(exp_line), FadeIn(lexp), 0.4],
                  [sh.animate.set_value(0.4 * period), 1.0],
                  [FadeIn(obs_line), FadeIn(lobs), sh.animate.set_value(0), 1.0],
                  [sh.animate.set_value(0.4 * period), 1.0])
        self.clean()

        # ---- 两条假设
        def card(x, title, body, color):
            box = RoundedRectangle(width=6.3, height=2.2, corner_radius=0.2, stroke_color=color, stroke_width=3,
                                   fill_color=color, fill_opacity=0.06).move_to([x, 2.2, 0])
            tt = T(title, 32, color, weight=BOLD)
            bb = VGroup(*[T(b, 26) for b in body]).arrange(DOWN, buff=0.15)
            g = VGroup(tt, bb).arrange(DOWN, buff=0.3).move_to(box)
            return VGroup(box, g)

        c1 = card(-3.45, "假设一 · 相对性原理", ["物理定律在所有惯性系中", "形式相同"], C_BLUE)
        c2 = card(3.45, "假设二 · 光速不变", ["真空光速对所有惯性观察者都是 c", "与光源运动无关"], C_GOLD)
        yr = T("1905 · 爱因斯坦", 26, C_GREY).move_to([0, 3.65, 0])
        # 假设一配图：两个参考系中同一条定律
        f1 = VGroup()
        for x, name in ((-5.0, "地面"), (-1.9, "火车")):
            b = RoundedRectangle(width=2.6, height=1.3, corner_radius=0.1, color=C_BLUE, stroke_width=2).move_to([x, -0.6, 0])
            e = eq(r"\nabla\!\cdot\!\mathbf{E}=\rho/\varepsilon_0", 30).move_to(b)
            n = T(name, 22, C_GREY).next_to(b, DOWN, buff=0.12)
            f1.add(VGroup(b, e, n))
        # 假设二配图：运动光源发出的光
        lamp_t = ValueTracker(0)
        lamp = VGroup(Rectangle(width=0.7, height=0.4, color=C_GOLD, stroke_width=3, fill_opacity=0.2),
                      T("光源", 18, C_GOLD))
        lamp.add_updater(lambda m: m.move_to([1.2 + 0.7 * lamp_t.get_value(), -0.6, 0]))
        lamp_arrow = always_redraw(lambda: Arrow(lamp.get_bottom() + DOWN * 0.15 + LEFT * 0.3,
                                                 lamp.get_bottom() + DOWN * 0.15 + RIGHT * 0.45, buff=0,
                                                 color=C_GOLD, stroke_width=4, max_tip_length_to_length_ratio=0.35))
        lv2 = T("v", 22, C_GOLD)
        lv2.add_updater(lambda m: m.next_to(lamp_arrow, RIGHT, buff=0.08))
        phot = Dot(radius=0.1, color=GLOW)
        phot.add_updater(lambda m: m.move_to([min(1.6 + 2.2 * lamp_t.get_value(), 6.6), -0.6, 0]))
        lc = eq(r"c", 36, C_YELLOW)
        lc.add_updater(lambda m: m.next_to(phot, UP, buff=0.12))
        nc = eq(r"\text{not } c+v", 28, C_GREY).move_to([5.4, -1.5, 0])
        self.beat("1905年，爱因斯坦提出两条假设。一：物理定律在所有惯性系中相同；",
                  [FadeIn(yr), FadeIn(c1, shift=UP * 0.2), 1.0],
                  [LaggedStart(*[FadeIn(g) for g in f1], lag_ratio=0.4), 1.2])
        self.add(lamp, lamp_arrow, lv2)
        self.beat("二：真空中的光速对所有惯性观察者都是c，与光源运动无关。",
                  [FadeIn(c2, shift=UP * 0.2), FadeIn(lamp), 1.0],
                  lambda: self.add(phot, lc),
                  [lamp_t.animate.set_value(2.3), 2.3],
                  [FadeIn(nc), 0.6])
        self.clean()

        cv = eq(r"c + v", 90).move_to([0, 1.6, 0])
        cross = Cross(cv, stroke_color=C_RED, stroke_width=8)
        cc = eq(r"c", 110, C_YELLOW).move_to([0, 1.6, 0])
        tw = VGroup(T("时间", 60, C_BLUE, weight=BOLD), T("空间", 60, C_TEAL, weight=BOLD)).arrange(RIGHT, buff=2.0)
        tw.move_to([0, -0.9, 0])
        self.beat("要保住光速c，时间和空间必须让步。",
                  [Write(cv), 0.7], [Create(cross), 0.5],
                  [ReplacementTransform(VGroup(cv, cross), cc), FadeIn(tw, shift=UP * 0.3), 0.8],
                  [ApplyWave(tw, amplitude=0.25), 1.2])
        self.clean()

    # ================================================================ 第二章：光钟
    def part_light_clock(self):
        c, L, yb = 2.0, 2.4, -1.5
        yt = yb + L
        tau = L / c                       # 1.2
        beta = 0.6
        v = beta * c                      # 1.2
        dt_m = tau * gam(beta)            # 1.5
        Tr, Tm = ValueTracker(0), ValueTracker(0)

        def mirrors(x):
            return VGroup(Line([x - 0.55, yt, 0], [x + 0.55, yt, 0]), Line([x - 0.55, yb, 0], [x + 0.55, yb, 0])
                          ).set_stroke(C_WHITE, 7)

        xr = -5.2
        rest = mirrors(xr)
        pr = Dot(radius=0.1, color=GLOW)
        pr.add_updater(lambda m: m.move_to([xr, yb + L * tri_wave(Tr.get_value(), tau), 0]))
        brace = BraceBetweenPoints([xr - 0.75, yt, 0], [xr - 0.75, yb, 0], direction=LEFT, color=C_GREY)
        lL = eq("L", 40).next_to(brace, LEFT, buff=0.12)
        lrest = T("静止的光钟", 26, C_GREY).move_to([xr, yt + 0.45, 0])
        dtau = eq(r"\Delta\tau = L/c", 40, C_TEAL).move_to([xr, yt + 1.15, 0])

        x0 = -2.4
        mov = mirrors(x0)
        mov.add_updater(lambda m: m.move_to([x0 + v * Tm.get_value(), (yt + yb) / 2, 0]))
        pm = Dot(radius=0.1, color=GLOW)
        pm.add_updater(lambda m: m.move_to([x0 + v * Tm.get_value(), yb + L * tri_wave(Tm.get_value(), dt_m), 0]))
        varr = Arrow([x0 - 0.4, yb - 0.45, 0], [x0 + 0.6, yb - 0.45, 0], buff=0, color=C_RED, stroke_width=5,
                     max_tip_length_to_length_ratio=0.3)
        varr.add_updater(lambda m: m.move_to([x0 + v * Tm.get_value(), yb - 0.45, 0]))
        lvv = eq("v", 34, C_RED)
        lvv.add_updater(lambda m: m.next_to(varr, RIGHT, buff=0.1))
        lmov = T("运动的光钟（地面看）", 26, C_GREY).move_to([x0 + 1.8, yt + 0.45, 0])

        # 读数
        cnt_r = DecimalNumber(0, num_decimal_places=1, font_size=36, color=C_TEAL)
        cnt_m = DecimalNumber(0, num_decimal_places=1, font_size=36, color=C_GOLD)
        base = [0.0]
        cnt_r.add_updater(lambda m: m.set_value((Tr.get_value() - base[0]) / tau))
        cnt_m.add_updater(lambda m: m.set_value(Tm.get_value() / dt_m))
        rl1 = T("静止钟 嘀嗒数", 24, C_TEAL)
        rl2 = T("运动钟 嘀嗒数", 24, C_GOLD)
        read = VGroup(VGroup(rl1, cnt_r).arrange(RIGHT, buff=0.3), VGroup(rl2, cnt_m).arrange(RIGHT, buff=0.3)
                      ).arrange(DOWN, aligned_edge=LEFT, buff=0.35).move_to([4.9, -0.1, 0])

        self.add(rest, pr)
        self.beat("光钟：光子在镜间往返一趟算一次嘀嗒，用时Δτ = L/c。",
                  [FadeIn(rest), FadeIn(pr), FadeIn(lrest), GrowFromCenter(brace), FadeIn(lL), 0.8],
                  [Tr.animate.set_value(2 * tau), Write(dtau), 2.4])
        trace = TracedPath(pm.get_center, stroke_color=C_YELLOW, stroke_width=3)
        base[0] = Tr.get_value()
        self.add(mov, pm, trace, varr, lvv)
        self.beat("让光钟以v运动：地面看来光子走斜线，路程更长，而光速仍是c。",
                  [FadeIn(mov), FadeIn(lmov), FadeIn(read), GrowArrow(varr), 0.7],
                  [Tr.animate.set_value(base[0] + 2 * dt_m), Tm.animate.set_value(2 * dt_m), 4.5])
        # 冻结并取出第一个直角三角形
        A = np.array([x0, yb, 0])
        B = np.array([x0 + v * dt_m, yt, 0])
        F = np.array([x0 + v * dt_m, yb, 0])
        trig = VGroup(Line(A, B, color=C_YELLOW, stroke_width=6), Line(A, F, color=C_RED, stroke_width=6),
                      Line(F, B, color=C_TEAL, stroke_width=6))
        for m in (pr, pm, mov, varr, lvv, cnt_r, cnt_m):
            m.clear_updaters()
        self.play(FadeIn(trig), run_time=0.5)
        self.play(*[FadeOut(m) for m in (rest, pr, brace, lL, lrest, dtau, mov, pm, trace, varr, lvv, lmov, read)],
                  trig.animate.scale(1.15).move_to([-4.6, -0.2, 0]), run_time=1.0)
        A2, F2, B2 = trig[1].get_start(), trig[1].get_end(), trig[2].get_end()
        ra = RightAngle(trig[1], trig[2], length=0.25, quadrant=(-1, 1), color=C_GREY)
        hyp_lab = eq(r"c\Delta t", 40, C_YELLOW).move_to((A2 + B2) / 2 + np.array([-0.55, 0.35, 0]))
        base_lab = eq(r"v\Delta t", 40, C_RED).next_to(trig[1], DOWN, buff=0.15)
        vert_lab = eq(r"L = c\Delta\tau", 40, C_TEAL).next_to(trig[2], RIGHT, buff=0.15)
        perp = T("垂直于运动方向的长度不变", 20, C_GREY).next_to(base_lab, DOWN, buff=0.12)
        e1 = mt(r"(c\Delta t)^2", "=", r"(v\Delta t)^2", "+", r"(c\Delta\tau)^2").move_to([2.6, 2.6, 0])
        e1[0].set_color(C_YELLOW)
        e1[2].set_color(C_RED)
        e1[4].set_color(C_TEAL)
        self.beat("斜边cΔt，底边vΔt，竖边L = cΔτ。用勾股定理：",
                  [FadeIn(ra), Write(hyp_lab), 0.6], [Write(base_lab), 0.5], [Write(vert_lab), FadeIn(perp), 0.6],
                  [Write(e1), 1.2])
        e2 = mt(r"\Delta t^2", r"(c^2 - v^2)", "=", r"c^2\Delta\tau^2").move_to([2.6, 1.4, 0])
        e3 = mt(r"\Delta t", "=", r"\frac{\Delta\tau}{\sqrt{1 - v^2/c^2}}").move_to([2.6, 1.3, 0])
        e4 = mt(r"\Delta t", "=", r"\gamma", r"\,\Delta\tau", size=64).move_to([2.6, 0.0, 0])
        e4[2].set_color(C_YELLOW)
        gdef = mt(r"\gamma", "=", r"\frac{1}{\sqrt{1 - v^2/c^2}}", size=44).move_to([2.6, -1.5, 0])
        gdef[0].set_color(C_YELLOW)
        box = SurroundingRectangle(e4, color=C_YELLOW, buff=0.2, corner_radius=0.1)
        self.beat("解出Δt = γΔτ：运动的钟慢了γ倍。",
                  [TransformMatchingTex(e1.copy(), e2), 1.2], 0.3,
                  [TransformMatchingTex(e2, e3), 1.2], 0.3,
                  [TransformMatchingTex(e3.copy(), e4), FadeIn(gdef, shift=UP * 0.2), 1.2],
                  [Create(box), 0.6])
        self.clean()

    def part_gamma(self):
        ax = Axes(x_range=[0, 1.0, 0.2], y_range=[0, 7, 1], x_length=7.2, y_length=5.0,
                  axis_config={"color": C_GREY, "include_tip": False, "font_size": 26},
                  x_axis_config={"numbers_to_include": [0.2, 0.4, 0.6, 0.8, 1.0]},
                  y_axis_config={"numbers_to_include": [1, 2, 3, 4, 5, 6, 7]}).move_to([-1.4, 0.65, 0])
        xl = eq(r"v/c", 34).next_to(ax.x_axis.get_right(), RIGHT, buff=0.2)
        yl = eq(r"\gamma", 40, C_YELLOW).next_to(ax.y_axis.get_top(), LEFT, buff=0.15)
        bmax = np.sqrt(1 - 1 / 49.0)
        curve = ax.plot(lambda b: gam(b), x_range=[0, bmax, 0.002], color=C_YELLOW, stroke_width=5)
        asym = DashedLine(ax.c2p(1, 0), ax.c2p(1, 7), color=C_RED, stroke_width=3)
        lasym = eq(r"v = c", 30, C_RED).next_to(ax.c2p(1, 6.3), RIGHT, buff=0.3)
        bt = ValueTracker(0.0)
        dot = Dot(radius=0.11, color=C_WHITE)
        dot.add_updater(lambda m: m.move_to(ax.c2p(bt.get_value(), gam(bt.get_value()))))
        gdef = mt(r"\gamma", "=", r"\frac{1}{\sqrt{1 - v^2/c^2}}", size=44).move_to([4.9, 2.8, 0])
        gdef[0].set_color(C_YELLOW)
        bnum = DecimalNumber(0, num_decimal_places=3, font_size=38)
        gnum = DecimalNumber(1, num_decimal_places=2, font_size=38, color=C_YELLOW)
        bnum.add_updater(lambda m: m.set_value(bt.get_value()))
        gnum.add_updater(lambda m: m.set_value(gam(bt.get_value())))
        r1 = VGroup(eq(r"v/c =", 38), bnum).arrange(RIGHT, buff=0.2)
        r2 = VGroup(eq(r"\gamma =", 38, C_YELLOW), gnum).arrange(RIGHT, buff=0.2)
        rd = VGroup(r1, r2).arrange(DOWN, aligned_edge=LEFT, buff=0.3).move_to([5.2, 0.9, 0])
        b2 = np.sqrt(3) / 2
        h1 = DashedLine(ax.c2p(0, 2), ax.c2p(b2, 2), color=C_GREY, stroke_width=2)
        v1 = DashedLine(ax.c2p(b2, 0), ax.c2p(b2, 2), color=C_GREY, stroke_width=2)
        mark = T("地面 2 秒，钟走 1 秒", 24, C_TEAL).move_to([5.2, -0.6, 0])
        self.add(dot)
        self.beat("γ叫洛伦兹因子：0.87c时约为2，趋近光速时趋于无穷。",
                  [Create(ax), FadeIn(xl), FadeIn(yl), FadeIn(gdef), 0.8],
                  [Create(curve), FadeIn(rd), bt.animate.set_value(b2), 2.4],
                  [Create(h1), Create(v1), FadeIn(mark), 0.6],
                  [bt.animate.set_value(0.985), Create(asym), FadeIn(lasym), 2.2])
        self.clean()

        # ---- 一切过程同样变慢 + 相互性
        def clock(center, color):
            face = Circle(1.1, color=color, stroke_width=4).move_to(center)
            ticks = VGroup(*[Line(center + 0.92 * np.array([np.sin(a), np.cos(a), 0]),
                                  center + 1.05 * np.array([np.sin(a), np.cos(a), 0]), color=color, stroke_width=3)
                             for a in np.linspace(0, TAU, 12, endpoint=False)])
            hand = Line(center, center + UP * 0.85, color=C_WHITE, stroke_width=5)
            return VGroup(face, ticks, hand)

        cA, cB = np.array([-3.6, 1.2, 0]), np.array([3.6, 1.2, 0])
        kA, kB = clock(cA, C_TEAL), clock(cB, C_GOLD)
        rA, rB = ValueTracker(1.0), ValueTracker(0.5)
        w = TAU / 3.0
        kA[2].add_updater(lambda m, dt: m.rotate(-w * rA.get_value() * dt, about_point=cA))
        kB[2].add_updater(lambda m, dt: m.rotate(-w * rB.get_value() * dt, about_point=cB))

        def heart(center, rt):
            h = MathTex(r"\heartsuit", color=C_RED, font_size=60).move_to(center)
            h0 = h.height
            ph = [0.0]

            def upd(m, dt):
                ph[0] += rt.get_value() * dt * 1.6
                s = 1 + 0.25 * max(0.0, np.sin(TAU * ph[0])) ** 6
                m.set_height(h0 * s)
                m.move_to(center)

            h.add_updater(upd)
            return h

        hA, hB = heart(cA + DOWN * 1.75, rA), heart(cB + DOWN * 1.75, rB)
        ship = VGroup(RoundedRectangle(width=3.4, height=3.6, corner_radius=0.4, color=C_GOLD, stroke_width=2,
                                       stroke_opacity=0.6),
                      ).move_to(cB + DOWN * 0.55)
        nose = Polygon(ship.get_corner(UR) + DOWN * 0.6, ship.get_corner(DR) + UP * 0.6,
                       ship.get_right() + RIGHT * 0.8, color=C_GOLD, stroke_width=2, stroke_opacity=0.6)
        lA = T("地面", 26, C_TEAL).next_to(kA, UP, buff=0.2)
        lB = T("飞船（γ = 2）", 26, C_GOLD).next_to(kB, UP, buff=0.2)
        arB = Arrow(cB + DOWN * 2.55 + LEFT * 0.6, cB + DOWN * 2.55 + RIGHT * 0.6, buff=0, color=C_GOLD,
                    stroke_width=5)
        arA = Arrow(cA + DOWN * 2.55 + RIGHT * 0.6, cA + DOWN * 2.55 + LEFT * 0.6, buff=0, color=C_TEAL,
                    stroke_width=5)
        hdr1 = T("地面看：飞船里的一切都慢一半", 28, C_WHITE).move_to([0, 3.55, 0])
        hdr2 = T("飞船看：地面的钟慢一半", 28, C_WHITE).move_to([0, 3.55, 0])
        self.add(kA, kB, hA, hB)
        self.beat("在地面看来，飞船里的一切过程都同样变慢，包括心跳。",
                  [FadeIn(kA), FadeIn(kB), FadeIn(hA), FadeIn(hB), FadeIn(ship), FadeIn(nose), FadeIn(lA),
                   FadeIn(lB), GrowArrow(arB), FadeIn(hdr1), 1.0])
        lB2 = T("飞船", 26, C_GOLD).move_to(lB)
        lA2 = T("地面（γ = 2）", 26, C_TEAL).move_to(lA)
        self.beat("而且是相互的：飞船上的人也看到地面的钟变慢。",
                  [FadeOut(arB), GrowArrow(arA), FadeTransform(hdr1, hdr2),
                   FadeTransform(lA, lA2), FadeTransform(lB, lB2),
                   rA.animate.set_value(0.5), rB.animate.set_value(1.0), 1.2])
        self.clean()

    # ================================================================ μ子
    def part_muons(self):
        top, gy = 2.75, -2.15
        s = (top - gy) / 15.0           # 每千米的画面长度
        N = 40
        tau = 2.197
        lam0 = 0.998 * 0.299792458 * tau          # ≈0.657 km
        lam1 = lam0 * gam(0.998)                  # ≈10.4 km
        cols = [(-3.3, lam0, C_RED), (3.0, lam1, C_GREEN)]
        axis = Line([-6.4, gy, 0], [-6.4, top, 0], color=C_GREY, stroke_width=2)
        ticks = VGroup()
        for km in (0, 5, 10, 15):
            y = gy + s * km
            ticks.add(Line([-6.5, y, 0], [-6.3, y, 0], color=C_GREY, stroke_width=2))
            ticks.add(T(f"{km}", 20, C_GREY).next_to([-6.5, y, 0], LEFT, buff=0.08))
        ticks.add(T("高度/km", 20, C_GREY).move_to([-6.25, top + 0.4, 0]))
        air = VGroup(*[Rectangle(width=4.6, height=top - gy, stroke_width=0, fill_color=C_BLUE,
                                 fill_opacity=0.10).move_to([x, (top + gy) / 2, 0]) for x, _, _ in cols])
        ground = VGroup(*[Line([x - 2.3, gy, 0], [x + 2.3, gy, 0], color=C_GREEN, stroke_width=4)
                          for x, _, _ in cols])
        h1 = T("若无时间膨胀", 28, C_RED).move_to([cols[0][0], 3.6, 0])
        h2 = T("相对论（γ ≈ 16）", 28, C_GREEN).move_to([cols[1][0], 3.6, 0])
        s1 = T("以 0.998c 飞行，平均 ≈ 0.66 km", 22, C_GREY).move_to([cols[0][0], 3.15, 0])
        s2 = T("平均飞行 ≈ 10.4 km", 22, C_GREY).move_to([cols[1][0], 3.15, 0])
        rng = np.random.default_rng(7)
        groups, trackers = [], []
        for x, lam, col in cols:
            D = -lam * np.log(1 - (np.arange(N) + 0.5) / N)
            rng.shuffle(D)
            xs = x + rng.uniform(-2.0, 2.0, N)
            off = rng.uniform(0, 0.6, N)
            dots = VGroup(*[Dot([xs[i], top - s * 0.0, 0], radius=0.065, color=C_YELLOW) for i in range(N)])
            d = ValueTracker(0)
            state = np.zeros(N, dtype=int)

            def upd(m, d=d, D=D, xs=xs, off=off, state=state):
                dv = d.get_value()
                for i, dot in enumerate(m):
                    z = max(0.0, dv - off[i])
                    if state[i] == 0:
                        if z >= D[i] and D[i] < 15:
                            state[i] = 1
                            dot.set_color(C_GREY).set_opacity(0.35).scale(0.7)
                        elif z >= 15:
                            state[i] = 2
                            dot.set_color(C_GREEN).scale(1.3)
                    if state[i] == 1:
                        z = D[i]
                    z = min(z, 15.0)
                    dot.move_to([xs[i], top - s * z, 0])

            dots.add_updater(upd)
            groups.append((dots, state))
            trackers.append(d)
        cr = Arrow([0, 4.3, 0], [0, top + 0.05, 0], buff=0, color=C_PURPLE, stroke_width=5)
        lcr = T("宇宙射线", 22, C_PURPLE).next_to([0, 3.4, 0], RIGHT, buff=0.15)
        mu_lab = VGroup(T("μ子 静止寿命", 22, C_YELLOW), eq(r"\tau = 2.2\,\mu\mathrm{s}", 32, C_YELLOW)
                        ).arrange(DOWN, buff=0.1).move_to([-0.15, 0.6, 0])
        self.beat("μ子：宇宙射线在约15千米高空产生，静止寿命仅2.2微秒。",
                  [Create(axis), FadeIn(ticks), FadeIn(air), Create(ground), GrowArrow(cr), FadeIn(lcr), 0.9],
                  [Flash([cols[0][0], top, 0], color=C_PURPLE), Flash([cols[1][0], top, 0], color=C_PURPLE),
                   *[FadeIn(g[0], lag_ratio=0.02) for g in groups], FadeOut(cr), FadeOut(lcr), 1.0],
                  [FadeIn(mu_lab), 0.6])
        self._muon_beats(groups, trackers, h1, s1, h2, s2, cols)
        self.clean()

        # ---- 其他证据：储存环 + 环球原子钟
        ringc, globec = np.array([-3.5, 1.1, 0]), np.array([3.5, 1.1, 0])
        ring = Circle(1.35, color=C_BLUE, stroke_width=6).move_to(ringc)
        ang = ValueTracker(0)
        pdots = VGroup(*[Dot(radius=0.07, color=C_YELLOW) for _ in range(5)])
        pdots.add_updater(lambda m: [d.move_to(ringc + 1.35 * np.array(
            [np.cos(ang.get_value() + k * TAU / 5), np.sin(ang.get_value() + k * TAU / 5), 0]))
            for k, d in enumerate(m)])
        rt = T("CERN μ子储存环 · 1977", 26, C_BLUE).move_to(ringc + UP * 2.0)
        rr = VGroup(eq(r"\gamma \approx 29.3", 34),
                    eq(r"2.2\,\mu\mathrm{s}\ \to\ 64.4\,\mu\mathrm{s}", 34, C_YELLOW),
                    T("与预言相符到约千分之一", 22, C_GREY)).arrange(DOWN, buff=0.18).move_to(ringc + DOWN * 2.35)
        globe = VGroup(Circle(1.2, color=C_TEAL, stroke_width=3),
                       Ellipse(width=2.4, height=0.7, color=C_TEAL, stroke_width=1.5, stroke_opacity=0.5),
                       Ellipse(width=0.9, height=2.4, color=C_TEAL, stroke_width=1.5, stroke_opacity=0.5)
                       ).move_to(globec)
        pl = ValueTracker(0)
        east = Dot(radius=0.09, color=C_GOLD)
        west = Dot(radius=0.09, color=C_PURPLE)
        east.add_updater(lambda m: m.move_to(globec + np.array([1.55 * np.cos(pl.get_value()),
                                                                0.55 * np.sin(pl.get_value()), 0])))
        west.add_updater(lambda m: m.move_to(globec + np.array([1.55 * np.cos(-pl.get_value() + PI),
                                                                0.55 * np.sin(-pl.get_value() + PI), 0])))
        orbit = Ellipse(width=3.1, height=1.1, color=C_GREY, stroke_width=1.5).move_to(globec)
        gt = T("Hafele–Keating · 1971", 26, C_TEAL).move_to(globec + UP * 2.0)
        gr = VGroup(T("铯原子钟乘客机环球飞行", 22, C_GREY),
                    VGroup(T("东行", 22, C_GOLD), eq(r"-59\ \mathrm{ns}", 32, C_GOLD),
                           T("西行", 22, C_PURPLE), eq(r"+273\ \mathrm{ns}", 32, C_PURPLE)).arrange(RIGHT, buff=0.18),
                    T("与预言相符（狭义 + 广义相对论）", 22, C_GREY)).arrange(DOWN, buff=0.18).move_to(globec + DOWN * 2.35)
        self.add(pdots, east, west)
        self.beat("加速器中的μ子、环球飞行的原子钟，也都验证了时间膨胀。",
                  [Create(ring), FadeIn(rt), FadeIn(globe), Create(orbit), FadeIn(gt), 0.8],
                  [ang.animate.set_value(3 * TAU), pl.animate.set_value(TAU), FadeIn(rr), FadeIn(gr), 4.0])
        self.clean()

    def _muon_beats(self, groups, trackers, h1, s1, h2, s2, cols):
        c1 = T("抵达地面：0 / 40（约百亿分之一）", 22, C_RED).move_to(s1)
        self.beat("若无时间膨胀，平均只能飞约660米，穿过大气只剩约百亿分之一。",
                  [FadeIn(h1), FadeIn(s1), 0.5],
                  [trackers[0].animate(rate_func=linear).set_value(15.8), 4.5],
                  [FadeTransform(s1, c1), 0.5])
        n_surv = int(np.sum(-cols[1][1] * np.log(1 - (np.arange(40) + 0.5) / 40) >= 15))
        c2 = T(f"抵达地面：{n_surv} / 40（期望约 24%）", 22, C_GREEN).move_to(s2)
        self.beat("实际上γ≈16，寿命延长到约35微秒，约四分之一能抵达地面。",
                  [FadeIn(h2), FadeIn(s2), 0.5],
                  [trackers[1].animate(rate_func=linear).set_value(15.8), 4.5],
                  [FadeTransform(s2, c2), 0.5])

    # ================================================================ 第三章：长度收缩
    def part_length(self):
        # μ子参考系疑问
        mu = Dot([0, 1.2, 0], radius=0.14, color=C_YELLOW)
        mul = T("μ子自己的钟", 24, C_YELLOW).next_to(mu, UP, buff=0.25)
        mut = eq(r"\tau = 2.2\,\mu\mathrm{s}", 40, C_YELLOW).next_to(mu, DOWN, buff=0.3)
        qm = T("15 km 怎么飞完？", 34, C_RED).move_to([0, -1.0, 0])
        self.beat("可在μ子自己看来，它的钟并没变慢。",
                  [FadeIn(mu, scale=2), FadeIn(mul), Write(mut), 0.9], [FadeIn(qm, shift=UP * 0.2), 0.6])
        self.clean(0.6)

        # 运动的尺
        L0 = 5.0
        b = ValueTracker(0.0)
        rod0 = Rectangle(width=L0, height=0.45, stroke_color=C_BLUE, fill_color=C_BLUE, fill_opacity=0.35,
                         stroke_width=3).move_to([-1.0, 2.3, 0])
        l0 = eq(r"L_0", 36, C_BLUE).next_to(rod0, RIGHT, buff=0.25)
        t0 = T("静止的尺", 24, C_GREY).next_to(rod0, LEFT, buff=0.3)
        rod = always_redraw(lambda: Rectangle(width=L0 / gam(b.get_value()), height=0.45, stroke_color=C_GOLD,
                                              fill_color=C_GOLD, fill_opacity=0.35, stroke_width=3
                                              ).move_to([-1.0, 0.6, 0]))
        speed = always_redraw(lambda: VGroup(*[Line(rod.get_left() + LEFT * (0.25 + 0.1 * k) + UP * (0.12 * (k - 1)),
                                                    rod.get_left() + LEFT * (0.75 + 0.15 * k) + UP * (0.12 * (k - 1)),
                                                    color=C_GOLD, stroke_width=2,
                                                    stroke_opacity=min(1, 3 * b.get_value()))
                                               for k in range(3)]))
        t1 = T("运动的尺", 24, C_GREY).move_to([t0.get_x(), 0.6, 0])
        guide = VGroup(DashedLine(rod0.get_corner(DL), rod0.get_corner(DL) + DOWN * 1.9, color=C_GREY, stroke_width=1.5),
                       DashedLine(rod0.get_corner(DR), rod0.get_corner(DR) + DOWN * 1.9, color=C_GREY, stroke_width=1.5))
        bn = DecimalNumber(0, num_decimal_places=2, font_size=36)
        ln = DecimalNumber(1, num_decimal_places=2, font_size=36, color=C_GOLD)
        bn.add_updater(lambda m: m.set_value(b.get_value()))
        ln.add_updater(lambda m: m.set_value(1 / gam(b.get_value())))
        rd = VGroup(VGroup(eq(r"v/c =", 36), bn).arrange(RIGHT, buff=0.15),
                    VGroup(eq(r"L/L_0 =", 36, C_GOLD), ln).arrange(RIGHT, buff=0.15)).arrange(RIGHT, buff=0.8)
        rd.move_to([-0.5, -0.65, 0])
        leq = mt(r"L", "=", r"\frac{L_0}{\gamma}", size=60).move_to([5.0, 1.5, 0])
        lnote = T("只沿运动方向；高度不变", 22, C_GREY).next_to(leq, DOWN, buff=0.3)
        self.add(rod, speed)
        self.beat("答案：运动的物体沿运动方向缩短，L = L₀/γ。",
                  [FadeIn(rod0), FadeIn(l0), FadeIn(t0), FadeIn(t1), FadeIn(guide), FadeIn(rd), Write(leq), 0.8],
                  [b.animate.set_value(0.9), FadeIn(lnote), 2.5])
        self.clean(0.6)

        # μ子参考系：大气被压扁
        top, gy = 2.75, -2.15
        s = (top - gy) / 15.0
        g = gam(0.998)
        thick = 15.0 * s / g
        lx, rx = -3.6, 3.4
        airL = Rectangle(width=3.4, height=top - gy, stroke_width=0, fill_color=C_BLUE, fill_opacity=0.12
                         ).move_to([lx, (top + gy) / 2, 0])
        grL = Line([lx - 1.7, gy, 0], [lx + 1.7, gy, 0], color=C_GREEN, stroke_width=4)
        hL = T("地面参考系：大气 15 km", 26, C_BLUE).move_to([lx, 3.5, 0])
        muL = Dot([lx, top, 0], radius=0.11, color=C_YELLOW)
        arrL = Arrow([lx + 0.4, top, 0], [lx + 0.4, top - 1.0, 0], buff=0, color=C_YELLOW, stroke_width=4)
        lvl = eq(r"0.998c", 28, C_YELLOW).next_to(arrL, RIGHT, buff=0.1)
        yy = ValueTracker(0)
        muy = 1.8
        slab = always_redraw(lambda: VGroup(
            Rectangle(width=3.4, height=thick, stroke_width=0, fill_color=C_BLUE, fill_opacity=0.45
                      ).move_to([rx, muy - thick / 2 + yy.get_value(), 0]),
            Line([rx - 1.7, muy - thick + yy.get_value(), 0], [rx + 1.7, muy - thick + yy.get_value(), 0],
                 color=C_GREEN, stroke_width=4)))
        hR = T("μ子参考系：大气只剩约 0.95 km", 26, C_GOLD).move_to([rx, 3.5, 0])
        muR = Dot([rx, muy, 0], radius=0.11, color=C_YELLOW)
        arrR = Arrow([rx + 2.1, muy - 1.6, 0], [rx + 2.1, muy - 0.6, 0], buff=0, color=C_BLUE, stroke_width=4)
        lvr = T("大气迎面而来", 20, C_BLUE).next_to(arrR, DOWN, buff=0.1)
        tclock = DecimalNumber(0, num_decimal_places=1, font_size=34, color=C_YELLOW)
        tclock.add_updater(lambda m: m.set_value(3.2 * min(1, yy.get_value() / (thick + 0.0001))))
        trow = VGroup(T("μ子的钟", 22, C_YELLOW), tclock, eq(r"\mu\mathrm{s}", 30, C_YELLOW)).arrange(RIGHT, buff=0.15)
        trow.move_to([rx, -0.6, 0])
        res = T("存活率都是 e^(−1.44) ≈ 24%", 24, C_GREEN).move_to([rx, -1.5, 0])
        res = VGroup(T("两种算法，存活率都约", 24, C_GREEN), eq(r"e^{-1.44}\approx 24\%", 34, C_GREEN)
                     ).arrange(RIGHT, buff=0.15).move_to([rx, -1.5, 0])
        self.add(slab)
        self.beat("μ子看到的大气只有约950米厚，结果一致。",
                  [FadeIn(airL), Create(grL), FadeIn(hL), FadeIn(muL), GrowArrow(arrL), FadeIn(lvl),
                   FadeIn(hR), FadeIn(muR), GrowArrow(arrR), FadeIn(lvr), FadeIn(trow), 0.8],
                  [yy.animate.set_value(thick + 0.02), 2.5],
                  [FadeIn(res), 0.6])
        self.clean()

    # ================================================================ 同时的相对性
    def part_simultaneity(self):
        c = 2.0
        a = 2.4
        gb = gam(0.5)
        yT, yB = 2.15, -0.75
        h = 0.9

        def car(cx, cy, half, color):
            body = Rectangle(width=2 * half, height=h, stroke_width=2, stroke_color=color, fill_color=color,
                             fill_opacity=0.08).move_to([cx, cy, 0])
            rw = Line([cx - half, cy - h / 2, 0], [cx - half, cy + h / 2, 0], color=C_WHITE, stroke_width=7)
            fw = Line([cx + half, cy - h / 2, 0], [cx + half, cy + h / 2, 0], color=C_WHITE, stroke_width=7)
            lamp = Dot([cx, cy + h / 2 - 0.12, 0], radius=0.07, color=C_GOLD)
            return VGroup(body, rw, fw, lamp)

        # 上：车厢系
        tt = ValueTracker(0)
        carT = car(0, yT, a, C_BLUE)
        lT = T("车厢参考系", 26, C_BLUE).move_to([-5.6, yT + 0.95, 0])
        fronts_T = always_redraw(lambda: self._fronts(0.0, yT, tt.get_value(), c, -a, a))
        trackT = Line([-6.8, yT - h / 2 - 0.05, 0], [6.8, yT - h / 2 - 0.05, 0], color=C_GREY, stroke_width=1.5,
                      stroke_opacity=0.5)
        simT = T("前后壁同时亮", 26, C_GREEN).move_to([0, yT - 0.85, 0])
        # 下：站台系
        tb = ValueTracker(0)
        v = 0.5 * c
        x_e = -1.6
        ha = a / gb
        carB = car(x_e, yB, ha, C_GOLD)
        carB.add_updater(lambda m: m.move_to([x_e + v * tb.get_value(), yB, 0]))
        lB = T("站台参考系（车速 0.5c）", 26, C_GOLD).move_to([-4.5, yB + 1.2, 0])
        fronts_B = always_redraw(lambda: self._fronts(x_e, yB, tb.get_value(), c,
                                                      x_e - ha + v * tb.get_value(), x_e + ha + v * tb.get_value()))
        plat = Line([-6.8, yB - h / 2 - 0.05, 0], [6.8, yB - h / 2 - 0.05, 0], color=C_GREY, stroke_width=3)
        emit = Triangle(color=C_GOLD, fill_opacity=1, stroke_width=0).scale(0.08).rotate(PI).move_to(
            [x_e, yB - h / 2 - 0.2, 0])
        lemit = T("闪光处", 18, C_GOLD).next_to(emit, DOWN, buff=0.08)
        varr = Arrow([1.4, yB + 1.2, 0], [2.6, yB + 1.2, 0], buff=0, color=C_GOLD, stroke_width=5)
        lv = eq(r"v", 32, C_GOLD).next_to(varr, RIGHT, buff=0.1)

        self.add(carT, fronts_T)
        t_hit = a / c
        tR = ha / (c + v)
        tF = ha / (c - v)

        def flash_wall(wall):
            wall.set_color(C_YELLOW)
            return [Flash(wall.get_center(), color=C_YELLOW, flash_radius=0.5)]

        self.beat("车厢中央闪光：车厢里看，光同时到达前后壁。",
                  [FadeIn(carT), FadeIn(lT), FadeIn(trackT), 0.6],
                  [tt.animate(rate_func=linear).set_value(t_hit), 1.8],
                  lambda: self.play(*flash_wall(carT[1]), *flash_wall(carT[2]), FadeIn(simT), run_time=0.8))
        self.add(carB, fronts_B)
        lr = T("① 后壁先亮", 24, C_GREEN)
        lf = T("② 前壁后亮", 24, C_RED)
        rate = 1.4
        self.beat("站台上看：后壁迎光而来，前壁背光而去，后壁先亮。",
                  [FadeIn(carB), FadeIn(lB), Create(plat), FadeIn(emit), FadeIn(lemit), GrowArrow(varr), FadeIn(lv), 0.6],
                  [tb.animate(rate_func=linear).set_value(tR), tR * rate],
                  lambda: lr.move_to([carB[1].get_x(), yB + 0.68, 0]),
                  lambda: self.play(*flash_wall(carB[1]), FadeIn(lr),
                                    tb.animate(rate_func=linear).set_value(tR + 0.4), run_time=0.4 * rate),
                  [tb.animate(rate_func=linear).set_value(tF), (tF - tR - 0.4) * rate],
                  lambda: lf.move_to([carB[2].get_x(), yB + 0.68, 0]),
                  lambda: self.play(*flash_wall(carB[2]), FadeIn(lf), run_time=0.6))
        note = T("（这是扣除光传到观察者眼中所需时间之后的结论，并非视觉延迟）", 22, C_GREY).move_to([0, -2.2, 0])
        eT = eq(r"t_{\text{rear}} = t_{\text{front}}", 34, C_GREEN).move_to([4.6, yT - 0.85, 0])
        eB = eq(r"t_{\text{rear}} < t_{\text{front}}", 34, C_RED).move_to([4.6, yB + 1.2, 0])
        self.beat("一个参考系里的“同时”，在另一个参考系里并不同时。",
                  [FadeOut(varr), FadeOut(lv), Write(eT), Write(eB), FadeIn(note), 1.0],
                  [Indicate(simT), Indicate(lr), Indicate(lf), 1.0])
        self.clean()

    def _fronts(self, x_e, y, t, c, xl, xr):
        """从 x_e 发出的两道光前，到达车壁 xl / xr 后停止"""
        left = max(x_e - c * t, xl)
        right = min(x_e + c * t, xr)
        g = VGroup(Line([left, y, 0], [right, y, 0], color=C_YELLOW, stroke_width=3, stroke_opacity=0.6))
        if t > 0:
            g.add(Dot([left, y, 0], radius=0.08, color=GLOW), Dot([right, y, 0], radius=0.08, color=GLOW))
        return g

    # ================================================================ 第四章：闵可夫斯基图
    def part_minkowski(self):
        R = 3.0
        O = np.array([-2.3, 0.7, 0])

        def P(x, ct):
            return O + np.array([x, ct, 0])

        bv = ValueTracker(0.0)      # 观看者（主动变换）速度
        bo = ValueTracker(0.0)      # 飞船参考系速度

        def to_view(x, ct):
            return lb(bv.get_value(), x, ct)

        def line_view(p, q, **kw):
            p2, q2 = to_view(*p), to_view(*q)
            c = clip_seg(p2, q2, R)
            if c is None:
                kw = dict(kw, stroke_opacity=0)
                return Line(P(R, R), P(R, R) + RIGHT * 1e-3, **kw)
            return Line(P(*c[0]), P(*c[1]), **kw)

        def grid(frame_b, color, op, axis_w=0, ks=range(-6, 7)):
            g = VGroup()
            for fam in (0, 1):
                for k in ks:
                    if k == 0 and axis_w == 0:
                        continue
                    if fam == 0:
                        p, q = (k, -14), (k, 14)
                    else:
                        p, q = (-14, k), (14, k)
                    p, q = lb(-frame_b, *p), lb(-frame_b, *q)   # 该参考系坐标 → 静止系
                    w = axis_w if k == 0 else 1.5
                    o = 1.0 if k == 0 else op
                    g.add(line_view(p, q, stroke_color=color, stroke_width=w, stroke_opacity=o))
            return g

        border = Square(2 * R, color=C_GREY, stroke_width=1.5, stroke_opacity=0.6).move_to(O)
        rest_grid = always_redraw(lambda: grid(0.0, C_BLUE, 0.28, axis_w=3.5))
        light = VGroup(Line(P(-R, -R), P(R, R)), Line(P(-R, R), P(R, -R))).set_stroke(C_YELLOW, 4)
        cone_f = Polygon(P(0, 0), P(R, R), P(-R, R), stroke_width=0, fill_color=C_YELLOW, fill_opacity=0.10)
        cone_p = Polygon(P(0, 0), P(R, -R), P(-R, -R), stroke_width=0, fill_color=C_YELLOW, fill_opacity=0.10)
        xl = eq("x", 34, C_BLUE)
        xl.add_updater(lambda m: m.move_to(P(*to_view(2.6, 0)) + UP * 0.3))
        tl = eq("ct", 34, C_BLUE)
        tl.add_updater(lambda m: m.move_to(P(*to_view(0, 2.6)) + LEFT * 0.38))
        you = always_redraw(lambda: line_view((0, -R * 2), (0, R * 2), stroke_color=C_WHITE, stroke_width=6))
        you_l = T("静止物体", 22, C_WHITE)
        you_l.add_updater(lambda m: m.move_to(P(*to_view(0, 1.9))).shift(LEFT * 0.7))
        light_l = T("光", 22, C_YELLOW).move_to(P(R - 0.25, R - 0.6))

        # 相机：从原点附近拉远
        fr = self.camera.frame
        fr.save_state()
        fr.scale(0.55).move_to(O)
        self.add(rest_grid, border, xl, tl)
        self.beat("时空图里，静止物体的世界线是竖线，光走45°斜线。",
                  [FadeIn(rest_grid), FadeIn(border), FadeIn(xl), FadeIn(tl), 0.8],
                  [Create(you), FadeIn(you_l), 0.8],
                  [Create(light), FadeIn(light_l), Restore(fr), 1.6])
        self.add(you, you_l)

        # 飞船坐标轴
        def ship_axes():
            b = bo.get_value()
            pa, qa = lb(-b, 0, -14), lb(-b, 0, 14)
            pb, qb = lb(-b, -14, 0), lb(-b, 14, 0)
            return VGroup(line_view(pa, qa, stroke_color=C_TEAL, stroke_width=5),
                          line_view(pb, qb, stroke_color=C_TEAL, stroke_width=5))

        sax = always_redraw(ship_axes)

        def ax_label(tex, which):
            m = eq(tex, 34, C_TEAL)

            def upd(mm):
                b = bo.get_value()
                if which == 0:
                    pt = to_view(*lb(-b, 0, 2.55))
                    mm.move_to(P(*pt) + RIGHT * 0.35)
                else:
                    pt = to_view(*lb(-b, 2.55, 0))
                    mm.move_to(P(*pt) + DOWN * 0.34)
            m.add_updater(upd)
            return m

        ctp, xp = ax_label("ct'", 0), ax_label("x'", 1)
        ship_l = T("飞船", 22, C_TEAL)
        ship_l.add_updater(lambda m: m.move_to(P(*to_view(*lb(-bo.get_value(), 0, 1.6)))).shift(RIGHT * 0.45))
        ship_grid = always_redraw(lambda: grid(bo.get_value(), C_TEAL, 0.35))
        lor = VGroup(eq(r"x' = \gamma\,(x - vt)", 36), eq(r"ct' = \gamma\,(ct - \beta x)", 36)
                     ).arrange(DOWN, aligned_edge=LEFT, buff=0.2).move_to([4.6, 3.0, 0])
        self.add(sax, ctp, xp)
        self.beat("运动观察者的时间轴和空间轴，都向光线倾斜。",
                  [FadeIn(sax), FadeIn(ctp), FadeIn(xp), FadeIn(ship_l), FadeOut(you_l), 0.5],
                  [bo.animate.set_value(0.5), 2.2],
                  lambda: ship_grid.update(),
                  [FadeIn(ship_grid), 0.6])
        self.add(ship_grid, ship_l)
        self.beat("洛伦兹变换像一把剪刀：网格沿光线一拉一压，光线纹丝不动。",
                  [FadeIn(lor), 0.6],
                  [bv.animate.set_value(0.5), 2.2],
                  [Indicate(light, color=GLOW, scale_factor=1.0), 0.8],
                  [bv.animate.set_value(0.0), 1.8])

        # 事件 A、B
        evA, evB, evC = (-1.5, 0.0), (1.5, 0.0), (0.0, 1.5)

        def ev_dot(e, color):
            d = Dot(radius=0.1, color=color)
            d.add_updater(lambda m: m.move_to(P(*to_view(*e))))
            return d

        dA, dB = ev_dot(evA, C_RED), ev_dot(evB, C_GOLD)
        lA = eq("A", 32, C_RED)
        lA.add_updater(lambda m: m.next_to(dA, UL, buff=0.08))
        lB_ = eq("B", 32, C_GOLD)
        lB_.add_updater(lambda m: m.next_to(dB, UR, buff=0.08))

        def hline(d, color):
            return always_redraw(lambda: DashedLine(d.get_center(), np.array([O[0], d.get_y(), 0]),
                                                    color=color, stroke_width=2.5))

        hA, hB = hline(dA, C_RED), hline(dB, C_GOLD)
        stA = T("A、B 同时", 26, C_WHITE)
        stB = T("B 先于 A", 26, C_GOLD)
        stC = T("A 先于 B", 26, C_RED)
        stat = VGroup(stA, stB, stC)
        for m in stat:
            m.move_to([4.6, -0.6, 0])

        def stat_upd(m):
            b = bv.get_value()
            stA.set_opacity(1 if abs(b) < 0.02 else 0)
            stB.set_opacity(1 if b >= 0.02 else 0)
            stC.set_opacity(1 if b <= -0.02 else 0)

        stat.add_updater(stat_upd)
        self.add(dA, dB, lA, lB_, hA, hB, stat)
        self.beat("原本同时的两个事件，在新坐标里一先一后。",
                  [FadeIn(dA, scale=2), FadeIn(dB, scale=2), FadeIn(lA), FadeIn(lB_), 0.6],
                  [bv.animate.set_value(0.5), 2.0])
        ieq = eq(r"s^2 = (c\Delta t)^2 - \Delta x^2", 46, C_YELLOW).move_to([4.6, 1.5, 0])
        ibox = SurroundingRectangle(ieq, color=C_YELLOW, buff=0.18, corner_radius=0.08)
        self.beat("所有人都同意的量：时空间隔 s² = (cΔt)² − Δx²。",
                  [Write(ieq), 1.2], [Create(ibox), 0.5])

        hyp_t = ParametricFunction(lambda u: P(1.5 * np.sinh(u), 1.5 * np.cosh(u)), t_range=[-1.316, 1.316],
                                   color=C_PURPLE, stroke_width=3)
        hyp_r = ParametricFunction(lambda u: P(1.5 * np.cosh(u), 1.5 * np.sinh(u)), t_range=[-1.316, 1.316],
                                   color=C_PURPLE, stroke_width=3)
        hyp_l = ParametricFunction(lambda u: P(-1.5 * np.cosh(u), 1.5 * np.sinh(u)), t_range=[-1.316, 1.316],
                                   color=C_PURPLE, stroke_width=3)
        dC = ev_dot(evC, C_GREEN)
        lC = eq("C", 32, C_GREEN)
        lC.add_updater(lambda m: m.next_to(dC, RIGHT, buff=0.12))
        dO = Dot(P(0, 0), radius=0.09, color=C_WHITE)
        lO = eq("O", 30).next_to(dO, DR, buff=0.05)
        self.add(dC, lC)
        self.beat("变换只让事件沿着间隔不变的双曲线滑动。",
                  [Create(hyp_t), Create(hyp_r), Create(hyp_l), FadeIn(dC, scale=2), FadeIn(lC), FadeIn(dO),
                   FadeIn(lO), 1.0],
                  [bv.animate.set_value(-0.5), 2.6],
                  [bv.animate.set_value(0.3), 1.8])
        tl1 = VGroup(T("C 在 O 的光锥内（类时）", 22, C_GREEN), T("C 永远在 O 之后", 22, C_GREEN)
                     ).arrange(DOWN, aligned_edge=LEFT, buff=0.12).move_to([4.6, -1.5, 0])
        self.beat("类时事件的先后永不颠倒；类空事件顺序可变，但它们无法相互影响。",
                  [FadeIn(cone_f), FadeIn(cone_p), FadeIn(tl1), 0.8],
                  [bv.animate.set_value(-0.55), 2.4],
                  [bv.animate.set_value(0.55), 2.4])
        self.clean()

    # ================================================================ 双生子
    def part_twins(self):
        k = 0.56
        O = np.array([-4.8, -2.15, 0])

        def P(x, t):
            return O + k * np.array([x, t, 0])

        earth = Line(P(0, 0), P(0, 10), color=C_BLUE, stroke_width=5)
        star = DashedLine(P(4, 0), P(4, 10), color=C_GREY, stroke_width=2)
        lstar = T("星球（4 光年）", 22, C_GREY).next_to(P(4, 10), UP, buff=0.12)
        learth = T("地球", 22, C_BLUE).next_to(P(0, 10), UP, buff=0.12)
        path = VMobject(color=C_GOLD, stroke_width=5).set_points_as_corners([P(0, 0), P(4, 5), P(0, 10)])
        lights = VGroup(DashedLine(P(0, 0), P(4.4, 4.4)), DashedLine(P(4, 5), P(0, 9))).set_stroke(C_YELLOW, 1.5, 0.4)
        eticks = VGroup(*[Line(P(-0.18, y), P(0.18, y), color=C_BLUE, stroke_width=3) for y in range(1, 11)])
        elabs = VGroup(*[T(str(y), 18, C_BLUE).next_to(P(-0.2, y), LEFT, buff=0.08) for y in (0, 5, 10)])
        ylab = T("地球时间（年）", 20, C_GREY).rotate(PI / 2).move_to(P(-1.4, 5))

        def trav(t):
            return (0.8 * t, t) if t <= 5 else (4 - 0.8 * (t - 5), t)

        tticks = VGroup()
        for tau in range(1, 7):
            t = tau * 5 / 3
            x, tt = trav(t)
            tticks.add(Dot(P(x, tt), radius=0.075, color=C_GOLD))
        T_ = ValueTracker(0)
        de = Dot(radius=0.11, color=C_BLUE)
        de.add_updater(lambda m: m.move_to(P(0, T_.get_value())))
        dt_ = Dot(radius=0.11, color=C_GOLD)
        dt_.add_updater(lambda m: m.move_to(P(*trav(T_.get_value()))))

        def tick_upd(m):
            Tv = T_.get_value()
            for i, d in enumerate(eticks):
                d.set_opacity(1 if Tv >= i + 1 - 1e-6 else 0.15)
            for i, d in enumerate(tticks):
                d.set_opacity(1 if Tv >= (i + 1) * 5 / 3 - 1e-6 else 0.0)

        ticks = VGroup(eticks, tticks)
        ticks.add_updater(tick_upd)
        ne = DecimalNumber(0, num_decimal_places=1, font_size=40, color=C_BLUE)
        nt = DecimalNumber(0, num_decimal_places=1, font_size=40, color=C_GOLD)
        ne.add_updater(lambda m: m.set_value(T_.get_value()))
        nt.add_updater(lambda m: m.set_value(0.6 * T_.get_value()))
        r1 = VGroup(T("地球", 28, C_BLUE), ne, T("年", 28, C_BLUE)).arrange(RIGHT, buff=0.2)
        r2 = VGroup(T("旅行者", 28, C_GOLD), nt, T("年", 28, C_GOLD)).arrange(RIGHT, buff=0.2)
        r1[2].add_updater(lambda m: m.next_to(ne, RIGHT, buff=0.2))
        r2[2].add_updater(lambda m: m.next_to(nt, RIGHT, buff=0.2))
        rd = VGroup(r1, r2).arrange(DOWN, aligned_edge=LEFT, buff=0.3).move_to([3.4, 2.6, 0])
        spd = T("速度 0.8c，γ = 5/3", 24, C_GREY).next_to(rd, DOWN, buff=0.35, aligned_edge=LEFT)
        self.beat("双胞胎之一以0.8c飞往4光年外的星球，再返回地球。",
                  [Create(earth), Create(star), FadeIn(lstar), FadeIn(learth), FadeIn(elabs), FadeIn(ylab),
                   FadeIn(lights), 0.9],
                  [Create(path), FadeIn(rd), FadeIn(spd), 1.4])
        self.add(ticks, de, dt_)
        self.beat("地球上过了10年，旅行者的钟只走了6年。",
                  [T_.animate(rate_func=linear).set_value(10), 4.5])
        q = VGroup(T("旅行者：明明是地球在动，", 24, C_WHITE), T("该是地球上的人更年轻？", 24, C_WHITE)
                   ).arrange(DOWN, aligned_edge=LEFT, buff=0.12).move_to([3.4, 0.3, 0])
        turn = Circle(0.25, color=C_RED, stroke_width=4).move_to(P(4, 5))
        sim1 = DashedLine(P(4, 5), P(0, 1.8), color=C_TEAL, stroke_width=2.5)
        sim2 = DashedLine(P(4, 5), P(0, 8.2), color=C_PINK, stroke_width=2.5)
        ljump = VGroup(T("“同时线”", 20, C_GREY), T("骤然转向", 20, C_GREY)).arrange(DOWN, buff=0.05).move_to(P(1.7, 5.0))
        ans = VGroup(T("旅行者：去程、返程是两个惯性系", 24, C_GOLD),
                     T("地球：始终是同一个惯性系", 24, C_BLUE)).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
        ans.move_to([3.4, 0.3, 0])
        self.beat("旅行者也能说是地球在动？关键：他掉头时换了惯性系，世界线是折线。",
                  [FadeIn(q, shift=UP * 0.2), 0.8], 1.2,
                  [Create(turn), Indicate(path, color=C_RED, scale_factor=1.0), 0.8],
                  [Create(sim1), Create(sim2), FadeIn(ljump), FadeTransform(q, ans), 1.0])
        f1 = mt(r"\tau = \sqrt{(c\Delta t)^2 - \Delta x^2}\,/\,c", size=36).move_to([3.4, -0.9, 0])
        f2 = VGroup(T("地球", 22, C_BLUE), eq(r"\sqrt{10^2-0^2} = 10", 32, C_BLUE)).arrange(RIGHT, buff=0.2)
        f3 = VGroup(T("旅行者", 22, C_GOLD), eq(r"2\times\sqrt{5^2-4^2} = 6", 32, C_GOLD)).arrange(RIGHT, buff=0.2)
        f23 = VGroup(f2, f3).arrange(DOWN, aligned_edge=LEFT, buff=0.15).move_to([3.4, -1.85, 0])
        self.beat("世界线的长度就是固有时：两事件之间，直线最长。",
                  [Write(f1), 0.9], [FadeIn(f23), Indicate(earth, color=GLOW, scale_factor=1.0), 1.0])
        self.clean()

    # ================================================================ 第五章：质能
    def part_energy(self):
        pT = ValueTracker(3.0)
        mc2 = 2.6
        A = np.array([-5.6, -1.7, 0])

        def tri():
            p = pT.get_value()
            Bp = A + RIGHT * p
            Cp = A + UP * mc2
            g = VGroup(Line(A, Bp, color=C_BLUE, stroke_width=6), Line(A, Cp, color=C_GOLD, stroke_width=6),
                       Line(Cp, Bp, color=C_WHITE, stroke_width=6))
            return g

        trg = always_redraw(tri)
        lp = eq("pc", 36, C_BLUE)
        lp.add_updater(lambda m: m.move_to(A + RIGHT * pT.get_value() / 2 + DOWN * 0.35).set_opacity(
            min(1, pT.get_value() / 0.6)))
        lm = eq("mc^2", 36, C_GOLD).move_to(A + UP * mc2 / 2 + LEFT * 0.6)
        lE = eq("E", 40, C_WHITE)
        lE.add_updater(lambda m: m.move_to(A + np.array([pT.get_value() / 2, mc2 / 2, 0]) +
                                           0.42 * normalize(np.array([mc2, pT.get_value() + 1e-6, 0]))))
        e1 = mt("E^2", "=", "(pc)^2", "+", "(mc^2)^2", size=56).move_to([2.6, 2.4, 0])
        e1[2].set_color(C_BLUE)
        e1[4].set_color(C_GOLD)
        mnote = T("m：不随速度改变的质量", 22, C_GREY).next_to(e1, DOWN, buff=0.3)
        self.add(trg)
        self.beat("能量与动量也合为一体：E² = (pc)² + (mc²)²。",
                  [Create(trg), FadeIn(lp), FadeIn(lm), FadeIn(lE), Write(e1), 1.4], [FadeIn(mnote), 0.4])
        self.add(lp, lE)
        e2 = mt("E", "=", "mc^2", size=80).move_to([2.6, 0.6, 0])
        e2[2].set_color(C_GOLD)
        pz = eq(r"p = 0", 40, C_BLUE).move_to([-3.6, 2.6, 0])
        self.beat("静止时p = 0，剩下E = mc²：质量本身就是能量。",
                  [FadeIn(pz), pT.animate.set_value(0.0), 1.6],
                  [TransformMatchingTex(e1.copy(), e2), 1.2])
        e3 = eq(r"1\,\mathrm{g}\times c^2 \approx 9\times 10^{13}\ \mathrm{J}", 42).move_to([2.6, -0.9, 0])
        e3n = T("≈ 两万多吨 TNT 当量", 26, C_GREY).next_to(e3, DOWN, buff=0.25)
        self.beat("1克质量的静能约9×10¹³焦耳。", [Write(e3), 1.0], [FadeIn(e3n), 0.5])
        self.clean()

        ax = Axes(x_range=[0, 1.0, 0.2], y_range=[0, 8, 1], x_length=7.2, y_length=5.0,
                  axis_config={"color": C_GREY, "include_tip": False, "font_size": 26},
                  x_axis_config={"numbers_to_include": [0.2, 0.4, 0.6, 0.8, 1.0]},
                  y_axis_config={"numbers_to_include": [1, 2, 4, 6, 8]}).move_to([-1.6, 0.65, 0])
        xl = eq(r"v/c", 34).next_to(ax.x_axis.get_right(), RIGHT, buff=0.2)
        yl = eq(r"E/mc^2", 34, C_GOLD).next_to(ax.y_axis.get_top(), RIGHT, buff=0.15)
        bmax = np.sqrt(1 - 1 / 64.0)
        rel = ax.plot(gam, x_range=[0, bmax, 0.002], color=C_GOLD, stroke_width=5)
        newt = ax.plot(lambda b: 1 + b * b / 2, x_range=[0, 1, 0.01], color=C_GREY, stroke_width=3)
        newt = DashedVMobject(newt, num_dashes=30)
        lnew = T("虚线：牛顿力学", 22, C_GREY).move_to(ax.c2p(0.5, 0.45))
        asym = DashedLine(ax.c2p(1, 0), ax.c2p(1, 8), color=C_RED, stroke_width=3)
        lasym = eq("v = c", 30, C_RED).next_to(ax.c2p(1, 4.0), RIGHT, buff=0.3)
        eg = mt("E", "=", r"\gamma", "mc^2", size=56).move_to(ax.c2p(0.3, 6.5))
        eg[2].set_color(C_YELLOW)
        bt = ValueTracker(0)
        dot = Dot(radius=0.11, color=C_WHITE)
        dot.add_updater(lambda m: m.move_to(ax.c2p(bt.get_value(), gam(bt.get_value()))))
        self.add(dot)
        fr = self.camera.frame
        fr.save_state()
        self.beat("能量E = γmc²：越接近光速越趋于无穷。",
                  [Create(ax), FadeIn(xl), FadeIn(yl), Write(eg), 0.8],
                  [Create(rel), Create(newt), FadeIn(lnew), Create(asym), FadeIn(lasym),
                   bt.animate.set_value(0.9), 2.0],
                  [bt.animate.set_value(0.99), fr.animate.scale(0.62).move_to(ax.c2p(0.62, 4.6)), 1.8])
        # 光子
        ph = ValueTracker(0)
        packet = always_redraw(lambda: ParametricFunction(
            lambda x: np.array([x, -1.3 + 0.25 * np.exp(-((x - (3.6 + ph.get_value())) / 0.35) ** 2) *
                                np.sin(14 * x), 0]), t_range=[3.0 + ph.get_value(), 4.2 + ph.get_value(), 0.02],
            color=GLOW, stroke_width=4))
        pl = VGroup(T("光子", 24, C_YELLOW), eq(r"m = 0,\ E = pc,\ v = c", 32, C_YELLOW)
                    ).arrange(DOWN, buff=0.12).move_to([5.0, -0.3, 0])
        no_c = T("有质量：永远到不了 c", 24, C_RED).move_to([4.9, 1.4, 0])
        self.add(packet)
        self.beat("所以有质量的物体永远到不了光速；光子没有质量，只能以c运动。",
                  [Restore(fr), FadeIn(no_c), 1.2],
                  [FadeIn(pl), ph.animate(rate_func=linear).set_value(2.4), 2.0])
        self.clean()

        # 结尾：光锥与因果
        Oc = np.array([0, 0.6, 0])
        Rr = 2.3
        fut = Polygon(Oc, Oc + np.array([Rr, Rr, 0]), Oc + np.array([-Rr, Rr, 0]), stroke_color=C_YELLOW,
                      stroke_width=3, fill_color=C_YELLOW, fill_opacity=0.15)
        past = Polygon(Oc, Oc + np.array([Rr, -Rr, 0]), Oc + np.array([-Rr, -Rr, 0]), stroke_color=C_YELLOW,
                       stroke_width=3, fill_color=C_YELLOW, fill_opacity=0.15)
        here = Dot(Oc, radius=0.1, color=C_WHITE)
        lh = T("此时此地", 22).next_to(here, RIGHT, buff=0.15)
        lf = T("未来：可被影响", 24, C_YELLOW).move_to(Oc + UP * 1.75)
        lp_ = T("过去：可影响此地", 24, C_YELLOW).move_to(Oc + DOWN * 1.75)
        le = T("别处：不能相互影响", 22, C_GREY).move_to(Oc + LEFT * 4.6)
        le2 = T("别处：不能相互影响", 22, C_GREY).move_to(Oc + RIGHT * 4.6)
        ceq = eq(r"c", 64, C_YELLOW)
        cl = T("= 因果的速度极限", 32, C_WHITE)
        VGroup(ceq, cl).arrange(RIGHT, buff=0.2).move_to([0, 3.55, 0])
        self.beat("c不只是光速，而是时空的速度上限——因果传播的极限。",
                  [DrawBorderThenFill(fut), DrawBorderThenFill(past), FadeIn(here), FadeIn(lh), 1.2],
                  [FadeIn(lf), FadeIn(lp_), FadeIn(le), FadeIn(le2), Write(ceq), FadeIn(cl), 1.0])
        self.clean(1.0)
