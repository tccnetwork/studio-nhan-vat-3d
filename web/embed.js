// Nhúng nhân vật vào một trang bất kỳ.
//
//   <script type="importmap">
//     { "imports": {
//         "three": "https://cdn.jsdelivr.net/npm/three@0.180.0/build/three.module.js",
//         "three/addons/": "https://cdn.jsdelivr.net/npm/three@0.180.0/examples/jsm/" } }
//   </script>
//   <script type="module">
//     import { createSinger } from './web/embed.js';
//     const singer = await createSinger('#slot', { state: '15_BuocDi_Mocap' });
//     singer.setHairstyle('bob');
//   </script>
//
// Mọi đường dẫn tài nguyên suy ra từ vị trí của chính file này, nên trang chủ
// nhà nằm ở đâu cũng được.
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { Character } from './core/character.js';
import { FrameController } from './core/framing.js';

const HERE = new URL('./', import.meta.url);

export async function createSinger(target, options = {}) {
    const el = typeof target === 'string' ? document.querySelector(target) : target;
    if (!el) throw new Error(`không tìm thấy nơi gắn: ${target}`);

    const base = new URL(options.base ?? '../', HERE);
    const opts = {
        background: options.background ?? 0x160d24,
        controls: options.controls ?? true,
        autoRotate: options.autoRotate ?? false,
        margin: options.margin ?? 1.14,   // chừa quanh nhân vật bao nhiêu
        distance: options.distance ?? null,  // null = tự tính từ hộp bao
        exposure: options.exposure ?? 1.35,
        ...options,
    };

    const scene = new THREE.Scene();
    if (opts.background !== null) scene.background = new THREE.Color(opts.background);

    const camera = new THREE.PerspectiveCamera(45, 1, 0.1, 100);
    const renderer = new THREE.WebGLRenderer({
        antialias: true, alpha: opts.background === null,
    });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = opts.exposure;
    renderer.domElement.style.display = 'block';
    el.appendChild(renderer.domElement);

    // Ô hiển thị toạ độ. Mặc định tắt: bản nhúng trên trang thật không nên
    // hiện thông tin gỡ lỗi trừ khi chủ trang chủ động bật.
    let hud = null;
    if (options.showCoords) {
        if (getComputedStyle(el).position === 'static') el.style.position = 'relative';
        hud = document.createElement('div');
        hud.style.cssText = 'position:absolute;left:8px;bottom:8px;z-index:2;'
            + 'padding:6px 9px;border-radius:6px;pointer-events:none;'
            + 'background:rgba(10,12,18,.72);color:#cfd6e4;'
            + 'font:11px/1.5 ui-monospace,Menlo,monospace;white-space:pre;'
            + 'font-variant-numeric:tabular-nums;';
        el.appendChild(hud);
    }

    // Từ r155 three.js bỏ hệ số PI nhân ngầm vào cường độ đèn, nên giữ nguyên
    // con số cũ sẽ cho ra cảnh tối đi khoảng 3,14 lần.
    const L = Math.PI;
    scene.add(new THREE.AmbientLight(0xffffff, 1.6 * L));
    const key = new THREE.DirectionalLight(0xfff8f0, 2.0 * L);
    key.position.set(0, 3.0, 3.0);
    scene.add(key);
    const rim = new THREE.DirectionalLight(0xbfd4ff, 0.9 * L);
    rim.position.set(-2, 2.4, -2.5);
    scene.add(rim);

    const character = await Character.load({
        manifestUrl: new URL('build/manifest.json', base).href,
        buildDir: new URL('build/', base).href,
        dracoPath: new URL('vendor/draco/', HERE).href,
    });
    scene.add(character.root);
    character.setState(options.state ?? character.manifest.defaultState, 0);
    if (options.hairstyle) character.setHairstyle(options.hairstyle);

    let controls = null;
    if (opts.controls) {
        controls = new OrbitControls(camera, renderer.domElement);
        controls.enableDamping = true;
        controls.dampingFactor = 0.05;
        controls.maxPolarAngle = Math.PI / 2 + 0.02;
        controls.autoRotate = opts.autoRotate;
        controls.autoRotateSpeed = 1.2;
        controls.enableZoom = options.zoom ?? true;
        // Pan của OrbitControls tắt hẳn: nó dời tâm xoay, mà tâm xoay phải luôn
        // nằm ở nhân vật. Việc dời nhân vật do camera.setViewOffset đảm nhiệm.
        controls.enablePan = false;
        controls.minDistance = 0.4;
        controls.maxDistance = 12;
    }
    // Khung hình tính từ hộp bao thật thay vì đặt cứng khoảng cách: khung chủ
    // nhà cao thấp rộng hẹp thế nào cũng phải thấy trọn nhân vật.
    const box = new THREE.Box3().setFromObject(character.root);
    const size = box.getSize(new THREE.Vector3());
    const lookAt = options.lookAt
        ? new THREE.Vector3(...options.lookAt)
        : box.getCenter(new THREE.Vector3());
    // Hộp bao của lưới có xương lấy theo tư thế bind, tức là hai tay dang ngang
    // nên rộng hơn nhân vật đang đứng nhiều. Dùng chiều cao làm chuẩn, chiều
    // ngang chỉ lấy một phần để không bị lùi ra quá xa.
    const shownWidth = Math.min(size.x, size.y * 0.55);

    // Toàn bộ phần xoay / dời khung / chốt giữ nhân vật nằm ở core/framing.js —
    // trang studio dùng chung đúng module đó, nên không có hai bản cài đặt để
    // lệch nhau.
    const frame_ = new FrameController({
        camera, controls, element: el, canvas: renderer.domElement,
        pivot: lookAt,
        keepInside: options.keepInside ?? 0.18,
        azimuth: options.azimuth ?? -0.079,
        polar: options.polar ?? 1.486,
    });

    function fitCamera() {
        if (opts.distance !== null) { placeCamera(opts.distance); return; }
        const vFov = THREE.MathUtils.degToRad(camera.fov);
        const forHeight = (size.y / 2) / Math.tan(vFov / 2);
        const hFov = 2 * Math.atan(Math.tan(vFov / 2) * camera.aspect);
        const forWidth = (shownWidth / 2) / Math.tan(hFov / 2);
        const d = Math.max(forHeight, forWidth) * opts.margin;
        if (controls) controls.target.copy(lookAt);
        frame_.place(d);
    }

    // --- âm thanh, chỉ dựng khi được yêu cầu ---
    let audioCtx = null, analyser = null, spectrum = null, audioEl = null, track = null;
    let uploadedUrl = null;
    function ensureGraph() {
        if (!audioEl) {
            audioEl = new Audio();
            audioEl.crossOrigin = 'anonymous';
            audioEl.loop = true;
        }
        if (!audioCtx) {
            audioCtx = new (window.AudioContext || window.webkitAudioContext)();
            analyser = audioCtx.createAnalyser();
            analyser.fftSize = 2048;          // ~23 Hz mỗi bin, đủ mịn để tách formant
            analyser.smoothingTimeConstant = 0.55;
            spectrum = new Float32Array(analyser.frequencyBinCount);
            audioCtx.createMediaElementSource(audioEl).connect(analyser);
            analyser.connect(audioCtx.destination);
        }
    }

    function ensureAudio(file) {
        const tracks = character.manifest.audioTracks || [];
        track = tracks.find(t => t.file === file) || tracks.find(t => t.default) || tracks[0];
        if (!track) return false;
        ensureGraph();
        const url = new URL('audio/' + track.file, base).href;
        if (audioEl.src !== url) { audioEl.src = url; character.beat.reset(); }
        return true;
    }

    let playing = false;
    const clock = new THREE.Clock();
    let alive = true;

    function resize() {
        const w = el.clientWidth || 1, h = el.clientHeight || 1;
        renderer.setSize(w, h, false);
        camera.aspect = w / h;
        camera.updateProjectionMatrix();
        frame_.apply();
        // Chỉ canh lại khung khi người dùng chưa đụng vào. Canh lại sau đó là
        // giật view về chỗ cũ ngay giữa lúc họ đang xoay.
        if (!frame_.userMoved) {
            fitCamera();
            if (controls) controls.update();
        }
    }
    const ro = new ResizeObserver(resize);
    ro.observe(el);
    resize();
    if (options.framing) frame_.setFraming(options.framing);

    const fmt = v => (v >= 0 ? ' ' : '') + v.toFixed(2);

    function view() {
        const t = controls ? controls.target : lookAt;
        return {
            target: t.clone(),
            camera: camera.position.clone(),
            distance: camera.position.distanceTo(t),
        };
    }

    function updateHud() {
        if (!hud) return;
        const v = view();
        const sp = frame_.screenPos();
        hud.textContent =
            `nhân vật trên khung   ${sp.x.toFixed(0)}% ngang   ${sp.y.toFixed(0)}% dọc\n`
            + `tâm nhìn   x ${fmt(v.target.x)}  y ${fmt(v.target.y)}  z ${fmt(v.target.z)}\n`
            + `máy quay   x ${fmt(v.camera.x)}  y ${fmt(v.camera.y)}  z ${fmt(v.camera.z)}\n`
            + `khoảng cách ${v.distance.toFixed(2)} m   ·   ${frame_.dragMode === 'dichuyen' ? 'kéo = dời' : 'kéo = xoay'}`
            + (playing && character.beat.bpm
                ? `\nnhịp ${character.beat.bpm.toFixed(0)} phách/phút`
                  + `  ·  độ tin ${character.beat.confidence.toFixed(0)}`
                  + `  ·  tốc độ nhảy ×${(character.current ? character.current.timeScale : 1).toFixed(2)}`
                : '');
    }

    function frame() {
        if (!alive) return;
        requestAnimationFrame(frame);
        const delta = clock.getDelta();
        updateHud();
        let audio = null;
        if (playing && analyser) {
            analyser.getFloatFrequencyData(spectrum);
            audio = { spectrumDb: spectrum, sampleRate: audioCtx.sampleRate, vocals: track.vocals };
        }
        character.update(delta, audio);
        if (controls) controls.update();
        renderer.render(scene, camera);
    }
    frame();

    return {
        character, scene, camera, renderer, controls,
        /** Phát một file nhạc người dùng tự chọn. Nhận File hoặc Blob.
         *  Bài tự tải lên mặc định coi là CÓ lời — người tải biết rõ hơn mọi
         *  phép đoán từ tín hiệu. Đặt vocals:false nếu là nhạc không lời. */
        async playFile(file, { vocals = true, dance = true } = {}) {
            ensureGraph();
            if (uploadedUrl) URL.revokeObjectURL(uploadedUrl);
            uploadedUrl = URL.createObjectURL(file);
            audioEl.src = uploadedUrl;
            track = { file: file.name || 'tải lên', label: file.name || 'tải lên', vocals };
            character.beat.reset();
            if (audioCtx.state === 'suspended') await audioCtx.resume();
            await audioEl.play();
            playing = true;
            if (dance) {
                const d = character.danceStates;
                if (d.length) character.setState(d[0]);
            }
            return { name: track.file, vocals };
        },
        /** Nhịp đang dò được: { bpm, confidence, beatPhase }. */
        getBeat() {
            const b = character.beat;
            return { bpm: b.bpm, confidence: b.confidence, beatPhase: b.beatPhase,
                     timeScale: character.current ? character.current.timeScale : 1 };
        },
        set beatSync(on) { character.beatSync = !!on; },
        get beatSync() { return character.beatSync; },
        states: character.manifest.states,
        hairstyles: character.manifest.hairstyles,
        audioTracks: character.manifest.audioTracks || [],
        setState: (clip, fade) => character.setState(clip, fade),
        setHairstyle: key => character.setHairstyle(key),
        setColor: (part, hex) => character.setColor(part, hex),
        async playAudio(file) {
            if (!ensureAudio(file)) return false;
            if (audioCtx.state === 'suspended') await audioCtx.resume();
            await audioEl.play();
            playing = true;
            return true;
        },
        pauseAudio() { if (audioEl) audioEl.pause(); playing = false; },
        /** Đưa góc nhìn về khung mặc định. */
        resetView() {
            frame_.reset();
            fitCamera();
            if (controls) controls.update();
        },
        /** 'xoay' hoặc 'dichuyen' — quyết định kéo chuột trái làm gì. */
        setDragMode: m => frame_.setDragMode(m),
        get dragMode() { return frame_.dragMode; },
        /** Toạ độ hiện tại: tâm nhìn, vị trí máy quay, khoảng cách. */
        getView: view,
        /** Khung hình hiện tại, dán thẳng vào createSinger({ framing: ... }) được. */
        getFraming: () => frame_.getFraming(),
        setFraming: fr => frame_.setFraming(fr),
        /** Vị trí nhân vật trên khung, phần trăm. */
        getScreenPos: () => frame_.screenPos(),
        /** Bật tắt ô hiển thị toạ độ trong khung. */
        showCoords(on) {
            if (on && !hud) {
                if (getComputedStyle(el).position === 'static') el.style.position = 'relative';
                hud = document.createElement('div');
                hud.style.cssText = 'position:absolute;left:8px;bottom:8px;z-index:2;'
                    + 'padding:6px 9px;border-radius:6px;pointer-events:none;'
                    + 'background:rgba(10,12,18,.72);color:#cfd6e4;'
                    + 'font:11px/1.5 ui-monospace,Menlo,monospace;white-space:pre;'
                    + 'font-variant-numeric:tabular-nums;';
                el.appendChild(hud);
            } else if (!on && hud) {
                hud.remove();
                hud = null;
            }
            return !!hud;
        },
        destroy() {
            alive = false;
            ro.disconnect();
            if (audioEl) audioEl.pause();
            renderer.dispose();
            renderer.domElement.remove();
        },
    };
}
