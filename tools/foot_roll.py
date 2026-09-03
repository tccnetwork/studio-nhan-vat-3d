"""Đo góc lật của bàn chân trong từng clip, bằng động học thuận trên chính GLB.

Cách đo: ở tư thế nghỉ, tìm trục cục bộ nào của xương bàn chân trỏ lên trời.
Ở mỗi khung, quay trục đó theo ma trận thế giới của khung ấy rồi lấy góc so
với hướng lên của thế giới. Góc đó chính là độ lật của lòng bàn chân:

    0°    lòng bàn chân song song mặt sàn
    ~40°  mũi chân hất lên hoặc gót hất lên khi bước — bình thường
    >90°  lòng bàn chân đã quay ngửa lên trời — bàn chân bị LẬT

Không đo bằng đại lượng nào suy ra từ chính phép retarget, nên kết quả độc lập
với giả định đã dùng lúc dựng.
"""
"""Đo hai góc của bàn chân trong từng clip, bằng động học thuận trên chính GLB.

    CHÚC  mũi chân chúc xuống hay hất lên, quanh trục ngang. Bước đi bình
          thường có góc này, tới 80–90° lúc rướn mũi chân.
    LẬT   lòng bàn chân quay ngang, quanh chính trục dọc bàn chân. Đây mới là
          lỗi: quá 45° là bắt đầu thấy lật, 180° là ngửa hẳn lên trời.

Phải chiếu cả pháp tuyến lòng bàn chân lẫn mốc so sánh lên mặt phẳng vuông góc
trục dọc rồi mới lấy góc giữa hai hình chiếu. Thiếu bước chiếu thì độ chúc lọt
vào kết quả và ngay cả tư thế T cũng báo lật 30° — thang đo tự hiệu chuẩn ở
chỗ đó: T-Pose phải ra đúng 0°.

Phép đo này không dùng bất kỳ đại lượng nào suy ra từ chính bộ retarget, nên
nó kiểm tra được scripts/retarget.py một cách độc lập.

    python3 tools/foot_roll.py [đường/dẫn.glb]
"""
import math
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import glb

NC = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}


def read_acc(g, blob, i):
    a = g['accessors'][i]
    v = g['bufferViews'][a['bufferView']]
    n = NC[a['type']]
    off = v.get('byteOffset', 0) + a.get('byteOffset', 0)
    stride = v.get('byteStride') or 4 * n
    return [struct.unpack_from('<' + 'f' * n, blob, off + k * stride)
            for k in range(a['count'])]


def quat_to_m3(q):
    x, y, z, w = q
    n = math.sqrt(x * x + y * y + z * z + w * w) or 1.0
    x, y, z, w = x / n, y / n, z / n, w / n
    return [
        [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
        [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
        [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],
    ]


def m3_mul(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3)]
            for i in range(3)]


def m3_apply(m, v):
    return [sum(m[i][k] * v[k] for k in range(3)) for i in range(3)]


def m3_t(m):
    return [[m[j][i] for j in range(3)] for i in range(3)]


def build(gltf, blob):
    nodes = gltf['nodes']
    parent = {}
    for i, n in enumerate(nodes):
        for c in n.get('children', []):
            parent[c] = i
    by_name = {n.get('name', ''): i for i, n in enumerate(nodes)}
    rest_r = {}
    rest_t = {}
    for i, n in enumerate(nodes):
        rest_r[i] = n.get('rotation', [0, 0, 0, 1])
        rest_t[i] = n.get('translation', [0, 0, 0])
    return parent, by_name, rest_r, rest_t


def sample(times, values, t):
    """Lấy mẫu gần nhất theo thời gian — mọi clip đều bake đều nên đủ chính xác."""
    lo, hi = 0, len(times) - 1
    if t <= times[0]:
        return values[0]
    if t >= times[hi]:
        return values[hi]
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if times[mid] <= t:
            lo = mid
        else:
            hi = mid
    return values[lo] if (t - times[lo]) < (times[hi] - t) else values[hi]


def clip_tracks(gltf, blob, anim):
    names = [n.get('name', '') for n in gltf['nodes']]
    out = {}
    for ch in anim['channels']:
        path = ch['target']['path']
        if path not in ('rotation', 'translation'):
            continue
        node = ch['target']['node']
        smp = anim['samplers'][ch['sampler']]
        times = [x[0] for x in read_acc(gltf, blob, smp['input'])]
        vals = read_acc(gltf, blob, smp['output'])
        out.setdefault(node, {})[path] = (times, vals)
    return out


def world_rot(node, chain_cache, parent, tracks, rest_r, t):
    if node in chain_cache:
        return chain_cache[node]
    tr = tracks.get(node, {})
    if 'rotation' in tr:
        q = sample(tr['rotation'][0], tr['rotation'][1], t)
    else:
        q = rest_r[node]
    local = quat_to_m3(q)
    p = parent.get(node)
    if p is None:
        w = local
    else:
        w = m3_mul(world_rot(p, chain_cache, parent, tracks, rest_r, t), local)
    chain_cache[node] = w
    return w


def norm(v):
    n = math.sqrt(sum(x * x for x in v)) or 1.0
    return [x / n for x in v]


def cross(a, b):
    return [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]]


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def world_pos(node, parent, tracks, rest_r, rest_t, t):
    """Vị trí thế giới của một khớp, tính cả phần dịch chuyển có hoạt hoá."""
    chain = []
    n = node
    while n is not None:
        chain.append(n)
        n = parent.get(n)
    p = [0.0, 0.0, 0.0]
    m = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
    for n in reversed(chain):
        tr = tracks.get(n, {})
        q = sample(*tr['rotation'], t) if 'rotation' in tr else rest_r[n]
        tv = sample(*tr['translation'], t) if 'translation' in tr else rest_t[n]
        p = [p[i] + m_row_dot(m, tv, i) for i in range(3)]
        m = m3_mul(m, quat_to_m3(q))
    return p, m


def m_row_dot(m, v, i):
    return sum(m[i][k] * v[k] for k in range(3))


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    model = (sys.argv[1] if len(sys.argv) > 1
             else os.path.join(root, 'build', 'female_singer_anime_idol.glb'))
    gltf, blob = glb.read(model)
    parent, by_name, rest_r, rest_t = build(gltf, blob)

    UP = [0.0, 1.0, 0.0]
    print('Tách riêng hai góc của bàn chân:')
    print('  CHÚC  = mũi chân chúc xuống hay hất lên, quanh trục ngang — bước đi bình thường có')
    print('  LẬT   = lòng bàn chân quay ngang, quanh trục dọc bàn chân — đây mới là lỗi')
    print()
    print('%-24s %9s %9s   %9s %9s   %s'
          % ('clip', 'chúc tb', 'chúc max', 'LẬT tb', 'LẬT max', 'khung lật >45°'))
    rows = []
    for anim in gltf.get('animations', []):
        tracks = clip_tracks(gltf, blob, anim)
        # thời lượng
        tmax = 0.0
        for node, tr in tracks.items():
            for path, (times, _) in tr.items():
                tmax = max(tmax, times[-1])
        n_frames = max(2, int(round(tmax * 30)) + 1)

        pitches, rolls = [], []
        bad = 0
        total = 0
        for side in ('L', 'R'):
            foot = by_name.get('J_Bip_%s_Foot' % side)
            toe = by_name.get('J_Bip_%s_ToeBase' % side)
            if foot is None or toe is None:
                continue
            r0 = world_rot(foot, {}, parent, {}, rest_r, 0.0)
            a_up = m3_apply(m3_t(r0), UP)      # trục cục bộ trỏ lên ở tư thế nghỉ
            for k in range(n_frames):
                t = k / 30.0
                pf, rf = world_pos(foot, parent, tracks, rest_r, rest_t, t)
                pt, _ = world_pos(toe, parent, tracks, rest_r, rest_t, t)
                fwd = norm([pt[i] - pf[i] for i in range(3)])
                nrm = norm(m3_apply(rf, a_up))
                # CHÚC: góc của trục dọc bàn chân so với mặt phẳng sàn.
                pitches.append(abs(math.degrees(math.asin(max(-1.0, min(1.0, fwd[1]))))))
                # LẬT: chỉ là phần xoay QUANH trục dọc bàn chân. Phải chiếu cả
                # pháp tuyến lòng bàn chân lẫn mốc so sánh lên mặt phẳng vuông
                # góc với trục dọc, rồi mới lấy góc giữa hai hình chiếu. Thiếu
                # bước chiếu thì độ chúc lọt vào kết quả và tư thế T cũng báo
                # lật 30° — chính là lỗi ở lần đo trước.
                rv = [UP[i] - fwd[i] * dot(fwd, UP) for i in range(3)]
                nv = [nrm[i] - fwd[i] * dot(fwd, nrm) for i in range(3)]
                if math.sqrt(dot(rv, rv)) < 1e-4 or math.sqrt(dot(nv, nv)) < 1e-4:
                    continue           # bàn chân dựng thẳng đứng, không định nghĩa được
                c = max(-1.0, min(1.0, dot(norm(nv), norm(rv))))
                roll = math.degrees(math.acos(c))
                rolls.append(roll)
                total += 1
                if roll > 45.0:
                    bad += 1
        if not rolls:
            continue
        rows.append((anim.get('name', '?'),
                     sum(pitches) / len(pitches), max(pitches),
                     sum(rolls) / len(rolls), max(rolls), bad, total))

    rows.sort(key=lambda r: -r[4])
    for name, pa, pm, ra, rm, bad, tot in rows:
        flag = ''
        if rm > 90:
            flag = '  ← LẬT NGỬA'
        elif rm > 45:
            flag = '  ← lật nhiều'
        print('%-24s %8.0f° %8.0f°   %8.0f° %8.0f°   %3d/%-4d%s'
              % (name, pa, pm, ra, rm, bad, tot, flag))


if __name__ == '__main__':
    main()
