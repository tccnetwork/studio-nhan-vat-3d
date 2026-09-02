// Pro Concert Stage Studio (Three.js Web 3D) - Full-Body Articulated Choreography

let scene, camera, renderer, controls, clock;
let modelRealistic = null, morphMeshesRealistic = [], mixerRealistic, actionRealistic;
let modelAnime = null, morphMeshesAnime = [], mixerAnime, actionAnime;

let stageSpotlights = [];
let particlesSystem;
let isZoomClose = false;
let currentMode = 'duo';

let audioContext = null, analyser = null, audioSource = null;
let audioDataArray = null, audioElement = null;
let isAudioPlaying = false;
let currentVocalEnergy = 0;

const container = document.getElementById('stage-viewport');

function init() {
    scene = new THREE.Scene();
    scene.background = new THREE.Color(0x05070f);
    scene.fog = new THREE.FogExp2(0x05070f, 0.03);
    clock = new THREE.Clock();

    camera = new THREE.PerspectiveCamera(45, container.clientWidth / container.clientHeight, 0.1, 100);
    camera.position.set(0, 1.45, 3.2);

    renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
    renderer.setSize(container.clientWidth, container.clientHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    renderer.outputEncoding = THREE.sRGBEncoding;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.35;
    container.appendChild(renderer.domElement);

    controls = new THREE.OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    controls.maxPolarAngle = Math.PI / 2 + 0.02;
    controls.target.set(0, 1.1, 0); // Focus on whole body & performance
    controls.update();

    setupConcertStage();
    setupLighting();
    setupAudioEngine();
    loadCharacters();
    setupUI();

    window.addEventListener('resize', onResize);
    animate();
}

function setupConcertStage() {
    const stageGeo = new THREE.CylinderGeometry(4.2, 4.5, 0.15, 64);
    const stageMat = new THREE.MeshStandardMaterial({
        color: 0x0f172a,
        roughness: 0.15,
        metalness: 0.85
    });
    const stageMesh = new THREE.Mesh(stageGeo, stageMat);
    stageMesh.position.y = 0.075;
    stageMesh.receiveShadow = true;
    scene.add(stageMesh);

    const ringGeo = new THREE.TorusGeometry(4.2, 0.03, 16, 64);
    const ringMat = new THREE.MeshBasicMaterial({ color: 0x38bdf8 });
    const ringMesh = new THREE.Mesh(ringGeo, ringMat);
    ringMesh.rotation.x = Math.PI / 2;
    ringMesh.position.y = 0.15;
    scene.add(ringMesh);

    const grid = new THREE.GridHelper(20, 40, 0xec4899, 0x1e293b);
    grid.position.y = 0;
    scene.add(grid);

    const particleCount = 350;
    const geometry = new THREE.BufferGeometry();
    const positions = new Float32Array(particleCount * 3);
    const colors = new Float32Array(particleCount * 3);

    for (let i = 0; i < particleCount; i++) {
        positions[i * 3] = (Math.random() - 0.5) * 10;
        positions[i * 3 + 1] = Math.random() * 5.0;
        positions[i * 3 + 2] = (Math.random() - 0.5) * 10;

        if (Math.random() > 0.5) {
            colors[i * 3] = 0.2; colors[i * 3 + 1] = 0.7; colors[i * 3 + 2] = 1.0;
        } else {
            colors[i * 3] = 1.0; colors[i * 3 + 1] = 0.3; colors[i * 3 + 2] = 0.8;
        }
    }

    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));

    const material = new THREE.PointsMaterial({
        size: 0.04,
        vertexColors: true,
        transparent: true,
        opacity: 0.85,
        blending: THREE.AdditiveBlending
    });

    particlesSystem = new THREE.Points(geometry, material);
    scene.add(particlesSystem);
}

function setupLighting() {
    scene.add(new THREE.AmbientLight(0xffffff, 1.5));

    const colors = [0x38bdf8, 0xec4899, 0xa855f7, 0xfbbf24];
    stageSpotlights = [];

    for (let i = 0; i < 4; i++) {
        const spot = new THREE.SpotLight(colors[i], 3.5, 16, Math.PI / 5, 0.4);
        spot.position.set((i - 1.5) * 2.5, 5.5, 2.5);
        spot.castShadow = true;
        scene.add(spot);
        scene.add(spot.target);
        stageSpotlights.push(spot);
    }
}

function setupAudioEngine() {
    audioElement = document.getElementById('audio-engine');
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

let skeletonHelperRealistic = null, skeletonHelperAnime = null;
let showSkeleton = false;

function loadCharacters() {
    const loader = new THREE.GLTFLoader();

    // 1. Load Realistic Singer (Full-Body Articulated Animation)
    loader.load('../model/female_singer_pro_stage.glb?v=' + Date.now(), (gltf) => {
        modelRealistic = gltf.scene;
        // Top surface of the concert stage cylinder is at y = 0.15
        modelRealistic.position.set(-0.75, 0.15, 0);
        modelRealistic.rotation.y = 0;

        morphMeshesRealistic = [];
        modelRealistic.traverse(c => {
            if (c.isMesh) {
                c.castShadow = true;
                c.receiveShadow = true;
                if (c.morphTargetInfluences && c.morphTargetInfluences.length > 0) {
                    morphMeshesRealistic.push(c);
                }
            }
        });

        skeletonHelperRealistic = new THREE.SkeletonHelper(modelRealistic);
        skeletonHelperRealistic.material.color.set(0xec4899);
        skeletonHelperRealistic.visible = showSkeleton;
        scene.add(skeletonHelperRealistic);

        if (gltf.animations && gltf.animations.length > 0) {
            mixerRealistic = new THREE.AnimationMixer(modelRealistic);
            gltf.animations.forEach(clip => mixerRealistic.clipAction(clip).play());
        }

        scene.add(modelRealistic);
    });

    // 2. Load Anime Idol Singer (Full-Body Articulated Animation)
    loader.load('../model/female_singer_anime_pro.glb?v=' + Date.now(), (gltf) => {
        modelAnime = gltf.scene;
        // Top surface of the concert stage cylinder is at y = 0.15
        modelAnime.position.set(0.75, 0.15, 0);
        modelAnime.rotation.y = 0;

        morphMeshesAnime = [];
        modelAnime.traverse(c => {
            if (c.isMesh) {
                c.castShadow = true;
                c.receiveShadow = true;
                if (c.material) c.material.side = THREE.DoubleSide;
                if (c.morphTargetInfluences && c.morphTargetInfluences.length > 0) {
                    morphMeshesAnime.push(c);
                }
            }
        });

        skeletonHelperAnime = new THREE.SkeletonHelper(modelAnime);
        skeletonHelperAnime.material.color.set(0x38bdf8);
        skeletonHelperAnime.visible = showSkeleton;
        scene.add(skeletonHelperAnime);

        if (gltf.animations && gltf.animations.length > 0) {
            mixerAnime = new THREE.AnimationMixer(modelAnime);
            gltf.animations.forEach(clip => mixerAnime.clipAction(clip).play());
        }

        scene.add(modelAnime);
    });
}

window.playMusic = function(url, label) {
    setupAudioContext();
    audioElement.src = url;
    audioElement.play().then(() => {
        isAudioPlaying = true;
        document.querySelectorAll('.music-btn').forEach(b => b.classList.remove('active'));
        if (url.includes('pop')) document.getElementById('btn-play-song1').classList.add('active');
        else document.getElementById('btn-play-song2').classList.add('active');
    });
};

window.stopMusic = function() {
    audioElement.pause();
    isAudioPlaying = false;
    currentVocalEnergy = 0;
    applyMorphA(0, 0);
    resetMorphB();
    document.querySelectorAll('.music-btn').forEach(b => b.classList.remove('active'));
};

window.switchChoreography = function(mode) {
    document.querySelectorAll('.choreo-btn').forEach(b => b.classList.remove('active'));
    
    if (mode === 'vocal') {
        document.getElementById('btn-choreo-1').classList.add('active');
        document.getElementById('current-choreo-label').textContent = "01_Live_Vocal_FullBody";
        if (mixerRealistic) mixerRealistic.timeScale = 1.0;
        if (mixerAnime) mixerAnime.timeScale = 1.0;
    } else if (mode === 'dance') {
        document.getElementById('btn-choreo-2').classList.add('active');
        document.getElementById('current-choreo-label').textContent = "02_Idol_Dance_130_BPM";
        if (mixerRealistic) mixerRealistic.timeScale = 1.3;
        if (mixerAnime) mixerAnime.timeScale = 1.35;
    } else {
        document.getElementById('btn-choreo-3').classList.add('active');
        document.getElementById('current-choreo-label').textContent = "03_High_Note_Climax";
        if (mixerRealistic) mixerRealistic.timeScale = 0.85;
        if (mixerAnime) mixerAnime.timeScale = 0.9;
    }
};

window.switchStageMode = function(mode) {
    currentMode = mode;
    document.querySelectorAll('.mode-btn').forEach(b => b.classList.remove('active'));

    if (mode === 'duo') {
        document.getElementById('mode-duo').classList.add('active');
        if (modelRealistic) { modelRealistic.visible = true; modelRealistic.position.x = -0.75; }
        if (modelAnime) { modelAnime.visible = true; modelAnime.position.x = 0.75; }
        controls.target.set(0, 1.1, 0);
    } else if (mode === 'realistic') {
        document.getElementById('mode-realistic').classList.add('active');
        if (modelRealistic) { modelRealistic.visible = true; modelRealistic.position.x = 0; }
        if (modelAnime) { modelAnime.visible = false; }
        controls.target.set(0, 1.1, 0);
    } else {
        document.getElementById('mode-anime').classList.add('active');
        if (modelRealistic) { modelRealistic.visible = false; }
        if (modelAnime) { modelAnime.visible = true; modelAnime.position.x = 0; }
        controls.target.set(0, 1.1, 0);
    }
};

function applyMorphA(openVal, smileVal) {
    morphMeshesRealistic.forEach(mesh => {
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

function applyMorphB(targetIdx, val) {
    morphMeshesAnime.forEach(mesh => {
        if (mesh.morphTargetInfluences && mesh.morphTargetInfluences.length > targetIdx) {
            mesh.morphTargetInfluences[targetIdx] = val;
        }
    });
}

function resetMorphB() {
    morphMeshesAnime.forEach(mesh => {
        if (mesh.morphTargetInfluences) {
            for (let i = 0; i < mesh.morphTargetInfluences.length; i++) mesh.morphTargetInfluences[i] = 0;
        }
    });
}

let camViewIndex = 0;

function setupUI() {
    const btnSkeleton = document.getElementById('btn-toggle-skeleton');
    if (btnSkeleton) {
        btnSkeleton.addEventListener('click', () => {
            showSkeleton = !showSkeleton;
            if (skeletonHelperRealistic) skeletonHelperRealistic.visible = showSkeleton;
            if (skeletonHelperAnime) skeletonHelperAnime.visible = showSkeleton;
            btnSkeleton.style.background = showSkeleton ? '#0284c7' : '';
            btnSkeleton.style.color = showSkeleton ? '#fff' : '#38bdf8';
            btnSkeleton.textContent = showSkeleton ? '🦴 Tắt Khung Xương' : '🦴 Hiện Khung Xương (Skeleton)';
        });
    }

    const btnCam = document.getElementById('btn-toggle-camera');
    btnCam.addEventListener('click', () => {
        camViewIndex = (camViewIndex + 1) % 3;
        if (camViewIndex === 0) {
            // Toàn thân sân khấu
            camera.position.set(0, 1.45, 3.2);
            controls.target.set(0, 1.1, 0);
            btnCam.textContent = '📷 Góc Máy: Toàn Sân Khấu';
        } else if (camViewIndex === 1) {
            // Cận cảnh khuôn mặt
            camera.position.set(0, 1.55, 1.3);
            controls.target.set(0, 1.45, 0);
            btnCam.textContent = '📷 Góc Máy: Cận Cảnh Mặt';
        } else {
            // Cận cảnh bàn tay & ngón tay
            camera.position.set(0.45, 1.15, 0.7);
            controls.target.set(0.45, 1.1, 0.1);
            btnCam.textContent = '🖐️ Góc Máy: Cận Cảnh Ngón Tay';
        }
        controls.update();
    });
}

function onResize() {
    camera.aspect = container.clientWidth / container.clientHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(container.clientWidth, container.clientHeight);
}

function animate() {
    requestAnimationFrame(animate);
    const delta = clock.getDelta();
    const elapsed = clock.getElapsedTime();

    if (mixerRealistic) mixerRealistic.update(delta);
    if (mixerAnime) mixerAnime.update(delta);

    if (skeletonHelperRealistic && skeletonHelperRealistic.visible) skeletonHelperRealistic.update();
    if (skeletonHelperAnime && skeletonHelperAnime.visible) skeletonHelperAnime.update();

    // Dynamic Moving Spotlights
    stageSpotlights.forEach((spot, i) => {
        const angle = elapsed * 1.5 + i * (Math.PI / 2);
        spot.target.position.set(Math.sin(angle) * 1.8, 1.2, Math.cos(angle) * 0.8);
    });

    if (particlesSystem) {
        const pos = particlesSystem.geometry.attributes.position.array;
        for (let i = 1; i < pos.length; i += 3) {
            pos[i] += delta * 0.4;
            if (pos[i] > 5.0) pos[i] = 0;
        }
        particlesSystem.geometry.attributes.position.needsUpdate = true;
    }

    // AUDIO DRIVEN LIP-SYNC
    if (isAudioPlaying && analyser) {
        analyser.getByteFrequencyData(audioDataArray);
        let sum = 0;
        for (let i = 4; i < 48; i++) sum += audioDataArray[i];
        const rawEnergy = (sum / 44) / 255.0;
        const targetEnergy = Math.min(1.0, Math.pow(rawEnergy * 1.5, 1.2));
        currentVocalEnergy += (targetEnergy - currentVocalEnergy) * 0.35;

        const pct = Math.round(currentVocalEnergy * 100);
        document.getElementById('vocal-meter').style.width = `${pct}%`;
        document.getElementById('vocal-pct').textContent = `${pct}%`;

        applyMorphA(currentVocalEnergy * 1.2, 0.3 + currentVocalEnergy * 0.3);

        resetMorphB();
        const vowelCycle = (elapsed * 2.8) % 5;
        if (vowelCycle < 1) applyMorphB(36, currentVocalEnergy * 1.2);
        else if (vowelCycle < 2) applyMorphB(37, currentVocalEnergy * 0.95);
        else if (vowelCycle < 3) applyMorphB(38, currentVocalEnergy * 0.9);
        else if (vowelCycle < 4) applyMorphB(39, currentVocalEnergy * 0.95);
        else applyMorphB(40, currentVocalEnergy * 1.1);

        applyMorphB(3, 0.3 + currentVocalEnergy * 0.4);
        const isWink = (elapsed % 4.0 > 1.8 && elapsed % 4.0 < 2.1);
        if (isWink) applyMorphB(13, 1.0);

        const vowelLabels = ['[Âm A]', '[Âm I]', '[Âm U]', '[Âm E]', '[Âm O]'];
        document.getElementById('current-viseme-label').textContent = isWink ? '😉 Nháy Mắt' : `${vowelLabels[Math.floor(vowelCycle)]} (${pct}%)`;
    }

    controls.update();
    renderer.render(scene, camera);
}

window.addEventListener('DOMContentLoaded', init);
