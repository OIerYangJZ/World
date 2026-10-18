# -*- coding: utf-8 -*-
"""
人工智能科普系列 · 公共样式与“节拍网格”场景基类

与物理科普的 Explainer 不同：这里字幕不由 manim 绘制，而是由 build.py 依据 bars.py
导出 ASS 后用 ffmpeg 烧录，起止时间与小节线逐帧对齐。动画同样对齐到小节线：

    from style import *
    class Video(BeatScene):
        def construct(self):
            self.at_bar(5)                         # 等到第 5 小节开头（之前若超时会报错）
            self.play_bars(Create(c), bars=1)      # 动画正好占 1 小节
            self.play_bars(FadeIn(t), bars=0.5)    # 半小节 = 2 拍
            ...
            self.finish()                          # 停在最后一小节结束处

所有时长都换算到“绝对帧号”：第 n 小节开头 = round((n−1)·240/BPM·fps) 帧，
因此不会累计取整误差，成片时长 = 总小节数 × 240 / BPM（精确到 1 帧）。
"""
import os
import sys

import numpy as np
from manim import *

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import beat  # noqa: E402

# ---------------------------------------------------------------- 画面规格：16:9 · 1920x1080 · 30fps
if not any(a in sys.argv for a in ("-ql", "-qm", "-qk", "--quality")):
    config.pixel_width = 1920
    config.pixel_height = 1080
    config.frame_rate = 30
config.background_color = "#0b0d14"

FONT = "Noto Sans CJK SC"
BG = "#0b0d14"


# ---------------------------------------------------------------- 兼容补丁
# manim 0.19 的 Camera.display_image_mobject 用 Image.fromarray(float 零数组, mode="RGBA")
# 新建整帧画布，Pillow ≥ 11.3 起不再接受（报 ValueError，随后写帧线程挂起）。
# 这里换成 Image.new，其余逻辑与原实现一致。只影响 ImageMobject。
def _display_image_mobject(self, image_mobject, pixel_array):
    from PIL import Image
    from scipy.spatial.distance import pdist
    corner_coords = self.points_to_pixel_coords(image_mobject, image_mobject.points)
    ul_coords, ur_coords, dl_coords, _ = corner_coords
    right_vect = ur_coords - ul_coords
    down_vect = dl_coords - ul_coords
    center_coords = ul_coords + (right_vect + down_vect) / 2
    sub_image = Image.fromarray(np.ascontiguousarray(image_mobject.get_pixel_array(), dtype=np.uint8))
    if sub_image.mode != "RGBA":
        sub_image = sub_image.convert("RGBA")
    pixel_width = max(int(pdist([ul_coords, ur_coords]).item()), 1)
    pixel_height = max(int(pdist([ul_coords, dl_coords]).item()), 1)
    sub_image = sub_image.resize((pixel_width, pixel_height), resample=image_mobject.resampling_algorithm)
    adjusted_angle = -int(360 * angle_of_vector(right_vect) / TAU)
    if adjusted_angle != 0:
        sub_image = sub_image.rotate(adjusted_angle, resample=image_mobject.resampling_algorithm, expand=1)
    full_image = Image.new("RGBA", (self.pixel_width, self.pixel_height), (0, 0, 0, 0))
    new_ul = (center_coords - np.array(sub_image.size) / 2).astype(int)
    full_image.paste(sub_image, box=(new_ul[0], new_ul[1], new_ul[0] + sub_image.size[0],
                                     new_ul[1] + sub_image.size[1]))
    self.overlay_PIL_image(pixel_array, full_image)


Camera.display_image_mobject = _display_image_mobject

# 3Blue1Brown 风格配色（与物理科普一致），全系列颜色语义见 规划.md 1.5
C_BLUE = "#58C4DD"     # 输入 / 数据 / token
C_TEAL = "#5CD0B3"
C_YELLOW = "#FFFF00"   # 参数 / 旋钮
C_GOLD = "#F0AC5F"     # 输出 / 概率 / 答案
C_RED = "#FC6255"      # 误差 / 损失
C_ORANGE = "#FF862F"
C_PURPLE = "#9A72AC"   # 注意力
C_GREEN = "#83C167"    # 梯度 / 更新方向
C_GREY = "#888888"     # 不活跃
C_DARK = "#2a2f3d"
C_WHITE = "#ECECEC"

SERIES = "人工智能科普 · 一层层打开黑箱"
SUB_SAFE_Y = -2.75     # 字幕区（ASS 烧录在底部）上沿，主体画面不要低于这条线


def T(text, size=36, color=C_WHITE, weight=NORMAL, **kw):
    """中文文本"""
    return Text(text, font=FONT, font_size=size, color=color, weight=weight, **kw)


class BeatScene(Scene):
    """按 bars.py 的 BPM 小节网格推进的场景"""

    EP_DIR = None  # 子类所在目录；默认取 scene.py 所在目录

    def setup(self):
        super().setup()
        ep_dir = self.EP_DIR or os.getcwd()
        self.bars_mod = beat.load_bars(ep_dir)
        self.bpm = self.bars_mod.BPM
        self.bar = beat.bar_len(self.bpm)
        self.total_bars = beat.total_bars(self.bars_mod.SECTIONS)
        self.fps = config.frame_rate
        self._pos = 1.0  # 逻辑位置（小节，精确值），避免按帧反推时的取整累积

    # ------------------------------------------------------------ 帧网格
    def frame_now(self):
        return int(round(self.renderer.time * self.fps))

    def frame_of_bar(self, n):
        """第 n 小节开头（n 可为小数，例如 5.5 = 第 5 小节第 3 拍）"""
        return int(round(beat.bar_time(self.bpm, n) * self.fps))

    def _advance(self, target):
        cur = self.frame_now()
        if cur > target:
            raise RuntimeError(f"动画超时：已到第 {cur} 帧，目标第 {target} 帧"
                               f"（小节 {target / self.fps / self.bar + 1:.2f}）")
        d = target - cur
        if d == 0:
            return
        moving = (self.always_update_mobjects or self.updaters or
                  any(m.has_time_based_updater() for m in self.get_mobject_family_members()))
        if moving:
            self.wait((d - 0.5) / self.fps, frozen_frame=False)
        else:
            self.wait((d + 0.5) / self.fps, frozen_frame=True)
        assert self.frame_now() == target, (self.frame_now(), target)

    def at_bar(self, n):
        """静止等待到第 n 小节开头"""
        if n < self._pos - 1e-9:
            raise RuntimeError(f"动画超时：逻辑位置已到小节 {self._pos:.3f}，目标小节 {n}")
        self._advance(self.frame_of_bar(n))
        self._pos = float(n)

    def play_bars(self, *anims, bars=1.0, until=None, **kw):
        """播放动画，时长正好 bars 个小节（或播放到第 until 小节开头）"""
        cur = self.frame_now()
        end = float(until) if until is not None else self._pos + bars
        target = self.frame_of_bar(end)
        d = target - cur
        if d <= 0:
            raise RuntimeError("play_bars 时长为 0")
        self.play(*anims, run_time=(d - 0.5) / self.fps, **kw)
        assert self.frame_now() == target, (self.frame_now(), target)
        self._pos = end

    def beats(self, n):
        """n 拍对应的小节数（4/4）"""
        return n / 4.0

    def finish(self):
        self.at_bar(self.total_bars + 1)

    # ------------------------------------------------------------ 常驻 UI（第 02 集起使用；第 01 集在自己的 scene.py 里有同名实现）
    def set_counter(self, text, bars=0.5):
        """右上角旋钮计数器：第一次淡入，之后整体变形成新数字"""
        new = knob_counter(text)
        if getattr(self, "counter", None) is None:
            self.counter = new
            self.play_bars(FadeIn(new, shift=LEFT * 0.2), bars=bars)
        else:
            self.play_bars(Transform(self.counter, new), bars=bars)

    def tag(self, text, bars=0.25):
        """左上角段落提示"""
        t = section_tag(text)
        old = getattr(self, "_tag", None)
        anims = [FadeIn(t, shift=RIGHT * 0.2)]
        if old is not None and old in self.mobjects:
            anims.append(FadeOut(old))
        self._tag = t
        self.play_bars(*anims, bars=bars)

    def keep(self):
        return [m for m in (getattr(self, "counter", None), getattr(self, "_tag", None)) if m is not None]

    def visible(self):
        return [m for m in self.mobjects if not isinstance(m, ValueTracker)]

    def fade_rest(self, bars=0.5, extra_keep=()):
        """淡出除常驻 UI 以外的全部元素"""
        keep = self.keep() + list(extra_keep)
        mobs = [m for m in self.visible() if m not in keep]
        if mobs:
            self.play_bars(*[FadeOut(m) for m in mobs], bars=bars)
        else:
            self.at_bar(self._pos + bars)

    # ------------------------------------------------------------ 结构化元素
    def clear(self, bars=0.5, keep=()):
        mobs = [m for m in self.mobjects if m not in keep]
        if mobs:
            self.play_bars(*[FadeOut(m) for m in mobs], bars=bars)


# ---------------------------------------------------------------- 通用部件
class Knob(VGroup):
    """旋钮：圆盘 + 指针 + 标签；value_tracker 的值按 [vmin, vmax] 映射到 −135°…+135°"""

    def __init__(self, label, tracker, vmin, vmax, radius=0.55, color=C_YELLOW, **kw):
        super().__init__(**kw)
        self.tracker, self.vmin, self.vmax = tracker, vmin, vmax
        disk = Circle(radius=radius, stroke_color=color, stroke_width=4,
                      fill_color=C_DARK, fill_opacity=1)
        ticks = VGroup(*[
            Line(ORIGIN, UP * 0.12, stroke_width=2, color=C_GREY)
            .shift(UP * (radius + 0.1)).rotate(a, about_point=ORIGIN)
            for a in np.linspace(135 * DEGREES, -135 * DEGREES, 11)
        ])
        self.disk = disk
        lab = T(label, size=30, color=color).next_to(disk, DOWN, buff=0.28)
        self.ptr = always_redraw(lambda: Line(
            disk.get_center(), disk.get_center() + radius * 0.82 * self._dir(),
            stroke_width=6, color=color))
        dot = Dot(disk.get_center(), radius=0.06, color=color)
        self.add(disk, ticks, self.ptr, dot, lab)

    def _dir(self):
        v = self.tracker.get_value()
        f = (v - self.vmin) / (self.vmax - self.vmin)
        f = min(max(f, 0), 1)
        th = (225 - 270 * f) * DEGREES   # f=0 指向左下，f=1 指向右下
        return np.array([np.cos(th), np.sin(th), 0])


def knob_counter(n_text="2", label="旋钮"):
    """右上角的旋钮计数器（全系列固定 UI）"""
    icon = VGroup(Circle(radius=0.16, stroke_color=C_YELLOW, stroke_width=3),
                  Line(ORIGIN, UP * 0.13, stroke_color=C_YELLOW, stroke_width=3))
    txt = T(f"{label} × ", size=28, color=C_GREY)
    num = T(n_text, size=34, color=C_YELLOW, weight=BOLD)
    g = VGroup(icon, txt, num).arrange(RIGHT, buff=0.12)
    g.to_corner(UR, buff=0.4)
    return g


def black_box(w=3.0, h=2.2, depth=0.5, color=C_GREY):
    """半透明“黑箱”：正面 + 斜后方的面，带一点立体感"""
    front = RoundedRectangle(width=w, height=h, corner_radius=0.12,
                             stroke_color=color, stroke_width=3,
                             fill_color="#151a26", fill_opacity=0.92)
    off = np.array([depth, depth * 0.6, 0])
    back = front.copy().set_fill(opacity=0.4).set_stroke(opacity=0.5).shift(off)
    edges = VGroup(*[
        Line(front.get_corner(c), front.get_corner(c) + off, stroke_color=color,
             stroke_width=2, stroke_opacity=0.6) for c in (UL, UR, DR)
    ])
    q = T("?", size=72, color=C_GREY, weight=BOLD).move_to(front)
    g = VGroup(back, edges, front, q)
    g.front, g.q = front, q
    return g


def title_card(ep_label, title, subtitle):
    s = T(SERIES, size=28, color=C_GREY)
    e = T(ep_label, size=32, color=C_YELLOW)
    t = T(title, size=84, weight=BOLD, color=C_WHITE)
    st = T(subtitle, size=40, color=C_BLUE)
    g = VGroup(s, e, t, st).arrange(DOWN, buff=0.4)
    line = Line(LEFT * 3.2, RIGHT * 3.2, color=C_BLUE, stroke_width=2).next_to(t, DOWN, buff=0.22)
    st.next_to(line, DOWN, buff=0.32)
    return VGroup(s, e, t, line, st)


def section_tag(text):
    """左上角的小标题（当前段落提示）"""
    return T(text, size=26, color=C_GREY).to_corner(UL, buff=0.4)
