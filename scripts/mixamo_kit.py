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
import os
import sys

import bpy
from mathutils import Vector

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
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
    fixed = {'metallic': 0, 'gloss': 0, 'normal': 0}
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
    print('    vật liệu: %d bỏ metallic, %d đảo glossiness, %d đưa về Non-Color'
          % (fixed['metallic'], fixed['gloss'], fixed['normal']))


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

    ground_clips(arm, keep, meshes)
    push_nla(arm, keep)
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
