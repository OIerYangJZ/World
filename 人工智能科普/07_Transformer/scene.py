# -*- coding: utf-8 -*-
"""
第 07 集《Transformer：一次只猜下一个词》

时间全部对齐 bars.py 的 BPM 小节网格（100 BPM，130 小节）。字幕由 build.py 烧录。
    ~/.venvs/manim/bin/python ../common/build.py 07_Transformer [--preview]

说明：概率、分数、切分方式、生成结果都是示意数值，不是某个真实模型的输出；
96 层、12,288 维、2048 上下文、1750 亿参数是 GPT-3 的公开数字。
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "common"))
from style import *  # noqa: E402,F401

PROMPT = ["床", "前", "明月", "光", "，", "疑", "是", "地", "上"]
CANDS = ["霜", "上", "雪", "面", "光", "白"]
PROBS = np.array([0.86, 0.04, 0.03, 0.03, 0.02, 0.02])
C_ATT, C_MLP = C_PURPLE, C_TEAL


def token_block(text, color=C_BLUE, size=30, pad=0.14, fill=0.18, h=0.6):
    t = T(text, size=size, color=C_WHITE)
    r = RoundedRectangle(width=max(t.width + 2 * pad, 0.5), height=h, corner_radius=0.08,
                         stroke_color=color, stroke_width=2.5, fill_color=color, fill_opacity=fill)
    return VGroup(r, t.move_to(r))


def sentence(words, y=0.0, size=30, color=C_BLUE, buff=0.1, x=0.0):
    return VGroup(*[token_block(w, color=color, size=size) for w in words]).arrange(RIGHT, buff=buff).move_to([x, y, 0])


def block(w=3.2, h=0.9, labels=True, size=24):
    """一个 Transformer 块：下面注意力，上面前馈"""
    att = RoundedRectangle(width=w, height=h / 2 - 0.03, corner_radius=0.08, color=C_ATT, fill_opacity=0.28, stroke_width=2.5)
    mlp = RoundedRectangle(width=w, height=h / 2 - 0.03, corner_radius=0.08, color=C_MLP, fill_opacity=0.28, stroke_width=2.5)
    mlp.next_to(att, UP, buff=0.06)
    g = VGroup(att, mlp)
    if labels:
        g.add(T("注意力", size=size, color=C_ATT).move_to(att), T("前馈", size=size, color=C_MLP).move_to(mlp))
    return g


def tower(n, w=3.2, h=0.9, gap=0.12, labels=True, size=24):
    g = VGroup(*[block(w, h, labels, size) for _ in range(n)]).arrange(UP, buff=gap)
    return g


def prob_bars(cands, probs, x0=0.0, y0=0.0, width=0.6, gap=0.3, hmax=3.0, color=C_GOLD, size=26):
    g = VGroup()
    for i, (c, p) in enumerate(zip(cands, probs)):
        x = x0 + i * (width + gap)
        h = max(p * hmax, 0.02)
        r = Rectangle(width=width, height=h, stroke_width=0, fill_color=color, fill_opacity=0.9).move_to([x, y0 + h / 2, 0])
        lab = T(c, size=size, color=C_WHITE).move_to([x, y0 - 0.32, 0])
        num = T(f"{p:.2f}", size=18, color=C_GREY).next_to(r, UP, buff=0.06)
        g.add(VGroup(r, lab, num))
    return g


def mini_net(scale=0.5, color=C_MLP):
    xs = [-0.6, 0, 0.6]
    sizes = [3, 4, 3]
    cols = [VGroup(*[Circle(radius=0.08, color=color, stroke_width=2).move_to([x, (n - 1) / 2 * 0.3 - i * 0.3, 0])
                     for i in range(n)]) for x, n in zip(xs, sizes)]
    eds = VGroup(*[Line(a.get_center(), b.get_center(), stroke_width=1, color=color, stroke_opacity=0.6)
                   for c1, c2 in zip(cols[:-1], cols[1:]) for a in c1 for b in c2])
    return VGroup(eds, *cols).scale(scale / 0.5)


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
        card = title_card("第 07 集", "Transformer", "一次只猜下一个词")
        s, e, t, line, st = card
        self.play_bars(FadeIn(s, shift=DOWN * 0.2), FadeIn(e, shift=DOWN * 0.2), bars=0.75)
        self.play_bars(Write(t), bars=1)
        self.play_bars(GrowFromCenter(line), FadeIn(st, shift=UP * 0.2), bars=0.75)
        self.at_bar(3.5)
        self.set_counter("586 亿", bars=0.5)
        self.at_bar(4.5)
        self.play_bars(FadeOut(card), bars=0.5)

    # ------------------------------------------------------------ 主歌一 5–20
    def verse1(self):
        self.at_bar(5)
        self.tag("组装零件")
        att = VGroup(RoundedRectangle(width=3.4, height=1.4, corner_radius=0.15, color=C_ATT, fill_opacity=0.25),
                     T("注意力", size=40, color=C_ATT)).move_to([-3.2, 0.4, 0])
        att[1].move_to(att[0])
        arcs = VGroup(*[ArcBetweenPoints(att[0].get_corner(DL) + RIGHT * (0.4 + 0.5 * i) + UP * 0.25,
                                         att[0].get_corner(DL) + RIGHT * (1.2 + 0.5 * i) + UP * 0.25, angle=-PI * 0.6,
                                         color=C_ATT, stroke_width=2) for i in range(4)])
        self.play_bars(FadeIn(att, shift=RIGHT * 2), bars=1)
        self.play_bars(Create(arcs), bars=0.75)
        # 7–8 前馈网络
        self.at_bar(7)
        mlp = VGroup(RoundedRectangle(width=3.4, height=1.4, corner_radius=0.15, color=C_MLP, fill_opacity=0.25),
                     T("前馈网络（MLP）", size=32, color=C_MLP)).move_to([3.2, 0.4, 0])
        mlp[1].move_to(mlp[0].get_top() + DOWN * 0.35)
        mn = mini_net(0.45).move_to(mlp[0].get_center() + DOWN * 0.2)
        ref = T("= 第 02 集那种神经网络", size=22, color=C_GREY).next_to(mlp, DOWN, buff=0.25)
        self.play_bars(FadeIn(mlp, shift=LEFT * 2), FadeIn(mn, shift=LEFT * 2), bars=1)
        self.play_bars(FadeIn(ref), bars=0.5)
        self.at_bar(8.75)
        self.play_bars(FadeOut(VGroup(att, arcs, mlp, mn, ref)), bars=0.25)
        # 9–10 注意力：token 之间交流
        self.at_bar(9)
        sent = sentence(PROMPT, y=-0.6)
        lab = T("注意力：信息在 token 之间流动", size=30, color=C_ATT).move_to([0, 2.2, 0])
        links = VGroup(*[ArcBetweenPoints(sent[i].get_top(), sent[j].get_top(), angle=-PI * 0.5 * min(1, 3 / max(abs(i - j) * 0.8, 0.1)),
                                          color=C_ATT, stroke_width=2.5, stroke_opacity=0.8)
                         for i, j in [(0, 3), (2, 3), (5, 8), (6, 7), (1, 0), (8, 3), (7, 5)]])
        self.play_bars(FadeIn(sent), FadeIn(lab), bars=0.5)
        self.play_bars(LaggedStart(*[Create(l) for l in links], lag_ratio=0.15), bars=1.25)
        # 11–12 前馈：每个 token 自己算
        self.at_bar(11)
        lab2 = T("前馈：每个 token 各自过一遍小网络", size=30, color=C_MLP).move_to(lab)
        nets = VGroup(*[mini_net(0.22).next_to(b, UP, buff=0.25) for b in sent])
        self.play_bars(FadeOut(links), Transform(lab, lab2), bars=0.5)
        self.play_bars(LaggedStart(*[FadeIn(n, shift=UP * 0.2) for n in nets], lag_ratio=0.08), bars=1.25)
        # 13–14 拼成一个块
        self.at_bar(13)
        self.play_bars(FadeOut(VGroup(nets, lab)), sent.animate.scale(0.8).move_to([0, -2.0, 0]), bars=0.5)
        b1 = block(w=4.0, h=1.4, size=30).move_to([0, -0.4, 0])
        bl = T("一个 Transformer 块", size=30, color=C_WHITE).next_to(b1, RIGHT, buff=0.4)
        self.play_bars(FadeIn(b1[0], shift=UP * 0.3), FadeIn(b1[2]), bars=0.5)
        self.play_bars(FadeIn(b1[1], shift=DOWN * 0.3), FadeIn(b1[3]), FadeIn(bl), bars=0.75)
        # 15–16 叠成四层
        self.at_bar(15)
        t4 = tower(4, w=4.0, h=1.0, gap=0.1, size=24).move_to([0, 0.35, 0]).align_to(b1, DOWN)
        cnt = T("4 层", size=30, color=C_WHITE).next_to(t4, RIGHT, buff=0.4)
        self.play_bars(FadeOut(bl), ReplacementTransform(b1, t4[0]), bars=0.5)
        self.play_bars(LaggedStart(*[TransformFromCopy(t4[0], t4[k]) for k in (1, 2, 3)], lag_ratio=0.4), FadeIn(cnt), bars=1.25)
        # 17–18 越叠越高
        self.at_bar(17)
        tall = tower(24, w=2.0, h=0.32, gap=0.03, labels=False).move_to([0, 0.35, 0])
        tall.align_to(sent, DOWN).shift(UP * 0.7)
        tall.stretch_to_fit_height(4.4).align_to([0, -1.6, 0], DOWN)
        dots = T("⋮", size=40, color=C_GREY).next_to(tall, UP, buff=0.05)
        c96 = T("GPT-3：96 层", size=32, color=C_YELLOW).next_to(tall, RIGHT, buff=0.5)
        self.play_bars(FadeOut(cnt), ReplacementTransform(t4, tall), bars=1)
        self.play_bars(FadeIn(dots), FadeIn(c96), bars=0.75)
        # 19–20 句子送进去
        self.at_bar(19)
        arr = Arrow(sent.get_top(), tall.get_bottom(), buff=0.05, color=C_BLUE, stroke_width=4)
        q = T("下一个 token？", size=28, color=C_GOLD).next_to(dots, UP, buff=0.1)
        self.play_bars(GrowArrow(arr), LaggedStart(*[b.animate.set_fill(opacity=0.5) for b in tall], lag_ratio=0.03), bars=1)
        self.play_bars(FadeIn(q), bars=0.5)
        self.at_bar(20.5)
        self.fade_rest(0.5)

    # ------------------------------------------------------------ 副歌
    def hook(self, s):
        self.at_bar(s)
        self.tag("一次只猜下一个词")
        sent = sentence(PROMPT, y=-2.0, size=24)
        tw = tower(6, w=2.4, h=0.55, gap=0.06, labels=False).move_to([0, 0.15, 0])
        q = T("下一个是谁？", size=30, color=C_GOLD).next_to(tw, UP, buff=0.2)
        self.play_bars(FadeIn(sent), FadeIn(tw), bars=0.75)
        self.play_bars(FadeIn(q, scale=1.3), bars=0.75)
        # ② 一层层堆
        self.at_bar(s + 2)
        self.play_bars(LaggedStart(*[Indicate(b, color=C_YELLOW, scale_factor=1.05) for b in tw], lag_ratio=0.12), bars=1.5)
        # ③ 概率排队
        self.at_bar(s + 4)
        bars_ = prob_bars(CANDS, PROBS, x0=2.8, y0=-0.9, width=0.45, gap=0.2, hmax=2.6, size=24)
        self.play_bars(FadeOut(q), LaggedStart(*[GrowFromEdge(b[0], DOWN) for b in bars_], lag_ratio=0.1),
                       *[FadeIn(b[1]) for b in bars_], *[FadeIn(b[2]) for b in bars_], bars=1.5)
        # ④ 挑一个接上去
        self.at_bar(s + 6)
        pick = token_block("霜", color=C_GOLD, size=24).move_to(bars_[0][0].get_top() + UP * 0.4)
        new_row = sentence(PROMPT + ["霜"], y=-2.0, size=24)
        self.play_bars(FadeIn(pick, scale=1.4), bars=0.5)
        self.play_bars(pick.animate.move_to(new_row[-1]), Transform(sent, new_row[:-1]), bars=0.75)
        self.play_bars(LaggedStart(*[b.animate.set_fill(opacity=0.55) for b in tw], lag_ratio=0.08), bars=0.75)
        # ⑤ 黑箱
        self.at_bar(s + 8)
        self.fade_rest(0.25)
        box = black_box(w=3.0, h=2.4, depth=0.45).move_to([0, 0.2, 0])
        inner = tower(5, w=1.4, h=0.36, gap=0.04, labels=False).move_to(box.front)
        self.play_bars(FadeIn(box), bars=0.25)
        self.play_bars(VGroup(box.front, box.q).animate.shift(UP * 0.3).set_opacity(0.12), FadeIn(inner), bars=0.5)
        slogan = T("一层一层，把黑箱打开", size=40, color=C_YELLOW, weight=BOLD).to_edge(UP, buff=0.3)
        self.play_bars(Write(slogan), bars=0.5)
        self.at_bar(s + 9.5)
        self.fade_rest(0.5)

    # ------------------------------------------------------------ 主歌二 31–50：残差流
    def verse2(self):
        self.at_bar(31)
        self.tag("残差流")
        xs = [-3.6, -1.8, 0.0, 1.8, 3.6]
        layers = VGroup(*[RoundedRectangle(width=0.9, height=4.2, corner_radius=0.1, color=C_GREY, stroke_width=1.5,
                                           fill_color=C_ATT if k % 2 == 0 else C_MLP, fill_opacity=0.12).move_to([x, 0.4, 0])
                          for k, x in enumerate(xs)])
        llabs = VGroup(*[T(f"第{k + 1}层", size=20, color=C_GREY).next_to(l, UP, buff=0.08) for k, l in enumerate(layers)])
        ys = [1.6, 0.4, -0.8]
        names = ["疑", "是", "地上"]
        belts = VGroup(*[Line([-6.0, y, 0], [6.0, y, 0], color=C_BLUE, stroke_width=6, stroke_opacity=0.35) for y in ys])
        tl = VGroup(*[token_block(n, size=26).move_to([-6.3, y, 0]) for n, y in zip(names, ys)])
        self.play_bars(FadeIn(layers), FadeIn(llabs), Create(belts), FadeIn(tl), bars=1)
        glows = VGroup(*[Dot([-5.6, y, 0], radius=0.12, color=C_BLUE) for y in ys])
        self.play_bars(*[g.animate.move_to([5.6, g.get_y(), 0]) for g in glows], bars=0.75, rate_func=linear)
        self.remove(glows)
        # 33–36 向量一层层加修改
        self.at_bar(33)
        y0 = ys[1]
        v = np.array([0.9, 0.3, 0]) * 1.1
        deltas = [np.array([0.05, 0.3, 0]), np.array([0.25, -0.15, 0]), np.array([-0.15, 0.3, 0]),
                  np.array([0.25, 0.15, 0]), np.array([-0.1, 0.3, 0])]
        start = np.array([-5.4, y0, 0])
        vec = Arrow(start, start + v, buff=0, color=C_YELLOW, stroke_width=6, max_tip_length_to_length_ratio=0.25)
        self.play_bars(GrowArrow(vec), bars=0.5)
        cur = v.copy()
        self.v2_bits = VGroup()
        per = 1.5 / 3
        for k in range(3):
            base = np.array([xs[k] - 0.6, y0, 0])
            moved = Arrow(base, base + cur, buff=0, color=C_YELLOW, stroke_width=6, max_tip_length_to_length_ratio=0.25)
            d = Arrow(base + cur, base + cur + deltas[k], buff=0, color=C_GREEN, stroke_width=7, max_tip_length_to_length_ratio=0.5)
            self.play_bars(Transform(vec, moved), bars=per / 2)
            self.play_bars(GrowArrow(d), bars=per / 2)
            cur = cur + deltas[k]
            self.v2_bits.add(d)
        add_l = T("每层只“加一笔”修改", size=26, color=C_GREEN).move_to([0, -2.1, 0])
        self.at_bar(35)
        self.play_bars(FadeIn(add_l), bars=0.25)
        for k in (3, 4):
            base = np.array([xs[k] - 0.6, y0, 0])
            moved = Arrow(base, base + cur, buff=0, color=C_YELLOW, stroke_width=6, max_tip_length_to_length_ratio=0.25)
            d = Arrow(base + cur, base + cur + deltas[k], buff=0, color=C_GREEN, stroke_width=7, max_tip_length_to_length_ratio=0.5)
            self.play_bars(Transform(vec, moved), GrowArrow(d), bars=0.375)
            cur = cur + deltas[k]
            self.v2_bits.add(d)
        res_l = T("残差流：小修改一层层累加，方向慢慢变", size=26, color=C_YELLOW).move_to(add_l)
        self.play_bars(Transform(add_l, res_l), bars=0.75)
        # 37–38 × 96
        self.at_bar(37)
        x96 = T("× 96 层（GPT-3）", size=34, color=C_YELLOW).move_to([4.8, 2.75, 0])
        self.play_bars(FadeIn(x96, scale=1.2), *[l.animate.set_stroke(C_YELLOW, opacity=0.8) for l in layers], bars=1)
        # 39–40 12,288 维
        self.at_bar(39)
        dim = T("传送带上的向量：12,288 维（GPT-3）", size=26, color=C_WHITE).move_to([0, -2.1, 0])
        self.play_bars(Transform(add_l, dim), bars=1)
        self.at_bar(40.5)
        self.fade_rest(0.5)
        # 41–42 参数构成
        self.at_bar(41)
        self.tag("1750 亿个旋钮在哪里")
        total = 1746.0
        parts = [("嵌入 约 6 亿", 6.4, C_BLUE), ("注意力 约 580 亿", 580.0, C_ATT), ("前馈 约 1160 亿", 1160.0, C_MLP)]
        W = 11.0
        bar = VGroup()
        x = -W / 2
        for nm, v_, col in parts:
            w = max(W * v_ / total, 0.06)
            r = Rectangle(width=w, height=0.8, stroke_width=0, fill_color=col, fill_opacity=0.85).move_to([x + w / 2, 0.6, 0])
            bar.add(r)
            x += w
        labs = VGroup(T("嵌入 ≈ 6 亿", size=22, color=C_BLUE).next_to(bar[0], DOWN, buff=0.35).shift(RIGHT * 0.5),
                      T("注意力 ≈ 580 亿（约 1/3）", size=24, color=C_ATT).next_to(bar[1], UP, buff=0.25),
                      T("前馈 ≈ 1160 亿（约 2/3）", size=24, color=C_MLP).next_to(bar[2], UP, buff=0.25))
        note = T("（GPT-3：每层注意力约 4×12,288²，前馈约 8×12,288²，共 96 层）", size=20, color=C_GREY).move_to([0, -1.0, 0])
        self.play_bars(LaggedStart(*[GrowFromEdge(r, LEFT) for r in bar], lag_ratio=0.3), bars=1)
        self.play_bars(FadeIn(labs), FadeIn(note), bars=0.75)
        # 43–44 前馈层与事实
        self.at_bar(43)
        self.play_bars(FadeOut(VGroup(bar, labs, note)), bars=0.25)
        mlp = VGroup(RoundedRectangle(width=4.2, height=2.4, corner_radius=0.15, color=C_MLP, fill_opacity=0.18),
                     T("前馈层", size=30, color=C_MLP)).move_to([0, 0.5, 0])
        mlp[1].move_to(mlp[0].get_top() + DOWN * 0.3)
        cells = VGroup(*[Square(side_length=0.32, color=C_MLP, fill_opacity=0.1, stroke_width=1.5) for _ in range(24)])
        cells.arrange_in_grid(rows=3, cols=8, buff=0.12).move_to(mlp[0].get_center() + DOWN * 0.25)
        rs = T("研究认为：很多“事实”像是存在这里", size=26, color=C_MLP).next_to(mlp, DOWN, buff=0.3)
        self.play_bars(FadeIn(mlp), FadeIn(cells), bars=0.5)
        self.play_bars(LaggedStart(*[c.animate.set_fill(C_GOLD, 0.8) for c in cells[3::5]], lag_ratio=0.2), FadeIn(rs), bars=1)
        # 45–46 埃菲尔铁塔
        self.at_bar(45)
        inp = token_block("埃菲尔铁塔位于", size=28).move_to([-4.8, 0.5, 0])
        a1 = Arrow(inp.get_right(), mlp[0].get_left(), buff=0.1, color=C_BLUE)
        out_bars = prob_bars(["巴黎", "伦敦", "罗马"], [0.08, 0.05, 0.04], x0=4.1, y0=-0.2, width=0.55, gap=0.25, hmax=3.0, size=22)
        out_hi = prob_bars(["巴黎", "伦敦", "罗马"], [0.72, 0.04, 0.03], x0=4.1, y0=-0.2, width=0.55, gap=0.25, hmax=3.0, size=22)
        a2 = Arrow(mlp[0].get_right(), [3.6, 0.5, 0], buff=0.1, color=C_GOLD)
        self.play_bars(FadeIn(inp), GrowArrow(a1), FadeIn(out_bars), GrowArrow(a2), bars=0.75)
        self.play_bars(Transform(out_bars, out_hi), Indicate(cells[8], color=C_GOLD), bars=0.75)
        ill = T("（示意）", size=20, color=C_GREY).next_to(out_bars, DOWN, buff=0.45)
        self.play_bars(FadeIn(ill), bars=0.25)
        # 47–48 只是一种解释
        self.at_bar(47)
        card = VGroup(T("这是研究中的一种解释：", size=26, color=C_WHITE),
                      T("前馈层像“键值记忆”，能推高与事实相关的词", size=24, color=C_GREY),
                      T("不是定论", size=28, color=C_RED, weight=BOLD)).arrange(DOWN, buff=0.15)
        bg = SurroundingRectangle(card, color=C_GREY, buff=0.25, corner_radius=0.12, fill_color=BG, fill_opacity=0.95)
        cg = VGroup(bg, card).move_to([0, -1.6, 0])
        self.play_bars(FadeOut(rs), FadeIn(cg, shift=UP * 0.2), bars=0.75)
        self.at_bar(48.75)
        self.fade_rest(0.25)
        # 49–50 1750 亿
        self.at_bar(49)
        big = T("175,000,000,000", size=80, color=C_YELLOW, weight=BOLD).move_to([0, 0.7, 0])
        sub = T("GPT-3（2020）的参数 = 旋钮个数", size=30, color=C_GREY).next_to(big, DOWN, buff=0.35)
        for t in ["700 亿", "1200 亿", "1600 亿", "1750 亿"]:
            self.set_counter(t, bars=0.15)
        self.play_bars(FadeIn(big, scale=0.8), FadeIn(sub), bars=0.75)
        nn = T("注：很多新模型不公开参数量；这里的数字都是 GPT-3 的", size=20, color=C_GREY).next_to(sub, DOWN, buff=0.25)
        self.play_bars(FadeIn(nn), bars=0.5)

    # ------------------------------------------------------------ 间奏一 51–54：完整前向
    def inst1(self):
        self.at_bar(51)
        self.fade_rest(0.25)
        self.tag("一次完整的前向")
        sent = sentence(PROMPT, y=-2.15, size=24)
        tw = tower(8, w=3.0, h=0.5, gap=0.05, labels=False).move_to([0, 0.0, 0])
        self.play_bars(FadeIn(sent), FadeIn(tw), bars=0.5)
        self.play_bars(LaggedStart(*[b.animate.set_fill(opacity=0.6) for b in tw], lag_ratio=0.15), bars=1.75)
        bars_ = prob_bars(CANDS, PROBS, x0=2.6, y0=0.6, width=0.4, gap=0.18, hmax=2.0, size=22)
        self.play_bars(LaggedStart(*[GrowFromEdge(b[0], DOWN) for b in bars_], lag_ratio=0.1),
                       *[FadeIn(b[1]) for b in bars_], *[FadeIn(b[2]) for b in bars_], bars=0.75)
        self.at_bar(54.5)
        self.fade_rest(0.5)

    # ------------------------------------------------------------ 主歌三 65–84：输出概率
    def verse3(self):
        self.at_bar(65)
        self.tag("塔顶：下一个 token 的概率")
        sent = sentence(PROMPT, y=-2.15, size=24, x=-2.8)
        tw = tower(6, w=2.6, h=0.5, gap=0.05, labels=False).move_to([-2.8, -0.1, 0])
        self.play_bars(FadeIn(sent), FadeIn(tw), bars=0.5)
        last = sent[-1]
        top_v = VGroup(*[Square(side_length=0.22, stroke_width=1, stroke_color="#2a2f3d",
                                fill_color=interpolate_color(ManimColor("#1a1f2c"), ManimColor(C_YELLOW), float(v)), fill_opacity=1)
                         for v in np.random.default_rng(4).uniform(0, 1, 10)]).arrange(RIGHT, buff=0.02).next_to(tw, UP, buff=0.25)
        hl = SurroundingRectangle(last, color=C_GOLD, buff=0.05)
        self.play_bars(Create(hl), TransformFromCopy(last, top_v), bars=1.0)
        tvl = T("最后一个 token 的向量", size=22, color=C_GOLD).next_to(top_v, UP, buff=0.12)
        self.play_bars(FadeIn(tvl), bars=0.25)
        # 67–68 和词表比一比
        self.at_bar(67)
        vocab = VGroup(*[token_block(c, color=C_GREY, size=22, h=0.5) for c in CANDS + ["…"]]).arrange(DOWN, buff=0.08).move_to([2.2, 0.0, 0])
        lines = VGroup(*[Line(top_v.get_right(), v.get_left(), color=C_GOLD, stroke_width=1.5, stroke_opacity=0.6) for v in vocab[:-1]])
        scores = [9.1, 6.2, 5.9, 5.8, 5.4, 5.4]
        sc = VGroup(*[T(f"{s_:.1f}", size=22, color=C_WHITE).next_to(v, RIGHT, buff=0.2) for v, s_ in zip(vocab[:-1], scores)])
        vl = T("词表里的每个 token", size=22, color=C_GREY).next_to(vocab, UP, buff=0.15)
        self.play_bars(FadeIn(vocab), FadeIn(vl), Create(lines), bars=1)
        self.play_bars(LaggedStart(*[FadeIn(s_) for s_ in sc], lag_ratio=0.1), bars=0.75)
        # 69–70 softmax → 概率
        self.at_bar(69)
        pbar = VGroup()
        for v, p in zip(vocab[:-1], PROBS):
            r = Rectangle(width=max(p * 3.6, 0.03), height=0.32, stroke_width=0, fill_color=C_GOLD, fill_opacity=0.9)
            r.next_to(v, RIGHT, buff=0.25)
            pbar.add(r)
        pn = VGroup(*[T(f"{p:.2f}", size=20, color=C_GREY).next_to(r, RIGHT, buff=0.1) for r, p in zip(pbar, PROBS)])
        sm = T("softmax → 概率（加起来 = 1）", size=24, color=C_GOLD).next_to(vocab, UP, buff=0.15).align_to(vocab, LEFT)
        self.play_bars(FadeOut(lines), ReplacementTransform(sc, pbar), ReplacementTransform(vl, sm), bars=1)
        self.play_bars(FadeIn(pn), bars=0.5)
        # 71–72 句子与问题
        self.at_bar(71)
        blank = token_block("？", color=C_GOLD, size=24).next_to(sent, RIGHT, buff=0.1)
        self.play_bars(FadeIn(blank, scale=1.3), bars=0.5)
        self.play_bars(Indicate(vocab[0], color=C_GOLD), bars=0.75)
        # 73–74 霜 最高
        self.at_bar(73)
        self.play_bars(pbar[0].animate.set_fill(C_GOLD, 1).set_stroke(C_WHITE, 2), vocab[0][0].animate.set_stroke(C_GOLD, 4),
                       pn[0].animate.set_color(C_GOLD).scale(1.3), bars=0.75)
        self.play_bars(Flash(pbar[0].get_right(), color=C_GOLD), bars=0.5)
        # 75–76 其他很矮
        self.at_bar(75)
        self.play_bars(*[pbar[i].animate.set_fill(opacity=0.45) for i in range(1, 6)], bars=0.75)
        demo = T("（概率为示意）", size=20, color=C_GREY).next_to(vocab, DOWN, buff=0.2)
        self.play_bars(FadeIn(demo), bars=0.25)
        # 77–78 不是查答案
        self.at_bar(77)
        nq = T("不是查答案：给每个候选估一个概率", size=26, color=C_WHITE).move_to([-0.4, 2.95, 0])
        self.play_bars(FadeIn(nq), bars=0.75)
        # 79–80 背过很多回
        self.at_bar(79)
        seen = T("这句诗在训练数据里出现过很多次 → 概率很集中", size=24, color=C_GREY).move_to(nq)
        self.play_bars(Transform(nq, seen), bars=0.75)
        self.at_bar(80.75)
        self.play_bars(FadeOut(VGroup(blank, demo)), bars=0.25)
        # 81–82 没见过的开头
        self.at_bar(81)
        new_sent = sentence(["窗外", "的", "雨", "下", "个", "不"], y=-2.15, size=24, x=-2.8)
        new_c = ["停", "住", "歇", "断", "完", "了"]
        new_p = np.array([0.52, 0.18, 0.12, 0.08, 0.06, 0.04])
        new_vocab = VGroup(*[token_block(c, color=C_GREY, size=22, h=0.5) for c in new_c + ["…"]]).arrange(DOWN, buff=0.08).move_to(vocab)
        new_bars = VGroup()
        for v, p in zip(new_vocab[:-1], new_p):
            r = Rectangle(width=max(p * 3.6, 0.03), height=0.32, stroke_width=0, fill_color=C_GOLD, fill_opacity=0.9)
            r.next_to(v, RIGHT, buff=0.25)
            new_bars.add(r)
        new_pn = VGroup(*[T(f"{p:.2f}", size=20, color=C_GREY).next_to(r, RIGHT, buff=0.1) for r, p in zip(new_bars, new_p)])
        spread = T("没见过的开头：概率更分散（示意）", size=24, color=C_GREY).move_to(nq)
        self.play_bars(Transform(sent, new_sent), Transform(vocab, new_vocab), Transform(pbar, new_bars), Transform(pn, new_pn),
                       FadeOut(hl), bars=1)
        self.play_bars(Transform(nq, spread), bars=0.5)
        # 83–84 整座塔开会
        self.at_bar(83)
        self.play_bars(LaggedStart(*[Indicate(b, color=C_YELLOW, scale_factor=1.04) for b in tw], lag_ratio=0.1),
                       Indicate(self.counter, color=C_YELLOW), bars=1.25)
        self.at_bar(84.5)
        self.fade_rest(0.5)

    # ------------------------------------------------------------ 桥段 85–92
    def bridge(self):
        self.at_bar(85)
        self.tag("一直猜下去")
        one = token_block("霜", color=C_GOLD, size=60, h=1.0).move_to([0, 0.4, 0])
        self.play_bars(FadeIn(one, scale=0.6), bars=1)
        self.play_bars(Indicate(one, color=C_GOLD), bars=1)
        self.at_bar(88.5)
        poem = ["疑", "是", "地", "上", "霜", "。", "举", "头", "望", "明月", "，", "低", "头", "思", "故乡", "。"]
        row1 = sentence(poem[:6], y=1.0, size=40)
        row2 = sentence(poem[6:], y=-0.3, size=40)
        rows = VGroup(*row1, *row2)
        for b in rows:
            b.set_opacity(0)
        self.add(rows)
        self.play_bars(one.animate.move_to(row1[4]).scale(0.66), bars=0.5)
        self.remove(one)
        row1[4].set_opacity(1)
        row1[4][0].set_fill(opacity=0.18)
        order = [0, 1, 2, 3, 5] + list(range(6, len(poem)))
        per = 3.5 / len(order)
        for idx in order:
            b = rows[idx]
            self.play_bars(b.animate.set_opacity(1).set_fill(opacity=0.18), bars=per)
        self.at_bar(92.5)
        self.fade_rest(0.5)

    # ------------------------------------------------------------ 主歌四 93–108
    def verse4(self):
        self.at_bar(93)
        self.tag("自回归：一个接一个")
        sent = sentence(PROMPT, y=-2.15, size=24)
        tw = tower(6, w=2.4, h=0.5, gap=0.05, labels=False).move_to([0, 0.3, 0])
        self.play_bars(FadeIn(sent), FadeIn(tw), bars=0.5)
        pick = token_block("霜", color=C_GOLD, size=24).next_to(tw, UP, buff=0.3)
        self.play_bars(FadeIn(pick, shift=UP * 0.2), bars=0.5)
        row = sentence(PROMPT + ["霜"], y=-2.15, size=24)
        self.play_bars(pick.animate.move_to(row[-1]), Transform(sent, row[:-1]), bars=0.5)
        self.play_bars(LaggedStart(*[b.animate.set_fill(opacity=0.55) for b in tw], lag_ratio=0.1), bars=0.25)
        # 95–96 再猜再接
        self.at_bar(95)
        seq = PROMPT + ["霜"]
        cur_row = VGroup(*sent, pick)
        for nxt in ["。", "举", "头"]:
            seq = seq + [nxt]
            new = sentence(seq, y=-2.15, size=22)
            if new.width > 13:
                new.scale_to_fit_width(13)
            p = token_block(nxt, color=C_GOLD, size=22).next_to(tw, UP, buff=0.3)
            self.play_bars(FadeIn(p, shift=UP * 0.2), LaggedStart(*[Indicate(b, color=C_YELLOW, scale_factor=1.03) for b in tw],
                                                                   lag_ratio=0.05), bars=0.3)
            self.play_bars(p.animate.move_to(new[-1]), Transform(cur_row, new[:-1]), bars=0.3)
            cur_row = VGroup(*cur_row, p)
        # 97–98 结束
        self.at_bar(97)
        end = token_block("〈结束〉", color=C_RED, size=24).next_to(tw, UP, buff=0.3)
        self.play_bars(FadeIn(end, scale=1.3), bars=0.5)
        done = T("回答完成", size=28, color=C_GREEN).next_to(end, RIGHT, buff=0.4)
        self.play_bars(FadeIn(done), bars=0.5)
        self.at_bar(98.75)
        self.fade_rest(0.25)
        # 99–100 温度
        self.at_bar(99)
        self.tag("温度：怎么挑")
        Tt = ValueTracker(1.0)
        base = PROBS.copy()

        X0, GAP = -3.6, 1.05
        tlabels = VGroup(*[T(c, size=28, color=C_WHITE).move_to([X0 + i * GAP, -1.72, 0]) for i, c in enumerate(CANDS)])

        def tbars():
            p = base ** (1.0 / Tt.get_value())
            p = p / p.sum()
            return VGroup(*[Rectangle(width=0.7, height=max(pi * 3.4, 0.02), stroke_width=0, fill_color=C_GOLD,
                                      fill_opacity=0.9).move_to([X0 + i * GAP, -1.4 + max(pi * 3.4, 0.02) / 2, 0])
                            for i, pi in enumerate(p)])

        bars_ = VGroup(always_redraw(tbars), tlabels)
        slider = Line([2.2, 0.2, 0], [6.0, 0.2, 0], color=C_GREY, stroke_width=4)
        knob = always_redraw(lambda: Dot(slider.point_from_proportion((np.log(Tt.get_value()) + np.log(4)) / (2 * np.log(4))),
                                         radius=0.15, color=C_ORANGE))
        sl = VGroup(T("温度", size=28, color=C_ORANGE).next_to(slider, UP, buff=0.35),
                    T("低", size=22, color=C_GREY).next_to(slider, DOWN, buff=0.15).align_to(slider, LEFT),
                    T("高", size=22, color=C_GREY).next_to(slider, DOWN, buff=0.15).align_to(slider, RIGHT))
        tval = always_redraw(lambda: T(f"T = {Tt.get_value():.2f}", size=24, color=C_ORANGE).next_to(slider, DOWN, buff=0.6))
        self.play_bars(FadeIn(bars_), Create(slider), FadeIn(knob), FadeIn(sl), FadeIn(tval), bars=1)
        self.play_bars(Wiggle(knob), bars=0.5)
        # 101–102 低 / 高
        self.at_bar(101)
        self.play_bars(Tt.animate.set_value(0.4), bars=0.75)
        self.play_bars(Tt.animate.set_value(3.5), bars=1)
        # 103–104 两次回答不一样
        self.at_bar(103)
        self.play_bars(FadeOut(VGroup(bars_, slider, knob, sl, tval)), bars=0.25)
        p_ = T("窗外的雨", size=34, color=C_BLUE)
        r1 = VGroup(p_.copy(), T("下个不停，", size=34, color=C_GOLD), T("像在敲门", size=34, color=C_GOLD)).arrange(RIGHT, buff=0.1)
        r2 = VGroup(p_.copy(), T("轻轻落下，", size=34, color=C_TEAL), T("湿了窗台", size=34, color=C_TEAL)).arrange(RIGHT, buff=0.1)
        lab1 = T("第 1 次：", size=26, color=C_GREY)
        lab2 = T("第 2 次：", size=26, color=C_GREY)
        g1 = VGroup(lab1, r1).arrange(RIGHT, buff=0.3)
        g2 = VGroup(lab2, r2).arrange(RIGHT, buff=0.3)
        gg = VGroup(g1, g2).arrange(DOWN, buff=0.5, aligned_edge=LEFT).move_to([0, 0.5, 0])
        self.play_bars(FadeIn(g1, shift=RIGHT * 0.2), bars=0.6)
        self.play_bars(FadeIn(g2, shift=RIGHT * 0.2), bars=0.6)
        dm = T("（生成结果为示意）", size=20, color=C_GREY).next_to(gg, DOWN, buff=0.35)
        self.play_bars(FadeIn(dm), bars=0.3)
        # 105–106 旋钮不动
        self.at_bar(105)
        lock = VGroup(RoundedRectangle(width=0.36, height=0.28, corner_radius=0.05, color=C_GREY, fill_opacity=1).shift(DOWN * 0.07),
                      Arc(radius=0.12, angle=PI, color=C_GREY, stroke_width=4).shift(UP * 0.09)).next_to(self.counter, LEFT, buff=0.2)
        card = VGroup(T("温度只影响“怎么挑”（采样）", size=28, color=C_ORANGE),
                      T("模型本身的 1750 亿个旋钮一个都不变", size=26, color=C_WHITE)).arrange(DOWN, buff=0.15).move_to([0, -1.5, 0])
        self.play_bars(FadeOut(dm), FadeIn(card, shift=UP * 0.2), FadeIn(lock), bars=0.75)
        self.at_bar(106.75)
        self.fade_rest(0.25)
        # 107–108 上下文窗口
        self.at_bar(107)
        self.tag("上下文窗口")
        cells = VGroup(*[Square(side_length=0.26, stroke_width=1, stroke_color="#2a2f3d", fill_color=C_BLUE, fill_opacity=0.5)
                         for _ in range(44)]).arrange(RIGHT, buff=0.03).move_to([0, 0.4, 0])
        win = SurroundingRectangle(VGroup(*cells[:18]), color=C_YELLOW, buff=0.06, stroke_width=4)
        wl = T("能看到的范围：上下文窗口（GPT-3：2048 个 token）", size=24, color=C_YELLOW).move_to([0, 1.4, 0])
        self.play_bars(FadeIn(cells), Create(win), FadeIn(wl), *[c.animate.set_fill(opacity=0.12) for c in cells[18:]], bars=0.5)
        shift = cells[1].get_center() - cells[0].get_center()
        outl = T("太长：最早的部分被挤出窗口，看不到", size=24, color=C_GREY).move_to([0, -0.6, 0])
        self.play_bars(win.animate.shift(shift * 26), *[c.animate.set_fill(opacity=0.12) for c in cells[:26]],
                       *[c.animate.set_fill(opacity=0.5) for c in cells[26:]], FadeIn(outl), bars=0.75)
        self.at_bar(108.5)
        self.fade_rest(0.5)

    # ------------------------------------------------------------ 间奏二 109–112：要点
    def inst2(self):
        self.at_bar(109)
        self.tag("本集要点")
        head = T("本集要点", size=46, color=C_YELLOW, weight=BOLD)
        pts = [
            "1. Transformer 块 = 注意力（词和词交流）+ 前馈（每个词自己算），叠几十到上百层",
            "2. 残差流：每层只在 token 的向量上“加一笔”；前馈层约占三分之二参数（GPT-3）",
            "3. 塔顶给词表里每个 token 打分 → softmax → 下一个 token 的概率",
            "4. 挑一个接上，再送回去猜下一个（自回归）；温度只影响怎么挑",
        ]
        items = VGroup(*[T(p, size=27) for p in pts]).arrange(DOWN, aligned_edge=LEFT, buff=0.3)
        g = VGroup(head, items).arrange(DOWN, buff=0.5).move_to([0, 0.35, 0])
        if g.width > 13.3:
            g.scale_to_fit_width(13.3)
        self.play_bars(FadeIn(head, shift=DOWN * 0.2), bars=0.25)
        for it in items:
            self.play_bars(FadeIn(it, shift=RIGHT * 0.3), bars=0.5)
        self.at_bar(112.5)
        self.play_bars(FadeOut(g), bars=0.5)

    # ------------------------------------------------------------ 尾声 123–130
    def outro(self):
        self.at_bar(123)
        self.tag("回顾")
        tw = tower(4, w=2.8, h=0.8, gap=0.08, size=22).move_to([-3.6, 0.3, 0])
        belt = Arrow(tw.get_corner(DL) + LEFT * 0.35 + DOWN * 0.3, tw.get_corner(UL) + LEFT * 0.35 + UP * 0.3, buff=0,
                     color=C_BLUE, stroke_width=6)
        bl = T("残差流", size=22, color=C_BLUE).next_to(belt, LEFT, buff=0.15)
        self.play_bars(FadeIn(tw), Create(belt), FadeIn(bl), bars=1.25)
        # 125–126 流程
        self.at_bar(125)
        steps = [("打分", C_GOLD), ("概率", C_GOLD), ("挑一个", C_ORANGE), ("接上", C_BLUE), ("再来", C_GREEN)]
        chips = VGroup()
        for s_, col in steps:
            t = T(s_, size=28, color=col)
            chips.add(VGroup(SurroundingRectangle(t, color=col, buff=0.15, corner_radius=0.1, stroke_width=2.5), t))
        chips.arrange(DOWN, buff=0.28).move_to([2.6, 0.3, 0])
        arrows = VGroup(*[Arrow(chips[i].get_bottom(), chips[i + 1].get_top(), buff=0.04, color=C_GREY, stroke_width=3,
                                max_tip_length_to_length_ratio=0.4) for i in range(4)])
        loop = CurvedArrow(chips[-1].get_right() + RIGHT * 0.1, chips[0].get_right() + RIGHT * 0.1, angle=PI * 0.8, color=C_GREEN)
        self.play_bars(LaggedStart(*[FadeIn(c) for c in chips], lag_ratio=0.15), Create(arrows), bars=1)
        self.play_bars(Create(loop), bars=0.5)
        # 127–128 旋钮全随机
        self.at_bar(127)
        self.play_bars(FadeOut(VGroup(tw, belt, bl, chips, arrows, loop)), bars=0.25)
        r = np.random.default_rng(3)
        trs = [ValueTracker(r.uniform(0, 1)) for _ in range(30)]
        knobs = VGroup(*[Knob("·", t, 0, 1, radius=0.22) for t in trs])
        for k in knobs:
            k[-1].set_opacity(0)
        knobs.arrange_in_grid(rows=3, cols=10, buff=0.35).move_to([0, 0.6, 0])
        kl = T("1750 亿个旋钮，一开始全是随机数", size=30, color=C_WHITE).next_to(knobs, DOWN, buff=0.4)
        self.play_bars(FadeIn(knobs), FadeIn(kl), bars=0.5)
        self.play_bars(*[t.animate.set_value(r.uniform(0, 1)) for t in trs], bars=0.75)
        self.at_bar(128.75)
        self.fade_rest(0.25)
        # 129–130 下集
        self.at_bar(129)
        books = VGroup()
        rr = np.random.default_rng(5)
        for i in range(14):
            h = rr.uniform(0.9, 1.5)
            books.add(Rectangle(width=0.32, height=h, stroke_color=C_GOLD, stroke_width=1.5, fill_color=C_GOLD,
                                fill_opacity=rr.uniform(0.15, 0.45)))
        books.arrange(RIGHT, buff=0.04, aligned_edge=DOWN).move_to([-3.2, 0.2, 0])
        shelf = Line(books.get_corner(DL) + LEFT * 0.2, books.get_corner(DR) + RIGHT * 0.2, color=C_GOLD, stroke_width=3)
        nxt = VGroup(T("下集", size=30, color=C_GREY), T("预训练", size=48, color=C_GOLD, weight=BOLD),
                     T("读遍互联网", size=32, color=C_GOLD)).arrange(DOWN, buff=0.22).move_to([3.0, 0.3, 0])
        self.play_bars(LaggedStart(*[GrowFromEdge(b, DOWN) for b in books], lag_ratio=0.05), Create(shelf),
                       FadeIn(nxt, shift=UP * 0.2), bars=1)
        self.at_bar(130.25)
        self.play_bars(*[FadeOut(m) for m in self.visible()], bars=0.75)
