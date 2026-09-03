#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Xuất file .vrm từ GLB đã dựng.

    python3 tools/make_vrm.py

VRM là một extension của glTF chứ không phải định dạng riêng, nên việc cần làm
là bổ sung khối VRMC_vrm mô tả: bộ xương người chuẩn, bảng biểu cảm, điểm nhìn,
siêu dữ liệu bản quyền — cộng VRMC_springBone cho tóc động.

Model gốc là VRoid nên tên xương đã theo đúng quy ước J_Bip_*, ánh xạ sang tên
xương chuẩn của VRM là một-một. Mặt nhân vật hướng +Z, đúng yêu cầu VRM 1.0
(bản 0.x thì ngược lại).

Hoạt ảnh bị lược bỏ: VRM mô tả một nhân vật, không phải một đoạn diễn.
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
import glb
import glb_prune
import catalog

# Tên xương VRoid -> tên xương chuẩn VRM 1.0
HUMAN_BONES = {
    'hips': 'J_Bip_C_Hips', 'spine': 'J_Bip_C_Spine', 'chest': 'J_Bip_C_Chest',
    'upperChest': 'J_Bip_C_UpperChest', 'neck': 'J_Bip_C_Neck', 'head': 'J_Bip_C_Head',
    'leftEye': 'J_Adj_L_FaceEye', 'rightEye': 'J_Adj_R_FaceEye',
}
for side, pre in (('left', 'L'), ('right', 'R')):
    HUMAN_BONES.update({
        f'{side}Shoulder': f'J_Bip_{pre}_Shoulder',
        f'{side}UpperArm': f'J_Bip_{pre}_UpperArm',
        f'{side}LowerArm': f'J_Bip_{pre}_LowerArm',
        f'{side}Hand': f'J_Bip_{pre}_Hand',
        f'{side}UpperLeg': f'J_Bip_{pre}_UpperLeg',
        f'{side}LowerLeg': f'J_Bip_{pre}_LowerLeg',
        f'{side}Foot': f'J_Bip_{pre}_Foot',
        f'{side}Toes': f'J_Bip_{pre}_ToeBase',
    })
    # Ngón cái VRM 1.0 dùng tên đốt bàn / gần / xa; bốn ngón kia là gần / giữa / xa.
    HUMAN_BONES.update({
        f'{side}ThumbMetacarpal': f'J_Bip_{pre}_Thumb1',
        f'{side}ThumbProximal': f'J_Bip_{pre}_Thumb2',
        f'{side}ThumbDistal': f'J_Bip_{pre}_Thumb3',
    })
    for finger in ('Index', 'Middle', 'Ring', 'Little'):
        HUMAN_BONES.update({
            f'{side}{finger}Proximal': f'J_Bip_{pre}_{finger}1',
            f'{side}{finger}Intermediate': f'J_Bip_{pre}_{finger}2',
            f'{side}{finger}Distal': f'J_Bip_{pre}_{finger}3',
        })

REQUIRED_BONES = [
    'hips', 'spine', 'head',
    'leftUpperArm', 'leftLowerArm', 'leftHand',
    'rightUpperArm', 'rightLowerArm', 'rightHand',
    'leftUpperLeg', 'leftLowerLeg', 'leftFoot',
    'rightUpperLeg', 'rightLowerLeg', 'rightFoot',
]

# Biểu cảm chuẩn VRM -> hậu tố tên morph target của VRoid
EXPRESSIONS = {
    'aa': 'Fcl_MTH_A', 'ih': 'Fcl_MTH_I', 'ou': 'Fcl_MTH_U',
    'ee': 'Fcl_MTH_E', 'oh': 'Fcl_MTH_O',
    'blink': 'Fcl_EYE_Close', 'blinkLeft': 'Fcl_EYE_Close_L',
    'blinkRight': 'Fcl_EYE_Close_R',
    'happy': 'Fcl_ALL_Joy', 'angry': 'Fcl_ALL_Angry',
    'sad': 'Fcl_ALL_Sorrow', 'relaxed': 'Fcl_ALL_Fun',
    'surprised': 'Fcl_ALL_Surprised', 'neutral': 'Fcl_ALL_Neutral',
}


def node_index(names, want):
    try:
        return names.index(want)
    except ValueError:
        return None


def build_humanoid(names):
    bones, missing = {}, []
    for vrm_name, vroid_name in HUMAN_BONES.items():
        i = node_index(names, vroid_name)
        if i is not None:
            bones[vrm_name] = {'node': i}
        elif vrm_name in REQUIRED_BONES:
            missing.append(f'{vrm_name} ({vroid_name})')
    if missing:
        raise SystemExit('Thiếu xương bắt buộc của VRM: ' + ', '.join(missing))
    return {'humanBones': bones}


def build_expressions(gltf, names):
    preset, unmatched = {}, []
    for vrm_name, suffix in EXPRESSIONS.items():
        binds = []
        for ni, node in enumerate(gltf['nodes']):
            if 'mesh' not in node:
                continue
            targets = gltf['meshes'][node['mesh']].get('extras', {}).get('targetNames', [])
            for mi, tname in enumerate(targets):
                # Blender ghi tên dạng "Face_Blendshape.Fcl_MTH_A"; so khớp phần đuôi
                # và loại trừ trùng tiền tố như Fcl_MTH_U với Fcl_MTH_Up.
                tail = tname.split('.')[-1]
                if tail == suffix:
                    binds.append({'node': ni, 'index': mi, 'weight': 1.0})
        if binds:
            preset[vrm_name] = {
                'morphTargetBinds': binds,
                'isBinary': vrm_name.startswith('blink'),
                'overrideBlink': 'none',
                'overrideLookAt': 'none',
                'overrideMouth': 'none',
            }
        else:
            unmatched.append(f'{vrm_name} ({suffix})')
    if unmatched:
        print(f'  không tìm được morph cho: {", ".join(unmatched)}')
    return {'preset': preset, 'custom': {}}


def build_spring_bones(gltf, names):
    """Chuỗi tóc và quả cầu va chạm, lấy đúng bảng mà web/core/hair.js dùng."""
    children = {}
    for i, n in enumerate(gltf['nodes']):
        for c in n.get('children', []):
            children.setdefault(i, []).append(c)

    colliders, indices = [], []
    for c in catalog.HAIR_COLLIDERS:
        i = node_index(names, c['bone'])
        if i is None:
            continue
        indices.append(len(colliders))
        colliders.append({
            'node': i,
            'shape': {'sphere': {'offset': list(c['offset']), 'radius': c['radius']}},
        })
    groups = [{'name': 'than_nguoi', 'colliders': indices}] if colliders else []

    def is_hair(i):
        n = names[i]
        return 'hair' in n.lower() and '_Sec_' in n

    springs = []
    for i, n in enumerate(gltf['nodes']):
        if not is_hair(i):
            continue
        parent = next((p for p, kids in children.items() if i in kids), None)
        if parent is not None and is_hair(parent):
            continue                       # không phải gốc chuỗi
        chain, cur = [], i
        while cur is not None:
            chain.append(cur)
            kids = [k for k in children.get(cur, []) if is_hair(k)]
            cur = kids[0] if kids else None
        if len(chain) < 2:
            continue
        springs.append({
            'name': names[i],
            'joints': [{
                'node': j,
                'hitRadius': 0.018,
                'stiffness': 0.6,
                'gravityPower': 0.3,
                'gravityDir': [0, -1, 0],
                'dragForce': 0.4,
            } for j in chain],
            'colliderGroups': list(range(len(groups))),
        })
    return {
        'specVersion': '1.0',
        'colliders': colliders,
        'colliderGroups': groups,
        'springs': springs,
    }


def make_vrm(src, dst, keep_animations=False):
    tmp = dst + '.tmp'
    if keep_animations:
        gltf, blob = glb.read(src)
    else:
        # VRM mô tả một nhân vật, không phải một đoạn diễn. Bỏ hoạt ảnh và dọn
        # luôn dữ liệu mồ côi thay vì để lại byte chết.
        glb_prune.prune(src, tmp, [], drop_all_anims=True)
        gltf, blob = glb.read(tmp)
        os.remove(tmp)

    names = [n.get('name', '') for n in gltf['nodes']]
    head = node_index(names, 'J_Bip_C_Head')

    vrm = {
        'specVersion': '1.0',
        'meta': dict(catalog.VRM_META),
        'humanoid': build_humanoid(names),
        'firstPerson': {'meshAnnotations': [
            {'node': i, 'type': 'auto'}
            for i, n in enumerate(gltf['nodes']) if 'mesh' in n
        ]},
        'lookAt': {
            'offsetFromHeadBone': [0.0, 0.06, 0.0],
            'type': 'bone',
            'rangeMapHorizontalInner': {'inputMaxValue': 90.0, 'outputScale': 10.0},
            'rangeMapHorizontalOuter': {'inputMaxValue': 90.0, 'outputScale': 10.0},
            'rangeMapVerticalDown': {'inputMaxValue': 90.0, 'outputScale': 10.0},
            'rangeMapVerticalUp': {'inputMaxValue': 90.0, 'outputScale': 10.0},
        },
        'expressions': build_expressions(gltf, names),
    }
    springs = build_spring_bones(gltf, names)

    gltf.setdefault('extensions', {})['VRMC_vrm'] = vrm
    used = gltf.setdefault('extensionsUsed', [])
    for name in ('VRMC_vrm', 'VRMC_springBone'):
        if name not in used:
            used.append(name)
    gltf['extensions']['VRMC_springBone'] = springs

    total = glb.write(dst, gltf, blob)
    print(f'  xương người   : {len(vrm["humanoid"]["humanBones"])} khớp '
          f'(bắt buộc {len(REQUIRED_BONES)} khớp đều có)')
    print(f'  biểu cảm      : {len(vrm["expressions"]["preset"])} nhóm chuẩn')
    print(f'  tóc động      : {len(springs["springs"])} chuỗi, '
          f'{len(springs["colliders"])} quả cầu va chạm')
    print(f'  hoạt ảnh      : {"giữ" if keep_animations else "đã lược bỏ"}')
    print(f'  {os.path.relpath(dst, ROOT)}  {glb.mb(total)}')
    return dst


if __name__ == '__main__':
    build = os.path.join(ROOT, 'build')
    make_vrm(os.path.join(build, 'female_singer_anime_idol.glb'),
             os.path.join(build, 'female_singer_anime_idol.vrm'),
             keep_animations='--keep-animations' in sys.argv)
