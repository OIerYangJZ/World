# -*- coding: utf-8 -*-
"""
一键构建某一集：渲染动画 → 生成字幕文件 → 合成背景音乐 → 混流输出成品 MP4。

    /opt/mvenv/bin/python common/build.py 01_黑洞            # 1080p30 成品
    /opt/mvenv/bin/python common/build.py 01_黑洞 --preview  # 480p15 快速预览

每集目录内需有 scene.py，其中定义名为 Video 的场景类。
"""
import os
import sys
import glob
import shutil
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

EPISODES = {
    "01_黑洞": ("黑洞：连光都逃不出的地方", "blackhole"),
    "02_量子场": ("量子场：万物底层的“场”", "quantum"),
    "03_电磁波": ("电磁波：光是怎样传播的", "em"),
    "04_广义相对论": ("广义相对论：引力就是时空的弯曲", "gr"),
    "05_狭义相对论": ("狭义相对论：光速不变带来的一切", "sr"),
}

MANIM = shutil.which("manim") or "/opt/mvenv/bin/manim"
PY = sys.executable


def run(cmd, **kw):
    print("+", " ".join(cmd), flush=True)
    subprocess.run(cmd, check=True, **kw)


def duration_of(path):
    out = subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                   "-of", "default=nw=1:nk=1", path])
    return float(out)


def main():
    ep = sys.argv[1].rstrip("/").split("/")[-1]
    preview = "--preview" in sys.argv
    title, style = EPISODES[ep]
    d = os.path.join(ROOT, ep)
    media = os.path.join(d, "media")
    env = dict(os.environ, SRT_OUT=os.path.join(d, "字幕.srt"),
               PYTHONPATH=HERE + os.pathsep + os.environ.get("PYTHONPATH", ""))
    q = "-ql" if preview else "-qh"
    run([MANIM, q, "--disable_caching", "--media_dir", media, "-o", "raw.mp4",
         os.path.join(d, "scene.py"), "Video"], env=env, cwd=d)
    if preview:
        # 预览模式：480p15，本地查看用（覆盖 manim 默认的 854x480）
        pass
    raw = glob.glob(os.path.join(media, "videos", "scene", "*", "raw.mp4"))
    raw = max(raw, key=os.path.getmtime)
    dur = duration_of(raw)
    wav = os.path.join(d, "media", "music.wav")
    run([PY, os.path.join(HERE, "music.py"), f"{dur + 1:.2f}", wav, style])
    name = title.split("：")[0]
    out = os.path.join(d, f"{name}{'_预览' if preview else ''}.mp4")
    fo = max(0.0, dur - 4)
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", raw, "-i", wav,
         "-map", "0:v", "-map", "1:a",
         "-c:v", "libx264", "-preset", "slow", "-crf", "20" if not preview else "28",
         "-pix_fmt", "yuv420p", "-r", "30" if not preview else "15",
         "-af", f"afade=t=out:st={fo:.2f}:d=4,volume=0.9",
         "-c:a", "aac", "-b:a", "192k", "-shortest",
         "-movflags", "+faststart",
         "-metadata", f"title={title}",
         out])
    print(f"OK  {out}  ({dur:.1f}s, {os.path.getsize(out) / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
