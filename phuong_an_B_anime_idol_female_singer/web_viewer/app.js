// Web 3D Studio for Anime 3D Idol Singer with 4 Animation States & Skeleton View

let scene, camera, renderer, controls, clock;
let characterModel = null, morphMeshes = [], mixer = null;
let skeletonHelper = null;
let particlesSystem;
let isWireframe = false;

let animationsMap = {};
let currentAction = null;
let currentActionName = '01_DungNghiem';

let audioContext = null, analyser = null, audioSource = null;
let audioDataArray = null, audioElement = null;
let isAudioPlaying = false;
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
        renderer.outputEncoding = THREE.sRGBEncoding;
        renderer.toneMapping = THREE.ACESFilmicToneMapping;
        renderer.toneMappingExposure = 1.35;
    } catch(err) {
        console.error("Critical WebGL Init Error:", err);
        container.innerHTML = '<div style="position:absolute;top:40%;left:50%;transform:translate(-50%,-50%);color:#f87171;text-align:center;font-family:sans-serif;background:rgba(15,23,42,0.95);padding:24px;border-radius:12px;border:2px solid #ef4444;box-shadow:0 0 20px rgba(239,68,68,0.3);"><h2>⚠️ Đang Khởi Động Lại Trình Vẽ 3D WebGL...</h2><p style="color:#cbd5e1;margin-top:8px;">Trình duyệt đang giải phóng bộ nhớ GPU. Vui lòng đóng bớt các tab 3D khác nếu đang mở nhiều tab.</p><button onclick="location.reload()" style="margin-top:16px;padding:10px 20px;background:#38bdf8;color:#0f172a;border:none;border-radius:8px;font-weight:bold;cursor:pointer;">🔄 Tải Lại Ngay (Reload)</button></div>';
        return;
    }

    controls = new THREE.OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    controls.maxPolarAngle = Math.PI / 2 + 0.02;
    controls.target.set(0, 1.1, 0);
    controls.update();

    setupLighting();
    setupStage();
    setupAudioElement();
    loadModel('../model/female_singer_anime_idol.glb?v=' + Date.now());
    setupUIEventListeners();

    window.addEventListener('resize', onWindowResize);
    animate();
}

function setupLighting() {
    scene.add(new THREE.AmbientLight(0xffffff, 1.6));

    const frontLight = new THREE.DirectionalLight(0xfff8f0, 2.0);
    frontLight.position.set(0, 3.0, 3.0);
    frontLight.castShadow = true;
    scene.add(frontLight);

    const spotPink = new THREE.SpotLight(0xec4899, 3.2, 14, Math.PI / 4, 0.3);
    spotPink.position.set(-2, 4.0, 2.0);
    spotPink.target.position.set(0, 1.1, 0);
    scene.add(spotPink);
    scene.add(spotPink.target);

    const spotPurple = new THREE.SpotLight(0xa855f7, 3.2, 14, Math.PI / 4, 0.3);
    spotPurple.position.set(2, 4.0, 2.0);
    spotPurple.target.position.set(0, 1.1, 0);
    scene.add(spotPurple);
    scene.add(spotPurple.target);
}

function setupStage() {
    const stageGeo = new THREE.CylinderGeometry(2.0, 2.1, 0.1, 64);
    const stageMat = new THREE.MeshStandardMaterial({
        color: 0x2e1045,
        roughness: 0.2,
        metalness: 0.8
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
    audioElement = new Audio('../../audio/jpop_anime_beat.mp3');
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
    if (characterModel) {
        scene.remove(characterModel);
        if (skeletonHelper) {
            scene.remove(skeletonHelper);
            skeletonHelper = null;
        }
    }

    const loader = new THREE.GLTFLoader();
    loader.load(path, (gltf) => {
        characterModel = gltf.scene;

        // Top surface of the stage cylinder is at y = 0.15m
        characterModel.position.set(0, 0.15, 0);
        characterModel.rotation.y = 0;

        morphMeshes = [];
        characterModel.traverse((child) => {
            if (child.isMesh) {
                child.castShadow = true;
                child.receiveShadow = true;
                if (child.material) child.material.side = THREE.DoubleSide;
                if (child.morphTargetInfluences && child.morphTargetInfluences.length > 0) {
                    morphMeshes.push(child);
                }

                // Identify Hairstyle Meshes
                const nameL = child.name.toLowerCase();
                if (nameL.includes('bob')) {
                    hairMeshes['bob'] = child;
                    child.visible = false;
                } else if (nameL.includes('curled') || nameL.includes('wavy')) {
                    hairMeshes['curled'] = child;
                    child.visible = false;
                } else if (nameL.includes('medium') || nameL.includes('shoulder')) {
                    hairMeshes['medium'] = child;
                    child.visible = false;
                } else if (nameL.includes('hair') && !nameL.includes('hairback')) {
                    hairMeshes['long'] = child;
                    child.visible = true;
                }
            }
        });

        // CREATE 3D SKELETON HELPER TO VISUALIZE ALL 154 BONES & 30 FINGER BONES
        skeletonHelper = new THREE.SkeletonHelper(characterModel);
        skeletonHelper.material.linewidth = 2;
        skeletonHelper.material.color.set(0x38bdf8);
        skeletonHelper.visible = document.getElementById('toggle-skeleton').checked;
        scene.add(skeletonHelper);

        // SETUP ALL 4 ANIMATION CLIPS
        animationsMap = {};
        if (gltf.animations && gltf.animations.length > 0) {
            mixer = new THREE.AnimationMixer(characterModel);
            console.log("Found animation clips:", gltf.animations.map(a => a.name));
            
            gltf.animations.forEach((clip) => {
                const action = mixer.clipAction(clip);
                animationsMap[clip.name] = action;
            });

            // Start with State 1: 01_DungNghiem
            const defaultClip = gltf.animations.find(c => c.name === '01_DungNghiem') || gltf.animations[0];
            if (defaultClip && animationsMap[defaultClip.name]) {
                currentAction = animationsMap[defaultClip.name];
                currentAction.play();
                currentActionName = defaultClip.name;
                updateAnimationHUD(defaultClip.name);
            }
        }

        cacheMorphIndices(characterModel);
        initHairPhysicsColliders(characterModel);
        scene.add(characterModel);
    }, undefined, (err) => {
        console.error("Error loading anime idol model:", err);
    });
}

// ==========================================
// MULTI-HAIRSTYLE SWITCHER ENGINE (4 STYLES)
// ==========================================
let hairMeshes = {
    'long': null,
    'curled': null,
    'medium': null,
    'bob': null
};
let currentHairstyle = 'long';

window.switchHairstyle = function(styleName) {
    currentHairstyle = styleName;
    document.querySelectorAll('.hair-btn').forEach(b => {
        b.classList.remove('active');
        b.style.background = 'transparent';
    });
    const activeBtn = document.getElementById(`btn-hair-${styleName}`);
    if (activeBtn) {
        activeBtn.classList.add('active');
        if (styleName === 'long') activeBtn.style.background = 'rgba(192, 132, 252, 0.2)';
        else if (styleName === 'curled') activeBtn.style.background = 'rgba(245, 158, 11, 0.2)';
        else if (styleName === 'medium') activeBtn.style.background = 'rgba(236, 72, 153, 0.2)';
        else if (styleName === 'bob') activeBtn.style.background = 'rgba(56, 189, 248, 0.2)';
    }

    for (const key in hairMeshes) {
        if (hairMeshes[key]) {
            hairMeshes[key].visible = (key === styleName);
        }
    }

    // Sync hair color picker to the new hairstyle
    const currentHairColor = document.getElementById('picker-hair') ? document.getElementById('picker-hair').value : '#ffffff';
    changeCharacterColor('hair', currentHairColor);
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
    const mouthJoyVal = smileVal * 0.85;
    const mouthUpVal = smileVal * 0.45;
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
const PART_MATERIAL_MAP = {
    hair: ['Hair_00_HAIR', 'HairBack_00_HAIR'],
    skin: ['Body_00_SKIN', 'Face_00_SKIN'],
    eyes: ['EyeIris_00_EYE'],
    tops: ['Tops_01_CLOTH'],
    bottoms: ['Bottoms_01_CLOTH'],
    shoes: ['Shoes_01_CLOTH']
};

function changeCharacterColor(part, hexColor) {
    if (!characterModel) return;
    const targetMatNames = PART_MATERIAL_MAP[part];
    if (!targetMatNames) return;

    characterModel.traverse((child) => {
        if (child.isMesh && child.material) {
            const materials = Array.isArray(child.material) ? child.material : [child.material];
            materials.forEach((mat) => {
                if (targetMatNames.some(name => mat.name.includes(name))) {
                    mat.color.set(hexColor);

                    // Enhanced lighting boost for dark textures (Eyes, Bottoms/Skirt, Tops, Shoes)
                    if (mat.emissive) {
                        if (part === 'eyes') {
                            mat.emissive.set(hexColor);
                            mat.emissiveIntensity = (hexColor.toLowerCase() === '#ffffff') ? 0.0 : 0.75;
                        } else if (part === 'bottoms') {
                            mat.emissive.set(hexColor);
                            mat.emissiveIntensity = (hexColor.toLowerCase() === '#ffffff' || hexColor.toLowerCase() === '#18181b') ? 0.0 : 0.55;
                        } else if (part === 'tops' || part === 'shoes' || part === 'hair') {
                            mat.emissive.set(hexColor);
                            mat.emissiveIntensity = (hexColor.toLowerCase() === '#ffffff') ? 0.0 : 0.25;
                        } else {
                            mat.emissive.set(0x000000);
                            mat.emissiveIntensity = 0.0;
                        }
                    }
                    mat.needsUpdate = true;
                }
            });
        }
    });

    const picker = document.getElementById(`picker-${part}`);
    if (picker) picker.value = hexColor;
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
let hairBonesList = [];
let bodyColliders = [];

function initHairPhysicsColliders(model) {
    hairBonesList = [];
    bodyColliders = [];

    let upperChestBone = null;
    let spineBone = null;
    let shoulderLBone = null;
    let shoulderRBone = null;
    let upperArmLBone = null;
    let upperArmRBone = null;

    model.traverse((node) => {
        if (node.isBone) {
            const name = node.name;
            if (name.includes('UpperChest')) upperChestBone = node;
            else if (name.includes('Spine')) spineBone = node;
            else if (name.includes('Shoulder_L')) shoulderLBone = node;
            else if (name.includes('Shoulder_R')) shoulderRBone = node;
            else if (name.includes('UpperArm_L') || name.includes('L_UpperArm')) upperArmLBone = node;
            else if (name.includes('UpperArm_R') || name.includes('R_UpperArm')) upperArmRBone = node;
            else if (name.toLowerCase().includes('hair') && name.includes('_Sec_')) {
                hairBonesList.push(node);
            }
        }
    });

    if (upperChestBone) {
        // Back of jacket collision sphere (covers shoulder blades & back contour)
        bodyColliders.push({ bone: upperChestBone, offset: new THREE.Vector3(0, -0.010, 0.045), radius: 0.138 });
        // Front chest collision sphere
        bodyColliders.push({ bone: upperChestBone, offset: new THREE.Vector3(0, -0.010, -0.040), radius: 0.135 });
    }
    if (spineBone) {
        bodyColliders.push({ bone: spineBone, offset: new THREE.Vector3(0, 0.010, 0.035), radius: 0.125 });
    }
    if (shoulderLBone) {
        bodyColliders.push({ bone: shoulderLBone, offset: new THREE.Vector3(0.040, 0, 0.015), radius: 0.098 });
    }
    if (shoulderRBone) {
        bodyColliders.push({ bone: shoulderRBone, offset: new THREE.Vector3(-0.040, 0, 0.015), radius: 0.098 });
    }
    if (upperArmRBone) {
        // Raised right arm deltoid collider for pointing gesture
        bodyColliders.push({ bone: upperArmRBone, offset: new THREE.Vector3(0, 0, 0), radius: 0.105 });
    }
    if (upperArmLBone) {
        bodyColliders.push({ bone: upperArmLBone, offset: new THREE.Vector3(0, 0, 0), radius: 0.095 });
    }
}

function resolveHairPhysicsCollisions() {
    if (!characterModel || hairBonesList.length === 0 || bodyColliders.length === 0) return;

    const collidersWorld = bodyColliders.map(c => {
        const center = c.offset.clone().applyMatrix4(c.bone.matrixWorld);
        return { center, radius: c.radius };
    });

    const hairWorldPos = new THREE.Vector3();
    const pushVec = new THREE.Vector3();

    for (let i = 0; i < hairBonesList.length; i++) {
        const bone = hairBonesList[i];
        if (!bone.parent) continue;

        bone.getWorldPosition(hairWorldPos);
        let collided = false;

        for (let j = 0; j < collidersWorld.length; j++) {
            const col = collidersWorld[j];
            const distSq = hairWorldPos.distanceToSquared(col.center);
            const r = col.radius;
            if (distSq < r * r && distSq > 0.00001) {
                const dist = Math.sqrt(distSq);
                const penetration = r - dist;
                pushVec.subVectors(hairWorldPos, col.center).normalize();
                hairWorldPos.addScaledVector(pushVec, penetration + 0.003); // 3mm soft surface contact
                collided = true;
            }
        }

        if (collided) {
            const localPos = bone.parent.worldToLocal(hairWorldPos);
            bone.position.copy(localPos);
        }
    }
}

function updateAnimationHUD(clipName) {
    let hud = document.getElementById('anim-hud');
    if (!hud) {
        hud = document.createElement('div');
        hud.id = 'anim-hud';
        hud.style.cssText = 'position: absolute; bottom: 20px; left: 50%; transform: translateX(-50%); background: rgba(15, 23, 42, 0.85); backdrop-filter: blur(8px); border: 1px solid #ff4b8b; border-radius: 9999px; padding: 8px 24px; color: #fff; font-size: 14px; font-weight: 600; box-shadow: 0 4px 20px rgba(0,0,0,0.5); z-index: 1000; pointer-events: none; text-align: center;';
        document.body.appendChild(hud);
    }
    const displayNameMap = {
        '01_DungNghiem': '🧍 Trạng thái 1: Đứng Nghiêm Trang Trọng',
        '02_DungNghi': '💃 Trạng thái 2: Đứng Nghỉ Chân Trái (Left Rest Idle)',
        '07_DungNghi_DoiXung': '💃 Trạng thái 3: Đứng Nghỉ Chân Phải (Right Rest Idle)',
        '03_TPose': '🤸 Trạng thái 4: Đứng Dạng T-Pose Chuẩn',
        '04_BuocDi_CoBan': '🏃 Trạng thái 5: Bước Đi Cơ Bản',
        '05_BuocDi_TuNhien': '🚶 Trạng thái 6: Bước Đi Điều Hòa Mượt Mà (Harmonic Mocap)',
        '06_TroTay_PhiaTruoc': '👉 Trạng thái 7: Chỉ Tay Phải (Right Hand Point)',
        '08_TroTay_Trai': '👈 Trạng thái 8: Chỉ Tay Trái (Left Hand Point)',
        '09_HaiTay_SongSong': '🙌 Trạng thái 9: 2 Tay Song Song Về Phía Trước (Dual Arms Forward)',
        '10_HaiTay_TruocMat': '🌸 Trạng thái 10: 2 Tay Song Song Trước Mặt (Dual Hands in Front of Face)',
        '11_TraiTim_YeuThuong': '💖 Trạng thái 11: Bắn Tim 2 Tay Dễ Thương (Idol Heart Hands Pose) ✨',
        '12_VayTay_ChaoHoi': '👋 Trạng thái 12: Vẫy Tay Chào Khán Giả Sân Khấu (Stage Wave Greeting) ✨',
        '13_Cuoi_DuyenDang': '😄 Trạng thái 13: Cười Duyên Rạng Rỡ & Khẽ Cười Giggle (Radiant Smile Pose) ✨',
        '14_CuiChao_KetThuc': '🙇‍♀️ Trạng thái 14: Cúi Chào Khán Giả Cảm Ơn Kết Màn (Stage Thank You Bow) ✨'
    };
    hud.innerHTML = `<span style="color: #ff4b8b;">Đang phát:</span> ${displayNameMap[clipName] || clipName}`;
}

window.switchAnimationState = function(stateName) {
    if (!mixer) return;
    document.querySelectorAll('.state-btn').forEach(b => b.classList.remove('active'));

    const btnIdMap = {
        '01_DungNghiem': 'btn-state-1',
        '02_DungNghi': 'btn-state-2',
        '07_DungNghi_DoiXung': 'btn-state-7',
        '03_TPose': 'btn-state-3',
        '04_BuocDi_CoBan': 'btn-state-4',
        '04_BuocDi': 'btn-state-4',
        '05_BuocDi_TuNhien': 'btn-state-5',
        '06_TroTay_PhiaTruoc': 'btn-state-6',
        '08_TroTay_Trai': 'btn-state-8',
        '09_HaiTay_SongSong': 'btn-state-9',
        '10_HaiTay_TruocMat': 'btn-state-10',
        '11_TraiTim_YeuThuong': 'btn-state-11',
        '12_VayTay_ChaoHoi': 'btn-state-12',
        '13_Cuoi_DuyenDang': 'btn-state-13',
        '14_CuiChao_KetThuc': 'btn-state-14'
    };
    if (btnIdMap[stateName]) {
        const btn = document.getElementById(btnIdMap[stateName]);
        if (btn) btn.classList.add('active');
    }

    // Find matching action
    let targetClipName = Object.keys(animationsMap).find(k => k === stateName) ||
                         Object.keys(animationsMap).find(k => k.includes(stateName)) ||
                         Object.keys(animationsMap).find(k => {
                             if (stateName.includes('01')) return k.includes('01') || k.includes('Nghiem');
                             if (stateName.includes('14')) return k.includes('14') || (k.includes('CuiChao') || k.includes('KetThuc'));
                             if (stateName.includes('13')) return k.includes('13') || (k.includes('Cuoi') || k.includes('DuyenDang'));
                             if (stateName.includes('12')) return k.includes('12') || (k.includes('VayTay') || k.includes('ChaoHoi'));
                             if (stateName.includes('11')) return k.includes('11') || (k.includes('TraiTim') || k.includes('YeuThuong'));
                             if (stateName.includes('10')) return k.includes('10') || (k.includes('HaiTay') && k.includes('TruocMat'));
                             if (stateName.includes('09')) return k.includes('09') || (k.includes('HaiTay') && k.includes('SongSong'));
                             if (stateName.includes('08')) return k.includes('08') || (k.includes('TroTay') && k.includes('Trai'));
                             if (stateName.includes('07')) return k.includes('07') || k.includes('DoiXung');
                             if (stateName.includes('06')) return k.includes('06') || k.includes('TroTay') || k.includes('PhiaTruoc');
                             if (stateName.includes('02')) return k.includes('02') || k.includes('Nghi');
                             if (stateName.includes('03')) return k.includes('03') || k.includes('TPose');
                             if (stateName.includes('04')) return k.includes('04') || k.includes('CoBan');
                             if (stateName.includes('05')) return k.includes('05') || k.includes('TuNhien');
                             return false;
                         });

    console.log("Switching to state:", stateName, "-> Resolved Clip:", targetClipName);
    const nextAction = animationsMap[targetClipName];
    if (nextAction && nextAction !== currentAction) {
        if (currentAction) {
            currentAction.fadeOut(0.25);
        }
        nextAction.reset().fadeIn(0.25).play();
        currentAction = nextAction;
        currentActionName = targetClipName;
        updateAnimationHUD(targetClipName);
    }
};

function setCameraView(view) {
    document.querySelectorAll('.btn-cam').forEach(b => b.classList.remove('active'));
    const btn = document.getElementById(`cam-${view}`);
    if (btn) btn.classList.add('active');

    if (view === 'full') {
        controls.target.set(0, 1.1, 0);
        camera.position.set(0, 1.45, 3.0);
    } else if (view === 'face') {
        controls.target.set(0, 1.45, 0);
        camera.position.set(0, 1.50, 0.95);
    } else if (view === 'hand') {
        controls.target.set(-0.35, 1.05, 0.1);
        camera.position.set(-0.35, 1.10, 0.65);
    }
    controls.update();
}

function applyMorph(targetIndex, value) {
    morphMeshes.forEach(mesh => {
        if (mesh.morphTargetInfluences && mesh.morphTargetInfluences.length > targetIndex) {
            mesh.morphTargetInfluences[targetIndex] = value;
        }
    });
}

function resetAllMorphs() {
    morphMeshes.forEach(mesh => {
        if (mesh.morphTargetInfluences) {
            for (let i = 0; i < mesh.morphTargetInfluences.length; i++) {
                mesh.morphTargetInfluences[i] = 0;
            }
        }
    });
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

    const btnAudio = document.getElementById('btn-toggle-audio');
    btnAudio.addEventListener('click', () => {
        setupAudioContext();
        if (!isAudioPlaying) {
            audioElement.play().then(() => {
                isAudioPlaying = true;
                btnAudio.textContent = '⏹ Tắt Nhạc J-Pop';
                btnAudio.style.background = '#e11d48';
            });
        } else {
            audioElement.pause();
            isAudioPlaying = false;
            currentVocalEnergy = 0;
            resetAllMorphs();
            btnAudio.textContent = '🎶 Bật Nhạc J-Pop Beat';
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

    if (mixer) {
        mixer.update(delta);
        resolveHairPhysicsCollisions();
    }

    if (skeletonHelper && skeletonHelper.visible) {
        skeletonHelper.update();
    }

    // SNAPPY BLINK & PLAYFUL WINK
    updateFacialAnimation(delta);

    // Audio Analysis & Reactive Viseme Blending (Mouth only)
    if (isAudioPlaying && analyser && audioDataArray) {
        analyser.getByteFrequencyData(audioDataArray);
        let sum = 0;
        for (let i = 2; i < 30; i++) sum += audioDataArray[i];
        let avg = sum / 28;
        currentVocalEnergy = Math.min(1.0, avg / 120);

        if (document.getElementById('toggle-auto-lipsync').checked) {
            const time = clock.getElapsedTime();
            const visemeList = [morphIndices.mouthA, morphIndices.mouthO, morphIndices.mouthI, morphIndices.mouthE].filter(idx => idx >= 0);
            const activeIdx = visemeList.length > 0 ? visemeList[Math.floor(time * 3.5) % visemeList.length] : -1;
            
            morphMeshes.forEach(mesh => {
                if (mesh.morphTargetInfluences) {
                    visemeList.forEach(vIdx => { mesh.morphTargetInfluences[vIdx] = 0; });
                    if (activeIdx >= 0) mesh.morphTargetInfluences[activeIdx] = currentVocalEnergy * 0.90;
                }
            });
        }
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
