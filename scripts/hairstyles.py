"""Sinh bộ kiểu tóc từ mái tóc dài gốc của VRoid.

Tách riêng khỏi build_character.py để thử nghiệm hình dạng tóc mà không phải
bake lại toàn bộ 14 trạng thái hoạt ảnh — xem tools/preview_hairstyles.py.
"""
import bpy
import mathutils


def build_hairstyles(char_arm):
    """Tạo 3 kiểu tóc cắt ngắn từ object 'Hair'. Trả về danh sách object mới."""
    # =========================================================================
    # CREATE MULTI-HAIRSTYLE COLLECTION: Long Silky, Shoulder Layered & Short Bob
    # =========================================================================
    print(">>> Creating Multi-Hairstyle Collection (Long Silky, Medium Shoulder & Short Bob)...")
    # Clean up any leftover hair duplicates from previous loads
    for obj in list(bpy.data.objects):
        if obj.type == 'MESH' and ('hair.' in obj.name.lower() or 'bob' in obj.name.lower() or 'shoulder' in obj.name.lower() or 'twintail' in obj.name.lower()):
            print(f"  Purging leftover duplicate hair mesh: {obj.name}")
            bpy.data.objects.remove(obj, do_unlink=True)

    orig_hair = bpy.data.objects.get('Hair')
    if orig_hair:
        # ------------------------------------------------------------------
        # Cắt ngắn tóc dài gốc thành các kiểu khác.
        #
        # Bản trước dùng if/else cứng để chia tóc thành "vạt bên" và "vạt sau",
        # rồi GHI ĐÈ toạ độ Y bằng một công thức chỉ phụ thuộc X. Ba hệ quả:
        #   1. Hai vùng nhận hai chiều dài khác nhau (1,30 so với 1,34) nên chỗ
        #      giáp ranh bị gãy thành một bậc thang thấy rõ.
        #   2. Y bị ép về dải 0,010-0,048 trong khi bán kính sọ đo được là 0,115
        #      tại z=1,42 — tóc chui vào trong đầu, đỉnh sọ lòi ra ngoài.
        #   3. Độ dày xếp lớp giữa các lọn bị nhân với 0,40 nên tóc bẹt như tấm ván.
        # Bản này giữ nguyên hình dạng lọn tóc, chỉ rút ngắn theo trục Z, và
        # chuyển mọi ranh giới cứng thành hàm chuyển mềm.
        # ------------------------------------------------------------------
        Z_HANG = 1.48        # đường chân tóc: phía trên giữ nguyên tuyệt đối
        Z_TIP_ORIG = 1.028   # chóp đuôi tóc gốc
        AXIS_Y = 0.015       # trục dọc của đầu trong mặt phẳng XY

        # Bán kính vỏ sọ đo trực tiếp từ mesh Face, dùng để chặn tóc lún vào đầu
        HEAD_PROFILE = [(1.24, 0.062), (1.30, 0.070), (1.36, 0.086),
                        (1.42, 0.115), (1.48, 0.103), (1.54, 0.091), (1.62, 0.060)]

        # Biên dạng bán kính của chính mái tóc gốc, đo theo từng dải cao 4 cm.
        # Đây là hình dạng mà trọng lực tạo ra: xoè đều ~0,19 m trên mỗi mét
        # rơi từ z=1,48 xuống 1,12, rồi tụm lại ở 6 cm cuối khi các lọn chụm
        # vào nhau. Cắt ngắn tóc thì phải cắt luôn phần xoè mà nó không còn
        # đủ chiều dài để tích luỹ — chứ không phải nhân co toàn bộ bán kính,
        # vì nhân co kéo cả phần ôm sọ vào theo và cho ra một cái vòm cứng.
        HAIR_PROFILE = [(1.480, 0.109), (1.420, 0.120), (1.360, 0.132),
                        (1.300, 0.142), (1.240, 0.157), (1.180, 0.172),
                        (1.120, 0.179), (1.060, 0.159), (1.028, 0.148)]

        def hair_flare(z):
            """Bán kính trung bình của tóc gốc tại cao độ z."""
            if z >= HAIR_PROFILE[0][0]:
                return HAIR_PROFILE[0][1]
            if z <= HAIR_PROFILE[-1][0]:
                return HAIR_PROFILE[-1][1]
            for (z0, r0), (z1, r1) in zip(HAIR_PROFILE, HAIR_PROFILE[1:]):
                if z1 <= z <= z0:
                    return r0 + (r1 - r0) * (z0 - z) / (z0 - z1)
            return HAIR_PROFILE[-1][1]

        FLARE_AT_HANG = HAIR_PROFILE[0][1]

        def head_radius(z):
            if z <= HEAD_PROFILE[0][0]:
                return HEAD_PROFILE[0][1]
            if z >= HEAD_PROFILE[-1][0]:
                return HEAD_PROFILE[-1][1]
            for (z0, r0), (z1, r1) in zip(HEAD_PROFILE, HEAD_PROFILE[1:]):
                if z0 <= z <= z1:
                    return r0 + (r1 - r0) * (z - z0) / (z1 - z0)
            return HEAD_PROFILE[-1][1]

        def smoothstep(edge0, edge1, x):
            """Chuyển mượt 0 -> 1, đạo hàm bằng 0 ở hai đầu nên không để lại gờ."""
            t = (x - edge0) / (edge1 - edge0)
            t = max(0.0, min(1.0, t))
            return t * t * (3.0 - 2.0 * t)

        def create_tapered_hairstyle(z_back, z_side, name, u_curve_depth=0.038,
                                     hang=0.75):
            """
            z_back / z_side : cao độ kết thúc của vạt tóc sau lưng và vạt hai bên
            u_curve_depth   : độ cong hình chữ U của đường cắt sau lưng
            hang            : 1,0 giữ nguyên tỉ lệ xoè; càng nhỏ tóc càng rơi
                              thẳng. Tóc ngắn không với tới vai nên không có gì
                              đẩy nó ra ngoài — nó phải rơi thẳng hơn tóc dài.
            """
            new_hair = orig_hair.copy()
            new_hair.data = orig_hair.data.copy()
            new_hair.name = name
            bpy.context.collection.objects.link(new_hair)

            me = new_hair.data
            orig_span = Z_HANG - Z_TIP_ORIG

            for v in me.vertices:
                if v.co.z >= Z_HANG:
                    continue

                z_orig = v.co.z
                t = (Z_HANG - z_orig) / orig_span
                t = max(0.0, min(1.0, t))

                # Trọng số "thuộc vạt bên": mềm theo cả Y (ra trước) lẫn X (ra ngoài)
                w_front = smoothstep(0.030, -0.060, v.co.y)
                w_x = smoothstep(0.030, 0.095, abs(v.co.x))
                w_side = w_front * w_x

                # Đường cắt hình chữ U ở sau lưng: giữa lưng dài nhất, hai bên vuốt lên
                x_norm = min(1.0, abs(v.co.x) / 0.14)
                z_target = ((z_back + u_curve_depth * smoothstep(0.0, 1.0, x_norm))
                            * (1.0 - w_side) + z_side * w_side)

                new_span = Z_HANG - z_target
                z_new = Z_HANG - t * new_span

                # Mái trước trán: bảo toàn, nhưng chuyển mềm sang phần bị cắt
                # thay vì cắt đứt ở đúng z = 1,35 như bản cũ.
                m_fringe = (smoothstep(-0.045, -0.080, v.co.y)
                            * smoothstep(1.320, 1.390, v.co.z))
                v.co.z = z_new * (1.0 - m_fringe) + v.co.z * m_fringe

                # Trọng lực: bỏ đi đúng phần xoè mà sợi tóc này không còn đủ
                # chiều dài để tích luỹ. Độ lệch riêng của từng đỉnh so với
                # biên dạng trung bình được giữ nguyên, nên các lớp tóc vẫn
                # dày mỏng khác nhau như cũ.
                dx, dy = v.co.x, v.co.y - AXIS_Y
                r = (dx * dx + dy * dy) ** 0.5
                if r > 1e-5:
                    k = new_span / orig_span
                    excursion = hair_flare(z_orig) - FLARE_AT_HANG
                    r_new = r - excursion * (1.0 - k * hang)
                    # Không bao giờ mảnh hơn chính cái đầu nó bọc
                    r_floor = min(r, head_radius(v.co.z) + 0.014)
                    r_new = max(r_new, r_floor)
                    scale = r_new / r
                    v.co.x = dx * scale
                    v.co.y = AXIS_Y + dy * scale

            me.update()

            # Pháp tuyến tách tuỳ biến của VRoid nay đã lệch vì đỉnh đã dịch chuyển.
            # Dựng lại theo kiểu tóc anime: hướng ra ngoài từ tâm hộp sọ, pha thêm
            # pháp tuyến hình học để không mất hoàn toàn khối của từng lọn.
            centre = mathutils.Vector((0.0, AXIS_Y, 1.40))
            radial = []
            for v in me.vertices:
                d = (v.co - centre)
                d.z *= 0.62                      # dẹt theo chiều dọc cho giống vỏ sọ
                if d.length < 1e-5:
                    d = mathutils.Vector((0.0, 0.0, 1.0))
                d.normalize()
                n = (d * 0.72 + v.normal * 0.28)
                if n.length < 1e-5:
                    n = d
                radial.append(n.normalized())
            try:
                me.normals_split_custom_set_from_vertices(radial)
            except Exception as exc:
                print(f"  Cảnh báo: không đặt được pháp tuyến tuỳ biến cho {name}: {exc}")

            mod = new_hair.modifiers.get('Armature')
            if not mod:
                mod = new_hair.modifiers.new(name='Armature', type='ARMATURE')
            mod.object = char_arm
            return new_hair

        # Kiểu 4 trên giao diện — Bob ngắn ôm gáy
        create_tapered_hairstyle(1.300, 1.335, 'Hair_ShortBob',
                                 u_curve_depth=0.026, hang=0.50)

        # Kiểu 3 — Ngang vai
        create_tapered_hairstyle(1.198, 1.240, 'Hair_MediumShoulder',
                                 u_curve_depth=0.036, hang=0.70)

        # Kiểu 2 — Dài vừa
        create_tapered_hairstyle(1.140, 1.180, 'Hair_WavyCurled',
                                 u_curve_depth=0.044, hang=0.85)

        print(">>> Multi-Hairstyle Collection Created Successfully with Salon-Grade U-Silhouette & 3D Contour!")

    return [o for o in bpy.data.objects
            if o.type == 'MESH' and o.name.startswith('Hair_')]
