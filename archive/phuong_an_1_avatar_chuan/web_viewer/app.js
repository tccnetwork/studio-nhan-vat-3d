// Web 3D Viewer for Humanoid Singer Avatar (Phương án 1)

let scene, camera, renderer, controls;
let mixer, currentAction, clock;
let characterModel = null, skinnedMesh = null;
let skeletonHelper = null;
let spotlight;
let isWireframe = false;
let isAutoLipSync = true;
let audioContext = null, isAudioPlaying = false, audioTimer = null;

const morphIndexMap = {
    'aa': 0,
    'O': 1,
    'E': 2,
    'U': 3,
    'jaw': 4,
    'smile': 5,
    'blink': 6
};

const container = document.getElementById('canvas-container');

function init() {
    // 1. Scene & Clock
    scene = new THREE.Scene();
    scene.background = new THREE.Color(0x0d1117);
    scene.fog = new THREE.FogExp2(0x0d1117, 0.06);
    clock = new THREE.Clock();

    // 2. Camera
    camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 0.1, 100);
    camera.position.set(0, 1.6, 3.8);

    // 3. Renderer
    renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.1;
    container.appendChild(renderer.domElement);

    // 4. Controls
    controls = new THREE.OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    controls.maxPolarAngle = Math.PI / 2 + 0.05;
    controls.minDistance = 0.8;
    controls.maxDistance = 8.0;
    controls.target.set(0, 1.4, 0);
    controls.update();

    // 5. Lighting
    setupLighting();

    // 6. Stage Floor
    setupStage();

    // 7. Load GLB Model
    loadModel();

    // 8. Event Listeners
    setupUIEventListeners();
    window.addEventListener('resize', onWindowResize);

    // 9. Start Loop
    animate();
}

function setupLighting() {
    // Ambient
    const ambientLight = new THREE.AmbientLight(0x334455, 1.2);
    scene.add(ambientLight);

    // Key Light
    const keyLight = new THREE.DirectionalLight(0xffffff, 1.6);
    keyLight.position.set(2, 4, 3);
    keyLight.castShadow = true;
    keyLight.shadow.mapSize.width = 1024;
    keyLight.shadow.mapSize.height = 1024;
    scene.add(keyLight);

    // Fill Light (Soft cool blue)
    const fillLight = new THREE.DirectionalLight(0x38bdf8, 0.8);
    fillLight.position.set(-3, 2, 2);
    scene.add(fillLight);

    // Spotlight directly above stage
    spotlight = new THREE.SpotLight(0x10b981, 3.0, 12, Math.PI / 5, 0.5, 1);
    spotlight.position.set(0, 4.5, 1.5);
    spotlight.target.position.set(0, 1.4, 0);
    scene.add(spotlight);
    scene.add(spotlight.target);

    // Rim light (Behind character for silhouette definition)
    const rimLight = new THREE.DirectionalLight(0xec4899, 1.5);
    rimLight.position.set(0, 3, -3);
    scene.add(rimLight);
}

function setupStage() {
    // Stage Floor Disc
    const stageGeo = new THREE.CylinderGeometry(1.6, 1.65, 0.1, 48);
    const stageMat = new THREE.MeshStandardMaterial({
        color: 0x161b22,
        roughness: 0.2,
        metalness: 0.6
    });
    const stageMesh = new THREE.Mesh(stageGeo, stageMat);
    stageMesh.position.y = 0.05;
    stageMesh.receiveShadow = true;
    scene.add(stageMesh);

    // Grid Floor
    const grid = new THREE.GridHelper(16, 32, 0x10b981, 0x21262d);
    grid.position.y = 0;
    scene.add(grid);
}

function loadModel() {
    const loader = new THREE.GLTFLoader();
    const modelPath = '../model/singer_humanoid_avatar.glb';

    loader.load(modelPath, (gltf) => {
        characterModel = gltf.scene;
        scene.add(characterModel);

        // Stats calculation & Finding Skinned Mesh
        let verts = 0;
        let triangles = 0;
        characterModel.traverse((child) => {
            if (child.isMesh) {
                child.castShadow = true;
                child.receiveShadow = true;
                if (child.isSkinnedMesh) {
                    skinnedMesh = child;
                }
                if (child.geometry) {
                    verts += child.geometry.attributes.position.count;
                    if (child.geometry.index) {
                        triangles += child.geometry.index.count / 3;
                    } else {
                        triangles += child.geometry.attributes.position.count / 3;
                    }
                }
            }
        });

        document.getElementById('stat-verts').textContent = verts.toLocaleString();
        document.getElementById('stat-triangles').textContent = triangles.toLocaleString();

        // Setup Skeleton Helper
        skeletonHelper = new THREE.SkeletonHelper(characterModel);
        skeletonHelper.material.linewidth = 2;
        skeletonHelper.visible = false;
        scene.add(skeletonHelper);

        // Setup Animation
        if (gltf.animations && gltf.animations.length > 0) {
            mixer = new THREE.AnimationMixer(characterModel);
            currentAction = mixer.clipAction(gltf.animations[0]);
            currentAction.play();
        }
    }, undefined, (err) => {
        console.error("Error loading model:", err);
    });
}

function setupUIEventListeners() {
    // Play/Pause button
    const btnPlay = document.getElementById('btn-play-pause');
    btnPlay.addEventListener('click', () => {
        if (!currentAction) return;
        if (currentAction.paused) {
            currentAction.paused = false;
            btnPlay.textContent = '⏸ Tạm Dừng';
            btnPlay.classList.add('primary');
        } else {
            currentAction.paused = true;
            btnPlay.textContent = '▶ Tiếp Tục Hát';
            btnPlay.classList.remove('primary');
        }
    });

    // Reset Pose
    document.getElementById('btn-reset-pose').addEventListener('click', () => {
        if (!currentAction) return;
        currentAction.reset();
        currentAction.play();
        btnPlay.textContent = '⏸ Tạm Dừng';
        btnPlay.classList.add('primary');
    });

    // Speed Slider
    const sliderSpeed = document.getElementById('slider-speed');
    const valSpeed = document.getElementById('val-speed');
    sliderSpeed.addEventListener('input', (e) => {
        const val = parseFloat(e.target.value);
        valSpeed.textContent = `${val.toFixed(1)}x`;
        if (mixer) mixer.timeScale = val;
    });

    // Skeleton Helper Toggle
    document.getElementById('toggle-skeleton').addEventListener('change', (e) => {
        if (skeletonHelper) skeletonHelper.visible = e.target.checked;
    });

    // Wireframe Toggle
    document.getElementById('toggle-wireframe').addEventListener('change', (e) => {
        isWireframe = e.target.checked;
        if (!characterModel) return;
        characterModel.traverse((child) => {
            if (child.isMesh && child.material) {
                if (Array.isArray(child.material)) {
                    child.material.forEach(m => m.wireframe = isWireframe);
                } else {
                    child.material.wireframe = isWireframe;
                }
            }
        });
    });

    // Auto Rotate
    document.getElementById('toggle-autorotate').addEventListener('change', (e) => {
        controls.autoRotate = e.target.checked;
        controls.autoRotateSpeed = 2.0;
    });

    // Spotlight Toggle
    document.getElementById('toggle-spotlight').addEventListener('change', (e) => {
        spotlight.visible = e.target.checked;
    });

    // Auto LipSync Toggle
    const toggleAutoLip = document.getElementById('toggle-auto-lipsync');
    toggleAutoLip.addEventListener('change', (e) => {
        isAutoLipSync = e.target.checked;
        const sliders = document.querySelectorAll('.morph-slider');
        sliders.forEach(s => s.disabled = isAutoLipSync);
    });

    // Morph Target Sliders (Manual Lip-Sync)
    ['aa', 'O', 'E', 'U', 'jaw', 'smile', 'blink'].forEach((viseme) => {
        const slider = document.getElementById(`morph-${viseme}`);
        const valLabel = document.getElementById(`val-${viseme}`);
        slider.addEventListener('input', (e) => {
            const val = parseFloat(e.target.value);
            valLabel.textContent = `${Math.round(val * 100)}%`;
            if (skinnedMesh && skinnedMesh.morphTargetInfluences) {
                const idx = morphIndexMap[viseme];
                skinnedMesh.morphTargetInfluences[idx] = val;
            }
        });
    });

    // Audio Demo
    const btnAudio = document.getElementById('btn-toggle-audio');
    btnAudio.addEventListener('click', () => {
        if (!isAudioPlaying) {
            startAudioVocalSong();
            btnAudio.textContent = '🔇 Tắt Nhạc Demo';
            btnAudio.style.background = '#e11d48';
        } else {
            stopAudioVocalSong();
            btnAudio.textContent = '🔊 Bật Nhạc Hát Demo';
            btnAudio.style.background = '';
        }
    });
}

// Procedural Audio Vocal Synthesizer
function startAudioVocalSong() {
    if (!audioContext) {
        audioContext = new (window.AudioContext || window.webkitAudioContext)();
    }
    if (audioContext.state === 'suspended') {
        audioContext.resume();
    }
    isAudioPlaying = true;
    
    // Melodic notes in C Major / Pentatonic (C4, D4, E4, G4, A4, C5)
    const melody = [261.63, 293.66, 329.63, 392.00, 440.00, 523.25, 440.00, 392.00];
    let noteIdx = 0;

    audioTimer = setInterval(() => {
        if (!isAudioPlaying) return;
        const time = audioContext.currentTime;
        const freq = melody[noteIdx % melody.length];

        playVocalSynthNote(time, freq);
        noteIdx++;
    }, 450);
}

function stopAudioVocalSong() {
    isAudioPlaying = false;
    if (audioTimer) clearInterval(audioTimer);
}

function playVocalSynthNote(time, freq) {
    const osc = audioContext.createOscillator();
    const gain = audioContext.createGain();
    const filter = audioContext.createBiquadFilter();

    osc.type = 'triangle';
    osc.frequency.setValueAtTime(freq, time);

    filter.type = 'bandpass';
    filter.frequency.setValueAtTime(freq * 1.5, time);
    filter.Q.setValueAtTime(3.0, time);

    gain.gain.setValueAtTime(0.01, time);
    gain.gain.linearRampToValueAtTime(0.3, time + 0.08);
    gain.gain.exponentialRampToValueAtTime(0.001, time + 0.42);

    osc.connect(filter);
    filter.connect(gain);
    gain.connect(audioContext.destination);

    osc.start(time);
    osc.stop(time + 0.45);
}

function onWindowResize() {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
}

function animate() {
    requestAnimationFrame(animate);

    const delta = clock.getDelta();
    const elapsed = clock.getElapsedTime();

    if (mixer) mixer.update(delta);
    controls.update();

    // Auto Lip-Sync Singing Simulation
    if (isAutoLipSync && skinnedMesh && skinnedMesh.morphTargetInfluences) {
        const t = elapsed;
        const w_aa = Math.max(0, Math.sin(t * Math.PI * 4.0)) * 0.85;
        const w_O = Math.max(0, Math.cos(t * Math.PI * 2.0)) * 0.6;
        const w_E = Math.max(0, Math.sin(t * Math.PI * 3.0 + 1.0)) * 0.5;
        const w_U = Math.max(0, Math.cos(t * Math.PI * 3.0)) * 0.4;
        const w_jaw = Math.max(0, Math.sin(t * Math.PI * 2.0)) * 0.9;
        const w_smile = 0.3 + 0.3 * Math.sin(t * Math.PI * 1.0);
        const w_blink = (t % 3.5 < 0.15) ? 1.0 : 0.0;

        skinnedMesh.morphTargetInfluences[morphIndexMap['aa']] = w_aa;
        skinnedMesh.morphTargetInfluences[morphIndexMap['O']] = w_O;
        skinnedMesh.morphTargetInfluences[morphIndexMap['E']] = w_E;
        skinnedMesh.morphTargetInfluences[morphIndexMap['U']] = w_U;
        skinnedMesh.morphTargetInfluences[morphIndexMap['jaw']] = w_jaw;
        skinnedMesh.morphTargetInfluences[morphIndexMap['smile']] = w_smile;
        skinnedMesh.morphTargetInfluences[morphIndexMap['blink']] = w_blink;

        // Update UI labels when auto lipsync is active
        document.getElementById('val-aa').textContent = `${Math.round(w_aa * 100)}%`;
        document.getElementById('val-O').textContent = `${Math.round(w_O * 100)}%`;
        document.getElementById('val-E').textContent = `${Math.round(w_E * 100)}%`;
        document.getElementById('val-U').textContent = `${Math.round(w_U * 100)}%`;
        document.getElementById('val-jaw').textContent = `${Math.round(w_jaw * 100)}%`;
        document.getElementById('val-smile').textContent = `${Math.round(w_smile * 100)}%`;
        document.getElementById('val-blink').textContent = `${Math.round(w_blink * 100)}%`;
        
        document.getElementById('morph-aa').value = w_aa;
        document.getElementById('morph-O').value = w_O;
        document.getElementById('morph-E').value = w_E;
        document.getElementById('morph-U').value = w_U;
        document.getElementById('morph-jaw').value = w_jaw;
        document.getElementById('morph-smile').value = w_smile;
        document.getElementById('morph-blink').value = w_blink;
    }

    renderer.render(scene, camera);
}

window.addEventListener('DOMContentLoaded', init);
