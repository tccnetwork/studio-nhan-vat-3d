// Studio 3D cho nhân vật nữ ca sĩ anime idol.
//
// File này là ES module: index.html khai importmap trỏ "three" sang CDN.
// Hàm nào được gọi từ thuộc tính onclick/oninput trong HTML đều phải gán vào
// window ở cuối file, vì module có phạm vi riêng chứ không đổ ra toàn cục.
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { Character } from './core/character.js';
import { selfTest as vowelSelfTest } from './core/lipsync.js';
import { FrameController } from './core/framing.js';

// Bộ giải nén Draco để ngay trong dự án thay vì lấy từ CDN: trang tải được
// khi không có mạng, và thời gian tải không còn phụ thuộc độ trễ của CDN.
const DRACO_DECODER_PATH = 'vendor/draco/';

//
// Danh sách trạng thái, kiểu tóc và nhóm vật liệu không nằm trong file này.
// Chúng đến từ build/manifest.json do quy trình dựng sinh ra từ
// scripts/catalog.py, nên thêm một trạng thái chỉ cần sửa một chỗ duy nhất.
const MANIFEST_URL = '../build/manifest.json';
const BUILD_DIR = '../build/';
const AUDIO_DIR = '../audio/';

/** Đường dẫn tới một bản nhạc. Mỗi bài khai báo thư mục riêng trong
 *  scripts/catalog.py, thiếu thì hiểu là audio/. */
function trackUrl(track) {
    return '../' + (track.dir || 'audio/') + track.file;
}

let manifest = null;
let stateByClip = {};      // ten clip -> muc trong manifest

let scene, camera, renderer, controls, clock;
let character = null;
let framing = null;
let characterModel = null, morphMeshes = [], mixer = null;
let skeletonHelper = null;
let particlesSystem;
let isWireframe = false;

let animationsMap = {};
let currentAction = null;
let currentActionName = '01_DungNghiem';

let audioContext = null, analyser = null, audioSource = null;
let audioDataArray = null, audioSpectrumDb = null, audioElement = null;
let currentTrack = { file: 'vocal_song_pop.mp3', vocals: true };
let isAudioPlaying = false;
let shownState = null;
let currentVocalEnergy = 0;

const container = document.getElementById('canvas-container');

function createSafeWebGLRenderer(containerEl) {
    if (renderer) {
        try {
            renderer.dispose();
            if (renderer.forceContextLoss) renderer.forceContextLoss();
        } catch(e) {}
    }
    if (containerEl) {
        while (containerEl.firstChild) {
            containerEl.removeChild(containerEl.firstChild);
        }
    }

    const canvas = document.createElement('canvas');
    containerEl.appendChild(canvas);

    let gl = null;
    const contextsToTry = ['webgl2', 'webgl', 'experimental-webgl'];
    const optList = [
        { antialias: true, alpha: false, powerPreference: 'default', failIfMajorPerformanceCaveat: false },
        { antialias: false, alpha: false, powerPreference: 'default', failIfMajorPerformanceCaveat: false },
        { antialias: false, alpha: false }
    ];

    for (let opt of optList) {
        for (let ctxName of contextsToTry) {
            try {
                gl = canvas.getContext(ctxName, opt);
                if (gl) break;
            } catch(e) {}
        }
        if (gl) break;
    }

    let r;
    try {
        if (gl) {
            r = new THREE.WebGLRenderer({ canvas: canvas, context: gl, antialias: true, alpha: false });
        } else {
            r = new THREE.WebGLRenderer({ antialias: false, powerPreference: 'default', failIfMajorPerformanceCaveat: false });
            containerEl.appendChild(r.domElement);
        }
    } catch(e) {
        console.warn("Retrying basic WebGLRenderer without antialias...", e);
        r = new THREE.WebGLRenderer({ antialias: false });
        containerEl.appendChild(r.domElement);
    }

    r.domElement.addEventListener('webglcontextlost', function(event) {
        event.preventDefault();
        console.warn('WebGL Context Lost. Auto recovering in 1.5s...');
        setTimeout(() => location.reload(), 1500);
    }, false);

    return r;
}

function init() {
    scene = new THREE.Scene();
    scene.background = new THREE.Color(0x160d24);
    scene.fog = new THREE.FogExp2(0x160d24, 0.035);
    clock = new THREE.Clock();

    camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 0.1, 100);
    camera.position.set(0, 1.45, 3.0);

    try {
        renderer = createSafeWebGLRenderer(container);
        renderer.setSize(window.innerWidth, window.innerHeight);
        renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        renderer.shadowMap.enabled = true;
        renderer.shadowMap.type = THREE.PCFSoftShadowMap;
        renderer.outputColorSpace = THREE.SRGBColorSpace;
        renderer.toneMapping = THREE.ACESFilmicToneMapping;
        renderer.toneMappingExposure = 1.35;
    } catch(err) {
        console.error("Critical WebGL Init Error:", err);
        container.innerHTML = '<div style="position:absolute;top:40%;left:50%;transform:translate(-50%,-50%);color:#f87171;text-align:center;font-family:sans-serif;background:rgba(15,23,42,0.95);padding:24px;border-radius:12px;border:2px solid #ef4444;box-shadow:0 0 20px rgba(239,68,68,0.3);"><h2>⚠️ Đang Khởi Động Lại Trình Vẽ 3D WebGL...</h2><p style="color:#cbd5e1;margin-top:8px;">Trình duyệt đang giải phóng bộ nhớ GPU. Vui lòng đóng bớt các tab 3D khác nếu đang mở nhiều tab.</p><button onclick="location.reload()" style="margin-top:16px;padding:10px 20px;background:#38bdf8;color:#0f172a;border:none;border-radius:8px;font-weight:bold;cursor:pointer;">🔄 Tải Lại Ngay (Reload)</button></div>';
        return;
    }

    controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    controls.maxPolarAngle = Math.PI / 2 + 0.02;
    controls.minDistance = 0.4;
    controls.maxDistance = 12;
    controls.target.set(0, 1.1, 0);
    controls.update();

    // Cùng module với bản nhúng: tâm xoay luôn ở nhân vật, dời nhân vật bằng
    // dịch khung ảnh. Trước đây trang này để pan mặc định của OrbitControls,
    // nên dời nhân vật là tâm xoay rời khỏi nó và xoay thì nhân vật văng vòng
    // quanh một điểm ở xa.
    framing = new FrameController({
        camera, controls, element: container, canvas: renderer.domElement,
        pivot: new THREE.Vector3(0, 1.1, 0),
    });

    setupLighting();
    setupStage();
    setupAudioElement();
    setupUIEventListeners();

    window.addEventListener('resize', onWindowResize);
    animate();

    loadManifest().then(() => {
        buildStateButtons();
        buildHairstyleButtons();
        buildAudioButtons();
        loadModel();
    });
}

// ==========================================
// MANIFEST — danh mục do quy trình dựng sinh ra
// ==========================================
function loadManifest() {
    return fetch(MANIFEST_URL + '?v=' + Date.now())
        .then(r => {
            if (!r.ok) throw new Error(`HTTP ${r.status}`);
            return r.json();
        })
        .then(m => {
            manifest = m;
            stateByClip = {};
            m.states.forEach(st => { stateByClip[st.clip] = st; });
            currentActionName = m.defaultState;
            return m;
        })
        .catch(err => {
            showFatal('Không đọc được build/manifest.json',
                      `${err.message}. Hãy dựng lại model bằng scripts/build_character.py, ` +
                      `hoặc mở trang qua một máy chủ web thay vì mở thẳng file.`);
            throw err;
        });
}

function showFatal(title, detail) {
    container.innerHTML = `<div style="position:absolute;top:40%;left:50%;transform:translate(-50%,-50%);` +
        `color:#fca5a5;text-align:center;font-family:sans-serif;background:rgba(15,23,42,0.96);` +
        `padding:24px 28px;border-radius:12px;border:2px solid #ef4444;max-width:520px;">` +
        `<h2 style="margin:0 0 8px;">${title}</h2>` +
        `<p style="color:#cbd5e1;font-size:14px;line-height:1.55;margin:0;">${detail}</p></div>`;
}

function hexToRgba(hex, alpha) {
    const n = parseInt(hex.slice(1), 16);
    return `rgba(${(n >> 16) & 255}, ${(n >> 8) & 255}, ${n & 255}, ${alpha})`;
}

function buildStateButtons() {
    const grid = document.getElementById('state-btn-grid');
    const pageTitle = document.getElementById('page-title');
    if (pageTitle) {
        pageTitle.textContent =
            `Nữ Ca Sĩ Anime Idol — ${manifest.states.length} Trạng Thái Hoạt Ảnh`;
    }
    const title = document.getElementById('state-card-title');
    if (title) title.textContent = `🎬 ${manifest.states.length} Trạng Thái Hoạt Ảnh Ca Sĩ Idol`;
    if (!grid) return;
    grid.innerHTML = '';
    manifest.states.forEach(st => {
        const b = document.createElement('button');
        b.id = stateButtonId(st.clip);
        b.className = 'btn state-btn' + (st.clip === manifest.defaultState ? ' active' : '');
        b.textContent = `${st.order}. ${st.icon} ${st.label}`;
        b.title = `${st.desc} — ${st.frames} frame @ ${st.fps} fps`;
        b.style.borderColor = st.accent;
        b.style.color = st.accent;
        if (st.clip === manifest.defaultState) b.style.background = hexToRgba(st.accent, 0.18);
        b.addEventListener('click', () => switchAnimationState(st.clip));
        grid.appendChild(b);
    });
}

function buildHairstyleButtons() {
    const box = document.getElementById('hair-btn-grid');
    const badge = document.getElementById('hair-count-badge');
    if (badge) badge.textContent = `${manifest.hairstyles.length} KIỂU TÓC`;
    if (!box) return;
    box.innerHTML = '';
    manifest.hairstyles.forEach((h, i) => {
        const b = document.createElement('button');
        b.id = `btn-hair-${h.key}`;
        b.className = 'btn hair-btn' + (h.default ? ' active' : '');
        b.style.cssText = 'justify-content:flex-start;padding:10px 12px;font-weight:700;font-size:13px;';
        b.style.border = `1.5px solid ${h.accent}`;
        b.style.color = h.accent;
        if (h.default) b.style.background = hexToRgba(h.accent, 0.2);
        b.textContent = `${h.icon} ${i + 1}. ${h.label} (${h.desc})`;
        b.addEventListener('click', () => switchHairstyle(h.key));
        box.appendChild(b);
    });
}

function buildAudioButtons() {
    const box = document.getElementById('audio-track-grid');
    const tracks = manifest.audioTracks || [];
    if (!box || tracks.length === 0) return;
    currentTrack = tracks.find(t => t.default) || tracks[0];
    box.innerHTML = '';
    tracks.forEach(t => {
        const b = document.createElement('button');
        b.id = 'btn-track-' + t.file.replace(/[^a-z0-9]/gi, '_');
        b.className = 'btn audio-btn' + (t === currentTrack ? ' active' : '');
        b.style.cssText = 'justify-content:flex-start;padding:8px 10px;font-size:12px;';
        b.textContent = `${t.icon} ${t.label}` + (t.vocals ? '' : ' — không nhép miệng');
        b.addEventListener('click', () => selectAudioTrack(t));
        box.appendChild(b);
    });
    updateLipSyncNote();
}

function selectAudioTrack(track) {
    currentTrack = track;
    document.querySelectorAll('#audio-track-grid .btn').forEach(b => b.classList.remove('active'));
    const btn = document.getElementById('btn-track-' + track.file.replace(/[^a-z0-9]/gi, '_'));
    if (btn) btn.classList.add('active');
    const wasPlaying = isAudioPlaying;
    if (audioElement) {
        audioElement.pause();
        audioElement.src = trackUrl(track);
        if (wasPlaying) audioElement.play().catch(() => {});
    }
    // Bài mới có tempo khác: giữ lại lịch sử flux của bài cũ thì phải mất vài
    // giây bộ dò mới gột hết, trong lúc đó nhân vật nhảy sai nhịp.
    if (character) character.beat.reset();
    updateLipSyncNote();
    updateAudioButton();
}

function updateLipSyncNote() {
    const note = document.getElementById('lipsync-note');
    if (!note) return;
    note.textContent = currentTrack.vocals
        ? 'Bản này có giọng hát nên khẩu hình chạy theo nguyên âm nghe được.'
        : 'Bản này không có lời nên nhân vật ngậm miệng.';
}

function stateButtonId(clip) {
    return 'btn-state-' + clip.replace(/[^A-Za-z0-9]/g, '_');
}

function setupLighting() {
    // Từ r155 three.js tính ánh sáng theo đơn vị vật lý: hệ số PI trước đây
    // nhân ngầm vào cường độ đã bị bỏ, nên cùng một con số cho ra cảnh tối hơn
    // khoảng 3,14 lần. Hướng dẫn chuyển đổi chính thức là nhân cường độ với PI.
    const L = Math.PI;
    // Riêng đèn spot còn đổi cả cách suy giảm theo khoảng cách, nên chỉ nhân PI
    // là chưa đủ: sàn sân khấu cách đèn khoảng 4 m vẫn tối hơn hẳn bản cũ.
    // Hệ số này căn theo ảnh chụp đối chiếu chứ không suy ra từ công thức.
    const SPOT = L * 3.0;

    scene.add(new THREE.AmbientLight(0xffffff, 1.6 * L));

    const frontLight = new THREE.DirectionalLight(0xfff8f0, 2.0 * L);
    frontLight.position.set(0, 3.0, 3.0);
    frontLight.castShadow = true;
    scene.add(frontLight);

    // Từ r155 three.js đổi sang đèn theo đơn vị vật lý và decay mặc định là 2;
    // r128 dùng decay 1. Đặt lại 1 để ánh sáng sân khấu giữ nguyên như cũ.
    const spotPink = new THREE.SpotLight(0xec4899, 3.2 * SPOT, 14, Math.PI / 4, 0.3);
    spotPink.decay = 1;
    spotPink.position.set(-2, 4.0, 2.0);
    spotPink.target.position.set(0, 1.1, 0);
    scene.add(spotPink);
    scene.add(spotPink.target);

    const spotPurple = new THREE.SpotLight(0xa855f7, 3.2 * SPOT, 14, Math.PI / 4, 0.3);
    spotPurple.decay = 1;
    spotPurple.position.set(2, 4.0, 2.0);
    spotPurple.target.position.set(0, 1.1, 0);
    scene.add(spotPurple);
    scene.add(spotPurple.target);
}

function setupStage() {
    const stageGeo = new THREE.CylinderGeometry(2.0, 2.1, 0.1, 64);
    // metalness 0,8 mà không có environment map thì đúng ra phải ra gần như đen:
    // bề mặt kim loại chỉ phản chiếu môi trường chứ hầu như không có phản xạ
    // khuếch tán. r128 chưa tính đúng nên sàn vẫn sáng; r180 thì tối hẳn.
    // Hạ metalness để sàn bắt được ánh đèn spot đúng như thiết kế ban đầu.
    const stageMat = new THREE.MeshStandardMaterial({
        color: 0x2e1045,
        roughness: 0.35,
        metalness: 0.25
    });
    const stageMesh = new THREE.Mesh(stageGeo, stageMat);
    stageMesh.position.y = 0.05;
    stageMesh.receiveShadow = true;
    scene.add(stageMesh);

    const grid = new THREE.GridHelper(16, 32, 0xec4899, 0x581c87);
    grid.position.y = 0;
    scene.add(grid);

    const particleCount = 300;
    const geometry = new THREE.BufferGeometry();
    const positions = new Float32Array(particleCount * 3);
    const colors = new Float32Array(particleCount * 3);

    for (let i = 0; i < particleCount; i++) {
        positions[i * 3] = (Math.random() - 0.5) * 8;
        positions[i * 3 + 1] = Math.random() * 4.5;
        positions[i * 3 + 2] = (Math.random() - 0.5) * 8;

        if (Math.random() > 0.5) {
            colors[i * 3] = 1.0; colors[i * 3 + 1] = 0.4; colors[i * 3 + 2] = 0.8;
        } else {
            colors[i * 3] = 0.7; colors[i * 3 + 1] = 0.5; colors[i * 3 + 2] = 1.0;
        }
    }

    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));

    const material = new THREE.PointsMaterial({
        size: 0.035,
        vertexColors: true,
        transparent: true,
        opacity: 0.8,
        blending: THREE.AdditiveBlending
    });

    particlesSystem = new THREE.Points(geometry, material);
    scene.add(particlesSystem);
}

function setupAudioElement() {
    audioElement = new Audio(trackUrl(currentTrack));
    audioElement.crossOrigin = "anonymous";
    audioElement.loop = true;
}

function setupAudioContext() {
    if (!audioContext) {
        audioContext = new (window.AudioContext || window.webkitAudioContext)();
        analyser = audioContext.createAnalyser();
        // 256 bin cho ra độ phân giải ~187 Hz mỗi bin — quá thô để tách được
        // hai formant vốn cách nhau vài trăm Hz. 2048 cho ~23 Hz mỗi bin.
        analyser.fftSize = 2048;
        analyser.smoothingTimeConstant = 0.55;
        audioDataArray = new Uint8Array(analyser.frequencyBinCount);
        audioSpectrumDb = new Float32Array(analyser.frequencyBinCount);

        audioSource = audioContext.createMediaElementSource(audioElement);
        audioSource.connect(analyser);
        analyser.connect(audioContext.destination);
    }
    if (audioContext.state === 'suspended') {
        audioContext.resume();
    }
}

async function loadModel() {
    if (character) {
        scene.remove(character.root);
        if (skeletonHelper) { scene.remove(skeletonHelper); skeletonHelper = null; }
    }
    try {
        character = await Character.load({
            manifestUrl: MANIFEST_URL,
            buildDir: BUILD_DIR,
            dracoPath: DRACO_DECODER_PATH,
        });
    } catch (err) {
        showFatal('Không tải được model', String(err && err.message || err));
        throw err;
    }

    characterModel = character.root;
    characterModel.position.set(0, 0.15, 0);   // mặt sàn sân khấu ở y = 0,15 m
    morphMeshes = character.morphMeshes;
    hairMeshes = character.hairMeshes;
    mixer = character.mixer;
    animationsMap = character.actions;
    const dflt = character.manifest.hairstyles.find(h => h.default);
    if (dflt) currentHairstyle = dflt.key;

    scene.add(characterModel);

    skeletonHelper = new THREE.SkeletonHelper(characterModel);
    skeletonHelper.material.linewidth = 2;
    skeletonHelper.material.color.set(0x38bdf8);
    const skelToggle = document.getElementById('toggle-skeleton');
    skeletonHelper.visible = skelToggle ? skelToggle.checked : false;
    scene.add(skeletonHelper);

    cacheMorphIndices(characterModel);
    character.setState(manifest.defaultState, 0);
    currentAction = character.current;
    currentActionName = character.currentName;
    updateAnimationHUD(currentActionName);
    console.log(`Đã nạp: ${Object.keys(animationsMap).length} clip`);
}

// ==========================================
// MULTI-HAIRSTYLE SWITCHER ENGINE (4 STYLES)
// ==========================================
let hairMeshes = {};          // key trong manifest -> THREE.Mesh
let currentHairstyle = 'long';

window.switchHairstyle = function(styleName) {
    currentHairstyle = styleName;
    document.querySelectorAll('.hair-btn').forEach(b => {
        b.classList.remove('active');
        b.style.background = 'transparent';
    });
    const entry = manifest.hairstyles.find(h => h.key === styleName);
    const activeBtn = document.getElementById(`btn-hair-${styleName}`);
    if (activeBtn && entry) {
        activeBtn.classList.add('active');
        activeBtn.style.background = hexToRgba(entry.accent, 0.2);
    }

    character.setHairstyle(styleName);

    const picker = document.getElementById('picker-hair');
    changeCharacterColor('hair', picker ? picker.value : '#ffffff');
};

// ==========================================
// DYNAMIC SMILE & CHARISMATIC EXPRESSION ENGINE
// ==========================================
let smileState = {
    baseIntensity: 0.65, // 65% pleasant idol smile by default
    currentIntensity: 0.65,
    isAutoDynamic: true,
    timer: 0
};

window.onAutoSmileToggle = function(checked) {
    smileState.isAutoDynamic = checked;
};

window.onSmileSliderChange = function(val) {
    const num = parseFloat(val) / 100.0;
    smileState.baseIntensity = num;
    smileState.currentIntensity = num;
    const disp = document.getElementById('smile-val-display');
    if (disp) disp.innerText = Math.round(val) + '%';
};

window.setSmilePreset = function(val) {
    const slider = document.getElementById('slider-smile');
    if (slider) slider.value = val;
    window.onSmileSliderChange(val);
};

// ==========================================
// SNAPPY NATURAL BLINK & PLAYFUL WINK ENGINE
// ==========================================
let blinkState = {
    timer: 2.0,
    isBlinking: false,
    blinkProgress: 0,
    blinkDuration: 0.16, // 160ms snappy natural blink
    isWink: false,
    winkSide: 'L',
    doubleBlinkPending: false
};

let morphIndices = {
    eyeClose: -1,
    eyeCloseL: -1,
    eyeCloseR: -1,
    eyeJoy: -1,
    eyeJoyL: -1,
    eyeJoyR: -1,
    allJoy: -1,
    allFun: -1,
    brwJoy: -1,
    mouthJoy: -1,
    mouthUp: -1,
    mouthA: -1,
    mouthI: -1,
    mouthU: -1,
    mouthE: -1,
    mouthO: -1
};

function cacheMorphIndices(model) {
    model.traverse((child) => {
        if (child.isMesh && child.morphTargetDictionary) {
            const dict = child.morphTargetDictionary;
            for (const key in dict) {
                const idx = dict[key];
                if (key.includes('EYE_Close') && !key.includes('_L') && !key.includes('_R')) morphIndices.eyeClose = idx;
                else if (key.includes('EYE_Close_L')) morphIndices.eyeCloseL = idx;
                else if (key.includes('EYE_Close_R')) morphIndices.eyeCloseR = idx;
                else if (key.includes('EYE_Joy_L')) morphIndices.eyeJoyL = idx;
                else if (key.includes('EYE_Joy_R')) morphIndices.eyeJoyR = idx;
                else if (key.includes('EYE_Joy') && !key.includes('_L') && !key.includes('_R')) morphIndices.eyeJoy = idx;
                else if (key.includes('ALL_Joy')) morphIndices.allJoy = idx;
                else if (key.includes('ALL_Fun')) morphIndices.allFun = idx;
                else if (key.includes('BRW_Joy')) morphIndices.brwJoy = idx;
                else if (key.includes('MTH_Joy')) morphIndices.mouthJoy = idx;
                else if (key.includes('MTH_Up')) morphIndices.mouthUp = idx;
                else if (key.includes('MTH_A')) morphIndices.mouthA = idx;
                else if (key.includes('MTH_I')) morphIndices.mouthI = idx;
                else if (key.includes('MTH_U')) morphIndices.mouthU = idx;
                else if (key.includes('MTH_E')) morphIndices.mouthE = idx;
                else if (key.includes('MTH_O')) morphIndices.mouthO = idx;
            }
        }
    });
    console.log("Cached Morph Indices with Smile Engine:", morphIndices);
}

function triggerManualWink() {
    blinkState.isBlinking = true;
    blinkState.blinkProgress = 0;
    blinkState.blinkDuration = 0.32; // 320ms playful wink
    blinkState.isWink = true;
    blinkState.winkSide = Math.random() > 0.5 ? 'L' : 'R';
}

function updateFacialAnimation(delta) {
    if (!characterModel || morphMeshes.length === 0) return;

    // 1. Calculate Dynamic Smile Intensity
    if (smileState.isAutoDynamic) {
        smileState.timer += delta;
        const smileOsc = Math.sin(smileState.timer * 2.2) * 0.12; // breathing smile fluctuation
        smileState.currentIntensity = Math.max(0.0, Math.min(1.0, smileState.baseIntensity + smileOsc));
    } else {
        smileState.currentIntensity = smileState.baseIntensity;
    }

    const smileVal = smileState.currentIntensity;
    // Morph cười giữ miệng ở một hình cố định khá mạnh (đo được 0,55–0,65 suốt
    // bài) và nuốt mất các khẩu hình nguyên âm — nhìn vào chỉ thấy cười chứ
    // không thấy hát. Nhả bớt cười Ở MIỆNG theo đúng mức miệng đang mở, còn
    // mắt và mày vẫn cười nguyên để gương mặt không bị lạnh.
    let singing = 0;
    if (character && character.visemes) {
        for (const k in character.visemes) {
            if (character.visemes[k] > singing) singing = character.visemes[k];
        }
    }
    const mouthDamp = 1 - 0.8 * singing;
    const mouthJoyVal = smileVal * 0.85 * mouthDamp;
    const mouthUpVal = smileVal * 0.45 * mouthDamp;
    const eyeJoyVal = smileVal * 0.40;
    const brwJoyVal = smileVal * 0.30;
    const allJoyVal = smileVal * 0.35;

    // 2. Blink & Wink Calculation
    const autoBlinkEnabled = document.getElementById('toggle-auto-blink') ? document.getElementById('toggle-auto-blink').checked : true;
    const autoWinkEnabled = document.getElementById('toggle-auto-wink') ? document.getElementById('toggle-auto-wink').checked : false;

    let eyeCloseVal = 0;
    let eyeCloseLVal = 0;
    let eyeCloseRVal = 0;
    let eyeJoyLVal = 0;
    let eyeJoyRVal = 0;

    if (autoBlinkEnabled || blinkState.isBlinking) {
        if (!blinkState.isBlinking) {
            blinkState.timer -= delta;
            if (blinkState.timer <= 0) {
                blinkState.isBlinking = true;
                blinkState.blinkProgress = 0;

                if (autoWinkEnabled && Math.random() < 0.28) {
                    blinkState.isWink = true;
                    blinkState.blinkDuration = 0.32; // 320ms playful wink
                    blinkState.winkSide = Math.random() > 0.5 ? 'L' : 'R';
                    blinkState.timer = 4.0 + Math.random() * 4.5;
                } else {
                    blinkState.isWink = false;
                    blinkState.blinkDuration = 0.16; // 160ms SNAPPY NATURAL BLINK!
                    blinkState.timer = 2.4 + Math.random() * 2.8;

                    if (Math.random() < 0.20 && !blinkState.doubleBlinkPending) {
                        blinkState.doubleBlinkPending = true;
                    }
                }
            }
        }

        if (blinkState.isBlinking) {
            blinkState.blinkProgress += delta / blinkState.blinkDuration;
            let intensity = 0;

            if (blinkState.blinkProgress <= 1.0) {
                const p = blinkState.blinkProgress;
                // Snappy Asymmetric Velocity Curve
                if (p < 0.35) {
                    intensity = Math.sin((p / 0.35) * (Math.PI / 2)); // Snappy fast closing (56ms)
                } else if (p < 0.45) {
                    intensity = 1.0; // Momentary full close
                } else {
                    intensity = Math.cos(((p - 0.45) / 0.55) * (Math.PI / 2)); // Crisp open
                }

                if (blinkState.isWink) {
                    if (blinkState.winkSide === 'L') {
                        eyeCloseLVal = intensity;
                        eyeJoyLVal = intensity * 0.75;
                    } else {
                        eyeCloseRVal = intensity;
                        eyeJoyRVal = intensity * 0.75;
                    }
                } else {
                    eyeCloseVal = intensity;
                }
            } else {
                blinkState.isBlinking = false;
                blinkState.blinkProgress = 0;
                blinkState.isWink = false;

                if (blinkState.doubleBlinkPending) {
                    blinkState.doubleBlinkPending = false;
                    blinkState.timer = 0.10; // Immediate snappy 2nd blink!
                }
            }
        }
    }

    // 3. Apply to Morph Target Meshes
    morphMeshes.forEach(mesh => {
        if (mesh.morphTargetInfluences) {
            if (morphIndices.eyeClose >= 0) mesh.morphTargetInfluences[morphIndices.eyeClose] = eyeCloseVal;
            if (morphIndices.eyeCloseL >= 0) mesh.morphTargetInfluences[morphIndices.eyeCloseL] = eyeCloseLVal;
            if (morphIndices.eyeCloseR >= 0) mesh.morphTargetInfluences[morphIndices.eyeCloseR] = eyeCloseRVal;
            if (morphIndices.eyeJoyL >= 0) mesh.morphTargetInfluences[morphIndices.eyeJoyL] = eyeJoyLVal;
            if (morphIndices.eyeJoyR >= 0) mesh.morphTargetInfluences[morphIndices.eyeJoyR] = eyeJoyRVal;
            
            // Smile Blendshapes
            if (morphIndices.mouthJoy >= 0) mesh.morphTargetInfluences[morphIndices.mouthJoy] = mouthJoyVal;
            if (morphIndices.mouthUp >= 0) mesh.morphTargetInfluences[morphIndices.mouthUp] = mouthUpVal;
            if (morphIndices.eyeJoy >= 0) mesh.morphTargetInfluences[morphIndices.eyeJoy] = eyeJoyVal;
            if (morphIndices.brwJoy >= 0) mesh.morphTargetInfluences[morphIndices.brwJoy] = brwJoyVal;
            if (morphIndices.allJoy >= 0) mesh.morphTargetInfluences[morphIndices.allJoy] = allJoyVal;
        }
    });
}

// ==========================================
// REAL-TIME CHARACTER COLOR CUSTOMIZER
// ==========================================
function changeCharacterColor(part, hexColor) {
    if (character) character.setColor(part, hexColor);
}

function applyColorPreset(part, hexColor) {
    changeCharacterColor(part, hexColor);
}

function randomizeCharacterStyle() {
    const hairPal = ['#ffc0cb', '#fef08a', '#e0e7ff', '#854d0e', '#c084fc', '#22d3ee', '#1e293b', '#f97316', '#a855f7'];
    const eyePal = ['#38bdf8', '#c084fc', '#f43f5e', '#fbbf24', '#34d399', '#ec4899', '#6366f1'];
    const skinPal = ['#ffffff', '#ffe4e6', '#fef3c7', '#fed7aa'];
    const topsPal = ['#ffffff', '#18181b', '#f43f5e', '#0284c7', '#f472b6', '#a855f7', '#10b981', '#fbbf24'];
    const bottomsPal = ['#be123c', '#1e3a8a', '#ec4899', '#a855f7', '#0284c7', '#10b981', '#f59e0b'];
    const shoesPal = ['#ffffff', '#18181b', '#f43f5e', '#8b5cf6', '#0284c7'];

    const pick = arr => arr[Math.floor(Math.random() * arr.length)];
    changeCharacterColor('hair', pick(hairPal));
    changeCharacterColor('eyes', pick(eyePal));
    changeCharacterColor('skin', pick(skinPal));
    changeCharacterColor('tops', pick(topsPal));
    changeCharacterColor('bottoms', pick(bottomsPal));
    changeCharacterColor('shoes', pick(shoesPal));
}

function resetCharacterColors() {
    changeCharacterColor('hair', '#ffffff');
    changeCharacterColor('skin', '#ffffff');
    changeCharacterColor('eyes', '#ffffff');
    changeCharacterColor('tops', '#ffffff');
    changeCharacterColor('bottoms', '#18181b');
    changeCharacterColor('shoes', '#ffffff');
}

// ==========================================
// REAL-TIME HAIR COLLISION & SPRING PHYSICS
// ==========================================
// Vật lý tóc, khẩu hình và việc chuyển clip đều nằm trong core/character.js —
// bản nhúng embed.js dùng chung đúng cài đặt đó. Ở đây chỉ còn phần giao diện.
//
// Tự kiểm tra bộ phân loại nguyên âm: mở Console rồi gõ __vowelProbe().
// Phải ra "A->A I->I U->U E->E O->O", không có chữ SAI nào.
window.__vowelProbe = vowelSelfTest;

function updateAnimationHUD(clipName) {
    let hud = document.getElementById('anim-hud');
    if (!hud) {
        hud = document.createElement('div');
        hud.id = 'anim-hud';
        hud.style.cssText = 'position: absolute; bottom: 20px; left: 50%; transform: translateX(-50%); background: rgba(15, 23, 42, 0.85); backdrop-filter: blur(8px); border: 1px solid #ff4b8b; border-radius: 9999px; padding: 8px 24px; color: #fff; font-size: 14px; font-weight: 600; box-shadow: 0 4px 20px rgba(0,0,0,0.5); z-index: 1000; pointer-events: none; text-align: center;';
        document.body.appendChild(hud);
    }
    const st = stateByClip[clipName];
    const name = st ? `${st.icon} Trạng thái ${st.order}: ${st.desc}` : clipName;
    hud.innerHTML = `<span style="color: #ff4b8b;">Đang phát:</span> ${name}`;
}

/** Tô sáng nút của trạng thái đang chạy. Tách riêng vì bộ dựng bài cũng đổi
 *  trạng thái, mà nó gọi thẳng Character chứ không đi qua switchAnimationState. */
function highlightState(clipName) {
    document.querySelectorAll('.state-btn').forEach(b => {
        b.classList.remove('active');
        b.style.background = 'transparent';
    });
    const btn = document.getElementById(stateButtonId(clipName));
    if (btn) {
        btn.classList.add('active');
        const st = stateByClip[clipName];
        if (st) btn.style.background = hexToRgba(st.accent, 0.18);
    }
}

/** Giao quyền chọn động tác cho bộ dựng bài, và bật nhạc nếu chưa bật.
 *  Không có nhạc thì bộ dựng bài không có nhịp để bám, nên nó chỉ đặt một clip
 *  rồi đứng đó — người bấm nút sẽ tưởng nút hỏng. */
async function startDancing() {
    if (!character) return;
    const cb = document.getElementById('toggle-choreo');
    if (cb) cb.checked = true;
    character.setChoreography(true);
    // Cập nhật nút NGAY, trước khi đụng tới âm thanh: phần âm thanh có thể chờ,
    // còn người bấm thì phải thấy nút đổi lập tức.
    updateDanceButton();
    if (!isAudioPlaying && audioElement) {
        setupAudioContext();
        try {
            // Chờ CÓ HẠN. resume() không bao giờ hoàn tất khi trang chưa được
            // mở khoá, và await trần ở đây từng treo luôn cả phần cập nhật nút.
            if (audioContext && audioContext.state !== 'running') {
                await Promise.race([audioContext.resume(),
                                    new Promise(r => setTimeout(r, 700))]);
            }
            await audioElement.play();
            isAudioPlaying = true;
        } catch (err) {
            const n = document.getElementById('choreo-note');
            if (n) n.textContent = 'Bấm thêm một lần để trình duyệt cho phát nhạc.';
        }
    }
    updateAudioButton();
    updateDanceButton();
}

function stopDancing() {
    if (!character) return;
    character.setChoreography(false);
    const cb = document.getElementById('toggle-choreo');
    if (cb) cb.checked = false;
    updateDanceButton();
}

function updateDanceButton() {
    const b = document.getElementById('btn-dance');
    if (!b || !character) return;
    const on = character.choreo.enabled;
    b.textContent = on ? '⏹ Dừng Nhảy' : '💃 Nhảy Theo Nhạc';
    b.style.background = on
        ? 'linear-gradient(135deg,#475569,#64748b)'
        : 'linear-gradient(135deg,#7c3aed,#db2777)';
}

/** Nhãn nút nhạc phải theo bài đang chọn, không đóng đinh tên một bài. */
function updateAudioButton() {
    const b = document.getElementById('btn-toggle-audio');
    if (!b) return;
    b.textContent = isAudioPlaying
        ? ('⏹ Tắt ' + (currentTrack.label || 'nhạc'))
        : ('🎶 Bật ' + (currentTrack.label || 'nhạc'));
    b.style.background = isAudioPlaying ? '#e11d48' : '';
}

window.switchAnimationState = function(clipName) {
    if (!character) return;
    if (!animationsMap[clipName]) {
        console.warn('Không có clip', clipName, '— các clip có trong model:',
                     Object.keys(animationsMap));
        return;
    }
    highlightState(clipName);
    // Người dùng tự chọn trạng thái thì nhường quyền cho họ: để bộ dựng bài
    // chạy tiếp thì vài giây nữa nó lại đổi mất, tưởng nút bấm bị hỏng.
    if (character.choreo.enabled) {
        character.setChoreography(false);
        const cb = document.getElementById('toggle-choreo');
        if (cb) cb.checked = false;
        updateDanceButton();
    }
    // Character.setState lo phần hoà mềm và dừng hẳn clip cũ.
    if (!character.setState(clipName)) return;
    currentAction = character.current;
    currentActionName = character.currentName;
    updateAnimationHUD(clipName);
};

function setCameraView(view) {
    const btn = document.getElementById(`cam-${view}`);
    document.querySelectorAll('.btn-cam').forEach(b => b.classList.remove('active'));
    if (btn) btn.classList.add('active');
    if (!framing) return;
    // Cận cảnh thì tâm xoay dời sang chính bộ phận đang xem, nhờ vậy xoay quanh
    // khuôn mặt là quay quanh khuôn mặt chứ không quanh giữa người.
    const preset = {
        full: { pivot: [0, 1.1, 0], distance: 3.0 },
        face: { pivot: [0, 1.45, 0], distance: 0.85 },
        hand: { pivot: [-0.35, 1.05, 0.1], distance: 0.6 },
    }[view] || { pivot: [0, 1.1, 0], distance: 3.0 };
    framing.offset.x = 0;
    framing.offset.y = 0;
    framing.apply();
    framing.setPivot(new THREE.Vector3(...preset.pivot), preset.distance);
}

function setupUIEventListeners() {
    document.getElementById('toggle-skeleton').addEventListener('change', (e) => {
        if (skeletonHelper) {
            skeletonHelper.visible = e.target.checked;
        }
    });

    document.getElementById('toggle-particles').addEventListener('change', (e) => {
        if (particlesSystem) particlesSystem.visible = e.target.checked;
    });

    document.getElementById('toggle-wireframe').addEventListener('change', (e) => {
        isWireframe = e.target.checked;
        if (!characterModel) return;
        characterModel.traverse((child) => {
            if (child.isMesh && child.material) {
                if (Array.isArray(child.material)) child.material.forEach(m => m.wireframe = isWireframe);
                else child.material.wireframe = isWireframe;
            }
        });
    });

    const dragHint = document.getElementById('drag-hint');
    const rotBtn = document.getElementById('btn-drag-rotate');
    const movBtn = document.getElementById('btn-drag-move');
    const setDrag = (mode) => {
        if (!framing) return;
        framing.setDragMode(mode);
        const moving = mode === 'dichuyen';
        rotBtn.classList.toggle('active', !moving);
        movBtn.classList.toggle('active', moving);
        dragHint.textContent = moving
            ? 'Kéo chuột trái để DỜI nhân vật trong khung · chuột phải để xoay.'
            : 'Kéo chuột trái để XOAY quanh nhân vật · chuột phải cũng xoay.';
    };
    rotBtn.addEventListener('click', () => setDrag('xoay'));
    movBtn.addEventListener('click', () => setDrag('dichuyen'));
    document.getElementById('btn-view-reset').addEventListener('click', () => {
        if (framing) framing.reset(3.0);
    });
    setDrag('xoay');

    document.getElementById('toggle-autorotate').addEventListener('change', (e) => {
        controls.autoRotate = e.target.checked;
        controls.autoRotateSpeed = 2.0;
    });

    const btnPlayPause = document.getElementById('btn-play-pause');
    btnPlayPause.addEventListener('click', () => {
        if (mixer) {
            mixer.timeScale = mixer.timeScale === 0 ? 1 : 0;
            btnPlayPause.textContent = mixer.timeScale === 0 ? '▶ Tiếp Tục' : '⏸ Tạm Dừng Hoạt Ảnh';
        }
    });

    // --- tải bài hát lên ---
    const songDrop = document.getElementById('song-drop');
    const beatNote = document.getElementById('beat-note');
    let uploadedUrl = null;
    // Chrome chỉ cho AudioContext chạy khi trang đã có thao tác bấm thật. Sự
    // kiện 'change' của ô chọn file KHÔNG được tính là thao tác đó, còn kích
    // hoạt tạm thời từ cú bấm mở hộp thoại thì đã hết hạn trong lúc người dùng
    // ngồi duyệt file. Nên nếu đợi tới lúc chọn xong file mới mở khoá thì
    // resume() treo vĩnh viễn: thẻ audio đứng im, không lỗi, không thông báo —
    // đúng cảnh "chọn mp3 mà nhạc không chạy". Vì vậy mở khoá ngay ở cú bấm
    // đầu tiên trên trang, tức là chính cú bấm mở hộp thoại chọn file.
    function unlockAudio() {
        if (!audioElement) return;
        setupAudioContext();
        if (audioContext && audioContext.state === 'running') {
            window.removeEventListener('pointerdown', unlockAudio, true);
            window.removeEventListener('keydown', unlockAudio, true);
        }
    }
    window.addEventListener('pointerdown', unlockAudio, true);
    window.addEventListener('keydown', unlockAudio, true);

    function offerManualPlay(msg, file) {
        songDrop.innerHTML = msg
            + '<br><button id="song-retry" class="btn" style="margin-top:6px;font-size:11px;padding:5px 9px;">▶ Bấm để phát</button>';
        const retry = document.getElementById('song-retry');
        if (!retry) return;
        retry.addEventListener('click', async () => {
            try {
                // Cú bấm này là thao tác thật nên resume() chắc chắn xong.
                if (audioContext && audioContext.state !== 'running') await audioContext.resume();
                await audioElement.play();
                afterSongStarted(file);
            } catch (e) { songDrop.textContent = 'Vẫn không phát được: ' + e.message; }
        });
    }

    function afterSongStarted(file) {
        isAudioPlaying = true;
        const btn = document.getElementById('btn-toggle-audio');
        if (btn) btn.textContent = '⏸ Tắt Nhạc';
        songDrop.innerHTML = 'Đang phát: <b style="color:#e2e8f0">' + file.name + '</b>';
        startDancing();
    }

    async function useSong(file) {
        if (!file) return;
        if (!audioElement) setupAudioElement();
        setupAudioContext();
        if (uploadedUrl) URL.revokeObjectURL(uploadedUrl);
        uploadedUrl = URL.createObjectURL(file);
        audioElement.src = uploadedUrl;
        audioElement.load();
        // Bài người dùng tự tải lên mặc định coi là CÓ lời: người tải biết rõ
        // hơn mọi phép đoán từ tín hiệu — xem chú thích trong scripts/catalog.py.
        currentTrack = { file: file.name, label: file.name, vocals: true };
        if (character) character.beat.reset();
        updateLipSyncNote();
        songDrop.innerHTML = 'Đang mở <b style="color:#e2e8f0">' + file.name + '</b>…';
        try {
            // Chờ context nhưng CÓ HẠN: khi trang chưa được mở khoá, resume()
            // không bao giờ hoàn tất, và await trần sẽ nuốt luôn cả thông báo.
            if (audioContext && audioContext.state !== 'running') {
                await Promise.race([
                    audioContext.resume(),
                    new Promise(res => setTimeout(res, 700)),
                ]);
            }
            if (audioElement.readyState < 2) {
                await new Promise(res => {
                    const done = () => res();
                    audioElement.addEventListener('canplay', done, { once: true });
                    audioElement.addEventListener('error', done, { once: true });
                    setTimeout(done, 8000);
                });
            }
            if (audioElement.error) {
                songDrop.textContent = 'Không đọc được file này (mã lỗi '
                    + audioElement.error.code + '). Hãy thử file mp3/m4a/wav khác.';
                return;
            }
            await audioElement.play();
            // Thẻ audio chạy nhưng context còn treo thì hoàn toàn không ra
            // tiếng, vì cả đồ thị âm thanh đi qua context này.
            if (audioContext && audioContext.state !== 'running') {
                offerManualPlay('Trình duyệt chưa cho phát tự động.', file);
                return;
            }
            afterSongStarted(file);
        } catch (err) {
            offerManualPlay('Trình duyệt chặn phát tự động (' + err.name + ').', file);
        }
    }
    if (songDrop) {
        document.getElementById('song-pick').addEventListener('change',
            e => useSong(e.target.files[0]));
        ['dragenter', 'dragover'].forEach(t => songDrop.addEventListener(t, e => {
            e.preventDefault(); songDrop.style.borderColor = '#7fb2ff';
        }));
        songDrop.addEventListener('dragleave', () => { songDrop.style.borderColor = '#4b5675'; });
        songDrop.addEventListener('drop', e => {
            e.preventDefault(); songDrop.style.borderColor = '#4b5675';
            useSong(e.dataTransfer.files[0]);
        });
        setInterval(() => {
            if (!character || !beatNote) return;
            const b = character.beat;
            beatNote.textContent = (isAudioPlaying && b.bpm)
                ? `nhịp ${b.bpm.toFixed(0)} phách/phút · độ tin ${b.confidence.toFixed(0)}`
                  + ` · tốc độ nhảy ×${(character.current ? character.current.timeScale : 1).toFixed(2)}`
                : '';
        }, 400);
    }

    const cbChoreo = document.getElementById('toggle-choreo');
    if (cbChoreo) cbChoreo.addEventListener('change', () => {
        if (!character) return;
        character.setChoreography(cbChoreo.checked);
    });
    const cbAlive = document.getElementById('toggle-alive');
    if (cbAlive) cbAlive.addEventListener('change', () => {
        if (character) character.alive.enabled = cbAlive.checked;
    });

    const lyricsBox = document.getElementById('lyrics-box');
    const lyricsNote = document.getElementById('lyrics-note');
    if (lyricsBox) {
        let timer = null;
        lyricsBox.addEventListener('input', () => {
            clearTimeout(timer);
            timer = setTimeout(() => {
                if (!character) return;
                const r = character.setLyrics(lyricsBox.value);
                lyricsNote.textContent = r
                    ? `${r.lines} câu · ${r.syllables} âm tiết — khẩu hình lấy nguyên âm từ lời,`
                      + ' thời điểm lấy từ tiếng hát.'
                    : 'Chưa có lời — khẩu hình đoán nguyên âm từ formant.';
            }, 400);
        });
    }

    const btnAudio = document.getElementById('btn-toggle-audio');
    btnAudio.addEventListener('click', async () => {
        setupAudioContext();
        if (!isAudioPlaying) {
            if (audioContext && audioContext.state !== 'running') await audioContext.resume();
            try { await audioElement.play(); isAudioPlaying = true; } catch (e) { /* bị chặn */ }
            const cb = document.getElementById('toggle-choreo');
            if (cb && cb.checked && character) character.setChoreography(true);
        } else {
            audioElement.pause();
            isAudioPlaying = false;
            currentVocalEnergy = 0;
            resetAllMorphs();
        }
        updateAudioButton();
        updateDanceButton();
    });

    const btnDance = document.getElementById('btn-dance');
    if (btnDance) btnDance.addEventListener('click', () => {
        if (character && character.choreo.enabled) stopDancing();
        else startDancing();
    });
    updateAudioButton();
}

function onWindowResize() {
    if (framing) framing.apply();
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
}

function animate() {
    requestAnimationFrame(animate);
    const delta = clock.getDelta();

    // Character lo cả ba: chạy mixer, mô phỏng tóc, và khẩu hình theo nguyên âm.
    if (character) {
        const lipToggle = document.getElementById('toggle-auto-lipsync');
        let audio = null;
        if (isAudioPlaying && analyser && audioSpectrumDb) {
            analyser.getFloatFrequencyData(audioSpectrumDb);
            audio = {
                spectrumDb: audioSpectrumDb,
                sampleRate: audioContext.sampleRate,
                vocals: currentTrack.vocals && (!lipToggle || lipToggle.checked),
            };
        }
        character.update(delta, audio);

        // Bộ dựng bài đổi trạng thái từ bên trong Character, nên giao diện phải
        // tự soi lại chứ không được chờ ai gọi.
        if (character.currentName !== shownState) {
            shownState = character.currentName;
            highlightState(shownState);
        }
        const note = document.getElementById('choreo-note');
        if (note) {
            if (!character.choreo.enabled) {
                note.textContent = '';
            } else if (!isAudioPlaying) {
                // Đừng ghi đè lời nhắc bấm lại khi trình duyệt còn chặn nhạc.
                if (!note.textContent) note.textContent = 'bật nhạc để nhân vật bám nhịp';
            } else if (character.beat.bpm > 0) {
                note.textContent = `${character.beat.bpm.toFixed(0)} phách/phút · nền `
                    + `${String(character.choreo.base).split('_')[0]} · tay `
                    + (character.gesture ? character.gesture.split('_')[0] : 'nghỉ')
                    + ` · phách ${character.choreo.beats}`;
            } else {
                note.textContent = 'đang nghe để dò nhịp bài hát…';
            }
        }
    }

    if (skeletonHelper && skeletonHelper.visible) {
        skeletonHelper.update();
    }

    // SNAPPY BLINK & PLAYFUL WINK
    updateFacialAnimation(delta);

    // Mức âm thanh thô, chỉ để hiệu ứng lấp lánh nhún theo nhạc.
    if (isAudioPlaying && analyser && audioDataArray) {
        analyser.getByteFrequencyData(audioDataArray);
        let sum = 0;
        for (let i = 4; i < 60; i++) sum += audioDataArray[i];
        currentVocalEnergy = Math.min(1.0, (sum / 56) / 120);
    } else {
        currentVocalEnergy = 0;
    }

    // Gentle Sparkle Float
    if (particlesSystem && particlesSystem.visible) {
        const positions = particlesSystem.geometry.attributes.position.array;
        for (let i = 1; i < positions.length; i += 3) {
            positions[i] += delta * 0.25;
            if (positions[i] > 4.5) positions[i] = 0;
        }
        particlesSystem.geometry.attributes.position.needsUpdate = true;
    }

    controls.update();
    renderer.render(scene, camera);
}

window.onload = init;

// ==========================================
// Hàm được gọi từ thuộc tính onclick/oninput trong index.html.
// Module có phạm vi riêng nên phải gán tường minh vào window.
// ==========================================
Object.assign(window, {
    setCameraView,
    changeCharacterColor,
    applyColorPreset,
    randomizeCharacterStyle,
    resetCharacterColors,
    triggerManualWink,
});
