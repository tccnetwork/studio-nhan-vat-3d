import bpy
import math

def clean_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)

def process_model_A():
    print("=== Processing Model A (Realistic Female Singer) ===")
    clean_scene()
    
    input_glb = '/Volumes/DATA/ctg_ai/3d/phuong_an_A_realistic_female_singer/model/female_singer_realistic.glb'
    out_dir = '/Volumes/DATA/ctg_ai/3d/phuong_an_A_realistic_female_singer/model'
    
    bpy.ops.import_scene.gltf(filepath=input_glb)
    
    # Set Scene FPS & Frame Range
    bpy.context.scene.render.fps = 30
    bpy.context.scene.frame_start = 1
    bpy.context.scene.frame_end = 120 # 4 seconds loop
    
    # 1. Animate Armature (Singing / Performance Swaying)
    armature = None
    for obj in bpy.data.objects:
        if obj.type == 'ARMATURE':
            armature = obj
            break
            
    if armature:
        bpy.context.view_layer.objects.active = armature
        armature.animation_data_create()
        action = bpy.data.actions.new(name="Realistic_Singing_Performance")
        armature.animation_data.action = action
        
        bpy.ops.object.mode_set(mode='POSE')
        
        # Keyframe natural singing motion on bones
        for frame in range(1, 121):
            bpy.context.scene.frame_set(frame)
            t = (frame / 120.0) * math.pi * 2
            
            for pbone in armature.pose.bones:
                name = pbone.name.lower()
                if 'hips' in name:
                    pbone.location.x = math.sin(t * 2) * 0.02
                    pbone.location.z = math.sin(t * 4) * 0.008
                    pbone.rotation_euler.z = math.sin(t * 2) * 0.04
                    pbone.keyframe_insert(data_path="location", frame=frame)
                    pbone.keyframe_insert(data_path="rotation_euler", frame=frame)
                elif 'spine' in name or 'chest' in name:
                    pbone.rotation_euler.y = math.sin(t * 2) * 0.03
                    pbone.rotation_euler.x = math.sin(t * 4) * 0.02 # breathing
                    pbone.keyframe_insert(data_path="rotation_euler", frame=frame)
                elif 'head' in name:
                    pbone.rotation_euler.x = math.sin(t * 4) * 0.05
                    pbone.rotation_euler.y = math.sin(t * 2) * 0.08
                    pbone.rotation_euler.z = math.cos(t * 2) * 0.04
                    pbone.keyframe_insert(data_path="rotation_euler", frame=frame)
                elif 'rightarm' in name or 'right_arm' in name or 'arm_r' in name:
                    # Bring hand towards chest (holding microphone)
                    pbone.rotation_euler.x = -0.4 + math.sin(t * 2) * 0.05
                    pbone.rotation_euler.z = -0.3
                    pbone.keyframe_insert(data_path="rotation_euler", frame=frame)
                elif 'leftarm' in name or 'left_arm' in name or 'arm_l' in name:
                    # Gentle performance gesture
                    pbone.rotation_euler.x = 0.15 + math.sin(t * 2) * 0.08
                    pbone.rotation_euler.z = 0.35
                    pbone.keyframe_insert(data_path="rotation_euler", frame=frame)
        
        bpy.ops.object.mode_set(mode='OBJECT')

    # 2. Animate Shape Keys (Lip-Sync Mouth Opening & Smiling)
    for obj in bpy.data.objects:
        if obj.type == 'MESH' and obj.data.shape_keys:
            key_blocks = obj.data.shape_keys.key_blocks
            obj.data.shape_keys.animation_data_create()
            
            for frame in range(1, 121):
                t = (frame / 120.0) * math.pi * 2
                open_val = max(0.0, math.sin(t * 8.0)) * 0.95
                smile_val = 0.3 + 0.3 * math.sin(t * 2.0)
                
                if 'mouthOpen' in key_blocks:
                    key_blocks['mouthOpen'].value = open_val
                    key_blocks['mouthOpen'].keyframe_insert(data_path="value", frame=frame)
                if 'mouthSmile' in key_blocks:
                    key_blocks['mouthSmile'].value = smile_val
                    key_blocks['mouthSmile'].keyframe_insert(data_path="value", frame=frame)

    # 3. Export .glb
    glb_out = f"{out_dir}/female_singer_realistic.glb"
    bpy.ops.export_scene.gltf(
        filepath=glb_out,
        export_format='GLB',
        export_animations=True,
        export_morph=True,
        export_skins=True
    )
    print(f"Exported GLB: {glb_out}")

    # 4. Export .fbx
    fbx_out = f"{out_dir}/female_singer_realistic.fbx"
    bpy.ops.export_scene.fbx(
        filepath=fbx_out,
        bake_anim=True,
        bake_anim_use_all_actions=True,
        use_mesh_modifiers=True,
        add_leaf_bones=False
    )
    print(f"Exported FBX: {fbx_out}")

    # 5. Save .blend
    blend_out = f"{out_dir}/female_singer_realistic.blend"
    bpy.ops.wm.save_as_mainfile(filepath=blend_out)
    print(f"Saved Blend: {blend_out}")


def process_model_B():
    print("=== Processing Model B (Anime 3D Idol Singer) ===")
    clean_scene()
    
    input_glb = '/Volumes/DATA/ctg_ai/3d/phuong_an_B_anime_idol_female_singer/model/female_singer_anime_idol.glb'
    out_dir = '/Volumes/DATA/ctg_ai/3d/phuong_an_B_anime_idol_female_singer/model'
    
    bpy.ops.import_scene.gltf(filepath=input_glb)
    
    bpy.context.scene.render.fps = 30
    bpy.context.scene.frame_start = 1
    bpy.context.scene.frame_end = 120
    
    # 1. Animate Armature (J-Pop 130 BPM Idol Performance)
    armature = None
    for obj in bpy.data.objects:
        if obj.type == 'ARMATURE':
            armature = obj
            break
            
    if armature:
        bpy.context.view_layer.objects.active = armature
        armature.animation_data_create()
        action = bpy.data.actions.new(name="Anime_Idol_JPop_Performance")
        armature.animation_data.action = action
        
        bpy.ops.object.mode_set(mode='POSE')
        
        for frame in range(1, 121):
            bpy.context.scene.frame_set(frame)
            t = (frame / 120.0) * math.pi * 2
            
            for pbone in armature.pose.bones:
                name = pbone.name
                if 'Hips' in name:
                    pbone.location.x = math.sin(t * 2) * 0.025
                    pbone.location.z = abs(math.sin(t * 4)) * 0.015
                    pbone.rotation_euler.z = math.sin(t * 2) * 0.05
                    pbone.keyframe_insert(data_path="location", frame=frame)
                    pbone.keyframe_insert(data_path="rotation_euler", frame=frame)
                elif 'Head' in name and 'end' not in name:
                    pbone.rotation_euler.x = math.sin(t * 4) * 0.06
                    pbone.rotation_euler.y = math.sin(t * 2) * 0.10
                    pbone.rotation_euler.z = math.cos(t * 2) * 0.05
                    pbone.keyframe_insert(data_path="rotation_euler", frame=frame)
        
        bpy.ops.object.mode_set(mode='OBJECT')

    # 2. Animate Shape Keys (A, I, U, E, O + Joy + Wink)
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
        
        for frame in range(1, 121):
            cycle_idx = int((frame / 24.0)) % 5
            mouth_open = max(0.0, math.sin((frame / 120.0) * math.pi * 10.0)) * 0.95
            is_wink = (35 <= frame <= 45) or (95 <= frame <= 105)
            
            for i, v_name in enumerate(vowels):
                if v_name in kb:
                    val = mouth_open if i == cycle_idx else 0.0
                    kb[v_name].value = val
                    kb[v_name].keyframe_insert(data_path="value", frame=frame)
                    
            if 'Face_Blendshape.Fcl_ALL_Joy' in kb:
                kb['Face_Blendshape.Fcl_ALL_Joy'].value = 0.4 + 0.3 * math.sin((frame / 120.0) * math.pi * 4.0)
                kb['Face_Blendshape.Fcl_ALL_Joy'].keyframe_insert(data_path="value", frame=frame)
                
            if 'Face_Blendshape.Fcl_EYE_Close_L' in kb:
                kb['Face_Blendshape.Fcl_EYE_Close_L'].value = 1.0 if is_wink else 0.0
                kb['Face_Blendshape.Fcl_EYE_Close_L'].keyframe_insert(data_path="value", frame=frame)

    # 3. Export .glb
    glb_out = f"{out_dir}/female_singer_anime_idol.glb"
    bpy.ops.export_scene.gltf(
        filepath=glb_out,
        export_format='GLB',
        export_animations=True,
        export_morph=True,
        export_skins=True
    )
    print(f"Exported GLB: {glb_out}")

    # 4. Export .fbx
    fbx_out = f"{out_dir}/female_singer_anime_idol.fbx"
    bpy.ops.export_scene.fbx(
        filepath=fbx_out,
        bake_anim=True,
        bake_anim_use_all_actions=True,
        use_mesh_modifiers=True,
        add_leaf_bones=False
    )
    print(f"Exported FBX: {fbx_out}")

    # 5. Save .blend
    blend_out = f"{out_dir}/female_singer_anime_idol.blend"
    bpy.ops.wm.save_as_mainfile(filepath=blend_out)
    print(f"Saved Blend: {blend_out}")


if __name__ == '__main__':
    process_model_A()
    process_model_B()
    print("ALL EXPORTS COMPLETED SUCCESSFULLY!")
