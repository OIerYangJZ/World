# -*- coding: utf-8 -*-
"""
程序化生成的氛围背景音乐（无版权问题，完全由代码合成）。

  - 柔和的和弦铺底（多个略微失谐的正弦/三角波叠加 + 慢速包络）
  - 稀疏的钢琴感琶音（衰减正弦 + 泛音）
  - 低频持续音
  - 简单的多抽头延迟 + 卷积混响营造空间感

用法：python3 music.py <时长秒> <输出.wav> <风格名>
"""
import sys
import wave
import numpy as np

SR = 44100

# 每种风格：根音 MIDI、和弦进行（相对根音的半音集合）、每和弦秒数、琶音密度、亮度
STYLES = {
    "blackhole":  dict(root=45, prog=[[0, 3, 7, 10], [-4, 0, 3, 7], [-7, -3, 0, 5], [-2, 2, 5, 9]], bar=8.0, arp=0.55, bright=0.6, seed=1),
    "quantum":    dict(root=50, prog=[[0, 4, 7, 11], [-3, 0, 4, 9], [-7, -3, 0, 4], [-5, -1, 2, 7]], bar=6.0, arp=0.9, bright=0.9, seed=2),
    "em":         dict(root=48, prog=[[0, 4, 7, 14], [-3, 0, 4, 9], [5, 9, 12, 16], [-5, 2, 7, 11]], bar=6.0, arp=1.0, bright=1.0, seed=3),
    "gr":         dict(root=43, prog=[[0, 7, 10, 15], [-4, 3, 7, 12], [-2, 5, 9, 14], [-7, 0, 5, 10]], bar=8.0, arp=0.6, bright=0.7, seed=4),
    "sr":         dict(root=47, prog=[[0, 4, 7, 11], [-5, -1, 2, 7], [-3, 0, 4, 9], [-8, -1, 4, 7]], bar=6.0, arp=0.85, bright=0.9, seed=5),
}


def mtof(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def pad_voice(f, n, rng):
    t = np.arange(n) / SR
    out = np.zeros(n)
    for det in (-0.12, 0.0, 0.11):
        ff = f * 2 ** (det / 12)
        ph = rng.uniform(0, 2 * np.pi)
        out += np.sin(2 * np.pi * ff * t + ph)
        out += 0.18 * np.sin(2 * np.pi * 2 * ff * t + ph)      # 轻微泛音
    lfo = 0.75 + 0.25 * np.sin(2 * np.pi * rng.uniform(0.05, 0.15) * t + rng.uniform(0, 6))
    return out * lfo / 3


def env_adsr(n, a, r):
    e = np.ones(n)
    na, nr = int(a * SR), int(r * SR)
    na, nr = min(na, n // 2), min(nr, n // 2)
    e[:na] = np.linspace(0, 1, na) ** 1.5
    e[n - nr:] = np.linspace(1, 0, nr) ** 1.5
    return e


def pluck(f, dur, bright):
    n = int(dur * SR)
    t = np.arange(n) / SR
    y = (np.sin(2 * np.pi * f * t) + 0.35 * bright * np.sin(2 * np.pi * 2 * f * t)
         + 0.12 * bright * np.sin(2 * np.pi * 3 * f * t))
    y *= np.exp(-t * 2.2) * (1 - np.exp(-t * 300))
    return y


def reverb(x, rng, seconds=3.2, mix=0.35):
    n = int(seconds * SR)
    t = np.arange(n) / SR
    ir = rng.standard_normal(n) * np.exp(-t * 3.0 / seconds * 2.3)
    ir[:int(0.012 * SR)] = 0
    ir /= np.sqrt(np.sum(ir ** 2))
    # FFT 卷积
    L = len(x) + n
    nfft = 1 << (L - 1).bit_length()
    y = np.fft.irfft(np.fft.rfft(x, nfft) * np.fft.rfft(ir, nfft), nfft)[:len(x)]
    return (1 - mix) * x + mix * y * 0.9


def lowpass(x, cutoff):
    # 一阶低通（向量化近似：频域）
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    H = 1 / np.sqrt(1 + (f / cutoff) ** 4)
    return np.fft.irfft(X * H, len(x))


def render(duration, style):
    p = STYLES[style]
    rng = np.random.default_rng(p["seed"])
    n = int(duration * SR)
    L = np.zeros(n)
    R = np.zeros(n)
    bar = p["bar"]
    nb = int(np.ceil(duration / bar)) + 1
    # ---- 和弦铺底
    for b in range(nb):
        chord = p["prog"][b % len(p["prog"])]
        s = int(b * bar * SR)
        ln = int((bar + 3.0) * SR)
        if s >= n:
            break
        ln = min(ln, n - s)
        e = env_adsr(ln, 2.5, 3.0)
        for i, iv in enumerate(chord):
            v = pad_voice(mtof(p["root"] + 12 + iv), ln, rng) * e * 0.10
            pan = 0.5 + 0.35 * np.sin(i * 1.7 + b)
            L[s:s + ln] += v * (1 - pan)
            R[s:s + ln] += v * pan
        # 低音
        bass = pad_voice(mtof(p["root"] - 12 + chord[0]), ln, rng) * e * 0.09
        L[s:s + ln] += bass
        R[s:s + ln] += bass
    # ---- 琶音
    step = bar / 8
    k = 0
    tt = 4.0
    while tt < duration - 6:
        b = int(tt // bar)
        chord = p["prog"][b % len(p["prog"])]
        if rng.random() < p["arp"] * 0.6:
            iv = chord[rng.integers(len(chord))] + 12 * rng.integers(1, 3)
            y = pluck(mtof(p["root"] + iv), 3.0, p["bright"]) * 0.07 * rng.uniform(0.6, 1.0)
            s = int(tt * SR)
            m = min(len(y), n - s)
            pan = rng.uniform(0.2, 0.8)
            L[s:s + m] += y[:m] * (1 - pan)
            R[s:s + m] += y[:m] * pan
        tt += step
        k += 1
    L = lowpass(L, 2500 + 2500 * p["bright"])
    R = lowpass(R, 2500 + 2500 * p["bright"])
    L = reverb(L, rng)
    R = reverb(R, np.random.default_rng(p["seed"] + 100))
    # 总体包络：淡入淡出
    fade = np.ones(n)
    fi, fo = int(3 * SR), int(5 * SR)
    fade[:fi] = np.linspace(0, 1, fi)
    fade[-fo:] = np.linspace(1, 0, fo)
    L *= fade
    R *= fade
    st = np.stack([L, R], axis=1)
    st /= np.max(np.abs(st)) + 1e-9
    st *= 0.5  # 约 -6 dBFS 峰值
    return st


def write_wav(path, st):
    data = (np.clip(st, -1, 1) * 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(data.tobytes())


if __name__ == "__main__":
    dur, out, style = float(sys.argv[1]), sys.argv[2], sys.argv[3]
    write_wav(out, render(dur, style))
    print("wrote", out)
