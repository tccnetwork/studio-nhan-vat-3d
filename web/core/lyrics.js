// Nhép miệng theo lời bài hát khi lời KHÔNG có mốc thời gian.
//
// Có lời kèm mốc thời gian (.lrc) thì mọi thứ dễ: cứ tới giây nào thì hát chữ
// nào. Chỉ có lời trần thì phải chia việc:
//
//     thời điểm  <- lấy từ âm thanh (mỗi âm tiết bật lên là một mốc)
//     nguyên âm  <- lấy từ lời (chữ thứ n trong câu)
//
// Cách này đoán hình miệng chính xác hơn hẳn dò formant trên bản phối, vì
// tiếng Việt và tiếng Nhật đều một âm tiết một nguyên âm chính. Đổi lại nó có
// thể trôi: bộ dò bỏ sót hay đếm thừa một âm tiết là lệch cả câu. Nên mỗi
// khoảng lặng đủ dài được coi là hết câu, và con trỏ nhảy về đầu câu kế —
// chỗ nghỉ lấy hơi trở thành mốc chỉnh lại.

const VOWEL_MAP = {
    a: 'A', e: 'E', i: 'I', o: 'O', u: 'U', y: 'I',
};

// Phụ âm phát ra bằng MÔI. Muốn kêu được /m/, /b/, /p/ thì hai môi phải chạm
// hẳn vào nhau, còn /ph/, /v/ thì môi dưới chạm răng trên — đóng một nửa.
// Đây là chỗ hụt lớn nhất của bản cũ: miệng chưa bao giờ khép giữa câu, mà
// tiếng Việt thì đầy âm tiết đóng bằng môi ("em", "đẹp", "mưa", "bên").
const ONSET_FULL = /^(m|b|p)/;         // mím hẳn trước khi bật ra
const ONSET_HALF = /^(ph|v)/;          // môi dưới chạm răng
const CODA_FULL = /(m|p)$/;            // âm tiết đóng lại bằng môi

/** Một âm tiết cần mím môi ở đầu và ở cuối bao nhiêu (0..1). */
export function syllableLips(word) {
    const plain = stripMarks(word).replace(/[^a-z]/g, '');
    if (!plain) return { closeIn: 0, closeOut: 0 };
    return {
        closeIn: ONSET_HALF.test(plain) ? 0.55 : (ONSET_FULL.test(plain) ? 1 : 0),
        closeOut: CODA_FULL.test(plain) ? 1 : 0,
    };
}

/** Bỏ dấu tiếng Việt để còn lại chữ cái gốc. */
function stripMarks(word) {
    return word.normalize('NFD')
        .replace(/[̀-ͯ]/g, '')
        .replace(/đ/g, 'd').replace(/Đ/g, 'D')
        .toLowerCase();
}

/** Chuỗi nguyên âm của một âm tiết, ví dụ "tiếng" -> ['I','E'].
 *  Lấy tối đa hai nguyên âm: miệng chuyển qua cả hai trong một nguyên âm đôi. */
export function syllableVowels(word) {
    const plain = stripMarks(word).replace(/[^a-z]/g, '');
    const out = [];
    for (const ch of plain) {
        const v = VOWEL_MAP[ch];
        if (!v) continue;
        if (out[out.length - 1] !== v) out.push(v);
        if (out.length === 2) break;
    }
    return out.length ? out : ['A'];   // âm tiết không có nguyên âm thì mở nhẹ
}

/** Tách lời trần thành câu và âm tiết. Xuống dòng là hết câu. */
export function parseLyrics(text) {
    return String(text || '')
        .split(/\r?\n/)
        .map(line => line.trim())
        .filter(line => line.length > 0 && !/^\[/.test(line))
        .map(line => ({
            text: line,
            syllables: line.split(/[\s,.;:!?—–-]+/)
                .filter(Boolean)
                .map(w => ({ word: w, vowels: syllableVowels(w), ...syllableLips(w) })),
        }))
        .filter(l => l.syllables.length > 0);
}

export class LyricsDriver {
    constructor(text, {
        onsetRise = 0.16,      // mức tăng so với nền gần nhất, coi là âm tiết mới
        minGap = 0.11,         // giây, hai âm tiết không thể sát hơn thế
        lineBreak = 0.9,       // giây im tiếng thì coi là hết câu
        floorRise = 2.2,       // tốc độ nền bò lên, mỗi giây
        maxHold = 0.55,        // giữ một khẩu hình lâu hơn thế thì tự sang chữ kế
        closeOutAt = 0.55,     // qua bấy nhiêu phần âm tiết thì bắt đầu khép cuối
        closeInAt = 0.78,      // qua bấy nhiêu phần thì mím sẵn cho chữ kế
    } = {}) {
        this.lines = parseLyrics(text);
        this.onsetRise = onsetRise;
        this.minGap = minGap;
        this.lineBreak = lineBreak;
        this.floorRise = floorRise;
        this.maxHold = maxHold;
        this.closeOutAt = closeOutAt;
        this.closeInAt = closeInAt;
        this.close = 0;        // mức mím môi cần có ngay lúc này, 0..1
        this.period = 0.3;     // khoảng cách trung bình giữa hai âm tiết, giây
        this.line = 0;
        this.syl = -1;
        this.vowel = null;
        // Đặt lớn sẵn: nếu bắt đầu từ 0 thì chính bộ lọc khoảng cách tối thiểu
        // sẽ từ chối âm tiết ĐẦU TIÊN, và cả câu lệch đi một chữ.
        this.since = 99;       // giây kể từ âm tiết gần nhất
        this.quiet = 0;        // giây đang im tiếng
        // Nền để đo cú tăng. Trước đây chỗ này so mức to của KHUNG NÀY với
        // KHUNG TRƯỚC, cách nhau khoảng 16 ms — mà mức to đã bị làm trơn nên
        // không bao giờ nhảy nổi 0,16 trong ngần ấy thời gian. Hậu quả đo được:
        // cả bài chỉ bắt được đúng một âm tiết, miệng đứng nguyên chữ đầu tiên
        // suốt 32 giây. Nền tụt ngay khi nhạc nhỏ lại và bò lên chậm, nên cú
        // tăng được đo trên khoảng vài trăm mili giây, đúng độ dài một âm tiết.
        this._floor = 0;
        this._sub = 0;         // vị trí trong nguyên âm đôi
    }

    get totalSyllables() {
        return this.lines.reduce((n, l) => n + l.syllables.length, 0);
    }

    /** Âm tiết kế tiếp trong câu, để mím môi SẴN trước khi nó bật ra.
     *  Phải mím trước: cú bật /m/, /b/, /p/ chỉ kêu được khi hai môi đang chạm
     *  nhau, mà bộ dò khởi âm lại bắt đúng vào lúc nó đã bật rồi. */
    _next() {
        const line = this.lines[this.line];
        if (!line) return null;
        if (this.syl + 1 < line.syllables.length) return line.syllables[this.syl + 1];
        const nl = this.lines[(this.line + 1) % this.lines.length];
        return nl && nl.syllables.length ? nl.syllables[0] : null;
    }

    /** Mức mím môi cần có ở thời điểm hiện tại. */
    _lipClose() {
        if (this.quiet > 0.35) return 0.55;      // nghỉ giữa câu: môi khép hờ
        const line = this.lines[this.line];
        if (!line || this.syl < 0) return 0;
        const cur = line.syllables[this.syl];
        if (!cur) return 0;
        const p = Math.max(0.12, Math.min(0.9, this.period));
        const phase = this.since / p;
        let close = 0;
        // Nửa sau của âm tiết: khép lại nếu âm tiết kết thúc bằng môi.
        if (cur.closeOut && phase > this.closeOutAt) {
            close = cur.closeOut
                * Math.min(1, (phase - this.closeOutAt) / (1 - this.closeOutAt));
        }
        // Sát chữ kế: mím sẵn nếu chữ ấy mở đầu bằng môi.
        const nx = this._next();
        if (nx && nx.closeIn && phase > this.closeInAt) {
            close = Math.max(close, nx.closeIn
                * Math.min(1, (phase - this.closeInAt) / (1 - this.closeInAt)));
        }
        return Math.min(1, close);
    }

    /** level: mức to của giọng, 0..1. Trả về nguyên âm đang cần mở, hoặc null. */
    push(level, dt) {
        this.since += dt;
        if (level < 0.18) {
            this.quiet += dt;
            if (this.quiet > this.lineBreak && this.syl >= 0) {
                // Hết câu: nhảy về đầu câu kế, coi chỗ lấy hơi là mốc chỉnh lại.
                this.line = (this.line + 1) % Math.max(1, this.lines.length);
                this.syl = -1;
                this.vowel = null;
            }
        } else {
            this.quiet = 0;
        }

        if (level < this._floor) this._floor = level;
        else this._floor += Math.min(1, this.floorRise * dt) * (level - this._floor);
        const rise = level - this._floor;

        // Hát liền hơi thì không có cú tăng nào rõ rệt. Giữ mãi một khẩu hình
        // trông như bị đơ, nên quá maxHold mà vẫn đang có tiếng thì sang chữ kế.
        const stuck = this.since > this.maxHold && level > 0.25;

        if ((rise > this.onsetRise || stuck) && this.since > this.minGap && this.lines.length) {
            // Nhịp âm tiết đo từ chính khoảng cách vừa qua, bám mềm để một cú
            // bắt hụt không kéo lệch cả câu.
            if (this.since < 1.2) this.period += (this.since - this.period) * 0.35;
            this.since = 0;
            this._floor = level;
            const line = this.lines[this.line];
            this.syl++;
            if (this.syl >= line.syllables.length) {
                this.line = (this.line + 1) % this.lines.length;
                this.syl = 0;
            }
            this._sub = 0;
            this.vowel = this.lines[this.line].syllables[this.syl].vowels[0];
        } else if (this.vowel && this.syl >= 0) {
            // Nguyên âm đôi: nửa sau của âm tiết chuyển sang nguyên âm thứ hai.
            const vs = this.lines[this.line].syllables[this.syl].vowels;
            if (vs.length > 1 && this.since > 0.10 && this._sub === 0) {
                this._sub = 1;
                this.vowel = vs[1];
            }
        }
        if (this.quiet > 0.25) this.vowel = null;
        this.close = this._lipClose();
        return this.vowel;
    }

    reset() {
        this.line = 0; this.syl = -1; this.vowel = null;
        this.since = 99; this.quiet = 0; this._floor = 0; this._sub = 0;
        this.close = 0; this.period = 0.3;
    }
}
