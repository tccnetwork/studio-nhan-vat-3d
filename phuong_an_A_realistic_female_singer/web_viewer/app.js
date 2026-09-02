// Web 3D Studio for Realistic Female Pop Singer (Phong Cách A) with Full-Body Dance & LipSync

let scene, camera, renderer, controls, clock;
let characterModel = null, morphMeshes = [], mixer = null;
let isWireframe = false;

let audioContext = null, analyser = null, audioSource = null;
let audioDataArray = null, audioElement = null;
let isAudioPlaying = false;
let currentVocalEnergy = 0;

const container = document.getElementById('canvas-container');

function init() {
    scene = new THREE.Scene();
    scene.background = new THREE.Color(0x0e1320);
    scene.fog = new THREE.FogExp2(0x0e1320, 0.035);
    clock = new THREE.Clock();

    camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 0.1, 100);
    camera.position.set(0, 1.45, 3.0); // Full body view

    renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.shadowMap.enabled = true;
    renderer.outputEncoding = THREE.sRGBEncoding;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.3;
    container.appendChild(renderer.domElement);

    controls = new THREE.OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    controls.target.set(0, 1.1, 0);
    controls.update();

    setupLighting();
    setupStage();
    setupAudioElement();
    loadModel('../model/female_singer_realistic.glb?v=' + Date.now());
    setupUIEventListeners();

    window.addEventListener('resize', onWindowResize);
    animate();
}

function setupLighting() {
    scene.add(new THREE.AmbientLight(0xffffff, 1.6));

    const frontLight = new THREE.DirectionalLight(0xffffff, 2.0);
    frontLight.position.set(0, 3.0, 3.0);
    frontLight.castShadow = true;
    scene.add(frontLight);

    const spot = new THREE.SpotLight(0x38bdf8, 3.0, 12, Math.PI / 4, 0.3);
    spot.position.set(0, 4.0, 2.0);
    spot.target.position.set(0, 1.1, 0);
    scene.add(spot);
    scene.add(spot.target);
}

function setupStage() {
    const stageGeo = new THREE.CylinderGeometry(2.0, 2.1, 0.1, 64);
    const stageMat = new THREE.MeshStandardMaterial({
        color: 0x1e293b,
        roughness: 0.2,
        metalness: 0.8
    });
    const stageMesh = new THREE.Mesh(stageGeo, stageMat);
    stageMesh.position.y = 0.05;
    stageMesh.receiveShadow = true;
    scene.add(stageMesh);

    const grid = new THREE.GridHelper(16, 32, 0x38bdf8, 0x334155);
    grid.position.y = 0;
    scene.add(grid);
}

function setupAudioElement() {
    audioElement = new Audio('../../audio/vocal_song_pop.mp3');
    audioElement.crossOrigin = "anonymous";
    audioElement.loop = true;
}

function setupAudioContext() {
    if (!audioContext) {
        audioContext = new (window.AudioContext || window.webkitAudioContext)();
        analyser = audioContext.createAnalyser();
        analyser.fftSize = 256;
        analyser.smoothingTimeConstant = 0.6;
        audioDataArray = new Uint8Array(analyser.frequencyBinCount);

        audioSource = audioContext.createMediaElementSource(audioElement);
        audioSource.connect(analyser);
        analyser.connect(audioContext.destination);
    }
    if (audioContext.state === 'suspended') {
        audioContext.resume();
    }
}

function loadModel(path) {
    if (characterModel) scene.remove(characterModel);

    const loader = new THREE.GLTFLoader();
    loader.load(path, (gltf) => {
        characterModel = gltf.scene;

        const box = new THREE.Box3().setFromObject(characterModel);
        characterModel.position.y = -box.min.y;
        characterModel.rotation.y = 0;

        morphMeshes = [];
        characterModel.traverse((child) => {
            if (child.isMesh) {
                child.castShadow = true;
                child.receiveShadow = true;
                if (child.morphTargetInfluences && child.morphTargetInfluences.length > 0) {
                    morphMeshes.push(child);
                }
            }
        });

        // PLAY FULL-BODY ARTICULATED SINGER DANCE ANIMATION
        if (gltf.animations && gltf.animations.length > 0) {
            mixer = new THREE.AnimationMixer(characterModel);
            gltf.animations.forEach((clip) => {
                const action = mixer.clipAction(clip);
                action.play();
            });
        }

        scene.add(characterModel);
    }, undefined, (err) => {
        console.error("Error loading realistic female model:", err);
    });
}

function applyMorphOnModel(openVal, smileVal) {
    morphMeshes.forEach(mesh => {
        if (mesh.morphTargetDictionary) {
            if ('mouthOpen' in mesh.morphTargetDictionary) {
                mesh.morphTargetInfluences[mesh.morphTargetDictionary['mouthOpen']] = openVal;
            }
            if ('mouthSmile' in mesh.morphTargetDictionary) {
                mesh.morphTargetInfluences[mesh.morphTargetDictionary['mouthSmile']] = smileVal;
            }
        }
    });
}

function setupUIEventListeners() {
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

    document.getElementById('toggle-autorotate').addEventListener('change', (e) => {
        controls.autoRotate = e.target.checked;
        controls.autoRotateSpeed = 2.0;
    });

    const btnAudio = document.getElementById('btn-toggle-audio');
    btnAudio.addEventListener('click', () => {
        setupAudioContext();
        if (!isAudioPlaying) {
            audioElement.play().then(() => {
                isAudioPlaying = true;
                btnAudio.textContent = '⏹ Tắt Bài Hát Hát Thật';
                btnAudio.style.background = '#e11d48';
            });
        } else {
            audioElement.pause();
            isAudioPlaying = false;
            currentVocalEnergy = 0;
            applyMorphOnModel(0, 0);
            btnAudio.textContent = '🎶 Phát Bài Hát Có Lời Thật';
            btnAudio.style.background = '';
        }
    });
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

    if (mixer) {
        mixer.update(delta);
    }

    if (isAudioPlaying && analyser) {
        analyser.getByteFrequencyData(audioDataArray);
        let sum = 0;
        for (let i = 4; i < 48; i++) sum += audioDataArray[i];
        const rawEnergy = (sum / 44) / 255.0;
        const targetEnergy = Math.min(1.0, Math.pow(rawEnergy * 1.5, 1.2));
        currentVocalEnergy += (targetEnergy - currentVocalEnergy) * 0.35;

        applyMorphOnModel(currentVocalEnergy * 1.15, 0.25 + currentVocalEnergy * 0.3);
    }

    controls.update();
    renderer.render(scene, camera);
}

window.addEventListener('DOMContentLoaded', init);
