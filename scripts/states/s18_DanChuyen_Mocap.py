# -*- coding: utf-8 -*-
"""STATE 18: cử chỉ dẫn chuyện, retarget từ mocap."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import retarget

CLIP = '18_DanChuyen_Mocap'
bake = retarget.mocap_state(CLIP, 'dataset-1_guide_happy_001.bvh',
                            # Cử chỉ dẫn chuyện không tuần hoàn, nên điểm CẮT
                            # mới quyết định chứ không phải độ dài: quét cả hai
                            # chiều và chấm theo mối nối so với bước thường.
                            offset=10, loop_lo=30, loop_hi=110,
                            seamless=True, blend=6)
