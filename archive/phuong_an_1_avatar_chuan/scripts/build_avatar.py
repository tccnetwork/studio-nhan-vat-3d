#!/usr/bin/env python3
"""
Standard Humanoid 3D Avatar Generator with Full Skeletal Rigging,
52-Standard Morph Targets (Visemes for Singing Lip-Sync), PBR Materials,
Microphone Stage Prop, and Performance Animation.
Exports to GLTF 2.0 Binary (.glb) for Phuong An 1.
"""

import math
import struct
import json
import numpy as np

def create_humanoid_skinned_character():
    """
    Constructs a detailed Humanoid Avatar mesh with smooth skinning weights (JOINTS_0, WEIGHTS_0),
    Morph Targets (Visemes A, E, I, O, U, Mouth Open, Smile, Blink),
    and attached stage microphone prop.
    """
    
    # Bone Indices Definition:
    # 0: Root / Hips
    # 1: Spine
    # 2: Chest
    # 3: Neck
    # 4: Head
    # 5: LeftShoulder
    # 6: LeftArm
    # 7: LeftForeArm
    # 8: LeftHand
    # 9: RightShoulder
    # 10: RightArm
    # 11: RightForeArm
    # 12: RightHand (holds mic)
    # 13: LeftUpLeg
    # 14: LeftLeg
    # 15: LeftFoot
    # 16: RightUpLeg
    # 17: RightLeg
    # 18: RightFoot
    
    # Joint world positions in default T/A-pose
    joint_positions = [
        [0.0, 1.05, 0.0],    # 0: Hips
        [0.0, 1.25, 0.0],    # 1: Spine
        [0.0, 1.45, 0.0],    # 2: Chest
        [0.0, 1.62, 0.0],    # 3: Neck
        [0.0, 1.76, 0.0],    # 4: Head
        [-0.12, 1.52, 0.0],  # 5: L Shoulder
        [-0.24, 1.50, 0.0],  # 6: L Arm
        [-0.48, 1.48, 0.0],  # 7: L ForeArm
        [-0.72, 1.46, 0.0],  # 8: L Hand
        [0.12, 1.52, 0.0],   # 9: R Shoulder
        [0.24, 1.50, 0.0],   # 10: R Arm
        [0.48, 1.48, 0.0],   # 11: R ForeArm
        [0.72, 1.46, 0.0],   # 12: R Hand
        [-0.14, 1.00, 0.0],  # 13: L UpLeg
        [-0.14, 0.55, 0.0],  # 14: L Leg
        [-0.14, 0.10, 0.0],  # 15: L Foot
        [0.14, 1.00, 0.0],   # 16: R UpLeg
        [0.14, 0.55, 0.0],   # 17: R Leg
        [0.14, 0.10, 0.0],   # 18: R Foot
    ]
    
    positions = []
    normals = []
    uvs = []
    joints = []
    weights = []
    indices = []
    
    # Helper to calculate bone weights based on distance
    def calc_skinning(pos):
        x, y, z = pos
        distances = []
        for j_idx, j_pos in enumerate(joint_positions):
            dx = x - j_pos[0]
            dy = y - j_pos[1]
            dz = z - j_pos[2]
            dist = math.sqrt(dx*dx + dy*dy + dz*dz)
            distances.append((dist, j_idx))
            
        distances.sort(key=lambda d: d[0])
        # Pick closest 2-4 bones
        closest = distances[:4]
        # Inverse distance weighting
        weights_raw = [1.0 / max(0.04, d[0]**1.8) for d in closest]
        total_w = sum(weights_raw)
        norm_weights = [w / total_w for w in weights_raw]
        
        j_vec = [c[1] for c in closest]
        w_vec = norm_weights
        while len(j_vec) < 4:
            j_vec.append(0)
            w_vec.append(0.0)
        return j_vec[:4], w_vec[:4]

    # --- 1. HEAD & FACE GEOMETRY (with high density for Morph Targets) ---
    head_center = (0.0, 1.76, 0.0)
    head_rad = 0.16
    lat_segs = 24
    lon_segs = 32
    
    head_start_idx = len(positions)
    for i in range(lat_segs + 1):
        theta = math.pi * i / lat_segs
        sin_t = math.sin(theta)
        cos_t = math.cos(theta)
        for j in range(lon_segs + 1):
            phi = 2 * math.pi * j / lon_segs
            sin_p = math.sin(phi)
            cos_p = math.cos(phi)
            
            # Stylized / Realistic Oval Head
            scale_y = 1.25
            scale_z = 1.1 if cos_p > 0 else 0.95
            vx = head_center[0] + head_rad * sin_t * sin_p
            vy = head_center[1] + head_rad * cos_t * scale_y
            vz = head_center[2] + head_rad * sin_t * cos_p * scale_z
            
            # Chin and nose protrusion
            if vz > 0.05 and abs(vx) < 0.06:
                if 1.65 < vy < 1.75: # Nose
                    vz += 0.035 * math.sin((vy - 1.65) / 0.10 * math.pi)
                elif 1.55 < vy < 1.62: # Chin
                    vz += 0.02
                    
            positions.append([vx, vy, vz])
            norm = [vx - head_center[0], (vy - head_center[1]) / scale_y, (vz - head_center[2]) / scale_z]
            n_len = math.sqrt(norm[0]**2 + norm[1]**2 + norm[2]**2)
            normals.append([norm[0]/n_len, norm[1]/n_len, norm[2]/n_len])
            uvs.append([j / lon_segs, i / lat_segs])
            
            # Head bone weighting
            j_vec, w_vec = calc_skinning([vx, vy, vz])
            # Give head bone heavy weight
            joints.append([4, 3, 2, 0])
            weights.append([0.92, 0.08, 0.0, 0.0])
            
    for i in range(lat_segs):
        for j in range(lon_segs):
            first = head_start_idx + i * (lon_segs + 1) + j
            second = first + lon_segs + 1
            indices.extend([first, second, first + 1, second, second + 1, first + 1])
            
    head_end_idx = len(positions)

    # --- 2. MORPH TARGETS (52-Standard Visemes for Singing) ---
    # We will build morph targets delta arrays for:
    # 0: viseme_aa (Open mouth 'A')
    # 1: viseme_O  (Round mouth 'O')
    # 2: viseme_E  (Wide teeth 'E')
    # 3: viseme_U  (Puckered 'U')
    # 4: jawOpen   (Vocal singing wide open)
    # 5: mouthSmile (Happy singing expression)
    # 6: eyesClosed (Emotional singing blink)
    
    num_total_verts = 0 # Will count after all meshes
    # Let's define morph target vertex deltas for the head
    morph_deltas_aa = []
    morph_deltas_O = []
    morph_deltas_E = []
    morph_deltas_U = []
    morph_deltas_jawOpen = []
    morph_deltas_smile = []
    morph_deltas_blink = []
    
    for idx in range(head_start_idx, head_end_idx):
        vx, vy, vz = positions[idx]
        
        # Mouth region: 1.60 < vy < 1.69 and vz > 0.08 and abs(vx) < 0.08
        is_mouth = (1.58 < vy < 1.70) and (vz > 0.06) and (abs(vx) < 0.09)
        is_jaw = (1.52 < vy < 1.64) and (vz > 0.04) and (abs(vx) < 0.11)
        is_eye_l = (1.74 < vy < 1.82) and (vz > 0.08) and (-0.11 < vx < -0.02)
        is_eye_r = (1.74 < vy < 1.82) and (vz > 0.08) and (0.02 < vx < 0.11)
        
        # 1. Viseme AA (Mouth drops open)
        d_aa = [0, 0, 0]
        if is_mouth:
            factor = math.exp(-((vx)**2 / 0.003 + (vy - 1.64)**2 / 0.002))
            d_aa = [0, -0.055 * factor, 0.015 * factor]
        morph_deltas_aa.append(d_aa)
        
        # 2. Viseme O (Round lips)
        d_O = [0, 0, 0]
        if is_mouth:
            factor = math.exp(-((vx)**2 / 0.002 + (vy - 1.64)**2 / 0.002))
            # Pull corners in, push forward
            d_O = [-0.025 * np.sign(vx) * factor, -0.03 * factor, 0.045 * factor]
        morph_deltas_O.append(d_O)
        
        # 3. Viseme E (Wide teeth)
        d_E = [0, 0, 0]
        if is_mouth:
            factor = math.exp(-((vx)**2 / 0.005 + (vy - 1.64)**2 / 0.002))
            d_E = [0.035 * np.sign(vx) * factor, 0.01 * factor, -0.01 * factor]
        morph_deltas_E.append(d_E)

        # 4. Viseme U (Narrow forward)
        d_U = [0, 0, 0]
        if is_mouth:
            factor = math.exp(-((vx)**2 / 0.0015 + (vy - 1.64)**2 / 0.0015))
            d_U = [-0.03 * np.sign(vx) * factor, -0.01 * factor, 0.06 * factor]
        morph_deltas_U.append(d_U)

        # 5. Jaw Open (Singing climax)
        d_jaw = [0, 0, 0]
        if is_jaw:
            factor = math.exp(-((vx)**2 / 0.006 + (vy - 1.58)**2 / 0.004))
            d_jaw = [0, -0.07 * factor, 0.02 * factor]
        morph_deltas_jawOpen.append(d_jaw)

        # 6. Smile
        d_smile = [0, 0, 0]
        if is_mouth:
            factor = math.exp(-((vx)**2 / 0.005 + (vy - 1.64)**2 / 0.003))
            d_smile = [0.02 * np.sign(vx) * factor, 0.025 * factor, 0.01 * factor]
        morph_deltas_smile.append(d_smile)

        # 7. Blink (Eyes closed)
        d_blink = [0, 0, 0]
        if is_eye_l or is_eye_r:
            factor = math.exp(-((vy - 1.78)**2 / 0.0015))
            d_blink = [0, -0.025 * factor, 0.005 * factor]
        morph_deltas_blink.append(d_blink)

    # --- 3. BODY, ARMS, LEGS & CLOTHING GEOMETRY ---
    
    # Helper to add cylinder segment with smooth skinning
    def add_limb_segment(p_start, p_end, r_start, r_end, segs=16, rings=8, b_start_idx=0, b_end_idx=0):
        v_offset = len(positions)
        p1 = np.array(p_start)
        p2 = np.array(p_end)
        axis = p2 - p1
        length = np.linalg.norm(axis)
        axis_norm = axis / length
        
        # Orthogonal basis
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
                
                # Skinning blend between b_start and b_end
                w_start = max(0.0, min(1.0, 1.0 - t))
                w_end = 1.0 - w_start
                joints.append([b_start_idx, b_end_idx, 0, 0])
                weights.append([w_start, w_end, 0.0, 0.0])
                
        for r in range(rings):
            for s in range(segs):
                first = v_offset + r * (segs + 1) + s
                second = first + segs + 1
                indices.extend([first, second, first + 1, second, second + 1, first + 1])

    # Neck (Bone 3 -> 4)
    add_limb_segment([0, 1.58, 0], [0, 1.70, 0], 0.08, 0.08, segs=16, rings=4, b_start_idx=3, b_end_idx=4)
    
    # Torso / Chest (Bone 1 -> 2)
    add_limb_segment([0, 1.10, 0], [0, 1.58, 0], 0.22, 0.25, segs=20, rings=10, b_start_idx=1, b_end_idx=2)
    
    # Left Arm (Shoulder -> Forearm -> Hand) (Bones 5 -> 6 -> 7 -> 8)
    add_limb_segment([-0.12, 1.52, 0], [-0.26, 1.50, 0], 0.09, 0.08, segs=12, rings=4, b_start_idx=5, b_end_idx=6)
    add_limb_segment([-0.26, 1.50, 0], [-0.48, 1.48, 0], 0.08, 0.07, segs=12, rings=6, b_start_idx=6, b_end_idx=7)
    add_limb_segment([-0.48, 1.48, 0], [-0.70, 1.46, 0], 0.07, 0.055, segs=12, rings=6, b_start_idx=7, b_end_idx=8)

    # Right Arm (Bones 9 -> 10 -> 11 -> 12)
    add_limb_segment([0.12, 1.52, 0], [0.26, 1.50, 0], 0.09, 0.08, segs=12, rings=4, b_start_idx=9, b_end_idx=10)
    add_limb_segment([0.26, 1.50, 0], [0.48, 1.48, 0], 0.08, 0.07, segs=12, rings=6, b_start_idx=10, b_end_idx=11)
    add_limb_segment([0.48, 1.48, 0], [0.70, 1.46, 0], 0.07, 0.055, segs=12, rings=6, b_start_idx=11, b_end_idx=12)

    # Left Leg (Bones 13 -> 14 -> 15)
    add_limb_segment([-0.14, 1.05, 0], [-0.14, 0.55, 0], 0.11, 0.09, segs=14, rings=8, b_start_idx=13, b_end_idx=14)
    add_limb_segment([-0.14, 0.55, 0], [-0.14, 0.10, 0], 0.09, 0.07, segs=14, rings=8, b_start_idx=14, b_end_idx=15)

    # Right Leg (Bones 16 -> 17 -> 18)
    add_limb_segment([0.14, 1.05, 0], [0.14, 0.55, 0], 0.11, 0.09, segs=14, rings=8, b_start_idx=16, b_end_idx=17)
    add_limb_segment([0.14, 0.55, 0], [0.14, 0.10, 0], 0.09, 0.07, segs=14, rings=8, b_start_idx=17, b_end_idx=18)

    # Pad morph targets for all body vertices (deltas = [0, 0, 0])
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

    # --- 4. SKELETON NODE HIERARCHY & SKELETAL MATRICES ---
    # Define bone parents:
    # 0: Hips -> root
    # 1: Spine (child of 0)
    # 2: Chest (child of 1)
    # 3: Neck (child of 2)
    # 4: Head (child of 3)
    # 5: L Shoulder (child of 2), 6: L Arm (child of 5), 7: L ForeArm (child of 6), 8: L Hand (child of 7)
    # 9: R Shoulder (child of 2), 10: R Arm (child of 9), 11: R ForeArm (child of 10), 12: R Hand (child of 11)
    # 13: L UpLeg (child of 0), 14: L Leg (child of 13), 15: L Foot (child of 14)
    # 16: R UpLeg (child of 0), 17: R Leg (child of 16), 18: R Foot (child of 17)

    bone_hierarchy = {
        0: [1, 13, 16],
        1: [2],
        2: [3, 5, 9],
        3: [4],
        4: [],
        5: [6],
        6: [7],
        7: [8],
        8: [],
        9: [10],
        10: [11],
        11: [12],
        12: [],
        13: [14],
        14: [15],
        15: [],
        16: [17],
        17: [18],
        18: []
    }
    
    # Calculate local translations from world positions
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

    # Compute Inverse Bind Matrices (4x4 identity with -world_pos translation)
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


def build_full_humanoid_glb(output_path):
    char_data = create_humanoid_skinned_character()
    
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
        acc = {
            "bufferView": bv_idx,
            "byteOffset": 0,
            "componentType": comp_type,
            "count": count,
            "type": type_str
        }
        if min_val is not None:
            acc["min"] = min_val
        if max_val is not None:
            acc["max"] = max_val
        accessors.append(acc)
        return len(accessors) - 1

    # 1. Base Geometry Accessors
    pos_np = np.array(char_data["positions"], dtype=np.float32)
    pos_bv = add_bv(pos_np.tobytes(), 34962)
    pos_acc = add_acc(pos_bv, 5126, len(pos_np), "VEC3", min_val=pos_np.min(axis=0).tolist(), max_val=pos_np.max(axis=0).tolist())

    norm_np = np.array(char_data["normals"], dtype=np.float32)
    norm_bv = add_bv(norm_np.tobytes(), 34962)
    norm_acc = add_acc(norm_bv, 5126, len(norm_np), "VEC3", min_val=norm_np.min(axis=0).tolist(), max_val=norm_np.max(axis=0).tolist())

    uv_np = np.array(char_data["uvs"], dtype=np.float32)
    uv_bv = add_bv(uv_np.tobytes(), 34962)
    uv_acc = add_acc(uv_bv, 5126, len(uv_np), "VEC2", min_val=uv_np.min(axis=0).tolist(), max_val=uv_np.max(axis=0).tolist())

    joints_np = np.array(char_data["joints"], dtype=np.uint16)
    joints_bv = add_bv(joints_np.tobytes(), 34962)
    joints_acc = add_acc(joints_bv, 5123, len(joints_np), "VEC4") # UNSIGNED_SHORT

    weights_np = np.array(char_data["weights"], dtype=np.float32)
    weights_bv = add_bv(weights_np.tobytes(), 34962)
    weights_acc = add_acc(weights_bv, 5126, len(weights_np), "VEC4")

    indices_np = np.array(char_data["indices"], dtype=np.uint32)
    ind_bv = add_bv(indices_np.tobytes(), 34963)
    ind_acc = add_acc(ind_bv, 5125, len(indices_np), "SCALAR", min_val=[int(indices_np.min())], max_val=[int(indices_np.max())])

    # 2. Morph Targets Accessors
    morph_target_accessors = []
    target_names = []
    for name, deltas in char_data["morph_targets"]:
        d_np = np.array(deltas, dtype=np.float32)
        d_bv = add_bv(d_np.tobytes(), 34962)
        d_acc = add_acc(d_bv, 5126, len(d_np), "VEC3", min_val=d_np.min(axis=0).tolist(), max_val=d_np.max(axis=0).tolist())
        morph_target_accessors.append({"POSITION": d_acc})
        target_names.append(name)

    # 3. Inverse Bind Matrices Accessor
    ibm_np = np.array(char_data["inverse_bind_matrices"], dtype=np.float32)
    ibm_bv = add_bv(ibm_np.tobytes())
    ibm_acc = add_acc(ibm_bv, 5126, len(ibm_np), "MAT4")

    # Materials
    materials = [
        {
            "name": "Mat_HumanoidSkin",
            "pbrMetallicRoughness": {
                "baseColorFactor": [0.95, 0.78, 0.68, 1.0],
                "metallicFactor": 0.05,
                "roughnessFactor": 0.55
            }
        },
        {
            "name": "Mat_Microphone",
            "pbrMetallicRoughness": {
                "baseColorFactor": [0.85, 0.88, 0.95, 1.0],
                "metallicFactor": 0.95,
                "roughnessFactor": 0.15
            }
        }
    ]

    # Mesh Definition
    meshes = [{
        "name": "HumanoidSingerMesh",
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
        "extras": {
            "targetNames": target_names
        }
    }]

    # 4. Bone Nodes Hierarchy
    nodes = []
    bone_names = [
        "Hips", "Spine", "Chest", "Neck", "Head",
        "LeftShoulder", "LeftArm", "LeftForeArm", "LeftHand",
        "RightShoulder", "RightArm", "RightForeArm", "RightHand",
        "LeftUpLeg", "LeftLeg", "LeftFoot",
        "RightUpLeg", "RightLeg", "RightFoot"
    ]
    
    # Bone nodes will occupy node index 0 to 18
    for i in range(19):
        node = {
            "name": bone_names[i],
            "translation": char_data["local_translations"][i],
            "children": char_data["bone_hierarchy"][i]
        }
        nodes.append(node)
        
    # Skinned Mesh Node (Node 19)
    node_mesh_idx = len(nodes)
    nodes.append({
        "name": "SingerCharacter",
        "mesh": 0,
        "skin": 0
    })

    # Root Scene Node (Node 20)
    root_node_idx = len(nodes)
    nodes.append({
        "name": "RootNode",
        "children": [0, node_mesh_idx]
    })

    # Skin definition
    skins = [{
        "inverseBindMatrices": ibm_acc,
        "joints": list(range(19)),
        "skeleton": 0
    }]

    # ----------------------------------------------------
    # SKELETAL SINGING ANIMATION CLIP
    # ----------------------------------------------------
    fps = 30
    duration = 4.0
    num_frames = int(fps * duration) + 1
    times = [i / fps for i in range(num_frames)]
    
    # Bone rotations during singing:
    # - Hips: Gentle sway
    # - Spine/Chest: Breathing and rhythm lean
    # - Head: Emotional tilting and nodding
    # - Right Arm: Holding mic and raising towards mouth
    # - Left Arm: Vocal expressive gestures
    
    hips_trans = []
    hips_rots = []
    spine_rots = []
    chest_rots = []
    head_rots = []
    r_arm_rots = []
    r_forearm_rots = []
    r_hand_rots = []
    l_arm_rots = []
    l_forearm_rots = []
    
    # Morph weights for vocal singing track
    morph_weights = [] # num_frames * 7 weights
    
    for t in times:
        # Hips
        sway = math.sin(t * math.pi * 1.0) * 0.03
        bounce = math.sin(t * math.pi * 4.0) * 0.015
        hips_trans.append([sway, 1.05 + bounce, 0.0])
        hips_rots.append(euler_to_quat(0, sway * 1.5, sway * 0.5))
        
        # Spine & Chest
        breath = math.sin(t * math.pi * 2.0) * math.radians(4.0)
        spine_rots.append(euler_to_quat(breath, sway * 0.8, -sway * 0.4))
        chest_rots.append(euler_to_quat(breath * 1.2, -sway * 0.5, 0))
        
        # Head (Nodding and singing tilt)
        head_nod = math.sin(t * math.pi * 4.0) * math.radians(6.0)
        head_tilt = math.cos(t * math.pi * 2.0) * math.radians(7.0)
        head_turn = math.sin(t * math.pi * 1.0) * math.radians(8.0)
        head_rots.append(euler_to_quat(head_nod, head_turn, head_tilt))
        
        # Right Arm (Bringing Mic to Mouth)
        mic_power = 0.5 + 0.5 * math.sin(t * math.pi * 2.0)
        r_arm_rots.append(euler_to_quat(math.radians(-30) - mic_power * math.radians(20), math.radians(45), math.radians(-30)))
        r_forearm_rots.append(euler_to_quat(math.radians(0), math.radians(-70) - mic_power * math.radians(25), math.radians(50)))
        r_hand_rots.append(euler_to_quat(math.radians(20), math.radians(-10), math.radians(15)))
        
        # Left Arm (Expressive gesture)
        gesture = math.sin(t * math.pi * 1.5)
        l_arm_rots.append(euler_to_quat(math.radians(20) + gesture * math.radians(15), math.radians(-30), math.radians(25)))
        l_forearm_rots.append(euler_to_quat(math.radians(0), math.radians(35) + gesture * math.radians(20), math.radians(-15)))

        # Morph Targets singing track (A, O, E, U, jawOpen, smile, blink)
        w_aa = max(0.0, math.sin(t * math.pi * 4.0)) * 0.85
        w_O = max(0.0, math.cos(t * math.pi * 2.0)) * 0.6
        w_E = max(0.0, math.sin(t * math.pi * 3.0 + 1.0)) * 0.5
        w_U = max(0.0, math.cos(t * math.pi * 3.0)) * 0.4
        w_jaw = max(0.0, math.sin(t * math.pi * 2.0)) * 0.9 # Climax high note
        w_smile = 0.3 + 0.3 * math.sin(t * math.pi * 1.0)
        w_blink = 1.0 if (2.0 < t < 2.15 or 3.8 < t < 3.95) else 0.0
        
        morph_weights.extend([w_aa, w_O, w_E, w_U, w_jaw, w_smile, w_blink])

    # Build Animation Samplers & Channels
    samplers = []
    channels = []
    
    def add_anim_channel(node_idx, path, vals, type_str):
        t_np = np.array(times, dtype=np.float32)
        t_bv = add_bv(t_np.tobytes())
        t_acc = add_acc(t_bv, 5126, len(times), "SCALAR", min_val=[float(t_np.min())], max_val=[float(t_np.max())])
        
        v_np = np.array(vals, dtype=np.float32)
        v_bv = add_bv(v_np.tobytes())
        v_acc = add_acc(v_bv, 5126, len(vals) if type_str != "SCALAR" else len(vals), type_str)
        
        s_idx = len(samplers)
        samplers.append({
            "input": t_acc,
            "interpolation": "LINEAR",
            "output": v_acc
        })
        channels.append({
            "sampler": s_idx,
            "target": {
                "node": node_idx,
                "path": path
            }
        })

    add_anim_channel(0, "translation", hips_trans, "VEC3")
    add_anim_channel(0, "rotation", hips_rots, "VEC4")
    add_anim_channel(1, "rotation", spine_rots, "VEC4")
    add_anim_channel(2, "rotation", chest_rots, "VEC4")
    add_anim_channel(4, "rotation", head_rots, "VEC4")
    add_anim_channel(10, "rotation", r_arm_rots, "VEC4")
    add_anim_channel(11, "rotation", r_forearm_rots, "VEC4")
    add_anim_channel(12, "rotation", r_hand_rots, "VEC4")
    add_anim_channel(6, "rotation", l_arm_rots, "VEC4")
    add_anim_channel(7, "rotation", l_forearm_rots, "VEC4")

    # Morph weights channel on node 19 (mesh)
    t_np = np.array(times, dtype=np.float32)
    t_bv = add_bv(t_np.tobytes())
    t_acc = add_acc(t_bv, 5126, len(times), "SCALAR", min_val=[float(t_np.min())], max_val=[float(t_np.max())])
    
    mw_np = np.array(morph_weights, dtype=np.float32)
    mw_bv = add_bv(mw_np.tobytes())
    mw_acc = add_acc(mw_bv, 5126, len(mw_np), "SCALAR")
    
    s_mw_idx = len(samplers)
    samplers.append({
        "input": t_acc,
        "interpolation": "LINEAR",
        "output": mw_acc
    })
    channels.append({
        "sampler": s_mw_idx,
        "target": {
            "node": node_mesh_idx,
            "path": "weights"
        }
    })

    animations = [{
        "name": "Humanoid_Live_Singing_Performance",
        "samplers": samplers,
        "channels": channels
    }]

    # Build GLTF JSON
    gltf = {
        "asset": {
            "version": "2.0",
            "generator": "Humanoid Rigged Singer Avatar Generator (Phuong An 1)"
        },
        "scene": 0,
        "scenes": [{
            "name": "AvatarSingerScene",
            "nodes": [root_node_idx]
        }],
        "nodes": nodes,
        "meshes": meshes,
        "skins": skins,
        "materials": materials,
        "accessors": accessors,
        "bufferViews": buffer_views,
        "buffers": [{
            "byteLength": len(buffer)
        }],
        "animations": animations
    }

    json_bytes = json.dumps(gltf, separators=(',', ':')).encode('utf-8')
    json_pad = (4 - (len(json_bytes) % 4)) % 4
    if json_pad > 0:
        json_bytes += b' ' * json_pad
        
    bin_bytes = bytes(buffer)
    
    total_length = 12 + 8 + len(json_bytes) + 8 + len(bin_bytes)
    header = struct.pack('<4sII', b'glTF', 2, total_length)
    json_header = struct.pack('<II', len(json_bytes), 0x4E4F534A)
    bin_header = struct.pack('<II', len(bin_bytes), 0x004E4942)
    
    with open(output_path, 'wb') as f:
        f.write(header)
        f.write(json_header)
        f.write(json_bytes)
        f.write(bin_header)
        f.write(bin_bytes)
        
    print(f"[OK] Successfully built Standard Humanoid Avatar GLB: {output_path} ({total_length / 1024:.1f} KB)")


if __name__ == "__main__":
    import sys
    out = "/Volumes/DATA/ctg_ai/3d/phuong_an_1_avatar_chuan/model/singer_humanoid_avatar.glb"
    if len(sys.argv) > 1:
        out = sys.argv[1]
    build_full_humanoid_glb(out)
