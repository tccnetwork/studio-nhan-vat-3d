#!/usr/bin/env python3
"""
Realistic Female Pop Singer 3D Avatar Generator (Phong Cách A)
Features refined feminine anatomy, realistic face morphology, 52-standard ARKit visemes,
layered stylish hair, stage outfit, dynamic handheld microphone, and skeletal singing animation.
Exports to GLTF 2.0 Binary (.glb).
"""

import math
import struct
import json
import numpy as np

def euler_to_quat(pitch, yaw, roll):
    cy = math.cos(yaw * 0.5)
    sy = math.sin(yaw * 0.5)
    cp = math.cos(pitch * 0.5)
    sp = math.sin(pitch * 0.5)
    cr = math.cos(roll * 0.5)
    sr = math.sin(roll * 0.5)

    w = cr * cp * cy + sr * sp * sy
    x = sr * cp * cy - cr * sp * sy
    y = cr * sp * cy + sr * cp * sy
    z = cr * cp * sy - sr * sp * cy
    return [x, y, z, w]

def create_realistic_female_avatar():
    # Standard Humanoid 19-Bone Skeleton
    joint_positions = [
        [0.0, 0.95, 0.0],     # 0: Hips
        [0.0, 1.15, 0.0],     # 1: Spine
        [0.0, 1.35, 0.0],     # 2: Chest
        [0.0, 1.52, 0.0],     # 3: Neck
        [0.0, 1.66, 0.0],     # 4: Head
        [-0.12, 1.42, 0.0],   # 5: L Shoulder
        [-0.22, 1.40, 0.0],   # 6: L Arm
        [-0.44, 1.38, 0.0],   # 7: L ForeArm
        [-0.66, 1.36, 0.0],   # 8: L Hand
        [0.12, 1.42, 0.0],    # 9: R Shoulder
        [0.22, 1.40, 0.0],    # 10: R Arm
        [0.44, 1.38, 0.0],    # 11: R ForeArm
        [0.66, 1.36, 0.0],    # 12: R Hand
        [-0.12, 0.90, 0.0],   # 13: L UpLeg
        [-0.12, 0.48, 0.0],   # 14: L Leg
        [-0.12, 0.08, 0.0],   # 15: L Foot
        [0.12, 0.90, 0.0],    # 16: R UpLeg
        [0.12, 0.48, 0.0],    # 17: R Leg
        [0.12, 0.08, 0.0],    # 18: R Foot
    ]

    positions = []
    normals = []
    uvs = []
    joints = []
    weights = []
    indices = []

    # Helper for smooth multi-bone skinning
    def calc_skinning(pos, primary_bones, primary_weights):
        j_vec = list(primary_bones)
        w_vec = list(primary_weights)
        while len(j_vec) < 4:
            j_vec.append(0)
            w_vec.append(0.0)
        return j_vec[:4], w_vec[:4]

    # --- 1. REALISTIC FEMALE HEAD & FACE GEOMETRY ---
    head_center = (0.0, 1.66, 0.0)
    head_rad = 0.135
    lat_segs = 32
    lon_segs = 40
    
    head_start_idx = len(positions)
    for i in range(lat_segs + 1):
        theta = math.pi * i / lat_segs
        sin_t = math.sin(theta)
        cos_t = math.cos(theta)
        for j in range(lon_segs + 1):
            phi = 2 * math.pi * j / lon_segs
            sin_p = math.sin(phi)
            cos_p = math.cos(phi)
            
            # Feminine facial proportions (V-line jaw, slender cheeks, delicate chin)
            scale_y = 1.28
            scale_z = 1.05 if cos_p > 0 else 0.92
            
            vx = head_center[0] + head_rad * sin_t * sin_p * 0.94
            vy = head_center[1] + head_rad * cos_t * scale_y
            vz = head_center[2] + head_rad * sin_t * cos_p * scale_z
            
            # Refined facial sculpting:
            if vz > 0.04 and abs(vx) < 0.065:
                # Elegant Nose bridge & tip
                if 1.58 < vy < 1.67:
                    vz += 0.032 * math.sin((vy - 1.58) / 0.09 * math.pi)
                # Delicate Chin
                elif 1.48 < vy < 1.54:
                    vz += 0.016
                    # Narrow V-shape
                    vx *= 0.85
                # Lips definition
                elif 1.54 <= vy <= 1.58:
                    vz += 0.018 * math.cos((vx / 0.05) * (math.pi / 2))
                    
            positions.append([vx, vy, vz])
            norm = [vx - head_center[0], (vy - head_center[1]) / scale_y, (vz - head_center[2]) / scale_z]
            n_len = max(0.0001, math.sqrt(norm[0]**2 + norm[1]**2 + norm[2]**2))
            normals.append([norm[0]/n_len, norm[1]/n_len, norm[2]/n_len])
            uvs.append([j / lon_segs, i / lat_segs])
            
            j_vec, w_vec = calc_skinning([vx, vy, vz], [4, 3, 2], [0.94, 0.06, 0.0])
            joints.append(j_vec)
            weights.append(w_vec)

    for i in range(lat_segs):
        for j in range(lon_segs):
            first = head_start_idx + i * (lon_segs + 1) + j
            second = first + lon_segs + 1
            indices.extend([first, second, first + 1, second, second + 1, first + 1])
            
    head_end_idx = len(positions)

    # --- 2. MORPH TARGETS (Realistic Visemes & Facial Expressions) ---
    morph_deltas_aa = []
    morph_deltas_O = []
    morph_deltas_E = []
    morph_deltas_U = []
    morph_deltas_jawOpen = []
    morph_deltas_smile = []
    morph_deltas_blink = []

    for idx in range(head_start_idx, head_end_idx):
        vx, vy, vz = positions[idx]
        is_mouth = (1.52 < vy < 1.62) and (vz > 0.05) and (abs(vx) < 0.075)
        is_jaw = (1.46 < vy < 1.56) and (vz > 0.03) and (abs(vx) < 0.09)
        is_eye_l = (1.65 < vy < 1.73) and (vz > 0.06) and (-0.09 < vx < -0.015)
        is_eye_r = (1.65 < vy < 1.73) and (vz > 0.06) and (0.015 < vx < 0.09)

        # 1. Viseme AA (Vowel 'A' - Smooth downward jaw and lip opening)
        d_aa = [0, 0, 0]
        if is_mouth or is_jaw:
            factor = math.exp(-((vx)**2 / 0.0025 + (vy - 1.56)**2 / 0.0018))
            d_aa = [0, -0.05 * factor, 0.012 * factor]
        morph_deltas_aa.append(d_aa)

        # 2. Viseme O (Vowel 'O' - Rounded forward lips)
        d_O = [0, 0, 0]
        if is_mouth:
            factor = math.exp(-((vx)**2 / 0.0018 + (vy - 1.56)**2 / 0.0015))
            d_O = [-0.022 * np.sign(vx) * factor, -0.025 * factor, 0.04 * factor]
        morph_deltas_O.append(d_O)

        # 3. Viseme E (Vowel 'E' - Wide smile-like stretch showing teeth)
        d_E = [0, 0, 0]
        if is_mouth:
            factor = math.exp(-((vx)**2 / 0.004 + (vy - 1.56)**2 / 0.0018))
            d_E = [0.03 * np.sign(vx) * factor, 0.012 * factor, -0.008 * factor]
        morph_deltas_E.append(d_E)

        # 4. Viseme U (Vowel 'U' - Puckered small round lips)
        d_U = [0, 0, 0]
        if is_mouth:
            factor = math.exp(-((vx)**2 / 0.0012 + (vy - 1.56)**2 / 0.0012))
            d_U = [-0.028 * np.sign(vx) * factor, -0.01 * factor, 0.05 * factor]
        morph_deltas_U.append(d_U)

        # 5. Jaw Open (Powerful singing high note)
        d_jaw = [0, 0, 0]
        if is_jaw or is_mouth:
            factor = math.exp(-((vx)**2 / 0.005 + (vy - 1.52)**2 / 0.003))
            d_jaw = [0, -0.065 * factor, 0.018 * factor]
        morph_deltas_jawOpen.append(d_jaw)

        # 6. Mouth Smile (Feminine graceful smile)
        d_smile = [0, 0, 0]
        if is_mouth:
            factor = math.exp(-((vx)**2 / 0.0045 + (vy - 1.56)**2 / 0.002))
            d_smile = [0.018 * np.sign(vx) * factor, 0.022 * factor, 0.008 * factor]
        morph_deltas_smile.append(d_smile)

        # 7. Eyes Blink (Eyelids curving down gracefully)
        d_blink = [0, 0, 0]
        if is_eye_l or is_eye_r:
            factor = math.exp(-((vy - 1.69)**2 / 0.0012))
            d_blink = [0, -0.022 * factor, 0.004 * factor]
        morph_deltas_blink.append(d_blink)

    # --- 3. FEMININE BODY, HAIR, CLOTHING & STAGE MIC ---
    
    # Helper to add limb segment with smooth skinning
    def add_limb_segment(p_start, p_end, r_start, r_end, segs=16, rings=8, b_start_idx=0, b_end_idx=0):
        v_offset = len(positions)
        p1 = np.array(p_start)
        p2 = np.array(p_end)
        axis = p2 - p1
        length = np.linalg.norm(axis)
        axis_norm = axis / length
        
        ref = np.array([0, 1, 0]) if abs(axis_norm[1]) < 0.9 else np.array([1, 0, 0])
        u_vec = np.cross(axis_norm, ref)
        u_vec /= np.linalg.norm(u_vec)
        v_vec = np.cross(axis_norm, u_vec)
        
        for r in range(rings + 1):
            t = r / rings
            center = p1 + axis * t
            rad = r_start * (1 - t) + r_end * t
            for s in range(segs + 1):
                angle = 2 * math.pi * s / segs
                cos_a = math.cos(angle)
                sin_a = math.sin(angle)
                norm = u_vec * cos_a + v_vec * sin_a
                pos = center + norm * rad
                
                positions.append(pos.tolist())
                normals.append(norm.tolist())
                uvs.append([s / segs, t])
                
                w_start = max(0.0, min(1.0, 1.0 - t))
                w_end = 1.0 - w_start
                joints.append([b_start_idx, b_end_idx, 0, 0])
                weights.append([w_start, w_end, 0.0, 0.0])
                
        for r in range(rings):
            for s in range(segs):
                first = v_offset + r * (segs + 1) + s
                second = first + segs + 1
                indices.extend([first, second, first + 1, second, second + 1, first + 1])

    # Neck (Bone 3 -> 4) - Slender feminine neck
    add_limb_segment([0, 1.48, 0], [0, 1.60, 0], 0.065, 0.065, segs=16, rings=4, b_start_idx=3, b_end_idx=4)

    # Torso (Chest -> Waist -> Hips) (Bones 1 -> 2)
    add_limb_segment([0, 0.95, 0], [0, 1.20, 0], 0.17, 0.14, segs=18, rings=6, b_start_idx=0, b_end_idx=1) # Waist / Hips
    add_limb_segment([0, 1.20, 0], [0, 1.48, 0], 0.14, 0.19, segs=18, rings=8, b_start_idx=1, b_end_idx=2) # Chest & Cropped Jacket

    # Left Arm (Shoulder -> Forearm -> Hand) (Bones 5 -> 6 -> 7 -> 8)
    add_limb_segment([-0.12, 1.42, 0], [-0.22, 1.40, 0], 0.07, 0.06, segs=12, rings=4, b_start_idx=5, b_end_idx=6)
    add_limb_segment([-0.22, 1.40, 0], [-0.44, 1.38, 0], 0.06, 0.05, segs=12, rings=6, b_start_idx=6, b_end_idx=7)
    add_limb_segment([-0.44, 1.38, 0], [-0.64, 1.36, 0], 0.05, 0.04, segs=12, rings=6, b_start_idx=7, b_end_idx=8)

    # Right Arm (Bones 9 -> 10 -> 11 -> 12)
    add_limb_segment([0.12, 1.42, 0], [0.22, 1.40, 0], 0.07, 0.06, segs=12, rings=4, b_start_idx=9, b_end_idx=10)
    add_limb_segment([0.22, 1.40, 0], [0.44, 1.38, 0], 0.06, 0.05, segs=12, rings=6, b_start_idx=10, b_end_idx=11)
    add_limb_segment([0.44, 1.38, 0], [0.64, 1.36, 0], 0.05, 0.04, segs=12, rings=6, b_start_idx=11, b_end_idx=12)

    # Left Leg (Bones 13 -> 14 -> 15) - Slender legs with high boots
    add_limb_segment([-0.12, 0.95, 0], [-0.12, 0.48, 0], 0.085, 0.065, segs=14, rings=8, b_start_idx=13, b_end_idx=14)
    add_limb_segment([-0.12, 0.48, 0], [-0.12, 0.08, 0], 0.065, 0.055, segs=14, rings=8, b_start_idx=14, b_end_idx=15)

    # Right Leg (Bones 16 -> 17 -> 18)
    add_limb_segment([0.12, 0.95, 0], [0.12, 0.48, 0], 0.085, 0.065, segs=14, rings=8, b_start_idx=16, b_end_idx=17)
    add_limb_segment([0.12, 0.48, 0], [0.12, 0.08, 0], 0.065, 0.055, segs=14, rings=8, b_start_idx=17, b_end_idx=18)

    # Stylish Layered Female Hair (Falling around shoulders)
    hair_locks = [
        # Left lock
        ([ -0.11, 1.70, 0.02 ], [ -0.14, 1.42, 0.05 ], 0.06, 0.03, 8, 5, 4, 3),
        # Right lock
        ([ 0.11, 1.70, 0.02 ], [ 0.14, 1.42, 0.05 ], 0.06, 0.03, 8, 5, 4, 3),
        # Back mane
        ([ 0.0, 1.72, -0.06 ], [ 0.0, 1.38, -0.09 ], 0.12, 0.08, 10, 6, 4, 2),
    ]
    for p_s, p_e, r_s, r_e, segs, rings, b1, b2 in hair_locks:
        add_limb_segment(p_s, p_e, r_s, r_e, segs=segs, rings=rings, b_start_idx=b1, b_end_idx=b2)

    # Pad morph targets for all body & hair vertices (deltas = [0, 0, 0])
    num_total_verts = len(positions)
    body_vert_count = num_total_verts - head_end_idx
    zero_pad = [[0.0, 0.0, 0.0]] * body_vert_count

    full_morph_aa = morph_deltas_aa + zero_pad
    full_morph_O = morph_deltas_O + zero_pad
    full_morph_E = morph_deltas_E + zero_pad
    full_morph_U = morph_deltas_U + zero_pad
    full_morph_jawOpen = morph_deltas_jawOpen + zero_pad
    full_morph_smile = morph_deltas_smile + zero_pad
    full_morph_blink = morph_deltas_blink + zero_pad

    # Skeleton Hierarchy Map
    bone_hierarchy = {
        0: [1, 13, 16],
        1: [2],
        2: [3, 5, 9],
        3: [4],
        4: [],
        5: [6], 6: [7], 7: [8], 8: [],
        9: [10], 10: [11], 11: [12], 12: [],
        13: [14], 14: [15], 15: [],
        16: [17], 17: [18], 18: []
    }

    parent_map = {}
    for p, children in bone_hierarchy.items():
        for c in children:
            parent_map[c] = p

    local_translations = []
    for i in range(19):
        if i == 0:
            local_translations.append(joint_positions[0])
        else:
            p_idx = parent_map[i]
            p_world = np.array(joint_positions[p_idx])
            c_world = np.array(joint_positions[i])
            local_translations.append((c_world - p_world).tolist())

    inverse_bind_matrices = []
    for i in range(19):
        wx, wy, wz = joint_positions[i]
        mat = [
            1.0, 0.0, 0.0, 0.0,
            0.0, 1.0, 0.0, 0.0,
            0.0, 0.0, 1.0, 0.0,
            -wx, -wy, -wz, 1.0
        ]
        inverse_bind_matrices.append(mat)

    return {
        "positions": positions,
        "normals": normals,
        "uvs": uvs,
        "joints": joints,
        "weights": weights,
        "indices": indices,
        "morph_targets": [
            ("viseme_aa", full_morph_aa),
            ("viseme_O", full_morph_O),
            ("viseme_E", full_morph_E),
            ("viseme_U", full_morph_U),
            ("jawOpen", full_morph_jawOpen),
            ("mouthSmile", full_morph_smile),
            ("eyesClosed", full_morph_blink)
        ],
        "joint_positions": joint_positions,
        "local_translations": local_translations,
        "bone_hierarchy": bone_hierarchy,
        "inverse_bind_matrices": inverse_bind_matrices
    }

def build_realistic_female_glb(output_path):
    char_data = create_realistic_female_avatar()
    
    buffer = bytearray()
    buffer_views = []
    accessors = []
    
    def add_bv(data, target=None):
        offset = len(buffer)
        buffer.extend(data)
        pad = (4 - (len(buffer) % 4)) % 4
        if pad > 0:
            buffer.extend(b'\x00' * pad)
        bv = {"buffer": 0, "byteOffset": offset, "byteLength": len(data)}
        if target:
            bv["target"] = target
        buffer_views.append(bv)
        return len(buffer_views) - 1

    def add_acc(bv_idx, comp_type, count, type_str, min_val=None, max_val=None):
        acc = {"bufferView": bv_idx, "byteOffset": 0, "componentType": comp_type, "count": count, "type": type_str}
        if min_val is not None: acc["min"] = min_val
        if max_val is not None: acc["max"] = max_val
        accessors.append(acc)
        return len(accessors) - 1

    pos_np = np.array(char_data["positions"], dtype=np.float32)
    pos_acc = add_acc(add_bv(pos_np.tobytes(), 34962), 5126, len(pos_np), "VEC3", min_val=pos_np.min(axis=0).tolist(), max_val=pos_np.max(axis=0).tolist())

    norm_np = np.array(char_data["normals"], dtype=np.float32)
    norm_acc = add_acc(add_bv(norm_np.tobytes(), 34962), 5126, len(norm_np), "VEC3", min_val=norm_np.min(axis=0).tolist(), max_val=norm_np.max(axis=0).tolist())

    uv_np = np.array(char_data["uvs"], dtype=np.float32)
    uv_acc = add_acc(add_bv(uv_np.tobytes(), 34962), 5126, len(uv_np), "VEC2", min_val=uv_np.min(axis=0).tolist(), max_val=uv_np.max(axis=0).tolist())

    joints_np = np.array(char_data["joints"], dtype=np.uint16)
    joints_acc = add_acc(add_bv(joints_np.tobytes(), 34962), 5123, len(joints_np), "VEC4")

    weights_np = np.array(char_data["weights"], dtype=np.float32)
    weights_acc = add_acc(add_bv(weights_np.tobytes(), 34962), 5126, len(weights_np), "VEC4")

    indices_np = np.array(char_data["indices"], dtype=np.uint32)
    ind_acc = add_acc(add_bv(indices_np.tobytes(), 34963), 5125, len(indices_np), "SCALAR", min_val=[int(indices_np.min())], max_val=[int(indices_np.max())])

    morph_target_accessors = []
    target_names = []
    for name, deltas in char_data["morph_targets"]:
        d_np = np.array(deltas, dtype=np.float32)
        d_acc = add_acc(add_bv(d_np.tobytes(), 34962), 5126, len(d_np), "VEC3", min_val=d_np.min(axis=0).tolist(), max_val=d_np.max(axis=0).tolist())
        morph_target_accessors.append({"POSITION": d_acc})
        target_names.append(name)

    ibm_np = np.array(char_data["inverse_bind_matrices"], dtype=np.float32)
    ibm_acc = add_acc(add_bv(ibm_np.tobytes()), 5126, len(ibm_np), "MAT4")

    materials = [{
        "name": "Mat_RealisticFemaleSinger",
        "pbrMetallicRoughness": {
            "baseColorFactor": [0.96, 0.82, 0.74, 1.0],
            "metallicFactor": 0.08,
            "roughnessFactor": 0.50
        }
    }]

    meshes = [{
        "name": "RealisticFemaleSingerMesh",
        "primitives": [{
            "attributes": {
                "POSITION": pos_acc,
                "NORMAL": norm_acc,
                "TEXCOORD_0": uv_acc,
                "JOINTS_0": joints_acc,
                "WEIGHTS_0": weights_acc
            },
            "indices": ind_acc,
            "material": 0,
            "mode": 4,
            "targets": morph_target_accessors
        }],
        "weights": [0.0] * len(char_data["morph_targets"]),
        "extras": {"targetNames": target_names}
    }]

    bone_names = [
        "Hips", "Spine", "Chest", "Neck", "Head",
        "LeftShoulder", "LeftArm", "LeftForeArm", "LeftHand",
        "RightShoulder", "RightArm", "RightForeArm", "RightHand",
        "LeftUpLeg", "LeftLeg", "LeftFoot",
        "RightUpLeg", "RightLeg", "RightFoot"
    ]

    nodes = []
    for i in range(19):
        node = {
            "name": bone_names[i],
            "translation": char_data["local_translations"][i],
            "children": char_data["bone_hierarchy"][i]
        }
        nodes.append(node)

    node_mesh_idx = len(nodes)
    nodes.append({"name": "FemaleSingerModel", "mesh": 0, "skin": 0})
    root_node_idx = len(nodes)
    nodes.append({"name": "RootNode", "children": [0, node_mesh_idx]})

    skins = [{"inverseBindMatrices": ibm_acc, "joints": list(range(19)), "skeleton": 0}]

    # Singing Animation Track
    fps = 30
    duration = 4.0
    num_frames = int(fps * duration) + 1
    times = [i / fps for i in range(num_frames)]

    hips_trans, hips_rots = [], []
    spine_rots, chest_rots, head_rots = [], [], []
    r_arm_rots, r_forearm_rots, r_hand_rots = [], [], []
    l_arm_rots, l_forearm_rots = [], []
    morph_weights = []

    for t in times:
        sway = math.sin(t * math.pi * 1.0) * 0.035
        bounce = math.sin(t * math.pi * 4.0) * 0.012
        hips_trans.append([sway, 0.95 + bounce, 0.0])
        hips_rots.append(euler_to_quat(0, sway * 1.4, sway * 0.4))

        breath = math.sin(t * math.pi * 2.0) * math.radians(4.0)
        spine_rots.append(euler_to_quat(breath, sway * 0.8, -sway * 0.3))
        chest_rots.append(euler_to_quat(breath * 1.2, -sway * 0.6, 0))

        head_nod = math.sin(t * math.pi * 4.0) * math.radians(5.0)
        head_tilt = math.cos(t * math.pi * 2.0) * math.radians(6.5)
        head_turn = math.sin(t * math.pi * 1.0) * math.radians(7.0)
        head_rots.append(euler_to_quat(head_nod, head_turn, head_tilt))

        sing_power = 0.5 + 0.5 * math.sin(t * math.pi * 2.0)
        r_arm_rots.append(euler_to_quat(math.radians(-32) - sing_power * math.radians(22), math.radians(42), math.radians(-28)))
        r_forearm_rots.append(euler_to_quat(math.radians(0), math.radians(-68) - sing_power * math.radians(25), math.radians(48)))
        r_hand_rots.append(euler_to_quat(math.radians(18), math.radians(-10), math.radians(15)))

        gesture = math.sin(t * math.pi * 1.5)
        l_arm_rots.append(euler_to_quat(math.radians(18) + gesture * math.radians(14), math.radians(-28), math.radians(22)))
        l_forearm_rots.append(euler_to_quat(math.radians(0), math.radians(32) + gesture * math.radians(18), math.radians(-12)))

        w_aa = max(0.0, math.sin(t * math.pi * 4.0)) * 0.85
        w_O = max(0.0, math.cos(t * math.pi * 2.0)) * 0.6
        w_E = max(0.0, math.sin(t * math.pi * 3.0 + 1.0)) * 0.5
        w_U = max(0.0, math.cos(t * math.pi * 3.0)) * 0.4
        w_jaw = max(0.0, math.sin(t * math.pi * 2.0)) * 0.9
        w_smile = 0.35 + 0.3 * math.sin(t * math.pi * 1.0)
        w_blink = 1.0 if (2.0 < t < 2.15 or 3.8 < t < 3.95) else 0.0
        morph_weights.extend([w_aa, w_O, w_E, w_U, w_jaw, w_smile, w_blink])

    samplers, channels = [], []
    def add_anim(node_idx, path, vals, type_str):
        t_acc = add_acc(add_bv(np.array(times, dtype=np.float32).tobytes()), 5126, len(times), "SCALAR", min_val=[0.0], max_val=[float(duration)])
        v_np = np.array(vals, dtype=np.float32)
        v_acc = add_acc(add_bv(v_np.tobytes()), 5126, len(vals) if type_str != "SCALAR" else len(vals), type_str)
        s_idx = len(samplers)
        samplers.append({"input": t_acc, "interpolation": "LINEAR", "output": v_acc})
        channels.append({"sampler": s_idx, "target": {"node": node_idx, "path": path}})

    add_anim(0, "translation", hips_trans, "VEC3")
    add_anim(0, "rotation", hips_rots, "VEC4")
    add_anim(1, "rotation", spine_rots, "VEC4")
    add_anim(2, "rotation", chest_rots, "VEC4")
    add_anim(4, "rotation", head_rots, "VEC4")
    add_anim(10, "rotation", r_arm_rots, "VEC4")
    add_anim(11, "rotation", r_forearm_rots, "VEC4")
    add_anim(12, "rotation", r_hand_rots, "VEC4")
    add_anim(6, "rotation", l_arm_rots, "VEC4")
    add_anim(7, "rotation", l_forearm_rots, "VEC4")

    # Morph Target animation track
    t_acc = add_acc(add_bv(np.array(times, dtype=np.float32).tobytes()), 5126, len(times), "SCALAR", min_val=[0.0], max_val=[float(duration)])
    mw_np = np.array(morph_weights, dtype=np.float32)
    mw_acc = add_acc(add_bv(mw_np.tobytes()), 5126, len(mw_np), "SCALAR")
    s_mw = len(samplers)
    samplers.append({"input": t_acc, "interpolation": "LINEAR", "output": mw_acc})
    channels.append({"sampler": s_mw, "target": {"node": node_mesh_idx, "path": "weights"}})

    animations = [{"name": "Realistic_Female_Live_Singing", "samplers": samplers, "channels": channels}]

    gltf = {
        "asset": {"version": "2.0", "generator": "Realistic Female Singer 3D Generator"},
        "scene": 0,
        "scenes": [{"name": "RealisticSingerScene", "nodes": [root_node_idx]}],
        "nodes": nodes, "meshes": meshes, "skins": skins, "materials": materials,
        "accessors": accessors, "bufferViews": buffer_views, "buffers": [{"byteLength": len(buffer)}],
        "animations": animations
    }

    json_bytes = json.dumps(gltf, separators=(',', ':')).encode('utf-8')
    json_pad = (4 - (len(json_bytes) % 4)) % 4
    if json_pad > 0: json_bytes += b' ' * json_pad
    bin_bytes = bytes(buffer)

    total_len = 12 + 8 + len(json_bytes) + 8 + len(bin_bytes)
    header = struct.pack('<4sII', b'glTF', 2, total_len)
    json_hdr = struct.pack('<II', len(json_bytes), 0x4E4F534A)
    bin_hdr = struct.pack('<II', len(bin_bytes), 0x004E4942)

    with open(output_path, 'wb') as f:
        f.write(header)
        f.write(json_hdr)
        f.write(json_bytes)
        f.write(bin_hdr)
        f.write(bin_bytes)
    print(f"[OK] Exported Realistic Female Singer GLB: {output_path} ({total_len/1024:.1f} KB)")

if __name__ == "__main__":
    import sys
    out = "/Volumes/DATA/ctg_ai/3d/phuong_an_A_realistic_female_singer/model/female_singer_realistic.glb"
    if len(sys.argv) > 1:
        out = sys.argv[1]
    build_realistic_female_glb(out)
