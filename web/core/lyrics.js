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
                .map(w => ({ word: w, vowels: syllableVowels(w) })),
        }))
        .filter(l => l.syllables.length > 0);
}

export class LyricsDriver {
    constructor(text, {
        onsetRise = 0.16,      // mức tăng coi là một âm tiết mới
        minGap = 0.11,         // giây, hai âm tiết không thể sát hơn thế
        lineBreak = 0.9,       // giây im tiếng thì coi là hết câu
    } = {}) {
        this.lines = parseLyrics(text);
        this.onsetRise = onsetRise;
        this.minGap = minGap;
        this.lineBreak = lineBreak;
        this.line = 0;
        this.syl = -1;
        this.vowel = null;
        // Đặt lớn sẵn: nếu bắt đầu từ 0 thì chính bộ lọc khoảng cách tối thiểu
        // sẽ từ chối âm tiết ĐẦU TIÊN, và cả câu lệch đi một chữ.
        this.since = 99;       // giây kể từ âm tiết gần nhất
        this.quiet = 0;        // giây đang im tiếng
        this._prev = 0;
        this._sub = 0;         // vị trí trong nguyên âm đôi
    }

    get totalSyllables() {
        return this.lines.reduce((n, l) => n + l.syllables.length, 0);
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

        const rise = level - this._prev;
        this._prev = level;
        if (rise > this.onsetRise && this.since > this.minGap && this.lines.length) {
            this.since = 0;
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
        return this.vowel;
    }

    reset() {
        this.line = 0; this.syl = -1; this.vowel = null;
        this.since = 99; this.quiet = 0; this._prev = 0; this._sub = 0;
    }
}
