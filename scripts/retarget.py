# -*- coding: utf-8 -*-
"""Retarget mocap BVH sang bộ xương VRoid của nhân vật.

Vì sao không chép thẳng góc quay cục bộ
---------------------------------------
Rest pose của bộ BVH này vô nghĩa: mọi xương nằm dọc trục X, chân trái và chân
phải tách nhau theo trục Z. Toàn bộ tư thế nằm trong kênh xoay chứ không nằm ở
rest pose. Chép góc quay cục bộ từ một rest pose như vậy sang một nhân vật đứng
T-pose thì ra tư thế rối loạn — đó là lý do sáu script retarget đời trước đều
bỏ dở.

Cách làm ở đây là bám hướng: mỗi frame, đọc **hướng thật trong không gian thế
giới** của từng xương BVH ở tư thế đã animate, rồi xoay xương tương ứng của
nhân vật để chỉ đúng hướng đó. Cách này không phụ thuộc rest pose.

Hai bộ xương may mắn cùng quy ước, đo từ chính dữ liệu:
    trục lên     Z cho cả hai
    hướng mặt    -Y cho cả hai
    bên trái     +X cho cả hai
    đơn vị       BVH tính bằng cm, nhân vật bằng m
    chiều cao    đầu ở 139 cm so với 138,6 cm — lệch 1%
Nên phép biến đổi chỉ còn một hệ số tỉ lệ, không có phép xoay hệ trục nào.
"""
import bpy
import math
import os
from mathutils import Vector

# Hướng của một xương phải đo bằng vector từ khớp này tới **khớp con**, không
# phải bằng tail - head. glTF không lưu chiều dài xương nên khi nhập vào Blender,
# mọi xương được gán tail tuỳ tiện dọc +Z: xương đùi có head ở z = 0,868 nhưng
# tail ở z = 1,221, tức là "chỉ lên trời" trong khi chân thật thì đi xuống.
# Bám theo tail - head là bám vào một đại lượng giả — và nó còn qua được phép
# kiểm tra nếu ta so chính đại lượng giả đó ở cả hai phía.
#
# Mỗi mục: (xương BVH, khớp con BVH, xương nhân vật, khớp con nhân vật)
BONE_MAP = [
    ('Hips',       'Spine',      'J_Bip_C_Hips',      'J_Bip_C_Spine'),
    ('Spine',      'Chest',      'J_Bip_C_Spine',     'J_Bip_C_Chest'),
    ('Chest',      'Neck',       'J_Bip_C_Chest',     'J_Bip_C_Neck'),
    ('Neck',       'Head',       'J_Bip_C_Neck',      'J_Bip_C_Head'),
    ('UpperArm_L', 'LowerArm_L', 'J_Bip_L_UpperArm',  'J_Bip_L_LowerArm'),
    ('LowerArm_L', 'Hand_L',     'J_Bip_L_LowerArm',  'J_Bip_L_Hand'),
    ('UpperArm_R', 'LowerArm_R', 'J_Bip_R_UpperArm',  'J_Bip_R_LowerArm'),
    ('LowerArm_R', 'Hand_R',     'J_Bip_R_LowerArm',  'J_Bip_R_Hand'),
    ('UpperLeg_L', 'LowerLeg_L', 'J_Bip_L_UpperLeg',  'J_Bip_L_LowerLeg'),
    ('LowerLeg_L', 'Foot_L',     'J_Bip_L_LowerLeg',  'J_Bip_L_Foot'),
    ('Foot_L',     'Toes_L',     'J_Bip_L_Foot',      'J_Bip_L_ToeBase'),
    ('UpperLeg_R', 'LowerLeg_R', 'J_Bip_R_UpperLeg',  'J_Bip_R_LowerLeg'),
    ('LowerLeg_R', 'Foot_R',     'J_Bip_R_LowerLeg',  'J_Bip_R_Foot'),
    ('Foot_R',     'Toes_R',     'J_Bip_R_Foot',      'J_Bip_R_ToeBase'),
]

# Xương đầu không có khớp con thật (BVH kết thúc bằng End Site rỗng), nên không
# bám hướng được; nó giữ nguyên tư thế so với cổ.

BVH_TO_METRE = 0.01


def load_bvh(path):
    """Nạp BVH và trả về (armature, frame_start, frame_end)."""
    before = set(bpy.data.objects)
    bpy.ops.import_anim.bvh(filepath=path, use_fps_scale=False,
                            update_scene_fps=False, update_scene_duration=False)
    arm = next(o for o in set(bpy.data.objects) - before if o.type == 'ARMATURE')
    act = arm.animation_data.action
    first, last = (int(round(v)) for v in act.frame_range)
    return arm, first, last


def discard_bvh(arm):
    act = arm.animation_data.action if arm.animation_data else None
    data = arm.data
    bpy.data.objects.remove(arm, do_unlink=True)
    if act:
        bpy.data.actions.remove(act)
    if data.users == 0:
        bpy.data.armatures.remove(data)


def _joint_dir(arm, bone_name, child_name):
    """Hướng từ khớp này tới khớp con, trong không gian thế giới."""
    a = arm.pose.bones.get(bone_name)
    b = arm.pose.bones.get(child_name)
    if a is None or b is None:
        return None
    d = (arm.matrix_world @ b.head) - (arm.matrix_world @ a.head)
    return d.normalized() if d.length > 1e-6 else None


def _aim(arm, bone_name, child_name, target_dir):
    """Xoay một xương để đoạn nối nó với khớp con chỉ theo target_dir.

    Phép xoay phải quay quanh **đầu xương**, không quanh gốc toạ độ. Nhân thẳng
    q @ pb.matrix là xoay quanh gốc, làm mọi xương nằm xa gốc bị hất đi chỗ
    khác — bàn tay ở x = 0,54 m văng đi nửa mét chỉ vì một phép xoay nhỏ.
    """
    cur = _joint_dir(arm, bone_name, child_name)
    if cur is None:
        return
    pb = arm.pose.bones[bone_name]
    q = cur.rotation_difference(target_dir)
    m = q.to_matrix().to_4x4() @ pb.matrix
    m.translation = pb.matrix.translation      # giữ nguyên vị trí đầu xương
    pb.matrix = m
    bpy.context.view_layer.update()


def _lowest_point(char_arm):
    """Cao độ thấp nhất của bàn chân và mũi chân ở frame hiện tại."""
    lows = []
    for name in ('J_Bip_L_Foot', 'J_Bip_R_Foot',
                 'J_Bip_L_ToeBase', 'J_Bip_R_ToeBase'):
        pb = char_arm.pose.bones.get(name)
        if pb:
            lows.append(min((char_arm.matrix_world @ pb.head).z,
                            (char_arm.matrix_world @ pb.tail).z))
    return min(lows) if lows else 0.0


LEG_CHAIN = {
    'L': ('J_Bip_L_UpperLeg', 'J_Bip_L_LowerLeg', 'J_Bip_L_Foot', 'J_Bip_L_ToeBase'),
    'R': ('J_Bip_R_UpperLeg', 'J_Bip_R_LowerLeg', 'J_Bip_R_Foot', 'J_Bip_R_ToeBase'),
}


def _sole_height(arm, side):
    """Cao độ thấp nhất của bàn chân và mũi chân ở frame hiện tại."""
    _, _, foot, toe = LEG_CHAIN[side]
    zs = []
    for n in (foot, toe):
        pb = arm.pose.bones.get(n)
        if pb:
            zs += [pb.head.z, pb.tail.z]
    return min(zs) if zs else 0.0


def _two_bone_ik(arm, side, ankle_target):
    """Đặt cổ chân vào ankle_target bằng cách giải góc gối theo hình học.

    Giữ nguyên hướng gối mà mocap đã cho: dùng chính vị trí gối hiện tại làm
    vector cực, nên chân không bị lật ngược ra sau khi giải.
    """
    upper, lower, foot, _toe = LEG_CHAIN[side]
    pu, pl, pf = (arm.pose.bones.get(n) for n in (upper, lower, foot))
    if not (pu and pl and pf):
        return
    hip = pu.head.copy()
    l1 = (pl.head - pu.head).length
    l2 = (pf.head - pl.head).length
    axis = ankle_target - hip
    d = axis.length
    if d < 1e-5:
        return
    # Không cho chân duỗi thẳng hoàn toàn: gối thẳng đơ nhìn rất giả.
    d = max(abs(l1 - l2) + 1e-4, min(d, (l1 + l2) * 0.999))
    axis = axis.normalized()

    pole = pl.head - hip
    pole = pole - axis * pole.dot(axis)
    if pole.length < 1e-5:
        pole = Vector((0.0, -1.0, 0.0))          # gối hướng ra trước
        pole = pole - axis * pole.dot(axis)
    pole.normalize()

    a = (l1 * l1 - l2 * l2 + d * d) / (2.0 * d)
    h2 = l1 * l1 - a * a
    h = math.sqrt(h2) if h2 > 0 else 0.0
    knee = hip + axis * a + pole * h

    foot_dir_before = _joint_dir(arm, foot, LEG_CHAIN[side][3])
    _aim(arm, upper, lower, (knee - hip).normalized())
    _aim(arm, lower, foot, (ankle_target - pl.head).normalized())
    if foot_dir_before is not None:
        _aim(arm, foot, LEG_CHAIN[side][3], foot_dir_before)


def lock_feet(char_arm, act, frames, contact_band=0.03):
    """Ép bàn chân chạm đúng mặt sàn trong những frame đang chống.

    Bước retarget FK chỉ nâng cả clip lên một lần cho khớp toàn cục, nên trong
    từng frame bàn chân vẫn có thể lơ lửng vài milimét tới hơn một xentimét.
    Ở đây mỗi frame được chỉnh riêng bằng IK hai xương.
    """
    scene = bpy.context.scene
    first, last = frames
    fixed = 0
    for side in ('L', 'R'):
        heights = []
        for f in range(first, last + 1):
            scene.frame_set(f)
            bpy.context.view_layer.update()
            heights.append(_sole_height(char_arm, side))
        floor = min(heights)
        for i, f in enumerate(range(first, last + 1)):
            lift = heights[i] - floor
            if lift > contact_band:
                continue                          # đang ở pha đưa chân, không đụng
            if abs(heights[i]) < 1e-4:
                continue
            scene.frame_set(f)
            bpy.context.view_layer.update()
            upper, lower, foot, toe = LEG_CHAIN[side]
            target = char_arm.pose.bones[foot].head.copy()
            target.z -= heights[i]                # hạ hoặc nâng cho đúng mặt sàn
            _two_bone_ik(char_arm, side, target)
            for n in (upper, lower, foot):
                char_arm.pose.bones[n].keyframe_insert(
                    data_path='rotation_quaternion', frame=f)
            fixed += 1
    print(f'    khoá bàn chân: chỉnh {fixed} lượt chân-frame về đúng mặt sàn')


def find_loop_length(bvh_arm, first, lo=16, hi=90):
    """Tìm độ dài clip khép kín nhất, tính bằng frame.

    So hướng của toàn bộ khớp ở frame đầu với frame đầu + N, chọn N cho tổng
    sai lệch góc nhỏ nhất. Cắt bừa một đoạn mocap thì lúc lặp lại sẽ giật.
    """
    scene = bpy.context.scene

    def dirs(f):
        scene.frame_set(f)
        bpy.context.view_layer.update()
        out = []
        for src, src_child, _dst, _dc in BONE_MAP:
            d = _joint_dir(bvh_arm, src, src_child)
            out.append(d if d else Vector((0, 0, 1)))
        return out

    base = dirs(first)
    best, best_err = lo, None
    for n in range(lo, hi + 1):
        cur = dirs(first + n)
        err = sum(a.angle(b, 0.0) for a, b in zip(base, cur))
        if best_err is None or err < best_err:
            best, best_err = n, err
    print(f'    điểm lặp khép nhất: {best} frame '
          f'(lệch tổng cộng {math.degrees(best_err):.1f} độ trên {len(base)} khớp)')
    return best


def retarget(char_arm, bvh_arm, clip_name, frames=None,
             in_place=True, ground=True, scale=None, lock=True):
    """Bake một action mới trên char_arm từ chuyển động của bvh_arm.

    in_place : bỏ thành phần tịnh tiến theo hướng đi để clip lặp được tại chỗ;
               vẫn giữ nhún dọc và lắc ngang vì đó là phần làm dáng đi có sức nặng.
    ground   : hạ hoặc nâng toàn bộ clip sao cho điểm thấp nhất của bàn chân
               chạm mặt sàn, thay vì để nhân vật lún xuống hay bay lơ lửng.
    """
    scene = bpy.context.scene
    first, last = frames if frames else (int(scene.frame_start), int(scene.frame_end))

    if scale is None:
        # Căn theo chiều cao hông thay vì đoán: hai bộ xương lệch nhau vài phần trăm.
        scene.frame_set(first)
        bpy.context.view_layer.update()
        bvh_hip = (bvh_arm.matrix_world @ bvh_arm.pose.bones['Hips'].head).z
        char_hip = (char_arm.matrix_world
                    @ char_arm.data.bones['J_Bip_C_Hips'].head_local).z
        scale = char_hip / bvh_hip if bvh_hip else BVH_TO_METRE
    print(f'    tỉ lệ BVH -> nhân vật: {scale:.5f} '
          f'(so với {BVH_TO_METRE} nếu chỉ đổi cm sang m)')

    for b in char_arm.pose.bones:
        b.rotation_mode = 'QUATERNION'
    if not char_arm.animation_data:
        char_arm.animation_data_create()
    act = bpy.data.actions.new(name=clip_name)
    char_arm.animation_data.action = act

    hips_pb = char_arm.pose.bones['J_Bip_C_Hips']
    hips_rest = char_arm.data.bones['J_Bip_C_Hips'].head_local.copy()

    # Quét trước quỹ đạo hông để tách phần đi tới khỏi phần dao động.
    hips_y = []
    for f in range(first, last + 1):
        scene.frame_set(f)
        bpy.context.view_layer.update()
        hips_y.append((bvh_arm.matrix_world @ bvh_arm.pose.bones['Hips'].head).y * scale)
    span_n = max(1, len(hips_y) - 1)
    drift = (hips_y[-1] - hips_y[0]) / span_n

    scene.frame_set(first)
    bpy.context.view_layer.update()
    origin = (bvh_arm.matrix_world @ bvh_arm.pose.bones['Hips'].head) * scale

    lowest = []
    out_frame = 0
    for src in range(first, last + 1):
        out_frame += 1
        scene.frame_set(src)
        bpy.context.view_layer.update()

        # --- gốc: đặt hông ---
        hip_world = (bvh_arm.matrix_world @ bvh_arm.pose.bones['Hips'].head) * scale
        delta = hip_world - origin
        if in_place:
            # Chỉ trừ đi phần đi tới đều, giữ lại dao động trước sau của hông.
            # Ép thẳng Y = 0 sẽ xoá dao động đó và dồn nó xuống bàn chân, thành
            # ra chân chống lúc nhanh lúc chậm — đúng cảm giác trượt patin.
            delta.y -= drift * (src - first)
        # pose_bone.location nằm trong hệ trục riêng của xương chứ không phải
        # hệ thế giới, nên gán thẳng vector thế giới vào đó là dịch sai hướng.
        # Đặt qua ma trận rồi để Blender tự quy về location.
        m = hips_pb.matrix.copy()
        m.translation = hips_rest + delta
        hips_pb.matrix = m
        bpy.context.view_layer.update()

        # --- xoay: bám hướng, cha trước con ---
        for src, src_child, dst, dst_child in BONE_MAP:
            pb = char_arm.pose.bones.get(dst)
            tgt = _joint_dir(bvh_arm, src, src_child)
            if pb is None or tgt is None:
                continue
            _aim(char_arm, dst, dst_child, tgt)
            pb.keyframe_insert(data_path='rotation_quaternion', frame=out_frame)
        hips_pb.keyframe_insert(data_path='location', frame=out_frame)

        lowest.append(_lowest_point(char_arm))

    # --- chạm sàn: dịch cả clip lên hoặc xuống theo trục Z của thế giới ---
    if ground and lowest:
        drop = min(lowest)
        if abs(drop) > 1e-4:
            print(f'    điểm thấp nhất của bàn chân ở {drop * 100:+.1f} cm '
                  f'-> dịch cả clip cho chạm sàn')
            # pose_bone.location nằm trong hệ trục riêng của xương. Với xương
            # hông chỉ thẳng lên, trục Z cục bộ của nó lại là -Y của thế giới,
            # nên cộng thẳng vào fcurve location[2] là đẩy nhân vật ra sau chứ
            # không nâng lên. Quy đổi một lần qua ma trận rest của xương.
            rest3 = char_arm.data.bones['J_Bip_C_Hips'].matrix_local.to_3x3()
            local_shift = rest3.inverted() @ Vector((0.0, 0.0, -drop))
            curves = {f.array_index: f for f in act.fcurves
                      if f.data_path == 'pose.bones["J_Bip_C_Hips"].location'}
            for axis in range(3):
                fc = curves.get(axis)
                if not fc or abs(local_shift[axis]) < 1e-6:
                    continue
                for kp in fc.keyframe_points:
                    kp.co[1] += local_shift[axis]
                    kp.handle_left[1] += local_shift[axis]
                    kp.handle_right[1] += local_shift[axis]
                fc.update()

    if ground and lock:
        lock_feet(char_arm, act, (1, out_frame))

    print(f'    đã bake {out_frame} frame vào "{clip_name}"')
    return act


def close_loop(char_arm, act, n_frames, blend=6):
    """Kéo mấy frame cuối về khớp với frame đầu để clip lặp không giật.

    Đoạn mocap nào có chu kỳ thật — bước đi, vẫy tay — thì find_loop_length đã
    cắt gọn. Nhưng vũ đạo hay cử chỉ dẫn chuyện thì không tuần hoàn, cắt ở đâu
    cũng còn một cú giật ở chỗ nối. Ở đây mấy frame cuối được slerp dần về tư
    thế của frame đầu, đổi lấy một chút biến dạng ở đuôi để hết giật.
    """
    scene = bpy.context.scene
    bones = [char_arm.pose.bones[d] for _s, _sc, d, _dc in BONE_MAP
             if d in char_arm.pose.bones]

    scene.frame_set(1)
    bpy.context.view_layer.update()
    head_pose = {pb.name: pb.rotation_quaternion.copy() for pb in bones}

    blend = min(blend, n_frames // 3)
    for i in range(blend):
        f = n_frames - blend + 1 + i
        w = (i + 1) / (blend + 1)
        scene.frame_set(f)
        bpy.context.view_layer.update()
        for pb in bones:
            cur = pb.rotation_quaternion.copy()
            tgt = head_pose[pb.name].copy()
            if cur.dot(tgt) < 0.0:
                tgt.negate()               # tránh đi vòng xa trên mặt cầu
            pb.rotation_quaternion = cur.slerp(tgt, w)
            pb.keyframe_insert(data_path='rotation_quaternion', frame=f)
    print(f'    làm khép vòng: hoà {blend} frame cuối về tư thế frame đầu')


def mocap_state(clip_name, bvh_file, offset=0, loop_lo=20, loop_hi=90,
                in_place=True, blend=0):
    """Trả về hàm bake cho một trạng thái lấy chuyển động từ file BVH.

    offset : bỏ qua bấy nhiêu frame đầu. Các bản ghi dài thường mở đầu bằng
             đoạn diễn viên đứng chờ, lấy đúng đoạn đó thì clip không có gì.
    """
    def bake(char_arm, pb):
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        bvh_arm, first, last = load_bvh(os.path.join(root, 'mocap', bvh_file))
        try:
            start = min(first + offset, last - loop_lo - 1)
            hi = min(loop_hi, last - start - 1)
            span = find_loop_length(bvh_arm, start, lo=loop_lo, hi=hi)
            # Thứ tự quan trọng: làm khép vòng trước rồi mới khoá bàn chân.
            # Làm ngược lại thì phép hoà đuôi clip sẽ nhấc chân khỏi sàn ở đúng
            # mấy frame vừa được chỉnh cho chạm sàn.
            act = retarget(char_arm, bvh_arm, clip_name,
                           frames=(start, start + span - 1),
                           in_place=in_place, ground=True, lock=not blend)
            if blend:
                close_loop(char_arm, act, span, blend=blend)
                lock_feet(char_arm, act, (1, span))
        finally:
            discard_bvh(bvh_arm)
            bpy.context.view_layer.objects.active = char_arm
        return act

    return bake
