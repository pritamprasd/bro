// =========================================================================
// BRO CORE ENGINE: DOM, TAB LAZY LOADER, SFX, TERMINAL, WS TELEMETRY & INIT
// =========================================================================

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

// Global Lucide Icon Renderer
function renderIcons() {
  if (window.lucide && typeof window.lucide.createIcons === 'function') {
    window.lucide.createIcons();
  }
}

// Tab file mapping
const TAB_FILE_MAP = {
  'calendar': 'calendar.html',
  'displays': 'displays.html',
  'settings': 'settings.html',
  'history': 'history.html',
  'errors': 'alerts.html',
  'alerts': 'alerts.html',
  'memory': 'memory.html',
  'guide': 'guide.html',
  'resources': 'resources.html'
};

const loadedTabs = new Set(['command']);
let modalsLoaded = false;

async function loadModals() {
  if (modalsLoaded) return;
  try {
    let res = await fetch('tabs/modals.html').catch(() => null);
    if (!res || !res.ok) {
      res = await fetch('/static/tabs/modals.html').catch(() => null);
    }
    if (res && res.ok) {
      const html = await res.text();
      const container = document.getElementById('modals-container');
      if (container) {
        container.innerHTML = html;
        modalsLoaded = true;
        renderIcons();
      }
    }
  } catch (e) {
    console.warn('Failed to load modals partial:', e);
  }
}

async function loadTabContent(tabName) {
  if (loadedTabs.has(tabName)) return true;
  const fileName = TAB_FILE_MAP[tabName] || (tabName + '.html');
  try {
    let res = await fetch('tabs/' + fileName).catch(() => null);
    if (!res || !res.ok) {
      res = await fetch('/static/tabs/' + fileName).catch(() => null);
    }
    if (res && res.ok) {
      const html = await res.text();
      const container = document.getElementById('tabs-container');
      if (container) {
        container.insertAdjacentHTML('beforeend', html);
        loadedTabs.add(tabName);
        renderIcons();
        return true;
      }
    }
  } catch (err) {
    console.error('Failed to load tab ' + tabName + ':', err);
  }
  return false;
}

// Non-blocking idle prefetcher
function prefetchTabs() {
  const tabsToPrefetch = ['calendar', 'displays', 'settings', 'history', 'errors', 'memory', 'resources', 'guide'];
  loadModals();
  let idx = 0;
  function prefetchNext() {
    if (idx >= tabsToPrefetch.length) return;
    const tab = tabsToPrefetch[idx++];
    if (!loadedTabs.has(tab)) {
      loadTabContent(tab).then(() => {
        setTimeout(prefetchNext, 80);
      });
    } else {
      prefetchNext();
    }
  }
  if (window.requestIdleCallback) {
    window.requestIdleCallback(() => prefetchNext(), { timeout: 1500 });
  } else {
    setTimeout(prefetchNext, 500);
  }
}

// On-demand dynamic tab switcher
async function switchTab(name, targetBtn = null) {
  let requestedSettingsSection = null;
  if (name === 'models') {
    name = 'settings';
    requestedSettingsSection = 'brain';
  } else if (name === 'telemetry') {
    name = 'settings';
    requestedSettingsSection = 'watchdogs';
  }

  // Load tab HTML on-demand if not yet in DOM
  if (!loadedTabs.has(name) && name !== 'command') {
    await loadTabContent(name);
  }

  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));

  const tabBtn = targetBtn || (window.event && window.event.target ? window.event.target.closest('.tab-btn') : null) || document.getElementById('tab-btn-' + name);
  if (tabBtn) tabBtn.classList.add('active');

  const target = document.getElementById('tab-' + name);
  if (target) target.classList.add('active');

  if (name === 'displays' && typeof loadDesktopMonitors === 'function') loadDesktopMonitors();
  if (name === 'calendar' && typeof loadCalendar === 'function') loadCalendar();
  if (name === 'history' && typeof loadHistory === 'function') loadHistory();
  if (name === 'settings') {
    if (requestedSettingsSection && typeof showSettingsSection === 'function') {
      showSettingsSection(requestedSettingsSection);
    } else if (typeof showSettingsSection === 'function' && !document.querySelector('.settings-section.active')) {
      showSettingsSection('brain');
    }
    if (typeof loadModels === 'function') loadModels();
    if (typeof loadVoices === 'function') loadVoices();
    if (typeof loadDesktopMonitors === 'function') loadDesktopMonitors();
    if (typeof loadMemoryConfig === 'function') loadMemoryConfig();
    if (typeof loadGatewayProviders === 'function') loadGatewayProviders();
    if (typeof loadDailyBriefConfig === 'function') loadDailyBriefConfig();
    if (typeof loadBriefSlots === 'function') loadBriefSlots();
  }
  if ((name === 'errors' || name === 'alerts') && typeof loadErrors === 'function') loadErrors();
  if (name === 'resources' && typeof loadDesignDocument === 'function') loadDesignDocument();
  if (name === 'memory' && typeof loadMemory === 'function') {
    loadMemory();
  }
  setTimeout(renderIcons, 60);
}


    function setGoal(text) {
      document.getElementById('goal-input').value = text;
    }


    let audioCtx = null;


    let sfxEnabled = true;


    function getAudioContext() {
      if (!audioCtx) {
        const AudioContextClass = window.AudioContext || window.webkitAudioContext;
        if (AudioContextClass) {
          audioCtx = new AudioContextClass();
        }
      }
      if (audioCtx && audioCtx.state === 'suspended') {
        audioCtx.resume();
      }
      return audioCtx;
    }


    function toggleTacticalSfx(enabled) {
      sfxEnabled = !!enabled;
      const toggle = document.getElementById('settings-sfx-toggle');
      if (toggle && toggle.checked !== sfxEnabled) toggle.checked = sfxEnabled;
    }


    function playTacticalSfx(type) {
      if (!sfxEnabled) return;
      try {
        const ctx = getAudioContext();
        if (!ctx) return;
        const now = ctx.currentTime;

        if (type === 'mic_start') {
          const osc1 = ctx.createOscillator();
          const gain1 = ctx.createGain();
          osc1.type = 'sine';
          osc1.frequency.setValueAtTime(587.33, now);
          osc1.frequency.exponentialRampToValueAtTime(880, now + 0.12);
          gain1.gain.setValueAtTime(0.08, now);
          gain1.gain.exponentialRampToValueAtTime(0.001, now + 0.14);
          osc1.connect(gain1);
          gain1.connect(ctx.destination);
          osc1.start(now);
          osc1.stop(now + 0.15);
        } else if (type === 'mic_stop') {
          const osc = ctx.createOscillator();
          const gain = ctx.createGain();
          osc.type = 'sine';
          osc.frequency.setValueAtTime(784, now);
          osc.frequency.exponentialRampToValueAtTime(440, now + 0.12);
          gain.gain.setValueAtTime(0.07, now);
          gain.gain.exponentialRampToValueAtTime(0.001, now + 0.14);
          osc.connect(gain);
          gain.connect(ctx.destination);
          osc.start(now);
          osc.stop(now + 0.15);
        } else if (type === 'barge_in') {
          const osc = ctx.createOscillator();
          const gain = ctx.createGain();
          osc.type = 'triangle';
          osc.frequency.setValueAtTime(180, now);
          osc.frequency.exponentialRampToValueAtTime(40, now + 0.15);
          gain.gain.setValueAtTime(0.16, now);
          gain.gain.exponentialRampToValueAtTime(0.001, now + 0.16);
          osc.connect(gain);
          gain.connect(ctx.destination);
          osc.start(now);
          osc.stop(now + 0.17);
        } else if (type === 'success') {
          [523.25, 659.25, 783.99].forEach((freq, idx) => {
            const osc = ctx.createOscillator();
            const gain = ctx.createGain();
            osc.type = 'sine';
            osc.frequency.setValueAtTime(freq, now + idx * 0.05);
            gain.gain.setValueAtTime(0.06, now + idx * 0.05);
            gain.gain.exponentialRampToValueAtTime(0.001, now + idx * 0.05 + 0.08);
            osc.connect(gain);
            gain.connect(ctx.destination);
            osc.start(now + idx * 0.05);
            osc.stop(now + idx * 0.05 + 0.09);
          });
        } else if (type === 'warning') {
          const osc = ctx.createOscillator();
          const gain = ctx.createGain();
          osc.type = 'sawtooth';
          osc.frequency.setValueAtTime(320, now);
          osc.frequency.setValueAtTime(440, now + 0.08);
          gain.gain.setValueAtTime(0.08, now);
          gain.gain.exponentialRampToValueAtTime(0.001, now + 0.18);
          osc.connect(gain);
          gain.connect(ctx.destination);
          osc.start(now);
          osc.stop(now + 0.2);
        }
      } catch (e) {
        console.warn('Audio SFX error:', e);
      }
    }


    let quantumAnimFrameId = null;


    let currentVoiceVisualizerState = 'idle';


    let currentVisualizerAudioLevel = 0.0;


    let visualizerTime = 0;


    function appendLog(type, text) {
      const term = document.getElementById('terminal-logs');
      const div = document.createElement('div');
      div.className = 'log-line log-' + type;

      if (typeof text === 'string' && text.includes('```')) {
        const parts = text.split(/(```[\s\S]*?```)/g);
        parts.forEach(part => {
          if (part.startsWith('```') && part.endsWith('```')) {
            const lines = part.slice(3, -3).trim().split('\n');
            const lang = lines[0].match(/^[a-zA-Z0-9_-]+$/) ? lines.shift() : '';
            const code = lines.join('\n');

            const codeWrap = document.createElement('div');
            codeWrap.className = 'terminal-code-block';
            codeWrap.style.cssText = 'position: relative; background: rgba(2, 6, 18, 0.85); border: 1px solid rgba(0, 240, 255, 0.25); border-radius: 8px; padding: 0.85rem; margin: 0.5rem 0; font-family: "JetBrains Mono", monospace; box-shadow: inset 0 2px 6px rgba(0,0,0,0.5);';

            const copyBtn = document.createElement('button');
            copyBtn.className = 'btn btn-sm btn-cyan';
            copyBtn.style.cssText = 'position: absolute; top: 8px; right: 8px; font-size: 0.68rem; padding: 0.2rem 0.55rem; z-index: 10; opacity: 0.9;';
            copyBtn.innerHTML = '<i data-lucide="copy" class="hud-icon-xs"></i> <span>COPY</span>';
            copyBtn.onclick = () => {
              navigator.clipboard.writeText(code).then(() => {
                copyBtn.innerHTML = '<i data-lucide="check" class="hud-icon-xs"></i> <span>COPIED!</span>';
                copyBtn.className = 'btn btn-sm btn-success';
                playTacticalSfx('success');
                setTimeout(() => {
                  copyBtn.innerHTML = '<i data-lucide="copy" class="hud-icon-xs"></i> <span>COPY</span>';
                  copyBtn.className = 'btn btn-sm btn-cyan';
                  renderIcons();
                }, 2000);
              });
            };

            const pre = document.createElement('pre');
            pre.style.cssText = 'margin: 0; padding-top: 1.5rem; overflow-x: auto; white-space: pre-wrap; word-break: break-all; color: #a6e3a1; font-size: 0.8rem; line-height: 1.45;';
            pre.innerText = code;

            codeWrap.appendChild(copyBtn);
            codeWrap.appendChild(pre);
            div.appendChild(codeWrap);
          } else if (part.trim()) {
            const span = document.createElement('span');
            span.innerText = part;
            div.appendChild(span);
          }
        });
      } else {
        div.innerText = text;
      }

      term.appendChild(div);
      term.scrollTop = term.scrollHeight;
      renderIcons();
    }


    let attachedFilePaths = [];


    async function handleFileUpload(event) {
      const file = event.target.files[0];
      if (!file) return;
      const formData = new FormData();
      formData.append('file', file);
      try {
        const res = await fetch('/api/upload', { method: 'POST', body: formData });
        const data = await res.json();
        attachedFilePaths.push(data.path);
        renderAttachmentChips();
      } catch (e) {
        alert('File upload failed: ' + e);
      }
    }


    function renderAttachmentChips() {
      const container = document.getElementById('attachment-chips-container');
      container.innerHTML = '';
      attachedFilePaths.forEach((p, idx) => {
        const name = p.split('/').pop();
        const chip = document.createElement('div');
        chip.className = 'attachment-chip';
        chip.innerHTML = `<i data-lucide="file-text" class="hud-icon-xs"></i> ${name} <span class="remove-btn" onclick="removeAttachment(${idx})">×</span>`;
        container.appendChild(chip);
      });
      renderIcons();
    }


    function removeAttachment(idx) {
      attachedFilePaths.splice(idx, 1);
      renderAttachmentChips();
    }


    let modalUploadedPath = null;


    async function handleModalFileUpload(event) {
      const file = event.target.files[0];
      if (!file) return;
      document.getElementById('modal-selected-filename').innerText = "Uploading " + file.name + "...";
      const formData = new FormData();
      formData.append('file', file);
      try {
        const res = await fetch('/api/upload', { method: 'POST', body: formData });
        const data = await res.json();
        modalUploadedPath = data.path;
        document.getElementById('modal-selected-filename').innerText = "✔ Ready: " + file.name;
      } catch (e) {
        alert('Upload failed: ' + e);
      }
    }


    async function submitSuppliedFile() {
      const pathInput = document.getElementById('modal-path-input').value.trim();
      const finalPath = modalUploadedPath || pathInput;
      if (!finalPath) {
        alert("Please select/drop a file or enter a local file path.");
        return;
      }
      await fetch('/api/supply-file', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ file_path: finalPath })
      });
      document.getElementById('file-request-modal').classList.remove('active');
      modalUploadedPath = null;
      document.getElementById('modal-path-input').value = '';
    }


    async function cancelSuppliedFile() {
      await fetch('/api/supply-file', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ file_path: null })
      });
      document.getElementById('file-request-modal').classList.remove('active');
      modalUploadedPath = null;
      document.getElementById('modal-path-input').value = '';
    }


    function openLightbox(src, title) {
      document.getElementById('lightbox-image').src = src;
      document.getElementById('lightbox-title').innerText = title || 'Screenshot Inspection (1920x1080)';
      document.getElementById('lightbox-modal').classList.add('active');
    }


    function closeLightbox(e) {
      if (!e || e.target.id === 'lightbox-modal' || e.target.classList.contains('btn-danger')) {
        document.getElementById('lightbox-modal').classList.remove('active');
      }
    }


    let currentTerminalFontSize = parseInt(localStorage.getItem('bro_terminal_font_size') || '15', 10);


    function applyTerminalFontSize() {
      const term = document.getElementById('terminal-logs');
      if (term) {
        term.style.setProperty('--terminal-font-size', currentTerminalFontSize + 'px');
      }
      const ind = document.getElementById('terminal-font-indicator');
      if (ind) ind.innerText = currentTerminalFontSize + 'px';
      try {
        localStorage.setItem('bro_terminal_font_size', currentTerminalFontSize);
      } catch (e) { }
    }


    function adjustTerminalFont(delta) {
      currentTerminalFontSize = Math.max(12, Math.min(26, currentTerminalFontSize + delta));
      applyTerminalFontSize();
    }


    function resetTerminalFont() {
      currentTerminalFontSize = 15;
      applyTerminalFontSize();
    }


    function clearTerminalLogs() {
      const term = document.getElementById('terminal-logs');
      term.innerHTML = '<div class="log-line" style="color: var(--neon-cyan);">[SYSTEM] Terminal logs cleared. Live stream active.</div>';
    }


    function copyTerminalLogs() {
      const term = document.getElementById('terminal-logs');
      navigator.clipboard.writeText(term.innerText).then(() => {
        alert("Terminal logs copied to clipboard!");
      });
    }


    function copySnippet(text) {
      navigator.clipboard.writeText(text).then(() => {
        alert("Copied command to clipboard:\n" + text);
      });
    }


    async function pasteClipboard() {
      try {
        const text = await navigator.clipboard.readText();
        if (text) {
          const input = document.getElementById('goal-input');
          input.value = (input.value ? input.value + ' ' : '') + text;
        }
      } catch (e) {
        alert("Could not access clipboard directly: " + e);
      }
    }


    let ws;


    function connectWS() {
      const proto = location.protocol === 'https:' ? 'wss:' : 'ws:';
      ws = new WebSocket(`${proto}//${location.host}/ws`);
      ws.onopen = () => {
        const dot = document.getElementById('ws-status-dot');
        const txt = document.getElementById('ws-status-text');
        if (dot) dot.className = 'status-dot dot-green';
        if (txt) txt.innerText = 'Live WebSocket Connected';
      };
      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          if (msg.event === 'task_start') {
            startMultiStepSession(msg.data.goal);
          }
          if (msg.event === 'thought') {
            appendLog('thought', '💭 ' + msg.data);
            if (currentConversationMode === 'audio_only') {
              updateVoiceVisualizerState('processing', `REASONING: ${msg.data.slice(0, 45)}...`);
            }
          }
          if (msg.event === 'action') {
            appendLog('action', `⚡ [${msg.data.actuator}] ${msg.data.detail}`);
            recordActuatorAction(msg.data.actuator, msg.data.detail);
            if (currentConversationMode === 'audio_only') {
              if (msg.data.actuator === 'voice') {
                updateVoiceVisualizerState('speaking', 'BRO SPEAKING (BRO BUTLER)...');
              } else {
                updateVoiceVisualizerState('processing', `ACTION: ${msg.data.actuator}`);
              }
            }
          }
          if (msg.event === 'step') {
            appendLog('step', `▶ Step ${msg.data.step}/${msg.data.total}: ${msg.data.desc}`);
            updateMissionProgress(msg.data.step, msg.data.total, msg.data.desc);
            updateMultiStepSidebar(msg.data.step, msg.data.total, msg.data.desc);
            if (currentConversationMode === 'audio_only') {
              updateVoiceVisualizerState('processing', `STEP ${msg.data.step}/${msg.data.total}`);
            }
          }
          if (msg.event === 'calendar_updated') {
            loadCalendar();
          }
          if (msg.event === 'conversation_mode_changed') {
            if (currentConversationMode !== msg.data.conversation_mode) {
              syncConversationModeUI(msg.data.conversation_mode, true);
            }
          }
          if (msg.event === 'model_policy_changed') {
            if (msg.data.policy) {
              syncPolicyUI(msg.data.policy, msg.data.cloud_model, true);
            }
          }
          if (msg.event === 'voice_changed') {
            if (msg.data.tts_voice && msg.data.tts_voice !== currentActiveVoice) {
              currentActiveVoice = msg.data.tts_voice;
              ['voice-select-dropdown', 'audio-hud-voice-select', 'sel-voice-model'].forEach(id => {
                const el = document.getElementById(id);
                if (el && el.value !== currentActiveVoice) el.value = currentActiveVoice;
              });
            }
            if (msg.data.tts_rate && msg.data.tts_rate !== currentActiveRate) {
              currentActiveRate = msg.data.tts_rate;
              const mult = parseRateToMultiplier(currentActiveRate);
              syncSpeedUI(mult, true);
            }
          }
          if (msg.event === 'pre_response') {
            const preText = (typeof msg.data === 'object' && msg.data.text) ? msg.data.text : msg.data;
            if (preText) {
              if (currentConversationMode === 'audio_only') {
                const broSub = document.getElementById('sub-bro-text');
                if (broSub) broSub.innerText = `"${preText}"`;
                updateVoiceVisualizerState('speaking', 'ACKNOWLEDGING...');
              }
              appendLog('thought', `💬 [BRO] ${preText}`);
            }
          }
          if (msg.event === 'task_response' || msg.event === 'response') {
            const respText = (typeof msg.data === 'object' && msg.data.text) ? msg.data.text : msg.data;
            if (respText) {
              lastBroadcastResponse = respText;
              if (currentConversationMode === 'audio_only') {
                const broSub = document.getElementById('sub-bro-text');
                if (broSub) broSub.innerText = `"${respText}"`;
                updateVoiceVisualizerState('speaking', 'BRO SPEAKING...');
              }
              appendLog('result', '✔ ' + respText);
            }
          }
          if (msg.event === 'response_chunk') {
            const chunk = (typeof msg.data === 'object' && msg.data.chunk) ? msg.data.chunk : msg.data;
            const accum = (typeof msg.data === 'object' && msg.data.accumulated) ? msg.data.accumulated : chunk;
            if (currentConversationMode === 'audio_only') {
              const broSub = document.getElementById('sub-bro-text');
              if (broSub && accum) broSub.innerText = `"${accum}"`;
              updateVoiceVisualizerState('speaking', 'BRO STREAMING...');
            }
          }
          if (msg.event === 'task_finish') {
            isTaskExecuting = false;
            const resultText = msg.data.result;
            if (resultText && resultText !== lastBroadcastResponse) {
              appendLog('result', '✔ ' + resultText);
            }
            lastBroadcastResponse = '';
            document.getElementById('active-task-label').innerText = 'COMPLETED';
            hideMissionProgress();
            finishMultiStepSession(resultText);
            loadHistory();

            // Variant 3: Automatic 90% Screen Explanation Dialog on Diagrams
            if (resultText && resultText.includes('```mermaid')) {
              const mMatch = resultText.match(/```mermaid([\s\S]*?)```/);
              if (mMatch) {
                const diagramCode = mMatch[0];
                const cleanText = resultText.replace(/```mermaid[\s\S]*?```/, '').trim();
                openContextualExplanation('System Architecture & Explanation', diagramCode, cleanText);
              }
            }

            if (currentConversationMode === 'audio_only') {
              if (resultText) {
                const broSub = document.getElementById('sub-bro-text');
                if (broSub) broSub.innerText = `"${resultText}"`;
              }
              updateVoiceVisualizerState('speaking', 'BRO REPLY COMPLETED');
            }

            // Continuous Hands-Free Re-Arming Protocol
            if (handsFreeLoopEnabled && shouldKeepListening) {
              if (currentConversationMode === 'audio_only') {
                setTimeout(() => {
                  if (currentConversationMode === 'audio_only' && handsFreeLoopEnabled && shouldKeepListening && !isTaskExecuting) {
                    updateVoiceVisualizerState('listening', '🟢 LISTENING... SPEAK NOW');
                  }
                }, 400);
              }
              scheduleRecognitionRestart(700);
            } else {
              if (currentConversationMode === 'audio_only') {
                updateVoiceVisualizerState('idle', '⚪ READY // CLICK CORE TO SPEAK');
              }
              stopSpeechRecognitionUI();
            }
          }
          if (msg.event === 'briefing') {
            appendLog('result', '☀️ [DAILY BRIEF] ' + msg.data);
            if (currentConversationMode === 'audio_only') {
              document.getElementById('sub-bro-text').innerText = `"${msg.data}"`;
              updateVoiceVisualizerState('speaking', 'DAILY BRIEF DELIVERED');
              setTimeout(() => {
                if (currentConversationMode === 'audio_only') updateVoiceVisualizerState('idle', '⚪ READY // CLICK CORE TO SPEAK');
              }, 4000);
            }
          }
          if (msg.event === 'file_requested') {
            showFileRequestModal(msg.data.description, msg.data.expected_filename);
          }
          if (msg.event === 'show_media') {
            showVisualMediaModal(msg.data);
          }
          if (msg.event === 'desktop_changed') {
            loadDesktopMonitors();
          }
          if (msg.event === 'telemetry') updateTelemetry(msg.data);
        } catch (e) { }
      };
      ws.onclose = () => {
        const dot = document.getElementById('ws-status-dot');
        const txt = document.getElementById('ws-status-text');
        if (dot) dot.className = 'status-dot dot-amber';
        if (txt) txt.innerText = 'Reconnecting...';
        setTimeout(connectWS, 3000);
      };
    }


    connectWS();


    if (window.mermaid) {
      try {
        mermaid.initialize({
          startOnLoad: false,
          theme: 'dark',
          securityLevel: 'loose',
          themeVariables: {
            darkMode: true,
            background: '#0a0f1d',
            primaryColor: '#00e5ff',
            primaryBorderColor: '#00e5ff',
            primaryTextColor: '#ffffff',
            lineColor: '#2979ff',
            secondaryColor: '#101c34',
            tertiaryColor: '#0d1527'
          }
        });
      } catch (e) {
        console.warn("Mermaid init notice:", e);
      }
    }


    let currentMediaData = null;


    let showingRawMediaCode = false;


    async function showVisualMediaModal(data) {
      if (!data) return;
      currentMediaData = data;
      showingRawMediaCode = false;

      const modal = document.getElementById('media-display-modal');
      const icon = document.getElementById('media-modal-icon');
      const title = document.getElementById('media-modal-title');
      const caption = document.getElementById('media-modal-caption');
      const badge = document.getElementById('media-type-badge');
      const container = document.getElementById('media-render-container');
      const rawCode = document.getElementById('media-raw-code');
      const btnToggle = document.getElementById('btn-toggle-raw');

      title.innerText = data.title || 'Visual Observation';
      caption.innerText = data.caption || 'Bro Tactical Visual Analysis Unit';
      rawCode.innerText = data.content || '';
      rawCode.style.display = 'none';
      container.style.display = 'flex';
      btnToggle.innerHTML = '<i data-lucide="code" class="hud-icon-xs"></i> View Raw Syntax';

      const mediaType = (data.media_type || 'image').toLowerCase();
      badge.innerText = mediaType.toUpperCase();

      if (mediaType === 'file') {
        showFileViewerModal(data.title, data.content, data.caption);
        return;
      }

      if (mediaType === 'diagram') {
        openContextualExplanation(data.title || 'Contextual Architecture & Explanation', data.content, data.caption || 'Contextual visual architecture and relational flow.');
        return;
      } else if (mediaType === 'chart') {
        icon.innerHTML = '<i data-lucide="trending-up" class="hud-icon-md text-green"></i>';
        badge.style.borderColor = 'var(--neon-green)';
        badge.style.color = 'var(--neon-green)';
        badge.style.background = 'rgba(0, 230, 118, 0.15)';

        if ((data.content || '').trim().startsWith('<svg')) {
          container.innerHTML = `<div class="mermaid-viewport">${data.content}</div>`;
        } else {
          const imgUrl = (data.content || '').startsWith('/') ? `/api/media/file?path=${encodeURIComponent(data.content)}` : data.content;
          container.innerHTML = `<img src="${imgUrl}" class="media-viewer-img" alt="Visual Chart" onclick="openLightbox('${imgUrl}', '${data.title || 'Chart'}')">`;
        }
      } else {
        // Image
        icon.innerHTML = '<i data-lucide="image" class="hud-icon-md text-amber"></i>';
        badge.style.borderColor = 'var(--neon-amber)';
        badge.style.color = 'var(--neon-amber)';
        badge.style.background = 'rgba(255, 171, 0, 0.15)';

        const imgUrl = (data.content || '').startsWith('/') ? `/api/media/file?path=${encodeURIComponent(data.content)}` : data.content;
        container.innerHTML = `
          <div style="display: flex; flex-direction: column; align-items: center; gap: 0.5rem;">
            <img src="${imgUrl}" class="media-viewer-img" alt="Captured Image" onclick="openLightbox('${imgUrl}', '${data.title || 'Image'}')">
            <span style="font-size: 0.72rem; color: var(--text-muted); font-family: 'JetBrains Mono', monospace;">Click image to expand in 1080p Lightbox</span>
          </div>
        `;
      }

      modal.classList.add('active');
      renderIcons();
    }


    function closeMediaModal() {
      const modal = document.getElementById('media-display-modal');
      if (modal) modal.classList.remove('active');
    }


    function toggleRawMediaCode() {
      const container = document.getElementById('media-render-container');
      const rawCode = document.getElementById('media-raw-code');
      const btn = document.getElementById('btn-toggle-raw');
      showingRawMediaCode = !showingRawMediaCode;
      if (showingRawMediaCode) {
        container.style.display = 'none';
        rawCode.style.display = 'block';
        btn.innerHTML = '<i data-lucide="eye" class="hud-icon-xs"></i> View Visual Render';
      } else {
        container.style.display = 'flex';
        rawCode.style.display = 'none';
        btn.innerHTML = '<i data-lucide="code" class="hud-icon-xs"></i> View Raw Syntax';
      }
      renderIcons();
    }


    async function copyMediaContent() {
      if (!currentMediaData) return;
      try {
        await navigator.clipboard.writeText(currentMediaData.content || '');
        alert('Copied media content / syntax to clipboard!');
      } catch (e) {
        alert('Unable to access clipboard: ' + e);
      }
    }


    async function spawnDesktopWindowFromModal() {
      if (!currentMediaData) return;
      try {
        await fetch('/api/media/show', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            media_type: currentMediaData.media_type,
            content: currentMediaData.content,
            title: currentMediaData.title,
            caption: currentMediaData.caption,
            target: 'system_window'
          })
        });
      } catch (e) {
        alert('Failed to spawn desktop system window: ' + e);
      }
    }


    async function showArchitectureDiagram() {
      const diag = `graph TD
    User["👤 User (Voice / Web / Hotkey / CLI)"] --> Router["⚡ Tier-0 Router (Sub-100ms Llama 3.2 3B)"]
    Router -->|Casual Greeting| Butler["🔊 Bro Butler Voice (RyanNeural)"]
    Router -->|Complex Task| Gemma["🧠 Tier-1 Gemma 4 12B (Pinned in VRAM)"]
    Gemma --> Perception["👁️ Vision Grounding (Qwen2.5-VL 7B)"]
    Gemma --> Gatekeeper{"🛡️ High-Stakes Action?"}
    Gatekeeper -->|Yes| Overlay["🪟 X11 Approval Overlay"]
    Gatekeeper -->|No / Authorized| Actuators["⚡ Actuators"]
    Actuators --> Desktop["🖱️ Desktop UI (mss + pyautogui)"]
    Actuators --> Chrome["🌐 Dual Browser (Everyday CDP + Sandbox)"]
    Actuators --> Python["🐍 Python Runner & Data Crunch"]
    Actuators --> Visuals["📊 Visual Media (Web Dialog + System Window)"]
    Visuals --> HUD["🖥️ Bro Variant 2 Tactical HUD"]`;
      showVisualMediaModal({
        media_type: 'diagram',
        content: diag,
        title: 'Bro Variant 2 Tactical Architecture',
        caption: 'Multi-tier Perception-Reasoning-Action (ReAct) Engine with Dual Visual Display'
      });
    }


    let detectedMonitors = [];


    let currentMainScreenIndex = 1;


    let availableVoices = [];


    let currentActiveVoice = 'en-GB-RyanNeural';


    let currentActiveRate = '+2%';


    let currentSpeedMultiplier = 1.0;


    function showFileRequestModal(desc, exp) {
      document.getElementById('modal-req-desc').innerText = desc;
      document.getElementById('modal-req-exp').innerText = exp ? ("Expected filename: " + exp) : "";
      document.getElementById('modal-selected-filename').innerText = "No file selected yet";
      document.getElementById('modal-path-input').value = '';
      document.getElementById('file-request-modal').classList.add('active');
    }


    function updateMissionProgress(step, total, desc) {
      const p = document.getElementById('mission-progress');
      p.classList.add('active');
      const pct = Math.round((step / total) * 100);
      document.getElementById('mission-step-title').innerText = `Step ${step}/${total}: ${desc}`;
      document.getElementById('mission-step-pct').innerText = `${pct}%`;
      document.getElementById('mission-progress-bar').style.width = `${pct}%`;
    }


    function hideMissionProgress() {
      setTimeout(() => {
        document.getElementById('mission-progress').classList.remove('active');
      }, 3000);
    }


    function updateTelemetry(data) {
      if (data.gpu_temp) {
        document.getElementById('val-gpu-temp').innerText = data.gpu_temp + '°C';
        document.getElementById('bar-gpu-temp').style.width = Math.min(100, (data.gpu_temp / 90) * 100) + '%';
      }
      if (data.vram_used_mb) {
        document.getElementById('val-vram').innerText = data.vram_used_mb + ' / ' + data.vram_total_mb + ' MB';
        document.getElementById('bar-vram').style.width = Math.min(100, (data.vram_used_mb / data.vram_total_mb) * 100) + '%';
      }
      if (data.ram_percent) {
        document.getElementById('val-ram').innerText = data.ram_percent + '% (' + data.ram_used_gb + ' GB)';
        document.getElementById('bar-ram').style.width = data.ram_percent + '%';
      }
      if (data.cpu_percent) {
        document.getElementById('val-cpu').innerText = data.cpu_percent + '%';
        document.getElementById('bar-cpu').style.width = data.cpu_percent + '%';
      }
      if (data.disk_percent !== undefined) {
        const rootUsed = data.disk_root_used_gb || 0;
        const rootTotal = data.disk_root_total_gb || 0;
        document.getElementById('val-disk-root').innerText = `${rootUsed} / ${rootTotal} GB (${data.disk_percent}%)`;
        document.getElementById('bar-disk-root').style.width = data.disk_percent + '%';
      }
      if (data.disk_hdd) {
        const hddCont = document.getElementById('meter-disk-hdd-container');
        if (hddCont) hddCont.style.display = 'block';
        document.getElementById('val-disk-hdd').innerText = `${data.disk_hdd.used_gb} / ${data.disk_hdd.total_gb} GB (${data.disk_hdd.percent}%)`;
        document.getElementById('bar-disk-hdd').style.width = data.disk_hdd.percent + '%';
      }
    }


    let recognition = null;


    let isRecording = false;


    let isTaskExecuting = false;


    let lastBroadcastResponse = '';


    let shouldKeepListening = false;


    let recognitionRestartTimeout = null;


    let handsFreeLoopEnabled = true;


    let isBroSpeaking = false;


    document.addEventListener('fullscreenchange', () => {
      const hud = document.getElementById('audio-only-hud');
      if (!hud) return;
      if (!document.fullscreenElement && hud.classList.contains('hud-fullscreen')) {
        exitAudioFullscreen();
      }
    });


    document.addEventListener('webkitfullscreenchange', () => {
      const hud = document.getElementById('audio-only-hud');
      if (!hud) return;
      if (!document.webkitFullscreenElement && hud.classList.contains('hud-fullscreen')) {
        exitAudioFullscreen();
      }
    });


    window.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        const hud = document.getElementById('audio-only-hud');
        if (hud && hud.classList.contains('hud-fullscreen')) {
          exitAudioFullscreen();
        }
      }
    });


    let mediaRecorder = null;


    let audioChunks = [];


    let isWhisperRecording = false;


    let speechFinalTranscript = '';


    let speechSilenceTimer = null;


    async function runTask(explicitGoal = null) {
      const input = document.getElementById('goal-input');
      const goal = (explicitGoal || (input ? input.value : '')).trim();
      if (!goal) return;

      isTaskExecuting = true;
      if (recognitionRestartTimeout) {
        clearTimeout(recognitionRestartTimeout);
        recognitionRestartTimeout = null;
      }
      if (recognition) {
        try { recognition.abort(); } catch (e) { }
      }

      if (currentConversationMode === 'audio_only') {
        updateVoiceVisualizerState('processing', `PROCESSING: "${goal.slice(0, 35)}"`);
        document.getElementById('sub-user-text').innerText = `"${goal}"`;
        document.getElementById('sub-bro-text').innerText = "Analyzing and executing...";
      }

      document.getElementById('active-task-label').innerText = 'EXECUTING...';
      appendLog('step', `▶ User Goal: "${goal}"`);
      if (input) input.value = '';

      const payload = {
        goal: goal,
        conversation_mode: currentConversationMode
      };
      if (attachedFilePaths.length) {
        payload.file_paths = [...attachedFilePaths];
      }

      try {
        await fetch('/api/run', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
      } catch (e) {
        isTaskExecuting = false;
        appendLog('error', 'Task execution request failed: ' + e);
        loadErrors();
        if (currentConversationMode === 'audio_only') {
          updateVoiceVisualizerState('idle', 'ERROR // CLICK CORE TO RETRY');
        }
        if (handsFreeLoopEnabled && shouldKeepListening) {
          scheduleRecognitionRestart(1200);
        }
      }
    }


    async function triggerBrief() {
      try {
        const res = await fetch('/api/brief', { method: 'POST' });
        const data = await res.json();
        appendLog('result', '☀️ ' + data.briefing);
      } catch (e) {
        alert('Daily brief error: ' + e);
      }
    }


    async function launchCDP() {
      const btn = document.getElementById('btn-cdp');
      btn.innerText = 'Connecting to Chrome...';
      try {
        const res = await fetch('/api/browser/launch-cdp', { method: 'POST' });
        const data = await res.json();
        if (data.available || data.success) {
          btn.innerText = '✔ Chrome Attached (CDP :9222)';
          btn.style.borderColor = 'var(--neon-green)';
        } else {
          btn.innerText = '✖ Launch Failed';
        }
      } catch (e) {
        btn.innerText = '✖ Error';
      }
    }


    async function runOrganizer() {
      try {
        const res = await fetch('/api/organizer/run', { method: 'POST' });
        const data = await res.json();
        alert(`Organized ${data.moved_count} file(s):\n` + data.details.join('\n'));
      } catch (e) { alert('Organizer error: ' + e); }
    }


    async function killSwitch() {
      if (confirm('Are you sure you want to trigger the Master Kill Switch? This will terminate all Bro processes.')) {
        await fetch('/api/system/kill', { method: 'POST' });
        alert('Kill signal sent. Bro Variant 2 services terminated.');
      }
    }


    let currentModelPolicy = 'local_only';


    let cachedGatewayProviders = [];


    let cachedBriefConfig = null;


    let explanationZoom = 1.0;


    let currentExplanationSvg = '';


    async function openContextualExplanation(title, diagramCode, explanationText) {
      const modal = document.getElementById('contextual-explanation-modal');
      const titleElem = document.getElementById('explanation-modal-title');
      const viewport = document.getElementById('explanation-diagram-viewport');
      const summaryCapsule = document.getElementById('explanation-summary-capsule');
      const deepDiveBody = document.getElementById('explanation-deep-dive-body');

      if (!modal) return;
      if (titleElem) titleElem.innerText = title || 'Contextual Architecture & System Explanation';

      // Split summary (first 2-3 sentences) from remaining details
      let summary = '';
      let remaining = explanationText || '';
      const periodIdx = remaining.indexOf('. ');
      if (periodIdx !== -1) {
        const secondPeriod = remaining.indexOf('. ', periodIdx + 2);
        const splitAt = (secondPeriod !== -1) ? secondPeriod + 1 : periodIdx + 1;
        summary = remaining.slice(0, splitAt).trim();
        remaining = remaining.slice(splitAt).trim();
      } else {
        summary = remaining;
        remaining = 'Would you like to dig deeper into any specific aspect of this architecture?';
      }

      if (summaryCapsule) {
        summaryCapsule.innerHTML = `<b>EXECUTIVE SUMMARY:</b><br>${summary}`;
      }
      if (deepDiveBody) {
        deepDiveBody.innerHTML = remaining.replace(/\n\n/g, '<br><br>').replace(/\n/g, '<br>');
      }

      // Render Mermaid diagram
      if (viewport && diagramCode) {
        viewport.innerHTML = '<div style="color: var(--neon-cyan); font-family: monospace;">Rendering interactive diagram...</div>';
        let cleanMermaid = diagramCode.trim();
        if (cleanMermaid.startsWith('```mermaid')) {
          cleanMermaid = cleanMermaid.replace(/^```mermaid\s*/i, '').replace(/```\s*$/, '').trim();
        } else if (cleanMermaid.startsWith('```')) {
          cleanMermaid = cleanMermaid.replace(/^```[a-z]*\s*/i, '').replace(/```\s*$/, '').trim();
        }

        if (window.mermaid) {
          try {
            const id = 'mermaid-expl-' + Math.floor(Math.random() * 1000000);
            const res = await mermaid.render(id, cleanMermaid);
            currentExplanationSvg = res.svg;
            viewport.innerHTML = res.svg;
          } catch (err) {
            console.warn("Mermaid render error:", err);
            viewport.innerHTML = `<pre style="color: #a6e3a1; font-family: monospace; text-align: left;">${cleanMermaid}</pre>`;
          }
        } else {
          viewport.innerHTML = `<pre style="color: #a6e3a1; font-family: monospace; text-align: left;">${cleanMermaid}</pre>`;
        }
      }

      explanationZoom = 1.0;
      if (viewport) viewport.style.transform = `scale(${explanationZoom})`;
      modal.style.display = 'flex';
      if (window.lucide) lucide.createIcons();
    }


    function zoomExplanationDiagram(factor) {
      explanationZoom = Math.max(0.4, Math.min(3.0, explanationZoom * factor));
      const viewport = document.getElementById('explanation-diagram-viewport');
      if (viewport) viewport.style.transform = `scale(${explanationZoom})`;
    }


    function resetExplanationZoom() {
      explanationZoom = 1.0;
      const viewport = document.getElementById('explanation-diagram-viewport');
      if (viewport) viewport.style.transform = `scale(1.0)`;
    }


    function exportExplanationSvg() {
      if (!currentExplanationSvg) {
        alert("No SVG diagram available to export.");
        return;
      }
      const blob = new Blob([currentExplanationSvg], { type: 'image/svg+xml' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `bro_diagram_${Date.now()}.svg`;
      a.click();
      URL.revokeObjectURL(url);
    }


    function closeExplanationModal() {
      const modal = document.getElementById('contextual-explanation-modal');
      if (modal) modal.style.display = 'none';
    }


    function askFollowUpExplanation(promptText) {
      closeExplanationModal();
      setGoal(promptText);
      runTask();
    }


    let cachedRuns = [];


    let activeFilter = 'all';


    let selectedRunId = null;


    let briefSlotsData = [];


    const TOPIC_OPTIONS = ['weather', 'calendar', 'tech_news', 'world_news', 'hardware'];


    document.addEventListener('click', (e) => {
      if (!e.target.closest('.report-download-group')) {
        closeReportDropdown();
      }
    });


    let memoryFiles = [];


    let currentActiveMemoryFile = 'preferences.md';


    let currentMemoryView = 'editor'; // 'editor' | 'vault'


    let currentResolvedMemoryDir = '~/ai-memory/bro';


    async function pollStatus() {
      try {
        const res = await fetch('/api/status');
        const data = await res.json();
        if (data.telemetry) updateTelemetry(data.telemetry);
        if (data.conversation_mode && (!window.userInteractingWithMode)) {
          if (currentConversationMode !== data.conversation_mode) {
            syncConversationModeUI(data.conversation_mode, false);
          }
        }
        if (typeof data.autonomous_mode === 'boolean') {
          syncAutonomousUI(data.autonomous_mode);
        }
        if (typeof data.tts_volume === 'number' && data.tts_volume !== currentActiveVolume) {
          syncVolumeUI(data.tts_volume, true);
        }
        const valPol = document.getElementById('val-policy');
        if (valPol && data.policy) valPol.innerText = data.policy.toUpperCase();

        // Update Watchdogs Matrix with Visual Borders & Toggle Switches
        function updateSentinelCard(cardId, swId, dotId, isActive, activeDotClass = 'dot-green', inactiveDotClass = 'dot-gray') {
          const card = document.getElementById(cardId);
          const sw = document.getElementById(swId);
          const dot = document.getElementById(dotId);
          if (card) {
            if (isActive) {
              card.classList.add('is-active');
              card.classList.remove('is-inactive');
            } else {
              card.classList.add('is-inactive');
              card.classList.remove('is-active');
            }
          }
          if (sw && sw.checked !== !!isActive) sw.checked = !!isActive;
          if (dot) dot.className = 'status-dot ' + (isActive ? activeDotClass : inactiveDotClass);
        }

        updateSentinelCard('card-sentinel', 'matrix-sw-sentinel', 'dot-sentinel', data.sentinel_active);
        updateSentinelCard('card-organizer', 'matrix-sw-organizer', 'dot-organizer', data.organizer_active);
        updateSentinelCard('card-spotlight', 'matrix-sw-spotlight', 'dot-spotlight', data.spotlight_enabled);
        updateSentinelCard('card-cdp', 'matrix-sw-cdp', 'dot-cdp', data.cdp_browser_available);
        const subCdp = document.getElementById('sub-cdp');
        if (subCdp) subCdp.innerText = data.cdp_browser_available ? 'Attached (:9222)' : 'Port :9222 Standby';
        updateSentinelCard('card-tier0', 'matrix-sw-tier0', 'dot-tier0', data.tier0_enabled, 'dot-green', 'dot-amber');
        const subTier0 = document.getElementById('sub-tier0');
        if (subTier0) subTier0.innerText = data.tier0_enabled ? ('<100ms ' + (data.tier0_model || 'Llama 3.2 3B')) : 'Disabled (Direct Gemma 4)';
        updateSentinelCard('card-telegram', 'matrix-sw-telegram', 'dot-telegram', data.cron_brief_active);
        if (typeof data.desktop_screen_index === 'number' && data.desktop_screen_index !== currentMainScreenIndex) {
          currentMainScreenIndex = data.desktop_screen_index;
          loadDesktopMonitors();
        }
        if (data.tts_voice && data.tts_voice !== currentActiveVoice) {
          currentActiveVoice = data.tts_voice;
          ['voice-select-dropdown', 'audio-hud-voice-select', 'sel-voice-model', 'settings-voice-select'].forEach(id => {
            const el = document.getElementById(id);
            if (el && el.value !== currentActiveVoice) el.value = currentActiveVoice;
          });
        }
        if (data.tts_rate && data.tts_rate !== currentActiveRate) {
          currentActiveRate = data.tts_rate;
          const mult = parseRateToMultiplier(currentActiveRate);
          syncSpeedUI(mult, true);
        }
        if (data.policy && data.policy !== currentModelPolicy) {
          syncPolicyUI(data.policy, data.cloud_model, false);
        }
        if (data.stt_engine && data.stt_engine !== currentSttEngine) {
          currentSttEngine = data.stt_engine;
          const sttSel = document.getElementById('settings-stt-engine-select');
          if (sttSel && sttSel.value !== currentSttEngine) sttSel.value = currentSttEngine;
        }
        if (typeof data.sfx_enabled === 'boolean' && data.sfx_enabled !== sfxEnabled) {
          sfxEnabled = data.sfx_enabled;
          const sfxEl = document.getElementById('settings-sfx-toggle');
          if (sfxEl && sfxEl.checked !== sfxEnabled) sfxEl.checked = sfxEnabled;
        }
        if (typeof data.rag_chunks === 'number') {
          const chunkBadge = document.getElementById('obsidian-chunk-count');
          if (chunkBadge) chunkBadge.innerText = `${data.rag_chunks} Chunks Indexed`;
        }

        // Update Active Neural & LLM Settings Container (Variant 4)
        const activeTier0El = document.getElementById('active-llm-tier0');
        if (activeTier0El) {
          activeTier0El.innerText = data.tier0_enabled ? `${data.tier0_model || 'llama3.2:3b'} (Active)` : 'Disabled (Direct)';
          activeTier0El.style.color = data.tier0_enabled ? 'var(--neon-amber)' : 'var(--text-muted)';
        }
        const activeTextEl = document.getElementById('active-llm-text');
        if (activeTextEl) {
          const selText = document.getElementById('sel-text-model');
          const txtModel = (selText && selText.value) || data.local_text_model || 'gemma4:12b';
          activeTextEl.innerText = `${txtModel} (Local)`;
        }
        const activeVisionEl = document.getElementById('active-llm-vision');
        if (activeVisionEl) {
          const selVis = document.getElementById('sel-vision-model');
          const visModel = (selVis && selVis.value) || data.local_vision_model || 'qwen2.5vl:7b';
          activeVisionEl.innerText = visModel;
        }
        const activePolEl = document.getElementById('active-llm-policy');
        if (activePolEl && data.policy) {
          activePolEl.innerText = data.policy.toUpperCase().replace('_', ' ');
        }
        const genzToggle = document.getElementById('settings-genz-greetings-toggle');
        if (genzToggle && typeof data.gen_z_greetings === 'boolean' && genzToggle.checked !== data.gen_z_greetings) {
          genzToggle.checked = data.gen_z_greetings;
        }
      } catch (e) { }
      loadErrors();
    }


    const MONTH_NAMES = [


      "January", "February", "March", "April", "May", "June",


      "July", "August", "September", "October", "November", "December"


    ];


    let currentViewerContent = '';


    let multiStepState = {
      active: false,
      step: 0,
      total: 0,
      goal: '',
      actuators: {},
      steps: []
    };


    const ACTUATOR_COLORS = {
      desktop: '#00e5ff',
      browser: '#2979ff',
      shell: '#00ff9d',
      python: '#a855f7',
      macro: '#ffab00',
      memory: '#ff6b6b',
      voice: '#38bdf8',
      other: '#94a3b8'
    };


    function toggleMultiStepSidebar() {
      const sb = document.getElementById('multi-step-sidebar');
      if (sb) sb.classList.toggle('collapsed');
      renderIcons();
    }


    function showMultiStepSidebar() {
      const sb = document.getElementById('multi-step-sidebar');
      if (sb) sb.classList.remove('collapsed');
      renderIcons();
    }


    function startMultiStepSession(goal) {
      multiStepState = {
        active: true,
        step: 0,
        total: 10,
        goal: goal || 'Autonomous Mission',
        actuators: {},
        steps: []
      };
      const badge = document.getElementById('multi-step-counter-badge');
      if (badge) badge.innerText = 'INITIALIZING';
      const label = document.getElementById('multi-step-progress-label');
      if (label) label.innerText = '0 / 0';
      const bar = document.getElementById('multi-step-progress-bar');
      if (bar) bar.style.width = '0%';
      const breadcrumbs = document.getElementById('multi-step-breadcrumbs');
      if (breadcrumbs) breadcrumbs.innerHTML = `<div style="color: var(--neon-cyan); font-size: 0.74rem; font-family: 'JetBrains Mono', monospace; padding: 0.5rem 0;">▶ Goal: ${escapeHtml(goal)}</div>`;
      showMultiStepSidebar();
    }


    function updateMultiStepSidebar(step, total, desc) {
      multiStepState.active = true;
      multiStepState.step = step;
      multiStepState.total = total;

      const pct = Math.min(100, Math.round((step / total) * 100));
      const bar = document.getElementById('multi-step-progress-bar');
      if (bar) bar.style.width = `${pct}%`;

      const label = document.getElementById('multi-step-progress-label');
      if (label) label.innerText = `${step} / ${total} (${pct}%)`;

      const badge = document.getElementById('multi-step-counter-badge');
      if (badge) badge.innerText = `STEP ${step}/${total}`;

      const toggleLabel = document.getElementById('multi-step-toggle-label');
      if (toggleLabel) toggleLabel.innerText = `Steps (${step}/${total})`;

      // Add to breadcrumb stream
      const breadcrumbs = document.getElementById('multi-step-breadcrumbs');
      if (breadcrumbs) {
        // Mark previous cards as completed
        breadcrumbs.querySelectorAll('.step-breadcrumb-card').forEach(c => {
          c.classList.remove('active');
          c.classList.add('completed');
        });

        const card = document.createElement('div');
        card.className = 'step-breadcrumb-card active';
        const now = new Date().toTimeString().slice(0, 8);
        card.innerHTML = `
          <div style="display: flex; justify-content: space-between; align-items: center;">
            <span style="font-weight: 700; color: var(--neon-cyan); font-family: 'JetBrains Mono', monospace;">STEP ${step}</span>
            <span style="color: var(--text-muted); font-size: 0.68rem; font-family: 'JetBrains Mono', monospace;">${now}</span>
          </div>
          <div style="color: #ffffff; line-height: 1.3; font-size: 0.73rem;">${escapeHtml(desc)}</div>
        `;
        breadcrumbs.appendChild(card);
        breadcrumbs.scrollTop = breadcrumbs.scrollHeight;
      }
      showMultiStepSidebar();
    }


    function recordActuatorAction(actuator, detail) {
      if (!actuator) return;
      const key = actuator.toLowerCase().split('_')[0] || 'other';
      multiStepState.actuators[key] = (multiStepState.actuators[key] || 0) + 1;

      const activeLabel = document.getElementById('multi-step-actuator-active');
      if (activeLabel) activeLabel.innerText = `${actuator}`;

      renderActuatorBreakdown();
    }


    function renderActuatorBreakdown() {
      const bar = document.getElementById('multi-step-actuator-bar');
      const legend = document.getElementById('multi-step-actuator-legend');
      if (!bar || !legend) return;

      const entries = Object.entries(multiStepState.actuators);
      const totalCalls = entries.reduce((acc, [, count]) => acc + count, 0);

      if (totalCalls === 0) {
        bar.innerHTML = '<div style="width: 100%; background: rgba(255,255,255,0.08);"></div>';
        legend.innerHTML = '<span>No actions dispatched yet</span>';
        return;
      }

      let barHtml = '';
      let legendHtml = '';
      entries.forEach(([name, count]) => {
        const pct = Math.round((count / totalCalls) * 100);
        const col = ACTUATOR_COLORS[name] || ACTUATOR_COLORS.other;
        barHtml += `<div style="width: ${pct}%; background: ${col};" title="${name}: ${pct}% (${count})"></div>`;
        legendHtml += `<span style="display: flex; align-items: center; gap: 3px;"><span style="display:inline-block; width:6px; height:6px; border-radius:50%; background:${col};"></span>${name}: ${pct}%</span>`;
      });

      bar.innerHTML = barHtml;
      legend.innerHTML = legendHtml;
    }


    function finishMultiStepSession(result) {
      multiStepState.active = false;
      const badge = document.getElementById('multi-step-counter-badge');
      if (badge) badge.innerText = 'FINISHED';

      const bar = document.getElementById('multi-step-progress-bar');
      if (bar) bar.style.width = '100%';

      const breadcrumbs = document.getElementById('multi-step-breadcrumbs');
      if (breadcrumbs) {
        const finCard = document.createElement('div');
        finCard.className = 'step-breadcrumb-card completed';
        finCard.style.borderColor = 'var(--neon-green)';
        finCard.innerHTML = `
          <div style="color: var(--neon-green); font-weight: 700; font-family: 'JetBrains Mono', monospace;">✔ MISSION COMPLETED</div>
          <div style="color: #cbd5e1; font-size: 0.72rem; line-height: 1.35;">${escapeHtml(result || 'Task completed successfully.')}</div>
        `;
        breadcrumbs.appendChild(finCard);
        breadcrumbs.scrollTop = breadcrumbs.scrollHeight;
      }
    }


    pollStatus();


    setInterval(pollStatus, 5000);


    loadHistory();


    loadDesktopMonitors();


    loadVoices();


    loadModels();


    loadGatewayProviders();


    loadDailyBriefConfig();


    loadMemory();


    loadCalendar();


    applyTerminalFontSize();


    document.addEventListener('DOMContentLoaded', () => {
      initThemeUI();
      initAudioVisualizerUI();
      startAudioVisualizerLoop();
      applyTerminalFontSize();
      loadVoices();
      loadModels();
      loadGatewayProviders();
      loadDailyBriefConfig();
      loadMemory();
      loadCalendar();
      renderIcons();
    });


    setTimeout(renderIcons, 200);


    setTimeout(renderIcons, 1000);
