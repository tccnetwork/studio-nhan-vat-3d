// Vật lý tóc mô phỏng lúc chạy, theo quy ước spring bone của VRM.
//
// Trước đây chuyển động tóc được bake cứng vào từng clip: 0,864 MB trong
// 1,33 MB dữ liệu hoạt ảnh chỉ để lưu xương tóc. Tính lúc chạy thì tóc phản
// ứng với chuyển động thật, nên nó cũng đúng cả trong lúc chuyển tiếp giữa hai
// trạng thái — điều bản bake cứng không làm được.
import * as THREE from 'three';

const _v1 = new THREE.Vector3();
const _v2 = new THREE.Vector3();
const _v3 = new THREE.Vector3();
const _q1 = new THREE.Quaternion();
const _q2 = new THREE.Quaternion();
const _qi = new THREE.Quaternion();
const _m1 = new THREE.Matrix4();
const _m2 = new THREE.Matrix4();

// Bảng quả cầu va chạm đến từ manifest (scripts/catalog.py), không viết cứng
// ở đây: tools/make_vrm.py cũng đọc đúng bảng đó khi ghi phần VRMC_springBone.

export class HairPhysics {
    constructor(options = {}) {
        this.step = options.step ?? 1 / 60;      // bước cố định, không đổi theo fps
        this.drag = options.drag ?? 0.38;        // hãm quán tính
        this.stiffness = options.stiffness ?? 0.055;  // lực kéo về tư thế nghỉ
        this.gravity = options.gravity ?? 0.020; // độ trĩu xuống
        this.radius = options.radius ?? 0.018;   // bán kính lọn tóc khi va chạm
        this.springs = [];
        this.colliders = [];
        this._accum = 0;
    }

    /** Tìm xương tóc và quả cầu va chạm trong model vừa nạp.
     *  colliderSpec lấy từ manifest.hairColliders. */
    build(model, colliderSpec = []) {
        this.springs = [];
        this.colliders = [];
        const bones = new Map();
        const hairBones = [];
        model.traverse(node => {
            if (!node.isBone) return;
            bones.set(node.name, node);
            const n = node.name;
            if (n.toLowerCase().includes('hair') && n.includes('_Sec_')) hairBones.push(node);
        });

        for (const c of colliderSpec) {
            const bone = bones.get(c.bone);
            if (bone) {
                this.colliders.push({
                    bone,
                    offset: new THREE.Vector3(...c.offset),
                    radius: c.radius,
                });
            }
        }

        for (const bone of hairBones) {
            const child = bone.children.find(c => c.isBone);
            if (!bone.parent || !child) continue;
            const len = child.position.length();
            if (len < 1e-5) continue;
            let depth = 0;
            for (let p = bone.parent; p && p.isBone; p = p.parent) depth++;
            this.springs.push({
                bone, child, depth, len,
                restLocalQuat: bone.quaternion.clone(),
                childLocalPos: child.position.clone().normalize(),
                prevTip: child.getWorldPosition(new THREE.Vector3()),
                curTip: child.getWorldPosition(new THREE.Vector3()),
                // Ma trận của xương cha ở bước trước, để quy vận tốc về hệ quy
                // chiếu đang chuyển động của cha — xem chú thích trong _step.
                parentLast: bone.parent.matrixWorld.clone(),
            });
        }
        // Cha trước con: đốt gốc phải chốt xong thì đốt sau mới tính đúng vị trí.
        this.springs.sort((a, b) => a.depth - b.depth);
        return this.springs.length;
    }

    update(delta) {
        if (this.springs.length === 0) return;
        this._accum += Math.min(delta, 0.1);
        let steps = 0;
        while (this._accum >= this.step && steps < 3) {
            this._step();
            this._accum -= this.step;
            steps++;
        }
        if (steps === 3) this._accum = 0;   // tụt fps thì bỏ bớt chứ không dồn nợ
    }

    _step() {
        const cols = this.colliders.map(c => ({
            center: c.offset.clone().applyMatrix4(c.bone.matrixWorld),
            radius: c.radius,
        }));

        for (const sp of this.springs) {
            const bone = sp.bone;

            // Quán tính phải đo trong hệ quy chiếu của xương cha, không phải hệ
            // thế giới. Khi cha xoay, chóp tóc con bị cuốn đi theo — nếu vẫn so
            // với vị trí cũ trong hệ thế giới thì đốt con nhận một vận tốc ma,
            // và mỗi đốt trong chuỗi nhận một vận tốc ma khác nhau. Kết quả là
            // các khớp cong ngược chiều nhau: tóc gấp khúc như lò xo thay vì rủ.
            //
            // Cách chữa: dời prevTip và curTip theo đúng chuyển động của cha kể
            // từ bước trước, rồi mới tính quán tính.
            _m1.copy(bone.parent.matrixWorld).multiply(_m2.copy(sp.parentLast).invert());
            sp.prevTip.applyMatrix4(_m1);
            sp.curTip.applyMatrix4(_m1);
            sp.parentLast.copy(bone.parent.matrixWorld);

            const head = bone.getWorldPosition(_v1).clone();
            bone.parent.getWorldQuaternion(_q1);

            // Hướng mà đốt tóc sẽ chỉ nếu không có lực nào tác động
            const restDir = sp.childLocalPos.clone()
                .applyQuaternion(sp.restLocalQuat)
                .applyQuaternion(_q1)
                .normalize();

            const next = sp.curTip.clone()
                .add(_v2.subVectors(sp.curTip, sp.prevTip).multiplyScalar(1 - this.drag))
                .addScaledVector(restDir, this.stiffness * sp.len)
                .add(_v3.set(0, -this.gravity * sp.len, 0));

            // Đốt tóc không co giãn: chóp luôn nằm trên mặt cầu bán kính len
            next.sub(head).setLength(sp.len).add(head);
            // Một giá trị NaN lọt vào sẽ lan ra cả bộ xương mà không báo gì.
            // Gặp thì đưa đốt tóc về tư thế nghỉ rồi chạy tiếp.
            if (!Number.isFinite(next.x + next.y + next.z)) {
                next.copy(head).addScaledVector(restDir, sp.len);
                sp.prevTip.copy(next);
            }

            for (const col of cols) {
                const d = next.distanceTo(col.center);
                const r = col.radius + this.radius;
                if (d < r && d > 1e-5) {
                    next.sub(col.center).setLength(r).add(col.center);
                    next.sub(head).setLength(sp.len).add(head);
                }
            }

            // Xoay đốt tóc để nó chỉ về chóp mới, tính trong không gian thế giới
            const curDir = sp.child.getWorldPosition(_v2).sub(head);
            const tgtDir = _v3.subVectors(next, head);
            if (curDir.lengthSq() > 1e-10 && tgtDir.lengthSq() > 1e-10) {
                _q2.setFromUnitVectors(curDir.normalize(), tgtDir.normalize());
                bone.parent.getWorldQuaternion(_q1);
                _qi.copy(_q1).invert();
                bone.quaternion.premultiply(_q1).premultiply(_q2).premultiply(_qi);
                // BẮT BUỘC chuẩn hoá lại. Mỗi bước nhân chồng ba quaternion, sai
                // số dấu phẩy động dồn lại làm |q| lệch khỏi 1 — mà ma trận xoay
                // sinh từ quaternion nhân tỉ lệ theo |q|². Không chuẩn hoá thì
                // sau 100 giây |q| lên tới hàng tỉ và tóc phình kín màn hình.
                bone.quaternion.normalize();
                bone.updateMatrixWorld(true);
            }

            sp.prevTip.copy(sp.curTip);
            sp.curTip.copy(next);
        }
    }
}
