// Bộ dựng bài: tự ghép các động tác đang có thành một bài nhảy chạy theo nhạc.
//
// Vốn liếng thật của dự án, đo từ file GLB đã xuất chứ không phải từ danh sách
// trạng thái: 19 clip nhưng chỉ 9 clip có cử động, và trong đó đúng 2 clip là
// vũ đạo. Mười clip còn lại đứng hình hoàn toàn. Nếu cứ bốc ngẫu nhiên trong 19
// clip thì phần lớn thời gian là cắt qua cắt lại giữa các ảnh tĩnh.
//
// Nên chia làm hai tầng:
//   nền   — clip có cử động, giữ chân và thân, đổi ở ranh giới CÂU nhạc;
//   gợi ý — clip đứng hình, dùng làm dáng tay đắp thêm, đổi ở ranh giới NHỊP.
//
// Chính vì các clip kia đứng hình mà chúng lại là nguyên liệu tốt cho tầng đắp
// thêm: một tư thế bất động là đúng thứ phép trộn cộng thêm cần — bắn tim, chỉ
// tay, hai tay trước mặt vốn là bộ từ vựng động tác thần tượng.
//
// Không đụng tới three.js: module này chỉ ra quyết định, còn Character mới là
// chỗ thi hành. Nhờ vậy kiểm thử được bằng nhịp giả lập.

/** Bộ sinh số giả ngẫu nhiên gieo được hạt, để kiểm thử lặp lại được kết quả. */
function makeRandom(seed) {
    let s = (seed >>> 0) || 0x2f6e2b1;
    return () => {
        s ^= s << 13; s >>>= 0;
        s ^= s >> 17;
        s ^= s << 5; s >>>= 0;
        return s / 0x100000000;
    };
}

export class Choreographer {
    constructor(manifest, {
        phraseBeats = 8,       // đổi nền mỗi câu 8 phách
        gestureBeats = 4,      // đổi dáng tay mỗi 4 phách
        restChance = 0.25,     // tỉ lệ câu để tay nghỉ, không đắp gì
        holdChance = 0.35,     // tỉ lệ giữ nguyên nền sang câu kế
        dancePreference = 2.4, // clip đánh dấu vũ đạo được ưu tiên bấy nhiêu lần
        minMovingBones = 13,   // clip ít xương động hơn thế không đủ làm nền
        costSoftness = 14,     // độ, càng lớn càng ít quan tâm chi phí chuyển
        // Đo trên nhạc thật (ba bài trong music/ và hai bài mẫu): những lần dò
        // ĐÚNG có độ tin cậy 5,2–7,0, lần dò SAI duy nhất được 2,3. Ngưỡng cũ
        // là 6 — nằm ngay giữa dải đúng, nên loại mất hai trong ba bài của
        // người dùng và bộ dựng bài ngồi im. Đặt ở giữa hai mức mới tách sạch.
        minConfidence = 4,
        seed = 0,
    } = {}) {
        this.manifest = manifest;
        this.phraseBeats = phraseBeats;
        this.gestureBeats = gestureBeats;
        this.restChance = restChance;
        this.holdChance = holdChance;
        this.dancePreference = dancePreference;
        this.costSoftness = costSoftness;
        this.minConfidence = minConfidence;
        this.rand = makeRandom(seed);

        const states = manifest.states || [];
        // Kho nền. Chỉ lấy hai clip đánh dấu vũ đạo thì bộ dựng bài không có gì
        // để chọn: nó thay phiên đúng hai clip ấy mỗi câu, nhìn ra ngay là máy.
        // Nên lấy thêm mọi clip mocap đủ nhiều xương cử động, còn hai clip vũ
        // đạo thì được ưu tiên bằng trọng số chứ không bằng cách loại người khác.
        this.bases = [];
        this.basePref = {};
        for (const s of states) {
            const enough = (s.movingBones || 0) >= minMovingBones;
            if (!s.dance && !(s.kind === 'motion' && enough)) continue;
            this.bases.push(s.clip);
            this.basePref[s.clip] = s.dance ? dancePreference : 1;
        }
        // Ảnh tĩnh dùng làm dáng tay. Bỏ T-Pose (tư thế kỹ thuật) và các thế
        // đứng nghỉ (đắp lên chỉ ra đúng dáng đang có, không thấy gì).
        const SKIP = /TPose|DungNghiem|DungNghi/;
        this.gestures = states
            .filter(s => s.kind === 'pose' && !SKIP.test(s.clip))
            .map(s => s.clip);
        this.transitions = manifest.transitions || {};

        this.reset();
    }

    reset() {
        this.enabled = false;
        this.base = null;
        this.gesture = null;
        this.beats = 0;
        this._lastPhase = 0;
        this._sinceBeat = 0;
    }

    get ready() { return this.bases.length > 0; }

    /** Chi phí chuyển từ clip a sang b, tính lúc dựng model. Thiếu số liệu thì
     *  trả về một giá trị trung tính chứ không loại bỏ nước đi. */
    cost(a, b) {
        const row = this.transitions[a];
        if (!row || row[b] === undefined) return this.costSoftness;
        return row[b];
    }

    /** Bốc một clip theo trọng số nghiêng về nước đi rẻ. Không chọn cứng nước
     *  rẻ nhất: làm vậy thì hai clip cứ thay nhau mãi, nhìn ra ngay là máy. */
    _pick(list, from, avoid) {
        const pool = list.filter(c => c !== avoid);
        const use = pool.length ? pool : list;
        if (!use.length) return null;
        const weights = use.map(c => {
            const k = from ? this.cost(from, c) : 0;
            return (this.basePref[c] || 1) * Math.exp(-k / this.costSoftness);
        });
        const total = weights.reduce((a, b) => a + b, 0);
        let r = this.rand() * total;
        for (let i = 0; i < use.length; i++) {
            r -= weights[i];
            if (r <= 0) return use[i];
        }
        return use[use.length - 1];
    }

    /** Đếm phách và ra quyết định.
     *
     *  @param delta giây
     *  @param beat  { bpm, beatPhase, confidence } từ BeatTracker
     *  @returns { base, gesture } — trường nào khác null là có thay đổi cần
     *           thi hành; trả về đối tượng rỗng khi chưa tới ranh giới.
     */
    update(delta, beat) {
        const out = { base: null, gesture: null };
        if (!this.enabled || !this.ready) return out;

        // Chưa có nhạc hoặc chưa dò ra nhịp: cứ đặt một nền rồi đứng yên đó,
        // còn hơn nhảy loạn không ăn nhập gì với bài.
        if (!beat || !beat.bpm || beat.confidence < this.minConfidence) {
            if (!this.base) out.base = this.base = this._pick(this.bases, null, null);
            return out;
        }

        // Đầu phách nhận ra ở chỗ beatPhase quay vòng về 0.
        this._sinceBeat += delta;
        const wrapped = beat.beatPhase < this._lastPhase;
        this._lastPhase = beat.beatPhase;
        if (!wrapped) return out;
        // Chặn đếm trùng khi khung hình dài hơn nửa phách.
        if (this._sinceBeat < 60 / beat.bpm * 0.5) return out;
        this._sinceBeat = 0;

        const first = this.beats === 0;
        this.beats++;

        if (first || this.beats % this.phraseBeats === 1) {
            // Vũ đạo thật có lặp: câu nào cũng đổi thì thành nhảy loạn. Thỉnh
            // thoảng giữ nguyên nền thêm một câu nữa.
            if (first || this.rand() > this.holdChance) {
                out.base = this.base = this._pick(this.bases, this.base, this.base);
            }
        }
        if (first || this.beats % this.gestureBeats === 1) {
            if (this.gestures.length && this.rand() > this.restChance) {
                out.gesture = this.gesture = this._pick(this.gestures, null, this.gesture);
            } else {
                out.gesture = this.gesture = '';   // chuỗi rỗng: hạ tay xuống
            }
        }
        return out;
    }
}
