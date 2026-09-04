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
// Formant được dò QUANH vị trí riêng của từng nguyên âm chứ không lấy một đỉnh
// to nhất toàn dải. Lý do: trên bản phối đã trộn nhạc cụ, đỉnh to nhất trong
// dải F1 gần như luôn là tiếng bass 250–450 Hz, nên F1 dò ra luôn thấp và
// nguyên âm A (F1 ≈ 850) trở thành bất khả thi — miệng chỉ chúm chím U/I/O,
// nhìn không ra đang hát. Đo được: đỉnh của A đứng yên ở 0,0 suốt cả bài.
const F1_SPAN = 0.45;         // dò trong khoảng ±45% quanh F1 chuẩn
const F2_SPAN = 0.35;
// Phạt theo khoảng cách log tới formant chuẩn. Không có nó thì các cửa sổ dò
// chồng lấn nhau và một đỉnh mạnh duy nhất nuôi điểm cho nhiều nguyên âm cùng
// lúc — đo được: F2 của U ở 950 Hz lọt vào cửa sổ F2 của A nên A thắng cả trên
// tiếng U. Có phạt thì đỉnh phải vừa nổi vừa ĐÚNG CHỖ mới ghi điểm.
const F1_PENALTY = 430;
const F2_PENALTY = 340;
const VOICE_BAND = [90, 4000];
const MIN_PROMINENCE = 1.2;   // dB nổi trên bao hình; dưới mức này coi như không có giọng
const ENV_SPAN = 0.45;        // bề rộng cửa sổ tính bao hình, theo tỉ lệ tần số

/** Độ nổi của từng bin so với bao hình phổ trơn quanh nó.
 *
 *  Bản phối nào cũng nghiêng mạnh về phía trầm, và chính độ nghiêng đó kéo mọi
 *  phép dò đỉnh xuống vùng bass. Trừ đi bao hình thì chỉ còn lại các cộng hưởng
 *  hẹp — tức là formant. Cửa sổ rộng theo tỉ lệ tần số nên đều nhau trên thang
 *  log, đúng cách tai người nghe.
 */
function prominence(db, out) {
    const n = db.length;
    const cum = prominence._cum && prominence._cum.length === n + 1
        ? prominence._cum : (prominence._cum = new Float64Array(n + 1));
    for (let i = 0; i < n; i++) {
        const v = db[i];
        cum[i + 1] = cum[i] + (isFinite(v) ? v : -120);
    }
    out[0] = 0;
    for (let i = 1; i < n; i++) {
        const lo = Math.max(1, Math.floor(i * (1 - ENV_SPAN)));
        const hi = Math.min(n - 1, Math.ceil(i * (1 + ENV_SPAN)));
        const mean = (cum[hi + 1] - cum[lo]) / (hi - lo + 1);
        out[i] = (isFinite(db[i]) ? db[i] : -120) - mean;
    }
    return out;
}

/** Đỉnh tốt nhất quanh một formant chuẩn: vừa nổi cao, vừa gần đúng tần số. */
function peakProm(prom, binHz, fRef, span, penalty) {
    const from = Math.max(1, Math.floor(fRef * (1 - span) / binHz));
    const to = Math.min(prom.length - 1, Math.ceil(fRef * (1 + span) / binHz));
    let best = -Infinity, at = from;
    for (let i = from; i <= to; i++) {
        const d = Math.log((i * binHz) / fRef);
        const score = prom[i] - penalty * d * d;
        if (score > best) { best = score; at = i; }
    }
    return { prom: best, hz: at * binHz };
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
    const binHz = sampleRate / (db.length * 2);
    const prom = classifyVowel._buf && classifyVowel._buf.length === db.length
        ? classifyVowel._buf : (classifyVowel._buf = new Float32Array(db.length));
    prominence(db, prom);

    // Chấm điểm từng nguyên âm bằng độ nổi quanh CHÍNH cặp formant của nó. Cách
    // này khiến mọi nguyên âm đều có cơ hội ngang nhau, kể cả A ở vùng tần số
    // mà tiếng bass không với tới.
    let best = null, bestScore = -Infinity, bestWeak = -Infinity, bf1 = 0, bf2 = 0;
    for (const v of VOWELS) {
        const p1 = peakProm(prom, binHz, v.f1, F1_SPAN, F1_PENALTY);
        const p2 = peakProm(prom, binHz, v.f2, F2_SPAN, F2_PENALTY);
        // Đòi CẢ HAI formant cùng đúng: formant yếu hơn được nhân đôi trọng số.
        // Nếu chỉ cộng hai điểm lại thì một đỉnh mạnh duy nhất đủ sức gánh cho
        // một giả thuyết sai — đo được: đỉnh F2 của U ở 950 Hz một mình kéo A
        // thắng ngay trên chính tiếng U.
        const weak = Math.min(p1.prom, p2.prom);
        const score = 2 * weak + Math.max(p1.prom, p2.prom);
        if (score > bestScore) {
            bestScore = score; bestWeak = weak; best = v.key; bf1 = p1.hz; bf2 = p2.hz;
        }
    }
    // Không có cộng hưởng nào nổi rõ thì đang là đoạn nhạc cụ: ngậm miệng còn
    // hơn mấp máy bừa.
    if (bestWeak < MIN_PROMINENCE) return null;
    return { key: best, f1: bf1, f2: bf2, prominence: bestWeak };
}

/** Cổng lọc mức to, tự bám nền và trần.
 *
 *  Không dùng ngưỡng dB tuyệt đối: giá trị getFloatFrequencyData phụ thuộc mức
 *  thu và cách phối của từng bản, nên một con số cứng chỉ đúng với đúng một file.
 */
export function createLoudnessGate({
    snap = 12.0,        // tốc độ bám theo hướng "mở rộng", mỗi giây
    floorUp = 0.85,     // nền bò lên, hằng số thời gian ~1,2 giây
    ceilDown = 0.40,    // trần tụt xuống, hằng số thời gian ~2,5 giây
    minRange = 8,       // dB, khoảng động nhỏ nhất còn coi là có nghĩa
} = {}) {
    let floor = null, ceil = null;
    return {
        reset() { floor = null; ceil = null; },
        /** Trả về 0..1: 0 là im tiếng, 1 là to bằng đoạn to nhất gần đây.
         *
         *  Nền phải hồi lên trong khoảng một giây. Bản cũ cho nền bò lên với
         *  hằng số thời gian 125 giây và trần tụt trong 50 giây, nên sau vài
         *  giây đầu bài, nền dính luôn ở chỗ im nhất từng gặp và mọi thứ sau
         *  đó nằm sát trần. Đo trên bài thật: p10 0,85 · p50 0,92 · p90 0,98,
         *  tức là cổng gần như trả về hằng số 1. Hệ quả: khẩu hình lúc nào
         *  cũng mở hết cỡ, "miệng nhỏ" không bao giờ bật, và câu hát to hay
         *  nhỏ đều ra một hình miệng.
         */
        level(db, sampleRate, delta) {
            const lv = bandEnergyDb(db, sampleRate);
            if (!isFinite(lv)) return 0;
            if (floor === null) { floor = lv; ceil = lv + minRange; }
            const fast = Math.min(1, snap * delta);
            floor += (lv < floor ? fast : Math.min(1, floorUp * delta)) * (lv - floor);
            ceil += (lv > ceil ? fast : Math.min(1, ceilDown * delta)) * (lv - ceil);
            const range = Math.max(minRange, ceil - floor);
            return Math.min(1, Math.max(0, (lv - floor) / range));
        },
    };
}

/** Tự kiểm tra: dựng phổ tổng hợp có formant biết trước rồi đối chiếu.
 *
 *  Ca "trần" là giọng hát sạch. Ca "có nhạc" thêm tiếng bass rất to ở 300 Hz và
 *  độ nghiêng phổ về phía trầm — đúng thứ có trong mọi bản phối thật, và đúng
 *  thứ từng làm nguyên âm A không bao giờ được chọn. Cả hai ca phải đúng hết.
 */
export function selfTest(sampleRate = 48000, bins = 1024) {
    const make = (f1, f2, band) => {
        const db = new Float32Array(bins).fill(-80);
        const binHz = sampleRate / (bins * 2);
        for (let i = 1; i < bins; i++) {
            const hz = i * binHz;
            db[i] = -80
                + 46 * Math.exp(-Math.pow((hz - f1) / 90, 2))
                + 40 * Math.exp(-Math.pow((hz - f2) / 140, 2))
                + 30 * Math.exp(-Math.pow((hz - 220) / 60, 2));
            if (band) {
                db[i] += 52 * Math.exp(-Math.pow((hz - 300) / 70, 2))   // bass
                       + 44 * Math.exp(-Math.pow((hz - 150) / 50, 2))   // trống
                       + 18 * Math.exp(-hz / 900);                      // nghiêng về trầm
            }
        }
        return db;
    };
    const run = band => VOWELS.map(v => {
        const g = classifyVowel(make(v.f1, v.f2, band), sampleRate);
        const got = g ? g.key : 'null';
        return `${v.key}->${got}${got === v.key ? '' : ' SAI'}`;
    }).join(' ');
    const silence = classifyVowel(new Float32Array(bins).fill(-90), sampleRate);
    return 'tran:    ' + run(false) + '\ncó nhạc: ' + run(true)
         + '\nim lặng: ' + (silence ? 'SAI (đáng lẽ ngậm miệng)' : 'ngậm miệng, đúng');
}
