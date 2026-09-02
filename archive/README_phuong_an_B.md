# Phong Cách B: Nữ Ca Sĩ Anime 3D Idol (J-Pop / VTuber Style)

Thư mục này chứa mô hình **Nữ Ca Sĩ Phong Cách Anime 3D Thần Tượng (Idol)** với tỷ lệ cơ thể anime dễ thương, tóc Twin-tails bồng bềnh, váy xếp ly xòe, micro tai nghe và hoạt ảnh vũ đạo J-Pop 130 BPM.

---

## 1. Cấu Trúc Thư Mục

```
phuong_an_B_anime_idol_female_singer/
├── model/
│   └── female_singer_anime_idol.glb       # File 3D GLB chuẩn (608 KB)
├── web_viewer/
│   ├── index.html                         # Web Studio Sân Khấu Anime riêng biệt
│   ├── style.css                          # Giao diện điều khiển Studio Pastel
│   └── app.js                             # Three.js + Lip-Sync Studio & Web Audio J-Pop Beat
├── scripts/
│   └── build_anime_idol_female_singer.py  # Script dựng hình và đóng gói GLB
└── README.md
```

---

## 2. Thông Số Kỹ Thuật

| Thông số | Giá trị |
| :--- | :--- |
| **Định dạng file** | GLTF 2.0 Binary (`.glb`) |
| **Kích thước file** | **608 KB** |
| **Số lượng đỉnh (Vertices)** | ~3,900 vertices |
| **Khung xương (Rigging)** | 19 Khớp xương Humanoid chuẩn |
| **Tóc & Phụ kiện** | Tóc hai chùm Twin-Tails uốn lượn, nơ cổ áo, váy xếp ly xòe |
| **Khẩu hình (Morph Targets)** | 8 Anime Visemes: `viseme_aa`, `viseme_O`, `viseme_E`, `viseme_U`, `jawOpen`, `mouthSmile`, `eyesClosed`, và `eyeWinkLeft` (Nháy mắt) |
| **Hoạt ảnh (Animation)** | `Anime_Idol_JPop_Live_Performance` (30 FPS, nhún nhảy 130 BPM, tạo dáng idol, nháy mắt duyên dáng) |
