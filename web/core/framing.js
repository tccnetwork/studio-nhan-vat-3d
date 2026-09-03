// Điều khiển khung hình: xoay quanh nhân vật, dời nhân vật trong khung, và
// giữ nó không trôi ra ngoài.
//
// Vì sao không dùng thẳng pan của OrbitControls: pan dịch CẢ tâm xoay lẫn máy
// quay. Dời nhân vật một chút là tâm xoay rời khỏi nhân vật, rồi xoay thì nhân
// vật văng vòng quanh một điểm ở xa. Ở đây tâm xoay luôn nằm ở nhân vật, còn
// việc dời nhân vật làm bằng camera.setViewOffset — dịch khung ảnh chứ không
// dịch máy quay.
import * as THREE from 'three';

export class FrameController {
    /** pivot: điểm mà máy quay xoay quanh và cũng là điểm dùng để đo vị trí
     *  trên khung. Trang studio đổi điểm này khi chuyển giữa toàn thân /
     *  khuôn mặt / bàn tay, nên nó là tham số chứ không cố định. */
    constructor({ camera, controls, element, canvas, pivot,
                  keepInside = 0.18, azimuth = -0.079, polar = 1.486 }) {
        this.camera = camera;
        this.controls = controls;
        this.el = element;
        this.canvas = canvas || (controls && controls.domElement);
        this.pivot = pivot.clone();
        this.keepInside = keepInside;
        this.azimuth = azimuth;
        this.polar = polar;
        this.offset = { x: 0, y: 0 };      // pixel
        this.dragMode = 'xoay';
        this.userMoved = false;
        this._probe = new THREE.Vector3();

        if (controls) {
            // Tâm xoay phải luôn ở nhân vật, nên pan của OrbitControls tắt hẳn.
            controls.enablePan = false;
            controls.addEventListener('start', () => { this.userMoved = true; });
        }
        this._bindDrag();
        this.setDragMode('xoay');
    }

    _bindDrag() {
        const cv = this.canvas;
        if (!cv) return;
        let last = null;
        cv.addEventListener('pointerdown', e => {
            if (this.dragMode !== 'dichuyen' || e.button !== 0) return;
            last = { x: e.clientX, y: e.clientY };
            this.userMoved = true;
            cv.setPointerCapture(e.pointerId);
            e.preventDefault();
        });
        cv.addEventListener('pointermove', e => {
            if (!last) return;
            this.offset.x += e.clientX - last.x;
            this.offset.y += e.clientY - last.y;
            last = { x: e.clientX, y: e.clientY };
            this.apply();
        });
        const end = e => {
            if (!last) return;
            last = null;
            try { cv.releasePointerCapture(e.pointerId); } catch (_) {}
        };
        cv.addEventListener('pointerup', end);
        cv.addEventListener('pointercancel', end);
    }

    get size() {
        return { w: this.el.clientWidth || 1, h: this.el.clientHeight || 1 };
    }

    /** 'xoay' — kéo trái để xoay. 'dichuyen' — kéo trái để dời nhân vật. */
    setDragMode(mode) {
        this.dragMode = mode;
        if (!this.controls) return;
        const move = mode === 'dichuyen';
        this.controls.mouseButtons = {
            LEFT: move ? null : THREE.MOUSE.ROTATE,
            MIDDLE: THREE.MOUSE.DOLLY,
            RIGHT: THREE.MOUSE.ROTATE,
        };
        this.controls.touches = {
            ONE: move ? null : THREE.TOUCH.ROTATE,
            TWO: THREE.TOUCH.DOLLY_ROTATE,
        };
    }

    apply() {
        const { w, h } = this.size;
        const maxX = (0.5 - this.keepInside) * w;
        const maxY = (0.5 - this.keepInside) * h;
        this.offset.x = THREE.MathUtils.clamp(this.offset.x, -maxX, maxX);
        this.offset.y = THREE.MathUtils.clamp(this.offset.y, -maxY, maxY);
        if (this.offset.x === 0 && this.offset.y === 0) this.camera.clearViewOffset();
        else this.camera.setViewOffset(w, h, -this.offset.x, -this.offset.y, w, h);
    }

    /** Nhân vật đang ở bao nhiêu phần trăm khung. Đo bằng phép chiếu thật qua
     *  ma trận máy quay, không suy từ biến nội bộ — suy từ biến nội bộ là tự
     *  soi lại chính mình, biến lệch với hình thì con số vẫn đẹp mà vẫn sai. */
    screenPos() {
        this.camera.updateMatrixWorld();
        this._probe.copy(this.pivot).project(this.camera);
        return { x: this._probe.x * 50 + 50, y: 50 - this._probe.y * 50 };
    }

    /** Đặt máy quay ở khoảng cách dist, theo góc mặc định. */
    place(dist) {
        const t = this.controls ? this.controls.target : this.pivot;
        this.camera.position.set(
            t.x + dist * Math.sin(this.polar) * Math.sin(this.azimuth),
            t.y + dist * Math.cos(this.polar),
            t.z + dist * Math.sin(this.polar) * Math.cos(this.azimuth));
        this.camera.lookAt(t);
    }

    /** Dời tâm xoay sang điểm khác, ví dụ khi chuyển sang cận cảnh khuôn mặt. */
    setPivot(p, distance = null) {
        this.pivot.copy(p);
        if (this.controls) this.controls.target.copy(p);
        if (distance !== null) this.place(distance);
        if (this.controls) this.controls.update();
    }

    getFraming() {
        const { w, h } = this.size;
        const t = this.controls ? this.controls.target : this.pivot;
        const off = this.camera.position.clone().sub(t);
        const d = off.length();
        return {
            distance: +d.toFixed(3),
            azimuth: +Math.atan2(off.x, off.z).toFixed(4),
            polar: +Math.acos(THREE.MathUtils.clamp(off.y / d, -1, 1)).toFixed(4),
            frameOffset: { x: +(this.offset.x / w).toFixed(4), y: +(this.offset.y / h).toFixed(4) },
        };
    }

    setFraming(fr) {
        if (!fr) return;
        const { w, h } = this.size;
        if (fr.frameOffset) {
            this.offset.x = (fr.frameOffset.x ?? 0) * w;
            this.offset.y = (fr.frameOffset.y ?? 0) * h;
            this.apply();
        }
        const t = this.controls ? this.controls.target : this.pivot;
        const dist = fr.distance ?? this.camera.position.distanceTo(t);
        const az = fr.azimuth ?? this.azimuth, po = fr.polar ?? this.polar;
        this.camera.position.set(
            t.x + dist * Math.sin(po) * Math.sin(az),
            t.y + dist * Math.cos(po),
            t.z + dist * Math.sin(po) * Math.cos(az));
        this.camera.lookAt(t);
        if (this.controls) this.controls.update();
        this.userMoved = true;
    }

    reset(distance = null) {
        this.userMoved = false;
        this.offset.x = 0;
        this.offset.y = 0;
        this.apply();
        if (this.controls) this.controls.target.copy(this.pivot);
        if (distance !== null) this.place(distance);
        if (this.controls) this.controls.update();
    }
}
