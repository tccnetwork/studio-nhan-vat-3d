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

    let userMoved = false;
    let controls = null;
    if (opts.controls) {
        controls = new OrbitControls(camera, renderer.domElement);
        controls.enableDamping = true;
        controls.dampingFactor = 0.05;
        controls.maxPolarAngle = Math.PI / 2 + 0.02;
        controls.autoRotate = opts.autoRotate;
        controls.autoRotateSpeed = 1.2;
        controls.enableZoom = options.zoom ?? true;
        controls.enablePan = options.pan ?? true;
        controls.minDistance = 0.4;
        controls.maxDistance = 12;
        // Người dùng đã tự đặt góc nhìn thì đừng kéo họ về chỗ cũ nữa.
        controls.addEventListener('start', () => { userMoved = true; });
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

    function fitCamera() {
        if (opts.distance !== null) { camera.position.set(0, lookAt.y, opts.distance); return; }
        const vFov = THREE.MathUtils.degToRad(camera.fov);
        const forHeight = (size.y / 2) / Math.tan(vFov / 2);
        const hFov = 2 * Math.atan(Math.tan(vFov / 2) * camera.aspect);
        const forWidth = (shownWidth / 2) / Math.tan(hFov / 2);
        const d = Math.max(forHeight, forWidth) * opts.margin;
        camera.position.set(0, lookAt.y, d);
        if (controls) controls.target.copy(lookAt);
        camera.lookAt(lookAt);
    }

    // --- âm thanh, chỉ dựng khi được yêu cầu ---
    let audioCtx = null, analyser = null, spectrum = null, audioEl = null, track = null;
    function ensureAudio(file) {
        const tracks = character.manifest.audioTracks || [];
        track = tracks.find(t => t.file === file) || tracks.find(t => t.default) || tracks[0];
        if (!track) return false;
        if (!audioEl) {
            audioEl = new Audio(new URL('audio/' + track.file, base).href);
            audioEl.crossOrigin = 'anonymous';
            audioEl.loop = true;
        } else if (!audioEl.src.endsWith(track.file)) {
            audioEl.src = new URL('audio/' + track.file, base).href;
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
        // Chỉ canh lại khung khi người dùng chưa đụng vào. Canh lại sau đó là
        // giật view về chỗ cũ ngay giữa lúc họ đang xoay.
        if (!userMoved) {
            fitCamera();
            if (controls) controls.update();
        }
    }
    const ro = new ResizeObserver(resize);
    ro.observe(el);
    resize();

    function frame() {
        if (!alive) return;
        requestAnimationFrame(frame);
        const delta = clock.getDelta();
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
        resetView() { userMoved = false; fitCamera(); if (controls) controls.update(); },
        destroy() {
            alive = false;
            ro.disconnect();
            if (audioEl) audioEl.pause();
            renderer.dispose();
            renderer.domElement.remove();
        },
    };
}
