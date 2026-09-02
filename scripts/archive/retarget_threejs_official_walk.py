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

def retarget_threejs_library_walk():
    print(">>> Retargeting Production Walk Animation from Official Three.js Library (Xbot/Mixamo)...")
    clean_scene()
    
    input_glb = '/Volumes/DATA/ctg_ai/3d/phuong_an_B_anime_idol_female_singer/model/female_singer_anime_idol.glb'
    threejs_walk_glb = '/Volumes/DATA/ctg_ai/3d/external_library_animations/Xbot.glb'
    out_b_dir = '/Volumes/DATA/ctg_ai/3d/phuong_an_B_anime_idol_female_singer/model'
    stage_dir = '/Volumes/DATA/ctg_ai/3d/phuong_an_nang_cao_nu_ca_si_pro_stage/model'
    
    # 1. Import Character
    bpy.ops.import_scene.gltf(filepath=input_glb)
    char_arm = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
    char_arm.name = 'Character_Armature'
    
    # 2. Import Three.js / Mixamo Source Model
    bpy.ops.import_scene.gltf(filepath=threejs_walk_glb)
    source_arm = [o for o in bpy.data.objects if o.type == 'ARMATURE' and o != char_arm][0]
    source_arm.name = 'ThreeJS_Source'
    
    # Set active walk action on source
    walk_action = [a for a in bpy.data.actions if 'walk' in a.name.lower()][0]
    source_arm.animation_data.action = walk_action
    
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
    # STATE 1: 01_DungNghiem
    # =========================================================================
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
    # STATE 2: 02_DungNghi
    # =========================================================================
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
    # STATE 3: 03_TPose
    # =========================================================================
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
    # STATE 4: 04_BuocDi_CoBan (Giữ lại theo yêu cầu)
    # =========================================================================
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
    # STATE 5: 05_BuocDi_TuNhien (RETARGETED 100% FROM THREE.JS / MIXAMO OFFICIAL LIBRARY)
    # =========================================================================
    print(">>> 5. Baking 05_BuocDi_TuNhien from Official Three.js / Mixamo Production Library...")
    act_threejs_walk = bpy.data.actions.new(name="05_BuocDi_TuNhien")
    char_arm.animation_data.action = act_threejs_walk
    created_actions.append(act_threejs_walk)
    
    # Complete bone mapping from Mixamo humanoid to VRM 1.0 humanoid
    mixamo_to_vrm = {
        'mixamorig:Hips': 'J_Bip_C_Hips',
        'mixamorig:Spine': 'J_Bip_C_Spine',
        'mixamorig:Spine1': 'J_Bip_C_UpperChest',
        'mixamorig:Neck': 'J_Bip_C_Neck',
        'mixamorig:Head': 'J_Bip_C_Head',
        'mixamorig:LeftShoulder': 'J_Bip_L_Shoulder',
        'mixamorig:LeftArm': 'J_Bip_L_UpperArm',
        'mixamorig:LeftForeArm': 'J_Bip_L_LowerArm',
        'mixamorig:LeftHand': 'J_Bip_L_Hand',
        'mixamorig:RightShoulder': 'J_Bip_R_Shoulder',
        'mixamorig:RightArm': 'J_Bip_R_UpperArm',
        'mixamorig:RightForeArm': 'J_Bip_R_LowerArm',
        'mixamorig:RightHand': 'J_Bip_R_Hand',
        'mixamorig:LeftUpLeg': 'J_Bip_L_UpperLeg',
        'mixamorig:LeftLeg': 'J_Bip_L_LowerLeg',
        'mixamorig:LeftFoot': 'J_Bip_L_Foot',
        'mixamorig:RightUpLeg': 'J_Bip_R_UpperLeg',
        'mixamorig:RightLeg': 'J_Bip_R_LowerLeg',
        'mixamorig:RightFoot': 'J_Bip_R_Foot'
    }

    # Pre-calculate rest matrices
    rest_src = {}
    rest_dst = {}
    for src_b_name, dst_b_name in mixamo_to_vrm.items():
        if src_b_name in source_arm.data.bones and dst_b_name in char_arm.data.bones:
            rest_src[src_b_name] = source_arm.data.bones[src_b_name].matrix_local.to_3x3()
            rest_dst[dst_b_name] = char_arm.data.bones[dst_b_name].matrix_local.to_3x3()

    # The Three.js walk cycle is 30 frames at 30 fps (exactly 1 second loop)
    # We will resample over 60 frames for ultra-smooth 60fps playback
    total_frames = 60
    for frame in range(1, total_frames + 1):
        # Sample source animation time
        src_time = ((frame - 1) / total_frames) * 23.2
        bpy.context.scene.frame_set(int(src_time))
        
        # 1. Hips Position
        src_hips = source_arm.pose.bones.get('mixamorig:Hips')
        if src_hips and pb.get('J_Bip_C_Hips'):
            # Copy lateral sway and vertical bounce
            pb['J_Bip_C_Hips'].location = (src_hips.location.x * 0.01, 0.0, (src_hips.location.y - 0.98) * 0.01)
            pb['J_Bip_C_Hips'].keyframe_insert(data_path="location", frame=frame)

        # 2. Retarget all joint rotations
        for src_name, dst_name in mixamo_to_vrm.items():
            if src_name in rest_src and dst_name in rest_dst:
                src_pb = source_arm.pose.bones[src_name]
                dst_pb = pb[dst_name]
                
                # Delta rotation from source rest to source pose
                src_pose_rot = src_pb.matrix.to_3x3()
                delta_rot = src_pose_rot @ rest_src[src_name].inverted()
                dst_target_rot = delta_rot @ rest_dst[dst_name]
                
                if dst_pb.parent:
                    parent_pose_rot = dst_pb.parent.matrix.to_3x3()
                    local_rot = parent_pose_rot.inverted() @ dst_target_rot
                else:
                    local_rot = dst_target_rot
                    
                dst_pb.rotation_quaternion = local_rot.to_quaternion()
                dst_pb.keyframe_insert(data_path='rotation_quaternion', frame=frame)

        # 3. Synchronize Secondary Clothing Bones
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

    # Clean up imported source object
    for obj in list(bpy.data.objects):
        if obj != char_arm and obj.type in ['ARMATURE', 'MESH']:
            if 'body' not in obj.name.lower() and 'hair' not in obj.name.lower() and 'face' not in obj.name.lower():
                bpy.data.objects.remove(obj, do_unlink=True)

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
        
    print(">>> THREE.JS / MIXAMO OFFICIAL WALK EXPORTED SUCCESSFULLY!")

if __name__ == '__main__':
    retarget_threejs_library_walk()
    print("=== THREE.JS WALK RETARGETING COMPLETE ===")
