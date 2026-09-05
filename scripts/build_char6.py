# -*- coding: utf-8 -*-
"""Dựng lại bộ vật liệu cho char6.fbx (Erika Archer) rồi xuất GLB.

    /Applications/Blender.app/Contents/MacOS/Blender --background \
        --factory-startup --python scripts/build_char6.py

Vì sao cần: FBX gốc trỏ tới chín file texture ngoài mà dự án không có
(FemaleFitA_Body_diffuse.png, Erika_Archer_Clothes_diffuse.png…), và bên trong
file cũng không nhúng ảnh — có mục Video và RelativeFilename nhưng không có
Content. Nên Blender tô toàn thân bằng màu hồng tím báo thiếu ảnh.

Phần còn lại của model thì lành lặn: cả 13 lưới đều có UV, đều đã tô mượt và
có pháp tuyến tuỳ biến. Nên chỗ duy nhất phải làm là vật liệu.

Hai quyết định đáng nói:

  * TÁCH VẬT LIỆU THEO TỪNG LƯỚI. Bản gốc dồn bảy món — áo, giáp, mũ trùm,
    quần, giày, ống tên, ống tay — vào chung đúng một vật liệu Akai_MAT1. Không
    có texture thì bảy món ấy thành một khối màu duy nhất, mất hết ranh giới.
    Mỗi lưới một vật liệu là cách rẻ nhất để lấy lại chiều sâu.

  * MÀU KHAI BÁO THEO sRGB RỒI ĐỔI SANG TUYẾN TÍNH. Blender nhận base_color ở
    không gian tuyến tính; nhét thẳng số hex vào là ra một bản nhợt hẳn so với
    màu đã chọn.
"""
import math
import os
import sys

import bpy
from mathutils import Vector

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE = os.path.join(ROOT, 'source', 'char6.fbx')
OUT_DIR = os.path.join(ROOT, 'build', 'char6')

# Bảng màu: một cung thủ trùm mũ trong rừng. Cùng một họ xanh rêu cho vải, họ
# nâu cho da thuộc và gỗ, và đúng một điểm nhấn ấm ở ống tên.
# Vai của từng lưới đọc từ ảnh định danh chứ không đoán theo tên: "helmet"
# thật ra là áo choàng trùm đầu phủ cả vai, còn "armor" là áo tunic quấn và
# váy. Vải đi họ xanh rêu, da thuộc đi họ nâu, da người là điểm ấm duy nhất —
# tách hai họ ra thì mắt đọc được ngay đâu là vải đâu là da.
LOOK = {
    'HeadAndHand':  ('#CB9E7F', 0.52, 0.0, 'Da'),
    'helmet':       ('#2C3927', 0.88, 0.0, 'AoChoangTrum'),
    'armor':        ('#5C6B45', 0.84, 0.0, 'AoTunic'),
    'body':         ('#3B382F', 0.90, 0.0, 'VanhQuan'),
    'trousers':     ('#3B382F', 0.90, 0.0, 'Quan'),
    'boots':        ('#4A3524', 0.45, 0.0, 'Giay'),
    'sleeve_left':  ('#6B4A30', 0.48, 0.0, 'BaoTayTrai'),
    'sleeve_right': ('#6B4A30', 0.48, 0.0, 'BaoTayPhai'),
    'arrow_box':    ('#7E5B34', 0.52, 0.0, 'OngTen'),
    'bow':          ('#6B4526', 0.54, 0.0, 'Cung'),
    'arrow':        ('#A18E68', 0.62, 0.0, 'Ten'),
    'eyes_shadow':  ('#17130F', 0.92, 0.0, 'MiMat'),
}

# Mắt phải tách làm ba vòng, nếu không cả cầu mắt thành một màu đặc và gương
# mặt hỏng hẳn. Không có texture nên ranh giới lấy theo HƯỚNG PHÁP TUYẾN: phần
# quay thẳng ra trước là con ngươi, vòng quanh nó là tròng đen, còn lại là
# tròng trắng.
# Tóc nằm CHUNG lưới với mũ trùm, nên một màu duy nhất biến tóc thành mấy cái
# gai vải xanh lá trước mặt. May là chúng rời nhau về mặt hình học: lưới
# "helmet" có 61 mảnh không dính nhau, mảnh lớn nhất 454 đỉnh là cái mũ, còn
# 60 mảnh mười-mấy đỉnh nằm ngay trước trán chính là từng lọn tóc.
HAIR = ('#3D2B20', 0.42, 'Toc')

# Sau khi gỡ phần bị che, lưới "body" chỉ còn hai vành mỏng ở chỗ giáp ranh:
# một ở miệng giày, một ở lưng quần. Chúng cần thiết để không hở, nhưng phải
# mang màu của món kề bên — để nguyên một màu "áo lót" thì thành hai vệt kem
# vắt ngang chân, nhìn như lỗi. Cắt theo cao độ.
BODY_SPLIT_Z = 0.70

EYE_RINGS = [
    (18.0, '#141110', 0.10, 'ConNguoi'),
    (34.0, '#4E6B4A', 0.18, 'TrongDen'),
    (999.0, '#EAE4DB', 0.24, 'TrongTrang'),
]


def srgb_to_linear(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def hex_rgba(code, alpha=1.0):
    code = code.lstrip('#')
    rgb = [int(code[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]
    return tuple(srgb_to_linear(c) for c in rgb) + (alpha,)


def make_material(name, color, rough, metal):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = hex_rgba(color)
    bsdf.inputs['Roughness'].default_value = rough
    bsdf.inputs['Metallic'].default_value = metal
    return mat


# Ba mảnh này là BẢN SAO cùng bề mặt với lưới "body", dùng chung đúng toạ độ
# đỉnh. Bản gốc chạy được vì mỗi mảnh lấy một vùng texture khác nhau, nên hai
# lớp trùng khít mà nhìn vẫn ra một lớp. Cho mỗi mảnh một màu đặc thì hai lớp
# tranh nhau độ sâu và ra loang lổ như áo rằn ri — đo được: boots trùng 470
# trên 470 đỉnh, trousers 477 trên 492, armor 527 trên 1165.
COVERS_BODY = ('boots', 'trousers', 'armor')


def strip_hidden_body_faces(eps_mm=0.25):
    """Xoá những mặt của "body" bị các mảnh ngoài phủ kín.

    Đẩy mảnh ngoài ra một milimét cũng hết tranh chấp, nhưng để lại một lớp
    hình học không ai nhìn thấy.

    So TRỌNG TÂM MẶT chứ không so từng đỉnh. Ba mảnh ngoài dùng chung đường may
    với body, nên nếu chỉ hỏi "cả bốn đỉnh của mặt này có trùng đỉnh nào của
    mảnh ngoài không" thì một mặt nằm hẳn ở vùng hở, chỉ tình cờ có đủ đỉnh
    nằm trên đường may, cũng bị coi là bị che. Lần đầu tôi làm thế và nó xoá
    1331 trên 1350 mặt — gần như cả lưới, kể cả phần ngực trên đang lộ ra.
    Trọng tâm thì chỉ trùng khi hai mặt thật sự nằm chồng lên nhau.
    """
    from mathutils.kdtree import KDTree
    body = bpy.data.objects.get('body')
    if body is None:
        return
    outer = []
    for name in COVERS_BODY:
        o = bpy.data.objects.get(name)
        if o is None:
            continue
        mo = o.matrix_world
        outer += [mo @ poly.center for poly in o.data.polygons]
    if not outer:
        return
    tree = KDTree(len(outer))
    for i, p in enumerate(outer):
        tree.insert(p, i)
    tree.balance()

    mw = body.matrix_world
    eps = eps_mm / 1000.0
    doomed = []
    for poly in body.data.polygons:
        _c, _i, d = tree.find(mw @ poly.center)
        if d < eps:
            doomed.append(poly.index)
    if not doomed:
        return
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(body.data)
    bm.faces.ensure_lookup_table()
    for i in doomed:
        bm.faces[i].tag = True
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.tag], context='FACES')
    before_v = len(body.data.vertices)
    bm.to_mesh(body.data)
    bm.free()
    body.data.update()
    print('    bỏ %d mặt của "body" bị %s phủ kín (còn %d mặt, %d đỉnh)'
          % (len(doomed), '/'.join(COVERS_BODY),
             len(body.data.polygons), len(body.data.vertices)))


def clear_old_materials():
    """Bỏ hẳn vật liệu cũ. Chúng còn giữ nút ảnh trỏ vào file không tồn tại,
    và bộ xuất glTF vẫn cố ghi những nút đó ra."""
    for obj in bpy.data.objects:
        if obj.type == 'MESH':
            obj.data.materials.clear()
    for mat in list(bpy.data.materials):
        if mat.users == 0:
            bpy.data.materials.remove(mat)
    for img in list(bpy.data.images):
        if img.users == 0:
            bpy.data.images.remove(img)


def paint_eyes(obj):
    """Gán ba vật liệu cho cầu mắt theo góc giữa pháp tuyến mặt và hướng nhìn.

    Nhân vật quay mặt về phía -Y, nên hướng nhìn là -Y của thế giới. Với mỗi
    mặt, góc càng nhỏ nghĩa là mặt ấy càng nằm chính giữa mặt trước cầu mắt.
    """
    mats = [make_material('Char6_' + nm, col, rough, 0.0)
            for _a, col, rough, nm in EYE_RINGS]
    for m in mats:
        obj.data.materials.append(m)
    forward = Vector((0.0, -1.0, 0.0))
    rot = obj.matrix_world.to_3x3()
    counts = [0] * len(mats)
    for poly in obj.data.polygons:
        n = (rot @ poly.normal).normalized()
        ang = math.degrees(n.angle(forward, math.pi))
        for i, (limit, _c, _r, _nm) in enumerate(EYE_RINGS):
            if ang <= limit:
                poly.material_index = i
                counts[i] += 1
                break
    print('    mắt: %s' % ', '.join(
        '%s %d mặt' % (EYE_RINGS[i][3], c) for i, c in enumerate(counts)))


def split_hood_hair():
    """Tách tóc khỏi mũ trùm theo mảnh rời, rồi cho tóc vật liệu riêng."""
    import bmesh
    o = bpy.data.objects.get('helmet')
    if o is None:
        return False
    bm = bmesh.new()
    bm.from_mesh(o.data)
    bm.verts.ensure_lookup_table()
    seen = set()
    comps = []
    for v in bm.verts:
        if v.index in seen:
            continue
        stack, comp = [v], set()
        seen.add(v.index)
        while stack:
            x = stack.pop()
            comp.add(x.index)
            for e in x.link_edges:
                y = e.other_vert(x)
                if y.index not in seen:
                    seen.add(y.index)
                    stack.append(y)
        comps.append(comp)
    bm.free()
    if len(comps) < 2:
        return False
    comps.sort(key=len, reverse=True)
    hood = comps[0]
    n_hair = 0
    for poly in o.data.polygons:
        if not all(i in hood for i in poly.vertices):
            poly.material_index = 1
            n_hair += 1
    print('    tách tóc khỏi mũ: %d mảnh rời, mũ %d đỉnh, tóc %d mặt'
          % (len(comps), len(hood), n_hair))
    return True


# Mũi tên nằm ngửa dưới chân vì xương "arrow" treo vào Hips, và đo được nó
# đứng yên tuyệt đối trong cả bảy clip — không clip nào dùng nó để bắn. Chuyển
# sang treo vào chính xương cầm cung thì nó đi theo cung ở mọi tư thế, trông
# như đã lắp sẵn trên dây, mà không phải dựng thêm một khung hoạt ảnh nào.
BOW_BONE = 'mixamorig:Left_arch1'
ARROW_BONE = 'mixamorig:arrow'
ARROW_AHEAD = 0.12      # mét, phần mũi nhô ra trước tay cầm
ARROW_LIFT = 0.02       # mét, nâng khỏi tay cầm cho khỏi cắm vào cung


def nock_arrow_on_bow():
    """Dời mũi tên lên cung và đổi xương cha sang xương cầm cung."""
    import math
    from mathutils import Matrix, Vector
    arm = next((o for o in bpy.data.objects if o.type == 'ARMATURE'), None)
    mesh = bpy.data.objects.get('arrow')
    if arm is None or mesh is None:
        return
    bones = arm.data.bones
    if BOW_BONE not in bones or ARROW_BONE not in bones:
        return

    mw = arm.matrix_world
    grip = mw @ bones[BOW_BONE].head_local
    limb = (mw @ bones[BOW_BONE].tail_local - grip).normalized()

    # Trục dọc mũi tên hiện tại và tâm của nó, đo từ chính lưới.
    mmw = mesh.matrix_world
    pts = [mmw @ v.co for v in mesh.data.vertices]
    centre = sum(pts, Vector()) / len(pts)
    axis = Vector((0.0, 1.0, 0.0))          # đo được: mũi tên nằm dọc +Y
    half = max((p - centre).dot(axis) for p in pts)

    # Hướng bắn: vuông góc với cả trục cánh cung lẫn trục xương cầm cung.
    shoot = limb.cross(Vector((0.0, 1.0, 0.0)))
    if shoot.length < 1e-4:
        shoot = Vector((1.0, 0.0, 0.0))
    shoot.normalize()
    if shoot.x < 0:                          # mũi phải hướng ra ngoài, xa thân
        shoot = -shoot
    target = grip + shoot * (ARROW_AHEAD - half) + limb * ARROW_LIFT

    rot = axis.rotation_difference(shoot).to_matrix().to_4x4()
    xform = Matrix.Translation(target) @ rot @ Matrix.Translation(-centre)

    for v in mesh.data.vertices:            # lưới bám cứng vào một xương duy nhất
        v.co = mmw.inverted() @ (xform @ (mmw @ v.co))
    mesh.data.update()

    prev = bpy.context.view_layer.objects.active
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode='EDIT')
    eb = arm.data.edit_bones
    a, b = eb[ARROW_BONE], eb[BOW_BONE]
    a.head = mw.inverted() @ (xform @ (mw @ a.head))
    a.tail = mw.inverted() @ (xform @ (mw @ a.tail))
    a.parent = b
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.context.view_layer.objects.active = prev

    # Khoá cũ của xương này được viết trong hệ của Hips; giữ lại sau khi đổi cha
    # là đặt mũi tên sai chỗ. Chúng vốn đứng yên nên bỏ đi không mất gì.
    dropped = 0
    for act in bpy.data.actions:
        for fc in [f for f in act.fcurves
                   if f.data_path.startswith('pose.bones["%s"]' % ARROW_BONE)]:
            act.fcurves.remove(fc)
            dropped += 1
    print('    lắp mũi tên lên cung: đổi cha sang %s, bỏ %d đường cong cũ'
          % (BOW_BONE.replace('mixamorig:', ''), dropped))


def drop_duplicate_actions():
    """Bỏ những clip trùng nội dung. Ba clip 202 khung giống hệt nhau."""
    # So TOÀN BỘ đường cong. Lần đầu tôi chỉ lấy 40 đường cong đầu và cứ bảy
    # khoá lấy một, nên sót mất một cặp trùng: kiểm lại trong GLB thì hai clip
    # ấy giống hệt nhau ở cả 264 kênh.
    seen = {}
    for act in sorted(bpy.data.actions, key=lambda a: a.name):
        vals = []
        for fc in sorted(act.fcurves, key=lambda f: (f.data_path, f.array_index)):
            vals.append((fc.data_path, fc.array_index,
                         tuple(round(kp.co[1], 5) for kp in fc.keyframe_points)))
        key = (round(act.frame_range[1] - act.frame_range[0]), tuple(vals))
        if key in seen:
            print('    bỏ clip trùng: %s' % act.name[-38:])
            bpy.data.actions.remove(act)
        else:
            seen[key] = act.name


def tidy_actions():
    """Đặt lại tên bảy clip Mixamo. Tên gốc kiểu
    'Armature.001|Armature.001|Armature.004|mixamo.com|Layer0.001' vừa dài vừa
    không phân biệt được clip nào với clip nào."""
    acts = sorted(bpy.data.actions, key=lambda a: a.frame_range[1] - a.frame_range[0])
    seen = {}
    for act in acts:
        n = int(act.frame_range[1] - act.frame_range[0]) + 1
        key = n
        seen[key] = seen.get(key, 0) + 1
        suffix = '' if seen[key] == 1 else '_%d' % seen[key]
        act.name = 'Mixamo_%03dkhung%s' % (n, suffix)
    print('    hoạt ảnh:', ', '.join(a.name for a in bpy.data.actions))


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.scene.render.fps = 30
    bpy.context.scene.render.fps_base = 1.0

    print('>>> Nạp %s' % os.path.basename(SOURCE))
    bpy.ops.import_scene.fbx(filepath=SOURCE)

    clear_old_materials()

    print('>>> Gỡ hình học bị che')
    strip_hidden_body_faces()

    print('>>> Dựng vật liệu, mỗi lưới một màu riêng')
    for obj in bpy.data.objects:
        if obj.type != 'MESH':
            continue
        if obj.name == 'eyes':
            paint_eyes(obj)
            continue
        spec = LOOK.get(obj.name)
        if spec is None:
            print('    ! chưa có màu cho lưới', obj.name)
            continue
        color, rough, metal, label = spec
        obj.data.materials.append(
            make_material('Char6_' + label, color, rough, metal))
        for poly in obj.data.polygons:
            poly.material_index = 0
        if obj.name == 'body':
            obj.data.materials.append(
                make_material('Char6_VanhGiay', LOOK['boots'][0],
                              LOOK['boots'][1], 0.0))
            mw = obj.matrix_world
            low = 0
            for poly in obj.data.polygons:
                if (mw @ poly.center).z < BODY_SPLIT_Z:
                    poly.material_index = 1
                    low += 1
            print('      vành dưới %d mặt lấy màu giày, vành trên %d mặt lấy màu quần'
                  % (low, len(obj.data.polygons) - low))
        if obj.name == 'helmet':
            obj.data.materials.append(
                make_material('Char6_' + HAIR[2], HAIR[0], HAIR[1], 0.0))
            split_hood_hair()
        print('    %-14s %-10s %s  nhám %.2f' % (obj.name, label, color, rough))

    print('>>> Lắp mũi tên và dọn clip trùng')
    nock_arrow_on_bow()
    drop_duplicate_actions()
    tidy_actions()

    os.makedirs(OUT_DIR, exist_ok=True)
    out = os.path.join(OUT_DIR, 'char6.glb')
    print('>>> Xuất %s' % out)
    bpy.ops.export_scene.gltf(
        filepath=out, export_format='GLB',
        export_animations=True, export_nla_strips=False,
        export_skins=True, export_morph=False,
        export_draco_mesh_compression_enable=True,
        export_draco_mesh_compression_level=6,
        export_draco_position_quantization=14,
        export_draco_normal_quantization=10,
        export_draco_texcoord_quantization=12)
    # Bản thứ hai KHÔNG nén Draco, dành cho trang nhúng thẳng vào HTML: bộ giải
    # Draco phải tải thêm file, mà artifact chặn mọi thứ ngoài script. Xuất cùng
    # lúc để hai bản không bao giờ lệch nhau.
    web = os.path.join(OUT_DIR, 'char6_web.glb')
    bpy.ops.export_scene.gltf(
        filepath=web, export_format='GLB',
        export_animations=True, export_nla_strips=False,
        export_skins=True, export_morph=False,
        export_draco_mesh_compression_enable=False)
    print('>>> Xong: %.2f MB (nén Draco) · %.2f MB (bản nhúng)'
          % (os.path.getsize(out) / 1048576, os.path.getsize(web) / 1048576))


if __name__ == '__main__':
    main()
