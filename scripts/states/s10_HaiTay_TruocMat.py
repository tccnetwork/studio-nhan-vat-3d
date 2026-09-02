# -*- coding: utf-8 -*-
"""STATE 10: 10_HaiTay_TruocMat (60 frames - Dual Hands in Front of Face)"""
import bpy
import math
import mathutils

from rig import create_quaternion

CLIP = '10_HaiTay_TruocMat'


def bake(char_arm, pb):
    print(">>> 10. Baking 10_HaiTay_TruocMat (Dual Hands in Front of Face) with Soft Silky Hair...")
    act_hands_face = bpy.data.actions.new(name="10_HaiTay_TruocMat")
    char_arm.animation_data.action = act_hands_face

    for frame in range(1, 61):
        bpy.context.scene.frame_set(frame)
        t = (frame / 60.0) * math.pi * 2.0
        sway = math.sin(t) * 0.012
        breath = math.sin(t * 2) * 0.025
        
        # Upright balanced idol stance
        if pb.get('J_Bip_C_Hips'):
            pb['J_Bip_C_Hips'].location = (0.0, 0.0, -0.010)
            pb['J_Bip_C_Hips'].keyframe_insert(data_path="location", frame=frame)
            pb['J_Bip_C_Hips'].rotation_quaternion = create_quaternion((0.02, 0.0, sway * 0.5))
            pb['J_Bip_C_Hips'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        # Legs: Symmetric elegant stance
        if pb.get('J_Bip_L_UpperLeg'):
            pb['J_Bip_L_UpperLeg'].rotation_quaternion = create_quaternion((-0.04, 0.0, -0.04))
            pb['J_Bip_L_UpperLeg'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_L_LowerLeg'):
            pb['J_Bip_L_LowerLeg'].rotation_quaternion = create_quaternion((0.08, 0, 0))
            pb['J_Bip_L_LowerLeg'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        if pb.get('J_Bip_R_UpperLeg'):
            pb['J_Bip_R_UpperLeg'].rotation_quaternion = create_quaternion((-0.04, 0.0, 0.04))
            pb['J_Bip_R_UpperLeg'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_R_LowerLeg'):
            pb['J_Bip_R_LowerLeg'].rotation_quaternion = create_quaternion((0.08, 0, 0))
            pb['J_Bip_R_LowerLeg'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        # Torso & Spine: Graceful upright spine
        if pb.get('J_Bip_C_Spine'):
            pb['J_Bip_C_Spine'].rotation_quaternion = create_quaternion((0.03 + breath * 0.4, 0.0, 0.0))
            pb['J_Bip_C_Spine'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_C_UpperChest'):
            pb['J_Bip_C_UpperChest'].rotation_quaternion = create_quaternion((0.05 + breath * 0.7, 0.0, 0.0))
            pb['J_Bip_C_UpperChest'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        # Head & Neck
        if pb.get('J_Bip_C_Neck'):
            pb['J_Bip_C_Neck'].rotation_quaternion = create_quaternion((0.01, 0.0, 0.0))
            pb['J_Bip_C_Neck'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_C_Head'):
            pb['J_Bip_C_Head'].rotation_quaternion = create_quaternion((-0.02, 0.0, sway * 0.5))
            pb['J_Bip_C_Head'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        # DUAL ARMS RAISED IN FRONT OF FACE (Parallel, chin/mouth level)
        arm_breath = math.sin(t * 2) * 0.015
        
        # Right Arm: angled forward & upward in front of right cheek
        if pb.get('J_Bip_R_UpperArm'):
            pb['J_Bip_R_UpperArm'].rotation_quaternion = create_quaternion((-0.82 + arm_breath, 0.22, 0.35))
            pb['J_Bip_R_UpperArm'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_R_LowerArm'):
            pb['J_Bip_R_LowerArm'].rotation_quaternion = create_quaternion((0.0, 0.0, 1.25))
            pb['J_Bip_R_LowerArm'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_R_Hand'):
            pb['J_Bip_R_Hand'].rotation_quaternion = create_quaternion((0.15, 0.0, -0.20))
            pb['J_Bip_R_Hand'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        # Left Arm: angled forward & upward in front of left cheek
        if pb.get('J_Bip_L_UpperArm'):
            pb['J_Bip_L_UpperArm'].rotation_quaternion = create_quaternion((-0.82 + arm_breath, -0.22, -0.35))
            pb['J_Bip_L_UpperArm'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_L_LowerArm'):
            pb['J_Bip_L_LowerArm'].rotation_quaternion = create_quaternion((0.0, 0.0, -1.25))
            pb['J_Bip_L_LowerArm'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_L_Hand'):
            pb['J_Bip_L_Hand'].rotation_quaternion = create_quaternion((0.15, 0.0, 0.20))
            pb['J_Bip_L_Hand'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        # FINGERS: Cute graceful open fingers framing the face
        for side in ['L', 'R']:
            sign = -1.0 if side == 'L' else 1.0
            for f in ['Index', 'Middle', 'Ring', 'Little']:
                for seg in [1, 2, 3]:
                    f_bone = f'J_Bip_{side}_{f}{seg}'
                    if pb.get(f_bone):
                        curl = 0.08 * seg * sign
                        pitch_f = -0.06 * seg
                        pb[f_bone].rotation_quaternion = create_quaternion((pitch_f, 0.0, curl))
                        pb[f_bone].keyframe_insert(data_path="rotation_quaternion", frame=frame)
            
            for seg in [1, 2, 3]:
                t_bone = f'J_Bip_{side}_Thumb{seg}'
                if pb.get(t_bone):
                    pb[t_bone].rotation_quaternion = create_quaternion((0.15, -0.10 * sign, -0.15 * sign))
                    pb[t_bone].keyframe_insert(data_path="rotation_quaternion", frame=frame)

    return act_hands_face
