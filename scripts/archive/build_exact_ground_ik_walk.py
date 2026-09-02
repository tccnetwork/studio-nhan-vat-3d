import bpy
import math
import mathutils

def clean_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)

def merge_vertex_groups(mesh_obj, source_group_name, target_group_name):
    src_vg = mesh_obj.vertex_groups.get(source_group_name)
    tgt_vg = mesh_obj.vertex_groups.get(target_group_name)
    if not src_vg:
        return
    if not tgt_vg:
        tgt_vg = mesh_obj.vertex_groups.new(name=target_group_name)
    for v in mesh_obj.data.vertices:
        w_src = 0.0
        w_tgt = 0.0
        for g in v.groups:
            if g.group == src_vg.index:
                w_src = g.weight
            elif g.group == tgt_vg.index:
                w_tgt = g.weight
        if w_src > 0.0:
            new_weight = min(1.0, w_tgt + w_src)
            tgt_vg.add([v.index], new_weight, 'REPLACE')
            src_vg.remove([v.index])

def create_quaternion(euler_tuple):
    return mathutils.Euler(euler_tuple, 'XYZ').to_quaternion()

# Analytical 2-Bone Inverse Kinematics for Grounded Leg
L1 = 0.353 # Thigh
L2 = 0.415 # Shin

def solve_leg_ik(target_x, target_y):
    # target_x: forward/backward offset from hip
    # target_y: vertical offset from hip (negative value, around -0.74m)
    dx = target_x
    dy = target_y
    d = math.hypot(dx, dy)
    d = max(0.20, min(d, L1 + L2 - 0.002))
    
    # Knee flexion angle
    cos_knee = (L1*L1 + L2*L2 - d*d) / (2.0 * L1 * L2)
    cos_knee = max(-1.0, min(1.0, cos_knee))
    alpha_knee = math.acos(cos_knee)
    theta_knee = math.pi - alpha_knee # bend angle >= 0
    
    # Thigh pitch angle
    psi = math.atan2(dx, -dy)
    cos_thigh = (L1*L1 + d*d - L2*L2) / (2.0 * L1 * d)
    cos_thigh = max(-1.0, min(1.0, cos_thigh))
    beta = math.acos(cos_thigh)
    theta_thigh = psi + (beta - 0.25) # calibrated to VRM rest pose
    
    # Ankle pitch angle to keep foot flat on ground
    theta_ankle = -(theta_thigh - theta_knee * 0.85)
    return theta_thigh, theta_knee, theta_ankle

def build_ground_ik_walk():
    print(">>> 1. Loading Base Character and Purging Old Actions...")
    clean_scene()
    
    input_glb = '/Volumes/DATA/ctg_ai/3d/phuong_an_B_anime_idol_female_singer/model/female_singer_anime_idol.glb'
    out_b_dir = '/Volumes/DATA/ctg_ai/3d/phuong_an_B_anime_idol_female_singer/model'
    stage_dir = '/Volumes/DATA/ctg_ai/3d/phuong_an_nang_cao_nu_ca_si_pro_stage/model'
    
    bpy.ops.import_scene.gltf(filepath=input_glb)
    char_arm = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
    char_arm.name = 'Character_Armature'
    
    # Purge ALL old actions
    for a in list(bpy.data.actions):
        bpy.data.actions.remove(a)
    if char_arm.animation_data:
        for t in list(char_arm.animation_data.nla_tracks):
            char_arm.animation_data.nla_tracks.remove(t)

    # Merge clothing vertex weights
    body_obj = None
    for obj in bpy.data.objects:
        if obj.type == 'MESH' and 'body' in obj.name.lower():
            body_obj = obj
            break
            
    if body_obj:
        for vg_name in ['J_Aim_L_TopsUpperArm', 'J_Sec_L_TopsUpperArmInside', 'J_Sec_L_TopsUpperArmOutside', 'J_Roll_L_UpperArm']:
            merge_vertex_groups(body_obj, vg_name, 'J_Bip_L_UpperArm')
        for vg_name in ['J_Aim_R_TopsUpperArm', 'J_Sec_R_TopsUpperArmInside', 'J_Sec_R_TopsUpperArmOutside', 'J_Roll_R_UpperArm']:
            merge_vertex_groups(body_obj, vg_name, 'J_Bip_R_UpperArm')
        for vg_name in ['J_Aim_L_UpperLeg', 'J_Roll_L_UpperLeg', 'J_Sec_L_TopsUpperLegFront', 'J_Sec_L_TopsUpperLegBack', 'J_Sec_L_TopsUpperLegSide']:
            merge_vertex_groups(body_obj, vg_name, 'J_Bip_L_UpperLeg')
        for vg_name in ['J_Aim_R_UpperLeg', 'J_Roll_R_UpperLeg', 'J_Sec_R_TopsUpperLegFront', 'J_Sec_R_TopsUpperLegBack', 'J_Sec_R_TopsUpperLegSide']:
            merge_vertex_groups(body_obj, vg_name, 'J_Bip_R_UpperLeg')

    bpy.context.view_layer.objects.active = char_arm
    if not char_arm.animation_data:
        char_arm.animation_data_create()

    pb = char_arm.pose.bones
    for b in pb:
        b.rotation_mode = 'QUATERNION'

    created_actions = []

    # =========================================================================
    # STATE 1: 01_DungNghiem (60 frames)
    # =========================================================================
    print(">>> 1. Creating 01_DungNghiem...")
    act_nghiem = bpy.data.actions.new(name="01_DungNghiem")
    char_arm.animation_data.action = act_nghiem
    created_actions.append(act_nghiem)
    for frame in range(1, 61):
        bpy.context.scene.frame_set(frame)
        t = (frame / 60.0) * math.pi * 2
        breath = math.sin(t) * 0.025
        if pb.get('J_Bip_C_Hips'):
            pb['J_Bip_C_Hips'].location = (0, 0, 0); pb['J_Bip_C_Hips'].keyframe_insert(data_path="location", frame=frame)
            pb['J_Bip_C_Hips'].rotation_quaternion = create_quaternion((0, 0, 0)); pb['J_Bip_C_Hips'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_C_Spine'): pb['J_Bip_C_Spine'].rotation_quaternion = create_quaternion((0.01 + breath * 0.3, 0, 0)); pb['J_Bip_C_Spine'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_C_UpperChest'): pb['J_Bip_C_UpperChest'].rotation_quaternion = create_quaternion((0.02 + breath * 0.7, 0, 0)); pb['J_Bip_C_UpperChest'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_C_Neck'): pb['J_Bip_C_Neck'].rotation_quaternion = create_quaternion((0, 0, 0)); pb['J_Bip_C_Neck'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_C_Head'): pb['J_Bip_C_Head'].rotation_quaternion = create_quaternion((-0.01, 0, 0)); pb['J_Bip_C_Head'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        l_arm_q = create_quaternion((0.0, 0.0, -1.35))
        r_arm_q = create_quaternion((0.0, 0.0, 1.35))
        if pb.get('J_Bip_L_UpperArm'): pb['J_Bip_L_UpperArm'].rotation_quaternion = l_arm_q; pb['J_Bip_L_UpperArm'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_R_UpperArm'): pb['J_Bip_R_UpperArm'].rotation_quaternion = r_arm_q; pb['J_Bip_R_UpperArm'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_L_LowerArm'): pb['J_Bip_L_LowerArm'].rotation_quaternion = create_quaternion((0, 0, 0)); pb['J_Bip_L_LowerArm'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_R_LowerArm'): pb['J_Bip_R_LowerArm'].rotation_quaternion = create_quaternion((0, 0, 0)); pb['J_Bip_R_LowerArm'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_L_Hand'): pb['J_Bip_L_Hand'].rotation_quaternion = create_quaternion((0, -0.15, 0)); pb['J_Bip_L_Hand'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_R_Hand'): pb['J_Bip_R_Hand'].rotation_quaternion = create_quaternion((0, 0.15, 0)); pb['J_Bip_R_Hand'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        l_leg_q = create_quaternion((0, 0, -0.02))
        r_leg_q = create_quaternion((0, 0, 0.02))
        if pb.get('J_Bip_L_UpperLeg'): pb['J_Bip_L_UpperLeg'].rotation_quaternion = l_leg_q; pb['J_Bip_L_UpperLeg'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_R_UpperLeg'): pb['J_Bip_R_UpperLeg'].rotation_quaternion = r_leg_q; pb['J_Bip_R_UpperLeg'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_L_LowerLeg'): pb['J_Bip_L_LowerLeg'].rotation_quaternion = create_quaternion((0, 0, 0)); pb['J_Bip_L_LowerLeg'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_R_LowerLeg'): pb['J_Bip_R_LowerLeg'].rotation_quaternion = create_quaternion((0, 0, 0)); pb['J_Bip_R_LowerLeg'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_L_Foot'): pb['J_Bip_L_Foot'].rotation_quaternion = create_quaternion((0, 0, 0)); pb['J_Bip_L_Foot'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_R_Foot'): pb['J_Bip_R_Foot'].rotation_quaternion = create_quaternion((0, 0, 0)); pb['J_Bip_R_Foot'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        for side in ['L', 'R']:
            for f_name in ['Thumb', 'Index', 'Middle', 'Ring', 'Little']:
                for seg in range(1, 4):
                    b_name = f'J_Bip_{side}_{f_name}{seg}'
                    if pb.get(b_name): pb[b_name].rotation_quaternion = create_quaternion((0, 0, 0)); pb[b_name].keyframe_insert(data_path="rotation_quaternion", frame=frame)

    # =========================================================================
    # STATE 2: 02_DungNghi (120 frames)
    # =========================================================================
    print(">>> 2. Creating 02_DungNghi...")
    act_nghi = bpy.data.actions.new(name="02_DungNghi")
    char_arm.animation_data.action = act_nghi
    created_actions.append(act_nghi)
    for frame in range(1, 121):
        bpy.context.scene.frame_set(frame)
        t = (frame / 120.0) * math.pi * 2
        sway = math.sin(t) * 0.015
        breath = math.sin(t * 2) * 0.03
        if pb.get('J_Bip_C_Hips'):
            pb['J_Bip_C_Hips'].location = (0.035 + sway * 0.5, 0, -0.015); pb['J_Bip_C_Hips'].keyframe_insert(data_path="location", frame=frame)
            pb['J_Bip_C_Hips'].rotation_quaternion = create_quaternion((0.02, 0.04, -0.06 + sway)); pb['J_Bip_C_Hips'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_C_Spine'): pb['J_Bip_C_Spine'].rotation_quaternion = create_quaternion((0.02 + breath * 0.3, -0.02, 0.04)); pb['J_Bip_C_Spine'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_C_UpperChest'): pb['J_Bip_C_UpperChest'].rotation_quaternion = create_quaternion((0.03 + breath * 0.7, -0.02, 0.03)); pb['J_Bip_C_UpperChest'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_C_Neck'): pb['J_Bip_C_Neck'].rotation_quaternion = create_quaternion((0.01, 0.02, 0)); pb['J_Bip_C_Neck'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_C_Head'): pb['J_Bip_C_Head'].rotation_quaternion = create_quaternion((0.02, 0.04 + sway, 0.03)); pb['J_Bip_C_Head'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        r_up_q = create_quaternion((-0.02, 0.0, 0.05))
        if pb.get('J_Bip_R_UpperLeg'): pb['J_Bip_R_UpperLeg'].rotation_quaternion = r_up_q; pb['J_Bip_R_UpperLeg'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_R_LowerLeg'): pb['J_Bip_R_LowerLeg'].rotation_quaternion = create_quaternion((0.04, 0, 0)); pb['J_Bip_R_LowerLeg'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        l_up_q = create_quaternion((-0.18, 0.05, -0.08))
        if pb.get('J_Bip_L_UpperLeg'): pb['J_Bip_L_UpperLeg'].rotation_quaternion = l_up_q; pb['J_Bip_L_UpperLeg'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_L_LowerLeg'): pb['J_Bip_L_LowerLeg'].rotation_quaternion = create_quaternion((0.35, 0, 0)); pb['J_Bip_L_LowerLeg'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        l_arm_q = create_quaternion((0.05, -0.05, -1.22 + sway))
        r_arm_q = create_quaternion((0.03, 0.05, 1.24 - sway))
        if pb.get('J_Bip_L_UpperArm'): pb['J_Bip_L_UpperArm'].rotation_quaternion = l_arm_q; pb['J_Bip_L_UpperArm'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_R_UpperArm'): pb['J_Bip_R_UpperArm'].rotation_quaternion = r_arm_q; pb['J_Bip_R_UpperArm'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_L_LowerArm'): pb['J_Bip_L_LowerArm'].rotation_quaternion = create_quaternion((0, 0, -0.18)); pb['J_Bip_L_LowerArm'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_R_LowerArm'): pb['J_Bip_R_LowerArm'].rotation_quaternion = create_quaternion((0, 0, 0.15)); pb['J_Bip_R_LowerArm'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

    # =========================================================================
    # STATE 3: 03_TPose (30 frames)
    # =========================================================================
    print(">>> 3. Creating 03_TPose...")
    act_tpose = bpy.data.actions.new(name="03_TPose")
    char_arm.animation_data.action = act_tpose
    created_actions.append(act_tpose)
    for frame in range(1, 31):
        bpy.context.scene.frame_set(frame)
        if pb.get('J_Bip_C_Hips'):
            pb['J_Bip_C_Hips'].location = (0, 0, 0); pb['J_Bip_C_Hips'].keyframe_insert(data_path="location", frame=frame)
            pb['J_Bip_C_Hips'].rotation_quaternion = create_quaternion((0, 0, 0)); pb['J_Bip_C_Hips'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        for b_name in ['J_Bip_C_Spine', 'J_Bip_C_UpperChest', 'J_Bip_C_Neck', 'J_Bip_C_Head',
                       'J_Bip_L_Shoulder', 'J_Bip_R_Shoulder', 'J_Bip_L_UpperArm', 'J_Bip_L_LowerArm', 'J_Bip_L_Hand',
                       'J_Bip_R_UpperArm', 'J_Bip_R_LowerArm', 'J_Bip_R_Hand',
                       'J_Bip_L_UpperLeg', 'J_Bip_L_LowerLeg', 'J_Bip_L_Foot',
                       'J_Bip_R_UpperLeg', 'J_Bip_R_LowerLeg', 'J_Bip_R_Foot']:
            if pb.get(b_name): pb[b_name].rotation_quaternion = create_quaternion((0, 0, 0)); pb[b_name].keyframe_insert(data_path="rotation_quaternion", frame=frame)

    # =========================================================================
    # STATE 4: 04_BuocDi_CoBan (60 frames)
    # =========================================================================
    print(">>> 4. Creating 04_BuocDi_CoBan...")
    act_walk_basic = bpy.data.actions.new(name="04_BuocDi_CoBan")
    char_arm.animation_data.action = act_walk_basic
    created_actions.append(act_walk_basic)
    for frame in range(1, 61):
        bpy.context.scene.frame_set(frame)
        phi = (frame / 60.0) * math.pi * 2
        l_stride = math.sin(phi)
        r_stride = -math.sin(phi)
        if pb.get('J_Bip_C_Hips'):
            pb['J_Bip_C_Hips'].location = (math.sin(phi) * 0.04, 0, -abs(math.sin(phi * 2)) * 0.045); pb['J_Bip_C_Hips'].keyframe_insert(data_path="location", frame=frame)
            pb['J_Bip_C_Hips'].rotation_quaternion = create_quaternion((0.04, -math.sin(phi) * 0.10, math.sin(phi) * 0.06)); pb['J_Bip_C_Hips'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_C_Spine'): pb['J_Bip_C_Spine'].rotation_quaternion = create_quaternion((0.02, math.sin(phi) * 0.06, -math.sin(phi) * 0.03)); pb['J_Bip_C_Spine'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_L_UpperLeg'): pb['J_Bip_L_UpperLeg'].rotation_quaternion = create_quaternion((l_stride * 0.55, 0, -0.02)); pb['J_Bip_L_UpperLeg'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_L_LowerLeg'): pb['J_Bip_L_LowerLeg'].rotation_quaternion = create_quaternion((max(0.0, -l_stride * 1.15 + 0.15), 0, 0)); pb['J_Bip_L_LowerLeg'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_R_UpperLeg'): pb['J_Bip_R_UpperLeg'].rotation_quaternion = create_quaternion((r_stride * 0.55, 0, 0.02)); pb['J_Bip_R_UpperLeg'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_R_LowerLeg'): pb['J_Bip_R_LowerLeg'].rotation_quaternion = create_quaternion((max(0.0, -r_stride * 1.15 + 0.15), 0, 0)); pb['J_Bip_R_LowerLeg'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_L_UpperArm'): pb['J_Bip_L_UpperArm'].rotation_quaternion = create_quaternion((r_stride * 0.45, 0, -1.25)); pb['J_Bip_L_UpperArm'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_R_UpperArm'): pb['J_Bip_R_UpperArm'].rotation_quaternion = create_quaternion((l_stride * 0.45, 0, 1.25)); pb['J_Bip_R_UpperArm'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

    # =========================================================================
    # STATE 5: 05_BuocDi_TuNhien (60 frames STRICT CONTINUOUS GROUND CONTACT IK)
    # =========================================================================
    print(">>> 5. Creating 05_BuocDi_TuNhien with Mathematical 2-Bone Ground Planted IK...")
    act_walk_ik = bpy.data.actions.new(name="05_BuocDi_TuNhien")
    char_arm.animation_data.action = act_walk_ik
    created_actions.append(act_walk_ik)

    total_frames = 60
    stride_half_len = 0.16 # Half stride length forward/backward
    base_ankle_y = -0.745  # Distance from hip to ground ankle

    for frame in range(1, total_frames + 1):
        bpy.context.scene.frame_set(frame)
        # Normalized phase tau in [0, 1)
        tau = (frame - 1) / total_frames
        
        # 1. Calculate Left & Right Foot Ankle Target Positions relative to Hip
        # Stance phase: tau in [0, 0.60] (60% time on ground)
        # Swing phase:  tau in [0.60, 1.00] (40% time in air)
        
        # Left Leg:
        if tau <= 0.60:
            # Stance: Foot slides smoothly along ground Y = 0 from +stride to -stride
            s_t = tau / 0.60
            l_x = stride_half_len * (1.0 - 2.0 * s_t)
            l_y = base_ankle_y # Ground level
        else:
            # Swing: Foot lifts off, swings forward to +stride
            sw_t = (tau - 0.60) / 0.40
            l_x = -stride_half_len + 2.0 * stride_half_len * sw_t
            # Parabolic lift in air (peaks at +0.055m)
            l_y = base_ankle_y + math.sin(sw_t * math.pi) * 0.055

        # Right Leg: Phase offset by 0.50 (50%)
        tau_r = (tau + 0.50) % 1.0
        if tau_r <= 0.60:
            s_t = tau_r / 0.60
            r_x = stride_half_len * (1.0 - 2.0 * s_t)
            r_y = base_ankle_y # Ground level
        else:
            sw_t = (tau_r - 0.60) / 0.40
            r_x = -stride_half_len + 2.0 * stride_half_len * sw_t
            r_y = base_ankle_y + math.sin(sw_t * math.pi) * 0.055

        # 2. Dynamic Hip Height & Sway
        # Hip lowers when legs split into stride to ensure ground contact
        # Hip vertical bounce: 2 troughs per cycle when legs are widest apart
        hip_drop = -0.025 * (math.sin(tau * math.pi * 2.0) ** 2)
        hip_sway_x = 0.020 * math.sin(tau * math.pi * 2.0)

        # Apply target offsets accounting for hip drop
        l_thigh, l_knee, l_ankle = solve_leg_ik(l_x, l_y - hip_drop)
        r_thigh, r_knee, r_ankle = solve_leg_ik(r_x, r_y - hip_drop)

        # 3. Apply to Character Hips
        if pb.get('J_Bip_C_Hips'):
            pb['J_Bip_C_Hips'].location = (hip_sway_x, 0.0, hip_drop)
            pb['J_Bip_C_Hips'].keyframe_insert(data_path="location", frame=frame)
            # Pelvis rotation: pitch forward slightly, yaw with legs, roll with hip sway
            pelvis_pitch = 0.02
            pelvis_yaw = math.sin(tau * math.pi * 2.0) * 0.07
            pelvis_roll = -math.sin(tau * math.pi * 2.0) * 0.05
            pb['J_Bip_C_Hips'].rotation_quaternion = create_quaternion((pelvis_pitch, pelvis_yaw, pelvis_roll))
            pb['J_Bip_C_Hips'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        # 4. Apply IK Rotations to Legs
        if pb.get('J_Bip_L_UpperLeg'):
            pb['J_Bip_L_UpperLeg'].rotation_quaternion = create_quaternion((l_thigh, 0.0, -0.02))
            pb['J_Bip_L_UpperLeg'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_L_LowerLeg'):
            pb['J_Bip_L_LowerLeg'].rotation_quaternion = create_quaternion((l_knee, 0.0, 0.0))
            pb['J_Bip_L_LowerLeg'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_L_Foot'):
            pb['J_Bip_L_Foot'].rotation_quaternion = create_quaternion((l_ankle, 0.0, 0.0))
            pb['J_Bip_L_Foot'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        if pb.get('J_Bip_R_UpperLeg'):
            pb['J_Bip_R_UpperLeg'].rotation_quaternion = create_quaternion((r_thigh, 0.0, 0.02))
            pb['J_Bip_R_UpperLeg'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_R_LowerLeg'):
            pb['J_Bip_R_LowerLeg'].rotation_quaternion = create_quaternion((r_knee, 0.0, 0.0))
            pb['J_Bip_R_LowerLeg'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_R_Foot'):
            pb['J_Bip_R_Foot'].rotation_quaternion = create_quaternion((r_ankle, 0.0, 0.0))
            pb['J_Bip_R_Foot'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        # 5. Spine & Chest Counter-Balance
        if pb.get('J_Bip_C_Spine'):
            pb['J_Bip_C_Spine'].rotation_quaternion = create_quaternion((0.015, -pelvis_yaw * 0.6, -pelvis_roll * 0.5))
            pb['J_Bip_C_Spine'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_C_UpperChest'):
            pb['J_Bip_C_UpperChest'].rotation_quaternion = create_quaternion((0.025, -pelvis_yaw * 0.4, -pelvis_roll * 0.4))
            pb['J_Bip_C_UpperChest'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        # 6. Neck & Head: Straight forward with gentle nodding
        if pb.get('J_Bip_C_Neck'):
            pb['J_Bip_C_Neck'].rotation_quaternion = create_quaternion((0.015 * math.sin(tau * math.pi * 4.0), 0.0, 0.0))
            pb['J_Bip_C_Neck'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_C_Head'):
            pb['J_Bip_C_Head'].rotation_quaternion = create_quaternion((-0.02 + 0.02 * math.sin(tau * math.pi * 4.0), 0.0, 0.0))
            pb['J_Bip_C_Head'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        # 7. Arms & Hands: Naturally down along the flanks with graceful swing
        arm_swing = math.sin(tau * math.pi * 2.0) * 0.25
        if pb.get('J_Bip_L_UpperArm'):
            pb['J_Bip_L_UpperArm'].rotation_quaternion = create_quaternion((-arm_swing, 0.0, -1.26))
            pb['J_Bip_L_UpperArm'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_L_LowerArm'):
            pb['J_Bip_L_LowerArm'].rotation_quaternion = create_quaternion((0.0, 0.0, -0.20))
            pb['J_Bip_L_LowerArm'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_L_Hand'):
            pb['J_Bip_L_Hand'].rotation_quaternion = create_quaternion((0.0, -0.15, 0.0))
            pb['J_Bip_L_Hand'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        if pb.get('J_Bip_R_UpperArm'):
            pb['J_Bip_R_UpperArm'].rotation_quaternion = create_quaternion((arm_swing, 0.0, 1.26))
            pb['J_Bip_R_UpperArm'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_R_LowerArm'):
            pb['J_Bip_R_LowerArm'].rotation_quaternion = create_quaternion((0.0, 0.0, 0.20))
            pb['J_Bip_R_LowerArm'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_R_Hand'):
            pb['J_Bip_R_Hand'].rotation_quaternion = create_quaternion((0.0, 0.15, 0.0))
            pb['J_Bip_R_Hand'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        # Fingers: relaxed feminine curve
        for side in ['L', 'R']:
            for f_name in ['Thumb', 'Index', 'Middle', 'Ring', 'Little']:
                for seg in range(1, 4):
                    b_name = f'J_Bip_{side}_{f_name}{seg}'
                    if pb.get(b_name):
                        pb[b_name].rotation_quaternion = create_quaternion((0.0, -0.18, -0.10 if side=='L' else 0.10))
                        pb[b_name].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        # Hair dynamics
        for pb_b in pb:
            if 'Hair' in pb_b.name:
                pb_b.rotation_quaternion = create_quaternion((0.08 + 0.05 * math.sin(tau * math.pi * 4.0), 0.0, 0.04 * math.sin(tau * math.pi * 2.0)))
                pb_b.keyframe_insert(data_path="rotation_quaternion", frame=frame)

        # Synchronize clothing secondary bones
        if pb.get('J_Bip_L_UpperArm'):
            for s in ['J_Aim_L_TopsUpperArm', 'J_Roll_L_UpperArm', 'J_Sec_L_TopsUpperArmInside', 'J_Sec_L_TopsUpperArmOutside']:
                if pb.get(s): pb[s].rotation_quaternion = pb['J_Bip_L_UpperArm'].rotation_quaternion; pb[s].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_R_UpperArm'):
            for s in ['J_Aim_R_TopsUpperArm', 'J_Roll_R_UpperArm', 'J_Sec_R_TopsUpperArmInside', 'J_Sec_R_TopsUpperArmOutside']:
                if pb.get(s): pb[s].rotation_quaternion = pb['J_Bip_R_UpperArm'].rotation_quaternion; pb[s].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_L_UpperLeg'):
            for s in ['J_Aim_L_UpperLeg', 'J_Roll_L_UpperLeg', 'J_Sec_L_TopsUpperLegFront', 'J_Sec_L_TopsUpperLegBack', 'J_Sec_L_TopsUpperLegSide']:
                if pb.get(s): pb[s].rotation_quaternion = pb['J_Bip_L_UpperLeg'].rotation_quaternion; pb[s].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_R_UpperLeg'):
            for s in ['J_Aim_R_UpperLeg', 'J_Roll_R_UpperLeg', 'J_Sec_R_TopsUpperLegFront', 'J_Sec_R_TopsUpperLegBack', 'J_Sec_R_TopsUpperLegSide']:
                if pb.get(s): pb[s].rotation_quaternion = pb['J_Bip_R_UpperLeg'].rotation_quaternion; pb[s].keyframe_insert(data_path="rotation_quaternion", frame=frame)

    # Push all 5 actions to NLA Tracks
    print(">>> Pushing all 5 actions to NLA tracks...")
    for act in created_actions:
        track = char_arm.animation_data.nla_tracks.new()
        track.name = act.name
        track.strips.new(act.name, 1, act)

    print(">>> Actions in Blender database:", [a.name for a in bpy.data.actions])

    bpy.ops.object.mode_set(mode='OBJECT')

    # Facial Blendshapes
    face_obj = None
    for obj in bpy.data.objects:
        if obj.type == 'MESH' and 'face' in obj.name.lower() and obj.data.shape_keys:
            face_obj = obj
            break
            
    if face_obj and face_obj.data.shape_keys:
        kb = face_obj.data.shape_keys.key_blocks
        face_obj.data.shape_keys.animation_data_create()
        vowels = ['Face_Blendshape.Fcl_MTH_A', 'Face_Blendshape.Fcl_MTH_I', 'Face_Blendshape.Fcl_MTH_U', 'Face_Blendshape.Fcl_MTH_O', 'Face_Blendshape.Fcl_MTH_E']
        for frame in range(1, 121):
            cycle_idx = int((frame / 16.0)) % 5
            mouth_open = max(0.0, math.sin((frame / 30.0) * math.pi * 6.0)) * 0.95
            is_wink = (40 <= frame <= 55) or (90 <= frame <= 105)
            for i, v_name in enumerate(vowels):
                if v_name in kb:
                    kb[v_name].value = mouth_open if i == cycle_idx else 0.0
                    kb[v_name].keyframe_insert(data_path="value", frame=frame)
            if 'Face_Blendshape.Fcl_ALL_Joy' in kb:
                kb['Face_Blendshape.Fcl_ALL_Joy'].value = 0.45 + 0.3 * math.sin((frame / 120.0) * math.pi * 4.0)
                kb['Face_Blendshape.Fcl_ALL_Joy'].keyframe_insert(data_path="value", frame=frame)
            if 'Face_Blendshape.Fcl_EYE_Close_L' in kb:
                kb['Face_Blendshape.Fcl_EYE_Close_L'].value = 1.0 if is_wink else 0.0
                kb['Face_Blendshape.Fcl_EYE_Close_L'].keyframe_insert(data_path="value", frame=frame)

    print(">>> Exporting PRISTINE GLB, FBX, BLEND...")
    for folder, fname in [(out_b_dir, "female_singer_anime_idol"), (stage_dir, "female_singer_anime_pro")]:
        bpy.ops.export_scene.gltf(
            filepath=f"{folder}/{fname}.glb",
            export_format='GLB',
            export_animations=True,
            export_nla_strips=True,
            export_morph=True,
            export_skins=True
        )
        bpy.ops.export_scene.fbx(
            filepath=f"{folder}/{fname}.fbx",
            bake_anim=True,
            bake_anim_use_all_actions=True,
            use_mesh_modifiers=True,
            add_leaf_bones=False
        )
        bpy.ops.wm.save_as_mainfile(filepath=f"{folder}/{fname}.blend")
        
    print(">>> GROUND IK WALK EXPORTED!")

if __name__ == '__main__':
    build_ground_ik_walk()
    print("=== GROUND IK BUILD COMPLETE ===")
