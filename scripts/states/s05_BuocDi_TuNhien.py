# -*- coding: utf-8 -*-
"""STATE 5: 05_BuocDi_TuNhien (60 frames BIOMECHANICAL NATURAL STANCE WALK)"""
import bpy
import math
import mathutils

from rig import apply_soft_hair_drape, create_quaternion, get_biomechanical_gait_frame

CLIP = '05_BuocDi_TuNhien'


def bake(char_arm, pb):
    print(">>> 5. Baking Biomechanical Natural Walk with Full Stance Weight Shift & Soft Hair...")
    act_walk_mocap = bpy.data.actions.new(name="05_BuocDi_TuNhien")
    char_arm.animation_data.action = act_walk_mocap

    for frame in range(1, 61):
        bpy.context.scene.frame_set(frame)
        phi = (frame / 60.0) * math.pi * 2.0
        g = get_biomechanical_gait_frame(phi, is_energetic=False)
        
        # 1. Hips Translation & Weight Shift onto Stance Leg
        if pb.get('J_Bip_C_Hips'):
            pb['J_Bip_C_Hips'].location = g['hip_loc']
            pb['J_Bip_C_Hips'].keyframe_insert(data_path="location", frame=frame)
            pb['J_Bip_C_Hips'].rotation_quaternion = create_quaternion(g['hip_rot'])
            pb['J_Bip_C_Hips'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        # 2. Torso Posture: Straight back & proud lifted chest (Image 1 reference)
        if pb.get('J_Bip_C_Spine'):
            pb['J_Bip_C_Spine'].rotation_quaternion = create_quaternion(g['spine_rot'])
            pb['J_Bip_C_Spine'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_C_UpperChest'):
            pb['J_Bip_C_UpperChest'].rotation_quaternion = create_quaternion(g['chest_rot'])
            pb['J_Bip_C_UpperChest'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_C_Neck'):
            pb['J_Bip_C_Neck'].rotation_quaternion = create_quaternion(g['neck_rot'])
            pb['J_Bip_C_Neck'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_C_Head'):
            pb['J_Bip_C_Head'].rotation_quaternion = create_quaternion(g['head_rot'])
            pb['J_Bip_C_Head'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        # 3. Grounded Legs & Feet with Heel Strike and Toe Push-Off
        if pb.get('J_Bip_L_UpperLeg'):
            pb['J_Bip_L_UpperLeg'].rotation_quaternion = create_quaternion((g['l_thigh'], -g['hip_rot'][1] * 0.3, -0.025))
            pb['J_Bip_L_UpperLeg'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_L_LowerLeg'):
            pb['J_Bip_L_LowerLeg'].rotation_quaternion = create_quaternion((g['l_knee'], 0.0, 0.0))
            pb['J_Bip_L_LowerLeg'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_L_Foot'):
            pb['J_Bip_L_Foot'].rotation_quaternion = create_quaternion((g['l_foot'], 0.0, 0.0))
            pb['J_Bip_L_Foot'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_L_ToeBase'):
            pb['J_Bip_L_ToeBase'].rotation_quaternion = create_quaternion((g['l_toe'], 0.0, 0.0))
            pb['J_Bip_L_ToeBase'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        if pb.get('J_Bip_R_UpperLeg'):
            pb['J_Bip_R_UpperLeg'].rotation_quaternion = create_quaternion((g['r_thigh'], -g['hip_rot'][1] * 0.3, 0.025))
            pb['J_Bip_R_UpperLeg'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_R_LowerLeg'):
            pb['J_Bip_R_LowerLeg'].rotation_quaternion = create_quaternion((g['r_knee'], 0.0, 0.0))
            pb['J_Bip_R_LowerLeg'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_R_Foot'):
            pb['J_Bip_R_Foot'].rotation_quaternion = create_quaternion((g['r_foot'], 0.0, 0.0))
            pb['J_Bip_R_Foot'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_R_ToeBase'):
            pb['J_Bip_R_ToeBase'].rotation_quaternion = create_quaternion((g['r_toe'], 0.0, 0.0))
            pb['J_Bip_R_ToeBase'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        # 4. Natural Counter-Balancing Arm Swings
        if pb.get('J_Bip_L_UpperArm'):
            pb['J_Bip_L_UpperArm'].rotation_quaternion = create_quaternion((g['l_arm'], 0.04, -1.26 + 0.05 * math.cos(phi)))
            pb['J_Bip_L_UpperArm'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_L_LowerArm'):
            pb['J_Bip_L_LowerArm'].rotation_quaternion = create_quaternion((0.15 + 0.12 * max(0.0, g['l_arm']), 0.0, -0.18))
            pb['J_Bip_L_LowerArm'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_L_Hand'):
            pb['J_Bip_L_Hand'].rotation_quaternion = create_quaternion((0.0, -0.10, 0.0))
            pb['J_Bip_L_Hand'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        if pb.get('J_Bip_R_UpperArm'):
            pb['J_Bip_R_UpperArm'].rotation_quaternion = create_quaternion((g['r_arm'], -0.04, 1.26 - 0.05 * math.cos(phi)))
            pb['J_Bip_R_UpperArm'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_R_LowerArm'):
            pb['J_Bip_R_LowerArm'].rotation_quaternion = create_quaternion((0.15 + 0.12 * max(0.0, g['r_arm']), 0.0, 0.18))
            pb['J_Bip_R_LowerArm'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_R_Hand'):
            pb['J_Bip_R_Hand'].rotation_quaternion = create_quaternion((0.0, 0.10, 0.0))
            pb['J_Bip_R_Hand'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        # Fingers: relaxed feminine curve
        for side in ['L', 'R']:
            for f_name in ['Thumb', 'Index', 'Middle', 'Ring', 'Little']:
                for seg in range(1, 4):
                    b_name = f'J_Bip_{side}_{f_name}{seg}'
                    if pb.get(b_name):
                        pb[b_name].rotation_quaternion = create_quaternion((0.0, -0.18, -0.10 if side=='L' else 0.10))
                        pb[b_name].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        apply_soft_hair_drape(pb, frame, phi * 2.0, sway_amp=0.028, bounce_amp=0.032)
    return act_walk_mocap
