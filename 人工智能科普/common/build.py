# -*- coding: utf-8 -*-
"""
一键构建某一集：校验小节表 → 导出 小节表.csv / 小节表.md / 字幕.srt / 字幕.ass
→ manim 渲染（静音）→ ffmpeg 烧录字幕 → 校验成片时长与帧数。

    ~/.venvs/manim/bin/python common/build.py 01_机器怎么学             # 1080p30 成品
    ~/.venvs/manim/bin/python common/build.py 01_机器怎么学 --preview   # 480p15 快速预览
    ~/.venvs/manim/bin/python common/build.py 01_机器怎么学 --tables    # 只导出表格与字幕

每集目录内需有 bars.py（时间契约）与 scene.py（class Video(BeatScene)）。
成片没有音轨：说唱人声由作者按同一 BPM 用 ACE 生成后自行合成。
"""
import glob
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import beat  # noqa: E402

EPISODES = {
    "01_机器怎么学": "机器怎么学",
    "02_神经网络": "神经网络",
    "03_梯度下降": "梯度下降",
    "04_反向传播": "反向传播",
    "05_词向量": "词向量",
    "06_注意力": "注意力",
    "07_Transformer": "Transformer",
    "08_预训练": "预训练",
}

MANIM = os.path.join(os.path.dirname(sys.executable), "manim")
if not os.path.exists(MANIM):
    MANIM = shutil.which("manim")


def run(cmd, **kw):
    print("+", " ".join(cmd), flush=True)
    subprocess.run(cmd, check=True, **kw)


def probe(path):
    out = subprocess.check_output([
        "ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0",
        "-show_entries", "stream=nb_read_frames,width,height,r_frame_rate",
        "-of", "default=nw=1", path]).decode()
    info = dict(l.split("=", 1) for l in out.strip().splitlines())
    streams = subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "stream=codec_type",
        "-of", "csv=p=0", path]).decode().split()
    info["streams"] = streams
    return info


def export_tables(d, mod, title, fps):
    warns, tot = beat.validate(mod)
    for w in warns:
        print("警告", w)
    beat.write_csv(mod, os.path.join(d, "小节表.csv"))
    beat.write_md(mod, os.path.join(d, "小节表.md"), title)
    beat.write_srt(mod, os.path.join(d, "字幕.srt"))
    beat.write_ass(mod, os.path.join(d, "字幕.ass"), fps=fps)
    # 把完整小节表同步进讲解稿（两个标记之间）
    doc = os.path.join(d, "讲解稿.md")
    if os.path.exists(doc):
        s = open(doc, encoding="utf-8").read()
        a, b = "<!-- BAR_TABLE_BEGIN -->", "<!-- BAR_TABLE_END -->"
        if a in s and b in s:
            s = s[:s.index(a) + len(a)] + "\n" + beat.md_table(mod) + "\n" + s[s.index(b):]
            open(doc, "w", encoding="utf-8").write(s)
    print(f"小节表：{tot} 小节，{tot * beat.bar_len(mod.BPM):.3f} 秒，{len(mod.LINES)} 句歌词")
    return tot


def main():
    ep = sys.argv[1].rstrip("/").split("/")[-1]
    preview = "--preview" in sys.argv
    title = EPISODES[ep]
    d = os.path.join(ROOT, ep)
    mod = beat.load_bars(d)
    fps = 15 if preview else 30
    tot = export_tables(d, mod, title, 30)
    if "--tables" in sys.argv:
        return
    ass = os.path.join(d, "字幕.ass")
    media = os.path.join(d, "media")
    env = dict(os.environ, PYTHONPATH=HERE + os.pathsep + os.environ.get("PYTHONPATH", ""))
    q = "-ql" if preview else "-qh"
    run([MANIM, q, "--disable_caching", "--media_dir", media, "-o", "raw.mp4",
         os.path.join(d, "scene.py"), "Video"], env=env, cwd=d)
    raw = glob.glob(os.path.join(media, "videos", "scene", "*", "raw.mp4"))
    raw = max(raw, key=os.path.getmtime)
    out = os.path.join(d, f"{title}{'_预览' if preview else ''}.mp4")
    sub = ass
    if preview:
        sub = os.path.join(media, "preview.ass")
        beat.write_ass(mod, sub, fps=15)
    # 烧录字幕；-an 保证成片静音（无音轨）
    esc = sub.replace("\\", "/").replace(":", r"\:").replace("'", r"\'")
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", raw,
         "-vf", f"subtitles='{esc}'",
         "-an", "-c:v", "libx264", "-preset", "slow", "-crf", "28" if preview else "18",
         "-pix_fmt", "yuv420p", "-r", str(fps), "-movflags", "+faststart",
         "-metadata", f"title={title}", out])
    info = probe(out)
    expect = round(tot * beat.bar_len(mod.BPM) * fps)
    n = int(info["nb_read_frames"])
    print(f"成片：{out}  {info['width']}x{info['height']} @ {info['r_frame_rate']}  "
          f"{n} 帧（期望 {expect}）  音轨：{'无' if 'audio' not in info['streams'] else '有'}")
    if n != expect:
        raise SystemExit(f"帧数与小节网格不符：{n} ≠ {expect}")
    if "audio" in info["streams"]:
        raise SystemExit("成片不应包含音轨")
    print(f"OK  {os.path.getsize(out) / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
