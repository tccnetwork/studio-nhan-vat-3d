import bpy
import math
import mathutils

def clean_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)

# -------------------------------------------------------------------------
# GENERATE QUATERNION FULL-BODY DANCE FOR MODEL B (ANIME IDOL)
# -------------------------------------------------------------------------
def generate_quaternion_model_B():
    print(">>> Generating Visible Deep Knee-Bends & Articulated Dance for Model B (Anime)...")
    clean_scene()
    
    input_glb = '/Volumes/DATA/ctg_ai/3d/phuong_an_B_anime_idol_female_singer/model/female_singer_anime_idol.glb'
    out_dir = '/Volumes/DATA/ctg_ai/3d/phuong_an_B_anime_idol_female_singer/model'
    stage_dir = '/Volumes/DATA/ctg_ai/3d/phuong_an_nang_cao_nu_ca_si_pro_stage/model'
    
    bpy.ops.import_scene.gltf(filepath=input_glb)
    
    bpy.context.scene.render.fps = 30
    bpy.context.scene.frame_start = 1
    bpy.context.scene.frame_end = 240
    
    armature = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
    bpy.context.view_layer.objects.active = armature
    armature.animation_data_create()
    
    action = bpy.data.actions.new(name="01_Idol_FullBody_Dance_DeepKneeBends")
    armature.animation_data.action = action
    
    bpy.ops.object.mode_set(mode='POSE')
    
    for frame in range(1, 241):
        bpy.context.scene.frame_set(frame)
        t = (frame / 240.0) * math.pi * 2
        # J-Pop 130 BPM
        beat_t = (frame / 30.0) * math.pi * 4.33
        
        # 1. HIPS: Deep Rhythmic Bouncing (Nhún hông sâu thấy rõ)
        hips = armature.pose.bones.get('J_Bip_C_Hips')
        if hips:
            hips.location.x = math.sin(beat_t * 0.5) * 0.06
            # Deep vertical dip: down 0.08m on beats!
            hips.location.z = -abs(math.sin(beat_t)) * 0.075
            hips.keyframe_insert(data_path="location", frame=frame)
            
            hips_euler = mathutils.Euler((
                math.sin(beat_t) * 0.06,
                math.cos(beat_t * 0.5) * 0.08,
                math.sin(beat_t * 0.5) * 0.12
            ), 'XYZ')
            hips.rotation_mode = 'QUATERNION'
            hips.rotation_quaternion = hips_euler.to_quaternion()
            hips.keyframe_insert(data_path="rotation_quaternion", frame=frame)

        # 2. LEGS & DEEP KNEE BENDS (GẬP ĐẦU GỐI RÕ RỆT)
        l_up = armature.pose.bones.get('J_Bip_L_UpperLeg')
        l_low = armature.pose.bones.get('J_Bip_L_LowerLeg')
        l_ft = armature.pose.bones.get('J_Bip_L_Foot')
        
        r_up = armature.pose.bones.get('J_Bip_R_UpperLeg')
        r_low = armature.pose.bones.get('J_Bip_R_LowerLeg')
        r_ft = armature.pose.bones.get('J_Bip_R_Foot')
        
        # Knee flexion cycle: from 0.2 rad (11 deg) to 0.95 rad (55 DEG DEEP BEND!)
        knee_bend_L = 0.20 + 0.75 * max(0.0, math.sin(beat_t * 0.5))
        knee_bend_R = 0.20 + 0.75 * max(0.0, -math.sin(beat_t * 0.5))
        
        if l_up and l_low:
            # Thigh tilts forward
            l_up_euler = mathutils.Euler((-knee_bend_L * 0.65, 0.0, -0.04), 'XYZ')
            l_up.rotation_mode = 'QUATERNION'
            l_up.rotation_quaternion = l_up_euler.to_quaternion()
            l_up.keyframe_insert(data_path="rotation_quaternion", frame=frame)
            
            # LowerLeg (KNEE) bends deeply back!
            l_low_euler = mathutils.Euler((knee_bend_L * 1.35, 0.0, 0.0), 'XYZ')
            l_low.rotation_mode = 'QUATERNION'
            l_low.rotation_quaternion = l_low_euler.to_quaternion()
            l_low.keyframe_insert(data_path="rotation_quaternion", frame=frame)
            
            if l_ft:
                l_ft_euler = mathutils.Euler((-knee_bend_L * 0.7, 0.0, 0.0), 'XYZ')
                l_ft.rotation_mode = 'QUATERNION'
                l_ft.rotation_quaternion = l_ft_euler.to_quaternion()
                l_ft.keyframe_insert(data_path="rotation_quaternion", frame=frame)
                
        if r_up and r_low:
            r_up_euler = mathutils.Euler((-knee_bend_R * 0.65, 0.0, 0.04), 'XYZ')
            r_up.rotation_mode = 'QUATERNION'
            r_up.rotation_quaternion = r_up_euler.to_quaternion()
            r_up.keyframe_insert(data_path="rotation_quaternion", frame=frame)
            
            # Right KNEE bends deeply back!
            r_low_euler = mathutils.Euler((knee_bend_R * 1.35, 0.0, 0.0), 'XYZ')
            r_low.rotation_mode = 'QUATERNION'
            r_low.rotation_quaternion = r_low_euler.to_quaternion()
            r_low.keyframe_insert(data_path="rotation_quaternion", frame=frame)
            
            if r_ft:
                r_ft_euler = mathutils.Euler((-knee_bend_R * 0.7, 0.0, 0.0), 'XYZ')
                r_ft.rotation_mode = 'QUATERNION'
                r_ft.rotation_quaternion = r_ft_euler.to_quaternion()
                r_ft.keyframe_insert(data_path="rotation_quaternion", frame=frame)

        # 3. SPINE & HEAD
        spine = armature.pose.bones.get('J_Bip_C_Spine')
        head = armature.pose.bones.get('J_Bip_C_Head')
        if spine:
            spine_euler = mathutils.Euler((math.sin(beat_t) * 0.04, -math.sin(beat_t * 0.5) * 0.08, 0.0), 'XYZ')
            spine.rotation_mode = 'QUATERNION'
            spine.rotation_quaternion = spine_euler.to_quaternion()
            spine.keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if head:
            head_euler = mathutils.Euler((math.sin(beat_t) * 0.09, math.sin(beat_t * 0.5) * 0.16, math.cos(beat_t * 0.5) * 0.08), 'XYZ')
            head.rotation_mode = 'QUATERNION'
            head.rotation_quaternion = head_euler.to_quaternion()
            head.keyframe_insert(data_path="rotation_quaternion", frame=frame)

        # 4. ARMS & ELBOWS (TAY & KHUỶU TAY)
        r_arm = armature.pose.bones.get('J_Bip_R_UpperArm')
        r_fore = armature.pose.bones.get('J_Bip_R_LowerArm')
        r_hand = armature.pose.bones.get('J_Bip_R_Hand')
        
        l_arm = armature.pose.bones.get('J_Bip_L_UpperArm')
        l_fore = armature.pose.bones.get('J_Bip_L_LowerArm')
        l_hand = armature.pose.bones.get('J_Bip_L_Hand')
        
        if r_arm and r_fore:
            r_arm_euler = mathutils.Euler((-0.80 + math.sin(beat_t * 0.5) * 0.10, 0.35, -0.45), 'XYZ')
            r_arm.rotation_mode = 'QUATERNION'
            r_arm.rotation_quaternion = r_arm_euler.to_quaternion()
            r_arm.keyframe_insert(data_path="rotation_quaternion", frame=frame)
            
            # Right ELBOW flexed to mouth!
            r_fore_euler = mathutils.Euler((-1.45 + math.sin(beat_t) * 0.12, -0.45, 0.0), 'XYZ')
            r_fore.rotation_mode = 'QUATERNION'
            r_fore.rotation_quaternion = r_fore_euler.to_quaternion()
            r_fore.keyframe_insert(data_path="rotation_quaternion", frame=frame)
            
        if l_arm and l_fore:
            idol_cycle = (frame % 80) / 80.0 * math.pi * 2
            l_arm_euler = mathutils.Euler((0.45 + math.sin(idol_cycle) * 0.35, -0.25, 0.55 + math.cos(idol_cycle) * 0.30), 'XYZ')
            l_arm.rotation_mode = 'QUATERNION'
            l_arm.rotation_quaternion = l_arm_euler.to_quaternion()
            l_arm.keyframe_insert(data_path="rotation_quaternion", frame=frame)
            
            # Left ELBOW articulating!
            l_fore_euler = mathutils.Euler((-0.75 - abs(math.sin(idol_cycle)) * 0.60, 0.0, 0.0), 'XYZ')
            l_fore.rotation_mode = 'QUATERNION'
            l_fore.rotation_quaternion = l_fore_euler.to_quaternion()
            l_fore.keyframe_insert(data_path="rotation_quaternion", frame=frame)

        # 5. TWIN-TAILS HAIR SWAY
        for pb in armature.pose.bones:
            if 'Hair' in pb.name:
                h_euler = mathutils.Euler((-math.sin(beat_t) * 0.10, 0.0, -math.sin(beat_t * 0.5) * 0.12), 'XYZ')
                pb.rotation_mode = 'QUATERNION'
                pb.rotation_quaternion = h_euler.to_quaternion()
                pb.keyframe_insert(data_path="rotation_quaternion", frame=frame)

    bpy.ops.object.mode_set(mode='OBJECT')

    # Animate Facial Shape Keys
    face_obj = None
    for obj in bpy.data.objects:
        if obj.type == 'MESH' and 'face' in obj.name.lower() and obj.data.shape_keys:
            face_obj = obj
            break
            
    if face_obj and face_obj.data.shape_keys:
        kb = face_obj.data.shape_keys.key_blocks
        face_obj.data.shape_keys.animation_data_create()
        
        vowels = [
            'Face_Blendshape.Fcl_MTH_A',
            'Face_Blendshape.Fcl_MTH_I',
            'Face_Blendshape.Fcl_MTH_U',
            'Face_Blendshape.Fcl_MTH_E',
            'Face_Blendshape.Fcl_MTH_O'
        ]
        
        for frame in range(1, 241):
            cycle_idx = int((frame / 16.0)) % 5
            mouth_open = max(0.0, math.sin((frame / 30.0) * math.pi * 6.0)) * 0.95
            is_wink = (40 <= frame <= 55) or (120 <= frame <= 135) or (200 <= frame <= 215)
            
            for i, v_name in enumerate(vowels):
                if v_name in kb:
                    val = mouth_open if i == cycle_idx else 0.0
                    kb[v_name].value = val
                    kb[v_name].keyframe_insert(data_path="value", frame=frame)
                    
            if 'Face_Blendshape.Fcl_ALL_Joy' in kb:
                kb['Face_Blendshape.Fcl_ALL_Joy'].value = 0.4 + 0.3 * math.sin((frame / 240.0) * math.pi * 4.0)
                kb['Face_Blendshape.Fcl_ALL_Joy'].keyframe_insert(data_path="value", frame=frame)
                
            if 'Face_Blendshape.Fcl_EYE_Close_L' in kb:
                kb['Face_Blendshape.Fcl_EYE_Close_L'].value = 1.0 if is_wink else 0.0
                kb['Face_Blendshape.Fcl_EYE_Close_L'].keyframe_insert(data_path="value", frame=frame)

    # Export to both Model B folder and Stage folder
    for folder, fname in [(out_dir, "female_singer_anime_idol"), (stage_dir, "female_singer_anime_pro")]:
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
        
    print(">>> Model B Exported with Clean Quaternions Successfully!")


# -------------------------------------------------------------------------
# GENERATE QUATERNION FULL-BODY DANCE FOR MODEL A (REALISTIC)
# -------------------------------------------------------------------------
def generate_quaternion_model_A():
    print(">>> Generating Visible Deep Knee-Bends & Articulated Dance for Model A (Realistic)...")
    clean_scene()
    
    input_glb = '/Volumes/DATA/ctg_ai/3d/phuong_an_A_realistic_female_singer/model/female_singer_realistic.glb'
    out_dir = '/Volumes/DATA/ctg_ai/3d/phuong_an_A_realistic_female_singer/model'
    stage_dir = '/Volumes/DATA/ctg_ai/3d/phuong_an_nang_cao_nu_ca_si_pro_stage/model'
    
    bpy.ops.import_scene.gltf(filepath=input_glb)
    
    bpy.context.scene.render.fps = 30
    bpy.context.scene.frame_start = 1
    bpy.context.scene.frame_end = 240
    
    armature = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
    bpy.context.view_layer.objects.active = armature
    armature.animation_data_create()
    
    action = bpy.data.actions.new(name="01_Realistic_FullBody_Dance_DeepKneeBends")
    armature.animation_data.action = action
    
    bpy.ops.object.mode_set(mode='POSE')
    
    for frame in range(1, 241):
        bpy.context.scene.frame_set(frame)
        t = (frame / 240.0) * math.pi * 2
        beat_t = (frame / 30.0) * math.pi * 4.0
        
        # 1. HIPS
        hips = armature.pose.bones.get('Hips')
        if hips:
            hips.location.x = math.sin(t * 2.0) * 0.05
            hips.location.y = math.cos(t * 2.0) * 0.02
            hips.location.z = -abs(math.sin(beat_t * 0.5)) * 0.075 # Deep dip!
            hips.keyframe_insert(data_path="location", frame=frame)
            
            hips_euler = mathutils.Euler((
                math.sin(beat_t * 0.5) * 0.05,
                math.cos(t * 2.0) * 0.06,
                math.sin(t * 2.0) * 0.10
            ), 'XYZ')
            hips.rotation_mode = 'QUATERNION'
            hips.rotation_quaternion = hips_euler.to_quaternion()
            hips.keyframe_insert(data_path="rotation_quaternion", frame=frame)

        # 2. LEGS & KNEES (GẬP ĐẦU GỐI)
        l_up = armature.pose.bones.get('LeftUpLeg')
        l_leg = armature.pose.bones.get('LeftLeg')
        l_ft = armature.pose.bones.get('LeftFoot')
        
        r_up = armature.pose.bones.get('RightUpLeg')
        r_leg = armature.pose.bones.get('RightLeg')
        r_ft = armature.pose.bones.get('RightFoot')
        
        k_flex_L = 0.20 + 0.75 * max(0.0, math.sin(beat_t * 0.5))
        k_flex_R = 0.20 + 0.75 * max(0.0, -math.sin(beat_t * 0.5))
        
        if l_up and l_leg:
            l_up_euler = mathutils.Euler((-k_flex_L * 0.65, 0.0, -0.05), 'XYZ')
            l_up.rotation_mode = 'QUATERNION'
            l_up.rotation_quaternion = l_up_euler.to_quaternion()
            l_up.keyframe_insert(data_path="rotation_quaternion", frame=frame)
            
            # Left KNEE bend!
            l_leg_euler = mathutils.Euler((k_flex_L * 1.35, 0.0, 0.0), 'XYZ')
            l_leg.rotation_mode = 'QUATERNION'
            l_leg.rotation_quaternion = l_leg_euler.to_quaternion()
            l_leg.keyframe_insert(data_path="rotation_quaternion", frame=frame)
            
            if l_ft:
                l_ft_euler = mathutils.Euler((-k_flex_L * 0.7, 0.0, 0.0), 'XYZ')
                l_ft.rotation_mode = 'QUATERNION'
                l_ft.rotation_quaternion = l_ft_euler.to_quaternion()
                l_ft.keyframe_insert(data_path="rotation_quaternion", frame=frame)
                
        if r_up and r_leg:
            r_up_euler = mathutils.Euler((-k_flex_R * 0.65, 0.0, 0.05), 'XYZ')
            r_up.rotation_mode = 'QUATERNION'
            r_up.rotation_quaternion = r_up_euler.to_quaternion()
            r_up.keyframe_insert(data_path="rotation_quaternion", frame=frame)
            
            # Right KNEE bend!
            r_leg_euler = mathutils.Euler((k_flex_R * 1.35, 0.0, 0.0), 'XYZ')
            r_leg.rotation_mode = 'QUATERNION'
            r_leg.rotation_quaternion = r_leg_euler.to_quaternion()
            r_leg.keyframe_insert(data_path="rotation_quaternion", frame=frame)
            
            if r_ft:
                r_ft_euler = mathutils.Euler((-k_flex_R * 0.7, 0.0, 0.0), 'XYZ')
                r_ft.rotation_mode = 'QUATERNION'
                r_ft.rotation_quaternion = r_ft_euler.to_quaternion()
                r_ft.keyframe_insert(data_path="rotation_quaternion", frame=frame)

        # 3. ARMS
        r_arm = armature.pose.bones.get('RightArm')
        r_fore = armature.pose.bones.get('RightForeArm')
        l_arm = armature.pose.bones.get('LeftArm')
        l_fore = armature.pose.bones.get('LeftForeArm')
        
        if r_arm and r_fore:
            r_arm_euler = mathutils.Euler((-0.75 + math.sin(t * 2.0) * 0.10, 0.30, -0.45), 'XYZ')
            r_arm.rotation_mode = 'QUATERNION'
            r_arm.rotation_quaternion = r_arm_euler.to_quaternion()
            r_arm.keyframe_insert(data_path="rotation_quaternion", frame=frame)
            
            # Right ELBOW flexed to mouth!
            r_fore_euler = mathutils.Euler((-1.40 + math.sin(beat_t * 0.5) * 0.12, -0.40, 0.0), 'XYZ')
            r_fore.rotation_mode = 'QUATERNION'
            r_fore.rotation_quaternion = r_fore_euler.to_quaternion()
            r_fore.keyframe_insert(data_path="rotation_quaternion", frame=frame)
            
        if l_arm and l_fore:
            g_phase = (frame % 120) / 120.0 * math.pi * 2
            l_arm_euler = mathutils.Euler((0.40 + math.sin(g_phase) * 0.30, -0.20, 0.50 + math.cos(g_phase) * 0.25), 'XYZ')
            l_arm.rotation_mode = 'QUATERNION'
            l_arm.rotation_quaternion = l_arm_euler.to_quaternion()
            l_arm.keyframe_insert(data_path="rotation_quaternion", frame=frame)
            
            # Left ELBOW articulating!
            l_fore_euler = mathutils.Euler((-0.70 - abs(math.sin(g_phase)) * 0.55, 0.0, 0.0), 'XYZ')
            l_fore.rotation_mode = 'QUATERNION'
            l_fore.rotation_quaternion = l_fore_euler.to_quaternion()
            l_fore.keyframe_insert(data_path="rotation_quaternion", frame=frame)

    bpy.ops.object.mode_set(mode='OBJECT')

    # Export Model A
    for folder, fname in [(out_dir, "female_singer_realistic"), (stage_dir, "female_singer_pro_stage")]:
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
        
    print(">>> Model A Exported with Clean Quaternions Successfully!")


if __name__ == '__main__':
    generate_quaternion_model_B()
    generate_quaternion_model_A()
    print("=== ALL QUATERNION DEEP KNEE-BEND DANCE GENERATIONS COMPLETED! ===")
