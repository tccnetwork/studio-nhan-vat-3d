#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""So sánh hai file GLB về cấu trúc, không so từng byte.

    python3 tools/glb_diff.py cu.glb moi.glb

Dùng để kiểm chứng một lần tái cấu trúc không làm đổi kết quả: đối chiếu danh
sách lưới kèm số đỉnh, danh sách clip kèm số kênh và số byte dữ liệu, số xương
và số texture. Byte của file xuất không bao giờ trùng khít giữa hai lần chạy
Blender, nên so từng byte là vô nghĩa.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import glb


def summarise(path):
    gltf, _ = glb.read(path)
    views, accs = gltf.get('bufferViews', []), gltf.get('accessors', [])

    def nbytes(a):
        return sum(views[v]['byteLength'] for v in glb.view_ids(accs[a]))

    node_of_mesh = {}
    for i, nd in enumerate(gltf.get('nodes', [])):
        if 'mesh' in nd:
            node_of_mesh[nd['mesh']] = nd.get('name', f'node{i}')

    meshes = {}
    for i, m in enumerate(gltf.get('meshes', [])):
        verts = sum(accs[p['attributes']['POSITION']]['count'] for p in m['primitives'])
        meshes[node_of_mesh.get(i, m.get('name', f'mesh{i}'))] = verts

    clips = {}
    for a in gltf.get('animations', []):
        b = sum(nbytes(s['input']) + nbytes(s['output']) for s in a['samplers'])
        clips[a.get('name', '?')] = (len(a['channels']), b)

    return dict(meshes=meshes, clips=clips,
                joints=len(gltf['skins'][0]['joints']) if gltf.get('skins') else 0,
                images=len(gltf.get('images', [])),
                nodes=len(gltf.get('nodes', [])))


def diff(p1, p2):
    a, b = summarise(p1), summarise(p2)
    issues = []
    print(f'\n  A: {p1}\n  B: {p2}\n')

    for key in ('joints', 'images', 'nodes'):
        mark = '=' if a[key] == b[key] else '≠'
        if a[key] != b[key]:
            issues.append(f'{key}: {a[key]} -> {b[key]}')
        print(f'  {mark} {key:8s} {a[key]:>6} | {b[key]:>6}')

    print('\n  Lưới (số đỉnh)')
    for name in sorted(set(a['meshes']) | set(b['meshes'])):
        va, vb = a['meshes'].get(name), b['meshes'].get(name)
        mark = '=' if va == vb else '≠'
        if va != vb:
            issues.append(f'lưới {name}: {va} -> {vb}')
        print(f'  {mark} {name:26s} {str(va):>7} | {str(vb):>7}')

    print('\n  Clip (số kênh, KB dữ liệu)')
    for name in sorted(set(a['clips']) | set(b['clips'])):
        ca, cb = a['clips'].get(name), b['clips'].get(name)
        sa = f'{ca[0]}ch {ca[1]/1024:.0f}KB' if ca else '—'
        sb = f'{cb[0]}ch {cb[1]/1024:.0f}KB' if cb else '—'
        same = ca and cb and ca[0] == cb[0] and abs(ca[1] - cb[1]) <= 64
        if not same:
            issues.append(f'clip {name}: {sa} -> {sb}')
        print(f'  {"=" if same else "≠"} {name:26s} {sa:>13} | {sb:>13}')

    print()
    if issues:
        print(f'  \033[31m✗\033[0m {len(issues)} khác biệt:')
        for i in issues:
            print(f'      {i}')
    else:
        print('  \033[32m✓\033[0m hai file giống nhau về cấu trúc\n')
    return len(issues)


if __name__ == '__main__':
    sys.exit(min(diff(sys.argv[1], sys.argv[2]), 1))
