// Lõi nhân vật: nạp model, đổi trạng thái, đổi kiểu tóc, đổi màu, vật lý tóc
// và khẩu hình. Không đụng tới giao diện studio, nên bản nhúng (embed.js) và
// trang studio (app.js) dùng chung đúng một bản cài đặt.
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { DRACOLoader } from 'three/addons/loaders/DRACOLoader.js';
import { HairPhysics } from './hair.js';
import { classifyVowel, createLoudnessGate } from './lipsync.js';
import { BeatTracker, matchTimeScale } from './beat.js';
import { LyricsDriver } from './lyrics.js';
import { AliveLayer } from './alive.js';
import { Choreographer } from './choreo.js';

const STATE_FADE = 0.25;
const VISEME_ATTACK = 14.0;   // tốc độ mở khẩu hình
const VISEME_RELEASE = 7.0;   // tốc độ đóng lại, chậm hơn cho đỡ giật
const VOICE_ONSET = 0.25;     // dưới mức này coi như đang giữa hai câu hát
const GESTURE_FADE = 0.35;    // giây hoà cho lớp tay đắp thêm
const GESTURE_WEIGHT = 0.85;  // đắp gần hết, chừa lại chút nền cho tay còn nhịp
// Xương thuộc tầng đắp thêm. Chỉ thân trên: hông và chân phải để nguyên cho
// clip nền giữ, nếu không dáng tay tĩnh sẽ ghì luôn cả bước nhảy.
const UPPER_BODY = /Spine|Chest|Neck|Head|Shoulder|Arm|Hand|Thumb|Index|Middle|Ring|Little/;
const LOWER_BODY = /Hips|UpperLeg|LowerLeg|Foot|Toe/;

export async function loadManifest(url) {
    const res = await fetch(url + (url.includes('?') ? '' : '?v=' + Date.now()));
    if (!res.ok) throw new Error(`không đọc được ${url}: HTTP ${res.status}`);
    return res.json();
}

export class Character {
    constructor(gltf, manifest) {
        this.manifest = manifest;
        this.root = gltf.scene;
        this.clips = gltf.animations;
        this.mixer = new THREE.AnimationMixer(this.root);
        this.actions = {};
        this.current = null;
        this.currentName = null;

        this.morphMeshes = [];
        this.morphIndices = {};
        this.hairMeshes = {};
        this.hair = new HairPhysics();
        this.gate = createLoudnessGate();
        this.visemes = { A: 0, I: 0, U: 0, E: 0, O: 0 };
        this.beat = new BeatTracker();
        this.beatSync = true;        // cho điệu nhảy chạy theo nhịp bài hát
        this._syncedFor = null;
        this.lyrics = null;          // LyricsDriver khi người dùng dán lời vào
        this.alive = new AliveLayer();
        this.choreo = new Choreographer(manifest);
        this.gestureActions = {};
        this.gesture = null;
        this._loud = 0;

        this._removeRootDrift();
        for (const clip of this.clips) this.actions[clip.name] = this.mixer.clipAction(clip);
        this._prepareGestures();
        this._prepare();
        this.alive.build(this.root);
    }

    static async load({ manifestUrl, buildDir, dracoPath }) {
        const manifest = await loadManifest(manifestUrl);
        const loader = new GLTFLoader();
        const draco = new DRACOLoader();
        draco.setDecoderPath(dracoPath);
        loader.setDRACOLoader(draco);
        const gltf = await loader.loadAsync(
            buildDir + manifest.model + '?v=' + encodeURIComponent(manifest.generated));
        return new Character(gltf, manifest);
    }

    _prepare() {
        this.root.traverse(child => {
            if (!child.isMesh) return;
            child.castShadow = true;
            child.receiveShadow = true;
            if (child.material) child.material.side = THREE.DoubleSide;
            if (child.morphTargetInfluences && child.morphTargetInfluences.length) {
                this.morphMeshes.push(child);
            }
            const entry = this.manifest.hairstyles.find(h => h.mesh === child.name);
            if (entry) {
                this.hairMeshes[entry.key] = child;
                child.visible = !!entry.default;
            }
        });

        for (const mesh of this.morphMeshes) {
            const dict = mesh.morphTargetDictionary || {};
            // So khớp CHÍNH XÁC tên morph, không dùng chuỗi con: "Fcl_MTH_Angry"
            // cũng chứa "MTH_A", và trước đây nó chỉ thua vì tình cờ đứng trước
            // Fcl_MTH_A trong danh sách. Đổi thứ tự một cái là miệng chữ A biến
            // thành miệng giận dữ.
            const WANT = { Fcl_MTH_A: 'A', Fcl_MTH_I: 'I', Fcl_MTH_U: 'U',
                           Fcl_MTH_E: 'E', Fcl_MTH_O: 'O' };
            for (const key in dict) {
                const slot = WANT[key.split('.').pop()];
                if (slot) this.morphIndices[slot] = dict[key];
            }
        }
        // Không dựng lò xo tóc ở đây: lúc này model chưa vào cảnh và chưa được
        // đặt đúng chỗ, nên vị trí chóp tóc ban đầu sẽ lệch và tóc bị giật lên
        // ở frame đầu. Dựng ở lần update() đầu tiên, khi ma trận đã đúng.
    }

    get stateNames() { return this.manifest.states.map(s => s.clip); }

    /** Khử độ trôi ngang của xương gốc.
     *
     *  Đo trên file đã xuất: clip vũ đạo dài trôi 385 mm mỗi vòng lặp, clip vũ
     *  đạo ngắn trôi 54 mm. Lặp vài lần là nhân vật đi khỏi khung hình. Ở đây
     *  trừ đi đúng phần trôi tuyến tính nên nhịp lắc hông vẫn còn nguyên, chỉ
     *  có chỗ đứng là quay lại điểm xuất phát sau mỗi vòng.
     *
     *  Đánh đổi: bàn chân sẽ trượt nhẹ so với sàn, vì chuyển động gốc vốn là
     *  thứ bù cho bước chân. Trôi khỏi sân khấu vẫn tệ hơn nhiều.
     */
    _removeRootDrift() {
        for (const st of this.manifest.states) {
            const d = st.driftMm;
            if (!d || (Math.abs(d[0]) < 5 && Math.abs(d[2]) < 5)) continue;
            const clip = this.clips.find(c => c.name === st.clip);
            if (!clip) continue;
            const track = clip.tracks.find(
                t => t.name.includes('Hips') && t.name.endsWith('.position'));
            if (!track) continue;
            const v = track.values;
            const n = v.length / 3;
            if (n < 2) continue;
            const dx = v[(n - 1) * 3] - v[0];
            const dz = v[(n - 1) * 3 + 2] - v[2];
            for (let i = 0; i < n; i++) {
                const k = i / (n - 1);
                v[i * 3] -= k * dx;
                v[i * 3 + 2] -= k * dz;
            }
        }
    }

    /** Dựng tầng tay đắp thêm từ các clip đứng hình.
     *
     *  Một tư thế bất động chính là thứ phép trộn cộng thêm cần: lấy hiệu giữa
     *  nó và thế đứng nghỉ thì được đúng "phần tay" của động tác, đắp lên bất
     *  kỳ clip nền nào cũng được. Nhờ vậy 10 ảnh tĩnh vốn vô dụng khi đứng một
     *  mình trở thành 10 dáng tay dùng chung với 2 nền vũ đạo.
     */
    _prepareGestures() {
        const idle = this.clips.find(c => /DungNghiem/.test(c.name)) || this.clips[0];
        if (!idle) return;
        for (const st of this.manifest.states) {
            if (st.kind !== 'pose') continue;
            const src = this.clips.find(c => c.name === st.clip);
            if (!src) continue;
            const clip = src.clone();
            clip.name = st.clip + '__gesture';
            clip.tracks = clip.tracks.filter(t => {
                const bone = t.name.split('.')[0];
                return UPPER_BODY.test(bone) && !LOWER_BODY.test(bone);
            });
            if (!clip.tracks.length) continue;
            THREE.AnimationUtils.makeClipAdditive(clip, 0, idle, 30);
            const action = this.mixer.clipAction(clip);
            action.blendMode = THREE.AdditiveAnimationBlendMode;
            action.loop = THREE.LoopRepeat;
            action.enabled = true;
            action.setEffectiveWeight(0);
            this.gestureActions[st.clip] = action;
        }
    }

    /** Đắp một dáng tay lên trên clip nền. Truyền chuỗi rỗng để hạ tay xuống. */
    setGesture(clipName, fade = GESTURE_FADE) {
        if (clipName === this.gesture) return false;
        const prev = this.gestureActions[this.gesture];
        if (prev) prev.fadeOut(fade);
        const next = clipName ? this.gestureActions[clipName] : null;
        if (next) {
            next.reset().play();
            next.setEffectiveWeight(0);
            next.fadeIn(fade);
            next.setEffectiveWeight(GESTURE_WEIGHT);
        }
        this.gesture = next ? clipName : '';
        return true;
    }

    /** Bật/tắt chế độ tự dựng bài theo nhạc. */
    setChoreography(on) {
        this.choreo.enabled = !!on;
        if (!on) {
            this.setGesture('');
            this.choreo.reset();
        }
        return this.choreo.enabled;
    }

    /** Đổi trạng thái, hoà mềm và **dừng hẳn** clip cũ.
     *  fadeOut chỉ hạ trọng số về 0 chứ không dừng action: mixer vẫn tính lại
     *  nó mỗi frame, mãi mãi. */
    setState(clipName, fade = STATE_FADE) {
        const next = this.actions[clipName];
        if (!next || next === this.current) return false;
        const prev = this.current;
        if (prev) {
            prev.fadeOut(fade);
            setTimeout(() => { if (this.current !== prev) prev.stop(); }, fade * 1000 + 60);
        }
        next.reset().fadeIn(fade).play();
        this.current = next;
        this.currentName = clipName;
        return true;
    }

    /** Dán lời bài hát (không cần mốc thời gian) để lấy nguyên âm theo chữ.
     *  Truyền chuỗi rỗng hoặc null để quay lại đoán nguyên âm từ formant. */
    setLyrics(text) {
        const t = String(text || '').trim();
        this.lyrics = t ? new LyricsDriver(t) : null;
        return this.lyrics
            ? { lines: this.lyrics.lines.length, syllables: this.lyrics.totalSyllables }
            : null;
    }

    setHairstyle(key) {
        for (const k in this.hairMeshes) this.hairMeshes[k].visible = (k === key);
    }

    setColor(part, hex) {
        const names = this.manifest.materialGroups[part];
        if (!names) return;
        const color = new THREE.Color(hex);
        this.root.traverse(child => {
            if (!child.isMesh || !child.material) return;
            const mats = Array.isArray(child.material) ? child.material : [child.material];
            for (const mat of mats) {
                if (names.includes(mat.name) && mat.color) mat.color.copy(color);
            }
        });
    }

    /** delta tính bằng giây. audio là { spectrumDb, sampleRate, vocals } hoặc null. */
    /** Trạng thái nào nên chạy theo nhịp, khai báo trong scripts/catalog.py. */
    _stateInfo(clip) {
        return this.manifest.states.find(s => s.clip === clip) || null;
    }

    /** Danh sách clip vũ đạo, để tự chuyển sang khi bật nhạc. */
    get danceStates() {
        return this.manifest.states.filter(s => s.dance).map(s => s.clip);
    }

    _syncTempo() {
        const st = this._stateInfo(this.currentName);
        if (!this.current) return;
        // Ngưỡng 4 chứ không phải 6: xem chú thích minConfidence trong choreo.js —
        // đo trên nhạc thật thì 6 loại mất phần lớn các lần dò đúng.
        if (!this.beatSync || !st || !st.beatSync || this.beat.confidence < 4) {
            if (this.current.timeScale !== 1) this.current.timeScale = 1;
            this._syncedFor = null;
            return;
        }
        const key = `${this.currentName}|${this.beat.bpm.toFixed(1)}`;
        if (key === this._syncedFor) return;
        const seconds = this.current.getClip().duration;
        const m = matchTimeScale(seconds, this.beat.bpm);
        this.current.timeScale = m.timeScale;
        this._syncedFor = key;
    }

    update(delta, audio = null) {
        this._loud = (audio && audio.spectrumDb)
            ? this.gate.level(audio.spectrumDb, audio.sampleRate, delta) : 0;

        // Bộ dựng bài ra quyết định trước khi mixer chạy, để cú hoà bắt đầu
        // ngay từ khung hình của đầu phách.
        const move = this.choreo.update(delta, this.beat);
        if (move.base) this.setState(move.base);
        if (move.gesture !== null) this.setGesture(move.gesture);

        this.mixer.update(delta);
        // Lớp sống phải chạy SAU mixer: nó cộng thêm lên tư thế vừa dựng xong.
        // Chạy trước thì mixer ghi đè và không thấy gì.
        this.alive.update(delta, this.beat, this._loud);
        if (!this._hairReady) {
            this.root.updateMatrixWorld(true);
            this.hair.build(this.root, this.manifest.hairColliders || []);
            this._hairReady = true;
        }
        this.hair.update(delta);
        this._updateVisemes(delta, audio);
        if (audio && audio.spectrumDb) this.beat.push(audio.spectrumDb, delta);
        this._syncTempo();
    }

    _updateVisemes(delta, audio) {
        let guess = null;
        // Chỉ nhép khi bản đang phát thực sự có giọng hát — điều này được khai
        // báo chứ không đoán từ tín hiệu; xem chú thích trong scripts/catalog.py.
        if (audio && audio.vocals && audio.spectrumDb) {
            // Đã đo ở update(); cổng lọc có trạng thái nên gọi lần nữa sẽ khiến
            // nó thích nghi nhanh gấp đôi.
            const loud = this._loud;
            if (this.lyrics) {
                // Có lời: thời điểm lấy từ âm thanh, nguyên âm lấy từ chữ.
                // Chính xác hơn hẳn đoán formant trên bản phối đã trộn nhạc cụ.
                const key = this.lyrics.push(loud, delta);
                if (key) guess = { key, openness: Math.min(1, Math.max(0.25, loud)) };
            } else if (loud > VOICE_ONSET) {
                guess = classifyVowel(audio.spectrumDb, audio.sampleRate);
                // Có sàn 0,45: khẩu hình mở he hé thì người xem không nhận ra
                // là đang hát. Đã có cổng lọc mức to chặn đoạn không có giọng
                // nên mở rõ ở đây là an toàn.
                if (guess) guess.openness = Math.min(1, 0.45 + (loud - VOICE_ONSET) / 0.45);
            }
        } else if (this.lyrics) {
            this.lyrics.push(0, delta);
        }
        for (const key in this.visemes) {
            const target = guess && guess.key === key ? guess.openness : 0;
            const rate = target > this.visemes[key] ? VISEME_ATTACK : VISEME_RELEASE;
            this.visemes[key] += (target - this.visemes[key]) * Math.min(1, rate * delta);
        }
        for (const mesh of this.morphMeshes) {
            if (!mesh.morphTargetInfluences) continue;
            for (const key in this.visemes) {
                const idx = this.morphIndices[key];
                if (idx !== undefined) mesh.morphTargetInfluences[idx] = this.visemes[key];
            }
        }
    }
}
