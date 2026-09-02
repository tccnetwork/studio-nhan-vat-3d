# -*- coding: utf-8 -*-
"""STATE 15: 15_BuocDi_Mocap — bước đi retarget từ mocap thật.

Khác với 04 và 05 vốn là keyframe quaternion viết tay bằng hàm sin, trạng thái
này lấy chuyển động từ mocap/dataset-1_walk_happy_001.bvh. Xem scripts/retarget.py
để biết vì sao phải bám hướng khớp-tới-khớp thay vì chép góc quay cục bộ.
"""
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import retarget

CLIP = '15_BuocDi_Mocap'
BVH = 'dataset-1_walk_happy_001.bvh'


def bake(char_arm, pb):
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    path = os.path.join(root, 'mocap', BVH)
    bvh_arm, first, last = retarget.load_bvh(path)
    try:
        span = retarget.find_loop_length(bvh_arm, first, lo=16, hi=min(90, last - first - 1))
        act = retarget.retarget(char_arm, bvh_arm, CLIP,
                                frames=(first, first + span - 1),
                                in_place=True, ground=True)
    finally:
        retarget.discard_bvh(bvh_arm)
        # Xoá object BVH làm mất active object; các bước sau của quy trình dựng
        # gọi bpy.ops.object.mode_set nên cần có active object hợp lệ.
        bpy.context.view_layer.objects.active = char_arm
    return act
