#!/usr/bin/env python3
"""Báo cáo ngân sách byte của một file GLB.

    python3 tools/glb_report.py build/female_singer_anime_idol.glb

In ra: danh sách clip hoạt ảnh, bảng lưới kèm số đỉnh, và byte tiêu tốn
theo từng hạng mục. Dùng để đối chiếu trước / sau mỗi lần dựng.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import glb


def report(path):
    gltf, blob = glb.read(path)
    views = gltf.get('bufferViews', [])
    accs = gltf.get('accessors', [])

    def size_of(acc_id):
        return sum(views[v]['byteLength'] for v in glb.view_ids(accs[acc_id]))

    print(f'\n=== {path} ===')
    print(f'File trên đĩa : {glb.mb(os.path.getsize(path))}')
    print(f'Chunk BIN     : {glb.mb(len(blob))}')

    anims = gltf.get('animations', [])
    print(f'\nHoạt ảnh ({len(anims)} clip)')
    for a in anims:
        n = sum(size_of(s['input']) + size_of(s['output']) for s in a['samplers'])
        print(f'  {a.get("name", "?"):24s} {len(a["channels"]):4d} kênh  {glb.mb(n):>9s}')

    # Lưới, gộp theo node để thấy tên thật trong cảnh
    node_of_mesh = {}
    for i, nd in enumerate(gltf.get('nodes', [])):
        if 'mesh' in nd:
            node_of_mesh.setdefault(nd['mesh'], []).append(nd.get('name', f'node{i}'))

    print(f'\nLưới ({len(gltf.get("meshes", []))})')
    for i, m in enumerate(gltf.get('meshes', [])):
        verts = sum(accs[p['attributes']['POSITION']]['count'] for p in m['primitives'])
        nbytes = sum(size_of(a) for a in set(glb.accessor_ids(m)))
        morphs = len(m['primitives'][0].get('targets', []))
        names = ', '.join(node_of_mesh.get(i, ['(không gắn node)']))
        print(f'  {names:32s} {verts:7d} đỉnh  {morphs:3d} morph  {glb.mb(nbytes):>9s}')

    # Ngân sách theo hạng mục
    used = {}

    def add(cat, nbytes):
        used[cat] = used.get(cat, 0) + nbytes

    for i, m in enumerate(gltf.get('meshes', [])):
        names = ' '.join(node_of_mesh.get(i, [m.get('name', '')]))
        cat = 'Tóc' if 'Hair' in names else 'Thân + mặt'
        for a in set(glb.accessor_ids(m)):
            add(cat, size_of(a))
    for a in anims:
        for s in a['samplers']:
            add('Hoạt ảnh', size_of(s['input']) + size_of(s['output']))
    for sk in gltf.get('skins', []):
        if 'inverseBindMatrices' in sk:
            add('Bộ xương', size_of(sk['inverseBindMatrices']))
    for im in gltf.get('images', []):
        if 'bufferView' in im:
            add('Texture', views[im['bufferView']]['byteLength'])

    print('\nNgân sách byte')
    total = sum(used.values())
    for k, v in sorted(used.items(), key=lambda x: -x[1]):
        bar = '█' * round(v / total * 34) if total else ''
        print(f'  {k:14s} {glb.mb(v):>9s}  {v / total * 100:5.1f}%  {bar}')
    print(f'  {"TỔNG":14s} {glb.mb(total):>9s}')
    print(f'\nNode: {len(gltf.get("nodes", []))}   '
          f'Xương: {len(gltf["skins"][0]["joints"]) if gltf.get("skins") else 0}   '
          f'Texture: {len(gltf.get("images", []))}')


if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit('Cách dùng: python3 tools/glb_report.py <file.glb> [file2.glb ...]')
    for p in sys.argv[1:]:
        report(p)
