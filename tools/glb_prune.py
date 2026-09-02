#!/usr/bin/env python3
r"""Cắt bỏ node / hoạt ảnh khỏi GLB rồi dọn sạch dữ liệu mồ côi.

    # bỏ 6 lưới tóc trùng
    python3 tools/glb_prune.py vao.glb ra.glb --drop-nodes 'Hair_WavyCurled\.\d+'

    # dựng model nguồn: chỉ giữ tóc gốc, bỏ mọi hoạt ảnh
    python3 tools/glb_prune.py vao.glb source.glb \
        --drop-nodes 'Hair_(ShortBob|MediumShoulder|WavyCurled)' --drop-all-animations

Sau khi bỏ node, công cụ thu gom rác theo thứ tự
mesh -> accessor -> bufferView,
rồi đóng gói lại chunk BIN nên file thu nhỏ thật sự chứ không chỉ ẩn đi.
"""
import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import glb


def remap(old_list, keep_ids):
    """Trả về (danh sách mới, bảng ánh xạ chỉ số cũ -> mới)."""
    table = {}
    out = []
    for i, item in enumerate(old_list):
        if i in keep_ids:
            table[i] = len(out)
            out.append(item)
    return out, table


def prune(src, dst, drop_patterns, drop_all_anims=False, keep_anims=None):
    gltf, blob = glb.read(src)
    nodes = gltf.get('nodes', [])

    # --- 1. Chọn node cần bỏ, kèm toàn bộ node con ---
    pats = [re.compile(p) for p in drop_patterns]
    doomed = set()
    for i, nd in enumerate(nodes):
        name = nd.get('name', '')
        if any(p.fullmatch(name) for p in pats):
            doomed.add(i)
    frontier = list(doomed)
    while frontier:
        for child in nodes[frontier.pop()].get('children', []):
            if child not in doomed:
                doomed.add(child)
                frontier.append(child)

    joints = set(gltf['skins'][0]['joints']) if gltf.get('skins') else set()
    locked = doomed & joints
    if locked:
        raise SystemExit(f'Dừng: {len(locked)} node bị chọn đang là xương của skin — '
                         f'bỏ sẽ hỏng bộ xương.')

    dropped_names = sorted(nodes[i].get('name', f'node{i}') for i in doomed)
    keep_nodes = set(range(len(nodes))) - doomed
    new_nodes, node_map = remap(nodes, keep_nodes)
    for nd in new_nodes:
        if 'children' in nd:
            kids = [node_map[c] for c in nd['children'] if c in node_map]
            if kids:
                nd['children'] = kids
            else:
                del nd['children']
    for scene in gltf.get('scenes', []):
        scene['nodes'] = [node_map[n] for n in scene.get('nodes', []) if n in node_map]
    for sk in gltf.get('skins', []):
        sk['joints'] = [node_map[j] for j in sk['joints']]
        if 'skeleton' in sk:
            sk['skeleton'] = node_map[sk['skeleton']]
    gltf['nodes'] = new_nodes

    # --- 2. Hoạt ảnh: bỏ theo yêu cầu, và bỏ kênh trỏ vào node đã xóa ---
    anims = gltf.get('animations', [])
    if drop_all_anims:
        kept_anims = []
    else:
        kept_anims = [a for a in anims
                      if keep_anims is None or a.get('name') in keep_anims]
    survivors = []
    for a in kept_anims:
        chans, samps, samp_map = [], [], {}
        for ch in a['channels']:
            tgt = ch['target'].get('node')
            if tgt is None or tgt not in node_map:
                continue
            ch['target']['node'] = node_map[tgt]
            if ch['sampler'] not in samp_map:
                samp_map[ch['sampler']] = len(samps)
                samps.append(a['samplers'][ch['sampler']])
            ch['sampler'] = samp_map[ch['sampler']]
            chans.append(ch)
        if chans:
            a['channels'], a['samplers'] = chans, samps
            survivors.append(a)
    dropped_anims = [a.get('name') for a in anims if a not in survivors]
    if survivors:
        gltf['animations'] = survivors
    else:
        gltf.pop('animations', None)

    # --- 3. Dọn rác: mesh -> accessor -> bufferView ---
    keep_meshes = {nd['mesh'] for nd in gltf['nodes'] if 'mesh' in nd}
    new_meshes, mesh_map = remap(gltf.get('meshes', []), keep_meshes)
    for nd in gltf['nodes']:
        if 'mesh' in nd:
            nd['mesh'] = mesh_map[nd['mesh']]
    gltf['meshes'] = new_meshes

    # Material / texture / image dùng chung giữa các lưới nên việc bỏ vài lưới
    # gần như không giải phóng được gì ở đây. Giữ nguyên toàn bộ: rẻ hơn nhiều
    # so với rủi ro cắt nhầm một tham chiếu texture nằm trong extension.

    keep_acc = set()
    for m in new_meshes:
        keep_acc.update(glb.accessor_ids(m))
    for sk in gltf.get('skins', []):
        if 'inverseBindMatrices' in sk:
            keep_acc.add(sk['inverseBindMatrices'])
    for a in gltf.get('animations', []):
        for s in a['samplers']:
            keep_acc.add(s['input'])
            keep_acc.add(s['output'])
    new_accs, acc_map = remap(gltf.get('accessors', []), keep_acc)
    for m in new_meshes:
        for p in m['primitives']:
            p['attributes'] = {k: acc_map[v] for k, v in p['attributes'].items()}
            if 'indices' in p:
                p['indices'] = acc_map[p['indices']]
            if 'targets' in p:
                p['targets'] = [{k: acc_map[v] for k, v in t.items()}
                                for t in p['targets']]
    for sk in gltf.get('skins', []):
        if 'inverseBindMatrices' in sk:
            sk['inverseBindMatrices'] = acc_map[sk['inverseBindMatrices']]
    for a in gltf.get('animations', []):
        for s in a['samplers']:
            s['input'] = acc_map[s['input']]
            s['output'] = acc_map[s['output']]
    gltf['accessors'] = new_accs

    keep_views = set()
    for acc in new_accs:
        keep_views.update(glb.view_ids(acc))
    for im in gltf.get('images', []):
        if 'bufferView' in im:
            keep_views.add(im['bufferView'])

    # --- 4. Đóng gói lại chunk BIN, chỉ giữ phần còn dùng ---
    old_views = gltf.get('bufferViews', [])
    new_views, view_map = [], {}
    chunks = []
    cursor = 0
    for i, bv in enumerate(old_views):
        if i not in keep_views:
            continue
        start = bv.get('byteOffset', 0)
        data = blob[start:start + bv['byteLength']]
        pad = -cursor % 4
        if pad:
            chunks.append(b'\x00' * pad)
            cursor += pad
        nv = dict(bv, byteOffset=cursor, buffer=0)
        chunks.append(data)
        cursor += len(data)
        view_map[i] = len(new_views)
        new_views.append(nv)
    new_blob = b''.join(chunks)

    for acc in new_accs:
        if 'bufferView' in acc:
            acc['bufferView'] = view_map[acc['bufferView']]
        if 'sparse' in acc:
            acc['sparse']['indices']['bufferView'] = view_map[acc['sparse']['indices']['bufferView']]
            acc['sparse']['values']['bufferView'] = view_map[acc['sparse']['values']['bufferView']]
    for im in gltf.get('images', []):
        if 'bufferView' in im:
            im['bufferView'] = view_map[im['bufferView']]
    gltf['bufferViews'] = new_views
    gltf['buffers'] = [{'byteLength': len(new_blob)}]

    total = glb.write(dst, gltf, new_blob)

    before = os.path.getsize(src)
    print(f'Đã bỏ {len(dropped_names)} node: {", ".join(dropped_names) or "(không có)"}')
    if dropped_anims:
        print(f'Đã bỏ {len(dropped_anims)} clip: {", ".join(str(n) for n in dropped_anims)}')
    print(f'bufferView {len(old_views)} -> {len(new_views)}   '
          f'accessor {len(gltf.get("accessors", []))} còn lại')
    print(f'{glb.mb(before)} -> {glb.mb(total)}  '
          f'(giảm {(1 - total / before) * 100:.1f}%)')
    return total


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('src')
    ap.add_argument('dst')
    ap.add_argument('--drop-nodes', nargs='*', default=[],
                    metavar='REGEX', help='biểu thức khớp trọn tên node cần bỏ')
    ap.add_argument('--drop-all-animations', action='store_true')
    ap.add_argument('--keep-animations', nargs='*', default=None,
                    metavar='TÊN', help='chỉ giữ những clip có tên này')
    args = ap.parse_args()
    prune(args.src, args.dst, args.drop_nodes,
          args.drop_all_animations, args.keep_animations)
