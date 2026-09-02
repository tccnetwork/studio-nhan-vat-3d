import bpy
import math
import mathutils
import bmesh
import argparse
import os
import re
import sys

# Thư mục gốc dự án, suy ra từ vị trí file này (scripts/build_character.py).
# Blender chạy script qua Text Editor thì không có __file__, nên có đường lui.
try:
    ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
except NameError:
    ROOT = '/Volumes/DATA/ctg_ai/3d'
SOURCE_DIR = os.path.join(ROOT, 'source')   # model nguồn — chỉ đọc
BUILD_DIR = os.path.join(ROOT, 'build')     # kết quả dựng — ghi đè thoải mái

sys.path.insert(0, os.path.join(ROOT, 'scripts'))
import hairstyles
import manifest
import states


def parse_args():
    """Tham số đặt sau dấu -- trên dòng lệnh Blender.

        blender --background --python scripts/build_character.py -- --states 04_BuocDi_CoBan

    Dựng đủ 14 trạng thái mất khoảng 10 phút, trong đó riêng bake chiếm 7 phút.
    Chọn một trạng thái thì chỉ còn khoảng một phút, đủ nhanh để thử đi thử lại.
    """
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    ap = argparse.ArgumentParser(prog='build_character.py')
    ap.add_argument('--states', default=None,
                    help='danh sách clip cách nhau bằng dấu phẩy; bỏ trống = dựng tất cả')
    ap.add_argument('--fast', action='store_true',
                    help='chỉ xuất GLB, bỏ qua FBX và blend (tiết kiệm ~90 giây)')
    ap.add_argument('--list', action='store_true',
                    help='in danh sách trạng thái rồi thoát')
    return ap.parse_args(argv)

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

def build_character(wanted_states=None, fast=False):
    partial = bool(wanted_states)
    print(">>> Nạp model nguồn" + (f" — chỉ dựng: {', '.join(wanted_states)}" if partial else ""))
    clean_scene()
    
    # source/ chỉ đọc, build/ chỉ ghi. Trước Giai đoạn 0 hai đường dẫn này
    # trỏ vào cùng một file, nên mỗi lần chạy lại là một lần chồng thêm bản
    # sao kiểu tóc lên model — đến khi phát hiện thì đã có 6 bản thừa.
    input_glb = os.path.join(SOURCE_DIR, 'female_singer_anime_idol_base.glb')
    # Dựng thiếu trạng thái thì không được ghi đè lên bản chính thức: kết quả
    # đó không khớp danh mục và sẽ làm verify_build.py báo lỗi nhầm.
    out_b_dir = os.path.join(BUILD_DIR, 'preview') if partial else BUILD_DIR

    if os.path.commonpath([os.path.abspath(input_glb), os.path.abspath(out_b_dir)]) \
            == os.path.abspath(SOURCE_DIR):
        raise RuntimeError('Đầu ra đang trỏ vào source/ — dừng để không ghi đè model nguồn.')
    os.makedirs(out_b_dir, exist_ok=True)
    
    
    # Import Character
    bpy.ops.import_scene.gltf(filepath=input_glb)
    char_arm = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
    char_arm.name = 'Character_Armature'
    
    # Purge old actions
    for a in list(bpy.data.actions):
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

    # Dọn vết tích của những vòng nhập/xuất glTF lặp lại. Mỗi vòng để lại một
    # object rỗng mang tên trùng với lưới, nên model đã tích được 44 cái tên
    # Face … Face.042 trước khi lưới thật phải lùi xuống thành "Face.043".
    # Chúng chiếm chỗ trong danh sách node của file xuất và chặn việc đặt lại
    # tên cho lưới thật.
    strip = lambda n: re.sub(r'\.\d{3}$', '', n)
    mesh_bases = {strip(o.name) for o in bpy.data.objects if o.type == 'MESH'}
    junk = [o for o in bpy.data.objects
            if o.type == 'EMPTY' and not o.children and strip(o.name) in mesh_bases]
    if junk:
        print(f"  Dọn {len(junk)} object rỗng trùng tên lưới "
              f"({junk[0].name} … {junk[-1].name})")
        for o in junk:
            bpy.data.objects.remove(o, do_unlink=True)

    for obj in list(bpy.data.objects):
        if obj.type != 'MESH':
            continue
        base = strip(obj.name)
        if base != obj.name and base not in bpy.data.objects:
            print(f"  Chuẩn hoá tên lưới: {obj.name} -> {base}")
            obj.name = base
        if obj.data and re.search(r'\.\d{3}$', obj.data.name):
            obj.data.name = strip(obj.data.name)

    bpy.context.view_layer.objects.active = char_arm
    if not char_arm.animation_data:
        char_arm.animation_data_create()

    pb = char_arm.pose.bones
    for b in pb:
        b.rotation_mode = 'QUATERNION'


    # =========================================================================
    # BAKE TRẠNG THÁI — mỗi trạng thái một module ở scripts/states/
    # =========================================================================
    created_actions = states.bake_states(char_arm, pb, wanted=wanted_states)


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

    if bpy.context.view_layer.objects.active is None:
        bpy.context.view_layer.objects.active = char_arm
    bpy.ops.object.mode_set(mode='OBJECT')

    # =========================================================================
    # BỘ KIỂU TÓC — thuật toán nằm ở scripts/hairstyles.py
    # =========================================================================
    hairstyles.build_hairstyles(char_arm)

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

    MODEL_NAME = "female_singer_anime_idol"
    stem = f"{out_b_dir}/{MODEL_NAME}"

    if partial:
        print(">>> Dựng thiếu trạng thái nên bỏ qua manifest.json")
    else:
        print(">>> Ghi manifest.json từ scripts/catalog.py...")
        manifest.write_manifest(os.path.join(out_b_dir, 'manifest.json'),
                                model_file=MODEL_NAME + '.glb',
                                source_file=os.path.basename(input_glb),
                                actions=bpy.data.actions)

    print(">>> Xuất GLB" + ("" if fast else ", FBX, BLEND") + "...")
    # Nén Draco: dữ liệu lưới chiếm 5,6 MB trong 9,66 MB, và đây là phần duy
    # nhất nén được — texture đã là PNG, còn keyframe hoạt ảnh thì Draco không
    # đụng tới. Lượng tử hoá để mức thận trọng: vị trí 14 bit, và generic 14 bit
    # vì nhóm đó chứa cả trọng số skinning lẫn 57 morph target khuôn mặt.
    bpy.ops.export_scene.gltf(
        filepath=stem + ".glb",
        export_format='GLB',
        export_animations=True,
        export_nla_strips=True,
        export_morph=True,
        export_skins=True,
        export_draco_mesh_compression_enable=True,
        export_draco_mesh_compression_level=6,
        export_draco_position_quantization=14,
        export_draco_normal_quantization=10,
        export_draco_texcoord_quantization=12,
        export_draco_color_quantization=10,
        export_draco_generic_quantization=14
    )
    if not fast:
        bpy.ops.export_scene.fbx(
            filepath=stem + ".fbx",
            bake_anim=True,
            bake_anim_use_all_actions=True,
            use_mesh_modifiers=True,
            add_leaf_bones=False
        )
        bpy.ops.wm.save_as_mainfile(filepath=stem + ".blend")

    print(f">>> DỰNG XONG -> {stem}.glb")
    if not partial:
        print(">>> Kiểm tra bằng: python3 tools/verify_build.py")


if __name__ == '__main__':
    args = parse_args()
    if args.list:
        for clip, mod in states.ORDER:
            print(f"  {clip:24s} scripts/states/{mod}.py")
    else:
        build_character(
            wanted_states=[s.strip() for s in args.states.split(',')] if args.states else None,
            fast=args.fast)
