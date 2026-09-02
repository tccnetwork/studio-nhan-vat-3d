# -*- coding: utf-8 -*-
"""STATE 9: 09_HaiTay_SongSong (60 frames - Dual Arms Parallel Forward)"""
import bpy
import math
import mathutils

from rig import apply_dual_arm_hair_drape, create_quaternion

CLIP = '09_HaiTay_SongSong'


def bake(char_arm, pb):
    print(">>> 9. Baking 09_HaiTay_SongSong (Dual Arms Parallel Forward) with Soft Silky Hair...")
    act_dual_arms = bpy.data.actions.new(name="09_HaiTay_SongSong")
    char_arm.animation_data.action = act_dual_arms

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

        # DUAL ARMS: EXTENDED PARALLEL FORWARD (Horizontal to audience)
        point_swing = math.sin(t) * 0.015
        
        # Right Arm
        if pb.get('J_Bip_R_UpperArm'):
            pb['J_Bip_R_UpperArm'].rotation_quaternion = create_quaternion((-1.30 + point_swing, 0.06, 0.12))
            pb['J_Bip_R_UpperArm'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_R_LowerArm'):
            pb['J_Bip_R_LowerArm'].rotation_quaternion = create_quaternion((0.0, 0.0, 0.04))
            pb['J_Bip_R_LowerArm'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_R_Hand'):
            pb['J_Bip_R_Hand'].rotation_quaternion = create_quaternion((0.06, 0.0, -0.04))
            pb['J_Bip_R_Hand'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        # Left Arm
        if pb.get('J_Bip_L_UpperArm'):
            pb['J_Bip_L_UpperArm'].rotation_quaternion = create_quaternion((-1.30 + point_swing, -0.06, -0.12))
            pb['J_Bip_L_UpperArm'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_L_LowerArm'):
            pb['J_Bip_L_LowerArm'].rotation_quaternion = create_quaternion((0.0, 0.0, -0.04))
            pb['J_Bip_L_LowerArm'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_L_Hand'):
            pb['J_Bip_L_Hand'].rotation_quaternion = create_quaternion((0.06, 0.0, 0.04))
            pb['J_Bip_L_Hand'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        # FINGERS: Graceful open hands pointing parallel forward
        for side in ['L', 'R']:
            sign = -1.0 if side == 'L' else 1.0
            for f in ['Index', 'Middle', 'Ring', 'Little']:
                for seg in [1, 2, 3]:
                    f_bone = f'J_Bip_{side}_{f}{seg}'
                    if pb.get(f_bone):
                        curl = 0.06 * seg * sign
                        pitch_f = -0.04 * seg
                        pb[f_bone].rotation_quaternion = create_quaternion((pitch_f, 0.0, curl))
                        pb[f_bone].keyframe_insert(data_path="rotation_quaternion", frame=frame)
            
            for seg in [1, 2, 3]:
                t_bone = f'J_Bip_{side}_Thumb{seg}'
                if pb.get(t_bone):
                    pb[t_bone].rotation_quaternion = create_quaternion((0.10, -0.08 * sign, -0.10 * sign))
                    pb[t_bone].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        apply_dual_arm_hair_drape(pb, frame, t, sway_amp=0.018, bounce_amp=0.022)
    return act_dual_arms
