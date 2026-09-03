#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Sinh lại build/manifest.json từ danh mục và file GLB đã xuất.

    python3 tools/write_manifest.py

Dùng khi chỉ đổi nhãn, màu, thứ tự hiển thị hay danh sách bản nhạc trong
scripts/catalog.py — những thứ không đụng tới hình học hay hoạt ảnh. Chạy lại
cả quy trình dựng chỉ để viết một file JSON là mất mười lăm phút vô ích.

Số frame đọc thẳng từ GLB nên manifest vẫn mô tả đúng file nằm cạnh nó.
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
import glb
import manifest


def frames_from_glb(gltf):
    acc = gltf['accessors']
    out = {}
    for anim in gltf.get('animations', []):
        longest = 0
        for smp in anim['samplers']:
            longest = max(longest, acc[smp['input']]['count'])
        out[anim.get('name', '?')] = longest
    return out


if __name__ == '__main__':
    build = os.path.join(ROOT, 'build')
    model = 'female_singer_anime_idol.glb'
    gltf, _ = glb.read(os.path.join(build, model))
    manifest.write_manifest(os.path.join(build, 'manifest.json'),
                            model_file=model,
                            source_file='female_singer_anime_idol_base.glb',
                            frames_by_clip=frames_from_glb(gltf))
