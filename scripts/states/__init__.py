# -*- coding: utf-8 -*-
"""Sổ đăng ký trạng thái hoạt ảnh — mỗi trạng thái một module.

Thứ tự trong ORDER là thứ tự bake, không phải thứ tự hiển thị; thứ tự hiển thị
nằm ở scripts/catalog.py.
"""
import importlib

ORDER = [
    ('01_DungNghiem', 's01_DungNghiem'),
    ('02_DungNghi', 's02_DungNghi'),
    ('03_TPose', 's03_TPose'),
    ('04_BuocDi_CoBan', 's04_BuocDi_CoBan'),
    ('05_BuocDi_TuNhien', 's05_BuocDi_TuNhien'),
    ('06_TroTay_PhiaTruoc', 's06_TroTay_PhiaTruoc'),
    ('07_DungNghi_DoiXung', 's07_DungNghi_DoiXung'),
    ('08_TroTay_Trai', 's08_TroTay_Trai'),
    ('09_HaiTay_SongSong', 's09_HaiTay_SongSong'),
    ('10_HaiTay_TruocMat', 's10_HaiTay_TruocMat'),
    ('11_TraiTim_YeuThuong', 's11_TraiTim_YeuThuong'),
    ('12_VayTay_ChaoHoi', 's12_VayTay_ChaoHoi'),
    ('13_Cuoi_DuyenDang', 's13_Cuoi_DuyenDang'),
    ('14_CuiChao_KetThuc', 's14_CuiChao_KetThuc'),
    ('15_BuocDi_Mocap', 's15_BuocDi_Mocap'),
    ('16_VayTay_Mocap', 's16_VayTay_Mocap'),
    ('17_NhayMua_Mocap', 's17_NhayMua_Mocap'),
    ('18_DanChuyen_Mocap', 's18_DanChuyen_Mocap'),
]


def bake_states(char_arm, pb, wanted=None):
    """Bake các trạng thái được chọn. wanted=None nghĩa là bake tất cả."""
    if wanted:
        unknown = [w for w in wanted if w not in dict(ORDER)]
        if unknown:
            raise SystemExit('Không có trạng thái: ' + ', '.join(unknown)
                             + '\nCó thể chọn: ' + ', '.join(c for c, _ in ORDER))
    actions = []
    for clip, mod_name in ORDER:
        if wanted and clip not in wanted:
            continue
        print(f'>>> Bake {clip}')
        mod = importlib.import_module('states.' + mod_name)
        actions.append(mod.bake(char_arm, pb))
    return actions
