# -*- coding: utf-8 -*-
"""STATE 15: bước đi retarget từ mocap thật.

Khác 04 và 05 vốn là keyframe quaternion viết tay bằng hàm sin. Xem
scripts/retarget.py để biết vì sao phải bám hướng khớp-tới-khớp.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import retarget

CLIP = '15_BuocDi_Mocap'
# Bàn chân của clip này phải gọn hơn hẳn các clip vũ đạo: người xem đặt nó
# cạnh 04 và 05 — hai dáng đi dựng bằng tay, có cổ chân đúng 0° và mũi chân
# 0..2° suốt chu kỳ — nên mọi chỗ vặn hay xoay đều lộ ra ngay. Thu nhỏ biên độ
# rồi mới kẹp, để giữ nguyên nhịp bước của chuyển động thật.
bake = retarget.mocap_state(CLIP, 'dataset-1_walk_happy_001.bvh',
                            loop_lo=16, loop_hi=90,
                            foot=dict(ankle_scale=0.25, max_ankle_deg=8.0,
                                      yaw_scale=0.15, max_yaw_deg=8.0))
