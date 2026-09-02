# Phong Cách A: Nữ Ca Sĩ Realistic Pop Singer 3D (Ready Player Me Standard)

Thư mục này chứa mô hình **Nữ Ca Sĩ Phong Cách Người Thật / Bán Thực Tế** với đầy đủ khung xương Humanoid, 7 ARKit Morph Targets (Visemes), trang phục biểu diễn và hoạt ảnh đứng hát.

---

## 1. Cấu Trúc Thư Mục

```
phuong_an_A_realistic_female_singer/
├── model/
│   └── female_singer_realistic.glb       # File 3D GLB chuẩn (503 KB)
├── web_viewer/
│   ├── index.html                        # Web Studio 3D riêng biệt
│   ├── style.css                         # Giao diện điều khiển Studio
│   └── app.js                            # Three.js + Studio Lip-Sync + Online ReadyPlayerMe Loader
├── scripts/
│   └── build_realistic_female_singer.py  # Script dựng hình và đóng gói GLB
└── README.md
```

---

## 2. Thông Số Kỹ Thuật

| Thông số | Giá trị |
| :--- | :--- |
| **Định dạng file** | GLTF 2.0 Binary (`.glb`) |
| **Kích thước file** | **503 KB** |
| **Số lượng đỉnh (Vertices)** | ~3,300 vertices |
| **Khung xương (Rigging)** | 19 Khớp xương Humanoid chuẩn (Mixamo / Mecanim compatible) |
| **Skinning Type** | Linear Blend Skinning (LBS) 4-weights uốn dẻo mềm mại |
| **Khẩu hình (Morph Targets)** | 7 Visemes: `viseme_aa` (A), `viseme_O` (O), `viseme_E` (E), `viseme_U` (U), `jawOpen`, `mouthSmile`, `eyesClosed` |
| **Hoạt ảnh (Animation)** | `Realistic_Female_Live_Singing` (30 FPS, đung đưa cơ thể, nâng mic lên miệng khi lên nốt cao, nhắm mắt phiêu) |

---

## 3. Tính Năng Nổi Bật
* Hỗ trợ nạp trực tiếp avatar từ **Ready Player Me**: Bạn có thể tạo avatar từ ảnh của mình trên *readyplayer.me*, sau đó dán ID vào ô nhập liệu trên Web Viewer để xem nhân vật hát ngay lập tức!
