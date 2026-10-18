#!/usr/bin/env bash
# 渲染环境（Debian 13 / Python 3.13 测试通过）。本系列不用 LaTeX：公式全部用 Text 绘制。
set -e
sudo apt-get install -y libcairo2-dev libpango1.0-dev pkg-config python3-dev build-essential \
  fonts-noto-cjk ffmpeg
python3 -m venv ~/.venvs/manim
~/.venvs/manim/bin/pip install --upgrade pip wheel
~/.venvs/manim/bin/pip install manim==0.19.0 scipy
