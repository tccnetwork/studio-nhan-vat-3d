# -*- coding: utf-8 -*-
"""STATE 18: cử chỉ dẫn chuyện, retarget từ mocap."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import retarget

CLIP = '18_DanChuyen_Mocap'
bake = retarget.mocap_state(CLIP, 'dataset-1_guide_happy_001.bvh',
                            offset=10, loop_lo=20, loop_hi=80, blend=6)
