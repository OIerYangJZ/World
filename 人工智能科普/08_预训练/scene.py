# -*- coding: utf-8 -*-
"""
第 08 集《预训练：读遍互联网》

时间全部对齐 bars.py 的 BPM 小节网格（86 BPM，122 小节）。字幕由 build.py 烧录。
    ~/.venvs/manim/bin/python ../common/build.py 08_预训练 [--preview]

说明：曲线、比例尺、续写示例都是示意；15 万亿 token（Llama 3）、3×10²³ FLOPs（GPT-3）、
约 20 token/参数（Chinchilla）为公开论文中的数字。
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "common"))
from style import *  # noqa: E402,F401

C_ATT, C_MLP = C_PURPLE, C_TEAL
TEXT = ["今天", "天气", "很", "好", "，", "我们", "去", "公园", "散步", "。"]


def token_block(text, color=C_BLUE, size=30, pad=0.14, fill=0.18, h=0.6):
    t = T(text, size=size, color=C_WHITE)
    r = RoundedRectangle(width=max(t.width + 2 * pad, 0.5), height=h, corner_radius=0.08,
                         stroke_color=color, stroke_width=2.5, fill_color=color, fill_opacity=fill)
    return VGroup(r, t.move_to(r))


def sentence(words, y=0.0, size=30, color=C_BLUE, buff=0.1, x=0.0):
    return VGroup(*[token_block(w, color=color, size=size) for w in words]).arrange(RIGHT, buff=buff).move_to([x, y, 0])


def block(w=2.4, h=0.5):
    att = RoundedRectangle(width=w, height=h / 2 - 0.03, corner_radius=0.06, color=C_ATT, fill_opacity=0.28, stroke_width=2)
    mlp = RoundedRectangle(width=w, height=h / 2 - 0.03, corner_radius=0.06, color=C_MLP, fill_opacity=0.28, stroke_width=2)
    mlp.next_to(att, UP, buff=0.04)
    return VGroup(att, mlp)


def tower(n, w=2.4, h=0.5, gap=0.05):
    return VGroup(*[block(w, h) for _ in range(n)]).arrange(UP, buff=gap)


def book(h=0.9, w=0.28, color=C_GOLD, op=0.35):
    return Rectangle(width=w, height=h, stroke_color=color, stroke_width=1.5, fill_color=color, fill_opacity=op)


def reader(scale=1.0, color=C_WHITE):
    head = Circle(radius=0.2, color=color, stroke_width=3).move_to(UP * 0.95)
    body = Line(UP * 0.75, UP * 0.2, color=color, stroke_width=3)
    legs = VGroup(Line(UP * 0.2, DOWN * 0.3 + LEFT * 0.2, color=color, stroke_width=3),
                  Line(UP * 0.2, DOWN * 0.3 + RIGHT * 0.2, color=color, stroke_width=3))
    bk = Rectangle(width=0.45, height=0.32, color=C_GOLD, fill_opacity=0.5).move_to(UP * 0.5 + RIGHT * 0.35)
    arms = Line(UP * 0.6, bk.get_left(), color=color, stroke_width=3)
    return VGroup(head, body, legs, arms, bk).scale(scale)


class Video(BeatScene):
    EP_DIR = os.path.dirname(os.path.abspath(__file__))

    def construct(self):
        self.counter = None
        self.intro()          # 1–4
        self.verse1()         # 5–20
        self.hook(21)         # 21–30
        self.verse2()         # 31–46
        self.inst1()          # 47–50
        self.hook(51)         # 51–60
        self.verse3()         # 61–76
        self.bridge()         # 77–84
        self.verse4()         # 85–100
        self.inst2()          # 101–104
        self.hook(105)        # 105–114
        self.outro()          # 115–122
        self.finish()

    # ------------------------------------------------------------ 公共：遮挡猜词
    def mask_quiz(self, sent, k, mask=None):
        """遮住第 k 个之后（含 k）的 token，返回遮挡块和问号卡"""
        covered = VGroup(*sent[k:])
        m = Rectangle(width=covered.width + 0.2, height=sent.height + 0.2, stroke_color=C_GREY, stroke_width=2,
                      fill_color="#1a1f2c", fill_opacity=1).move_to(covered).align_to(covered, LEFT).shift(LEFT * 0.1)
        q = VGroup(RoundedRectangle(width=1.7, height=0.55, corner_radius=0.1, color=C_GOLD, fill_opacity=0.15),
                   T("下一个是？", size=22, color=C_GOLD))
        q[1].move_to(q[0])
        q.next_to(sent[k], UP, buff=0.3)
        return m, q

    # ------------------------------------------------------------ 前奏 1–4
    def intro(self):
        card = title_card("第 08 集", "预训练", "读遍互联网")
        s, e, t, line, st = card
        self.play_bars(FadeIn(s, shift=DOWN * 0.2), FadeIn(e, shift=DOWN * 0.2), bars=0.75)
        self.play_bars(Write(t), bars=1)
        self.play_bars(GrowFromCenter(line), FadeIn(st, shift=UP * 0.2), bars=0.75)
        self.at_bar(3.5)
        self.set_counter("1750 亿", bars=0.5)
        self.at_bar(4.5)
        self.play_bars(FadeOut(card), bars=0.5)

    # ------------------------------------------------------------ 主歌一 5–20：自监督
    def verse1(self):
        self.at_bar(5)
        self.tag("旋钮全是乱数")
        tw = tower(6).move_to([-3.5, 0.3, 0])
        r = np.random.default_rng(3)
        trs = [ValueTracker(r.uniform(0, 1)) for _ in range(18)]
        knobs = VGroup(*[Knob("·", t, 0, 1, radius=0.22) for t in trs])
        for k in knobs:
            k[-1].set_opacity(0)
        knobs.arrange_in_grid(rows=3, cols=6, buff=0.32).move_to([2.6, 0.4, 0])
        self.play_bars(FadeIn(tw), FadeIn(knobs), bars=0.75)
        self.play_bars(*[t.animate.set_value(r.uniform(0, 1)) for t in trs], bars=1)
        # 7–8 没有老师
        self.at_bar(7)
        self.play_bars(FadeOut(VGroup(tw, knobs)), bars=0.25)
        teacher = VGroup(Circle(radius=0.35, color=C_WHITE, stroke_width=3).move_to(UP * 1.2),
                         Line(UP * 0.85, DOWN * 0.3, color=C_WHITE, stroke_width=3),
                         Line(UP * 0.5, UP * 0.9 + RIGHT * 0.8, color=C_WHITE, stroke_width=3),
                         Rectangle(width=1.6, height=1.0, color=C_GREY).move_to(RIGHT * 1.7 + UP * 1.0)).move_to([-1.0, 0.4, 0])
        cross = VGroup(Line(UL, DR), Line(UR, DL)).set_stroke(C_RED, 8).scale(1.3).move_to(teacher)
        q = T("答案在哪？", size=36, color=C_GOLD).next_to(teacher, RIGHT, buff=0.8)
        self.play_bars(FadeIn(teacher), bars=0.5)
        self.play_bars(Create(cross), FadeIn(q), bars=0.75)
        # 9–10 一段文字
        self.at_bar(9)
        self.play_bars(FadeOut(VGroup(teacher, cross, q)), bars=0.25)
        self.tag("答案就在文字里")
        sent = sentence(TEXT, y=0.0, size=32)
        self.play_bars(LaggedStart(*[FadeIn(b, shift=UP * 0.15) for b in sent], lag_ratio=0.1), bars=1.25)
        # 11–12 遮住后面，猜下一个
        self.at_bar(11)
        m, qc = self.mask_quiz(sent, 1)
        self.play_bars(FadeIn(m), FadeIn(qc), bars=0.5)
        for k in (2, 3, 4):
            m2, q2 = self.mask_quiz(sent, k)
            self.play_bars(Transform(m, m2), Transform(qc, q2), bars=0.4)
        # 13–14 猜错 → 损失 → 反向 → 旋钮
        self.at_bar(13)
        guess = VGroup(T("猜：", size=26, color=C_GREY), token_block("冷", color=C_RED, size=26)).arrange(RIGHT, buff=0.1)
        guess.next_to(qc, UP, buff=0.2)
        ans = VGroup(T("答案：", size=26, color=C_GREY), token_block("好", color=C_GREEN, size=26)).arrange(RIGHT, buff=0.1)
        ans.next_to(guess, RIGHT, buff=0.5)
        self.play_bars(FadeIn(guess), FadeIn(ans), bars=0.5)
        loss = VGroup(Rectangle(width=2.2, height=0.3, color=C_RED, fill_opacity=0.8), T("损失", size=22, color=C_RED))
        loss.arrange(RIGHT, buff=0.2).move_to([-4.0, -1.6, 0])
        mt = tower(3, w=1.6, h=0.4).move_to([0.5, -1.7, 0])
        back = Arrow(mt.get_top() + UP * 0.1, mt.get_bottom() + DOWN * 0.1, buff=0, color=C_RED, stroke_width=5).next_to(mt, RIGHT, buff=0.15)
        mk = VGroup(*[Knob("·", ValueTracker(0.3 + 0.1 * i), 0, 1, radius=0.18) for i in range(3)]).arrange(RIGHT, buff=0.25)
        for kk in mk:
            kk[-1].set_opacity(0)
        mk.next_to(back, RIGHT, buff=0.4)
        self.play_bars(FadeIn(loss), FadeIn(mt), bars=0.5)
        self.play_bars(GrowArrow(back), FadeIn(mk), bars=0.5)
        self.play_bars(*[kk.tracker.animate.set_value(kk.tracker.get_value() + 0.25) for kk in mk], bars=0.5)
        # 15–16 自监督
        self.at_bar(15)
        self.play_bars(FadeOut(VGroup(guess, ans, loss, mt, back, mk)), bars=0.25)
        ss = VGroup(T("自监督", size=44, color=C_GOLD, weight=BOLD), T("不用人工标注：文字自己就是答案", size=28, color=C_WHITE)).arrange(DOWN, buff=0.2)
        ss.move_to([0, -1.7, 0])
        self.play_bars(FadeIn(ss, shift=UP * 0.2), bars=0.75)
        self.at_bar(16.75)
        self.fade_rest(0.25)
        # 17–18 练习簿
        self.at_bar(17)
        self.tag("现成的练习簿")

        def icon(kind):
            if kind == "网页":
                g = VGroup(RoundedRectangle(width=1.5, height=1.1, corner_radius=0.08, color=C_BLUE),
                           Line(LEFT * 0.75, RIGHT * 0.75, color=C_BLUE).shift(UP * 0.35),
                           *[Line(LEFT * 0.5, RIGHT * (0.5 - 0.2 * i), color=C_GREY).shift(DOWN * (0.05 + 0.2 * i)) for i in range(3)])
            elif kind == "书籍":
                g = VGroup(*[book(1.0, 0.25, C_GOLD, 0.4).shift(RIGHT * 0.3 * i) for i in range(4)]).move_to(ORIGIN)
            elif kind == "百科":
                g = VGroup(Circle(radius=0.55, color=C_TEAL), T("百科", size=26, color=C_TEAL))
            else:
                g = VGroup(RoundedRectangle(width=1.5, height=1.1, corner_radius=0.08, color=C_GREEN), T("</>", size=34, color=C_GREEN))
            return VGroup(g, T(kind, size=26, color=C_WHITE).next_to(g, DOWN, buff=0.25))

        icons = VGroup(*[icon(k) for k in ["网页", "书籍", "百科", "代码"]]).arrange(RIGHT, buff=1.2).move_to([0, 0.5, 0])
        self.play_bars(LaggedStart(*[FadeIn(i, shift=UP * 0.2) for i in icons], lag_ratio=0.2), bars=1.25)
        # 19–20 传送带
        self.at_bar(19)
        self.play_bars(FadeOut(icons), bars=0.25)
        cards = VGroup()
        for i in range(10):
            c = VGroup(RoundedRectangle(width=1.4, height=0.9, corner_radius=0.1, color=C_GOLD, fill_opacity=0.12),
                       T(f"第 {i + 1} 题", size=20, color=C_GOLD))
            c[1].move_to(c[0])
            cards.add(c)
        cards.arrange(RIGHT, buff=0.25).move_to([3.0, 0.3, 0]).align_to([-5.5, 0, 0], LEFT)
        more = T("……", size=40, color=C_GOLD).next_to(cards, RIGHT, buff=0.2)
        self.add(cards, more)
        self.play_bars(VGroup(cards, more).animate.shift(LEFT * 6), bars=1.25, rate_func=linear)
        self.fade_rest(0.5)

    # ------------------------------------------------------------ 副歌
    def hook(self, s):
        self.at_bar(s)
        self.tag("猜下一个词")
        sent = sentence(TEXT, y=0.6, size=30)
        m, qc = self.mask_quiz(sent, 2)
        self.play_bars(FadeIn(sent), bars=0.5)
        self.play_bars(FadeIn(m), FadeIn(qc), bars=0.5)
        m2, q2 = self.mask_quiz(sent, 3)
        self.play_bars(Transform(m, m2), Transform(qc, q2), bars=0.5)
        # ② 记录
        self.at_bar(s + 2)
        marks = VGroup()
        for i, ok in enumerate([True, False, True, True, False, True, True, True]):
            marks.add(T("✓" if ok else "✗", size=32, color=C_GREEN if ok else C_RED))
        marks.arrange(RIGHT, buff=0.35).move_to([0, -1.0, 0])
        self.play_bars(LaggedStart(*[FadeIn(x, scale=1.5) for x in marks], lag_ratio=0.15), bars=1.25)
        # ③ 书堆 + 计时器
        self.at_bar(s + 4)
        self.play_bars(FadeOut(VGroup(sent, m, qc, marks)), bars=0.25)
        r = np.random.default_rng(s)
        stack = VGroup(*[Rectangle(width=r.uniform(1.4, 1.9), height=0.16, stroke_color=C_GOLD, stroke_width=1.2,
                                   fill_color=C_GOLD, fill_opacity=r.uniform(0.2, 0.5)) for _ in range(26)]).arrange(UP, buff=0.02)
        stack.move_to([-2.5, 0.0, 0]).align_to([0, -2.2, 0], DOWN)
        rd = reader(0.9).move_to([1.5, -1.0, 0])
        years = ValueTracker(0)
        yt = always_redraw(lambda: T(f"已读 {int(years.get_value()):,} 年", size=30, color=C_GOLD).move_to([3.6, 1.2, 0]))
        self.play_bars(LaggedStart(*[FadeIn(b, shift=DOWN * 0.3) for b in stack], lag_ratio=0.05), FadeIn(rd), FadeIn(yt),
                       years.animate.set_value(95000), bars=1.5)
        # ④ 误差曲线往下
        self.at_bar(s + 6)
        self.play_bars(FadeOut(VGroup(stack, rd, yt)), bars=0.25)
        ax = Axes(x_range=[0, 6], y_range=[0, 3], x_length=6.0, y_length=3.2, tips=False,
                  axis_config=dict(color=C_GREY, stroke_width=2)).move_to([0, 0.2, 0])
        xl = T("规模", size=24, color=C_GREY).next_to(ax.x_axis, RIGHT, buff=0.15)
        yl = T("误差", size=24, color=C_RED).next_to(ax.y_axis, UP, buff=0.1)
        cv = ax.plot(lambda x: 2.7 * np.exp(-0.42 * x) + 0.15, x_range=[0, 6], color=C_RED, stroke_width=4)
        self.play_bars(FadeIn(ax), FadeIn(xl), FadeIn(yl), bars=0.25)
        self.play_bars(Create(cv), bars=1.25)
        # ⑤ 黑箱
        self.at_bar(s + 8)
        self.fade_rest(0.25)
        box = black_box(w=3.2, h=2.2, depth=0.45).move_to([0, 0.2, 0])
        pages = VGroup(*[Rectangle(width=0.5, height=0.65, stroke_color=C_GOLD, stroke_width=1.2, fill_color=C_GOLD,
                                   fill_opacity=0.25).rotate(r.uniform(-0.4, 0.4)).move_to(box.front.get_center() + np.array([r.uniform(-1, 1), r.uniform(-0.6, 0.5), 0]))
                         for _ in range(10)])
        self.play_bars(FadeIn(box), bars=0.25)
        self.play_bars(VGroup(box.front, box.q).animate.shift(UP * 0.3).set_opacity(0.12), FadeIn(pages), bars=0.5)
        slogan = T("一层一层，把黑箱打开", size=40, color=C_YELLOW, weight=BOLD).to_edge(UP, buff=0.3)
        self.play_bars(Write(slogan), bars=0.5)
        self.at_bar(s + 9.5)
        self.fade_rest(0.5)

    # ------------------------------------------------------------ 主歌二 31–46：规模
    def verse2(self):
        self.at_bar(31)
        self.tag("读了多少？")
        big = T("约 15,000,000,000,000 个 token", size=52, color=C_GOLD, weight=BOLD).move_to([0, 0.9, 0])
        if big.width > 12.5:
            big.scale_to_fit_width(12.5)
        src = T("Llama 3（2024）的训练数据量", size=28, color=C_GREY).next_to(big, DOWN, buff=0.3)
        self.play_bars(FadeIn(big, scale=0.8), bars=0.75)
        self.play_bars(FadeIn(src), bars=0.5)
        # 33–34 读书小人
        self.at_bar(33)
        self.play_bars(big.animate.scale(0.55).move_to([0, 2.6, 0]), FadeOut(src), bars=0.5)
        rd = reader(1.4).move_to([-3.2, -0.2, 0])
        cond = VGroup(T("每分钟读 300 个 token", size=30, color=C_WHITE), T("不吃、不睡、不停", size=30, color=C_WHITE)).arrange(DOWN, buff=0.2)
        cond.move_to([2.4, 0.6, 0])
        self.play_bars(FadeIn(rd), FadeIn(cond), bars=0.75)
        self.play_bars(Wiggle(rd[4]), bars=0.5)
        # 35–36 9.5 万年
        self.at_bar(35)
        years = ValueTracker(0)
        yt = always_redraw(lambda: T(f"{int(years.get_value()):,} 年", size=54, color=C_GOLD, weight=BOLD).move_to([2.4, -0.5, 0]))
        self.play_bars(FadeIn(yt), years.animate.set_value(95000), bars=1)
        calc = T("15×10¹² ÷ 300 ÷ 525,600（每年分钟数）≈ 9.5 万年 · 数量级估算", size=22, color=C_GREY).move_to([0.6, -1.9, 0])
        self.play_bars(FadeIn(calc), bars=0.5)
        self.at_bar(36.75)
        self.fade_rest(0.25, extra_keep=[big])
        # 37–38 GPU
        self.at_bar(37)
        self.tag("算了多少？")
        grid = VGroup(*[Rectangle(width=0.26, height=0.36, stroke_color=C_GREEN, stroke_width=1, fill_color=C_GREEN, fill_opacity=0.08)
                        for _ in range(32 * 8)]).arrange_in_grid(rows=8, cols=32, buff=0.06).move_to([0, 0.3, 0])
        gl = T("上万块 GPU · 连续跑上数周到数月（最大的模型）", size=26, color=C_GREEN).next_to(grid, DOWN, buff=0.3)
        self.play_bars(FadeOut(big), FadeIn(grid), bars=0.5)
        self.play_bars(LaggedStart(*[g.animate.set_fill(opacity=0.7) for g in grid], lag_ratio=0.003), FadeIn(gl), bars=1.25)
        # 39–40 3×10²³
        self.at_bar(39)
        self.play_bars(FadeOut(grid), FadeOut(gl), bars=0.25)
        flops = VGroup(T("GPT-3（2020）训练", size=32, color=C_WHITE),
                       T("约 3×10²³ 次浮点运算", size=52, color=C_YELLOW, weight=BOLD)).arrange(DOWN, buff=0.3).move_to([0, 0.8, 0])
        self.play_bars(FadeIn(flops[0]), FadeIn(flops[1], scale=0.8), bars=1)
        # 41–42 核对
        self.at_bar(41)
        check = T("核对：6 × 1750 亿参数 × 3000 亿 token ≈ 3.15×10²³", size=30, color=C_GREY).next_to(flops, DOWN, buff=0.6)
        rule = T("（训练计算量 ≈ 6 × 参数量 × token 数：每个 token 前向约 2 次、反向约 4 次运算 / 参数）", size=20, color=C_GREY).next_to(check, DOWN, buff=0.2)
        self.play_bars(FadeIn(check), bars=0.75)
        self.play_bars(FadeIn(rule), bars=0.5)
        # 43–44 旧账
        self.at_bar(43)
        old = T("注意：这些都是 GPT-3（2020）的数；很多新模型不公开", size=28, color=C_ORANGE).move_to([0, -1.9, 0])
        self.play_bars(FadeIn(old, shift=UP * 0.2), bars=0.75)
        self.at_bar(44.75)
        self.fade_rest(0.25)
        # 45–46 每个旋钮都是猜词调出来的
        self.at_bar(45)
        line = T("旋钮的数量早就超过了 1000 亿，", size=32, color=C_WHITE)
        line2 = T("而每一个都是被“猜下一个词”这个任务调出来的。", size=32, color=C_WHITE)
        g = VGroup(line, line2).arrange(DOWN, buff=0.25).move_to([0, 0.5, 0])
        self.play_bars(Indicate(self.counter, color=C_YELLOW), FadeIn(line), bars=0.75)
        self.play_bars(FadeIn(line2), bars=0.75)

    # ------------------------------------------------------------ 间奏一 47–50：比例尺
    def inst1(self):
        self.at_bar(47)
        self.fade_rest(0.25)
        self.tag("数据规模（示意）")
        b1 = book(1.0, 0.7, C_GOLD, 0.5).move_to([0, 0.3, 0])
        l1 = T("一本书", size=30, color=C_GOLD).next_to(b1, DOWN, buff=0.3)
        self.play_bars(FadeIn(b1), FadeIn(l1), bars=0.5)
        shelf = VGroup(*[book(0.8, 0.14, C_GOLD, 0.4) for _ in range(30)]).arrange(RIGHT, buff=0.02).move_to([0, 0.3, 0])
        l2 = T("一个书架", size=30, color=C_GOLD).next_to(shelf, DOWN, buff=0.3)
        self.play_bars(ReplacementTransform(b1, shelf), Transform(l1, l2), bars=0.75)
        lib = VGroup(Polygon([-1.4, 0.6, 0], [1.4, 0.6, 0], [0, 1.2, 0], color=C_GOLD),
                     *[Line([x, -0.8, 0], [x, 0.6, 0], color=C_GOLD, stroke_width=4) for x in np.linspace(-1.1, 1.1, 6)],
                     Line([-1.4, -0.8, 0], [1.4, -0.8, 0], color=C_GOLD, stroke_width=4)).move_to([0, 0.3, 0])
        l3 = T("一座图书馆", size=30, color=C_GOLD).next_to(lib, DOWN, buff=0.3)
        self.play_bars(ReplacementTransform(shelf, lib), Transform(l1, l3), bars=0.75)
        city = VGroup(*[lib.copy().scale(0.22) for _ in range(40)]).arrange_in_grid(rows=4, cols=10, buff=0.18).move_to([0, 0.4, 0])
        l4 = T("一座城的图书馆……（示意）", size=30, color=C_GOLD).next_to(city, DOWN, buff=0.3)
        self.play_bars(ReplacementTransform(lib, city), Transform(l1, l4), bars=1)
        self.at_bar(50.5)
        self.fade_rest(0.5)

    # ------------------------------------------------------------ 主歌三 61–76：规模定律
    def verse3(self):
        self.at_bar(61)
        self.tag("规模定律")
        ax = Axes(x_range=[0, 6], y_range=[0, 3], x_length=8.0, y_length=4.2, tips=False,
                  axis_config=dict(color=C_GREY, stroke_width=2)).move_to([-0.8, 0.25, 0])
        xl = T("算力（对数）", size=24, color=C_GREY).next_to(ax.x_axis, DOWN, buff=0.15).align_to(ax.x_axis, RIGHT)
        yl = T("误差（对数）", size=24, color=C_RED).next_to(ax.y_axis, UP, buff=0.1).align_to(ax.y_axis, LEFT)
        self.play_bars(Create(ax), FadeIn(xl), FadeIn(yl), bars=1)
        demo = T("（示意）", size=20, color=C_GREY).next_to(yl, RIGHT, buff=0.3)
        self.play_bars(FadeIn(demo), bars=0.25)
        # 63–64 一组曲线
        self.at_bar(63)

        def env(x):
            return 2.75 - 0.42 * x

        curves = VGroup()
        cols = [interpolate_color(ManimColor(C_BLUE), ManimColor(C_PURPLE), i / 5) for i in range(6)]
        for i in range(6):
            x0 = 0.15 + 0.8 * i
            floor = env(x0 + 1.4) - 0.05
            y0 = 2.85

            def f(x, x0=x0, floor=floor, y0=y0):
                return floor + (y0 - floor) * np.exp(-1.6 * (x - x0))

            curves.add(ax.plot(f, x_range=[x0, min(6, x0 + 3.2)], color=cols[i], stroke_width=3))
        sizes = T("小模型 → 大模型", size=24, color=C_PURPLE).move_to([4.8, 1.8, 0])
        self.play_bars(LaggedStart(*[Create(c) for c in curves], lag_ratio=0.25), FadeIn(sizes), bars=1.75)
        # 65–66 包络直线
        self.at_bar(65)
        env_l = ax.plot(lambda x: env(x) - 0.06, x_range=[0.6, 5.4], color=C_GOLD, stroke_width=5)
        el = T("几乎一条直线", size=28, color=C_GOLD).next_to(ax.c2p(4.2, env(4.2)), UR, buff=0.2)
        self.play_bars(Create(env_l), FadeIn(el), bars=1.25)
        # 67–68 名字
        self.at_bar(67)
        nm = T("规模定律（Kaplan 等，2020）", size=28, color=C_WHITE).move_to([4.0, 2.6, 0])
        if nm.get_right()[0] > 6.9:
            nm.shift(LEFT * (nm.get_right()[0] - 6.9))
        nm2 = T("参数、数据、算力越多，误差按幂律下降", size=22, color=C_GREY).next_to(nm, DOWN, buff=0.15)
        if nm2.get_right()[0] > 6.9:
            nm2.shift(LEFT * (nm2.get_right()[0] - 6.9))
        self.play_bars(FadeOut(sizes), FadeIn(nm), FadeIn(nm2), bars=0.75)
        self.at_bar(68.75)
        self.fade_rest(0.25)
        # 69–70 同样算力：U 形
        self.at_bar(69)
        self.tag("参数和数据要一起加")
        ax2 = Axes(x_range=[0, 6], y_range=[0, 3], x_length=7.0, y_length=3.8, tips=False,
                   axis_config=dict(color=C_GREY, stroke_width=2)).move_to([-1.2, 0.2, 0])
        x2 = T("模型大小（同样的算力）", size=22, color=C_GREY).next_to(ax2.x_axis, DOWN, buff=0.15).align_to(ax2.x_axis, RIGHT)
        y2 = T("误差", size=22, color=C_RED).next_to(ax2.y_axis, UP, buff=0.1).align_to(ax2.y_axis, LEFT)
        u = ax2.plot(lambda x: 0.18 * (x - 3.0) ** 2 + 0.8, x_range=[0.3, 5.7], color=C_RED, stroke_width=4)
        best = Dot(ax2.c2p(3.0, 0.8), radius=0.1, color=C_GOLD)
        lft = T("模型太小", size=22, color=C_GREY).next_to(ax2.c2p(0.8, 1.7), UP, buff=0.05)
        rgt = T("模型太大、数据太少", size=22, color=C_GREY).next_to(ax2.c2p(5.0, 1.6), UP, buff=0.05)
        self.play_bars(FadeIn(ax2), FadeIn(x2), FadeIn(y2), Create(u), bars=1)
        self.play_bars(FadeIn(best, scale=1.5), FadeIn(lft), FadeIn(rgt), bars=0.75)
        # 71–72 Chinchilla
        self.at_bar(71)
        ch = VGroup(T("Chinchilla（2022）", size=30, color=C_GOLD),
                    T("每个参数约配 20 个 token", size=28, color=C_WHITE),
                    T("例：700 亿参数 × 1.4 万亿 token", size=22, color=C_GREY)).arrange(DOWN, buff=0.18).move_to([4.4, -1.0, 0])
        if ch.get_right()[0] > 6.9:
            ch.shift(LEFT * (ch.get_right()[0] - 6.9))
        self.play_bars(LaggedStart(*[FadeIn(c, shift=LEFT * 0.2) for c in ch], lag_ratio=0.3), Indicate(best, color=C_GOLD), bars=1.5)
        self.at_bar(72.75)
        self.fade_rest(0.25)
        # 73–74 只在范围内
        self.at_bar(73)
        self.tag("经验规律")
        ax3 = Axes(x_range=[0, 8], y_range=[0, 3], x_length=9.0, y_length=3.8, tips=False,
                   axis_config=dict(color=C_GREY, stroke_width=2)).move_to([-0.3, 0.2, 0])
        solid = ax3.plot(lambda x: 2.75 - 0.3 * x, x_range=[0.2, 5.0], color=C_GOLD, stroke_width=5)
        dash = DashedVMobject(ax3.plot(lambda x: 2.75 - 0.3 * x, x_range=[5.0, 7.8], color=C_GOLD, stroke_width=4), num_dashes=14)
        zone = Rectangle(width=ax3.c2p(5, 0)[0] - ax3.c2p(0.2, 0)[0], height=3.8, stroke_width=0, fill_color=C_GREEN,
                         fill_opacity=0.06).move_to(ax3.c2p(2.6, 1.5))
        zl = T("实测范围", size=24, color=C_GREEN).move_to(ax3.c2p(2.6, 2.85))
        qm = T("？", size=48, color=C_GOLD).next_to(ax3.c2p(7.6, 0.5), UP, buff=0.1)
        self.play_bars(FadeIn(ax3), FadeIn(zone), Create(solid), FadeIn(zl), bars=1)
        self.play_bars(Create(dash), FadeIn(qm), bars=0.75)
        # 75–76 注释卡
        self.at_bar(75)
        card = VGroup(T("经验规律 · 有适用范围", size=30, color=C_WHITE),
                      T("不是物理定律，不代表“无限加大就无限变强”", size=26, color=C_RED)).arrange(DOWN, buff=0.18)
        bg = SurroundingRectangle(card, color=C_GREY, buff=0.22, corner_radius=0.12, fill_color=BG, fill_opacity=0.95)
        VGroup(bg, card).move_to([0, -1.9, 0])
        self.play_bars(FadeIn(bg), FadeIn(card), bars=0.75)
        self.at_bar(76.5)
        self.fade_rest(0.5)

    # ------------------------------------------------------------ 桥段 77–84
    def bridge(self):
        self.at_bar(77)
        self.tag("要猜准，得懂世界")
        q1 = VGroup(T("水烧到一百度会", size=40, color=C_WHITE), token_block("____", color=C_GOLD, size=34))
        q1.arrange(RIGHT, buff=0.2).move_to([0, 1.3, 0])
        q2 = VGroup(T("法国的首都是", size=40, color=C_WHITE), token_block("____", color=C_GOLD, size=34))
        q2.arrange(RIGHT, buff=0.2).move_to([0, 0.0, 0])
        self.play_bars(FadeIn(q1), bars=1)
        self.play_bars(FadeIn(q2), bars=1)
        a1 = token_block("沸腾", color=C_GREEN, size=34).move_to(q1[1])
        a2 = token_block("巴黎", color=C_GREEN, size=34).move_to(q2[1])
        self.play_bars(Transform(q1[1], a1), Transform(q2[1], a2), bars=1.5)
        self.at_bar(81)
        self.play_bars(VGroup(q1, q2).animate.scale(0.6).move_to([-4.0, 1.6, 0]), bars=0.5)
        tw = tower(8, w=2.6, h=0.42).move_to([0.6, -0.1, 0])
        self.play_bars(FadeIn(tw), bars=0.75)
        tags = VGroup(T("语法", size=30, color=C_BLUE), T("事实", size=30, color=C_GOLD), T("推理套路", size=30, color=C_GREEN))
        tags.arrange(DOWN, buff=0.45).move_to([4.2, 0.0, 0])
        lines = VGroup(*[Line(tw.get_right() + RIGHT * 0.1, t.get_left() + LEFT * 0.1, color=t.get_color(), stroke_width=2) for t in tags])
        self.play_bars(LaggedStart(*[AnimationGroup(Create(l), FadeIn(t)) for l, t in zip(lines, tags)], lag_ratio=0.4), bars=2)
        self.at_bar(84.5)
        self.fade_rest(0.5)

    # ------------------------------------------------------------ 主歌四 85–100
    def verse4(self):
        self.at_bar(85)
        self.tag("基座模型")
        tw = tower(6).move_to([-4.0, 0.3, 0])
        lab = VGroup(T("基座模型", size=32, color=C_GOLD, weight=BOLD), T("= 文档续写机", size=26, color=C_WHITE)).arrange(DOWN, buff=0.12)
        lab.next_to(tw, DOWN, buff=0.3)
        self.play_bars(FadeIn(tw), FadeIn(lab), bars=1)
        # 87–88 问题
        self.at_bar(87)
        doc = RoundedRectangle(width=7.4, height=4.0, corner_radius=0.15, color=C_GREY, fill_color="#121621", fill_opacity=1).move_to([2.2, 0.3, 0])
        l1 = T("1. 法国的首都是哪里？", size=30, color=C_WHITE).move_to(doc.get_corner(UL) + np.array([2.0, -0.6, 0]), aligned_edge=LEFT)
        l1.align_to(doc.get_left() + RIGHT * 0.4, LEFT)
        self.play_bars(FadeIn(doc), FadeIn(l1), bars=1)
        # 89–90 续写出更多题目
        self.at_bar(89)
        l2 = T("2. 德国的首都是哪里？", size=30, color=C_GOLD).next_to(l1, DOWN, buff=0.35, aligned_edge=LEFT)
        l3 = T("3. 意大利的首都是哪里？", size=30, color=C_GOLD).next_to(l2, DOWN, buff=0.35, aligned_edge=LEFT)
        self.play_bars(Write(l2), bars=0.6)
        self.play_bars(Write(l3), bars=0.6)
        qm = T("？", size=60, color=C_RED).next_to(l3, RIGHT, buff=0.5)
        self.play_bars(FadeIn(qm, scale=1.5), bars=0.3)
        # 91–92 有时也直接回答
        self.at_bar(91)
        alt = T("另一种续写：法国的首都是巴黎。", size=28, color=C_GREEN).next_to(l3, DOWN, buff=0.45, aligned_edge=LEFT)
        tend = T("只是倾向，不是绝对", size=24, color=C_GREY).next_to(alt, DOWN, buff=0.15, aligned_edge=LEFT)
        self.play_bars(FadeIn(alt), bars=0.75)
        self.play_bars(FadeIn(tend), bars=0.5)
        self.at_bar(92.75)
        self.fade_rest(0.25)
        # 93–94 偏见与错误
        self.at_bar(93)
        self.tag("照单全收")
        tw2 = tower(6).move_to([3.4, 0.3, 0])
        docs = VGroup()
        r = np.random.default_rng(6)
        for i in range(12):
            bad = i % 4 == 1
            d = VGroup(Rectangle(width=0.8, height=1.0, stroke_color=C_RED if bad else C_GREY, stroke_width=2,
                                 fill_color="#1a1f2c", fill_opacity=1),
                       *[Line(LEFT * 0.28, RIGHT * 0.28, color=C_RED if (bad and j == 1) else C_GREY, stroke_width=2).shift(UP * (0.25 - 0.18 * j))
                         for j in range(4)])
            d.move_to([r.uniform(-6, -1.5), r.uniform(-1.6, 2.0), 0])
            docs.add(d)
        bl = T("红色：带偏见或错误的内容", size=24, color=C_RED).move_to([-3.6, -2.3, 0])
        self.play_bars(FadeIn(tw2), FadeIn(docs), FadeIn(bl), bars=0.5)
        self.play_bars(LaggedStart(*[d.animate.move_to(tw2.get_center()).scale(0.2).set_opacity(0) for d in docs], lag_ratio=0.06),
                       bars=1.0)
        self.at_bar(94.75)
        self.fade_rest(0.25)
        # 95–96 涌现：突然跳升
        self.at_bar(95)
        self.tag("“涌现”？")
        axL = Axes(x_range=[0, 6], y_range=[0, 1], x_length=4.8, y_length=3.0, tips=False,
                   axis_config=dict(color=C_GREY, stroke_width=2)).move_to([-3.3, 0.55, 0])
        jump = axL.plot(lambda x: 0.03 + 0.8 / (1 + np.exp(-6 * (x - 4.4))), x_range=[0, 6], color=C_ORANGE, stroke_width=4)
        tL = T("计分：全对才算对", size=24, color=C_ORANGE).next_to(axL, UP, buff=0.2)
        xL = T("模型规模", size=20, color=C_GREY).next_to(axL.x_axis, DOWN, buff=0.12)
        self.play_bars(FadeIn(axL), FadeIn(tL), FadeIn(xL), bars=0.5)
        self.play_bars(Create(jump), bars=1)
        sud = T("突然冒出来？", size=26, color=C_ORANGE).next_to(axL.c2p(4.4, 0.6), LEFT, buff=0.2)
        self.play_bars(FadeIn(sud), bars=0.25)
        # 97–98 换种量法：平滑
        self.at_bar(97)
        axR = Axes(x_range=[0, 6], y_range=[0, 1], x_length=4.8, y_length=3.0, tips=False,
                   axis_config=dict(color=C_GREY, stroke_width=2)).move_to([3.3, 0.55, 0])
        smooth_ = axR.plot(lambda x: 0.1 + 0.13 * x, x_range=[0, 6], color=C_TEAL, stroke_width=4)
        tR = T("换成连续的计分", size=24, color=C_TEAL).next_to(axR, UP, buff=0.2)
        xR = T("模型规模", size=20, color=C_GREY).next_to(axR.x_axis, DOWN, buff=0.12)
        self.play_bars(FadeIn(axR), FadeIn(tR), FadeIn(xR), bars=0.5)
        self.play_bars(Create(smooth_), bars=1)
        sl = T("慢慢上升", size=26, color=C_TEAL).next_to(axR.c2p(3.5, 0.6), UP, buff=0.1)
        self.play_bars(FadeIn(sl), bars=0.25)
        # 99–100 仍有争论
        self.at_bar(99)
        card = VGroup(T("“涌现”是否真的突然出现：学界仍有争论", size=28, color=C_WHITE),
                      T("结论和“怎么计分、怎么测量”有关（曲线为示意）", size=22, color=C_GREY)).arrange(DOWN, buff=0.15)
        card.move_to([0, -2.25, 0])
        self.play_bars(FadeIn(card, shift=UP * 0.2), bars=0.75)
        self.at_bar(100.5)
        self.fade_rest(0.5)

    # ------------------------------------------------------------ 间奏二 101–104：要点
    def inst2(self):
        self.at_bar(101)
        self.tag("本集要点")
        head = T("本集要点", size=46, color=C_YELLOW, weight=BOLD)
        pts = [
            "1. 预训练 = 在海量文本上猜下一个 token；文字自己就是答案（自监督）",
            "2. 规模巨大：例如 Llama 3 约 15 万亿 token；GPT-3 训练约 3×10²³ 次运算",
            "3. 规模定律：参数、数据、算力越多，误差越规律地下降（经验规律，有范围）",
            "4. 预训练完 = 基座模型：只会续写，照单全收数据里的偏见；“涌现”仍有争论",
        ]
        items = VGroup(*[T(p, size=27) for p in pts]).arrange(DOWN, aligned_edge=LEFT, buff=0.3)
        g = VGroup(head, items).arrange(DOWN, buff=0.5).move_to([0, 0.35, 0])
        if g.width > 13.3:
            g.scale_to_fit_width(13.3)
        self.play_bars(FadeIn(head, shift=DOWN * 0.2), bars=0.25)
        for it in items:
            self.play_bars(FadeIn(it, shift=RIGHT * 0.3), bars=0.5)
        self.at_bar(104.5)
        self.play_bars(FadeOut(g), bars=0.5)

    # ------------------------------------------------------------ 尾声 115–122
    def outro(self):
        self.at_bar(115)
        self.tag("回顾")
        sent = sentence(TEXT, y=0.5, size=30)
        m, qc = self.mask_quiz(sent, 5)
        self.play_bars(FadeIn(sent), FadeIn(m), FadeIn(qc), bars=0.75)
        m2, q2 = self.mask_quiz(sent, 6)
        self.play_bars(Transform(m, m2), Transform(qc, q2), bars=0.5)
        # 117–118 续写机
        self.at_bar(117)
        self.play_bars(FadeOut(VGroup(sent, m, qc)), bars=0.25)
        tw = tower(6).move_to([0, 0.4, 0])
        lab = T("基座模型：只会往下续写", size=30, color=C_GOLD).next_to(tw, DOWN, buff=0.3)
        self.play_bars(FadeIn(tw), FadeIn(lab), bars=1)
        # 119–120 怎么变成助手
        self.at_bar(119)
        self.play_bars(VGroup(tw, lab).animate.scale(0.7).move_to([-4.2, 0.2, 0]), bars=0.5)
        qb = VGroup(RoundedRectangle(width=4.2, height=0.9, corner_radius=0.2, color=C_BLUE, fill_opacity=0.15),
                    T("法国的首都是哪里？", size=28, color=C_BLUE))
        qb[1].move_to(qb[0])
        qb.move_to([1.6, 1.2, 0])
        ab = VGroup(DashedVMobject(RoundedRectangle(width=4.2, height=0.9, corner_radius=0.2, color=C_GREEN), num_dashes=30),
                    T("（好好回答的助手？）", size=26, color=C_GREEN))
        ab[1].move_to(ab[0])
        ab.move_to([2.4, -0.2, 0])
        self.play_bars(FadeIn(qb), FadeIn(ab), bars=1)
        # 121–122 下集
        self.at_bar(121)
        self.play_bars(FadeOut(VGroup(qb, ab)), bars=0.25)
        nxt = VGroup(T("下集（正片）", size=28, color=C_GREY), T("后训练", size=48, color=C_GREEN, weight=BOLD),
                     T("从续写机器到 AI 助手", size=30, color=C_GREEN)).arrange(DOWN, buff=0.2).move_to([2.0, 0.6, 0])
        side = T("岔路 · 番外二：强化学习——AI 怎么自己学会下棋", size=22, color=C_GREY).next_to(nxt, DOWN, buff=0.35)
        self.play_bars(FadeIn(nxt, shift=UP * 0.2), FadeIn(side), bars=1)
        self.at_bar(122.25)
        self.play_bars(*[FadeOut(m) for m in self.visible()], bars=0.75)
