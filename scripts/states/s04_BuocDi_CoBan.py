# -*- coding: utf-8 -*-
"""STATE 4: 04_BuocDi_CoBan (60 frames)"""
import bpy
import math
import mathutils

from rig import create_quaternion, get_biomechanical_gait_frame

CLIP = '04_BuocDi_CoBan'


def bake(char_arm, pb):
    print(">>> 4. Creating 04_BuocDi_CoBan with Biomechanical Stance Weight Shift...")
    act_walk_basic = bpy.data.actions.new(name="04_BuocDi_CoBan")
    char_arm.animation_data.action = act_walk_basic
    for frame in range(1, 61):
        bpy.context.scene.frame_set(frame)
        phi = (frame / 60.0) * math.pi * 2.0
        g = get_biomechanical_gait_frame(phi, is_energetic=True)
        
        if pb.get('J_Bip_C_Hips'):
            pb['J_Bip_C_Hips'].location = g['hip_loc']; pb['J_Bip_C_Hips'].keyframe_insert(data_path="location", frame=frame)
            pb['J_Bip_C_Hips'].rotation_quaternion = create_quaternion(g['hip_rot']); pb['J_Bip_C_Hips'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_C_Spine'):
            pb['J_Bip_C_Spine'].rotation_quaternion = create_quaternion(g['spine_rot']); pb['J_Bip_C_Spine'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_C_UpperChest'):
            pb['J_Bip_C_UpperChest'].rotation_quaternion = create_quaternion(g['chest_rot']); pb['J_Bip_C_UpperChest'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_C_Neck'):
            pb['J_Bip_C_Neck'].rotation_quaternion = create_quaternion(g['neck_rot']); pb['J_Bip_C_Neck'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_C_Head'):
            pb['J_Bip_C_Head'].rotation_quaternion = create_quaternion(g['head_rot']); pb['J_Bip_C_Head'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        if pb.get('J_Bip_L_UpperLeg'):
            pb['J_Bip_L_UpperLeg'].rotation_quaternion = create_quaternion((g['l_thigh'], 0.0, -0.02)); pb['J_Bip_L_UpperLeg'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_L_LowerLeg'):
            pb['J_Bip_L_LowerLeg'].rotation_quaternion = create_quaternion((g['l_knee'], 0.0, 0.0)); pb['J_Bip_L_LowerLeg'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_L_Foot'):
            pb['J_Bip_L_Foot'].rotation_quaternion = create_quaternion((g['l_foot'], 0.0, 0.0)); pb['J_Bip_L_Foot'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_L_ToeBase'):
            pb['J_Bip_L_ToeBase'].rotation_quaternion = create_quaternion((g['l_toe'], 0.0, 0.0)); pb['J_Bip_L_ToeBase'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        if pb.get('J_Bip_R_UpperLeg'):
            pb['J_Bip_R_UpperLeg'].rotation_quaternion = create_quaternion((g['r_thigh'], 0.0, 0.02)); pb['J_Bip_R_UpperLeg'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_R_LowerLeg'):
            pb['J_Bip_R_LowerLeg'].rotation_quaternion = create_quaternion((g['r_knee'], 0.0, 0.0)); pb['J_Bip_R_LowerLeg'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_R_Foot'):
            pb['J_Bip_R_Foot'].rotation_quaternion = create_quaternion((g['r_foot'], 0.0, 0.0)); pb['J_Bip_R_Foot'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_R_ToeBase'):
            pb['J_Bip_R_ToeBase'].rotation_quaternion = create_quaternion((g['r_toe'], 0.0, 0.0)); pb['J_Bip_R_ToeBase'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        if pb.get('J_Bip_L_UpperArm'):
            pb['J_Bip_L_UpperArm'].rotation_quaternion = create_quaternion((g['l_arm'], 0.04, -1.26 + 0.05 * math.cos(phi))); pb['J_Bip_L_UpperArm'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_L_LowerArm'):
            pb['J_Bip_L_LowerArm'].rotation_quaternion = create_quaternion((0.15 + 0.12 * max(0.0, g['l_arm']), 0.0, -0.18)); pb['J_Bip_L_LowerArm'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_R_UpperArm'):
            pb['J_Bip_R_UpperArm'].rotation_quaternion = create_quaternion((g['r_arm'], -0.04, 1.26 - 0.05 * math.cos(phi))); pb['J_Bip_R_UpperArm'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_R_LowerArm'):
            pb['J_Bip_R_LowerArm'].rotation_quaternion = create_quaternion((0.15 + 0.12 * max(0.0, g['r_arm']), 0.0, 0.18)); pb['J_Bip_R_LowerArm'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

    return act_walk_basic
