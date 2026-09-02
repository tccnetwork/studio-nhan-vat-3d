# PHƯƠNG ÁN NÂNG CAO: NỮ CA SĨ BIỂU DIỄN VŨ ĐẠO & HÁT LIVE CHUYÊN NGHIỆP (PRO CONCERT STAGE)

Thư mục này được tạo riêng để phát triển chuyên sâu các **động tác vũ đạo sân khấu, cử chỉ biểu cảm ca sĩ thực tế và hệ thống nhép môi theo sóng âm** cho nhân vật nữ.

---

## 1. CẤU TRÚC THƯ MỤC

```
/Volumes/DATA/ctg_ai/3d/phuong_an_nang_cao_nu_ca_si_pro_stage/
├── model/
│   ├── female_singer_pro_stage.blend    # File Blender gốc Ca sĩ Realistic (Bake 240 Frames Vũ đạo)
│   ├── female_singer_pro_stage.fbx      # File FBX chuẩn nhúng Animation & Shape Keys
│   ├── female_singer_pro_stage.glb      # File GLB chuẩn nhúng Animation & PBR Textures
│   │
│   ├── female_singer_anime_pro.blend    # File Blender gốc Ca sĩ Anime Idol (Bake 240 Frames Vũ đạo J-Pop 130 BPM)
│   ├── female_singer_anime_pro.fbx      # File FBX chuẩn nhúng Animation & 58 Shape Keys
│   └── female_singer_anime_pro.glb      # File GLB chuẩn nhúng Animation & PBR Textures
│
├── web_studio/                          # Sân Khấu Hòa Nhạc 3D Pro (Live Concert Studio)
│   ├── index.html                       # Giao diện sân khấu đèn Spotlight, chuyển đổi vũ đạo
│   ├── style.css                        # Giao diện HUD sân khấu hiện đại
│   └── app.js                           # Three.js + Web Audio FFT Real-Time LipSync
│
├── scripts/
│   └── generate_pro_singer_choreography.py # Script Blender Python tạo chuyển động vũ đạo
│
└── README.md                            # Hướng dẫn chi tiết
```

---

## 2. CÁC ĐỘNG TÁC BIỂU DIỄN ĐÃ ĐƯỢC THIẾT KẾ (CHOREOGRAPHY)

1. **`01_Live_Pop_Vocal_Performance` (Hát Live Phiêu Lãng - 240 Frames / 8s Loop)**:
   * **Tay phải**: Giữ micro không dây sát miệng khi hát nốt trầm/trung, nâng cao và hơi nghiêng khi lên nốt cao trào.
   * **Tay trái**: Thực hiện các cử chỉ diễn cảm kể chuyện (vươn bàn tay về phía khán giả, đặt tay lên ngực khi hát câu từ xúc động).
   * **Hông & Thân mình**: Chuyển trọng tâm chân nhịp nhàng, ưỡn ngực lấy hơi và ngửa nhẹ đầu khi hát nốt cao.
2. **`02_Idol_Dance_130_BPM` (Vũ Đạo Idol Sôi Động - 128/130 BPM)**:
   * Nhún nhảy dứt khoát theo từng nhịp bass (Pop step bounce).
   * Tóc hai chùm Twin-Tails uốn lượn theo quán tính chuyển động của cơ thể.
   * Khuôn mặt liên tục biến đổi giữa các nguyên âm A-I-U-E-O kết hợp nụ cười Joy và nháy mắt (Wink 😉).
3. **`03_High_Note_Climax_Diva` (Điệp Khúc Bùng Nổ)**:
   * Hai tay mở rộng đón ánh đèn sân khấu, miệng mở rộng hết cỡ để phô diễn giọng hát nội lực.

---

## 3. CÁCH MỞ VÀ TRẢI NGHIỆM

### A. Xem trên trình duyệt Web (Sân Khấu Hòa Nhạc 3D Pro):
1. Chạy lệnh trong Terminal:
   ```bash
   python3 -m http.server 8080 --directory /Volumes/DATA/ctg_ai/3d
   ```
2. Truy cập: `http://localhost:8080/phuong_an_nang_cao_nu_ca_si_pro_stage/web_studio/`
   * Bấm các nút chọn bài hát: `Bài 1 (Pop Vocal)` hoặc `Bài 2 (J-Pop Dance)`.
   * Bấm đổi các vũ đạo: `🎙️ Hát Live Phiêu Lãng`, `⚡ Vũ Đạo Idol 130 BPM`, `🔥 Nốt Cao Trào`.
   * Bấm đổi chế độ sân khấu: `Song Ca (Cả 2)`, `Solo Realistic`, `Solo Anime Idol`.

### B. Mở và chỉnh sửa trực tiếp trong Blender:
* Nhấp đúp chuột vào file:
  * [`female_singer_pro_stage.blend`](file:///Volumes/DATA/ctg_ai/3d/phuong_an_nang_cao_nu_ca_si_pro_stage/model/female_singer_pro_stage.blend) (Mẫu Realistic)
  * [`female_singer_anime_pro.blend`](file:///Volumes/DATA/ctg_ai/3d/phuong_an_nang_cao_nu_ca_si_pro_stage/model/female_singer_anime_pro.blend) (Mẫu Anime Idol)
* Nhấn phím `Spacebar` để xem toàn bộ 240 Frames vũ đạo và chỉnh sửa Keyframe trong **Dope Sheet / Action Editor**.
