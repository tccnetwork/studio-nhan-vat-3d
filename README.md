# Studio Nhân Vật 3D

Quy trình dựng nhân vật 3D cho web, chạy hoàn toàn bằng Blender headless và
three.js. Không có bước nào phải mở giao diện Blender: mọi thứ là script, dựng
lại lúc nào cũng ra đúng kết quả cũ.

Trong repo có **bốn nhân vật**, mỗi nhân vật một trình xem riêng:

| nhân vật | nguồn | dựng bằng | trang xem |
|---|---|---|---|
| Cô ca sĩ anime idol | VRoid Studio, 154 xương, 57 blendshape | `scripts/build_character.py` | `web/` |
| Cung thủ Erika | `char6.fbx`, rig Mixamo 87 xương | `scripts/build_char6.py` | `web/char6.html` |
| Hiệp sĩ thập tự | ba file `char4*.fbx`, rig Mixamo 86 xương | `scripts/build_char4.py` | `web/char4.html` |
| Nhân vật nam | nắn từ chính rig của cô ca sĩ | `scripts/build_idol_male.py` | `web/idol_male.html` |

Cộng thêm một trang thứ tư, `web/idol_mimic.html`, cho cô ca sĩ diễn lại **11
động tác của cả hai nhân vật Mixamo** — kèm theo cả đồ nghề: cung, ống tên,
kiếm, khiên — để so hai bên cạnh nhau. Đây là bài toán chuyển động tác giữa hai
bộ xương khác chuẩn hoàn toàn.

Cô ca sĩ là phần lớn nhất: 19 trạng thái hoạt ảnh (5 trong đó retarget từ mocap
thật), 57 blendshape khuôn mặt, khẩu hình bám theo tiếng hát, và một bản nhúng
được vào trang khác. Phần lớn tài liệu bên dưới nói về nhân vật này.

```
source/     Model nguồn — CHỈ ĐỌC. Không script nào được ghi vào đây.
build/      Kết quả dựng (glb / fbx / blend / manifest.json). Dựng lại là có.
web/        core/     lõi dùng chung: nạp model, vật lý tóc, khẩu hình,
                      điều khiển khung hình
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

## Bắt đầu

Cần **Blender 4.5** (đường dẫn mặc định trên macOS là
`/Applications/Blender.app/Contents/MacOS/Blender`) và **Python 3** cho vài
tiện ích trong `tools/`. Không cần cài gói nào thêm: các script chỉ dùng thư
viện có sẵn trong Blender.

**Model nguồn không nằm trong repo.** Thư mục `source/` bị `.gitignore` loại,
vì nó chứa file Mixamo và VRoid không nên phát tán lại. Muốn dựng lại thì phải
xin riêng năm file này rồi bỏ vào `source/`:

```
source/char4.fbx                          hiệp sĩ, rig đầy đủ + take 445 khung
source/char4_1.fbx                        hiệp sĩ, bản rút gọn (không bắt buộc)
source/char4_e.fbx                        hiệp sĩ, bản đồ phân vùng + váy giáp
source/char6.fbx                          cung thủ
source/female_singer_anime_idol_base.glb  cô ca sĩ
```

Chưa có `source/` thì vẫn xem được các trang web nếu thư mục `build/` đã có
sẵn; `build/` cũng bị gitignore vì dựng lại là ra.

```bash
# dựng lần lượt ba nhân vật
BL=/Applications/Blender.app/Contents/MacOS/Blender
$BL --background --factory-startup --python scripts/build_character.py
$BL --background --factory-startup --python scripts/build_char6.py
$BL --background --factory-startup --python scripts/build_char4.py
$BL --background --factory-startup --python scripts/build_idol_mimic.py -- cungthu
$BL --background --factory-startup --python scripts/build_idol_mimic.py -- kiemsi

# nhân vật nam nắn từ rig cô ca sĩ, rồi mượn động tác của hiệp sĩ
$BL --background --factory-startup --python scripts/build_idol_male.py
$BL --background --factory-startup --python scripts/build_idol_mimic.py -- kiemsi nam

# rồi mở trình xem
python3 -m http.server 8080
```

| trang | đường dẫn |
|---|---|
| studio cô ca sĩ | `http://localhost:8080/web/` |
| cung thủ Erika | `http://localhost:8080/web/char6.html` |
| hiệp sĩ thập tự | `http://localhost:8080/web/char4.html` |
| cô ca sĩ bắt chước | `http://localhost:8080/web/idol_mimic.html` |
| — mở thẳng bộ hiệp sĩ | `…/web/idol_mimic.html?nguon=kiemsi` |
| nhân vật nam | `http://localhost:8080/web/idol_male.html` |

## Bốn bài học đắt nhất

Bốn cái bẫy dưới đây đã ăn của tôi nhiều giờ và đều sẽ ăn lại của người sau,
vì không cái nào báo lỗi — chúng chỉ cho ra kết quả sai một cách hợp lý.

**Blender 4.4 trở lên: gán action thôi chưa đủ.** Phải gán cả `action_slot`.
Thiếu slot thì action nằm đó mà không điều khiển gì, và mọi phép đọc tư thế
trả về tư thế nghỉ. Lỗi này từng làm tôi kết luận nhầm rằng "sáu clip đã chết".

```python
ad.action = act
if getattr(act, 'slots', None):
    ad.action_slot = act.slots[0]     # thiếu dòng này là hỏng, không báo gì
```

**Bộ xuất glTF chỉ đọc NLA.** Action đang gán trực tiếp sẽ không được xuất, nên
bước đẩy lên NLA phải chạy SAU CÙNG. Và nó đặt tên hoạt ảnh theo tên *action*
chứ không theo tên track — hai action trùng tên là hỏng. Ngược lại, action còn
sót trong file cũng bị nó vớ lấy: gỡ đối tượng ra khỏi cảnh chưa đủ, phải xoá
cả action, nếu không nó gán bừa lên bộ xương khác.

**`ray_cast` và `closest_point_on_mesh` đo trong hệ toạ độ RIÊNG của đối
tượng.** Lưới gắn vào bộ xương Mixamo có tỉ lệ 0,01, nên truyền thẳng 0,30 m
vào tham số `distance` thì thành 3 mm — không tia nào chạm được gì và phép thử
báo "không có mặt nào khuất". Luôn quy đổi:

```python
unit = 1.0 / (obj.matrix_world.to_3x3() @ Vector((1, 0, 0))).length
obj.ray_cast(origin_local, dir_local, distance=reach_met * unit)
```

**Xoá action không đưa pose channel về tư thế nghỉ.** `pose.bones[].matrix` giữ
nguyên giá trị cuối cùng. Muốn tư thế nghỉ thật thì đọc
`data.bones[].matrix_local`. Cùng họ với nó: xoá sạch khe vật liệu sau khi đã
gán `poly.material_index` thì Blender kẹp mọi chỉ số về 0.

## Ba nhân vật, ba bài toán khác nhau

### Cung thủ Erika — `scripts/build_char6.py`

`char6.fbx` trỏ tới chín texture không tồn tại, nên Blender tô toàn thân bằng
màu hồng tím báo thiếu ảnh. Toàn bộ màu trong bản dựng là tự viết, không phải
khôi phục. Ba mảnh `boots` / `trousers` / `armor` là bản sao cùng bề mặt với
`body` — bản gốc chạy được vì mỗi mảnh lấy một vùng texture khác nhau; cho mỗi
mảnh một màu đặc thì hai lớp tranh nhau độ sâu và ra loang lổ như áo rằn ri.
Đã xoá phần bị phủ kín, so theo **trọng tâm mặt** chứ không theo từng đỉnh.

Bảy "clip" trong file thật ra là một động tác bị cắt cụt ở bảy chỗ. Cắt lại
thành năm clip đúng chỗ, dựng thêm mũi tên bay khi bắn, và nặn hai blendshape
(nhắm mắt, mỉm cười) từ chính hình học vì model trắng trơn không có cái nào.

### Hiệp sĩ thập tự — `scripts/build_char4.py`

Ba file `char4*.fbx` hoá ra là cùng một nhân vật. `char4_1.fbx` không có gì mà
`char4.fbx` chưa có. Sáu trong bảy lưới của `char4_e.fbx` **không phải chi tiết
thêm**: đo từng đỉnh thì `armor` trùng 2082/2084 với lưới thân, `head`
2014/2014, `boots` 1066/1066. Chúng là *bản đồ phân vùng* của chính lưới thân.

Gộp thẳng cả ba file ra 22 571 đỉnh với sáu lớp chồng khít nhau. Dùng chúng làm
bản đồ để gán vật liệu theo vùng thì còn 12 994 đỉnh mà nhiều màu hơn. Chỉ
`trousers` là hình học mới — váy giáp và giáp đùi, `char4.fbx` thiếu hẳn.

18 hoạt ảnh cũng là một: trượt từng clip ngắn dọc clip dài rồi so tư thế, cả 13
clip ngắn đều khớp một đoạn của clip 445 khung với sai lệch dưới 1°. Cắt lại
thành sáu clip, và lòi ra một đoạn *nhảy chém* mà không clip có tên nào chứa.

Chữ thập trên khiên vẽ bằng hình học vì không có texture nào để dán: trục tấm
lấy bằng phân tích trục chính, chiều pháp tuyến hỏi xương cầm, đầu phình là đầu
trên. Bốn món trang bị tháo được từ trang web — mũ trụ, khiên, kiếm, váy giáp.

### Nắn thành nhân vật nam — `scripts/build_idol_male.py`

Cùng bộ xương 154 khớp và 58 khẩu hình của cô ca sĩ, chỉ đổi tỉ lệ người: vai
rộng thêm 22%, hông thu 6%, cao thêm 6,6 cm. Tỉ lệ ngực trên hông đi từ 1,05
lên 1,30 — bản gốc có ngực và hông gần bằng nhau, đó là dấu hiệu dáng nữ rõ
nhất trong số đo.

Sửa lưới thôi là hỏng phép skin: ma trận bind vẫn tính theo hình cũ nên hễ vào
tư thế là lưới trượt khỏi xương. Ở đây mọi phép nắn là MỘT hàm biến đổi điểm,
áp cho cả đỉnh lưới lẫn head/tail của xương trong tư thế nghỉ. Chuyển được sáu
động tác của hiệp sĩ lên anh ta chính là phép kiểm cho việc đó:

```bash
$BL --background --factory-startup --python scripts/build_idol_mimic.py -- kiemsi nam
```

Không warp được theo cao độ, vì rig VRoid ở tư thế chữ T: hai cánh tay nằm
ngang ở z≈1,27 và vươn tới x=±0,70, nên một phép co giãn X phụ thuộc z sẽ kéo
dài cánh tay thay vì nới vai. Mọi phép nắn đều đi kèm mặt nạ trọng số xương —
tổng trọng số của nhóm xương liên quan tại đỉnh đó, một trường liên tục nên
không để lại đường nối.

Hai cái bẫy riêng của khẩu hình. Thứ nhất, `Fcl_MTH_Close` KHÔNG khép được
miệng: đo ra nó chỉ dịch đỉnh miệng tối đa 0,67 mm, vì cái miệng hé lộ lưỡi nằm
sẵn trong hình nền của VRoid. Phải khép bằng hình học, và nén cả vùng chứ không
riêng lưới trong miệng — lưới da có lỗ ở chỗ ấy, thu mỗi phần trong thì hở ra
nhìn thấu vào trong đầu. Thứ hai, khẩu hình glTF lưu TOẠ ĐỘ TUYỆT ĐỐI của toàn
bộ đỉnh, nên mọi phép nắn phải áp cho cả 58 khẩu hình; bỏ qua là hễ chớp mắt,
khuôn mặt lại bật về hình nữ cũ.

### Chuyển động tác giữa hai rig — `scripts/build_idol_mimic.py`

Một script, hai nguồn và hai đích: `-- cungthu` lấy động tác của Erika,
`-- kiemsi` lấy của hiệp sĩ; tham số thứ hai `nu` (mặc định) hay `nam` chọn
nhân vật nhận. Cùng bảng ánh xạ xương, cùng phép ghim trục thứ hai, cùng cách mang đồ
cầm tay sang — khác nhau chỉ ở bảng `SOURCES`: file nguồn, mốc tại chỗ của từng
clip, và món nào cầm ở tay nào.

86–87 xương Mixamo sang 154 xương VRoid. Không chép quaternion được: cùng một số
đo xoay đặt lên hai rig khác chuẩn cho ra hai tư thế khác nhau, vì hướng xương
lúc nghỉ đã khác sẵn. Dùng lại `scripts/retarget.py` của phần mocap: bám hướng
nối hai khớp, không quan tâm tư thế nghỉ.

Bám hướng thôi vẫn chưa đủ cho ba chỗ. `_aim` chỉ ghim *hướng* của đoạn xương,
còn góc xoay *quanh* chính hướng đó vẫn tự do — với xương chậu thì đoạn
Hips→Spine gần như thẳng đứng, nên cái bị bỏ tự do chính là hướng mặt. Bảng
`TWISTS` ghim thêm trục thứ hai: hai háng cho chậu, đường ngón trỏ–ngón út cho
bàn tay, đường nối hai mắt cho đầu.

Đồ cầm tay sang được nhờ một phép đồng dạng đưa cả vùng bàn tay bên nguồn về
vùng bàn tay bên đích. Hệ trục bàn tay dựng từ giải phẫu — dọc lòng bàn tay tới
ngón giữa, ngang lòng bàn tay từ ngón trỏ sang ngón út — chứ không lấy hướng
xương lúc nghỉ, vì hai rig đặt bàn tay lúc nghỉ khác nhau và lấy hướng ấy thì
đồ xoay ngang. Đặt xương VÀ lưới bằng đúng phép ấy thì thế bind không đổi, khỏi
sơn lại trọng số.

Một chi tiết đáng nhớ: khiên của hiệp sĩ vốn treo vào **cẳng tay**, nhưng ở đây
gắn vào **bàn tay**. Góc vặn của cẳng tay không được ghim trong phép chuyển,
còn bàn tay thì có — treo vào cẳng tay là mặt khiên quay lung tung.

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

Cuộn chuột để phóng to thu nhỏ, giới hạn 0,4 – 12 m.

**Tâm xoay luôn nằm ở nhân vật.** Thao tác pan sẵn có của OrbitControls dịch cả
tâm xoay lẫn máy quay — dời nhân vật một chút là tâm xoay rời khỏi nhân vật,
rồi xoay thì nhân vật văng vòng quanh một điểm ở xa. Nên pan của OrbitControls
bị tắt hẳn, và việc dời nhân vật làm bằng `camera.setViewOffset`: dịch khung
ảnh chứ không dịch máy quay. Nhân vật dời được trong khoảng 18% – 82% của khung
(đổi bằng `keepInside`), và xoay thì lúc nào cũng quay quanh chính nó.

Từ lúc người xem đụng vào, việc khung đổi kích thước không canh lại góc nhìn
nữa — canh lại lúc đó là giật view ngay giữa khi họ đang xoay.
`singer.resetView()` đưa về khung mặc định.

Tắt bằng `controls: false` cho một bản nhúng tĩnh, hoặc `zoom: false` /
`pan: false` để chỉ cho xoay.

Góc nhìn mặc định hơi chếch sang bên và hơi cao (`azimuth −0,079`, `polar
1,486`) chứ không nhìn thẳng trực diện — trực diện trông phẳng và cứng hơn.

Căn được khung ưng ý rồi thì `singer.getFraming()` trả về đúng bộ số để dán
ngược vào `createSinger({ framing: ... })`, gồm khoảng cách, hai góc xoay và
mức dịch khung. Trang demo có nút **Chép khung hình này** làm sẵn việc đó.

Bật `showCoords: true` để hiện toạ độ tâm nhìn, vị trí máy quay và khoảng cách
ngay trong khung, kèm dòng đầu cho biết **nhân vật đang ở bao nhiêu phần trăm
khung**. Con số đó đo bằng phép chiếu thật qua ma trận máy quay chứ không suy
ra từ biến nội bộ — suy ra từ biến nội bộ là tự soi lại chính mình, biến lệch
với thứ đang hiển thị thì con số vẫn đẹp mà vẫn sai. Mặc định tắt vì bản nhúng trên trang
thật không nên hiện thông tin gỡ lỗi. Bật tắt lúc chạy bằng
`singer.showCoords(true|false)`, hoặc lấy số bằng `singer.getView()` nếu muốn
tự vẽ chỗ khác.

**Trang studio và bản nhúng dùng chung `web/core/`** — vật lý tóc, bộ phân loại
nguyên âm, phần nạp model và điều khiển khung hình chỉ có một cài đặt duy nhất.
Trang studio từng để pan mặc định của OrbitControls nên dính đúng lỗi trên:
dời nhân vật là tâm xoay rời khỏi nó. Nay cả hai trang dùng `core/framing.js`.
Riêng studio, tâm xoay còn dời theo nút cận cảnh — xoay quanh khuôn mặt là quay
quanh khuôn mặt thật, không quanh giữa người.

## Nhảy theo nhạc tự tải lên

Kéo thả một file nhạc vào trang studio hoặc trang demo nhúng, nhân vật chuyển
sang trạng thái vũ đạo và **chỉnh tốc độ để vòng nhảy trùng nhịp bài hát**.

`web/core/beat.js` dò nhịp bằng spectral flux: mỗi khung tính tổng phần năng
lượng *tăng* so với khung trước — tiếng gõ, tiếng bật dây, phụ âm đầu đều làm
năng lượng bật lên, nên đường flux có đỉnh nhọn ở đúng chỗ có nhịp. Tự tương
quan đường đó cho ra chu kỳ.

Hai chi tiết quan trọng:

* **Sửa lỗi bát độ.** Chu kỳ gấp đôi bao giờ cũng tự tương quan mạnh vì cứ hai
  phách thì trùng một lần, nên đỉnh cao nhất hay rơi vào nửa tempo — 160 phách
  bị đọc thành 80. Nếu chu kỳ bằng một nửa vẫn còn mạnh gần bằng thì chọn cái
  ngắn hơn.
* **Không cần biết clip ứng với mấy phách nhạc.** `matchTimeScale` chọn số phách
  sao cho tốc độ phát lệch ít nhất so với 1,0, nhờ vậy điệu nhảy vừa khớp lưới
  nhịp vừa giữ gần đúng tốc độ gốc.

Kiểm thử bằng chuỗi phổ tổng hợp có tempo biết trước, chạy thẳng trong node:
đúng 10/10 từ 70 đến 175 phách/phút, sai số dưới 0,3%. Đo tích hợp trong trình
duyệt: nhạc 128 phách cho tốc độ ×0,979 tức vòng nhảy đúng 4,00 phách; 96 phách
cho 3,00 phách; 150 phách cho 5,00 phách. Trạng thái không đánh dấu `beat_sync`
trong `scripts/catalog.py` thì không bị tua.

### Lời bài hát không có mốc thời gian

Có lời kèm mốc thời gian (`.lrc`) thì dễ: tới giây nào hát chữ nào. Chỉ có
**lời trần** thì `web/core/lyrics.js` chia việc:

```
thời điểm  <-  lấy từ âm thanh (mỗi âm tiết bật lên là một mốc)
nguyên âm  <-  lấy từ lời (chữ thứ n trong câu)
```

Chính xác hơn hẳn dò formant trên bản phối, vì tiếng Việt một âm tiết một
nguyên âm chính. `syllableVowels` bỏ dấu rồi lấy tối đa hai nguyên âm, nên
"Tiếng" ra I rồi E — miệng chuyển qua cả nguyên âm đôi.

Nhược điểm là **trôi**: bỏ sót hay đếm thừa một âm tiết là lệch cả câu. Mỗi
khoảng lặng dài hơn 0,9 giây được coi là hết câu và con trỏ nhảy về đầu câu kế
— chỗ lấy hơi trở thành mốc chỉnh lại.

Kiểm thử chạy thẳng trong node: **12/12 âm tiết đúng** ở cả năm kịch bản — hát
đều, hát nhanh, có nhiễu 30%, nghỉ ngắn 0,5 giây, nghỉ dài 2 giây.

Bài tự tải lên mặc định coi là **có lời** — người tải biết rõ hơn mọi phép đoán
từ tín hiệu.

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

Quán tính của mỗi đốt tóc phải đo **trong hệ quy chiếu của xương cha**, không
phải hệ thế giới. Khi cha xoay, chóp tóc con bị cuốn đi theo; nếu vẫn so với vị
trí cũ trong hệ thế giới thì đốt con nhận một vận tốc ma, và mỗi đốt trong chuỗi
nhận một vận tốc ma khác nhau — các khớp cong ngược chiều nhau và tóc gấp khúc
như lò xo. Đo được: sửa xong độ cong trung bình từ 17,9° xuống 12,2°, số cặp nếp
gấp lớn hơn 6° từ 12 xuống 8 mỗi khung.

Quaternion của mỗi đốt tóc **phải được chuẩn hoá lại sau mỗi bước**. Mỗi bước
nhân chồng ba quaternion, sai số dấu phẩy động dồn lại làm `|q|` lệch khỏi 1 —
mà ma trận xoay sinh từ quaternion nhân tỉ lệ theo `|q|²`. Đo được: không chuẩn
hoá thì sau 6.000 bước (100 giây) `|q|` lên tới **2,3 tỉ** và tóc phình kín màn
hình; có chuẩn hoá thì đứng yên ở 1,000000.

Bốn hằng số ở đầu `web/core/hair.js`: `HAIR_DRAG` (hãm quán tính), `HAIR_STIFFNESS`
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

Tham số của cả ba kiểu nằm trong bảng `STYLES` ở đầu file. Đo độ gọn của đường
cắt bằng:

```bash
$BL --background --factory-startup --python tools/hair_hem.py
```

Nó chia vành tóc theo góc quanh đầu, lấy cao độ thấp nhất mỗi ô rồi đo chênh
lệch giữa các ô kề nhau — cách nói bằng số cho cái mà mắt gọi là "răng cưa".
Kiểu tóc dài gốc của VRoid dùng làm mốc.

Một kết quả đáng lưu: tính theo tỉ lệ trên chính độ dài, ba kiểu cắt **không hề
lởm chởm hơn tóc gốc** (khoảng 9–10% ở cả bốn). Nhưng cùng một tỉ lệ đọc ra rất
khác nhau: 10% trên 49 cm tóc dài là "tỉa layer", còn 10% trên 21 cm tóc bob thì
vành tóc nằm sát cổ nên thành "răng cưa". Vì thế tóc càng ngắn `evenness` càng
phải nhỏ.

Bốn tham số của mỗi kiểu: `z_back` / `z_side` là cao độ kết thúc của vạt sau và
vạt bên, `u_curve_depth` là độ cong chữ U của đường cắt sau lưng, và `hang`
điều khiển mức xoè còn giữ lại — tóc càng ngắn thì càng phải rơi thẳng, vì nó
không với tới vai nên không có gì đẩy nó ra ngoài.
