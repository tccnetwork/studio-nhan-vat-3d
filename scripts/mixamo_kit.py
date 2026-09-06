# -*- coding: utf-8 -*-
"""Bộ công cụ: đưa một nhân vật Mixamo bất kỳ vào dự án và gắn sẵn hoạt ảnh.

    /Applications/Blender.app/Contents/MacOS/Blender --background \
        --factory-startup --python scripts/mixamo_kit.py -- \
        source/Punching_Bag_1.fbx boxer_nam

Đưa file vào, nhận lại một GLB đã sửa vật liệu và đã có sẵn toàn bộ kho động
tác của dự án. Không phải viết script riêng cho từng nhân vật.

Vì sao chép thẳng góc xoay được
------------------------------
Đo tư thế nghỉ của sáu rig Mixamo trong dự án, lệch hướng trung bình so với
Ch38: Ch37 3,6°, hiệp sĩ 5,2°, cung thủ 4,9°, Xbot 4,9°. Đủ nhỏ để chép thẳng
góc xoay cục bộ, không cần phép chuyển bám hướng như khi sang rig VRoid.

Riêng Soldier.glb lệch trung bình 64,6° và cực đại 177° — tư thế nghỉ của nó
khác hẳn, xương bị lật ngược. Nên nó KHÔNG nằm trong kho; lấy bừa là nhân vật
vặn xoắn. Xbot đã có idle/walk/run nên không mất gì.

Chỉ chiều cao hông là phải bù: các nhân vật cao thấp khác nhau 3–14%, nên kênh
tịnh tiến của xương hông được nhân theo đúng tỉ lệ ấy.
"""
import math
import os
import sys

import bpy
from mathutils import Vector

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
OUT_ROOT = os.path.join(ROOT, 'build')
STD = 'mixamorig:'
# Draco chỉ nén hình học, không đụng tới ảnh. Nhân vật Mixamo kèm bốn map
# 4096² nên file xuất ra 53 MB dù lưới chỉ 28 nghìn đỉnh. Thu về 2048 là đủ
# cho trình xem web mà nhẹ đi bốn lần mỗi map.
MAX_TEX = 1024

# Kho động tác. Mỗi mục: (file, {tên action nguồn: tên clip ra}).
# None nghĩa là lấy tất cả action có tên bắt đầu bằng chữ số.
# Đặt tên rõ nguồn: hiệp sĩ và cung thủ đều có clip tên 03_GucNga, để trùng
# thì Blender tự thêm hậu tố .001 và clip thứ hai mang tên vô nghĩa.
CLIP_SOURCES = [
    (os.path.join(ROOT, 'build', 'char4', 'char4.glb'), {
        '01_ThuThe': '20_ThuThe', '02_DiBo': '21_DiBoGiap',
        '03_GucNga': '22_GucNga', '04_ChemNgang': '23_ChemNgang',
        '05_NhayChem': '24_NhayChem', '06_DamThang': '25_DamThang',
    }),
    (os.path.join(ROOT, 'build', 'char6', 'char6.glb'), {
        '01_DungYen': '30_DungThu', '02_DiChuyen': '31_LaoToi',
        '03_GucNga': '32_NgaGuc', '04_BanCung': '33_BanCung',
        '05_TrungDon': '34_TrungDon',
    }),
    (os.path.join(ROOT, 'external_library_animations', 'Xbot.glb'), {
        'idle': '10_DungYen', 'walk': '11_DiBo', 'run': '12_ChayBo',
        'agree': '13_GatDau', 'headShake': '14_LacDau',
    }),
]


# Tủ đồ mượn từ file khác. Áo may cho rig Mixamo nào cũng đeo được lên rig
# Mixamo khác, vì cùng tên xương — chỉ phải đổi tiền tố nhóm đỉnh.
PB1 = os.path.join(ROOT, 'source', 'Punching_Bag_1.fbx')
PB2 = os.path.join(ROOT, 'source', 'Punching_Bag_2.fbx')
WARDROBE = {
    'boxer_nam': [(PB2, ('Ch37_Shirt', 'Ch37_Zipper', 'Ch37_Pants'))],
    'boxer_nu': [(PB1, ('Ch38_Shirt',))],
    # Hình nộm có thân trọn vẹn nên mặc được cả hai bộ mà không hở chỗ nào.
    'manocanh': [(PB1, ('Ch38_Shirt', 'Ch38_Shorts', 'Ch38_Socks', 'Ch38_Shoes')),
                 (PB2, ('Ch37_Shirt', 'Ch37_Zipper', 'Ch37_Pants', 'Ch37_Sneakers'))],
}
# Da hở được nặn vừa bộ đồ GỐC. Mặc bộ dài chồng lên thì mấy mảng ấy chọc
# xuyên qua vải, nên phải tách ra thành lưới riêng để ẩn đi được.
BARE_Z = 0.95            # đảo lưới nằm hẳn dưới mức này là da chân hở
# Quần áo may vừa thân người này thì chật với thân người kia. Hình nộm to hơn
# hai võ sĩ nên thân chọc ra ngoài áo mượn. Thu thân vào theo pháp tuyến là
# phép sửa một lần dùng cho MỌI bộ đồ; đẩy từng bộ áo ra thì phải chỉnh lại
# mỗi lần thêm đồ mới.
# Nới rộng quần áo mượn, KHÔNG thu người. Thu người thì hỏng: chi thể chỉ dày
# 5–7 cm nên bù vào từ hai phía là gần như sập, và thử ở 14 mm đã nát ngón tay,
# ở 20 mm nát cả tay chân. Áo là vỏ mỏng, nới ra chỉ rộng thêm chứ không tự
# giao nhau.
INFLATE_MM = {'manocanh': 12.0}


# Chừa những chỗ mảnh. Ngón tay và ngón chân chỉ dày cỡ chục milimét nên thu
# đều tay là bóp nát chúng thành gai — thử rồi. Đầu thì luôn hở nên không cần
# thu, mà thu là méo mặt.
def inflate(obj, mm):
    """Nới một lưới vỏ ra ngoài theo pháp tuyến đỉnh.

    Toạ độ đỉnh nằm trong hệ riêng của đối tượng nên phải quy đổi từ milimét
    của thế giới.
    """
    unit = (obj.matrix_world.to_3x3() @ Vector((1.0, 0.0, 0.0))).length
    d = (mm / 1000.0) / unit
    for v in obj.data.vertices:
        v.co = v.co + v.normal * d
    obj.data.update()


def split_bare_skin(body, z_max=BARE_Z):
    """Tách các đảo lưới nằm thấp của lưới thân ra thành một đối tượng riêng.

    Tách theo ĐẢO LIÊN THÔNG chứ không cắt theo cao độ: cắt theo cao độ sẽ xẻ
    đôi một mảng da, để lại mép hở.
    """
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(body.data)
    bm.verts.ensure_lookup_table()
    seen = set()
    islands = []
    for v in bm.verts:
        if v.index in seen:
            continue
        stack, comp = [v], []
        while stack:
            x = stack.pop()
            if x.index in seen:
                continue
            seen.add(x.index)
            comp.append(x)
            for e in x.link_edges:
                o = e.other_vert(x)
                if o.index not in seen:
                    stack.append(o)
        islands.append(comp)
    mw = body.matrix_world
    low = []
    for comp in islands:
        top = max((mw @ v.co).z for v in comp)
        if top < z_max:
            low += [v.index for v in comp]
    bm.free()
    if not low:
        print('    không có mảng da hở nào cần tách')
        return None

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = body
    body.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')
    for i in low:
        body.data.vertices[i].select = True
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.separate(type='SELECTED')
    bpy.ops.object.mode_set(mode='OBJECT')
    made = [o for o in bpy.context.selected_objects if o is not body]
    if not made:
        return None
    skin = made[0]
    skin.name = body.name.split('_')[0] + '_BareLegs'
    print('    tách %d đỉnh da hở thành "%s"' % (len(low), skin.name))
    return skin


def borrow_clothes(host, path, names):
    """Đắp quần áo từ một file Mixamo khác sang bộ xương đang dựng.

    Phải GIỮ NGUYÊN ma trận thế giới của lưới áo sau khi đổi cha. Bỏ bước đó
    thì áo phình khổng lồ — hai file có tỉ lệ đối tượng khác nhau và phép đổi
    cha mang theo tỉ lệ cũ.
    """
    host_pre = find_prefix(host)
    before = set(bpy.data.objects)
    before_act = set(bpy.data.actions)
    if path.lower().endswith('.fbx'):
        bpy.ops.import_scene.fbx(filepath=path)
    else:
        bpy.ops.import_scene.gltf(filepath=path)
    new = set(bpy.data.objects) - before
    guest = next((o for o in new if o.type == 'ARMATURE'), None)
    guest_pre = find_prefix(guest) if guest else ''
    got = []
    for o in list(new):
        if o.type != 'MESH' or o.name not in names:
            if o is not guest:
                bpy.data.objects.remove(o, do_unlink=True)
            continue
        for g in o.vertex_groups:
            if guest_pre and g.name.startswith(guest_pre):
                g.name = host_pre + g.name[len(guest_pre):]
        mw = o.matrix_world.copy()
        o.parent = host
        o.matrix_parent_inverse = host.matrix_world.inverted()
        o.matrix_world = mw
        for m in list(o.modifiers):
            o.modifiers.remove(m)
        o.modifiers.new('Armature', 'ARMATURE').object = host
        got.append(o.name)
    if guest:
        bpy.data.objects.remove(guest, do_unlink=True)
    # Xoá dứt điểm action của khách. Lọc theo users == 0 là không đủ: bộ nhập
    # FBX bật fake user nên action vẫn còn một người dùng giả, và nó lọt vào
    # danh sách "hoạt ảnh sẵn có" của chủ nhà.
    for act in list(set(bpy.data.actions) - before_act):
        act.use_fake_user = False
        bpy.data.actions.remove(act)
    print('    mượn %d món: %s' % (len(got), ', '.join(got)))
    return got


def find_prefix(arm):
    """Mixamo đánh số tiền tố khi xuất nhiều lần: mixamorig5:, mixamorig6:...
    nên không thể ghi cứng 'mixamorig:'."""
    for b in arm.data.bones:
        if b.name.endswith(':Hips'):
            return b.name[:-len('Hips')]
    return ''


def normalise_prefix(arm, meshes):
    """Đổi mọi tiền tố về mixamorig: — xương, nhóm đỉnh, và đường dẫn trong
    action. Bỏ sót nhóm đỉnh là lưới rời khỏi xương ngay khi vào tư thế."""
    pre = find_prefix(arm)
    if pre == STD or not pre:
        return 0
    n = 0
    for b in arm.data.bones:
        if b.name.startswith(pre):
            b.name = STD + b.name[len(pre):]
            n += 1
    for o in meshes:
        for g in o.vertex_groups:
            if g.name.startswith(pre):
                g.name = STD + g.name[len(pre):]
    for act in bpy.data.actions:
        for fc in act.fcurves:
            if pre in fc.data_path:
                fc.data_path = fc.data_path.replace(pre, STD)
    print('    đổi tiền tố %s -> %s trên %d xương' % (pre, STD, n))
    return n


_ALPHA_CACHE = {}


def alpha_varies(img, thresh=0.99):
    """Kênh alpha của ảnh có thật sự dùng đến không.

    Lấy mẫu thưa bằng numpy: ảnh 4096² là 67 triệu số thực, đọc hết thì mỗi
    tấm mất hàng chục giây.
    """
    import numpy as np
    key = img.name
    if key in _ALPHA_CACHE:
        return _ALPHA_CACHE[key]
    w, h = img.size
    if w == 0 or img.channels < 4:
        _ALPHA_CACHE[key] = False
        return False
    buf = np.empty(len(img.pixels), dtype=np.float32)
    img.pixels.foreach_get(buf)
    a = buf.reshape(-1, 4)[::17, 3]
    out = bool(a.min() < thresh)
    _ALPHA_CACHE[key] = out
    print('        alpha "%s": nhỏ nhất %.3f -> %s'
          % (img.name[:22], float(a.min()), 'có dùng' if out else 'đục hoàn toàn'))
    return out


def fix_materials():
    """Sửa ba lỗi của bộ nhập FBX, cả ba đều làm nhân vật trông như nhựa.

    1. Metallic = 0,5. Da và vải phải là 0. Đây là thủ phạm chính.
    2. Map glossiness nối thẳng vào Roughness. Glossiness là NGHỊCH ĐẢO của
       roughness, nối thẳng thì chỗ nhẵn hoá nhám và ngược lại.
    3. Map normal và các map dữ liệu bị để ở không gian màu sRGB. Chúng chứa
       SỐ chứ không phải màu, đọc qua đường cong sRGB là sai giá trị.

    Normal map thì bộ nhập nối đúng sẵn — lần đầu tôi tưởng nó treo lơ lửng vì
    thấy ảnh nối vào một ô tên "Color", nhưng đó chính là đầu vào của node
    Normal Map.
    """
    fixed = {'metallic': 0, 'gloss': 0, 'normal': 0, 'blend': 0, 'spec': 0}
    for m in bpy.data.materials:
        if not m.use_nodes:
            continue
        nt = m.node_tree
        b = nt.nodes.get('Principled BSDF')
        if b is None:
            continue
        if b.inputs['Metallic'].default_value != 0.0 and not b.inputs['Metallic'].links:
            b.inputs['Metallic'].default_value = 0.0
            fixed['metallic'] += 1

        # Bộ nhập FBX nối kênh alpha của ảnh diffuse vào MỌI vật liệu, kể cả
        # những chỗ ảnh đó đục hoàn toàn. Hệ quả: glTF xuất ra alphaMode BLEND
        # kèm doubleSided, và trình duyệt sắp xếp độ sâu sai — tóc, áo và thân
        # đè lẫn nhau tuỳ góc nhìn. Trong Blender gần như không thấy, nên phải
        # đọc thẳng file glTF mới phát hiện.
        #
        # Phân biệt bằng SỐ chứ không đoán: đo kênh alpha của chính tấm ảnh.
        # Chỉ TÓC mới thật sự cần alpha. Ảnh diffuse của Mixamo có kênh alpha
        # dùng để giấu phần thân nằm dưới quần áo, nhưng áp nó lên vật liệu
        # thân thì khuôn mặt bị băm nát — mắt rách, da thủng lỗ. Phần bị giấu
        # ấy vốn nằm khuất dưới áo nên bỏ alpha đi không mất gì.
        al = b.inputs['Alpha']
        if al.links:
            img = getattr(al.links[0].from_node, 'image', None)
            if 'hair' in m.name.lower() and img is not None and alpha_varies(img):
                # Tóc thật sự cần alpha. Dùng CLIP (glTF ghi alphaMode MASK)
                # thay vì BLEND: mặt nạ không cần sắp xếp độ sâu nên không loạn.
                m.blend_method = 'CLIP'
                m.alpha_threshold = 0.5
                fixed['blend'] += 1
            else:
                nt.links.remove(al.links[0])
                al.default_value = 1.0
                m.blend_method = 'OPAQUE'
                m.use_backface_culling = True
                fixed['blend'] += 1

        # Blender xuất specular ra glTF với hệ số nhân 2, nên để mặc định 1,0 ở
        # đây thành 2,0 trong file — ngoài dải hợp lý và làm mọi thứ bóng như
        # nhựa. 0,5 mới là giá trị vật lý bình thường.
        sp = b.inputs.get('Specular IOR Level')
        if sp is not None and not sp.links and sp.default_value > 0.5:
            sp.default_value = 0.5
            fixed['spec'] += 1

        r = b.inputs['Roughness']
        if r.links:
            src = r.links[0].from_node
            if src.type == 'TEX_IMAGE' and 'Gloss' in (src.image.name or '') + (
                    os.path.basename(src.image.filepath or '')):
                inv = nt.nodes.new('ShaderNodeInvert')
                inv.location = (src.location.x + 220, src.location.y)
                nt.links.new(inv.inputs['Color'], src.outputs['Color'])
                nt.links.new(r, inv.outputs['Color'])
                src.image.colorspace_settings.name = 'Non-Color'
                fixed['gloss'] += 1

        # Chỉ ảnh đi vào Base Color mới là màu thật; normal, specular,
        # glossiness đều là dữ liệu.
        for n in nt.nodes:
            if n.type != 'TEX_IMAGE' or not n.image:
                continue
            to_color = any(l.to_socket.name == 'Base Color'
                           for o in n.outputs for l in o.links)
            if not to_color and n.image.colorspace_settings.name != 'Non-Color':
                n.image.colorspace_settings.name = 'Non-Color'
                fixed['normal'] += 1
    print('    vật liệu: %d bỏ metallic, %d đảo glossiness, %d Non-Color, '
          '%d về đục, %d hạ specular'
          % (fixed['metallic'], fixed['gloss'], fixed['normal'],
             fixed['blend'], fixed['spec']))


def shrink_textures():
    """Thu ảnh về MAX_TEX. Bốn map 4096² là 53 MB file xuất, mà trình xem web
    không cần tới độ phân giải ấy."""
    n = 0
    for img in bpy.data.images:
        w, h = img.size
        if max(w, h) <= MAX_TEX or w == 0:
            continue
        k = MAX_TEX / max(w, h)
        img.scale(max(1, int(w * k)), max(1, int(h * k)))
        n += 1
    if n:
        print('    thu %d ảnh về tối đa %d px' % (n, MAX_TEX))


def hip_height(arm):
    b = arm.data.bones.get(STD + 'Hips')
    return (arm.matrix_world @ b.head_local).z if b else 1.0


def copy_action(src_act, name, scale):
    """Chép một action sang tên mới, nhân kênh tịnh tiến hông theo tỉ lệ.

    Chép ĐƯỜNG CONG chứ không bake từng khung: hai rig cùng chuẩn Mixamo nên
    góc xoay cục bộ mang đúng một ý nghĩa, và chép đường cong thì nhanh hơn
    hàng trăm lần mà không mất mát gì.
    """
    act = bpy.data.actions.new(name)
    for fc in src_act.fcurves:
        nfc = act.fcurves.new(fc.data_path, index=fc.array_index,
                              action_group=fc.group.name if fc.group else '')
        k = scale if ('Hips' in fc.data_path and fc.data_path.endswith('.location')) else 1.0
        nfc.keyframe_points.add(len(fc.keyframe_points))
        for i, kp in enumerate(fc.keyframe_points):
            p = nfc.keyframe_points[i]
            p.co = (kp.co[0], kp.co[1] * k)
            p.interpolation = 'LINEAR'
        nfc.update()
    act.use_fake_user = True
    return act


def load_clips(arm):
    """Nạp kho động tác từ các file khác, chép sang rig đang dựng."""
    my_h = hip_height(arm)
    made = []
    for path, mapping in CLIP_SOURCES:
        if not os.path.exists(path):
            print('    bỏ qua %s (không có)' % os.path.basename(path))
            continue
        before_act = set(bpy.data.actions)
        before_obj = set(bpy.data.objects)
        bpy.ops.import_scene.gltf(filepath=path)
        new_obj = set(bpy.data.objects) - before_obj
        src_arm = next((o for o in new_obj if o.type == 'ARMATURE'), None)
        pre = find_prefix(src_arm) if src_arm else STD
        ratio = my_h / hip_height(src_arm) if src_arm else 1.0
        got = 0
        for act in sorted(set(bpy.data.actions) - before_act, key=lambda a: a.name):
            if mapping is None:
                if not act.name[:1].isdigit():
                    continue
                out = act.name
            else:
                if act.name not in mapping:
                    continue
                out = mapping[act.name]
            for fc in act.fcurves:                 # đưa về tiền tố chuẩn
                if pre != STD and pre in fc.data_path:
                    fc.data_path = fc.data_path.replace(pre, STD)
            made.append(copy_action(act, out, ratio).name)
            got += 1
        for o in new_obj:
            bpy.data.objects.remove(o, do_unlink=True)
        for act in list(set(bpy.data.actions) - before_act):
            if act.name not in made:
                bpy.data.actions.remove(act)
        print('    %-14s lấy %d clip, tỉ lệ hông %.3f'
              % (os.path.basename(path), got, ratio))
    return made


# Lưới chứa bàn chân. Căn theo XƯƠNG bàn chân thì lún 1,6–5 cm vì đế giày nằm
# thấp hơn xương; phải đo bằng đỉnh lưới thật.
SHOE_HINTS = ('shoe', 'sneaker', 'boot', 'sock', 'foot')


def foot_meshes(meshes):
    picked = [o for o in meshes
              if any(h in o.name.lower() for h in SHOE_HINTS)]
    return picked or meshes


def ground_clips(arm, names, meshes):
    """Hạ từng clip xuống cho bàn chân chạm sàn.

    Clip mượn từ nhân vật khác thì kênh tịnh tiến hông tính theo chiều cao hông
    của NGƯỜI KIA, nên đắp sang người này là lơ lửng hoặc lún. Đo điểm thấp
    nhất qua cả clip rồi dời MỘT lượng cố định — dời theo từng khung sẽ xoá mất
    chuyển động lên xuống vốn có.

    Căn theo điểm thấp nhất đúng cho mọi loại clip, kể cả ngã và nhảy: lúc ngã
    thì thân chạm sàn, lúc nhảy thì chân chạm sàn ở đầu và cuối. Ban đầu tôi
    loại trừ ba clip ấy vì sợ nhấc chúng lên khỏi sàn — không cần.

    Lượng dời tính trong hệ thế giới rồi quy về hệ riêng của xương hông, vì
    pose.bones[].location nằm trong hệ trục của xương chứ không phải hệ thế giới.
    """
    scene = bpy.context.scene
    ad = arm.animation_data or arm.animation_data_create()
    if arm.data.bones.get(STD + 'Hips') is None:
        return
    feet = foot_meshes(meshes)
    rest3 = (arm.matrix_world @ arm.data.bones[STD + 'Hips'].matrix_local).to_3x3()
    inv3 = rest3.inverted()
    moved = 0
    for name in names:
        act = bpy.data.actions.get(name)
        if act is None:
            continue
        ad.action = act
        if getattr(act, 'slots', None):
            ad.action_slot = act.slots[0]
        n = int(act.frame_range[1])
        step = max(1, n // 20)
        lo = 1e9
        for f in range(1, n + 1, step):
            scene.frame_set(f)
            dg = bpy.context.evaluated_depsgraph_get()
            for o in feet:
                mw = o.matrix_world
                for v in o.evaluated_get(dg).data.vertices:
                    z = (mw @ v.co).z
                    if z < lo:
                        lo = z
        if lo > 1e8 or abs(lo) < 0.004:
            continue
        d = inv3 @ Vector((0.0, 0.0, -lo))
        for fc in act.fcurves:
            if not (fc.data_path.endswith('.location') and 'Hips' in fc.data_path):
                continue
            off = d[fc.array_index]
            for kp in fc.keyframe_points:
                kp.co = (kp.co[0], kp.co[1] + off)
            fc.update()
        moved += 1
    ad.action = None
    print('    hạ %d clip cho chân chạm sàn (đo trên %d lưới bàn chân)'
          % (moved, len(feet)))


def push_nla(arm, names):
    ad = arm.animation_data or arm.animation_data_create()
    ad.action = None
    for t in list(ad.nla_tracks):
        ad.nla_tracks.remove(t)
    for n in sorted(names):
        act = bpy.data.actions.get(n)
        if act is None:
            continue
        tr = ad.nla_tracks.new()
        tr.name = n
        tr.strips.new(n, 1, act)


ALPHA_CUTOFF = 0.5

# --- Chớp mắt --------------------------------------------------------------
# Nhân vật Mixamo không có khẩu hình nào, y như cung thủ char6. Nặn một cái từ
# chính hình học: kéo mí trên xuống đường giữa mắt.
BLINK_KEY = 'NhamMat'
FACE_CLIP = 'Mat_ChopMat'
FACE_SECONDS = 18.0
BLINK_AT = (2.4, 6.9, 11.2, 11.7, 16.3)   # giây; hai cú sát nhau là chớp kép
BLINK_DOWN, BLINK_UP = 0.05, 0.09         # giây để nhắm và để mở
LID_PUSH = 0.0016         # m, đẩy mí ra trước cho ôm cầu mắt
LOWER_PULL = 0.30         # mí dưới nhích lên bằng 30% mí trên
CLOSE_LINE = 0.30         # đường khép nằm dưới tâm mắt 30% nửa-cao
EYE_DEPTH = 0.035         # m, chỉ đụng tới lớp mặt trước; gáy cùng độ cao thì tha
# Mắt RỘNG 46 mm mà chỉ CAO 19 mm. Vùng ảnh hưởng tròn muốn phủ hết bề ngang
# thì tất yếu vơ luôn lông mày (cách tâm mắt 23 mm) và kéo nó sụp xuống. Nên
# hai trục phải nới riêng, và trục dọc phải dừng trước chân mày.
REACH_X, REACH_UP, REACH_DOWN = 1.35, 1.80, 2.40
FULL = 0.40               # trong ngần này thì khép hết cỡ
MIN_VERTS = 150           # ít hơn ngần này nghĩa là chỗ đó không có mắt

# Suy vị trí mắt theo tỉ lệ hộp sọ, đo từ hàng mi của af1 (mốc chắc chắn: nó
# là một lưới riêng). Dùng cho nhân vật gộp hết vào một lưới như af2.
EYE_OF_HEAD = dict(z=0.462, x=0.409, y=0.126, rx=0.261, rz=0.0422)


def smoothstep(a, b, x):
    t = min(1.0, max(0.0, (x - a) / (b - a)))
    return t * t * (3.0 - 2.0 * t)


def head_box(arm, meshes):
    """Hộp sọ: các đỉnh bám xương đầu và nằm trên khớp cổ."""
    hb = next((b for b in arm.data.bones if b.name.lower().endswith('head')), None)
    if hb is None:
        return None
    base = (arm.matrix_world @ hb.head_local).z
    pts = []
    for m in meshes:
        g = m.vertex_groups.get(hb.name)
        if g is None:
            continue
        mw = m.matrix_world
        for v in m.data.vertices:
            if any(vg.group == g.index and vg.weight > 0.5 for vg in v.groups):
                p = mw @ v.co
                if p.z > base:
                    pts.append(p)
    if len(pts) < 200:
        return None
    return (base, max(p.z for p in pts), max(abs(p.x) for p in pts),
            min(p.y for p in pts), max(p.y for p in pts))


def _pair(pts, tag):
    """Chẻ một đám điểm thành mắt phải / mắt trái, trả về (tâm, nửa-rộng, nửa-cao)."""
    out = []
    for pick in (lambda p: p.x > 0.008, lambda p: p.x < -0.008):
        side = [p for p in pts if pick(p)]
        if len(side) < 12:
            return None
        c = sum(side, Vector()) / len(side)
        rx = (max(p.x for p in side) - min(p.x for p in side)) / 2
        rz = (max(p.z for p in side) - min(p.z for p in side)) / 2
        out.append((c, max(0.010, rx), max(0.006, rz)))
    print('    mốc: %s' % tag)
    return out


def find_eyes(arm, meshes):
    """Trả về [(tâm, nửa-rộng, nửa-cao)] cho mắt phải và mắt trái.

    Rig Mixamo 65 xương không có xương mắt, nên phải đọc từ hình học. Mốc là
    HÀNG MI. Nó luôn dùng chung vật liệu với tóc, nên lọc theo vật liệu thôi thì
    ra cả mái tóc. Hai điều kiện nữa mới tách được: chỉ lấy NỬA TRƯỚC của đầu
    (bỏ tóc mai vòng ra sau), rồi trong đó lấy DẢI THẤP NHẤT 20 mm (bỏ mái và
    chỏm). Thử trên af1 — nơi hàng mi là lưới riêng nên biết trước đáp án — quy
    tắc này ra đúng 375 đỉnh mỗi bên, lệch tâm 0,1 mm.
    """
    lash = []
    for m in meshes:
        low = m.name.lower()
        # "Eyeleashes" là lỗi chính tả có thật trong file gốc của Ch37.
        if 'lash' in low or 'leash' in low or low.endswith(('_eye', '_eyes')):
            lash += [m.matrix_world @ v.co for v in m.data.vertices]
    got = _pair(lash, 'lưới hàng mi riêng') if lash else None
    if got:
        return got

    box = head_box(arm, meshes)
    if box is not None:
        base, top, W, y0, y1 = box
        cut = y0 + 0.30 * (y1 - y0)
        pts = []
        for m in meshes:
            idx = [i for i, mt in enumerate(m.data.materials)
                   if mt and 'hair' in mt.name.lower()]
            if not idx:
                continue
            keep = set()
            for poly in m.data.polygons:
                if poly.material_index in idx:
                    keep.update(poly.vertices)
            mw = m.matrix_world
            pts += [q for q in (mw @ m.data.vertices[i].co for i in keep)
                    if q.y < cut and q.z > base]
        if pts:
            z0 = min(p.z for p in pts)
            got = _pair([p for p in pts if p.z < z0 + 0.020],
                        'dải mi thấp nhất trong vật liệu tóc')
            if got:
                return got

    if box is None:
        return None
    # Cùng đường: đoán theo tỉ lệ hộp sọ đo được từ af1.
    base, top, W, y0, y1 = box
    r = EYE_OF_HEAD
    h, d = top - base, y1 - y0
    print('    mốc: tỉ lệ hộp sọ (cao %.0f mm)' % (h * 1000))
    return [(Vector((k * r['x'] * W, y0 + r['y'] * d, base + r['z'] * h)),
             r['rx'] * W, r['rz'] * h) for k in (1.0, -1.0)]


def add_blink(arm, meshes):
    """Nặn khẩu hình nhắm mắt: hạ mí trên xuống đường khép, mí dưới nhích lên."""
    eyes = find_eyes(arm, meshes)
    if eyes is None:
        print('    không định vị được mắt, bỏ qua chớp mắt')
        return []
    for c, rx, rz in eyes:
        print('    mắt (%.3f, %.3f, %.3f)  rộng %.1f mm  cao %.1f mm'
              % (c.x, c.y, c.z, rx * 2000, rz * 2000))
    made = []
    for m in meshes:
        low = m.name.lower()
        if 'hair' in low and 'lash' not in low:
            continue          # tóc mái không nhắm theo mắt
        mw = m.matrix_world
        inv = mw.inverted()
        key = None
        moved = 0
        for v in m.data.vertices:
            p = mw @ v.co
            for c, rx, rz in eyes:
                if abs(p.y - c.y) > EYE_DEPTH:
                    continue
                dz = p.z - c.z
                up = REACH_UP if dz > 0 else REACH_DOWN
                d = math.hypot(dz / (rz * up), (p.x - c.x) / (rx * REACH_X))
                w = 1.0 - smoothstep(FULL, 1.0, d)
                if w <= 0.002:
                    continue
                if key is None:
                    if m.data.shape_keys is None:
                        m.shape_key_add(name='Basis', from_mix=False)
                    key = m.shape_key_add(name=BLINK_KEY, from_mix=False)
                line = c.z - CLOSE_LINE * rz
                q = p.copy()
                q.z = p.z + w * (line - p.z) * (1.0 if p.z > line else LOWER_PULL)
                q.y -= LID_PUSH * w
                key.data[v.index].co = inv @ q
                moved += 1
                break
        if key is None:
            continue
        if moved < MIN_VERTS:
            # Ma-nơ-canh không có mắt: mặt nó trơn, chỉ vài chục đỉnh lọt vào
            # vùng ước lượng. Nặn ở đó chỉ làm móp mặt chứ không thành cái chớp.
            m.shape_key_remove(key)
            if len(m.data.shape_keys.key_blocks) == 1:
                m.shape_key_remove(m.data.shape_keys.key_blocks[0])
            print('    %s: chỉ %d đỉnh quanh mắt, bỏ qua' % (m.name, moved))
            continue
        made.append(m.name)
        print('    %s: nặn "%s" trên %d đỉnh' % (m.name, BLINK_KEY, moved))
    return made


def animate_blink(meshes, names):
    """Một clip mặt dài 18 giây, lặp độc lập với clip thân.

    Mỗi lưới phải có action riêng vì Blender không cho hai action trùng tên, và
    bộ xuất glTF đặt tên hoạt ảnh theo tên action. Trang xem phát mọi clip có
    tiền tố Mat_ nên vẫn khớp nhau.
    """
    n = FACE_SECONDS * 30.0
    made = []
    for i, nm in enumerate(names):
        m = bpy.data.objects.get(nm)
        keys = m.data.shape_keys if m else None
        if keys is None:
            continue
        if keys.animation_data is None:
            keys.animation_data_create()
        ad = keys.animation_data
        ad.action = None
        for t in list(ad.nla_tracks):
            ad.nla_tracks.remove(t)
        name = FACE_CLIP if i == 0 else '%s_%d' % (FACE_CLIP, i)
        act = bpy.data.actions.new(name)
        fc = act.fcurves.new('key_blocks["%s"].value' % BLINK_KEY)
        fc.keyframe_points.insert(1.0, 0.0).interpolation = 'LINEAR'
        for t in BLINK_AT:
            for off, val in ((-BLINK_DOWN, 0.0), (0.0, 1.0), (BLINK_UP, 0.0)):
                x = max(1.0, min(n, (t + off) * 30.0))
                fc.keyframe_points.insert(x, val).interpolation = 'LINEAR'
        fc.keyframe_points.insert(n, 0.0).interpolation = 'LINEAR'
        fc.update()
        act.use_fake_user = True
        tr = ad.nla_tracks.new()
        tr.name = name
        st = tr.strips.new(name, 1, act)
        # Blender 4.4+ dùng action có "ngăn": gán action vào strip thôi thì ngăn
        # vẫn trống và strip không điều khiển gì cả.
        if hasattr(st, 'action_slot') and act.slots:
            st.action_slot = act.slots[0]
        made.append(name)
    print('    clip mặt: %.0f giây, %d cú chớp, trên %d lưới'
          % (FACE_SECONDS, len(BLINK_AT), len(names)))
    return made


def patch_alpha_mode(path):
    """Đổi alphaMode BLEND thành MASK ngay trong file glTF đã xuất.

    Bộ xuất của Blender 4.5 không còn đọc material.blend_method — đặt nó thành
    CLIP trong Blender vẫn ra BLEND trong file. Thay vì đoán tiếp xem nó đọc
    thuộc tính nào, vá thẳng vào JSON: chắc chắn và kiểm được bằng cách đọc lại.

    BLEND buộc trình duyệt sắp xếp độ sâu giữa các lưới, và sắp sai thì tóc, áo
    và thân đè lẫn nhau tuỳ góc nhìn. MASK chỉ cắt theo ngưỡng nên không cần
    sắp xếp gì — đúng thứ cần cho tóc và cho phần thân bị alpha giấu đi.
    """
    import glb as glblib
    js, blob = glblib.read(path)
    n = 0
    for m in js.get('materials', []):
        if m.get('alphaMode') == 'BLEND':
            m['alphaMode'] = 'MASK'
            m['alphaCutoff'] = ALPHA_CUTOFF
            n += 1
    if n:
        glblib.write(path, js, blob)
    print('    vá %d vật liệu BLEND -> MASK trong %s'
          % (n, os.path.basename(path)))


def build(src, tag, own_name='00_DamBao'):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.scene.render.fps = 30
    print('>>> Nạp %s' % os.path.basename(src))
    if src.lower().endswith('.fbx'):
        bpy.ops.import_scene.fbx(filepath=src)
    else:
        bpy.ops.import_scene.gltf(filepath=src)
    arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
    meshes = [o for o in bpy.data.objects if o.type == 'MESH']
    verts = sum(len(o.data.vertices) for o in meshes)
    print('    %d xương, %d lưới, %d đỉnh' % (len(arm.data.bones), len(meshes), verts))

    normalise_prefix(arm, meshes)

    # Lưới thân: theo hậu tố _body, hoặc lưới nhiều đỉnh nhất nếu chỉ có một
    # lưới duy nhất như hình nộm (tên nó là "Ch36", không có hậu tố nào).
    body = next((o for o in meshes if o.name.lower().endswith('_body')), None)
    if body is None and len(meshes) == 1:
        body = meshes[0]
    # Chỉ tách da hở khi nhân vật SẼ mặc đồ mượn. Không mượn gì thì phép tách
    # chỉ băm nhỏ lưới vô ích.
    if body is not None and tag in WARDROBE:
        skin = split_bare_skin(body)
        if skin is not None:
            meshes.append(skin)
    grew = []
    for path, names in WARDROBE.get(tag, []):
        grew += borrow_clothes(arm, path, names)
    mm = INFLATE_MM.get(tag)
    if mm:
        for n in grew:
            o = bpy.data.objects.get(n)
            if o is not None:
                inflate(o, mm)
        print('    nới %d món đồ mượn ra %.0f mm' % (len(grew), mm))
    if tag in WARDROBE:
        meshes = [o for o in bpy.data.objects if o.type == 'MESH']
        normalise_prefix(arm, meshes)

    fix_materials()
    shrink_textures()

    own = [a for a in bpy.data.actions]
    keep = []
    for i, a in enumerate(own):
        a.name = own_name if len(own) == 1 else '%s_%d' % (own_name, i + 1)
        a.use_fake_user = True
        keep.append(a.name)
    print('    hoạt ảnh sẵn có: %s' % keep)

    print('>>> Nạp kho động tác')
    keep += load_clips(arm)

    print('>>> Chớp mắt')
    meshes = [o for o in bpy.data.objects if o.type == 'MESH']
    face = animate_blink(meshes, add_blink(arm, meshes))

    ground_clips(arm, keep, meshes)
    push_nla(arm, keep)
    # Clip mặt nằm trên datablock khẩu hình, không phải bộ xương, nên chỉ thêm
    # vào danh sách giữ SAU khi đã dàn chân và dựng NLA cho thân.
    keep += face
    for a in list(bpy.data.actions):
        if a.name not in keep:
            bpy.data.actions.remove(a)

    out_dir = os.path.join(OUT_ROOT, tag)
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, tag + '.glb')
    bpy.ops.export_scene.gltf(
        filepath=out, export_format='GLB',
        export_animations=True, export_nla_strips=True,
        export_skins=True, export_morph=True,
        export_draco_mesh_compression_enable=True,
        export_draco_mesh_compression_level=6,
        export_draco_position_quantization=14,
        export_draco_normal_quantization=10,
        export_draco_texcoord_quantization=12)
    patch_alpha_mode(out)
    print('>>> Xong %s: %.2f MB, %d clip'
          % (os.path.basename(out), os.path.getsize(out) / 1048576, len(keep)))
    return out


def main():
    args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    if not args:
        raise SystemExit('dùng: <file nguồn> [<tên thư mục ra>]')
    src = args[0] if os.path.isabs(args[0]) else os.path.join(ROOT, args[0])
    tag = args[1] if len(args) > 1 else os.path.splitext(os.path.basename(src))[0].lower()
    build(src, tag)


if __name__ == '__main__':
    main()
