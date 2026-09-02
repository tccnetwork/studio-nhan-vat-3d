// Web 3D Viewer for Procedural Cyber Singer (Phương án 3)

let scene, camera, renderer, controls;
let mixer, currentAction, clock;
let characterModel = null;
let spotlightLeft, spotlightRight;
let particlesSystem;
let isWireframe = false;
let audioContext = null, isAudioPlaying = false, audioTimer = null;

const container = document.getElementById('canvas-container');

function init() {
    // 1. Scene & Clock
    scene = new THREE.Scene();
    scene.background = new THREE.Color(0x0a0c14);
    scene.fog = new THREE.FogExp2(0x0a0c14, 0.08);
    clock = new THREE.Clock();

    // 2. Camera
    camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 0.1, 100);
    camera.position.set(0, 1.6, 4.2);

    // 3. Renderer
    renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.2;
    container.appendChild(renderer.domElement);

    // 4. Controls
    controls = new THREE.OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    controls.maxPolarAngle = Math.PI / 2 + 0.05;
    controls.minDistance = 1.0;
    controls.maxDistance = 10.0;
    controls.target.set(0, 1.1, 0);
    controls.update();

    // 5. Lights
    setupLighting();

    // 6. Environment (Stage, Grid, Dust Particles)
    setupStageEnvironment();

    // 7. Load GLB Model
    loadModel();

    // 8. Event Listeners
    setupUIEventListeners();
    window.addEventListener('resize', onWindowResize);

    // 9. Start Loop
    animate();
}

function setupLighting() {
    // Ambient Light
    const ambientLight = new THREE.AmbientLight(0x223355, 1.2);
    scene.add(ambientLight);

    // Main Stage Key Light
    const keyLight = new THREE.DirectionalLight(0xffffff, 1.5);
    keyLight.position.set(2, 5, 3);
    keyLight.castShadow = true;
    keyLight.shadow.mapSize.width = 1024;
    keyLight.shadow.mapSize.height = 1024;
    scene.add(keyLight);

    // Stage Spotlights (Cyan & Magenta)
    spotlightLeft = new THREE.SpotLight(0x00f2fe, 3.5, 15, Math.PI / 6, 0.4, 1);
    spotlightLeft.position.set(-3, 4, 2);
    spotlightLeft.target.position.set(0, 1.2, 0);
    scene.add(spotlightLeft);
    scene.add(spotlightLeft.target);

    spotlightRight = new THREE.SpotLight(0xff007f, 3.5, 15, Math.PI / 6, 0.4, 1);
    spotlightRight.position.set(3, 4, 2);
    spotlightRight.target.position.set(0, 1.2, 0);
    scene.add(spotlightRight);
    scene.add(spotlightRight.target);

    // Rim light from behind
    const rimLight = new THREE.DirectionalLight(0x00ffff, 1.8);
    rimLight.position.set(0, 3, -4);
    scene.add(rimLight);
}

function setupStageEnvironment() {
    // Stage Floor Grid
    const grid = new THREE.GridHelper(20, 40, 0x00f2fe, 0x1a2536);
    grid.position.y = -0.01;
    scene.add(grid);

    // Dust particles
    const particleCount = 400;
    const geometry = new THREE.BufferGeometry();
    const positions = new Float32Array(particleCount * 3);
    const colors = new Float32Array(particleCount * 3);

    for (let i = 0; i < particleCount; i++) {
        positions[i * 3] = (Math.random() - 0.5) * 8;
        positions[i * 3 + 1] = Math.random() * 4;
        positions[i * 3 + 2] = (Math.random() - 0.5) * 8;

        // Cyan / Magenta colored particles
        if (Math.random() > 0.5) {
            colors[i * 3] = 0.0;
            colors[i * 3 + 1] = 0.9;
            colors[i * 3 + 2] = 1.0;
        } else {
            colors[i * 3] = 1.0;
            colors[i * 3 + 1] = 0.2;
            colors[i * 3 + 2] = 0.8;
        }
    }

    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));

    const material = new THREE.PointsMaterial({
        size: 0.035,
        vertexColors: true,
        transparent: true,
        opacity: 0.7,
        blending: THREE.AdditiveBlending
    });

    particlesSystem = new THREE.Points(geometry, material);
    scene.add(particlesSystem);
}

function loadModel() {
    const loader = new THREE.GLTFLoader();
    const modelPath = '../model/procedural_cyber_singer.glb';

    loader.load(modelPath, (gltf) => {
        characterModel = gltf.scene;
        scene.add(characterModel);

        // Stats calculation
        let verts = 0;
        let triangles = 0;
        characterModel.traverse((child) => {
            if (child.isMesh) {
                child.castShadow = true;
                child.receiveShadow = true;
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
        valSpeed.textContent = `${val.toFixed(1)}x (${Math.round(val * 120)} BPM)`;
        if (mixer) mixer.timeScale = val;
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

    // Spotlight Toggle
    document.getElementById('toggle-spotlight').addEventListener('change', (e) => {
        spotlightLeft.visible = e.target.checked;
        spotlightRight.visible = e.target.checked;
    });

    // Particles Toggle
    document.getElementById('toggle-particles').addEventListener('change', (e) => {
        if (particlesSystem) particlesSystem.visible = e.target.checked;
    });

    // Auto Rotate
    document.getElementById('toggle-autorotate').addEventListener('change', (e) => {
        controls.autoRotate = e.target.checked;
        controls.autoRotateSpeed = 2.0;
    });

    // Audio Synth Beat
    const btnAudio = document.getElementById('btn-toggle-audio');
    btnAudio.addEventListener('click', () => {
        if (!isAudioPlaying) {
            startAudioBeat();
            btnAudio.textContent = '🔇 Tắt Beat Nhạc';
            btnAudio.style.background = '#e11d48';
        } else {
            stopAudioBeat();
            btnAudio.textContent = '🔊 Bật Nhạc Beat Sân Khấu';
            btnAudio.style.background = '';
        }
    });
}

// Procedural Web Audio Synth Beat (120 BPM Funky Cyber Vocal Beat)
function startAudioBeat() {
    if (!audioContext) {
        audioContext = new (window.AudioContext || window.webkitAudioContext)();
    }
    if (audioContext.state === 'suspended') {
        audioContext.resume();
    }
    isAudioPlaying = true;
    let step = 0;
    const interval = (60 / 120) * 1000 / 4; // 16th notes at 120 BPM

    audioTimer = setInterval(() => {
        if (!isAudioPlaying) return;
        const time = audioContext.currentTime;

        // Kick on beat 0, 4, 8, 12
        if (step % 4 === 0) {
            playKick(time);
        }
        // Hihat on offbeats
        if (step % 2 === 1) {
            playHiHat(time);
        }
        // Synth bass/chord every 2 beats
        if (step % 8 === 0) {
            playSynth(time, [220, 261.63, 329.63][(step / 8) % 3]);
        }
        step = (step + 1) % 16;
    }, interval);
}

function stopAudioBeat() {
    isAudioPlaying = false;
    if (audioTimer) clearInterval(audioTimer);
}

function playKick(time) {
    const osc = audioContext.createOscillator();
    const gain = audioContext.createGain();
    osc.frequency.setValueAtTime(130, time);
    osc.frequency.exponentialRampToValueAtTime(0.01, time + 0.25);
    gain.gain.setValueAtTime(0.8, time);
    gain.gain.exponentialRampToValueAtTime(0.01, time + 0.25);
    osc.connect(gain);
    gain.connect(audioContext.destination);
    osc.start(time);
    osc.stop(time + 0.25);
}

function playHiHat(time) {
    const osc = audioContext.createOscillator();
    const gain = audioContext.createGain();
    osc.type = 'highpass';
    osc.frequency.setValueAtTime(8000, time);
    gain.gain.setValueAtTime(0.15, time);
    gain.gain.exponentialRampToValueAtTime(0.01, time + 0.05);
    osc.connect(gain);
    gain.connect(audioContext.destination);
    osc.start(time);
    osc.stop(time + 0.05);
}

function playSynth(time, freq) {
    const osc = audioContext.createOscillator();
    const gain = audioContext.createGain();
    osc.type = 'sawtooth';
    osc.frequency.setValueAtTime(freq, time);
    gain.gain.setValueAtTime(0.2, time);
    gain.gain.exponentialRampToValueAtTime(0.01, time + 0.4);
    osc.connect(gain);
    gain.connect(audioContext.destination);
    osc.start(time);
    osc.stop(time + 0.4);
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

    // Spotlight gentle movement
    if (spotlightLeft && spotlightRight) {
        spotlightLeft.position.x = -3 + Math.sin(elapsed * 1.5) * 0.8;
        spotlightRight.position.x = 3 + Math.cos(elapsed * 1.5) * 0.8;
    }

    // Gentle particle floating
    if (particlesSystem) {
        const positions = particlesSystem.geometry.attributes.position.array;
        for (let i = 1; i < positions.length; i += 3) {
            positions[i] += delta * 0.2;
            if (positions[i] > 4.0) positions[i] = 0;
        }
        particlesSystem.geometry.attributes.position.needsUpdate = true;
    }

    renderer.render(scene, camera);
}

window.addEventListener('DOMContentLoaded', init);
