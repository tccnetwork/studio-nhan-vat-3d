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
HIDE_ARROW = False

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


# Mốc thời gian của chu trình bắn trong đoạn 03, đọc từ ảnh dựng dày:
#   0,33-0,50  với tay ra sau vai lấy tên
#   0,50-0,70  đưa xuống lắp vào cung
#   0,70-1,10  giương, dây căng hình chữ V
#   ~1,10      buông
SHOT_CLIP = '03_BanCung'
DEATH_CLIP = '02_GucNga'
T_GRAB = 0.36        # giây, tay chạm ống tên
T_NOCK = 0.62        # giây, tên đã nằm trên dây
# Buông ở 1,02 chứ không phải 1,10: đoạn chỉ dài 1,20 giây, buông muộn thì mũi
# tên chỉ còn hai khung để bay và mắt không kịp thấy gì.
T_LOOSE = 1.02       # giây, buông dây
# Tên thật bay 60 m/s. Ở đây chậm hơn nhiều, vì trong sáu khung còn lại mà bay
# đúng tốc độ thật thì nó đi 12 mét, tức biến mất ngay khung đầu tiên.
FLY_SPEED = 15.0     # m/s
FLY_FADE = 0.16      # giây để thu nhỏ về 0 sau khi bay


def animate_arrow_shot():
    """Cho mũi tên hiện ra đúng lúc và bay đi khi buông dây.

    Ba chặng, đều bám theo vị trí THẬT của bàn tay và tay cầm cung ở từng khung
    chứ không đặt toạ độ cứng:

      ẩn        trước khi với tay lấy tên, và trong ba đoạn còn lại
      trên tay  từ lúc chạm ống tên tới lúc lắp xong
      trên dây  từ lúc lắp tới lúc buông: gốc ở tay kéo, mũi chỉ qua tay cầm cung
      bay       sau khi buông: đi thẳng theo hướng bắn rồi thu nhỏ về 0
    """
    from mathutils import Matrix, Vector
    arm = next((o for o in bpy.data.objects if o.type == 'ARMATURE'), None)
    mesh = bpy.data.objects.get('arrow')
    act = bpy.data.actions.get(SHOT_CLIP)
    if arm is None or mesh is None or act is None:
        return
    ad = arm.animation_data
    mw = arm.matrix_world
    pb = arm.pose.bones[ARROW_BONE]

    # Ma trận NGHỈ phải lấy từ data.bones, không phải từ pose.bones. Gỡ action
    # ra KHÔNG đặt lại tư thế: các kênh pose vẫn giữ nguyên giá trị cuối cùng,
    # nên pb.matrix lúc đó là một tư thế bất kỳ chứ không phải tư thế nghỉ.
    # Đo được hậu quả: mũi tên lệch đúng 62° ở mọi khung.
    rest_bone = arm.data.bones[ARROW_BONE].matrix_local.copy()
    pts = [mesh.matrix_world @ v.co for v in mesh.data.vertices]
    centre, own, _len, half = _long_axis(pts)   # trục lấy từ hình học, không đoán
    own = _tip_direction(pts, centre, own)      # và chiều lấy từ bề ngang hai đầu
    half = max((p - centre).dot(own) for p in pts)

    ad.action = act
    if getattr(act, 'slots', None):
        ad.action_slot = act.slots[0]

    def place(nock_at, direction, scale):
        """Đặt gốc mũi tên vào nock_at, mũi chỉ theo direction."""
        d = direction.normalized()
        rot = own.rotation_difference(d).to_matrix().to_4x4()
        want = Matrix.Translation(nock_at + d * half) @ rot @ Matrix.Translation(-centre)
        m = mw.inverted() @ want @ mw @ rest_bone
        pb.matrix = m
        pb.scale = (scale, scale, scale)

    fps = 30.0
    n = int(act.frame_range[1])
    loose_f = int(round(T_LOOSE * fps)) + 1
    fly_dir = None
    fly_from = None
    for f in range(1, n + 1):
        bpy.context.scene.frame_set(f)
        bpy.context.view_layer.update()
        t = (f - 1) / fps
        g = lambda nm: mw @ arm.pose.bones[nm].head
        rh, grip = g('mixamorig:RightHand'), g('mixamorig:Left_arch1')

        if t < T_GRAB:
            pb.scale = (0.0, 0.0, 0.0)
        elif t < T_NOCK:
            # cầm trên tay, mũi hướng về phía cung
            place(rh, (grip - rh), 1.0)
        elif f <= loose_f:
            place(rh, (grip - rh), 1.0)
            fly_dir = (grip - rh).normalized()
            fly_from = grip
        else:
            dt = (f - loose_f) / fps
            scale = max(0.0, 1.0 - dt / FLY_FADE)
            place(fly_from + fly_dir * (FLY_SPEED * dt), fly_dir, scale)

        pb.keyframe_insert(data_path='location', frame=f)
        pb.keyframe_insert(data_path='rotation_quaternion', frame=f)
        pb.keyframe_insert(data_path='scale', frame=f)

        if f in (20, 26, 30):            # kiểm ngay tại chỗ, không tin phép suy
            bpy.context.view_layer.update()
            dg = bpy.context.evaluated_depsgraph_get()
            em = mesh.evaluated_get(dg)
            md = em.to_mesh()
            wp = [em.matrix_world @ v.co for v in md.vertices]
            em.to_mesh_clear()
            cc, vv, _l, _h = _long_axis(wp)
            dd = (grip - rh).normalized()
            vv = _tip_direction(wp, cc, vv)
            a = math.degrees(vv.angle(dd))
            print('      khung %d: mũi chỉ %.2f %.2f %.2f | muốn %.2f %.2f %.2f'
                  ' | lệch %.0f° (đã tính cả chiều)'
                  % (f, vv.x, vv.y, vv.z, dd.x, dd.y, dd.z, a))

    # Ba đoạn còn lại: giấu hẳn mũi tên đi.
    for other in bpy.data.actions:
        if other.name == SHOT_CLIP:
            continue
        end = int(other.frame_range[1])
        path = 'pose.bones["%s"].scale' % ARROW_BONE
        for i in range(3):
            # Đường cong này đã có sẵn từ lúc cắt đoạn, tạo lại là lỗi.
            fc = next((f for f in other.fcurves
                       if f.data_path == path and f.array_index == i), None)
            if fc is None:
                fc = other.fcurves.new(path, index=i)
            else:
                # clear() chứ không remove() từng cái: xoá trong lúc duyệt thì
                # chỉ số trượt và Blender báo "Keyframe not in F-Curve".
                fc.keyframe_points.clear()
            for fr in (1, end):
                kp = fc.keyframe_points.insert(fr, 0.0)
                kp.interpolation = 'CONSTANT'
            fc.update()
    print('    mũi tên: hiện ở %.2fs, lắp lúc %.2fs, buông ở khung %d, '
          'tắt sau %.2fs; ba đoạn kia giấu hẳn'
          % (T_GRAB, T_NOCK, loose_f, FLY_FADE))


def trim_death_tail(rise=0.08):
    """Cắt mấy khung cuối của đoạn gục ngã, chỗ nhân vật bật dậy.

    File gốc nối các take liền nhau nên sau khi ngã xuống, pose lập tức kéo về
    thế đứng để vào take sau. Đo được: hông nằm yên ở 0,14-0,15 m suốt mười mấy
    khung rồi vọt lên 0,35 - 0,51 - 0,68 - 0,84 ở bốn khung cuối. Giữ nguyên
    thì nhân vật vừa chết xong đã bật dậy.
    """
    arm = next((o for o in bpy.data.objects if o.type == 'ARMATURE'), None)
    act = bpy.data.actions.get(DEATH_CLIP)
    if arm is None or act is None:
        return
    ad = arm.animation_data
    ad.action = act
    if getattr(act, 'slots', None):
        ad.action_slot = act.slots[0]
    n = int(act.frame_range[1])
    zs = []
    for f in range(1, n + 1):
        bpy.context.scene.frame_set(f)
        dg = bpy.context.evaluated_depsgraph_get()
        ev = arm.evaluated_get(dg)
        zs.append((ev.matrix_world @ ev.pose.bones['mixamorig:Hips'].head).z)
    lo = min(zs)
    cut = n
    for f in range(n, 0, -1):
        if zs[f - 1] <= lo + rise:
            cut = f
            break
    if cut >= n:
        return
    # Xoá từng khoá trong lúc duyệt thì chỉ số trượt và Blender báo "Keyframe
    # not in F-Curve". Giữ lại phần cần rồi dựng lại cả đường cong.
    for fc in act.fcurves:
        keep = [(kp.co[0], kp.co[1]) for kp in fc.keyframe_points
                if kp.co[0] <= cut + 0.5]
        fc.keyframe_points.clear()
        for x, y in keep:
            kp = fc.keyframe_points.insert(x, y)
            kp.interpolation = 'LINEAR'
        fc.update()
    print('    cắt đuôi %s: bỏ %d khung bật dậy, còn %d khung (hông nằm ở %.2f m)'
          % (DEATH_CLIP, n - cut, cut, lo))


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


def _tip_direction(pts, centre, axis):
    """Đầu nào của mũi tên là MŨI NHỌN.

    Trục chính chỉ cho biết đường thẳng, không cho biết chiều. Nhận ra bằng bề
    ngang: đuôi có ba cánh lông xoè rộng, mũi thì thu nhọn. So bán kính trung
    bình quanh trục ở 20% chiều dài mỗi đầu — đầu nào mảnh hơn là mũi.
    """
    ext = [(p - centre).dot(axis) for p in pts]
    lo, hi = min(ext), max(ext)
    span = hi - lo
    if span < 1e-6:
        return axis

    def spread(sel):
        rs = []
        for p, e in zip(pts, ext):
            if not sel(e):
                continue
            radial = (p - centre) - axis * e
            rs.append(radial.length)
        return sum(rs) / len(rs) if rs else 0.0

    front = spread(lambda e: e > hi - span * 0.20)
    back = spread(lambda e: e < lo + span * 0.20)
    return axis if front <= back else -axis


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
# số đo. Lần đầu tôi đặt tên theo cao độ bàn tay và sai cả bốn; lần thứ hai
# xem sáu khung thưa của đoạn 3 và vẫn đọc sai thành "nâng cung rồi hạ".
# Dựng dày chín khung mỗi nửa mới thấy: 0,78-1,08 giây dây cung căng hình chữ
# V, tay phải kéo về sau, rồi 1,14 giây buông. ĐÓ LÀ MỘT CHU TRÌNH BẮN ĐẦY ĐỦ.
SEGMENTS = [
    ('01_DungYen',     1,  62),   # đứng thở tại chỗ
    ('02_GucNga',     62, 138),   # trúng đòn, ngã ngửa, nằm sấp dưới đất
    ('03_BanCung',   138, 173),   # với tay lấy tên, lắp, giương, buông dây
    ('04_TrungDon',  173, 202),   # giật người vì trúng đòn rồi đứng lại
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


def push_actions_to_nla():
    """Đẩy mọi action lên strip NLA — bộ xuất glTF chỉ lấy hoạt ảnh từ đó.

    Phải gọi SAU CÙNG. Trước đây bước này nằm ngay trong split_long_clip, và
    hậu quả rất khó thấy: mọi hàm sau đó muốn đọc tư thế NGHỈ đều đặt
    animation_data.action = None, nhưng NLA vẫn đang điều khiển bộ xương nên
    thứ đọc được là một tư thế bất kỳ. Đo được: mũi tên lệch đúng 62° ở mọi
    khung vì mốc nghỉ của nó lấy nhầm.
    """
    arm = next((o for o in bpy.data.objects if o.type == 'ARMATURE'), None)
    if arm is None:
        return
    if not arm.animation_data:
        arm.animation_data_create()
    ad = arm.animation_data
    ad.action = None
    for t in list(ad.nla_tracks):
        ad.nla_tracks.remove(t)
    for act in sorted(bpy.data.actions, key=lambda a: a.name):
        track = ad.nla_tracks.new()
        track.name = act.name
        track.strips.new(act.name, 1, act)
    print('    đẩy %d action lên NLA' % len(bpy.data.actions))


# ---- Khẩu hình chớp mắt và mỉm cười -------------------------------------
#
# Model không có sẵn một morph target nào, nên hai khẩu hình này được nặn từ
# hình học. Đầu có 4432 đỉnh, mỗi mắt 277 đỉnh quanh nó, vùng miệng 1416 —
# thừa mật độ để biến dạng mà không rách.
#
# Mốc đo từ mặt cắt dọc giữa mặt: mắt z 1,646-1,680; mũi nhô nhất ở z 1,627;
# môi ở z ~1,605 (chỗ mặt nhô lại lần nữa sau khi lõm dưới mũi).
FACE_MESH = 'HeadAndHand'
EYE_R = 0.026            # mét, bán kính vùng mí bị kéo
BLINK_PUSH = 0.0015      # đẩy mí ra trước cho ôm cầu mắt
MOUTH_Z = 1.605
MOUTH_X = 0.021          # nửa bề rộng miệng
# Vùng ảnh hưởng hình BẦU DỤC: rộng ngang, hẹp dọc. Dùng hình tròn bán kính
# 24 mm thì nó với lên tới z 1,629, tức chạm cánh mũi (mũi nhô nhất ở 1,627) —
# nhìn ra ngay là mũi bị kéo méo khi cười hết mức.
MOUTH_RX = 0.027
MOUTH_RZ = 0.013
SMILE_LIFT = 0.0045      # nâng khoé miệng
SMILE_BACK = 0.0020      # kéo khoé ra sau một chút
SMILE_DEFAULT = 0.45     # mức cười giữ thường trực


def _falloff(t):
    """1 ở tâm, 0 ở mép, mượt hai đầu."""
    t = max(0.0, min(1.0, t))
    return 1.0 - (t * t * (3.0 - 2.0 * t))


def add_face_shapes():
    """Nặn hai khẩu hình: nhắm mắt và mỉm cười."""
    from mathutils import Vector
    face = bpy.data.objects.get(FACE_MESH)
    eyes = bpy.data.objects.get('eyes')
    if face is None or eyes is None:
        return
    ep = [eyes.matrix_world @ v.co for v in eyes.data.vertices]
    left = [p for p in ep if p.x > 0]
    right = [p for p in ep if p.x <= 0]
    centres = [sum(g, Vector()) / len(g) for g in (left, right) if g]

    if face.data.shape_keys is None:
        face.shape_key_add(name='Basis', from_mix=False)
    basis = face.data.shape_keys.key_blocks['Basis']
    mw = face.matrix_world
    inv = mw.inverted()

    blink = face.shape_key_add(name='NhamMat', from_mix=False)
    moved = 0
    for i, v in enumerate(face.data.vertices):
        w = mw @ v.co
        for c in centres:
            flat = ((w.x - c.x) ** 2 + (w.z - c.z) ** 2) ** 0.5
            if flat > EYE_R or w.y > c.y + 0.035:
                continue
            k = _falloff(flat / EYE_R)
            if k <= 0.0:
                continue
            # kéo mí về đường ngang giữa mắt: mí trên xuống, mí dưới lên
            tgt = Vector((w.x, w.y - BLINK_PUSH * k, w.z + (c.z - w.z) * k))
            blink.data[i].co = inv @ tgt
            moved += 1
            break

    smile = face.shape_key_add(name='MimCuoi', from_mix=False)
    lifted = 0
    for i, v in enumerate(face.data.vertices):
        w = mw @ v.co
        for sx in (MOUTH_X, -MOUTH_X):
            e = (((w.x - sx) / MOUTH_RX) ** 2 + ((w.z - MOUTH_Z) / MOUTH_RZ) ** 2) ** 0.5
            if e > 1.0 or w.y > -0.075:
                continue
            k = _falloff(e)
            if k <= 0.0:
                continue
            out = 0.0012 if sx > 0 else -0.0012
            tgt = Vector((w.x + out * k,
                          w.y + SMILE_BACK * k,
                          w.z + SMILE_LIFT * k))
            smile.data[i].co = inv @ tgt
            lifted += 1
            break

    blink.value = 0.0
    smile.value = SMILE_DEFAULT
    print('    khẩu hình: NhamMat %d đỉnh, MimCuoi %d đỉnh (cười giữ %.2f)'
          % (moved, lifted, SMILE_DEFAULT))
    return face


BLINK_EVERY = 2.6        # giây giữa hai lần chớp
BLINK_DOWN = 0.06        # giây nhắm lại
BLINK_UP = 0.10          # giây mở ra


def animate_blink(face):
    """Chớp mắt trong từng đoạn, đẩy lên NLA cùng tên để gộp vào cùng clip."""
    keys = face.data.shape_keys
    if keys is None:
        return
    if keys.animation_data is None:
        keys.animation_data_create()
    ad = keys.animation_data
    ad.action = None
    for t in list(ad.nla_tracks):
        ad.nla_tracks.remove(t)
    path = 'key_blocks["NhamMat"].value'
    total = 0
    for act_arm in sorted(bpy.data.actions, key=lambda a: a.name):
        if not act_arm.name[0].isdigit():
            continue
        n = int(act_arm.frame_range[1])
        act = bpy.data.actions.new('blink_' + act_arm.name)
        fc = act.fcurves.new(path)
        fc.keyframe_points.insert(1, 0.0).interpolation = 'LINEAR'
        # Chớp lần đầu ở 35% đoạn, để đoạn ngắn 1 giây cũng có ít nhất một cú.
        # Bản trước đặt lần đầu ở 1,17 giây nên hai đoạn ngắn không chớp lần nào.
        t = max(0.30, (n / 30.0) * 0.35)
        while t * 30 < n - 3:
            f = t * 30
            for off, val in ((-BLINK_DOWN * 30, 0.0), (0, 1.0), (BLINK_UP * 30, 0.0)):
                x = max(1.0, min(float(n), f + off))
                fc.keyframe_points.insert(x, val).interpolation = 'LINEAR'
            total += 1
            t += BLINK_EVERY
        fc.keyframe_points.insert(float(n), 0.0).interpolation = 'LINEAR'
        fc.update()

        # Kênh "weights" của glTF ghi TẤT CẢ trọng số morph cùng lúc. Chỉ khoá
        # mỗi cái chớp mắt thì cái cười bị ghi 0 đè lên và tắt hẳn khi phát —
        # đo được morph=[0.87, 0] trong lúc chớp. Nên phải khoá giữ nó luôn.
        fs = act.fcurves.new('key_blocks["MimCuoi"].value')
        for x in (1.0, float(n)):
            fs.keyframe_points.insert(x, SMILE_DEFAULT).interpolation = 'LINEAR'
        fs.update()
        act.use_fake_user = True
        track = ad.nla_tracks.new()
        track.name = act_arm.name
        # Tên STRIP mới là thứ bộ xuất glTF dùng để gộp, không phải tên action.
        # Đặt tên action là "blink_..." mà để nguyên tên strip thì file ra thêm
        # bốn animation rời tên blink_*, và bấm clip thân thì mắt không chớp.
        strip = track.strips.new(act_arm.name, 1, act)
        strip.name = act_arm.name
    print('    chớp mắt: %d lần trên %d đoạn' % (total, len(ad.nla_tracks)))


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
    if HIDE_ARROW:
        hide_arrow()
    drop_duplicate_actions()
    split_long_clip()
    trim_death_tail()
    if not HIDE_ARROW:
        animate_arrow_shot()
    push_actions_to_nla()
    face = add_face_shapes()
    if face is not None:
        animate_blink(face)
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
        export_skins=True, export_morph=True,
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
        export_skins=True, export_morph=True,
        export_draco_mesh_compression_enable=False)
    print('>>> Xong: %.2f MB (nén Draco) · %.2f MB (bản nhúng)'
          % (os.path.getsize(out) / 1048576, os.path.getsize(web) / 1048576))


if __name__ == '__main__':
    main()
