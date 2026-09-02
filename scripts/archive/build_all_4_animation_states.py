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

def build_all_4_states():
    print(">>> Building All 4 Animation States for Female 3D Character...")
    clean_scene()
    
    input_glb = '/Volumes/DATA/ctg_ai/3d/phuong_an_B_anime_idol_female_singer/model/female_singer_anime_idol.glb'
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

    # Get all pose bone references
    pb = char_arm.pose.bones
    
    # Set rotation mode to QUATERNION for all bones
    for b in pb:
        b.rotation_mode = 'QUATERNION'

    created_actions = []

    # =========================================================================
    # STATE 1: 01_DungNghiem (Đứng Nghiêm / Attention Stand - 60 frames)
    # =========================================================================
    print(">>> Creating State 1: 01_DungNghiem (Đứng nghiêm)...")
    act_nghiem = bpy.data.actions.new(name="01_DungNghiem")
    char_arm.animation_data.action = act_nghiem
    created_actions.append(act_nghiem)
    
    for frame in range(1, 61):
        bpy.context.scene.frame_set(frame)
        t = (frame / 60.0) * math.pi * 2 # Breathing cycle (2 seconds)
        breath = math.sin(t) * 0.025
        
        # Hips: neutral upright
        if pb.get('J_Bip_C_Hips'):
            pb['J_Bip_C_Hips'].location = (0, 0, 0)
            pb['J_Bip_C_Hips'].keyframe_insert(data_path="location", frame=frame)
            pb['J_Bip_C_Hips'].rotation_quaternion = create_quaternion((0, 0, 0))
            pb['J_Bip_C_Hips'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
            
        # Spine & Chest (upright, tall with breathing)
        if pb.get('J_Bip_C_Spine'):
            pb['J_Bip_C_Spine'].rotation_quaternion = create_quaternion((0.01 + breath * 0.3, 0, 0))
            pb['J_Bip_C_Spine'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_C_UpperChest'):
            pb['J_Bip_C_UpperChest'].rotation_quaternion = create_quaternion((0.02 + breath * 0.7, 0, 0))
            pb['J_Bip_C_UpperChest'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_C_Neck'):
            pb['J_Bip_C_Neck'].rotation_quaternion = create_quaternion((0, 0, 0))
            pb['J_Bip_C_Neck'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_C_Head'):
            pb['J_Bip_C_Head'].rotation_quaternion = create_quaternion((-0.01, 0, 0))
            pb['J_Bip_C_Head'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        # Shoulders slightly pulled back
        if pb.get('J_Bip_L_Shoulder'):
            pb['J_Bip_L_Shoulder'].rotation_quaternion = create_quaternion((0, 0, -0.04))
            pb['J_Bip_L_Shoulder'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_R_Shoulder'):
            pb['J_Bip_R_Shoulder'].rotation_quaternion = create_quaternion((0, 0, 0.04))
            pb['J_Bip_R_Shoulder'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        # Arms: straight down along thighs
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
            
        # Hands: parallel along thighs
        if pb.get('J_Bip_L_Hand'):
            pb['J_Bip_L_Hand'].rotation_quaternion = create_quaternion((0, -0.15, 0))
            pb['J_Bip_L_Hand'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_R_Hand'):
            pb['J_Bip_R_Hand'].rotation_quaternion = create_quaternion((0, 0.15, 0))
            pb['J_Bip_R_Hand'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        # Secondary shirt bones
        for s in ['J_Aim_L_TopsUpperArm', 'J_Roll_L_UpperArm', 'J_Sec_L_TopsUpperArmInside', 'J_Sec_L_TopsUpperArmOutside']:
            if pb.get(s):
                pb[s].rotation_quaternion = l_arm_q
                pb[s].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        for s in ['J_Aim_R_TopsUpperArm', 'J_Roll_R_UpperArm', 'J_Sec_R_TopsUpperArmInside', 'J_Sec_R_TopsUpperArmOutside']:
            if pb.get(s):
                pb[s].rotation_quaternion = r_arm_q
                pb[s].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        # Legs: straight parallel, standing firmly
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
        if pb.get('J_Bip_L_Foot'):
            pb['J_Bip_L_Foot'].rotation_quaternion = create_quaternion((0, 0, 0))
            pb['J_Bip_L_Foot'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_R_Foot'):
            pb['J_Bip_R_Foot'].rotation_quaternion = create_quaternion((0, 0, 0))
            pb['J_Bip_R_Foot'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        # Secondary pants bones
        for s in ['J_Aim_L_UpperLeg', 'J_Roll_L_UpperLeg', 'J_Sec_L_TopsUpperLegFront', 'J_Sec_L_TopsUpperLegBack', 'J_Sec_L_TopsUpperLegSide']:
            if pb.get(s):
                pb[s].rotation_quaternion = l_leg_q
                pb[s].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        for s in ['J_Aim_R_UpperLeg', 'J_Roll_R_UpperLeg', 'J_Sec_R_TopsUpperLegFront', 'J_Sec_R_TopsUpperLegBack', 'J_Sec_R_TopsUpperLegSide']:
            if pb.get(s):
                pb[s].rotation_quaternion = r_leg_q
                pb[s].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        # Fingers: straight & neat
        for side in ['L', 'R']:
            for f_name in ['Thumb', 'Index', 'Middle', 'Ring', 'Little']:
                for seg in range(1, 4):
                    b_name = f'J_Bip_{side}_{f_name}{seg}'
                    if pb.get(b_name):
                        pb[b_name].rotation_quaternion = create_quaternion((0, 0, 0))
                        pb[b_name].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        # Hair: gentle rest
        for b in pb:
            if 'Hair' in b.name:
                b.rotation_quaternion = create_quaternion((0.02, 0, 0))
                b.keyframe_insert(data_path="rotation_quaternion", frame=frame)

    # =========================================================================
    # STATE 2: 02_DungNghi (Đứng Trạng Thái Nghỉ / Relaxed Stand - 120 frames)
    # =========================================================================
    print(">>> Creating State 2: 02_DungNghi (Đứng trạng thái nghỉ)...")
    act_nghi = bpy.data.actions.new(name="02_DungNghi")
    char_arm.animation_data.action = act_nghi
    created_actions.append(act_nghi)
    
    for frame in range(1, 121):
        bpy.context.scene.frame_set(frame)
        t = (frame / 120.0) * math.pi * 2 # 4s breathing & subtle idle cycle
        sway = math.sin(t) * 0.015
        breath = math.sin(t * 2) * 0.03
        
        # Hips: weight shifted to right leg (contrapposto)
        if pb.get('J_Bip_C_Hips'):
            pb['J_Bip_C_Hips'].location = (0.035 + sway * 0.5, 0, -0.015)
            pb['J_Bip_C_Hips'].keyframe_insert(data_path="location", frame=frame)
            pb['J_Bip_C_Hips'].rotation_quaternion = create_quaternion((0.02, 0.04, -0.06 + sway))
            pb['J_Bip_C_Hips'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
            
        # Spine & Chest counter-tilt for natural balance
        if pb.get('J_Bip_C_Spine'):
            pb['J_Bip_C_Spine'].rotation_quaternion = create_quaternion((0.02 + breath * 0.3, -0.02, 0.04))
            pb['J_Bip_C_Spine'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_C_UpperChest'):
            pb['J_Bip_C_UpperChest'].rotation_quaternion = create_quaternion((0.03 + breath * 0.7, -0.02, 0.03))
            pb['J_Bip_C_UpperChest'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_C_Neck'):
            pb['J_Bip_C_Neck'].rotation_quaternion = create_quaternion((0, 0.02, -0.01))
            pb['J_Bip_C_Neck'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_C_Head'):
            pb['J_Bip_C_Head'].rotation_quaternion = create_quaternion((0.02, 0.04 + sway, 0.03))
            pb['J_Bip_C_Head'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        # Right Leg: Support weight (trụ thẳng)
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

        # Left Leg: Relaxed (gối hơi chùng về phía trước)
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

        # Secondary pants bones
        for s in ['J_Aim_L_UpperLeg', 'J_Roll_L_UpperLeg', 'J_Sec_L_TopsUpperLegFront', 'J_Sec_L_TopsUpperLegBack', 'J_Sec_L_TopsUpperLegSide']:
            if pb.get(s):
                pb[s].rotation_quaternion = l_up_q
                pb[s].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        for s in ['J_Aim_R_UpperLeg', 'J_Roll_R_UpperLeg', 'J_Sec_R_TopsUpperLegFront', 'J_Sec_R_TopsUpperLegBack', 'J_Sec_R_TopsUpperLegSide']:
            if pb.get(s):
                pb[s].rotation_quaternion = r_up_q
                pb[s].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        # Arms: Loosely hanging with gentle natural curve
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
        if pb.get('J_Bip_L_Hand'):
            pb['J_Bip_L_Hand'].rotation_quaternion = create_quaternion((0, -0.15, -0.1))
            pb['J_Bip_L_Hand'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_R_Hand'):
            pb['J_Bip_R_Hand'].rotation_quaternion = create_quaternion((0, 0.15, 0.1))
            pb['J_Bip_R_Hand'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        # Secondary shirt bones
        for s in ['J_Aim_L_TopsUpperArm', 'J_Roll_L_UpperArm', 'J_Sec_L_TopsUpperArmInside', 'J_Sec_L_TopsUpperArmOutside']:
            if pb.get(s):
                pb[s].rotation_quaternion = l_arm_q
                pb[s].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        for s in ['J_Aim_R_TopsUpperArm', 'J_Roll_R_UpperArm', 'J_Sec_R_TopsUpperArmInside', 'J_Sec_R_TopsUpperArmOutside']:
            if pb.get(s):
                pb[s].rotation_quaternion = r_arm_q
                pb[s].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        # Fingers: relaxed gentle curve
        for side in ['L', 'R']:
            for f_name in ['Thumb', 'Index', 'Middle', 'Ring', 'Little']:
                for seg in range(1, 4):
                    b_name = f'J_Bip_{side}_{f_name}{seg}'
                    if pb.get(b_name):
                        pb[b_name].rotation_quaternion = create_quaternion((0, -0.15, -0.10 if side=='L' else 0.10))
                        pb[b_name].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        # Hair: soft sway
        for b in pb:
            if 'Hair' in b.name:
                b.rotation_quaternion = create_quaternion((0.04 + sway, 0, sway * 0.5))
                b.keyframe_insert(data_path="rotation_quaternion", frame=frame)

    # =========================================================================
    # STATE 3: 03_TPose (Đứng Dạng T-Pose - 30 frames)
    # =========================================================================
    print(">>> Creating State 3: 03_TPose (Đứng dạng T-Pose)...")
    act_tpose = bpy.data.actions.new(name="03_TPose")
    char_arm.animation_data.action = act_tpose
    created_actions.append(act_tpose)
    
    for frame in range(1, 31):
        bpy.context.scene.frame_set(frame)
        
        # Hips: neutral origin
        if pb.get('J_Bip_C_Hips'):
            pb['J_Bip_C_Hips'].location = (0, 0, 0)
            pb['J_Bip_C_Hips'].keyframe_insert(data_path="location", frame=frame)
            pb['J_Bip_C_Hips'].rotation_quaternion = create_quaternion((0, 0, 0))
            pb['J_Bip_C_Hips'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
            
        for b_name in ['J_Bip_C_Spine', 'J_Bip_C_UpperChest', 'J_Bip_C_Neck', 'J_Bip_C_Head',
                       'J_Bip_L_Shoulder', 'J_Bip_R_Shoulder',
                       'J_Bip_L_UpperArm', 'J_Bip_L_LowerArm', 'J_Bip_L_Hand',
                       'J_Bip_R_UpperArm', 'J_Bip_R_LowerArm', 'J_Bip_R_Hand',
                       'J_Bip_L_UpperLeg', 'J_Bip_L_LowerLeg', 'J_Bip_L_Foot',
                       'J_Bip_R_UpperLeg', 'J_Bip_R_LowerLeg', 'J_Bip_R_Foot']:
            if pb.get(b_name):
                pb[b_name].rotation_quaternion = create_quaternion((0, 0, 0))
                pb[b_name].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        for side in ['L', 'R']:
            for s in [f'J_Aim_{side}_TopsUpperArm', f'J_Roll_{side}_UpperArm', f'J_Sec_{side}_TopsUpperArmInside', f'J_Sec_{side}_TopsUpperArmOutside',
                      f'J_Aim_{side}_UpperLeg', f'J_Roll_{side}_UpperLeg', f'J_Sec_{side}_TopsUpperLegFront', f'J_Sec_{side}_TopsUpperLegBack', f'J_Sec_{side}_TopsUpperLegSide']:
                if pb.get(s):
                    pb[s].rotation_quaternion = create_quaternion((0, 0, 0))
                    pb[s].keyframe_insert(data_path="rotation_quaternion", frame=frame)
            for f_name in ['Thumb', 'Index', 'Middle', 'Ring', 'Little']:
                for seg in range(1, 4):
                    b_name = f'J_Bip_{side}_{f_name}{seg}'
                    if pb.get(b_name):
                        pb[b_name].rotation_quaternion = create_quaternion((0, 0, 0))
                        pb[b_name].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        for b in pb:
            if 'Hair' in b.name:
                b.rotation_quaternion = create_quaternion((0, 0, 0))
                b.keyframe_insert(data_path="rotation_quaternion", frame=frame)

    # =========================================================================
    # STATE 4: 04_BuocDi (Bước Đi / Natural Walk Cycle - 60 frames)
    # =========================================================================
    print(">>> Creating State 4: 04_BuocDi (Bước đi)...")
    act_walk = bpy.data.actions.new(name="04_BuocDi")
    char_arm.animation_data.action = act_walk
    created_actions.append(act_walk)
    
    for frame in range(1, 61):
        bpy.context.scene.frame_set(frame)
        phi = (frame / 60.0) * math.pi * 2 # 1 full walk stride cycle
        
        # Hips: vertical bounce on steps + lateral sway over supporting foot + hip twist
        hip_bounce = -abs(math.sin(phi * 2)) * 0.045
        hip_sway = math.sin(phi) * 0.04
        hip_twist = -math.sin(phi) * 0.10
        hip_roll = math.sin(phi) * 0.06
        
        if pb.get('J_Bip_C_Hips'):
            pb['J_Bip_C_Hips'].location = (hip_sway, 0, hip_bounce)
            pb['J_Bip_C_Hips'].keyframe_insert(data_path="location", frame=frame)
            pb['J_Bip_C_Hips'].rotation_quaternion = create_quaternion((0.04, hip_twist, hip_roll))
            pb['J_Bip_C_Hips'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        # Spine & Chest: counter-twist to hips for natural gait
        if pb.get('J_Bip_C_Spine'):
            pb['J_Bip_C_Spine'].rotation_quaternion = create_quaternion((0.02, -hip_twist * 0.6, -hip_roll * 0.5))
            pb['J_Bip_C_Spine'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_C_UpperChest'):
            pb['J_Bip_C_UpperChest'].rotation_quaternion = create_quaternion((0.02, -hip_twist * 0.8, -hip_roll * 0.7))
            pb['J_Bip_C_UpperChest'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_C_Head'):
            pb['J_Bip_C_Head'].rotation_quaternion = create_quaternion((-0.02, hip_twist * 0.4, 0))
            pb['J_Bip_C_Head'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        # LEGS (Walking Biomechanics):
        # Left Leg:
        l_stride = math.sin(phi)
        l_knee_bend = max(0.0, -l_stride * 1.15 + 0.15) if l_stride < 0 else max(0.0, l_stride * 0.3)
        l_foot_rot = -l_stride * 0.45
        l_up_q = create_quaternion((l_stride * 0.55, 0.0, -0.02))
        
        if pb.get('J_Bip_L_UpperLeg'):
            pb['J_Bip_L_UpperLeg'].rotation_quaternion = l_up_q
            pb['J_Bip_L_UpperLeg'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_L_LowerLeg'):
            pb['J_Bip_L_LowerLeg'].rotation_quaternion = create_quaternion((l_knee_bend, 0, 0))
            pb['J_Bip_L_LowerLeg'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_L_Foot'):
            pb['J_Bip_L_Foot'].rotation_quaternion = create_quaternion((l_foot_rot, 0, 0))
            pb['J_Bip_L_Foot'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        # Right Leg (Anti-phase to Left Leg):
        r_stride = -math.sin(phi)
        r_knee_bend = max(0.0, -r_stride * 1.15 + 0.15) if r_stride < 0 else max(0.0, r_stride * 0.3)
        r_foot_rot = -r_stride * 0.45
        r_up_q = create_quaternion((r_stride * 0.55, 0.0, 0.02))
        
        if pb.get('J_Bip_R_UpperLeg'):
            pb['J_Bip_R_UpperLeg'].rotation_quaternion = r_up_q
            pb['J_Bip_R_UpperLeg'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_R_LowerLeg'):
            pb['J_Bip_R_LowerLeg'].rotation_quaternion = create_quaternion((r_knee_bend, 0, 0))
            pb['J_Bip_R_LowerLeg'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_R_Foot'):
            pb['J_Bip_R_Foot'].rotation_quaternion = create_quaternion((r_foot_rot, 0, 0))
            pb['J_Bip_R_Foot'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        # Secondary pants bones
        for s in ['J_Aim_L_UpperLeg', 'J_Roll_L_UpperLeg', 'J_Sec_L_TopsUpperLegFront', 'J_Sec_L_TopsUpperLegBack', 'J_Sec_L_TopsUpperLegSide']:
            if pb.get(s):
                pb[s].rotation_quaternion = l_up_q
                pb[s].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        for s in ['J_Aim_R_UpperLeg', 'J_Roll_R_UpperLeg', 'J_Sec_R_TopsUpperLegFront', 'J_Sec_R_TopsUpperLegBack', 'J_Sec_R_TopsUpperLegSide']:
            if pb.get(s):
                pb[s].rotation_quaternion = r_up_q
                pb[s].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        # ARMS (Opposite swing to legs):
        # Left arm swings forward when Right leg steps forward
        l_arm_swing = r_stride * 0.45
        r_arm_swing = l_stride * 0.45
        l_arm_q = create_quaternion((l_arm_swing, 0.0, -1.25))
        r_arm_q = create_quaternion((r_arm_swing, 0.0, 1.25))
        
        if pb.get('J_Bip_L_UpperArm'):
            pb['J_Bip_L_UpperArm'].rotation_quaternion = l_arm_q
            pb['J_Bip_L_UpperArm'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_R_UpperArm'):
            pb['J_Bip_R_UpperArm'].rotation_quaternion = r_arm_q
            pb['J_Bip_R_UpperArm'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_L_LowerArm'):
            pb['J_Bip_L_LowerArm'].rotation_quaternion = create_quaternion((0, 0, -0.20 - max(0.0, l_arm_swing) * 0.4))
            pb['J_Bip_L_LowerArm'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_R_LowerArm'):
            pb['J_Bip_R_LowerArm'].rotation_quaternion = create_quaternion((0, 0, 0.20 + max(0.0, r_arm_swing) * 0.4))
            pb['J_Bip_R_LowerArm'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        # Secondary shirt bones
        for s in ['J_Aim_L_TopsUpperArm', 'J_Roll_L_UpperArm', 'J_Sec_L_TopsUpperArmInside', 'J_Sec_L_TopsUpperArmOutside']:
            if pb.get(s):
                pb[s].rotation_quaternion = l_arm_q
                pb[s].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        for s in ['J_Aim_R_TopsUpperArm', 'J_Roll_R_UpperArm', 'J_Sec_R_TopsUpperArmInside', 'J_Sec_R_TopsUpperArmOutside']:
            if pb.get(s):
                pb[s].rotation_quaternion = r_arm_q
                pb[s].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        # Fingers: natural relaxed walk grip
        for side in ['L', 'R']:
            for f_name in ['Thumb', 'Index', 'Middle', 'Ring', 'Little']:
                for seg in range(1, 4):
                    b_name = f'J_Bip_{side}_{f_name}{seg}'
                    if pb.get(b_name):
                        pb[b_name].rotation_quaternion = create_quaternion((0, -0.25, -0.15 if side=='L' else 0.15))
                        pb[b_name].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        # Hair: dynamic spring bobbing with step momentum
        for pb_b in pb:
            if 'Hair' in pb_b.name:
                pb_b.rotation_quaternion = create_quaternion((0.06 + math.sin(phi * 2) * 0.05, 0, math.cos(phi) * 0.03))
                pb_b.keyframe_insert(data_path="rotation_quaternion", frame=frame)

    # Push all created actions to NLA Tracks so GLTF exporter exports all 4 clips
    print(">>> Pushing all actions to NLA tracks for multi-clip GLTF export...")
    for track in list(char_arm.animation_data.nla_tracks):
        char_arm.animation_data.nla_tracks.remove(track)
    for act in created_actions:
        track = char_arm.animation_data.nla_tracks.new()
        track.name = act.name
        track.strips.new(act.name, 1, act)

    bpy.ops.object.mode_set(mode='OBJECT')

    # Facial Blendshapes for live singing and expressions
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

    # Export for Model B and Stage Pro
    print(">>> Exporting all 4 Animation States to .glb, .fbx, .blend...")
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
        
    print(">>> ALL 4 ANIMATION STATES EXPORTED SUCCESSFULLY!")

if __name__ == '__main__':
    build_all_4_states()
    print("=== ALL 4 STATES BAKED & PACKAGED ===")
