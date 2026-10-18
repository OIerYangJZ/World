# 人工智能科普 · 一层层打开黑箱

用大白话 + 3Blue1Brown 风格的几何动画讲清楚 AI 是怎么工作的。全系列正片 10 集 + 番外 5 集，规划见 [`规划.md`](规划.md)。

- 画面：16:9，1920×1080，30 fps，H.264；深色背景、几何动画，配色沿用物理科普系列
- 声音：**成片静音（无音轨）**，只烧录说唱字幕。说唱人声由作者按同一 BPM 用 ACE 生成后自行合成
- 时间：每集的 `bars.py` 是唯一的“时间契约”（BPM 小节网格）。字幕与动画都在小节线上切换，成片帧数 = 总小节数 × 240 / BPM × 30（构建时逐帧核对）

| 集 | 标题 | 曲风 / BPM | 成品视频 | 时长 |
|---|---|---|---|---|
| 正片 01 | 机器怎么“学”：一台会自己拧旋钮的函数 | 经典 boom bap / 88 | [`01_机器怎么学/机器怎么学.mp4`](01_机器怎么学/机器怎么学.mp4) | 5:32.7 |

## 每集文件

```
0X_主题/
├── bars.py        # 时间契约：BPM、段落、每句歌词（字幕稿 / 演唱稿）及画面事件
├── 讲解稿.md      # 大纲、节拍规则、演唱提示、完整歌词与小节表（自动同步）、画面设计、事实核查
├── scene.py       # manim 动画（class Video(BeatScene)，时间点全部由小节表计算）
├── 小节表.csv     # 小节表（给作者对齐 ACE 人声用）
├── 小节表.md      # 同上，Markdown 版
├── 字幕.srt       # 外挂字幕（时间 = 小节线）
├── 字幕.ass       # 烧录用字幕（起止取整到帧）
└── 主题.mp4       # 成片（静音，已烧录字幕）
```

## 构建

```bash
bash common/setup_env.sh                                       # 首次：cairo/pango、Noto CJK 字体、manim 0.19
~/.venvs/manim/bin/python common/build.py 01_机器怎么学 --tables   # 只导出小节表与字幕
~/.venvs/manim/bin/python common/build.py 01_机器怎么学 --preview  # 480p15 预览
~/.venvs/manim/bin/python common/build.py 01_机器怎么学            # 1080p30 成片
```

`common/` 里：`beat.py`（小节网格、校验、导出 CSV / MD / SRT / ASS、演唱稿自动转换）、`style.py`（配色、`BeatScene` 节拍场景基类、旋钮 / 黑箱 / 计数器等公共部件）、`build.py`（一键构建）。
