// Khẩu hình: đoán nguyên âm đang phát ra từ phổ âm thanh.
//
// Nguyên âm được xác định bởi hai formant — hai đỉnh cộng hưởng của khoang
// miệng. F1 phản ánh độ mở hàm, F2 phản ánh vị trí lưỡi trước sau; cặp
// (F1, F2) gần như xác định duy nhất một nguyên âm.
//
// Module này không đụng tới three.js hay DOM, và classifyVowel là hàm thuần,
// nên kiểm thử được bằng phổ tổng hợp có formant biết trước.

// Bảng formant theo giọng nữ, hợp với nhân vật của dự án.
export const VOWELS = [
    { key: 'A', f1: 850, f2: 1220 },
    { key: 'I', f1: 350, f2: 2750 },
    { key: 'U', f1: 370, f2: 950 },
    { key: 'E', f1: 560, f2: 2350 },
    { key: 'O', f1: 450, f2: 800 },
];

// F2 của các nguyên âm sau nằm rất thấp — O ở khoảng 800 Hz, U ở 950 — nên dải
// dò F2 phải chạm xuống dưới 1000, nếu không cả hai đều bị dò trượt và lẫn vào
// nhau. Đổi lại phải ràng buộc F2 luôn cao hơn F1 để hai phép dò không cùng bắt
// vào một đỉnh.
const F1_BAND = [250, 1000];
const F2_BAND = [700, 3200];
const F2_ABOVE_F1 = 1.25;
const VOICE_BAND = [90, 4000];

function peakInBand(db, sampleRate, lo, hi) {
    const binHz = sampleRate / (db.length * 2);
    const from = Math.max(1, Math.floor(lo / binHz));
    const to = Math.min(db.length - 2, Math.ceil(hi / binHz));
    if (to <= from) return { hz: 0, db: -Infinity };
    let best = from, bestDb = -Infinity;
    for (let i = from; i <= to; i++) {
        if (db[i] > bestDb) { bestDb = db[i]; best = i; }
    }
    // Nội suy parabol quanh đỉnh: không có bước này thì tần số bị lượng tử theo
    // bin và nguyên âm nhảy qua nhảy lại giữa hai ô cạnh nhau.
    const y0 = db[best - 1], y1 = db[best], y2 = db[best + 1];
    let shift = 0;
    if (isFinite(y0) && isFinite(y2)) {
        const denom = y0 - 2 * y1 + y2;
        if (Math.abs(denom) > 1e-6) shift = 0.5 * (y0 - y2) / denom;
    }
    return { hz: (best + shift) * binHz, db: bestDb };
}

export function bandEnergyDb(db, sampleRate, lo = VOICE_BAND[0], hi = VOICE_BAND[1]) {
    const binHz = sampleRate / (db.length * 2);
    const from = Math.max(1, Math.floor(lo / binHz));
    const to = Math.min(db.length - 1, Math.ceil(hi / binHz));
    if (to < from) return -Infinity;
    let sum = 0;
    for (let i = from; i <= to; i++) sum += db[i];
    return sum / (to - from + 1);
}

/** Đoán nguyên âm từ một phổ dB. Hàm thuần, không giữ trạng thái. */
export function classifyVowel(db, sampleRate) {
    const p1 = peakInBand(db, sampleRate, F1_BAND[0], F1_BAND[1]);
    const lo2 = Math.max(F2_BAND[0], p1.hz * F2_ABOVE_F1);
    if (lo2 >= F2_BAND[1]) return null;
    const p2 = peakInBand(db, sampleRate, lo2, F2_BAND[1]);
    if (!isFinite(p1.db) || !isFinite(p2.db)) return null;

    // So sánh theo thang log: tai người nghe tần số theo tỉ lệ chứ không theo hiệu.
    let best = null, bestDist = Infinity;
    for (const v of VOWELS) {
        const d1 = Math.log(p1.hz / v.f1);
        const d2 = Math.log(p2.hz / v.f2);
        const dist = d1 * d1 + d2 * d2 * 0.7;   // F1 quan trọng hơn cho độ mở miệng
        if (dist < bestDist) { bestDist = dist; best = v.key; }
    }
    return { key: best, f1: p1.hz, f2: p2.hz };
}

/** Cổng lọc mức to, tự bám nền và trần.
 *
 *  Không dùng ngưỡng dB tuyệt đối: giá trị getFloatFrequencyData phụ thuộc mức
 *  thu và cách phối của từng bản, nên một con số cứng chỉ đúng với đúng một file.
 */
export function createLoudnessGate({ adapt = 0.4, minRange = 8 } = {}) {
    let floor = null, ceil = null;
    return {
        reset() { floor = null; ceil = null; },
        /** Trả về 0..1: 0 là im tiếng, 1 là to bằng đoạn to nhất gần đây. */
        level(db, sampleRate, delta) {
            const lv = bandEnergyDb(db, sampleRate);
            if (!isFinite(lv)) return 0;
            if (floor === null) { floor = lv; ceil = lv + minRange; }
            const k = Math.min(1, adapt * delta);
            // Nền tụt nhanh, lên chậm; trần thì ngược lại.
            floor += (lv < floor ? 0.5 : k * 0.02) * (lv - floor);
            ceil += (lv > ceil ? 0.5 : k * 0.05) * (lv - ceil);
            const range = Math.max(minRange, ceil - floor);
            return Math.min(1, Math.max(0, (lv - floor) / range));
        },
    };
}

/** Tự kiểm tra: dựng phổ tổng hợp có formant biết trước rồi đối chiếu.
 *  Phải trả về "A->A I->I U->U E->E O->O", không có chữ SAI nào. */
export function selfTest(sampleRate = 48000, bins = 1024) {
    const make = (f1, f2) => {
        const db = new Float32Array(bins).fill(-80);
        const binHz = sampleRate / (bins * 2);
        for (let i = 1; i < bins; i++) {
            const hz = i * binHz;
            db[i] = -80
                + 46 * Math.exp(-Math.pow((hz - f1) / 90, 2))
                + 40 * Math.exp(-Math.pow((hz - f2) / 140, 2))
                + 30 * Math.exp(-Math.pow((hz - 220) / 60, 2));
        }
        return db;
    };
    return VOWELS.map(v => {
        const g = classifyVowel(make(v.f1, v.f2), sampleRate);
        const got = g ? g.key : 'null';
        return `${v.key}->${got}${got === v.key ? '' : ' SAI'}`;
    }).join(' ');
}
