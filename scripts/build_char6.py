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
# đứng yên tuyệt đối trong cả bảy clip — không clip nào dùng nó để bắn.
# Mũi tên rời dài 0,75 m trong khi năm thân tên trong ống chỉ dựng nửa trên,
# dài 0,374 m — cắm chung vào ống thì nó thò ra dài gấp đôi, nhìn không hợp.
# Trên cung cũng không hợp vì chưa có động tác bắn nào. Nên bỏ hẳn nó khỏi bản
# xuất. Đặt False thì quay lại cách cắm vào ống.
HIDE_ARROW = True

QUIVER_MESH = 'arrow_box'
QUIVER_BONE = 'mixamorig:Spine2'      # ống tên bám chủ yếu vào xương này
ARROW_BONE = 'mixamorig:arrow'
ARROW_PROUD = 0.045                   # mét, nhô cao hơn bó tên sẵn có
ARROW_ASIDE = 0.030                   # mét, lệch sang bên cho khỏi cắm vào nhau


def _mesh_islands(obj):
    """Các mảnh rời của một lưới, trả về danh sách toạ độ thế giới."""
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.verts.ensure_lookup_table()
    mw = obj.matrix_world
    seen, parts = set(), []
    for v in bm.verts:
        if v.index in seen:
            continue
        stack, comp = [v], []
        seen.add(v.index)
        while stack:
            x = stack.pop()
            comp.append(mw @ x.co)
            for e in x.link_edges:
                y = e.other_vert(x)
                if y.index not in seen:
                    seen.add(y.index)
                    stack.append(y)
        parts.append(comp)
    bm.free()
    return parts


def _long_axis(pts):
    """Tâm, trục dài nhất và chiều dài của một đám điểm."""
    from mathutils import Matrix, Vector
    c = sum(pts, Vector()) / len(pts)
    xx = yy = zz = xy = xz = yz = 0.0
    for p in pts:
        d = p - c
        xx += d.x * d.x; yy += d.y * d.y; zz += d.z * d.z
        xy += d.x * d.y; xz += d.x * d.z; yz += d.y * d.z
    M = Matrix(((xx, xy, xz), (xy, yy, yz), (xz, yz, zz)))
    v = Vector((0.3, 0.2, 1.0)).normalized()
    for _ in range(50):
        v = (M @ v).normalized()
    if v.z < 0:
        v = -v
    ext = [(p - c).dot(v) for p in pts]
    return c, v, max(ext) - min(ext), max(ext)


def hide_arrow():
    """Bỏ hẳn mũi tên rời khỏi bản xuất, cùng xương của nó."""
    mesh = bpy.data.objects.get('arrow')
    if mesh is not None:
        bpy.data.objects.remove(mesh, do_unlink=True)
    arm = next((o for o in bpy.data.objects if o.type == 'ARMATURE'), None)
    if arm and ARROW_BONE in arm.data.bones:
        prev = bpy.context.view_layer.objects.active
        bpy.context.view_layer.objects.active = arm
        bpy.ops.object.mode_set(mode='EDIT')
        eb = arm.data.edit_bones
        eb.remove(eb[ARROW_BONE])
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.context.view_layer.objects.active = prev
    dropped = 0
    for act in bpy.data.actions:
        for fc in [f for f in act.fcurves
                   if f.data_path.startswith('pose.bones["%s"]' % ARROW_BONE)]:
            act.fcurves.remove(fc)
            dropped += 1
    print('    ẩn mũi tên rời: bỏ lưới, bỏ xương, bỏ %d đường cong' % dropped)


def put_arrow_in_quiver():
    """Cắm mũi tên rời vào ống tên sau lưng, căn theo bó tên đã có sẵn.

    Vì sao không để trên cung: xương "arrow" vốn treo vào Hips và đo được nó
    đứng yên tuyệt đối trong cả bảy clip, tức chưa bao giờ được dùng để bắn.
    Lắp sẵn lên dây thì nhìn không hợp lý vì nhân vật còn phải rút tên trong
    đoạn 02_RutTen.

    Hướng và độ cao lấy từ chính năm thân tên đang nằm trong ống, không đặt số
    cứng: chúng dài 0,374 m vì chỉ dựng nửa trên, còn mũi tên rời dài 0,75 m
    nên phải căn theo ĐẦU TRÊN chứ không phải theo tâm.
    """
    from mathutils import Matrix, Vector
    arm = next((o for o in bpy.data.objects if o.type == 'ARMATURE'), None)
    mesh = bpy.data.objects.get('arrow')
    quiver = bpy.data.objects.get(QUIVER_MESH)
    if arm is None or mesh is None or quiver is None:
        return
    if QUIVER_BONE not in arm.data.bones or ARROW_BONE not in arm.data.bones:
        return

    # Năm thân tên trong ống: các mảnh dài gần bằng nhau, ít đỉnh.
    shafts = []
    for pts in _mesh_islands(quiver):
        if not (6 <= len(pts) <= 12):
            continue
        c, v, length, top = _long_axis(pts)
        if 0.25 < length < 0.55:
            shafts.append((c, v, top))
    if not shafts:
        return
    axis = sum((v for _c, v, _t in shafts), Vector()) / len(shafts)
    axis.normalize()
    tops = [c + v * t for c, v, t in shafts]
    top_mid = sum(tops, Vector()) / len(tops)
    side = axis.cross(Vector((0.0, 1.0, 0.0)))
    if side.length < 1e-4:
        side = Vector((1.0, 0.0, 0.0))
    side.normalize()

    mmw = mesh.matrix_world
    pts = [mmw @ v.co for v in mesh.data.vertices]
    centre = sum(pts, Vector()) / len(pts)
    own = Vector((0.0, 1.0, 0.0))          # đo được: mũi tên nằm dọc +Y
    half = max((p - centre).dot(own) for p in pts)

    target = top_mid + axis * (ARROW_PROUD - half) + side * ARROW_ASIDE
    rot = own.rotation_difference(axis).to_matrix().to_4x4()
    xform = Matrix.Translation(target) @ rot @ Matrix.Translation(-centre)

    for v in mesh.data.vertices:
        v.co = mmw.inverted() @ (xform @ (mmw @ v.co))
    mesh.data.update()

    prev = bpy.context.view_layer.objects.active
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode='EDIT')
    eb = arm.data.edit_bones
    a = eb[ARROW_BONE]
    mw = arm.matrix_world
    a.head = mw.inverted() @ (xform @ (mw @ a.head))
    a.tail = mw.inverted() @ (xform @ (mw @ a.tail))
    a.parent = eb[QUIVER_BONE]
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.context.view_layer.objects.active = prev

    dropped = 0
    for act in bpy.data.actions:
        for fc in [f for f in act.fcurves
                   if f.data_path.startswith('pose.bones["%s"]' % ARROW_BONE)]:
            act.fcurves.remove(fc)
            dropped += 1
    print('    cắm mũi tên vào ống: căn theo %d thân tên sẵn có, '
          'đổi cha sang %s, bỏ %d đường cong cũ'
          % (len(shafts), QUIVER_BONE.replace('mixamorig:', ''), dropped))


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


# Bảy "clip" trong FBX không phải bảy động tác. Đo bằng cách trượt từng clip
# ngắn dọc clip dài: cả bốn đều khớp từ khung 1 với sai lệch ĐÚNG 0° — chúng là
# cùng một động tác bị cắt cụt ở 27, 30, 32 và 71 khung. Ba bản 202 khung thì
# trùng nhau ở cả 264 kênh.
#
# Bản đầy đủ là một chu trình bắn cung, và các khung 62, 138, 173, 202 có tư
# thế giống hệt nhau (lệch 0°) — đó là thế thủ mà mỗi đoạn đều quay về. Nên cắt
# ở đúng bốn mốc ấy thì được bốn clip tự khép vòng và nối được với nhau.
# Tên đặt theo thứ NHÌN THẤY trên ảnh dựng từng đoạn, không theo suy đoán từ
# số đo. Lần đầu tôi đặt tên theo cao độ bàn tay và sai cả bốn: đoạn 2 tưởng là
# "rút tên" hoá ra là nhào lộn trên không, đoạn 3 tưởng "giương và bắn" hoá ra
# chỉ nâng cung lên rồi hạ xuống. TRONG CẢ BỐN ĐOẠN KHÔNG CÓ ĐỘNG TÁC BẮN NÀO.
SEGMENTS = [
    ('01_DungVaBuoc',  1,  62),   # đứng thở, rồi bước lấn tới một nhịp
    ('02_NhaoLon',    62, 138),   # bật nhảy, lộn trên không rồi tiếp đất
    ('03_NangCung',  138, 173),   # đưa cung lên quá đầu rồi hạ xuống
    ('04_XoayNguoi', 173, 202),   # xoay người tại chỗ rồi về hướng cũ
]


def split_long_clip():
    """Cắt clip dài thành bốn đoạn tại những mốc có cùng tư thế."""
    if not bpy.data.actions:
        return
    src = max(bpy.data.actions, key=lambda a: a.frame_range[1] - a.frame_range[0])
    made = []
    for name, lo, hi in SEGMENTS:
        act = bpy.data.actions.new(name)
        for fc in src.fcurves:
            nfc = act.fcurves.new(fc.data_path, index=fc.array_index,
                                  action_group=fc.group.name if fc.group else '')
            nfc.keyframe_points.add(hi - lo + 1)
            for k, f in enumerate(range(lo, hi + 1)):
                kp = nfc.keyframe_points[k]
                kp.co = (f - lo + 1, fc.evaluate(f))
                kp.interpolation = 'LINEAR'
            nfc.update()
        act.use_fake_user = True
        made.append((name, hi - lo + 1))
    for a in list(bpy.data.actions):
        if a.name not in dict(made):
            bpy.data.actions.remove(a)

    # Action rời không tự đi vào file: bộ xuất glTF lấy hoạt ảnh từ các strip
    # NLA. Bỏ bước này thì GLB ra 0,16 MB và không có clip nào.
    arm = next((o for o in bpy.data.objects if o.type == 'ARMATURE'), None)
    if arm:
        if not arm.animation_data:
            arm.animation_data_create()
        ad = arm.animation_data
        ad.action = None
        for t in list(ad.nla_tracks):
            ad.nla_tracks.remove(t)
        for name, _n in made:
            track = ad.nla_tracks.new()
            track.name = name
            track.strips.new(name, 1, bpy.data.actions[name])
    print('    cắt clip dài thành %d đoạn: %s'
          % (len(made), ', '.join('%s %d khung' % m for m in made)))


# ---- Dựng động tác bắn ----------------------------------------------------
#
# Bốn đoạn có sẵn KHÔNG có động tác bắn nào: đứng-bước, nhào lộn, nâng cung,
# xoay người. Không có lúc kéo dây, không có lúc buông. Nên đoạn này là do dựng
# thêm, không phải khôi phục thứ có sẵn trong file.
#
# Tư thế tay đặt bằng IK hai xương chứ không gõ quaternion: cho trước vị trí
# bàn tay thì giải ra khuỷu, nên tay luôn co duỗi trong tầm giải phẫu. Phần
# thân giữ nguyên tư thế thủ lấy từ khung đầu của 03_NangCung.

# Tắt: đoạn này dựng ra nhìn hỏng — cung dựng đứng cạnh mặt, hai tay vặn, không
# ra thế giương cung. Giữ mã lại để làm tiếp, nhưng không đưa vào bản xuất.
MAKE_SHOOT = False

SHOOT_NAME = '05_BanTen'
SHOOT_FPS = 30
# (giây, tay cung duỗi bao nhiêu phần tầm với, tay dây lùi bao nhiêu mét sau cằm)
SHOOT_KEYS = [
    (0.00, 0.55, -0.02),   # thủ
    (0.35, 0.88, 0.02),    # nâng cung, tay trái duỗi về đích
    (0.85, 0.92, 0.26),    # kéo hết dây, tay phải về sau cằm
    (1.05, 0.92, 0.27),    # giữ
    (1.15, 0.90, 0.10),    # buông, tay phải bật nhẹ ra sau
    (1.75, 0.55, -0.02),   # về thủ
]
RELEASE_T = 1.15
ARROW_SPEED = 26.0        # m/s
ARROW_GONE = 0.30         # giây sau khi buông thì mất hẳn


def _two_bone_ik(arm, upper, lower, end, target, pole):
    """Đặt bàn tay vào đúng target bằng cách giải khuỷu, rồi nhắm hai xương.

    Nhắm từng xương tới khớp kế tiếp — cùng cách bộ retarget của dự án làm —
    nên phép xoay quay quanh ĐẦU xương, không quanh gốc toạ độ.
    """
    from mathutils import Matrix, Vector
    mw = arm.matrix_world
    pb_u, pb_l, pb_e = arm.pose.bones[upper], arm.pose.bones[lower], arm.pose.bones[end]
    a = mw @ pb_u.head
    l1 = (mw @ pb_l.head - a).length
    l2 = (mw @ pb_e.head - (mw @ pb_l.head)).length
    to = target - a
    d = min(to.length, (l1 + l2) * 0.995)
    if d < 1e-5:
        return
    dirv = to.normalized()
    cos_a = max(-1.0, min(1.0, (l1 * l1 + d * d - l2 * l2) / (2 * l1 * d)))
    ang = math.acos(cos_a)
    axis = dirv.cross(pole - a)
    if axis.length < 1e-5:
        axis = dirv.cross(Vector((0.0, 0.0, 1.0)))
    axis.normalize()
    elbow = a + (Matrix.Rotation(ang, 4, axis) @ dirv) * l1

    for bone, child_pos in ((upper, elbow), (lower, a + dirv * d)):
        pb = arm.pose.bones[bone]
        head = mw @ pb.head
        cur = (mw @ arm.pose.bones[{upper: lower, lower: end}[bone]].head) - head
        want = child_pos - head
        if cur.length < 1e-6 or want.length < 1e-6:
            continue
        q = cur.normalized().rotation_difference(want.normalized())
        m = q.to_matrix().to_4x4() @ pb.matrix
        m.translation = pb.matrix.translation
        pb.matrix = m
        bpy.context.view_layer.update()


def make_shoot_clip():
    """Dựng thêm một đoạn: giương cung, buông dây, mũi tên bay đi rồi mất."""
    from mathutils import Matrix, Vector
    arm = next((o for o in bpy.data.objects if o.type == 'ARMATURE'), None)
    if arm is None:
        return
    base = bpy.data.actions.get('03_NangCung')
    if base is None:
        return

    ad = arm.animation_data
    ad.action = base
    if getattr(base, 'slots', None):
        ad.action_slot = base.slots[0]
    bpy.context.scene.frame_set(1)
    bpy.context.view_layer.update()
    ready = {pb.name: (pb.rotation_quaternion.copy(), pb.location.copy())
             for pb in arm.pose.bones}

    mw = arm.matrix_world
    g = lambda n: mw @ arm.pose.bones[n].head
    hips, head = g('mixamorig:Hips'), g('mixamorig:Head')
    grip = g('mixamorig:Left_arch1')
    aim = Vector((grip.x - hips.x, grip.y - hips.y, 0.0)).normalized()
    lateral = aim.cross(Vector((0.0, 0.0, 1.0))).normalized()
    reach = ((g('mixamorig:LeftForeArm') - g('mixamorig:LeftArm')).length
             + (g('mixamorig:LeftHand') - g('mixamorig:LeftForeArm')).length)
    l_sh, r_sh = g('mixamorig:LeftArm'), g('mixamorig:RightArm')
    chin = head + Vector((0.0, 0.0, -0.06)) + aim * 0.02

    act = bpy.data.actions.new(SHOOT_NAME)
    ad.action = act
    if getattr(act, 'slots', None):
        ad.action_slot = act.slots[0]

    spine2 = arm.pose.bones['mixamorig:Spine2']
    arrow_pb = arm.pose.bones['mixamorig:arrow']
    arrow_rest_local = (arrow_pb.location.copy(), arrow_pb.rotation_quaternion.copy())

    last = SHOOT_KEYS[-1][0]
    for t, extend, pull in SHOOT_KEYS:
        f = int(round(t * SHOOT_FPS)) + 1
        for pb in arm.pose.bones:            # bắt đầu lại từ tư thế thủ
            q, loc = ready[pb.name]
            pb.rotation_quaternion = q.copy()
            pb.location = loc.copy()
        bpy.context.view_layer.update()

        bow_target = l_sh + aim * (reach * extend) + Vector((0.0, 0.0, 0.06))
        _two_bone_ik(arm, 'mixamorig:LeftArm', 'mixamorig:LeftForeArm',
                     'mixamorig:LeftHand', bow_target,
                     l_sh + lateral * 0.4 + Vector((0.0, 0.0, -0.5)))
        string_target = chin - aim * pull + lateral * 0.03
        _two_bone_ik(arm, 'mixamorig:RightArm', 'mixamorig:RightForeArm',
                     'mixamorig:RightHand', string_target,
                     r_sh - aim * 0.3 + lateral * 0.35)

        for pb in arm.pose.bones:
            pb.keyframe_insert(data_path='rotation_quaternion', frame=f)
        arm.pose.bones['mixamorig:Hips'].keyframe_insert(data_path='location', frame=f)

    # --- mũi tên: bám cung tới lúc buông, sau đó bay thẳng rồi thu về 0 ---
    n_frames = int(round(last * SHOOT_FPS)) + 1
    rel_f = int(round(RELEASE_T * SHOOT_FPS)) + 1
    gone_f = rel_f + int(round(ARROW_GONE * SHOOT_FPS))
    for f in range(1, n_frames + 1):
        bpy.context.scene.frame_set(f)
        bpy.context.view_layer.update()
        s2 = mw @ spine2.matrix                     # hệ của xương cha
        hand = mw @ arm.pose.bones['mixamorig:LeftHand'].head
        if f <= rel_f:
            pos, scale = hand + aim * 0.10, 1.0
        else:
            dt = (f - rel_f) / SHOOT_FPS
            pos = hand + aim * (0.10 + ARROW_SPEED * dt)
            scale = max(0.0, 1.0 - (f - rel_f) / max(1, gone_f - rel_f))
        local = s2.inverted() @ Matrix.Translation(pos)
        arrow_pb.location = local.translation
        arrow_pb.scale = (scale, scale, scale)
        arrow_pb.keyframe_insert(data_path='location', frame=f)
        arrow_pb.keyframe_insert(data_path='scale', frame=f)

    act.use_fake_user = True
    print('    dựng %s: %d khung, buông ở khung %d, mũi tên tắt ở khung %d'
          % (SHOOT_NAME, n_frames, rel_f, gone_f))
    return act


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

    print('>>> Lắp mũi tên và dọn hoạt ảnh')
    hide_arrow() if HIDE_ARROW else put_arrow_in_quiver()
    drop_duplicate_actions()
    split_long_clip()
    shoot = make_shoot_clip() if MAKE_SHOOT else None
    if shoot is not None:
        ad = next(o for o in bpy.data.objects if o.type == 'ARMATURE').animation_data
        ad.action = None
        track = ad.nla_tracks.new()
        track.name = SHOOT_NAME
        track.strips.new(SHOOT_NAME, 1, shoot)

    os.makedirs(OUT_DIR, exist_ok=True)
    out = os.path.join(OUT_DIR, 'char6.glb')
    print('>>> Xuất %s' % out)
    bpy.ops.export_scene.gltf(
        filepath=out, export_format='GLB',
        export_animations=True, export_nla_strips=True,
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
        export_animations=True, export_nla_strips=True,
        export_skins=True, export_morph=False,
        export_draco_mesh_compression_enable=False)
    print('>>> Xong: %.2f MB (nén Draco) · %.2f MB (bản nhúng)'
          % (os.path.getsize(out) / 1048576, os.path.getsize(web) / 1048576))


if __name__ == '__main__':
    main()
