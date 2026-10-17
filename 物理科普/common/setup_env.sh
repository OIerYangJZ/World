#!/usr/bin/env bash
# 渲染环境（Ubuntu 24.04 测试通过）
set -e
apt-get install -y libpango1.0-dev fonts-noto-cjk ffmpeg \
  texlive-latex-base texlive-latex-extra texlive-fonts-recommended texlive-science dvisvgm cm-super
python3 -m venv /opt/mvenv
/opt/mvenv/bin/pip install --upgrade pip setuptools wheel
/opt/mvenv/bin/pip install manim==0.22.0 scipy
