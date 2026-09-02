# -*- coding: utf-8 -*-
"""STATE 14: 14_CuiChao_KetThuc (60 frames - Stage Bow / Concert Thank You 🙇‍♀️)"""
import bpy
import math
import mathutils

from rig import apply_bow_hair_drape, create_quaternion

CLIP = '14_CuiChao_KetThuc'


def bake(char_arm, pb):
    print(">>> 14. Baking 14_CuiChao_KetThuc (Concert Stage Bow) with Soft Silky Hair...")
    act_bow = bpy.data.actions.new(name="14_CuiChao_KetThuc")
    char_arm.animation_data.action = act_bow

    for frame in range(1, 61):
        bpy.context.scene.frame_set(frame)
        
        # Smooth bow curve across 60 frames:
        # Frame 1-18: Bow smoothly down
        # Frame 19-42: Hold polite respectful bow with gentle breathing
        # Frame 43-60: Smoothly return upright
        if frame <= 18:
            bow_factor = (1.0 - math.cos((frame / 18.0) * math.pi)) * 0.5
        elif frame <= 42:
            bow_hold_t = ((frame - 18) / 24.0) * math.pi * 2.0
            bow_factor = 1.0 + math.sin(bow_hold_t) * 0.02
        else:
            bow_factor = (1.0 + math.cos(((frame - 42) / 18.0) * math.pi)) * 0.5
        
        # 1. Hips & Pelvis: 100% STATIONARY PINNED (No displacement, no rotation)
        if pb.get('J_Bip_C_Hips'):
            pb['J_Bip_C_Hips'].location = (0.0, 0.0, 0.0)
            pb['J_Bip_C_Hips'].keyframe_insert(data_path="location", frame=frame)
            pb['J_Bip_C_Hips'].rotation_quaternion = create_quaternion((0.0, 0.0, 0.0))
            pb['J_Bip_C_Hips'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        # 2. Legs & Feet: 100% PINNED FIRMLY TO THE FLOOR (Attention / Neutral)
        if pb.get('J_Bip_L_UpperLeg'):
            pb['J_Bip_L_UpperLeg'].rotation_quaternion = create_quaternion((0.0, 0.0, -0.015))
            pb['J_Bip_L_UpperLeg'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_L_LowerLeg'):
            pb['J_Bip_L_LowerLeg'].rotation_quaternion = create_quaternion((0.0, 0.0, 0.0))
            pb['J_Bip_L_LowerLeg'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_L_Foot'):
            pb['J_Bip_L_Foot'].rotation_quaternion = create_quaternion((0.0, 0.0, 0.0))
            pb['J_Bip_L_Foot'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        if pb.get('J_Bip_R_UpperLeg'):
            pb['J_Bip_R_UpperLeg'].rotation_quaternion = create_quaternion((0.0, 0.0, 0.015))
            pb['J_Bip_R_UpperLeg'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_R_LowerLeg'):
            pb['J_Bip_R_LowerLeg'].rotation_quaternion = create_quaternion((0.0, 0.0, 0.0))
            pb['J_Bip_R_LowerLeg'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_R_Foot'):
            pb['J_Bip_R_Foot'].rotation_quaternion = create_quaternion((0.0, 0.0, 0.0))
            pb['J_Bip_R_Foot'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        # 3. Upper body: Gentle, polite forward bend (Spine + Chest + Head ~ 25 degrees total)
        if pb.get('J_Bip_C_Spine'):
            pb['J_Bip_C_Spine'].rotation_quaternion = create_quaternion((0.26 * bow_factor, 0.0, 0.0))
            pb['J_Bip_C_Spine'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_C_Chest'):
            pb['J_Bip_C_Chest'].rotation_quaternion = create_quaternion((0.08 * bow_factor, 0.0, 0.0))
            pb['J_Bip_C_Chest'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_C_UpperChest'):
            pb['J_Bip_C_UpperChest'].rotation_quaternion = create_quaternion((0.10 * bow_factor, 0.0, 0.0))
            pb['J_Bip_C_UpperChest'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        if pb.get('J_Bip_C_Neck'):
            pb['J_Bip_C_Neck'].rotation_quaternion = create_quaternion((0.06 * bow_factor, 0.0, 0.0))
            pb['J_Bip_C_Neck'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_C_Head'):
            pb['J_Bip_C_Head'].rotation_quaternion = create_quaternion((0.08 * bow_factor, 0.0, 0.0))
            pb['J_Bip_C_Head'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        # 4. Arms & Hands: Neatly brought together in front of upper thighs (Polite idol bow)
        if pb.get('J_Bip_R_UpperArm'):
            pb['J_Bip_R_UpperArm'].rotation_quaternion = create_quaternion((0.18 * bow_factor, 0.0, 1.25 - 0.15 * bow_factor))
            pb['J_Bip_R_UpperArm'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_R_LowerArm'):
            pb['J_Bip_R_LowerArm'].rotation_quaternion = create_quaternion((0.0, 0.0, 0.22 * bow_factor))
            pb['J_Bip_R_LowerArm'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_R_Hand'):
            pb['J_Bip_R_Hand'].rotation_quaternion = create_quaternion((0.05 * bow_factor, 0.0, -0.05 * bow_factor))
            pb['J_Bip_R_Hand'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        if pb.get('J_Bip_L_UpperArm'):
            pb['J_Bip_L_UpperArm'].rotation_quaternion = create_quaternion((0.18 * bow_factor, 0.0, -1.25 + 0.15 * bow_factor))
            pb['J_Bip_L_UpperArm'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_L_LowerArm'):
            pb['J_Bip_L_LowerArm'].rotation_quaternion = create_quaternion((0.0, 0.0, -0.22 * bow_factor))
            pb['J_Bip_L_LowerArm'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_L_Hand'):
            pb['J_Bip_L_Hand'].rotation_quaternion = create_quaternion((0.05 * bow_factor, 0.0, 0.05 * bow_factor))
            pb['J_Bip_L_Hand'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        # 5. Fingers: Gently and naturally closed
        for side in ['L', 'R']:
            sign = -1.0 if side == 'L' else 1.0
            for f in ['Index', 'Middle', 'Ring', 'Little']:
                for seg in [1, 2, 3]:
                    f_bone = f'J_Bip_{side}_{f}{seg}'
                    if pb.get(f_bone):
                        pb[f_bone].rotation_quaternion = create_quaternion((0.0, 0.0, -0.03 * seg * sign * bow_factor))
                        pb[f_bone].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        # 6. Hair forward physics drape
        apply_bow_hair_drape(pb, frame, bow_factor)

    return act_bow
