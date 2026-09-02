# -*- coding: utf-8 -*-
"""STATE 11: 11_TraiTim_YeuThuong (60 frames - Idol Heart Hands Gesture 💖)"""
import bpy
import math
import mathutils

from rig import create_quaternion

CLIP = '11_TraiTim_YeuThuong'


def bake(char_arm, pb):
    print(">>> 11. Baking 11_TraiTim_YeuThuong (Idol Heart Hands) with Soft Silky Hair...")
    act_heart = bpy.data.actions.new(name="11_TraiTim_YeuThuong")
    char_arm.animation_data.action = act_heart

    for frame in range(1, 61):
        bpy.context.scene.frame_set(frame)
        t = (frame / 60.0) * math.pi * 2.0
        sway = math.sin(t) * 0.015
        breath = math.sin(t * 2) * 0.025
        
        # Stance: Cute anime idol pose (Right foot slightly out, left knee bent inward)
        if pb.get('J_Bip_C_Hips'):
            pb['J_Bip_C_Hips'].location = (0.02, 0.0, -0.015)
            pb['J_Bip_C_Hips'].keyframe_insert(data_path="location", frame=frame)
            pb['J_Bip_C_Hips'].rotation_quaternion = create_quaternion((0.02, 0.04, -0.04 + sway))
            pb['J_Bip_C_Hips'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        if pb.get('J_Bip_L_UpperLeg'):
            pb['J_Bip_L_UpperLeg'].rotation_quaternion = create_quaternion((-0.14, 0.06, -0.08))
            pb['J_Bip_L_UpperLeg'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_L_LowerLeg'):
            pb['J_Bip_L_LowerLeg'].rotation_quaternion = create_quaternion((0.25, 0, 0))
            pb['J_Bip_L_LowerLeg'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        if pb.get('J_Bip_R_UpperLeg'):
            pb['J_Bip_R_UpperLeg'].rotation_quaternion = create_quaternion((-0.02, 0.0, 0.05))
            pb['J_Bip_R_UpperLeg'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_R_LowerLeg'):
            pb['J_Bip_R_LowerLeg'].rotation_quaternion = create_quaternion((0.05, 0, 0))
            pb['J_Bip_R_LowerLeg'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        if pb.get('J_Bip_C_Spine'):
            pb['J_Bip_C_Spine'].rotation_quaternion = create_quaternion((0.03 + breath * 0.4, -0.02, 0.02))
            pb['J_Bip_C_Spine'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_C_UpperChest'):
            pb['J_Bip_C_UpperChest'].rotation_quaternion = create_quaternion((0.05 + breath * 0.7, -0.02, 0.02))
            pb['J_Bip_C_UpperChest'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        if pb.get('J_Bip_C_Neck'):
            pb['J_Bip_C_Neck'].rotation_quaternion = create_quaternion((0.01, 0.02, 0.0))
            pb['J_Bip_C_Neck'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_C_Head'):
            pb['J_Bip_C_Head'].rotation_quaternion = create_quaternion((-0.02, 0.04 + sway, 0.06)) # cute head tilt
            pb['J_Bip_C_Head'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        # Arms: Brought together in front of chest to form heart
        if pb.get('J_Bip_R_UpperArm'):
            pb['J_Bip_R_UpperArm'].rotation_quaternion = create_quaternion((-0.70, 0.28, 0.42))
            pb['J_Bip_R_UpperArm'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_R_LowerArm'):
            pb['J_Bip_R_LowerArm'].rotation_quaternion = create_quaternion((0.0, 0.0, 1.40))
            pb['J_Bip_R_LowerArm'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_R_Hand'):
            pb['J_Bip_R_Hand'].rotation_quaternion = create_quaternion((0.20, 0.15, -0.35))
            pb['J_Bip_R_Hand'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        if pb.get('J_Bip_L_UpperArm'):
            pb['J_Bip_L_UpperArm'].rotation_quaternion = create_quaternion((-0.70, -0.28, -0.42))
            pb['J_Bip_L_UpperArm'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_L_LowerArm'):
            pb['J_Bip_L_LowerArm'].rotation_quaternion = create_quaternion((0.0, 0.0, -1.40))
            pb['J_Bip_L_LowerArm'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_L_Hand'):
            pb['J_Bip_L_Hand'].rotation_quaternion = create_quaternion((0.20, -0.15, 0.35))
            pb['J_Bip_L_Hand'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        # Fingers: Curved arches of the heart
        for side in ['L', 'R']:
            sign = -1.0 if side == 'L' else 1.0
            for f in ['Index', 'Middle']:
                for seg in [1, 2, 3]:
                    f_bone = f'J_Bip_{side}_{f}{seg}'
                    if pb.get(f_bone):
                        pb[f_bone].rotation_quaternion = create_quaternion((0.0, 0.0, 0.85 * sign))
                        pb[f_bone].keyframe_insert(data_path="rotation_quaternion", frame=frame)
            for f in ['Ring', 'Little']:
                for seg in [1, 2, 3]:
                    f_bone = f'J_Bip_{side}_{f}{seg}'
                    if pb.get(f_bone):
                        pb[f_bone].rotation_quaternion = create_quaternion((0.0, 0.0, 1.25 * sign))
                        pb[f_bone].keyframe_insert(data_path="rotation_quaternion", frame=frame)
            
            for seg in [1, 2, 3]:
                t_bone = f'J_Bip_{side}_Thumb{seg}'
                if pb.get(t_bone):
                    pb[t_bone].rotation_quaternion = create_quaternion((0.40, 0.20 * sign, 0.60 * sign))
                    pb[t_bone].keyframe_insert(data_path="rotation_quaternion", frame=frame)

    return act_heart
