# -*- coding: utf-8 -*-
"""
物理科普系列 · 公共样式与“讲解节拍”工具

每个视频的场景类继承 Explainer，用 self.say(字幕, *动画) 推进讲解：
  - 字幕立即切换并显示在画面底部；
  - 动画与字幕同时播放；
  - 若动画比阅读字幕所需时间短，自动补足等待，保证观众读得完；
  - 每条字幕的起止时间被记录下来，渲染结束时写出 .srt 文件（供 B站/小红书 上传外挂字幕）。

用法：
    from style import *
    class BlackHole(Explainer):
        def construct(self):
            self.title_card("黑洞", "连光都逃不出的地方")
            self.say("……", Create(circle))
"""
import os
import re
import numpy as np
from manim import *

# ---------------------------------------------------------------- 画面规格：16:9 · 1920x1080 · 30fps
import sys as _sys
if not any(a in _sys.argv for a in ("-ql", "-qm", "-qk", "--quality")):
    config.pixel_width = 1920
    config.pixel_height = 1080
    config.frame_rate = 30
config.background_color = "#0b0d14"

FONT = "Noto Sans CJK SC"
BG = "#0b0d14"

# 3Blue1Brown 风格配色
C_BLUE = "#58C4DD"
C_TEAL = "#5CD0B3"
C_YELLOW = "#FFFF00"
C_GOLD = "#F0AC5F"
C_RED = "#FC6255"
C_PINK = "#FF862F"
C_PURPLE = "#9A72AC"
C_GREEN = "#83C167"
C_GREY = "#888888"
C_WHITE = "#ECECEC"

SUB_FONT_SIZE = 34
SUB_MAX_CHARS = 26          # 每行最多汉字数（约）
SUB_Y = -3.35               # 字幕基线位置
CHARS_PER_SEC = 4.6         # 中文舒适阅读速度


def T(text, size=36, color=C_WHITE, weight=NORMAL, **kw):
    """中文文本"""
    return Text(text, font=FONT, font_size=size, color=color, weight=weight, **kw)


def reading_time(text):
    n = len(re.sub(r"\s", "", text))
    return max(2.2, n / CHARS_PER_SEC + 0.7)


def wrap_sub(text, maxc=SUB_MAX_CHARS):
    """按标点优先把长句分成至多两行"""
    if len(text) <= maxc:
        return text
    mid = len(text) / 2
    best, best_d = None, 1e9
    for i, ch in enumerate(text):
        if ch == "—" and i + 1 < len(text) and text[i + 1] == "—":
            continue
        if ch in "，、；：。？！,;:—" and 0 < i < len(text) - 1:
            d = abs(i + 1 - mid)
            if d < best_d and max(i + 1, len(text) - i - 1) <= maxc + 4:
                best, best_d = i + 1, d
    if best is None:
        best = int(round(mid))
        # 不在数字、英文单词或“——”中间断行
        def bad(k):
            a, b = text[k - 1], text[k]
            return (a.isascii() and a.isalnum() and b.isascii() and b.isalnum()) or (a == b == "—")
        for off in range(len(text)):
            for k in (best - off, best + off):
                if 0 < k < len(text) and not bad(k):
                    best = k
                    break
            else:
                continue
            break
    return text[:best] + "\n" + text[best:]


def fmt_srt_time(t):
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


class SubtitleMixin:
    """字幕 + 节拍系统。与 Scene / MovingCameraScene / ThreeDScene 混用。"""

    def _sub_setup(self):
        self._sub = None
        self._cues = []          # [start, end, text]
        self._fixed = isinstance(self, ThreeDScene)

    def _now(self):
        return self.renderer.time

    def _make_sub(self, text):
        txt = T(wrap_sub(text), size=SUB_FONT_SIZE, color=WHITE, line_spacing=0.9)
        txt.move_to([0, SUB_Y, 0])
        if txt.width > 13.6:
            txt.scale_to_fit_width(13.6)
        back = BackgroundRectangle(txt, color=BLACK, fill_opacity=0.55, buff=0.16,
                                   corner_radius=0.08)
        g = VGroup(back, txt)
        g.move_to([0, SUB_Y + (0.22 if "\n" in txt.text or txt.height > 0.7 else 0), 0])
        g.set_z_index(1000)
        return g

    def _set_sub(self, text):
        self._close_cue()
        if self._sub is not None:
            self.remove(self._sub)
            self._sub = None
        if text:
            self._sub = self._make_sub(text)
            if self._fixed:
                self.add_fixed_in_frame_mobjects(self._sub)
            self.add(self._sub)
            self._cues.append([self._now(), None, text])

    def _close_cue(self):
        if self._cues and self._cues[-1][1] is None:
            self._cues[-1][1] = self._now()

    def say(self, text, *anims, run_time=None, extra=0.0, rate_func=None, lag_ratio=None):
        """显示一条字幕，同时播放动画，并保证字幕停留足够长。"""
        self._set_sub(text)
        need = reading_time(text) + extra
        t0 = self._now()
        if anims:
            kw = {}
            if run_time is not None:
                kw["run_time"] = run_time
            if rate_func is not None:
                kw["rate_func"] = rate_func
            if lag_ratio is not None:
                kw["lag_ratio"] = lag_ratio
            self.play(*anims, **kw)
        rest = need - (self._now() - t0)
        if rest > 0.05:
            self.wait(rest)

    def clear_sub(self):
        self._set_sub(None)

    # ------------------------------------------------------------ 结构化元素
    def title_card(self, title, subtitle, series="物理科普 · 一次讲透"):
        self.clear_sub()
        s = T(series, size=28, color=C_GREY)
        t = T(title, size=96, weight=BOLD, color=C_WHITE)
        st = T(subtitle, size=44, color=C_BLUE)
        g = VGroup(s, t, st).arrange(DOWN, buff=0.45)
        line = Line(LEFT * 3, RIGHT * 3, color=C_BLUE, stroke_width=2).next_to(t, DOWN, buff=0.22)
        st.next_to(line, DOWN, buff=0.35)
        if self._fixed:
            self.add_fixed_in_frame_mobjects(s, t, st, line)
        self.play(FadeIn(s, shift=DOWN * 0.2), Write(t), run_time=1.6)
        self.play(GrowFromCenter(line), FadeIn(st, shift=UP * 0.2), run_time=1.0)
        self.wait(2.0)
        self.play(*[FadeOut(m) for m in (s, t, st, line)], run_time=0.8)

    def chapter(self, idx, name):
        """章节标题卡"""
        self.clear_sub()
        n = T(idx, size=40, color=C_YELLOW)
        t = T(name, size=64, weight=BOLD)
        g = VGroup(n, t).arrange(DOWN, buff=0.35)
        if self._fixed:
            self.add_fixed_in_frame_mobjects(g)
        self.play(FadeIn(n, shift=RIGHT * 0.3), FadeIn(t, shift=UP * 0.3), run_time=0.9)
        self.wait(1.3)
        self.play(FadeOut(g), run_time=0.6)

    def corner_title(self, text):
        """左上角的小标题（当前章节提示）"""
        m = T(text, size=26, color=C_GREY).to_corner(UL, buff=0.4)
        if self._fixed:
            self.add_fixed_in_frame_mobjects(m)
        return m

    def end_card(self, lines, closing="感谢观看 · 物理科普 · 一次讲透"):
        self.clear_sub()
        head = T("本集要点", size=52, weight=BOLD, color=C_YELLOW)
        items = VGroup(*[T(f"{i+1}. {l}", size=34) for i, l in enumerate(lines)])
        items.arrange(DOWN, aligned_edge=LEFT, buff=0.32)
        g = VGroup(head, items).arrange(DOWN, buff=0.6)
        if g.height > 6.4:
            g.scale_to_fit_height(6.4)
        if self._fixed:
            self.add_fixed_in_frame_mobjects(g)
        self.play(FadeIn(head, shift=DOWN * 0.2))
        for it in items:
            self.play(FadeIn(it, shift=RIGHT * 0.3), run_time=0.5)
        self.wait(max(4.0, sum(len(l) for l in lines) / CHARS_PER_SEC * 0.6))
        self.play(FadeOut(g))
        c = T(closing, size=36, color=C_GREY)
        if self._fixed:
            self.add_fixed_in_frame_mobjects(c)
        self.play(FadeIn(c))
        self.wait(2.5)
        self.play(FadeOut(c), run_time=1.2)
        self.wait(0.5)

    # ------------------------------------------------------------ 字幕文件
    def write_srt(self):
        self._close_cue()
        out = os.environ.get("SRT_OUT")
        if not out:
            return
        with open(out, "w", encoding="utf-8") as f:
            for i, (a, b, text) in enumerate(self._cues, 1):
                f.write(f"{i}\n{fmt_srt_time(a)} --> {fmt_srt_time(b)}\n{text}\n\n")

    def fade_all(self, run_time=0.8, keep=()):
        mobs = [m for m in self.mobjects if m is not self._sub and m not in keep]
        if mobs:
            self.play(*[FadeOut(m) for m in mobs], run_time=run_time)


class Explainer(SubtitleMixin, MovingCameraScene):
    def setup(self):
        super().setup()
        self._sub_setup()

    def tear_down(self):
        self.write_srt()
        super().tear_down()


class Explainer3D(SubtitleMixin, ThreeDScene):
    def setup(self):
        super().setup()
        self._sub_setup()

    def tear_down(self):
        self.write_srt()
        super().tear_down()


def eq(tex, size=48, color=C_WHITE):
    """公式（需要 LaTeX）"""
    return MathTex(tex, font_size=size, color=color)
