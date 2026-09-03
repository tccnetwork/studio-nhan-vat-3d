#!/usr/bin/env python3
"""Tính dữ liệu cho bộ dựng bài, ghi thẳng vào build/manifest.json.

Ba thứ được tính, tất cả đều đo từ chính file GLB đã xuất chứ không khai báo tay:

  kind        Clip là tư thế tĩnh hay có cử động thật. Đo được: 10 trong 19
              trạng thái xoay dưới 3° và dịch dưới 20 mm — chúng là ảnh tĩnh,
              không phải hoạt cảnh. Biết điều đó thì mới ghép đúng: ảnh tĩnh
              dùng làm lớp tay đắp thêm, clip có cử động mới dùng làm nền.

  drift       Độ trôi gốc sau một vòng lặp. Clip vũ đạo dài trôi 385 mm mỗi
              vòng, tức là nhân vật đi khỏi sân khấu sau vài lần lặp.

  transitions Chi phí chuyển từ clip này sang clip kia: khoảng cách tư thế
              giữa khung cuối của clip đi và khung đầu của clip đến. Bộ dựng
              bài chọn nước đi rẻ nhất để cú chuyển không bị giật.

Chạy: python3 tools/choreo_data.py [đường/dẫn.glb] [đường/dẫn/manifest.json]
"""
import json
import math
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import glb

# Ngưỡng phân loại. Dưới ngần này thì mắt thường không thấy clip đang động.
POSE_ROT_DEG = 3.0
POSE_MOVE_MM = 20.0

# Xương nào đáng kể khi so tư thế. Ngón tay và xương phụ động liên tục mà không
# ảnh hưởng tới dáng nhìn từ xa, tính vào chỉ làm nhiễu chi phí chuyển.
SKIP = ('Thumb', 'Index', 'Middle', 'Ring', 'Little', 'J_Sec_', 'J_Adj_',
        'J_Aim_', 'J_Roll_', '_end', 'Eye', 'Face')
WEIGHTS = [
    ('Hips', 3.0), ('Spine', 3.0), ('Chest', 2.5),
    ('UpperLeg', 2.5), ('LowerLeg', 2.0), ('Foot', 1.5),
    ('UpperArm', 2.0), ('LowerArm', 1.5), ('Hand', 1.0),
    ('Shoulder', 1.2), ('Neck', 1.2), ('Head', 1.2),
]

NC = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}
CT = {5126: ('f', 4), 5123: ('H', 2), 5121: ('B', 1)}


def bone_weight(name):
    for key, w in WEIGHTS:
        if key in name:
            return w
    return 0.0


def read_accessor(gltf, blob, index):
    acc = gltf['accessors'][index]
    view = gltf['bufferViews'][acc['bufferView']]
    fmt, size = CT[acc['componentType']]
    n = NC[acc['type']]
    off = view.get('byteOffset', 0) + acc.get('byteOffset', 0)
    stride = view.get('byteStride') or size * n
    return [struct.unpack_from('<' + fmt * n, blob, off + i * stride)
            for i in range(acc['count'])]


def quat_angle(a, b):
    """Góc giữa hai quaternion, tính bằng độ. Lấy trị tuyệt đối của tích vô
    hướng vì q và -q là cùng một phép xoay."""
    d = abs(sum(x * y for x, y in zip(a, b)))
    return 2.0 * math.degrees(math.acos(max(-1.0, min(1.0, d))))


def sample_clips(gltf, blob):
    """{tên clip: {tên xương: {'rot': [...], 'pos': [...]}}}"""
    names = [n.get('name', '') for n in gltf['nodes']]
    out = {}
    for anim in gltf.get('animations', []):
        bones = {}
        for ch in anim['channels']:
            path = ch['target']['path']
            if path not in ('rotation', 'translation'):
                continue
            bone = names[ch['target']['node']]
            values = read_accessor(gltf, blob, anim['samplers'][ch['sampler']]['output'])
            bones.setdefault(bone, {})['rot' if path == 'rotation' else 'pos'] = values
        out[anim.get('name', '?')] = bones
    return out


def classify(bones):
    """Tư thế tĩnh hay hoạt cảnh thật, kèm số xương thực sự cử động."""
    moving = 0
    max_move_mm = 0.0
    for name, tracks in bones.items():
        rot = tracks.get('rot')
        if rot and len(rot) > 1:
            amp = max(quat_angle(rot[0], q) for q in rot[1:])
            if amp > POSE_ROT_DEG and bone_weight(name) > 0:
                moving += 1
        pos = tracks.get('pos')
        if pos and len(pos) > 1:
            span = max(max(p[c] for p in pos) - min(p[c] for p in pos) for c in range(3))
            max_move_mm = max(max_move_mm, span * 1000.0)
    kind = 'pose' if (moving == 0 and max_move_mm < POSE_MOVE_MM) else 'motion'
    return kind, moving, max_move_mm


def root_drift_mm(bones):
    """Độ trôi ngang của gốc sau một vòng: lệch giữa khung đầu và khung cuối.
    Bỏ qua trục dọc vì nhún lên xuống là chuyện bình thường."""
    hips = bones.get('J_Bip_C_Hips', {})
    pos = hips.get('pos')
    if not pos or len(pos) < 2:
        return [0.0, 0.0, 0.0]
    return [(pos[-1][c] - pos[0][c]) * 1000.0 for c in range(3)]


def transition_cost(from_bones, to_bones):
    """Khoảng cách tư thế giữa khung CUỐI của clip đi và khung ĐẦU của clip đến,
    tính bằng độ, có trọng số theo mức quan trọng của xương."""
    num = 0.0
    den = 0.0
    for name, tracks in from_bones.items():
        w = bone_weight(name)
        if w <= 0 or any(s in name for s in SKIP):
            continue
        a = tracks.get('rot')
        b = to_bones.get(name, {}).get('rot')
        if not a or not b:
            continue
        ang = quat_angle(a[-1], b[0])
        num += w * ang * ang
        den += w
    return math.sqrt(num / den) if den else 0.0


def main():
    model = sys.argv[1] if len(sys.argv) > 1 else 'build/female_singer_anime_idol.glb'
    manifest_path = sys.argv[2] if len(sys.argv) > 2 else 'build/manifest.json'
    gltf, blob = glb.read(model)
    clips = sample_clips(gltf, blob)

    with open(manifest_path, encoding='utf-8') as fh:
        manifest = json.load(fh)

    print('%-24s %-7s %6s %10s' % ('clip', 'loại', 'xương', 'trôi (mm)'))
    for state in manifest['states']:
        bones = clips.get(state['clip'])
        if not bones:
            continue
        kind, moving, _ = classify(bones)
        drift = root_drift_mm(bones)
        state['kind'] = kind
        state['movingBones'] = moving
        # Chỉ khử trôi ngang; nhún dọc giữ nguyên vì đó là nhịp của điệu nhảy.
        state['driftMm'] = [round(drift[0], 1), 0.0, round(drift[2], 1)]
        print('%-24s %-7s %6d %10.0f' % (state['clip'], kind, moving,
                                         math.hypot(drift[0], drift[2])))

    motions = [s['clip'] for s in manifest['states'] if s.get('kind') == 'motion']
    table = {}
    for a in motions:
        row = {b: round(transition_cost(clips[a], clips[b]), 1)
               for b in motions if b != a}
        table[a] = row
    manifest['transitions'] = table

    with open(manifest_path, 'w', encoding='utf-8') as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=1)

    print('\nchi phí chuyển (độ), càng nhỏ càng mượt:')
    head = [c.split('_', 1)[0] for c in motions]
    print('%-24s %s' % ('từ \\ sang', ' '.join('%5s' % h for h in head)))
    for a in motions:
        cells = ['%5.0f' % table[a][b] if b in table[a] else '    ·' for b in motions]
        print('%-24s %s' % (a, ' '.join(cells)))
    print('\nđã ghi vào', manifest_path)


if __name__ == '__main__':
    main()
