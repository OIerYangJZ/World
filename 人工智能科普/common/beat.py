# -*- coding: utf-8 -*-
"""
人工智能科普系列 · BPM 小节网格工具（不依赖 manim）

每集目录里的 bars.py 是唯一的“时间契约”，定义：
    BPM        —— 每分钟拍数（4/4 拍，一小节 = 4 拍）
    SECTIONS   —— [(段落名, 起始小节, 小节数), ...]，必须首尾相接、从第 1 小节开始
    LINES      —— [Line(起始小节, 小节数, 字幕稿, sung=演唱稿或None, visual=画面事件), ...]

起始时间 = (小节号 − 1) × 240 / BPM。字幕严格在小节线上切换，不做提前量。
由它导出：小节表.csv、小节表.md、字幕.srt、字幕.ass（烧录用），动画里的时间点也由它计算。
"""
import csv
import importlib.util
import os
import re
from dataclasses import dataclass


@dataclass
class Line:
    bar: int              # 起始小节（1 起）
    bars: int             # 占几个小节
    sub: str              # 字幕稿（烧进画面 / SRT）
    sung: str = None      # 演唱稿（喂给 ACE）；None 时由 sung_text() 自动生成
    visual: str = ""      # 画面事件


def load_bars(ep_dir):
    path = os.path.join(ep_dir, "bars.py")
    spec = importlib.util.spec_from_file_location("bars", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def bar_len(bpm):
    return 240.0 / bpm


def bar_time(bpm, n):
    """第 n 小节（1 起）的起始时间（秒）"""
    return (n - 1) * bar_len(bpm)


def total_bars(sections):
    return sum(n for _, _, n in sections)


def section_of(sections, bar):
    for name, s, n in sections:
        if s <= bar < s + n:
            return name
    raise ValueError(f"小节 {bar} 不在任何段落里")


# ---------------------------------------------------------------- 演唱稿自动转换
_DIG = "零一二三四五六七八九"
ACRONYMS = {  # 按字母唱的缩写：演唱稿里用空格隔开
    "GPT": "G P T", "RLHF": "R L H F", "SFT": "S F T", "DPO": "D P O", "ViT": "V I T",
    "AI": "A I", "MLP": "M L P", "GPU": "G P U",
}


def _int_to_cn(n):
    if n == 0:
        return "零"
    units = ["", "十", "百", "千"]
    big = ["", "万", "亿", "万亿"]
    parts, i = [], 0
    while n > 0:
        n, chunk = divmod(n, 10000)
        if chunk:
            s, zero = "", False
            for k in range(3, -1, -1):
                d = chunk // (10 ** k) % 10
                if d:
                    if zero:
                        s += "零"
                        zero = False
                    s += _DIG[d] + units[k]
                elif s:
                    zero = True
            parts.append((s, i, chunk))
        else:
            parts.append(("", i, 0))
        i += 1
    out = ""
    for idx in range(len(parts) - 1, -1, -1):
        s, k, chunk = parts[idx]
        if s:
            if out and chunk < 1000:
                out += "零"
            out += s + big[k]
    out = out.replace("零零", "零")
    if out.startswith("一十"):
        out = out[1:]
    return out


def sung_text(sub):
    """字幕稿 → 演唱稿：数字写汉字、年份逐位读、缩写按字母拆开、去掉不唱的符号"""
    s = sub
    s = re.sub(r"(\d{4})(?=\s*年)", lambda m: "".join(_DIG[int(c)] for c in m.group(1)), s)
    s = re.sub(r"(\d+)%", lambda m: "百分之" + _int_to_cn(int(m.group(1))), s)
    s = re.sub(r"\d{1,3}(?:,\d{3})+|\d+", lambda m: _int_to_cn(int(m.group(0).replace(",", ""))), s)
    for k, v in ACRONYMS.items():
        s = re.sub(rf"(?<![A-Za-z]){k}(?![A-Za-z])", v, s)
    s = re.sub(r"([A-Za-z])-(?=[零一二三四五六七八九十])", r"\1 ", s)   # GPT-3 → G P T 三
    s = s.replace("“", "").replace("”", "").replace("《", "").replace("》", "").replace("——", "，")
    return s


# ---------------------------------------------------------------- 校验
def reading_load(text):
    """字幕阅读量：汉字计 1；英文短词（≤5 字母）计 1，长词计 2；标点不计"""
    n = 0
    for w in re.findall(r"[A-Za-z]+", text):
        n += 1 if len(w) <= 5 else 2
    n += len(re.findall(r"[一-鿿0-9]", text))
    return n


def validate(mod, chars_per_sec=4.6):
    """检查段落连续、歌词不重叠且落在有人声的段落内；返回 (警告列表, 总小节数)"""
    warns = []
    secs = mod.SECTIONS
    expect = 1
    for name, s, n in secs:
        if s != expect:
            raise ValueError(f"段落 {name} 应从第 {expect} 小节开始，实际 {s}")
        expect = s + n
    tot = total_bars(secs)
    last_end = 1
    for ln in sorted(mod.LINES, key=lambda l: l.bar):
        if ln.bar < last_end:
            raise ValueError(f"第 {ln.bar} 小节的歌词与上一句重叠：{ln.sub}")
        if ln.bar + ln.bars - 1 > tot:
            raise ValueError(f"歌词超出总小节数：{ln.sub}")
        a, b = section_of(secs, ln.bar), section_of(secs, ln.bar + ln.bars - 1)
        if a != b:
            raise ValueError(f"歌词跨段落：{ln.sub}")
        dur = ln.bars * bar_len(mod.BPM)
        load = reading_load(ln.sub)
        if load / dur > chars_per_sec:
            warns.append(f"[阅读超速] 小节 {ln.bar}：{load} 字 / {dur:.2f}s = {load/dur:.1f} 字/秒 > {chars_per_sec}：{ln.sub}")
        last_end = ln.bar + ln.bars
    return warns, tot


# ---------------------------------------------------------------- 导出
def fmt_srt(t):
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def fmt_ass(t):
    cs = int(round(t * 100))
    h, cs = divmod(cs, 360000)
    m, cs = divmod(cs, 6000)
    s, cs = divmod(cs, 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def fmt_mmss(t):
    m, s = divmod(t, 60)
    return f"{int(m)}:{s:05.2f}"


def cues(mod):
    out = []
    for ln in sorted(mod.LINES, key=lambda l: l.bar):
        a = bar_time(mod.BPM, ln.bar)
        b = bar_time(mod.BPM, ln.bar + ln.bars)
        out.append((a, b, ln))
    return out


def write_srt(mod, path):
    with open(path, "w", encoding="utf-8") as f:
        for i, (a, b, ln) in enumerate(cues(mod), 1):
            f.write(f"{i}\n{fmt_srt(a)} --> {fmt_srt(b)}\n{ln.sub}\n\n")


ASS_HEAD = """[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Rap,Noto Sans CJK SC,54,&H00ECECEC,&H00ECECEC,&H73000000,&H73000000,0,0,0,0,100,100,1,0,3,14,0,2,120,120,58,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def write_ass(mod, path, fps=30):
    """烧录用 ASS。起止时间取整到帧边界（与动画用同一套帧网格），避免 libass 的 1/100 秒取整误差。"""
    import math

    def cs_of(t):
        # 第 k 帧（k = round(t·fps)）的显示时刻是 k/fps；取不超过它的整厘秒，
        # 保证该帧正好是字幕出现（或消失）的第一帧
        k = round(t * fps)
        cs = math.floor(k * 100 / fps + 1e-9)
        h, cs = divmod(cs, 360000)
        m, cs = divmod(cs, 6000)
        s, cs = divmod(cs, 100)
        return f"{h}:{m:02d}:{s:02d}.{cs:02d}"

    with open(path, "w", encoding="utf-8") as f:
        f.write(ASS_HEAD)
        for a, b, ln in cues(mod):
            text = ln.sub.replace("\n", r"\N")
            f.write(f"Dialogue: 0,{cs_of(a)},{cs_of(b)},Rap,,0,0,0,,{text}\n")


def table_rows(mod):
    """小节表：每个段落一行（器乐段 / 无词处）或每句歌词一行"""
    bpm, rows = mod.BPM, []
    lines = sorted(mod.LINES, key=lambda l: l.bar)
    for name, s, n in mod.SECTIONS:
        inside = [l for l in lines if s <= l.bar < s + n]
        cur = s
        for ln in inside:
            if ln.bar > cur:
                rows.append((cur, ln.bar - cur, name, "", "", "（器乐）"))
            rows.append((ln.bar, ln.bars, name, ln.sung or sung_text(ln.sub), ln.sub, ln.visual))
            cur = ln.bar + ln.bars
        if cur < s + n:
            vis = getattr(mod, "INSTRUMENTAL_VISUALS", {}).get(name, "（器乐）")
            rows.append((cur, s + n - cur, name, "", "", vis))
    out = []
    for bar, nb, name, sung, sub, vis in rows:
        a, b = bar_time(bpm, bar), bar_time(bpm, bar + nb)
        rng = f"{bar}" if nb == 1 else f"{bar}–{bar + nb - 1}"
        out.append(dict(小节=rng, 段落=name, 起始=fmt_mmss(a), 结束=fmt_mmss(b),
                        起始秒=f"{a:.3f}", 结束秒=f"{b:.3f}", 演唱稿=sung, 字幕稿=sub, 画面事件=vis))
    return out


def write_csv(mod, path):
    rows = table_rows(mod)
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def md_table(mod):
    bpm = mod.BPM
    tot = total_bars(mod.SECTIONS)
    head = (f"- BPM：{bpm}（4/4 拍），每小节 {bar_len(bpm):.4f} 秒，共 {tot} 小节，"
            f"总时长 {fmt_mmss(tot * bar_len(bpm))}（{tot * bar_len(bpm):.3f} 秒）\n"
            f"- 起始时间 = (小节号 − 1) × 240 / {bpm}；字幕在小节线上切换，不做提前量\n\n")
    seg = "| 段落 | 小节 | 起始 |\n|---|---|---|\n" + "".join(
        f"| {name} | {s}–{s + n - 1} | {fmt_mmss(bar_time(bpm, s))} |\n" for name, s, n in mod.SECTIONS)
    t = "| 小节 | 段落 | 起始 | 结束 | 演唱稿（ACE） | 字幕稿 | 画面事件 |\n|---|---|---|---|---|---|---|\n"
    for r in table_rows(mod):
        cells = [r["小节"], r["段落"], r["起始"], r["结束"], r["演唱稿"], r["字幕稿"], r["画面事件"]]
        t += "| " + " | ".join(c.replace("|", "\\|") for c in cells) + " |\n"
    return head + seg + "\n" + t


def write_md(mod, path, title):
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"# 小节表 · {title}\n\n")
        f.write("> 由 `bars.py` 自动生成（`python common/build.py <集目录> --tables`），请勿手改。\n\n")
        f.write(md_table(mod))
