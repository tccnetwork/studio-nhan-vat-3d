// Dò nhịp và tempo của bản nhạc đang phát.
//
// Cách làm: mỗi khung lấy phổ, tính "spectral flux" — tổng phần năng lượng
// TĂNG so với khung trước. Tiếng gõ, tiếng bật dây, phụ âm đầu đều làm năng
// lượng tăng đột ngột, nên đường flux có những đỉnh nhọn ở đúng chỗ có nhịp.
// Tự tương quan đường đó cho ra chu kỳ nhịp; dò pha cho ra vị trí phách.
//
// Module này không đụng tới AudioContext hay DOM: nó nhận phổ đã lấy sẵn qua
// push(). Nhờ vậy kiểm thử được bằng chuỗi phổ tổng hợp có tempo biết trước.

const HISTORY = 420;          // khung giữ lại, ~7 giây ở 60 Hz
const MIN_BPM = 60;
const MAX_BPM = 190;

export class BeatTracker {
    constructor({ rate = 60, minBpm = MIN_BPM, maxBpm = MAX_BPM } = {}) {
        this.rate = rate;                  // số khung mỗi giây
        this.minBpm = minBpm;
        this.maxBpm = maxBpm;
        this.flux = new Float32Array(HISTORY);
        this.n = 0;
        this.prev = null;
        this.bpm = 0;
        this.confidence = 0;
        this.beatPhase = 0;                // 0..1 trong một phách
        this._sinceEstimate = 0;
    }

    /** spectrumDb: Float32Array dB như getFloatFrequencyData. */
    push(spectrumDb, dt = 1 / this.rate) {
        const n = spectrumDb.length;
        if (!this.prev || this.prev.length !== n) {
            this.prev = new Float32Array(n);
            this.prev.set(spectrumDb);
            return;
        }
        // Chỉ lấy phần tăng: nhịp là lúc năng lượng bật lên, không phải lúc tắt.
        let f = 0;
        const top = Math.min(n, Math.floor(n * 0.45));   // bỏ dải rất cao, phần lớn là nhiễu
        for (let i = 1; i < top; i++) {
            const d = spectrumDb[i] - this.prev[i];
            if (d > 0) f += d;
        }
        this.prev.set(spectrumDb);
        this.flux[this.n % HISTORY] = f;
        this.n++;

        this._sinceEstimate += dt;
        if (this.n >= HISTORY / 2 && this._sinceEstimate >= 0.5) {
            this._sinceEstimate = 0;
            this._estimate();
        }
        if (this.bpm > 0) {
            this.beatPhase = (this.beatPhase + dt * this.bpm / 60) % 1;
        }
    }

    _ordered() {
        const len = Math.min(this.n, HISTORY);
        const out = new Float32Array(len);
        const start = this.n >= HISTORY ? this.n % HISTORY : 0;
        for (let i = 0; i < len; i++) out[i] = this.flux[(start + i) % HISTORY];
        // Trừ đường trung bình trượt: chỉ giữ phần nhô lên so với nền.
        const w = 24;
        const sm = new Float32Array(len);
        let run = 0;
        for (let i = 0; i < len; i++) {
            run += out[i];
            if (i >= w) run -= out[i - w];
            sm[i] = run / Math.min(i + 1, w);
        }
        for (let i = 0; i < len; i++) out[i] = Math.max(0, out[i] - sm[i]);
        return out;
    }

    _estimate() {
        const env = this._ordered();
        const len = env.length;
        const loLag = Math.floor(this.rate * 60 / this.maxBpm);
        const hiLag = Math.ceil(this.rate * 60 / this.minBpm);
        if (len < hiLag * 2) return;

        let best = 0, bestScore = 0, mean = 0, count = 0;
        const scores = new Float32Array(hiLag + 1);
        for (let lag = loLag; lag <= hiLag; lag++) {
            let s = 0;
            for (let i = 0; i + lag < len; i++) s += env[i] * env[i + lag];
            s /= (len - lag);
            scores[lag] = s;
            mean += s; count++;
            if (s > bestScore) { bestScore = s; best = lag; }
        }
        if (!best || count === 0) return;
        mean /= count;

        // Sửa lỗi bát độ. Chu kỳ gấp đôi bao giờ cũng tự tương quan mạnh — cứ
        // hai phách thì trùng một lần — nên đỉnh cao nhất hay rơi vào nửa
        // tempo. Nếu chu kỳ bằng một nửa (hoặc một phần ba) vẫn còn mạnh gần
        // bằng, chọn cái ngắn hơn: 160 nhịp mỗi phút bị đọc thành 80 chính là
        // trường hợp này.
        for (const div of [2, 3]) {
            const shorter = Math.round(best / div);
            if (shorter < loLag) continue;
            if (scores[shorter] >= bestScore * 0.62) {
                best = shorter;
                bestScore = scores[shorter];
                break;
            }
        }

        // Nội suy parabol quanh đỉnh cho chu kỳ mịn hơn một khung
        const y0 = scores[best - 1] || 0, y1 = scores[best], y2 = scores[best + 1] || 0;
        const denom = y0 - 2 * y1 + y2;
        const shift = Math.abs(denom) > 1e-9 ? 0.5 * (y0 - y2) / denom : 0;
        const lag = best + Math.max(-1, Math.min(1, shift));

        this.bpm = this.rate * 60 / lag;
        this.confidence = mean > 1e-9 ? bestScore / mean : 0;

        // Pha: thử mọi độ lệch trong một chu kỳ, chọn chỗ tổng flux lớn nhất.
        let bestOff = 0, bestSum = -1;
        const step = Math.max(1, Math.round(lag));
        for (let off = 0; off < step; off++) {
            let s = 0;
            for (let i = len - 1 - off; i >= 0; i -= step) s += env[i];
            if (s > bestSum) { bestSum = s; bestOff = off; }
        }
        this.beatPhase = (bestOff / lag) % 1;
    }

    reset() {
        this.n = 0;
        this.prev = null;
        this.bpm = 0;
        this.confidence = 0;
        this.flux.fill(0);
    }
}

/** Hệ số tua clip để một vòng lặp trùng với một số phách nguyên của bài hát.
 *
 *  Không cần biết clip ứng với mấy phách nhạc: chọn số phách n sao cho tốc độ
 *  phát lệch ít nhất so với 1,0 — nhờ vậy điệu nhảy vừa khớp lưới nhịp vừa giữ
 *  gần đúng tốc độ gốc.
 */
export function matchTimeScale(clipSeconds, bpm, { maxDeviation = 0.35 } = {}) {
    if (!bpm || !clipSeconds) return { timeScale: 1, beats: 0 };
    const beatSec = 60 / bpm;
    let best = null;
    for (let n = 1; n <= 32; n++) {
        const scale = clipSeconds / (n * beatSec);
        const dev = Math.abs(Math.log(scale));
        if (!best || dev < best.dev) best = { dev, scale, beats: n };
    }
    if (!best || best.dev > Math.log(1 + maxDeviation)) {
        return { timeScale: 1, beats: 0 };
    }
    return { timeScale: best.scale, beats: best.beats };
}
