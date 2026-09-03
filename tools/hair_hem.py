# -*- coding: utf-8 -*-
"""Đo độ răng cưa của đường cắt tóc.

    /Applications/Blender.app/Contents/MacOS/Blender --background \
        --factory-startup --python tools/hair_hem.py

Chia vành tóc thành các ô theo góc quanh đầu, lấy cao độ thấp nhất trong mỗi ô,
rồi đo chênh lệch giữa các ô kề nhau. Đường cắt gọn thì chênh lệch nhỏ; đường
cắt lởm chởm thì lớn. Đây là cách nói bằng số cho cái mà mắt gọi là "răng cưa".

Kiểu tóc dài gốc của VRoid dùng làm mốc: nó đẹp, nên con số của nó là mức mà ba
kiểu cắt tự động nên hướng tới.
"""
import math
import os
import sys

import bpy

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
import hairstyles

BINS = 48
AXIS_Y = 0.015


def hem_profile(obj, bins=BINS):
    """Cao độ thấp nhất theo từng ô góc. Ô rỗng trả về None."""
    low = [None] * bins
    for v in obj.data.vertices:
        ang = math.atan2(v.co.y - AXIS_Y, v.co.x)
        i = int((ang + math.pi) / (2 * math.pi) * bins) % bins
        if low[i] is None or v.co.z < low[i]:
            low[i] = v.co.z
    return low


def raggedness(low):
    """Chênh lệch trung bình và lớn nhất giữa hai ô kề nhau, tính bằng cm."""
    vals = [(i, z) for i, z in enumerate(low) if z is not None]
    if len(vals) < 4:
        return 0.0, 0.0
    diffs = []
    for k in range(len(vals)):
        _, a = vals[k]
        _, b = vals[(k + 1) % len(vals)]
        diffs.append(abs(a - b) * 100.0)
    return sum(diffs) / len(diffs), max(diffs)


if __name__ == '__main__':
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(
        filepath=os.path.join(ROOT, 'source', 'female_singer_anime_idol_base.glb'))
    arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
    hairstyles.build_hairstyles(arm)

    print('\n>>> ĐỘ RĂNG CƯA CỦA ĐƯỜNG CẮT (cm, càng nhỏ càng gọn)')
    print('>>>   %-22s %9s %9s %8s %9s'
          % ('kiểu tóc', 'răng cưa', 'lớn nhất', 'độ dài', 'tỉ lệ'))
    order = ['Hair', 'Hair_WavyCurled', 'Hair_MediumShoulder', 'Hair_ShortBob']
    for name in order:
        obj = bpy.data.objects.get(name)
        if not obj:
            continue
        low = hem_profile(obj)
        avg, mx = raggedness(low)
        zs = [z for z in low if z is not None]
        span = (max(zs) - min(zs)) * 100.0
        label = name + (' (gốc)' if name == 'Hair' else '')
        print('>>>   %-22s %9.2f %9.2f %8.1f %8.1f%%'
              % (label, avg, mx, span, avg / span * 100 if span else 0))
