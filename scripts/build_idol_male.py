# -*- coding: utf-8 -*-
"""Nắn cô ca sĩ VRoid thành một nhân vật nam, giữ nguyên bộ xương và khẩu hình.

    /Applications/Blender.app/Contents/MacOS/Blender --background \
        --factory-startup --python scripts/build_idol_male.py

Vì sao không sửa thẳng lưới
---------------------------
Sửa toạ độ đỉnh mà không sửa tư thế nghỉ của xương là hỏng phép skin: ma trận
bind vẫn tính theo hình cũ, nên hễ vào tư thế là lưới trượt khỏi xương. Ở đây
mọi phép nắn là MỘT hàm biến đổi điểm, và hàm ấy được áp cho cả đỉnh lưới lẫn
head/tail của xương trong tư thế nghỉ. Bind đổi theo, skin giữ nguyên.

Vì sao không warp theo cao độ
------------------------------
Rig VRoid ở tư thế chữ T: hai cánh tay nằm ngang ở z≈1,27, vươn tới x=±0,70.
Một phép co giãn X phụ thuộc z sẽ kéo dài cánh tay thay vì nới vai. Nên mọi
phép nắn đều đi kèm MẶT NẠ TRỌNG SỐ XƯƠNG — tổng trọng số của nhóm xương liên
quan tại đỉnh đó. Mặt nạ là trường liên tục nên không để lại đường nối.

Số đo trước khi nắn: ngực rộng 0,343 m, hông 0,326 m — gần bằng nhau, đúng
dáng nữ. Đích là ngực nở hơn hông rõ rệt.
"""
import math
import os
import sys

import bpy
from mathutils import Vector

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
SRC = os.path.join(ROOT, 'source', 'female_singer_anime_idol_base.glb')
OUT_DIR = os.path.join(ROOT, 'build', 'idol_male')

# --- tham số dáng người ----------------------------------------------------
SHOULDER_OUT = 0.024      # m, đẩy cả chuỗi cánh tay ra ngoài mỗi bên
CHEST_WIDE   = 1.17       # nở lồng ngực theo bề ngang
HIP_NARROW   = 0.90       # thu hông
NECK_THICK   = 1.16
ARM_THICK    = 1.12
LEG_THICK    = 1.05
HEIGHT       = 1.045      # 1,60 m -> 1,67 m

# Ngực: đẩy mặt trước lùi lại, mạnh nhất ở đúng cao độ nhô ra nhiều nhất.
BUST_Z    = 1.150         # đo được mặt trước nhô tới y = -0,132 quanh đây
BUST_SPAN = 0.075
BUST_PUSH = 0.026         # m, đẩy về phía sau

# Trục để co giãn quanh: tay nằm ngang nên dày lên là co giãn trong mặt (y,z);
# chân dựng đứng nên là mặt (x,y).
ARM_AXIS_Y, ARM_AXIS_Z = 0.025, 1.274
LEG_AXIS_X = 0.077
NECK_AXIS_Y = 0.030

# --- tham số khuôn mặt -----------------------------------------------------
# Mắt anime nam hẹp và dẹt hơn hẳn, chứ không phải chỉ nhỏ đi. Thu đều hai
# chiều thì vẫn ra mắt nữ, chỉ là nhỏ hơn.
EYE_SHRINK_X = 0.90
EYE_SHRINK_Z = 0.76
BROW_DOWN  = 0.005        # m, hạ chân mày xuống sát mắt
JAW_WIDE   = 1.08         # bạnh quai hàm
JAW_Z      = 1.480        # sau khi đã kéo cao 4,5%, cằm nằm ở 1,413
JAW_SPAN   = 0.055

EYE_MATS  = ('EyeIris', 'EyeWhite', 'EyeHighlight', 'FaceEyeline')
BROW_MATS = ('FaceBrow',)
HAIRBACK  = 'HairBack'

GROUPS = {
    'arm':  lambda n: any(k in n for k in ('Shoulder', 'UpperArm', 'LowerArm',
                                           '_Hand', 'Index', 'Little',
                                           'Middle', 'Ring', 'Thumb')),
    'chest': lambda n: any(k in n for k in ('C_Spine', 'C_Chest', 'C_UpperChest')),
    'hips': lambda n: 'C_Hips' in n,
    'neck': lambda n: 'C_Neck' in n,
    'leg':  lambda n: any(k in n for k in ('UpperLeg', 'LowerLeg', '_Foot',
                                           'ToeBase')),
}


def smoothstep(a, b, x):
    t = max(0.0, min(1.0, (x - a) / (b - a)))
    return t * t * (3.0 - 2.0 * t)


def warp(p, m):
    """Một điểm, một bộ mặt nạ -> điểm mới. Dùng chung cho lưới và cho xương."""
    q = p.copy()

    # vai và cả chuỗi cánh tay đẩy ra ngoài — phép TỊNH TIẾN nên cứng tuyệt
    # đối, không làm biến dạng cánh tay chút nào
    if m['arm'] > 0.0:
        q.x += math.copysign(SHOULDER_OUT * m['arm'], q.x if q.x else 1.0)

    # tay dày lên: co giãn trong mặt phẳng vuông góc với trục tay
    if m['arm'] > 0.0:
        k = 1.0 + (ARM_THICK - 1.0) * m['arm']
        q.y = ARM_AXIS_Y + (q.y - ARM_AXIS_Y) * k
        q.z = ARM_AXIS_Z + (q.z - ARM_AXIS_Z) * k

    q.x *= 1.0 + (CHEST_WIDE - 1.0) * m['chest']
    q.x *= 1.0 + (HIP_NARROW - 1.0) * m['hips']

    if m['neck'] > 0.0:
        k = 1.0 + (NECK_THICK - 1.0) * m['neck']
        q.x *= k
        q.y = NECK_AXIS_Y + (q.y - NECK_AXIS_Y) * k

    if m['leg'] > 0.0:
        k = 1.0 + (LEG_THICK - 1.0) * m['leg']
        ax = math.copysign(LEG_AXIS_X, q.x if q.x else 1.0)
        q.x = ax + (q.x - ax) * k
        q.y *= k

    # ngực phẳng: chỉ đụng vào nửa trước, và tắt dần theo cao độ
    if m['chest'] > 0.0 and q.y < 0.0:
        hump = math.exp(-((p.z - BUST_Z) / BUST_SPAN) ** 2)
        q.y += BUST_PUSH * hump * m['chest']
        if q.y > 0.0:
            q.y = 0.0

    q.z *= HEIGHT
    return q


def vertex_masks(obj):
    """Mặt nạ trọng số cho từng đỉnh: tổng trọng số của nhóm xương liên quan."""
    gi = {g.index: g.name for g in obj.vertex_groups}
    out = []
    for v in obj.data.vertices:
        m = {k: 0.0 for k in GROUPS}
        for g in v.groups:
            name = gi.get(g.group, '')
            for k, pred in GROUPS.items():
                if pred(name):
                    m[k] += g.weight
        for k in m:
            m[k] = min(1.0, m[k])
        out.append(m)
    return out


def bone_masks(name):
    return {k: (1.0 if pred(name) else 0.0) for k, pred in GROUPS.items()}


def reshape(arm, meshes):
    for obj in meshes:
        mw = obj.matrix_world
        inv = mw.inverted()
        masks = vertex_masks(obj)
        for v in obj.data.vertices:
            v.co = inv @ warp(mw @ v.co, masks[v.index])
        # Khẩu hình cũng phải nắn theo, nếu không thì hễ chớp mắt là mặt bật
        # về hình cũ.
        sk = obj.data.shape_keys
        if sk:
            for kb in sk.key_blocks:
                for i in range(len(kb.data)):
                    kb.data[i].co = inv @ warp(mw @ kb.data[i].co, masks[i])
        obj.data.update()

    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode='EDIT')
    mw = arm.matrix_world
    inv = mw.inverted()
    for eb in arm.data.edit_bones:
        m = bone_masks(eb.name)
        eb.head = inv @ warp(mw @ eb.head, m)
        eb.tail = inv @ warp(mw @ eb.tail, m)
    bpy.ops.object.mode_set(mode='OBJECT')
    print('    nắn %d lưới và %d xương' % (len(meshes), len(arm.data.bones)))


def mat_verts(obj, keys):
    got = set()
    for p in obj.data.polygons:
        if any(k in obj.data.materials[p.material_index].name for k in keys):
            got.update(p.vertices)
    return got


# Khép miệng bằng HÌNH HỌC, không bằng khẩu hình. Model có sẵn
# Fcl_MTH_Close, nhưng đo ra nó chỉ dịch đỉnh miệng tối đa 0,67 mm và trung
# bình 0,02 mm — cái miệng hé lộ lưỡi nằm sẵn trong hình nền của VRoid chứ
# không phải một trạng thái mở mà khẩu hình ấy đóng lại được.
MOUTH_Z = 1.4514          # tâm miệng sau khi đã kéo cao 4,5%
MOUTH_RX = 0.055          # bán trục ngang của vùng ảnh hưởng
MOUTH_RZ = 0.030          # bán trục dọc
MOUTH_CLOSE = 0.30        # nén còn bao nhiêu phần chiều cao


def close_mouth(face):
    """Nén vùng miệng theo chiều dọc để hai môi khép lại.

    Nén CẢ vùng chứ không riêng lưới trong miệng: lưới da có lỗ ở chỗ miệng,
    thu nhỏ mỗi phần trong thì hở ra nhìn thấu vào trong đầu.

    Khẩu hình cũng phải nén theo, vì khẩu hình glTF lưu toạ độ tuyệt đối của
    toàn bộ đỉnh — bỏ qua là hễ chớp mắt miệng lại bật mở.
    """
    mw = face.matrix_world
    inv = mw.inverted()

    def squash(p):
        r = math.hypot(p.x / MOUTH_RX, (p.z - MOUTH_Z) / MOUTH_RZ)
        w = 1.0 - smoothstep(0.55, 1.35, r)
        if w <= 0.0:
            return p
        k = 1.0 - w * (1.0 - MOUTH_CLOSE)
        q = p.copy()
        q.z = MOUTH_Z + (p.z - MOUTH_Z) * k
        return q

    n = 0
    sk = face.data.shape_keys
    for v in face.data.vertices:
        p = mw @ v.co
        q = squash(p)
        if (q - p).length > 1e-6:
            n += 1
        v.co = inv @ q
    if sk:
        for kb in sk.key_blocks:
            for i in range(len(kb.data)):
                kb.data[i].co = inv @ squash(mw @ kb.data[i].co)
    face.data.update()
    print('    khép miệng: nén %d đỉnh còn %.0f%% chiều cao, kèm %d khẩu hình'
          % (n, MOUTH_CLOSE * 100, len(sk.key_blocks) if sk else 0))


def reshape_face(face):
    """Thu nhỏ mắt, hạ chân mày, bạnh quai hàm.

    Ở kiểu anime, khác biệt nam/nữ đọc ra chủ yếu ở cỡ mắt và độ cao chân mày
    chứ không ở khối xương. Thu mắt quanh TÂM TỪNG BÊN chứ không quanh gốc toạ
    độ, nếu không hai mắt xích lại gần nhau.
    """
    mw = face.matrix_world
    inv = mw.inverted()
    eyes = mat_verts(face, EYE_MATS)
    brow = mat_verts(face, BROW_MATS)
    if eyes:
        for side in (1, -1):
            pts = [i for i in eyes if (mw @ face.data.vertices[i].co).x * side > 0]
            if not pts:
                continue
            c = sum(((mw @ face.data.vertices[i].co) for i in pts),
                    Vector()) / len(pts)
            for i in pts:
                p = mw @ face.data.vertices[i].co
                d = p - c
                d.x *= EYE_SHRINK_X
                d.z *= EYE_SHRINK_Z
                face.data.vertices[i].co = inv @ (c + d)
        print('    mắt: thu %d đỉnh, ngang ×%.2f dọc ×%.2f quanh tâm từng bên'
              % (len(eyes), EYE_SHRINK_X, EYE_SHRINK_Z))
    for i in brow:
        p = mw @ face.data.vertices[i].co
        p.z -= BROW_DOWN
        face.data.vertices[i].co = inv @ p
    if brow:
        print('    chân mày: hạ %d đỉnh xuống %.0f mm' % (len(brow), BROW_DOWN * 1000))
    n = 0
    for v in face.data.vertices:
        p = mw @ v.co
        w = 1.0 - smoothstep(JAW_Z - JAW_SPAN, JAW_Z, p.z)
        if w <= 0.001:
            continue
        p.x *= 1.0 + (JAW_WIDE - 1.0) * w
        v.co = inv @ p
        n += 1
    print('    quai hàm: bạnh %d đỉnh tối đa %.0f%%' % (n, (JAW_WIDE - 1) * 100))
    face.data.update()


def strip_hair_back(body):
    """Bỏ phần tóc dài nằm trong lưới thân. Nó là một vật liệu riêng nên tách
    được sạch, và tóc ngắn thì không còn gì che lưng."""
    import bmesh
    doomed = [p.index for p in body.data.polygons
              if HAIRBACK in body.data.materials[p.material_index].name]
    if not doomed:
        return
    bm = bmesh.new()
    bm.from_mesh(body.data)
    bm.faces.ensure_lookup_table()
    for i in doomed:
        bm.faces[i].tag = True
    import bmesh as _b
    _b.ops.delete(bm, geom=[f for f in bm.faces if f.tag], context='FACES')
    bm.to_mesh(body.data)
    bm.free()
    body.data.update()
    print('    bỏ %d mặt tóc sau lưng khỏi lưới thân' % len(doomed))


def short_hair(arm):
    """Cắt tóc dài thành kiểu ngắn nam, dùng lại bộ cắt của dự án."""
    import hairstyles
    # Vạt hai bên là chi tiết đọc ra "nữ" mạnh nhất: bob rẽ ngôi giữa với hai
    # lọn dài tới cằm. z_side phải cao hơn z_back để cắt cụt hẳn hai lọn ấy.
    hairstyles.STYLES = [dict(name='Hair_Male', z_back=1.452, z_side=1.470,
                              u_curve_depth=0.004, hang=0.02, evenness=0.10)]
    made = hairstyles.build_hairstyles(arm)
    old = bpy.data.objects.get('Hair')
    if old is not None:
        bpy.data.objects.remove(old, do_unlink=True)
    for o in made:
        o.name = 'Hair'
        o.hide_render = False
        o.hide_viewport = False
    print('    tóc: cắt ngắn, còn %d lưới tóc'
          % len([o for o in bpy.data.objects
                 if o.type == 'MESH' and 'Hair' in o.name]))


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.scene.render.fps = 30
    print('>>> Nạp cô ca sĩ')
    bpy.ops.import_scene.gltf(filepath=SRC)
    for o in list(bpy.data.objects):
        if o.type == 'MESH' and o.name.startswith('Icosphere'):
            bpy.data.objects.remove(o, do_unlink=True)
    arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
    body = bpy.data.objects['Body']
    face = next(o for o in bpy.data.objects
                if o.type == 'MESH' and o.name.startswith('Face'))

    print('>>> Cắt tóc ngắn')
    strip_hair_back(body)
    short_hair(arm)

    print('>>> Nắn dáng')
    meshes = [o for o in bpy.data.objects if o.type == 'MESH']
    reshape(arm, meshes)

    print('>>> Nắn khuôn mặt')
    reshape_face(face)
    close_mouth(face)

    os.makedirs(OUT_DIR, exist_ok=True)
    out = os.path.join(OUT_DIR, 'idol_male.glb')
    bpy.ops.export_scene.gltf(
        filepath=out, export_format='GLB',
        export_animations=False, export_skins=True, export_morph=True,
        export_draco_mesh_compression_enable=True,
        export_draco_mesh_compression_level=6,
        export_draco_position_quantization=14,
        export_draco_normal_quantization=10,
        export_draco_texcoord_quantization=12)
    print('>>> Xong: %s, %.2f MB' % (out, os.path.getsize(out) / 1048576))


if __name__ == '__main__':
    main()
