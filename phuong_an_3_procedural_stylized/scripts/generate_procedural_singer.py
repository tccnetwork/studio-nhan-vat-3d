#!/usr/bin/env python3
"""
Procedural 3D Cyber Singer Generator
Generates a stylized 3D pop/cyber singer with microphone, stage, materials,
and hierarchical singing animations directly into a GLB (GLTF 2.0) file.
"""

import math
import struct
import json
import numpy as np

def create_cube_mesh(dx, dy, dz, center=(0, 0, 0)):
    cx, cy, cz = center
    hx, hy, hz = dx / 2, dy / 2, dz / 2
    positions = []
    normals = []
    uvs = []
    indices = []
    
    faces = [
        # Front (+Z)
        ([(-hx, -hy, hz), (hx, -hy, hz), (hx, hy, hz), (-hx, hy, hz)], (0, 0, 1)),
        # Back (-Z)
        ([(hx, -hy, -hz), (-hx, -hy, -hz), (-hx, hy, -hz), (hx, hy, -hz)], (0, 0, -1)),
        # Top (+Y)
        ([(-hx, hy, hz), (hx, hy, hz), (hx, hy, -hz), (-hx, hy, -hz)], (0, 1, 0)),
        # Bottom (-Y)
        ([(-hx, -hy, -hz), (hx, -hy, -hz), (hx, -hy, hz), (-hx, -hy, hz)], (0, -1, 0)),
        # Right (+X)
        ([(hx, -hy, hz), (hx, -hy, -hz), (hx, hy, -hz), (hx, hy, hz)], (1, 0, 0)),
        # Left (-X)
        ([(-hx, -hy, -hz), (-hx, -hy, hz), (-hx, hy, hz), (-hx, hy, -hz)], (-1, 0, 0)),
    ]
    
    for quad, norm in faces:
        base_idx = len(positions)
        for (vx, vy, vz), (u, v) in zip(quad, [(0, 0), (1, 0), (1, 1), (0, 1)]):
            positions.append([vx + cx, vy + cy, vz + cz])
            normals.append(list(norm))
            uvs.append([u, v])
        indices.extend([base_idx, base_idx + 1, base_idx + 2, base_idx, base_idx + 2, base_idx + 3])
        
    return positions, normals, uvs, indices

def create_cylinder_mesh(r_bottom, r_top, height, segments=24, center=(0, 0, 0)):
    cx, cy, cz = center
    positions = []
    normals = []
    uvs = []
    indices = []
    
    hh = height / 2
    for s in range(segments + 1):
        theta = 2.0 * math.pi * s / segments
        cos_t = math.cos(theta)
        sin_t = math.sin(theta)
        u = s / segments
        
        positions.append([cx + r_bottom * cos_t, cy - hh, cz + r_bottom * sin_t])
        normals.append([cos_t, 0.0, sin_t])
        uvs.append([u, 0.0])
        # Top vertex
        positions.append([cx + r_top * cos_t, cy + hh, cz + r_top * sin_t])
        normals.append([cos_t, 0.0, sin_t])
        uvs.append([u, 1.0])
        
    for s in range(segments):
        b1 = 2 * s
        t1 = 2 * s + 1
        b2 = 2 * (s + 1)
        t2 = 2 * (s + 1) + 1
        indices.extend([b1, b2, t1, t1, b2, t2])
        
    top_center_idx = len(positions)
    positions.append([cx, cy + hh, cz])
    normals.append([0.0, 1.0, 0.0])
    uvs.append([0.5, 0.5])
    for s in range(segments + 1):
        theta = 2.0 * math.pi * s / segments
        cos_t = math.cos(theta)
        sin_t = math.sin(theta)
        positions.append([cx + r_top * cos_t, cy + hh, cz + r_top * sin_t])
        normals.append([0.0, 1.0, 0.0])
        uvs.append([0.5 + 0.5 * cos_t, 0.5 + 0.5 * sin_t])
    for s in range(segments):
        idx = top_center_idx + 1 + s
        indices.extend([top_center_idx, idx, idx + 1])
        
    bot_center_idx = len(positions)
    positions.append([cx, cy - hh, cz])
    normals.append([0.0, -1.0, 0.0])
    uvs.append([0.5, 0.5])
    for s in range(segments + 1):
        theta = 2.0 * math.pi * s / segments
        cos_t = math.cos(theta)
        sin_t = math.sin(theta)
        positions.append([cx + r_bottom * cos_t, cy - hh, cz + r_bottom * sin_t])
        normals.append([0.0, -1.0, 0.0])
        uvs.append([0.5 + 0.5 * cos_t, 0.5 + 0.5 * sin_t])
    for s in range(segments):
        idx = bot_center_idx + 1 + s
        indices.extend([bot_center_idx, idx + 1, idx])
        
    return positions, normals, uvs, indices

def create_sphere_mesh(radius, lat_segments=16, lon_segments=24, center=(0, 0, 0)):
    cx, cy, cz = center
    positions = []
    normals = []
    uvs = []
    indices = []
    
    for i in range(lat_segments + 1):
        theta = math.pi * i / lat_segments
        sin_t = math.sin(theta)
        cos_t = math.cos(theta)
        
        for j in range(lon_segments + 1):
            phi = 2 * math.pi * j / lon_segments
            sin_p = math.sin(phi)
            cos_p = math.cos(phi)
            
            x = cos_p * sin_t
            y = cos_t
            z = sin_p * sin_t
            
            positions.append([cx + radius * x, cy + radius * y, cz + radius * z])
            normals.append([x, y, z])
            uvs.append([j / lon_segments, i / lat_segments])
            
    for i in range(lat_segments):
        for j in range(lon_segments):
            first = i * (lon_segments + 1) + j
            second = first + lon_segments + 1
            indices.extend([first, second, first + 1, second, second + 1, first + 1])
            
    return positions, normals, uvs, indices

def create_torus_mesh(r_major, r_minor, seg_major=24, seg_minor=12, center=(0, 0, 0), arc=math.pi):
    cx, cy, cz = center
    positions = []
    normals = []
    uvs = []
    indices = []
    
    for i in range(seg_major + 1):
        u = i / seg_major
        theta = arc * u
        cos_t = math.cos(theta)
        sin_t = math.sin(theta)
        
        for j in range(seg_minor + 1):
            v = j / seg_minor
            phi = 2 * math.pi * v
            cos_p = math.cos(phi)
            sin_p = math.sin(phi)
            
            x = (r_major + r_minor * cos_p) * cos_t
            y = (r_major + r_minor * cos_p) * sin_t
            z = r_minor * sin_p
            
            nx = cos_p * cos_t
            ny = cos_p * sin_t
            nz = sin_p
            
            positions.append([cx + x, cy + y, cz + z])
            normals.append([nx, ny, nz])
            uvs.append([u, v])
            
    for i in range(seg_major):
        for j in range(seg_minor):
            first = i * (seg_minor + 1) + j
            second = first + seg_minor + 1
            indices.extend([first, second, first + 1, second, second + 1, first + 1])
            
    return positions, normals, uvs, indices

def combine_meshes(mesh_list):
    all_pos = []
    all_norm = []
    all_uvs = []
    all_indices = []
    
    for pos, norm, uvs, inds in mesh_list:
        offset = len(all_pos)
        all_pos.extend(pos)
        all_norm.extend(norm)
        all_uvs.extend(uvs)
        all_indices.extend([idx + offset for idx in inds])
        
    return all_pos, all_norm, all_uvs, all_indices


class GLBBuilder:
    def __init__(self):
        self.buffer = bytearray()
        self.buffer_views = []
        self.accessors = []
        self.meshes = []
        self.nodes = []
        self.materials = []
        self.animations = []
        
    def add_buffer_view(self, data, target=None):
        offset = len(self.buffer)
        self.buffer.extend(data)
        pad = (4 - (len(self.buffer) % 4)) % 4
        if pad > 0:
            self.buffer.extend(b'\x00' * pad)
            
        bv = {
            "buffer": 0,
            "byteOffset": offset,
            "byteLength": len(data),
        }
        if target:
            bv["target"] = target
        self.buffer_views.append(bv)
        return len(self.buffer_views) - 1

    def add_accessor(self, buffer_view_idx, component_type, count, type_str, min_val=None, max_val=None):
        acc = {
            "bufferView": buffer_view_idx,
            "byteOffset": 0,
            "componentType": component_type,
            "count": count,
            "type": type_str
        }
        if min_val is not None:
            acc["min"] = min_val
        if max_val is not None:
            acc["max"] = max_val
        self.accessors.append(acc)
        return len(self.accessors) - 1

    def add_material(self, name, base_color=(1, 1, 1, 1), metallic=0.1, roughness=0.5, emissive=(0, 0, 0)):
        mat = {
            "name": name,
            "pbrMetallicRoughness": {
                "baseColorFactor": list(base_color),
                "metallicFactor": float(metallic),
                "roughnessFactor": float(roughness)
            }
        }
        if any(e > 0 for e in emissive):
            mat["emissiveFactor"] = list(emissive)
        self.materials.append(mat)
        return len(self.materials) - 1

    def add_mesh_primitive(self, positions, normals, uvs, indices, material_idx, name="Mesh"):
        pos_np = np.array(positions, dtype=np.float32)
        pos_bytes = pos_np.tobytes()
        pos_bv = self.add_buffer_view(pos_bytes, 34962)
        pos_acc = self.add_accessor(
            pos_bv, 5126, len(positions), "VEC3",
            min_val=pos_np.min(axis=0).tolist(),
            max_val=pos_np.max(axis=0).tolist()
        )
        
        norm_np = np.array(normals, dtype=np.float32)
        norm_bytes = norm_np.tobytes()
        norm_bv = self.add_buffer_view(norm_bytes, 34962)
        norm_acc = self.add_accessor(
            norm_bv, 5126, len(normals), "VEC3",
            min_val=norm_np.min(axis=0).tolist(),
            max_val=norm_np.max(axis=0).tolist()
        )
        
        uv_np = np.array(uvs, dtype=np.float32)
        uv_bytes = uv_np.tobytes()
        uv_bv = self.add_buffer_view(uv_bytes, 34962)
        uv_acc = self.add_accessor(
            uv_bv, 5126, len(uvs), "VEC2",
            min_val=uv_np.min(axis=0).tolist(),
            max_val=uv_np.max(axis=0).tolist()
        )
        
        ind_np = np.array(indices, dtype=np.uint32)
        ind_bytes = ind_np.tobytes()
        ind_bv = self.add_buffer_view(ind_bytes, 34963)
        ind_acc = self.add_accessor(
            ind_bv, 5125, len(indices), "SCALAR",
            min_val=[int(ind_np.min())],
            max_val=[int(ind_np.max())]
        )
        
        mesh_idx = len(self.meshes)
        self.meshes.append({
            "name": name,
            "primitives": [{
                "attributes": {
                    "POSITION": pos_acc,
                    "NORMAL": norm_acc,
                    "TEXCOORD_0": uv_acc
                },
                "indices": ind_acc,
                "material": material_idx,
                "mode": 4
            }]
        })
        return mesh_idx

    def add_node(self, name, mesh_idx=None, children=None, translation=None, rotation=None, scale=None):
        node = {"name": name}
        if mesh_idx is not None:
            node["mesh"] = mesh_idx
        if children:
            node["children"] = children
        if translation:
            node["translation"] = list(translation)
        if rotation:
            node["rotation"] = list(rotation)
        if scale:
            node["scale"] = list(scale)
        self.nodes.append(node)
        return len(self.nodes) - 1

    def add_animation(self, name, samplers_data, channels_data):
        samplers = []
        for times, values, interp, out_type in samplers_data:
            t_np = np.array(times, dtype=np.float32)
            t_bv = self.add_buffer_view(t_np.tobytes())
            t_acc = self.add_accessor(t_bv, 5126, len(times), "SCALAR", min_val=[float(t_np.min())], max_val=[float(t_np.max())])
            
            v_np = np.array(values, dtype=np.float32)
            v_bv = self.add_buffer_view(v_np.tobytes())
            v_acc = self.add_accessor(v_bv, 5126, len(values), out_type)
            
            samplers.append({
                "input": t_acc,
                "interpolation": interp,
                "output": v_acc
            })
            
        channels = []
        for s_idx, target_node, path in channels_data:
            channels.append({
                "sampler": s_idx,
                "target": {
                    "node": target_node,
                    "path": path
                }
            })
            
        self.animations.append({
            "name": name,
            "samplers": samplers,
            "channels": channels
        })

    def build_glb(self, output_path):
        gltf = {
            "asset": {
                "version": "2.0",
                "generator": "Procedural Cyber Singer 3D Generator"
            },
            "scene": 0,
            "scenes": [{
                "name": "ConcertScene",
                "nodes": [i for i, n in enumerate(self.nodes) if not any(i in (parent.get("children") or []) for parent in self.nodes)]
            }],
            "nodes": self.nodes,
            "meshes": self.meshes,
            "materials": self.materials,
            "accessors": self.accessors,
            "bufferViews": self.buffer_views,
            "buffers": [{
                "byteLength": len(self.buffer)
            }]
        }
        if self.animations:
            gltf["animations"] = self.animations

        json_bytes = json.dumps(gltf, separators=(',', ':')).encode('utf-8')
        json_pad = (4 - (len(json_bytes) % 4)) % 4
        if json_pad > 0:
            json_bytes += b' ' * json_pad
            
        bin_bytes = bytes(self.buffer)
        
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
            
        print(f"[OK] Exported GLB to: {output_path} ({total_length / 1024:.1f} KB)")


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


def generate_singer_glb(output_file):
    glb = GLBBuilder()
    
    # ----------------------------------------------------
    # MATERIALS
    # ----------------------------------------------------
    mat_skin = glb.add_material("Mat_Skin", base_color=(1.0, 0.82, 0.72, 1.0), roughness=0.6, metallic=0.0)
    mat_hair = glb.add_material("Mat_Hair", base_color=(0.12, 0.12, 0.16, 1.0), roughness=0.3, metallic=0.2)
    mat_jacket = glb.add_material("Mat_Jacket", base_color=(0.20, 0.35, 0.85, 1.0), roughness=0.4, metallic=0.2)
    mat_shirt = glb.add_material("Mat_Shirt", base_color=(0.95, 0.95, 0.95, 1.0), roughness=0.8, metallic=0.0)
    mat_pants = glb.add_material("Mat_Pants", base_color=(0.15, 0.16, 0.20, 1.0), roughness=0.7, metallic=0.1)
    mat_shoes_white = glb.add_material("Mat_ShoesWhite", base_color=(0.95, 0.95, 0.98, 1.0), roughness=0.3, metallic=0.1)
    mat_shoes_coral = glb.add_material("Mat_ShoesCoral", base_color=(1.0, 0.3, 0.45, 1.0), roughness=0.4, metallic=0.2)
    mat_chrome = glb.add_material("Mat_Chrome", base_color=(0.85, 0.88, 0.92, 1.0), roughness=0.15, metallic=0.95)
    mat_mic_body = glb.add_material("Mat_MicBody", base_color=(0.18, 0.20, 0.24, 1.0), roughness=0.35, metallic=0.8)
    mat_neon_cyan = glb.add_material("Mat_NeonCyan", base_color=(0.0, 0.9, 1.0, 1.0), roughness=0.2, metallic=0.1, emissive=(0.0, 0.8, 1.0))
    mat_neon_magenta = glb.add_material("Mat_NeonMagenta", base_color=(1.0, 0.1, 0.7, 1.0), roughness=0.2, metallic=0.1, emissive=(1.0, 0.1, 0.7))
    mat_stage = glb.add_material("Mat_Stage", base_color=(0.08, 0.09, 0.12, 1.0), roughness=0.25, metallic=0.8)
    mat_stage_glow = glb.add_material("Mat_StageGlow", base_color=(0.0, 0.9, 1.0, 1.0), roughness=0.1, metallic=0.0, emissive=(0.0, 0.75, 1.0))

    # ----------------------------------------------------
    # MESHES
    # ----------------------------------------------------
    stage_mesh_parts = [
        create_cylinder_mesh(1.6, 1.5, 0.12, segments=36, center=(0, 0.06, 0)),
        create_cylinder_mesh(1.65, 1.62, 0.04, segments=36, center=(0, 0.02, 0))
    ]
    m_stage = glb.add_mesh_primitive(*combine_meshes(stage_mesh_parts), mat_stage, name="StageBase")
    m_stage_glow = glb.add_mesh_primitive(*create_cylinder_mesh(1.52, 1.51, 0.03, segments=36, center=(0, 0.125, 0)), mat_stage_glow, name="StageGlow")
    
    torso_parts = [
        create_cube_mesh(0.48, 0.44, 0.28, center=(0, 0.22, 0)),
        create_cylinder_mesh(0.16, 0.18, 0.12, segments=16, center=(0, 0.45, 0)),
        create_cube_mesh(0.20, 0.30, 0.04, center=(0, 0.24, 0.13))
    ]
    m_torso = glb.add_mesh_primitive(*combine_meshes(torso_parts), mat_jacket, name="TorsoJacket")
    
    head_parts_skin = [
        create_sphere_mesh(0.24, lat_segments=16, lon_segments=20, center=(0, 0.22, 0)),
        create_sphere_mesh(0.035, lat_segments=8, lon_segments=8, center=(0, 0.19, 0.235)),
        create_cube_mesh(0.08, 0.04, 0.03, center=(0, 0.13, 0.22))
    ]
    m_head_skin = glb.add_mesh_primitive(*combine_meshes(head_parts_skin), mat_skin, name="HeadSkin")
    
    eyes_parts = [
        create_sphere_mesh(0.045, lat_segments=8, lon_segments=12, center=(-0.08, 0.22, 0.215)),
        create_sphere_mesh(0.045, lat_segments=8, lon_segments=12, center=(0.08, 0.22, 0.215)),
        create_cube_mesh(0.07, 0.015, 0.02, center=(-0.08, 0.28, 0.22)),
        create_cube_mesh(0.07, 0.015, 0.02, center=(0.08, 0.28, 0.22))
    ]
    m_eyes = glb.add_mesh_primitive(*combine_meshes(eyes_parts), mat_neon_cyan, name="HeadEyes")

    hair_parts = [
        create_sphere_mesh(0.26, lat_segments=12, lon_segments=16, center=(0, 0.26, -0.02)),
        create_cube_mesh(0.28, 0.04, 0.24, center=(0, 0.32, -0.18)),
        create_cylinder_mesh(0.06, 0.02, 0.24, segments=8, center=(-0.21, 0.18, 0.04)),
        create_cylinder_mesh(0.06, 0.02, 0.24, segments=8, center=(0.21, 0.18, 0.04))
    ]
    m_hair = glb.add_mesh_primitive(*combine_meshes(hair_parts), mat_hair, name="HairCap")

    headphone_band = create_torus_mesh(0.26, 0.025, seg_major=24, seg_minor=10, center=(0, 0.24, 0), arc=math.pi)
    m_hp_band = glb.add_mesh_primitive(*headphone_band, mat_chrome, name="HeadphoneBand")
    
    hp_cups_parts = [
        create_cylinder_mesh(0.08, 0.08, 0.06, segments=16, center=(-0.25, 0.22, 0)),
        create_cylinder_mesh(0.08, 0.08, 0.06, segments=16, center=(0.25, 0.22, 0))
    ]
    m_hp_cups = glb.add_mesh_primitive(*combine_meshes(hp_cups_parts), mat_hair, name="HeadphoneCups")
    
    hp_rings_parts = [
        create_cylinder_mesh(0.085, 0.085, 0.015, segments=16, center=(-0.27, 0.22, 0)),
        create_cylinder_mesh(0.085, 0.085, 0.015, segments=16, center=(0.27, 0.22, 0))
    ]
    m_hp_rings = glb.add_mesh_primitive(*combine_meshes(hp_rings_parts), mat_neon_magenta, name="HeadphoneNeonRings")

    m_upper_arm_l = glb.add_mesh_primitive(*create_cylinder_mesh(0.07, 0.06, 0.30, segments=12, center=(0, -0.15, 0)), mat_jacket, name="UpperArmL")
    m_upper_arm_r = glb.add_mesh_primitive(*create_cylinder_mesh(0.07, 0.06, 0.30, segments=12, center=(0, -0.15, 0)), mat_jacket, name="UpperArmR")
    
    m_forearm_l = glb.add_mesh_primitive(*create_cylinder_mesh(0.06, 0.05, 0.28, segments=12, center=(0, -0.14, 0)), mat_jacket, name="ForearmL")
    m_forearm_r = glb.add_mesh_primitive(*create_cylinder_mesh(0.06, 0.05, 0.28, segments=12, center=(0, -0.14, 0)), mat_jacket, name="ForearmR")
    
    hand_l_parts = [
        create_sphere_mesh(0.055, lat_segments=8, lon_segments=10, center=(0, -0.04, 0)),
        create_cylinder_mesh(0.018, 0.014, 0.09, segments=6, center=(-0.03, -0.07, 0.02)),
        create_cylinder_mesh(0.016, 0.012, 0.10, segments=6, center=(0.0, -0.09, 0.02)),
        create_cylinder_mesh(0.016, 0.012, 0.09, segments=6, center=(0.03, -0.08, 0.01))
    ]
    m_hand_l = glb.add_mesh_primitive(*combine_meshes(hand_l_parts), mat_skin, name="HandL")

    hand_r_parts = [
        create_sphere_mesh(0.06, lat_segments=8, lon_segments=10, center=(0, 0, 0)),
        create_cylinder_mesh(0.02, 0.02, 0.12, segments=8, center=(0.04, 0, 0.04))
    ]
    m_hand_r = glb.add_mesh_primitive(*combine_meshes(hand_r_parts), mat_skin, name="HandR")

    mic_grille_mesh = create_sphere_mesh(0.045, lat_segments=12, lon_segments=16, center=(0, 0.16, 0))
    m_mic_grille = glb.add_mesh_primitive(*mic_grille_mesh, mat_chrome, name="MicGrille")
    
    mic_body_parts = [
        create_cylinder_mesh(0.028, 0.042, 0.04, segments=16, center=(0, 0.11, 0)),
        create_cylinder_mesh(0.022, 0.026, 0.18, segments=16, center=(0, 0.0, 0)),
        create_cylinder_mesh(0.024, 0.022, 0.04, segments=16, center=(0, -0.11, 0))
    ]
    m_mic_body = glb.add_mesh_primitive(*combine_meshes(mic_body_parts), mat_mic_body, name="MicBody")
    
    m_mic_neon = glb.add_mesh_primitive(*create_cylinder_mesh(0.027, 0.027, 0.015, segments=16, center=(0, 0.08, 0)), mat_neon_cyan, name="MicNeonRing")

    m_pelvis = glb.add_mesh_primitive(*create_cube_mesh(0.44, 0.20, 0.26, center=(0, -0.05, 0)), mat_pants, name="Pelvis")
    
    m_thigh_l = glb.add_mesh_primitive(*create_cylinder_mesh(0.09, 0.075, 0.42, segments=12, center=(0, -0.21, 0)), mat_pants, name="ThighL")
    m_thigh_r = glb.add_mesh_primitive(*create_cylinder_mesh(0.09, 0.075, 0.42, segments=12, center=(0, -0.21, 0)), mat_pants, name="ThighR")
    
    m_calf_l = glb.add_mesh_primitive(*create_cylinder_mesh(0.075, 0.065, 0.40, segments=12, center=(0, -0.20, 0)), mat_pants, name="CalfL")
    m_calf_r = glb.add_mesh_primitive(*create_cylinder_mesh(0.075, 0.065, 0.40, segments=12, center=(0, -0.20, 0)), mat_pants, name="CalfR")
    
    shoe_parts_white = [
        create_cube_mesh(0.13, 0.05, 0.26, center=(0, 0.025, 0.04)),
        create_sphere_mesh(0.065, lat_segments=8, lon_segments=10, center=(0, 0.04, 0.14))
    ]
    shoe_parts_coral = [
        create_cube_mesh(0.12, 0.11, 0.22, center=(0, 0.09, 0.02)),
        create_cylinder_mesh(0.075, 0.075, 0.08, segments=12, center=(0, 0.16, -0.01))
    ]
    m_shoe_white_l = glb.add_mesh_primitive(*combine_meshes(shoe_parts_white), mat_shoes_white, name="ShoeWhiteL")
    m_shoe_coral_l = glb.add_mesh_primitive(*combine_meshes(shoe_parts_coral), mat_shoes_coral, name="ShoeCoralL")
    m_shoe_white_r = glb.add_mesh_primitive(*combine_meshes(shoe_parts_white), mat_shoes_white, name="ShoeWhiteR")
    m_shoe_coral_r = glb.add_mesh_primitive(*combine_meshes(shoe_parts_coral), mat_shoes_coral, name="ShoeCoralR")

    # ----------------------------------------------------
    # SCENE HIERARCHY / NODES
    # ----------------------------------------------------
    n_mic_grille = glb.add_node("MicGrilleNode", mesh_idx=m_mic_grille)
    n_mic_body = glb.add_node("MicBodyNode", mesh_idx=m_mic_body)
    n_mic_neon = glb.add_node("MicNeonNode", mesh_idx=m_mic_neon)
    n_mic_root = glb.add_node("Microphone", children=[n_mic_grille, n_mic_body, n_mic_neon], 
                             translation=[0.05, 0.12, 0.10], rotation=euler_to_quat(math.radians(-30), math.radians(20), math.radians(-15)))

    n_hand_r = glb.add_node("Hand_R", mesh_idx=m_hand_r, children=[n_mic_root], translation=[0, -0.30, 0])
    n_forearm_r = glb.add_node("Forearm_R", mesh_idx=m_forearm_r, children=[n_hand_r], translation=[0, -0.30, 0],
                               rotation=euler_to_quat(math.radians(-75), math.radians(-35), math.radians(20)))
    n_arm_r = glb.add_node("UpperArm_R", mesh_idx=m_upper_arm_r, children=[n_forearm_r], translation=[0.30, 0.38, 0.0],
                           rotation=euler_to_quat(math.radians(25), math.radians(-15), math.radians(-30)))

    n_hand_l = glb.add_node("Hand_L", mesh_idx=m_hand_l, translation=[0, -0.30, 0])
    n_forearm_l = glb.add_node("Forearm_L", mesh_idx=m_forearm_l, children=[n_hand_l], translation=[0, -0.30, 0],
                               rotation=euler_to_quat(math.radians(-45), math.radians(30), math.radians(-20)))
    n_arm_l = glb.add_node("UpperArm_L", mesh_idx=m_upper_arm_l, children=[n_forearm_l], translation=[-0.30, 0.38, 0.0],
                           rotation=euler_to_quat(math.radians(15), math.radians(20), math.radians(35)))

    n_hp_band = glb.add_node("HPBandNode", mesh_idx=m_hp_band)
    n_hp_cups = glb.add_node("HPCupsNode", mesh_idx=m_hp_cups)
    n_hp_rings = glb.add_node("HPRingsNode", mesh_idx=m_hp_rings)
    n_hair = glb.add_node("HairNode", mesh_idx=m_hair)
    n_eyes = glb.add_node("EyesNode", mesh_idx=m_eyes)
    n_head_mesh = glb.add_node("HeadMeshNode", mesh_idx=m_head_skin)
    
    n_head = glb.add_node("Head", children=[n_head_mesh, n_eyes, n_hair, n_hp_band, n_hp_cups, n_hp_rings],
                          translation=[0, 0.50, 0])

    n_torso = glb.add_node("Torso", mesh_idx=m_torso, children=[n_head, n_arm_l, n_arm_r], translation=[0, 0.15, 0])

    n_shoe_l = glb.add_node("Shoe_L", children=[
        glb.add_node("SW_L", mesh_idx=m_shoe_white_l),
        glb.add_node("SC_L", mesh_idx=m_shoe_coral_l)
    ], translation=[0, -0.40, 0.02])
    n_calf_l = glb.add_node("Calf_L", mesh_idx=m_calf_l, children=[n_shoe_l], translation=[0, -0.42, 0])
    n_thigh_l = glb.add_node("Thigh_L", mesh_idx=m_thigh_l, children=[n_calf_l], translation=[-0.14, -0.10, 0])

    n_shoe_r = glb.add_node("Shoe_R", children=[
        glb.add_node("SW_R", mesh_idx=m_shoe_white_r),
        glb.add_node("SC_R", mesh_idx=m_shoe_coral_r)
    ], translation=[0, -0.40, 0.02])
    n_calf_r = glb.add_node("Calf_R", mesh_idx=m_calf_r, children=[n_shoe_r], translation=[0, -0.42, 0])
    n_thigh_r = glb.add_node("Thigh_R", mesh_idx=m_thigh_r, children=[n_calf_r], translation=[0.14, -0.10, 0])

    n_pelvis = glb.add_node("Pelvis", mesh_idx=m_pelvis, children=[n_thigh_l, n_thigh_r])
    n_char_root = glb.add_node("CharacterRoot", children=[n_pelvis, n_torso], translation=[0, 1.05, 0])

    n_stage_mesh = glb.add_node("StageMesh", mesh_idx=m_stage)
    n_stage_glow_node = glb.add_node("StageGlowMesh", mesh_idx=m_stage_glow)
    n_stage_root = glb.add_node("Stage", children=[n_stage_mesh, n_stage_glow_node])

    glb.add_node("WorldRoot", children=[n_stage_root, n_char_root])

    # ----------------------------------------------------
    # ANIMATION: "Singing_Performance_VocalLoop"
    # ----------------------------------------------------
    fps = 30
    duration = 4.0
    num_frames = int(fps * duration) + 1
    times = [i / fps for i in range(num_frames)]
    
    root_translations = []
    root_rotations = []
    for t in times:
        bounce = math.sin(t * math.pi * 4.0) * 0.025
        sway_x = math.sin(t * math.pi * 1.0) * 0.04
        root_translations.append([sway_x, 1.05 + bounce, 0.0])
        hip_yaw = math.sin(t * math.pi * 1.0) * 0.08
        hip_roll = math.cos(t * math.pi * 1.0) * 0.04
        root_rotations.append(euler_to_quat(0, hip_yaw, hip_roll))
        
    torso_rotations = []
    for t in times:
        pitch = math.sin(t * math.pi * 2.0) * math.radians(6.0) - math.radians(2.0)
        yaw = -math.sin(t * math.pi * 1.0) * math.radians(5.0)
        roll = -math.cos(t * math.pi * 1.0) * math.radians(3.0)
        torso_rotations.append(euler_to_quat(pitch, yaw, roll))
        
    head_rotations = []
    for t in times:
        nod = math.sin(t * math.pi * 4.0) * math.radians(5.0)
        tilt = math.cos(t * math.pi * 2.0) * math.radians(8.0)
        turn = math.sin(t * math.pi * 1.0) * math.radians(7.0)
        head_rotations.append(euler_to_quat(nod, turn, tilt))
        
    arm_r_rotations = []
    forearm_r_rotations = []
    for t in times:
        sing_power = 0.5 + 0.5 * math.sin(t * math.pi * 2.0)
        shoulder_pitch = math.radians(20) + sing_power * math.radians(15)
        shoulder_yaw = math.radians(-15) - sing_power * math.radians(10)
        shoulder_roll = math.radians(-30) + sing_power * math.radians(8)
        arm_r_rotations.append(euler_to_quat(shoulder_pitch, shoulder_yaw, shoulder_roll))
        
        forearm_pitch = math.radians(-75) - sing_power * math.radians(20)
        forearm_yaw = math.radians(-35)
        forearm_roll = math.radians(20)
        forearm_r_rotations.append(euler_to_quat(forearm_pitch, forearm_yaw, forearm_roll))

    arm_l_rotations = []
    forearm_l_rotations = []
    for t in times:
        gesture = math.sin(t * math.pi * 1.5)
        shoulder_pitch = math.radians(15) + gesture * math.radians(18)
        shoulder_yaw = math.radians(20) + gesture * math.radians(15)
        shoulder_roll = math.radians(35) + gesture * math.radians(12)
        arm_l_rotations.append(euler_to_quat(shoulder_pitch, shoulder_yaw, shoulder_roll))
        
        forearm_pitch = math.radians(-45) - gesture * math.radians(25)
        forearm_yaw = math.radians(30)
        forearm_roll = math.radians(-20)
        forearm_l_rotations.append(euler_to_quat(forearm_pitch, forearm_yaw, forearm_roll))

    samplers_data = [
        (times, root_translations, "LINEAR", "VEC3"),
        (times, root_rotations, "LINEAR", "VEC4"),
        (times, torso_rotations, "LINEAR", "VEC4"),
        (times, head_rotations, "LINEAR", "VEC4"),
        (times, arm_r_rotations, "LINEAR", "VEC4"),
        (times, forearm_r_rotations, "LINEAR", "VEC4"),
        (times, arm_l_rotations, "LINEAR", "VEC4"),
        (times, forearm_l_rotations, "LINEAR", "VEC4"),
    ]
    
    channels_data = [
        (0, n_char_root, "translation"),
        (1, n_char_root, "rotation"),
        (2, n_torso, "rotation"),
        (3, n_head, "rotation"),
        (4, n_arm_r, "rotation"),
        (5, n_forearm_r, "rotation"),
        (6, n_arm_l, "rotation"),
        (7, n_forearm_l, "rotation"),
    ]
    
    glb.add_animation("Singing_Performance_VocalLoop", samplers_data, channels_data)
    glb.build_glb(output_file)

if __name__ == "__main__":
    import sys
    out = "/Volumes/DATA/ctg_ai/3d/phuong_an_3_procedural_stylized/model/procedural_cyber_singer.glb"
    if len(sys.argv) > 1:
        out = sys.argv[1]
    generate_singer_glb(out)
