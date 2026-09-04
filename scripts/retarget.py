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
import re
from mathutils import Quaternion, Vector

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


# Đặt NO_LEVEL_FEET=1 để dựng bản KHÔNG san lật, dùng khi cần so hai bản.
LEVEL_FEET = os.environ.get('NO_LEVEL_FEET') != '1'


def _signed_roll(fwd, normal, ref):
    """Góc xoay của normal so với ref, tính QUANH trục fwd, kèm dấu.

    Phải chiếu cả hai vector lên mặt phẳng vuông góc fwd rồi mới lấy góc giữa
    hai hình chiếu. Thiếu bước chiếu thì độ chúc mũi chân lọt vào kết quả, và
    ngay cả tư thế T cũng báo lật 30°.
    """
    nv = normal - fwd * normal.dot(fwd)
    rv = ref - fwd * ref.dot(fwd)
    if nv.length < 1e-4 or rv.length < 1e-4:
        return None
    nv.normalize()
    rv.normalize()
    a = nv.angle(rv, 0.0)
    return -a if nv.cross(rv).dot(fwd) < 0 else a


def _forward_sign(char_arm):
    """Dấu để đường nối hai khớp háng cho ra hướng NHÌN chứ không phải hướng sau.

    Không suy ra bằng cách lập luận về chiều tay của hệ trục: hệ của Blender và
    hệ của glTF ngược tay nhau, tôi đã viết nhầm một lần và bộ dựng kẹp mũi chân
    quanh đúng hướng ngược lại — đo ra mũi chân bị ép về sau 144°. Ở đây dấu
    được hiệu chuẩn bằng chính tư thế nghỉ: lúc đứng nghỉ mũi chân chỉ về trước.
    """
    b = char_arm.data.bones
    need = ('J_Bip_L_UpperLeg', 'J_Bip_R_UpperLeg',
            'J_Bip_L_Foot', 'J_Bip_L_ToeBase', 'J_Bip_R_Foot', 'J_Bip_R_ToeBase')
    if any(n not in b for n in need):
        return None, None
    mw = char_arm.matrix_world
    hip = (mw @ b['J_Bip_R_UpperLeg'].head_local) - (mw @ b['J_Bip_L_UpperLeg'].head_local)
    hip.z = 0.0
    if hip.length < 1e-6:
        return None, None
    cand = hip.normalized().cross(Vector((0.0, 0.0, 1.0)))
    if cand.length < 1e-6:
        return None, None
    cand.normalize()
    toes = Vector((0.0, 0.0, 0.0))
    for side in ('L', 'R'):
        v = ((mw @ b['J_Bip_%s_ToeBase' % side].head_local)
             - (mw @ b['J_Bip_%s_Foot' % side].head_local))
        v.z = 0.0
        if v.length > 1e-6:
            toes += v.normalized()
    if toes.length < 1e-6:
        return None, None
    return (1.0 if cand.dot(toes.normalized()) > 0 else -1.0), cand


def _body_forward(char_arm, sign):
    """Hướng nhìn của thân người trên mặt sàn, suy từ đường nối hai khớp háng."""
    l = char_arm.pose.bones.get('J_Bip_L_UpperLeg')
    r = char_arm.pose.bones.get('J_Bip_R_UpperLeg')
    if l is None or r is None or sign is None:
        return None
    mw = char_arm.matrix_world
    hip = (mw @ r.head) - (mw @ l.head)
    hip.z = 0.0
    if hip.length < 1e-6:
        return None
    return (hip.normalized().cross(Vector((0.0, 0.0, 1.0))) * sign).normalized()


def level_feet(char_arm, act, frames, max_ankle_deg=30.0, max_yaw_deg=35.0,
               min_flat=0.35, ankle_scale=1.0, yaw_scale=1.0):
    """Gỡ phần vặn cổ chân vượt quá giới hạn sinh lý.

    Vì sao cần: _aim() xoay một xương bằng phép quay cung ngắn nhất tới hướng
    đích. Phép đó khoá được hướng, tức 2 trong 3 bậc tự do, còn góc xoay quanh
    chính hướng ấy thì bỏ trống — nó thừa hưởng độ xoắn tích luỹ dọc chuỗi
    xương. Với bàn chân, hậu quả là bàn chân vặn rời khỏi ống chân.

    ĐO ĐÚNG ĐẠI LƯỢNG là chỗ dễ sai nhất ở đây. Góc giữa lòng bàn chân và
    hướng lên của THẾ GIỚI thì không bị giới hạn gì: chân xoay ra ngoài hay
    người nghiêng đều làm nó lớn lên một cách hoàn toàn bình thường. Lần đầu
    tôi ép theo đại lượng đó và làm hỏng hẳn clip đi bộ — clip ấy góc so với
    thế giới lên tới 180° nhưng CỔ CHÂN chỉ vặn 27°, tức là vốn không có lỗi;
    ép xong thì cổ chân vặn 169°.

    Đại lượng có giới hạn sinh lý là góc giữa bàn chân và CẲNG CHÂN: khớp cổ
    chân lật trong/lật ngoài được khoảng ±25–30°. Ở đây chỉ gỡ phần vượt quá
    ngần ấy, và mốc 0 lấy từ chính tư thế nghỉ của bộ xương.

    Phép xoay đặt quanh trục nối cổ chân với mũi chân. Trục đó đi qua cả hai
    khớp nên mũi chân KHÔNG dịch chuyển — bước này không phá vị trí chân mà
    lock_feet vừa đặt, và cũng không đụng tới độ chúc mũi chân.

    Bước thứ hai: kẹp góc MŨI CHÂN LỆCH so với hướng thân người. Đây là bậc tự
    do còn lại mà phép nhắm hướng không khoá, và bản mocap để nó chạy loạn: đo
    trên chính file BVH gốc, khi bước đi mũi chân đảo từ -15° tới -173°, tức là
    chỉ ngược ra sau. Khớp cổ chân không làm được thế — gập bàn chân hết cỡ
    khoảng 50° thì mũi chân vẫn còn chỉ về trước. Hai clip đi bộ dựng bằng tay
    giữ trong khoảng -9°..+2° suốt chu kỳ.

    Phép kẹp này xoay bàn chân quanh trục thẳng đứng đi qua cổ chân, nên chỉ
    đổi hướng mũi chân, không đổi độ chúc. Bỏ qua những khung bàn chân dựng gần
    thẳng đứng (min_flat): ở đó hướng mũi chân vừa không xác định rõ vừa không
    nhìn ra được.

    ankle_scale, yaw_scale: THU NHỎ biên độ trước khi kẹp. Kẹp không thôi thì
    tín hiệu dính lì ở trần — đo được trên clip đi mocap: cổ chân nằm đúng 30°
    suốt tám khung liền, mũi chân nằm đúng -35°. Nhân nhỏ lại thì giữ nguyên
    nhịp và hình dáng của chuyển động thật, chỉ hạ biên xuống. Hai clip đi bộ
    dựng bằng tay của dự án — thứ người dùng lấy làm chuẩn — có cổ chân đúng 0°
    và mũi chân 0..2° suốt chu kỳ.
    """
    if not LEVEL_FEET:
        print('    san vặn cổ chân: BỎ QUA (NO_LEVEL_FEET=1)')
        return
    scene = bpy.context.scene
    first, last = frames
    up = Vector((0.0, 0.0, 1.0))            # Blender dựng trục Z lên trời
    limit = math.radians(max_ankle_deg)

    # Trục cục bộ nào của bàn chân trỏ lên trời, và góc vặn cổ chân, đều lấy ở
    # tư thế nghỉ của bộ xương gốc nên độc lập với tư thế đang đặt.
    rest = {}
    for side in ('L', 'R'):
        _, lower, foot, toe = LEG_CHAIN[side]
        eb_f = char_arm.data.bones.get(foot)
        eb_t = char_arm.data.bones.get(toe)
        eb_l = char_arm.data.bones.get(lower)
        if None in (eb_f, eb_t, eb_l):
            continue
        mw = char_arm.matrix_world
        r0 = (mw @ eb_f.matrix_local).to_3x3()
        a_up = r0.inverted() @ up
        p_foot = mw @ eb_f.head_local
        p_toe = mw @ eb_t.head_local
        p_knee = mw @ eb_l.head_local
        fwd0 = (p_toe - p_foot)
        shin0 = (p_knee - p_foot)
        if fwd0.length < 1e-6 or shin0.length < 1e-6:
            continue
        fwd0.normalize()
        base = _signed_roll(fwd0, r0 @ a_up, shin0.normalized())
        rest[side] = (a_up, base or 0.0)

    worst_before = 0.0
    worst_after = 0.0
    touched = 0
    yaw_before = 0.0
    yaw_after = 0.0
    yaw_touched = 0
    yaw_limit = math.radians(max_yaw_deg)
    fwd_sign, _ = _forward_sign(char_arm)
    print(f'    hướng nhìn hiệu chuẩn từ tư thế nghỉ: dấu {fwd_sign}')
    for f in range(first, last + 1):
        scene.frame_set(f)
        bpy.context.view_layer.update()
        body = _body_forward(char_arm, fwd_sign)

        # --- bước 1: kẹp hướng mũi chân ---
        for side in ('L', 'R'):
            if side not in rest or body is None:
                continue
            _, _, foot, toe = LEG_CHAIN[side]
            pf = char_arm.pose.bones.get(foot)
            pt = char_arm.pose.bones.get(toe)
            if pf is None or pt is None:
                continue
            mw = char_arm.matrix_world
            ankle = mw @ pf.head
            v = (mw @ pt.head) - ankle
            flat = Vector((v.x, v.y, 0.0))
            if v.length < 1e-6 or flat.length / v.length < min_flat:
                continue                    # bàn chân dựng đứng, hướng không rõ
            fwd = flat.normalized()
            yaw = fwd.angle(body, 0.0)
            if body.cross(fwd).z < 0:
                yaw = -yaw
            yaw_before = max(yaw_before, abs(yaw))
            want = yaw * yaw_scale
            if want > yaw_limit:
                want = yaw_limit
            elif want < -yaw_limit:
                want = -yaw_limit
            excess = yaw - want
            if abs(excess) < math.radians(0.5):
                yaw_after = max(yaw_after, abs(yaw))
                continue
            q = Quaternion(Vector((0.0, 0.0, 1.0)), -excess)
            m = q.to_matrix().to_4x4() @ pf.matrix
            m.translation = pf.matrix.translation
            pf.matrix = m
            bpy.context.view_layer.update()
            pf.keyframe_insert(data_path='rotation_quaternion', frame=f)
            yaw_touched += 1
            yaw_after = max(yaw_after, abs(yaw - excess))

        # --- bước 2: kẹp góc vặn cổ chân ---
        for side in ('L', 'R'):
            if side not in rest:
                continue
            a_up, base = rest[side]
            _, lower, foot, toe = LEG_CHAIN[side]
            pf = char_arm.pose.bones.get(foot)
            pt = char_arm.pose.bones.get(toe)
            pl = char_arm.pose.bones.get(lower)
            if None in (pf, pt, pl):
                continue
            mw = char_arm.matrix_world
            ankle = mw @ pf.head
            fwd = (mw @ pt.head) - ankle
            shin = (mw @ pl.head) - ankle
            if fwd.length < 1e-6 or shin.length < 1e-6:
                continue
            fwd.normalize()
            normal = (mw @ pf.matrix).to_3x3() @ a_up
            roll = _signed_roll(fwd, normal, shin.normalized())
            if roll is None:
                continue
            roll -= base                    # 0 nghĩa là đúng như tư thế nghỉ
            worst_before = max(worst_before, abs(roll))
            want = roll * ankle_scale
            if want > limit:
                want = limit
            elif want < -limit:
                want = -limit
            excess = roll - want
            if abs(excess) < math.radians(0.5):
                worst_after = max(worst_after, abs(roll))
                continue
            q = Quaternion(fwd, excess)
            m = q.to_matrix().to_4x4() @ pf.matrix
            m.translation = pf.matrix.translation
            pf.matrix = m
            bpy.context.view_layer.update()
            pf.keyframe_insert(data_path='rotation_quaternion', frame=f)
            touched += 1
            worst_after = max(worst_after, abs(roll - excess))

    print(f'    kẹp hướng mũi chân: sửa {yaw_touched} lượt chân-frame, '
          f'lệch lớn nhất {math.degrees(yaw_before):.0f}° '
          f'-> {math.degrees(yaw_after):.0f}°')
    print(f'    san vặn cổ chân: sửa {touched} lượt chân-frame, '
          f'vặn lớn nhất {math.degrees(worst_before):.0f}° '
          f'-> {math.degrees(worst_after):.0f}°')


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


def find_dance_loop(bvh_arm, first, last, window=720, lag_lo=30, lag_hi=220, step=2):
    """Tìm chu kỳ của một đoạn vũ đạo dài, rồi chọn chỗ bắt đầu khép nhất.

    find_loop_length dò từng độ dài từ một điểm bắt đầu cố định — hợp với đoạn
    ngắn, nhưng với bản ghi bốn nghìn frame thì điểm bắt đầu mới là thứ quyết
    định. Ở đây làm hai bước:

      1. Lấy mẫu hướng khớp trên một cửa sổ dài rồi tự tương quan để tìm chu kỳ
         thật của điệu nhảy.
      2. Với chu kỳ đó, quét các chỗ bắt đầu và chọn chỗ có sai lệch nhỏ nhất.

    Trả về (frame bắt đầu, số frame).
    """
    scene = bpy.context.scene
    end = min(last - 1, first + window)
    frames = list(range(first, end, step))
    feats = []
    for f in frames:
        scene.frame_set(f)
        bpy.context.view_layer.update()
        v = []
        for src, src_child, _d, _dc in BONE_MAP:
            d = _joint_dir(bvh_arm, src, src_child) or Vector((0, 0, 1))
            v += [d.x, d.y, d.z]
        feats.append(v)
    n = len(feats)
    if n < 8:
        return first, lag_lo

    def dist(i, j):
        a, b = feats[i], feats[j]
        return sum((x - y) * (x - y) for x, y in zip(a, b))

    # --- bước 1: chu kỳ ---
    # Không lấy cực tiểu toàn cục: khoảng cách giữa hai tư thế tăng dần theo độ
    # trễ, nên cực tiểu toàn cục luôn rơi vào độ trễ nhỏ nhất bất kể điệu nhảy
    # có chu kỳ bao nhiêu. Chu kỳ thật là chỗ đường cong **trũng xuống so với
    # nền quanh nó**, nên phải chuẩn hoá theo nền rồi mới tìm cực tiểu cục bộ.
    lo_i = max(1, lag_lo // step)
    hi_i = min(lag_hi // step, n - 4)
    lags = list(range(lo_i, hi_i))
    if len(lags) < 5:
        return frames[0], lag_lo
    scores = []
    for lag in lags:
        pairs = n - lag
        scores.append(sum(dist(i, i + lag) for i in range(pairs)) / pairs)

    half = max(2, len(lags) // 8)
    ratios = []
    for k in range(len(lags)):
        a, b = max(0, k - half), min(len(lags), k + half + 1)
        base = sum(scores[a:b]) / (b - a)
        ratios.append(scores[k] / base if base > 1e-9 else 1.0)

    best_k, best_ratio = None, None
    for k in range(1, len(lags) - 1):
        if ratios[k] > ratios[k - 1] or ratios[k] > ratios[k + 1]:
            continue                      # không phải đáy
        if best_ratio is None or ratios[k] < best_ratio:
            best_k, best_ratio = k, ratios[k]
    if best_k is None:
        best_k, best_ratio = min(range(len(lags)), key=lambda k: ratios[k]), min(ratios)
    best_lag = lags[best_k]
    best_score = scores[best_k]
    period = best_lag * step
    print(f'    độ trũng của chu kỳ so với nền: {best_ratio:.2f} '
          f'(1,00 nghĩa là không có chu kỳ nào nổi lên)')

    # --- bước 2: chỗ bắt đầu ---
    best_start, best_err = frames[0], None
    for i in range(0, n - best_lag):
        err = dist(i, i + best_lag)
        if best_err is None or err < best_err:
            best_start, best_err = frames[i], err
    print(f'    chu kỳ điệu nhảy: {period} frame; bắt đầu ở frame {best_start} '
          f'(sai lệch {best_err:.3f} so với trung bình {best_score:.3f})')
    return best_start, period


def retarget(char_arm, bvh_arm, clip_name, frames=None,
             in_place=True, ground=True, scale=None, lock=True, foot=None):
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
        level_feet(char_arm, act, (1, out_frame), **(foot or {}))

    print(f'    đã bake {out_frame} frame vào "{clip_name}"')
    return act


def close_loop(char_arm, act, n_frames, blend=6):
    """Kéo mấy frame cuối về khớp với frame đầu để clip lặp không giật.

    Đoạn mocap nào có chu kỳ thật — bước đi, vẫy tay — thì find_loop_length đã
    cắt gọn. Nhưng vũ đạo hay cử chỉ dẫn chuyện thì không tuần hoàn, cắt ở đâu
    cũng còn một cú giật ở chỗ nối. Ở đây mấy frame cuối được slerp dần về tư
    thế của frame đầu, đổi lấy một chút biến dạng ở đuôi để hết giật.

    Hoà CẢ VỊ TRÍ HÔNG chứ không chỉ góc xoay. Bản cũ bỏ sót chỗ này và đo được
    hậu quả: clip dẫn chuyện lệch 110 mm theo trục dọc ở mối nối, tức cả người
    nảy lên 11 cm mỗi vòng lặp — thấy rõ hơn hẳn mọi sai lệch góc.

    Trọng số chạy tới đúng 1 ở khung cuối. Bản cũ dừng ở blend/(blend+1), tức
    với blend=6 thì còn giữ lại một phần bảy sai lệch ban đầu.
    """
    scene = bpy.context.scene
    # Lấy xương từ chính các đường cong của action, KHÔNG lấy từ BONE_MAP.
    # BONE_MAP thiếu UpperChest, Head, vai và bàn tay, nên bản cũ để nguyên sai
    # lệch ở những xương ấy: đo được clip vũ đạo dài còn giật 5,8 lần mức bình
    # thường dù đã khép vòng, và phần lớn sai lệch nằm ở đầu và ngực trên.
    names = set()
    for fc in act.fcurves:
        m = re.match(r'pose\.bones\["([^"]+)"\]\.rotation_quaternion', fc.data_path)
        if m:
            names.add(m.group(1))
    bones = [char_arm.pose.bones[n] for n in sorted(names)
             if n in char_arm.pose.bones]
    hips = char_arm.pose.bones.get('J_Bip_C_Hips')
    def _seam(last):
        scene.frame_set(1); bpy.context.view_layer.update()
        a = {pb.name: pb.matrix.to_quaternion() for pb in bones}
        scene.frame_set(last); bpy.context.view_layer.update()
        tot = 0.0
        for pb in bones:
            q = pb.matrix.to_quaternion()
            tot += math.degrees(2 * math.acos(min(1.0, abs(q.dot(a[pb.name])))))
        return tot

    def _typical_step():
        """Mức đổi tư thế bình thường giữa hai khung, lấy trung vị."""
        steps = []
        prev = None
        for f in range(1, n_frames + 1, max(1, n_frames // 24)):
            scene.frame_set(f)
            bpy.context.view_layer.update()
            cur = {pb.name: pb.matrix.to_quaternion() for pb in bones}
            if prev is not None:
                tot = 0.0
                for pb in bones:
                    d = abs(cur[pb.name].dot(prev[pb.name]))
                    tot += math.degrees(2 * math.acos(min(1.0, d)))
                steps.append(tot / max(1, n_frames // 24))
            prev = cur
        steps.sort()
        return steps[len(steps) // 2] if steps else 1.0

    gap = _seam(n_frames)
    step = max(0.5, _typical_step())
    # Cửa sổ hoà phải đủ dài để phần sửa mỗi khung KHÔNG lớn hơn chuyển động
    # bình thường của chính clip đó. Đặt cứng 6 khung là sai: đo được clip vũ
    # đạo dài lệch 314,7° ở mối nối, hoà trên 6 khung chỉ còn 51,7° — vẫn gấp
    # nhiều lần một bước bình thường, và người xem thấy đúng một cú giật mỗi
    # vòng. Cần khoảng gap/step khung; trần là một phần ba clip.
    want = int(math.ceil(gap / (0.6 * step)))
    blend = max(1, min(max(blend, want), n_frames // 3))
    print(f'    khép vòng: {len(bones)} xương, lệch mối nối {gap:.0f}°, '
          f'bước thường {step:.1f}° -> hoà trên {blend} khung')

    scene.frame_set(1)
    bpy.context.view_layer.update()
    head_pose = {pb.name: pb.rotation_quaternion.copy() for pb in bones}
    head_loc = hips.location.copy() if hips else None
    for i in range(blend):
        f = n_frames - blend + 1 + i
        w = (i + 1) / blend
        scene.frame_set(f)
        bpy.context.view_layer.update()
        for pb in bones:
            cur = pb.rotation_quaternion.copy()
            tgt = head_pose[pb.name].copy()
            if cur.dot(tgt) < 0.0:
                tgt.negate()               # tránh đi vòng xa trên mặt cầu
            pb.rotation_quaternion = cur.slerp(tgt, w)
            pb.keyframe_insert(data_path='rotation_quaternion', frame=f)
        if hips and head_loc is not None:
            hips.location = hips.location.lerp(head_loc, w)
            hips.keyframe_insert(data_path='location', frame=f)

    # Khung cuối giờ TRÙNG KHÍT khung đầu, nên phải bỏ nó đi. Giữ lại thì mỗi
    # vòng lặp nhân vật đứng hình thêm một khung — vẫn là giật, chỉ nhỏ hơn.
    # Bỏ rồi thì bước từ khung áp chót về khung đầu đúng bằng bước bình thường,
    # vì phép hoà ở trên vốn nhắm cho khung cuối rơi trúng tư thế khung đầu.
    for fc in act.fcurves:
        doomed = [kp for kp in fc.keyframe_points
                  if abs(kp.co[0] - n_frames) < 0.5]
        for kp in doomed:
            fc.keyframe_points.remove(kp)
        fc.update()
    print(f'      còn lệch {_seam(n_frames - 1):.0f}° — so với bước thường {step:.0f}°')


def mocap_state(clip_name, bvh_file, offset=0, loop_lo=20, loop_hi=90,
                in_place=True, blend=0, dance=False,
                foot=None):
    """Trả về hàm bake cho một trạng thái lấy chuyển động từ file BVH.

    offset : bỏ qua bấy nhiêu frame đầu. Các bản ghi dài thường mở đầu bằng
             đoạn diễn viên đứng chờ, lấy đúng đoạn đó thì clip không có gì.
    foot   : tham số truyền thẳng cho level_feet, ví dụ
             dict(ankle_scale=0.25, yaw_scale=0.15, max_ankle_deg=8,
                  max_yaw_deg=8) cho clip đi bộ, nơi người xem so ngay với
             dáng đi tự nhiên nên bàn chân phải rất gọn.
    """
    foot = dict(foot or {})
    def bake(char_arm, pb):
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        bvh_arm, first, last = load_bvh(os.path.join(root, 'mocap', bvh_file))
        try:
            if dance:
                start, span = find_dance_loop(bvh_arm, first + offset, last,
                                              lag_lo=loop_lo, lag_hi=loop_hi)
            else:
                start = min(first + offset, last - loop_lo - 1)
                hi = min(loop_hi, last - start - 1)
                span = find_loop_length(bvh_arm, start, lo=loop_lo, hi=hi)
            # Khép vòng phải chạy SAU CÙNG. Trước đây nó chạy trước khoá bàn
            # chân, và hai bước sau ghi đè khoá lên đúng mấy khung ở đuôi nên
            # mở lại mối nối vừa hoà xong: đo được chân còn lệch 18–24° ở chỗ
            # nối dù đã gọi close_loop. Đổi lại, mấy khung cuối có thể hở chân
            # khỏi sàn một chút — đánh đổi đáng giá so với cú giật mỗi vòng.
            act = retarget(char_arm, bvh_arm, clip_name,
                           frames=(start, start + span - 1),
                           in_place=in_place, ground=True, lock=not blend,
                           foot=foot)
            if blend:
                lock_feet(char_arm, act, (1, span))
                level_feet(char_arm, act, (1, span), **foot)
                close_loop(char_arm, act, span, blend=blend)
        finally:
            discard_bvh(bvh_arm)
            bpy.context.view_layer.objects.active = char_arm
        return act

    return bake
