# -*- coding: utf-8 -*-
"""STATE 16: vẫy tay chào, retarget từ mocap."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import retarget

CLIP = '16_VayTay_Mocap'
bake = retarget.mocap_state(CLIP, 'dataset-1_byebye_happy_001.bvh',
                            offset=40, loop_lo=24, loop_hi=90, blend=6)
