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

# Interpolation helper
def lerp(a, b, t):
    return a + (b - a) * t

def get_leg_gait_angles(tau):
    """
    Gait cycle for 1 leg over tau in [0, 1):
    0.00 - 0.10: Double support (Heel strike & load)
    0.10 - 0.50: Single support (Mid stance & push off)
    0.50 - 0.60: Double support (Pre swing / toe off)
    0.60 - 1.00: Swing phase (Knee bends, leg swings forward)
    """
    tau = tau % 1.0
    
    # 1. STANCE PHASE [0.00, 0.60] (60% of cycle ON THE GROUND)
    if tau < 0.60:
        s = tau / 0.60 # s in [0, 1]
        # Thigh moves smoothly from +0.45 rad (front) to -0.42 rad (back)
        thigh = lerp(0.45, -0.42, s)
        
        # Knee: absorbs shock on strike, extends straight in mid-stance, flexes at toe-off
        if s < 0.20:
            # Heel strike & impact absorption: knee flexes to 0.25 rad
            knee = lerp(0.04, 0.28, s / 0.20)
            foot = lerp(-0.35, 0.0, s / 0.20) # Heel down to flat
        elif s < 0.75:
            # Mid-stance: leg is straight, foot flat on floor
            k_s = (s - 0.20) / 0.55
            knee = lerp(0.28, 0.04, k_s)
            foot = 0.0 # Flat foot
        else:
            # Pre-swing / Toe-off: heel lifts off ground, toe on ground
            t_s = (s - 0.75) / 0.25
            knee = lerp(0.04, 0.35, t_s)
            foot = lerp(0.0, 0.45, t_s) # Toe roll
            
    # 2. SWING PHASE [0.60, 1.00] (40% of cycle IN THE AIR)
    else:
        s = (tau - 0.60) / 0.40 # s in [0, 1]
        # Thigh swings from -0.42 rad (back) back to +0.45 rad (front)
        # Sinusoidal ease
        ease_s = 0.5 - 0.5 * math.cos(s * math.pi)
        thigh = lerp(-0.42, 0.45, ease_s)
        
        # Knee bends deeply to 1.20 rad (70 degrees) to lift foot above ground, then extends for strike
        if s < 0.50:
            knee = lerp(0.35, 1.25, s / 0.50)
            foot = lerp(0.45, -0.15, s / 0.50) # Ankle dorsiflex
        else:
            knee = lerp(1.25, 0.04, (s - 0.50) / 0.50)
            foot = lerp(-0.15, -0.35, (s - 0.50) / 0.50) # Prep heel strike
            
    return thigh, knee, foot

def build_all_states_strict_grounded_walk():
    print(">>> Building All 5 Animation States with Biomechanically Grounded Walk (2 chân không bao giờ rời đất cùng lúc)...")
    clean_scene()
    
    input_glb = '/Volumes/DATA/ctg_ai/3d/phuong_an_B_anime_idol_female_singer/model/female_singer_anime_idol.glb'
    out_b_dir = '/Volumes/DATA/ctg_ai/3d/phuong_an_B_anime_idol_female_singer/model'
    stage_dir = '/Volumes/DATA/ctg_ai/3d/phuong_an_nang_cao_nu_ca_si_pro_stage/model'
    
    bpy.ops.import_scene.gltf(filepath=input_glb)
    char_arm = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
    char_arm.name = 'Character_Armature'
    
    # BIND CLOTHING VERTEX WEIGHTS
    body_obj = None
    for obj in bpy.data.objects:
        if obj.type == 'MESH' and 'body' in obj.name.lower():
            body_obj = obj
            break
            
    if body_obj:
        for vg_name in ['J_Aim_L_TopsUpperArm', 'J_Sec_L_TopsUpperArmInside', 'J_Sec_L_TopsUpperArmOutside', 'J_Roll_L_UpperArm']:
            merge_vertex_groups(body_obj, vg_name, 'J_Bip_L_UpperArm')
        for vg_name in ['J_Aim_R_TopsUpperArm', 'J_Sec_R_TopsUpperArmInside', 'J_Sec_R_TopsUpperArmOutside', 'J_Roll_R_UpperArm']:
            merge_vertex_groups(body_obj, vg_name, 'J_Bip_R_UpperArm')
        for vg_name in ['J_Aim_L_UpperLeg', 'J_Roll_L_UpperLeg', 'J_Sec_L_TopsUpperLegFront', 'J_Sec_L_TopsUpperLegBack', 'J_Sec_L_TopsUpperLegSide']:
            merge_vertex_groups(body_obj, vg_name, 'J_Bip_L_UpperLeg')
        for vg_name in ['J_Aim_R_UpperLeg', 'J_Roll_R_UpperLeg', 'J_Sec_R_TopsUpperLegFront', 'J_Sec_R_TopsUpperLegBack', 'J_Sec_R_TopsUpperLegSide']:
            merge_vertex_groups(body_obj, vg_name, 'J_Bip_R_UpperLeg')

    bpy.context.view_layer.objects.active = char_arm
    if not char_arm.animation_data:
        char_arm.animation_data_create()

    pb = char_arm.pose.bones
    for b in pb:
        b.rotation_mode = 'QUATERNION'

    created_actions = []

    # =========================================================================
    # STATE 1: 01_DungNghiem (60 frames)
    # =========================================================================
    print(">>> 1. Creating 01_DungNghiem...")
    act_nghiem = bpy.data.actions.new(name="01_DungNghiem")
    char_arm.animation_data.action = act_nghiem
    created_actions.append(act_nghiem)
    for frame in range(1, 61):
        bpy.context.scene.frame_set(frame)
        t = (frame / 60.0) * math.pi * 2
        breath = math.sin(t) * 0.025
        if pb.get('J_Bip_C_Hips'):
            pb['J_Bip_C_Hips'].location = (0, 0, 0); pb['J_Bip_C_Hips'].keyframe_insert(data_path="location", frame=frame)
            pb['J_Bip_C_Hips'].rotation_quaternion = create_quaternion((0, 0, 0)); pb['J_Bip_C_Hips'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_C_Spine'): pb['J_Bip_C_Spine'].rotation_quaternion = create_quaternion((0.01 + breath * 0.3, 0, 0)); pb['J_Bip_C_Spine'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_C_UpperChest'): pb['J_Bip_C_UpperChest'].rotation_quaternion = create_quaternion((0.02 + breath * 0.7, 0, 0)); pb['J_Bip_C_UpperChest'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_C_Head'): pb['J_Bip_C_Head'].rotation_quaternion = create_quaternion((-0.01, 0, 0)); pb['J_Bip_C_Head'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        l_arm_q = create_quaternion((0.0, 0.0, -1.35))
        r_arm_q = create_quaternion((0.0, 0.0, 1.35))
        if pb.get('J_Bip_L_UpperArm'): pb['J_Bip_L_UpperArm'].rotation_quaternion = l_arm_q; pb['J_Bip_L_UpperArm'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_R_UpperArm'): pb['J_Bip_R_UpperArm'].rotation_quaternion = r_arm_q; pb['J_Bip_R_UpperArm'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_L_LowerArm'): pb['J_Bip_L_LowerArm'].rotation_quaternion = create_quaternion((0, 0, 0)); pb['J_Bip_L_LowerArm'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_R_LowerArm'): pb['J_Bip_R_LowerArm'].rotation_quaternion = create_quaternion((0, 0, 0)); pb['J_Bip_R_LowerArm'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_L_Hand'): pb['J_Bip_L_Hand'].rotation_quaternion = create_quaternion((0, -0.15, 0)); pb['J_Bip_L_Hand'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_R_Hand'): pb['J_Bip_R_Hand'].rotation_quaternion = create_quaternion((0, 0.15, 0)); pb['J_Bip_R_Hand'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        l_leg_q = create_quaternion((0, 0, -0.02))
        r_leg_q = create_quaternion((0, 0, 0.02))
        if pb.get('J_Bip_L_UpperLeg'): pb['J_Bip_L_UpperLeg'].rotation_quaternion = l_leg_q; pb['J_Bip_L_UpperLeg'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_R_UpperLeg'): pb['J_Bip_R_UpperLeg'].rotation_quaternion = r_leg_q; pb['J_Bip_R_UpperLeg'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_L_LowerLeg'): pb['J_Bip_L_LowerLeg'].rotation_quaternion = create_quaternion((0, 0, 0)); pb['J_Bip_L_LowerLeg'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_R_LowerLeg'): pb['J_Bip_R_LowerLeg'].rotation_quaternion = create_quaternion((0, 0, 0)); pb['J_Bip_R_LowerLeg'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        for side in ['L', 'R']:
            for f_name in ['Thumb', 'Index', 'Middle', 'Ring', 'Little']:
                for seg in range(1, 4):
                    b_name = f'J_Bip_{side}_{f_name}{seg}'
                    if pb.get(b_name): pb[b_name].rotation_quaternion = create_quaternion((0, 0, 0)); pb[b_name].keyframe_insert(data_path="rotation_quaternion", frame=frame)

    # =========================================================================
    # STATE 2: 02_DungNghi (120 frames)
    # =========================================================================
    print(">>> 2. Creating 02_DungNghi...")
    act_nghi = bpy.data.actions.new(name="02_DungNghi")
    char_arm.animation_data.action = act_nghi
    created_actions.append(act_nghi)
    for frame in range(1, 121):
        bpy.context.scene.frame_set(frame)
        t = (frame / 120.0) * math.pi * 2
        sway = math.sin(t) * 0.015
        breath = math.sin(t * 2) * 0.03
        if pb.get('J_Bip_C_Hips'):
            pb['J_Bip_C_Hips'].location = (0.035 + sway * 0.5, 0, -0.015); pb['J_Bip_C_Hips'].keyframe_insert(data_path="location", frame=frame)
            pb['J_Bip_C_Hips'].rotation_quaternion = create_quaternion((0.02, 0.04, -0.06 + sway)); pb['J_Bip_C_Hips'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_C_Spine'): pb['J_Bip_C_Spine'].rotation_quaternion = create_quaternion((0.02 + breath * 0.3, -0.02, 0.04)); pb['J_Bip_C_Spine'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_C_UpperChest'): pb['J_Bip_C_UpperChest'].rotation_quaternion = create_quaternion((0.03 + breath * 0.7, -0.02, 0.03)); pb['J_Bip_C_UpperChest'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_C_Head'): pb['J_Bip_C_Head'].rotation_quaternion = create_quaternion((0.02, 0.04 + sway, 0.03)); pb['J_Bip_C_Head'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        r_up_q = create_quaternion((-0.02, 0.0, 0.05))
        if pb.get('J_Bip_R_UpperLeg'): pb['J_Bip_R_UpperLeg'].rotation_quaternion = r_up_q; pb['J_Bip_R_UpperLeg'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_R_LowerLeg'): pb['J_Bip_R_LowerLeg'].rotation_quaternion = create_quaternion((0.04, 0, 0)); pb['J_Bip_R_LowerLeg'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        l_up_q = create_quaternion((-0.18, 0.05, -0.08))
        if pb.get('J_Bip_L_UpperLeg'): pb['J_Bip_L_UpperLeg'].rotation_quaternion = l_up_q; pb['J_Bip_L_UpperLeg'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_L_LowerLeg'): pb['J_Bip_L_LowerLeg'].rotation_quaternion = create_quaternion((0.35, 0, 0)); pb['J_Bip_L_LowerLeg'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        l_arm_q = create_quaternion((0.05, -0.05, -1.22 + sway))
        r_arm_q = create_quaternion((0.03, 0.05, 1.24 - sway))
        if pb.get('J_Bip_L_UpperArm'): pb['J_Bip_L_UpperArm'].rotation_quaternion = l_arm_q; pb['J_Bip_L_UpperArm'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_R_UpperArm'): pb['J_Bip_R_UpperArm'].rotation_quaternion = r_arm_q; pb['J_Bip_R_UpperArm'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_L_LowerArm'): pb['J_Bip_L_LowerArm'].rotation_quaternion = create_quaternion((0, 0, -0.18)); pb['J_Bip_L_LowerArm'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_R_LowerArm'): pb['J_Bip_R_LowerArm'].rotation_quaternion = create_quaternion((0, 0, 0.15)); pb['J_Bip_R_LowerArm'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

    # =========================================================================
    # STATE 3: 03_TPose (30 frames)
    # =========================================================================
    print(">>> 3. Creating 03_TPose...")
    act_tpose = bpy.data.actions.new(name="03_TPose")
    char_arm.animation_data.action = act_tpose
    created_actions.append(act_tpose)
    for frame in range(1, 31):
        bpy.context.scene.frame_set(frame)
        if pb.get('J_Bip_C_Hips'):
            pb['J_Bip_C_Hips'].location = (0, 0, 0); pb['J_Bip_C_Hips'].keyframe_insert(data_path="location", frame=frame)
            pb['J_Bip_C_Hips'].rotation_quaternion = create_quaternion((0, 0, 0)); pb['J_Bip_C_Hips'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        for b_name in ['J_Bip_C_Spine', 'J_Bip_C_UpperChest', 'J_Bip_C_Neck', 'J_Bip_C_Head',
                       'J_Bip_L_Shoulder', 'J_Bip_R_Shoulder', 'J_Bip_L_UpperArm', 'J_Bip_L_LowerArm', 'J_Bip_L_Hand',
                       'J_Bip_R_UpperArm', 'J_Bip_R_LowerArm', 'J_Bip_R_Hand',
                       'J_Bip_L_UpperLeg', 'J_Bip_L_LowerLeg', 'J_Bip_L_Foot',
                       'J_Bip_R_UpperLeg', 'J_Bip_R_LowerLeg', 'J_Bip_R_Foot']:
            if pb.get(b_name): pb[b_name].rotation_quaternion = create_quaternion((0, 0, 0)); pb[b_name].keyframe_insert(data_path="rotation_quaternion", frame=frame)

    # =========================================================================
    # STATE 4: 04_BuocDi_CoBan (60 frames - Stylized In-Place Walk)
    # =========================================================================
    print(">>> 4. Creating 04_BuocDi_CoBan...")
    act_walk_basic = bpy.data.actions.new(name="04_BuocDi_CoBan")
    char_arm.animation_data.action = act_walk_basic
    created_actions.append(act_walk_basic)
    for frame in range(1, 61):
        bpy.context.scene.frame_set(frame)
        phi = (frame / 60.0) * math.pi * 2
        l_stride = math.sin(phi)
        r_stride = -math.sin(phi)
        
        if pb.get('J_Bip_C_Hips'):
            pb['J_Bip_C_Hips'].location = (math.sin(phi) * 0.04, 0, -abs(math.sin(phi * 2)) * 0.045); pb['J_Bip_C_Hips'].keyframe_insert(data_path="location", frame=frame)
            pb['J_Bip_C_Hips'].rotation_quaternion = create_quaternion((0.04, -math.sin(phi) * 0.10, math.sin(phi) * 0.06)); pb['J_Bip_C_Hips'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_C_Spine'): pb['J_Bip_C_Spine'].rotation_quaternion = create_quaternion((0.02, math.sin(phi) * 0.06, -math.sin(phi) * 0.03)); pb['J_Bip_C_Spine'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        if pb.get('J_Bip_L_UpperLeg'): pb['J_Bip_L_UpperLeg'].rotation_quaternion = create_quaternion((l_stride * 0.55, 0, -0.02)); pb['J_Bip_L_UpperLeg'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_L_LowerLeg'): pb['J_Bip_L_LowerLeg'].rotation_quaternion = create_quaternion((max(0.0, -l_stride * 1.15 + 0.15), 0, 0)); pb['J_Bip_L_LowerLeg'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_R_UpperLeg'): pb['J_Bip_R_UpperLeg'].rotation_quaternion = create_quaternion((r_stride * 0.55, 0, 0.02)); pb['J_Bip_R_UpperLeg'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_R_LowerLeg'): pb['J_Bip_R_LowerLeg'].rotation_quaternion = create_quaternion((max(0.0, -r_stride * 1.15 + 0.15), 0, 0)); pb['J_Bip_R_LowerLeg'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        if pb.get('J_Bip_L_UpperArm'): pb['J_Bip_L_UpperArm'].rotation_quaternion = create_quaternion((r_stride * 0.45, 0, -1.25)); pb['J_Bip_L_UpperArm'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_R_UpperArm'): pb['J_Bip_R_UpperArm'].rotation_quaternion = create_quaternion((l_stride * 0.45, 0, 1.25)); pb['J_Bip_R_UpperArm'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

    # =========================================================================
    # STATE 5: 05_BuocDi_TuNhien (60 frames - STRICT GROUND CONTACT BIOMECHANICS)
    # AT LEAST 1 FOOT (AND 20% OF TIME BOTH FEET) LOCKED ON GROUND AT ALL TIMES!
    # =========================================================================
    print(">>> 5. Creating 05_BuocDi_TuNhien with Strict Continuous Ground Contact...")
    act_walk_grounded = bpy.data.actions.new(name="05_BuocDi_TuNhien")
    char_arm.animation_data.action = act_walk_grounded
    created_actions.append(act_walk_grounded)
    
    for frame in range(1, 61):
        bpy.context.scene.frame_set(frame)
        tau_left = ((frame - 1) / 60.0) % 1.0
        tau_right = (tau_left + 0.50) % 1.0
        
        # Calculate precise gait angles for left and right legs
        l_thigh, l_knee, l_foot = get_leg_gait_angles(tau_left)
        r_thigh, r_knee, r_foot = get_leg_gait_angles(tau_right)
        
        # Hip Weight Shift:
        # The pelvis is directly supported by whichever leg is in stance!
        # When left leg is in mid-stance (tau_left in [0.2, 0.4]), pelvis shifts to left (pelvis_x = +0.035)
        # When right leg is in mid-stance (tau_right in [0.2, 0.4]), pelvis shifts to right (pelvis_x = -0.035)
        pelvis_x = math.cos(tau_left * math.pi * 2) * 0.032
        
        # Pelvis drops lowest on double support (frames 1, 30) and rises highest during mid-stance (frames 15, 45)
        # Double support dip = -0.035m, mid-stance peak = 0.0m
        pelvis_z = -0.035 * (0.5 + 0.5 * math.cos(tau_left * math.pi * 4))
        
        # Pelvis Yaw: Pelvis rotates forward with the swinging leg
        pelvis_yaw = (l_thigh - r_thigh) * 0.22
        pelvis_roll = -pelvis_x * 1.5 # Pelvis drops slightly on swinging side
        
        if pb.get('J_Bip_C_Hips'):
            pb['J_Bip_C_Hips'].location = (pelvis_x, 0, pelvis_z)
            pb['J_Bip_C_Hips'].keyframe_insert(data_path="location", frame=frame)
            pb['J_Bip_C_Hips'].rotation_quaternion = create_quaternion((0.04, pelvis_yaw, pelvis_roll))
            pb['J_Bip_C_Hips'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        # Torso & Chest counter-rotation for human balance
        if pb.get('J_Bip_C_Spine'):
            pb['J_Bip_C_Spine'].rotation_quaternion = create_quaternion((0.02, -pelvis_yaw * 0.75, -pelvis_roll * 0.6))
            pb['J_Bip_C_Spine'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_C_UpperChest'):
            pb['J_Bip_C_UpperChest'].rotation_quaternion = create_quaternion((0.02, -pelvis_yaw * 0.9, -pelvis_roll * 0.75))
            pb['J_Bip_C_UpperChest'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_C_Head'):
            pb['J_Bip_C_Head'].rotation_quaternion = create_quaternion((-0.02, pelvis_yaw * 0.35, 0))
            pb['J_Bip_C_Head'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        # APPLY LEGS:
        l_up_q = create_quaternion((l_thigh, 0.0, -0.02))
        if pb.get('J_Bip_L_UpperLeg'): pb['J_Bip_L_UpperLeg'].rotation_quaternion = l_up_q; pb['J_Bip_L_UpperLeg'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_L_LowerLeg'): pb['J_Bip_L_LowerLeg'].rotation_quaternion = create_quaternion((l_knee, 0, 0)); pb['J_Bip_L_LowerLeg'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_L_Foot'): pb['J_Bip_L_Foot'].rotation_quaternion = create_quaternion((l_foot, 0, 0)); pb['J_Bip_L_Foot'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        r_up_q = create_quaternion((r_thigh, 0.0, 0.02))
        if pb.get('J_Bip_R_UpperLeg'): pb['J_Bip_R_UpperLeg'].rotation_quaternion = r_up_q; pb['J_Bip_R_UpperLeg'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_R_LowerLeg'): pb['J_Bip_R_LowerLeg'].rotation_quaternion = create_quaternion((r_knee, 0, 0)); pb['J_Bip_R_LowerLeg'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_R_Foot'): pb['J_Bip_R_Foot'].rotation_quaternion = create_quaternion((r_foot, 0, 0)); pb['J_Bip_R_Foot'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        # Secondary pants bones
        for s in ['J_Aim_L_UpperLeg', 'J_Roll_L_UpperLeg', 'J_Sec_L_TopsUpperLegFront', 'J_Sec_L_TopsUpperLegBack', 'J_Sec_L_TopsUpperLegSide']:
            if pb.get(s): pb[s].rotation_quaternion = l_up_q; pb[s].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        for s in ['J_Aim_R_UpperLeg', 'J_Roll_R_UpperLeg', 'J_Sec_R_TopsUpperLegFront', 'J_Sec_R_TopsUpperLegBack', 'J_Sec_R_TopsUpperLegSide']:
            if pb.get(s): pb[s].rotation_quaternion = r_up_q; pb[s].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        # ARMS: Left Arm swings in opposite direction to Left Leg (follows Right Leg r_thigh)
        l_arm_swing = r_thigh * 0.95
        r_arm_swing = l_thigh * 0.95
        
        l_arm_q = create_quaternion((l_arm_swing, 0.05, -1.25))
        r_arm_q = create_quaternion((r_arm_swing, -0.05, 1.25))
        if pb.get('J_Bip_L_UpperArm'): pb['J_Bip_L_UpperArm'].rotation_quaternion = l_arm_q; pb['J_Bip_L_UpperArm'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_R_UpperArm'): pb['J_Bip_R_UpperArm'].rotation_quaternion = r_arm_q; pb['J_Bip_R_UpperArm'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        
        l_elbow_bend = -0.15 - max(0.0, l_arm_swing) * 0.65
        r_elbow_bend = 0.15 + max(0.0, r_arm_swing) * 0.65
        if pb.get('J_Bip_L_LowerArm'): pb['J_Bip_L_LowerArm'].rotation_quaternion = create_quaternion((0, 0, l_elbow_bend)); pb['J_Bip_L_LowerArm'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_R_LowerArm'): pb['J_Bip_R_LowerArm'].rotation_quaternion = create_quaternion((0, 0, r_elbow_bend)); pb['J_Bip_R_LowerArm'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        if pb.get('J_Bip_L_Hand'): pb['J_Bip_L_Hand'].rotation_quaternion = create_quaternion((0.15 * math.sin(tau_left * math.pi * 2), -0.15, 0)); pb['J_Bip_L_Hand'].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pb.get('J_Bip_R_Hand'): pb['J_Bip_R_Hand'].rotation_quaternion = create_quaternion((0.15 * math.sin(tau_right * math.pi * 2), 0.15, 0)); pb['J_Bip_R_Hand'].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        for s in ['J_Aim_L_TopsUpperArm', 'J_Roll_L_UpperArm', 'J_Sec_L_TopsUpperArmInside', 'J_Sec_L_TopsUpperArmOutside']:
            if pb.get(s): pb[s].rotation_quaternion = l_arm_q; pb[s].keyframe_insert(data_path="rotation_quaternion", frame=frame)
        for s in ['J_Aim_R_TopsUpperArm', 'J_Roll_R_UpperArm', 'J_Sec_R_TopsUpperArmInside', 'J_Sec_R_TopsUpperArmOutside']:
            if pb.get(s): pb[s].rotation_quaternion = r_arm_q; pb[s].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        for side in ['L', 'R']:
            for f_name in ['Thumb', 'Index', 'Middle', 'Ring', 'Little']:
                for seg in range(1, 4):
                    b_name = f'J_Bip_{side}_{f_name}{seg}'
                    if pb.get(b_name):
                        pb[b_name].rotation_quaternion = create_quaternion((0, -0.25, -0.12 if side=='L' else 0.12))
                        pb[b_name].keyframe_insert(data_path="rotation_quaternion", frame=frame)

        # Hair react to walking momentum
        for pb_b in pb:
            if 'Hair' in pb_b.name:
                pb_b.rotation_quaternion = create_quaternion((0.08 + math.sin(tau_left * math.pi * 4) * 0.05, 0, math.cos(tau_left * math.pi * 2) * 0.03))
                pb_b.keyframe_insert(data_path="rotation_quaternion", frame=frame)

    # Push all 5 actions to NLA Tracks for multi-clip GLTF export
    print(">>> Pushing all 5 actions to NLA tracks for clean export...")
    for track in list(char_arm.animation_data.nla_tracks):
        char_arm.animation_data.nla_tracks.remove(track)
    for act in created_actions:
        track = char_arm.animation_data.nla_tracks.new()
        track.name = act.name
        track.strips.new(act.name, 1, act)

    bpy.ops.object.mode_set(mode='OBJECT')

    # Facial Blendshapes
    face_obj = None
    for obj in bpy.data.objects:
        if obj.type == 'MESH' and 'face' in obj.name.lower() and obj.data.shape_keys:
            face_obj = obj
            break
            
    if face_obj and face_obj.data.shape_keys:
        kb = face_obj.data.shape_keys.key_blocks
        face_obj.data.shape_keys.animation_data_create()
        vowels = ['Face_Blendshape.Fcl_MTH_A', 'Face_Blendshape.Fcl_MTH_I', 'Face_Blendshape.Fcl_MTH_U', 'Face_Blendshape.Fcl_MTH_E', 'Face_Blendshape.Fcl_MTH_O']
        for frame in range(1, 121):
            cycle_idx = int((frame / 16.0)) % 5
            mouth_open = max(0.0, math.sin((frame / 30.0) * math.pi * 6.0)) * 0.95
            is_wink = (40 <= frame <= 55) or (90 <= frame <= 105)
            for i, v_name in enumerate(vowels):
                if v_name in kb:
                    kb[v_name].value = mouth_open if i == cycle_idx else 0.0
                    kb[v_name].keyframe_insert(data_path="value", frame=frame)
            if 'Face_Blendshape.Fcl_ALL_Joy' in kb:
                kb['Face_Blendshape.Fcl_ALL_Joy'].value = 0.45 + 0.3 * math.sin((frame / 120.0) * math.pi * 4.0)
                kb['Face_Blendshape.Fcl_ALL_Joy'].keyframe_insert(data_path="value", frame=frame)
            if 'Face_Blendshape.Fcl_EYE_Close_L' in kb:
                kb['Face_Blendshape.Fcl_EYE_Close_L'].value = 1.0 if is_wink else 0.0
                kb['Face_Blendshape.Fcl_EYE_Close_L'].keyframe_insert(data_path="value", frame=frame)

    print(">>> Exporting all 5 Animation States to .glb, .fbx, .blend...")
    for folder, fname in [(out_b_dir, "female_singer_anime_idol"), (stage_dir, "female_singer_anime_pro")]:
        bpy.ops.export_scene.gltf(
            filepath=f"{folder}/{fname}.glb",
            export_format='GLB',
            export_animations=True,
            export_nla_strips=True,
            export_morph=True,
            export_skins=True
        )
        bpy.ops.export_scene.fbx(
            filepath=f"{folder}/{fname}.fbx",
            bake_anim=True,
            bake_anim_use_all_actions=True,
            use_mesh_modifiers=True,
            add_leaf_bones=False
        )
        bpy.ops.wm.save_as_mainfile(filepath=f"{folder}/{fname}.blend")
        
    print(">>> ALL 5 ANIMATION STATES EXPORTED WITH STRICT GROUND CONTACT!")

if __name__ == '__main__':
    build_all_states_strict_grounded_walk()
    print("=== DONE ===")
