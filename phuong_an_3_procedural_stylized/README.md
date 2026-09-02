# Phương Án 3: Thiết Kế Nhân Vật 3D Bằng Code Procedural (Python)

Thư mục này chứa mô hình nhân vật **Stylized Cyber Singer 3D** được tạo hoàn toàn bằng mã nguồn Python toán học (không dùng phần mềm đồ họa bên ngoài), xuất ra file `.glb` chuẩn GLTF 2.0.

---

## 1. Cấu Trúc Thư Mục

```
phuong_an_3_procedural_stylized/
├── model/
│   └── procedural_cyber_singer.glb      # File 3D GLB hoàn chỉnh (Mesh + Material + Animation)
├── web_viewer/
│   ├── index.html                       # Trình xem 3D tương tác trên Web
│   ├── style.css                        # Giao diện HUD Cyberpunk
│   └── app.js                           # Three.js engine + Web Audio Synth Beat
├── scripts/
│   └── generate_procedural_singer.py    # Mã nguồn Python sinh hình học 3D & GLB
└── README.md
```

---

## 2. Thông Số Kỹ Thuật Mô Hình

| Thông số | Giá trị |
| :--- | :--- |
| **Định dạng file** | GLTF 2.0 Binary (`.glb`) |
| **Kích thước file** | **228 KB** (Cực nhẹ, tối ưu 100%) |
| **Số lượng đỉnh (Vertices)** | ~3,500 vertices |
| **Số lượng đa giác (Triangles)** | ~6,100 triangles |
| **Chất liệu (PBR Materials)** | 12 vật liệu PBR (Neon Glow, Metallic Chrome, Matte Cloth, Skin tone) |
| **Hệ thống phân cấp xương (Hierarchy)** | 16 Nodes (World -> Stage -> Root -> Pelvis -> Torso -> Head -> Arms -> Hands -> Mic) |
| **Animation Track** | `Singing_Performance_VocalLoop` (30 FPS, nhịp 120 BPM, chuyển động đung đưa hát + tay vung mic) |

---

## 3. Cách Xem Và Sử Dụng

### Cách 1: Xem trực tiếp trên trình duyệt Web (Khuyên dùng)
1. Mở terminal và chạy lệnh khởi tạo máy chủ web cục bộ:
   ```bash
   python3 -m http.server 8080
   ```
2. Truy cập: `http://localhost:8080/phuong_an_3_procedural_stylized/web_viewer/`

### Cách 2: Tái tạo lại mô hình bằng Python
Nếu muốn tinh chỉnh kích thước, màu sắc hoặc animation:
```bash
python3 scripts/generate_procedural_singer.py
```

### Cách 3: Nhập (Import) vào Game Engine hoặc Phần mềm 3D
* **Unity / Unreal Engine**: Kéo trực tiếp file `model/procedural_cyber_singer.glb` vào thư mục `Assets/` hoặc `Content/`.
* **Blender**: Chọn `File -> Import -> glTF 2.0 (.glb/.gltf)`.
* **Three.js / Babylon.js**: Dùng `GLTFLoader` để tải vào ứng dụng Web.
