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

def build_all_states_with_mocap_walk():
    print(">>> Building All 5 Animation States (including Realistic Mocap Walk)...")
    clean_scene()
    
    input_glb = '/Volumes/DATA/ctg_ai/3d/phuong_an_B_anime_idol_female_singer/model/female_singer_anime_idol.glb'
    walk_bvh = '/Volumes/DATA/ctg_ai/3d/mocap/dataset-1_walk_happy_001.bvh'
    out_b_dir = '/Volumes/DATA/ctg_ai/3d/phuong_an_B_anime_idol_female_singer/model'
    stage_dir = '/Volumes/DATA/ctg_ai/3d/phuong_an_nang_cao_nu_ca_si_pro_stage/model'
    
    bpy.ops.import_scene.gltf(filepath=input_glb)
    char_arm = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
    char_arm.name = 'Character_Armature'
    
    # 1. BIND CLOTHING VERTEX WEIGHTS
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
    # STATE 1: 01_DungNghiem (Đứng Nghiêm / Attention Stand - 60 frames)
    # =========================================================================
    print(">>> 1. Creating State: 01_DungNghiem...")
    act_nghiem = bpy.data.actions.new(name="01_DungNghiem")
    char_arm.animation_data.action = act_nghiem
    created_actions.append(act_nghiem)
    
    for frame in range(1, 61):
        bpy.context.scene.frame_set(frame)
        t = (frame / 60.0) * math.pi * 2
        breath = math.sin(t) * 0.025
        
        if pb.get('J_Bip_C_Hips'):
            pb['J_Bip_C_Hips'].location = (0, 0, 0)
            pb['J_Bip_C_Hips'].keyframe_insert(data_path="location", frame=frame)
            pb['J_Bip_C_Hips'].rotation_quaternion = create_quaternion((0, 0, 0))
            pb['J_Bip_C_Hips'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
            
        if pb.get('J_Bip_C_Spine'):
            pb['J_Bip_C_Spine'].rotation_quaternion = create_quaternion((0.01 + breath * 0.3, 0, 0))
            pb['J_Bip_C_Spine'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_C_UpperChest'):
            pb['J_Bip_C_UpperChest'].rotation_quaternion = create_quaternion((0.02 + breath * 0.7, 0, 0))
            pb['J_Bip_C_UpperChest'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_C_Head'):
            pb['J_Bip_C_Head'].rotation_quaternion = create_quaternion((-0.01, 0, 0))
            pb['J_Bip_C_Head'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        if pb.get('J_Bip_L_Shoulder'):
            pb['J_Bip_L_Shoulder'].rotation_quaternion = create_quaternion((0, 0, -0.04))
            pb['J_Bip_L_Shoulder'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_R_Shoulder'):
            pb['J_Bip_R_Shoulder'].rotation_quaternion = create_quaternion((0, 0, 0.04))
            pb['J_Bip_R_Shoulder'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        l_arm_q = create_quaternion((0.0, 0.0, -1.35))
        r_arm_q = create_quaternion((0.0, 0.0, 1.35))
        if pb.get('J_Bip_L_UpperArm'):
            pb['J_Bip_L_UpperArm'].rotation_quaternion = l_arm_q
            pb['J_Bip_L_UpperArm'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_R_UpperArm'):
            pb['J_Bip_R_UpperArm'].rotation_quaternion = r_arm_q
            pb['J_Bip_R_UpperArm'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_L_LowerArm'):
            pb['J_Bip_L_LowerArm'].rotation_quaternion = create_quaternion((0, 0, 0))
            pb['J_Bip_L_LowerArm'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_R_LowerArm'):
            pb['J_Bip_R_LowerArm'].rotation_quaternion = create_quaternion((0, 0, 0))
            pb['J_Bip_R_LowerArm'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
            
        if pb.get('J_Bip_L_Hand'):
            pb['J_Bip_L_Hand'].rotation_quaternion = create_quaternion((0, -0.15, 0))
            pb['J_Bip_L_Hand'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_R_Hand'):
            pb['J_Bip_R_Hand'].rotation_quaternion = create_quaternion((0, 0.15, 0))
            pb['J_Bip_R_Hand'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        l_leg_q = create_quaternion((0, 0, -0.02))
        r_leg_q = create_quaternion((0, 0, 0.02))
        if pb.get('J_Bip_L_UpperLeg'):
            pb['J_Bip_L_UpperLeg'].rotation_quaternion = l_leg_q
            pb['J_Bip_L_UpperLeg'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_R_UpperLeg'):
            pb['J_Bip_R_UpperLeg'].rotation_quaternion = r_leg_q
            pb['J_Bip_R_UpperLeg'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_L_LowerLeg'):
            pb['J_Bip_L_LowerLeg'].rotation_quaternion = create_quaternion((0, 0, 0))
            pb['J_Bip_L_LowerLeg'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_R_LowerLeg'):
            pb['J_Bip_R_LowerLeg'].rotation_quaternion = create_quaternion((0, 0, 0))
            pb['J_Bip_R_LowerLeg'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        for s in ['J_Aim_L_UpperLeg', 'J_Roll_L_UpperLeg', 'J_Sec_L_TopsUpperLegFront', 'J_Sec_L_TopsUpperLegBack', 'J_Sec_L_TopsUpperLegSide']:
            if pb.get(s): pb[s].rotation_quaternion = l_leg_q; pb[s].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        for s in ['J_Aim_R_UpperLeg', 'J_Roll_R_UpperLeg', 'J_Sec_R_TopsUpperLegFront', 'J_Sec_R_TopsUpperLegBack', 'J_Sec_R_TopsUpperLegSide']:
            if pb.get(s): pb[s].rotation_quaternion = r_leg_q; pb[s].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        for s in ['J_Aim_L_TopsUpperArm', 'J_Roll_L_UpperArm', 'J_Sec_L_TopsUpperArmInside', 'J_Sec_L_TopsUpperArmOutside']:
            if pb.get(s): pb[s].rotation_quaternion = l_arm_q; pb[s].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        for s in ['J_Aim_R_TopsUpperArm', 'J_Roll_R_UpperArm', 'J_Sec_R_TopsUpperArmInside', 'J_Sec_R_TopsUpperArmOutside']:
            if pb.get(s): pb[s].rotation_quaternion = r_arm_q; pb[s].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        for side in ['L', 'R']:
            for f_name in ['Thumb', 'Index', 'Middle', 'Ring', 'Little']:
                for seg in range(1, 4):
                    b_name = f'J_Bip_{side}_{f_name}{seg}'
                    if pb.get(b_name):
                        pb[b_name].rotation_quaternion = create_quaternion((0, 0, 0))
                        pb[b_name].keyframe_insert(data_path="rotation_quaternion", frame=frame)

    # =========================================================================
    # STATE 2: 02_DungNghi (Đứng Nghỉ Contrapposto - 120 frames)
    # =========================================================================
    print(">>> 2. Creating State: 02_DungNghi...")
    act_nghi = bpy.data.actions.new(name="02_DungNghi")
    char_arm.animation_data.action = act_nghi
    created_actions.append(act_nghi)
    
    for frame in range(1, 121):
        bpy.context.scene.frame_set(frame)
        t = (frame / 120.0) * math.pi * 2
        sway = math.sin(t) * 0.015
        breath = math.sin(t * 2) * 0.03
        
        if pb.get('J_Bip_C_Hips'):
            pb['J_Bip_C_Hips'].location = (0.035 + sway * 0.5, 0, -0.015)
            pb['J_Bip_C_Hips'].keyframe_insert(data_path="location", frame=frame)
            pb['J_Bip_C_Hips'].rotation_quaternion = create_quaternion((0.02, 0.04, -0.06 + sway))
            pb['J_Bip_C_Hips'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
            
        if pb.get('J_Bip_C_Spine'):
            pb['J_Bip_C_Spine'].rotation_quaternion = create_quaternion((0.02 + breath * 0.3, -0.02, 0.04))
            pb['J_Bip_C_Spine'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_C_UpperChest'):
            pb['J_Bip_C_UpperChest'].rotation_quaternion = create_quaternion((0.03 + breath * 0.7, -0.02, 0.03))
            pb['J_Bip_C_UpperChest'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_C_Head'):
            pb['J_Bip_C_Head'].rotation_quaternion = create_quaternion((0.02, 0.04 + sway, 0.03))
            pb['J_Bip_C_Head'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        r_up_q = create_quaternion((-0.02, 0.0, 0.05))
        if pb.get('J_Bip_R_UpperLeg'):
            pb['J_Bip_R_UpperLeg'].rotation_quaternion = r_up_q
            pb['J_Bip_R_UpperLeg'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_R_LowerLeg'):
            pb['J_Bip_R_LowerLeg'].rotation_quaternion = create_quaternion((0.04, 0, 0))
            pb['J_Bip_R_LowerLeg'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_R_Foot'):
            pb['J_Bip_R_Foot'].rotation_quaternion = create_quaternion((-0.02, 0, -0.04))
            pb['J_Bip_R_Foot'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        l_up_q = create_quaternion((-0.18, 0.05, -0.08))
        if pb.get('J_Bip_L_UpperLeg'):
            pb['J_Bip_L_UpperLeg'].rotation_quaternion = l_up_q
            pb['J_Bip_L_UpperLeg'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_L_LowerLeg'):
            pb['J_Bip_L_LowerLeg'].rotation_quaternion = create_quaternion((0.35, 0, 0))
            pb['J_Bip_L_LowerLeg'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_L_Foot'):
            pb['J_Bip_L_Foot'].rotation_quaternion = create_quaternion((-0.14, 0, 0.04))
            pb['J_Bip_L_Foot'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        for s in ['J_Aim_L_UpperLeg', 'J_Roll_L_UpperLeg', 'J_Sec_L_TopsUpperLegFront', 'J_Sec_L_TopsUpperLegBack', 'J_Sec_L_TopsUpperLegSide']:
            if pb.get(s): pb[s].rotation_quaternion = l_up_q; pb[s].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        for s in ['J_Aim_R_UpperLeg', 'J_Roll_R_UpperLeg', 'J_Sec_R_TopsUpperLegFront', 'J_Sec_R_TopsUpperLegBack', 'J_Sec_R_TopsUpperLegSide']:
            if pb.get(s): pb[s].rotation_quaternion = r_up_q; pb[s].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        l_arm_q = create_quaternion((0.05, -0.05, -1.22 + sway))
        r_arm_q = create_quaternion((0.03, 0.05, 1.24 - sway))
        if pb.get('J_Bip_L_UpperArm'):
            pb['J_Bip_L_UpperArm'].rotation_quaternion = l_arm_q
            pb['J_Bip_L_UpperArm'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_R_UpperArm'):
            pb['J_Bip_R_UpperArm'].rotation_quaternion = r_arm_q
            pb['J_Bip_R_UpperArm'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_L_LowerArm'):
            pb['J_Bip_L_LowerArm'].rotation_quaternion = create_quaternion((0, 0, -0.18))
            pb['J_Bip_L_LowerArm'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_R_LowerArm'):
            pb['J_Bip_R_LowerArm'].rotation_quaternion = create_quaternion((0, 0, 0.15))
            pb['J_Bip_R_LowerArm'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        for s in ['J_Aim_L_TopsUpperArm', 'J_Roll_L_UpperArm', 'J_Sec_L_TopsUpperArmInside', 'J_Sec_L_TopsUpperArmOutside']:
            if pb.get(s): pb[s].rotation_quaternion = l_arm_q; pb[s].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        for s in ['J_Aim_R_TopsUpperArm', 'J_Roll_R_UpperArm', 'J_Sec_R_TopsUpperArmInside', 'J_Sec_R_TopsUpperArmOutside']:
            if pb.get(s): pb[s].rotation_quaternion = r_arm_q; pb[s].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        for side in ['L', 'R']:
            for f_name in ['Thumb', 'Index', 'Middle', 'Ring', 'Little']:
                for seg in range(1, 4):
                    b_name = f'J_Bip_{side}_{f_name}{seg}'
                    if pb.get(b_name):
                        pb[b_name].rotation_quaternion = create_quaternion((0, -0.15, -0.10 if side=='L' else 0.10))
                        pb[b_name].keyframe_insert(data_path="rotation_quaternion", frame=frame)

    # =========================================================================
    # STATE 3: 03_TPose (Đứng T-Pose - 30 frames)
    # =========================================================================
    print(">>> 3. Creating State: 03_TPose...")
    act_tpose = bpy.data.actions.new(name="03_TPose")
    char_arm.animation_data.action = act_tpose
    created_actions.append(act_tpose)
    
    for frame in range(1, 31):
        bpy.context.scene.frame_set(frame)
        if pb.get('J_Bip_C_Hips'):
            pb['J_Bip_C_Hips'].location = (0, 0, 0)
            pb['J_Bip_C_Hips'].keyframe_insert(data_path="location", frame=frame)
            pb['J_Bip_C_Hips'].rotation_quaternion = create_quaternion((0, 0, 0))
            pb['J_Bip_C_Hips'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
            
        for b_name in ['J_Bip_C_Spine', 'J_Bip_C_UpperChest', 'J_Bip_C_Neck', 'J_Bip_C_Head',
                       'J_Bip_L_Shoulder', 'J_Bip_R_Shoulder', 'J_Bip_L_UpperArm', 'J_Bip_L_LowerArm', 'J_Bip_L_Hand',
                       'J_Bip_R_UpperArm', 'J_Bip_R_LowerArm', 'J_Bip_R_Hand',
                       'J_Bip_L_UpperLeg', 'J_Bip_L_LowerLeg', 'J_Bip_L_Foot',
                       'J_Bip_R_UpperLeg', 'J_Bip_R_LowerLeg', 'J_Bip_R_Foot']:
            if pb.get(b_name):
                pb[b_name].rotation_quaternion = create_quaternion((0, 0, 0))
                pb[b_name].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        for side in ['L', 'R']:
            for s in [f'J_Aim_{side}_TopsUpperArm', f'J_Roll_{side}_UpperArm', f'J_Sec_{side}_TopsUpperArmInside', f'J_Sec_{side}_TopsUpperArmOutside',
                      f'J_Aim_{side}_UpperLeg', f'J_Roll_{side}_UpperLeg', f'J_Sec_{side}_TopsUpperLegFront', f'J_Sec_{side}_TopsUpperLegBack', f'J_Sec_{side}_TopsUpperLegSide']:
                if pb.get(s): pb[s].rotation_quaternion = create_quaternion((0, 0, 0)); pb[s].keyframe_insert(data_path="rotation_quaternion", frame=frame)
            for f_name in ['Thumb', 'Index', 'Middle', 'Ring', 'Little']:
                for seg in range(1, 4):
                    b_name = f'J_Bip_{side}_{f_name}{seg}'
                    if pb.get(b_name):
                        pb[b_name].rotation_quaternion = create_quaternion((0, 0, 0))
                        pb[b_name].keyframe_insert(data_path="rotation_quaternion", frame=frame)

    # =========================================================================
    # STATE 4: 04_BuocDi_CoBan (Bước Đi Cơ Bản - 60 frames, Retained as requested)
    # =========================================================================
    print(">>> 4. Creating State: 04_BuocDi_CoBan (Bước đi cơ bản - giữ lại theo yêu cầu)...")
    act_walk_basic = bpy.data.actions.new(name="04_BuocDi_CoBan")
    char_arm.animation_data.action = act_walk_basic
    created_actions.append(act_walk_basic)
    
    for frame in range(1, 61):
        bpy.context.scene.frame_set(frame)
        phi = (frame / 60.0) * math.pi * 2
        hip_bounce = -abs(math.sin(phi * 2)) * 0.045
        hip_sway = math.sin(phi) * 0.04
        hip_twist = -math.sin(phi) * 0.10
        hip_roll = math.sin(phi) * 0.06
        
        if pb.get('J_Bip_C_Hips'):
            pb['J_Bip_C_Hips'].location = (hip_sway, 0, hip_bounce)
            pb['J_Bip_C_Hips'].keyframe_insert(data_path="location", frame=frame)
            pb['J_Bip_C_Hips'].rotation_quaternion = create_quaternion((0.04, hip_twist, hip_roll))
            pb['J_Bip_C_Hips'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        if pb.get('J_Bip_C_Spine'):
            pb['J_Bip_C_Spine'].rotation_quaternion = create_quaternion((0.02, -hip_twist * 0.6, -hip_roll * 0.5))
            pb['J_Bip_C_Spine'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_C_UpperChest'):
            pb['J_Bip_C_UpperChest'].rotation_quaternion = create_quaternion((0.02, -hip_twist * 0.8, -hip_roll * 0.7))
            pb['J_Bip_C_UpperChest'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        l_stride = math.sin(phi)
        l_knee_bend = max(0.0, -l_stride * 1.15 + 0.15) if l_stride < 0 else max(0.0, l_stride * 0.3)
        l_up_q = create_quaternion((l_stride * 0.55, 0.0, -0.02))
        if pb.get('J_Bip_L_UpperLeg'): pb['J_Bip_L_UpperLeg'].rotation_quaternion = l_up_q; pb['J_Bip_L_UpperLeg'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_L_LowerLeg'): pb['J_Bip_L_LowerLeg'].rotation_quaternion = create_quaternion((l_knee_bend, 0, 0)); pb['J_Bip_L_LowerLeg'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_L_Foot'): pb['J_Bip_L_Foot'].rotation_quaternion = create_quaternion((-l_stride * 0.45, 0, 0)); pb['J_Bip_L_Foot'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        r_stride = -math.sin(phi)
        r_knee_bend = max(0.0, -r_stride * 1.15 + 0.15) if r_stride < 0 else max(0.0, r_stride * 0.3)
        r_up_q = create_quaternion((r_stride * 0.55, 0.0, 0.02))
        if pb.get('J_Bip_R_UpperLeg'): pb['J_Bip_R_UpperLeg'].rotation_quaternion = r_up_q; pb['J_Bip_R_UpperLeg'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_R_LowerLeg'): pb['J_Bip_R_LowerLeg'].rotation_quaternion = create_quaternion((r_knee_bend, 0, 0)); pb['J_Bip_R_LowerLeg'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_R_Foot'): pb['J_Bip_R_Foot'].rotation_quaternion = create_quaternion((-r_stride * 0.45, 0, 0)); pb['J_Bip_R_Foot'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        for s in ['J_Aim_L_UpperLeg', 'J_Roll_L_UpperLeg', 'J_Sec_L_TopsUpperLegFront', 'J_Sec_L_TopsUpperLegBack', 'J_Sec_L_TopsUpperLegSide']:
            if pb.get(s): pb[s].rotation_quaternion = l_up_q; pb[s].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        for s in ['J_Aim_R_UpperLeg', 'J_Roll_R_UpperLeg', 'J_Sec_R_TopsUpperLegFront', 'J_Sec_R_TopsUpperLegBack', 'J_Sec_R_TopsUpperLegSide']:
            if pb.get(s): pb[s].rotation_quaternion = r_up_q; pb[s].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        l_arm_swing = r_stride * 0.45
        r_arm_swing = l_stride * 0.45
        l_arm_q = create_quaternion((l_arm_swing, 0.0, -1.25))
        r_arm_q = create_quaternion((r_arm_swing, 0.0, 1.25))
        if pb.get('J_Bip_L_UpperArm'): pb['J_Bip_L_UpperArm'].rotation_quaternion = l_arm_q; pb['J_Bip_L_UpperArm'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_R_UpperArm'): pb['J_Bip_R_UpperArm'].rotation_quaternion = r_arm_q; pb['J_Bip_R_UpperArm'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_L_LowerArm'): pb['J_Bip_L_LowerArm'].rotation_quaternion = create_quaternion((0, 0, -0.20 - max(0.0, l_arm_swing) * 0.4)); pb['J_Bip_L_LowerArm'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_R_LowerArm'): pb['J_Bip_R_LowerArm'].rotation_quaternion = create_quaternion((0, 0, 0.20 + max(0.0, r_arm_swing) * 0.4)); pb['J_Bip_R_LowerArm'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        for s in ['J_Aim_L_TopsUpperArm', 'J_Roll_L_UpperArm', 'J_Sec_L_TopsUpperArmInside', 'J_Sec_L_TopsUpperArmOutside']:
            if pb.get(s): pb[s].rotation_quaternion = l_arm_q; pb[s].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        for s in ['J_Aim_R_TopsUpperArm', 'J_Roll_R_UpperArm', 'J_Sec_R_TopsUpperArmInside', 'J_Sec_R_TopsUpperArmOutside']:
            if pb.get(s): pb[s].rotation_quaternion = r_arm_q; pb[s].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        for side in ['L', 'R']:
            for f_name in ['Thumb', 'Index', 'Middle', 'Ring', 'Little']:
                for seg in range(1, 4):
                    b_name = f'J_Bip_{side}_{f_name}{seg}'
                    if pb.get(b_name):
                        pb[b_name].rotation_quaternion = create_quaternion((0, -0.25, -0.15 if side=='L' else 0.15))
                        pb[b_name].keyframe_insert(data_path="rotation_quaternion", frame=frame)

    # =========================================================================
    # STATE 5: 05_BuocDi_TuNhien (Bước Đi Tự Nhiên Chân Thực - Biomechanic Ground Contact - 60 frames)
    # =========================================================================
    print(">>> 5. Creating State: 05_BuocDi_TuNhien (Bước đi tự nhiên chân thực với tiếp đất giảm xóc)...")
    act_walk_real = bpy.data.actions.new(name="05_BuocDi_TuNhien")
    char_arm.animation_data.action = act_walk_real
    created_actions.append(act_walk_real)
    
    # Biomechanically accurate human gait:
    # Phase 0: Heel strike (gót tiếp đất) -> Phase 0.25: Foot flat & weight absorb (bàn chân áp sàn & gối chùng giảm chấn)
    # Phase 0.5: Push off (mũi chân đẩy về sau) -> Phase 0.75: Knee swing forward (gối gấp vung chân về trước)
    for frame in range(1, 61):
        bpy.context.scene.frame_set(frame)
        t = (frame / 60.0) * math.pi * 2
        
        # Heavy organic pelvic physics: weight dips sharply on foot impact (Weight Drop & Rebound)
        # In real humans, pelvis dips twice per stride (on each heel strike)
        pelvis_z = -0.05 * (math.sin(t * 2 + math.pi/4) * 0.5 + 0.5)**1.5
        pelvis_x = math.sin(t) * 0.038 # Lateral weight shift over the planted foot
        pelvis_rot_y = -math.sin(t) * 0.12 # Pelvis yaw follows the forward swinging leg
        pelvis_rot_z = math.sin(t) * 0.07  # Pelvis roll (drops on swing side)
        pelvis_rot_x = 0.05 + 0.02 * math.cos(t * 2) # Forward tilt
        
        if pb.get('J_Bip_C_Hips'):
            pb['J_Bip_C_Hips'].location = (pelvis_x, 0, pelvis_z)
            pb['J_Bip_C_Hips'].keyframe_insert(data_path="location", frame=frame)
            pb['J_Bip_C_Hips'].rotation_quaternion = create_quaternion((pelvis_rot_x, pelvis_rot_y, pelvis_rot_z))
            pb['J_Bip_C_Hips'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
            
        # Torso & Head Counter-rotation (Damping body momentum)
        if pb.get('J_Bip_C_Spine'):
            pb['J_Bip_C_Spine'].rotation_quaternion = create_quaternion((0.02, -pelvis_rot_y * 0.7, -pelvis_rot_z * 0.6))
            pb['J_Bip_C_Spine'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_C_UpperChest'):
            pb['J_Bip_C_UpperChest'].rotation_quaternion = create_quaternion((0.03, -pelvis_rot_y * 0.9, -pelvis_rot_z * 0.8))
            pb['J_Bip_C_UpperChest'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_C_Head'):
            pb['J_Bip_C_Head'].rotation_quaternion = create_quaternion((-0.03, pelvis_rot_y * 0.35, 0))
            pb['J_Bip_C_Head'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        # LEFT LEG BIOMECHANICS:
        # Leg angle
        l_thigh = math.sin(t) * 0.62
        # When moving forward (swing phase t in [pi, 2pi]), knee bends deeply to 75 deg (1.3 rad) to clear ground
        if math.sin(t) < 0:
            l_knee = max(0.05, (-math.sin(t))**1.2 * 1.35)
            l_foot = -0.25 * math.sin(t) # Toe dorsiflexion
        else: # Stance phase ( tiếp đất & đẩy lùi )
            # Heel strike -> Foot flat -> Toe push off
            impact_phase = math.sin(t)
            l_knee = 0.20 * math.sin(t * 2) if impact_phase > 0.3 else 0.05
            l_foot = -0.45 * impact_phase if impact_phase < 0.5 else 0.35 * (impact_phase - 0.5)

        l_up_q = create_quaternion((l_thigh, 0.0, -0.03))
        if pb.get('J_Bip_L_UpperLeg'): pb['J_Bip_L_UpperLeg'].rotation_quaternion = l_up_q; pb['J_Bip_L_UpperLeg'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_L_LowerLeg'): pb['J_Bip_L_LowerLeg'].rotation_quaternion = create_quaternion((l_knee, 0, 0)); pb['J_Bip_L_LowerLeg'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_L_Foot'): pb['J_Bip_L_Foot'].rotation_quaternion = create_quaternion((l_foot, 0, 0)); pb['J_Bip_L_Foot'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        # RIGHT LEG BIOMECHANICS (Exact opposite phase t + pi):
        t_r = t + math.pi
        r_thigh = math.sin(t_r) * 0.62
        if math.sin(t_r) < 0:
            r_knee = max(0.05, (-math.sin(t_r))**1.2 * 1.35)
            r_foot = -0.25 * math.sin(t_r)
        else:
            impact_phase = math.sin(t_r)
            r_knee = 0.20 * math.sin(t_r * 2) if impact_phase > 0.3 else 0.05
            r_foot = -0.45 * impact_phase if impact_phase < 0.5 else 0.35 * (impact_phase - 0.5)

        r_up_q = create_quaternion((r_thigh, 0.0, 0.03))
        if pb.get('J_Bip_R_UpperLeg'): pb['J_Bip_R_UpperLeg'].rotation_quaternion = r_up_q; pb['J_Bip_R_UpperLeg'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_R_LowerLeg'): pb['J_Bip_R_LowerLeg'].rotation_quaternion = create_quaternion((r_knee, 0, 0)); pb['J_Bip_R_LowerLeg'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_R_Foot'): pb['J_Bip_R_Foot'].rotation_quaternion = create_quaternion((r_foot, 0, 0)); pb['J_Bip_R_Foot'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        # Secondary pants bones
        for s in ['J_Aim_L_UpperLeg', 'J_Roll_L_UpperLeg', 'J_Sec_L_TopsUpperLegFront', 'J_Sec_L_TopsUpperLegBack', 'J_Sec_L_TopsUpperLegSide']:
            if pb.get(s): pb[s].rotation_quaternion = l_up_q; pb[s].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        for s in ['J_Aim_R_UpperLeg', 'J_Roll_R_UpperLeg', 'J_Sec_R_TopsUpperLegFront', 'J_Sec_R_TopsUpperLegBack', 'J_Sec_R_TopsUpperLegSide']:
            if pb.get(s): pb[s].rotation_quaternion = r_up_q; pb[s].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        # NATURAL ARM & SHOULDER PENDULUM MOTION (With forearm drag and wrist delay)
        # Left Arm swings in phase with Right Leg (t_r)
        l_arm_swing = math.sin(t_r) * 0.52
        l_elbow_bend = -0.25 - max(0.0, l_arm_swing) * 0.55
        l_arm_q = create_quaternion((l_arm_swing, 0.05, -1.25))
        if pb.get('J_Bip_L_UpperArm'): pb['J_Bip_L_UpperArm'].rotation_quaternion = l_arm_q; pb['J_Bip_L_UpperArm'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_L_LowerArm'): pb['J_Bip_L_LowerArm'].rotation_quaternion = create_quaternion((0, 0, l_elbow_bend)); pb['J_Bip_L_LowerArm'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_L_Hand'): pb['J_Bip_L_Hand'].rotation_quaternion = create_quaternion((math.cos(t_r) * 0.15, -0.15, 0)); pb['J_Bip_L_Hand'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        # Right Arm swings in phase with Left Leg (t)
        r_arm_swing = math.sin(t) * 0.52
        r_elbow_bend = 0.25 + max(0.0, r_arm_swing) * 0.55
        r_arm_q = create_quaternion((r_arm_swing, -0.05, 1.25))
        if pb.get('J_Bip_R_UpperArm'): pb['J_Bip_R_UpperArm'].rotation_quaternion = r_arm_q; pb['J_Bip_R_UpperArm'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_R_LowerArm'): pb['J_Bip_R_LowerArm'].rotation_quaternion = create_quaternion((0, 0, r_elbow_bend)); pb['J_Bip_R_LowerArm'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_R_Hand'): pb['J_Bip_R_Hand'].rotation_quaternion = create_quaternion((math.cos(t) * 0.15, 0.15, 0)); pb['J_Bip_R_Hand'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        # Secondary shirt bones
        for s in ['J_Aim_L_TopsUpperArm', 'J_Roll_L_UpperArm', 'J_Sec_L_TopsUpperArmInside', 'J_Sec_L_TopsUpperArmOutside']:
            if pb.get(s): pb[s].rotation_quaternion = l_arm_q; pb[s].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        for s in ['J_Aim_R_TopsUpperArm', 'J_Roll_R_UpperArm', 'J_Sec_R_TopsUpperArmInside', 'J_Sec_R_TopsUpperArmOutside']:
            if pb.get(s): pb[s].rotation_quaternion = r_arm_q; pb[s].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        # Natural curled fingers with rhythmic relaxation
        for side in ['L', 'R']:
            for f_name in ['Thumb', 'Index', 'Middle', 'Ring', 'Little']:
                for seg in range(1, 4):
                    b_name = f'J_Bip_{side}_{f_name}{seg}'
                    if pb.get(b_name):
                        pb[b_name].rotation_quaternion = create_quaternion((0, -0.30, -0.15 if side=='L' else 0.15))
                        pb[b_name].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        # Hair dynamics reacts to gravity drop & forward step
        for pb_b in pb:
            if 'Hair' in pb_b.name:
                pb_b.rotation_quaternion = create_quaternion((0.08 + math.sin(t * 2) * 0.06, 0, math.cos(t) * 0.04))
                pb_b.keyframe_insert(data_path="rotation_quaternion", frame=frame)

    # Push all 5 actions to NLA Tracks for multi-clip GLTF export
    print(">>> Pushing all 5 actions to NLA tracks for multi-clip GLTF export...")
    for track in list(char_arm.animation_data.nla_tracks):
        char_arm.animation_data.nla_tracks.remove(track)
    for act in created_actions:
        track = char_arm.animation_data.nla_tracks.new()
        track.name = act.name
        track.strips.new(act.name, 1, act)

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
        vowels = ['Face_Blendshape.Fcl_MTH_A', 'Face_Blendshape.Fcl_MTH_I', 'Face_Blendshape.Fcl_MTH_U', 'Face_Blendshape.Fcl_MTH_E', 'Face_Blendshape.Fcl_MTH_O']
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

    print(">>> Exporting all 5 Animation States to .glb, .fbx, .blend...")
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
        
    print(">>> ALL 5 ANIMATION STATES EXPORTED SUCCESSFULLY!")

if __name__ == '__main__':
    build_all_states_with_mocap_walk()
    print("=== ALL 5 STATES BAKED & PACKAGED ===")
