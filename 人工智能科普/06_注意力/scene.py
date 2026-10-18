# -*- coding: utf-8 -*-
"""
第 06 集《注意力：每个词都在看别的词》

时间全部对齐 bars.py 的 BPM 小节网格（140 BPM，204 小节；歌词按 70 BPM 半拍感写）。
字幕由 build.py 烧录。
    ~/.venvs/manim/bin/python ../common/build.py 06_注意力 [--preview]

说明：切分方式、分数、注意力权重、矩阵都是示意数值，不是某个真实模型的输出。
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "common"))
from style import *  # noqa: E402,F401

TOKENS = ["小明", "把", "苹果", "递给", "了", "妹妹", "，", "因为", "她", "饿", "了"]
SHE, MEIMEI, XIAOMING = 8, 5, 0
# “她”对前面各词（含自己）的示意分数（点积）
SCORES = np.array([1.4, -0.6, 0.5, 0.0, -0.8, 3.0, -1.0, -0.2, 0.8])
WEIGHTS = np.exp(SCORES) / np.exp(SCORES).sum()


def token_block(text, color=C_BLUE, size=30, pad=0.14, fill=0.18):
    t = T(text, size=size, color=C_WHITE)
    r = RoundedRectangle(width=max(t.width + 2 * pad, 0.5), height=0.62, corner_radius=0.08,
                         stroke_color=color, stroke_width=2.5, fill_color=color, fill_opacity=fill)
    return VGroup(r, t.move_to(r))


def sentence(y=0.0, size=30, color=C_BLUE, words=TOKENS, buff=0.12):
    return VGroup(*[token_block(w, color=color, size=size) for w in words]).arrange(RIGHT, buff=buff).move_to([0, y, 0])


def val_color(v):
    v = float(np.clip(v, -1, 1))
    if v >= 0:
        return interpolate_color(ManimColor("#1a1f2c"), ManimColor(C_YELLOW), v)
    return interpolate_color(ManimColor("#1a1f2c"), ManimColor(C_BLUE), -v)


def strip(vals, cell=0.3):
    return VGroup(*[Square(side_length=cell, stroke_color="#2a2f3d", stroke_width=1, fill_color=val_color(v), fill_opacity=1)
                    for v in vals]).arrange(RIGHT, buff=0.02)


def arc(a, b, color=C_PURPLE, width=3, opacity=0.9, height=0.5):
    """a、b 为两个 token 方块，从 a 的顶部画到 b 的顶部"""
    p, q = a.get_top() + UP * 0.04, b.get_top() + UP * 0.04
    dist = max(np.linalg.norm(q - p), 1e-3)
    th = PI * 0.55 * min(1.0, 3.0 / dist)            # 远的弧线不拱太高
    ang = th if q[0] < p[0] else -th                  # 两种方向都向上拱
    return ArcBetweenPoints(p, q, angle=ang, stroke_color=color, stroke_width=width, stroke_opacity=opacity)


def attn_matrix(n, seed=3, causal=False, focus=None):
    r = np.random.default_rng(seed)
    M = r.uniform(0, 1, (n, n)) ** 3 + np.eye(n) * 0.6
    if focus:
        for i, j, v in focus:
            M[i, j] = v
    if causal:
        M = np.tril(M)
    M = M / M.sum(axis=1, keepdims=True)
    return M


def matrix_grid(M, cell=0.36, labels=None, color=C_PURPLE, mask=False):
    n = M.shape[0]
    g = VGroup()
    for i in range(n):
        for j in range(n):
            masked = mask and j > i
            sq = Square(side_length=cell, stroke_color="#2a2f3d", stroke_width=1,
                        fill_color=C_GREY if masked else interpolate_color(ManimColor("#151a26"), ManimColor(color),
                                                                           float(min(1.0, M[i, j] * 2.2))),
                        fill_opacity=0.35 if masked else 1)
            sq.move_to([j * cell, -i * cell, 0])
            g.add(sq)
    g.center()
    out = VGroup(g)
    if labels:
        rl = VGroup(*[T(w, size=18, color=C_GREY).next_to(g[i * n], LEFT, buff=0.1) for i, w in enumerate(labels)])
        cl = VGroup(*[T(w, size=14, color=C_GREY).next_to(g[j], UP, buff=0.08) for j, w in enumerate(labels)])
        out.add(rl, cl)
    out.cells = g
    return out


def _rgba(rgb):
    return np.dstack([rgb, np.full(rgb.shape[:2], 255, np.uint8)])


class Video(BeatScene):
    EP_DIR = os.path.dirname(os.path.abspath(__file__))

    def construct(self):
        self.counter = None
        self.intro()          # 1–8
        self.verse1()         # 9–32
        self.hook(33)         # 33–52
        self.verse2()         # 53–76
        self.inst()           # 77–84
        self.hook(85)         # 85–104
        self.verse3()         # 105–128
        self.bridge()         # 129–144
        self.verse4()         # 145–168
        self.hook(169)        # 169–188
        self.outro()          # 189–204
        self.finish()

    # ------------------------------------------------------------ 前奏 1–8
    def intro(self):
        card = title_card("第 06 集", "注意力", "每个词都在看别的词")
        s, e, t, line, st = card
        self.play_bars(FadeIn(s, shift=DOWN * 0.2), FadeIn(e, shift=DOWN * 0.2), bars=1.5)
        self.play_bars(Write(t), bars=2)
        self.play_bars(GrowFromCenter(line), FadeIn(st, shift=UP * 0.2), bars=1.5)
        self.set_counter("6.2 亿", bars=1)
        self.at_bar(8)
        self.play_bars(FadeOut(card), bars=1)

    # ------------------------------------------------------------ 主歌一 9–32
    def verse1(self):
        self.at_bar(9)
        self.tag("回顾：同一个“苹果”")
        fc, tc = np.array([-3.6, 0.2, 0]), np.array([3.6, 0.2, 0])
        fb = VGroup(Ellipse(width=2.8, height=1.5, color=C_GREEN, fill_opacity=0.08).move_to(fc),
                    T("食物", size=26, color=C_GREEN).move_to(fc + DOWN * 1.0))
        tb = VGroup(Ellipse(width=2.8, height=1.5, color=C_PURPLE, fill_opacity=0.08).move_to(tc),
                    T("科技", size=26, color=C_PURPLE).move_to(tc + DOWN * 1.0))
        pt = Dot([0, 0.2, 0], radius=0.13, color=C_RED)
        pl = T("苹果", size=28, color=C_RED).next_to(pt, UP, buff=0.15)
        a1 = Arrow(pt.get_center(), fc + RIGHT * 1.2, buff=0.15, color=C_GREEN, stroke_width=5)
        a2 = Arrow(pt.get_center(), tc + LEFT * 1.2, buff=0.15, color=C_PURPLE, stroke_width=5)
        self.play_bars(FadeIn(fb), FadeIn(tb), FadeIn(pt), FadeIn(pl), bars=1.5)
        self.play_bars(GrowArrow(a1), GrowArrow(a2), bars=1.5)
        self.at_bar(12.5)
        self.fade_rest(0.5)
        # 13–16 例句
        self.at_bar(13)
        self.tag("一个例句")
        sent = sentence(y=0.4)
        self.sent = sent
        self.play_bars(LaggedStart(*[FadeIn(b, shift=UP * 0.2) for b in sent], lag_ratio=0.12), bars=2.5)
        demo = T("（切分为示意）", size=20, color=C_GREY).next_to(sent, DOWN, buff=0.3)
        self.play_bars(FadeIn(demo), bars=0.5)
        # 17–20 “她”是谁
        self.at_bar(17)
        she = sent[SHE]
        q = T("？", size=48, color=C_GOLD).next_to(she, UP, buff=0.25)
        self.play_bars(she[0].animate.set_stroke(C_GOLD, width=4), FadeIn(q, scale=1.5), bars=0.75)
        g1 = arc(she, sent[XIAOMING], color=C_GREY, width=3)
        g2 = arc(she, sent[MEIMEI], color=C_GREY, width=3)
        self.play_bars(Create(g1), bars=0.75)
        self.play_bars(FadeOut(g1), Create(g2), bars=0.75)
        ok = T("人一眼看出：妹妹", size=28, color=C_GREEN).next_to(sent, UP, buff=1.6)
        self.play_bars(g2.animate.set_stroke(C_GREEN, width=5), sent[MEIMEI][0].animate.set_stroke(C_GREEN, width=4),
                       FadeIn(ok), bars=1)
        # 21–24 孤零零的向量
        self.at_bar(21)
        self.play_bars(FadeOut(VGroup(q, g2, ok)), sent[MEIMEI][0].animate.set_stroke(C_BLUE, width=2.5), bars=0.5)
        vec = strip(np.random.default_rng(1).uniform(-1, 1, 18)).move_to([0, -1.2, 0])
        self.play_bars(TransformFromCopy(she, vec), demo.animate.set_opacity(0), bars=1.5)
        vl = T("查表得到的向量：还没看上下文", size=26, color=C_GREY).next_to(vec, DOWN, buff=0.25)
        self.play_bars(FadeIn(vl), bars=1)
        # 25–28 伸出虚线去找
        self.at_bar(25)
        arcs = VGroup(*[arc(she, b, color=C_PURPLE, width=2, opacity=0.6) for i, b in enumerate(sent) if i != SHE])
        self.play_bars(LaggedStart(*[Create(a) for a in arcs], lag_ratio=0.1), bars=2.5)
        fl = T("让“她”自己去找关系", size=28, color=C_PURPLE).next_to(sent, UP, buff=1.7)
        self.play_bars(FadeIn(fl), bars=0.5)
        # 29–32 注意力
        self.at_bar(29)
        self.play_bars(FadeOut(VGroup(arcs, fl, vec, vl)), bars=0.5)
        big = T("注意力", size=96, color=C_PURPLE, weight=BOLD).move_to([0, 2.0, 0])
        glow = big.copy().set_stroke(C_PURPLE, width=10, opacity=0.3)
        self.play_bars(Write(big), FadeIn(glow), bars=2)
        self.at_bar(32)
        self.fade_rest(1)

    # ------------------------------------------------------------ 副歌
    def hook(self, s):
        self.at_bar(s)
        self.tag("每个词都在看别的词")
        sent = sentence(y=-0.2)
        self.play_bars(FadeIn(sent), bars=1)
        r = np.random.default_rng(s)
        allarcs = VGroup()
        for i in range(len(sent)):
            for j in r.choice([k for k in range(len(sent)) if k != i], 2, replace=False):
                allarcs.add(arc(sent[i], sent[j], color=C_PURPLE, width=1.5, opacity=0.35))
        self.play_bars(LaggedStart(*[Create(a) for a in allarcs], lag_ratio=0.03), bars=2.5)
        # ② Query 探照灯、Key 标签、Value 内容盒
        self.at_bar(s + 4)
        she = sent[SHE]
        self.play_bars(FadeOut(allarcs), bars=0.5)
        cone = Polygon(she.get_top(), sent[0].get_top() + UP * 2.3 + LEFT * 0.3, sent[0].get_top() + UP * 0.9 + LEFT * 0.3,
                       stroke_width=0, fill_color=C_PURPLE, fill_opacity=0.16)
        ql = T("Query", size=26, color=C_PURPLE).next_to(she, UP, buff=1.2)
        keys = VGroup(*[RoundedRectangle(width=0.5, height=0.3, corner_radius=0.06, color=C_GOLD, fill_opacity=0.3)
                        .next_to(b, UP, buff=0.12) for i, b in enumerate(sent) if i < SHE])
        kl = T("Key", size=24, color=C_GOLD).next_to(keys, LEFT, buff=0.2)
        vals = VGroup(*[Square(side_length=0.3, color=C_TEAL, fill_opacity=0.35).next_to(b, DOWN, buff=0.15)
                        for i, b in enumerate(sent) if i < SHE])
        vl = T("Value", size=24, color=C_TEAL).next_to(vals, LEFT, buff=0.2)
        self.play_bars(FadeIn(cone), FadeIn(ql), bars=1)
        self.play_bars(LaggedStart(*[FadeIn(k, shift=DOWN * 0.1) for k in keys], lag_ratio=0.08), FadeIn(kl),
                       LaggedStart(*[FadeIn(v, shift=UP * 0.1) for v in vals], lag_ratio=0.08), FadeIn(vl), bars=1.75)
        # ③ 越对得上，连线越粗
        self.at_bar(s + 8)
        self.play_bars(FadeOut(cone), bars=0.5)
        warcs = VGroup(*[arc(she, sent[i], color=C_PURPLE, width=1 + 14 * WEIGHTS[i], opacity=0.35 + 0.65 * WEIGHTS[i] / WEIGHTS.max())
                         for i in range(SHE)])
        self.play_bars(LaggedStart(*[Create(a) for a in warcs], lag_ratio=0.1), bars=2)
        self.play_bars(Indicate(sent[MEIMEI], color=C_PURPLE, scale_factor=1.2), bars=1)
        # ④ 互相看彼此
        self.at_bar(s + 12)
        self.play_bars(FadeOut(VGroup(warcs, keys, vals, kl, vl, ql)), bars=0.5)
        mutual = VGroup()
        for i in range(len(sent)):
            for j in range(len(sent)):
                if i != j and abs(i - j) <= 3:
                    mutual.add(arc(sent[i], sent[j], color=C_PURPLE, width=1.2, opacity=0.4))
        self.play_bars(LaggedStart(*[Create(a) for a in mutual], lag_ratio=0.01), bars=2)
        self.play_bars(mutual.animate.set_stroke(opacity=0.85), bars=1)
        # ⑤ 黑箱
        self.at_bar(s + 16)
        self.fade_rest(0.5)
        box = black_box(w=3.4, h=2.2, depth=0.45).move_to([0, 0.2, 0])
        mini = sentence(y=0, size=14, words=["小明", "苹果", "妹妹", "她"], buff=0.1).move_to(box.front.get_center() + DOWN * 0.35)
        marcs = VGroup(*[arc(mini[i], mini[j], width=2, height=0.3) for i, j in [(3, 2), (3, 0), (1, 0), (2, 1)]])
        self.play_bars(FadeIn(box), bars=0.5)
        self.play_bars(VGroup(box.front, box.q).animate.shift(UP * 0.3).set_opacity(0.12), FadeIn(mini), Create(marcs), bars=1)
        slogan = T("一层一层，把黑箱打开", size=40, color=C_YELLOW, weight=BOLD).to_edge(UP, buff=0.3)
        self.play_bars(Write(slogan), bars=1)
        self.at_bar(s + 19)
        self.fade_rest(1)

    # ------------------------------------------------------------ 主歌二 53–76：Q / K / V
    def verse2(self):
        self.at_bar(53)
        self.tag("Query · Key · Value")
        she = token_block("她", color=C_BLUE, size=34).move_to([-5.6, 0.4, 0])
        x = strip(np.random.default_rng(1).uniform(-1, 1, 8), cell=0.28).next_to(she, RIGHT, buff=0.3)
        mats = VGroup()
        outs = VGroup()
        for k, (nm, col, y) in enumerate([("W_Q", C_PURPLE, 1.7), ("W_K", C_GOLD, 0.4), ("W_V", C_TEAL, -0.9)]):
            m = VGroup(Rectangle(width=1.3, height=0.9, color=C_YELLOW, fill_opacity=0.12),
                       T(nm, size=26, color=C_YELLOW)).move_to([-0.6, y, 0])
            m[1].move_to(m[0])
            o = VGroup(strip(np.random.default_rng(10 + k).uniform(-1, 1, 6), cell=0.28),
                       T(["q（Query）", "k（Key）", "v（Value）"][k], size=24, color=col))
            o.arrange(RIGHT, buff=0.25).move_to([3.4, y, 0])
            mats.add(m)
            outs.add(o)
        arr_in = VGroup(*[Arrow(x.get_right(), m.get_left(), buff=0.1, color=C_GREY, stroke_width=2.5) for m in mats])
        arr_out = VGroup(*[Arrow(m.get_right(), o.get_left(), buff=0.1, color=C_GREY, stroke_width=2.5) for m, o in zip(mats, outs)])
        self.play_bars(FadeIn(she), FadeIn(x), bars=0.75)
        self.play_bars(LaggedStart(*[GrowArrow(a) for a in arr_in], lag_ratio=0.2), FadeIn(mats), bars=1)
        cnote = T("加上 GPT-3 全部注意力层的矩阵：约 580 亿（嵌入表 6.2 亿 + 580 亿）", size=18, color=C_GREY).to_corner(UR, buff=0.4).shift(DOWN * 0.55)
        self.set_counter("586 亿", bars=0.5)
        self.play_bars(FadeIn(cnote), LaggedStart(*[GrowArrow(a) for a in arr_out], lag_ratio=0.2), FadeIn(outs), bars=1.25)
        self.cnote = cnote
        self.qkv = VGroup(she, x, mats, outs, arr_in, arr_out)
        # 57–60 Query：我在找什么
        self.at_bar(57)
        self.play_bars(FadeOut(self.qkv), bars=0.5)
        sent = sentence(y=-0.5)
        self.sent = sent
        she_b = sent[SHE]
        qv = VGroup(strip(np.random.default_rng(10).uniform(-1, 1, 6), cell=0.28), T("q", size=26, color=C_PURPLE)).arrange(RIGHT, buff=0.15)
        qv.move_to(she_b.get_center() + UP * 2.3 + LEFT * 1.0)
        bubble = VGroup(T("我在找：前面提到的、", size=22, color=C_PURPLE), T("会“饿”的那个人？", size=22, color=C_PURPLE)).arrange(DOWN, buff=0.06)
        bub = VGroup(SurroundingRectangle(bubble, color=C_PURPLE, buff=0.15, corner_radius=0.12), bubble).next_to(qv, RIGHT, buff=0.3)
        self.play_bars(FadeIn(sent), bars=0.75)
        self.play_bars(FadeIn(qv), she_b[0].animate.set_stroke(C_PURPLE, width=4), bars=0.75)
        self.play_bars(FadeIn(bub, shift=LEFT * 0.2), bars=1)
        # 61–64 Key：标签
        self.at_bar(61)
        tags = {0: "男孩·人", 2: "水果", 3: "动作", 5: "女孩·人", 7: "原因"}
        keys = VGroup()
        for i in range(SHE):
            txt = tags.get(i, "")
            k = RoundedRectangle(width=max(0.55, len(txt) * 0.22 + 0.2), height=0.36, corner_radius=0.07, color=C_GOLD, fill_opacity=0.25)
            k.next_to(sent[i], UP, buff=0.18)
            if txt:
                k = VGroup(k, T(txt, size=16, color=C_GOLD).move_to(k))
            keys.add(k)
        kl = T("k：我有什么", size=24, color=C_GOLD).move_to([-5.0, 1.7, 0])
        self.play_bars(LaggedStart(*[FadeIn(k, shift=DOWN * 0.1) for k in keys], lag_ratio=0.1), FadeIn(kl),
                       FadeOut(self.cnote), bars=2.5)
        # 65–68 Value：内容盒
        self.at_bar(65)
        vals = VGroup(*[VGroup(Square(side_length=0.34, color=C_TEAL, fill_opacity=0.35)).next_to(sent[i], DOWN, buff=0.18)
                        for i in range(SHE)])
        vlab = T("v：被看中时，要递过去的内容", size=24, color=C_TEAL).move_to([0, -1.75, 0])
        self.play_bars(LaggedStart(*[FadeIn(v, shift=UP * 0.1) for v in vals], lag_ratio=0.1), FadeIn(vlab), bars=2.5)
        # 69–72 点积打分
        self.at_bar(69)
        self.play_bars(FadeOut(bub), bars=0.5)
        dots = VGroup(*[Line(qv[0].get_bottom(), keys[i].get_top(), color=C_PURPLE, stroke_width=1.5, stroke_opacity=0.6)
                        for i in range(SHE)])
        scores = VGroup(*[T(f"{SCORES[i]:+.1f}".replace("-", "−"), size=22, color=C_WHITE).next_to(keys[i], UP, buff=0.1)
                          for i in range(SHE)])
        dl = T("q · k（点积）：对得上就分高", size=24, color=C_PURPLE).move_to([3.6, 2.6, 0])
        self.play_bars(LaggedStart(*[Create(d) for d in dots], lag_ratio=0.08), FadeIn(dl), bars=1.5)
        self.play_bars(FadeOut(dots), LaggedStart(*[FadeIn(sc, shift=UP * 0.1) for sc in scores], lag_ratio=0.08), bars=1.5)
        # 73–76 妹妹最高；比喻说明
        self.at_bar(73)
        hl = SurroundingRectangle(VGroup(scores[MEIMEI], keys[MEIMEI], sent[MEIMEI]), color=C_GREEN, buff=0.08)
        self.play_bars(Create(hl), scores[MEIMEI].animate.set_color(C_GREEN).scale(1.3), bars=1)
        note = VGroup(T("“提问 / 标签 / 内容”只是比喻：", size=22, color=C_GREY),
                      T("q、k、v 都是向量乘上学出来的矩阵（线性变换），具体含义不由人规定", size=20, color=C_GREY)).arrange(DOWN, buff=0.08)
        note.move_to([0, -2.35, 0])
        self.play_bars(FadeOut(vlab), FadeIn(note), bars=1)
        self.at_bar(76)
        self.fade_rest(1)

    # ------------------------------------------------------------ 间奏 77–84：注意力矩阵
    def inst(self):
        self.at_bar(77)
        self.tag("注意力矩阵")
        M = attn_matrix(len(TOKENS), seed=5, focus=[(SHE, MEIMEI, 3.0), (2, 3, 1.5), (3, 0, 1.2)])
        mg = matrix_grid(M, cell=0.42, labels=TOKENS).move_to([-1.9, 0.15, 0])
        cells = mg.cells
        n = len(TOKENS)
        for sq in cells:
            sq.save_state()
            sq.set_fill(opacity=0)
        self.add(mg)
        rl = T("行：谁在看", size=24, color=C_GREY).next_to(mg, LEFT, buff=0.2).shift(UP * 2.4)
        cl = T("列：被看的词", size=24, color=C_GREY).move_to([2.2, 2.7, 0])
        self.play_bars(FadeIn(rl), FadeIn(cl), bars=0.5)
        for i in range(n):
            self.play_bars(*[cells[i * n + j].animate.restore() for j in range(n)], bars=5.0 / n)
        formula = VGroup(T("公式彩蛋", size=20, color=C_GREY),
                         T("Attention(Q, K, V) = softmax(QKᵀ / √d) · V", size=20, color=C_PURPLE)).arrange(DOWN, buff=0.1)
        formula.move_to([4.0, -1.9, 0])
        if formula.get_right()[0] > 6.8:
            formula.shift(LEFT * (formula.get_right()[0] - 6.8))
        self.play_bars(FadeIn(formula), bars=1)
        self.at_bar(84)
        self.fade_rest(1)

    # ------------------------------------------------------------ 主歌三 105–128：softmax、加权、掩码
    def verse3(self):
        self.at_bar(105)
        self.tag("softmax：分数 → 比例")
        labels = TOKENS[:SHE + 1]
        ax_y0 = -0.6
        xs = np.linspace(-4.8, 3.2, len(labels))
        bars_ = VGroup()
        for x, sc in zip(xs, SCORES):
            h = sc * 0.55
            r = Rectangle(width=0.55, height=max(abs(h), 0.02), stroke_width=0, fill_color=C_PURPLE if sc >= 0 else C_GREY,
                          fill_opacity=0.85)
            r.move_to([x, ax_y0 + h / 2, 0])
            bars_.add(r)
        base = Line([-5.4, ax_y0, 0], [3.8, ax_y0, 0], color=C_GREY, stroke_width=2)
        labs = VGroup(*[T(w, size=22, color=C_WHITE).move_to([x, ax_y0 - 0.95, 0]) for x, w in zip(xs, labels)])
        nums = VGroup(*[T(f"{sc:+.1f}".replace("-", "−"), size=20, color=C_GREY).next_to(b, UP if sc >= 0 else DOWN, buff=0.06)
                        for b, sc in zip(bars_, SCORES)])
        title = T("分数（点积）", size=26, color=C_PURPLE).move_to([0, 2.6, 0])
        self.play_bars(Create(base), FadeIn(labs), LaggedStart(*[GrowFromEdge(b, DOWN) for b in bars_], lag_ratio=0.08),
                       FadeIn(nums), FadeIn(title), bars=1.5)
        new_bars = VGroup()
        for x, w in zip(xs, WEIGHTS):
            h = w * 4.2
            new_bars.add(Rectangle(width=0.55, height=max(h, 0.02), stroke_width=0, fill_color=C_PURPLE, fill_opacity=0.9)
                         .move_to([x, ax_y0 + h / 2, 0]))
        new_nums = VGroup(*[T(f"{w:.2f}", size=20, color=C_WHITE).next_to(b, UP, buff=0.06) for b, w in zip(new_bars, WEIGHTS)])
        title2 = T("softmax 之后：都是正数，加起来 = 1", size=24, color=C_PURPLE).move_to([0, 2.6, 0])
        self.play_bars(Transform(bars_, new_bars), Transform(nums, new_nums), Transform(title, title2), bars=1.75)
        self.bars_, self.nums, self.xs, self.labs, self.base = bars_, nums, xs, labs, base
        # 109–112 注意力权重
        self.at_bar(109)
        w_l = T("注意力权重", size=34, color=C_PURPLE, weight=BOLD).move_to([4.6, 2.2, 0])
        mm = SurroundingRectangle(VGroup(bars_[MEIMEI], nums[MEIMEI]), color=C_GREEN, buff=0.08)
        bigger = T("大的更大，小的更小", size=24, color=C_WHITE).move_to([4.6, 0.6, 0])
        self.play_bars(FadeIn(w_l), Create(mm), bars=1)
        self.play_bars(FadeIn(bigger), bars=1)
        # 113–116 加权求和
        self.at_bar(113)
        self.tag("按比例把 Value 加起来")
        self.play_bars(FadeOut(VGroup(mm, bigger, title, w_l)), bars=0.5)
        vboxes = VGroup(*[Square(side_length=0.42, color=C_TEAL, fill_opacity=0.4).move_to([x, -2.35, 0]) for x in self.xs])
        self.play_bars(FadeIn(vboxes), bars=0.5)
        sigma = VGroup(Circle(radius=0.42, color=C_TEAL), T("Σ", size=38, color=C_TEAL)).move_to([5.4, -1.0, 0])
        moving = VGroup(*[vb.copy().scale(0.3 + 2.2 * w) for vb, w in zip(vboxes, WEIGHTS)])
        self.play_bars(FadeIn(sigma), *[m.animate.move_to(sigma).set_opacity(0.0) for m in moving], bars=1.5)
        self.remove(moving)
        # 117–120 加到“她”身上
        self.at_bar(117)
        self.play_bars(FadeOut(VGroup(self.bars_, self.nums, self.labs, self.base, vboxes)), sigma.animate.move_to([-3.0, 0.6, 0]), bars=0.5)
        rng = np.random.default_rng(2)
        she_v = rng.uniform(-1, 1, 14)
        mei_v = rng.uniform(-1, 1, 14)
        s_old = strip(she_v, cell=0.36).move_to([1.5, 1.4, 0])
        s_lab = T("“她”原来的向量", size=24, color=C_WHITE).next_to(s_old, UP, buff=0.15)
        upd = strip(mei_v * 0.8, cell=0.36).move_to([1.5, 0.6, 0])
        u_lab = T("+ 注意力带来的更新（主要来自“妹妹”）", size=22, color=C_TEAL).next_to(upd, RIGHT, buff=0.2)
        if u_lab.get_right()[0] > 6.9:
            u_lab.next_to(upd, DOWN, buff=0.12)
        self.play_bars(FadeIn(s_old), FadeIn(s_lab), TransformFromCopy(sigma, upd), FadeIn(u_lab), bars=1.25)
        s_new = strip(np.clip(0.5 * she_v + 0.8 * mei_v, -1, 1), cell=0.36).move_to([1.5, -0.6, 0])
        n_lab = T("= 更新后的“她”：带上了“妹妹”的信息", size=24, color=C_GREEN).next_to(s_new, DOWN, buff=0.2)
        self.play_bars(TransformFromCopy(VGroup(s_old, upd), s_new), FadeIn(n_lab), bars=1.25)
        self.at_bar(120.5)
        self.fade_rest(0.5)
        # 121–124 因果掩码
        self.at_bar(121)
        self.tag("只能看前面：掩码")
        M = attn_matrix(len(TOKENS), seed=5, causal=True, focus=[(SHE, MEIMEI, 3.0), (2, 0, 1.2), (3, 2, 1.0)])
        mg = matrix_grid(M, cell=0.42, labels=TOKENS, mask=True).move_to([-2.0, 0.1, 0])
        n = len(TOKENS)
        upper = VGroup(*[mg.cells[i * n + j] for i in range(n) for j in range(n) if j > i])
        lower = VGroup(*[mg.cells[i * n + j] for i in range(n) for j in range(n) if j <= i])
        for sq in upper:
            sq.save_state()
            sq.set_fill(C_PURPLE, opacity=0.6)
        self.play_bars(FadeIn(mg), bars=1)
        ml = VGroup(T("像 GPT 这样生成文字的模型：", size=24, color=C_WHITE),
                    T("每个词只能看自己和前面的词", size=24, color=C_WHITE)).arrange(DOWN, buff=0.1, aligned_edge=LEFT)
        ml.move_to([4.3, 1.2, 0])
        self.play_bars(*[sq.animate.restore() for sq in upper], FadeIn(ml), bars=1.5)
        gl = T("灰色 = 不许看（未来）", size=22, color=C_GREY).next_to(ml, DOWN, buff=0.35).align_to(ml, LEFT)
        self.play_bars(FadeIn(gl), bars=0.5)
        # 125–128 一个个写出来
        self.at_bar(125)
        self.play_bars(FadeOut(mg), FadeOut(ml), FadeOut(gl), bars=0.5)
        row = sentence(y=-0.2, words=TOKENS)
        hidden = VGroup(*[RoundedRectangle(width=b.width, height=b.height, corner_radius=0.08, stroke_color=C_GREY, stroke_width=2,
                                           fill_color=C_GREY, fill_opacity=0.15).move_to(b) for b in row])
        self.play_bars(FadeIn(hidden), bars=0.25)
        per = 1.75 / len(row)
        for i, b in enumerate(row):
            anims = [ReplacementTransform(hidden[i], b)]
            if i > 0:
                anims += [Create(arc(b, row[j], width=1.5, opacity=0.6)) for j in range(max(0, i - 2), i)]
            self.play_bars(*anims, bars=per)
        bert = T("（BERT 等编码器模型可以前后都看）", size=22, color=C_GREY).move_to([0, -1.6, 0])
        self.play_bars(FadeIn(bert), bars=0.5)
        self.at_bar(128)
        self.fade_rest(1)

    # ------------------------------------------------------------ 桥段 129–144
    def bridge(self):
        self.at_bar(129)
        self.tag("意思是看出来的")
        she = token_block("她", color=C_BLUE, size=60).move_to([0, 0.4, 0])
        spot = Circle(radius=1.4, stroke_width=0, fill_color=C_WHITE, fill_opacity=0.06).move_to(she)
        self.play_bars(FadeIn(spot), FadeIn(she, scale=0.8), bars=2)
        lonely = T("只靠自己：不知道指谁", size=28, color=C_GREY).next_to(she, DOWN, buff=0.7)
        self.play_bars(FadeIn(lonely), bars=2)
        self.at_bar(136.5)
        self.play_bars(FadeOut(VGroup(spot, lonely)), she.animate.scale(0.6).move_to([-1.0, 1.9, 0]), bars=0.5)
        # 137–144 看了谁：她 → 妹妹；苹果 → 手机
        self.at_bar(137)
        mei = token_block("妹妹", color=C_BLUE, size=36).move_to([-4.0, 1.9, 0])
        a = arc(she, mei, color=C_PURPLE, width=5)
        self.play_bars(FadeIn(mei), Create(a), she[0].animate.set_fill(C_GREEN, 0.4), bars=1.5)
        s2 = sentence(y=-0.2, size=30, words=["新", "苹果", "手机", "发布", "了"], color=C_BLUE)
        s2.move_to([3.2, 1.9, 0])
        a2 = arc(s2[1], s2[2], color=C_PURPLE, width=4)
        self.play_bars(FadeIn(s2), Create(a2), bars=1.25)
        fc, tc = np.array([-2.8, -1.1, 0]), np.array([2.8, -1.1, 0])
        fb = VGroup(Ellipse(width=2.6, height=1.2, color=C_GREEN, fill_opacity=0.08).move_to(fc),
                    T("食物", size=24, color=C_GREEN).move_to(fc + DOWN * 0.85))
        tb = VGroup(Ellipse(width=2.6, height=1.2, color=C_PURPLE, fill_opacity=0.08).move_to(tc),
                    T("科技", size=24, color=C_PURPLE).move_to(tc + DOWN * 0.85))
        pt = Dot(fc + RIGHT * 0.3, radius=0.13, color=C_RED)
        pl = T("苹果", size=24, color=C_RED)
        pl.add_updater(lambda m: m.next_to(pt, UP, buff=0.1))
        self.play_bars(FadeIn(fb), FadeIn(tb), FadeIn(pt), FadeIn(pl), bars=1)
        push = Arrow(fc + RIGHT * 0.8, tc + LEFT * 0.6, buff=0, color=C_TEAL, stroke_width=4)
        pv = T("“手机”传来的 Value", size=22, color=C_TEAL).next_to(push, UP, buff=0.1)
        self.play_bars(GrowArrow(push), FadeIn(pv), bars=1)
        self.play_bars(pt.animate.move_to(tc + LEFT * 0.2), bars=2.25)
        pl.clear_updaters()
        self.at_bar(144.25)
        self.fade_rest(0.75)

    # ------------------------------------------------------------ 主歌四 145–168
    def verse4(self):
        self.at_bar(145)
        self.tag("多头注意力")
        sent = sentence(y=-1.0)
        self.play_bars(FadeIn(sent), bars=0.75)
        heads = [
            (C_PURPLE, [(SHE, MEIMEI), (SHE, XIAOMING)]),
            (C_TEAL, [(3, 0), (3, 2), (3, 5)]),
            (C_ORANGE, [(i, i - 1) for i in range(1, len(TOKENS))]),
        ]
        hg = VGroup()
        for col, pairs in heads:
            hg.add(VGroup(*[arc(sent[i], sent[j], color=col, width=3, opacity=0.85) for i, j in pairs]))
        self.play_bars(LaggedStart(*[Create(h) for h in hg], lag_ratio=0.35), bars=2.75)
        # 149–152 标签
        self.at_bar(149)
        hl = VGroup(T("头 A：像在追代词（她 → 妹妹）", size=24, color=C_PURPLE),
                    T("头 B：像在找“谁做了什么”（递给 → 小明、苹果、妹妹）", size=24, color=C_TEAL),
                    T("头 C：总看前一个词", size=24, color=C_ORANGE)).arrange(DOWN, aligned_edge=LEFT, buff=0.18)
        hl.move_to([0, 2.3, 0])
        self.play_bars(LaggedStart(*[FadeIn(x, shift=RIGHT * 0.2) for x in hl], lag_ratio=0.3), bars=2.5)
        # 153–156 很多头看不出规律
        self.at_bar(153)
        self.fade_rest(0.5)
        r = np.random.default_rng(7)
        wall = Group()
        for k in range(24):
            n = 10
            if k % 6 == 0:
                A = np.eye(n) * 0.9
            elif k % 6 == 3:
                A = np.eye(n, k=-1) * 0.9
            else:
                A = r.uniform(0, 1, (n, n)) ** 2
            A = np.tril(A) + 0.02
            A = A / A.max()
            rgb = (np.stack([0x15 + (0x9A - 0x15) * A, 0x1a + (0x72 - 0x1a) * A, 0x26 + (0xAC - 0x26) * A], -1)).astype(np.uint8)
            im = ImageMobject(_rgba(rgb))
            im.set_resampling_algorithm(RESAMPLING_ALGORITHMS["nearest"])
            im.scale_to_fit_height(1.05)
            wall.add(im)
        wall.arrange_in_grid(rows=3, cols=8, buff=0.18).move_to([0, 0.5, 0])
        self.play_bars(LaggedStart(*[FadeIn(w) for w in wall], lag_ratio=0.04), bars=1.5)
        wl = T("研究观察：有的头有清楚的模式，很多头看不出规律", size=26, color=C_GREY).next_to(wall, DOWN, buff=0.35)
        self.play_bars(FadeIn(wl), bars=1)
        # 157–160 GPT-3：96 × 96
        self.at_bar(157)
        self.fade_rest(0.5)
        rr = np.random.default_rng(9)
        G = rr.uniform(0.2, 1.0, (96, 96))
        rgb = (np.stack([0x15 + (0x9A - 0x15) * G, 0x1a + (0x72 - 0x1a) * G, 0x26 + (0xAC - 0x26) * G], -1)).astype(np.uint8)
        rgb = np.kron(rgb, np.ones((4, 4, 1), np.uint8))
        rgb[::4, :, :] = 11
        rgb[:, ::4, :] = 11
        grid = ImageMobject(_rgba(rgb))
        grid.set_resampling_algorithm(RESAMPLING_ALGORITHMS["nearest"])
        grid.scale_to_fit_height(4.2).move_to([-2.0, 0.25, 0])
        gt = VGroup(T("GPT-3", size=34, color=C_YELLOW, weight=BOLD), T("每层 96 个头", size=28, color=C_WHITE),
                    T("× 96 层", size=28, color=C_WHITE), T("= 9,216 个注意力头", size=30, color=C_PURPLE)).arrange(DOWN, buff=0.2, aligned_edge=LEFT)
        gt.move_to([3.6, 0.4, 0])
        self.play_bars(FadeIn(grid), bars=1)
        self.play_bars(LaggedStart(*[FadeIn(x, shift=LEFT * 0.2) for x in gt], lag_ratio=0.25), bars=1.5)
        # 161–164 2014
        self.at_bar(161)
        self.fade_rest(0.5)
        self.tag("历史")
        line = Line([-6, 0.2, 0], [6, 0.2, 0], color=C_GREY, stroke_width=3)
        def ev(yr, t1, t2, col, x):
            tick = Line([x, 0.05, 0], [x, 0.35, 0], color=col, stroke_width=4)
            y_ = T(str(yr), size=32, color=col, weight=BOLD).next_to(tick, UP, buff=0.12)
            a = T(t1, size=24, color=col).next_to(tick, DOWN, buff=0.2)
            b = T(t2, size=20, color=C_GREY).next_to(a, DOWN, buff=0.1)
            return VGroup(tick, y_, a, b)
        e1 = ev(2014, "Bahdanau 等", "注意力用于机器翻译（配合循环网络）", C_WHITE, -3.2)
        self.play_bars(Create(line), FadeIn(e1), bars=1.5)
        self.play_bars(Indicate(e1[1], color=C_PURPLE), bars=1)
        # 165–168 2017
        self.at_bar(165)
        e2 = ev(2017, "Vaswani 等《Attention Is All You Need》", "完全用注意力替代循环结构 → Transformer", C_PURPLE, 2.6)
        self.play_bars(FadeIn(e2, shift=UP * 0.2), bars=1.25)
        fm = VGroup(T("公式彩蛋", size=20, color=C_GREY),
                    T("Attention(Q, K, V) = softmax(QKᵀ / √d) · V", size=26, color=C_PURPLE)).arrange(DOWN, buff=0.1).move_to([0, 2.4, 0])
        self.play_bars(FadeIn(fm), bars=1.25)
        self.at_bar(168)
        self.fade_rest(1)

    # ------------------------------------------------------------ 尾声 189–204（含本集要点）
    def outro(self):
        self.at_bar(189)
        self.tag("本集要点")
        steps = [("Query 提问", C_PURPLE), ("和 Key 比对打分", C_GOLD), ("softmax 变比例", C_PURPLE),
                 ("Value 加权求和", C_TEAL), ("更新自己", C_GREEN)]
        chips = VGroup()
        for s_, col in steps:
            t = T(s_, size=28, color=col)
            chips.add(VGroup(SurroundingRectangle(t, color=col, buff=0.18, corner_radius=0.12, stroke_width=2.5), t))
        chips.arrange(RIGHT, buff=0.45)
        if chips.width > 13.2:
            chips.scale_to_fit_width(13.2)
        chips.move_to([0, 1.0, 0])
        arrows = VGroup(*[Arrow(chips[i].get_right(), chips[i + 1].get_left(), buff=0.05, color=C_GREY, stroke_width=3,
                                max_tip_length_to_length_ratio=0.4) for i in range(4)])
        self.play_bars(FadeIn(chips[0]), bars=0.75)
        self.play_bars(GrowArrow(arrows[0]), FadeIn(chips[1]), bars=1.25)
        # 193–196
        self.at_bar(193)
        for i in (2, 3, 4):
            self.play_bars(GrowArrow(arrows[i - 1]), FadeIn(chips[i]), bars=0.9)
        extra = VGroup(T("生成文字的模型：只能看前面（掩码）", size=24, color=C_GREY),
                       T("多头并行：各找各的关系", size=24, color=C_GREY)).arrange(DOWN, buff=0.12).next_to(chips, DOWN, buff=0.5)
        self.play_bars(FadeIn(extra), bars=0.5)
        # 197–200 零件 → 机器
        self.at_bar(197)
        self.play_bars(FadeOut(VGroup(chips, arrows, extra)), bars=0.5)
        part = VGroup(RoundedRectangle(width=2.6, height=0.8, corner_radius=0.12, color=C_PURPLE, fill_opacity=0.3),
                      T("注意力", size=30, color=C_PURPLE)).move_to([-4.5, 0.4, 0])
        part[1].move_to(part[0])
        tower = VGroup(*[RoundedRectangle(width=3.0, height=0.7, corner_radius=0.1, color=C_GREY, stroke_width=2,
                                          fill_opacity=0).move_to([2.0, -1.6 + 0.85 * k, 0]) for k in range(5)])
        tl = T("？", size=40, color=C_GREY).next_to(tower, RIGHT, buff=0.3)
        self.play_bars(FadeIn(part), Create(tower), FadeIn(tl), bars=1)
        self.play_bars(part.animate.scale(1.12).move_to(tower[2]), bars=1.25)
        # 201–204 下集
        self.at_bar(201)
        nxt = VGroup(T("下集", size=28, color=C_GREY), T("Transformer", size=48, color=C_GOLD, weight=BOLD),
                     T("一次只猜下一个词", size=30, color=C_GOLD)).arrange(DOWN, buff=0.2).move_to([-3.6, 0.3, 0])
        self.play_bars(FadeOut(tl), FadeIn(nxt, shift=UP * 0.2), *[t.animate.set_stroke(C_GOLD) for t in tower], bars=1.5)
        self.at_bar(203.75)
        self.play_bars(*[FadeOut(m) for m in self.visible()], bars=1.25)
