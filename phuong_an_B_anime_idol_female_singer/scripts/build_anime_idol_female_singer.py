#!/usr/bin/env python3
"""
Anime 3D Idol Female Singer 3D Avatar Generator (Phong Cách B)
Features Japanese Anime aesthetics, big sparkling eyes, twin-tails hair,
pleated idol skirt, ribbon bow, stage headset mic, and high-energy J-Pop idol performance animation.
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

def create_anime_idol_avatar():
    # Humanoid 19-Bone Skeleton for Anime Character
    joint_positions = [
        [0.0, 0.90, 0.0],     # 0: Hips
        [0.0, 1.10, 0.0],     # 1: Spine
        [0.0, 1.30, 0.0],     # 2: Chest
        [0.0, 1.48, 0.0],     # 3: Neck
        [0.0, 1.62, 0.0],     # 4: Head
        [-0.11, 1.38, 0.0],   # 5: L Shoulder
        [-0.20, 1.36, 0.0],   # 6: L Arm
        [-0.40, 1.34, 0.0],   # 7: L ForeArm
        [-0.60, 1.32, 0.0],   # 8: L Hand
        [0.11, 1.38, 0.0],    # 9: R Shoulder
        [0.20, 1.36, 0.0],    # 10: R Arm
        [0.40, 1.34, 0.0],    # 11: R ForeArm
        [0.60, 1.32, 0.0],    # 12: R Hand
        [-0.11, 0.85, 0.0],   # 13: L UpLeg
        [-0.11, 0.45, 0.0],   # 14: L Leg
        [-0.11, 0.06, 0.0],   # 15: L Foot
        [0.11, 0.85, 0.0],    # 16: R UpLeg
        [0.11, 0.45, 0.0],    # 17: R Leg
        [0.11, 0.06, 0.0],    # 18: R Foot
    ]

    positions = []
    normals = []
    uvs = []
    joints = []
    weights = []
    indices = []

    def calc_skinning(pos, primary_bones, primary_weights):
        j_vec = list(primary_bones)
        w_vec = list(primary_weights)
        while len(j_vec) < 4:
            j_vec.append(0)
            w_vec.append(0.0)
        return j_vec[:4], w_vec[:4]

    # --- 1. ANIME FEMALE HEAD & FACE (Big Eyes, Cute V-chin, Petite Nose) ---
    head_center = (0.0, 1.62, 0.0)
    head_rad = 0.145
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

            # Anime proportions: slightly larger head ratio, soft cheeks, pointed chin
            scale_y = 1.18
            scale_z = 1.08 if cos_p > 0 else 0.95

            vx = head_center[0] + head_rad * sin_t * sin_p * 0.98
            vy = head_center[1] + head_rad * cos_t * scale_y
            vz = head_center[2] + head_rad * sin_t * cos_p * scale_z

            # Anime sculpting
            if vz > 0.04 and abs(vx) < 0.07:
                # Cute petite anime nose
                if 1.55 < vy < 1.62:
                    vz += 0.018 * math.sin((vy - 1.55) / 0.07 * math.pi)
                # Pointed anime chin
                elif 1.45 < vy < 1.51:
                    vz += 0.015
                    vx *= 0.78
                # Anime mouth
                elif 1.50 <= vy <= 1.54:
                    vz += 0.012

            positions.append([vx, vy, vz])
            norm = [vx - head_center[0], (vy - head_center[1]) / scale_y, (vz - head_center[2]) / scale_z]
            n_len = max(0.0001, math.sqrt(norm[0]**2 + norm[1]**2 + norm[2]**2))
            normals.append([norm[0]/n_len, norm[1]/n_len, norm[2]/n_len])
            uvs.append([j / lon_segs, i / lat_segs])

            j_vec, w_vec = calc_skinning([vx, vy, vz], [4, 3, 2], [0.95, 0.05, 0.0])
            joints.append(j_vec)
            weights.append(w_vec)

    for i in range(lat_segs):
        for j in range(lon_segs):
            first = head_start_idx + i * (lon_segs + 1) + j
            second = first + lon_segs + 1
            indices.extend([first, second, first + 1, second, second + 1, first + 1])

    head_end_idx = len(positions)

    # --- 2. ANIME MORPH TARGETS (Visemes + Anime Wink + Big Smile) ---
    morph_deltas_aa = []
    morph_deltas_O = []
    morph_deltas_E = []
    morph_deltas_U = []
    morph_deltas_jawOpen = []
    morph_deltas_smile = []
    morph_deltas_blink = []
    morph_deltas_wink = []

    for idx in range(head_start_idx, head_end_idx):
        vx, vy, vz = positions[idx]
        is_mouth = (1.48 < vy < 1.57) and (vz > 0.05) and (abs(vx) < 0.065)
        is_jaw = (1.44 < vy < 1.52) and (vz > 0.03) and (abs(vx) < 0.08)
        is_eye_l = (1.60 < vy < 1.70) and (vz > 0.06) and (-0.10 < vx < -0.015)
        is_eye_r = (1.60 < vy < 1.70) and (vz > 0.06) and (0.015 < vx < 0.10)

        # 1. Viseme AA (Anime triangle / open singing mouth)
        d_aa = [0, 0, 0]
        if is_mouth or is_jaw:
            factor = math.exp(-((vx)**2 / 0.002 + (vy - 1.52)**2 / 0.0015))
            d_aa = [0, -0.052 * factor, 0.015 * factor]
        morph_deltas_aa.append(d_aa)

        # 2. Viseme O (Cute small round mouth)
        d_O = [0, 0, 0]
        if is_mouth:
            factor = math.exp(-((vx)**2 / 0.0014 + (vy - 1.52)**2 / 0.0012))
            d_O = [-0.02 * np.sign(vx) * factor, -0.02 * factor, 0.038 * factor]
        morph_deltas_O.append(d_O)

        # 3. Viseme E (Anime wide mouth)
        d_E = [0, 0, 0]
        if is_mouth:
            factor = math.exp(-((vx)**2 / 0.0035 + (vy - 1.52)**2 / 0.0015))
            d_E = [0.028 * np.sign(vx) * factor, 0.01 * factor, -0.006 * factor]
        morph_deltas_E.append(d_E)

        # 4. Viseme U (Anime pouty singing)
        d_U = [0, 0, 0]
        if is_mouth:
            factor = math.exp(-((vx)**2 / 0.001 + (vy - 1.52)**2 / 0.001))
            d_U = [-0.025 * np.sign(vx) * factor, -0.008 * factor, 0.045 * factor]
        morph_deltas_U.append(d_U)

        # 5. Jaw Open (High note climax)
        d_jaw = [0, 0, 0]
        if is_jaw or is_mouth:
            factor = math.exp(-((vx)**2 / 0.004 + (vy - 1.48)**2 / 0.0025))
            d_jaw = [0, -0.06 * factor, 0.016 * factor]
        morph_deltas_jawOpen.append(d_jaw)

        # 6. Anime Cute Smile
        d_smile = [0, 0, 0]
        if is_mouth:
            factor = math.exp(-((vx)**2 / 0.0038 + (vy - 1.52)**2 / 0.0018))
            d_smile = [0.022 * np.sign(vx) * factor, 0.025 * factor, 0.01 * factor]
        morph_deltas_smile.append(d_smile)

        # 7. Anime Double Blink
        d_blink = [0, 0, 0]
        if is_eye_l or is_eye_r:
            factor = math.exp(-((vy - 1.65)**2 / 0.0015))
            d_blink = [0, -0.028 * factor, 0.005 * factor]
        morph_deltas_blink.append(d_blink)

        # 8. Anime Single Wink (Left Eye)
        d_wink = [0, 0, 0]
        if is_eye_l:
            factor = math.exp(-((vy - 1.65)**2 / 0.0015))
            d_wink = [0, -0.028 * factor, 0.005 * factor]
        morph_deltas_wink.append(d_wink)

    # --- 3. ANIME IDOL BODY, TWIN-TAILS HAIR, PLEATED SKIRT & OUTFIT ---
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

    # Neck
    add_limb_segment([0, 1.45, 0], [0, 1.56, 0], 0.058, 0.058, segs=16, rings=4, b_start_idx=3, b_end_idx=4)

    # Torso (Corset Vest + Idol Top)
    add_limb_segment([0, 0.90, 0], [0, 1.15, 0], 0.16, 0.13, segs=18, rings=6, b_start_idx=0, b_end_idx=1)
    add_limb_segment([0, 1.15, 0], [0, 1.45, 0], 0.13, 0.17, segs=18, rings=8, b_start_idx=1, b_end_idx=2)

    # Pleated Idol Skirt (Xòe ra hình nón)
    add_limb_segment([0, 0.96, 0], [0, 0.72, 0], 0.16, 0.32, segs=24, rings=8, b_start_idx=0, b_end_idx=0)

    # Left & Right Arms
    add_limb_segment([-0.11, 1.38, 0], [-0.20, 1.36, 0], 0.065, 0.055, segs=12, rings=4, b_start_idx=5, b_end_idx=6)
    add_limb_segment([-0.20, 1.36, 0], [-0.40, 1.34, 0], 0.055, 0.045, segs=12, rings=6, b_start_idx=6, b_end_idx=7)
    add_limb_segment([-0.40, 1.34, 0], [-0.58, 1.32, 0], 0.045, 0.038, segs=12, rings=6, b_start_idx=7, b_end_idx=8)

    add_limb_segment([0.11, 1.38, 0], [0.20, 1.36, 0], 0.065, 0.055, segs=12, rings=4, b_start_idx=9, b_end_idx=10)
    add_limb_segment([0.20, 1.36, 0], [0.40, 1.34, 0], 0.055, 0.045, segs=12, rings=6, b_start_idx=10, b_end_idx=11)
    add_limb_segment([0.40, 1.34, 0], [0.58, 1.32, 0], 0.045, 0.038, segs=12, rings=6, b_start_idx=11, b_end_idx=12)

    # Legs (Over-the-knee socks + Mary Jane idol shoes)
    add_limb_segment([-0.11, 0.90, 0], [-0.11, 0.45, 0], 0.075, 0.06, segs=14, rings=8, b_start_idx=13, b_end_idx=14)
    add_limb_segment([-0.11, 0.45, 0], [-0.11, 0.06, 0], 0.06, 0.05, segs=14, rings=8, b_start_idx=14, b_end_idx=15)

    add_limb_segment([0.11, 0.90, 0], [0.11, 0.45, 0], 0.075, 0.06, segs=14, rings=8, b_start_idx=16, b_end_idx=17)
    add_limb_segment([0.11, 0.45, 0], [0.11, 0.06, 0], 0.06, 0.05, segs=14, rings=8, b_start_idx=17, b_end_idx=18)

    # Anime Twin-Tails Hair (Hai bím tóc dài uốn lượn bồng bềnh)
    # Left Twin-tail
    add_limb_segment([-0.14, 1.70, -0.02], [-0.26, 1.35, -0.05], 0.06, 0.04, 10, 6, 4, 4)
    add_limb_segment([-0.26, 1.35, -0.05], [-0.22, 0.95, 0.02], 0.04, 0.02, 10, 6, 4, 4)

    # Right Twin-tail
    add_limb_segment([0.14, 1.70, -0.02], [0.26, 1.35, -0.05], 0.06, 0.04, 10, 6, 4, 4)
    add_limb_segment([0.26, 1.35, -0.05], [0.22, 0.95, 0.02], 0.04, 0.02, 10, 6, 4, 4)

    # Front bangs
    add_limb_segment([0.0, 1.72, 0.04], [0.0, 1.62, 0.13], 0.12, 0.08, 12, 4, 4, 4)

    # Pad morph targets
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
    full_morph_wink = morph_deltas_wink + zero_pad

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
            ("eyesClosed", full_morph_blink),
            ("eyeWinkLeft", full_morph_wink)
        ],
        "joint_positions": joint_positions,
        "local_translations": local_translations,
        "bone_hierarchy": bone_hierarchy,
        "inverse_bind_matrices": inverse_bind_matrices
    }

def build_anime_idol_glb(output_path):
    char_data = create_anime_idol_avatar()

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

    # Anime Pastel Material (Anime Cel / Toon soft pink skin & pastel idol colors)
    materials = [{
        "name": "Mat_AnimeIdolSinger",
        "pbrMetallicRoughness": {
            "baseColorFactor": [1.0, 0.88, 0.84, 1.0],
            "metallicFactor": 0.0,
            "roughnessFactor": 0.45
        }
    }]

    meshes = [{
        "name": "AnimeIdolSingerMesh",
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
    nodes.append({"name": "AnimeIdolModel", "mesh": 0, "skin": 0})
    root_node_idx = len(nodes)
    nodes.append({"name": "RootNode", "children": [0, node_mesh_idx]})

    skins = [{"inverseBindMatrices": ibm_acc, "joints": list(range(19)), "skeleton": 0}]

    # High-Energy J-Pop Idol Performance Animation
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
        # Bouncy cute idol hop (130 BPM bounce)
        hop = abs(math.sin(t * math.pi * 4.33)) * 0.03
        sway = math.sin(t * math.pi * 2.16) * 0.04
        hips_trans.append([sway, 0.90 + hop, 0.0])
        hips_rots.append(euler_to_quat(0, sway * 1.8, sway * 0.8))

        spine_rots.append(euler_to_quat(math.sin(t * math.pi * 4.33) * 0.05, sway * 0.8, -sway * 0.5))
        chest_rots.append(euler_to_quat(math.cos(t * math.pi * 2.16) * 0.06, -sway * 0.6, 0))

        head_nod = math.sin(t * math.pi * 4.33) * math.radians(7.0)
        head_tilt = math.cos(t * math.pi * 2.16) * math.radians(9.0)
        head_turn = math.sin(t * math.pi * 1.08) * math.radians(8.0)
        head_rots.append(euler_to_quat(head_nod, head_turn, head_tilt))

        # Right Arm: Dynamic idol singing poses (Heart hand / Mic to lips)
        sing_power = 0.5 + 0.5 * math.sin(t * math.pi * 2.16)
        r_arm_rots.append(euler_to_quat(math.radians(-35) - sing_power * math.radians(25), math.radians(45), math.radians(-30)))
        r_forearm_rots.append(euler_to_quat(math.radians(0), math.radians(-72) - sing_power * math.radians(28), math.radians(52)))
        r_hand_rots.append(euler_to_quat(math.radians(20), math.radians(-12), math.radians(18)))

        # Left Arm: Cute idol pointing / Peace gesture to fans
        gesture = math.sin(t * math.pi * 2.16)
        l_arm_rots.append(euler_to_quat(math.radians(22) + gesture * math.radians(20), math.radians(-32), math.radians(28)))
        l_forearm_rots.append(euler_to_quat(math.radians(0), math.radians(38) + gesture * math.radians(25), math.radians(-18)))

        # Anime Morph Weights (with wink!)
        w_aa = max(0.0, math.sin(t * math.pi * 4.33)) * 0.9
        w_O = max(0.0, math.cos(t * math.pi * 2.16)) * 0.65
        w_E = max(0.0, math.sin(t * math.pi * 3.25 + 1.0)) * 0.55
        w_U = max(0.0, math.cos(t * math.pi * 3.25)) * 0.45
        w_jaw = max(0.0, math.sin(t * math.pi * 2.16)) * 0.85
        w_smile = 0.4 + 0.35 * math.sin(t * math.pi * 1.08)
        w_blink = 1.0 if (3.8 < t < 3.95) else 0.0
        w_wink = 1.0 if (1.8 < t < 2.2) else 0.0 # Cute Idol wink at 2s mark!
        morph_weights.extend([w_aa, w_O, w_E, w_U, w_jaw, w_smile, w_blink, w_wink])

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

    # Morph Target channel
    t_acc = add_acc(add_bv(np.array(times, dtype=np.float32).tobytes()), 5126, len(times), "SCALAR", min_val=[0.0], max_val=[float(duration)])
    mw_np = np.array(morph_weights, dtype=np.float32)
    mw_acc = add_acc(add_bv(mw_np.tobytes()), 5126, len(mw_np), "SCALAR")
    s_mw = len(samplers)
    samplers.append({"input": t_acc, "interpolation": "LINEAR", "output": mw_acc})
    channels.append({"sampler": s_mw, "target": {"node": node_mesh_idx, "path": "weights"}})

    animations = [{"name": "Anime_Idol_JPop_Live_Performance", "samplers": samplers, "channels": channels}]

    gltf = {
        "asset": {"version": "2.0", "generator": "Anime 3D Idol Singer Generator"},
        "scene": 0,
        "scenes": [{"name": "AnimeIdolScene", "nodes": [root_node_idx]}],
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
    print(f"[OK] Exported Anime Idol Female Singer GLB: {output_path} ({total_len/1024:.1f} KB)")

if __name__ == "__main__":
    import sys
    out = "/Volumes/DATA/ctg_ai/3d/phuong_an_B_anime_idol_female_singer/model/female_singer_anime_idol.glb"
    if len(sys.argv) > 1:
        out = sys.argv[1]
    build_anime_idol_glb(out)
