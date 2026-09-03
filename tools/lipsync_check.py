#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Đo bộ phát hiện giọng hát trên các file âm thanh của dự án.

    afconvert -f WAVE -d LEI16@48000 -c 1 audio/vocal_song_pop.mp3 /tmp/v.wav
    python3 tools/lipsync_check.py /tmp/v.wav /tmp/beat.wav

Câu hỏi cần trả lời: nhân vật có im miệng khi chỉ có nhạc, và chỉ nhép khi có
lời hát không? Bộ đo này chạy cùng phép tính đặc trưng và cùng ngưỡng với
web/app.js, nên con số ở đây là con số của bản chạy thật.
"""
import sys
import wave

import numpy as np

FFT = 2048
HOP = 1024
F1_BAND = (250.0, 1100.0)
F2_BAND = (1100.0, 3200.0)
VOICE_BAND = (90.0, 4000.0)
PITCH_RANGE = (80.0, 500.0)


def load(path):
    w = wave.open(path)
    sr = w.getframerate()
    x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16)
    return x.astype(np.float32) / 32768.0, sr


def frames(x, n=FFT, hop=HOP):
    for i in range(0, len(x) - n, hop):
        yield x[i:i + n]


def clarity(frame):
    """Độ rõ tuần hoàn: đỉnh tự tương quan trong dải cao độ giọng người.

    Giọng hát có cấu trúc tuần hoàn rất rõ; trống và nhiễu thì không. Đây là
    dấu hiệu tách giọng khỏi nhạc cụ gõ tốt nhất trong nhóm rẻ tiền.
    """
    f = frame - frame.mean()
    if np.abs(f).max() < 1e-4:
        return 0.0, 0.0
    ac = np.correlate(f, f, mode='full')[len(f) - 1:]
    if ac[0] <= 0:
        return 0.0, 0.0
    ac /= ac[0]
    lo = int(48000 / PITCH_RANGE[1])
    hi = min(len(ac) - 1, int(48000 / PITCH_RANGE[0]))
    seg = ac[lo:hi]
    if len(seg) == 0:
        return 0.0, 0.0
    k = int(np.argmax(seg))
    return float(seg[k]), 48000.0 / (lo + k)


def spectrum_db(frame):
    win = np.hanning(len(frame))
    mag = np.abs(np.fft.rfft(frame * win))[:-1]
    return 20.0 * np.log10(np.maximum(mag, 1e-10))


def band(db, sr, lo, hi):
    bin_hz = sr / (len(db) * 2)
    return int(lo / bin_hz), min(len(db) - 1, int(hi / bin_hz))


def analyse(path, label):
    x, sr = load(path)
    lv, cl, pr = [], [], []
    for fr in frames(x):
        db = spectrum_db(fr)
        a, b = band(db, sr, *VOICE_BAND)
        lv.append(db[a:b].mean())
        c, _f0 = clarity(fr)
        cl.append(c)
        a1, b1 = band(db, sr, *F1_BAND)
        a2, b2 = band(db, sr, *F2_BAND)
        env = db[a1:b2].mean()
        pr.append(max(db[a1:b1].max() - env, db[a2:b2].max() - env))
    lv, cl, pr = np.array(lv), np.array(cl), np.array(pr)
    print(f'\n=== {label} ({len(lv)} khung, {len(x)/sr:.0f} giây) ===')
    for name, arr in (('mức dải giọng (dB)', lv),
                      ('độ rõ tuần hoàn', cl),
                      ('độ nhô formant (dB)', pr)):
        q = np.percentile(arr, [10, 50, 90])
        print(f'  {name:22s} p10={q[0]:7.2f}  trung vị={q[1]:7.2f}  p90={q[2]:7.2f}')
    return lv, cl, pr


if __name__ == '__main__':
    a = analyse(sys.argv[1], 'CÓ LỜI HÁT')
    b = analyse(sys.argv[2], 'CHỈ CÓ NHẠC')
    print('\n=== tỉ lệ khung vượt ngưỡng ===')
    print(f'{"ngưỡng độ rõ":>16s} {"có lời":>10s} {"chỉ nhạc":>10s}')
    for t in (0.30, 0.40, 0.50, 0.60, 0.70, 0.80):
        print(f'{t:>16.2f} {(a[1] > t).mean() * 100:9.1f}% {(b[1] > t).mean() * 100:9.1f}%')
