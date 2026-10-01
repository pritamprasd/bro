import re
from pathlib import Path

def extract_js():
    web_dir = Path("/home/pritam/code/ai/jarvis/src/bro/ui/web")
    content = (web_dir / "index.html").read_text(encoding="utf-8")
    lines = content.splitlines()

    # Find the main script tag
    script_start = -1
    for i in range(len(lines)-1, -1, -1):
        if '<script>' in lines[i] and i > 5000:
            script_start = i + 1
            break
    
    script_end = -1
    for i in range(len(lines)-1, -1, -1):
        if '</script>' in lines[i]:
            script_end = i
            break

    js_lines = lines[script_start:script_end]
    js_text = "\n".join(js_lines)

    print(f"Script lines: {script_start} to {script_end} (total {len(js_lines)} lines)")

    # 1. themes.js
    themes_js = """// ==========================================================================
// BRO TACTICAL HUD // THEME MANAGEMENT (DEFAULT, NEOMORPHISM, GLASSMORPHISM)
// ==========================================================================

function setSystemTheme(themeName) {
  if (themeName !== 'default' && themeName !== 'neumorphism' && themeName !== 'glassmorphism') {
    themeName = 'default';
  }
  document.documentElement.setAttribute('data-theme', themeName);
  localStorage.setItem('bro_system_theme', themeName);

  document.querySelectorAll('.theme-card').forEach(c => c.classList.remove('active'));
  const activeCard = document.getElementById('theme-card-' + themeName);
  if (activeCard) activeCard.classList.add('active');

  const dotDef = document.getElementById('dot-theme-default');
  const dotNeu = document.getElementById('dot-theme-neumorphism');
  const dotGlass = document.getElementById('dot-theme-glassmorphism');
  if (dotDef && dotNeu) {
    dotDef.className = (themeName === 'default') ? 'status-dot dot-green' : 'status-dot dot-gray';
    dotNeu.className = (themeName === 'neumorphism') ? 'status-dot dot-green' : 'status-dot dot-gray';
    if (dotGlass) dotGlass.className = (themeName === 'glassmorphism') ? 'status-dot dot-green' : 'status-dot dot-gray';
  }

  const badge = document.getElementById('theme-active-badge');
  if (badge) {
    if (themeName === 'glassmorphism') {
      badge.innerText = 'AURORA GLASSMORPHISM';
      badge.style.color = '#00e5ff';
      badge.style.borderColor = '#00e5ff';
    } else if (themeName === 'neumorphism') {
      badge.innerText = 'NEOMORPHISM ACTIVE';
      badge.style.color = '#00d2ff';
      badge.style.borderColor = '#00d2ff';
    } else {
      badge.innerText = 'DEFAULT CYBER';
      badge.style.color = '#a855f7';
      badge.style.borderColor = '#a855f7';
    }
  }

  playTacticalSfx('click');
  appendLog('step', `🎨 System UX Theme switched to: ${themeName.toUpperCase()}`);
}

function initThemeUI() {
  const currentTheme = localStorage.getItem('bro_system_theme') || 'default';
  document.documentElement.setAttribute('data-theme', currentTheme);

  document.querySelectorAll('.theme-card').forEach(c => c.classList.remove('active'));
  const activeCard = document.getElementById('theme-card-' + currentTheme);
  if (activeCard) activeCard.classList.add('active');

  const dotDef = document.getElementById('dot-theme-default');
  const dotNeu = document.getElementById('dot-theme-neumorphism');
  const dotGlass = document.getElementById('dot-theme-glassmorphism');
  if (dotDef && dotNeu) {
    dotDef.className = (currentTheme === 'default') ? 'status-dot dot-green' : 'status-dot dot-gray';
    dotNeu.className = (currentTheme === 'neumorphism') ? 'status-dot dot-green' : 'status-dot dot-gray';
    if (dotGlass) dotGlass.className = (currentTheme === 'glassmorphism') ? 'status-dot dot-green' : 'status-dot dot-gray';
  }

  const badge = document.getElementById('theme-active-badge');
  if (badge) {
    if (currentTheme === 'glassmorphism') {
      badge.innerText = 'AURORA GLASSMORPHISM';
      badge.style.color = '#00e5ff';
      badge.style.borderColor = '#00e5ff';
    } else if (currentTheme === 'neumorphism') {
      badge.innerText = 'NEOMORPHISM ACTIVE';
      badge.style.color = '#00d2ff';
      badge.style.borderColor = '#00d2ff';
    } else {
      badge.innerText = 'DEFAULT CYBER';
      badge.style.color = '#a855f7';
      badge.style.borderColor = '#a855f7';
    }
  }
}
"""
    (web_dir / "js" / "themes.js").write_text(themes_js.strip(), encoding="utf-8")

    # 2. visualizer.js
    vis_js = """// ==========================================================================
// BRO TACTICAL HUD // AUDIO HUD VISUALIZERS (QUANTUM SPHERE, ARC REACTOR, SPECTRUM)
// ==========================================================================

let quantumAnimFrameId = null;
let quantumParticles = [];
const NUM_QUANTUM_PARTICLES = 160;
let activeVisualizerStyle = localStorage.getItem('bro_audio_visualizer_style') || 'quantum_sphere';
let currentVoiceVisualizerState = 'idle';
let currentVisualizerAudioLevel = 0.0;
let visualizerTime = 0;

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
  if (styleName !== 'quantum_sphere' && styleName !== 'arc_reactor' && styleName !== 'equalizer_matrix') {
    styleName = 'quantum_sphere';
  }
  activeVisualizerStyle = styleName;
  localStorage.setItem('bro_audio_visualizer_style', styleName);

  document.querySelectorAll('.anim-style-card').forEach(c => c.classList.remove('active'));
  const activeCard = document.getElementById('anim-card-' + styleName);
  if (activeCard) activeCard.classList.add('active');

  const dotQ = document.getElementById('dot-anim-quantum_sphere');
  const dotR = document.getElementById('dot-anim-arc_reactor');
  const dotE = document.getElementById('dot-anim-equalizer_matrix');
  if (dotQ) dotQ.className = styleName === 'quantum_sphere' ? 'status-dot dot-green' : 'status-dot dot-gray';
  if (dotR) dotR.className = styleName === 'arc_reactor' ? 'status-dot dot-green' : 'status-dot dot-gray';
  if (dotE) dotE.className = styleName === 'equalizer_matrix' ? 'status-dot dot-green' : 'status-dot dot-gray';

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
    } else {
      badge.innerText = 'SPECTRUM MATRIX';
      badge.style.color = '#00ff9d';
      badge.style.borderColor = '#00ff9d';
    }
  }

  const stageQ = document.getElementById('vis-stage-quantum');
  const stageR = document.getElementById('vis-stage-reactor');
  const stageE = document.getElementById('vis-stage-equalizer');
  if (stageQ) stageQ.style.display = styleName === 'quantum_sphere' ? 'flex' : 'none';
  if (stageR) stageR.style.display = styleName === 'arc_reactor' ? 'flex' : 'none';
  if (stageE) stageE.style.display = styleName === 'equalizer_matrix' ? 'flex' : 'none';

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
  if (dotQ) dotQ.className = savedStyle === 'quantum_sphere' ? 'status-dot dot-green' : 'status-dot dot-gray';
  if (dotR) dotR.className = savedStyle === 'arc_reactor' ? 'status-dot dot-green' : 'status-dot dot-gray';
  if (dotE) dotE.className = savedStyle === 'equalizer_matrix' ? 'status-dot dot-green' : 'status-dot dot-gray';

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
    } else {
      badge.innerText = 'SPECTRUM MATRIX';
      badge.style.color = '#00ff9d';
      badge.style.borderColor = '#00ff9d';
    }
  }

  const stageQ = document.getElementById('vis-stage-quantum');
  const stageR = document.getElementById('vis-stage-reactor');
  const stageE = document.getElementById('vis-stage-equalizer');
  if (stageQ) stageQ.style.display = savedStyle === 'quantum_sphere' ? 'flex' : 'none';
  if (stageR) stageR.style.display = savedStyle === 'arc_reactor' ? 'flex' : 'none';
  if (stageE) stageE.style.display = savedStyle === 'equalizer_matrix' ? 'flex' : 'none';
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
    }

    quantumAnimFrameId = requestAnimationFrame(renderLoop);
  }

  if (!quantumAnimFrameId) {
    quantumAnimFrameId = requestAnimationFrame(renderLoop);
  }
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

  ctx.save();
  ctx.beginPath();
  ctx.arc(cx, cy, r, 0, Math.PI * 2);
  ctx.clip();

  const sphereBg = ctx.createRadialGradient(cx, cy * 0.95, 10, cx, cy, r);
  sphereBg.addColorStop(0, 'rgba(7, 14, 34, 0.94)');
  sphereBg.addColorStop(0.5, 'rgba(10, 24, 52, 0.88)');
  sphereBg.addColorStop(0.85, 'rgba(0, 110, 190, 0.55)');
  sphereBg.addColorStop(0.98, 'rgba(0, 229, 255, 0.85)');
  sphereBg.addColorStop(1, 'rgba(0, 229, 255, 1)');
  ctx.fillStyle = sphereBg;
  ctx.fillRect(0, 0, w, h);

  for (let s = 0; s < 16; s++) {
    const sx = cx + Math.sin(visualizerTime * 0.4 + s * 1.35) * (r * 0.72);
    const sy = cy + Math.cos(visualizerTime * 0.35 + s * 1.75) * (r * 0.62);
    ctx.fillStyle = `rgba(255, 255, 255, ${0.25 + 0.35 * Math.sin(visualizerTime + s)})`;
    ctx.beginPath();
    ctx.arc(sx, sy, 1.2, 0, Math.PI * 2);
    ctx.fill();
  }

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

  ctx.restore();

  ctx.lineWidth = 2.5;
  const rimGrad = ctx.createLinearGradient(0, cy - r, 0, cy + r);
  rimGrad.addColorStop(0, 'rgba(0, 240, 255, 0.95)');
  rimGrad.addColorStop(0.5, 'rgba(0, 180, 255, 0.8)');
  rimGrad.addColorStop(1, 'rgba(0, 240, 255, 0.95)');
  ctx.strokeStyle = rimGrad;
  ctx.beginPath();
  ctx.arc(cx, cy, r, 0, Math.PI * 2);
  ctx.stroke();

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
      document.exitFullscreen().catch(() => { });
    } else if (document.webkitFullscreenElement) {
      document.webkitExitFullscreen();
    }
  } catch (e) { }

  renderIcons();
}
"""
    (web_dir / "js" / "visualizer.js").write_text(vis_js.strip(), encoding="utf-8")
    print("themes.js and visualizer.js created!")

if __name__ == "__main__":
    extract_js()
