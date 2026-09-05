# -*- coding: utf-8 -*-
"""Gộp ba file char4 thành một nhân vật hiệp sĩ duy nhất, dựng lại vật liệu.

    /Applications/Blender.app/Contents/MacOS/Blender --background \
        --factory-startup --python scripts/build_char4.py

Ba file nguồn chứa gì
--------------------
char4.fbx    bộ xương đầy đủ nhất (86 xương, có Sword_joint và Shield_joint),
             lưới Body/Helmet/Shield/Sword, và 18 action.
char4_1.fbx  cùng nhân vật, ít xương hơn, một action — không có gì mới.
char4_e.fbx  bảy lưới ở thang 100×. Sáu lưới trong đó KHÔNG phải chi tiết
             thêm: chúng trùng khít từng đỉnh với "Body" của char4 (armor
             2082/2084, head 2014/2014, boots 1066/1066, hai ống tay 693 và
             694). Đó là bản đồ phân vùng của chính lưới thân. Chỉ "trousers"
             mới là hình học mới: váy giáp và giáp đùi, char4.fbx thiếu hẳn.

Nên bản gộp KHÔNG nhập sáu lưới trùng ấy. Chúng được dùng làm bản đồ để gán
vật liệu theo vùng cho một lưới thân duy nhất. Gộp thẳng cả ba file sẽ ra 22571
đỉnh với sáu lớp chồng khít nhau; cách này còn 8926 đỉnh mà nhiều màu hơn.

18 action thật ra là một
------------------------
Trượt từng clip ngắn dọc clip dài rồi so tư thế: cả 13 clip ngắn đều khớp một
đoạn của clip 445 khung với sai lệch dưới 1°. Idle khớp từ khung 1, Walk từ 120,
nhóm "chết" từ 160, Attack từ 240, Attack2 từ 348. Vậy chỉ có một take dài, và
việc cần làm là cắt nó ở đúng chỗ chứ không phải giữ 18 bản.
"""
import math
import os
import sys

import bpy
from mathutils import Matrix, Vector

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_MAIN = os.path.join(ROOT, 'source', 'char4.fbx')
SRC_EXTRA = os.path.join(ROOT, 'source', 'char4_e.fbx')
OUT_DIR = os.path.join(ROOT, 'build', 'char4')
FPS = 30

# Sáu lưới của char4_e dùng làm bản đồ phân vùng cho lưới thân.
REGION_PARTS = ['armor', 'head', 'boots', 'sleeve_left', 'sleeve_right']
REGION_REST = 'conlai'                 # phần thân không thuộc mảnh nào: váy, đùi
EXTRA_MESH = 'trousers'                # hình học mới duy nhất
EXTRA_SCALE = 0.01                     # char4_e ở thang 100×, đo bằng đỉnh

# Bảng màu hiệp sĩ thập tự: thép mài, vải chẽn đỏ thẫm, viền đồng.
#            màu        nhám  kim loại
STEEL      = ('#B4BAC2', 0.26, 1.00)
STEEL_DARK = ('#6E757F', 0.46, 1.00)
STEEL_EDGE = ('#C6CBD2', 0.18, 1.00)
STEEL_ARM  = ('#9AA1AA', 0.34, 1.00)
MAIL       = ('#3F444B', 0.70, 1.00)
CLOTH      = ('#8E2F3A', 0.78, 0.00)
FIELD      = ('#E6E1D3', 0.62, 0.00)
GOLD       = ('#B08D3F', 0.32, 1.00)

# Hai vùng dưới đây tên gọi đánh lừa, phải dựng ảnh định danh mới biết:
# "head" không phải cái đầu — cái đầu nằm gọn trong mũ trụ — mà là cả vùng cổ,
# vai và lưng trên, nên tô màu lưới sẫm thì lưng thành một mảng đen. "conlai"
# sau khi lắp váy giáp chỉ còn vài mảnh vụn ở gấu váy, tô đỏ thì thành đốm lem
# nhem chứ không ra tấm vải nào.
REGION_LOOK = {
    'armor':        ('Giap_Than', STEEL),
    'head':         ('Giap_Vai', STEEL),
    'boots':        ('Giap_Chan', STEEL_DARK),
    'sleeve_left':  ('Bao_Tay_Trai', STEEL_ARM),
    'sleeve_right': ('Bao_Tay_Phai', STEEL_ARM),
    'conlai':       ('Vien_Gau', STEEL_DARK),
}

# Một take dài 445 khung. Mốc cắt đọc từ nhịp đổi tư thế và cao độ hông, rồi
# xác nhận bằng ảnh dựng từng khung quanh mỗi mốc.
SEGMENTS = [
    ('01_ThuThe',    1, 118),   # đứng thủ, hông đứng yên ở 0,80 m
    ('02_DiBo',    119, 155),   # hông dao động 0,77–0,85
    ('03_GucNga',  156, 232),   # hông rơi về 0,11 và nằm im; khung 233 là rác
    ('04_ChemNgang', 236, 270),  # vung kiếm ngang rồi về thế thủ
    ('05_NhayChem',  271, 347),  # lấy đà, bật người, bổ xuống, quỳ gối đỡ
    ('06_DamThang',  348, 414),  # đâm thẳng, tay kiếm duỗi hết
]
LOOP_CLIPS = ('01_ThuThe', '02_DiBo')


def srgb_to_linear(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def hex_rgba(code, alpha=1.0):
    code = code.lstrip('#')
    rgb = [int(code[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]
    return tuple(srgb_to_linear(c) for c in rgb) + (alpha,)


def make_material(name, look):
    color, rough, metal = look
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    b = mat.node_tree.nodes.get('Principled BSDF')
    b.inputs['Base Color'].default_value = hex_rgba(color)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    mat.diffuse_color = hex_rgba(color)
    return mat


def clean():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.scene.render.fps = FPS
    bpy.context.scene.render.fps_base = 1.0


def clear_old_materials():
    """Vật liệu cũ còn giữ nút ảnh trỏ vào thư mục tạm của Mixamo đã biến mất;
    bộ xuất glTF vẫn cố ghi những nút đó ra."""
    for o in bpy.data.objects:
        if o.type == 'MESH':
            o.data.materials.clear()
    for m in list(bpy.data.materials):
        if m.users == 0:
            bpy.data.materials.remove(m)
    for i in list(bpy.data.images):
        if i.users == 0:
            bpy.data.images.remove(i)


def vkey(p):
    return (round(p.x, 4), round(p.y, 4), round(p.z, 4))


def region_map(body, parts):
    """Gán chỉ số vật liệu cho từng mặt của lưới thân theo bản đồ phân vùng.

    Bỏ phiếu theo ĐỈNH của mặt chứ không theo trọng tâm: các mảnh dùng chung
    đường may với thân, nên mặt nằm trên đường may có đỉnh của cả hai vùng —
    lấy vùng chiếm đa số là đúng, còn hoà thì không có nghĩa gì.
    """
    owner = {}
    for i, name in enumerate(REGION_PARTS):
        o = parts.get(name)
        if o is None:
            continue
        for v in o.data.vertices:
            owner[vkey((o.matrix_world @ v.co) * EXTRA_SCALE)] = i
    rest = len(REGION_PARTS)
    mw = body.matrix_world
    vk = [owner.get(vkey(mw @ v.co)) for v in body.data.vertices]
    count = [0] * (rest + 1)
    for poly in body.data.polygons:
        got = [vk[i] for i in poly.vertices if vk[i] is not None]
        idx = max(set(got), key=got.count) if got else rest
        poly.material_index = idx
        count[idx] += 1
    names = REGION_PARTS + [REGION_REST]
    print('    phân vùng lưới thân: %s'
          % ', '.join('%s %d mặt' % (n, c) for n, c in zip(names, count)))
    return names


def bring_extra(arm, obj):
    """Đưa váy giáp từ char4_e sang bộ xương của char4.

    Dữ liệu lưới nằm trong hệ Y-up, phép xoay về Z-up nằm ở đối tượng cha. Nên
    không đặt được ma trận đơn vị; phải nhân đúng phép đã kiểm bằng đỉnh —
    ma trận thế giới nhân 0,01.
    """
    mw = Matrix.Scale(EXTRA_SCALE, 4) @ obj.matrix_world
    obj.parent = arm
    obj.matrix_parent_inverse = arm.matrix_world.inverted()
    obj.matrix_world = mw
    for m in list(obj.modifiers):
        obj.modifiers.remove(m)
    mod = obj.modifiers.new('Armature', 'ARMATURE')
    mod.object = arm
    bpy.context.view_layer.update()
    return obj


def _dirs():
    """Mười bốn hướng phủ đều quanh một điểm: sáu trục và tám đường chéo."""
    out = [Vector(d) for d in ((1, 0, 0), (-1, 0, 0), (0, 1, 0),
                               (0, -1, 0), (0, 0, 1), (0, 0, -1))]
    for x in (1, -1):
        for y in (1, -1):
            for z in (1, -1):
                out.append(Vector((x, y, z)).normalized())
    return out


DIRS = _dirs()


def push_out(obj, mm=8.0):
    """Đẩy lớp ngoài ra khỏi lớp trong theo pháp tuyến đỉnh.

    Váy giáp và váy của lưới thân KHÔNG lớp nào nằm trong lớp nào — chúng đan
    xuyên qua nhau, nên mọi phép "xoá phần bị che" đều bắt được vài mặt rồi
    thôi, còn lại đá nhau về độ sâu thành mảng lởm chởm khi xoay. Đẩy hẳn lớp
    ngoài ra thì hết chồng chéo, và khi đó phần thân bên dưới mới thật sự nằm
    trong để xoá đi được.

    Toạ độ đỉnh nằm trong hệ riêng của đối tượng, ở đây 1 đơn vị = 1 cm.
    """
    from mathutils import Vector as V
    unit = (obj.matrix_world.to_3x3() @ V((1.0, 0.0, 0.0))).length
    d = (mm / 1000.0) / unit
    obj.data.calc_normals_split() if hasattr(obj.data, 'calc_normals_split') else None
    for v in obj.data.vertices:
        v.co = v.co + v.normal * d
    obj.data.update()
    print('    đẩy %s ra %.0f mm theo pháp tuyến' % (obj.name, mm))


def strip_under(body, cover, margin_mm=1.0):
    """Xoá mặt thân nằm hẳn bên trong một lớp phủ KÍN.

    Chỉ dùng được với khối kín. Váy giáp là một ống khép nên hợp lệ; mũ trụ hở
    đáy thì không, thử rồi và bản dựng thủng lỗ ở vai.

    closest_point_on_mesh trả về khoảng cách trong hệ toạ độ riêng của đối
    tượng, mà lưới này gắn vào bộ xương tỉ lệ 0,01 — không quy đổi thì ngưỡng
    một milimét thành mười xăng-ti-mét.
    """
    import bmesh
    from mathutils import Vector as V
    mw = body.matrix_world
    inv = cov_inv = cover.matrix_world.inverted()
    unit = 1.0 / (cover.matrix_world.to_3x3() @ V((1.0, 0.0, 0.0))).length
    bb = [cover.matrix_world @ V(c) for c in cover.bound_box]
    lo = V((min(p[i] for p in bb) for i in range(3)))
    hi = V((max(p[i] for p in bb) for i in range(3)))
    doomed = []
    for poly in body.data.polygons:
        w = mw @ poly.center
        if any(w[i] < lo[i] or w[i] > hi[i] for i in range(3)):
            continue
        ok, loc, nor, _i = cover.closest_point_on_mesh(inv @ w)
        if not ok:
            continue
        d = loc - (inv @ w)
        if d.dot(nor) > 0 and d.length / unit > margin_mm / 1000.0:
            doomed.append(poly.index)
    if not doomed:
        print('    không có mặt nào nằm dưới %s' % cover.name)
        return
    bm = bmesh.new()
    bm.from_mesh(body.data)
    bm.faces.ensure_lookup_table()
    for i in doomed:
        bm.faces[i].tag = True
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.tag], context='FACES')
    before = len(body.data.polygons)
    bm.to_mesh(body.data)
    bm.free()
    body.data.update()
    print('    bỏ %d mặt nằm dưới %s (%d -> %d mặt)'
          % (len(doomed), cover.name, before, len(body.data.polygons)))


def strip_hidden(body, covers, reach=0.30, weld_mm=3.0):
    """Xoá mặt của lưới thân mà không góc nhìn nào thấy được.

    Một mặt chỉ nhìn được từ BÁN CẦU phía pháp tuyến của nó. Nên phép thử là:
    trong các hướng thuộc bán cầu ấy, có hướng nào thoát ra ngoài không. Không
    thoát hướng nào thì mặt vô hình, xoá được.

    Hai cái bẫy ở đây:

    Đơn vị. ray_cast và closest_point_on_mesh làm việc trong hệ toạ độ RIÊNG
    của đối tượng, mà các lưới này gắn vào bộ xương tỉ lệ 0,01 — truyền thẳng
    0,30 m vào tham số distance thì thành 3 mm, không tia nào chạm được gì và
    phép thử báo "không có mặt nào khuất".

    Vỏ hở. Phép "điểm nằm trong khối" bằng closest_point_on_mesh nhận bừa cả
    mặt ngực lẫn mặt vai, vì mũ trụ hở đáy; bản dựng ra thủng lỗ ở vai. Bắn tia
    thì không dính lỗi đó.
    """
    import bmesh
    mw = body.matrix_world
    n3 = mw.to_3x3()
    inv = [c.matrix_world.inverted() for c in covers]
    # tỉ lệ từ mét của thế giới sang đơn vị riêng của mỗi lớp phủ
    unit = [1.0 / (c.matrix_world.to_3x3() @ Vector((1.0, 0.0, 0.0))).length
            for c in covers]
    hidden, welded = [], []
    for poly in body.data.polygons:
        w = mw @ poly.center
        nw = (n3 @ poly.normal).normalized()
        front = [d for d in DIRS if d.dot(nw) > 0.1]
        open_dir = False
        for d in front:
            hit = False
            for c, iv, k in zip(covers, inv, unit):
                s3 = iv.to_3x3()
                ok, _l, _n, _i = c.ray_cast(iv @ w, (s3 @ d).normalized(),
                                            distance=reach * k)
                if ok:
                    hit = True
                    break
            if not hit:
                open_dir = True
                break
        if not open_dir and front:
            hidden.append(poly.index)
            continue
        for c, iv, k in zip(covers, inv, unit):
            ok, loc, nor, _i = c.closest_point_on_mesh(iv @ w)
            if not ok:
                continue
            if ((loc - (iv @ w)).length / k < weld_mm / 1000.0
                    and (c.matrix_world.to_3x3() @ nor).normalized().dot(nw) > 0.6):
                welded.append(poly.index)
                break
    doomed = sorted(set(hidden) | set(welded))
    if not doomed:
        print('    không có mặt nào khuất')
        return
    bm = bmesh.new()
    bm.from_mesh(body.data)
    bm.faces.ensure_lookup_table()
    for i in doomed:
        bm.faces[i].tag = True
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.tag], context='FACES')
    before = len(body.data.polygons)
    bm.to_mesh(body.data)
    bm.free()
    body.data.update()
    print('    bỏ %d mặt: %d bị che kín, %d trùng khít (%d -> %d mặt)'
          % (len(doomed), len(hidden), len(welded), before,
             len(body.data.polygons)))


def plate_frame(obj, anchor):
    """Hệ trục riêng của một tấm: pháp tuyến tấm và hai trục trong mặt phẳng.

    Lấy bằng phân tích trục chính của đám đỉnh, KHÔNG lấy tổng pháp-tuyến-nhân-
    diện-tích: với một vỏ kín tổng ấy triệt tiêu về 0, còn với vỏ hở nó ra một
    hướng vô nghĩa. Phương sai nhỏ nhất là bề dày tấm, lớn nhất là trục dài.

    Chiều của pháp tuyến hỏi xương cầm: mặt trong là mặt quay về phía cánh tay.
    Đầu nào của trục dài là đầu trên thì đo bề ngang hai nửa — khiên hình giọt
    nước phình ở trên, thóp ở dưới.
    """
    mw = obj.matrix_world
    pts = [mw @ v.co for v in obj.data.vertices]
    c = sum(pts, Vector()) / len(pts)
    cov = [[sum(d[i] * d[j] for d in (p - c for p in pts)) for j in range(3)]
           for i in range(3)]
    vals, vecs = _eigen3(cov)
    order = sorted(range(3), key=lambda k: vals[k])
    n = Vector(vecs[order[0]]).normalized()      # phương sai nhỏ nhất
    u = Vector(vecs[order[2]]).normalized()      # trục dài
    if n.dot((c - anchor).normalized()) < 0.0:
        n = -n
    u = (u - n * u.dot(n)).normalized()
    v = n.cross(u).normalized()
    hi = [abs((p - c).dot(v)) for p in pts if (p - c).dot(u) > 0]
    lo = [abs((p - c).dot(v)) for p in pts if (p - c).dot(u) <= 0]
    if hi and lo and sum(hi) / len(hi) < sum(lo) / len(lo):
        u = -u                                   # đầu phình là đầu trên
        v = n.cross(u).normalized()
    return n, u, v, c


def _eigen3(m):
    """Trị riêng và vector riêng của ma trận đối xứng 3×3, bằng phép quay
    Jacobi. Viết tay vì Blender rời không kèm numpy."""
    a = [row[:] for row in m]
    v = [[1.0 if i == j else 0.0 for j in range(3)] for i in range(3)]
    for _ in range(50):
        p, q, off = 0, 1, 0.0
        for i in range(3):
            for j in range(i + 1, 3):
                if abs(a[i][j]) > off:
                    off, p, q = abs(a[i][j]), i, j
        if off < 1e-12:
            break
        theta = (a[q][q] - a[p][p]) / (2.0 * a[p][q])
        t = (1.0 if theta >= 0 else -1.0) / (abs(theta) + math.sqrt(theta * theta + 1.0))
        c = 1.0 / math.sqrt(t * t + 1.0)
        s = t * c
        for k in range(3):
            akp, akq = a[k][p], a[k][q]
            a[k][p], a[k][q] = c * akp - s * akq, s * akp + c * akq
        for k in range(3):
            apk, aqk = a[p][k], a[q][k]
            a[p][k], a[q][k] = c * apk - s * aqk, s * apk + c * aqk
        for k in range(3):
            vkp, vkq = v[k][p], v[k][q]
            v[k][p], v[k][q] = c * vkp - s * vkq, s * vkp + c * vkq
    return [a[i][i] for i in range(3)], [[v[0][k], v[1][k], v[2][k]] for k in range(3)]


CROSS_BAR = 0.20          # nửa bề rộng thanh dọc, theo nửa bề ngang khiên
CROSS_ARM_AT = 0.22       # tâm thanh ngang, tính từ tâm khiên lên phía đầu phình
CROSS_ARM = 0.16          # nửa bề dày thanh ngang
CROSS_REACH = 0.66        # thanh ngang vươn ra tới đâu theo bề ngang


def paint_shield(obj, arm, cuts=3):
    """Vẽ chữ thập lên khiên bằng hình học, vì không có texture nào để dán.

    Chỉ chia nhỏ MẶT TRƯỚC. Chia cả vỏ thì 54 mặt thành 3456 — riêng cái khiên
    chiếm hơn một phần tư số đỉnh của cả nhân vật, trong khi mặt sau và cạnh
    tấm không cần chi tiết gì.
    """
    import bmesh
    joint = arm.data.bones.get('mixamorig:Shield_joint')
    anchor = (arm.matrix_world @ joint.parent.head_local
              if joint is not None and joint.parent is not None
              else arm.matrix_world @ arm.data.bones['mixamorig:Hips'].head_local)
    n, u, v, c = plate_frame(obj, anchor)

    mw = obj.matrix_world
    n3 = mw.to_3x3()
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.faces.ensure_lookup_table()
    front = [f for f in bm.faces if (n3 @ f.normal).normalized().dot(n) > 0.5]
    edges = {e for f in front for e in f.edges}
    for _ in range(cuts):
        res = bmesh.ops.subdivide_edges(bm, edges=list(edges), cuts=1,
                                        use_grid_fill=True)
        edges = {g for g in res['geom_inner'] if isinstance(g, bmesh.types.BMEdge)}
        edges |= {e for g in res['geom_split'] if isinstance(g, bmesh.types.BMEdge)
                  for e in [g]}
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()

    pts = [mw @ vv.co for vv in obj.data.vertices]
    hu = max(abs((p - c).dot(u)) for p in pts) or 1.0
    hv = max(abs((p - c).dot(v)) for p in pts) or 1.0
    obj.data.materials.clear()
    for name, look in (('Khien_Nen', FIELD), ('Khien_Thap', CLOTH),
                       ('Khien_Vien', GOLD), ('Khien_Lung', STEEL_DARK)):
        obj.data.materials.append(make_material(name, look))
    tally = [0, 0, 0, 0]
    for poly in obj.data.polygons:
        d = (mw @ poly.center) - c
        f = (n3 @ poly.normal).normalized().dot(n)
        if f < -0.5:
            idx = 3
        elif abs(f) <= 0.5:
            idx = 2
        else:
            a, b = d.dot(u) / hu, d.dot(v) / hv
            bar = abs(b) < CROSS_BAR
            crossarm = abs(a - CROSS_ARM_AT) < CROSS_ARM and abs(b) < CROSS_REACH
            idx = 1 if (bar or crossarm) else 0
        poly.material_index = idx
        tally[idx] += 1
    print('    khiên: %d mặt; nền %d, chữ thập %d, viền %d, lưng %d'
          % (len(obj.data.polygons), *tally))


def paint_sword(obj, arm, grip=0.30):
    """Chia lưỡi và chuôi theo trục dài của thanh kiếm.

    Đầu nào là chuôi thì hỏi xương Sword_joint chứ không đoán: chuôi là đầu
    nằm gần khớp cầm.
    """
    mw = obj.matrix_world
    pts = [mw @ v.co for v in obj.data.vertices]
    centre = sum(pts, Vector()) / len(pts)
    best, axis = -1.0, Vector((0, 0, 1))
    for cand in (Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))):
        s = sum(abs((p - centre).dot(cand)) for p in pts)
        if s > best:
            best, axis = s, cand
    ts = [(p - centre).dot(axis) for p in pts]
    lo, hi = min(ts), max(ts)
    joint = arm.pose.bones.get('mixamorig:Sword_joint')
    jt = ((arm.matrix_world @ joint.head) - centre).dot(axis) if joint else lo
    near_lo = abs(jt - lo) < abs(jt - hi)

    obj.data.materials.clear()
    obj.data.materials.append(make_material('Kiem_Luoi', STEEL_EDGE))
    obj.data.materials.append(make_material('Kiem_Chuoi', GOLD))
    n = 0
    for poly in obj.data.polygons:
        t = ((mw @ poly.center) - centre).dot(axis)
        frac = (t - lo) / (hi - lo) if hi > lo else 0.0
        is_grip = frac < grip if near_lo else frac > 1.0 - grip
        poly.material_index = 1 if is_grip else 0
        n += is_grip
    print('    kiếm: %d mặt chuôi / %d mặt, chuôi ở đầu %s'
          % (n, len(obj.data.polygons), 'thấp' if near_lo else 'cao'))


def split_master(arm):
    """Cắt take 445 khung thành sáu clip, đổi gốc khung về 1."""
    src = max(bpy.data.actions, key=lambda a: a.frame_range[1])
    print('    take gốc %d khung' % int(src.frame_range[1]))
    keep = {}
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
        keep[name] = hi - lo + 1
    for a in list(bpy.data.actions):
        if a.name not in keep:
            bpy.data.actions.remove(a)
    print('    cắt thành %d clip: %s'
          % (len(keep), ', '.join('%s %d khung' % kv for kv in keep.items())))


def loop_clip(arm, name):
    """Hoà đuôi clip về khung đầu cho lặp không giật."""
    act = bpy.data.actions.get(name)
    if act is None:
        return
    ad = arm.animation_data
    ad.action = act
    if getattr(act, 'slots', None):
        ad.action_slot = act.slots[0]
    scene = bpy.context.scene
    n = int(act.frame_range[1])
    bones = [pb for pb in arm.pose.bones
             if any(fc.data_path == 'pose.bones["%s"].rotation_quaternion' % pb.name
                    for fc in act.fcurves)]
    if not bones or n < 8:
        return

    def snap(f):
        scene.frame_set(f)
        bpy.context.view_layer.update()
        return {pb.name: pb.rotation_quaternion.copy() for pb in bones}

    def gap(a, b):
        return sum(math.degrees(2 * math.acos(min(1.0, abs(a[k].dot(b[k])))))
                   for k in a)

    head = snap(1)
    tail = snap(n)
    steps, prev = [], head
    for f in range(2, n + 1):
        cur = snap(f)
        steps.append(gap(prev, cur))
        prev = cur
    steps.sort()
    step = max(0.3, steps[len(steps) // 2])
    blend = max(3, min(int(math.ceil(gap(tail, head) / (0.6 * step))), n // 2))

    hips = arm.pose.bones.get('mixamorig:Hips')
    scene.frame_set(1)
    bpy.context.view_layer.update()
    hloc = hips.location.copy() if hips else None
    for i in range(blend):
        f = n - blend + 1 + i
        w = (i + 1) / blend
        scene.frame_set(f)
        bpy.context.view_layer.update()
        for pb in bones:
            cur = pb.rotation_quaternion.copy()
            tgt = head[pb.name].copy()
            if cur.dot(tgt) < 0.0:
                tgt.negate()
            pb.rotation_quaternion = cur.slerp(tgt, w)
            pb.keyframe_insert(data_path='rotation_quaternion', frame=f)
        if hips and hloc is not None:
            hips.location = hips.location.lerp(hloc, w)
            hips.keyframe_insert(data_path='location', frame=f)
    for fc in act.fcurves:
        vals = [(kp.co[0], kp.co[1]) for kp in fc.keyframe_points if kp.co[0] < n - 0.5]
        fc.keyframe_points.clear()
        for x, y in vals:
            fc.keyframe_points.insert(x, y).interpolation = 'LINEAR'
        fc.update()
    print('    khép vòng %s: lệch %.0f°, bước thường %.1f° -> hoà %d khung, còn %d'
          % (name, gap(tail, head), step, blend, n - 1))


def push_nla(arm):
    ad = arm.animation_data or arm.animation_data_create()
    ad.action = None
    for t in list(ad.nla_tracks):
        ad.nla_tracks.remove(t)
    for name, _lo, _hi in SEGMENTS:
        act = bpy.data.actions.get(name)
        if act is None:
            continue
        track = ad.nla_tracks.new()
        track.name = name
        track.strips.new(name, 1, act)


def main():
    clean()
    print('>>> Nạp char4.fbx (bộ xương đầy đủ + take dài)')
    bpy.ops.import_scene.fbx(filepath=SRC_MAIN)
    arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
    main_mesh = {o.name: o for o in bpy.data.objects if o.type == 'MESH'}
    body = main_mesh['Body']

    print('>>> Nạp char4_e.fbx làm bản đồ phân vùng')
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=SRC_EXTRA)
    extra_objs = set(bpy.data.objects) - before
    parts = {o.name: o for o in extra_objs if o.type == 'MESH'}

    # Dựng vật liệu TRƯỚC khi phân vùng: xoá sạch khe vật liệu sau khi đã gán
    # chỉ số thì Blender kẹp mọi chỉ số về 0, và lưới thân xuất ra một màu duy
    # nhất — đúng cái lỗi mà cả pipeline này sinh ra để tránh.
    print('>>> Dựng vật liệu')
    clear_old_materials()
    names = REGION_PARTS + [REGION_REST]
    for n in names:
        label, look = REGION_LOOK[n]
        body.data.materials.append(make_material(label, look))
    region_map(body, parts)

    skirt = bring_extra(arm, parts[EXTRA_MESH])
    skirt.name = 'Skirt'
    for o in extra_objs:
        if o is not skirt:
            bpy.data.objects.remove(o, do_unlink=True)

    print('>>> Bỏ hình học không ai nhìn thấy')
    push_out(skirt, 14.0)
    strip_under(body, skirt)
    strip_hidden(body, [skirt, main_mesh['Helmet']])

    main_mesh['Helmet'].data.materials.append(make_material('Mu_Sat', STEEL))
    skirt.data.materials.append(make_material('Vay_Giap', STEEL_DARK))
    paint_shield(main_mesh['Shield'], arm)
    paint_sword(main_mesh['Sword'], arm)

    print('>>> Cắt hoạt ảnh')
    split_master(arm)
    for name in LOOP_CLIPS:
        loop_clip(arm, name)
    push_nla(arm)

    os.makedirs(OUT_DIR, exist_ok=True)
    verts = sum(len(o.data.vertices) for o in bpy.data.objects if o.type == 'MESH')
    for fname, draco in (('char4.glb', True), ('char4_web.glb', False)):
        out = os.path.join(OUT_DIR, fname)
        bpy.ops.export_scene.gltf(
            filepath=out, export_format='GLB',
            export_animations=True, export_nla_strips=True,
            export_skins=True, export_morph=False,
            export_draco_mesh_compression_enable=draco,
            export_draco_mesh_compression_level=6,
            export_draco_position_quantization=14,
            export_draco_normal_quantization=10)
        print('>>> %s: %.2f MB' % (fname, os.path.getsize(out) / 1048576))
    print('>>> Xong: %d đỉnh, %d lưới, %d vật liệu, %d clip'
          % (verts, len([o for o in bpy.data.objects if o.type == 'MESH']),
             len(bpy.data.materials), len(SEGMENTS)))


if __name__ == '__main__':
    main()
