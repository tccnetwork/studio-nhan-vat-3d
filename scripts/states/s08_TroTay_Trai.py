# -*- coding: utf-8 -*-
"""STATE 8: 08_TroTay_Trai (60 frames - Symmetrical Mirror of 06_TroTay_PhiaTruoc)"""
import bpy
import math
import mathutils

from rig import apply_left_pointing_hair_drape, create_quaternion

CLIP = '08_TroTay_Trai'


def bake(char_arm, pb):
    print(">>> 8. Baking 08_TroTay_Trai (Symmetrical Left Pointing) with Perfect Fist & Soft Silky Hair...")
    act_point_left = bpy.data.actions.new(name="08_TroTay_Trai")
    char_arm.animation_data.action = act_point_left

    for frame in range(1, 61):
        bpy.context.scene.frame_set(frame)
        t = (frame / 60.0) * math.pi * 2.0
        sway = -math.sin(t) * 0.015
        breath = math.sin(t * 2) * 0.025
        
        # Stance: Dynamic confident idol pose (mirrored)
        if pb.get('J_Bip_C_Hips'):
            pb['J_Bip_C_Hips'].location = (-0.025 + sway * 0.4, 0, -0.015)
            pb['J_Bip_C_Hips'].keyframe_insert(data_path="location", frame=frame)
            pb['J_Bip_C_Hips'].rotation_quaternion = create_quaternion((0.02, -0.05 + sway, 0.05))
            pb['J_Bip_C_Hips'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        # Legs (mirrored)
        if pb.get('J_Bip_R_UpperLeg'):
            pb['J_Bip_R_UpperLeg'].rotation_quaternion = create_quaternion((-0.12, -0.04, 0.06))
            pb['J_Bip_R_UpperLeg'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_R_LowerLeg'):
            pb['J_Bip_R_LowerLeg'].rotation_quaternion = create_quaternion((0.20, 0, 0))
            pb['J_Bip_R_LowerLeg'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        if pb.get('J_Bip_L_UpperLeg'):
            pb['J_Bip_L_UpperLeg'].rotation_quaternion = create_quaternion((-0.02, 0, -0.06))
            pb['J_Bip_L_UpperLeg'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_L_LowerLeg'):
            pb['J_Bip_L_LowerLeg'].rotation_quaternion = create_quaternion((0.05, 0, 0))
            pb['J_Bip_L_LowerLeg'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        # Torso & Spine (mirrored)
        if pb.get('J_Bip_C_Spine'):
            pb['J_Bip_C_Spine'].rotation_quaternion = create_quaternion((0.03 + breath * 0.3, 0.04, -0.02))
            pb['J_Bip_C_Spine'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_C_UpperChest'):
            pb['J_Bip_C_UpperChest'].rotation_quaternion = create_quaternion((0.04 + breath * 0.6, 0.06, -0.02))
            pb['J_Bip_C_UpperChest'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        # Head & Neck (mirrored)
        if pb.get('J_Bip_C_Neck'):
            pb['J_Bip_C_Neck'].rotation_quaternion = create_quaternion((0.01, -0.04 + sway, 0.02))
            pb['J_Bip_C_Neck'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_C_Head'):
            pb['J_Bip_C_Head'].rotation_quaternion = create_quaternion((-0.02, -0.08 + sway, -0.04))
            pb['J_Bip_C_Head'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        # LEFT ARM: POINTING FORWARD DIRECTLY AT AUDIENCE
        point_swing = math.sin(t) * 0.02
        if pb.get('J_Bip_L_UpperArm'):
            pb['J_Bip_L_UpperArm'].rotation_quaternion = create_quaternion((-1.32 + point_swing, -0.18, -0.35))
            pb['J_Bip_L_UpperArm'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_L_LowerArm'):
            pb['J_Bip_L_LowerArm'].rotation_quaternion = create_quaternion((0.0, 0.0, -0.15))
            pb['J_Bip_L_LowerArm'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_L_Hand'):
            pb['J_Bip_L_Hand'].rotation_quaternion = create_quaternion((0.10, 0.0, 0.0))
            pb['J_Bip_L_Hand'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        # LEFT FINGERS:
        # 1. Index Finger: STRAIGHT, POINTING FORWARD
        for seg in [1, 2, 3]:
            if pb.get(f'J_Bip_L_Index{seg}'):
                pb[f'J_Bip_L_Index{seg}'].rotation_quaternion = create_quaternion((0.0, 0.0, 0.0))
                pb[f'J_Bip_L_Index{seg}'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        # 2. Middle, Ring, Little Fingers: CURLED TIGHTLY INWARD INTO PALM (-Z)
        for f in ['Middle', 'Ring', 'Little']:
            for seg in [1, 2, 3]:
                curl_angle = -1.45 if seg < 3 else -1.30
                if pb.get(f'J_Bip_L_{f}{seg}'):
                    pb[f'J_Bip_L_{f}{seg}'].rotation_quaternion = create_quaternion((0.0, 0.0, curl_angle))
                    pb[f'J_Bip_L_{f}{seg}'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        # 3. Thumb: CLENCHED & WRAPPED TIGHTLY OVER THE FIST
        if pb.get('J_Bip_L_Thumb1'):
            pb['J_Bip_L_Thumb1'].rotation_quaternion = create_quaternion((0.70, -0.25, -0.85))
            pb['J_Bip_L_Thumb1'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_L_Thumb2'):
            pb['J_Bip_L_Thumb2'].rotation_quaternion = create_quaternion((0.0, 0.0, -1.20))
            pb['J_Bip_L_Thumb2'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_L_Thumb3'):
            pb['J_Bip_L_Thumb3'].rotation_quaternion = create_quaternion((0.0, 0.0, -1.10))
            pb['J_Bip_L_Thumb3'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        # RIGHT ARM & HAND: Gracefully resting on waist
        if pb.get('J_Bip_R_UpperArm'):
            pb['J_Bip_R_UpperArm'].rotation_quaternion = create_quaternion((0.15, 0.30, 0.85))
            pb['J_Bip_R_UpperArm'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_R_LowerArm'):
            pb['J_Bip_R_LowerArm'].rotation_quaternion = create_quaternion((0.0, 0.0, 0.75))
            pb['J_Bip_R_LowerArm'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_R_Hand'):
            pb['J_Bip_R_Hand'].rotation_quaternion = create_quaternion((0.0, 0.20, 0.0))
            pb['J_Bip_R_Hand'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        for f in ['Middle', 'Ring', 'Little', 'Index']:
            for seg in [1, 2, 3]:
                if pb.get(f'J_Bip_R_{f}{seg}'):
                    pb[f'J_Bip_R_{f}{seg}'].rotation_quaternion = create_quaternion((0.0, 0.0, 0.55))
                    pb[f'J_Bip_R_{f}{seg}'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        for seg in [1, 2, 3]:
            if pb.get(f'J_Bip_R_Thumb{seg}'):
                pb[f'J_Bip_R_Thumb{seg}'].rotation_quaternion = create_quaternion((0.0, 0.0, 0.45))
                pb[f'J_Bip_R_Thumb{seg}'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        apply_left_pointing_hair_drape(pb, frame, t, sway_amp=0.018, bounce_amp=0.022)
    return act_point_left
