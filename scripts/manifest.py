# -*- coding: utf-8 -*-
"""Xuất build/manifest.json để trình xem tự sinh giao diện.

Danh mục lấy từ scripts/catalog.py; số frame đọc trực tiếp từ action vừa bake
nên manifest luôn mô tả đúng file vừa xuất, không phải một bản chép tay.
"""
import datetime
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import catalog

FPS = 30


def frames_from_actions(actions):
    """Số frame của từng clip, đọc từ bpy.data.actions lúc dựng."""
    out = {}
    for a in actions:
        first, last = a.frame_range
        out[a.name] = int(round(last - first)) + 1
    return out


def write_manifest(path, model_file, source_file, frames_by_clip):
    """frames_by_clip: {tên clip: số frame}.

    Nhận sẵn số frame thay vì nhận đối tượng của Blender, nhờ đó
    tools/write_manifest.py sinh lại được manifest từ chính file GLB đã xuất mà
    không phải chạy lại cả quy trình dựng mười lăm phút.
    """
    by_name = frames_by_clip
    missing = [s['clip'] for s in catalog.STATES if s['clip'] not in by_name]
    if missing:
        raise RuntimeError(
            'Danh mục khai báo các clip không có trong bản dựng: '
            + ', '.join(missing))
    extra = [n for n in by_name
             if n not in catalog.state_clips() and n != catalog.FACE_CLIP]
    if extra:
        print(f'  Cảnh báo: bản dựng có clip không nằm trong danh mục: {extra}')

    states = []
    for s in sorted(catalog.STATES, key=lambda x: x['order']):
        states.append({
            'clip': s['clip'],
            'order': s['order'],
            'icon': s['icon'],
            'label': s['label'],
            'desc': s['desc'],
            'accent': s['accent'],
            'frames': by_name[s['clip']],
            'fps': FPS,
        })

    data = {
        'schema': 1,
        'generated': datetime.datetime.now().replace(microsecond=0).isoformat(),
        'model': model_file,
        'source': source_file,
        'defaultState': states[0]['clip'],
        'states': states,
        'hairstyles': [dict(h) for h in catalog.HAIRSTYLES],
        'audioTracks': [dict(t) for t in catalog.AUDIO_TRACKS],
        'materialGroups': catalog.MATERIAL_GROUPS,
    }
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f'  manifest: {len(states)} trạng thái, '
          f'{len(data["hairstyles"])} kiểu tóc -> {path}')
    return data
