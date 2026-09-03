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

    let userMoved = false;
    let dragMode = options.dragMode ?? 'xoay';
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
    setDragMode(dragMode);
    // Hộp bao của lưới có xương lấy theo tư thế bind, tức là hai tay dang ngang
    // nên rộng hơn nhân vật đang đứng nhiều. Dùng chiều cao làm chuẩn, chiều
    // ngang chỉ lấy một phần để không bị lùi ra quá xa.
    const shownWidth = Math.min(size.x, size.y * 0.55);

    // Dời nhân vật trong khung KHÔNG được đụng tới tâm xoay.
    //
    // Thao tác pan của OrbitControls dịch cả tâm xoay lẫn máy quay. Dời nhân
    // vật một chút là tâm xoay rời khỏi nhân vật, rồi xoay thì nhân vật văng
    // vòng quanh một điểm ở xa — đúng hiện tượng chủ dự án gặp. Hai bản chốt
    // trước của tôi chỉ giới hạn tâm xoay đi bao xa, tức là chữa triệu chứng.
    //
    // Ở đây tâm xoay bị khoá cứng vào nhân vật (pan của OrbitControls tắt hẳn),
    // còn việc dời nhân vật làm bằng camera.setViewOffset — dịch khung ảnh chứ
    // không dịch máy quay. Xoay vì thế luôn quay quanh nhân vật, ở mọi lúc.
    const KEEP = options.keepInside ?? 0.18;   // lề tối thiểu quanh khung, 0..0.5
    const frameOffset = { x: 0, y: 0 };        // pixel
    const _probe = new THREE.Vector3();

    function applyFrameOffset() {
        const w = el.clientWidth || 1, h = el.clientHeight || 1;
        const maxX = (0.5 - KEEP) * w, maxY = (0.5 - KEEP) * h;
        frameOffset.x = THREE.MathUtils.clamp(frameOffset.x, -maxX, maxX);
        frameOffset.y = THREE.MathUtils.clamp(frameOffset.y, -maxY, maxY);
        if (frameOffset.x === 0 && frameOffset.y === 0) camera.clearViewOffset();
        else camera.setViewOffset(w, h, -frameOffset.x, -frameOffset.y, w, h);
    }

    /** Nhân vật đang nằm đâu trên khung, tính bằng phần trăm. 50/50 là giữa.
     *
     *  Đo bằng phép chiếu thật qua ma trận của máy quay, KHÔNG suy ra từ biến
     *  frameOffset. Suy ra từ biến nội bộ là tự soi lại chính mình: nếu biến đó
     *  lệch với thứ đang hiển thị thì con số vẫn đẹp mà vẫn sai. */
    function screenPos() {
        camera.updateMatrixWorld();
        _probe.copy(lookAt).project(camera);
        return { x: _probe.x * 50 + 50, y: 50 - _probe.y * 50 };
    }

    // --- kéo để dời: tự xử lý, không mượn pan của OrbitControls ---
    let dragging = false, lastX = 0, lastY = 0;
    renderer.domElement.addEventListener('pointerdown', e => {
        if (dragMode !== 'dichuyen' || e.button !== 0) return;
        dragging = true; userMoved = true;
        lastX = e.clientX; lastY = e.clientY;
        renderer.domElement.setPointerCapture(e.pointerId);
        e.preventDefault();
    });
    renderer.domElement.addEventListener('pointermove', e => {
        if (!dragging) return;
        frameOffset.x += e.clientX - lastX;
        frameOffset.y += e.clientY - lastY;
        lastX = e.clientX; lastY = e.clientY;
        applyFrameOffset();
    });
    const endDrag = e => {
        if (!dragging) return;
        dragging = false;
        try { renderer.domElement.releasePointerCapture(e.pointerId); } catch (_) {}
    };
    renderer.domElement.addEventListener('pointerup', endDrag);
    renderer.domElement.addEventListener('pointercancel', endDrag);

    /** 'xoay' — kéo trái để xoay quanh nhân vật (mặc định).
     *  'dichuyen' — kéo trái để dời nhân vật trong khung, xoay chuyển sang chuột phải. */
    function setDragMode(mode) {
        dragMode = mode;
        if (!controls) return;
        const move = mode === 'dichuyen';
        controls.mouseButtons = {
            LEFT: move ? null : THREE.MOUSE.ROTATE,
            MIDDLE: THREE.MOUSE.DOLLY,
            RIGHT: THREE.MOUSE.ROTATE,
        };
        controls.touches = {
            ONE: move ? null : THREE.TOUCH.ROTATE,
            TWO: THREE.TOUCH.DOLLY_ROTATE,
        };
    }

    /** Khung hình hiện tại, ở dạng dán thẳng vào createSinger được. */
    function getFraming() {
        const w = el.clientWidth || 1, h = el.clientHeight || 1;
        const off = camera.position.clone().sub(controls ? controls.target : lookAt);
        const dist = off.length();
        return {
            distance: +dist.toFixed(3),
            azimuth: +Math.atan2(off.x, off.z).toFixed(4),      // radian, 0 = nhìn từ trước
            polar: +Math.acos(THREE.MathUtils.clamp(off.y / dist, -1, 1)).toFixed(4),
            frameOffset: {
                x: +(frameOffset.x / w).toFixed(4),             // tỉ lệ bề rộng khung
                y: +(frameOffset.y / h).toFixed(4),
            },
        };
    }

    function applyFraming(fr) {
        if (!fr) return;
        const w = el.clientWidth || 1, h = el.clientHeight || 1;
        if (fr.frameOffset) {
            frameOffset.x = (fr.frameOffset.x ?? 0) * w;
            frameOffset.y = (fr.frameOffset.y ?? 0) * h;
            applyFrameOffset();
        }
        const dist = fr.distance ?? camera.position.distanceTo(lookAt);
        const az = fr.azimuth ?? 0, po = fr.polar ?? Math.PI / 2;
        const t = controls ? controls.target : lookAt;
        camera.position.set(
            t.x + dist * Math.sin(po) * Math.sin(az),
            t.y + dist * Math.cos(po),
            t.z + dist * Math.sin(po) * Math.cos(az));
        camera.lookAt(t);
        if (controls) controls.update();
        userMoved = true;      // đã có khung hình chỉ định thì đừng tự canh lại
    }

    // Góc nhìn mặc định hơi chếch sang bên và hơi cao, theo đúng khung mà chủ
    // dự án tự căn tay — nhìn thẳng trực diện trông phẳng và cứng hơn.
    const DEF_AZIMUTH = options.azimuth ?? -0.079;   // radian
    const DEF_POLAR = options.polar ?? 1.486;

    function placeCamera(dist) {
        const t = controls ? controls.target : lookAt;
        camera.position.set(
            t.x + dist * Math.sin(DEF_POLAR) * Math.sin(DEF_AZIMUTH),
            t.y + dist * Math.cos(DEF_POLAR),
            t.z + dist * Math.sin(DEF_POLAR) * Math.cos(DEF_AZIMUTH));
        camera.lookAt(t);
    }

    function fitCamera() {
        if (opts.distance !== null) { placeCamera(opts.distance); return; }
        const vFov = THREE.MathUtils.degToRad(camera.fov);
        const forHeight = (size.y / 2) / Math.tan(vFov / 2);
        const hFov = 2 * Math.atan(Math.tan(vFov / 2) * camera.aspect);
        const forWidth = (shownWidth / 2) / Math.tan(hFov / 2);
        const d = Math.max(forHeight, forWidth) * opts.margin;
        if (controls) controls.target.copy(lookAt);
        placeCamera(d);
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
        applyFrameOffset();
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
    if (options.framing) applyFraming(options.framing);

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
        const sp = screenPos();
        hud.textContent =
            `nhân vật trên khung   ${sp.x.toFixed(0)}% ngang   ${sp.y.toFixed(0)}% dọc\n`
            + `tâm nhìn   x ${fmt(v.target.x)}  y ${fmt(v.target.y)}  z ${fmt(v.target.z)}\n`
            + `máy quay   x ${fmt(v.camera.x)}  y ${fmt(v.camera.y)}  z ${fmt(v.camera.z)}\n`
            + `khoảng cách ${v.distance.toFixed(2)} m   ·   ${dragMode === 'dichuyen' ? 'kéo = dời' : 'kéo = xoay'}`;
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
            userMoved = false;
            frameOffset.x = 0; frameOffset.y = 0;
            applyFrameOffset();
            if (controls) controls.target.copy(lookAt);
            fitCamera();
            if (controls) controls.update();
        },
        /** 'xoay' hoặc 'dichuyen' — quyết định kéo chuột trái làm gì. */
        setDragMode,
        get dragMode() { return dragMode; },
        /** Toạ độ hiện tại: tâm nhìn, vị trí máy quay, khoảng cách. */
        getView: view,
        /** Khung hình hiện tại, dán thẳng vào createSinger({ framing: ... }) được. */
        getFraming,
        setFraming: applyFraming,
        /** Vị trí nhân vật trên khung, phần trăm. */
        getScreenPos: screenPos,
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
