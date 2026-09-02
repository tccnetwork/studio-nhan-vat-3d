# -*- coding: utf-8 -*-
"""Hàm dùng chung cho mọi trạng thái: quaternion, gộp vertex group, và bộ máy
dáng đi sinh học dùng cho hai trạng thái bước đi.

Các hàm rủ tóc đã bị gỡ: tóc nay được mô phỏng lúc chạy trong web/app.js chứ
không bake cứng vào từng clip. Xương tóc từng chiếm 0,864 MB trong 1,33 MB dữ
liệu hoạt ảnh, và mỗi module trạng thái phải lặp lại cùng một đoạn rủ tóc.

Tách khỏi build_character.py để mỗi trạng thái ở scripts/states/ nạp được
riêng, nhờ đó dựng lại một trạng thái không phải bake cả 14 cái.
"""
import bpy
import math
import mathutils


def clean_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)

def merge_vertex_groups(mesh_obj, source_group_name, target_group_name):
    src_vg = mesh_obj.vertex_groups.get(source_group_name)
    tgt_vg = mesh_obj.vertex_groups.get(target_group_name)
    if not src_vg:
        return
    if not tgt_vg:
        tgt_vg = mesh_obj.vertex_groups.new(name=target_group_name)
    for v in mesh_obj.data.vertices:
        w_src = 0.0
        w_tgt = 0.0
        for g in v.groups:
            if g.group == src_vg.index:
                w_src = g.weight
            elif g.group == tgt_vg.index:
                w_tgt = g.weight
        if w_src > 0.0:
            new_weight = min(1.0, w_tgt + w_src)
            tgt_vg.add([v.index], new_weight, 'REPLACE')
            src_vg.remove([v.index])

def create_quaternion(euler_tuple):
    return mathutils.Euler(euler_tuple, 'XYZ').to_quaternion()

# Natural gravity plumb-line drape mapping (falls vertically straight down along body)
BACK_HAIR_DRAPE = {1: -0.005, 2: -0.005, 3: 0.0, 4: 0.0, 5: 0.0, 6: 0.0}
FRONT_SIDE_DRAPE = {1: 0.015, 2: 0.010, 3: 0.0, 4: 0.0}


def get_biomechanical_gait_frame(phi, is_energetic=False):
    # 1. Hips Translation & Pelvis Sway (Trọng tâm dồn chuẩn xác vào chân trụ)
    # Khi phi in [0, pi] (chân Trái làm trụ), hông dịch chuyển sang Trái (+X)
    # Khi phi in [pi, 2pi] (chân Phải làm trụ), hông dịch chuyển sang Phải (-X)
    sway_amp = 0.034 if is_energetic else 0.030
    bounce_amp = 0.020 if is_energetic else 0.016
    
    hip_sway = sway_amp * math.sin(phi)
    # Nhún thấp nhất khi 2 chân tiếp đất (phi=0, pi), cao nhất khi đứng trên 1 chân trụ (phi=pi/2, 3pi/2)
    hip_bounce = -bounce_amp * math.cos(phi * 2.0)
    
    # Xoay hông theo sải chân (Pelvic yaw) và nghiêng xương chậu (Pelvic list/roll)
    pelvis_yaw = -0.075 * math.sin(phi)
    pelvis_roll = -0.040 * math.sin(phi) # Hông bên chân trụ nâng lên, hông bên chân lăng hạ nhẹ

    # 2. Dáng Người Thẳng Đứng, Ngực Vươn Cao (Chuẩn hình vẽ mẫu)
    spine_pitch = 0.045
    chest_pitch = 0.040
    neck_pitch = -0.015
    head_pitch = -0.020 + 0.010 * math.sin(phi * 2.0)
    
    spine_yaw = -pelvis_yaw * 0.65
    spine_roll = -pelvis_roll * 0.60
    chest_yaw = -pelvis_yaw * 0.45

    # 3. Hàm tính động tác chân chuẩn giải phẫu (Heel-Strike -> Flat -> Push-Off -> Swing)
    def calc_leg(leg_phi):
        p = leg_phi % (math.pi * 2.0)
        stride_amp = 0.44 if is_energetic else 0.40
        
        # Thigh Pitch: Đưa về trước (-X) khi tiếp đất, đưa ra sau (+X) khi đạp đẩy
        thigh = -stride_amp * math.cos(p)
        
        # Gối (Knee Flexion):
        if p < math.pi:
            # GIAI ĐOẠN TIẾP ĐẤT & CHÂN TRỤ (Stance Phase):
            # - Tiếp đất (p=0): Gối duỗi gần thẳng (0.05 rad) để gót chạm sàn
            # - Hấp thụ lực (p=pi/4): Gối khuỵu nhẹ (0.16 rad) chịu trọng lượng cơ thể
            # - Chân trụ thẳng (p=pi/2): Chân trụ duỗi thẳng (0.03 rad) nâng toàn bộ cơ thể lên cao
            # - Đạp lùi (p=3pi/4 đến pi): Chân đẩy thẳng ra sau (0.04 rad)
            cushion = math.sin(p * 2.0) ** 2
            knee = 0.04 + 0.14 * cushion * (1.0 if p < math.pi * 0.45 else 0.20)
        else:
            # GIAI ĐOẠN VUNG CHÂN (Swing Phase):
            # Gối gập sâu (lên đến 0.78 rad) để nhấc bàn chân không quẹt sàn!
            sw_p = p - math.pi
            knee = 0.04 + 0.76 * (math.sin(sw_p) ** 1.35)
            
        # Bàn Chân (Foot / Ankle Pitch):
        if p < math.pi * 0.35:
            # Heel-strike (Gót chạm đất, mũi chếch lên +0.36 rad -> lăn phẳng 0.0)
            foot = 0.36 * math.cos((p / (math.pi * 0.35)) * (math.pi / 2.0))
        elif p < math.pi * 0.55:
            # Flat Foot: Bàn chân phẳng hoàn toàn 100% trên mặt sàn khi gánh trọng tâm
            foot = 0.0
        elif p < math.pi:
            # Push-off: Gót chân nhấc cao, mũi chân miết đẩy sàn (-0.55 rad)
            push_p = (p - math.pi * 0.55) / (math.pi * 0.45)
            foot = -0.55 * (math.sin(push_p * (math.pi / 2.0)) ** 1.4)
        else:
            # Vung chân trên không: Thả lỏng rồi chuẩn bị gót tiếp đất
            sw_p = (p - math.pi) / math.pi
            if sw_p < 0.60:
                foot = -0.15 * (1.0 - sw_p / 0.60)
            else:
                foot = 0.36 * (((sw_p - 0.60) / 0.40) ** 1.3)
                
        # Khớp mũi chân (ToeBase): Uốn cong khi gót nhấc đẩy sàn
        if math.pi * 0.65 < p < math.pi:
            toe_p = (p - math.pi * 0.65) / (math.pi * 0.35)
            toe = 0.35 * math.sin(toe_p * math.pi)
        else:
            toe = 0.0
            
        return thigh, knee, foot, toe

    l_thigh, l_knee, l_foot, l_toe = calc_leg(phi)
    r_thigh, r_knee, r_foot, r_toe = calc_leg(phi + math.pi)
    
    # Đánh tay ngược hướng chân tự nhiên
    arm_amp = 0.35 if is_energetic else 0.30
    l_arm = -arm_amp * math.sin(phi)
    r_arm = arm_amp * math.sin(phi)
    
    return {
        'hip_loc': (hip_sway, 0.0, hip_bounce),
        'hip_rot': (0.02, pelvis_yaw, pelvis_roll),
        'spine_rot': (spine_pitch, spine_yaw, spine_roll),
        'chest_rot': (chest_pitch, chest_yaw, 0.0),
        'neck_rot': (neck_pitch, 0.0, 0.0),
        'head_rot': (head_pitch, 0.0, 0.0),
        'l_thigh': l_thigh, 'l_knee': l_knee, 'l_foot': l_foot, 'l_toe': l_toe,
        'r_thigh': r_thigh, 'r_knee': r_knee, 'r_foot': r_foot, 'r_toe': r_toe,
        'l_arm': l_arm, 'r_arm': r_arm
    }
