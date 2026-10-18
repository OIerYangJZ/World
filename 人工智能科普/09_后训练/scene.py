# -*- coding: utf-8 -*-
"""
第 09 集《后训练：从续写机器到 AI 助手》

时间全部对齐 bars.py 的 BPM 小节网格（90 BPM，122 小节）。字幕由 build.py 烧录。
    ~/.venvs/manim/bin/python ../common/build.py 09_后训练 [--preview]

说明：示范对话、回答卡片、分数山、解题路线都是示意；画面讲的是公开论文中的代表性方法。
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "common"))
from style import *  # noqa: E402,F401

C_ATT, C_MLP = C_PURPLE, C_TEAL


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


def bubble(text, color=C_BLUE, size=26, left=True):
    t = T(text, size=size, color=C_WHITE)
    r = RoundedRectangle(width=t.width + 0.5, height=t.height + 0.35, corner_radius=0.2, stroke_color=color,
                         stroke_width=2.5, fill_color=color, fill_opacity=0.2)
    return VGroup(r, t.move_to(r))


def knob_grid(n_rows=3, n_cols=8, seed=2, radius=0.22):
    r = np.random.default_rng(seed)
    trs = [ValueTracker(r.uniform(0.2, 0.8)) for _ in range(n_rows * n_cols)]
    ks = VGroup(*[Knob("·", t, 0, 1, radius=radius) for t in trs])
    for k in ks:
        k[-1].set_opacity(0)
    ks.arrange_in_grid(rows=n_rows, cols=n_cols, buff=0.32)
    return ks, trs


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

    # ------------------------------------------------------------ 前奏 1–4
    def intro(self):
        c = title_card("第 09 集", "后训练", "从续写机器到 AI 助手")
        s, e, t, line, st = c
        self.play_bars(FadeIn(s, shift=DOWN * 0.2), FadeIn(e, shift=DOWN * 0.2), bars=0.75)
        self.play_bars(Write(t), bars=1)
        self.play_bars(GrowFromCenter(line), FadeIn(st, shift=UP * 0.2), bars=0.75)
        self.at_bar(3.5)
        self.set_counter("1750 亿", bars=0.5)
        self.at_bar(4.5)
        self.play_bars(FadeOut(c), bars=0.5)

    # ------------------------------------------------------------ 主歌一 5–20：对话也是续写
    def verse1(self):
        self.at_bar(5)
        self.tag("基座模型")
        tw = tower(6).move_to([-3.6, 0.3, 0])
        lab = VGroup(T("基座模型", size=30, color=C_GOLD, weight=BOLD), T("满肚子文本，只会续写", size=24, color=C_GREY)).arrange(DOWN, buff=0.1)
        lab.next_to(tw, DOWN, buff=0.3)
        self.play_bars(FadeIn(tw), FadeIn(lab), bars=1)
        self.tw, self.twlab = tw, lab
        # 7–8 续写考卷
        self.at_bar(7)
        doc = card(["1. 法国的首都是哪里？", "2. 德国的首都是哪里？", "3. 意大利的首都是哪里？"], width=5.4, size=26)
        doc.move_to([2.2, 0.4, 0])
        for i in (1, 2):
            doc[1][0][i].set_color(C_GOLD)
        qm = T("？", size=56, color=C_RED).next_to(doc, RIGHT, buff=0.2)
        self.play_bars(FadeIn(doc), bars=0.75)
        self.play_bars(FadeIn(qm, scale=1.4), bars=0.5)
        self.at_bar(8.75)
        self.play_bars(FadeOut(VGroup(doc, qm)), bars=0.25)
        # 9–10 掀开聊天气泡
        self.at_bar(9)
        self.tag("聊天 = 续写一页文档")
        ui = RoundedRectangle(width=5.6, height=3.6, corner_radius=0.25, color=C_GREY, fill_color="#121621", fill_opacity=1).move_to([2.2, 0.3, 0])
        b1 = bubble("法国的首都是哪里？", C_BLUE).move_to(ui.get_corner(UR) + np.array([-1.8, -0.7, 0]))
        b2 = bubble("巴黎。", C_GREEN).move_to(ui.get_corner(UL) + np.array([1.0, -1.6, 0]))
        self.play_bars(FadeIn(ui), FadeIn(b1), FadeIn(b2), bars=0.75)
        docv = card(["用户：法国的首都是哪里？", "助手："], width=5.4, size=28)
        docv.move_to(ui)
        self.play_bars(VGroup(ui, b1, b2).animate.shift(UP * 0.4).rotate(0.12).set_opacity(0.0), FadeIn(docv), bars=1)
        # 11–12 一行一行
        self.at_bar(11)
        roles = VGroup(SurroundingRectangle(docv[1][0][0][:3], color=C_BLUE, buff=0.05),
                       SurroundingRectangle(docv[1][0][1][:3], color=C_GREEN, buff=0.05))
        self.play_bars(Create(roles), bars=1)
        rl = T("固定格式：用户说一句，助手接一句", size=24, color=C_GREY).next_to(docv, DOWN, buff=0.3)
        self.play_bars(FadeIn(rl), bars=0.5)
        # 13–14 光标在“助手：”后
        self.at_bar(13)
        cur = Rectangle(width=0.06, height=0.4, stroke_width=0, fill_color=C_WHITE, fill_opacity=1).next_to(docv[1][0][1], RIGHT, buff=0.1)
        zone = DashedVMobject(Rectangle(width=3.0, height=0.55, color=C_GOLD).next_to(docv[1][0][1], RIGHT, buff=0.05).align_to(cur, LEFT), num_dashes=24)
        zl = T("模型续写这一块", size=24, color=C_GOLD).next_to(zone, DOWN, buff=0.15)
        self.play_bars(FadeIn(cur), Create(zone), FadeIn(zl), FadeOut(roles), FadeOut(rl), bars=0.75)
        self.play_bars(cur.animate.set_opacity(0), bars=0.25)
        self.play_bars(cur.animate.set_opacity(1), bars=0.25)
        self.play_bars(cur.animate.set_opacity(0), bars=0.25)
        # 15–16 同一个模型
        self.at_bar(15)
        same = T("同一个模型，同一套旋钮", size=28, color=C_WHITE).next_to(self.twlab, DOWN, buff=0.25)
        self.play_bars(Indicate(self.tw, color=C_YELLOW, scale_factor=1.03), Indicate(self.counter, color=C_YELLOW), FadeIn(same), bars=1)
        self.same = same
        # 17–18 续写好助手的回答
        self.at_bar(17)
        ans = T("法国的首都是巴黎。", size=28, color=C_GREEN).move_to(zone.get_center())
        self.play_bars(FadeOut(zl), Write(ans), cur.animate.set_opacity(0), bars=1)
        good = T("好助手的回答", size=24, color=C_GREEN).next_to(zone, DOWN, buff=0.15)
        self.play_bars(FadeIn(good), bars=0.5)
        # 19–20 路线图
        self.at_bar(19)
        self.fade_rest(0.25)
        steps = VGroup(card(["看示范"], title="① 监督微调", tcolor=C_BLUE, width=3.4, size=26),
                       card(["听评价（比较好坏）"], title="② 基于反馈的强化学习", tcolor=C_ORANGE, width=3.8, size=24),
                       card(["答对给奖励"], title="③ 推理训练（后面讲）", tcolor=C_GREEN, width=3.4, size=24)).arrange(RIGHT, buff=0.6)
        if steps.width > 13:
            steps.scale_to_fit_width(13)
        steps.move_to([0, 0.4, 0])
        arr = VGroup(*[Arrow(steps[i].get_right(), steps[i + 1].get_left(), buff=0.08, color=C_GREY) for i in range(2)])
        self.play_bars(LaggedStart(FadeIn(steps[0]), GrowArrow(arr[0]), FadeIn(steps[1]), lag_ratio=0.35), bars=0.75)
        self.play_bars(GrowArrow(arr[1]), FadeIn(steps[2]), steps[2].animate.set_opacity(0.5), bars=0.5)
        self.at_bar(20.5)
        self.fade_rest(0.5)

    # ------------------------------------------------------------ 副歌
    def hook(self, s):
        self.at_bar(s)
        self.tag("从续写机器到助手")
        tw = tower(5, w=2.0, h=0.45).move_to([-4.6, 0.2, 0])
        q = T("怎么当助手？", size=28, color=C_GOLD).next_to(tw, UP, buff=0.25)
        self.play_bars(FadeIn(tw), bars=0.5)
        self.play_bars(FadeIn(q, scale=1.3), bars=0.75)
        # ② 示范
        self.at_bar(s + 2)
        demo = card(["问：怎么煮溏心蛋？", "答：水开后放蛋，煮 6 分钟，", "    捞出泡冷水。"], title="示范", tcolor=C_BLUE, width=4.6, size=22)
        demo.move_to([0.4, 0.4, 0])
        self.play_bars(FadeIn(demo, shift=LEFT * 0.3), bars=1)
        self.play_bars(Indicate(demo[0], color=C_BLUE, scale_factor=1.02), bars=0.5)
        # ③ 两个回答，人来挑
        self.at_bar(s + 4)
        self.play_bars(FadeOut(demo), bars=0.25)
        A = card(["回答 A：", "鸡蛋煮熟即可。"], width=3.6, size=22).move_to([-0.6, 0.4, 0])
        B = card(["回答 B：", "水开放蛋，6 分钟，", "泡冷水更好剥。"], width=3.6, size=22).move_to([3.6, 0.4, 0])
        self.play_bars(FadeIn(A), FadeIn(B), bars=0.5)
        hand = VGroup(Circle(radius=0.16, color=C_WHITE, fill_opacity=1), Line(ORIGIN, DOWN * 0.45 + LEFT * 0.2, color=C_WHITE, stroke_width=5))
        hand.move_to(B.get_bottom() + DOWN * 0.6 + RIGHT * 0.6)
        self.play_bars(FadeIn(hand), hand.animate.move_to(B.get_center() + DOWN * 0.2), bars=0.5)
        self.play_bars(B[0].animate.set_stroke(C_GREEN, 4), Flash(B.get_corner(UR), color=C_GREEN), bars=0.5)
        # ④ 一点点地改
        self.at_bar(s + 6)
        self.play_bars(FadeOut(VGroup(A, B, hand, q)), bars=0.25)
        ks, trs = knob_grid(3, 7, seed=s, radius=0.22)
        ks.move_to([1.2, 0.4, 0])
        self.play_bars(FadeIn(ks), bars=0.5)
        self.play_bars(*[t.animate.set_value(t.get_value() + 0.08) for t in trs], bars=1)
        # ⑤ 黑箱
        self.at_bar(s + 8)
        self.fade_rest(0.25)
        box = black_box(w=3.2, h=2.2, depth=0.45).move_to([0, 0.2, 0])
        inner = VGroup(bubble("你好！", C_BLUE, size=20), bubble("有什么能帮你？", C_GREEN, size=20)).arrange(DOWN, buff=0.12, aligned_edge=LEFT)
        inner.move_to(box.front)
        self.play_bars(FadeIn(box), bars=0.25)
        self.play_bars(VGroup(box.front, box.q).animate.shift(UP * 0.3).set_opacity(0.12), FadeIn(inner), bars=0.5)
        slogan = T("一层一层，把黑箱打开", size=40, color=C_YELLOW, weight=BOLD).to_edge(UP, buff=0.3)
        self.play_bars(Write(slogan), bars=0.5)
        self.at_bar(s + 9.5)
        self.fade_rest(0.5)

    # ------------------------------------------------------------ 主歌二 31–46：监督微调
    def verse2(self):
        self.at_bar(31)
        self.tag("① 监督微调")
        title = VGroup(T("监督微调", size=56, color=C_BLUE, weight=BOLD), T("SFT（Supervised Fine-Tuning）", size=26, color=C_GREY)).arrange(DOWN, buff=0.2)
        title.move_to([0, 0.6, 0])
        self.play_bars(Write(title[0]), bars=1)
        self.play_bars(FadeIn(title[1]), bars=0.5)
        # 33–34 示范卡
        self.at_bar(33)
        self.play_bars(title.animate.scale(0.5).move_to([0, 2.7, 0]), bars=0.5)
        demos = VGroup(
            card(["问：怎么煮溏心蛋？", "答：水开放蛋，煮 6 分钟……"], width=4.0, size=20),
            card(["问：把“谢谢”翻成英文", "答：Thank you."], width=4.0, size=20),
            card(["问：写两句秋天的诗", "答：风把叶子写成信……"], width=4.0, size=20)).arrange(RIGHT, buff=0.3).move_to([0, 0.5, 0])
        if demos.width > 13.2:
            demos.scale_to_fit_width(13.2)
        dl = T("人写的“问题 + 理想回答”（示意）", size=24, color=C_BLUE).next_to(demos, DOWN, buff=0.3)
        self.play_bars(LaggedStart(*[FadeIn(d, shift=UP * 0.2) for d in demos], lag_ratio=0.3), FadeIn(dl), bars=1.25)
        # 35–36 还是猜下一个 token
        self.at_bar(35)
        self.play_bars(FadeOut(VGroup(demos, dl)), bars=0.25)
        tw = tower(5, w=2.2, h=0.45).move_to([-3.8, 0.1, 0])
        toks = VGroup(*[RoundedRectangle(width=0.62, height=0.5, corner_radius=0.06, color=C_GREEN, fill_opacity=0.2) for _ in range(6)])
        words = ["水开", "放", "蛋", "，", "煮", "6"]
        toks = VGroup(*[VGroup(t, T(w, size=20, color=C_WHITE).move_to(t)) for t, w in zip(toks, words)]).arrange(RIGHT, buff=0.08)
        toks.move_to([2.2, 0.6, 0])
        tl = T("示范回答的每个 token 都是“答案”：仍然是猜下一个 token", size=24, color=C_GREEN).move_to([1.0, -1.3, 0])
        self.play_bars(FadeIn(tw), FadeIn(toks), bars=0.5)
        self.play_bars(LaggedStart(*[Indicate(t, color=C_GREEN) for t in toks], lag_ratio=0.15), FadeIn(tl), bars=1)
        # 37–38 少而精
        self.at_bar(37)
        self.play_bars(FadeOut(VGroup(tw, toks, tl)), bars=0.25)
        big = Rectangle(width=11.0, height=0.6, stroke_width=0, fill_color=C_GOLD, fill_opacity=0.6).move_to([0, 0.9, 0])
        small = Rectangle(width=0.35, height=0.6, stroke_width=0, fill_color=C_BLUE, fill_opacity=0.9).align_to(big, LEFT).set_y(-0.4)
        bl = T("预训练数据：万亿级 token", size=24, color=C_GOLD).next_to(big, UP, buff=0.15).align_to(big, LEFT)
        sl = T("示范数据：少得多，但要精心挑选（长度为示意）", size=24, color=C_BLUE).next_to(small, RIGHT, buff=0.3)
        self.play_bars(GrowFromEdge(big, LEFT), FadeIn(bl), bars=0.75)
        self.play_bars(GrowFromEdge(small, LEFT), FadeIn(sl), bars=0.75)
        # 39–40 格式
        self.at_bar(39)
        self.play_bars(FadeOut(VGroup(big, small, bl, sl)), bars=0.25)
        fmt = card(["结论：煮 6 分钟左右。", "1. 水烧开再放蛋", "2. 计时 6 分钟", "3. 捞出泡冷水"], title="助手的回答格式", tcolor=C_GREEN, width=5.0, size=24)
        fmt.move_to([0, 0.4, 0])
        self.play_bars(FadeIn(fmt), bars=0.75)
        self.play_bars(Indicate(fmt[1][1][0], color=C_GREEN), bars=0.5)
        # 41–42 描红
        self.at_bar(41)
        self.play_bars(FadeOut(fmt), bars=0.25)
        tmpl = T("水开放蛋，煮六分钟", size=64, color=C_GREY).set_opacity(0.35).move_to([0, 0.5, 0])
        over = T("水开放蛋，煮六分钟", size=64, color=C_GOLD).move_to(tmpl)
        self.play_bars(FadeIn(tmpl), bars=0.25)
        self.play_bars(Write(over), bars=1.25)
        self.v2_tmpl = VGroup(tmpl, over)
        # 43–44 两个都不算错
        self.at_bar(43)
        self.play_bars(FadeOut(self.v2_tmpl), bars=0.25)
        A = card(["回答 A：", "水开后煮 6 分钟。"], width=4.2, size=24).move_to([-2.8, 0.5, 0])
        B = card(["回答 B：", "水开后煮 6 分钟，", "捞出泡冷水更好剥壳。"], width=4.2, size=24).move_to([2.8, 0.5, 0])
        self.play_bars(FadeIn(A), FadeIn(B), bars=0.75)
        q = T("都没错，哪个更好？", size=30, color=C_GOLD).move_to([0, -1.6, 0])
        self.play_bars(FadeIn(q), bars=0.5)
        # 45–46 天平
        self.at_bar(45)
        beam = Line(LEFT * 1.4, RIGHT * 1.4, color=C_WHITE, stroke_width=4).move_to([0, 2.0, 0])
        post = Line([0, 2.0, 0], [0, 1.2, 0], color=C_WHITE, stroke_width=4)
        pans = VGroup(Arc(radius=0.35, start_angle=PI, angle=PI, color=C_WHITE).move_to(beam.get_left() + DOWN * 0.35),
                      Arc(radius=0.35, start_angle=PI, angle=PI, color=C_WHITE).move_to(beam.get_right() + DOWN * 0.35))
        scale_ = VGroup(beam, post, pans)
        self.play_bars(FadeIn(scale_), bars=0.5)
        self.play_bars(Rotate(VGroup(beam, pans), -0.12, about_point=[0, 2.0, 0]), bars=0.75)
        jl = T("需要有人来评判", size=26, color=C_ORANGE).next_to(q, DOWN, buff=0.2)
        self.play_bars(FadeIn(jl), bars=0.5)

    # ------------------------------------------------------------ 间奏一 47–50：描红
    def inst1(self):
        self.at_bar(47)
        self.fade_rest(0.25)
        self.tag("照着示范学")
        lines = ["先说结论，再分点说明", "不知道就说不知道", "语气礼貌，回答完整"]
        rows = VGroup()
        for i, l in enumerate(lines):
            tm = T(l, size=44, color=C_GREY).set_opacity(0.3)
            ov = T(l, size=44, color=C_GOLD)
            rows.add(VGroup(tm, ov))
        for i, r in enumerate(rows):
            r.move_to([0, 1.4 - 1.1 * i, 0])
            r[1].move_to(r[0])
        self.play_bars(*[FadeIn(r[0]) for r in rows], bars=0.5)
        for r in rows:
            self.play_bars(Write(r[1]), bars=0.75)
        demo = T("（示意：示范数据教的是“好助手”的说话方式）", size=22, color=C_GREY).move_to([0, -2.1, 0])
        self.play_bars(FadeIn(demo), bars=0.25)
        self.at_bar(50.5)
        self.fade_rest(0.5)

    # ------------------------------------------------------------ 主歌三 61–76：RLHF
    def verse3(self):
        self.at_bar(61)
        self.tag("② 基于反馈的强化学习")
        board = VGroup(*[Line([-1.2, -1.2 + 0.4 * i, 0], [1.2, -1.2 + 0.4 * i, 0], color=C_GREY, stroke_width=1.5) for i in range(7)],
                       *[Line([-1.2 + 0.4 * i, -1.2, 0], [-1.2 + 0.4 * i, 1.2, 0], color=C_GREY, stroke_width=1.5) for i in range(7)])
        stones = VGroup(Dot([-0.4, 0.4, 0], radius=0.15, color=BLACK).set_stroke(C_WHITE, 2), Dot([0.4, 0.0, 0], radius=0.15, color=C_WHITE),
                        Dot([0.0, -0.4, 0], radius=0.15, color=BLACK).set_stroke(C_WHITE, 2))
        g = VGroup(board, stones).move_to([-3.6, 0.3, 0])
        rl = VGroup(T("奖励（赢了）", size=28, color=C_GOLD), T("→ 调高这些走法的概率", size=28, color=C_WHITE)).arrange(DOWN, buff=0.2)
        rl.move_to([2.4, 0.6, 0])
        ref = T("（强化学习，详见番外二）", size=22, color=C_GREY).next_to(rl, DOWN, buff=0.3)
        self.play_bars(FadeIn(g), FadeIn(rl[0]), bars=0.75)
        self.play_bars(FadeIn(rl[1]), FadeIn(ref), bars=0.75)
        self.at_bar(62.75)
        self.fade_rest(0.25)
        # 63–64 两个回答
        self.at_bar(63)
        qq = bubble("怎么煮溏心蛋？", C_BLUE, size=26).move_to([0, 2.2, 0])
        A = card(["回答 A：", "水开后煮 6 分钟。"], width=4.2, size=24).move_to([-2.8, 0.3, 0])
        B = card(["回答 B：", "水开放蛋煮 6 分钟，", "泡冷水更好剥壳。"], width=4.2, size=24).move_to([2.8, 0.3, 0])
        self.play_bars(FadeIn(qq), bars=0.5)
        self.play_bars(FadeIn(A, shift=UP * 0.2), FadeIn(B, shift=UP * 0.2), bars=0.75)
        # 65–66 人来比
        self.at_bar(65)
        hand = VGroup(Circle(radius=0.16, color=C_WHITE, fill_opacity=1), Line(ORIGIN, DOWN * 0.45 + LEFT * 0.2, color=C_WHITE, stroke_width=5))
        hand.move_to([0, -1.4, 0])
        self.play_bars(FadeIn(hand), hand.animate.move_to(B.get_center() + DOWN * 0.3), bars=0.5)
        cmp = T("A  <  B", size=40, color=C_GREEN, weight=BOLD).move_to([0, -1.5, 0])
        self.play_bars(B[0].animate.set_stroke(C_GREEN, 4), FadeIn(cmp, scale=1.3), bars=0.5)
        note = T("人给的是比较 / 排序，不是绝对分数", size=22, color=C_GREY).next_to(cmp, DOWN, buff=0.15)
        self.play_bars(FadeIn(note), bars=0.5)
        # 67–68 打分模型
        self.at_bar(67)
        self.play_bars(FadeOut(VGroup(qq, A, B, hand, note)), cmp.animate.scale(0.5).move_to([-5.0, 1.8, 0]), bars=0.25)
        pairs = VGroup(cmp, *[T(t, size=20, color=C_GREEN).move_to([-5.0, 1.8 - 0.45 * (i + 1), 0])
                              for i, t in enumerate(["C < D", "F < E", "G < H", "J < I", "……"])])
        self.play_bars(LaggedStart(*[FadeIn(p) for p in pairs[1:]], lag_ratio=0.15), bars=0.5)
        rm = VGroup(RoundedRectangle(width=2.8, height=1.6, corner_radius=0.15, color=C_ORANGE, fill_opacity=0.15),
                    T("打分模型", size=30, color=C_ORANGE)).move_to([0, 0.6, 0])
        rm[1].move_to(rm[0])
        arrs = Arrow([-4.2, 0.9, 0], rm.get_left(), buff=0.1, color=C_GREY)
        gauge = VGroup(Arc(radius=0.9, start_angle=PI, angle=-PI, color=C_GREY, stroke_width=6).move_to([4.0, 0.9, 0]))
        needle = Line(gauge.get_center() + DOWN * 0.45, gauge.get_center() + DOWN * 0.45 + 0.8 * UP, color=C_GOLD, stroke_width=5)
        needle.rotate(0.9, about_point=needle.get_start())
        gl = T("分数", size=24, color=C_GOLD).next_to(gauge, DOWN, buff=0.1)
        arr2 = Arrow(rm.get_right(), gauge.get_left() + DOWN * 0.2, buff=0.1, color=C_GREY)
        sep = T("（另外训练出来的一个网络）", size=20, color=C_GREY).next_to(rm, DOWN, buff=0.2)
        self.play_bars(GrowArrow(arrs), FadeIn(rm), FadeIn(sep), GrowArrow(arr2), FadeIn(gauge), FadeIn(needle), FadeIn(gl), bars=0.75)
        self.play_bars(Rotate(needle, -1.4, about_point=needle.get_start()), bars=0.5)
        # 69–70 分数山 + 弹簧
        self.at_bar(69)
        self.fade_rest(0.25)
        ax = Axes(x_range=[-4, 4], y_range=[0, 2], x_length=9, y_length=3.2, tips=False,
                  axis_config=dict(color=C_GREY, stroke_width=1.5)).move_to([0, 0.0, 0])
        hill = ax.plot(lambda x: 1.7 * np.exp(-((x - 1.8) ** 2) / 2.0), x_range=[-4, 4], color=C_ORANGE, stroke_width=4)
        hl = T("打分模型给的分数", size=22, color=C_ORANGE).next_to(ax.c2p(1.8, 1.7), UP, buff=0.1)
        x0 = -1.8
        pos = ValueTracker(x0)
        dot = always_redraw(lambda: Dot(ax.c2p(pos.get_value(), 1.7 * np.exp(-((pos.get_value() - 1.8) ** 2) / 2.0)), radius=0.14, color=C_GREEN))
        anchor = Dot(ax.c2p(x0, 0), radius=0.08, color=C_GREY)
        al = T("原来的模型", size=20, color=C_GREY).next_to(anchor, DOWN, buff=0.12)

        def spring():
            a = anchor.get_center()
            b = dot.get_center()
            n = 14
            pts = [a + (b - a) * k / n + (np.array([-(b - a)[1], (b - a)[0], 0]) / (np.linalg.norm(b - a) + 1e-6)) * (0.12 if k % 2 else -0.12) * (0 < k < n)
                   for k in range(n + 1)]
            return VMobject(stroke_color=C_BLUE, stroke_width=2.5).set_points_as_corners(pts)

        spr = always_redraw(spring)
        self.play_bars(FadeIn(ax), Create(hill), FadeIn(hl), FadeIn(anchor), FadeIn(al), FadeIn(dot), FadeIn(spr), bars=0.5)
        self.play_bars(pos.animate.set_value(0.9), bars=1.0)
        sl = T("弹簧：不能离原来的模型太远", size=22, color=C_BLUE).move_to([-3.6, 1.9, 0])
        self.play_bars(FadeIn(sl), bars=0.25)
        # 71–72 RLHF / InstructGPT
        self.at_bar(71)
        nm = VGroup(T("基于人类反馈的强化学习（RLHF）", size=30, color=C_WHITE), T("InstructGPT（2022）", size=26, color=C_GREY)).arrange(DOWN, buff=0.12)
        nm.move_to([2.6, 2.6, 0])
        if nm.get_right()[0] > 6.9:
            nm.shift(LEFT * (nm.get_right()[0] - 6.9))
        self.play_bars(FadeIn(nm, shift=DOWN * 0.2), bars=0.75)
        self.at_bar(72.75)
        self.fade_rest(0.25)
        # 73–74 13 亿 vs 1750 亿
        self.at_bar(73)
        s1 = Square(side_length=0.35, color=C_GREEN, fill_opacity=0.5).move_to([-3.6, 0.3, 0])
        s2 = Square(side_length=3.4, color=C_GREY, fill_opacity=0.15).move_to([2.6, 0.3, 0])
        l1 = VGroup(T("InstructGPT", size=24, color=C_GREEN), T("13 亿参数 + RLHF", size=22, color=C_GREEN)).arrange(DOWN, buff=0.08).next_to(s1, DOWN, buff=0.3)
        l2 = VGroup(T("GPT-3", size=24, color=C_GREY), T("1750 亿参数", size=22, color=C_GREY)).arrange(DOWN, buff=0.08).next_to(s2, DOWN, buff=0.2)
        self.play_bars(FadeIn(s1), FadeIn(s2), FadeIn(l1), FadeIn(l2), bars=0.75)
        pref = VGroup(T("评审者更喜欢左边的回答", size=28, color=C_GOLD), T("（不是“全面更聪明”）", size=22, color=C_GREY)).arrange(DOWN, buff=0.1)
        pref.move_to([-3.2, 2.3, 0])
        self.play_bars(FadeIn(pref), Indicate(s1, color=C_GOLD, scale_factor=1.5), bars=0.75)
        self.at_bar(74.75)
        self.fade_rest(0.25)
        # 75–76 变体
        self.at_bar(75)
        v1 = card(["照一份写明原则的“宪法”，", "让 AI 来比较、给反馈"], title="Constitutional AI（2022）", tcolor=C_PURPLE, width=5.6, size=22)
        v2 = card(["直接从“哪个更好”的比较里学，", "省掉单独的打分模型"], title="DPO（2023）", tcolor=C_TEAL, width=5.6, size=22)
        vs = VGroup(v1, v2).arrange(RIGHT, buff=0.5).move_to([0, 0.4, 0])
        if vs.width > 13.2:
            vs.scale_to_fit_width(13.2)
        self.play_bars(FadeIn(v1, shift=UP * 0.2), bars=0.6)
        self.play_bars(FadeIn(v2, shift=UP * 0.2), bars=0.6)
        self.at_bar(76.5)
        self.fade_rest(0.5)

    # ------------------------------------------------------------ 桥段 77–84
    def bridge(self):
        self.at_bar(77)
        self.tag("大小没变，方向变了")
        ks, trs = knob_grid(4, 10, seed=7, radius=0.24)
        ks.move_to([0, 0.4, 0])
        self.play_bars(FadeIn(ks), bars=1)
        same = T("1750 亿：一个没多", size=36, color=C_YELLOW).next_to(ks, DOWN, buff=0.4)
        self.play_bars(Indicate(self.counter, color=C_YELLOW), FadeIn(same), bars=1.5)
        self.at_bar(81)
        dirc = T("方向变了：每个都轻轻一改", size=36, color=C_GREEN).move_to(same)
        self.play_bars(Transform(same, dirc), bars=0.75)
        self.play_bars(*[t.animate.set_value(t.get_value() + 0.12) for t in trs], bars=2)
        self.play_bars(*[t.animate.set_value(t.get_value() - 0.04) for t in trs], bars=0.75)
        self.fade_rest(0.5)

    # ------------------------------------------------------------ 主歌四 85–100
    def verse4(self):
        self.at_bar(85)
        self.tag("③ 推理训练")
        prob = T("17 × 24 = ?", size=56, color=C_WHITE).move_to([-3.2, 1.2, 0])
        judge = VGroup(RoundedRectangle(width=2.6, height=1.2, corner_radius=0.15, color=C_GREEN, fill_opacity=0.12),
                       T("自动判卷", size=28, color=C_GREEN)).move_to([3.2, 1.2, 0])
        judge[1].move_to(judge[0])
        self.play_bars(Write(prob), bars=0.75)
        self.play_bars(FadeIn(judge), bars=0.5)
        jl = T("答案对不对，能自动检查（数学题、编程题的测试）", size=22, color=C_GREY).move_to([0, 0.0, 0])
        self.play_bars(FadeIn(jl), bars=0.5)
        # 87–88 多条路线
        self.at_bar(87)
        self.play_bars(FadeOut(jl), judge.animate.scale(0.7).move_to([4.8, 2.4, 0]), bars=0.25)
        ends = [("408", True), ("398", False), ("408", True), ("418", False), ("408", True)]
        paths = VGroup()
        labels = VGroup()
        for i, (a, ok) in enumerate(ends):
            y = 0.6 - 0.55 * i
            p = VMobject(stroke_color=C_GREY, stroke_width=3).set_points_smoothly(
                [prob.get_bottom() + DOWN * 0.1, [-1.5, (0.6 + y) / 2 + 0.1, 0], [0.8, y, 0], [2.4, y, 0]])
            paths.add(p)
            labels.add(T(a + ("  ✓" if ok else "  ✗"), size=24, color=C_GREEN if ok else C_GREY).next_to([2.4, y, 0], RIGHT, buff=0.15))
        self.play_bars(LaggedStart(*[Create(p) for p in paths], lag_ratio=0.15), LaggedStart(*[FadeIn(l) for l in labels], lag_ratio=0.15), bars=1)
        self.play_bars(*[p.animate.set_stroke(C_GREEN if ok else C_GREY, width=7 if ok else 1.5, opacity=1 if ok else 0.4)
                         for p, (_, ok) in zip(paths, ends)], bars=0.75)
        # 89–90 先写思考
        self.at_bar(89)
        self.play_bars(FadeOut(VGroup(paths, labels)), bars=0.25)
        think = card(["思考：17 × 24 = 17 × 20 + 17 × 4", "= 340 + 68", "= 408"], title="（先写出思考过程）", tcolor=C_GREY, width=5.2, size=24)
        think.move_to([1.6, -0.35, 0])
        ans = T("答案：408", size=34, color=C_GREEN, weight=BOLD).next_to(think, DOWN, buff=0.3)
        self.play_bars(FadeIn(think[0]), Write(think[1]), bars=1.25)
        self.play_bars(FadeIn(ans), bars=0.5)
        # 91–92 推理模型
        self.at_bar(91)
        rm = T("推理模型：例如 OpenAI o1（2024）、DeepSeek-R1（2025）", size=24, color=C_WHITE).move_to([-0.9, 2.85, 0])
        self.play_bars(FadeIn(rm, shift=DOWN * 0.2), bars=0.75)
        self.at_bar(92.75)
        self.play_bars(FadeOut(VGroup(prob, judge, ans, rm)), think.animate.move_to([-2.4, 0.4, 0]), bars=0.25)
        # 93–94 思考 ≠ 内部真实计算
        self.at_bar(93)
        inner = VGroup(*[Line([2.0 + 0.3 * i, -0.8, 0], [2.0 + 0.3 * j, 1.6, 0], color=C_PURPLE, stroke_width=1, stroke_opacity=0.4)
                         for i in range(8) for j in range(8)])
        il = T("模型内部的计算", size=22, color=C_PURPLE).next_to(inner, DOWN, buff=0.2)
        neq = T("≠", size=64, color=C_RED).move_to([0.9, 0.4, 0])
        self.play_bars(FadeIn(inner), FadeIn(il), bars=0.75)
        self.play_bars(FadeIn(neq, scale=1.4), bars=0.5)
        nt = T("“思考过程”是生成的文字，不等于内部计算的完整记录", size=22, color=C_GREY).move_to([0, -2.2, 0])
        self.play_bars(FadeIn(nt), bars=0.5)
        self.at_bar(94.75)
        self.fade_rest(0.25)
        # 95–96 谄媚
        self.at_bar(95)
        self.tag("风险：谄媚")
        u = bubble("我觉得 2 + 2 = 5", C_BLUE, size=28).move_to([2.2, 1.6, 0])
        bad = bubble("对，你说得对！", C_RED, size=28).move_to([-2.4, 0.3, 0])
        x_ = T("✗", size=48, color=C_RED, weight=BOLD).next_to(bad, RIGHT, buff=0.3)
        good = bubble("其实 2 + 2 = 4。", C_GREEN, size=28).move_to([-2.2, -1.2, 0])
        self.play_bars(FadeIn(u), bars=0.5)
        self.play_bars(FadeIn(bad), FadeIn(x_), bars=0.5)
        self.play_bars(FadeIn(good), bars=0.5)
        sy = T("谄媚：学会顺着用户说", size=26, color=C_RED).move_to([3.0, -1.2, 0])
        self.play_bars(FadeIn(sy), bars=0.25)
        # 97–98 钻空子
        self.at_bar(97)
        self.fade_rest(0.25)
        gauge = Arc(radius=1.1, start_angle=PI, angle=-PI, color=C_GREY, stroke_width=8).move_to([-3.0, 0.5, 0])
        needle = Line(gauge.get_center() + DOWN * 0.55, gauge.get_center() + DOWN * 0.55 + UP * 1.0, color=C_GOLD, stroke_width=6)
        needle.rotate(1.2, about_point=needle.get_start())
        gl = T("分数", size=26, color=C_GOLD).next_to(gauge, DOWN, buff=0.15)
        task = card(["任务：修好程序", "结果：没修好"], width=4.0, size=26).move_to([2.8, 0.5, 0])
        task[1][0][1].set_color(C_RED)
        self.play_bars(FadeIn(gauge), FadeIn(needle), FadeIn(gl), FadeIn(task), bars=0.5)
        self.play_bars(Rotate(needle, -2.2, about_point=needle.get_start()), bars=0.75)
        hk = T("钻奖励的空子：分数高，事情没办好", size=26, color=C_RED).move_to([0, -1.6, 0])
        self.play_bars(FadeIn(hk), bars=0.5)
        # 99–100 公开方法
        self.at_bar(99)
        self.fade_rest(0.25)
        nc = VGroup(T("片中讲的是公开论文里的代表性方法", size=30, color=C_WHITE),
                    T("各公司具体的后训练流程大多不公开", size=28, color=C_GREY)).arrange(DOWN, buff=0.2).move_to([0, 0.4, 0])
        self.play_bars(FadeIn(nc, shift=UP * 0.2), bars=0.75)
        self.at_bar(100.5)
        self.fade_rest(0.5)

    # ------------------------------------------------------------ 间奏二 101–104：要点
    def inst2(self):
        self.at_bar(101)
        self.tag("本集要点")
        head = T("本集要点", size=46, color=C_YELLOW, weight=BOLD)
        pts = [
            "1. 聊天也是续写：对话排成“用户 / 助手”格式的文档，模型续写助手那一段",
            "2. 监督微调：用人写的示范回答继续训练（仍然是猜下一个 token）",
            "3. 基于人类反馈的强化学习：人比较好坏 → 训练打分模型 → 朝高分调（不能离太远）",
            "4. 推理训练：答对给奖励；旋钮数量没变，方向变了",
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
        steps = VGroup(card(["看示范，学格式"], title="① 监督微调", tcolor=C_BLUE, width=3.6, size=24),
                       card(["比较好坏，朝高分调"], title="② 基于反馈的强化学习", tcolor=C_ORANGE, width=3.9, size=22),
                       card(["答对给奖励"], title="③ 推理训练", tcolor=C_GREEN, width=3.4, size=24)).arrange(RIGHT, buff=0.5)
        if steps.width > 13:
            steps.scale_to_fit_width(13)
        steps.move_to([0, 0.9, 0])
        self.play_bars(LaggedStart(FadeIn(steps[0]), FadeIn(steps[1]), lag_ratio=0.4), bars=1)
        # 117–118
        self.at_bar(117)
        self.play_bars(FadeIn(steps[2]), bars=0.5)
        ks, trs = knob_grid(1, 10, seed=4, radius=0.2)
        ks.move_to([0, -1.2, 0])
        self.play_bars(FadeIn(ks), bars=0.25)
        self.play_bars(*[t.animate.set_value(t.get_value() + 0.1) for t in trs], Indicate(self.counter, color=C_YELLOW), bars=0.75)
        # 119–120 靠得住吗？
        self.at_bar(119)
        self.fade_rest(0.25)
        b = bubble("法国的首都是巴黎。", C_GREEN, size=30).move_to([-1.0, 0.5, 0])
        q = T("？", size=72, color=C_RED).next_to(b, RIGHT, buff=0.4)
        rel = T("说的话都靠得住吗？", size=30, color=C_WHITE).next_to(b, DOWN, buff=0.5)
        self.play_bars(FadeIn(b), bars=0.5)
        self.play_bars(FadeIn(q, scale=1.5), FadeIn(rel), bars=0.75)
        # 121–122 下集
        self.at_bar(121)
        self.play_bars(FadeOut(VGroup(b, q, rel)), bars=0.25)
        nxt = VGroup(T("下集", size=30, color=C_GREY), T("能与不能", size=48, color=C_GOLD, weight=BOLD),
                     T("幻觉、工具与看不透的黑箱", size=30, color=C_GOLD)).arrange(DOWN, buff=0.22).move_to([0, 0.5, 0])
        self.play_bars(FadeIn(nxt, shift=UP * 0.2), bars=1)
        self.at_bar(122.25)
        self.play_bars(*[FadeOut(m) for m in self.visible()], bars=0.75)
