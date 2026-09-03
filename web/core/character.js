// Lõi nhân vật: nạp model, đổi trạng thái, đổi kiểu tóc, đổi màu, vật lý tóc
// và khẩu hình. Không đụng tới giao diện studio, nên bản nhúng (embed.js) và
// trang studio (app.js) dùng chung đúng một bản cài đặt.
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { DRACOLoader } from 'three/addons/loaders/DRACOLoader.js';
import { HairPhysics } from './hair.js';
import { classifyVowel, createLoudnessGate } from './lipsync.js';

const STATE_FADE = 0.25;
const VISEME_ATTACK = 14.0;   // tốc độ mở khẩu hình
const VISEME_RELEASE = 7.0;   // tốc độ đóng lại, chậm hơn cho đỡ giật
const VOICE_ONSET = 0.25;     // dưới mức này coi như đang giữa hai câu hát

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

        for (const clip of this.clips) this.actions[clip.name] = this.mixer.clipAction(clip);
        this._prepare();
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
            for (const key in dict) {
                const i = dict[key];
                if (key.includes('MTH_A')) this.morphIndices.A = i;
                else if (key.includes('MTH_I')) this.morphIndices.I = i;
                else if (key.includes('MTH_U') && !key.includes('MTH_Up')) this.morphIndices.U = i;
                else if (key.includes('MTH_E')) this.morphIndices.E = i;
                else if (key.includes('MTH_O')) this.morphIndices.O = i;
            }
        }
        // Không dựng lò xo tóc ở đây: lúc này model chưa vào cảnh và chưa được
        // đặt đúng chỗ, nên vị trí chóp tóc ban đầu sẽ lệch và tóc bị giật lên
        // ở frame đầu. Dựng ở lần update() đầu tiên, khi ma trận đã đúng.
    }

    get stateNames() { return this.manifest.states.map(s => s.clip); }

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
    update(delta, audio = null) {
        this.mixer.update(delta);
        if (!this._hairReady) {
            this.root.updateMatrixWorld(true);
            this.hair.build(this.root);
            this._hairReady = true;
        }
        this.hair.update(delta);
        this._updateVisemes(delta, audio);
    }

    _updateVisemes(delta, audio) {
        let guess = null;
        // Chỉ nhép khi bản đang phát thực sự có giọng hát — điều này được khai
        // báo chứ không đoán từ tín hiệu; xem chú thích trong scripts/catalog.py.
        if (audio && audio.vocals && audio.spectrumDb) {
            const loud = this.gate.level(audio.spectrumDb, audio.sampleRate, delta);
            if (loud > VOICE_ONSET) {
                guess = classifyVowel(audio.spectrumDb, audio.sampleRate);
                if (guess) guess.openness = Math.min(1, (loud - VOICE_ONSET) / 0.55);
            }
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
                if (idx !== undefined) mesh.morphTargetInfluences[idx] = this.visemes[key] * 0.92;
            }
        }
    }
}
