# -*- coding: utf-8 -*-
"""Chuyển năm động tác của cung thủ char6 sang bộ xương của cô ca sĩ.

    /Applications/Blender.app/Contents/MacOS/Blender --background \
        --factory-startup --python scripts/build_idol_mimic.py

Hai bộ xương khác chuẩn hoàn toàn: char6 dùng rig Mixamo 87 xương
(mixamorig:*), cô ca sĩ dùng rig VRoid 154 xương (J_Bip_*). Không chép thẳng
quaternion được, vì hướng xương gốc của hai rig khác nhau — chép sang là nhân
vật vặn xoắn.

Cách làm giống hệt phần mocap của dự án: bám HƯỚNG NỐI hai khớp. Với mỗi khung,
đo hướng từ khớp cha tới khớp con trên rig nguồn, rồi xoay xương tương ứng của
rig đích sao cho hướng ấy trùng. Cách này không quan tâm hướng xương gốc, nên
chuyển được giữa hai chuẩn bất kỳ.

Điểm khác duy nhất so với mocap BVH: cột sống. Mixamo có Spine/Spine1/Spine2,
VRoid có Spine/Chest/UpperChest — số đốt bằng nhau nên ánh xạ một-một được.
"""
import os
import sys

import bpy

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
import retarget  # noqa: E402

IDOL = os.path.join(ROOT, 'source', 'female_singer_anime_idol_base.glb')
ARCHER = os.path.join(ROOT, 'build', 'char6', 'char6.glb')
OUT_DIR = os.path.join(ROOT, 'build', 'idol_mimic')

M = 'mixamorig:'
MIXAMO_MAP = [
    (M + 'Hips',        M + 'Spine',        'J_Bip_C_Hips',      'J_Bip_C_Spine'),
    (M + 'Spine',       M + 'Spine1',       'J_Bip_C_Spine',     'J_Bip_C_Chest'),
    (M + 'Spine1',      M + 'Spine2',       'J_Bip_C_Chest',     'J_Bip_C_UpperChest'),
    (M + 'Spine2',      M + 'Neck',         'J_Bip_C_UpperChest', 'J_Bip_C_Neck'),
    (M + 'Neck',        M + 'Head',         'J_Bip_C_Neck',      'J_Bip_C_Head'),
    (M + 'LeftShoulder', M + 'LeftArm',     'J_Bip_L_Shoulder',  'J_Bip_L_UpperArm'),
    (M + 'LeftArm',     M + 'LeftForeArm',  'J_Bip_L_UpperArm',  'J_Bip_L_LowerArm'),
    (M + 'LeftForeArm', M + 'LeftHand',     'J_Bip_L_LowerArm',  'J_Bip_L_Hand'),
    (M + 'RightShoulder', M + 'RightArm',   'J_Bip_R_Shoulder',  'J_Bip_R_UpperArm'),
    (M + 'RightArm',    M + 'RightForeArm', 'J_Bip_R_UpperArm',  'J_Bip_R_LowerArm'),
    (M + 'RightForeArm', M + 'RightHand',   'J_Bip_R_LowerArm',  'J_Bip_R_Hand'),
    (M + 'LeftUpLeg',   M + 'LeftLeg',      'J_Bip_L_UpperLeg',  'J_Bip_L_LowerLeg'),
    (M + 'LeftLeg',     M + 'LeftFoot',     'J_Bip_L_LowerLeg',  'J_Bip_L_Foot'),
    (M + 'LeftFoot',    M + 'LeftToeBase',  'J_Bip_L_Foot',      'J_Bip_L_ToeBase'),
    (M + 'RightUpLeg',  M + 'RightLeg',     'J_Bip_R_UpperLeg',  'J_Bip_R_LowerLeg'),
    (M + 'RightLeg',    M + 'RightFoot',    'J_Bip_R_LowerLeg',  'J_Bip_R_Foot'),
    (M + 'RightFoot',   M + 'RightToeBase', 'J_Bip_R_Foot',      'J_Bip_R_ToeBase'),
]

# Đoạn nào đứng tại chỗ thì khử luôn phần đi tới, đoạn nào cố ý di chuyển thì
# giữ. Đoạn gục ngã bắt buộc phải giữ, vì cả động tác là ngã xuống đất.
IN_PLACE = {
    '01_DungYen': True,
    '02_DiChuyen': False,
    '03_GucNga': False,
    '04_BanCung': True,
    '05_TrungDon': True,
}
# Khoá bàn chân xuống sàn chỉ hợp với đoạn đứng; đoạn ngã và đoạn chạy thì
# không, vì chân vốn rời sàn.
LOCK_FEET = {'01_DungYen', '04_BanCung', '05_TrungDon'}


def clean():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.scene.render.fps = 30
    bpy.context.scene.render.fps_base = 1.0


def armature_of(objs):
    return next((o for o in objs if o.type == 'ARMATURE'), None)


def main():
    clean()

    print('>>> Nạp cô ca sĩ')
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=IDOL)
    idol_objs = set(bpy.data.objects) - before
    idol_arm = armature_of(idol_objs)

    print('>>> Nạp cung thủ làm nguồn động tác')
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=ARCHER)
    archer_objs = set(bpy.data.objects) - before
    src_arm = armature_of(archer_objs)
    if idol_arm is None or src_arm is None:
        raise RuntimeError('không tìm thấy đủ hai bộ xương')

    have = {b.name for b in src_arm.data.bones}
    miss = [a for a, b, _c, _d in MIXAMO_MAP if a not in have]
    if miss:
        raise RuntimeError('rig nguồn thiếu xương: %s' % miss)
    have2 = {b.name for b in idol_arm.data.bones}
    miss2 = [c for _a, _b, c, _d in MIXAMO_MAP if c not in have2]
    if miss2:
        raise RuntimeError('rig đích thiếu xương: %s' % miss2)
    print('    ánh xạ %d cặp xương, cả hai rig đều có đủ' % len(MIXAMO_MAP))

    retarget.BONE_MAP = MIXAMO_MAP
    retarget.SRC_ROOT = M + 'Hips'

    made = []
    for act in sorted(bpy.data.actions, key=lambda a: a.name):
        if not act.name[0].isdigit():
            continue                      # bỏ clip khuôn mặt
        ad = src_arm.animation_data
        ad.action = act
        if getattr(act, 'slots', None):
            # Từ Blender 4.4, gán action thôi chưa đủ: thiếu slot thì action
            # nằm đó mà không điều khiển gì, và mọi phép đọc tư thế trả về tư
            # thế nghỉ.
            ad.action_slot = act.slots[0]
        n = int(act.frame_range[1])
        print('>>> Chuyển %s (%d khung)' % (act.name, n))
        new = retarget.retarget(
            idol_arm, src_arm, 'mimic_' + act.name, frames=(1, n),
            in_place=IN_PLACE.get(act.name, True), ground=True,
            lock=act.name in LOCK_FEET)
        made.append(new.name)

    # Đẩy lên NLA: bộ xuất glTF chỉ lấy hoạt ảnh từ strip.
    ad = idol_arm.animation_data
    ad.action = None
    for t in list(ad.nla_tracks):
        ad.nla_tracks.remove(t)
    for name in made:
        track = ad.nla_tracks.new()
        track.name = name
        track.strips.new(name, 1, bpy.data.actions[name])

    for o in archer_objs:                 # chỉ mượn động tác, không lấy hình
        bpy.data.objects.remove(o, do_unlink=True)

    # Xoá luôn action gốc của cung thủ. Xoá đối tượng thôi chưa đủ: action vẫn
    # nằm trong file, và bộ xuất glTF vớ được là gán bừa lên bộ xương cô ca sĩ
    # — quaternion Mixamo áp thẳng lên xương VRoid thì nhân vật vặn xoắn.
    keep = set(made)
    for act in list(bpy.data.actions):
        if act.name not in keep:
            bpy.data.actions.remove(act)
    print('    còn lại %d action: %s' % (len(bpy.data.actions),
                                         sorted(a.name for a in bpy.data.actions)))

    os.makedirs(OUT_DIR, exist_ok=True)
    out = os.path.join(OUT_DIR, 'idol_mimic.glb')
    print('>>> Xuất %s' % out)
    bpy.ops.export_scene.gltf(
        filepath=out, export_format='GLB',
        export_animations=True, export_nla_strips=True,
        export_skins=True, export_morph=True,
        export_draco_mesh_compression_enable=True,
        export_draco_mesh_compression_level=6,
        export_draco_position_quantization=14,
        export_draco_normal_quantization=10,
        export_draco_texcoord_quantization=12)
    print('>>> Xong: %.2f MB, %d clip' % (os.path.getsize(out) / 1048576, len(made)))


if __name__ == '__main__':
    main()
