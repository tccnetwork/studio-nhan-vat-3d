# -*- coding: utf-8 -*-
"""Chuyển động tác của một nhân vật Mixamo sang bộ xương của cô ca sĩ.

    /Applications/Blender.app/Contents/MacOS/Blender --background \
        --factory-startup --python scripts/build_idol_mimic.py -- cungthu
    /Applications/Blender.app/Contents/MacOS/Blender --background \
        --factory-startup --python scripts/build_idol_mimic.py -- kiemsi

Hai nguồn dùng chung đúng một đường: cùng bảng ánh xạ xương, cùng phép ghim
trục thứ hai, cùng cách mang đồ cầm tay sang. Khác nhau chỉ ở bảng cấu hình
SOURCES bên dưới — file nguồn, mốc tại chỗ của từng clip, và món nào cầm ở tay
nào.

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
SOURCES = {
    'cungthu': {
        'ten': 'cung thủ Erika',
        'glb': os.path.join(ROOT, 'build', 'char6', 'char6.glb'),
        'ra': 'idol_mimic.glb',
        'dau': 'mimic_',
        # Đoạn nào đứng tại chỗ thì khử luôn phần đi tới, đoạn nào cố ý di
        # chuyển thì giữ. Đoạn gục ngã bắt buộc phải giữ, vì cả động tác là ngã
        # xuống đất.
        'tai_cho': {'01_DungYen': True, '02_DiChuyen': False,
                    '03_GucNga': False, '04_BanCung': True,
                    '05_TrungDon': True},
        # Khoá bàn chân xuống sàn chỉ hợp với đoạn đứng; đoạn ngã và đoạn chạy
        # thì không, vì chân vốn rời sàn.
        'khoa_chan': {'01_DungYen', '04_BanCung', '05_TrungDon'},
        'do': [
            {'ten': 'cung', 'luoi': 'bow',
             'xuong': [M + 'Left_arch1', M + 'Left_arch2', M + 'Left_arch2_end'],
             'doi_ten': ['Bow_arch1', 'Bow_arch2', 'Bow_arch2_end'],
             'cha': 'J_Bip_L_Hand', 'he_truc': 'tay_trai', 'chep_xoay': True},
            {'ten': 'ống tên', 'luoi': 'arrow_box',
             'xuong': [M + 'Spine2'], 'doi_ten': ['Quiver'],
             'cha': 'J_Bip_C_UpperChest', 'he_truc': 'than',
             'chep_xoay': False, 'gan_cung': True},
        ],
    },
    'kiemsi': {
        'ten': 'hiệp sĩ thập tự',
        'glb': os.path.join(ROOT, 'build', 'char4', 'char4.glb'),
        'ra': 'idol_knight.glb',
        'dau': 'knight_',
        # Đo gốc di chuyển từng clip rồi mới đặt: đi bộ lệch xa nhất 0,56 m,
        # gục ngã 1,25 m và hông rơi xuống -0,79 m, nhảy chém hông vọt lên
        # +0,97 m. Ba đoạn ấy phải giữ nguyên phần đi tới.
        'tai_cho': {'01_ThuThe': True, '02_DiBo': False, '03_GucNga': False,
                    '04_ChemNgang': True, '05_NhayChem': False,
                    '06_DamThang': True},
        'khoa_chan': {'01_ThuThe', '04_ChemNgang'},
        'do': [
            {'ten': 'kiếm', 'luoi': 'sword',
             'xuong': [M + 'Sword_joint', M + 'Sword_joint_end'],
             'doi_ten': ['Sword_joint', 'Sword_joint_end'],
             'cha': 'J_Bip_R_Hand', 'he_truc': 'tay_phai', 'chep_xoay': True},
            # Khiên vốn treo vào cẳng tay, nhưng ở đây gắn vào BÀN TAY. Góc vặn
            # của cẳng tay không được ghim trong phép chuyển, còn bàn tay thì
            # có — treo vào cẳng tay là mặt khiên quay lung tung.
            {'ten': 'khiên', 'luoi': 'shield',
             'xuong': [M + 'Shield_joint', M + 'Shield_joint_end'],
             'doi_ten': ['Shield_joint', 'Shield_joint_end'],
             'cha': 'J_Bip_L_Hand', 'he_truc': 'tay_trai', 'chep_xoay': True},
        ],
    },
}

# Hệ trục dựng từ giải phẫu chứ không lấy hướng xương lúc nghỉ: hai rig đặt
# xương lúc nghỉ khác nhau, lấy hướng ấy thì đồ cầm tay xoay ngang.
FRAMES = {
    'tay_trai': ((M + 'LeftHand', M + 'LeftHandMiddle1',
                  M + 'LeftHandIndex1', M + 'LeftHandPinky1'),
                 ('J_Bip_L_Hand', 'J_Bip_L_Middle1',
                  'J_Bip_L_Index1', 'J_Bip_L_Little1')),
    'tay_phai': ((M + 'RightHand', M + 'RightHandMiddle1',
                  M + 'RightHandIndex1', M + 'RightHandPinky1'),
                 ('J_Bip_R_Hand', 'J_Bip_R_Middle1',
                  'J_Bip_R_Index1', 'J_Bip_R_Little1')),
    'than':     ((M + 'Spine2', M + 'Neck', M + 'LeftArm', M + 'RightArm'),
                 ('J_Bip_C_UpperChest', 'J_Bip_C_Neck',
                  'J_Bip_L_UpperArm', 'J_Bip_R_UpperArm')),
}

# Đích của phép chuyển. Nhân vật nam là bản đã nắn dáng của chính cô ca sĩ nên
# dùng chung y hệt bảng ánh xạ; chuyển được lên anh ta cũng là phép kiểm rằng
# nắn dáng không làm hỏng bộ xương.
TARGETS = {
    'nu':  (os.path.join(ROOT, 'source', 'female_singer_anime_idol_base.glb'),
            os.path.join(ROOT, 'build', 'idol_mimic'), ''),
    'nam': (os.path.join(ROOT, 'build', 'idol_male', 'idol_male.glb'),
            os.path.join(ROOT, 'build', 'idol_male'), 'male_'),
}


def local_frame(arm, names):
    """Hệ trục trực chuẩn dựng từ bốn khớp: gốc, hướng dọc, và một cặp làm
    hướng ngang."""
    a, b, c, d = names
    w = arm.matrix_world
    p = w @ arm.data.bones[a].head_local
    u = (w @ arm.data.bones[b].head_local) - p
    e = (w @ arm.data.bones[c].head_local) - (w @ arm.data.bones[d].head_local)
    u.normalize()
    e = (e - u * e.dot(u)).normalized()
    n = u.cross(e)
    return Matrix(((u.x, e.x, n.x, p.x),
                   (u.y, e.y, n.y, p.y),
                   (u.z, e.z, n.z, p.z),
                   (0.0, 0.0, 0.0, 1.0)))


def rig_height(arm, hips, head):
    w = arm.matrix_world
    return ((w @ arm.data.bones[head].head_local)
            - (w @ arm.data.bones[hips].head_local)).length


def attach_prop(idol_arm, src_arm, src_objs, spec, scale):
    """Mang một món đồ từ rig nguồn sang rig cô ca sĩ, giữ nguyên phép skin.

    Một phép đồng dạng đưa cả vùng bàn tay (hoặc vùng thân) bên nguồn về vùng
    tương ứng bên đích. Đặt xương VÀ lưới bằng đúng phép ấy thì thế bind không
    đổi, nên không phải sơn lại trọng số gì.
    """
    key = spec['luoi'].lower()
    obj = next((o for o in src_objs
                if o.type == 'MESH' and o.name.lower().startswith(key)), None)
    if obj is None:
        print('    KHÔNG tìm thấy lưới %s' % spec['luoi'])
        return []

    fsrc, fdst = FRAMES[spec['he_truc']]
    t = (local_frame(idol_arm, fdst) @ Matrix.Scale(scale, 4)
         @ local_frame(src_arm, fsrc).inverted())

    ws = src_arm.matrix_world
    rest = []
    for name in spec['xuong']:
        b = src_arm.data.bones[name]
        rest.append((t @ (ws @ b.head_local), t @ (ws @ b.tail_local),
                     (t.to_3x3() @ ((ws @ b.matrix_local).to_3x3()
                                    @ Vector((0.0, 0.0, 1.0)))).normalized()))

    bpy.context.view_layer.objects.active = idol_arm
    bpy.ops.object.mode_set(mode='EDIT')
    eb = idol_arm.data.edit_bones
    made = []
    for i, (head, tail, roll) in enumerate(rest):
        nb = eb.new(spec['doi_ten'][i])
        nb.head, nb.tail = head, tail
        nb.align_roll(roll)
        nb.parent = eb[made[i - 1]] if i else eb[spec['cha']]
        nb.use_connect = False
        made.append(nb.name)
    bpy.ops.object.mode_set(mode='OBJECT')

    if spec.get('gan_cung'):
        # Ống tên skin vào ba xương thân, nặng nhất là Spine2 với 87% trọng số.
        # Gắn cứng vào một xương là đủ: nó vốn gần như không biến dạng.
        for vg in list(obj.vertex_groups):
            obj.vertex_groups.remove(vg)
        g = obj.vertex_groups.new(name=made[0])
        g.add(list(range(len(obj.data.vertices))), 1.0, 'REPLACE')
    else:
        ren = dict(zip(spec['xuong'], made))
        for vg in obj.vertex_groups:
            if vg.name in ren:
                vg.name = ren[vg.name]

    mw = t @ obj.matrix_world
    obj.parent = idol_arm
    obj.matrix_parent_inverse = idol_arm.matrix_world.inverted()
    obj.matrix_world = mw
    for m in list(obj.modifiers):
        obj.modifiers.remove(m)
    obj.modifiers.new('Armature', 'ARMATURE').object = idol_arm
    print('    %s: %d xương vào %s' % (spec['ten'], len(made), spec['cha']))
    return list(zip(spec['xuong'], made)) if spec.get('chep_xoay') else []


def copy_prop_motion(idol_arm, src_arm, clip_names, pairs, prefix):
    """Chép góc xoay cục bộ của xương đồ vật sang từng clip.

    Chép cục bộ ở đây là ĐÚNG, khác hẳn phần thân: xương bên đích là bản sao
    đồng dạng của xương nguồn, cùng tư thế nghỉ, nên góc xoay trong hệ riêng
    của xương mang đúng một ý nghĩa.
    """
    scene = bpy.context.scene
    ad = idol_arm.animation_data
    for name in clip_names:
        src_act = bpy.data.actions[name[len(prefix):]]
        sad = src_arm.animation_data
        sad.action = src_act
        if getattr(src_act, 'slots', None):
            sad.action_slot = src_act.slots[0]
        act = bpy.data.actions[name]
        ad.action = act
        if getattr(act, 'slots', None):
            ad.action_slot = act.slots[0]
        for f in range(1, int(src_act.frame_range[1]) + 1):
            scene.frame_set(f)
            for sb, db in pairs:
                dp = idol_arm.pose.bones[db]
                dp.rotation_mode = 'QUATERNION'
                dp.rotation_quaternion = src_arm.pose.bones[sb].matrix_basis.to_quaternion()
                dp.keyframe_insert(data_path='rotation_quaternion', frame=f)
    print('    chép chuyển động đồ vật vào %d clip' % len(clip_names))


def clean():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.scene.render.fps = 30
    bpy.context.scene.render.fps_base = 1.0


def armature_of(objs):
    return next((o for o in objs if o.type == 'ARMATURE'), None)


def main():
    args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    which = args[0] if args else 'cungthu'
    who = args[1] if len(args) > 1 else 'nu'
    if which not in SOURCES or who not in TARGETS:
        raise SystemExit('dùng: <%s> [<%s>]'
                         % ('|'.join(SOURCES), '|'.join(TARGETS)))
    cfg = SOURCES[which]
    idol_path, out_dir, out_pre = TARGETS[who]
    clean()

    print('>>> Nạp nhân vật đích (%s)' % who)
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=idol_path)
    idol_arm = armature_of(set(bpy.data.objects) - before)

    print('>>> Nạp %s làm nguồn động tác' % cfg['ten'])
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=cfg['glb'])
    src_objs = set(bpy.data.objects) - before
    src_arm = armature_of(src_objs)
    if idol_arm is None or src_arm is None:
        raise RuntimeError('không tìm thấy đủ hai bộ xương')

    have = {b.name for b in src_arm.data.bones}
    miss = [a for a, _b, _c, _d in MIXAMO_MAP if a not in have]
    have2 = {b.name for b in idol_arm.data.bones}
    miss2 = [c for _a, _b, c, _d in MIXAMO_MAP if c not in have2]
    if miss or miss2:
        raise RuntimeError('thiếu xương: nguồn %s, đích %s' % (miss, miss2))
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
            idol_arm, src_arm, cfg['dau'] + act.name, frames=(1, n),
            in_place=cfg['tai_cho'].get(act.name, True), ground=True,
            lock=act.name in cfg['khoa_chan'])
        made.append(new.name)

    print('>>> Mang đồ sang')
    scale = (rig_height(idol_arm, 'J_Bip_C_Hips', 'J_Bip_C_Head')
             / rig_height(src_arm, M + 'Hips', M + 'Head'))
    print('    tỉ lệ %.3f theo chiều cao rig' % scale)
    keep_mesh, pairs = set(), []
    for spec in cfg['do']:
        pairs += attach_prop(idol_arm, src_arm, src_objs, spec, scale)
        keep_mesh.add(spec['luoi'].lower())
    if pairs:
        copy_prop_motion(idol_arm, src_arm, made, pairs, cfg['dau'])

    # Đẩy lên NLA: bộ xuất glTF chỉ lấy hoạt ảnh từ strip.
    ad = idol_arm.animation_data
    ad.action = None
    for t in list(ad.nla_tracks):
        ad.nla_tracks.remove(t)
    for name in made:
        track = ad.nla_tracks.new()
        track.name = name
        track.strips.new(name, 1, bpy.data.actions[name])

    for o in src_objs:                    # chỉ mượn động tác, không lấy hình
        if o.type == 'MESH' and any(o.name.lower().startswith(k) for k in keep_mesh):
            continue                      # trừ đồ cầm tay, đã sang rồi
        bpy.data.objects.remove(o, do_unlink=True)

    # Xoá luôn action gốc. Xoá đối tượng thôi chưa đủ: action vẫn nằm trong
    # file, và bộ xuất glTF vớ được là gán bừa lên bộ xương cô ca sĩ —
    # quaternion Mixamo áp thẳng lên xương VRoid thì nhân vật vặn xoắn.
    keep = set(made)
    for act in list(bpy.data.actions):
        if act.name not in keep:
            bpy.data.actions.remove(act)

    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, out_pre + cfg['ra'])
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
