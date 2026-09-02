# HƯỚNG DẪN MỞ VÀ CHỈNH SỬA FILE 3D TRÊN BLENDER (.FBX / .GLB / .BLEND)

Tất cả các mô hình đã được xuất đầy đủ sang **3 định dạng chuẩn công nghiệp**: **`.glb`**, **`.fbx`** và **`.blend`** kèm theo **khung xương (Armature)**, **hoạt ảnh ca hát (Actions / Keyframes)** và **hệ thống khẩu hình biểu cảm (Shape Keys / Morph Targets)**.

---

## 1. DANH SÁCH FILE XUẤT CHO BLENDER

### 🎭 PHƯƠNG ÁN A: NỮ REALISTIC POP SINGER
Thư mục: `/Volumes/DATA/ctg_ai/3d/phuong_an_A_realistic_female_singer/model/`
1. **[`female_singer_realistic.blend`](file:///Volumes/DATA/ctg_ai/3d/phuong_an_A_realistic_female_singer/model/female_singer_realistic.blend)** *(4.3 MB)*: File dự án Blender gốc. Bạn chỉ cần **nhấp đúp chuột để mở trực tiếp trên Blender**.
2. **[`female_singer_realistic.fbx`](file:///Volumes/DATA/ctg_ai/3d/phuong_an_A_realistic_female_singer/model/female_singer_realistic.fbx)** *(1.7 MB)*: Định dạng Autodesk FBX chuẩn, nhúng sẵn Animation vũ đạo ca sĩ `Realistic_Singing_Performance` và Shape Keys.
3. **[`female_singer_realistic.glb`](file:///Volumes/DATA/ctg_ai/3d/phuong_an_A_realistic_female_singer/model/female_singer_realistic.glb)** *(1.7 MB)*: Định dạng GLTF 2.0 PBR, nhúng Texture và Animation.

---

### 🌸 PHƯƠNG ÁN B: NỮ ANIME 3D IDOL SINGER
Thư mục: `/Volumes/DATA/ctg_ai/3d/phuong_an_B_anime_idol_female_singer/model/`
1. **[`female_singer_anime_idol.blend`](file:///Volumes/DATA/ctg_ai/3d/phuong_an_B_anime_idol_female_singer/model/female_singer_anime_idol.blend)** *(10.0 MB)*: File dự án Blender gốc. Bạn chỉ cần **nhấp đúp chuột để mở trực tiếp trên Blender**.
2. **[`female_singer_anime_idol.fbx`](file:///Volumes/DATA/ctg_ai/3d/phuong_an_B_anime_idol_female_singer/model/female_singer_anime_idol.fbx)** *(3.2 MB)*: Định dạng FBX chuẩn, nhúng sẵn vũ đạo J-Pop 130 BPM `Anime_Idol_JPop_Performance` và 58 Shape Keys khẩu hình (A, I, U, E, O, Joy, Wink 😉).
3. **[`female_singer_anime_idol.glb`](file:///Volumes/DATA/ctg_ai/3d/phuong_an_B_anime_idol_female_singer/model/female_singer_anime_idol.glb)** *(5.2 MB)*: Định dạng GLTF 2.0 nhúng đầy đủ Material, Texture và Animation.

---

## 2. HƯỚNG DẪN CHỈNH SỬA TRÊN BLENDER

1. **Cách mở nhanh nhất**: Nhấp đúp chuột vào file `.blend` (hoặc mở Blender $\rightarrow$ `File > Open...` chọn file `.blend`).
2. **Chỉnh sửa chuyển động biểu diễn**:
   * Nhấn phím `Spacebar` trên bàn phím để xem nhân vật chuyển động nhép miệng và nhún nhảy theo bài hát.
   * Chuyển sang cửa sổ **Dope Sheet** hoặc **Action Editor** để thêm / bớt keyframe chuyển động theo ý muốn.
3. **Chỉnh sửa khẩu hình & biểu cảm (Lip-Sync / Shape Keys)**:
   * Chọn Mesh khuôn mặt (`Face` hoặc `Wolf3D_Head`).
   * Vào tab **Object Data Properties** (biểu tượng tam giác xanh ▽ ở cột bên phải) $\rightarrow$ mục **Shape Keys**.
   * Bạn có thể kéo giá trị `Value` (0.0 đến 1.0) của các Shape Key `Fcl_MTH_A`, `mouthOpen`, `Joy`, `Wink` để chỉnh sửa tạo hình hoặc nắn lại lưới Vertex bằng chế độ **Sculpt Mode**!
