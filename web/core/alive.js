// Lớp "sống": thở, dồn trọng tâm, đầu đưa nhẹ và nhún theo phách — tất cả tính
// bằng công thức rồi cộng thêm lên tư thế do mixer dựng ra.
//
// Lý do có module này: đo trên chính file GLB đã xuất thì 10 trong 19 trạng
// thái không có một xương nào xoay quá 3°, tức là chúng đứng hình hoàn toàn.
// Nhân vật đứng đó như ma-nơ-canh. Thay vì đi làm tay 10 clip mới, cộng một
// lớp chuyển động rất nhỏ lên trên là sửa được cả 10 trạng thái cùng lúc, và
// lớp này cũng làm điệu nhảy có nhịp thở hơn.
//
// Biên độ cố ý giữ rất nhỏ (1–3°). Ở mức đó mắt không đọc ra từng thành phần,
// chỉ thấy nhân vật đang sống; to hơn là thành ngọ nguậy.
import * as THREE from 'three';

const _q = new THREE.Quaternion();
const _e = new THREE.Euler();

/** Nhiễu trơn, tổng của hai sóng sin lệch pha vô ước — không lặp lại theo chu
 *  kỳ nghe được, nhưng vẫn liên tục và bị chặn biên, khác hẳn Math.random(). */
function wobble(t, speed, seed) {
    return 0.62 * Math.sin(t * speed + seed)
         + 0.38 * Math.sin(t * speed * 1.618 + seed * 2.4);
}

export class AliveLayer {
    constructor({
        breathRate = 0.23,     // nhịp thở mỗi giây, khoảng 14 hơi một phút
        breathDeg = 1.1,
        shiftPeriod = 7.0,     // giây cho một lần dồn trọng tâm qua lại
        shiftDeg = 1.9,
        headDeg = 1.4,
        beatDeg = 1.6,         // độ nhún trên mỗi phách
    } = {}) {
        this.enabled = true;
        this.breathRate = breathRate;
        this.breathDeg = breathDeg;
        this.shiftPeriod = shiftPeriod;
        this.shiftDeg = shiftDeg;
        this.headDeg = headDeg;
        this.beatDeg = beatDeg;
        this.bones = null;
        this.t = 0;
        this._pop = 0;         // biên độ cú nhún đang tắt dần
        this._lastPhase = 0;
        // Với mỗi xương, nhớ tư thế nền (do mixer dựng) và tư thế ta đã ghi ra.
        // Xem chú thích ở _add để biết vì sao bắt buộc phải nhớ.
        this._state = new Map();
        this._dirty = false;
    }

    /** Tìm xương theo tên VRoid. Gọi lại được nhiều lần. */
    build(root) {
        const find = name => root.getObjectByName(name) || null;
        this.bones = {
            hips: find('J_Bip_C_Hips'),
            spine: find('J_Bip_C_Spine'),
            chest: find('J_Bip_C_Chest'),
            upperChest: find('J_Bip_C_UpperChest'),
            neck: find('J_Bip_C_Neck'),
            head: find('J_Bip_C_Head'),
            shoulderL: find('J_Bip_L_Shoulder'),
            shoulderR: find('J_Bip_R_Shoulder'),
        };
        return this;
    }

    /** Cộng thêm sau khi mixer đã dựng xong tư thế của khung hình này.
     *
     *  @param delta  giây
     *  @param beat   { bpm, beatPhase, confidence } hoặc null khi không có nhạc
     *  @param energy 0..1, mức to của nhạc; dùng để nở biên độ khi bài mạnh
     */
    update(delta, beat = null, energy = 0) {
        if (!this.bones) return;
        if (!this.enabled) {
            // Tắt lớp này thì phải trả xương về nền, nếu không phần cộng thêm
            // cuối cùng nằm lại vĩnh viễn trên những xương mixer không ghi.
            if (this._dirty) this._restore();
            return;
        }
        this.t += delta;
        const t = this.t;
        const gain = 1 + 0.6 * Math.min(1, Math.max(0, energy));

        // Nhún theo phách: nảy lên ở đúng đầu phách rồi tắt dần. Nhận biết đầu
        // phách bằng chỗ beatPhase quay vòng về 0.
        if (beat && beat.bpm > 0 && beat.confidence > 6) {
            if (beat.beatPhase < this._lastPhase) this._pop = 1;
            this._lastPhase = beat.beatPhase;
        } else {
            this._lastPhase = 0;
        }
        this._pop = Math.max(0, this._pop - delta * 4.5);
        const pop = this._pop * this._pop;   // tắt nhanh lúc đầu, êm về sau

        const breath = Math.sin(t * this.breathRate * Math.PI * 2);
        const shift = Math.sin(t * Math.PI * 2 / this.shiftPeriod);

        const rad = Math.PI / 180;
        const B = this.bones;

        // Hông: dồn trọng tâm là nghiêng quanh trục trước-sau, kèm xoay nhẹ
        // quanh trục dọc — dồn hẳn sang một chân thì hông cũng hơi mở theo.
        this._add(B.hips,
            -pop * this.beatDeg * 0.5 * rad,
            shift * this.shiftDeg * 0.35 * rad,
            shift * this.shiftDeg * gain * rad);

        // Cột sống và ngực chống lại cái nghiêng của hông để đầu vẫn thẳng —
        // đây chính là điều cơ thể thật làm, và thiếu nó thì cả người đổ theo.
        this._add(B.spine,
            (breath * this.breathDeg * 0.45 + pop * this.beatDeg * 0.35) * rad,
            0,
            -shift * this.shiftDeg * 0.55 * gain * rad);
        this._add(B.chest,
            breath * this.breathDeg * gain * rad,
            wobble(t, 0.31, 1.7) * this.headDeg * 0.25 * rad,
            -shift * this.shiftDeg * 0.30 * rad);
        this._add(B.upperChest,
            breath * this.breathDeg * 0.6 * rad, 0, 0);

        // Vai nhô lên theo hơi thở, hai bên lệch pha một chút cho đỡ đối xứng.
        this._add(B.shoulderL, 0, 0, breath * this.breathDeg * 0.5 * rad);
        this._add(B.shoulderR, 0, 0, -breath * this.breathDeg * 0.42 * rad);

        // Cổ và đầu: đưa rất nhẹ, không theo chu kỳ nghe được.
        this._add(B.neck,
            wobble(t, 0.27, 0.4) * this.headDeg * 0.5 * rad,
            wobble(t, 0.19, 2.1) * this.headDeg * 0.6 * rad,
            wobble(t, 0.23, 4.2) * this.headDeg * 0.3 * rad);
        this._add(B.head,
            (wobble(t, 0.41, 1.1) * this.headDeg * 0.5 - pop * this.beatDeg * 0.4) * rad,
            wobble(t, 0.33, 3.3) * this.headDeg * 0.7 * rad,
            wobble(t, 0.29, 5.5) * this.headDeg * 0.4 * rad);
    }

    /** Cộng một phép xoay nhỏ vào tư thế hiện có, tính trong hệ của xương cha.
     *
     *  Dùng premultiply chứ không multiply: hệ trục riêng của từng xương VRoid
     *  không thống nhất, còn hệ của xương cha thì gần như thẳng đứng, nên góc
     *  đặt vào mới ra đúng hướng người xem chờ đợi.
     *
     *  Phần nhớ tư thế nền là BẮT BUỘC, không phải cho gọn. PropertyMixer của
     *  three.js chỉ gọi setValue khi giá trị vừa tính KHÁC giá trị nó đã ghi ở
     *  khung trước. Trong một clip tư thế tĩnh, xương ngực và xương vai có giá
     *  trị bất biến tuyệt đối nên mixer bỏ qua chúng hoàn toàn — và phần cộng
     *  thêm của khung này nằm chồng lên phần cộng thêm của mọi khung trước.
     *  Đo được: đặt 2° mỗi khung thì sau 4 giây xương ngực lệch 86°, trong khi
     *  xương hông (giá trị có xê dịch chút xíu nên mixer vẫn ghi) đứng yên ở 2°.
     *
     *  Cách nhận ra: nếu giá trị hiện tại đúng bằng cái ta đã ghi ra khung
     *  trước thì mixer đã không đụng vào, phải tự khôi phục nền.
     */
    _add(bone, x, y, z) {
        if (!bone) return;
        let st = this._state.get(bone);
        if (!st) {
            st = { base: bone.quaternion.clone(), written: bone.quaternion.clone() };
            this._state.set(bone, st);
        }
        if (Math.abs(bone.quaternion.dot(st.written)) > 1 - 1e-7) {
            bone.quaternion.copy(st.base);      // mixer bỏ qua xương này
        } else {
            st.base.copy(bone.quaternion);      // mixer vừa ghi nền mới
        }
        if (x || y || z) {
            _e.set(x, y, z, 'XYZ');
            _q.setFromEuler(_e);
            bone.quaternion.premultiply(_q).normalize();
        }
        st.written.copy(bone.quaternion);
        this._dirty = true;
    }

    /** Trả mọi xương về tư thế nền và quên trạng thái đã nhớ. */
    _restore() {
        for (const [bone, st] of this._state) {
            if (Math.abs(bone.quaternion.dot(st.written)) > 1 - 1e-7) {
                bone.quaternion.copy(st.base);
            }
        }
        this._state.clear();
        this._dirty = false;
    }
}
