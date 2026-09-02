# Studio Ca Sĩ 3D

Nhân vật nữ ca sĩ anime idol dựng trên nền VRoid Studio, kèm 14 trạng thái
hoạt ảnh, 57 blendshape khuôn mặt và một trình xem chạy thẳng trên trình duyệt.

```
source/     Model nguồn — CHỈ ĐỌC. Không script nào được ghi vào đây.
build/      Kết quả dựng (glb / fbx / blend / manifest.json). Dựng lại là có.
web/        Trình xem 3D — bản duy nhất, tự sinh giao diện từ manifest.
scripts/    catalog.py là danh mục gốc; build_character.py điều phối;
            states/ mỗi trạng thái một file; rig.py và hairstyles.py dùng chung.
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
BL=/Applications/Blender.app/Contents/MacOS/Blender

# đầy đủ 14 trạng thái, xuất glb + fbx + blend + manifest  (~10 phút)
$BL --background --factory-startup --python scripts/build_character.py

# một trạng thái, chỉ xuất glb, ghi vào build/preview/       (~37 giây)
$BL --background --factory-startup --python scripts/build_character.py -- \
    --states 04_BuocDi_CoBan --fast

# xem có những trạng thái nào
$BL --background --factory-startup --python scripts/build_character.py -- --list
```

Bake trạng thái chiếm khoảng 7 phút trong tổng 10 phút, nên `--states` là cách
duy nhất để thử đi thử lại một tư thế mà không mất cả buổi. Bản dựng thiếu
trạng thái luôn ghi vào `build/preview/`, không bao giờ đè lên bản chính thức.

Script đọc `source/female_singer_anime_idol_base.glb`, dựng kiểu tóc và 14
trạng thái, rồi ghi ra `build/`. Nó **không bao giờ** ghi vào `source/` — có
một lệnh chặn ngay đầu hàm dựng để bảo đảm điều đó.

Đối chiếu kết quả sau mỗi lần dựng:

```bash
python3 tools/verify_build.py     # thoát khác 0 nếu lệch danh mục
python3 tools/glb_report.py build/female_singer_anime_idol.glb
```

`verify_build.py` đối chiếu file GLB với `scripts/catalog.py` và bắt đúng những
thứ đã từng hỏng thật: lưới nhân bản đuôi `.001`, node rỗng tích tụ qua các vòng
nhập/xuất, thiếu hoặc thừa clip, mất texture, và manifest lệch với GLB.

Khi sửa những thứ đáng lẽ không được đổi kết quả — tách module, dọn dẹp — hãy
giữ lại bản GLB cũ rồi đối chiếu cấu trúc:

```bash
python3 tools/glb_diff.py /tmp/truoc.glb build/female_singer_anime_idol.glb
```

Nó so danh sách lưới kèm số đỉnh, clip kèm số kênh và số byte, số xương và số
texture. Byte của file xuất không bao giờ trùng khít giữa hai lần chạy Blender
nên so từng byte là vô nghĩa.

## Thêm một trạng thái hoạt ảnh

Danh sách trạng thái, kiểu tóc và nhóm vật liệu nằm ở **một chỗ duy nhất**:
[`scripts/catalog.py`](scripts/catalog.py). Quy trình dựng đọc file đó rồi xuất
`build/manifest.json`, và trình xem sinh toàn bộ nút bấm từ manifest.

Trước đây cùng một danh sách nằm rải ở bốn nơi — nút trong `web/index.html`, hai
bảng tra trong `web/app.js`, và tên clip trong script dựng — nên chúng đã kịp
lệch nhau: thẻ ghi "13 Trạng Thái" trong khi model có 14.

Các bước: thêm khối bake vào `scripts/build_character.py`, thêm một mục vào
`STATES` trong `catalog.py`, dựng lại, chạy `verify_build.py`. Không phải đụng
vào trình xem.

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

**Ba kiểu tóc cắt tự động chưa đạt.** Đã qua ba vòng sửa hình học và tốt hơn
nhiều so với ban đầu, nhưng chủ dự án đánh giá vẫn chưa được. Đang gác lại.
Ba nút vặn ở cuối `scripts/hairstyles.py`: `hang` (xoè hay rơi thẳng),
`evenness` (đường cắt đều hay tỉa layer), `z_back`/`z_side` (độ dài).

**Mocap chưa được retarget.** `scripts/build_character.py` nạp
`dataset-1_walk_happy_001.bvh` ở đầu rồi xóa ở cuối mà không dùng. Cả 14
trạng thái, kể cả hai trạng thái đi bộ, đều là keyframe quaternion viết tay.
Đây là việc chính của Giai đoạn 2.

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
