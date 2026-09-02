# Studio Ca Sĩ 3D

Nhân vật nữ ca sĩ anime idol dựng trên nền VRoid Studio, kèm 14 trạng thái
hoạt ảnh, 57 blendshape khuôn mặt và một trình xem chạy thẳng trên trình duyệt.

```
source/     Model nguồn — CHỈ ĐỌC. Không script nào được ghi vào đây.
build/      Kết quả dựng (glb / fbx / blend). Xóa lúc nào cũng được, dựng lại là có.
web/        Trình xem 3D — bản duy nhất.
scripts/    build_character.py dựng toàn bộ 14 trạng thái. Bản cũ nằm ở archive/.
tools/      Tiện ích thao tác GLB, không cần Blender.
mocap/      5 file BVH. Chưa dùng — xem "Việc còn dang dở".
audio/      Nhạc nền cho trình xem.
archive/    Bốn phương án đời trước và các bản viewer cũ. Không còn phát triển.
```

## Chạy trình xem

```bash
python3 -m http.server 8080
open http://localhost:8080/web/
```

## Dựng lại model

```bash
/Applications/Blender.app/Contents/MacOS/Blender --background \
    --factory-startup --python scripts/build_character.py
```

Script đọc `source/female_singer_anime_idol_base.glb`, dựng kiểu tóc và 14
trạng thái, rồi ghi ra `build/`. Nó **không bao giờ** ghi vào `source/` — có
một lệnh chặn ngay đầu hàm dựng để bảo đảm điều đó.

Đối chiếu kết quả sau mỗi lần dựng:

```bash
python3 tools/glb_report.py build/female_singer_anime_idol.glb
```

Số lưới phải đúng **4 tóc** (`Hair`, `Hair_ShortBob`, `Hair_MediumShoulder`,
`Hair_WavyCurled`) cộng `Body` và `Face`. Nếu xuất hiện tên kết thúc bằng
`.001`, `.002`… thì quy trình đã lại chồng lớp — dừng và tìm nguyên nhân.

## Tiện ích GLB

`tools/glb_report.py` in ngân sách byte theo hạng mục.
`tools/glb_prune.py` bỏ node hoặc clip hoạt ảnh rồi đóng gói lại chunk BIN.

```bash
# dựng lại model nguồn từ một bản xuất bất kỳ
python3 tools/glb_prune.py build/x.glb source/base.glb \
    --drop-nodes 'Hair_(ShortBob|MediumShoulder|WavyCurled)(\.\d+)?' \
    --drop-all-animations
```

Công cụ từ chối bỏ node đang là xương của skin, nên không thể vô tình phá
bộ xương 154 khớp.

## Việc còn dang dở

**Mocap chưa được retarget.** `scripts/build_character.py` nạp
`dataset-1_walk_happy_001.bvh` ở đầu rồi xóa ở cuối mà không dùng. Cả 14
trạng thái, kể cả hai trạng thái đi bộ, đều là keyframe quaternion viết tay.
Đây là việc chính của Giai đoạn 2.

**Trình xem viết cứng danh sách trạng thái.** 14 nút bấm nằm thẳng trong
`web/index.html`, ánh xạ tên clip nằm trong `web/app.js`. Thêm một trạng thái
là phải sửa ba chỗ. Giai đoạn 1 sẽ cho quy trình dựng xuất kèm
`build/manifest.json` để viewer tự sinh nút.

**three.js r128 phát hành năm 2021.** Chặn đường dùng nén meshopt và hệ quản
lý màu mới.

**Khẩu hình chưa bám lời hát.** Miệng xoay vòng nguyên âm theo đồng hồ chứ
không theo âm vị, dù trình xem đã có phân tích FFT thật.

## Thử nghiệm hình dạng tóc

Thuật toán cắt tóc nằm riêng ở [`scripts/hairstyles.py`](scripts/hairstyles.py).
Để thử một tham số mà không phải bake lại 14 trạng thái (chín phút), dùng:

```bash
/Applications/Blender.app/Contents/MacOS/Blender --background \
    --factory-startup --python tools/preview_hairstyles.py -- /tmp/xem_toc V1
```

Một lượt mất khoảng một phút và render 12 ảnh: bốn kiểu tóc, ba góc nhìn.
Nó dùng chung `scripts/hairstyles.py` với quy trình dựng thật nên hình ra là
hình thật, không phải bản mô phỏng riêng.

Ba tham số của mỗi kiểu: `z_back` / `z_side` là cao độ kết thúc của vạt sau và
vạt bên, `u_curve_depth` là độ cong chữ U của đường cắt sau lưng, và `hang`
điều khiển mức xoè còn giữ lại — tóc càng ngắn thì càng phải rơi thẳng, vì nó
không với tới vai nên không có gì đẩy nó ra ngoài.
