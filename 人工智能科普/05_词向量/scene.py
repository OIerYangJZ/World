# -*- coding: utf-8 -*-
"""
第 05 集《词向量：把文字变成一串数字》

时间全部对齐 bars.py 的 BPM 小节网格（90 BPM，122 小节）。字幕由 build.py 烧录。
    ~/.venvs/manim/bin/python ../common/build.py 05_词向量 [--preview]

说明：画面中的切分方式、编号、向量数值、点云位置都是示意，不是某个真实模型的数据。
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "common"))
from style import *  # noqa: E402,F401
import digits  # noqa: E402


def _rgba(rgb):
    return np.dstack([rgb, np.full(rgb.shape[:2], 255, np.uint8)])


def pix_image(arr, height):
    img = ImageMobject(_rgba(digits.to_rgb(arr)))
    img.set_resampling_algorithm(RESAMPLING_ALGORITHMS["nearest"])
    img.scale_to_fit_height(height)
    return img


def token_block(text, color=C_BLUE, size=40, pad=0.18, fill=0.18):
    t = T(text, size=size, color=C_WHITE)
    r = RoundedRectangle(width=max(t.width + 2 * pad, 0.7), height=t.height + 2 * pad, corner_radius=0.1,
                         stroke_color=color, stroke_width=3, fill_color=color, fill_opacity=fill)
    return VGroup(r, t.move_to(r))


def val_color(v):
    """−1…1 → 蓝…暗…黄"""
    v = float(np.clip(v, -1, 1))
    if v >= 0:
        return interpolate_color(ManimColor("#1a1f2c"), ManimColor(C_YELLOW), v)
    return interpolate_color(ManimColor("#1a1f2c"), ManimColor(C_BLUE), -v)


def vector_strip(vals, cell=0.42, show_num=True, n_show=None, size=16):
    g = VGroup()
    n_show = n_show or len(vals)
    for v in vals[:n_show]:
        sq = Square(side_length=cell, stroke_color="#2a2f3d", stroke_width=1.5, fill_color=val_color(v), fill_opacity=1)
        if show_num:
            sq = VGroup(sq, T(f"{v:+.2f}".replace("-", "−"), size=size,
                              color=BLACK if abs(v) > 0.55 and v > 0 else C_WHITE).move_to(sq))
        g.add(sq)
    g.arrange(RIGHT, buff=0.03)
    return g


# ---------------------------------------------------------------- 词向量点云（三维示意坐标，z 朝上）
CLUSTERS = {
    "动物": (C_GOLD, np.array([1.8, -0.6, 0.9]), ["猫", "狗", "兔子", "马", "老虎"]),
    "食物": (C_GREEN, np.array([-1.8, 0.6, 0.6]), ["香蕉", "面包", "米饭", "葡萄"]),
    "城市": (C_BLUE, np.array([0.9, 1.5, -0.7]), ["北京", "巴黎", "东京", "罗马"]),
    "电器": (C_PURPLE, np.array([-1.0, -1.4, -1.0]), ["冰箱", "手机", "电脑", "电视"]),
}
_r = np.random.default_rng(13)
WORDS = []
for name, (col, c, ws) in CLUSTERS.items():
    for k, w in enumerate(ws):
        a = TAU * k / len(ws) + 0.4
        off = np.array([0.55 * np.cos(a), 0.0, 0.5 * np.sin(a)])   # 竖直平面里排一圈，投影后不重叠
        WORDS.append((w, col, c + off + _r.normal(0, 0.04, 3), name))
RAND_POS = [_r.uniform(-2, 2, 3) for _ in WORDS]


def proj3(p, th, el, center, s=1.25):
    x, y, z = p * s
    xr = x * np.cos(th) - y * np.sin(th)
    yr = x * np.sin(th) + y * np.cos(th)
    return center + np.array([xr, z * np.cos(el) + yr * np.sin(el), 0])


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

    # ------------------------------------------------------------ 点云
    def make_cloud(self, th, el=0.35, center=np.array([0, 0.25, 0]), mix=None, s=1.25, label_size=24):
        """th, mix 为 ValueTracker；mix=0 随机位置，1 训练后位置"""
        dots, labels = VGroup(), VGroup()
        for k, (w, col, pos, _) in enumerate(WORDS):
            def where(k=k, pos=pos):
                m = 1.0 if mix is None else mix.get_value()
                p = (1 - m) * RAND_POS[k] + m * pos
                return proj3(p, th.get_value(), el, center, s)
            d = Dot(where(), radius=0.09, color=col)
            d.add_updater(lambda mob, f=where: mob.move_to(f()))
            lab = T(w, size=label_size, color=col)
            lab.add_updater(lambda mob, d=d: mob.next_to(d, UR, buff=0.04))
            dots.add(d)
            labels.add(lab)
        return dots, labels

    # ------------------------------------------------------------ 前奏 1–4
    def intro(self):
        card = title_card("第 05 集", "词向量", "把文字变成一串数字")
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
        self.tag("回顾：图片 = 数字")
        img = pix_image(digits.digit(7), 2.6).move_to([-3.0, 0.4, 0])
        arr = digits.digit(7)
        col = VGroup(*[T(f"{arr[r_, c_]:.1f}", size=22, color=C_BLUE) for r_, c_ in [(6, 8), (6, 12), (6, 16), (10, 17), (14, 15), (18, 13)]])
        col.add(T("⋮", size=26, color=C_GREY))
        col.arrange(DOWN, buff=0.14).move_to([1.2, 0.4, 0])
        ar = Arrow(img.get_right(), col.get_left(), buff=0.3, color=C_GREY)
        self.play_bars(FadeIn(img), bars=0.5)
        self.play_bars(GrowArrow(ar), FadeIn(col, shift=RIGHT * 0.2), bars=0.75)
        self.at_bar(6.75)
        self.play_bars(FadeOut(img), FadeOut(col), FadeOut(ar), bars=0.25)
        # 7–8 文字？
        self.at_bar(7)
        self.tag("文字怎么变成数字？")
        sent = VGroup(*[T(c, size=80, color=C_WHITE) for c in "床前明月光"]).arrange(RIGHT, buff=0.08).move_to([0, 0.9, 0])
        q = T("文字 → 数字？", size=36, color=C_GOLD).next_to(sent, DOWN, buff=0.7)
        self.play_bars(Write(sent), bars=1)
        self.play_bars(FadeIn(q), bars=0.5)
        # 9–10 切开
        self.at_bar(9)
        self.tag("第一步：切成 token")
        pieces = ["床", "前", "明月", "光"]
        blocks = VGroup(*[token_block(p, size=56) for p in pieces]).arrange(RIGHT, buff=0.35).move_to([0, 0.9, 0])
        cuts = VGroup(*[Line(UP * 0.8 + RIGHT * 0.2, DOWN * 0.8 + LEFT * 0.2, color=C_WHITE, stroke_width=4)
                        .move_to(sent[i].get_right() + RIGHT * 0.04) for i in (0, 1, 3)])
        self.play_bars(FadeOut(q), LaggedStart(*[Create(c) for c in cuts], lag_ratio=0.25), bars=0.75)
        self.play_bars(FadeOut(cuts), ReplacementTransform(sent[0], blocks[0][1]), ReplacementTransform(sent[1], blocks[1][1]),
                       ReplacementTransform(VGroup(sent[2], sent[3]), blocks[2][1]), ReplacementTransform(sent[4], blocks[3][1]),
                       *[FadeIn(b[0]) for b in blocks], bars=0.75)
        demo = T("（示意切法：不同模型切法不同）", size=22, color=C_GREY).next_to(blocks, DOWN, buff=0.35)
        self.play_bars(FadeIn(demo), bars=0.25)
        # 11–12 token（词元）
        self.at_bar(11)
        br = Brace(blocks, UP, color=C_BLUE)
        bt = VGroup(T("token", size=36, color=C_BLUE, weight=BOLD), T("（中文常译“词元”）", size=26, color=C_GREY)).arrange(RIGHT, buff=0.2)
        bt.next_to(br, UP, buff=0.15)
        self.play_bars(GrowFromCenter(br), FadeIn(bt), bars=1)
        self.v1_blocks = VGroup(blocks, br, bt, demo)
        # 13–14 常见词各占一个 token
        self.at_bar(13)
        self.play_bars(self.v1_blocks.animate.scale(0.7).move_to([0, 2.2, 0]), bars=0.5)
        common = VGroup(*[token_block(w, color=C_TEAL, size=40) for w in ["我们", "的", "今天", "天气"]]).arrange(RIGHT, buff=0.3)
        cl = T("常见的字词：往往一个 token", size=26, color=C_TEAL)
        cg = VGroup(cl, common).arrange(DOWN, buff=0.3).move_to([-3.4, -0.3, 0])
        self.play_bars(FadeIn(cl), LaggedStart(*[FadeIn(b, scale=0.8) for b in common], lag_ratio=0.2), bars=1)
        # 15–16 生僻字拆成小片段
        self.at_bar(15)
        rare = VGroup(token_block("龘", color=C_ORANGE, size=40))
        bytes_ = VGroup(*[token_block(f"片段{i}", color=C_ORANGE, size=22) for i in "①②③"]).arrange(RIGHT, buff=0.12)
        eng = VGroup(*[token_block(p, color=C_ORANGE, size=28) for p in ["un", "believ", "ably"]]).arrange(RIGHT, buff=0.1)
        rl = T("生僻字、长单词：拆成几段（示意）", size=26, color=C_ORANGE)
        r1 = VGroup(rare, Arrow(LEFT * 0.3, RIGHT * 0.3, color=C_GREY, buff=0), bytes_).arrange(RIGHT, buff=0.2)
        r2 = VGroup(T("unbelievably", size=30, color=C_WHITE), Arrow(LEFT * 0.3, RIGHT * 0.3, color=C_GREY, buff=0), eng).arrange(RIGHT, buff=0.2)
        rg = VGroup(rl, r1, r2).arrange(DOWN, buff=0.3).move_to([3.4, -0.3, 0])
        self.play_bars(FadeIn(rl), FadeIn(r1), bars=0.75)
        self.play_bars(FadeIn(r2), bars=0.75)
        self.at_bar(16.75)
        self.play_bars(FadeOut(cg), FadeOut(rg), bars=0.25)
        # 17–18 编号
        self.at_bar(17)
        self.play_bars(self.v1_blocks.animate.scale(1 / 0.7).move_to([0, 0.9, 0]), bars=0.5)
        ids = ["30586", "14581", "51003", "8723"]
        idt = VGroup(*[T(f"#{i}", size=28, color=C_GOLD).next_to(b, DOWN, buff=0.25) for i, b in zip(ids, blocks)])
        self.play_bars(LaggedStart(*[FadeIn(t, shift=UP * 0.2) for t in idt], lag_ratio=0.2), demo.animate.shift(DOWN * 0.55), bars=0.75)
        idn = T("每个 token 一个编号（编号为示意）", size=24, color=C_GOLD).next_to(demo, DOWN, buff=0.15)
        self.play_bars(FadeIn(idn), bars=0.5)
        # 19–20 词表大小
        self.at_bar(19)
        self.play_bars(FadeOut(VGroup(self.v1_blocks, idt, idn)), bars=0.25)
        bar = Rectangle(width=10, height=0.5, stroke_color=C_GREY, stroke_width=2).move_to([0, 0.5, 0])
        fill = Rectangle(width=10, height=0.42, stroke_width=0, fill_color=C_BLUE, fill_opacity=0.25).move_to(bar)
        ticks = VGroup()
        for v in (0, 50000, 100000, 150000, 200000, 250000):
            x = bar.get_left()[0] + 10 * v / 250000
            ticks.add(VGroup(Line([x, 0.2, 0], [x, 0.25, 0], color=C_GREY),
                             T(f"{v // 10000} 万" if v else "0", size=20, color=C_GREY).move_to([x, -0.05, 0])))
        x2 = bar.get_left()[0] + 10 * 50257 / 250000
        mark = VGroup(Line([x2, 0.8, 0], [x2, 0.2, 0], color=C_GOLD, stroke_width=4),
                      T("GPT-2：50,257", size=26, color=C_GOLD).move_to([x2, 1.1, 0]))
        rng_ = Rectangle(width=10 * (220000 - 30000) / 250000, height=0.42, stroke_width=0, fill_color=C_BLUE,
                         fill_opacity=0.55).move_to(bar).align_to(bar, LEFT).shift(RIGHT * 10 * 30000 / 250000)
        lab = T("词表大小：常见几万 ～ 二十多万", size=28, color=C_BLUE).move_to([0, 1.9, 0])
        self.play_bars(Create(bar), FadeIn(fill), FadeIn(ticks), FadeIn(lab), FadeIn(rng_), bars=0.75)
        self.play_bars(FadeIn(mark, shift=DOWN * 0.2), bars=0.5)
        self.at_bar(20.5)
        self.fade_rest(0.5)

    # ------------------------------------------------------------ 副歌
    def hook(self, s):
        self.at_bar(s)
        self.tag("词向量")
        blk = token_block("猫", color=C_GOLD, size=52).move_to([-4.6, 0.4, 0])
        vals = np.random.default_rng(s).uniform(-1, 1, 10)
        strip = vector_strip(vals, cell=0.62, size=17).move_to([1.2, 0.4, 0])
        dots_ = T("…", size=40, color=C_GREY).next_to(strip, RIGHT, buff=0.15)
        self.play_bars(FadeIn(blk, scale=0.8), bars=0.5)
        self.play_bars(TransformFromCopy(blk, strip), FadeIn(dots_), bars=1)
        # ② 住在一旁
        self.at_bar(s + 2)
        self.play_bars(FadeOut(VGroup(blk, strip, dots_)), bars=0.25)
        pts = {"猫": ([-1.0, 0.8], C_GOLD), "狗": ([-0.4, 1.1], C_GOLD), "冰箱": ([3.6, -1.2], C_PURPLE),
               "香蕉": ([-3.8, -1.0], C_GREEN), "北京": ([2.8, 1.6], C_BLUE)}
        pd = VGroup()
        for w, (xy, col) in pts.items():
            d = Dot([xy[0], xy[1], 0], radius=0.11, color=col)
            pd.add(VGroup(d, T(w, size=28, color=col).next_to(d, UL if w == "猫" else UR, buff=0.05)))
        self.play_bars(LaggedStart(*[FadeIn(p, scale=1.5) for p in pd], lag_ratio=0.15), bars=0.75)
        near = Ellipse(width=1.9, height=1.2, color=C_GOLD, stroke_width=2.5).move_to([-0.6, 1.05, 0])
        self.play_bars(Create(near), bars=0.5)
        # ③ 平行四边形
        self.at_bar(s + 4)
        self.play_bars(FadeOut(pd), FadeOut(near), bars=0.25)
        P = {"男人": np.array([-3.0, -1.2, 0]), "女人": np.array([-0.8, -0.5, 0]),
             "国王": np.array([-2.6, 1.1, 0]), "女王": np.array([-0.35, 1.9, 0])}
        pg = VGroup()
        for w, p in P.items():
            d = Dot(p, radius=0.1, color=C_WHITE)
            pg.add(VGroup(d, T(w, size=28, color=C_WHITE).next_to(d, LEFT if w in ("男人", "国王") else RIGHT, buff=0.12)))
        a1 = Arrow(P["男人"], P["女人"], buff=0.12, color=C_ORANGE, stroke_width=5)
        a2 = Arrow(P["国王"], P["女王"], buff=0.12, color=C_ORANGE, stroke_width=5)
        self.play_bars(FadeIn(pg), GrowArrow(a1), bars=0.75)
        self.play_bars(GrowArrow(a2), bars=0.75)
        # ④ 数字里装着词的模样
        self.at_bar(s + 6)
        self.play_bars(FadeOut(VGroup(pg, a1, a2)), bars=0.25)
        rows = VGroup()
        r_ = np.random.default_rng(s + 3)
        for w in ["猫", "狗", "冰箱"]:
            base = r_.uniform(-1, 1, 16) if w != "狗" else rows[0][1].vals + r_.normal(0, 0.15, 16)
            st = vector_strip(base, cell=0.42, show_num=False)
            st.vals = base
            rows.add(VGroup(T(w, size=28, color=C_WHITE).next_to(st, LEFT, buff=0.3), st))
        rows.arrange(DOWN, buff=0.3, aligned_edge=RIGHT).move_to([0.3, 0.4, 0])
        self.play_bars(LaggedStart(*[FadeIn(r) for r in rows], lag_ratio=0.25), bars=1)
        simi = T("猫和狗的数字很像", size=24, color=C_GOLD).next_to(rows, DOWN, buff=0.3)
        self.play_bars(FadeIn(simi), bars=0.5)
        # ⑤ 黑箱
        self.at_bar(s + 8)
        self.fade_rest(0.25)
        box = black_box(w=3.2, h=2.2, depth=0.45).move_to([0, 0.2, 0])
        inner = VGroup(*[Dot(box.front.get_center() + np.array([x, y, 0]), radius=0.05, color=c)
                         for (x, y, c) in [(-0.8, 0.4, C_GOLD), (-0.6, 0.5, C_GOLD), (-0.7, 0.25, C_GOLD),
                                           (0.6, -0.3, C_GREEN), (0.8, -0.4, C_GREEN), (0.1, 0.5, C_BLUE),
                                           (0.3, 0.6, C_BLUE), (-0.2, -0.5, C_PURPLE), (0.0, -0.6, C_PURPLE)]])
        self.play_bars(FadeIn(box), bars=0.25)
        self.play_bars(VGroup(box.front, box.q).animate.shift(UP * 0.3).set_opacity(0.12), FadeIn(inner), bars=0.5)
        slogan = T("一层一层，把黑箱打开", size=40, color=C_YELLOW, weight=BOLD).to_edge(UP, buff=0.3)
        self.play_bars(Write(slogan), bars=0.5)
        self.at_bar(s + 9.5)
        self.fade_rest(0.5)

    # ------------------------------------------------------------ 主歌二 31–46
    def verse2(self):
        self.at_bar(31)
        self.tag("编号没有“意思”")
        a = VGroup(T("#1873", size=34, color=C_GOLD), T("→", size=34, color=C_GREY), token_block("苹果", size=36)).arrange(RIGHT, buff=0.3)
        b = VGroup(T("#1874", size=34, color=C_GOLD), T("→", size=34, color=C_GREY), token_block("引擎", size=36)).arrange(RIGHT, buff=0.3)
        ab = VGroup(a, b).arrange(DOWN, buff=0.4).move_to([0, 0.6, 0])
        nt = T("编号挨着，意思毫不相干（示意）", size=26, color=C_GREY).next_to(ab, DOWN, buff=0.4)
        self.play_bars(FadeIn(a), FadeIn(b), bars=0.75)
        self.play_bars(FadeIn(nt), bars=0.5)
        # 33–34 配一串数字
        self.at_bar(33)
        self.tag("向量")
        self.play_bars(FadeOut(VGroup(ab, nt)), bars=0.25)
        blk = token_block("猫", color=C_GOLD, size=48).move_to([-5.0, 0.6, 0])
        vals = np.array([0.12, -0.83, 0.45, 0.67, -0.21, 0.9, -0.55, 0.03])
        strip = vector_strip(vals, cell=0.7, size=19).next_to(blk, RIGHT, buff=0.6)
        more = T("…", size=40, color=C_GREY).next_to(strip, RIGHT, buff=0.12)
        vl = T("向量 = 一串数字", size=30, color=C_YELLOW).next_to(strip, DOWN, buff=0.35)
        self.play_bars(FadeIn(blk), bars=0.25)
        self.play_bars(TransformFromCopy(blk, strip), FadeIn(more), FadeIn(vl), bars=1)
        # 35–36 一个点、一支箭
        self.at_bar(35)
        self.play_bars(FadeOut(VGroup(blk, strip, more, vl)), bars=0.25)
        th = ValueTracker(-0.5)
        cen = np.array([-2.6, -0.6, 0])

        def axes3():
            g = VGroup()
            for d, c, n in ((np.array([1, 0, 0]), C_GREY, "数1"), (np.array([0, 1, 0]), C_GREY, "数2"), (np.array([0, 0, 1]), C_GREY, "数3")):
                p0, p1 = proj3(np.zeros(3), th.get_value(), 0.35, cen, 1.6), proj3(d * 1.6, th.get_value(), 0.35, cen, 1.6)
                g.add(Arrow(p0, p1, buff=0, color=c, stroke_width=3, max_tip_length_to_length_ratio=0.08))
            return g

        ax3 = always_redraw(axes3)
        vec = np.array([1.0, 0.7, 1.1])
        pt = always_redraw(lambda: Dot(proj3(vec, th.get_value(), 0.35, cen, 1.6), radius=0.12, color=C_GOLD))
        ar = always_redraw(lambda: Arrow(proj3(np.zeros(3), th.get_value(), 0.35, cen, 1.6),
                                         proj3(vec, th.get_value(), 0.35, cen, 1.6), buff=0.1, color=C_GOLD, stroke_width=5))
        lab = T("(1.0, 0.7, 1.1)：三个数 = 三维空间里的一个点", size=26, color=C_GOLD).move_to([3.0, 1.2, 0])
        lab2 = T("一万多个数 = 一万多维空间里的一个点", size=24, color=C_GREY).next_to(lab, DOWN, buff=0.25)
        self.play_bars(FadeIn(ax3), FadeIn(pt), Create(ar), FadeIn(lab), bars=0.75)
        self.play_bars(th.animate.set_value(0.3), FadeIn(lab2), bars=0.75)
        # 37–38 12,288 个数
        self.at_bar(37)
        self.play_bars(FadeOut(VGroup(ax3, pt, ar, lab, lab2)), bars=0.25)
        long_vals = np.random.default_rng(3).uniform(-1, 1, 60)
        ls = vector_strip(long_vals, cell=0.2, show_num=False).move_to([0, 0.6, 0])
        blk2 = token_block("猫", color=C_GOLD, size=40).next_to(ls, UP, buff=0.4).align_to(ls, LEFT)
        self.play_bars(FadeIn(blk2), LaggedStart(*[FadeIn(c) for c in ls], lag_ratio=0.02), bars=0.75)
        g3 = T("GPT-3：每个 token 有 12,288 个数", size=34, color=C_YELLOW).next_to(ls, DOWN, buff=0.5)
        g3n = T("（这里只画了 60 个；12,288 是 GPT-3 的维度，不同模型不一样）", size=22, color=C_GREY).next_to(g3, DOWN, buff=0.15)
        self.play_bars(FadeIn(g3), FadeIn(g3n), bars=0.75)
        # 39–40 嵌入表
        self.at_bar(39)
        self.tag("嵌入表")
        self.play_bars(FadeOut(VGroup(ls, blk2, g3, g3n)), bars=0.25)
        names = ["猫", "狗", "床", "前", "明月", "光", "苹果", "⋮"]
        rr = np.random.default_rng(5)
        table = VGroup()
        self.table_vals = []
        for nm in names:
            if nm == "⋮":
                row = VGroup(T("⋮", size=28, color=C_GREY), T("⋮", size=28, color=C_GREY))
            else:
                v = rr.uniform(-1, 1, 22)
                self.table_vals.append(v)
                row = VGroup(T(nm, size=26, color=C_WHITE), vector_strip(v, cell=0.27, show_num=False))
            table.add(row)
        for row in table:
            row.arrange(RIGHT, buff=0.3)
        table.arrange(DOWN, buff=0.08, aligned_edge=LEFT).move_to([-1.6, 0.35, 0])
        for row in table[:-1]:
            row[0].move_to([table.get_left()[0] + 0.45, row[0].get_y(), 0])
        self.table = table
        hdr = T("嵌入表：每行是一个 token 的向量", size=28, color=C_YELLOW).next_to(table, UP, buff=0.25)
        self.play_bars(FadeIn(table), FadeIn(hdr), bars=0.75)
        hl = SurroundingRectangle(table[0], color=C_GOLD, buff=0.06)
        look = T("查表：取出“猫”那一行", size=24, color=C_GOLD).next_to(table, RIGHT, buff=0.3)
        knob_t = T("每个数都是旋钮", size=24, color=C_YELLOW).next_to(look, DOWN, buff=0.3).align_to(look, LEFT)
        self.play_bars(Create(hl), FadeIn(look), FadeIn(knob_t), bars=0.75)
        # 41–42 六亿多个旋钮
        self.at_bar(41)
        self.play_bars(FadeOut(hl), FadeOut(look), FadeOut(knob_t), FadeOut(hdr),
                       table.animate.scale(0.7).move_to([-3.4, 0.35, 0]), bars=0.25)
        eq = VGroup(T("GPT-3 的嵌入表", size=28, color=C_WHITE),
                    T("50,257 行 × 12,288 列", size=30, color=C_YELLOW),
                    T("≈ 6.2 亿个数（旋钮）", size=30, color=C_YELLOW)).arrange(DOWN, buff=0.15)
        eq.move_to([3.4, 0.35, 0])
        self.play_bars(FadeIn(eq), bars=0.5)
        self.set_counter("6.2 亿", bars=0.75)
        # 43–44 只占 1750 亿的一小块
        self.at_bar(43)
        self.play_bars(FadeOut(VGroup(table, eq)), bars=0.25)
        whole = Rectangle(width=11, height=0.7, stroke_color=C_GREY, stroke_width=2, fill_color=C_GREY, fill_opacity=0.15).move_to([0, 0.4, 0])
        wl = T("GPT-3 全部旋钮：1750 亿", size=28, color=C_GREY).next_to(whole, UP, buff=0.25)
        sliver = Rectangle(width=11 * 0.00353, height=0.7, stroke_width=0, fill_color=C_YELLOW, fill_opacity=1).align_to(whole, LEFT).set_y(0.4)
        mag = Circle(radius=0.45, color=C_YELLOW, stroke_width=3).move_to(sliver)
        sl = T("嵌入表约 6.2 亿：约 0.35%", size=26, color=C_YELLOW).next_to(whole, DOWN, buff=0.45).align_to(whole, LEFT)
        self.play_bars(FadeIn(whole), FadeIn(wl), bars=0.5)
        self.play_bars(FadeIn(sliver), Create(mag), FadeIn(sl), bars=0.75)
        # 45–46 随机 → 训练
        self.at_bar(45)
        self.play_bars(FadeOut(VGroup(whole, wl, sliver, mag, sl)), bars=0.25)
        rr2 = np.random.default_rng(8)
        grid = VGroup(*[Square(side_length=0.3, stroke_color="#2a2f3d", stroke_width=1, fill_color=val_color(rr2.uniform(-1, 1)),
                               fill_opacity=1) for _ in range(8 * 24)]).arrange_in_grid(rows=8, cols=24, buff=0.03).move_to([0, 0.5, 0])
        gl = T("一开始：随机数", size=28, color=C_GREY).next_to(grid, UP, buff=0.25)
        self.play_bars(FadeIn(grid), FadeIn(gl), bars=0.5)
        protos = [rr2.uniform(-1, 1, 24) for _ in range(3)]
        tgt = []
        for i in range(8):
            p = protos[i % 3]
            for j in range(24):
                tgt.append(val_color(p[j] + rr2.normal(0, 0.15)))
        gl2 = T("训练中：一点点调好（示意）", size=28, color=C_YELLOW).move_to(gl)
        self.play_bars(*[sq.animate.set_fill(c) for sq, c in zip(grid, tgt)], Transform(gl, gl2), bars=1)
        self.at_bar(46.75)
        self.fade_rest(0.25)

    # ------------------------------------------------------------ 间奏一 47–50：点云成团
    def inst1(self):
        self.at_bar(47)
        self.tag("训练让意思相近的词靠近（示意）")
        th = ValueTracker(-0.6)
        mix = ValueTracker(0.0)
        dots, labels = self.make_cloud(th, mix=mix)
        self.play_bars(FadeIn(dots), FadeIn(labels), bars=0.5)
        self.play_bars(mix.animate.set_value(1.0), th.animate.set_value(0.2), bars=2.0)
        self.play_bars(th.animate.set_value(0.5), bars=0.75)
        for m in list(dots) + list(labels):
            m.clear_updaters()
        self.fade_rest(0.5)

    # ------------------------------------------------------------ 主歌三 61–76
    def verse3(self):
        self.at_bar(61)
        self.tag("意思相近，住得近")
        th = ValueTracker(0.0)
        dots, labels = self.make_cloud(th)
        note = T("（示意：真实向量有上千维，这里画成三维）", size=20, color=C_GREY).move_to([0, 2.95, 0])
        self.play_bars(FadeIn(dots), FadeIn(labels), FadeIn(note), bars=0.75)
        self.play_bars(th.animate.set_value(0.45), bars=1.0)
        for m in list(dots) + list(labels):
            m.clear_updaters()
        idx = {w: i for i, (w, *_r2) in enumerate(WORDS)}
        # 63–64 猫—狗 近，猫—冰箱 远
        self.at_bar(63)
        cat, dog, fr = dots[idx["猫"]], dots[idx["狗"]], dots[idx["冰箱"]]
        l1 = Line(cat.get_center(), dog.get_center(), color=C_GOLD, stroke_width=4)
        l2 = DashedLine(cat.get_center(), fr.get_center(), color=C_GREY, stroke_width=3)
        t1 = T("金线：猫—狗，近", size=26, color=C_GOLD).move_to([4.9, 0.6, 0])
        t2 = T("灰线：猫—冰箱，远", size=26, color=C_GREY).move_to([4.9, 0.0, 0])
        self.play_bars(Create(l1), FadeIn(t1), bars=0.75)
        self.play_bars(Create(l2), FadeIn(t2), bars=0.75)
        # 65–66 各成一团
        self.at_bar(65)
        self.play_bars(FadeOut(VGroup(l1, l2, t1, t2)), bars=0.25)
        blobs = VGroup()
        for name, (col, c, ws) in CLUSTERS.items():
            members = VGroup(*[dots[idx[w]] for w in ws])
            e = Ellipse(width=members.width + 1.0, height=members.height + 0.8, color=col, stroke_width=2.5,
                        fill_color=col, fill_opacity=0.08).move_to(members)
            side = {"动物": DOWN, "食物": UP, "城市": UP, "电器": LEFT}[name]
            gl = T(name, size=30, color=col, weight=BOLD).next_to(e, side, buff=0.08)
            if name == "城市":
                gl.move_to(e.get_corner(DR) + np.array([0.45, 0.1, 0]))
            blobs.add(VGroup(e, gl))
        self.play_bars(LaggedStart(*[FadeIn(b) for b in blobs], lag_ratio=0.2), bars=1.25)
        self.at_bar(66.75)
        self.fade_rest(0.25)
        # 67–68 差 = 一支箭
        self.at_bar(67)
        self.tag("关系 = 方向")
        P = {"男人": np.array([-5.2, -1.4, 0]), "女人": np.array([-2.9, -0.6, 0]),
             "国王": np.array([-4.8, 1.0, 0]), "女王": np.array([-2.35, 1.95, 0])}
        Q = {"法国": np.array([1.4, -0.9, 0]), "意大利": np.array([4.0, -0.5, 0]),
             "巴黎": np.array([1.2, 1.2, 0]), "罗马": np.array([3.65, 1.75, 0])}
        allp = {**P, **Q}
        mk = {}
        for w, p in allp.items():
            d = Dot(p, radius=0.1, color=C_WHITE)
            side = LEFT if w in ("男人", "国王", "法国", "巴黎") else RIGHT
            mk[w] = VGroup(d, T(w, size=28, color=C_WHITE).next_to(d, side, buff=0.12))
        self.play_bars(FadeIn(mk["男人"]), FadeIn(mk["女人"]), bars=0.5)
        a1 = Arrow(P["男人"], P["女人"], buff=0.12, color=C_ORANGE, stroke_width=5)
        al = T("差 = 一支箭", size=24, color=C_ORANGE).next_to(a1, DOWN, buff=0.1)
        self.play_bars(GrowArrow(a1), FadeIn(al), bars=0.75)
        # 69–70 国王 → 女王 平行
        self.at_bar(69)
        self.play_bars(FadeIn(mk["国王"]), FadeIn(mk["女王"]), bars=0.5)
        a2 = Arrow(P["国王"], P["女王"], buff=0.12, color=C_ORANGE, stroke_width=5)
        side1 = DashedLine(P["男人"], P["国王"], color=C_GREY, stroke_width=2)
        side2 = DashedLine(P["女人"], P["女王"], color=C_GREY, stroke_width=2)
        self.play_bars(GrowArrow(a2), Create(side1), Create(side2), bars=0.75)
        par = T("几乎平行", size=24, color=C_ORANGE).next_to(a2, UP, buff=0.1)
        self.play_bars(FadeIn(par), bars=0.25)
        # 71–72 国王 − 男人 + 女人 → 接近女王
        self.at_bar(71)
        res = P["国王"] - P["男人"] + P["女人"]
        moving = Dot(P["国王"], radius=0.12, color=C_GOLD)
        self.play_bars(FadeIn(moving, scale=1.5), FadeOut(al), bars=0.25)
        self.play_bars(moving.animate.move_to(res), bars=0.75)
        star = Star(n=5, outer_radius=0.16, color=C_GOLD, fill_opacity=1).move_to(res)
        ring = Circle(radius=0.55, color=C_GOLD, stroke_width=2.5).move_to((res + P["女王"]) / 2)
        cl = T("国王 − 男人 + 女人 → 最接近：女王", size=24, color=C_GOLD).move_to([-3.6, 2.75, 0])
        self.play_bars(Transform(moving, star), Create(ring), FadeIn(cl), bars=0.5)
        # 73–74 巴黎 − 法国 + 意大利 → 罗马
        self.at_bar(73)
        self.play_bars(*[FadeIn(mk[w]) for w in Q], bars=0.5)
        b1 = Arrow(Q["法国"], Q["意大利"], buff=0.12, color=C_TEAL, stroke_width=5)
        b2 = Arrow(Q["巴黎"], Q["罗马"], buff=0.12, color=C_TEAL, stroke_width=5)
        res2 = Q["巴黎"] - Q["法国"] + Q["意大利"]
        star2 = Star(n=5, outer_radius=0.16, color=C_TEAL, fill_opacity=1).move_to(res2)
        cl2 = T("巴黎 − 法国 + 意大利 → 罗马旁边", size=24, color=C_TEAL).move_to([2.4, 2.75, 0])
        self.play_bars(GrowArrow(b1), GrowArrow(b2), bars=0.5)
        self.play_bars(FadeIn(star2, scale=1.5), FadeIn(cl2), bars=0.75)
        # 75–76 注释
        self.at_bar(75)
        card = VGroup(T("经典实验：word2vec 词向量（Mikolov 等，2013）", size=22, color=C_WHITE),
                      T("找“最接近的词”时，通常把输入的几个词排除在外", size=20, color=C_GREY),
                      T("不是每个类比都成立；大模型里也不是精确成立", size=20, color=C_GREY)).arrange(DOWN, buff=0.1)
        bg = SurroundingRectangle(card, color=C_GREY, buff=0.16, corner_radius=0.1, fill_color=BG, fill_opacity=0.95)
        VGroup(bg, card).move_to([-0.4, -2.2, 0])
        self.play_bars(FadeIn(bg), FadeIn(card), bars=0.75)
        self.at_bar(76.5)
        self.fade_rest(0.5)

    # ------------------------------------------------------------ 桥段 77–84
    def bridge(self):
        self.at_bar(77)
        self.tag("意思 → 位置，关系 → 方向")
        rr = np.random.default_rng(17)
        words = ["猫", "狗", "马", "香蕉", "面包", "北京", "巴黎", "东京", "冰箱", "手机", "国王", "女王", "男人", "女人"]
        txt = VGroup()
        for w in words:
            txt.add(T(w, size=34, color=C_WHITE).move_to([rr.uniform(-5.5, 5.5), rr.uniform(-1.8, 2.4), 0]))
        self.play_bars(LaggedStart(*[FadeIn(t) for t in txt], lag_ratio=0.06), bars=1.25)
        dts = VGroup(*[Dot(t.get_center(), radius=0.1, color=C_GOLD) for t in txt])
        big1 = T("意思 → 位置", size=48, color=C_GOLD, weight=BOLD).move_to([0, 2.8, 0])
        self.play_bars(*[ReplacementTransform(t, d) for t, d in zip(txt, dts)], FadeIn(big1), bars=1.5)
        self.at_bar(81)
        pairs = [(12, 13), (10, 11), (0, 1), (5, 6)]
        off = np.array([1.4, 0.6, 0])
        arrows = VGroup()
        for (i, j) in pairs:
            tgt = dts[i].get_center() + off
            arrows.add(Arrow(dts[i].get_center(), tgt, buff=0.1, color=C_ORANGE, stroke_width=5))
        big2 = T("关系 → 方向", size=48, color=C_ORANGE, weight=BOLD).move_to([0, 2.8, 0])
        self.play_bars(Transform(big1, big2), *[dts[j].animate.move_to(dts[i].get_center() + off) for i, j in pairs], bars=0.75)
        self.play_bars(LaggedStart(*[GrowArrow(a) for a in arrows], lag_ratio=0.25), bars=2.25)
        self.fade_rest(0.5)

    # ------------------------------------------------------------ 主歌四 85–100
    def verse4(self):
        self.at_bar(85)
        self.tag("一词多义")
        apple = token_block("苹果", color=C_RED, size=56).move_to([0, 0.8, 0])
        q = T("指哪个？", size=34, color=C_GREY).next_to(apple, DOWN, buff=0.4)
        self.play_bars(FadeIn(apple, scale=0.8), bars=0.5)
        self.play_bars(FadeIn(q), bars=0.5)
        # 87–88 两句话
        self.at_bar(87)
        s1 = T("削个苹果", size=40, color=C_WHITE).move_to([-3.8, 1.6, 0])
        s2 = T("苹果手机", size=40, color=C_WHITE).move_to([3.8, 1.6, 0])
        fruit = VGroup(Circle(radius=0.45, color=C_RED, fill_opacity=0.5), Line([0, 0.45, 0], [0.1, 0.7, 0], color=C_GREEN, stroke_width=4)
                       ).next_to(s1, DOWN, buff=0.35)
        phone = VGroup(RoundedRectangle(width=0.6, height=1.0, corner_radius=0.1, color=C_PURPLE, fill_opacity=0.3),
                       Dot(radius=0.04, color=C_PURPLE).shift(DOWN * 0.38)).next_to(s2, DOWN, buff=0.3)
        self.play_bars(FadeOut(q), apple.animate.scale(0.7).move_to([0, 2.3, 0]), FadeIn(s1), FadeIn(s2), bars=0.75)
        self.play_bars(FadeIn(fruit), FadeIn(phone), bars=0.75)
        # 89–90 同一个向量
        self.at_bar(89)
        food_c = np.array([-3.8, -1.2, 0])
        tech_c = np.array([3.8, -1.2, 0])
        fb = VGroup(Ellipse(width=2.6, height=1.3, color=C_GREEN, fill_opacity=0.08).move_to(food_c),
                    T("食物", size=24, color=C_GREEN).move_to(food_c + DOWN * 0.85))
        tb = VGroup(Ellipse(width=2.6, height=1.3, color=C_PURPLE, fill_opacity=0.08).move_to(tech_c),
                    T("电器 / 科技", size=24, color=C_PURPLE).move_to(tech_c + DOWN * 0.85))
        pt = Dot([0, -0.9, 0], radius=0.13, color=C_RED)
        pl = T("同一个向量", size=26, color=C_RED).next_to(pt, DOWN, buff=0.15)
        l1 = Arrow(s1.get_bottom() + DOWN * 1.1, pt.get_center(), buff=0.15, color=C_GREY, stroke_width=3)
        l2 = Arrow(s2.get_bottom() + DOWN * 1.1, pt.get_center(), buff=0.15, color=C_GREY, stroke_width=3)
        self.play_bars(FadeIn(fb), FadeIn(tb), FadeIn(pt), bars=0.5)
        self.play_bars(GrowArrow(l1), GrowArrow(l2), FadeIn(pl), bars=0.75)
        # 91–92 被两边拉
        self.at_bar(91)
        p1 = Arrow(pt.get_center(), food_c + RIGHT * 1.0, buff=0.15, color=C_GREEN, stroke_width=5)
        p2 = Arrow(pt.get_center(), tech_c + LEFT * 1.0, buff=0.15, color=C_PURPLE, stroke_width=5)
        self.play_bars(GrowArrow(p1), GrowArrow(p2), bars=0.75)
        self.play_bars(Wiggle(pt, scale_value=1.4), bars=0.75)
        # 93–94 看上下文
        self.at_bar(93)
        self.fade_rest(0.25)
        sent = VGroup(*[T(c, size=56, color=C_WHITE) for c in ["我", "削", "了", "个", "苹", "果"]]).arrange(RIGHT, buff=0.1).move_to([0, 0.4, 0])
        ap = VGroup(sent[4], sent[5])
        box = SurroundingRectangle(ap, color=C_RED, buff=0.08)
        arcs = VGroup(*[CurvedArrow(ap.get_top() + UP * 0.05, sent[i].get_top() + UP * 0.05, angle=0.9, color=C_PURPLE,
                                    stroke_width=3, tip_length=0.15) for i in (0, 1, 3)])
        ctx = T("看看上下文：下集“注意力”", size=28, color=C_PURPLE).next_to(sent, DOWN, buff=0.6)
        self.play_bars(FadeIn(sent), Create(box), bars=0.5)
        self.play_bars(LaggedStart(*[Create(a) for a in arcs], lag_ratio=0.25), FadeIn(ctx), bars=1)
        self.at_bar(94.75)
        self.fade_rest(0.25)
        # 95–96 strawberry
        self.at_bar(95)
        self.tag("彩蛋：数字母")
        word = VGroup(*[T(c, size=64, color=C_WHITE) for c in "strawberry"]).arrange(RIGHT, buff=0.04).move_to([0, 1.3, 0])
        qq = T("strawberry 里有几个 r？", size=32, color=C_WHITE).move_to([0, 2.5, 0])
        early = VGroup(T("早期模型：", size=30, color=C_GREY), T("2", size=36, color=C_RED, weight=BOLD),
                       T("✗", size=34, color=C_RED)).arrange(RIGHT, buff=0.15).move_to([-2.0, -1.0, 0])
        truth = VGroup(T("正确：", size=30, color=C_GREY), T("3", size=36, color=C_GREEN, weight=BOLD)).arrange(RIGHT, buff=0.15).move_to([2.4, -1.0, 0])
        self.play_bars(FadeIn(qq), FadeIn(word), bars=0.5)
        self.play_bars(FadeIn(early), *[word[i].animate.set_color(C_RED) for i in (2, 7, 8)], bars=0.5)
        self.play_bars(FadeIn(truth), bars=0.5)
        # 97–98 token 盖住字母
        self.at_bar(97)
        groups = [(0, 3, "str"), (3, 5, "aw"), (5, 10, "berry")]
        covers = VGroup()
        for a, b, lab in groups:
            seg = VGroup(*word[a:b])
            r_ = RoundedRectangle(width=seg.width + 0.25, height=seg.height + 0.45, corner_radius=0.12,
                                  stroke_color=C_BLUE, stroke_width=3, fill_color="#14304a", fill_opacity=1).move_to(seg)
            covers.add(VGroup(r_, T(lab, size=30, color=C_BLUE).move_to(r_)))
        self.play_bars(LaggedStart(*[FadeIn(c, scale=1.1) for c in covers], lag_ratio=0.25), bars=1)
        sees = T("模型看到的是 3 个 token，字母藏在方块里（示意切法）", size=24, color=C_BLUE).move_to([0, 0.1, 0])
        self.play_bars(FadeIn(sees), bars=0.5)
        # 99–100 现在能答对
        self.at_bar(99)
        now = T("现在很多模型已经能答对", size=32, color=C_GREEN).move_to([0, -2.1, 0])
        nn = T("（早期模型常错；原因之一是看不到 token 里的字母）", size=20, color=C_GREY).next_to(now, DOWN, buff=0.1)
        self.play_bars(FadeIn(now, shift=UP * 0.2), FadeIn(nn), bars=0.75)
        self.at_bar(100.5)
        self.fade_rest(0.5)

    # ------------------------------------------------------------ 间奏二 101–104：要点
    def inst2(self):
        self.at_bar(101)
        self.tag("本集要点")
        head = T("本集要点", size=46, color=C_YELLOW, weight=BOLD)
        pts = [
            "1. 文字先切成 token（词元），每个 token 有编号；切法因模型而异",
            "2. 查嵌入表把 token 换成向量（GPT-3：12,288 个数）；嵌入表也是旋钮",
            "3. 训练后意思相近的词离得近，某些方向带上含义（经典词向量实验）",
            "4. 同一个词只有一个向量：要看上下文才能分清意思 → 下集：注意力",
        ]
        items = VGroup(*[T(p, size=28) for p in pts]).arrange(DOWN, aligned_edge=LEFT, buff=0.32)
        g = VGroup(head, items).arrange(DOWN, buff=0.5).move_to([0, 0.35, 0])
        if g.width > 13.2:
            g.scale_to_fit_width(13.2)
        self.play_bars(FadeIn(head, shift=DOWN * 0.2), bars=0.25)
        for it in items:
            self.play_bars(FadeIn(it, shift=RIGHT * 0.3), bars=0.5)
        self.at_bar(104.5)
        self.play_bars(FadeOut(g), bars=0.5)

    # ------------------------------------------------------------ 尾声 115–122
    def outro(self):
        self.at_bar(115)
        self.tag("回顾")
        steps = [("句子", C_WHITE), ("token", C_BLUE), ("编号", C_GOLD), ("向量", C_YELLOW)]
        chips = VGroup()
        for s_, col in steps:
            t = T(s_, size=34, color=col)
            chips.add(VGroup(SurroundingRectangle(t, color=col, buff=0.2, corner_radius=0.12, stroke_width=2.5), t))
        chips.arrange(RIGHT, buff=0.9).move_to([0, 0.8, 0])
        arrows = VGroup(*[Arrow(chips[i].get_right(), chips[i + 1].get_left(), buff=0.1, color=C_GREY, stroke_width=3)
                          for i in range(3)])
        self.play_bars(FadeIn(chips[0]), bars=0.4)
        for i in range(1, 4):
            self.play_bars(GrowArrow(arrows[i - 1]), FadeIn(chips[i]), bars=0.4)
        # 117–118 位置与方向
        self.at_bar(117)
        self.play_bars(VGroup(chips, arrows).animate.scale(0.7).move_to([0, 2.3, 0]), bars=0.5)
        a = Dot([-1.8, -0.6, 0], color=C_WHITE)
        b = Dot([0.2, 0.0, 0], color=C_WHITE)
        c = Dot([-1.4, 0.9, 0], color=C_WHITE)
        d = Dot([0.6, 1.5, 0], color=C_WHITE)
        cl = VGroup(*[Dot([x, y, 0], radius=0.07, color=col) for x, y, col in
                      [(2.5, 0.8, C_GOLD), (2.8, 1.0, C_GOLD), (2.6, 0.5, C_GOLD), (3.6, -0.6, C_GREEN), (3.9, -0.4, C_GREEN)]])
        ar1 = Arrow(a.get_center(), b.get_center(), buff=0.08, color=C_ORANGE)
        ar2 = Arrow(c.get_center(), d.get_center(), buff=0.08, color=C_ORANGE)
        lab = T("意思 = 位置　关系 = 方向", size=30, color=C_WHITE).move_to([0.5, -1.7, 0])
        self.play_bars(FadeIn(VGroup(a, b, c, d, cl)), GrowArrow(ar1), GrowArrow(ar2), FadeIn(lab), bars=1)
        # 119–120 看看周围
        self.at_bar(119)
        self.play_bars(FadeOut(VGroup(a, b, c, d, cl, ar1, ar2, lab)), bars=0.25)
        apple = token_block("苹果", color=C_RED, size=48).move_to([0, 0.3, 0])
        neigh = VGroup(*[T(w, size=30, color=C_GREY).move_to(apple.get_center() + 1.7 * np.array([np.cos(t), 0.75 * np.sin(t), 0]))
                         for w, t in zip(["削", "手机", "红", "新款", "甜", "发布"], np.linspace(0, TAU, 7)[:-1])])
        qm = T("？", size=48, color=C_RED).next_to(apple, UR, buff=0.05)
        self.play_bars(FadeIn(apple), LaggedStart(*[FadeIn(n) for n in neigh], lag_ratio=0.1), FadeIn(qm), bars=1)
        # 121–122 下集：注意力
        self.at_bar(121)
        self.play_bars(FadeOut(VGroup(apple, neigh, qm)), bars=0.25)
        words = VGroup(*[token_block(w, color=C_BLUE, size=34) for w in ["小明", "把", "苹果", "递给", "妹妹"]]).arrange(RIGHT, buff=0.25).move_to([0, 0.0, 0])
        arcs = VGroup(*[CurvedArrow(words[i].get_top(), words[j].get_top(), angle=-0.8, color=C_PURPLE, stroke_width=3, tip_length=0.15)
                        for i, j in [(2, 0), (2, 3), (4, 3), (3, 0)]])
        nxt = VGroup(T("下集", size=28, color=C_GREY), T("注意力", size=46, color=C_PURPLE, weight=BOLD),
                     T("每个词都在看别的词", size=28, color=C_PURPLE)).arrange(DOWN, buff=0.2).move_to([0, -1.6, 0])
        self.play_bars(FadeIn(words), LaggedStart(*[Create(a_) for a_ in arcs], lag_ratio=0.2), FadeIn(nxt), bars=1)
        self.at_bar(122.25)
        self.play_bars(*[FadeOut(m) for m in self.visible()], bars=0.75)
