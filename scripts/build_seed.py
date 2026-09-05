# -*- coding: utf-8 -*-
"""Đưa Seed-san (avatar mẫu chính thức của chuẩn VRM) vào dự án.

    /Applications/Blender.app/Contents/MacOS/Blender --background \
        --factory-startup --python scripts/build_seed.py

Nguồn: kho GitHub của chuẩn VRM, tải thẳng không cần tài khoản
    https://raw.githubusercontent.com/vrm-c/vrm-specification/master/
    samples/Seed-san/vrm/Seed-san.vrm

Giấy phép nằm trong chính file, ở nhánh extensions.VRMC_vrm.meta — VRM nhúng
điều khoản vào metadata nên không phải đọc trang web rồi đoán:
    avatarPermission     everyone
    commercialUsage      corporation
    allowRedistribution  true
    modification         allowModificationRedistribution
    creditNotation       required   -> BẮT BUỘC ghi công VirtualCast, Inc.

Việc ở đây chỉ là nén lại cho web. File .vrm vốn đã là một glb hợp lệ nên trình
duyệt nạp thẳng được, nhưng nó nặng 10,9 MB vì chưa nén hình học.
"""
import os
import shutil

import bpy

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'source', 'Seed-san.vrm')
OUT_DIR = os.path.join(ROOT, 'build', 'seed')
CREDIT = 'Seed-san model by VirtualCast, Inc. — VRM Public License 1.0'


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.scene.render.fps = 30

    # Bộ nhập glTF lọc theo phần mở rộng nên .vrm bị từ chối; chép thành .glb
    # là nạp được, vì bên trong vốn đã là glb.
    tmp = os.path.join(OUT_DIR, '_seed_in.glb')
    os.makedirs(OUT_DIR, exist_ok=True)
    shutil.copyfile(SRC, tmp)
    print('>>> Nạp %s' % os.path.basename(SRC))
    bpy.ops.import_scene.gltf(filepath=tmp)
    os.remove(tmp)

    for o in list(bpy.data.objects):
        if o.type == 'MESH' and o.name.startswith('Icosphere'):
            bpy.data.objects.remove(o, do_unlink=True)

    arm = next((o for o in bpy.data.objects if o.type == 'ARMATURE'), None)
    meshes = [o for o in bpy.data.objects if o.type == 'MESH']
    verts = sum(len(o.data.vertices) for o in meshes)
    shapes = sum(len(o.data.shape_keys.key_blocks) for o in meshes
                 if o.data.shape_keys)
    print('    %d xương, %d lưới, %d đỉnh, %d khẩu hình, %d vật liệu'
          % (len(arm.data.bones) if arm else 0, len(meshes), verts, shapes,
             len(bpy.data.materials)))

    for fname, draco in (('seed.glb', True), ('seed_web.glb', False)):
        out = os.path.join(OUT_DIR, fname)
        bpy.ops.export_scene.gltf(
            filepath=out, export_format='GLB',
            export_animations=False, export_skins=True, export_morph=True,
            export_draco_mesh_compression_enable=draco,
            export_draco_mesh_compression_level=6,
            export_draco_position_quantization=14,
            export_draco_normal_quantization=10,
            export_draco_texcoord_quantization=12)
        print('>>> %s: %.2f MB' % (fname, os.path.getsize(out) / 1048576))
    print('>>> Ghi công bắt buộc: %s' % CREDIT)


if __name__ == '__main__':
    main()
