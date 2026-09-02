"""Đọc / ghi GLB thuần Python, không phụ thuộc Blender.

Dùng chung cho glb_report.py và glb_prune.py.
"""
import json
import struct

GLB_MAGIC = 0x46546C67
CHUNK_JSON = 0x4E4F534A
CHUNK_BIN = 0x004E4942


def read(path):
    """Trả về (gltf_dict, bin_bytes)."""
    with open(path, 'rb') as f:
        magic, version, _total = struct.unpack('<III', f.read(12))
        if magic != GLB_MAGIC:
            raise ValueError(f'{path}: không phải file GLB')
        if version != 2:
            raise ValueError(f'{path}: chỉ hỗ trợ glTF 2.0, file này là bản {version}')
        gltf, blob = None, b''
        while True:
            head = f.read(8)
            if len(head) < 8:
                break
            length, kind = struct.unpack('<II', head)
            data = f.read(length)
            if kind == CHUNK_JSON:
                gltf = json.loads(data.decode('utf-8'))
            elif kind == CHUNK_BIN:
                blob = data
    if gltf is None:
        raise ValueError(f'{path}: thiếu chunk JSON')
    return gltf, blob


def write(path, gltf, blob):
    """Ghi GLB với đệm 4 byte đúng chuẩn."""
    js = json.dumps(gltf, separators=(',', ':')).encode('utf-8')
    js += b' ' * (-len(js) % 4)
    blob = blob + b'\x00' * (-len(blob) % 4)
    total = 12 + 8 + len(js) + (8 + len(blob) if blob else 0)
    with open(path, 'wb') as f:
        f.write(struct.pack('<III', GLB_MAGIC, 2, total))
        f.write(struct.pack('<II', len(js), CHUNK_JSON))
        f.write(js)
        if blob:
            f.write(struct.pack('<II', len(blob), CHUNK_BIN))
            f.write(blob)
    return total


def view_ids(accessor):
    """Mọi bufferView mà một accessor tham chiếu (kể cả sparse)."""
    out = []
    if 'bufferView' in accessor:
        out.append(accessor['bufferView'])
    sparse = accessor.get('sparse')
    if sparse:
        out.append(sparse['indices']['bufferView'])
        out.append(sparse['values']['bufferView'])
    return out


def accessor_ids(mesh):
    """Mọi accessor mà một mesh tham chiếu."""
    out = []
    for prim in mesh['primitives']:
        out.extend(prim['attributes'].values())
        if 'indices' in prim:
            out.append(prim['indices'])
        for target in prim.get('targets', []):
            out.extend(target.values())
    return out


def mb(n):
    return f'{n / 1e6:.2f} MB'
