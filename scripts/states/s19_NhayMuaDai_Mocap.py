# -*- coding: utf-8 -*-
"""STATE 19: vũ đạo dài, retarget từ mocap.

Bản ghi gốc 4.751 frame (158 giây). Không cắt bằng cách dò từng độ dài như các
clip ngắn — với bản ghi dài thì chỗ bắt đầu mới là thứ quyết định. Xem
retarget.find_dance_loop: tự tương quan để tìm chu kỳ thật của điệu nhảy rồi
mới chọn chỗ bắt đầu khép nhất.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import retarget

CLIP = '19_NhayMuaDai_Mocap'
bake = retarget.mocap_state(CLIP, 'dataset-1_dance-long_normal_001.bvh',
                            offset=200, loop_lo=40, loop_hi=200,
                            dance=True, blend=6)
