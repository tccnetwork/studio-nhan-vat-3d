import bpy
import math

def clean_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)

def create_pro_singer_animations_A():
    print("=== Creating Pro Singer Choreography for Realistic Singer (Model A) ===")
    clean_scene()
    
    input_glb = '/Volumes/DATA/ctg_ai/3d/phuong_an_A_realistic_female_singer/model/female_singer_realistic.glb'
    out_dir = '/Volumes/DATA/ctg_ai/3d/phuong_an_nang_cao_nu_ca_si_pro_stage/model'
    
    bpy.ops.import_scene.gltf(filepath=input_glb)
    
    bpy.context.scene.render.fps = 30
    bpy.context.scene.frame_start = 1
    bpy.context.scene.frame_end = 240 # 8 seconds rich choreography
    
    armature = None
    for obj in bpy.data.objects:
        if obj.type == 'ARMATURE':
            armature = obj
            break
            
    if not armature:
        print("Error: No armature found in Model A")
        return

    bpy.context.view_layer.objects.active = armature
    armature.animation_data_create()
    
    # ----------------------------------------------------
    # ACTION 1: Live_Pop_Vocal_Performance (Phiêu Theo Giọng Hát)
    # ----------------------------------------------------
    action1 = bpy.data.actions.new(name="01_Live_Pop_Vocal_Performance")
    armature.animation_data.action = action1
    bpy.ops.object.mode_set(mode='POSE')
    
    for frame in range(1, 241):
        bpy.context.scene.frame_set(frame)
        t = (frame / 240.0) * math.pi * 2 # 1 full 8-second cycle
        beat_t = (frame / 30.0) * math.pi * 2 # 1Hz rhythm beat
        
        for pbone in armature.pose.bones:
            name = pbone.name.lower()
            
            # Hips / Pelvis: Weight shift & rhythmic stepping
            if 'hips' in name:
                pbone.location.x = math.sin(t * 2) * 0.035
                pbone.location.y = math.cos(t * 2) * 0.015
                pbone.location.z = (abs(math.sin(beat_t * 1.5)) * 0.012)
                pbone.rotation_euler.z = math.sin(t * 2) * 0.06
                pbone.rotation_euler.y = math.cos(t * 2) * 0.03
                pbone.keyframe_insert(data_path="location", frame=frame)
                pbone.keyframe_insert(data_path="rotation_euler", frame=frame)
                
            # Spine / Chest: Emotional breathing & vocal projection arching
            elif 'spine' in name or 'chest' in name:
                pbone.rotation_euler.x = math.sin(beat_t) * 0.035 + (0.04 if 60 <= frame <= 140 else 0.0)
                pbone.rotation_euler.y = -math.sin(t * 2) * 0.04
                pbone.rotation_euler.z = math.sin(t * 2) * 0.02
                pbone.keyframe_insert(data_path="rotation_euler", frame=frame)
                
            # Head / Neck: Tilting into microphone, looking up at high notes (frames 80-140)
            elif 'head' in name and 'end' not in name:
                is_high_note = (70 <= frame <= 140)
                pbone.rotation_euler.x = (-0.08 if is_high_note else math.sin(beat_t * 1.2) * 0.05)
                pbone.rotation_euler.y = math.sin(t * 2) * 0.12
                pbone.rotation_euler.z = math.cos(t * 2) * 0.06
                pbone.keyframe_insert(data_path="rotation_euler", frame=frame)
                
            # Right Arm: Holding Stage Mic (Raises close to mouth when singing)
            elif 'rightarm' in name or 'right_arm' in name or 'arm_r' in name:
                is_high_note = (70 <= frame <= 140)
                pbone.rotation_euler.x = (-0.65 if is_high_note else -0.42 + math.sin(t * 2) * 0.06)
                pbone.rotation_euler.y = 0.25
                pbone.rotation_euler.z = -0.32 + math.sin(beat_t) * 0.04
                pbone.keyframe_insert(data_path="rotation_euler", frame=frame)
                
            # Left Arm: Emotional Expressive Hand Gestures (Storytelling & Audience Interaction)
            elif 'leftarm' in name or 'left_arm' in name or 'arm_l' in name:
                if frame < 80:
                    # Palm open towards audience
                    pbone.rotation_euler.x = 0.35 + math.sin(t * 4) * 0.10
                    pbone.rotation_euler.z = 0.45 + math.cos(t * 4) * 0.08
                elif frame <= 150:
                    # Hand raised high for dramatic climax
                    pbone.rotation_euler.x = 0.75 + math.sin(t * 2) * 0.08
                    pbone.rotation_euler.z = 0.65
                else:
                    # Hand gently returning to heart/chest
                    pbone.rotation_euler.x = 0.20 + math.sin(t * 2) * 0.05
                    pbone.rotation_euler.z = 0.30
                pbone.keyframe_insert(data_path="rotation_euler", frame=frame)

    bpy.ops.object.mode_set(mode='OBJECT')

    # Animate Shape Keys for Realistic Singer
    for obj in bpy.data.objects:
        if obj.type == 'MESH' and obj.data.shape_keys:
            kb = obj.data.shape_keys.key_blocks
            obj.data.shape_keys.animation_data_create()
            
            for frame in range(1, 241):
                t = (frame / 240.0) * math.pi * 2
                beat_t = (frame / 30.0) * math.pi * 2
                
                # Big jaw drop during climax (frames 70-140)
                if 70 <= frame <= 140:
                    open_val = 0.7 + 0.3 * math.sin(beat_t * 3.0)
                    smile_val = 0.5 + 0.2 * math.sin(beat_t)
                else:
                    open_val = max(0.0, math.sin(beat_t * 2.5)) * 0.85
                    smile_val = 0.3 + 0.3 * math.sin(t * 2.0)
                    
                if 'mouthOpen' in kb:
                    kb['mouthOpen'].value = open_val
                    kb['mouthOpen'].keyframe_insert(data_path="value", frame=frame)
                if 'mouthSmile' in kb:
                    kb['mouthSmile'].value = smile_val
                    kb['mouthSmile'].keyframe_insert(data_path="value", frame=frame)

    # Export formats
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
    print("Exported Pro Singer Model A successfully!")


def create_pro_singer_animations_B():
    print("=== Creating Pro Idol Dance Choreography for Anime Singer (Model B) ===")
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
        print("Error: No armature found in Model B")
        return

    bpy.context.view_layer.objects.active = armature
    armature.animation_data_create()
    
    # ----------------------------------------------------
    # ACTION 1: KPop_JPop_Idol_Dance_Choreography
    # ----------------------------------------------------
    action1 = bpy.data.actions.new(name="01_Idol_Stage_Dance_Choreography")
    armature.animation_data.action = action1
    bpy.ops.object.mode_set(mode='POSE')
    
    for frame in range(1, 241):
        bpy.context.scene.frame_set(frame)
        t = (frame / 240.0) * math.pi * 2
        # 128 BPM Tempo (approx 2.13 beats/sec)
        beat_t = (frame / 30.0) * math.pi * 4.26
        
        for pbone in armature.pose.bones:
            name = pbone.name
            
            # Hips: Dynamic J-Pop Bounce & Side-to-Side Pop Steps
            if 'Hips' in name:
                pbone.location.x = math.sin(beat_t * 0.5) * 0.04
                pbone.location.z = abs(math.sin(beat_t)) * 0.02 # energetic bounce
                pbone.rotation_euler.z = math.sin(beat_t * 0.5) * 0.08
                pbone.rotation_euler.y = math.cos(beat_t * 0.5) * 0.05
                pbone.keyframe_insert(data_path="location", frame=frame)
                pbone.keyframe_insert(data_path="rotation_euler", frame=frame)
                
            # Head: Bouncy Idol nod & energetic angle tilts
            elif 'Head' in name and 'end' not in name:
                pbone.rotation_euler.x = math.sin(beat_t) * 0.08
                pbone.rotation_euler.y = math.sin(beat_t * 0.5) * 0.14
                pbone.rotation_euler.z = math.cos(beat_t * 0.5) * 0.08
                pbone.keyframe_insert(data_path="rotation_euler", frame=frame)
                
            # Hair physics secondary motion: Twin-tails swing with dance beats
            elif 'Hair' in name:
                pbone.rotation_euler.x = -math.sin(beat_t) * 0.05
                pbone.rotation_euler.z = -math.sin(beat_t * 0.5) * 0.06
                pbone.keyframe_insert(data_path="rotation_euler", frame=frame)

    bpy.ops.object.mode_set(mode='OBJECT')

    # Animate Shape Keys (A-I-U-E-O, Joy, Wink)
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

    # Export formats
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
    print("Exported Pro Anime Idol Model B successfully!")


if __name__ == '__main__':
    create_pro_singer_animations_A()
    create_pro_singer_animations_B()
    print("=== ALL PRO SINGER DANCE EXPORTS COMPLETED! ===")
