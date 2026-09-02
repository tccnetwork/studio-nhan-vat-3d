# -*- coding: utf-8 -*-
"""STATE 17: vũ đạo, retarget từ mocap.

Bản ghi gốc dài 1901 frame (63 giây). Chỉ lấy một đoạn khép kín ở giữa —
bake toàn bộ vừa mất nửa tiếng vừa cho ra một clip không lặp được.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import retarget

CLIP = '17_NhayMua_Mocap'
bake = retarget.mocap_state(CLIP, 'dataset-1_dance-short_normal_001.bvh',
                            offset=300, loop_lo=40, loop_hi=160, blend=8)
