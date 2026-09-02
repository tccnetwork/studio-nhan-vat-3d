import bpy
import math

def clean_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)

# -------------------------------------------------------------------------
# GENERATE FULL-BODY ARTICULATED SINGER CHOREOGRAPHY FOR MODEL A (REALISTIC)
# -------------------------------------------------------------------------
def generate_full_body_model_A():
    print(">>> Generating Full-Body Articulated Dance & Singing for Model A...")
    clean_scene()
    
    input_glb = '/Volumes/DATA/ctg_ai/3d/phuong_an_A_realistic_female_singer/model/female_singer_realistic.glb'
    out_dir = '/Volumes/DATA/ctg_ai/3d/phuong_an_nang_cao_nu_ca_si_pro_stage/model'
    
    bpy.ops.import_scene.gltf(filepath=input_glb)
    
    bpy.context.scene.render.fps = 30
    bpy.context.scene.frame_start = 1
    bpy.context.scene.frame_end = 240 # 8 seconds loop
    
    armature = None
    for obj in bpy.data.objects:
        if obj.type == 'ARMATURE':
            armature = obj
            break
            
    if not armature:
        print("Error: Armature not found!")
        return

    bpy.context.view_layer.objects.active = armature
    armature.animation_data_create()
    
    # -------------------------------------------------------------
    # ACTION: Pro_Singer_FullBody_Live_Performance
    # -------------------------------------------------------------
    action = bpy.data.actions.new(name="Pro_Singer_FullBody_Live_Performance")
    armature.animation_data.action = action
    
    bpy.ops.object.mode_set(mode='POSE')
    
    # Bone names mapping in ReadyPlayerMe
    # Hips, Spine, Spine1, Spine2, Neck, Head
    # LeftShoulder, LeftArm, LeftForeArm, LeftHand
    # RightShoulder, RightArm, RightForeArm, RightHand
    # LeftUpLeg, LeftLeg, LeftFoot, LeftToeBase
    # RightUpLeg, RightLeg, RightFoot, RightToeBase
    
    for frame in range(1, 241):
        bpy.context.scene.frame_set(frame)
        t = (frame / 240.0) * math.pi * 2 # 8s full cycle
        # Music beat: 120 BPM = 2 beats per second = 16 beats per 8s
        beat_t = (frame / 30.0) * math.pi * 4.0 
        
        # 1. HIPS & PELVIS KINETICS
        # Figure-8 sway + rhythmic vertical bounce
        hips = armature.pose.bones.get('Hips')
        if hips:
            hips.location.x = math.sin(t * 2.0) * 0.045
            hips.location.y = math.cos(t * 2.0) * 0.020
            # Dip down on each beat (nhún chân)
            hips.location.z = -abs(math.sin(beat_t * 0.5)) * 0.035
            hips.rotation_euler.z = math.sin(t * 2.0) * 0.08
            hips.rotation_euler.y = math.cos(t * 2.0) * 0.05
            hips.rotation_euler.x = math.sin(beat_t * 0.5) * 0.04
            hips.keyframe_insert(data_path="location", frame=frame)
            hips.keyframe_insert(data_path="rotation_euler", frame=frame)

        # 2. LEGS & KNEES ARTICULATION (CHÂN & ĐẦU GỐI)
        # Dynamic knee flexing & weight shifting (KHÔNG CÒN CỨNG ĐƠ!)
        l_upleg = armature.pose.bones.get('LeftUpLeg')
        l_leg = armature.pose.bones.get('LeftLeg')
        l_foot = armature.pose.bones.get('LeftFoot')
        
        r_upleg = armature.pose.bones.get('RightUpLeg')
        r_leg = armature.pose.bones.get('RightLeg')
        r_foot = armature.pose.bones.get('RightFoot')
        
        weight_left = math.sin(t * 2.0) # > 0 means weight on left leg
        
        if l_upleg and l_leg:
            # Left leg flexes and shifts
            knee_flex_L = 0.15 + 0.25 * max(0.0, math.sin(beat_t * 0.5))
            l_upleg.rotation_euler.x = -knee_flex_L * 0.6 + (0.08 if weight_left < 0 else -0.04)
            l_upleg.rotation_euler.z = -0.05 + math.sin(t * 2.0) * 0.04
            l_leg.rotation_euler.x = knee_flex_L * 1.1 # KNEE BEND!
            l_upleg.keyframe_insert(data_path="rotation_euler", frame=frame)
            l_leg.keyframe_insert(data_path="rotation_euler", frame=frame)
            if l_foot:
                l_foot.rotation_euler.x = -knee_flex_L * 0.5
                l_foot.keyframe_insert(data_path="rotation_euler", frame=frame)
                
        if r_upleg and r_leg:
            # Right leg flexes counter-synchronously
            knee_flex_R = 0.15 + 0.25 * max(0.0, -math.sin(beat_t * 0.5))
            r_upleg.rotation_euler.x = -knee_flex_R * 0.6 + (0.08 if weight_left > 0 else -0.04)
            r_upleg.rotation_euler.z = 0.05 + math.sin(t * 2.0) * 0.04
            r_leg.rotation_euler.x = knee_flex_R * 1.1 # KNEE BEND!
            r_upleg.keyframe_insert(data_path="rotation_euler", frame=frame)
            r_leg.keyframe_insert(data_path="rotation_euler", frame=frame)
            if r_foot:
                r_foot.rotation_euler.x = -knee_flex_R * 0.5
                r_foot.keyframe_insert(data_path="rotation_euler", frame=frame)

        # 3. SPINE & CHEST (THÂN MÌNH & LỒNG NGỰC)
        spine = armature.pose.bones.get('Spine')
        spine1 = armature.pose.bones.get('Spine1')
        spine2 = armature.pose.bones.get('Spine2')
        if spine:
            spine.rotation_euler.y = -math.sin(t * 2.0) * 0.06
            spine.rotation_euler.x = math.sin(beat_t * 0.5) * 0.03
            spine.keyframe_insert(data_path="rotation_euler", frame=frame)
        if spine2:
            # Chest breathing & posture arching
            spine2.rotation_euler.x = math.sin(beat_t * 0.25) * 0.05 + 0.02
            spine2.rotation_euler.y = -math.sin(t * 2.0) * 0.04
            spine2.keyframe_insert(data_path="rotation_euler", frame=frame)

        # 4. HEAD & NECK (CỔ & ĐẦU)
        head = armature.pose.bones.get('Head')
        neck = armature.pose.bones.get('Neck')
        if head:
            head.rotation_euler.x = math.sin(beat_t * 0.5) * 0.06 - 0.02
            head.rotation_euler.y = math.sin(t * 2.0) * 0.12
            head.rotation_euler.z = math.cos(t * 2.0) * 0.06
            head.keyframe_insert(data_path="rotation_euler", frame=frame)
        if neck:
            neck.rotation_euler.y = math.sin(t * 2.0) * 0.04
            neck.keyframe_insert(data_path="rotation_euler", frame=frame)

        # 5. RIGHT ARM & FOREARM - DYNAMIC MICROPHONE PERFORMANCE (TAY PHẢI CẦM MIC)
        r_shoulder = armature.pose.bones.get('RightShoulder')
        r_arm = armature.pose.bones.get('RightArm')
        r_forearm = armature.pose.bones.get('RightForeArm')
        r_hand = armature.pose.bones.get('RightHand')
        
        if r_arm and r_forearm:
            # Upper Arm lifts forward and inwards towards chest
            r_arm.rotation_euler.x = -0.65 + math.sin(t * 2.0) * 0.08
            r_arm.rotation_euler.y = 0.25
            r_arm.rotation_euler.z = -0.45 + math.sin(beat_t * 0.5) * 0.04
            
            # ForeArm (Elbow): DEEPLY BENT bringing hand with mic right to mouth!
            r_forearm.rotation_euler.x = -1.25 + math.sin(beat_t * 0.5) * 0.12
            r_forearm.rotation_euler.y = -0.35
            r_forearm.rotation_euler.z = 0.20
            
            r_arm.keyframe_insert(data_path="rotation_euler", frame=frame)
            r_forearm.keyframe_insert(data_path="rotation_euler", frame=frame)
            
            if r_hand:
                r_hand.rotation_euler.x = 0.35 + math.sin(beat_t * 0.5) * 0.08
                r_hand.rotation_euler.z = 0.15
                r_hand.keyframe_insert(data_path="rotation_euler", frame=frame)

        # 6. LEFT ARM & FOREARM - EXPRESSIVE LYRICAL GESTURES (TAY TRÁI DIỄN CẢM)
        l_shoulder = armature.pose.bones.get('LeftShoulder')
        l_arm = armature.pose.bones.get('LeftArm')
        l_forearm = armature.pose.bones.get('LeftForeArm')
        l_hand = armature.pose.bones.get('LeftHand')
        
        if l_arm and l_forearm:
            # Gesture cycle: opens arm outwards -> rises high -> pulls softly to heart
            gesture_phase = (frame % 120) / 120.0 * math.pi * 2
            
            # Upper arm smooth sweeping
            l_arm.rotation_euler.x = 0.35 + math.sin(gesture_phase) * 0.25
            l_arm.rotation_euler.y = -0.15
            l_arm.rotation_euler.z = 0.45 + math.cos(gesture_phase) * 0.20
            
            # Forearm (Elbow) actively articulating (gập và duỗi mềm mại!)
            l_forearm.rotation_euler.x = -0.55 - abs(math.sin(gesture_phase)) * 0.45
            l_forearm.rotation_euler.y = 0.25
            
            l_arm.keyframe_insert(data_path="rotation_euler", frame=frame)
            l_forearm.keyframe_insert(data_path="rotation_euler", frame=frame)
            
            if l_hand:
                # Wrist & fingers articulating with music
                l_hand.rotation_euler.x = math.sin(gesture_phase * 2) * 0.20
                l_hand.rotation_euler.y = math.cos(gesture_phase) * 0.15
                l_hand.rotation_euler.z = -0.20
                l_hand.keyframe_insert(data_path="rotation_euler", frame=frame)

    bpy.ops.object.mode_set(mode='OBJECT')

    # Animate Facial Shape Keys (LipSync & Smile)
    for obj in bpy.data.objects:
        if obj.type == 'MESH' and obj.data.shape_keys:
            kb = obj.data.shape_keys.key_blocks
            obj.data.shape_keys.animation_data_create()
            
            for frame in range(1, 241):
                beat_t = (frame / 30.0) * math.pi * 4.0
                open_val = max(0.0, math.sin(beat_t * 0.75)) * 0.95
                smile_val = 0.35 + 0.25 * math.sin((frame / 240.0) * math.pi * 2)
                
                if 'mouthOpen' in kb:
                    kb['mouthOpen'].value = open_val
                    kb['mouthOpen'].keyframe_insert(data_path="value", frame=frame)
                if 'mouthSmile' in kb:
                    kb['mouthSmile'].value = smile_val
                    kb['mouthSmile'].keyframe_insert(data_path="value", frame=frame)

    # Export all files for Model A
    bpy.ops.export_scene.gltf(
        filepath=f"{out_dir}/female_singer_pro_stage.glb",
        export_format='GLB',
        export_animations=True,
        export_morph=True,
        export_skins=True
    )
    bpy.ops.export_scene.fbx(
        filepath=f"{out_dir}/female_singer_pro_stage.fbx",
        bake_anim=True,
        bake_anim_use_all_actions=True,
        use_mesh_modifiers=True,
        add_leaf_bones=False
    )
    bpy.ops.wm.save_as_mainfile(filepath=f"{out_dir}/female_singer_pro_stage.blend")
    print(">>> Model A Full-Body Articulated Choreography Exported Successfully!")


# -------------------------------------------------------------------------
# GENERATE FULL-BODY ARTICULATED SINGER CHOREOGRAPHY FOR MODEL B (ANIME IDOL)
# -------------------------------------------------------------------------
def generate_full_body_model_B():
    print(">>> Generating Full-Body Articulated Dance & Singing for Model B (Anime Idol)...")
    clean_scene()
    
    input_glb = '/Volumes/DATA/ctg_ai/3d/phuong_an_B_anime_idol_female_singer/model/female_singer_anime_idol.glb'
    out_dir = '/Volumes/DATA/ctg_ai/3d/phuong_an_nang_cao_nu_ca_si_pro_stage/model'
    
    bpy.ops.import_scene.gltf(filepath=input_glb)
    
    bpy.context.scene.render.fps = 30
    bpy.context.scene.frame_start = 1
    bpy.context.scene.frame_end = 240
    
    armature = None
    for obj in bpy.data.objects:
        if obj.type == 'ARMATURE':
            armature = obj
            break
            
    if not armature:
        print("Error: Armature not found in Model B!")
        return

    bpy.context.view_layer.objects.active = armature
    armature.animation_data_create()
    
    action = bpy.data.actions.new(name="Pro_Idol_FullBody_JPop_Dance")
    armature.animation_data.action = action
    
    bpy.ops.object.mode_set(mode='POSE')
    
    for frame in range(1, 241):
        bpy.context.scene.frame_set(frame)
        t = (frame / 240.0) * math.pi * 2
        # J-Pop Tempo 130 BPM
        beat_t = (frame / 30.0) * math.pi * 4.33
        
        # 1. HIPS: J-Pop Bouncy Pop Steps
        hips = armature.pose.bones.get('J_Bip_C_Hips')
        if hips:
            hips.location.x = math.sin(beat_t * 0.5) * 0.05
            hips.location.z = -abs(math.sin(beat_t)) * 0.03 # Deep Energetic Bounce!
            hips.rotation_euler.z = math.sin(beat_t * 0.5) * 0.10
            hips.rotation_euler.y = math.cos(beat_t * 0.5) * 0.06
            hips.rotation_euler.x = math.sin(beat_t) * 0.05
            hips.keyframe_insert(data_path="location", frame=frame)
            hips.keyframe_insert(data_path="rotation_euler", frame=frame)

        # 2. LEGS & KNEES (CHÂN & ĐẦU GỐI NHÚN NHẢY IDOL)
        l_up = armature.pose.bones.get('J_Bip_L_UpperLeg')
        l_low = armature.pose.bones.get('J_Bip_L_LowerLeg')
        l_ft = armature.pose.bones.get('J_Bip_L_Foot')
        
        r_up = armature.pose.bones.get('J_Bip_R_UpperLeg')
        r_low = armature.pose.bones.get('J_Bip_R_LowerLeg')
        r_ft = armature.pose.bones.get('J_Bip_R_Foot')
        
        k_flex_L = 0.15 + 0.30 * max(0.0, math.sin(beat_t * 0.5))
        k_flex_R = 0.15 + 0.30 * max(0.0, -math.sin(beat_t * 0.5))
        
        if l_up and l_low:
            l_up.rotation_euler.x = -k_flex_L * 0.6
            l_low.rotation_euler.x = k_flex_L * 1.2 # KNEE FLEXION!
            l_up.keyframe_insert(data_path="rotation_euler", frame=frame)
            l_low.keyframe_insert(data_path="rotation_euler", frame=frame)
            if l_ft:
                l_ft.rotation_euler.x = -k_flex_L * 0.5
                l_ft.keyframe_insert(data_path="rotation_euler", frame=frame)
                
        if r_up and r_low:
            r_up.rotation_euler.x = -k_flex_R * 0.6
            r_low.rotation_euler.x = k_flex_R * 1.2 # KNEE FLEXION!
            r_up.keyframe_insert(data_path="rotation_euler", frame=frame)
            r_low.keyframe_insert(data_path="rotation_euler", frame=frame)
            if r_ft:
                r_ft.rotation_euler.x = -k_flex_R * 0.5
                r_ft.keyframe_insert(data_path="rotation_euler", frame=frame)

        # 3. SPINE & HEAD
        head = armature.pose.bones.get('J_Bip_C_Head')
        spine = armature.pose.bones.get('J_Bip_C_Spine')
        if head:
            head.rotation_euler.x = math.sin(beat_t) * 0.08
            head.rotation_euler.y = math.sin(beat_t * 0.5) * 0.14
            head.rotation_euler.z = math.cos(beat_t * 0.5) * 0.08
            head.keyframe_insert(data_path="rotation_euler", frame=frame)
        if spine:
            spine.rotation_euler.y = -math.sin(beat_t * 0.5) * 0.06
            spine.keyframe_insert(data_path="rotation_euler", frame=frame)

        # 4. ARMS: IDOL CHOREOGRAPHY (TAY CẦM MIC & TAY TẠO DÁNG IDOL)
        r_arm = armature.pose.bones.get('J_Bip_R_UpperArm')
        r_fore = armature.pose.bones.get('J_Bip_R_LowerArm')
        r_hand = armature.pose.bones.get('J_Bip_R_Hand')
        
        l_arm = armature.pose.bones.get('J_Bip_L_UpperArm')
        l_fore = armature.pose.bones.get('J_Bip_L_LowerArm')
        l_hand = armature.pose.bones.get('J_Bip_L_Hand')
        
        if r_arm and r_fore:
            # Right arm holds microphone at mouth
            r_arm.rotation_euler.x = -0.70 + math.sin(beat_t * 0.5) * 0.08
            r_arm.rotation_euler.y = 0.30
            r_arm.rotation_euler.z = -0.40
            
            # Forearm bent bringing hand to face
            r_fore.rotation_euler.x = -1.35 + math.sin(beat_t) * 0.10
            r_fore.rotation_euler.y = -0.40
            
            r_arm.keyframe_insert(data_path="rotation_euler", frame=frame)
            r_fore.keyframe_insert(data_path="rotation_euler", frame=frame)
            if r_hand:
                r_hand.rotation_euler.x = 0.40
                r_hand.keyframe_insert(data_path="rotation_euler", frame=frame)
                
        if l_arm and l_fore:
            # Left arm: Dynamic idol hand poses (pointing, heart gesture, wave)
            idol_cycle = (frame % 80) / 80.0 * math.pi * 2
            l_arm.rotation_euler.x = 0.40 + math.sin(idol_cycle) * 0.30
            l_arm.rotation_euler.y = -0.20
            l_arm.rotation_euler.z = 0.50 + math.cos(idol_cycle) * 0.25
            
            l_fore.rotation_euler.x = -0.65 - abs(math.sin(idol_cycle)) * 0.50
            
            l_arm.keyframe_insert(data_path="rotation_euler", frame=frame)
            l_fore.keyframe_insert(data_path="rotation_euler", frame=frame)
            if l_hand:
                l_hand.rotation_euler.z = -0.30 + math.sin(idol_cycle * 2) * 0.20
                l_hand.keyframe_insert(data_path="rotation_euler", frame=frame)

        # 5. TWIN-TAILS HAIR PHYSICS MOTION
        for pbone in armature.pose.bones:
            if 'Hair' in pbone.name:
                pbone.rotation_euler.x = -math.sin(beat_t) * 0.08
                pbone.rotation_euler.z = -math.sin(beat_t * 0.5) * 0.10
                pbone.keyframe_insert(data_path="rotation_euler", frame=frame)

    bpy.ops.object.mode_set(mode='OBJECT')

    # Animate Shape Keys
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

    # Export all files for Model B
    bpy.ops.export_scene.gltf(
        filepath=f"{out_dir}/female_singer_anime_pro.glb",
        export_format='GLB',
        export_animations=True,
        export_morph=True,
        export_skins=True
    )
    bpy.ops.export_scene.fbx(
        filepath=f"{out_dir}/female_singer_anime_pro.fbx",
        bake_anim=True,
        bake_anim_use_all_actions=True,
        use_mesh_modifiers=True,
        add_leaf_bones=False
    )
    bpy.ops.wm.save_as_mainfile(filepath=f"{out_dir}/female_singer_anime_pro.blend")
    print(">>> Model B Full-Body Articulated Choreography Exported Successfully!")


if __name__ == '__main__':
    generate_full_body_model_A()
    generate_full_body_model_B()
    print("=== FULL-BODY ARTICULATED SINGER DANCE COMPLETED! ===")
