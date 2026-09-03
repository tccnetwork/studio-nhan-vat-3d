#!/usr/bin/env python3
"""Đo độ vặn của bàn chân trong từng clip, bằng động học thuận trên chính GLB.

Đo hai đại lượng khác nhau, và phân biệt được chúng là toàn bộ giá trị của
công cụ này:

  CỔ CHÂN   góc giữa bàn chân và CẲNG CHÂN, quanh trục dọc bàn chân. Đây là
            đại lượng có giới hạn sinh lý: khớp cổ chân lật trong/lật ngoài
            được khoảng ±25–30°, quá thế là bàn chân vặn rời khỏi ống chân.
            Chỉ con số này mới nói được clip có lỗi hay không.

  SO THẾ GIỚI  góc giữa lòng bàn chân và hướng lên của thế giới. KHÔNG bị giới
            hạn gì: chân xoay ra ngoài hay người nghiêng đều làm nó lớn lên
            một cách hoàn toàn bình thường. Cột này chỉ để tham khảo.

Lẫn hai đại lượng này là một cái bẫy thật, không phải chuyện lý thuyết: lần
đầu tôi ép bàn chân theo cột SO THẾ GIỚI và làm hỏng hẳn clip đi bộ — clip ấy
so với thế giới lên tới 180° nhưng cổ chân chỉ vặn 27°, tức vốn không có lỗi;
ép xong thì cổ chân vặn 169°.

Hai điều kiện làm phép đo đúng:

  * Phải chiếu cả pháp tuyến lòng bàn chân lẫn mốc so sánh lên mặt phẳng vuông
    góc trục dọc rồi mới lấy góc giữa hai hình chiếu. Thiếu bước chiếu thì độ
    chúc mũi chân lọt vào kết quả và ngay cả tư thế T cũng báo vặn 30°.
  * Khi bàn chân gần thẳng hàng với cẳng chân (mũi chân rướn hết), hình chiếu
    co về 0 và góc vặn không còn xác định. Những khung đó phải bỏ ra, nếu không
    nhiễu ở đó bị đọc thành lỗi 60°.

Phép đo không dùng bất kỳ đại lượng nào suy ra từ scripts/retarget.py, nên nó
kiểm tra được bộ retarget một cách độc lập.

    python3 tools/foot_roll.py [đường/dẫn.glb]
"""
import math
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import glb

NC = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}
UP = (0.0, 1.0, 0.0)
ANKLE_LIMIT = 30.0        # độ, giới hạn sinh lý của khớp cổ chân
MIN_PROJ = 0.25           # dưới mức này coi như bàn chân thẳng hàng cẳng chân


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
    return ((1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)),
            (2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)),
            (2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)))


def m3_mul(a, b):
    return tuple(tuple(sum(a[i][k] * b[k][j] for k in range(3))
                       for j in range(3)) for i in range(3))


def m3_apply(m, v):
    return tuple(sum(m[i][k] * v[k] for k in range(3)) for i in range(3))


def m3_t(m):
    return tuple(tuple(m[j][i] for j in range(3)) for i in range(3))


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def norm(v):
    n = math.sqrt(dot(v, v)) or 1.0
    return tuple(x / n for x in v)


def scene_graph(gltf):
    parent = {}
    for i, n in enumerate(gltf['nodes']):
        for c in n.get('children', []):
            parent[c] = i
    by_name = {n.get('name', ''): i for i, n in enumerate(gltf['nodes'])}
    rest_r = {i: tuple(n.get('rotation', (0, 0, 0, 1)))
              for i, n in enumerate(gltf['nodes'])}
    rest_t = {i: tuple(n.get('translation', (0, 0, 0)))
              for i, n in enumerate(gltf['nodes'])}
    return parent, by_name, rest_r, rest_t


def sample(times, values, t):
    if t <= times[0]:
        return values[0]
    if t >= times[-1]:
        return values[-1]
    lo, hi = 0, len(times) - 1
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if times[mid] <= t:
            lo = mid
        else:
            hi = mid
    return values[lo] if (t - times[lo]) < (times[hi] - t) else values[hi]


def clip_tracks(gltf, blob, anim):
    out = {}
    for ch in anim['channels']:
        path = ch['target']['path']
        if path not in ('rotation', 'translation'):
            continue
        smp = anim['samplers'][ch['sampler']]
        times = [x[0] for x in read_acc(gltf, blob, smp['input'])]
        out.setdefault(ch['target']['node'], {})[path] = (
            times, read_acc(gltf, blob, smp['output']))
    return out


def world(node, parent, tracks, rest_r, rest_t, t):
    """Vị trí và ma trận xoay của một khớp trong hệ thế giới."""
    chain = []
    n = node
    while n is not None:
        chain.append(n)
        n = parent.get(n)
    p = (0.0, 0.0, 0.0)
    m = ((1, 0, 0), (0, 1, 0), (0, 0, 1))
    for n in reversed(chain):
        tr = tracks.get(n, {})
        q = sample(*tr['rotation'], t) if 'rotation' in tr else rest_r[n]
        tv = sample(*tr['translation'], t) if 'translation' in tr else rest_t[n]
        p = tuple(p[i] + sum(m[i][k] * tv[k] for k in range(3)) for i in range(3))
        m = m3_mul(m, quat_to_m3(q))
    return p, m


def signed_roll(fwd, normal, ref):
    """Góc xoay của normal so với ref, QUANH trục fwd. Trả về (góc, độ tin)."""
    nv = tuple(normal[i] - fwd[i] * dot(fwd, normal) for i in range(3))
    rv = tuple(ref[i] - fwd[i] * dot(fwd, ref) for i in range(3))
    ln, lr = math.sqrt(dot(nv, nv)), math.sqrt(dot(rv, rv))
    if ln < 1e-6 or lr < 1e-6:
        return None, 0.0
    nv, rv = norm(nv), norm(rv)
    a = math.degrees(math.acos(max(-1.0, min(1.0, dot(nv, rv)))))
    if dot(cross(nv, rv), fwd) < 0:
        a = -a
    return a, min(ln, lr)


def measure(model):
    gltf, blob = glb.read(model)
    parent, by_name, rest_r, rest_t = scene_graph(gltf)
    rows = []
    for anim in gltf.get('animations', []):
        tracks = clip_tracks(gltf, blob, anim)
        tmax = max((times[-1] for tr in tracks.values()
                    for (times, _) in tr.values()), default=0.0)
        n = max(2, int(round(tmax * 30)) + 1)
        ankle, wrld, skipped = [], [], 0
        for side in ('L', 'R'):
            foot = by_name.get('J_Bip_%s_Foot' % side)
            toe = by_name.get('J_Bip_%s_ToeBase' % side)
            knee = by_name.get('J_Bip_%s_LowerLeg' % side)
            if None in (foot, toe, knee):
                continue
            # Trục cục bộ trỏ lên trời, và góc vặn cổ chân, lấy ở tư thế nghỉ
            # để làm mốc 0 — nên số 0 nghĩa là "đúng như bộ xương gốc".
            _, r0 = world(foot, parent, {}, rest_r, rest_t, 0.0)
            a_up = m3_apply(m3_t(r0), UP)
            pf0, rf0 = world(foot, parent, {}, rest_r, rest_t, 0.0)
            pt0, _ = world(toe, parent, {}, rest_r, rest_t, 0.0)
            pk0, _ = world(knee, parent, {}, rest_r, rest_t, 0.0)
            base, _ = signed_roll(norm(tuple(pt0[i] - pf0[i] for i in range(3))),
                                  m3_apply(rf0, a_up),
                                  norm(tuple(pk0[i] - pf0[i] for i in range(3))))
            base = base or 0.0
            for k in range(n):
                t = k / 30.0
                pf, rf = world(foot, parent, tracks, rest_r, rest_t, t)
                pt, _ = world(toe, parent, tracks, rest_r, rest_t, t)
                pk, _ = world(knee, parent, tracks, rest_r, rest_t, t)
                fwd = norm(tuple(pt[i] - pf[i] for i in range(3)))
                shin = norm(tuple(pk[i] - pf[i] for i in range(3)))
                nrm = norm(m3_apply(rf, a_up))
                aw, _ = signed_roll(fwd, nrm, UP)
                aa, conf = signed_roll(fwd, nrm, shin)
                if aw is not None:
                    wrld.append(abs(aw))
                if aa is None or conf < MIN_PROJ:
                    skipped += 1        # mũi chân rướn thẳng hàng cẳng chân
                    continue
                ankle.append(abs(aa - base))
        if not ankle:
            continue
        rows.append(dict(
            name=anim.get('name', '?'),
            ankle_avg=sum(ankle) / len(ankle), ankle_max=max(ankle),
            world_avg=sum(wrld) / len(wrld) if wrld else 0.0,
            world_max=max(wrld) if wrld else 0.0,
            bad=sum(1 for a in ankle if a > ANKLE_LIMIT + 1.0),
            total=len(ankle), skipped=skipped))
    return rows


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    model = (sys.argv[1] if len(sys.argv) > 1
             else os.path.join(root, 'build', 'female_singer_anime_idol.glb'))
    rows = measure(model)
    rows.sort(key=lambda r: -r['ankle_max'])
    print('CỔ CHÂN là góc bàn chân so với cẳng chân — giới hạn sinh lý %.0f°.'
          % ANKLE_LIMIT)
    print('SO THẾ GIỚI chỉ để tham khảo, đại lượng này không bị giới hạn gì.')
    print()
    print('%-24s %18s %18s %14s %s'
          % ('clip', 'CỔ CHÂN tb/max', 'so t.giới tb/max', 'quá giới hạn',
             'bỏ (rướn mũi)'))
    for r in rows:
        flag = '  ← VẶN' if r['ankle_max'] > ANKLE_LIMIT + 1.0 else ''
        print('%-24s %8.0f° %8.0f° %8.0f° %8.0f° %8d/%-5d %8d%s'
              % (r['name'], r['ankle_avg'], r['ankle_max'],
                 r['world_avg'], r['world_max'], r['bad'], r['total'],
                 r['skipped'], flag))


if __name__ == '__main__':
    main()
