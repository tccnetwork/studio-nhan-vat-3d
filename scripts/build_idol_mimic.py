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
from mathutils import Matrix, Vector

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
    # Bàn tay phải căn riêng, nếu không nó chỉ treo theo cẳng tay — cây cung
    # cầm trong tay trái sẽ lệch theo cổ tay.
    (M + 'LeftHand',  M + 'LeftHandMiddle1',  'J_Bip_L_Hand',      'J_Bip_L_Middle1'),
    (M + 'RightHand', M + 'RightHandMiddle1', 'J_Bip_R_Hand',      'J_Bip_R_Middle1'),
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


BOW_MESH = 'bow'
# Cung skin vào chuỗi xương riêng treo vào bàn tay trái, không nằm trong bảng
# ánh xạ. Chép nguyên chuỗi ấy sang rig cô ca sĩ.
BOW_BONES = [M + 'Left_arch1', M + 'Left_arch2', M + 'Left_arch2_end']
BOW_RENAME = {M + 'Left_arch1': 'Bow_arch1',
              M + 'Left_arch2': 'Bow_arch2',
              M + 'Left_arch2_end': 'Bow_arch2_end'}
# Hệ trục bàn tay dựng từ giải phẫu chứ không lấy hướng xương lúc nghỉ: hai rig
# đặt bàn tay lúc nghỉ khác nhau, lấy hướng ấy thì cung xoay ngang.
HAND_SRC = (M + 'LeftHand', M + 'LeftHandMiddle1',
            M + 'LeftHandIndex1', M + 'LeftHandPinky1')
HAND_DST = ('J_Bip_L_Hand', 'J_Bip_L_Middle1',
            'J_Bip_L_Index1', 'J_Bip_L_Little1')


def local_frame(arm, names):
    """Hệ trục trực chuẩn dựng từ bốn khớp: gốc, hướng dọc, và một cặp làm
    hướng ngang. Dùng giải phẫu chứ không lấy hướng xương lúc nghỉ — hai rig đặt
    xương lúc nghỉ khác nhau, lấy hướng ấy thì đồ cầm tay xoay ngang."""
    hand, mid, idx, pky = names
    w = arm.matrix_world
    p = w @ arm.data.bones[hand].head_local
    u = (w @ arm.data.bones[mid].head_local) - p          # dọc lòng bàn tay
    a = (w @ arm.data.bones[idx].head_local) - (w @ arm.data.bones[pky].head_local)
    u.normalize()
    a = (a - u * a.dot(u)).normalized()                   # ngang, đã trực giao
    n = u.cross(a)
    return Matrix(((u.x, a.x, n.x, p.x),
                   (u.y, a.y, n.y, p.y),
                   (u.z, a.z, n.z, p.z),
                   (0.0, 0.0, 0.0, 1.0)))


QUIVER_MESH = 'arrow_box'
# Ống tên skin vào ba xương thân, nặng nhất là Spine2 (87% trọng số). Gắn cứng
# vào một xương duy nhất là đủ: nó vốn gần như không biến dạng.
QUIVER_ANCHOR_SRC = M + 'Spine2'
QUIVER_ANCHOR_DST = 'J_Bip_C_UpperChest'
TORSO_SRC = (M + 'Spine2', M + 'Neck', M + 'LeftArm', M + 'RightArm')
TORSO_DST = ('J_Bip_C_UpperChest', 'J_Bip_C_Neck',
             'J_Bip_L_UpperArm', 'J_Bip_R_UpperArm')


def rig_height(arm, hips, head):
    w = arm.matrix_world
    return ((w @ arm.data.bones[head].head_local)
            - (w @ arm.data.bones[hips].head_local)).length


def attach_bow(idol_arm, src_arm, archer_objs):
    """Chuyển cây cung sang tay cô ca sĩ, giữ nguyên phép skin."""
    bow = next((o for o in archer_objs
                if o.type == 'MESH' and o.name.startswith(BOW_MESH)), None)
    if bow is None:
        print('    KHÔNG tìm thấy lưới cung')
        return [], 1.0

    s = (rig_height(idol_arm, 'J_Bip_C_Hips', 'J_Bip_C_Head')
         / rig_height(src_arm, M + 'Hips', M + 'Head'))
    # Một phép đồng dạng đưa cả vùng bàn tay nguồn về vùng bàn tay đích. Đặt
    # xương VÀ lưới bằng đúng phép này thì thế bind không đổi, skin giữ nguyên.
    t = (local_frame(idol_arm, HAND_DST) @ Matrix.Scale(s, 4)
         @ local_frame(src_arm, HAND_SRC).inverted())
    print('    cung: tỉ lệ %.3f theo chiều cao rig' % s)

    ws = src_arm.matrix_world
    rest = []
    for name in BOW_BONES:
        b = src_arm.data.bones[name]
        rest.append((name,
                     t @ (ws @ b.head_local),
                     t @ (ws @ b.tail_local),
                     (t.to_3x3() @ ((ws @ b.matrix_local).to_3x3()
                                    @ Vector((0.0, 0.0, 1.0)))).normalized()))

    bpy.context.view_layer.objects.active = idol_arm
    bpy.ops.object.mode_set(mode='EDIT')
    eb = idol_arm.data.edit_bones
    parent = eb['J_Bip_L_Hand']
    made = []
    for i, (name, head, tail, roll_ref) in enumerate(rest):
        nb = eb.new(BOW_RENAME[name])
        nb.head, nb.tail = head, tail
        nb.align_roll(roll_ref)
        nb.parent = eb[BOW_RENAME[BOW_BONES[i - 1]]] if i else parent
        nb.use_connect = False
        made.append(nb.name)
    bpy.ops.object.mode_set(mode='OBJECT')

    for vg in bow.vertex_groups:
        if vg.name in BOW_RENAME:
            vg.name = BOW_RENAME[vg.name]
    mw = t @ bow.matrix_world
    bow.parent = idol_arm
    bow.matrix_parent_inverse = idol_arm.matrix_world.inverted()
    bow.matrix_world = mw
    for m in bow.modifiers:
        if m.type == 'ARMATURE':
            m.object = idol_arm
    print('    cung: gắn %d xương vào J_Bip_L_Hand' % len(made))
    return made, s


def attach_quiver(idol_arm, src_arm, archer_objs, scale):
    """Chuyển ống tên sang lưng cô ca sĩ, gắn cứng vào một xương ngực."""
    q = next((o for o in archer_objs
              if o.type == 'MESH' and o.name.startswith(QUIVER_MESH)), None)
    if q is None:
        print('    KHÔNG tìm thấy lưới ống tên')
        return None

    t = (local_frame(idol_arm, TORSO_DST) @ Matrix.Scale(scale, 4)
         @ local_frame(src_arm, TORSO_SRC).inverted())

    ws = src_arm.matrix_world
    b = src_arm.data.bones[QUIVER_ANCHOR_SRC]
    head = t @ (ws @ b.head_local)
    tail = t @ (ws @ b.tail_local)
    roll = (t.to_3x3() @ ((ws @ b.matrix_local).to_3x3()
                          @ Vector((0.0, 0.0, 1.0)))).normalized()

    bpy.context.view_layer.objects.active = idol_arm
    bpy.ops.object.mode_set(mode='EDIT')
    eb = idol_arm.data.edit_bones
    nb = eb.new('Quiver')
    nb.head, nb.tail = head, tail
    nb.align_roll(roll)
    nb.parent = eb[QUIVER_ANCHOR_DST]
    nb.use_connect = False
    name = nb.name
    bpy.ops.object.mode_set(mode='OBJECT')

    for vg in list(q.vertex_groups):
        q.vertex_groups.remove(vg)
    g = q.vertex_groups.new(name=name)
    g.add(list(range(len(q.data.vertices))), 1.0, 'REPLACE')

    mw = t @ q.matrix_world
    q.parent = idol_arm
    q.matrix_parent_inverse = idol_arm.matrix_world.inverted()
    q.matrix_world = mw
    for m in q.modifiers:
        if m.type == 'ARMATURE':
            m.object = idol_arm
    print('    ống tên: gắn cứng vào %s' % QUIVER_ANCHOR_DST)
    return name


def copy_bow_motion(idol_arm, src_arm, clip_names, bow_bones):
    """Chép góc xoay cục bộ của chuỗi xương cung sang từng clip.

    Chép cục bộ ở đây là ĐÚNG, khác hẳn phần thân: xương cung bên đích là bản
    sao đồng dạng của xương nguồn, cùng tư thế nghỉ, nên góc xoay trong hệ riêng
    của xương mang đúng một ý nghĩa. Nhờ vậy cung vẫn nhún theo lúc giương.
    """
    scene = bpy.context.scene
    ad = idol_arm.animation_data
    for name in clip_names:
        src_act = bpy.data.actions[name[len('mimic_'):]]
        sad = src_arm.animation_data
        sad.action = src_act
        if getattr(src_act, 'slots', None):
            sad.action_slot = src_act.slots[0]
        act = bpy.data.actions[name]
        ad.action = act
        if getattr(act, 'slots', None):
            ad.action_slot = act.slots[0]
        n = int(src_act.frame_range[1])
        for f in range(1, n + 1):
            scene.frame_set(f)
            for i, dst in enumerate(bow_bones):
                sp = src_arm.pose.bones[BOW_BONES[i]]
                dp = idol_arm.pose.bones[dst]
                dp.rotation_mode = 'QUATERNION'
                dp.rotation_quaternion = sp.matrix_basis.to_quaternion()
                dp.keyframe_insert(data_path='rotation_quaternion', frame=f)
    print('    cung: chép chuyển động vào %d clip' % len(clip_names))


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
    # Rig Mixamo có xương mắt, rig VRoid cũng có — bám được hướng nhìn, nếu
    # không thì cái đầu chỉ treo theo cổ và cúi gằm xuống đất lúc chạy.
    retarget.SRC_HEAD = M + 'Head'
    retarget.SRC_EYES = (M + 'LeftEye', M + 'RightEye')
    # Trục ngang để ghim nốt góc xoay còn tự do: hai háng cho chậu, đường
    # ngón trỏ–ngón út cho bàn tay.
    retarget.TWISTS = {
        'J_Bip_C_Hips': ('J_Bip_L_UpperLeg', 'J_Bip_R_UpperLeg',
                         M + 'LeftUpLeg', M + 'RightUpLeg'),
        'J_Bip_L_Hand': ('J_Bip_L_Index1', 'J_Bip_L_Little1',
                         M + 'LeftHandIndex1', M + 'LeftHandPinky1'),
        'J_Bip_R_Hand': ('J_Bip_R_Index1', 'J_Bip_R_Little1',
                         M + 'RightHandIndex1', M + 'RightHandPinky1'),
    }

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

    print('>>> Gắn cung và ống tên')
    bow_bones, scale = attach_bow(idol_arm, src_arm, archer_objs)
    if bow_bones:
        copy_bow_motion(idol_arm, src_arm, made, bow_bones)
    attach_quiver(idol_arm, src_arm, archer_objs, scale)

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
        if o.type == 'MESH' and (o.name.startswith(BOW_MESH)
                                 or o.name.startswith(QUIVER_MESH)):
            continue                      # trừ cung và ống tên, đã sang rồi
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
