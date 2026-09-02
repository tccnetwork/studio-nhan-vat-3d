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

def build_human_mocap_singer_performance():
    print(">>> 1. Importing Character Model...")
    clean_scene()
    
    input_glb = '/Volumes/DATA/ctg_ai/3d/phuong_an_B_anime_idol_female_singer/model/female_singer_anime_idol.glb'
    mocap_bvh = '/Volumes/DATA/ctg_ai/3d/mocap/dataset-1_dance-long_normal_001.bvh'
    out_b_dir = '/Volumes/DATA/ctg_ai/3d/phuong_an_B_anime_idol_female_singer/model'
    stage_dir = '/Volumes/DATA/ctg_ai/3d/phuong_an_nang_cao_nu_ca_si_pro_stage/model'
    
    bpy.ops.import_scene.gltf(filepath=input_glb)
    char_arm = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
    char_arm.name = 'Char_Armature'
    
    # 1. BIND CLOTHING VERTEX WEIGHTS DIRECTLY TO HUMANOID BONES
    body_obj = None
    for obj in bpy.data.objects:
        if obj.type == 'MESH' and 'body' in obj.name.lower():
            body_obj = obj
            break
            
    if body_obj:
        print("Binding clothing vertex weights on Body mesh...")
        for vg_name in ['J_Aim_L_TopsUpperArm', 'J_Sec_L_TopsUpperArmInside', 'J_Sec_L_TopsUpperArmOutside', 'J_Roll_L_UpperArm']:
            merge_vertex_groups(body_obj, vg_name, 'J_Bip_L_UpperArm')
        for vg_name in ['J_Aim_R_TopsUpperArm', 'J_Sec_R_TopsUpperArmInside', 'J_Sec_R_TopsUpperArmOutside', 'J_Roll_R_UpperArm']:
            merge_vertex_groups(body_obj, vg_name, 'J_Bip_R_UpperArm')
        for vg_name in ['J_Aim_L_UpperLeg', 'J_Roll_L_UpperLeg', 'J_Sec_L_TopsUpperLegFront', 'J_Sec_L_TopsUpperLegBack', 'J_Sec_L_TopsUpperLegSide']:
            merge_vertex_groups(body_obj, vg_name, 'J_Bip_L_UpperLeg')
        for vg_name in ['J_Aim_R_UpperLeg', 'J_Roll_R_UpperLeg', 'J_Sec_R_TopsUpperLegFront', 'J_Sec_R_TopsUpperLegBack', 'J_Sec_R_TopsUpperLegSide']:
            merge_vertex_groups(body_obj, vg_name, 'J_Bip_R_UpperLeg')

    # 2. IMPORT GENUINE HUMAN MOTION CAPTURE
    print(">>> 2. Importing Authentic Human Dance Mocap BVH...")
    bpy.ops.import_anim.bvh(filepath=mocap_bvh, target='ARMATURE', global_scale=0.01)
    bvh_arm = [o for o in bpy.data.objects if o.type == 'ARMATURE' and o != char_arm][0]
    bvh_arm.name = 'BVH_Armature'
    
    # Center mocap hips offset
    bpy.context.scene.frame_set(1)
    bvh_hips = bvh_arm.pose.bones.get('Hips')
    char_hips = char_arm.pose.bones.get('J_Bip_C_Hips')
    
    # Bone Retargeting Mapping
    bone_map = [
        ('J_Bip_C_Hips', 'Hips', True), # (Char_Bone, BVH_Bone, copy_location)
        ('J_Bip_C_Spine', 'Spine', False),
        ('J_Bip_C_UpperChest', 'Chest', False),
        ('J_Bip_C_Neck', 'Neck', False),
        ('J_Bip_C_Head', 'Head', False),
        ('J_Bip_L_Shoulder', 'Shoulder_L', False),
        ('J_Bip_L_UpperArm', 'UpperArm_L', False),
        ('J_Bip_L_LowerArm', 'LowerArm_L', False),
        ('J_Bip_L_Hand', 'Hand_L', False),
        ('J_Bip_R_Shoulder', 'Shoulder_R', False),
        ('J_Bip_L_UpperLeg', 'UpperLeg_L', False),
        ('J_Bip_L_LowerLeg', 'LowerLeg_L', False),
        ('J_Bip_L_Foot', 'Foot_L', False),
        ('J_Bip_R_UpperLeg', 'UpperLeg_R', False),
        ('J_Bip_R_LowerLeg', 'LowerLeg_R', False),
        ('J_Bip_R_Foot', 'Foot_R', False),
    ]
    
    bpy.context.view_layer.objects.active = char_arm
    bpy.ops.object.mode_set(mode='POSE')
    
    for char_b_name, bvh_b_name, copy_loc in bone_map:
        pb = char_arm.pose.bones.get(char_b_name)
        if pb:
            if copy_loc:
                c_loc = pb.constraints.new('COPY_LOCATION')
                c_loc.target = bvh_arm
                c_loc.subtarget = bvh_b_name
                c_loc.influence = 0.90
            c_rot = pb.constraints.new('COPY_ROTATION')
            c_rot.target = bvh_arm
            c_rot.subtarget = bvh_b_name
            c_rot.target_space = 'WORLD'
            c_rot.owner_space = 'WORLD'

    # 3. BAKE MOCAP TO CHARACTER
    TOTAL_FRAMES = 450 # 15 seconds of real human motion capture performance at 30 fps
    print(f">>> 3. Baking {TOTAL_FRAMES} frames of Real Human Mocap...")
    bpy.ops.nla.bake(
        frame_start=1,
        frame_end=TOTAL_FRAMES,
        step=1,
        only_selected=False,
        visual_keying=True,
        clear_constraints=True,
        bake_types={'POSE'}
    )
    
    # Remove BVH Armature
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.data.objects.remove(bvh_arm, do_unlink=True)
    
    # 4. LAYER SINGER VOCAL & MICROPHONE PERFORMANCE
    print(">>> 4. Layering Vocal Mic & Lyrical Hand Articulations...")
    bpy.context.view_layer.objects.active = char_arm
    bpy.ops.object.mode_set(mode='POSE')
    
    for frame in range(1, TOTAL_FRAMES + 1):
        bpy.context.scene.frame_set(frame)
        t = (frame / float(TOTAL_FRAMES)) * math.pi * 2
        beat_t = (frame / 30.0) * math.pi * 4.33
        phrase_t = (frame % 150) / 150.0 * math.pi * 2 # 5s phrasing cycle
        
        # A. RIGHT ARM: Natural Singer Microphone Pose (Holding mic near mouth while swaying)
        r_arm = char_arm.pose.bones.get('J_Bip_R_UpperArm')
        r_fore = char_arm.pose.bones.get('J_Bip_R_LowerArm')
        r_hand = char_arm.pose.bones.get('J_Bip_R_Hand')
        
        # Subtle mic movement (raising slightly on high notes, dipping on pauses)
        mic_lift = 0.08 * math.sin(phrase_t)
        
        if r_arm and r_fore:
            r_arm.rotation_mode = 'QUATERNION'
            r_arm.rotation_quaternion = mathutils.Euler((
                0.0,
                0.62 + mic_lift * 0.5,
                1.15 + math.sin(beat_t * 0.25) * 0.05
            ), 'XYZ').to_quaternion()
            r_arm.keyframe_insert(data_path="rotation_quaternion", frame=frame)
            
            r_fore.rotation_mode = 'QUATERNION'
            r_fore.rotation_quaternion = mathutils.Euler((
                0.0,
                0.22,
                1.28 + mic_lift
            ), 'XYZ').to_quaternion()
            r_fore.keyframe_insert(data_path="rotation_quaternion", frame=frame)
            
            if r_hand:
                r_hand.rotation_mode = 'QUATERNION'
                r_hand.rotation_quaternion = mathutils.Euler((0.0, 0.28, 0.18), 'XYZ').to_quaternion()
                r_hand.keyframe_insert(data_path="rotation_quaternion", frame=frame)
                
            # Secondary shirt bones follow right arm
            for sec_name in ['J_Aim_R_TopsUpperArm', 'J_Roll_R_UpperArm', 'J_Sec_R_TopsUpperArmInside', 'J_Sec_R_TopsUpperArmOutside']:
                b = char_arm.pose.bones.get(sec_name)
                if b:
                    b.rotation_mode = 'QUATERNION'
                    b.rotation_quaternion = r_arm.rotation_quaternion
                    b.keyframe_insert(data_path="rotation_quaternion", frame=frame)

        # Secondary shirt bones follow Left mocap arm
        l_arm = char_arm.pose.bones.get('J_Bip_L_UpperArm')
        if l_arm:
            for sec_name in ['J_Aim_L_TopsUpperArm', 'J_Roll_L_UpperArm', 'J_Sec_L_TopsUpperArmInside', 'J_Sec_L_TopsUpperArmOutside']:
                b = char_arm.pose.bones.get(sec_name)
                if b:
                    b.rotation_mode = 'QUATERNION'
                    b.rotation_quaternion = l_arm.rotation_quaternion
                    b.keyframe_insert(data_path="rotation_quaternion", frame=frame)

        # Secondary pants bones follow Mocap legs
        l_leg = char_arm.pose.bones.get('J_Bip_L_UpperLeg')
        if l_leg:
            for sec_name in ['J_Aim_L_UpperLeg', 'J_Roll_L_UpperLeg', 'J_Sec_L_TopsUpperLegFront', 'J_Sec_L_TopsUpperLegBack', 'J_Sec_L_TopsUpperLegSide']:
                b = char_arm.pose.bones.get(sec_name)
                if b:
                    b.rotation_mode = 'QUATERNION'
                    b.rotation_quaternion = l_leg.rotation_quaternion
                    b.keyframe_insert(data_path="rotation_quaternion", frame=frame)
                    
        r_leg = char_arm.pose.bones.get('J_Bip_R_UpperLeg')
        if r_leg:
            for sec_name in ['J_Aim_R_UpperLeg', 'J_Roll_R_UpperLeg', 'J_Sec_R_TopsUpperLegFront', 'J_Sec_R_TopsUpperLegBack', 'J_Sec_R_TopsUpperLegSide']:
                b = char_arm.pose.bones.get(sec_name)
                if b:
                    b.rotation_mode = 'QUATERNION'
                    b.rotation_quaternion = r_leg.rotation_quaternion
                    b.keyframe_insert(data_path="rotation_quaternion", frame=frame)

        # B. FINGERS: Left Hand Dynamic Splay & Clenched Fist / Right Hand Mic Grip
        curl_factor = (math.sin(phrase_t) + 1.0) * 0.5 # 0.0 (Open) to 1.0 (Fist)
        
        # Left Thumb:
        l_th_rot_y = 0.20 - curl_factor * 0.65
        l_th_rot_z = 0.25 - curl_factor * 0.70
        for seg in range(1, 4):
            pb = char_arm.pose.bones.get(f'J_Bip_L_Thumb{seg}')
            if pb:
                pb.rotation_mode = 'QUATERNION'
                pb.rotation_quaternion = mathutils.Euler((0.0, l_th_rot_y, l_th_rot_z), 'XYZ').to_quaternion()
                pb.keyframe_insert(data_path="rotation_quaternion", frame=frame)
                
        # Left 4 Fingers:
        left_finger_names = ['Index', 'Middle', 'Ring', 'Little']
        for i, f_name in enumerate(left_finger_names):
            splay_angle = (i - 1.5) * 0.08 * (1.0 - curl_factor)
            for seg in range(1, 4):
                pb = char_arm.pose.bones.get(f'J_Bip_L_{f_name}{seg}')
                if pb:
                    seg_curl_y = 0.08 * (1.0 - curl_factor) - 1.10 * curl_factor
                    seg_curl_z = splay_angle + 0.60 * curl_factor
                    pb.rotation_mode = 'QUATERNION'
                    pb.rotation_quaternion = mathutils.Euler((0.0, seg_curl_y, seg_curl_z), 'XYZ').to_quaternion()
                    pb.keyframe_insert(data_path="rotation_quaternion", frame=frame)

        # Right Hand: Firm mic grip
        r_grip_tightness = 0.85 + 0.15 * math.sin(beat_t)
        for seg in range(1, 4):
            pb = char_arm.pose.bones.get(f'J_Bip_R_Thumb{seg}')
            if pb:
                pb.rotation_mode = 'QUATERNION'
                pb.rotation_quaternion = mathutils.Euler((0.0, -0.45 * r_grip_tightness, -0.55 * r_grip_tightness), 'XYZ').to_quaternion()
                pb.keyframe_insert(data_path="rotation_quaternion", frame=frame)
        for f_name in ['Index', 'Middle', 'Ring', 'Little']:
            for seg in range(1, 4):
                pb = char_arm.pose.bones.get(f'J_Bip_R_{f_name}{seg}')
                if pb:
                    pb.rotation_mode = 'QUATERNION'
                    pb.rotation_quaternion = mathutils.Euler((0.0, -1.05 * r_grip_tightness, -0.35 * r_grip_tightness), 'XYZ').to_quaternion()
                    pb.keyframe_insert(data_path="rotation_quaternion", frame=frame)

        # C. FLUID HAIR PHYSICS
        for pb in char_arm.pose.bones:
            if 'Hair' in pb.name:
                parts = pb.name.split('_')
                seg_idx = 1
                for ch in parts[2]:
                    if ch.isdigit():
                        seg_idx = int(ch)
                        break
                strand_num = int(parts[3]) if len(parts) > 3 and parts[3].isdigit() else 5
                
                if strand_num <= 4:
                    h_rot_x = 0.02 + 0.015 * math.sin(beat_t * 0.5 - seg_idx * 0.2)
                    h_rot_z = 0.02 * math.cos(beat_t * 0.5)
                else:
                    phase_lag = seg_idx * 0.35
                    amplitude_x = 0.025 * seg_idx
                    amplitude_z = 0.030 * seg_idx
                    h_rot_x = 0.06 + amplitude_x * math.sin(beat_t - phase_lag)
                    h_rot_z = amplitude_z * math.sin(beat_t * 0.5 - phase_lag)
                
                pb.rotation_mode = 'QUATERNION'
                pb.rotation_quaternion = mathutils.Euler((h_rot_x, 0.0, h_rot_z), 'XYZ').to_quaternion()
                pb.keyframe_insert(data_path="rotation_quaternion", frame=frame)

    bpy.ops.object.mode_set(mode='OBJECT')

    # 5. FACIAL EXPRESSIONS & LIP-SYNC
    face_obj = None
    for obj in bpy.data.objects:
        if obj.type == 'MESH' and 'face' in obj.name.lower() and obj.data.shape_keys:
            face_obj = obj
            break
            
    if face_obj and face_obj.data.shape_keys:
        kb = face_obj.data.shape_keys.key_blocks
        face_obj.data.shape_keys.animation_data_create()
        vowels = ['Face_Blendshape.Fcl_MTH_A', 'Face_Blendshape.Fcl_MTH_I', 'Face_Blendshape.Fcl_MTH_U', 'Face_Blendshape.Fcl_MTH_E', 'Face_Blendshape.Fcl_MTH_O']
        for frame in range(1, TOTAL_FRAMES + 1):
            cycle_idx = int((frame / 16.0)) % 5
            mouth_open = max(0.0, math.sin((frame / 30.0) * math.pi * 6.0)) * 0.95
            is_wink = (40 <= frame <= 55) or (150 <= frame <= 165) or (320 <= frame <= 335)
            for i, v_name in enumerate(vowels):
                if v_name in kb:
                    kb[v_name].value = mouth_open if i == cycle_idx else 0.0
                    kb[v_name].keyframe_insert(data_path="value", frame=frame)
            if 'Face_Blendshape.Fcl_ALL_Joy' in kb:
                kb['Face_Blendshape.Fcl_ALL_Joy'].value = 0.45 + 0.3 * math.sin((frame / float(TOTAL_FRAMES)) * math.pi * 4.0)
                kb['Face_Blendshape.Fcl_ALL_Joy'].keyframe_insert(data_path="value", frame=frame)
            if 'Face_Blendshape.Fcl_EYE_Close_L' in kb:
                kb['Face_Blendshape.Fcl_EYE_Close_L'].value = 1.0 if is_wink else 0.0
                kb['Face_Blendshape.Fcl_EYE_Close_L'].keyframe_insert(data_path="value", frame=frame)

    bpy.context.scene.frame_start = 1
    bpy.context.scene.frame_end = TOTAL_FRAMES
    bpy.context.scene.render.fps = 30

    # 6. EXPORT
    print(">>> 5. Exporting Genuine Mocap Models (.glb, .fbx, .blend)...")
    for folder, fname in [(out_b_dir, "female_singer_anime_idol"), (stage_dir, "female_singer_anime_pro")]:
        bpy.ops.export_scene.gltf(
            filepath=f"{folder}/{fname}.glb",
            export_format='GLB',
            export_animations=True,
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
        
    print(">>> ALL MOCAP MODELS EXPORTED SUCCESSFULLY!")

if __name__ == '__main__':
    build_human_mocap_singer_performance()
    print("=== RETARGETING REAL HUMAN MOCAP COMPLETE ===")
