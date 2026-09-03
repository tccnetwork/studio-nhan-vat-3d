# Studio Ca Sĩ 3D

Nhân vật nữ ca sĩ anime idol dựng trên nền VRoid Studio, kèm 19 trạng thái
hoạt ảnh (5 trong đó retarget từ mocap thật), 57 blendshape khuôn mặt, một
trình xem chạy thẳng trên trình duyệt và một bản nhúng được vào trang khác.

```
source/     Model nguồn — CHỈ ĐỌC. Không script nào được ghi vào đây.
build/      Kết quả dựng (glb / fbx / blend / manifest.json). Dựng lại là có.
web/        core/     lõi dùng chung: nạp model, vật lý tóc, khẩu hình
            embed.js  bản nhúng vào trang khác — API công khai
            app.js    trang studio, dùng cùng lõi đó
            vendor/   bộ giải nén Draco để sẵn, không cần mạng
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

# đầy đủ 19 trạng thái, xuất glb + fbx + blend + manifest  (~70 giây)
$BL --background --factory-startup --python scripts/build_character.py

# một trạng thái, chỉ xuất glb, ghi vào build/preview/       (~37 giây)
$BL --background --factory-startup --python scripts/build_character.py -- \
    --states 04_BuocDi_CoBan --fast

# xem có những trạng thái nào
$BL --background --factory-startup --python scripts/build_character.py -- --list
```

Bản dựng thiếu trạng thái luôn ghi vào `build/preview/`, không bao giờ đè lên
bản chính thức.

Lượt dựng đầy đủ từng mất khoảng mười phút. Phần lớn thời gian đó là ghi
keyframe cho 59 xương tóc ở **mỗi frame của mỗi trạng thái**; từ khi tóc chuyển
sang mô phỏng lúc chạy thì chỉ còn khoảng bảy mươi giây.

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

**Khẩu hình chưa bám lời hát.** Miệng xoay vòng nguyên âm theo đồng hồ chứ
không theo âm vị, dù trình xem đã có phân tích FFT thật.

## Xuất VRM

```bash
python3 tools/make_vrm.py            # -> build/female_singer_anime_idol.vrm
```

VRM là một extension của glTF chứ không phải định dạng riêng, nên việc cần làm
là bổ sung khối `VRMC_vrm`: bộ xương người chuẩn, bảng biểu cảm, điểm nhìn, siêu
dữ liệu bản quyền — cộng `VRMC_springBone` cho tóc động. Model gốc là VRoid nên
tên xương đã theo đúng quy ước `J_Bip_*`, ánh xạ sang tên chuẩn VRM là một-một;
mặt nhân vật hướng +Z, đúng yêu cầu VRM 1.0 (bản 0.x thì ngược lại).

Hoạt ảnh bị lược bỏ vì VRM mô tả một nhân vật chứ không phải một đoạn diễn —
6,43 MB xuống 4,49 MB. Thêm `--keep-animations` nếu muốn giữ.

Kết quả đã kiểm chứng bằng chính thư viện `@pixiv/three-vrm`: nhận diện VRM 1.0,
54 khớp xương người (15 khớp bắt buộc đều có), 14 biểu cảm chuẩn, 47 đốt tóc
động, `lookAt` có, và `vrm.update()` chạy không lỗi sau khi đặt biểu cảm.

Phần cho phép sử dụng trong `VRM_META` của `scripts/catalog.py` đang đặt **chặt
nhất**: chỉ tác giả được dùng, không thương mại, không phân phối lại. Sửa ở đó
nếu muốn mở rộng.

## Nhúng nhân vật vào trang khác

```html
<script type="importmap">
{ "imports": {
    "three": "https://cdn.jsdelivr.net/npm/three@0.180.0/build/three.module.js",
    "three/addons/": "https://cdn.jsdelivr.net/npm/three@0.180.0/examples/jsm/" } }
</script>
<div id="slot" style="width:100%;height:520px"></div>
<script type="module">
  import { createSinger } from './web/embed.js';
  const singer = await createSinger('#slot', { state: '15_BuocDi_Mocap' });
  singer.setHairstyle('bob');
  singer.setColor('hair', '#ffc0cb');
  await singer.playAudio('vocal_song_pop.mp3');
</script>
```

Xem `web/embed-demo.html` để có ví dụ chạy được. `createSinger` trả về
`setState`, `setHairstyle`, `setColor`, `playAudio`, `pauseAudio`, `destroy`,
cùng ba danh sách `states` / `hairstyles` / `audioTracks` đọc thẳng từ manifest
— nên trang chủ nhà không phải viết cứng thứ gì.

Đường dẫn tài nguyên suy ra từ vị trí của chính `embed.js`, đổi được bằng tuỳ
chọn `base`. Không có tuỳ chọn nào bắt buộc.

Khung hình **tự tính từ hộp bao của model** và tính lại mỗi khi khung đổi kích
thước, nên khung chủ nhà cao thấp rộng hẹp thế nào cũng thấy trọn nhân vật.
Đặt `distance` nếu muốn tự quyết, `margin` để chừa nhiều hay ít quanh nhân vật.

Trong khung có hai kiểu kéo, đổi bằng `singer.setDragMode(...)` hoặc tuỳ chọn
`dragMode` lúc khởi tạo:

| | kéo chuột trái | chuột phải |
| :-- | :-- | :-- |
| `'xoay'` (mặc định) | xoay quanh nhân vật | dời nhân vật |
| `'dichuyen'` | **dời nhân vật** trong khung | xoay |

Cuộn chuột để phóng to thu nhỏ, giới hạn 0,4 – 12 m. Tâm nhìn bị chốt để nhân
vật không trôi khỏi khung, và chốt đó tính theo **tỉ lệ khung nhìn** chứ không
theo một khoảng cách cố định trong không gian 3D: phần nhìn thấy rộng bao nhiêu
là do mức phóng to quyết định, nên một chốt cứng tính bằng mét sẽ quá chặt khi
thu nhỏ và quá lỏng khi phóng to — ở khoảng cách nhỏ nhất, nửa bề rộng khung
chỉ khoảng 0,3 m. Sửa mức cho phép bằng `panFraction` (mặc định 0,30, tức lệch
nhiều nhất 30% nửa khung).

Từ lúc người xem đụng vào, việc khung đổi kích thước không canh lại góc nhìn
nữa — canh lại lúc đó là giật view ngay giữa khi họ đang xoay.
`singer.resetView()` đưa về khung mặc định.

Tắt bằng `controls: false` cho một bản nhúng tĩnh, hoặc `zoom: false` /
`pan: false` để chỉ cho xoay.

Bật `showCoords: true` để hiện toạ độ tâm nhìn, vị trí máy quay và khoảng cách
ngay trong khung — tiện khi đang căn góc. Mặc định tắt vì bản nhúng trên trang
thật không nên hiện thông tin gỡ lỗi. Bật tắt lúc chạy bằng
`singer.showCoords(true|false)`, hoặc lấy số bằng `singer.getView()` nếu muốn
tự vẽ chỗ khác.

**Trang studio và bản nhúng dùng chung `web/core/`** — vật lý tóc, bộ phân loại
nguyên âm và phần nạp model chỉ có một cài đặt duy nhất.

## Khẩu hình

Nguyên âm được đoán từ **hai formant** — hai đỉnh cộng hưởng của khoang miệng.
F1 phản ánh độ mở hàm, F2 phản ánh vị trí lưỡi trước sau; cặp (F1, F2) gần như
xác định duy nhất một nguyên âm. Bản trước xoay vòng nguyên âm theo đồng hồ
(`Math.floor(time * 3.5) % 4`) — nhìn thoáng thì khớp nhạc vì biên độ lấy từ âm
lượng, nhưng miệng mở hình gì thì không liên quan tới tiếng hát.

Kiểm tra bộ phân loại: mở Console trình duyệt, gõ `__vowelProbe()`. Nó dựng phổ
tổng hợp có formant biết trước và phải trả về `A->A I->I U->U E->E O->O`.

**Chỉ nhép khi bản nhạc có lời.** Trạng thái này được **khai báo** trong
`AUDIO_TRACKS` của `scripts/catalog.py` chứ không đoán từ tín hiệu. Tôi đã thử
đoán và đo bằng `tools/lipsync_check.py` trên chính hai file của dự án: bản có
lời và bản nhạc nền gần như không phân biệt được qua phổ — độ rõ tuần hoàn p90
bằng nhau (0,68), độ nhô formant trung vị chênh 0,5 dB. Ở mọi ngưỡng, bản không
lời vượt qua gần bằng bản có lời. Tách giọng khỏi bản phối là bài toán cần mô
hình học máy, không phải vài phép thống kê phổ.

## Vật lý tóc

Tóc **không** được bake vào clip. `web/app.js` mô phỏng spring bone theo quy ước
VRM: mỗi đốt tóc giữ vị trí chóp ở frame trước, mỗi bước lấy quán tính cộng lực
kéo về tư thế nghỉ cộng trọng lực, rồi ép chóp về đúng bán kính của đốt, cuối
cùng va chạm với các quả cầu bọc thân người.

Trước đây chuyển động tóc bake cứng vào từng clip: **0,864 MB trong 1,33 MB**
dữ liệu hoạt ảnh chỉ để lưu xương tóc, và mỗi module trạng thái phải lặp lại
cùng một đoạn rủ tóc. Nay tóc phản ứng với chuyển động thật nên nó cũng đúng cả
trong lúc chuyển tiếp giữa hai trạng thái — điều bản bake cứng không làm được.

Bốn hằng số ở đầu `web/app.js`: `HAIR_DRAG` (hãm quán tính), `HAIR_STIFFNESS`
(lực kéo về tư thế nghỉ), `HAIR_GRAVITY` (độ trĩu), `HAIR_RADIUS` (bán kính lọn
tóc khi va chạm). Mô phỏng chạy ở bước cố định 1/60 giây nên kết quả không đổi
theo tốc độ khung hình.

## Ghi chú về trình xem

`web/app.js` là **ES module**; `web/index.html` khai importmap trỏ `three` sang
CDN. Hàm nào được gọi từ thuộc tính `onclick` hay `oninput` trong HTML đều phải
gán vào `window` ở cuối `app.js` — module có phạm vi riêng, không đổ ra toàn cục.

Hai cái bẫy khi chuyển từ r128 lên r180, cả hai đều không báo lỗi mà chỉ làm
hình sai:

* **Đơn vị ánh sáng.** Từ r155, hệ số PI nhân ngầm vào cường độ đã bị bỏ, nên
  giữ nguyên con số cũ thì cảnh tối đi khoảng 3,14 lần. Đèn spot còn đổi cả
  công thức suy giảm theo khoảng cách nên cần hệ số riêng.
* **Vật liệu kim loại.** Sàn sân khấu đặt `metalness: 0.8` mà cảnh không có
  environment map: r128 vẫn vẽ sáng, r180 tính đúng nên ra gần như đen. Đã hạ
  metalness thay vì thêm environment map, để không đổi cách nhân vật bắt sáng.

## Thêm một trạng thái từ mocap

Cả 4 trạng thái mocap chỉ là vài dòng, nhờ khuôn trong `scripts/retarget.py`:

```python
CLIP = '17_NhayMua_Mocap'
bake = retarget.mocap_state(CLIP, 'dataset-1_dance-short_normal_001.bvh',
                            offset=300, loop_lo=40, loop_hi=160, blend=8)
```

`offset` bỏ qua đoạn đầu bản ghi (diễn viên thường đứng chờ vài giây).
`loop_lo`/`loop_hi` là khoảng frame để dò điểm lặp khép nhất. `blend` hoà mấy
frame cuối về tư thế frame đầu — cần cho những đoạn không tuần hoàn như vũ đạo
hay cử chỉ dẫn chuyện, vì cắt ở đâu cũng còn một cú giật.

Thứ tự bên trong quan trọng: **làm khép vòng trước, khoá bàn chân sau**. Làm
ngược lại thì phép hoà đuôi clip nhấc chân khỏi sàn ở đúng mấy frame vừa chỉnh.

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
