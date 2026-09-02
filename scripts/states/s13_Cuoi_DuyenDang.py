# -*- coding: utf-8 -*-
"""STATE 13: 13_Cuoi_DuyenDang (60 frames - Cute Idol Radiant Smile & Giggle 😄)"""
import bpy
import math
import mathutils

from rig import apply_pointing_hair_drape, create_quaternion

CLIP = '13_Cuoi_DuyenDang'


def bake(char_arm, pb):
    print(">>> 13. Baking 13_Cuoi_DuyenDang (Idol Radiant Smile & Giggle) with Soft Silky Hair...")
    act_smile = bpy.data.actions.new(name="13_Cuoi_DuyenDang")
    char_arm.animation_data.action = act_smile

    for frame in range(1, 61):
        bpy.context.scene.frame_set(frame)
        t = (frame / 60.0) * math.pi * 2.0
        sway = math.sin(t) * 0.015
        # Laughing shoulder/chest giggle bounce (rhythm 4x)
        giggle = math.sin(t * 4.0) * 0.012
        breath = math.sin(t * 2) * 0.020
        
        # Stance: Sweet idol stance, slight head tilt
        if pb.get('J_Bip_C_Hips'):
            pb['J_Bip_C_Hips'].location = (0.01, 0.0, -0.010 + giggle * 0.3)
            pb['J_Bip_C_Hips'].keyframe_insert(data_path="location", frame=frame)
            pb['J_Bip_C_Hips'].rotation_quaternion = create_quaternion((0.02, 0.02, sway * 0.5))
            pb['J_Bip_C_Hips'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        if pb.get('J_Bip_L_UpperLeg'):
            pb['J_Bip_L_UpperLeg'].rotation_quaternion = create_quaternion((-0.06, 0.02, -0.04))
            pb['J_Bip_L_UpperLeg'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_L_LowerLeg'):
            pb['J_Bip_L_LowerLeg'].rotation_quaternion = create_quaternion((0.10, 0, 0))
            pb['J_Bip_L_LowerLeg'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        if pb.get('J_Bip_R_UpperLeg'):
            pb['J_Bip_R_UpperLeg'].rotation_quaternion = create_quaternion((-0.04, 0.0, 0.04))
            pb['J_Bip_R_UpperLeg'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_R_LowerLeg'):
            pb['J_Bip_R_LowerLeg'].rotation_quaternion = create_quaternion((0.06, 0, 0))
            pb['J_Bip_R_LowerLeg'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        # Spine and chest chuckling / giggling with joy
        if pb.get('J_Bip_C_Spine'):
            pb['J_Bip_C_Spine'].rotation_quaternion = create_quaternion((0.03 + giggle + breath * 0.4, 0.01, 0.01))
            pb['J_Bip_C_Spine'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_C_UpperChest'):
            pb['J_Bip_C_UpperChest'].rotation_quaternion = create_quaternion((0.05 + giggle * 1.5 + breath * 0.7, 0.01, 0.01))
            pb['J_Bip_C_UpperChest'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        # Head tilted in a cute laughing angle
        if pb.get('J_Bip_C_Neck'):
            pb['J_Bip_C_Neck'].rotation_quaternion = create_quaternion((0.01, 0.02, 0.0))
            pb['J_Bip_C_Neck'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_C_Head'):
            pb['J_Bip_C_Head'].rotation_quaternion = create_quaternion((-0.03 + giggle * 0.5, 0.05 + sway, 0.08))
            pb['J_Bip_C_Head'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        # Right Hand: Raised near mouth/cheek covering giggles in charming anime idol way
        if pb.get('J_Bip_R_UpperArm'):
            pb['J_Bip_R_UpperArm'].rotation_quaternion = create_quaternion((-0.78, 0.25, 0.38))
            pb['J_Bip_R_UpperArm'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_R_LowerArm'):
            pb['J_Bip_R_LowerArm'].rotation_quaternion = create_quaternion((0.0, 0.0, 1.45))
            pb['J_Bip_R_LowerArm'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_R_Hand'):
            pb['J_Bip_R_Hand'].rotation_quaternion = create_quaternion((0.20, 0.10, -0.30))
            pb['J_Bip_R_Hand'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        for f in ['Index', 'Middle', 'Ring', 'Little']:
            for seg in [1, 2, 3]:
                f_bone = f'J_Bip_R_{f}{seg}'
                if pb.get(f_bone):
                    pb[f_bone].rotation_quaternion = create_quaternion((-0.04 * seg, 0.0, 0.08 * seg))
                    pb[f_bone].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_R_Thumb1'):
            pb['J_Bip_R_Thumb1'].rotation_quaternion = create_quaternion((0.20, 0.10, 0.15))
            pb['J_Bip_R_Thumb1'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        # Left Hand: Lightly resting near skirt/hip with cute curl
        if pb.get('J_Bip_L_UpperArm'):
            pb['J_Bip_L_UpperArm'].rotation_quaternion = create_quaternion((0.15, -0.22, -0.75))
            pb['J_Bip_L_UpperArm'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_L_LowerArm'):
            pb['J_Bip_L_LowerArm'].rotation_quaternion = create_quaternion((0.0, 0.0, -0.65))
            pb['J_Bip_L_LowerArm'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_L_Hand'):
            pb['J_Bip_L_Hand'].rotation_quaternion = create_quaternion((0.0, -0.15, 0.0))
            pb['J_Bip_L_Hand'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        for f in ['Index', 'Middle', 'Ring', 'Little']:
            for seg in [1, 2, 3]:
                f_bone = f'J_Bip_L_{f}{seg}'
                if pb.get(f_bone):
                    pb[f_bone].rotation_quaternion = create_quaternion((0.0, 0.0, -0.45))
                    pb[f_bone].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        apply_pointing_hair_drape(pb, frame, t, sway_amp=0.018, bounce_amp=0.022)
    return act_smile
