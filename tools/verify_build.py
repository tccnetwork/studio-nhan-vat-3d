#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Đối chiếu file GLB vừa dựng với danh mục trong scripts/catalog.py.

    python3 tools/verify_build.py

Thoát mã khác 0 nếu có sai lệch, để gắn được vào lệnh dựng tự động.

Kiểm tra đúng những thứ đã từng hỏng trong thực tế:
  - Lưới nhân bản (tên kết thúc bằng .001, .002…) — lỗi đã làm model phình từ
    608 KB lên 13,66 MB qua nhiều lượt chạy ghi đè lên chính đầu vào.
  - Thiếu hoặc thừa clip hoạt ảnh so với danh mục.
  - Thiếu lưới tóc mà trình xem có nút bấm cho nó.
  - Mất texture — bộ dọn rác GLB từng xoá nhầm cả 13 texture.
  - manifest.json lệch với file GLB nằm cạnh nó.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'scripts'))
import glb
import catalog

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DUP_SUFFIX = re.compile(r'\.\d{3}$')


def verify(glb_path, manifest_path):
    errors, warnings = [], []
    gltf, _ = glb.read(glb_path)

    mesh_nodes = [n.get('name', '') for n in gltf.get('nodes', []) if 'mesh' in n]
    clips = [a.get('name', '') for a in gltf.get('animations', [])]

    # --- lưới nhân bản ---
    dups = [n for n in mesh_nodes if DUP_SUFFIX.search(n)]
    if dups:
        errors.append(
            f'{len(dups)} lưới nhân bản: {", ".join(sorted(dups))}\n'
            f'      Quy trình dựng đang chồng lớp lên đầu ra cũ. '
            f'Kiểm tra input_glb và out_b_dir trong scripts/build_character.py.')

    # --- lưới bắt buộc ---
    for want in catalog.REQUIRED_MESHES:
        if not any(n == want or n.startswith(want + '.') for n in mesh_nodes):
            errors.append(f'thiếu lưới bắt buộc: {want}')

    # --- lưới tóc ---
    for want in catalog.hair_meshes():
        if want not in mesh_nodes:
            errors.append(f'thiếu lưới tóc "{want}" — trình xem có nút bấm cho nó')
    stray = [n for n in mesh_nodes
             if n.startswith('Hair') and n not in catalog.hair_meshes()]
    if stray:
        errors.append(f'lưới tóc không có trong danh mục: {", ".join(sorted(stray))}')

    # --- clip hoạt ảnh ---
    for want in catalog.state_clips():
        if want not in clips:
            errors.append(f'thiếu clip "{want}"')
    known = set(catalog.state_clips()) | {catalog.FACE_CLIP}
    for got in clips:
        if got not in known:
            warnings.append(f'clip không có trong danh mục: {got}')

    # --- node rác ---
    # Mỗi vòng nhập/xuất glTF từng để lại một object rỗng mang tên trùng lưới;
    # model đã tích được 44 cái trước khi phát hiện. Chúng không có mesh, không
    # phải xương, không phải camera hay đèn — chỉ chiếm chỗ trong danh sách node.
    joints = set(gltf['skins'][0]['joints']) if gltf.get('skins') else set()
    # Node con của một xương là đầu mút xương do Blender xuất ra — hợp lệ,
    # không phải rác.
    bone_tips = {c for j in joints for c in gltf['nodes'][j].get('children', [])}
    orphans = []
    for i, n in enumerate(gltf.get('nodes', [])):
        if i in joints or i in bone_tips or 'mesh' in n or 'camera' in n:
            continue
        if n.get('children') or 'skin' in n:
            continue
        name = n.get('name', f'node{i}')
        if name in catalog.ALLOWED_EMPTY_NODES:
            continue
        orphans.append(name)
    if orphans:
        shown = ', '.join(sorted(orphans)[:4])
        errors.append(f'{len(orphans)} node rỗng không dùng đến ({shown}'
                      f'{" …" if len(orphans) > 4 else ""})\n'
                      f'      Vết tích của vòng nhập/xuất glTF lặp lại.')

    # --- texture và bộ xương ---
    n_img = len(gltf.get('images', []))
    if n_img == 0:
        errors.append('không còn texture nào — kiểm tra bước dọn rác GLB')
    skins = gltf.get('skins', [])
    n_joints = len(skins[0]['joints']) if skins else 0
    if n_joints < 100:
        errors.append(f'chỉ còn {n_joints} xương, dự kiến 154')

    # --- manifest ---
    man = None
    if not os.path.exists(manifest_path):
        errors.append(f'thiếu {os.path.relpath(manifest_path, ROOT)}')
    else:
        with open(manifest_path, encoding='utf-8') as f:
            man = json.load(f)
        if man.get('model') != os.path.basename(glb_path):
            errors.append(f'manifest trỏ vào "{man.get("model")}" '
                          f'chứ không phải "{os.path.basename(glb_path)}"')
        man_clips = [s['clip'] for s in man.get('states', [])]
        if man_clips != [s['clip'] for s in
                         sorted(catalog.STATES, key=lambda x: x['order'])]:
            errors.append('danh sách trạng thái trong manifest lệch với danh mục')
        for st in man.get('states', []):
            if st['clip'] not in clips:
                errors.append(f'manifest khai clip "{st["clip"]}" không có trong GLB')
        for h in man.get('hairstyles', []):
            if h['mesh'] not in mesh_nodes:
                errors.append(f'manifest khai kiểu tóc "{h["mesh"]}" '
                              f'không có lưới tương ứng')

    # --- báo cáo ---
    size = os.path.getsize(glb_path) / 1e6
    print(f'\n  {os.path.relpath(glb_path, ROOT)}  {size:.2f} MB')
    print(f'  {len(mesh_nodes)} lưới · {len(clips)} clip · '
          f'{n_joints} xương · {n_img} texture')
    if man:
        print(f'  manifest dựng lúc {man.get("generated", "?")}, '
              f'{len(man.get("states", []))} trạng thái, '
              f'{len(man.get("hairstyles", []))} kiểu tóc')

    for w in warnings:
        print(f'  \033[33m~\033[0m {w}')
    for e in errors:
        print(f'  \033[31m✗\033[0m {e}')
    if not errors:
        print('  \033[32m✓\033[0m khớp danh mục\n')
    else:
        print(f'\n  {len(errors)} sai lệch\n')
    return len(errors)


if __name__ == '__main__':
    g = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        ROOT, 'build', 'female_singer_anime_idol.glb')
    sys.exit(min(verify(g, os.path.join(os.path.dirname(g), 'manifest.json')), 1))
