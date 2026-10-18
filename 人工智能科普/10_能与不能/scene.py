# -*- coding: utf-8 -*-
"""
第 10 集《能与不能：幻觉、工具与看不透的黑箱》

时间全部对齐 bars.py 的 BPM 小节网格（84 BPM，126 小节）。字幕由 build.py 烧录。
    ~/.venvs/manim/bin/python ../common/build.py 10_能与不能 [--preview]

说明：参考文献卡、镇长问答、手机诗、工具卡格式、特征墙上的问答都是虚构 / 示意；
金门大桥特征出自 Anthropic《Scaling Monosemanticity》（2024）及其演示。
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "common"))
from style import *  # noqa: E402,F401

C_ATT, C_MLP = C_PURPLE, C_TEAL
C_TOOL = C_ORANGE
PROMPT = ["床", "前", "明月", "光", "，", "疑", "是", "地", "上"]
EPS = ["机器怎么学", "神经网络", "梯度下降", "反向传播", "词向量", "注意力", "Transformer", "预训练", "后训练", "能与不能"]


def block(w=2.4, h=0.5):
    att = RoundedRectangle(width=w, height=h / 2 - 0.03, corner_radius=0.06, color=C_ATT, fill_opacity=0.28, stroke_width=2)
    mlp = RoundedRectangle(width=w, height=h / 2 - 0.03, corner_radius=0.06, color=C_MLP, fill_opacity=0.28, stroke_width=2)
    mlp.next_to(att, UP, buff=0.04)
    return VGroup(att, mlp)


def tower(n, w=2.4, h=0.5, gap=0.05):
    return VGroup(*[block(w, h) for _ in range(n)]).arrange(UP, buff=gap)


def card(lines, color=C_WHITE, width=4.6, size=24, title=None, tcolor=C_GOLD):
    txt = VGroup(*[T(l, size=size, color=color) for l in lines]).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
    items = [txt]
    if title:
        tt = T(title, size=size, color=tcolor, weight=BOLD)
        items = [tt, txt]
    body = VGroup(*items).arrange(DOWN, aligned_edge=LEFT, buff=0.18)
    bg = RoundedRectangle(width=max(width, body.width + 0.5), height=body.height + 0.45, corner_radius=0.15,
                          stroke_color=tcolor if title else C_GREY, stroke_width=2.5, fill_color="#121621", fill_opacity=1)
    body.move_to(bg)
    return VGroup(bg, body)


def bubble(text, color=C_BLUE, size=26):
    t = T(text, size=size, color=C_WHITE)
    r = RoundedRectangle(width=t.width + 0.5, height=t.height + 0.35, corner_radius=0.2, stroke_color=color,
                         stroke_width=2.5, fill_color=color, fill_opacity=0.2)
    return VGroup(r, t.move_to(r))


def token_block(text, color=C_BLUE, size=22, pad=0.1, fill=0.18, h=0.48):
    t = T(text, size=size, color=C_WHITE)
    r = RoundedRectangle(width=max(t.width + 2 * pad, 0.4), height=h, corner_radius=0.06,
                         stroke_color=color, stroke_width=2, fill_color=color, fill_opacity=fill)
    return VGroup(r, t.move_to(r))


def sentence(words, size=22, color=C_BLUE, buff=0.06, h=0.48):
    return VGroup(*[token_block(w, color=color, size=size, h=h) for w in words]).arrange(RIGHT, buff=buff)


def knob_grid(n_rows=3, n_cols=8, seed=2, radius=0.22):
    r = np.random.default_rng(seed)
    trs = [ValueTracker(r.uniform(0.2, 0.8)) for _ in range(n_rows * n_cols)]
    ks = VGroup(*[Knob("·", t, 0, 1, radius=radius) for t in trs])
    for k in ks:
        k[-1].set_opacity(0)
    ks.arrange_in_grid(rows=n_rows, cols=n_cols, buff=0.32)
    return ks, trs


def lock_icon(color=C_YELLOW, s=1.0):
    body = RoundedRectangle(width=0.8, height=0.62, corner_radius=0.08, color=color, fill_color=color, fill_opacity=0.25, stroke_width=3)
    shackle = Arc(radius=0.26, start_angle=0, angle=PI, color=color, stroke_width=5).next_to(body, UP, buff=-0.02)
    hole = Dot(body.get_center(), radius=0.06, color=color)
    return VGroup(shackle, body, hole).scale(s)


def magnifier(color=C_WHITE):
    ring = Circle(radius=0.38, color=color, stroke_width=5, fill_color=C_BLUE, fill_opacity=0.08)
    handle = Line(ring.point_at_angle(-PI / 4), ring.point_at_angle(-PI / 4) + np.array([0.42, -0.42, 0]), color=color, stroke_width=8)
    return VGroup(ring, handle)


def calculator():
    body = RoundedRectangle(width=1.7, height=2.2, corner_radius=0.15, color=C_GREY, fill_color="#121621", fill_opacity=1, stroke_width=3)
    disp = Rectangle(width=1.4, height=0.48, color=C_GREEN, stroke_width=2, fill_color=C_GREEN, fill_opacity=0.1)
    disp.move_to(body.get_top() + DOWN * 0.42)
    keys = VGroup(*[RoundedRectangle(width=0.26, height=0.22, corner_radius=0.04, color=C_GREY, stroke_width=1.5) for _ in range(12)])
    keys.arrange_in_grid(rows=4, cols=3, buff=(0.14, 0.1)).next_to(disp, DOWN, buff=0.18)
    g = VGroup(body, disp, keys)
    g.disp = disp
    return g


def search_icon():
    box = RoundedRectangle(width=2.0, height=0.5, corner_radius=0.25, color=C_GREY, stroke_width=2.5)
    m = magnifier(C_GREY).scale(0.35).move_to(box.get_right() + LEFT * 0.3)
    return VGroup(box, m)


def tool_card(text, size=24, color=C_TOOL):
    t = T(text, size=size, color=C_WHITE)
    r = RoundedRectangle(width=t.width + 0.4, height=t.height + 0.3, corner_radius=0.1, stroke_color=color, stroke_width=3,
                         fill_color=color, fill_opacity=0.22)
    return VGroup(r, t.move_to(r))


def shatter(mob, n=16, m=7, color=C_RED, seed=0):
    """把一个矩形区域碎成 n×m 个像素块"""
    w, h = mob.width / n, mob.height / m
    ul = mob.get_corner(UL)
    r = np.random.default_rng(seed)
    sq = VGroup(*[Square(side_length=min(w, h) * 0.9, stroke_width=0, fill_color=color, fill_opacity=r.uniform(0.25, 0.7))
                  .move_to(ul + np.array([w * (i + 0.5), -h * (j + 0.5), 0])) for i in range(n) for j in range(m)])
    return sq


def bridge(w=4.4, color="#C0362C"):
    """简笔几何的悬索桥（示意，不用照片）"""
    deck = Line([-w / 2, 0, 0], [w / 2, 0, 0], color=color, stroke_width=6)
    tx = w * 0.25
    towers = VGroup(*[Rectangle(width=0.16, height=1.7, stroke_width=0, fill_color=color, fill_opacity=1).move_to([x, 0.55, 0]) for x in (-tx, tx)])
    top = 1.35
    main = ParametricFunction(lambda t: np.array([t, 0.15 + (top - 0.15) * (t / tx) ** 2, 0]), t_range=[-tx, tx], color=color, stroke_width=3)
    sides = VGroup(Line([-tx, top, 0], [-w / 2, 0.15, 0], color=color, stroke_width=3),
                   Line([tx, top, 0], [w / 2, 0.15, 0], color=color, stroke_width=3))
    hangers = VGroup(*[Line([x, 0, 0], [x, 0.15 + (top - 0.15) * (x / tx) ** 2, 0], color=color, stroke_width=1.5)
                       for x in np.linspace(-tx * 0.85, tx * 0.85, 9)])
    water = VGroup(*[Line([-w / 2 + 0.3 * k, -0.35 - 0.12 * (k % 2), 0], [-w / 2 + 0.3 * k + 0.2, -0.35 - 0.12 * (k % 2), 0], color=C_BLUE, stroke_width=2, stroke_opacity=0.5)
                     for k in range(int(w / 0.3))])
    return VGroup(water, hangers, main, sides, towers, deck)


# ---------------------------------------------------------------- 尾声：十集回顾的小画面（中心在原点，约 4.6×2.3）
def mini_net(cols=(3, 4, 4, 2), color=C_BLUE):
    xs = np.linspace(-1.5, 1.5, len(cols))
    layers = VGroup(*[VGroup(*[Circle(radius=0.12, color=color, stroke_width=2, fill_color=color, fill_opacity=0.1)
                               .move_to([x, (n - 1) / 2 * 0.45 - i * 0.45, 0]) for i in range(n)]) for x, n in zip(xs, cols)])
    edges = VGroup(*[Line(a.get_center(), b.get_center(), stroke_width=1, color=C_GREY, stroke_opacity=0.5)
                     for c1, c2 in zip(layers[:-1], layers[1:]) for a in c1 for b in c2])
    return VGroup(edges, layers)


def recap_minis():
    out = []
    # 01 散点与直线
    r = np.random.default_rng(3)
    xs = np.linspace(-1.8, 1.8, 12)
    dots = VGroup(*[Dot([x, 0.42 * x - 0.1 + r.normal(0, 0.18), 0], radius=0.06, color=C_BLUE) for x in xs])
    piv = np.array([0, -0.1, 0])
    ln = Line(piv + np.array([-2.1, 0.63, 0]), piv + np.array([2.1, -0.63, 0]), color=C_YELLOW, stroke_width=4)
    ang = np.arctan(0.42) - np.arctan(-0.3)
    out.append((VGroup(dots, ln), lambda g=ln: Rotate(g, ang)))
    # 02 网络灯阵
    n2 = mini_net()
    out.append((n2, lambda g=n2: LaggedStart(*[c.animate.set_fill(C_YELLOW, 0.8) for c in g[1]], lag_ratio=0.45)))
    # 03 下山小球
    f = lambda x: 0.32 * x ** 2 - 0.9
    curve = ParametricFunction(lambda t: np.array([t, f(t), 0]), t_range=[-2.0, 2.0], color=C_RED, stroke_width=4)
    ball = Dot([-1.8, f(-1.8) + 0.12, 0], radius=0.12, color=C_GREEN)
    path = ParametricFunction(lambda t: np.array([t, f(t) + 0.12, 0]), t_range=[-1.8, 0.0], stroke_opacity=0)
    out.append((VGroup(curve, path, ball), lambda b=ball, p=path: MoveAlongPath(b, p, rate_func=rush_into)))
    # 04 红色反向流
    n4 = mini_net(color=C_GREY)
    arrs = VGroup(*[Arrow([x + 1.0, -1.15, 0], [x, -1.15, 0], buff=0.05, color=C_RED, stroke_width=4, max_tip_length_to_length_ratio=0.3)
                    for x in (0.5, -0.5, -1.5)])
    g4 = VGroup(n4.shift(UP * 0.15), arrs)
    out.append((g4, lambda n=n4, a=arrs: AnimationGroup(n[0].animate.set_color(C_RED).set_opacity(0.7),
                                                         LaggedStart(*[GrowArrow(x) for x in a], lag_ratio=0.4))))
    # 05 token → 向量
    s5 = sentence(PROMPT, size=18, h=0.4, buff=0.05).move_to([0, 0.6, 0])
    vecs = VGroup()
    alphas = []
    for tk in s5:
        a5 = r.uniform(0.2, 1, 5)
        alphas.append(a5)
        v = VGroup(*[Square(side_length=0.14, stroke_width=0, fill_color=C_BLUE, fill_opacity=0) for _ in range(5)]).arrange(DOWN, buff=0.03)
        vecs.add(v.next_to(tk, DOWN, buff=0.18))
    out.append((VGroup(s5, vecs), lambda v=vecs, al=alphas: LaggedStart(
        *[AnimationGroup(*[sq.animate.set_fill(opacity=a) for sq, a in zip(x, aa)]) for x, aa in zip(v, al)], lag_ratio=0.12)))
    # 06 注意力探照灯
    s6 = sentence(PROMPT, size=18, h=0.4, buff=0.05).move_to([0, -0.6, 0])
    arcs = VGroup(*[ArcBetweenPoints(s6[8].get_top(), s6[k].get_top(), angle=-PI * 0.55, color=C_ATT, stroke_width=w)
                    for k, w in ((2, 6), (3, 5), (7, 2), (0, 1.5))])
    arcs.set_stroke(opacity=0)
    out.append((VGroup(s6, arcs), lambda a=arcs: LaggedStart(*[x.animate.set_stroke(opacity=1) for x in a], lag_ratio=0.2)))
    # 07 高塔与概率
    tw7 = tower(4, w=1.2, h=0.36).move_to([-1.3, 0, 0])
    cands, probs = ["霜", "上", "雪", "面"], [0.86, 0.05, 0.05, 0.04]
    bars7 = VGroup()
    for i, (c, p) in enumerate(zip(cands, probs)):
        x = 0.5 + i * 0.5
        b = Rectangle(width=0.34, height=max(1.8 * p, 0.04), stroke_width=0, fill_color=C_GOLD, fill_opacity=0.9)
        b.move_to([x, -0.9 + b.height / 2, 0])
        bars7.add(VGroup(b, T(c, size=20, color=C_WHITE).move_to([x, -1.12, 0])))
    pick = T("霜", size=40, color=C_GOLD, weight=BOLD).move_to([0.5, 1.15, 0]).set_opacity(0)
    out.append((VGroup(tw7, bars7, pick), lambda p=pick, b=bars7: AnimationGroup(Indicate(b[0], color=C_GOLD), p.animate.set_opacity(1))))
    # 08 书架
    shelves = VGroup(*[Line([-2.0, y, 0], [2.0, y, 0], color=C_GREY, stroke_width=3) for y in (-1.0, -0.15, 0.7)])
    books = VGroup()
    for y in (-1.0, -0.15, 0.7):
        x = -1.95
        while x < 1.85:
            bw = r.uniform(0.08, 0.17)
            bh = r.uniform(0.45, 0.72)
            col = [C_GOLD, C_BLUE, C_GREY, C_TEAL][int(r.integers(0, 4))]
            books.add(Rectangle(width=bw, height=bh, stroke_width=0, fill_color=col, fill_opacity=0.25).move_to([x + bw / 2, y + bh / 2, 0]))
            x += bw + 0.03
    out.append((VGroup(shelves, books), lambda b=books: LaggedStart(*[x.animate.set_fill(opacity=0.85) for x in b], lag_ratio=0.01)))
    # 09 旋钮偏转
    ks = VGroup()
    ptrs = VGroup()
    for i in range(6):
        c = Circle(radius=0.28, color=C_YELLOW, stroke_width=3, fill_color=C_DARK, fill_opacity=1).move_to([-1.75 + 0.7 * i, 0, 0])
        a = r.uniform(-1, 1)
        p = Line(c.get_center(), c.get_center() + 0.22 * np.array([np.sin(a), np.cos(a), 0]), color=C_YELLOW, stroke_width=4)
        ks.add(c)
        ptrs.add(p)
    out.append((VGroup(ks, ptrs), lambda ps=ptrs: AnimationGroup(*[Rotate(p, -0.45, about_point=p.get_start()) for p in ps])))
    # 10 本集
    q = T("?", size=72, color=C_RED, weight=BOLD).move_to([-1.5, 0.1, 0])
    tc = tool_card("〔调用 计算器〕", size=18).move_to([0.6, 0.6, 0])
    feats = VGroup(*[Dot([0.0 + 0.35 * i, -0.6, 0], radius=0.09, color=C_GREY) for i in range(6)])
    out.append((VGroup(q, tc, feats), lambda f=feats: LaggedStart(*[f[i].animate.set_color(C_ATT).scale(1.5) for i in (1, 4)], lag_ratio=0.4)))
    return out


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
        self.outro()          # 111–124
        self.tail()           # 125–126
        self.finish()

    # ------------------------------------------------------------ 前奏 1–4
    def intro(self):
        c = title_card("第 10 集", "能与不能", "幻觉、工具与看不透的黑箱")
        s, e, t, line, st = c
        self.play_bars(FadeIn(s, shift=DOWN * 0.2), FadeIn(e, shift=DOWN * 0.2), bars=0.75)
        self.play_bars(Write(t), bars=1)
        self.play_bars(GrowFromCenter(line), FadeIn(st, shift=UP * 0.2), bars=0.75)
        self.at_bar(3.5)
        self.set_counter("1750 亿", bars=0.5)
        self.at_bar(4.5)
        self.play_bars(FadeOut(c), bars=0.5)

    # ------------------------------------------------------------ 主歌一 5–20：泛化与幻觉
    def _ask(self, prompt, answer, acolor, size=26):
        """左边问题飞进中间的塔，右边吐出回答"""
        q = T(prompt, size=size, color=C_BLUE)
        if q.width > 4.6:
            q.scale_to_fit_width(4.6)
        q.move_to([-4.3, 0.5, 0])
        a = T(answer, size=34, color=acolor, weight=BOLD)
        if a.width > 4.0:
            a.scale_to_fit_width(4.0)
        a.move_to([4.2, 0.5, 0])
        return q, a

    def verse1(self):
        self.at_bar(5)
        self.tag("背过，与举一反三")
        tw = tower(5, w=1.8, h=0.45).move_to([0, 0.5, 0])
        self.tw = tw
        q, a = self._ask("床前明月光，疑是地上__", "霜", C_GOLD)
        a.scale(1.8)
        self.play_bars(FadeIn(tw), FadeIn(q, shift=RIGHT * 0.3), bars=0.25)
        self.play_bars(q.copy().animate.scale(0.3).move_to(tw.get_left()).set_opacity(0), Indicate(tw, color=C_GOLD, scale_factor=1.03), bars=0.5)
        self.play_bars(FadeIn(a, shift=RIGHT * 0.3), bars=0.5)
        n1 = T("训练文本里出现过很多次：多半是“背过”的", size=24, color=C_GREY).move_to([0, -1.6, 0])
        self.play_bars(FadeIn(n1), bars=0.5)
        # 7–8 泛化
        self.at_bar(7)
        q2, a2 = self._ask("用“霜”字写一句关于手机的诗", "手机屏光冷如霜", C_GREEN, size=24)
        a2.scale(0.85)
        self.play_bars(FadeOut(VGroup(q, a, n1)), FadeIn(q2, shift=RIGHT * 0.3), bars=0.5)
        self.play_bars(q2.copy().animate.scale(0.3).move_to(tw.get_left()).set_opacity(0), Indicate(tw, color=C_GREEN, scale_factor=1.03), bars=0.5)
        self.play_bars(FadeIn(a2, shift=RIGHT * 0.3), bars=0.5)
        n2 = T("没见过的问题也能答：泛化（示意）", size=26, color=C_GREEN).move_to([0, -1.6, 0])
        self.play_bars(FadeIn(n2), bars=0.5)
        # 9–10 冷门问题
        self.at_bar(9)
        q3, a3 = self._ask("1923 年某小镇的镇长是谁？", "王德明，任期三年。", C_GOLD, size=24)
        a3.scale(0.75)
        self.play_bars(FadeOut(VGroup(q2, a2, n2)), FadeIn(q3, shift=RIGHT * 0.3), bars=0.5)
        self.play_bars(q3.copy().animate.scale(0.3).move_to(tw.get_left()).set_opacity(0), Indicate(tw, color=C_GOLD, scale_factor=1.03), bars=0.5)
        self.play_bars(FadeIn(a3, shift=RIGHT * 0.3), bars=0.4)
        qm = T("？", size=60, color=C_RED, weight=BOLD).next_to(a3, UP, buff=0.2)
        n3 = T("不知道的事，也说得像真的一样（虚构示意）", size=24, color=C_RED).move_to([0, -1.6, 0])
        self.play_bars(FadeIn(qm, scale=1.4), FadeIn(n3), bars=0.6)
        # 11–12 像对的话 vs 查证
        self.at_bar(11)
        self.play_bars(FadeOut(VGroup(q3, qm, n3)), tw.animate.move_to([-4.2, 0.4, 0]), a3.animate.move_to([-4.2, 2.2, 0]), bars=0.5)
        m1 = VGroup(T("像不像“对的话”", size=26, color=C_WHITE), Rectangle(width=4.0, height=0.36, color=C_GREY, stroke_width=2)).arrange(RIGHT, buff=0.3)
        m2 = VGroup(T("是否属实", size=26, color=C_WHITE), Rectangle(width=4.0, height=0.36, color=C_GREY, stroke_width=2)).arrange(RIGHT, buff=0.3)
        m2[1].align_to(m1[1], LEFT)
        m2[0].next_to(m2[1], LEFT, buff=0.3)
        ms = VGroup(m1, m2).arrange(DOWN, buff=0.6, aligned_edge=RIGHT).move_to([1.9, 0.6, 0])
        fill = Rectangle(width=4.0, height=0.36, stroke_width=0, fill_color=C_GREEN, fill_opacity=0.8).move_to(m1[1])
        qq = T("？", size=36, color=C_RED, weight=BOLD).move_to(m2[1])
        self.play_bars(FadeIn(ms), bars=0.4)
        self.play_bars(GrowFromEdge(fill, LEFT), FadeIn(qq, scale=1.4), bars=0.6)
        n4 = T("它学的是“什么样的话像对的”，生成时没有查证这一步", size=24, color=C_GREY).move_to([0.6, -1.4, 0])
        self.play_bars(FadeIn(n4), bars=0.5)
        # 13–14 参考文献卡
        self.at_bar(13)
        self.fade_rest(0.25)
        ref = card(["陈思远，周雨桐（2019）", "《月光意象的神经网络分析》", "《计算诗学学报》12(3): 45–67"],
                   title="参考文献 [1]", tcolor=C_GOLD, width=6.4, size=28).move_to([0, 0.5, 0])
        fake = T("（虚构示意）", size=22, color=C_GREY).next_to(ref, DOWN, buff=0.2)
        self.play_bars(FadeIn(ref, shift=UP * 0.2), FadeIn(fake), bars=0.75)
        ticks = VGroup(*[T("✓", size=30, color=C_GREEN).next_to(ln, RIGHT, buff=0.25) for ln in ref[1][1]])
        tl = T("作者、标题、期刊、页码：格式样样齐全", size=24, color=C_GREEN).next_to(fake, DOWN, buff=0.2)
        self.play_bars(LaggedStart(*[FadeIn(t, scale=1.5) for t in ticks], lag_ratio=0.3), FadeIn(tl), bars=0.75)
        # 15–16 一查：查无此文
        self.at_bar(15)
        mg = magnifier().move_to(ref.get_left() + RIGHT * 0.6 + UP * 0.3)
        crosses = VGroup(*[T("✗", size=30, color=C_RED, weight=BOLD).move_to(t) for t in ticks])
        self.play_bars(FadeIn(mg), FadeOut(tl), bars=0.25)
        self.play_bars(mg.animate.move_to(ref.get_right() + LEFT * 0.6 + DOWN * 0.3),
                       LaggedStart(*[Transform(t, c) for t, c in zip(ticks, crosses)], lag_ratio=0.3), bars=0.75)
        stamp = T("查无此文", size=48, color=C_RED, weight=BOLD).rotate(0.15).move_to(ref)
        self.play_bars(FadeIn(stamp, scale=1.5), FadeOut(mg), bars=0.25)
        px = shatter(ref[0], color=C_RED)
        self.play_bars(FadeOut(VGroup(ref, ticks, stamp)), FadeIn(px), bars=0.15)
        r = np.random.default_rng(1)
        self.play_bars(*[p.animate.shift(np.array([r.uniform(-1.5, 1.5), r.uniform(-2.2, -0.6), 0])).set_opacity(0) for p in px], bars=0.35)
        self.remove(px)
        hl = VGroup(T("幻觉：流利，但与事实不符", size=34, color=C_RED, weight=BOLD),
                    T("不是故意的，是“像对的话”生成得太自然", size=26, color=C_GREY)).arrange(DOWN, buff=0.2).move_to([0, 0.6, 0])
        self.play_bars(FadeIn(hl, shift=UP * 0.2), FadeOut(fake), bars=0.25)
        # 17–18 评分表
        self.at_bar(17)
        self.play_bars(FadeOut(hl), bars=0.25)
        rows = VGroup(
            VGroup(T("答对", size=30, color=C_GREEN), T("1 分", size=30, color=C_GREEN)),
            VGroup(T("答错", size=30, color=C_RED), T("0 分", size=30, color=C_RED)),
            VGroup(T("说“不知道”", size=30, color=C_GREY), T("0 分", size=30, color=C_GREY)))
        for i, rw in enumerate(rows):
            rw[0].move_to([-3.6, 1.4 - 0.75 * i, 0], aligned_edge=LEFT)
            rw[1].move_to([-0.6, 1.4 - 0.75 * i, 0], aligned_edge=LEFT)
        frame = SurroundingRectangle(rows, color=C_GREY, buff=0.3, corner_radius=0.1)
        head = T("只算对错的评分", size=26, color=C_WHITE).next_to(frame, UP, buff=0.15)
        self.play_bars(FadeIn(head), Create(frame), LaggedStart(*[FadeIn(rw) for rw in rows], lag_ratio=0.3), bars=0.75)
        conc = VGroup(T("猜一猜：有机会得分", size=28, color=C_GOLD), T("说不知道：一定 0 分", size=28, color=C_GREY)).arrange(DOWN, buff=0.25, aligned_edge=LEFT)
        conc.move_to([3.9, 0.7, 0])
        arr = Arrow(frame.get_right(), conc.get_left(), buff=0.15, color=C_GOLD)
        self.play_bars(GrowArrow(arr), FadeIn(conc), bars=0.5)
        src = T("原因之一（Kalai 等，OpenAI，2025）", size=22, color=C_GREY).move_to([0, -1.75, 0])
        self.play_bars(FadeIn(src), bars=0.5)
        # 19–20 办法
        self.at_bar(19)
        self.fade_rest(0.25)
        fixes = VGroup(card(["没把握时说出来"], title="说“我不确定”", tcolor=C_GREEN, width=3.6, size=24),
                       card(["先搜索，再回答"], title="查资料", tcolor=C_GREEN, width=3.6, size=24),
                       card(["重要的事要核对"], title="人来把关", tcolor=C_GREEN, width=3.6, size=24)).arrange(RIGHT, buff=0.45).move_to([0, 0.5, 0])
        self.play_bars(LaggedStart(*[FadeIn(f, shift=UP * 0.2) for f in fixes], lag_ratio=0.35), bars=1.0)
        nt = T("都只能减少幻觉，不能完全消除", size=24, color=C_GREY).next_to(fixes, DOWN, buff=0.4)
        self.play_bars(FadeIn(nt), bars=0.25)
        self.at_bar(20.5)
        self.fade_rest(0.5)

    # ------------------------------------------------------------ 副歌
    def hook(self, s):
        self.at_bar(s)
        self.tag("能与不能")
        # ① 一本正经
        b = bubble("答得很流利，格式也很漂亮……", C_GOLD, size=28).move_to([-0.6, 0.8, 0])
        qm = T("？", size=72, color=C_RED, weight=BOLD).next_to(b, RIGHT, buff=0.3)
        nt = T("幻觉：不是故意的", size=24, color=C_GREY).next_to(b, DOWN, buff=0.35)
        self.play_bars(FadeIn(b, shift=UP * 0.2), bars=0.75)
        self.play_bars(FadeIn(qm, scale=1.5), FadeIn(nt), bars=0.75)
        # ② 截止日期
        self.at_bar(s + 2)
        self.play_bars(FadeOut(VGroup(b, qm, nt)), bars=0.25)
        axis = Line([-5.5, 0.3, 0], [5.5, 0.3, 0], color=C_GREY, stroke_width=3)
        seen = Line([-5.5, 0.3, 0], [1.0, 0.3, 0], color=C_BLUE, stroke_width=6)
        flag = VGroup(Line([1.0, 0.3, 0], [1.0, 1.6, 0], color=C_WHITE, stroke_width=3),
                      Polygon([1.0, 1.6, 0], [1.9, 1.35, 0], [1.0, 1.1, 0], color=C_GOLD, fill_opacity=0.8, stroke_width=0))
        fl = T("训练截止", size=24, color=C_GOLD).next_to(flag, UP, buff=0.1)
        pts = VGroup(*[Dot([x, 0.3, 0], radius=0.1, color=C_BLUE) for x in (-4.5, -3.0, -1.6, -0.3)],
                     *[Dot([x, 0.3, 0], radius=0.1, color=C_GREY) for x in (2.4, 3.6, 4.8)])
        after = T("之后的事：没见过", size=24, color=C_GREY).move_to([3.6, -0.4, 0])
        self.play_bars(Create(axis), Create(seen), FadeIn(pts[:4]), bars=0.5)
        self.play_bars(FadeIn(flag), FadeIn(fl), FadeIn(pts[4:]), FadeIn(after), bars=0.75)
        # ③ 工具
        self.at_bar(s + 4)
        self.play_bars(FadeOut(VGroup(axis, seen, flag, fl, pts, after)), bars=0.25)
        model = VGroup(RoundedRectangle(width=2.4, height=1.6, corner_radius=0.15, color=C_GOLD, fill_opacity=0.12),
                       T("模型", size=30, color=C_GOLD)).move_to([-3.2, 0.5, 0])
        model[1].move_to(model[0])
        srch = search_icon().move_to([2.6, 1.5, 0])
        calc = calculator().scale(0.55).move_to([2.6, -0.3, 0])
        l1 = Line(model[0].get_right(), srch.get_left(), color=C_TOOL, stroke_width=3)
        l2 = Line(model[0].get_right(), calc.get_left(), color=C_TOOL, stroke_width=3)
        self.play_bars(FadeIn(model), bars=0.5)
        self.play_bars(Create(l1), Create(l2), FadeIn(srch), FadeIn(calc), bars=0.75)
        # ④ 看不清里面
        self.at_bar(s + 6)
        self.play_bars(FadeOut(VGroup(model, srch, calc, l1, l2)), bars=0.25)
        tw = tower(6, w=2.4, h=0.42).move_to([0, 0.5, 0])
        fog = Rectangle(width=3.4, height=tw.height + 0.4, stroke_width=0, fill_color=C_GREY, fill_opacity=0.55).move_to(tw)
        r = np.random.default_rng(s)
        lights = VGroup(*[Dot(tw.get_center() + np.array([r.uniform(-1, 1), r.uniform(-1.1, 1.1), 0]), radius=0.07, color=C_ATT) for _ in range(5)])
        self.play_bars(FadeIn(tw), bars=0.25)
        self.play_bars(FadeIn(fog), FadeIn(lights), bars=0.75)
        self.play_bars(LaggedStart(*[Flash(d, color=C_ATT, line_length=0.12) for d in lights], lag_ratio=0.2), bars=0.5)
        # ⑤ 黑箱
        self.at_bar(s + 8)
        self.fade_rest(0.25)
        box = black_box(w=3.2, h=2.3, depth=0.45).move_to([0, 0.1, 0])
        inner = tower(3, w=1.6, h=0.42).move_to(box.front)
        glow = VGroup(*[Dot(inner.get_center() + np.array([x, y, 0]), radius=0.08, color=C_ATT) for x, y in ((-0.4, 0.3), (0.3, -0.2), (0.5, 0.4))])
        self.play_bars(FadeIn(box), bars=0.25)
        self.play_bars(VGroup(box.front, box.q).animate.shift(UP * 0.3).set_opacity(0.12), FadeIn(inner), FadeIn(glow), bars=0.5)
        slogan = T("一层一层，把黑箱打开", size=40, color=C_YELLOW, weight=BOLD).move_to([0, 2.55, 0])
        self.play_bars(Write(slogan), bars=0.5)
        self.at_bar(s + 9.5)
        self.fade_rest(0.5)

    # ------------------------------------------------------------ 主歌二 31–46：知识截止与记忆
    def verse2(self):
        self.at_bar(31)
        self.tag("知识截止与“记忆”")
        ks, trs = knob_grid(3, 8, seed=31, radius=0.22)
        ks.move_to([-0.8, 0.5, 0])
        lk = lock_icon(s=1.3).next_to(ks, RIGHT, buff=0.6)
        ll = T("训练结束：旋钮定格", size=28, color=C_YELLOW).next_to(ks, DOWN, buff=0.45)
        self.play_bars(FadeIn(ks), bars=0.5)
        self.play_bars(*[t.animate.set_value(t.get_value() + 0.05) for t in trs], bars=0.5)
        self.play_bars(FadeIn(lk, shift=DOWN * 0.3), FadeIn(ll), Indicate(self.counter, color=C_YELLOW), bars=0.75)
        # 33–34 截止日期
        self.at_bar(33)
        self.play_bars(FadeOut(VGroup(ks, lk, ll)), bars=0.25)
        axis = Line([-5.8, 0.3, 0], [5.8, 0.3, 0], color=C_GREY, stroke_width=3)
        seen = Line([-5.8, 0.3, 0], [0.8, 0.3, 0], color=C_BLUE, stroke_width=8)
        cut = DashedLine([0.8, -0.6, 0], [0.8, 1.6, 0], color=C_GOLD)
        cl = T("截止日期", size=26, color=C_GOLD).next_to(cut, UP, buff=0.1)
        sl = T("训练文本", size=26, color=C_BLUE).move_to([-2.5, 0.85, 0])
        news = VGroup(*[card([t], width=1.9, size=20) for t in ("新闻", "新论文", "新比赛")]).arrange(RIGHT, buff=0.15).move_to([3.4, 1.0, 0])
        news.set_opacity(0.35)
        al = T("之后发生的事：没见过", size=26, color=C_GREY).move_to([3.4, -0.4, 0])
        self.play_bars(Create(axis), Create(seen), FadeIn(sl), bars=0.5)
        self.play_bars(Create(cut), FadeIn(cl), bars=0.5)
        self.play_bars(FadeIn(news), FadeIn(al), bars=0.5)
        # 35–36 聊天不改旋钮
        self.at_bar(35)
        self.fade_rest(0.25)
        tw = tower(5, w=2.0, h=0.45).move_to([3.8, 0.7, 0])
        tl = T("旋钮：不变", size=24, color=C_YELLOW).next_to(tw, DOWN, buff=0.25)
        self.v2_tw = tw
        u1 = bubble("我叫小林。", C_BLUE, size=24)
        a1 = bubble("你好，小林！", C_GREEN, size=24)
        u2 = bubble("我叫什么？", C_BLUE, size=24)
        a2 = bubble("你叫小林。", C_GREEN, size=24)
        u3 = bubble("再写句诗吧。", C_BLUE, size=24)
        chat = [u1, a1, u2, a2, u3]
        for i, bb in enumerate(chat):
            bb.move_to([-3.2 + (0.5 if i % 2 == 0 else -0.5), 2.3 - 0.75 * i, 0])
        self.chat = chat
        self.play_bars(FadeIn(tw), FadeIn(tl), FadeIn(u1, shift=UP * 0.2), bars=0.5)
        self.play_bars(u1.copy().animate.scale(0.4).move_to(tw.get_bottom()).set_opacity(0), bars=0.5)
        self.play_bars(FadeIn(a1, shift=UP * 0.2), Indicate(tl, color=C_YELLOW), Indicate(self.counter, color=C_YELLOW), bars=0.5)
        nc = T("聊天不改旋钮", size=26, color=C_GREY).next_to(tl, DOWN, buff=0.2)
        self.play_bars(FadeIn(nc), bars=0.25)
        # 37–38 整段对话重新喂一遍
        self.at_bar(37)
        self.play_bars(FadeIn(u2, shift=UP * 0.2), FadeOut(nc), bars=0.5)
        hist = VGroup(u1, a1, u2)
        self.play_bars(hist.copy().animate.scale(0.3).move_to(tw.get_bottom()).set_opacity(0), bars=0.75)
        self.play_bars(FadeIn(a2, shift=UP * 0.2), bars=0.5)
        # 39–40 一轮两轮三轮
        self.at_bar(39)
        self.play_bars(FadeIn(u3, shift=UP * 0.2), bars=0.4)
        hist = VGroup(*chat)
        lens = VGroup()
        for i, n in enumerate((1, 3, 5)):
            bar_ = Rectangle(width=0.32 * n, height=0.22, stroke_width=0, fill_color=C_BLUE, fill_opacity=0.8)
            lab = T(f"第 {i + 1} 轮", size=20, color=C_GREY)
            row = VGroup(lab, bar_).arrange(RIGHT, buff=0.15)
            lens.add(row)
        lens.arrange(DOWN, aligned_edge=LEFT, buff=0.12).move_to([0.6, -1.9, 0])
        ltitle = T("每轮的输入长度", size=20, color=C_GREY).next_to(lens, LEFT, buff=0.3)
        self.play_bars(hist.copy().animate.scale(0.3).move_to(tw.get_bottom()).set_opacity(0),
                       FadeIn(ltitle), LaggedStart(*[FadeIn(l, shift=RIGHT * 0.2) for l in lens], lag_ratio=0.35), bars=1.1)
        self.lens = VGroup(ltitle, lens)
        # 41–42 上下文
        self.at_bar(41)
        box = SurroundingRectangle(hist, color=C_BLUE, buff=0.2, corner_radius=0.15)
        bl = T("上下文 = 它的“记忆”", size=30, color=C_BLUE, weight=BOLD).next_to(box, RIGHT, buff=0.3).shift(UP * 0.2)
        if bl.get_right()[0] > tw.get_left()[0] - 0.1:
            bl.scale_to_fit_width(tw.get_left()[0] - 0.1 - box.get_right()[0] - 0.3).next_to(box, RIGHT, buff=0.3).shift(UP * 0.2)
        self.play_bars(Create(box), FadeOut(self.lens), bars=0.75)
        self.play_bars(FadeIn(bl), bars=0.5)
        # 43–44 窗口上限
        self.at_bar(43)
        self.fade_rest(0.25)
        win = Rectangle(width=9.0, height=0.8, color=C_WHITE, stroke_width=3).move_to([0, 0.6, 0])
        wl = T("上下文窗口（有上限）", size=26, color=C_WHITE).next_to(win, UP, buff=0.2)
        step = 0.68
        blocks = VGroup(*[Rectangle(width=0.62, height=0.6, stroke_width=0, fill_color=C_BLUE if k % 2 == 0 else C_GREEN, fill_opacity=0.7)
                          for k in range(16)]).arrange(RIGHT, buff=step - 0.62)
        blocks.align_to(win, LEFT).shift(RIGHT * 0.13).set_y(0.6)
        old, new = blocks[:13], blocks[13:]
        for b_ in new:
            b_.set_stroke(C_RED, 2)
        self.play_bars(Create(win), FadeIn(wl), bars=0.25)
        self.play_bars(LaggedStart(*[FadeIn(b_) for b_ in old], lag_ratio=0.08), bars=0.45)
        self.play_bars(LaggedStart(*[FadeIn(b_, shift=LEFT * 0.2) for b_ in new], lag_ratio=0.2), bars=0.25)
        over = blocks[:3]
        blocks.generate_target()
        blocks.target.shift(LEFT * 3 * step)
        blocks.target[:3].set_fill(C_GREY, 0.4)
        blocks.target[13:].set_stroke(width=0)
        self.play_bars(MoveToTarget(blocks), bars=0.5)
        cutl = T("装不下：删掉或压缩最早的部分（做法因产品而异）", size=22, color=C_GREY).next_to(win, DOWN, buff=0.3)
        self.play_bars(FadeOut(over, shift=LEFT * 0.4), FadeIn(cutl), bars=0.3)
        rest = blocks[3:]
        # 45–46 摘要便签
        self.at_bar(45)
        self.play_bars(FadeOut(cutl), bars=0.25)
        note = card(["用户叫小林，喜欢诗"], title="摘要", tcolor=C_GOLD, width=3.6, size=22).move_to([-4.0, -1.5, 0])
        drawer = Rectangle(width=4.0, height=0.5, color=C_GREY, stroke_width=2).move_to([-4.0, -2.2, 0])
        self.play_bars(FadeIn(note, shift=UP * 0.2), FadeIn(drawer), bars=0.5)
        front = VGroup(rest[0], rest[1])
        slot = front.get_center()
        self.play_bars(FadeOut(front, shift=UP * 0.3), FadeOut(drawer), note.animate.scale_to_fit_width(2 * step - 0.06).move_to(slot), bars=0.75)
        nl = T("仍是上下文：旋钮没变", size=26, color=C_YELLOW).move_to([2.6, -1.4, 0])
        self.play_bars(FadeIn(nl), Indicate(self.counter, color=C_YELLOW), bars=0.5)

    # ------------------------------------------------------------ 间奏 47–50：记忆完整演示
    def inst(self):
        self.at_bar(47)
        self.fade_rest(0.25)
        self.tag("每一轮，都从头读")
        tw = tower(5, w=2.0, h=0.45).move_to([4.2, 0.7, 0])
        ks, trs = knob_grid(1, 5, seed=47, radius=0.18)
        ks.next_to(tw, DOWN, buff=0.3)
        self.play_bars(FadeIn(tw), FadeIn(ks), bars=0.25)
        msgs = [("你好", C_BLUE), ("你好！", C_GREEN), ("今天写诗", C_BLUE), ("好的。", C_GREEN), ("要押韵", C_BLUE), ("没问题。", C_GREEN)]
        col = VGroup()
        bubbles = []
        for i, (t, c) in enumerate(msgs):
            bb = bubble(t, c, size=22).move_to([-3.6 + (0.4 if i % 2 == 0 else -0.4), 2.3 - 0.68 * i, 0])
            bubbles.append(bb)
        for k in range(3):
            u, a = bubbles[2 * k], bubbles[2 * k + 1]
            self.play_bars(FadeIn(u, shift=UP * 0.15), bars=0.15)
            col = VGroup(*bubbles[:2 * k + 1])
            self.play_bars(col.copy().animate.scale(0.3).move_to(tw.get_bottom()).set_opacity(0), bars=0.4)
            self.play_bars(FadeIn(a, shift=UP * 0.15), bars=0.25)
        nl = T("旋钮一个没动；“记得”，全靠每次重新读一遍", size=24, color=C_GREY).move_to([0, -2.2, 0])
        self.play_bars(FadeIn(nl), bars=0.35)
        self.at_bar(50.5)
        self.fade_rest(0.5)

    # ------------------------------------------------------------ 主歌三 61–76：工具与智能体
    def verse3(self):
        self.at_bar(61)
        self.tag("工具")
        tw = tower(5, w=2.0, h=0.45).move_to([-4.6, 0.6, 0])
        net = T("联网 ✗", size=26, color=C_RED).next_to(tw, DOWN, buff=0.3)
        prob = T("37 × 89 = ?", size=48, color=C_WHITE).move_to([1.2, 1.2, 0])
        wrong = T("= 3193", size=40, color=C_RED).next_to(prob, DOWN, buff=0.4)
        x_ = T("✗", size=40, color=C_RED, weight=BOLD).next_to(wrong, RIGHT, buff=0.3)
        wl = T("大数乘法容易算错（示意）", size=24, color=C_GREY).next_to(wrong, DOWN, buff=0.4)
        self.play_bars(FadeIn(tw), FadeIn(net), FadeIn(prob), bars=0.5)
        self.play_bars(Write(wrong), bars=0.6)
        self.play_bars(FadeIn(x_, scale=1.4), FadeIn(wl), bars=0.4)
        # 63–64 约定格式
        self.at_bar(63)
        self.play_bars(FadeOut(VGroup(wrong, x_, wl, net)), bars=0.25)
        tc = tool_card("〔调用 计算器：37×89〕", size=30).move_to([1.2, 0.0, 0])
        tl = T("约定好的格式：调用指令（示意）", size=24, color=C_TOOL).next_to(tc, DOWN, buff=0.3)
        self.play_bars(FadeIn(tc, scale=1.1), bars=0.75)
        self.play_bars(FadeIn(tl), bars=0.5)
        # 65–66 写出指令，暂停
        self.at_bar(65)
        self.play_bars(FadeOut(VGroup(tc, tl, prob)), bars=0.25)
        row = sentence(["37", "×", "89", "等于"], size=22, color=C_BLUE).move_to([-0.2, 1.4, 0]).align_to([-2.2, 0, 0], LEFT)
        tc2 = tool_card("〔调用 计算器：37×89〕", size=22).next_to(row, RIGHT, buff=0.1)
        self.play_bars(FadeIn(row), bars=0.25)
        self.play_bars(FadeIn(tc2[0]), Write(tc2[1]), bars=0.75)
        pause = VGroup(Rectangle(width=0.16, height=0.6, stroke_width=0, fill_color=C_WHITE, fill_opacity=1),
                       Rectangle(width=0.16, height=0.6, stroke_width=0, fill_color=C_WHITE, fill_opacity=1)).arrange(RIGHT, buff=0.14)
        pause.next_to(tc2, DOWN, buff=0.35)
        pl = T("生成先暂停", size=24, color=C_GREY).next_to(pause, RIGHT, buff=0.25)
        self.play_bars(FadeIn(pause, scale=1.3), FadeIn(pl), bars=0.5)
        # 67–68 程序执行，结果贴回
        self.at_bar(67)
        calc = calculator().move_to([5.4, -0.4, 0])
        cl = T("程序", size=22, color=C_GREY).next_to(calc, UP, buff=0.15)
        self.play_bars(FadeIn(calc), FadeIn(cl), FadeOut(VGroup(pause, pl)), bars=0.25)
        fly = tc2.copy()
        self.play_bars(fly.animate.scale(0.5).move_to(calc.disp).set_opacity(0), bars=0.5)
        res_d = T("3293", size=28, color=C_GREEN).move_to(calc.disp)
        self.play_bars(FadeIn(res_d), bars=0.25)
        res = tool_card("〔结果：3293〕", size=22, color=C_GREEN).next_to(tc2, DOWN, buff=0.2).align_to(row, LEFT)
        self.play_bars(TransformFromCopy(res_d, res), bars=0.6)
        rl = T("结果贴回上下文", size=24, color=C_GREEN).next_to(res, RIGHT, buff=0.3)
        self.play_bars(FadeIn(rl), bars=0.4)
        # 69–70 接着往下写
        self.at_bar(69)
        self.play_bars(FadeOut(rl), bars=0.25)
        cont = T("37 × 89 = 3293。", size=36, color=C_GOLD, weight=BOLD).next_to(res, DOWN, buff=0.45).align_to(row, LEFT)
        self.play_bars(Indicate(tw, color=C_GOLD, scale_factor=1.03), Write(cont), bars=1.0)
        src = T("答案有了来源", size=26, color=C_GREEN).next_to(cont, RIGHT, buff=0.4)
        self.play_bars(FadeIn(src), bars=0.5)
        # 71–72 三种工具，同一套
        self.at_bar(71)
        self.fade_rest(0.25)
        flow_heads = ["写指令", "程序执行", "贴回结果"]
        rows = VGroup()
        for name, ex in (("搜索", "〔搜索：今天的新闻〕"), ("计算器", "〔计算：37×89〕"), ("运行代码", "〔运行：画个图〕")):
            nm = T(name, size=26, color=C_TOOL)
            c1 = tool_card(ex, size=20)
            rows.add(VGroup(nm, c1))
        for i, r_ in enumerate(rows):
            r_[0].move_to([-5.4, 1.5 - 0.95 * i, 0])
            r_[1].move_to([-2.4, 1.5 - 0.95 * i, 0])
        heads = VGroup(*[T(h, size=24, color=C_GREY) for h in flow_heads])
        for h, x in zip(heads, (-2.4, 1.0, 4.2)):
            h.move_to([x, 2.4, 0])
        arrs = VGroup()
        tails = VGroup()
        for i, r_ in enumerate(rows):
            y = 1.5 - 0.95 * i
            a1 = Arrow([-0.6, y, 0], [0.2, y, 0], buff=0, color=C_GREY, stroke_width=3)
            gear = T("⚙", size=34, color=C_GREY).move_to([1.0, y, 0])
            a2 = Arrow([1.6, y, 0], [2.6, y, 0], buff=0, color=C_GREY, stroke_width=3)
            back = tool_card("〔结果〕", size=20, color=C_GREEN).move_to([4.2, y, 0])
            arrs.add(a1, a2)
            tails.add(gear, back)
        self.play_bars(FadeIn(heads), LaggedStart(*[FadeIn(r_) for r_ in rows], lag_ratio=0.3), bars=0.75)
        self.play_bars(LaggedStart(*[GrowArrow(a) for a in arrs], lag_ratio=0.1), LaggedStart(*[FadeIn(t) for t in tails], lag_ratio=0.1), bars=0.75)
        # 73–74 循环
        self.at_bar(73)
        self.fade_rest(0.25)
        names = ["想一步", "调用工具", "看结果", "再想"]
        cols = [C_GOLD, C_TOOL, C_GREEN, C_GOLD]
        cen = np.array([-1.6, 0.4, 0])
        R, RX = 1.5, 2.7
        nodes = VGroup()
        for k, (n, c) in enumerate(zip(names, cols)):
            ang = PI / 2 - k * PI / 2
            p = cen + np.array([RX * np.cos(ang), R * np.sin(ang), 0])
            nodes.add(VGroup(RoundedRectangle(width=1.9, height=0.62, corner_radius=0.15, color=c, fill_color="#121621", fill_opacity=1),
                             T(n, size=24, color=c)).move_to(p))
            nodes[-1][1].move_to(nodes[-1][0])
        loop = VGroup(*[CurvedArrow(nodes[k].get_center() + R * 0.0, nodes[(k + 1) % 4].get_center(), angle=-PI / 3, color=C_GREY, stroke_width=3)
                        for k in range(4)])
        for a in loop:
            a.set_z_index(-1)
        self.play_bars(LaggedStart(*[FadeIn(n) for n in nodes], lag_ratio=0.25), bars=0.6)
        self.play_bars(LaggedStart(*[Create(a) for a in loop], lag_ratio=0.2), bars=0.4)
        dot = Dot(nodes[0].get_center(), radius=0.12, color=C_YELLOW).set_z_index(-0.5)
        circ = VMobject().set_points_smoothly([cen + np.array([RX * np.sin(t), R * np.cos(t), 0]) for t in np.linspace(0, TAU, 41)])
        self.play_bars(MoveAlongPath(dot, circ), bars=0.7)
        self.v3_loop = VGroup(nodes, loop, dot)
        # 75–76 智能体
        self.at_bar(75)
        ag = T("智能体", size=36, color=C_YELLOW, weight=BOLD).move_to(cen)
        task = card(["① 查资料　✓", "② 算数据　✓", "③ 写报告　…"], title="任务", tcolor=C_WHITE, width=3.4, size=24).move_to([4.2, 0.6, 0])
        self.play_bars(FadeIn(ag, scale=1.3), FadeIn(task), bars=0.5)
        circ2 = circ.copy()
        self.play_bars(MoveAlongPath(dot, circ2), LaggedStart(*[Indicate(l, color=C_GREEN) for l in task[1][1][:2]], lag_ratio=0.4), bars=0.75)
        warn = T("每一步仍可能出错", size=22, color=C_GREY).next_to(task, DOWN, buff=0.3)
        self.play_bars(FadeIn(warn), bars=0.25)
        self.at_bar(76.5)
        self.fade_rest(0.5)

    # ------------------------------------------------------------ 桥段 77–84
    def bridge(self):
        self.at_bar(77)
        self.tag("看得见，却看不懂")
        r = np.random.default_rng(77)
        nums = VGroup(*[T(f"{v:+.2f}", size=22, color=C_YELLOW) for v in r.normal(0, 0.8, 12 * 7)])
        nums.arrange_in_grid(rows=7, cols=12, buff=(0.32, 0.2)).move_to([0, 0.45, 0])
        if nums.width > 12.8:
            nums.scale_to_fit_width(12.8)
        for n in nums:
            n.set_opacity(r.uniform(0.45, 1.0))
        self.play_bars(LaggedStart(*[FadeIn(n) for n in nums], lag_ratio=0.01), bars=1.25)
        lab = T("每个旋钮的数值都看得见", size=32, color=C_YELLOW, weight=BOLD).move_to([0, -2.25, 0])
        bg = BackgroundRectangle(lab, color=BG, fill_opacity=0.85, buff=0.15)
        self.play_bars(FadeIn(bg), FadeIn(lab), Indicate(self.counter, color=C_YELLOW), bars=1)
        self.play_bars(LaggedStart(*[Indicate(nums[i], color=C_WHITE, scale_factor=1.4) for i in r.choice(len(nums), 10, replace=False)], lag_ratio=0.1), bars=1.5)
        # 81–84
        self.at_bar(81)
        big = T("?", size=260, color=C_WHITE, weight=BOLD).move_to([0, 0.45, 0])
        lab2 = T("可它们合起来，在算什么？", size=32, color=C_WHITE, weight=BOLD).move_to(lab)
        self.play_bars(nums.animate.set_opacity(0.18), FadeIn(big, scale=0.6), Transform(lab, lab2), bars=1.5)
        self.play_bars(big.animate.scale(1.08), rate_func=there_and_back, bars=1.5)
        self.at_bar(84.5)
        self.fade_rest(0.5)

    # ------------------------------------------------------------ 主歌四 85–100：可解释性
    def verse4(self):
        self.at_bar(85)
        self.tag("可解释性：往里看")
        neur = VGroup(*[Circle(radius=0.28, color=C_GREY, stroke_width=2.5, fill_color=C_ATT, fill_opacity=0) for _ in range(12)]).arrange(RIGHT, buff=0.25)
        neur.move_to([0, 0.9, 0])
        nl = T("一排神经元", size=24, color=C_GREY).next_to(neur, UP, buff=0.3)
        con = T("概念：“下雨”", size=30, color=C_ATT).move_to([0, -0.6, 0])
        self.play_bars(FadeIn(neur), FadeIn(nl), bars=0.5)
        lit = {1: 0.9, 4: 0.6, 5: 0.8, 8: 0.5, 10: 0.7}
        self.play_bars(FadeIn(con), *[neur[i].animate.set_fill(C_ATT, a).set_stroke(C_ATT) for i, a in lit.items()], bars=0.75)
        nn = T("不是一个神经元，而是好几个一起亮", size=26, color=C_WHITE).move_to([0, -1.5, 0])
        self.play_bars(FadeIn(nn), bars=0.5)
        # 87–88 方向
        self.at_bar(87)
        self.play_bars(FadeOut(VGroup(nl, nn, con)), VGroup(neur).animate.scale(0.6).move_to([-3.8, 1.9, 0]), bars=0.4)
        plane = NumberPlane(x_range=[-3, 3], y_range=[-2, 2], x_length=4.8, y_length=3.2,
                            background_line_style=dict(stroke_color=C_GREY, stroke_opacity=0.25, stroke_width=1),
                            axis_config=dict(stroke_color=C_GREY, stroke_width=1.5)).move_to([1.6, 0.2, 0])
        o = plane.c2p(0, 0)
        v = Arrow(o, plane.c2p(2.2, 1.3), buff=0, color=C_ATT, stroke_width=6)
        vl = T("“下雨”的方向", size=24, color=C_ATT).next_to(v.get_end(), UP, buff=0.1)
        self.play_bars(FadeIn(plane), bars=0.35)
        self.play_bars(LaggedStart(*[Indicate(neur[i], color=C_ATT) for i in lit], lag_ratio=0.1), GrowArrow(v), FadeIn(vl), bars=0.75)
        cl = T("概念 = 空间里的一个方向", size=26, color=C_WHITE).move_to([-3.6, -0.6, 0])
        self.play_bars(FadeIn(cl), bars=0.5)
        # 89–90 叠加
        self.at_bar(89)
        dirs = [(-1.6, 1.7, C_BLUE), (-2.3, -0.9, C_GREEN), (0.6, -1.9, C_GOLD), (2.4, -0.6, C_RED)]
        more = VGroup(*[Arrow(o, plane.c2p(x, y), buff=0, color=c, stroke_width=5) for x, y, c in dirs])
        self.play_bars(FadeOut(cl), LaggedStart(*[GrowArrow(a) for a in more], lag_ratio=0.25), bars=1.0)
        sp = VGroup(T("5 个概念挤在 2 维里", size=26, color=C_WHITE), T("叠加（superposition，示意）", size=24, color=C_GREY)).arrange(DOWN, buff=0.15, aligned_edge=LEFT)
        sp.move_to([-3.9, -0.4, 0])
        self.play_bars(FadeIn(sp), bars=0.5)
        # 91–92 稀疏自编码器
        self.at_bar(91)
        self.fade_rest(0.25)
        vec = VGroup(*[Square(side_length=0.3, stroke_width=1, stroke_color=C_GREY, fill_color=C_ATT, fill_opacity=a)
                       for a in np.random.default_rng(91).uniform(0.2, 0.9, 6)]).arrange(DOWN, buff=0.04).move_to([-5.2, 0.4, 0])
        vl2 = T("一个向量", size=22, color=C_GREY).next_to(vec, DOWN, buff=0.2)
        sae = VGroup(RoundedRectangle(width=2.4, height=1.3, corner_radius=0.15, color=C_ATT, fill_opacity=0.12),
                     T("稀疏自编码器", size=24, color=C_ATT)).move_to([-2.4, 0.4, 0])
        sae[1].move_to(sae[0])
        a1 = Arrow(vec.get_right(), sae.get_left(), buff=0.1, color=C_GREY)
        feats = VGroup()
        on = {3: 1.4, 11: 1.0, 17: 0.8}
        for k in range(22):
            h = on.get(k, 0.04)
            feats.add(Rectangle(width=0.16, height=h, stroke_width=0, fill_color=C_ATT if k in on else C_GREY, fill_opacity=0.9))
        feats.arrange(RIGHT, buff=0.08, aligned_edge=DOWN).move_to([2.9, 0.0, 0]).align_to([0, -0.3, 0], DOWN)
        base = Line(feats.get_corner(DL) + LEFT * 0.1, feats.get_corner(DR) + RIGHT * 0.1, color=C_GREY, stroke_width=1.5)
        a2 = Arrow(sae.get_right(), base.get_left() + UP * 0.6, buff=0.1, color=C_GREY)
        fl = T("很多“特征”，每次只有少数几个亮", size=24, color=C_ATT).next_to(base, DOWN, buff=0.35)
        self.play_bars(FadeIn(vec), FadeIn(vl2), GrowArrow(a1), FadeIn(sae), bars=0.5)
        self.play_bars(GrowArrow(a2), Create(base), LaggedStart(*[GrowFromEdge(f, DOWN) for f in feats], lag_ratio=0.03), bars=0.75)
        self.play_bars(FadeIn(fl), bars=0.5)
        # 93–94 特征墙
        self.at_bar(93)
        self.fade_rest(0.25)
        labels = ["代码里的错误", "悲伤的语气", "法语", "DNA 序列", "金门大桥", "数学证明", "讽刺", "地名", "……"]
        wall = VGroup(*[card([l], width=3.4, size=24) for l in labels]).arrange_in_grid(rows=3, cols=3, buff=(0.3, 0.25)).move_to([0, 0.55, 0])
        self.wall = wall
        self.play_bars(LaggedStart(*[FadeIn(c, scale=0.9) for c in wall], lag_ratio=0.12), bars=1.0)
        wl = T("拆出数以百万计的特征，很多一看就懂（Anthropic，2024；标签为示意）", size=22, color=C_GREY).next_to(wall, DOWN, buff=0.3)
        if wl.width > 13:
            wl.scale_to_fit_width(13)
        self.play_bars(FadeIn(wl), bars=0.5)
        self.v4_wl = wl
        # 95–96 金门大桥特征
        self.at_bar(95)
        gg = wall[4]
        others = VGroup(*[c for i, c in enumerate(wall) if i != 4])
        self.play_bars(FadeOut(others), FadeOut(self.v4_wl), gg.animate.move_to([3.6, 1.7, 0]), bars=0.4)
        br = bridge().move_to([-3.0, 0.9, 0])
        txt = T("“我上周去了金门大桥……”", size=26, color=C_BLUE).move_to([-3.0, -0.6, 0])
        meter = VGroup(Rectangle(width=3.2, height=0.32, color=C_GREY, stroke_width=2)).move_to([3.6, 0.8, 0])
        mfill = Rectangle(width=3.2, height=0.32, stroke_width=0, fill_color=C_ATT, fill_opacity=0.9).move_to(meter)
        ml = T("特征强度", size=22, color=C_GREY).next_to(meter, DOWN, buff=0.15)
        self.play_bars(FadeIn(br), FadeIn(txt), FadeIn(meter), FadeIn(ml), bars=0.6)
        self.play_bars(GrowFromEdge(mfill, LEFT), gg[0].animate.set_stroke(C_ATT, 4), Flash(gg.get_corner(UR), color=C_ATT), bars=0.5)
        cite = T("Anthropic《Scaling Monosemanticity》（2024）", size=22, color=C_GREY).move_to([0, -1.6, 0])
        self.play_bars(FadeIn(cite), bars=0.5)
        # 97–98 调大
        self.at_bar(97)
        self.play_bars(FadeOut(VGroup(txt, meter, mfill, ml)), br.animate.scale(0.6).move_to([-4.8, 1.8, 0]), bars=0.25)
        track = Line([1.2, 0.8, 0], [6.0, 0.8, 0], color=C_GREY, stroke_width=4)
        knob = Dot([2.0, 0.8, 0], radius=0.16, color=C_ATT)
        tl = T("把这个特征调大", size=24, color=C_ATT).next_to(track, UP, buff=0.2)
        self.play_bars(gg.animate.next_to(tl, UP, buff=0.2), FadeIn(track), FadeIn(knob), FadeIn(tl), bars=0.25)
        self.play_bars(knob.animate.move_to([5.8, 0.8, 0]), bars=0.4)
        qb = bubble("你长什么样？", C_BLUE, size=24).move_to([-2.6, 0.7, 0])
        ab = bubble("我就像金门大桥：橙红色的塔，跨过海湾……", C_GREEN, size=22).move_to([-0.6, -0.4, 0])
        if ab.get_left()[0] < -6.8:
            ab.shift(RIGHT * (-6.8 - ab.get_left()[0]))
        self.play_bars(FadeIn(qb, shift=UP * 0.2), bars=0.35)
        self.play_bars(FadeIn(ab, shift=UP * 0.2), bars=0.5)
        dl = T("（问答为示意，依据该研究放大特征的演示）", size=20, color=C_GREY).next_to(cite, UP, buff=0.15)
        self.play_bars(FadeIn(dl), bars=0.25)
        # 99–100 安全，才刚开始
        self.at_bar(99)
        self.fade_rest(0.25)
        why = VGroup(T("要确认它按我们希望的方式工作", size=32, color=C_WHITE),
                     T("就得看懂它在算什么", size=32, color=C_GREEN, weight=BOLD)).arrange(DOWN, buff=0.2).move_to([0, 1.2, 0])
        pb = Rectangle(width=8.0, height=0.36, color=C_GREY, stroke_width=2).move_to([0, -0.4, 0])
        pf = Rectangle(width=0.7, height=0.36, stroke_width=0, fill_color=C_ATT, fill_opacity=0.9).align_to(pb, LEFT).set_y(-0.4)
        pl = T("看懂的部分：才刚开始（示意）", size=24, color=C_GREY).next_to(pb, DOWN, buff=0.25)
        self.play_bars(FadeIn(why, shift=UP * 0.2), bars=0.75)
        self.play_bars(Create(pb), GrowFromEdge(pf, LEFT), FadeIn(pl), bars=0.5)
        self.at_bar(100.5)
        self.fade_rest(0.5)

    # ------------------------------------------------------------ 尾声 111–124：正片回顾长镜头
    def outro(self):
        self.at_bar(111)
        self.tag("正片回顾")
        minis = recap_minis()
        counters = {0: "2", 1: "13,002", 4: "6.2 亿", 5: "586 亿", 6: "1750 亿"}
        n = len(minis)
        gap = 1.3
        slots = [np.array([(k - (n - 1) / 2) * gap, 2.45, 0]) for k in range(n)]
        thumbs = []
        cur = None
        for k, (g, anim) in enumerate(minis):
            if k:
                self.at_bar(111 + k)
            frame = RoundedRectangle(width=6.6, height=4.1, corner_radius=0.18, stroke_color=C_GREY, stroke_width=2.5,
                                     fill_color="#121621", fill_opacity=1)
            lab = T(f"第 {k + 1:02d} 集 · {EPS[k]}", size=26, color=C_GOLD if k == 9 else C_GREY).next_to(frame.get_top(), DOWN, buff=0.18)
            g.scale(1.2).move_to(frame.get_center() + DOWN * 0.22)
            panel = VGroup(frame, lab, g).move_to([0, -0.4, 0])
            anims = [FadeIn(panel, shift=LEFT * 0.6)]
            if cur is not None:
                anims.append(cur.animate.scale(0.165).move_to(slots[k - 1]))
            if k in counters:
                anims.append(Transform(self.counter, knob_counter(counters[k])))
            self.play_bars(*anims, bars=0.3)
            self.play_bars(anim(), bars=0.6 if k else 0.45)
            if cur is not None:
                thumbs.append(cur)
            cur = panel
        # 121–122 连成一条链，“霜”落下
        self.at_bar(121)
        self.play_bars(cur.animate.scale(0.165).move_to(slots[n - 1]), bars=0.3)
        thumbs.append(cur)
        chain = VGroup(*thumbs)
        arrs = VGroup(*[Arrow(thumbs[k].get_right(), thumbs[k + 1].get_left(), buff=0.02, color=C_GOLD, stroke_width=3,
                              max_tip_length_to_length_ratio=0.5) for k in range(n - 1)])
        self.play_bars(chain.animate.shift(DOWN * 1.1), bars=0.3)
        arrs.shift(DOWN * 1.1)
        self.play_bars(LaggedStart(*[GrowArrow(a) for a in arrs], lag_ratio=0.12), bars=0.6)
        frost = T("霜", size=110, color=C_GOLD, weight=BOLD).move_to(thumbs[6].get_center())
        frost.set_opacity(0)
        self.play_bars(frost.animate.set_opacity(1).move_to([0, -0.3, 0]), bars=0.4)
        msg = T("不是魔法，是可以被理解的数学", size=34, color=C_WHITE, weight=BOLD).move_to([0, -1.85, 0])
        self.play_bars(FadeIn(msg, shift=UP * 0.2), bars=0.4)
        # 123–124 黑箱最后一次打开
        self.at_bar(123)
        self.play_bars(FadeOut(VGroup(chain, arrs, msg)), frost.animate.scale(0.45).move_to([3.4, 0.2, 0]), bars=0.3)
        box = black_box(w=3.4, h=2.4, depth=0.5).move_to([0, 0.2, 0])
        q = T("床前明月光，疑是地上__", size=26, color=C_BLUE).move_to([-4.2, 0.2, 0])
        if q.get_right()[0] > box.get_left()[0] - 0.1:
            q.scale_to_fit_width(box.get_left()[0] - 0.1 + 6.8).move_to([(-6.8 + box.get_left()[0] - 0.1) / 2, 0.2, 0])
        self.play_bars(FadeIn(box), FadeIn(q), bars=0.3)
        inner = tower(3, w=1.8, h=0.45).move_to(box.front)
        self.play_bars(VGroup(box.front, box.q).animate.shift(UP * 0.3).set_opacity(0.12), FadeIn(inner), bars=0.5)
        slogan = T("一层一层，把黑箱打开", size=48, color=C_YELLOW, weight=BOLD).move_to([0, 2.5, 0])
        self.play_bars(Write(slogan), Indicate(frost, color=C_GOLD, scale_factor=1.3), bars=0.7)

    # ------------------------------------------------------------ 片尾 125–126：番外预告
    def tail(self):
        self.at_bar(125)
        self.fade_rest(0.25)
        head = T("番外预告", size=30, color=C_GREY)
        line = T("同样的旋钮和下山，还能看图、听声、画画", size=34, color=C_WHITE)
        cards = VGroup(card(["图片、声音也变成 token"], title="番外三 · 多模态", tcolor=C_BLUE, width=3.9, size=22),
                       card(["从噪声里画出一幅画"], title="番外四 · 扩散模型", tcolor=C_GOLD, width=3.9, size=22),
                       card(["认出 AI 写的字"], title="番外五 · 文本水印", tcolor=C_GREEN, width=3.9, size=22)).arrange(RIGHT, buff=0.35)
        g = VGroup(head, line, cards).arrange(DOWN, buff=0.4).move_to([0, 0.3, 0])
        if g.width > 13:
            g.scale_to_fit_width(13)
        self.play_bars(FadeIn(head), FadeIn(line, shift=UP * 0.2), bars=0.35)
        self.play_bars(LaggedStart(*[FadeIn(c, shift=UP * 0.2) for c in cards], lag_ratio=0.3), bars=0.6)
        self.at_bar(126.2)
        self.play_bars(*[FadeOut(m) for m in self.visible()], bars=0.8)
