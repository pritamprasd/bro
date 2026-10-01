// =========================================================================
// BRO AUDIO VISUALIZERS ENGINE
// =========================================================================

    let quantumParticles = [];


    const NUM_QUANTUM_PARTICLES = 160;


    let activeVisualizerStyle = localStorage.getItem('bro_audio_visualizer_style') || 'quantum_sphere';


    function initQuantumParticles() {
      quantumParticles = [];
      for (let i = 0; i < NUM_QUANTUM_PARTICLES; i++) {
        const t = i / (NUM_QUANTUM_PARTICLES - 1);
        quantumParticles.push({
          normX: t,
          layer: (i % 5) - 2,
          phaseOffset: (i * 0.16) + (Math.random() * 0.35),
          size: 1.5 + Math.random() * 2.2,
          baseAlpha: 0.65 + Math.random() * 0.35,
          driftY: (Math.random() - 0.5) * 5,
          speed: 0.85 + Math.random() * 0.5
        });
      }
    }


    function setAudioVisualizerStyle(styleName) {
      if (styleName !== 'quantum_sphere' && styleName !== 'arc_reactor' && styleName !== 'equalizer_matrix' && styleName !== 'talking_emoji') {
        styleName = 'quantum_sphere';
      }
      activeVisualizerStyle = styleName;
      localStorage.setItem('bro_audio_visualizer_style', styleName);

      // Update active cards in Settings
      document.querySelectorAll('.anim-style-card').forEach(c => c.classList.remove('active'));
      const activeCard = document.getElementById('anim-card-' + styleName);
      if (activeCard) activeCard.classList.add('active');

      const dotQ = document.getElementById('dot-anim-quantum_sphere');
      const dotR = document.getElementById('dot-anim-arc_reactor');
      const dotE = document.getElementById('dot-anim-equalizer_matrix');
      const dotEmoji = document.getElementById('dot-anim-talking_emoji');
      if (dotQ) dotQ.className = styleName === 'quantum_sphere' ? 'status-dot dot-green' : 'status-dot dot-gray';
      if (dotR) dotR.className = styleName === 'arc_reactor' ? 'status-dot dot-green' : 'status-dot dot-gray';
      if (dotE) dotE.className = styleName === 'equalizer_matrix' ? 'status-dot dot-green' : 'status-dot dot-gray';
      if (dotEmoji) dotEmoji.className = styleName === 'talking_emoji' ? 'status-dot dot-green' : 'status-dot dot-gray';

      const badge = document.getElementById('audiovisualizer-active-badge');
      if (badge) {
        if (styleName === 'quantum_sphere') {
          badge.innerText = 'QUANTUM SPHERE';
          badge.style.color = '#00e5ff';
          badge.style.borderColor = '#00e5ff';
        } else if (styleName === 'arc_reactor') {
          badge.innerText = 'ARC REACTOR';
          badge.style.color = '#3b82f6';
          badge.style.borderColor = '#3b82f6';
        } else if (styleName === 'talking_emoji') {
          badge.innerText = 'TALKING EMOJI';
          badge.style.color = '#fee440';
          badge.style.borderColor = '#fee440';
        } else {
          badge.innerText = 'SPECTRUM MATRIX';
          badge.style.color = '#00ff9d';
          badge.style.borderColor = '#00ff9d';
        }
      }

      // Update Audio Stage DOM Views
      const stageQ = document.getElementById('vis-stage-quantum');
      const stageR = document.getElementById('vis-stage-reactor');
      const stageE = document.getElementById('vis-stage-equalizer');
      const stageEmoji = document.getElementById('vis-stage-emoji');
      if (stageQ) stageQ.style.display = styleName === 'quantum_sphere' ? 'flex' : 'none';
      if (stageR) stageR.style.display = styleName === 'arc_reactor' ? 'flex' : 'none';
      if (stageE) stageE.style.display = styleName === 'equalizer_matrix' ? 'flex' : 'none';
      if (stageEmoji) stageEmoji.style.display = styleName === 'talking_emoji' ? 'flex' : 'none';

      playTacticalSfx('click');
      appendLog('step', `🎨 Audio HUD Visualizer animation set to: ${styleName.toUpperCase()}`);
    }


    function initAudioVisualizerUI() {
      const savedStyle = localStorage.getItem('bro_audio_visualizer_style') || 'quantum_sphere';
      activeVisualizerStyle = savedStyle;

      document.querySelectorAll('.anim-style-card').forEach(c => c.classList.remove('active'));
      const activeCard = document.getElementById('anim-card-' + savedStyle);
      if (activeCard) activeCard.classList.add('active');

      const dotQ = document.getElementById('dot-anim-quantum_sphere');
      const dotR = document.getElementById('dot-anim-arc_reactor');
      const dotE = document.getElementById('dot-anim-equalizer_matrix');
      const dotEmoji = document.getElementById('dot-anim-talking_emoji');
      if (dotQ) dotQ.className = savedStyle === 'quantum_sphere' ? 'status-dot dot-green' : 'status-dot dot-gray';
      if (dotR) dotR.className = savedStyle === 'arc_reactor' ? 'status-dot dot-green' : 'status-dot dot-gray';
      if (dotE) dotE.className = savedStyle === 'equalizer_matrix' ? 'status-dot dot-green' : 'status-dot dot-gray';
      if (dotEmoji) dotEmoji.className = savedStyle === 'talking_emoji' ? 'status-dot dot-green' : 'status-dot dot-gray';

      const badge = document.getElementById('audiovisualizer-active-badge');
      if (badge) {
        if (savedStyle === 'quantum_sphere') {
          badge.innerText = 'QUANTUM SPHERE';
          badge.style.color = '#00e5ff';
          badge.style.borderColor = '#00e5ff';
        } else if (savedStyle === 'arc_reactor') {
          badge.innerText = 'ARC REACTOR';
          badge.style.color = '#3b82f6';
          badge.style.borderColor = '#3b82f6';
        } else if (savedStyle === 'talking_emoji') {
          badge.innerText = 'TALKING EMOJI';
          badge.style.color = '#fee440';
          badge.style.borderColor = '#fee440';
        } else {
          badge.innerText = 'SPECTRUM MATRIX';
          badge.style.color = '#00ff9d';
          badge.style.borderColor = '#00ff9d';
        }
      }

      const stageQ = document.getElementById('vis-stage-quantum');
      const stageR = document.getElementById('vis-stage-reactor');
      const stageE = document.getElementById('vis-stage-equalizer');
      const stageEmoji = document.getElementById('vis-stage-emoji');
      if (stageQ) stageQ.style.display = savedStyle === 'quantum_sphere' ? 'flex' : 'none';
      if (stageR) stageR.style.display = savedStyle === 'arc_reactor' ? 'flex' : 'none';
      if (stageE) stageE.style.display = savedStyle === 'equalizer_matrix' ? 'flex' : 'none';
      if (stageEmoji) stageEmoji.style.display = savedStyle === 'talking_emoji' ? 'flex' : 'none';
    }


    function startAudioVisualizerLoop() {
      if (quantumParticles.length === 0) {
        initQuantumParticles();
      }

      function renderLoop() {
        visualizerTime += 0.035;

        if (activeVisualizerStyle === 'quantum_sphere') {
          renderQuantumSphereFrame();
        } else if (activeVisualizerStyle === 'equalizer_matrix') {
          renderEqualizerMatrixFrame();
        } else if (activeVisualizerStyle === 'talking_emoji') {
          renderTalkingEmojiFrame();
        }

        quantumAnimFrameId = requestAnimationFrame(renderLoop);
      }

      if (!quantumAnimFrameId) {
        quantumAnimFrameId = requestAnimationFrame(renderLoop);
      }
    }


    // =========================================================================
    // THREE.JS 3D MATTE TALKING EMOJI ENGINE (HIGH PERFORMANCE REAL-TIME AVATAR)
    // =========================================================================
    let threeEmojiInitialized = false;
    let threeRenderer = null;
    let threeScene = null;
    let threeCamera = null;
    let threeEmojiMeshGroup = null;
    let threeHeadMesh = null;
    let threeLeftEyeGroup = null;
    let threeRightEyeGroup = null;
    let threeLeftPupil = null;
    let threeRightPupil = null;
    let threeLeftUpperLid = null;
    let threeRightUpperLid = null;
    let threeLeftLowerLid = null;
    let threeRightLowerLid = null;
    let threeLeftEyebrow = null;
    let threeRightEyebrow = null;
    let threeMouthGroup = null;
    let threeMouthCavity = null;
    let threeMouthLip = null;
    let threeTeethMesh = null;
    let threeTongueMesh = null;
    let threeLeftCheek = null;
    let threeRightCheek = null;
    let threeLedLights = [];
    let threeParticlesGroup = null;
    let targetLookX = 0;
    let targetLookY = 0;
    let currentLookX = 0;
    let currentLookY = 0;

    function initThreeTalkingEmoji() {
      const canvas = document.getElementById('talking-emoji-canvas');
      if (!canvas || !window.THREE) return false;

      const w = 250;
      const h = 250;
      canvas.width = w;
      canvas.height = h;

      // 1. Scene & Camera
      threeScene = new THREE.Scene();
      threeCamera = new THREE.PerspectiveCamera(36, w / h, 0.1, 100);
      threeCamera.position.set(0, 0, 8.5);

      // 2. WebGL Renderer with Matte Filmic Tone Mapping
      try {
        threeRenderer = new THREE.WebGLRenderer({
          canvas: canvas,
          alpha: true,
          antialias: true,
          powerPreference: 'high-performance'
        });
        threeRenderer.setSize(w, h, false);
        threeRenderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
        if (THREE.ACESFilmicToneMapping) {
          threeRenderer.toneMapping = THREE.ACESFilmicToneMapping;
          threeRenderer.toneMappingExposure = 1.18;
        }
      } catch (e) {
        console.warn('WebGL initialization failed:', e);
        return false;
      }

      // 3. Matte Studio Lighting Hierarchy
      const ambient = new THREE.AmbientLight(0xffffff, 0.82);
      threeScene.add(ambient);

      const keyLight = new THREE.DirectionalLight(0xfff7ed, 1.4);
      keyLight.position.set(4, 5, 5.5);
      threeScene.add(keyLight);

      const fillLight = new THREE.DirectionalLight(0x7dd3fc, 0.7);
      fillLight.position.set(-4, -2, 4);
      threeScene.add(fillLight);

      const rimLight = new THREE.DirectionalLight(0xf472b6, 0.85);
      rimLight.position.set(0, -4, -4);
      threeScene.add(rimLight);

      const topLight = new THREE.PointLight(0xffffff, 0.9, 14);
      topLight.position.set(0, 4, 3.5);
      threeScene.add(topLight);

      // 4. Matte Material Palette (Soft Clay / Matte Rubber)
      const headMat = new THREE.MeshStandardMaterial({
        color: 0xffb703, // Vibrant matte golden-yellow emoji
        roughness: 0.58,
        metalness: 0.04
      });

      const eyeWhiteMat = new THREE.MeshStandardMaterial({
        color: 0xf8f9fa,
        roughness: 0.35,
        metalness: 0.0
      });

      const pupilMat = new THREE.MeshStandardMaterial({
        color: 0x0f172a,
        roughness: 0.3,
        metalness: 0.0
      });

      const eyelidMat = new THREE.MeshStandardMaterial({
        color: 0xffb703,
        roughness: 0.58,
        metalness: 0.04
      });

      const eyebrowMat = new THREE.MeshStandardMaterial({
        color: 0x4a2810,
        roughness: 0.75,
        metalness: 0.0
      });

      const cheekMat = new THREE.MeshStandardMaterial({
        color: 0xf43f5e,
        roughness: 0.9,
        metalness: 0.0,
        transparent: true,
        opacity: 0.72
      });

      const mouthCavityMat = new THREE.MeshStandardMaterial({
        color: 0x2b0938,
        roughness: 0.65,
        metalness: 0.04
      });

      const lipMat = new THREE.MeshStandardMaterial({
        color: 0xe11d48,
        roughness: 0.5,
        metalness: 0.05
      });

      const teethMat = new THREE.MeshStandardMaterial({
        color: 0xffffff,
        roughness: 0.25,
        metalness: 0.0
      });

      const tongueMat = new THREE.MeshStandardMaterial({
        color: 0xf43f5e,
        roughness: 0.55,
        metalness: 0.0
      });

      const headphoneMat = new THREE.MeshStandardMaterial({
        color: 0x181e29,
        roughness: 0.52,
        metalness: 0.4
      });

      const ledMat = new THREE.MeshBasicMaterial({
        color: 0x00f0ff
      });

      // 5. Construct 3D Hierarchical Model
      threeEmojiMeshGroup = new THREE.Group();
      threeScene.add(threeEmojiMeshGroup);

      // Head Sphere (Radius 2.0)
      threeHeadMesh = new THREE.Mesh(new THREE.SphereGeometry(2.0, 48, 48), headMat);
      threeEmojiMeshGroup.add(threeHeadMesh);

      // Matte Cheek Blush Disks
      const cheekGeo = new THREE.CircleGeometry(0.36, 24);
      threeLeftCheek = new THREE.Mesh(cheekGeo, cheekMat);
      threeLeftCheek.position.set(-1.08, -0.25, 1.66);
      threeLeftCheek.rotation.y = -0.42;
      threeEmojiMeshGroup.add(threeLeftCheek);

      threeRightCheek = new THREE.Mesh(cheekGeo, cheekMat);
      threeRightCheek.position.set(1.08, -0.25, 1.66);
      threeRightCheek.rotation.y = 0.42;
      threeEmojiMeshGroup.add(threeRightCheek);

      // Eyes (Left & Right)
      function create3DEye(side) {
        const eyeGroup = new THREE.Group();
        eyeGroup.position.set(side * 0.65, 0.4, 1.78);

        const sclera = new THREE.Mesh(new THREE.SphereGeometry(0.35, 32, 32), eyeWhiteMat);
        eyeGroup.add(sclera);

        const pupil = new THREE.Mesh(new THREE.SphereGeometry(0.18, 24, 24), pupilMat);
        pupil.position.set(0, 0, 0.21);
        eyeGroup.add(pupil);

        const glint = new THREE.Mesh(new THREE.SphereGeometry(0.06, 12, 12), teethMat);
        glint.position.set(-0.06, 0.07, 0.33);
        eyeGroup.add(glint);

        const upperLidGeo = new THREE.SphereGeometry(0.365, 24, 16, 0, Math.PI * 2, 0, Math.PI * 0.5);
        const upperLid = new THREE.Mesh(upperLidGeo, eyelidMat);
        upperLid.rotation.x = -Math.PI * 0.55;
        eyeGroup.add(upperLid);

        const lowerLidGeo = new THREE.SphereGeometry(0.365, 24, 16, 0, Math.PI * 2, Math.PI * 0.5, Math.PI * 0.5);
        const lowerLid = new THREE.Mesh(lowerLidGeo, eyelidMat);
        lowerLid.rotation.x = Math.PI * 0.55;
        eyeGroup.add(lowerLid);

        const browGeo = new THREE.TorusGeometry(0.35, 0.06, 12, 24, Math.PI * 0.65);
        const brow = new THREE.Mesh(browGeo, eyebrowMat);
        brow.position.set(0, 0.48, 0.05);
        brow.rotation.z = side < 0 ? -0.15 : Math.PI - 0.15;
        brow.rotation.x = 0.22;
        eyeGroup.add(brow);

        return { eyeGroup, pupil, upperLid, lowerLid, brow };
      }

      const leftEyeData = create3DEye(-1);
      threeLeftEyeGroup = leftEyeData.eyeGroup;
      threeLeftPupil = leftEyeData.pupil;
      threeLeftUpperLid = leftEyeData.upperLid;
      threeLeftLowerLid = leftEyeData.lowerLid;
      threeLeftEyebrow = leftEyeData.brow;
      threeEmojiMeshGroup.add(threeLeftEyeGroup);

      const rightEyeData = create3DEye(1);
      threeRightEyeGroup = rightEyeData.eyeGroup;
      threeRightPupil = rightEyeData.pupil;
      threeRightUpperLid = rightEyeData.upperLid;
      threeRightLowerLid = rightEyeData.lowerLid;
      threeRightEyebrow = rightEyeData.brow;
      threeEmojiMeshGroup.add(threeRightEyeGroup);

      // 3D Mouth Group
      threeMouthGroup = new THREE.Group();
      threeMouthGroup.position.set(0, -0.65, 1.82);

      const mouthGeo = new THREE.CylinderGeometry(0.48, 0.48, 0.25, 32);
      mouthGeo.rotateX(Math.PI * 0.5);
      threeMouthCavity = new THREE.Mesh(mouthGeo, mouthCavityMat);
      threeMouthGroup.add(threeMouthCavity);

      const lipGeo = new THREE.TorusGeometry(0.48, 0.065, 16, 36);
      threeMouthLip = new THREE.Mesh(lipGeo, lipMat);
      threeMouthLip.position.set(0, 0, 0.13);
      threeMouthGroup.add(threeMouthLip);

      threeTeethMesh = new THREE.Mesh(new THREE.BoxGeometry(0.62, 0.14, 0.1), teethMat);
      threeTeethMesh.position.set(0, 0.2, 0.1);
      threeMouthGroup.add(threeTeethMesh);

      threeTongueMesh = new THREE.Mesh(new THREE.SphereGeometry(0.28, 20, 16), tongueMat);
      threeTongueMesh.position.set(0, -0.2, 0.1);
      threeMouthGroup.add(threeTongueMesh);

      threeEmojiMeshGroup.add(threeMouthGroup);

      // Clean 3D Arched Headband (over the top of the head)
      const hpGroup = new THREE.Group();
      const headCurve = new THREE.CatmullRomCurve3([
        new THREE.Vector3(-2.08, 0, 0),
        new THREE.Vector3(-1.85, 1.45, 0),
        new THREE.Vector3(0, 2.22, 0),
        new THREE.Vector3(1.85, 1.45, 0),
        new THREE.Vector3(2.08, 0, 0)
      ]);
      const bandGeo = new THREE.TubeGeometry(headCurve, 32, 0.1, 12, false);
      const bandMesh = new THREE.Mesh(bandGeo, headphoneMat);
      hpGroup.add(bandMesh);

      threeLedLights = [];
      [-1, 1].forEach(side => {
        const cupGroup = new THREE.Group();
        cupGroup.position.set(side * 2.08, 0, 0);

        const cupGeo = new THREE.CylinderGeometry(0.52, 0.52, 0.38, 32);
        cupGeo.rotateZ(Math.PI * 0.5);
        const cupMesh = new THREE.Mesh(cupGeo, headphoneMat);
        cupGroup.add(cupMesh);

        const ledRingGeo = new THREE.TorusGeometry(0.44, 0.045, 12, 32);
        ledRingGeo.rotateY(Math.PI * 0.5);
        const ledMesh = new THREE.Mesh(ledRingGeo, ledMat.clone());
        ledMesh.position.set(side * 0.2, 0, 0);
        cupGroup.add(ledMesh);
        threeLedLights.push(ledMesh);

        hpGroup.add(cupGroup);
      });
      threeEmojiMeshGroup.add(hpGroup);

      // Floating Ambient Halo Particles
      const partGeo = new THREE.BufferGeometry();
      const partCount = 45;
      const posArray = new Float32Array(partCount * 3);
      for (let i = 0; i < partCount * 3; i += 3) {
        const radius = 2.4 + Math.random() * 1.6;
        const theta = Math.random() * Math.PI * 2;
        const phi = Math.acos(2 * Math.random() - 1);
        posArray[i] = radius * Math.sin(phi) * Math.cos(theta);
        posArray[i + 1] = radius * Math.sin(phi) * Math.sin(theta);
        posArray[i + 2] = radius * Math.cos(phi);
      }
      partGeo.setAttribute('position', new THREE.BufferAttribute(posArray, 3));
      const partMat = new THREE.PointsMaterial({
        size: 0.065,
        color: 0x00f0ff,
        transparent: true,
        opacity: 0.65
      });
      threeParticlesGroup = new THREE.Points(partGeo, partMat);
      threeScene.add(threeParticlesGroup);

      // Mouse Tracking
      window.addEventListener('mousemove', (e) => {
        const rect = canvas.getBoundingClientRect();
        if (rect.width > 0 && rect.height > 0) {
          const mouseX = (e.clientX - (rect.left + rect.width / 2)) / (window.innerWidth / 2);
          const mouseY = (e.clientY - (rect.top + rect.height / 2)) / (window.innerHeight / 2);
          targetLookX = Math.max(-0.6, Math.min(0.6, mouseX));
          targetLookY = Math.max(-0.4, Math.min(0.4, mouseY));
        }
      });

      threeEmojiInitialized = true;
      return true;
    }


    function renderTalkingEmojiFrame() {
      if (!threeEmojiInitialized) {
        const ok = initThreeTalkingEmoji();
        if (!ok) return;
      }

      // Smooth mouse & intent look tracking
      currentLookX += (targetLookX - currentLookX) * 0.08;
      currentLookY += (targetLookY - currentLookY) * 0.08;

      // Gentle 3D floating & breathing
      const time = visualizerTime;
      const floatY = Math.sin(time * 2.4) * 0.12;
      const breathScale = 1.0 + Math.sin(time * 2.0) * 0.015;

      threeEmojiMeshGroup.position.y = floatY;
      threeEmojiMeshGroup.scale.set(breathScale, breathScale, breathScale);

      // Periodic Natural Blinking (every ~3.5s)
      const blinkCycle = (time * 0.7) % (Math.PI * 2);
      const isBlink = (currentVoiceVisualizerState !== 'listening') && (Math.sin(blinkCycle) > 0.94);
      const targetUpperLidAngle = isBlink ? 0.05 : -Math.PI * 0.55;
      const targetLowerLidAngle = isBlink ? -0.05 : Math.PI * 0.55;

      if (threeLeftUpperLid && threeRightUpperLid) {
        threeLeftUpperLid.rotation.x += (targetUpperLidAngle - threeLeftUpperLid.rotation.x) * 0.35;
        threeRightUpperLid.rotation.x += (targetUpperLidAngle - threeRightUpperLid.rotation.x) * 0.35;
        threeLeftLowerLid.rotation.x += (targetLowerLidAngle - threeLeftLowerLid.rotation.x) * 0.35;
        threeRightLowerLid.rotation.x += (targetLowerLidAngle - threeRightLowerLid.rotation.x) * 0.35;
      }

      // State-Driven 3D Expressions & Dynamics
      let ledColorHex = 0x00f0ff; // Default cyan

      if (currentVoiceVisualizerState === 'speaking') {
        ledColorHex = 0xfee440; // Vibrant amber

        // Dynamic 3D Lip-Sync Mouth Modulation
        const voiceMod = Math.abs(Math.sin(time * 15.0)) * 0.55 + Math.abs(Math.cos(time * 9.2)) * 0.45;
        const mouthOpenY = 0.25 + voiceMod * 0.95 + (currentVisualizerAudioLevel * 1.4);
        const mouthWidthX = 0.95 + Math.sin(time * 6.0) * 0.25 + (currentVisualizerAudioLevel * 0.4);

        threeMouthGroup.scale.set(mouthWidthX, mouthOpenY, 1.0);
        threeMouthGroup.position.y = -0.68 - (mouthOpenY * 0.12);
        threeTongueMesh.position.y = -0.22 + Math.sin(time * 12.0) * 0.08;

        // Rhythmic speaking nod & slight head tilt
        const nodX = Math.sin(time * 7.5) * 0.08;
        const tiltZ = Math.sin(time * 3.8) * 0.05;
        threeEmojiMeshGroup.rotation.set(nodX + currentLookY * 0.25, currentLookX * 0.4, tiltZ);

        threeLeftEyebrow.position.y = 0.58;
        threeRightEyebrow.position.y = 0.58;

        threeLeftPupil.position.set(currentLookX * 0.08, -currentLookY * 0.08, 0.23);
        threeRightPupil.position.set(currentLookX * 0.08, -currentLookY * 0.08, 0.23);

      } else if (currentVoiceVisualizerState === 'listening') {
        ledColorHex = 0x00ff9d; // Attentive Emerald

        const listenPulse = 0.45 + Math.sin(time * 4.5) * 0.12;
        threeMouthGroup.scale.set(0.65, listenPulse, 0.8);
        threeMouthGroup.position.y = -0.68;

        // Curious head tilt towards user
        const listenTiltZ = 0.14 + Math.sin(time * 2.0) * 0.04;
        threeEmojiMeshGroup.rotation.set(currentLookY * 0.3 - 0.05, currentLookX * 0.45, listenTiltZ);

        threeLeftEyebrow.position.y = 0.62;
        threeRightEyebrow.position.y = 0.62;

        threeLeftPupil.position.set(currentLookX * 0.12, -currentLookY * 0.12, 0.24);
        threeRightPupil.position.set(currentLookX * 0.12, -currentLookY * 0.12, 0.24);

      } else if (currentVoiceVisualizerState === 'processing') {
        ledColorHex = 0xc026d3; // Thinking Magenta

        threeMouthGroup.scale.set(0.5, 0.18 + Math.sin(time * 8.0) * 0.08, 0.8);
        threeMouthGroup.position.y = -0.68;

        const thinkLookX = Math.sin(time * 3.0) * 0.15;
        const thinkLookY = 0.18;
        threeEmojiMeshGroup.rotation.set(0.12, thinkLookX, -0.08);

        threeLeftEyebrow.rotation.z = -0.35;
        threeRightEyebrow.rotation.z = Math.PI + 0.1;

        threeLeftPupil.position.set(thinkLookX, thinkLookY, 0.23);
        threeRightPupil.position.set(thinkLookX, thinkLookY, 0.23);

      } else {
        ledColorHex = 0x00f0ff; // Cyan

        threeMouthGroup.scale.set(1.0, 0.38 + Math.sin(time * 2.0) * 0.04, 0.85);
        threeMouthGroup.position.y = -0.68;

        threeEmojiMeshGroup.rotation.set(currentLookY * 0.2, currentLookX * 0.3, Math.sin(time * 1.5) * 0.03);

        threeLeftEyebrow.position.y = 0.52;
        threeRightEyebrow.position.y = 0.52;
        threeLeftEyebrow.rotation.z = -0.15;
        threeRightEyebrow.rotation.z = Math.PI - 0.15;

        threeLeftPupil.position.set(currentLookX * 0.08, -currentLookY * 0.08, 0.23);
        threeRightPupil.position.set(currentLookX * 0.08, -currentLookY * 0.08, 0.23);
      }

      threeLedLights.forEach(led => {
        if (led.material) {
          led.material.color.setHex(ledColorHex);
        }
      });

      if (threeParticlesGroup) {
        threeParticlesGroup.rotation.y = time * 0.15;
      }

      threeRenderer.render(threeScene, threeCamera);
    }


    function renderQuantumSphereFrame() {
      const canvas = document.getElementById('quantum-sphere-canvas');
      if (!canvas) return;
      const ctx = canvas.getContext('2d');
      if (!ctx) return;

      const w = canvas.width;
      const h = canvas.height;
      const cx = w / 2;
      const cy = h / 2;
      const r = (w / 2) - 18;

      ctx.clearRect(0, 0, w, h);

      // 1. Atmosphere Glow Corona
      let pulse = 0.8 + 0.2 * Math.sin(visualizerTime * 2.0);
      let coronaAlpha = 0.35;
      if (currentVoiceVisualizerState === 'listening') {
        pulse = 1.0 + 0.3 * Math.sin(visualizerTime * 4.5);
        coronaAlpha = 0.55;
      } else if (currentVoiceVisualizerState === 'processing') {
        pulse = 1.0 + 0.35 * Math.sin(visualizerTime * 6.0);
        coronaAlpha = 0.6;
      } else if (currentVoiceVisualizerState === 'speaking') {
        pulse = 1.1 + 0.4 * Math.sin(visualizerTime * 5.0);
        coronaAlpha = 0.65;
      }

      const aura = ctx.createRadialGradient(cx, cy, r * 0.8, cx, cy, r * 1.28);
      aura.addColorStop(0, `rgba(0, 229, 255, ${coronaAlpha * pulse})`);
      aura.addColorStop(0.65, `rgba(0, 140, 255, ${coronaAlpha * 0.45 * pulse})`);
      aura.addColorStop(1, 'rgba(0, 229, 255, 0)');
      ctx.fillStyle = aura;
      ctx.beginPath();
      ctx.arc(cx, cy, r * 1.28, 0, Math.PI * 2);
      ctx.fill();

      // 2. Save clip to sphere bounds for interior body and particle ribbon
      ctx.save();
      ctx.beginPath();
      ctx.arc(cx, cy, r, 0, Math.PI * 2);
      ctx.clip();

      // Translucent deep-space inner gradient
      const sphereBg = ctx.createRadialGradient(cx, cy * 0.95, 10, cx, cy, r);
      sphereBg.addColorStop(0, 'rgba(7, 14, 34, 0.94)');
      sphereBg.addColorStop(0.5, 'rgba(10, 24, 52, 0.88)');
      sphereBg.addColorStop(0.85, 'rgba(0, 110, 190, 0.55)');
      sphereBg.addColorStop(0.98, 'rgba(0, 229, 255, 0.85)');
      sphereBg.addColorStop(1, 'rgba(0, 229, 255, 1)');
      ctx.fillStyle = sphereBg;
      ctx.fillRect(0, 0, w, h);

      // Background Ambient Floating Stardust
      for (let s = 0; s < 16; s++) {
        const sx = cx + Math.sin(visualizerTime * 0.4 + s * 1.35) * (r * 0.72);
        const sy = cy + Math.cos(visualizerTime * 0.35 + s * 1.75) * (r * 0.62);
        ctx.fillStyle = `rgba(255, 255, 255, ${0.25 + 0.35 * Math.sin(visualizerTime + s)})`;
        ctx.beginPath();
        ctx.arc(sx, sy, 1.2, 0, Math.PI * 2);
        ctx.fill();
      }

      // 3. Sinuous Multi-Harmonic Particle Wave Ribbon
      const ampBase = (currentVoiceVisualizerState === 'idle') ? 14 : 32;
      const ampAudio = currentVisualizerAudioLevel * 50;
      const totalAmp = ampBase + ampAudio;
      const waveWidth = r * 1.88;
      const startX = cx - waveWidth / 2;

      const particlePoints = [];
      for (let i = 0; i < quantumParticles.length; i++) {
        const p = quantumParticles[i];
        const px = startX + p.normX * waveWidth;
        
        const freq1 = 0.024;
        const freq2 = 0.048;
        const freq3 = 0.012;
        const layerOffset = p.layer * 7.5;
        
        const w1 = Math.sin((px - startX) * freq1 + visualizerTime * 2.2 * p.speed + p.phaseOffset);
        const w2 = Math.cos((px - startX) * freq2 - visualizerTime * 1.8);
        const w3 = Math.sin((px - startX) * freq3 + visualizerTime * 3.0);
        
        const envelope = Math.sin(p.normX * Math.PI);
        const py = cy + (w1 * totalAmp + w2 * (totalAmp * 0.45) + w3 * (totalAmp * 0.25) + layerOffset + p.driftY) * envelope;
        
        particlePoints.push({ x: px, y: py, normX: p.normX, layer: p.layer, size: p.size, alpha: p.baseAlpha });
      }

      // Draw ribbon connector lines
      ctx.lineWidth = 0.9;
      for (let i = 0; i < particlePoints.length - 1; i++) {
        const p1 = particlePoints[i];
        const p2 = particlePoints[i + 1];
        if (Math.abs(p1.layer - p2.layer) <= 1 && Math.abs(p1.x - p2.x) < 22) {
          const gradLine = ctx.createLinearGradient(p1.x, p1.y, p2.x, p2.y);
          const col1 = getParticleColor(p1.normX);
          const col2 = getParticleColor(p2.normX);
          gradLine.addColorStop(0, col1.replace('rgb', 'rgba').replace(')', ', 0.35)'));
          gradLine.addColorStop(1, col2.replace('rgb', 'rgba').replace(')', ', 0.35)'));
          ctx.strokeStyle = gradLine;
          ctx.beginPath();
          ctx.moveTo(p1.x, p1.y);
          ctx.lineTo(p2.x, p2.y);
          ctx.stroke();
        }
      }

      // Draw Particle Dots with Cyan -> Magenta -> Violet Gradient
      for (let i = 0; i < particlePoints.length; i++) {
        const pt = particlePoints[i];
        const colorStr = getParticleColor(pt.normX);
        
        ctx.fillStyle = colorStr;
        ctx.shadowColor = colorStr;
        ctx.shadowBlur = 6;
        ctx.beginPath();
        ctx.arc(pt.x, pt.y, pt.size * (0.8 + 0.35 * Math.sin(visualizerTime * 3.0 + i)), 0, Math.PI * 2);
        ctx.fill();
      }
      ctx.shadowBlur = 0;

      ctx.restore(); // end sphere clip

      // 4. Sharp glowing rim border of Sphere
      ctx.lineWidth = 2.5;
      const rimGrad = ctx.createLinearGradient(0, cy - r, 0, cy + r);
      rimGrad.addColorStop(0, 'rgba(0, 240, 255, 0.95)');
      rimGrad.addColorStop(0.5, 'rgba(0, 180, 255, 0.8)');
      rimGrad.addColorStop(1, 'rgba(0, 240, 255, 0.95)');
      ctx.strokeStyle = rimGrad;
      ctx.beginPath();
      ctx.arc(cx, cy, r, 0, Math.PI * 2);
      ctx.stroke();

      // Specular highlight arc at top rim
      ctx.lineWidth = 1.8;
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.65)';
      ctx.beginPath();
      ctx.arc(cx, cy, r - 1.5, -Math.PI * 0.75, -Math.PI * 0.25);
      ctx.stroke();
    }


    function getParticleColor(normX) {
      if (normX < 0.33) {
        const f = normX / 0.33;
        const r = Math.round(0 + f * 224);
        const g = Math.round(229 - f * 165);
        const b = Math.round(255 - f * 4);
        return `rgb(${r}, ${g}, ${b})`;
      } else if (normX < 0.66) {
        const f = (normX - 0.33) / 0.33;
        const r = Math.round(224 - f * 67);
        const g = Math.round(64 + f * 14);
        const b = Math.round(251 - f * 30);
        return `rgb(${r}, ${g}, ${b})`;
      } else {
        const f = (normX - 0.66) / 0.34;
        const r = Math.round(157 - f * 157);
        const g = Math.round(78 + f * 151);
        const b = Math.round(221 + f * 34);
        return `rgb(${r}, ${g}, ${b})`;
      }
    }


    function renderEqualizerMatrixFrame() {
      const canvas = document.getElementById('equalizer-matrix-canvas');
      if (!canvas) return;
      const ctx = canvas.getContext('2d');
      if (!ctx) return;

      const w = canvas.width;
      const h = canvas.height;
      ctx.clearRect(0, 0, w, h);

      const numBars = 32;
      const barWidth = (w - (numBars * 4)) / numBars;

      for (let i = 0; i < numBars; i++) {
        const norm = i / numBars;
        const freq = Math.sin(visualizerTime * 3.5 + i * 0.35) * 0.5 + 0.5;
        const audioBoost = currentVisualizerAudioLevel * 0.8;
        const barHeight = Math.max(8, (h - 24) * (freq * 0.6 + audioBoost * 0.7 + (Math.sin(norm * Math.PI) * 0.3)));
        const x = i * (barWidth + 4) + 4;
        const y = h - barHeight - 8;

        const grad = ctx.createLinearGradient(0, y, 0, h);
        if (currentVoiceVisualizerState === 'speaking') {
          grad.addColorStop(0, '#fee440');
          grad.addColorStop(0.5, '#ff0054');
          grad.addColorStop(1, 'rgba(255, 0, 84, 0.2)');
        } else if (currentVoiceVisualizerState === 'listening') {
          grad.addColorStop(0, '#00ff9d');
          grad.addColorStop(0.5, '#00e5ff');
          grad.addColorStop(1, 'rgba(0, 229, 255, 0.2)');
        } else {
          grad.addColorStop(0, '#00e5ff');
          grad.addColorStop(0.5, '#3b82f6');
          grad.addColorStop(1, 'rgba(59, 130, 246, 0.2)');
        }

        ctx.fillStyle = grad;
        ctx.fillRect(x, y, barWidth, barHeight);

        // Peak Cap
        ctx.fillStyle = '#ffffff';
        ctx.fillRect(x, y - 3, barWidth, 2);
      }
    }


    function toggleAudioFullscreen() {
      const hud = document.getElementById('audio-only-hud');
      if (!hud) return;

      const isFs = hud.classList.contains('hud-fullscreen') || (document.fullscreenElement === hud);
      if (isFs) {
        exitAudioFullscreen();
      } else {
        enterAudioFullscreen();
      }
    }


    function enterAudioFullscreen() {
      const hud = document.getElementById('audio-only-hud');
      if (!hud) return;

      hud.classList.add('hud-fullscreen');
      const btn = document.getElementById('btn-audio-fullscreen');
      if (btn) {
        btn.className = 'btn btn-danger btn-sm';
        btn.innerHTML = '<i data-lucide="minimize-2" class="hud-icon-xs"></i> <span id="txt-audio-fullscreen">Exit Fullscreen</span>';
      }

      // Try requesting standard browser fullscreen if allowed
      try {
        if (hud.requestFullscreen) {
          hud.requestFullscreen().catch(() => { });
        } else if (hud.webkitRequestFullscreen) {
          hud.webkitRequestFullscreen();
        } else if (document.documentElement.requestFullscreen) {
          document.documentElement.requestFullscreen().catch(() => { });
        }
      } catch (e) { }

      renderIcons();
    }


    function exitAudioFullscreen() {
      const hud = document.getElementById('audio-only-hud');
      if (!hud) return;

      hud.classList.remove('hud-fullscreen');
      const btn = document.getElementById('btn-audio-fullscreen');
      if (btn) {
        btn.className = 'btn btn-cyan btn-sm';
        btn.innerHTML = '<i data-lucide="maximize-2" class="hud-icon-xs"></i> <span id="txt-audio-fullscreen">Fullscreen HUD</span>';
      }

      try {
        if (document.fullscreenElement) {
          if (document.exitFullscreen) {
            document.exitFullscreen().catch(() => { });
          } else if (document.webkitExitFullscreen) {
            document.webkitExitFullscreen();
          }
        }
      } catch (e) { }

      renderIcons();
    }
