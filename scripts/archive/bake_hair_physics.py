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

def bake_hair_physics_and_clothing():
    print(">>> Baking Physics-Based Fluid Hair & Bound Clothing...")
    clean_scene()
    
    input_glb = '/Volumes/DATA/ctg_ai/3d/phuong_an_B_anime_idol_female_singer/model/female_singer_anime_idol.glb'
    out_b_dir = '/Volumes/DATA/ctg_ai/3d/phuong_an_B_anime_idol_female_singer/model'
    stage_dir = '/Volumes/DATA/ctg_ai/3d/phuong_an_nang_cao_nu_ca_si_pro_stage/model'
    
    bpy.ops.import_scene.gltf(filepath=input_glb)
    
    # 1. BIND CLOTHING VERTEX GROUPS
    body_obj = None
    for obj in bpy.data.objects:
        if obj.type == 'MESH' and 'body' in obj.name.lower():
            body_obj = obj
            break
            
    if body_obj:
        print("Merging clothing vertex weights on Body mesh...")
        for vg_name in ['J_Aim_L_TopsUpperArm', 'J_Sec_L_TopsUpperArmInside', 'J_Sec_L_TopsUpperArmOutside', 'J_Roll_L_UpperArm']:
            merge_vertex_groups(body_obj, vg_name, 'J_Bip_L_UpperArm')
        for vg_name in ['J_Aim_R_TopsUpperArm', 'J_Sec_R_TopsUpperArmInside', 'J_Sec_R_TopsUpperArmOutside', 'J_Roll_R_UpperArm']:
            merge_vertex_groups(body_obj, vg_name, 'J_Bip_R_UpperArm')
        for vg_name in ['J_Aim_L_UpperLeg', 'J_Roll_L_UpperLeg', 'J_Sec_L_TopsUpperLegFront', 'J_Sec_L_TopsUpperLegBack', 'J_Sec_L_TopsUpperLegSide']:
            merge_vertex_groups(body_obj, vg_name, 'J_Bip_L_UpperLeg')
        for vg_name in ['J_Aim_R_UpperLeg', 'J_Roll_R_UpperLeg', 'J_Sec_R_TopsUpperLegFront', 'J_Sec_R_TopsUpperLegBack', 'J_Sec_R_TopsUpperLegSide']:
            merge_vertex_groups(body_obj, vg_name, 'J_Bip_R_UpperLeg')

    # 2. KEYFRAME ARMATURE ACTIONS
    armature = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
    bpy.context.view_layer.objects.active = armature
    armature.animation_data_create()
    
    action = bpy.data.actions.new(name="01_Idol_FullBody_Singing_Dance_FluidHair")
    armature.animation_data.action = action
    bpy.ops.object.mode_set(mode='POSE')
    
    for frame in range(1, 241):
        bpy.context.scene.frame_set(frame)
        t = (frame / 240.0) * math.pi * 2
        beat_t = (frame / 30.0) * math.pi * 4.33
        
        # HIPS
        hips = armature.pose.bones.get('J_Bip_C_Hips')
        if hips:
            hips.location.x = math.sin(beat_t * 0.5) * 0.05
            hips.location.z = -abs(math.sin(beat_t)) * 0.08
            hips.keyframe_insert(data_path="location", frame=frame)
            
            hips_euler = mathutils.Euler((
                math.sin(beat_t) * 0.06,
                math.cos(beat_t * 0.5) * 0.08,
                math.sin(beat_t * 0.5) * 0.12
            ), 'XYZ')
            hips.rotation_mode = 'QUATERNION'
            hips.rotation_quaternion = hips_euler.to_quaternion()
            hips.keyframe_insert(data_path="rotation_quaternion", frame=frame)

        # LEGS & SHORTS
        l_up = armature.pose.bones.get('J_Bip_L_UpperLeg')
        l_low = armature.pose.bones.get('J_Bip_L_LowerLeg')
        l_ft = armature.pose.bones.get('J_Bip_L_Foot')
        r_up = armature.pose.bones.get('J_Bip_R_UpperLeg')
        r_low = armature.pose.bones.get('J_Bip_R_LowerLeg')
        r_ft = armature.pose.bones.get('J_Bip_R_Foot')
        
        knee_bend_L = 0.25 + 0.80 * max(0.0, math.sin(beat_t * 0.5))
        knee_bend_R = 0.25 + 0.80 * max(0.0, -math.sin(beat_t * 0.5))
        l_up_quat = mathutils.Euler((-knee_bend_L * 0.65, 0.0, -0.04), 'XYZ').to_quaternion()
        r_up_quat = mathutils.Euler((-knee_bend_R * 0.65, 0.0, 0.04), 'XYZ').to_quaternion()
        
        if l_up and l_low:
            l_up.rotation_mode = 'QUATERNION'
            l_up.rotation_quaternion = l_up_quat
            l_up.keyframe_insert(data_path="rotation_quaternion", frame=frame)
            l_low.rotation_mode = 'QUATERNION'
            l_low.rotation_quaternion = mathutils.Euler((knee_bend_L * 1.40, 0.0, 0.0), 'XYZ').to_quaternion()
            l_low.keyframe_insert(data_path="rotation_quaternion", frame=frame)
            if l_ft:
                l_ft.rotation_mode = 'QUATERNION'
                l_ft.rotation_quaternion = mathutils.Euler((-knee_bend_L * 0.75, 0.0, 0.0), 'XYZ').to_quaternion()
                l_ft.keyframe_insert(data_path="rotation_quaternion", frame=frame)
            for sec_name in ['J_Aim_L_UpperLeg', 'J_Roll_L_UpperLeg', 'J_Sec_L_TopsUpperLegFront', 'J_Sec_L_TopsUpperLegBack', 'J_Sec_L_TopsUpperLegSide']:
                b = armature.pose.bones.get(sec_name)
                if b:
                    b.rotation_mode = 'QUATERNION'
                    b.rotation_quaternion = l_up_quat
                    b.keyframe_insert(data_path="rotation_quaternion", frame=frame)
                
        if r_up and r_low:
            r_up.rotation_mode = 'QUATERNION'
            r_up.rotation_quaternion = r_up_quat
            r_up.keyframe_insert(data_path="rotation_quaternion", frame=frame)
            r_low.rotation_mode = 'QUATERNION'
            r_low.rotation_quaternion = mathutils.Euler((knee_bend_R * 1.40, 0.0, 0.0), 'XYZ').to_quaternion()
            r_low.keyframe_insert(data_path="rotation_quaternion", frame=frame)
            if r_ft:
                r_ft.rotation_mode = 'QUATERNION'
                r_ft.rotation_quaternion = mathutils.Euler((-knee_bend_R * 0.75, 0.0, 0.0), 'XYZ').to_quaternion()
                r_ft.keyframe_insert(data_path="rotation_quaternion", frame=frame)
            for sec_name in ['J_Aim_R_UpperLeg', 'J_Roll_R_UpperLeg', 'J_Sec_R_TopsUpperLegFront', 'J_Sec_R_TopsUpperLegBack', 'J_Sec_R_TopsUpperLegSide']:
                b = armature.pose.bones.get(sec_name)
                if b:
                    b.rotation_mode = 'QUATERNION'
                    b.rotation_quaternion = r_up_quat
                    b.keyframe_insert(data_path="rotation_quaternion", frame=frame)

        # SPINE & HEAD
        spine = armature.pose.bones.get('J_Bip_C_Spine')
        head = armature.pose.bones.get('J_Bip_C_Head')
        if spine:
            spine.rotation_mode = 'QUATERNION'
            spine.rotation_quaternion = mathutils.Euler((math.sin(beat_t) * 0.04, -math.sin(beat_t * 0.5) * 0.08, 0.0), 'XYZ').to_quaternion()
            spine.keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if head:
            head.rotation_mode = 'QUATERNION'
            head.rotation_quaternion = mathutils.Euler((math.sin(beat_t) * 0.09, math.sin(beat_t * 0.5) * 0.16, math.cos(beat_t * 0.5) * 0.08), 'XYZ').to_quaternion()
            head.keyframe_insert(data_path="rotation_quaternion", frame=frame)

        # ARMS & SHIRT SLEEVES
        r_arm = armature.pose.bones.get('J_Bip_R_UpperArm')
        r_fore = armature.pose.bones.get('J_Bip_R_LowerArm')
        r_hand = armature.pose.bones.get('J_Bip_R_Hand')
        l_arm = armature.pose.bones.get('J_Bip_L_UpperArm')
        l_fore = armature.pose.bones.get('J_Bip_L_LowerArm')
        l_hand = armature.pose.bones.get('J_Bip_L_Hand')
        
        r_arm_quat = mathutils.Euler((
            0.0,
            0.65 + math.sin(beat_t * 0.5) * 0.08,
            1.15 + math.cos(beat_t * 0.5) * 0.06
        ), 'XYZ').to_quaternion()
        
        if r_arm and r_fore:
            r_arm.rotation_mode = 'QUATERNION'
            r_arm.rotation_quaternion = r_arm_quat
            r_arm.keyframe_insert(data_path="rotation_quaternion", frame=frame)
            r_fore.rotation_mode = 'QUATERNION'
            r_fore.rotation_quaternion = mathutils.Euler((0.0, 0.25, 1.25 + math.sin(beat_t) * 0.12), 'XYZ').to_quaternion()
            r_fore.keyframe_insert(data_path="rotation_quaternion", frame=frame)
            if r_hand:
                r_hand.rotation_mode = 'QUATERNION'
                r_hand.rotation_quaternion = mathutils.Euler((0.0, 0.3, 0.2), 'XYZ').to_quaternion()
                r_hand.keyframe_insert(data_path="rotation_quaternion", frame=frame)
            for sec_name in ['J_Aim_R_TopsUpperArm', 'J_Roll_R_UpperArm', 'J_Sec_R_TopsUpperArmInside', 'J_Sec_R_TopsUpperArmOutside']:
                b = armature.pose.bones.get(sec_name)
                if b:
                    b.rotation_mode = 'QUATERNION'
                    b.rotation_quaternion = r_arm_quat
                    b.keyframe_insert(data_path="rotation_quaternion", frame=frame)

        idol_cycle = (frame % 90) / 90.0 * math.pi * 2
        l_arm_quat = mathutils.Euler((
            0.0,
            -0.55 + math.sin(idol_cycle) * 0.30,
            -1.15 + math.cos(idol_cycle) * 0.25
        ), 'XYZ').to_quaternion()
        
        if l_arm and l_fore:
            l_arm.rotation_mode = 'QUATERNION'
            l_arm.rotation_quaternion = l_arm_quat
            l_arm.keyframe_insert(data_path="rotation_quaternion", frame=frame)
            l_fore.rotation_mode = 'QUATERNION'
            l_fore.rotation_quaternion = mathutils.Euler((0.0, -0.20, -0.85 - abs(math.sin(idol_cycle)) * 0.50), 'XYZ').to_quaternion()
            l_fore.keyframe_insert(data_path="rotation_quaternion", frame=frame)
            if l_hand:
                l_hand.rotation_mode = 'QUATERNION'
                l_hand.rotation_quaternion = mathutils.Euler((0.0, -0.2, -0.3 + math.sin(idol_cycle * 2) * 0.2), 'XYZ').to_quaternion()
                l_hand.keyframe_insert(data_path="rotation_quaternion", frame=frame)
            for sec_name in ['J_Aim_L_TopsUpperArm', 'J_Roll_L_UpperArm', 'J_Sec_L_TopsUpperArmInside', 'J_Sec_L_TopsUpperArmOutside']:
                b = armature.pose.bones.get(sec_name)
                if b:
                    b.rotation_mode = 'QUATERNION'
                    b.rotation_quaternion = l_arm_quat
                    b.keyframe_insert(data_path="rotation_quaternion", frame=frame)

        # -------------------------------------------------------------
        # 3. ADVANCED FLUID HAIR DYNAMICS (KHẮC PHỤC TÓC ĐÂM XUYÊN QUA ÁO)
        # -------------------------------------------------------------
        for pb in armature.pose.bones:
            if 'Hair' in pb.name:
                parts = pb.name.split('_') # e.g. J_Sec_Hair1_05
                # Extract segment index (1, 2, 3, 4, 5, 6)
                seg_idx = 1
                for ch in parts[2]:
                    if ch.isdigit():
                        seg_idx = int(ch)
                        break
                        
                strand_num = int(parts[3]) if len(parts) > 3 and parts[3].isdigit() else 5
                
                # Front bangs / side locks (Strands 1-4): very subtle floating
                if strand_num <= 4:
                    h_rot_x = 0.02 + 0.015 * math.sin(beat_t * 0.5 - seg_idx * 0.2)
                    h_rot_z = 0.02 * math.cos(beat_t * 0.5)
                # Back hair & Twin-tails (Strands 5-12):
                # Apply positive outward angle (+0.05) so it floats AWAY from shirt back!
                else:
                    # Wave propagation along chain segments
                    phase_lag = seg_idx * 0.35
                    amplitude_x = 0.025 * seg_idx
                    amplitude_z = 0.030 * seg_idx
                    
                    # Outward bias (+0.06 rad): prevents hair from piercing into back of shirt
                    h_rot_x = 0.06 + amplitude_x * math.sin(beat_t - phase_lag)
                    # Gentle side-to-side sway
                    h_rot_z = amplitude_z * math.sin(beat_t * 0.5 - phase_lag)
                
                pb.rotation_mode = 'QUATERNION'
                pb.rotation_quaternion = mathutils.Euler((h_rot_x, 0.0, h_rot_z), 'XYZ').to_quaternion()
                pb.keyframe_insert(data_path="rotation_quaternion", frame=frame)

    bpy.ops.object.mode_set(mode='OBJECT')

    # Facial Shape Keys
    face_obj = None
    for obj in bpy.data.objects:
        if obj.type == 'MESH' and 'face' in obj.name.lower() and obj.data.shape_keys:
            face_obj = obj
            break
            
    if face_obj and face_obj.data.shape_keys:
        kb = face_obj.data.shape_keys.key_blocks
        face_obj.data.shape_keys.animation_data_create()
        vowels = ['Face_Blendshape.Fcl_MTH_A', 'Face_Blendshape.Fcl_MTH_I', 'Face_Blendshape.Fcl_MTH_U', 'Face_Blendshape.Fcl_MTH_E', 'Face_Blendshape.Fcl_MTH_O']
        for frame in range(1, 241):
            cycle_idx = int((frame / 16.0)) % 5
            mouth_open = max(0.0, math.sin((frame / 30.0) * math.pi * 6.0)) * 0.95
            is_wink = (40 <= frame <= 55) or (120 <= frame <= 135) or (200 <= frame <= 215)
            for i, v_name in enumerate(vowels):
                if v_name in kb:
                    kb[v_name].value = mouth_open if i == cycle_idx else 0.0
                    kb[v_name].keyframe_insert(data_path="value", frame=frame)
            if 'Face_Blendshape.Fcl_ALL_Joy' in kb:
                kb['Face_Blendshape.Fcl_ALL_Joy'].value = 0.4 + 0.3 * math.sin((frame / 240.0) * math.pi * 4.0)
                kb['Face_Blendshape.Fcl_ALL_Joy'].keyframe_insert(data_path="value", frame=frame)
            if 'Face_Blendshape.Fcl_EYE_Close_L' in kb:
                kb['Face_Blendshape.Fcl_EYE_Close_L'].value = 1.0 if is_wink else 0.0
                kb['Face_Blendshape.Fcl_EYE_Close_L'].keyframe_insert(data_path="value", frame=frame)

    # Export Model B files
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
        
    print(">>> Model B Fluid Hair & Clothing Physics Exported Successfully!")

if __name__ == '__main__':
    bake_hair_physics_and_clothing()
    print("=== HAIR PHYSICS COMPLETED ===")
