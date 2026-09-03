# -*- coding: utf-8 -*-
"""Nguồn sự thật duy nhất cho danh mục trạng thái, kiểu tóc và nhóm vật liệu.

Trước file này, cùng một danh sách nằm rải ở bốn chỗ: nút bấm trong
web/index.html, bảng btnIdMap và bảng displayNameMap trong web/app.js, và tên
clip trong scripts/build_character.py. Thêm một trạng thái phải sửa cả bốn, và
chúng đã kịp lệch nhau — tiêu đề thẻ ghi "13 Trạng Thái" trong khi có 14.

Bây giờ quy trình dựng đọc file này rồi xuất ra build/manifest.json, và trình
xem tự sinh nút từ manifest. Thêm trạng thái chỉ cần thêm một mục ở đây.
"""

# order = thứ tự hiển thị trên giao diện; nhóm các tư thế đứng cạnh nhau
STATES = [
    dict(clip='01_DungNghiem',       order=1,  icon='🧍',   accent='#94a3b8',
         label='Đứng Nghiêm',        desc='Đứng nghiêm trang trọng'),
    dict(clip='02_DungNghi',         order=2,  icon='💃',   accent='#a3a3a3',
         label='Nghỉ (Trái)',        desc='Đứng nghỉ dồn chân trái'),
    dict(clip='07_DungNghi_DoiXung', order=3,  icon='💃',   accent='#c084fc',
         label='Nghỉ (Phải)',        desc='Đứng nghỉ dồn chân phải'),
    dict(clip='03_TPose',            order=4,  icon='🤸',   accent='#a3a3a3',
         label='T-Pose',             desc='Đứng dạng T-Pose chuẩn'),
    dict(clip='04_BuocDi_CoBan',     order=5,  icon='🏃',   accent='#a3a3a3',
         label='Đi Cơ Bản',          desc='Bước đi cơ bản'),
    dict(clip='05_BuocDi_TuNhien',   order=6,  icon='🚶',   accent='#4ade80',
         label='Đi Tự Nhiên',        desc='Bước đi dồn trọng tâm chân trụ'),
    dict(clip='06_TroTay_PhiaTruoc', order=7,  icon='👉',   accent='#f43f5e',
         label='Chỉ Tay Phải',       desc='Chỉ tay phải về phía trước'),
    dict(clip='08_TroTay_Trai',      order=8,  icon='👈',   accent='#fb7185',
         label='Chỉ Tay Trái',       desc='Chỉ tay trái về phía trước'),
    dict(clip='09_HaiTay_SongSong',  order=9,  icon='🙌',   accent='#38bdf8',
         label='2 Tay Song Song',    desc='Hai tay song song đưa về phía trước'),
    dict(clip='10_HaiTay_TruocMat',  order=10, icon='🌸',   accent='#f472b6',
         label='2 Tay Trước Mặt',    desc='Hai tay song song trước mặt'),
    dict(clip='11_TraiTim_YeuThuong', order=11, icon='💖',  accent='#ec4899',
         label='Bắn Tim 2 Tay',      desc='Tạo hình trái tim bằng hai tay'),
    dict(clip='12_VayTay_ChaoHoi',   order=12, icon='👋',   accent='#eab308',
         label='Vẫy Tay Chào',       desc='Vẫy tay chào khán giả'),
    dict(clip='13_Cuoi_DuyenDang',   order=13, icon='😄',   accent='#f59e0b',
         label='Cười Duyên',         desc='Cười rạng rỡ và khẽ giggle'),
    dict(clip='14_CuiChao_KetThuc',  order=14, icon='🙇‍♀️', accent='#10b981',
         label='Cúi Chào Cảm Ơn',    desc='Cúi chào khán giả kết màn'),
    dict(clip='15_BuocDi_Mocap',     order=15, icon='🎯', accent='#22d3ee',
         label='Đi (Mocap)',         desc='Bước đi retarget từ mocap thật'),
    dict(clip='16_VayTay_Mocap',     order=16, icon='🙋', accent='#34d399',
         label='Vẫy Tay (Mocap)',    desc='Vẫy tay chào, retarget từ mocap'),
    dict(clip='17_NhayMua_Mocap',    order=17, icon='💃', accent='#fb923c',
         label='Vũ Đạo (Mocap)',     desc='Một đoạn vũ đạo retarget từ mocap'),
    dict(clip='18_DanChuyen_Mocap',  order=18, icon='🗣️', accent='#818cf8',
         label='Dẫn Chuyện (Mocap)', desc='Cử chỉ dẫn chuyện, retarget từ mocap'),
]

# Không có clip khuôn mặt: biểu cảm do trình xem điều khiển lúc chạy, xem chú
# thích trong scripts/build_character.py. Để lại None để verify_build coi mọi
# clip ngoài danh mục là sai lệch thật.
FACE_CLIP = None

# key phải khớp với tên biến trong trình xem; mesh phải khớp tên object Blender
HAIRSTYLES = [
    dict(key='long',   mesh='Hair',                icon='✨', accent='#c084fc',
         label='Tóc Dài Suôn Mượt',  desc='Long Silky Idol', default=True),
    dict(key='curled', mesh='Hair_WavyCurled',     icon='🌸', accent='#f59e0b',
         label='Tóc Dài Vừa',        desc='Medium-Long Silky'),
    dict(key='medium', mesh='Hair_MediumShoulder', icon='🌸', accent='#ec4899',
         label='Tóc Ngang Vai',      desc='Shoulder Silky'),
    dict(key='bob',    mesh='Hair_ShortBob',       icon='🎀', accent='#38bdf8',
         label='Tóc Bob Ngắn',       desc='Short Bob Silky'),
]

# Các bản nhạc và bản nào thực sự có giọng hát.
#
# Không đoán bằng thuật toán: tôi đã đo trên chính hai file này bằng
# tools/lipsync_check.py và hai bản gần như không phân biệt được qua phổ — độ
# rõ tuần hoàn p90 bằng nhau (0,68), độ nhô formant trung vị chênh 0,5 dB. Một
# bộ dò rẻ tiền sẽ nhép miệng theo tiếng nhạc cụ. Nên trạng thái này được khai
# báo tường minh thay vì suy đoán.
AUDIO_TRACKS = [
    dict(file='vocal_song_pop.mp3', label='Bài hát có lời',
         icon='🎤', vocals=True, default=True),
    dict(file='jpop_anime_beat.mp3', label='Nhạc nền J-Pop',
         icon='🎶', vocals=False),
]

# Quả cầu bọc thân người để tóc không xuyên qua. Toạ độ đặt trong hệ của chính
# xương mang nó nên chúng đi theo người khi nhân vật cử động. Bảng này chảy qua
# manifest ra web/core/hair.js, và cũng được tools/make_vrm.py dùng để ghi phần
# VRMC_springBone — một bảng, hai nơi đọc.
HAIR_COLLIDERS = [
    dict(bone='J_Bip_C_UpperChest', offset=[0, -0.010, 0.045], radius=0.138),
    dict(bone='J_Bip_C_UpperChest', offset=[0, -0.010, -0.040], radius=0.135),
    dict(bone='J_Bip_C_Spine',      offset=[0, 0.010, 0.035],  radius=0.125),
    dict(bone='J_Bip_L_Shoulder',   offset=[0.040, 0, 0.015],  radius=0.098),
    dict(bone='J_Bip_R_Shoulder',   offset=[-0.040, 0, 0.015], radius=0.098),
    dict(bone='J_Bip_L_UpperArm',   offset=[0, 0, 0],          radius=0.095),
    dict(bone='J_Bip_R_UpperArm',   offset=[0, 0, 0],          radius=0.105),
]

# Siêu dữ liệu ghi vào file VRM. Đây là phần pháp lý của định dạng: nó nói ai
# được dùng avatar này và dùng vào việc gì. Mặc định đặt chặt nhất; sửa ở đây
# nếu muốn cho phép rộng hơn.
VRM_META = dict(
    name='Nữ Ca Sĩ Anime Idol',
    version='1.0',
    authors=['Dự án Studio Ca Sĩ 3D'],
    licenseUrl='https://vrm.dev/licenses/1.0/',
    avatarPermission='onlyAuthor',
    commercialUsage='personalNonProfit',
    creditNotation='required',
    allowExcessivelyViolentUsage=False,
    allowExcessivelySexualUsage=False,
    allowPoliticalOrReligiousUsage=False,
    allowAntisocialOrHateUsage=False,
    allowRedistribution=False,
    modification='prohibited',
)

# Nhóm vật liệu cho bộ đổi màu trong trình xem
MATERIAL_GROUPS = {
    'hair':    ['Hair_00_HAIR', 'HairBack_00_HAIR'],
    'skin':    ['Body_00_SKIN', 'Face_00_SKIN'],
    'eyes':    ['EyeIris_00_EYE'],
    'tops':    ['Tops_01_CLOTH'],
    'bottoms': ['Bottoms_01_CLOTH'],
    'shoes':   ['Shoes_01_CLOTH'],
}

# Các lưới bắt buộc phải có mặt trong file xuất — tools/verify_build.py kiểm tra
REQUIRED_MESHES = ['Body', 'Face']

# Node rỗng hợp lệ theo quy ước VRoid/VRM: "secondary" là gốc của hệ spring bone.
# Mọi node rỗng khác đều bị coi là rác tích tụ qua các vòng nhập/xuất glTF.
ALLOWED_EMPTY_NODES = {'secondary'}


def state_clips():
    return [s['clip'] for s in STATES]


def hair_meshes():
    return [h['mesh'] for h in HAIRSTYLES]
