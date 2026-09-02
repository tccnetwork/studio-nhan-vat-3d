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
bake = retarget.mocap_state(CLIP, 'dataset-1_walk_happy_001.bvh',
                            loop_lo=16, loop_hi=90)
