import bpy
import math
import mathutils
import bmesh

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

# Natural gravity plumb-line drape mapping (falls vertically straight down along body)
BACK_HAIR_DRAPE = {1: -0.005, 2: -0.005, 3: 0.0, 4: 0.0, 5: 0.0, 6: 0.0}
FRONT_SIDE_DRAPE = {1: 0.015, 2: 0.010, 3: 0.0, 4: 0.0}

def apply_soft_hair_drape(pb, frame, t, sway_amp=0.018, bounce_amp=0.022):
    """
    Applies organic gravity hair drape that falls straight down vertically:
    - Side strands: Hang straight down naturally beside the neck/collarbone.
    - Back hair: Hugs the upper back softly with zero backward flare.
    - Includes dynamic wave propagation phase lag for lifelike silky flow.
    """
    for b_name, pb_b in pb.items():
        if 'hair' in b_name.lower():
            # Back Hair Chains (05 to 10)
            if any(f'_{idx:02d}' in b_name for idx in range(5, 11)):
                seg = 1
                for s in range(1, 7):
                    if f'Hair{s}_' in b_name:
                        seg = s; break
                base_pitch = BACK_HAIR_DRAPE.get(seg, 0.0)
                phase = t - seg * 0.40
                pitch = base_pitch + bounce_amp * math.sin(phase)
                roll = sway_amp * math.cos(phase)
                pb_b.rotation_quaternion = create_quaternion((pitch, 0.0, roll))
                pb_b.keyframe_insert(data_path="rotation_quaternion", frame=frame)
                
            # Front Side Strands / Twintails (11, 12)
            elif any(f'_{idx:02d}' in b_name for idx in [11, 12]):
                seg = 1
                for s in range(1, 5):
                    if f'Hair{s}_' in b_name:
                        seg = s; break
                base_pitch = FRONT_SIDE_DRAPE.get(seg, 0.0)
                phase = t - seg * 0.35
                pitch = base_pitch + bounce_amp * 0.5 * math.sin(phase)
                roll = sway_amp * 0.5 * math.cos(phase)
                pb_b.rotation_quaternion = create_quaternion((pitch, 0.0, roll))
                pb_b.keyframe_insert(data_path="rotation_quaternion", frame=frame)
                
            # Front Bangs (01 to 04)
            elif any(f'_{idx:02d}' in b_name for idx in range(1, 5)):
                pb_b.rotation_quaternion = create_quaternion((-0.010, 0.0, 0.0))
                pb_b.keyframe_insert(data_path="rotation_quaternion", frame=frame)

def apply_pointing_hair_drape(pb, frame, t, sway_amp=0.018, bounce_amp=0.022):
    """
    Specialized drape for pointing pose:
    Counter-acts Head.yaw (+0.08) and Head.roll (+0.04).
    """
    for b_name, pb_b in pb.items():
        if 'hair' in b_name.lower():
            # Back Hair Chains (05 to 10)
            if any(f'_{idx:02d}' in b_name for idx in range(5, 11)):
                seg = 1
                for s in range(1, 7):
                    if f'Hair{s}_' in b_name:
                        seg = s; break
                
                chain_idx = 7
                for c in range(5, 11):
                    if f'_{c:02d}' in b_name:
                        chain_idx = c; break
                        
                base_pitch = BACK_HAIR_DRAPE.get(seg, 0.0)
                extra_roll = -0.04 if chain_idx >= 8 else -0.02
                phase = t - seg * 0.40
                pitch = base_pitch + bounce_amp * math.sin(phase)
                roll = extra_roll + sway_amp * math.cos(phase)
                
                pb_b.rotation_quaternion = create_quaternion((pitch, -0.06, roll))
                pb_b.keyframe_insert(data_path="rotation_quaternion", frame=frame)
                
            # Front Side Strands / Twintails (11, 12)
            elif any(f'_{idx:02d}' in b_name for idx in [11, 12]):
                seg = 1
                for s in range(1, 5):
                    if f'Hair{s}_' in b_name:
                        seg = s; break
                base_pitch = FRONT_SIDE_DRAPE.get(seg, 0.0)
                phase = t - seg * 0.35
                pitch = base_pitch + bounce_amp * 0.5 * math.sin(phase)
                roll = sway_amp * 0.5 * math.cos(phase)
                pb_b.rotation_quaternion = create_quaternion((pitch, 0.0, roll))
                pb_b.keyframe_insert(data_path="rotation_quaternion", frame=frame)
                
            # Front Bangs (01 to 04)
            elif any(f'_{idx:02d}' in b_name for idx in range(1, 5)):
                pb_b.rotation_quaternion = create_quaternion((-0.010, 0.0, 0.0))
                pb_b.keyframe_insert(data_path="rotation_quaternion", frame=frame)

def apply_left_pointing_hair_drape(pb, frame, t, sway_amp=0.018, bounce_amp=0.022):
    """
    Specialized drape for LEFT hand pointing pose:
    Counter-acts Head.yaw (-0.08).
    """
    for b_name, pb_b in pb.items():
        if 'hair' in b_name.lower():
            # Back Hair Chains (05 to 10)
            if any(f'_{idx:02d}' in b_name for idx in range(5, 11)):
                seg = 1
                for s in range(1, 7):
                    if f'Hair{s}_' in b_name:
                        seg = s; break
                
                chain_idx = 7
                for c in range(5, 11):
                    if f'_{c:02d}' in b_name:
                        chain_idx = c; break
                        
                base_pitch = BACK_HAIR_DRAPE.get(seg, 0.0)
                extra_roll = 0.04 if chain_idx <= 7 else 0.02
                phase = t - seg * 0.40
                pitch = base_pitch + bounce_amp * math.sin(phase)
                roll = extra_roll + sway_amp * math.cos(phase)
                
                pb_b.rotation_quaternion = create_quaternion((pitch, 0.06, roll))
                pb_b.keyframe_insert(data_path="rotation_quaternion", frame=frame)
                
            # Front Side Strands / Twintails (11, 12)
            elif any(f'_{idx:02d}' in b_name for idx in [11, 12]):
                seg = 1
                for s in range(1, 5):
                    if f'Hair{s}_' in b_name:
                        seg = s; break
                base_pitch = FRONT_SIDE_DRAPE.get(seg, 0.0)
                phase = t - seg * 0.35
                pitch = base_pitch + bounce_amp * 0.5 * math.sin(phase)
                roll = sway_amp * 0.5 * math.cos(phase)
                pb_b.rotation_quaternion = create_quaternion((pitch, 0.0, roll))
                pb_b.keyframe_insert(data_path="rotation_quaternion", frame=frame)
                
            # Front Bangs (01 to 04)
            elif any(f'_{idx:02d}' in b_name for idx in range(1, 5)):
                pb_b.rotation_quaternion = create_quaternion((-0.010, 0.0, 0.0))
                pb_b.keyframe_insert(data_path="rotation_quaternion", frame=frame)

def apply_dual_arm_hair_drape(pb, frame, t, sway_amp=0.018, bounce_amp=0.022):
    """
    Specialized drape for DUAL arms forward parallel pose.
    """
    for b_name, pb_b in pb.items():
        if 'hair' in b_name.lower():
            # Back Hair Chains (05 to 10)
            if any(f'_{idx:02d}' in b_name for idx in range(5, 11)):
                seg = 1
                for s in range(1, 7):
                    if f'Hair{s}_' in b_name:
                        seg = s; break
                base_pitch = BACK_HAIR_DRAPE.get(seg, 0.0)
                phase = t - seg * 0.40
                pitch = base_pitch + bounce_amp * math.sin(phase)
                roll = sway_amp * math.cos(phase)
                pb_b.rotation_quaternion = create_quaternion((pitch, 0.0, roll))
                pb_b.keyframe_insert(data_path="rotation_quaternion", frame=frame)
                
            # Front Side Strands / Twintails (11, 12)
            elif any(f'_{idx:02d}' in b_name for idx in [11, 12]):
                seg = 1
                for s in range(1, 5):
                    if f'Hair{s}_' in b_name:
                        seg = s; break
                base_pitch = FRONT_SIDE_DRAPE.get(seg, 0.0)
                phase = t - seg * 0.35
                pitch = base_pitch + bounce_amp * 0.5 * math.sin(phase)
                roll = sway_amp * 0.5 * math.cos(phase)
                pb_b.rotation_quaternion = create_quaternion((pitch, 0.0, roll))
                pb_b.keyframe_insert(data_path="rotation_quaternion", frame=frame)
                
            # Front Bangs (01 to 04)
            elif any(f'_{idx:02d}' in b_name for idx in range(1, 5)):
                pb_b.rotation_quaternion = create_quaternion((-0.010, 0.0, 0.0))
                pb_b.keyframe_insert(data_path="rotation_quaternion", frame=frame)

def apply_bow_hair_drape(pb, frame, bow_factor):
    """
    Specialized drape for Stage Bow:
    Hair drapes forward naturally along the bow angle without any sideways twist/rotation.
    """
    for b_name, pb_b in pb.items():
        if 'hair' in b_name.lower():
            if any(f'_{idx:02d}' in b_name for idx in range(5, 11)):
                seg = 1
                for s in range(1, 7):
                    if f'Hair{s}_' in b_name:
                        seg = s; break
                base_pitch = BACK_HAIR_DRAPE.get(seg, 0.0) + (0.08 + seg * 0.02) * bow_factor
                pb_b.rotation_quaternion = create_quaternion((base_pitch, 0.0, 0.0))
                pb_b.keyframe_insert(data_path="rotation_quaternion", frame=frame)
            elif any(f'_{idx:02d}' in b_name for idx in [11, 12]):
                seg = 1
                for s in range(1, 5):
                    if f'Hair{s}_' in b_name:
                        seg = s; break
                base_pitch = FRONT_SIDE_DRAPE.get(seg, 0.0) + 0.06 * bow_factor
                pb_b.rotation_quaternion = create_quaternion((base_pitch, 0.0, 0.0))
                pb_b.keyframe_insert(data_path="rotation_quaternion", frame=frame)
            elif any(f'_{idx:02d}' in b_name for idx in range(1, 5)):
                pb_b.rotation_quaternion = create_quaternion((-0.015, 0.0, 0.0))
                pb_b.keyframe_insert(data_path="rotation_quaternion", frame=frame)

def build_silky_soft_hair_5_states():
    print(">>> 1. Loading BVH Mocap Dataset & Character Model...")
    clean_scene()
    
    bvh_path = '/Volumes/DATA/ctg_ai/3d/mocap/dataset-1_walk_happy_001.bvh'
    input_glb = '/Volumes/DATA/ctg_ai/3d/phuong_an_B_anime_idol_female_singer/model/female_singer_anime_idol.glb'
    out_b_dir = '/Volumes/DATA/ctg_ai/3d/phuong_an_B_anime_idol_female_singer/model'
    stage_dir = '/Volumes/DATA/ctg_ai/3d/phuong_an_nang_cao_nu_ca_si_pro_stage/model'
    
    # Import BVH
    bpy.ops.import_anim.bvh(filepath=bvh_path)
    bvh_arm = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
    bvh_arm.name = 'BVH_Arm'
    
    # Import Character
    bpy.ops.import_scene.gltf(filepath=input_glb)
    char_arm = [o for o in bpy.data.objects if o.type == 'ARMATURE' and o != bvh_arm][0]
    char_arm.name = 'Character_Armature'
    
    # Purge old actions
    for a in list(bpy.data.actions):
        if a.name != 'dataset-1_walk_happy_001':
            bpy.data.actions.remove(a)
    if char_arm.animation_data:
        for t in list(char_arm.animation_data.nla_tracks):
            char_arm.animation_data.nla_tracks.remove(t)

    # Bind clothing vertex weights
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
    print(">>> 1. Creating 01_DungNghiem with Soft Silky Hair...")
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

        apply_soft_hair_drape(pb, frame, t, sway_amp=0.010, bounce_amp=0.015)

    # =========================================================================
    # STATE 2: 02_DungNghi (120 frames)
    # =========================================================================
    print(">>> 2. Creating 02_DungNghi with Soft Silky Hair...")
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

        apply_soft_hair_drape(pb, frame, t, sway_amp=0.018, bounce_amp=0.022)

    # =========================================================================
    # STATE 3: 03_TPose (30 frames)
    # =========================================================================
    print(">>> 3. Creating 03_TPose with Soft Silky Hair...")
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

        apply_soft_hair_drape(pb, frame, 0.0, sway_amp=0.0, bounce_amp=0.0)

    # =========================================================================
    # STATE 4 & 5: BIOMECHANICAL GAIT ENGINE (Trọng tâm chân trụ, Heel-Strike & Push-Off)
    # =========================================================================
    def get_biomechanical_gait_frame(phi, is_energetic=False):
        # 1. Hips Translation & Pelvis Sway (Trọng tâm dồn chuẩn xác vào chân trụ)
        # Khi phi in [0, pi] (chân Trái làm trụ), hông dịch chuyển sang Trái (+X)
        # Khi phi in [pi, 2pi] (chân Phải làm trụ), hông dịch chuyển sang Phải (-X)
        sway_amp = 0.034 if is_energetic else 0.030
        bounce_amp = 0.020 if is_energetic else 0.016
        
        hip_sway = sway_amp * math.sin(phi)
        # Nhún thấp nhất khi 2 chân tiếp đất (phi=0, pi), cao nhất khi đứng trên 1 chân trụ (phi=pi/2, 3pi/2)
        hip_bounce = -bounce_amp * math.cos(phi * 2.0)
        
        # Xoay hông theo sải chân (Pelvic yaw) và nghiêng xương chậu (Pelvic list/roll)
        pelvis_yaw = -0.075 * math.sin(phi)
        pelvis_roll = -0.040 * math.sin(phi) # Hông bên chân trụ nâng lên, hông bên chân lăng hạ nhẹ

        # 2. Dáng Người Thẳng Đứng, Ngực Vươn Cao (Chuẩn hình vẽ mẫu)
        spine_pitch = 0.045
        chest_pitch = 0.040
        neck_pitch = -0.015
        head_pitch = -0.020 + 0.010 * math.sin(phi * 2.0)
        
        spine_yaw = -pelvis_yaw * 0.65
        spine_roll = -pelvis_roll * 0.60
        chest_yaw = -pelvis_yaw * 0.45

        # 3. Hàm tính động tác chân chuẩn giải phẫu (Heel-Strike -> Flat -> Push-Off -> Swing)
        def calc_leg(leg_phi):
            p = leg_phi % (math.pi * 2.0)
            stride_amp = 0.44 if is_energetic else 0.40
            
            # Thigh Pitch: Đưa về trước (-X) khi tiếp đất, đưa ra sau (+X) khi đạp đẩy
            thigh = -stride_amp * math.cos(p)
            
            # Gối (Knee Flexion):
            if p < math.pi:
                # GIAI ĐOẠN TIẾP ĐẤT & CHÂN TRỤ (Stance Phase):
                # - Tiếp đất (p=0): Gối duỗi gần thẳng (0.05 rad) để gót chạm sàn
                # - Hấp thụ lực (p=pi/4): Gối khuỵu nhẹ (0.16 rad) chịu trọng lượng cơ thể
                # - Chân trụ thẳng (p=pi/2): Chân trụ duỗi thẳng (0.03 rad) nâng toàn bộ cơ thể lên cao
                # - Đạp lùi (p=3pi/4 đến pi): Chân đẩy thẳng ra sau (0.04 rad)
                cushion = math.sin(p * 2.0) ** 2
                knee = 0.04 + 0.14 * cushion * (1.0 if p < math.pi * 0.45 else 0.20)
            else:
                # GIAI ĐOẠN VUNG CHÂN (Swing Phase):
                # Gối gập sâu (lên đến 0.78 rad) để nhấc bàn chân không quẹt sàn!
                sw_p = p - math.pi
                knee = 0.04 + 0.76 * (math.sin(sw_p) ** 1.35)
                
            # Bàn Chân (Foot / Ankle Pitch):
            if p < math.pi * 0.35:
                # Heel-strike (Gót chạm đất, mũi chếch lên +0.36 rad -> lăn phẳng 0.0)
                foot = 0.36 * math.cos((p / (math.pi * 0.35)) * (math.pi / 2.0))
            elif p < math.pi * 0.55:
                # Flat Foot: Bàn chân phẳng hoàn toàn 100% trên mặt sàn khi gánh trọng tâm
                foot = 0.0
            elif p < math.pi:
                # Push-off: Gót chân nhấc cao, mũi chân miết đẩy sàn (-0.55 rad)
                push_p = (p - math.pi * 0.55) / (math.pi * 0.45)
                foot = -0.55 * (math.sin(push_p * (math.pi / 2.0)) ** 1.4)
            else:
                # Vung chân trên không: Thả lỏng rồi chuẩn bị gót tiếp đất
                sw_p = (p - math.pi) / math.pi
                if sw_p < 0.60:
                    foot = -0.15 * (1.0 - sw_p / 0.60)
                else:
                    foot = 0.36 * (((sw_p - 0.60) / 0.40) ** 1.3)
                    
            # Khớp mũi chân (ToeBase): Uốn cong khi gót nhấc đẩy sàn
            if math.pi * 0.65 < p < math.pi:
                toe_p = (p - math.pi * 0.65) / (math.pi * 0.35)
                toe = 0.35 * math.sin(toe_p * math.pi)
            else:
                toe = 0.0
                
            return thigh, knee, foot, toe

        l_thigh, l_knee, l_foot, l_toe = calc_leg(phi)
        r_thigh, r_knee, r_foot, r_toe = calc_leg(phi + math.pi)
        
        # Đánh tay ngược hướng chân tự nhiên
        arm_amp = 0.35 if is_energetic else 0.30
        l_arm = -arm_amp * math.sin(phi)
        r_arm = arm_amp * math.sin(phi)
        
        return {
            'hip_loc': (hip_sway, 0.0, hip_bounce),
            'hip_rot': (0.02, pelvis_yaw, pelvis_roll),
            'spine_rot': (spine_pitch, spine_yaw, spine_roll),
            'chest_rot': (chest_pitch, chest_yaw, 0.0),
            'neck_rot': (neck_pitch, 0.0, 0.0),
            'head_rot': (head_pitch, 0.0, 0.0),
            'l_thigh': l_thigh, 'l_knee': l_knee, 'l_foot': l_foot, 'l_toe': l_toe,
            'r_thigh': r_thigh, 'r_knee': r_knee, 'r_foot': r_foot, 'r_toe': r_toe,
            'l_arm': l_arm, 'r_arm': r_arm
        }

    # =========================================================================
    # STATE 4: 04_BuocDi_CoBan (60 frames)
    # =========================================================================
    print(">>> 4. Creating 04_BuocDi_CoBan with Biomechanical Stance Weight Shift...")
    act_walk_basic = bpy.data.actions.new(name="04_BuocDi_CoBan")
    char_arm.animation_data.action = act_walk_basic
    created_actions.append(act_walk_basic)
    for frame in range(1, 61):
        bpy.context.scene.frame_set(frame)
        phi = (frame / 60.0) * math.pi * 2.0
        g = get_biomechanical_gait_frame(phi, is_energetic=True)
        
        if pb.get('J_Bip_C_Hips'):
            pb['J_Bip_C_Hips'].location = g['hip_loc']; pb['J_Bip_C_Hips'].keyframe_insert(data_path="location", frame=frame)
            pb['J_Bip_C_Hips'].rotation_quaternion = create_quaternion(g['hip_rot']); pb['J_Bip_C_Hips'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_C_Spine'):
            pb['J_Bip_C_Spine'].rotation_quaternion = create_quaternion(g['spine_rot']); pb['J_Bip_C_Spine'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_C_UpperChest'):
            pb['J_Bip_C_UpperChest'].rotation_quaternion = create_quaternion(g['chest_rot']); pb['J_Bip_C_UpperChest'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_C_Neck'):
            pb['J_Bip_C_Neck'].rotation_quaternion = create_quaternion(g['neck_rot']); pb['J_Bip_C_Neck'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_C_Head'):
            pb['J_Bip_C_Head'].rotation_quaternion = create_quaternion(g['head_rot']); pb['J_Bip_C_Head'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        if pb.get('J_Bip_L_UpperLeg'):
            pb['J_Bip_L_UpperLeg'].rotation_quaternion = create_quaternion((g['l_thigh'], 0.0, -0.02)); pb['J_Bip_L_UpperLeg'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_L_LowerLeg'):
            pb['J_Bip_L_LowerLeg'].rotation_quaternion = create_quaternion((g['l_knee'], 0.0, 0.0)); pb['J_Bip_L_LowerLeg'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_L_Foot'):
            pb['J_Bip_L_Foot'].rotation_quaternion = create_quaternion((g['l_foot'], 0.0, 0.0)); pb['J_Bip_L_Foot'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_L_ToeBase'):
            pb['J_Bip_L_ToeBase'].rotation_quaternion = create_quaternion((g['l_toe'], 0.0, 0.0)); pb['J_Bip_L_ToeBase'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        if pb.get('J_Bip_R_UpperLeg'):
            pb['J_Bip_R_UpperLeg'].rotation_quaternion = create_quaternion((g['r_thigh'], 0.0, 0.02)); pb['J_Bip_R_UpperLeg'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_R_LowerLeg'):
            pb['J_Bip_R_LowerLeg'].rotation_quaternion = create_quaternion((g['r_knee'], 0.0, 0.0)); pb['J_Bip_R_LowerLeg'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_R_Foot'):
            pb['J_Bip_R_Foot'].rotation_quaternion = create_quaternion((g['r_foot'], 0.0, 0.0)); pb['J_Bip_R_Foot'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_R_ToeBase'):
            pb['J_Bip_R_ToeBase'].rotation_quaternion = create_quaternion((g['r_toe'], 0.0, 0.0)); pb['J_Bip_R_ToeBase'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        if pb.get('J_Bip_L_UpperArm'):
            pb['J_Bip_L_UpperArm'].rotation_quaternion = create_quaternion((g['l_arm'], 0.04, -1.26 + 0.05 * math.cos(phi))); pb['J_Bip_L_UpperArm'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_L_LowerArm'):
            pb['J_Bip_L_LowerArm'].rotation_quaternion = create_quaternion((0.15 + 0.12 * max(0.0, g['l_arm']), 0.0, -0.18)); pb['J_Bip_L_LowerArm'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_R_UpperArm'):
            pb['J_Bip_R_UpperArm'].rotation_quaternion = create_quaternion((g['r_arm'], -0.04, 1.26 - 0.05 * math.cos(phi))); pb['J_Bip_R_UpperArm'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_R_LowerArm'):
            pb['J_Bip_R_LowerArm'].rotation_quaternion = create_quaternion((0.15 + 0.12 * max(0.0, g['r_arm']), 0.0, 0.18)); pb['J_Bip_R_LowerArm'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        apply_soft_hair_drape(pb, frame, phi * 2.0, sway_amp=0.030, bounce_amp=0.035)

    # =========================================================================
    # STATE 5: 05_BuocDi_TuNhien (60 frames BIOMECHANICAL NATURAL STANCE WALK)
    # =========================================================================
    print(">>> 5. Baking Biomechanical Natural Walk with Full Stance Weight Shift & Soft Hair...")
    act_walk_mocap = bpy.data.actions.new(name="05_BuocDi_TuNhien")
    char_arm.animation_data.action = act_walk_mocap
    created_actions.append(act_walk_mocap)

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

    # =========================================================================
    # STATE 6: 06_TroTay_PhiaTruoc (60 frames FIST + POINTING + SOFT HAIR)
    # =========================================================================
    print(">>> 6. Baking 06_TroTay_PhiaTruoc with Perfect Fist & Soft Silky Hair...")
    act_point = bpy.data.actions.new(name="06_TroTay_PhiaTruoc")
    char_arm.animation_data.action = act_point
    created_actions.append(act_point)

    for frame in range(1, 61):
        bpy.context.scene.frame_set(frame)
        t = (frame / 60.0) * math.pi * 2.0
        sway = math.sin(t) * 0.015
        breath = math.sin(t) * 0.025
        
        # Stance: Dynamic confident idol pose
        if pb.get('J_Bip_C_Hips'):
            pb['J_Bip_C_Hips'].location = (0.025 + sway * 0.4, 0, -0.015)
            pb['J_Bip_C_Hips'].keyframe_insert(data_path="location", frame=frame)
            pb['J_Bip_C_Hips'].rotation_quaternion = create_quaternion((0.02, 0.05 + sway, -0.05))
            pb['J_Bip_C_Hips'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        # Legs
        if pb.get('J_Bip_L_UpperLeg'):
            pb['J_Bip_L_UpperLeg'].rotation_quaternion = create_quaternion((-0.12, 0.04, -0.06))
            pb['J_Bip_L_UpperLeg'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_L_LowerLeg'):
            pb['J_Bip_L_LowerLeg'].rotation_quaternion = create_quaternion((0.20, 0, 0))
            pb['J_Bip_L_LowerLeg'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        if pb.get('J_Bip_R_UpperLeg'):
            pb['J_Bip_R_UpperLeg'].rotation_quaternion = create_quaternion((-0.02, 0, 0.06))
            pb['J_Bip_R_UpperLeg'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_R_LowerLeg'):
            pb['J_Bip_R_LowerLeg'].rotation_quaternion = create_quaternion((0.05, 0, 0))
            pb['J_Bip_R_LowerLeg'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        # Torso & Spine
        if pb.get('J_Bip_C_Spine'):
            pb['J_Bip_C_Spine'].rotation_quaternion = create_quaternion((0.03 + breath * 0.3, -0.04, 0.02))
            pb['J_Bip_C_Spine'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_C_UpperChest'):
            pb['J_Bip_C_UpperChest'].rotation_quaternion = create_quaternion((0.04 + breath * 0.6, -0.06, 0.02))
            pb['J_Bip_C_UpperChest'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        # Head & Neck
        if pb.get('J_Bip_C_Neck'):
            pb['J_Bip_C_Neck'].rotation_quaternion = create_quaternion((0.01, 0.04 + sway, -0.02))
            pb['J_Bip_C_Neck'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_C_Head'):
            pb['J_Bip_C_Head'].rotation_quaternion = create_quaternion((-0.02, 0.08 + sway, 0.04))
            pb['J_Bip_C_Head'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        # RIGHT ARM: POINTING FORWARD DIRECTLY AT AUDIENCE
        point_swing = math.sin(t) * 0.02
        if pb.get('J_Bip_R_UpperArm'):
            pb['J_Bip_R_UpperArm'].rotation_quaternion = create_quaternion((-1.32 + point_swing, 0.18, 0.35))
            pb['J_Bip_R_UpperArm'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_R_LowerArm'):
            pb['J_Bip_R_LowerArm'].rotation_quaternion = create_quaternion((0.0, 0.0, 0.15))
            pb['J_Bip_R_LowerArm'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_R_Hand'):
            pb['J_Bip_R_Hand'].rotation_quaternion = create_quaternion((0.10, 0.0, 0.0))
            pb['J_Bip_R_Hand'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        # RIGHT FINGERS:
        # 1. Index Finger: STRAIGHT, POINTING FORWARD
        for seg in [1, 2, 3]:
            if pb.get(f'J_Bip_R_Index{seg}'):
                pb[f'J_Bip_R_Index{seg}'].rotation_quaternion = create_quaternion((0.0, 0.0, 0.0))
                pb[f'J_Bip_R_Index{seg}'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        # 2. Middle, Ring, Little Fingers: CURLED TIGHTLY INWARD INTO PALM (+Z)
        for f in ['Middle', 'Ring', 'Little']:
            for seg in [1, 2, 3]:
                curl_angle = 1.45 if seg < 3 else 1.30
                if pb.get(f'J_Bip_R_{f}{seg}'):
                    pb[f'J_Bip_R_{f}{seg}'].rotation_quaternion = create_quaternion((0.0, 0.0, curl_angle))
                    pb[f'J_Bip_R_{f}{seg}'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        # 3. Thumb: CLENCHED & WRAPPED TIGHTLY OVER THE FIST
        if pb.get('J_Bip_R_Thumb1'):
            pb['J_Bip_R_Thumb1'].rotation_quaternion = create_quaternion((0.70, 0.25, 0.85))
            pb['J_Bip_R_Thumb1'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_R_Thumb2'):
            pb['J_Bip_R_Thumb2'].rotation_quaternion = create_quaternion((0.0, 0.0, 1.20))
            pb['J_Bip_R_Thumb2'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_R_Thumb3'):
            pb['J_Bip_R_Thumb3'].rotation_quaternion = create_quaternion((0.0, 0.0, 1.10))
            pb['J_Bip_R_Thumb3'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        # LEFT ARM & HAND: Gracefully resting on waist
        if pb.get('J_Bip_L_UpperArm'):
            pb['J_Bip_L_UpperArm'].rotation_quaternion = create_quaternion((0.15, -0.30, -0.85))
            pb['J_Bip_L_UpperArm'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_L_LowerArm'):
            pb['J_Bip_L_LowerArm'].rotation_quaternion = create_quaternion((0.0, 0.0, -0.75))
            pb['J_Bip_L_LowerArm'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_L_Hand'):
            pb['J_Bip_L_Hand'].rotation_quaternion = create_quaternion((0.0, -0.20, 0.0))
            pb['J_Bip_L_Hand'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        for f in ['Middle', 'Ring', 'Little', 'Index']:
            for seg in [1, 2, 3]:
                if pb.get(f'J_Bip_L_{f}{seg}'):
                    pb[f'J_Bip_L_{f}{seg}'].rotation_quaternion = create_quaternion((0.0, 0.0, -0.55))
                    pb[f'J_Bip_L_{f}{seg}'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        for seg in [1, 2, 3]:
            if pb.get(f'J_Bip_L_Thumb{seg}'):
                pb[f'J_Bip_L_Thumb{seg}'].rotation_quaternion = create_quaternion((0.0, 0.0, -0.45))
                pb[f'J_Bip_L_Thumb{seg}'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        apply_pointing_hair_drape(pb, frame, t, sway_amp=0.018, bounce_amp=0.022)

    # =========================================================================
    # STATE 7: 07_DungNghi_DoiXung (120 frames - Symmetrical Mirror of 02_DungNghi)
    # =========================================================================
    print(">>> 7. Creating 07_DungNghi_DoiXung (Symmetrical Idle) with Soft Silky Hair...")
    act_nghi_mirror = bpy.data.actions.new(name="07_DungNghi_DoiXung")
    char_arm.animation_data.action = act_nghi_mirror
    created_actions.append(act_nghi_mirror)
    for frame in range(1, 121):
        bpy.context.scene.frame_set(frame)
        t = (frame / 120.0) * math.pi * 2
        sway = -math.sin(t) * 0.015
        breath = math.sin(t * 2) * 0.03
        if pb.get('J_Bip_C_Hips'):
            pb['J_Bip_C_Hips'].location = (-0.035 + sway * 0.5, 0, -0.015)
            pb['J_Bip_C_Hips'].keyframe_insert(data_path="location", frame=frame)
            pb['J_Bip_C_Hips'].rotation_quaternion = create_quaternion((0.02, -0.04, 0.06 + sway))
            pb['J_Bip_C_Hips'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_C_Spine'):
            pb['J_Bip_C_Spine'].rotation_quaternion = create_quaternion((0.02 + breath * 0.3, 0.02, -0.04))
            pb['J_Bip_C_Spine'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_C_UpperChest'):
            pb['J_Bip_C_UpperChest'].rotation_quaternion = create_quaternion((0.03 + breath * 0.7, 0.02, -0.03))
            pb['J_Bip_C_UpperChest'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_C_Neck'):
            pb['J_Bip_C_Neck'].rotation_quaternion = create_quaternion((0.01, -0.02, 0))
            pb['J_Bip_C_Neck'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_C_Head'):
            pb['J_Bip_C_Head'].rotation_quaternion = create_quaternion((0.02, -0.04 + sway, -0.03))
            pb['J_Bip_C_Head'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        # Left Leg: Standing Weight Bearing (Chân Trụ Trái)
        l_up_q = create_quaternion((-0.02, 0.0, -0.05))
        if pb.get('J_Bip_L_UpperLeg'):
            pb['J_Bip_L_UpperLeg'].rotation_quaternion = l_up_q
            pb['J_Bip_L_UpperLeg'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_L_LowerLeg'):
            pb['J_Bip_L_LowerLeg'].rotation_quaternion = create_quaternion((0.04, 0, 0))
            pb['J_Bip_L_LowerLeg'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        # Right Leg: Relaxed Bent (Chân Nghỉ Phải)
        r_up_q = create_quaternion((-0.18, -0.05, 0.08))
        if pb.get('J_Bip_R_UpperLeg'):
            pb['J_Bip_R_UpperLeg'].rotation_quaternion = r_up_q
            pb['J_Bip_R_UpperLeg'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_R_LowerLeg'):
            pb['J_Bip_R_LowerLeg'].rotation_quaternion = create_quaternion((0.35, 0, 0))
            pb['J_Bip_R_LowerLeg'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        # Arms: Symmetrical Natural Relaxation
        r_arm_q = create_quaternion((0.05, 0.05, 1.22 - sway))
        l_arm_q = create_quaternion((0.03, -0.05, -1.24 + sway))
        if pb.get('J_Bip_R_UpperArm'):
            pb['J_Bip_R_UpperArm'].rotation_quaternion = r_arm_q
            pb['J_Bip_R_UpperArm'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_L_UpperArm'):
            pb['J_Bip_L_UpperArm'].rotation_quaternion = l_arm_q
            pb['J_Bip_L_UpperArm'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_R_LowerArm'):
            pb['J_Bip_R_LowerArm'].rotation_quaternion = create_quaternion((0, 0, 0.18))
            pb['J_Bip_R_LowerArm'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_L_LowerArm'):
            pb['J_Bip_L_LowerArm'].rotation_quaternion = create_quaternion((0, 0, -0.15))
            pb['J_Bip_L_LowerArm'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        # Relaxed Fingers
        for side in ['L', 'R']:
            for f_name in ['Thumb', 'Index', 'Middle', 'Ring', 'Little']:
                for seg in range(1, 4):
                    b_name = f'J_Bip_{side}_{f_name}{seg}'
                    if pb.get(b_name):
                        pb[b_name].rotation_quaternion = create_quaternion((0.0, -0.15, -0.08 if side=='L' else 0.08))
                        pb[b_name].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        apply_soft_hair_drape(pb, frame, t, sway_amp=0.018, bounce_amp=0.022)

    # =========================================================================
    # STATE 8: 08_TroTay_Trai (60 frames - Symmetrical Mirror of 06_TroTay_PhiaTruoc)
    # =========================================================================
    print(">>> 8. Baking 08_TroTay_Trai (Symmetrical Left Pointing) with Perfect Fist & Soft Silky Hair...")
    act_point_left = bpy.data.actions.new(name="08_TroTay_Trai")
    char_arm.animation_data.action = act_point_left
    created_actions.append(act_point_left)

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

    # =========================================================================
    # STATE 9: 09_HaiTay_SongSong (60 frames - Dual Arms Parallel Forward)
    # =========================================================================
    print(">>> 9. Baking 09_HaiTay_SongSong (Dual Arms Parallel Forward) with Soft Silky Hair...")
    act_dual_arms = bpy.data.actions.new(name="09_HaiTay_SongSong")
    char_arm.animation_data.action = act_dual_arms
    created_actions.append(act_dual_arms)

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

    # =========================================================================
    # STATE 10: 10_HaiTay_TruocMat (60 frames - Dual Hands in Front of Face)
    # =========================================================================
    print(">>> 10. Baking 10_HaiTay_TruocMat (Dual Hands in Front of Face) with Soft Silky Hair...")
    act_hands_face = bpy.data.actions.new(name="10_HaiTay_TruocMat")
    char_arm.animation_data.action = act_hands_face
    created_actions.append(act_hands_face)

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

        # DUAL ARMS RAISED IN FRONT OF FACE (Parallel, chin/mouth level)
        arm_breath = math.sin(t * 2) * 0.015
        
        # Right Arm: angled forward & upward in front of right cheek
        if pb.get('J_Bip_R_UpperArm'):
            pb['J_Bip_R_UpperArm'].rotation_quaternion = create_quaternion((-0.82 + arm_breath, 0.22, 0.35))
            pb['J_Bip_R_UpperArm'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_R_LowerArm'):
            pb['J_Bip_R_LowerArm'].rotation_quaternion = create_quaternion((0.0, 0.0, 1.25))
            pb['J_Bip_R_LowerArm'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_R_Hand'):
            pb['J_Bip_R_Hand'].rotation_quaternion = create_quaternion((0.15, 0.0, -0.20))
            pb['J_Bip_R_Hand'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        # Left Arm: angled forward & upward in front of left cheek
        if pb.get('J_Bip_L_UpperArm'):
            pb['J_Bip_L_UpperArm'].rotation_quaternion = create_quaternion((-0.82 + arm_breath, -0.22, -0.35))
            pb['J_Bip_L_UpperArm'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_L_LowerArm'):
            pb['J_Bip_L_LowerArm'].rotation_quaternion = create_quaternion((0.0, 0.0, -1.25))
            pb['J_Bip_L_LowerArm'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_L_Hand'):
            pb['J_Bip_L_Hand'].rotation_quaternion = create_quaternion((0.15, 0.0, 0.20))
            pb['J_Bip_L_Hand'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        # FINGERS: Cute graceful open fingers framing the face
        for side in ['L', 'R']:
            sign = -1.0 if side == 'L' else 1.0
            for f in ['Index', 'Middle', 'Ring', 'Little']:
                for seg in [1, 2, 3]:
                    f_bone = f'J_Bip_{side}_{f}{seg}'
                    if pb.get(f_bone):
                        curl = 0.08 * seg * sign
                        pitch_f = -0.06 * seg
                        pb[f_bone].rotation_quaternion = create_quaternion((pitch_f, 0.0, curl))
                        pb[f_bone].keyframe_insert(data_path="rotation_quaternion", frame=frame)
            
            for seg in [1, 2, 3]:
                t_bone = f'J_Bip_{side}_Thumb{seg}'
                if pb.get(t_bone):
                    pb[t_bone].rotation_quaternion = create_quaternion((0.15, -0.10 * sign, -0.15 * sign))
                    pb[t_bone].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        apply_soft_hair_drape(pb, frame, t, sway_amp=0.018, bounce_amp=0.022)

    # =========================================================================
    # STATE 11: 11_TraiTim_YeuThuong (60 frames - Idol Heart Hands Gesture 💖)
    # =========================================================================
    print(">>> 11. Baking 11_TraiTim_YeuThuong (Idol Heart Hands) with Soft Silky Hair...")
    act_heart = bpy.data.actions.new(name="11_TraiTim_YeuThuong")
    char_arm.animation_data.action = act_heart
    created_actions.append(act_heart)

    for frame in range(1, 61):
        bpy.context.scene.frame_set(frame)
        t = (frame / 60.0) * math.pi * 2.0
        sway = math.sin(t) * 0.015
        breath = math.sin(t * 2) * 0.025
        
        # Stance: Cute anime idol pose (Right foot slightly out, left knee bent inward)
        if pb.get('J_Bip_C_Hips'):
            pb['J_Bip_C_Hips'].location = (0.02, 0.0, -0.015)
            pb['J_Bip_C_Hips'].keyframe_insert(data_path="location", frame=frame)
            pb['J_Bip_C_Hips'].rotation_quaternion = create_quaternion((0.02, 0.04, -0.04 + sway))
            pb['J_Bip_C_Hips'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        if pb.get('J_Bip_L_UpperLeg'):
            pb['J_Bip_L_UpperLeg'].rotation_quaternion = create_quaternion((-0.14, 0.06, -0.08))
            pb['J_Bip_L_UpperLeg'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_L_LowerLeg'):
            pb['J_Bip_L_LowerLeg'].rotation_quaternion = create_quaternion((0.25, 0, 0))
            pb['J_Bip_L_LowerLeg'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        if pb.get('J_Bip_R_UpperLeg'):
            pb['J_Bip_R_UpperLeg'].rotation_quaternion = create_quaternion((-0.02, 0.0, 0.05))
            pb['J_Bip_R_UpperLeg'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_R_LowerLeg'):
            pb['J_Bip_R_LowerLeg'].rotation_quaternion = create_quaternion((0.05, 0, 0))
            pb['J_Bip_R_LowerLeg'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        if pb.get('J_Bip_C_Spine'):
            pb['J_Bip_C_Spine'].rotation_quaternion = create_quaternion((0.03 + breath * 0.4, -0.02, 0.02))
            pb['J_Bip_C_Spine'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_C_UpperChest'):
            pb['J_Bip_C_UpperChest'].rotation_quaternion = create_quaternion((0.05 + breath * 0.7, -0.02, 0.02))
            pb['J_Bip_C_UpperChest'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        if pb.get('J_Bip_C_Neck'):
            pb['J_Bip_C_Neck'].rotation_quaternion = create_quaternion((0.01, 0.02, 0.0))
            pb['J_Bip_C_Neck'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_C_Head'):
            pb['J_Bip_C_Head'].rotation_quaternion = create_quaternion((-0.02, 0.04 + sway, 0.06)) # cute head tilt
            pb['J_Bip_C_Head'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        # Arms: Brought together in front of chest to form heart
        if pb.get('J_Bip_R_UpperArm'):
            pb['J_Bip_R_UpperArm'].rotation_quaternion = create_quaternion((-0.70, 0.28, 0.42))
            pb['J_Bip_R_UpperArm'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_R_LowerArm'):
            pb['J_Bip_R_LowerArm'].rotation_quaternion = create_quaternion((0.0, 0.0, 1.40))
            pb['J_Bip_R_LowerArm'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_R_Hand'):
            pb['J_Bip_R_Hand'].rotation_quaternion = create_quaternion((0.20, 0.15, -0.35))
            pb['J_Bip_R_Hand'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        if pb.get('J_Bip_L_UpperArm'):
            pb['J_Bip_L_UpperArm'].rotation_quaternion = create_quaternion((-0.70, -0.28, -0.42))
            pb['J_Bip_L_UpperArm'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_L_LowerArm'):
            pb['J_Bip_L_LowerArm'].rotation_quaternion = create_quaternion((0.0, 0.0, -1.40))
            pb['J_Bip_L_LowerArm'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_L_Hand'):
            pb['J_Bip_L_Hand'].rotation_quaternion = create_quaternion((0.20, -0.15, 0.35))
            pb['J_Bip_L_Hand'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        # Fingers: Curved arches of the heart
        for side in ['L', 'R']:
            sign = -1.0 if side == 'L' else 1.0
            for f in ['Index', 'Middle']:
                for seg in [1, 2, 3]:
                    f_bone = f'J_Bip_{side}_{f}{seg}'
                    if pb.get(f_bone):
                        pb[f_bone].rotation_quaternion = create_quaternion((0.0, 0.0, 0.85 * sign))
                        pb[f_bone].keyframe_insert(data_path="rotation_quaternion", frame=frame)
            for f in ['Ring', 'Little']:
                for seg in [1, 2, 3]:
                    f_bone = f'J_Bip_{side}_{f}{seg}'
                    if pb.get(f_bone):
                        pb[f_bone].rotation_quaternion = create_quaternion((0.0, 0.0, 1.25 * sign))
                        pb[f_bone].keyframe_insert(data_path="rotation_quaternion", frame=frame)
            
            for seg in [1, 2, 3]:
                t_bone = f'J_Bip_{side}_Thumb{seg}'
                if pb.get(t_bone):
                    pb[t_bone].rotation_quaternion = create_quaternion((0.40, 0.20 * sign, 0.60 * sign))
                    pb[t_bone].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        apply_soft_hair_drape(pb, frame, t, sway_amp=0.018, bounce_amp=0.022)

    # =========================================================================
    # STATE 12: 12_VayTay_ChaoHoi (60 frames - Cheerful Stage Wave 👋)
    # =========================================================================
    print(">>> 12. Baking 12_VayTay_ChaoHoi (Stage Wave) with Soft Silky Hair...")
    act_wave = bpy.data.actions.new(name="12_VayTay_ChaoHoi")
    char_arm.animation_data.action = act_wave
    created_actions.append(act_wave)

    for frame in range(1, 61):
        bpy.context.scene.frame_set(frame)
        t = (frame / 60.0) * math.pi * 2.0
        sway = math.sin(t) * 0.02
        breath = math.sin(t * 2) * 0.025
        wave_motion = math.sin(t * 3.0) * 0.45
        
        if pb.get('J_Bip_C_Hips'):
            pb['J_Bip_C_Hips'].location = (0.015, 0.0, -0.012)
            pb['J_Bip_C_Hips'].keyframe_insert(data_path="location", frame=frame)
            pb['J_Bip_C_Hips'].rotation_quaternion = create_quaternion((0.02, 0.03 + sway, -0.03))
            pb['J_Bip_C_Hips'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        if pb.get('J_Bip_L_UpperLeg'):
            pb['J_Bip_L_UpperLeg'].rotation_quaternion = create_quaternion((-0.08, 0.03, -0.05))
            pb['J_Bip_L_UpperLeg'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_L_LowerLeg'):
            pb['J_Bip_L_LowerLeg'].rotation_quaternion = create_quaternion((0.15, 0, 0))
            pb['J_Bip_L_LowerLeg'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        if pb.get('J_Bip_R_UpperLeg'):
            pb['J_Bip_R_UpperLeg'].rotation_quaternion = create_quaternion((-0.02, 0.0, 0.05))
            pb['J_Bip_R_UpperLeg'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_R_LowerLeg'):
            pb['J_Bip_R_LowerLeg'].rotation_quaternion = create_quaternion((0.05, 0, 0))
            pb['J_Bip_R_LowerLeg'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        if pb.get('J_Bip_C_Spine'):
            pb['J_Bip_C_Spine'].rotation_quaternion = create_quaternion((0.03 + breath * 0.4, -0.02, 0.02))
            pb['J_Bip_C_Spine'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_C_UpperChest'):
            pb['J_Bip_C_UpperChest'].rotation_quaternion = create_quaternion((0.05 + breath * 0.7, -0.02, 0.02))
            pb['J_Bip_C_UpperChest'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        if pb.get('J_Bip_C_Neck'):
            pb['J_Bip_C_Neck'].rotation_quaternion = create_quaternion((0.01, 0.03, 0.0))
            pb['J_Bip_C_Neck'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_C_Head'):
            pb['J_Bip_C_Head'].rotation_quaternion = create_quaternion((-0.04, 0.06 + sway, 0.02))
            pb['J_Bip_C_Head'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        # Right Arm Raised High Waving
        if pb.get('J_Bip_R_UpperArm'):
            pb['J_Bip_R_UpperArm'].rotation_quaternion = create_quaternion((-1.85, 0.35, 0.75))
            pb['J_Bip_R_UpperArm'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_R_LowerArm'):
            pb['J_Bip_R_LowerArm'].rotation_quaternion = create_quaternion((0.0, 0.0, 0.65))
            pb['J_Bip_R_LowerArm'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_R_Hand'):
            pb['J_Bip_R_Hand'].rotation_quaternion = create_quaternion((0.10, wave_motion, 0.0))
            pb['J_Bip_R_Hand'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        # Right Fingers: Open Fluttering
        for f in ['Index', 'Middle', 'Ring', 'Little']:
            for seg in [1, 2, 3]:
                f_bone = f'J_Bip_R_{f}{seg}'
                if pb.get(f_bone):
                    pb[f_bone].rotation_quaternion = create_quaternion((-0.04 * seg, 0.0, 0.06 * seg))
                    pb[f_bone].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_R_Thumb1'):
            pb['J_Bip_R_Thumb1'].rotation_quaternion = create_quaternion((0.15, 0.10, 0.15))
            pb['J_Bip_R_Thumb1'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        # Left Arm on Waist
        if pb.get('J_Bip_L_UpperArm'):
            pb['J_Bip_L_UpperArm'].rotation_quaternion = create_quaternion((0.15, -0.30, -0.85))
            pb['J_Bip_L_UpperArm'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_L_LowerArm'):
            pb['J_Bip_L_LowerArm'].rotation_quaternion = create_quaternion((0.0, 0.0, -0.75))
            pb['J_Bip_L_LowerArm'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_L_Hand'):
            pb['J_Bip_L_Hand'].rotation_quaternion = create_quaternion((0.0, -0.20, 0.0))
            pb['J_Bip_L_Hand'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        for f in ['Index', 'Middle', 'Ring', 'Little']:
            for seg in [1, 2, 3]:
                f_bone = f'J_Bip_L_{f}{seg}'
                if pb.get(f_bone):
                    pb[f_bone].rotation_quaternion = create_quaternion((0.0, 0.0, -0.55))
                    pb[f_bone].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        apply_pointing_hair_drape(pb, frame, t, sway_amp=0.018, bounce_amp=0.022)

    # =========================================================================
    # STATE 13: 13_Cuoi_DuyenDang (60 frames - Cute Idol Radiant Smile & Giggle 😄)
    # =========================================================================
    print(">>> 13. Baking 13_Cuoi_DuyenDang (Idol Radiant Smile & Giggle) with Soft Silky Hair...")
    act_smile = bpy.data.actions.new(name="13_Cuoi_DuyenDang")
    char_arm.animation_data.action = act_smile
    created_actions.append(act_smile)

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

    # =========================================================================
    # STATE 14: 14_CuiChao_KetThuc (60 frames - Stage Bow / Concert Thank You 🙇‍♀️)
    # =========================================================================
    print(">>> 14. Baking 14_CuiChao_KetThuc (Concert Stage Bow) with Soft Silky Hair...")
    act_bow = bpy.data.actions.new(name="14_CuiChao_KetThuc")
    char_arm.animation_data.action = act_bow
    created_actions.append(act_bow)

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

    # Delete BVH object before export
    bpy.data.objects.remove(bvh_arm, do_unlink=True)
    if bpy.data.actions.get('dataset-1_walk_happy_001'):
        bpy.data.actions.remove(bpy.data.actions['dataset-1_walk_happy_001'])

    # DELETE ANY JUNK / GIANT / UNUSED MESHES (Beta_Surface, Icosphere, etc.)
    print(">>> Purging all giant/junk meshes (Beta_Surface, Icosphere, etc.)...")
    for obj in list(bpy.data.objects):
        name_l = obj.name.lower()
        if obj.type == 'MESH':
            if 'beta_surface' in name_l or 'icosphere' in name_l:
                print(f"  Removing giant/junk mesh: {obj.name}")
                bpy.data.objects.remove(obj, do_unlink=True)
        elif obj.type == 'EMPTY':
            if 'beta' in name_l:
                bpy.data.objects.remove(obj, do_unlink=True)

    # Push all actions to NLA Tracks
    print(">>> Pushing all actions to NLA tracks...")
    for act in created_actions:
        track = char_arm.animation_data.nla_tracks.new()
        track.name = act.name
        track.strips.new(act.name, 1, act)

    print(">>> Actions in Blender database:", [a.name for a in bpy.data.actions])

    bpy.ops.object.mode_set(mode='OBJECT')

    # =========================================================================
    # CREATE MULTI-HAIRSTYLE COLLECTION: Long Silky, Shoulder Layered & Short Bob
    # =========================================================================
    print(">>> Creating Multi-Hairstyle Collection (Long Silky, Medium Shoulder & Short Bob)...")
    # Clean up any leftover hair duplicates from previous loads
    for obj in list(bpy.data.objects):
        if obj.type == 'MESH' and ('hair.' in obj.name.lower() or 'bob' in obj.name.lower() or 'shoulder' in obj.name.lower() or 'twintail' in obj.name.lower()):
            print(f"  Purging leftover duplicate hair mesh: {obj.name}")
            bpy.data.objects.remove(obj, do_unlink=True)

    orig_hair = bpy.data.objects.get('Hair')
    if orig_hair:
        # 1. Salon-Grade U-Silhouette & 3D Volume Anime Hairstyle Collection
        def create_perfect_tapered_hair(z_base_back, z_base_side, name, u_curve_depth=0.038):
            """
            Thuật toán Tóc Dáng Chữ U Chuẩn Salon (Salon-Grade U-Silhouette & 3D Volume):
            - Tạo đường viền đuôi tóc phía sau hình cánh cung chữ U mềm mại (phần giữa lưng dài hơn, hai bên vuốt nhẹ lên cao).
            - Phom tóc cong 3D ôm tròn theo hộp sọ và gáy (loại bỏ hoàn toàn cảm giác tóc bị ép dẹp như tấm ván phẳng).
            - Các lớp tóc xếp tầng tự nhiên, buông suôn mượt và kết thúc bằng từng ngọn nhọn chữ V thanh thoát.
            """
            new_hair = orig_hair.copy()
            new_hair.data = orig_hair.data.copy()
            new_hair.name = name
            bpy.context.collection.objects.link(new_hair)
            
            z_crown = 1.48
            z_min_orig = 1.028
            orig_span = z_crown - z_min_orig # ~0.452m
            
            for v in new_hair.data.vertices:
                # Mái trước trán (Y < -0.065 và Z > 1.35) -> giữ nguyên 100%
                if v.co.y < -0.065 and v.co.z > 1.35:
                    continue
                    
                if v.co.z < z_crown:
                    # Tỷ lệ vị trí dọc sợi tóc: 0.0 ở chân tóc, 1.0 ở chóp đuôi tóc
                    t = (z_crown - v.co.z) / orig_span
                    t = max(0.0, min(1.0, t))
                    
                    is_side = abs(v.co.x) > 0.05 and v.co.y < 0.02
                    
                    # 1. Đường cắt hình cánh cung chữ U mềm mại (U-Silhouette Arc)
                    # Ở giữa lưng (x=0) tóc dài hơn; ra hai bên vai (|x| tăng) tóc được vuốt nhẹ lên cao
                    x_norm = min(1.0, abs(v.co.x) / 0.12)
                    u_offset = (x_norm ** 1.6) * u_curve_depth
                    
                    if is_side:
                        z_target = z_base_side
                    else:
                        z_target = z_base_back + u_offset
                        
                    new_span = z_crown - z_target
                    v.co.z = z_crown - t * new_span
                    
                    # 2. Tạo khối 3D phồng tròn ôm theo phom đầu và gáy (Convex 3D Contour)
                    if is_side:
                        # Vạt tóc hai bên buông suôn thẳng ôm nhẹ dọc má và xương quai xanh
                        target_y = -0.030
                        v.co.y = target_y + (v.co.y - target_y) * (1.0 - t * 0.75)
                        v.co.x = v.co.x * (1.0 - t * 0.04)
                    else:
                        # Vạt tóc sau lưng: Phom cong 3D ôm theo gáy (ở giữa Y nhô ra, hai bên vuốt mềm ra trước)
                        convex_y = 0.048 - (abs(v.co.x) ** 1.8) * 0.85
                        # Giữ lại độ dày xếp lớp giữa các lọn tóc bên trong và bên ngoài
                        v.co.y = convex_y + (v.co.y - 0.045) * 0.40 * (1.0 - t * 0.50)
                        v.co.x = v.co.x * (1.0 - t * 0.03)
                        
            new_hair.data.update()
            mod = new_hair.modifiers.get('Armature')
            if not mod:
                mod = new_hair.modifiers.new(name='Armature', type='ARMATURE')
            mod.object = char_arm
            return new_hair

        # 1. Tóc Ngắn Bob Cá Tính (U-Silhouette Bob ôm gáy)
        create_perfect_tapered_hair(1.30, 1.34, 'Hair_ShortBob', u_curve_depth=0.025)

        # 2. Tóc Ngang Vai Thẳng Mượt (U-Silhouette Shoulder dáng cánh cung)
        create_perfect_tapered_hair(1.20, 1.25, 'Hair_MediumShoulder', u_curve_depth=0.038)

        # 3. Tóc Dài Vừa Thẳng Mượt (U-Silhouette Medium-Long)
        create_perfect_tapered_hair(1.14, 1.18, 'Hair_WavyCurled', u_curve_depth=0.045)

        print(">>> Multi-Hairstyle Collection Created Successfully with Salon-Grade U-Silhouette & 3D Contour!")

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
                kb['Face_Blendshape.Fcl_ALL_Joy'].value = 0.55 + 0.25 * math.sin((frame / 120.0) * math.pi * 4.0)
                kb['Face_Blendshape.Fcl_ALL_Joy'].keyframe_insert(data_path="value", frame=frame)
            if 'Face_Blendshape.Fcl_EYE_Close_L' in kb:
                kb['Face_Blendshape.Fcl_EYE_Close_L'].value = 1.0 if is_wink else 0.0
                kb['Face_Blendshape.Fcl_EYE_Close_L'].keyframe_insert(data_path="value", frame=frame)

    print(">>> Exporting PRISTINE 6-STATE GLB, FBX, BLEND WITH SILKY SOFT HAIR DRAPE...")
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
        
    print(">>> SILKY SOFT HAIR DRAPE BUILD COMPLETE!")

if __name__ == '__main__':
    build_silky_soft_hair_5_states()
    print("=== SILKY SOFT HAIR BUILD SUCCESSFUL ===")
