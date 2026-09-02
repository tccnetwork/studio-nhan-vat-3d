"""Render thử bộ kiểu tóc mà không phải bake lại 14 trạng thái hoạt ảnh.

    /Applications/Blender.app/Contents/MacOS/Blender --background \
        --factory-startup --python tools/preview_hairstyles.py -- <thu_muc_ra> <nhan>

Một lượt mất khoảng một phút, so với chín phút nếu chạy scripts/build_character.py.
Dùng chung scripts/hairstyles.py với quy trình dựng thật nên hình ra là hình thật.
"""
import bpy
import os
import sys
from mathutils import Vector

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
import hairstyles

argv = sys.argv[sys.argv.index('--') + 1:]
out_dir = argv[0] if argv else os.path.join(ROOT, 'build', 'preview_toc')
tag = argv[1] if len(argv) > 1 else 'xem'
os.makedirs(out_dir, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(
    filepath=os.path.join(ROOT, 'source', 'female_singer_anime_idol_base.glb'))
char_arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
hairstyles.build_hairstyles(char_arm)

sc = bpy.context.scene
sc.render.engine = 'BLENDER_EEVEE_NEXT'
sc.render.resolution_x, sc.render.resolution_y = 560, 780
sc.eevee.taa_render_samples = 16
sc.view_settings.view_transform = 'Standard'
sc.world = bpy.data.worlds.new('W')
sc.world.use_nodes = True
sc.world.node_tree.nodes['Background'].inputs[0].default_value = (0.10, 0.11, 0.14, 1)

for loc, energy, color in [((1.6, -2.4, 2.2), 900, (1, .97, .94)),
                           ((-2.2, 1.8, 2.0), 500, (.8, .85, 1)),
                           ((0, 2.6, 1.4), 350, (1, .9, .95))]:
    lt = bpy.data.lights.new('L', 'AREA')
    lt.energy, lt.size, lt.color = energy, 3.0, color
    ob = bpy.data.objects.new('L', lt)
    ob.location = loc
    ob.rotation_euler = (Vector((0, 0, 1.35)) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    sc.collection.objects.link(ob)

cam_data = bpy.data.cameras.new('C')
cam_data.lens = 85
cam = bpy.data.objects.new('C', cam_data)
sc.collection.objects.link(cam)
sc.camera = cam

HAIR = ['Hair', 'Hair_WavyCurled', 'Hair_MediumShoulder', 'Hair_ShortBob']
LABEL = {'Hair': '1_ToDai_GOC', 'Hair_WavyCurled': '2_DaiVua',
         'Hair_MediumShoulder': '3_NgangVai', 'Hair_ShortBob': '4_Bob'}
VIEWS = {'truoc': (0, -1.05), 'cheo': (-0.80, 0.70), 'ben': (-1.05, 0.05)}
TARGET = Vector((0, 0, 1.36))

for name in HAIR:
    if name not in bpy.data.objects:
        continue
    for h in HAIR:
        if h in bpy.data.objects:
            bpy.data.objects[h].hide_render = (h != name)
    for vname, (dx, dy) in VIEWS.items():
        cam.location = (dx * 1.15, dy * 1.15, 1.44)
        cam.rotation_euler = (TARGET - Vector(cam.location)).to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = os.path.join(out_dir, f'{tag}_{LABEL[name]}_{vname}.png')
        bpy.ops.render.render(write_still=True)
        print(f'>>> {sc.render.filepath}')
