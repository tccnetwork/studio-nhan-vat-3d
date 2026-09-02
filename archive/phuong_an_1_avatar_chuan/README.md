# Phương Án 1: Thiết Kế Humanoid Singer Avatar 3D (Rigging Chuẩn & Khẩu Hình Lip-Sync)

Thư mục này chứa mô hình nhân vật **Humanoid Singer 3D Avatar** được xây dựng theo chuẩn công nghiệp (tương thích Mixamo / ARKit / Oculus Visemes), xuất ra định dạng `.glb` và sẵn sàng chuyển đổi `.fbx`.

---

## 1. Cấu Trúc Thư Mục

```
phuong_an_1_avatar_chuan/
├── model/
│   └── singer_humanoid_avatar.glb       # File 3D GLB chuẩn (Mesh + Rig 19 Xương + 7 Visemes + Animation Hát)
├── web_viewer/
│   ├── index.html                       # Trình xem 3D chuyên sâu với Studio Lip-Sync
│   ├── style.css                        # Giao diện điều khiển Studio
│   └── app.js                           # Three.js engine + Lip-Sync controller & Skeleton visualizer
├── scripts/
│   └── build_avatar.py                  # Script dựng hình, tính toán Skinning weights & đóng gói GLB
└── README.md
```

---

## 2. Thông Số Kỹ Thuật Mô Hình

| Thông số | Giá trị |
| :--- | :--- |
| **Định dạng file** | GLTF 2.0 Binary (`.glb`) / Hỗ trợ xuất `.fbx` |
| **Kích thước file** | **379 KB** |
| **Số lượng đỉnh (Vertices)** | ~2,500 vertices (Tối ưu cho cả Web và Game Engine) |
| **Số lượng đa giác (Triangles)** | ~4,800 triangles |
| **Bộ xương (Skeleton Rig)** | 19 Khớp xương Humanoid chuẩn (Hips, Spine, Chest, Neck, Head, Shoulders, Arms, Forearms, Hands, Legs, Feet) |
| **Skinning Type** | Linear Blend Skinning (LBS) với 4 trọng số (Influences) trên mỗi đỉnh |
| **Khẩu hình (Morph Targets / Visemes)** | 7 Visemes: `viseme_aa` (A), `viseme_O` (O), `viseme_E` (E), `viseme_U` (U), `jawOpen` (Hàm mở), `mouthSmile` (Mỉm cười), `eyesClosed` (Nhắm mắt) |
| **Hoạt ảnh (Animation)** | `Humanoid_Live_Singing_Performance` (30 FPS, đung đưa cơ thể, đưa micro lên miệng hát cao trào, chuyển động khẩu hình đồng bộ) |

---

## 3. Cách Xem Và Sử Dụng

### Cách 1: Mở Web 3D Viewer (Khuyên dùng)
1. Khởi chạy HTTP server:
   ```bash
   python3 -m http.server 8080
   ```
2. Truy cập: `http://localhost:8080/phuong_an_1_avatar_chuan/web_viewer/`
3. Tại đây bạn có thể:
   * Bật/Tắt xem bộ khung xương chuyển động (`SkeletonHelper`).
   * Điều chỉnh thanh trượt thử từng khẩu hình miệng A, E, I, O, U hoặc bật chế độ tự động hát theo nhạc.
   * Bật nhạc hát demo và quan sát cử động môi nhép theo nhịp.

### Cách 2: Tái tạo lại mô hình bằng Python
```bash
python3 scripts/build_avatar.py
```

### Cách 3: Nhập (Import) vào Unity / Unreal Engine / Blender
* **Unity**: Kéo file `.glb` vào dự án -> Thiết lập Animation Type là `Humanoid`. Hệ thống Mecanim của Unity sẽ tự động nhận diện toàn bộ xương và blendshapes.
* **Unreal Engine**: Import vào Content Browser -> Chọn gán vào Humanoid Skeleton có sẵn.
* **Blender**: `File -> Import -> glTF 2.0 (.glb)`. Bạn sẽ thấy toàn bộ Armature, Shape Keys (Morph Targets) và Action Animation trong Dope Sheet.

### Cách 4: Chuyển đổi sang định dạng `.fbx`
Nếu cần định dạng `.fbx`, bạn có thể mở Blender và xuất:
```bash
# Lệnh Blender CLI tự động convert GLB sang FBX:
blender --background --python-expr "
import bpy
bpy.ops.import_scene.gltf(filepath='model/singer_humanoid_avatar.glb')
bpy.ops.export_scene.fbx(filepath='model/singer_humanoid_avatar.fbx', add_leaf_bones=False)
"
```
