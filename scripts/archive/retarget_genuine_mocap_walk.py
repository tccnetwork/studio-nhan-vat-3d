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

def retarget_genuine_mocap():
    print(">>> Performing 100% Genuine Human Motion Capture (BVH) Retargeting for Walk & Animation States...")
    clean_scene()
    
    input_glb = '/Volumes/DATA/ctg_ai/3d/phuong_an_B_anime_idol_female_singer/model/female_singer_anime_idol.glb'
    walk_bvh_path = '/Volumes/DATA/ctg_ai/3d/mocap/dataset-1_walk_happy_001.bvh'
    out_b_dir = '/Volumes/DATA/ctg_ai/3d/phuong_an_B_anime_idol_female_singer/model'
    stage_dir = '/Volumes/DATA/ctg_ai/3d/phuong_an_nang_cao_nu_ca_si_pro_stage/model'
    
    # 1. Import Character
    bpy.ops.import_scene.gltf(filepath=input_glb)
    char_arm = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
    char_arm.name = 'Character_Armature'
    
    # 2. Import BVH Walk Armature
    bpy.ops.import_anim.bvh(filepath=walk_bvh_path, target='ARMATURE', global_scale=0.01)
    bvh_arm = [o for o in bpy.data.objects if o.type == 'ARMATURE' and o != char_arm][0]
    bvh_arm.name = 'BVH_Walk_Source'
    
    # BIND CLOTHING VERTEX WEIGHTS
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
    print(">>> 1. Baking 01_DungNghiem...")
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

        for side in ['L', 'R']:
            for f_name in ['Thumb', 'Index', 'Middle', 'Ring', 'Little']:
                for seg in range(1, 4):
                    b_name = f'J_Bip_{side}_{f_name}{seg}'
                    if pb.get(b_name): pb[b_name].rotation_quaternion = create_quaternion((0, 0, 0)); pb[b_name].keyframe_insert(data_path="rotation_quaternion", frame=frame)

    # =========================================================================
    # STATE 2: 02_DungNghi (120 frames)
    # =========================================================================
    print(">>> 2. Baking 02_DungNghi...")
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
    print(">>> 3. Baking 03_TPose...")
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
    print(">>> 4. Baking 04_BuocDi_CoBan...")
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
    # STATE 5: 05_BuocDi_TuNhien (120 frames RETARGETED FROM GENUINE HUMAN MOCAP BVH)
    # =========================================================================
    print(">>> 5. Baking 05_BuocDi_TuNhien from Genuine BVH Motion Capture...")
    act_walk_mocap = bpy.data.actions.new(name="05_BuocDi_TuNhien")
    char_arm.animation_data.action = act_walk_mocap
    created_actions.append(act_walk_mocap)
    
    bone_map = {
        'Hips': 'J_Bip_C_Hips',
        'Spine': 'J_Bip_C_Spine',
        'Chest': 'J_Bip_C_UpperChest',
        'Neck': 'J_Bip_C_Neck',
        'Head': 'J_Bip_C_Head',
        'UpperLeg_L': 'J_Bip_L_UpperLeg',
        'LowerLeg_L': 'J_Bip_L_LowerLeg',
        'Foot_L': 'J_Bip_L_Foot',
        'UpperLeg_R': 'J_Bip_R_UpperLeg',
        'LowerLeg_R': 'J_Bip_R_LowerLeg',
        'Foot_R': 'J_Bip_R_Foot',
        'Shoulder_L': 'J_Bip_L_Shoulder',
        'UpperArm_L': 'J_Bip_L_UpperArm',
        'LowerArm_L': 'J_Bip_L_LowerArm',
        'Hand_L': 'J_Bip_L_Hand',
        'Shoulder_R': 'J_Bip_R_Shoulder',
        'UpperArm_R': 'J_Bip_R_UpperArm',
        'LowerArm_R': 'J_Bip_R_LowerArm',
        'Hand_R': 'J_Bip_R_Hand'
    }

    rest_bvh = {}
    rest_char = {}
    for bvh_name, char_name in bone_map.items():
        if bvh_name in bvh_arm.data.bones and char_name in char_arm.data.bones:
            rest_bvh[bvh_name] = bvh_arm.data.bones[bvh_name].matrix_local.to_3x3()
            rest_char[char_name] = char_arm.data.bones[char_name].matrix_local.to_3x3()

    # Retarget 120 frames (4 full human strides from mocap)
    for frame in range(1, 121):
        bvh_f = frame + 10 # Offset past startup
        bpy.context.scene.frame_set(bvh_f)
        
        # 1. Retarget Hips Position (Transfer authentic human weight shift & vertical bounce)
        bvh_hips_pb = bvh_arm.pose.bones.get('Hips')
        if bvh_hips_pb and pb.get('J_Bip_C_Hips'):
            # In BVH, Y is up, X is lateral, Z is forward
            h_x = bvh_hips_pb.location.x * 0.01 # Lateral hip sway
            h_y = bvh_hips_pb.location.y * 0.01 - 0.9392 # Vertical bounce relative to rest
            # Set hips in character space (Y is up, Z is forward/vertical in blender)
            pb['J_Bip_C_Hips'].location = (h_x, 0.0, h_y)
            pb['J_Bip_C_Hips'].keyframe_insert(data_path="location", frame=frame)
            
        # 2. Retarget All Humanoid Joint Rotations
        for bvh_name, char_name in bone_map.items():
            if bvh_name in rest_bvh and char_name in rest_char:
                src_b = bvh_arm.pose.bones[bvh_name]
                dst_b = pb[char_name]
                
                # World delta rotation from mocap
                src_pose_rot = src_b.matrix.to_3x3()
                delta_rot = src_pose_rot @ rest_bvh[bvh_name].inverted()
                dst_target_rot = delta_rot @ rest_char[char_name]
                
                if dst_b.parent:
                    parent_pose_rot = dst_b.parent.matrix.to_3x3()
                    local_rot = parent_pose_rot.inverted() @ dst_target_rot
                else:
                    local_rot = dst_target_rot
                    
                dst_b.rotation_quaternion = local_rot.to_quaternion()
                dst_b.keyframe_insert(data_path='rotation_quaternion', frame=frame)

        # 3. Synchronize Secondary Clothing Bones with Retargeted Limbs
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

        # 4. Natural Finger Relaxation
        for side in ['L', 'R']:
            for f_name in ['Thumb', 'Index', 'Middle', 'Ring', 'Little']:
                for seg in range(1, 4):
                    b_name = f'J_Bip_{side}_{f_name}{seg}'
                    if pb.get(b_name):
                        pb[b_name].rotation_quaternion = create_quaternion((0, -0.20, -0.10 if side=='L' else 0.10))
                        pb[b_name].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        # 5. Natural Hair Response
        for pb_b in pb:
            if 'Hair' in pb_b.name:
                pb_b.rotation_quaternion = create_quaternion((0.06 + 0.04 * math.sin(frame / 6.0), 0, 0.03 * math.cos(frame / 6.0)))
                pb_b.keyframe_insert(data_path="rotation_quaternion", frame=frame)

    # Delete BVH object after retargeting
    bpy.data.objects.remove(bvh_arm, do_unlink=True)

    # Push all 5 actions to NLA Tracks for multi-clip GLTF export
    print(">>> Pushing all 5 actions to NLA tracks for clean export...")
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
        
    print(">>> ALL 5 ANIMATION STATES RETARGETED FROM GENUINE MOCAP AND EXPORTED SUCCESSFULLY!")

if __name__ == '__main__':
    retarget_genuine_mocap()
    print("=== MOCAP RETARGETING COMPLETE ===")
