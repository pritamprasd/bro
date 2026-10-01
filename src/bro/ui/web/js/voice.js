// =========================================================================
// BRO VOICE ENGINE
// =========================================================================

    let currentActiveVolume = 100;


    function syncVolumeUI(vol, updateSlider = true) {
      currentActiveVolume = vol;
      const elVal = document.getElementById('settings-volume-val');
      if (elVal) elVal.innerText = vol + '%';
      if (updateSlider) {
        const elSlider = document.getElementById('settings-volume-slider');
        if (elSlider && parseInt(elSlider.value) !== vol) {
          elSlider.value = vol;
        }
      }
    }


    function onVolumeInput(val) {
      const vol = parseInt(val) || 100;
      syncVolumeUI(vol, false);
    }


    async function onVolumeChange(val) {
      const vol = parseInt(val) || 100;
      syncVolumeUI(vol, true);
      try {
        await fetch('/api/voice/select', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ volume: vol })
        });
        appendLog('step', `🔊 Bro voice volume calibrated to: ${vol}%.`);
      } catch (e) {
        console.error("Failed to update voice volume:", e);
      }
    }


    async function testBroVolume() {
      try {
        await fetch('/api/voice/preview', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            voice: currentActiveVoice,
            rate: currentActiveRate,
            volume: currentActiveVolume,
            sample_text: `Bro audio volume is calibrated to ${currentActiveVolume} percent, sir.`
          })
        });
      } catch (e) {
        console.error("Volume preview error:", e);
      }
    }


    function parseRateToMultiplier(rateStr) {
      if (!rateStr) return 1.0;
      const num = parseInt(rateStr);
      if (isNaN(num)) return 1.0;
      return Math.max(0.5, Math.min(2.0, Math.round((1.0 + num / 100) * 100) / 100));
    }


    function multiplierToRateStr(mult) {
      const pct = Math.round((mult - 1.0) * 100);
      return pct >= 0 ? `+${pct}%` : `${pct}%`;
    }


    function syncSpeedUI(mult, updateSliders = true) {
      currentSpeedMultiplier = mult;
      const formatted = mult.toFixed(2) + 'x';
      ['voice-speed-val', 'audio-hud-speed-val', 'models-tab-speed-val', 'settings-voice-speed-val'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.innerText = formatted;
      });
      if (updateSliders) {
        ['voice-speed-slider', 'audio-hud-speed-slider', 'models-tab-speed-slider', 'settings-voice-speed-slider'].forEach(id => {
          const el = document.getElementById(id);
          if (el && Math.abs(parseFloat(el.value) - mult) > 0.01) {
            el.value = mult;
          }
        });
      }
    }


    function onVoiceSpeedInput(value) {
      const mult = parseFloat(value) || 1.0;
      syncSpeedUI(mult, false);
      ['voice-speed-slider', 'audio-hud-speed-slider', 'models-tab-speed-slider', 'settings-voice-speed-slider'].forEach(id => {
        const el = document.getElementById(id);
        if (el && el.value !== value) el.value = value;
      });
    }


    async function onVoiceSpeedChange(value) {
      const mult = parseFloat(value) || 1.0;
      syncSpeedUI(mult, true);
      const rateStr = multiplierToRateStr(mult);
      currentActiveRate = rateStr;

      try {
        const res = await fetch('/api/voice/select', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ rate: rateStr })
        });
        const data = await res.json();
        if (data.current_rate) {
          currentActiveRate = data.current_rate;
        }
        appendLog('step', `⚡ Bro vocal speed updated to: ${mult.toFixed(2)}x (${rateStr}).`);
      } catch (e) {
        console.error("Failed to update voice speed:", e);
      }
    }


    function resetVoiceSpeed() {
      onVoiceSpeedInput("1.0");
      onVoiceSpeedChange("1.0");
    }


    async function loadVoices() {
      try {
        const res = await fetch('/api/voice/voices');
        const data = await res.json();
        availableVoices = data.voices || [];
        currentActiveVoice = data.current_voice || 'en-GB-RyanNeural';
        currentActiveRate = data.current_rate || '+2%';

        populateVoiceDropdown('voice-select-dropdown', availableVoices, currentActiveVoice);
        populateVoiceDropdown('audio-hud-voice-select', availableVoices, currentActiveVoice);
        populateVoiceDropdown('sel-voice-model', availableVoices, currentActiveVoice);
        populateVoiceDropdown('settings-voice-select', availableVoices, currentActiveVoice);

        const mult = parseRateToMultiplier(currentActiveRate);
        syncSpeedUI(mult, true);
      } catch (e) {
        console.error("Failed to load available voices:", e);
      }
    }


    function populateVoiceDropdown(elementId, voices, selectedVoice) {
      const el = document.getElementById(elementId);
      if (!el) return;
      el.innerHTML = '';

      const recGroup = document.createElement('optgroup');
      recGroup.label = '⭐ RECOMMENDED PERSONAS';

      const otherGroup = document.createElement('optgroup');
      otherGroup.label = '🌐 ALL VOICES';

      voices.forEach(v => {
        const opt = document.createElement('option');
        opt.value = v.short_name;
        const genderBadge = v.gender ? ` [${v.gender}]` : '';
        const localeBadge = v.locale ? ` (${v.locale})` : '';
        opt.innerText = `${v.name}${genderBadge}${localeBadge}`;
        if (v.short_name === selectedVoice) {
          opt.selected = true;
        }
        if (v.recommended) {
          recGroup.appendChild(opt);
        } else {
          otherGroup.appendChild(opt);
        }
      });

      if (recGroup.children.length > 0) el.appendChild(recGroup);
      if (otherGroup.children.length > 0) el.appendChild(otherGroup);
      el.value = selectedVoice;
    }


    async function onVoiceSelectChange(voiceId) {
      if (!voiceId) return;
      try {
        const res = await fetch('/api/voice/select', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ voice: voiceId })
        });
        const data = await res.json();
        currentActiveVoice = data.current_voice;

        // Synchronize all voice dropdowns
        ['voice-select-dropdown', 'audio-hud-voice-select', 'sel-voice-model', 'settings-voice-select'].forEach(id => {
          const el = document.getElementById(id);
          if (el && el.value !== currentActiveVoice) el.value = currentActiveVoice;
        });

        const voiceObj = availableVoices.find(v => v.short_name === voiceId);
        const voiceName = voiceObj ? voiceObj.name : voiceId;
        appendLog('step', `🎙️ Bro vocal persona switched to: ${voiceName} (${voiceId}).`);
      } catch (e) {
        console.error("Failed to update voice:", e);
        alert("Failed to update voice: " + e);
      }
    }


    async function previewSelectedVoice(voiceId) {
      const voice = voiceId || currentActiveVoice || (document.getElementById('settings-voice-select') ? document.getElementById('settings-voice-select').value : (document.getElementById('voice-select-dropdown') ? document.getElementById('voice-select-dropdown').value : 'en-GB-RyanNeural'));
      const voiceObj = availableVoices.find(v => v.short_name === voice);
      const voiceName = voiceObj ? voiceObj.name : voice;

      appendLog('thought', `🔊 Previewing voice persona: ${voiceName} at ${currentSpeedMultiplier.toFixed(2)}x speed...`);
      try {
        await fetch('/api/voice/preview', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            voice: voice,
            rate: currentActiveRate,
            text: `Greetings. This is Bro neural speech synthesis preview, operating at ${currentSpeedMultiplier.toFixed(2)} times speed.`
          })
        });
      } catch (e) {
        console.error("Failed to preview voice:", e);
      }
    }


    let currentConversationMode = 'audio+chat';


    function toggleHandsFreeLoop(enabled) {
      handsFreeLoopEnabled = enabled;
      const cb1 = document.getElementById('handsfree-checkbox');
      const cb2 = document.getElementById('settings-handsfree-loop');
      if (cb1 && cb1.checked !== enabled) cb1.checked = enabled;
      if (cb2 && cb2.checked !== enabled) cb2.checked = enabled;

      appendLog('step', `🎙️ Hands-Free Loop: ${enabled ? 'ENABLED' : 'PAUSED'}`);
      if (!enabled) {
        if (!isRecording) {
          shouldKeepListening = false;
          if (recognitionRestartTimeout) {
            clearTimeout(recognitionRestartTimeout);
            recognitionRestartTimeout = null;
          }
        }
      }
    }


    async function setConversationMode(mode) {
      if (currentConversationMode === mode) return;
      syncConversationModeUI(mode, true);

      try {
        await fetch('/api/settings/conversation-mode', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ mode: mode })
        });
      } catch (e) {
        console.warn("Failed to set conversation mode:", e);
      }
    }


    function syncConversationModeUI(mode, logChange = false) {
      const modeChanged = (currentConversationMode !== mode);
      currentConversationMode = mode;
      if (mode !== 'audio_only') {
        exitAudioFullscreen();
      }
      document.querySelectorAll('#conversation-mode-segmented .mode-pill').forEach(btn => btn.classList.remove('active'));
      const activeBtn = document.getElementById('btn-mode-' + mode.replace('+', '_'));
      if (activeBtn) activeBtn.classList.add('active');

      const badge = document.getElementById('current-mode-badge');
      const audioHud = document.getElementById('audio-only-hud');
      const voiceToggleBtn = document.getElementById('btn-voice-toggle');

      const quickStrip = document.getElementById('quick-action-strip');
      const homeQuickWidgets = document.getElementById('homepage-quick-widgets');

      if (mode === 'audio_only') {
        if (badge) {
          badge.innerHTML = '<i data-lucide="mic" class="hud-icon-xs"></i> AUDIO ONLY';
          badge.style.borderColor = 'var(--neon-cyan)';
          badge.style.color = 'var(--neon-cyan)';
          badge.style.background = 'rgba(0, 229, 255, 0.15)';
        }
        if (audioHud) audioHud.style.display = 'block';
        if (quickStrip) {
          quickStrip.style.display = 'block';
          renderIcons();
        }
        if (homeQuickWidgets) homeQuickWidgets.style.display = 'none';
        if (voiceToggleBtn) voiceToggleBtn.innerHTML = '<i data-lucide="volume-2" class="hud-icon-xs"></i> Voice: ON (Audio Only)';
        if (modeChanged) {
          shouldKeepListening = true;
          updateVoiceVisualizerState('listening', '🟢 LISTENING... SPEAK NOW');
          scheduleRecognitionRestart(300);
          if (logChange) {
            appendLog('step', 'Conversation Mode: AUDIO ONLY (Continuous Voice Dialogue Active)');
          }
        }
      } else if (mode === 'audio+chat') {
        if (badge) {
          badge.innerHTML = '<i data-lucide="zap" class="hud-icon-xs"></i> AUDIO + CHAT';
          badge.style.borderColor = 'var(--neon-cyan)';
          badge.style.color = 'var(--neon-cyan)';
          badge.style.background = 'rgba(0, 229, 255, 0.1)';
        }
        if (audioHud) audioHud.style.display = 'none';
        if (quickStrip) quickStrip.style.display = 'none';
        if (homeQuickWidgets) homeQuickWidgets.style.display = 'grid';
        if (voiceToggleBtn) voiceToggleBtn.innerHTML = '<i data-lucide="volume-2" class="hud-icon-xs"></i> Voice Reply: ON';
        if (modeChanged && logChange) {
          appendLog('step', 'Conversation Mode: AUDIO + CHAT (Voice Replies + Terminal Stream)');
        }
      } else if (mode === 'chat_only') {
        if (badge) {
          badge.innerHTML = '<i data-lucide="message-square" class="hud-icon-xs"></i> CHAT ONLY (SILENT)';
          badge.style.borderColor = '#a6e3a1';
          badge.style.color = '#a6e3a1';
          badge.style.background = 'rgba(166, 227, 161, 0.15)';
        }
        if (audioHud) audioHud.style.display = 'none';
        if (quickStrip) quickStrip.style.display = 'none';
        if (homeQuickWidgets) homeQuickWidgets.style.display = 'grid';
        if (voiceToggleBtn) voiceToggleBtn.innerHTML = '<i data-lucide="volume-x" class="hud-icon-xs"></i> Voice Reply: MUTED';
        if (modeChanged) {
          shouldKeepListening = false;
          if (recognitionRestartTimeout) {
            clearTimeout(recognitionRestartTimeout);
            recognitionRestartTimeout = null;
          }
          if (recognition) { try { recognition.abort(); } catch (e) { } }
          stopSpeechRecognitionUI();
          if (logChange) {
            appendLog('step', 'Conversation Mode: CHAT ONLY (Spoken Voice Disabled)');
          }
        }
      }
      renderIcons();
    }


    function updateVoiceVisualizerState(state, labelText) {
      currentVoiceVisualizerState = state;
      const core = document.getElementById('arc-visualizer-core');
      const pill = document.getElementById('voice-state-pill');
      const soundwave = document.getElementById('soundwave-container');
      const icon = document.getElementById('vis-reactor-icon');
      const qStage = document.getElementById('vis-stage-quantum');
      const qStatus = document.getElementById('quantum-hud-status');
      const qCaption = document.getElementById('quantum-hud-caption');
      const qMic = document.getElementById('quantum-hud-mic');
      const emojiStage = document.getElementById('vis-stage-emoji');
      const emojiStatus = document.getElementById('emoji-hud-status');
      const emojiCaption = document.getElementById('emoji-hud-caption');
      const emojiMic = document.getElementById('emoji-hud-mic');
      const matrixStatus = document.getElementById('matrix-status-text');

      if (core) core.className = 'arc-visualizer-core';
      if (soundwave) soundwave.className = 'soundwave-container';
      if (qStage) qStage.className = 'quantum-stage-wrapper';
      if (emojiStage) emojiStage.className = 'emoji-stage-wrapper';

      if (state === 'listening') {
        if (core) core.classList.add('vis-listening');
        if (soundwave) soundwave.classList.add('active-listening');
        if (qStage) qStage.classList.add('vis-listening');
        if (emojiStage) emojiStage.classList.add('vis-listening');
        if (icon) icon.innerHTML = '<i data-lucide="mic" style="width: 38px; height: 38px; stroke-width: 2.2;"></i>';
        if (pill) {
          pill.innerHTML = '<i data-lucide="radio" class="hud-icon-xs"></i> ' + (labelText || 'LISTENING... SPEAK NOW');
          pill.style.color = 'var(--neon-green)';
          pill.style.borderColor = 'var(--neon-green)';
        }
        if (qStatus) {
          qStatus.innerText = 'Listening...';
          qStatus.style.color = '#ffffff';
        }
        if (emojiStatus) {
          emojiStatus.innerText = 'Listening...';
          emojiStatus.style.color = '#00ff9d';
        }
        if (qMic) {
          qMic.style.borderColor = 'var(--neon-green)';
          qMic.style.boxShadow = '0 0 25px rgba(0, 255, 157, 0.7)';
          qMic.style.color = 'var(--neon-green)';
        }
        if (emojiMic) {
          emojiMic.style.borderColor = 'var(--neon-green)';
          emojiMic.style.boxShadow = '0 0 25px rgba(0, 255, 157, 0.7)';
          emojiMic.style.color = 'var(--neon-green)';
        }
        if (matrixStatus) {
          matrixStatus.innerText = 'SPECTRUM ACTIVE // LISTENING';
          matrixStatus.style.color = 'var(--neon-green)';
        }
      } else if (state === 'processing') {
        if (core) core.classList.add('vis-processing');
        if (soundwave) soundwave.classList.add('active-processing');
        if (qStage) qStage.classList.add('vis-processing');
        if (emojiStage) emojiStage.classList.add('vis-processing');
        if (icon) icon.innerHTML = '<i data-lucide="zap" style="width: 38px; height: 38px; stroke-width: 2.2;"></i>';
        if (pill) {
          pill.innerHTML = '<i data-lucide="cpu" class="hud-icon-xs"></i> ' + (labelText || 'EVALUATING INTENT & ACTIONS...');
          pill.style.color = 'var(--neon-cyan)';
          pill.style.borderColor = 'var(--neon-cyan)';
        }
        if (qStatus) {
          qStatus.innerText = 'Thinking...';
          qStatus.style.color = 'var(--neon-cyan)';
        }
        if (emojiStatus) {
          emojiStatus.innerText = 'Thinking...';
          emojiStatus.style.color = 'var(--neon-purple)';
        }
        if (qMic) {
          qMic.style.borderColor = 'var(--neon-cyan)';
          qMic.style.boxShadow = '0 0 25px rgba(0, 229, 255, 0.7)';
          qMic.style.color = 'var(--neon-cyan)';
        }
        if (emojiMic) {
          emojiMic.style.borderColor = 'var(--neon-purple)';
          emojiMic.style.boxShadow = '0 0 25px rgba(168, 85, 247, 0.7)';
          emojiMic.style.color = 'var(--neon-purple)';
        }
        if (matrixStatus) {
          matrixStatus.innerText = 'NEURAL REASONING // PROCESSING';
          matrixStatus.style.color = 'var(--neon-cyan)';
        }
      } else if (state === 'speaking') {
        if (core) core.classList.add('vis-speaking');
        if (soundwave) soundwave.classList.add('active-speaking');
        if (qStage) qStage.classList.add('vis-speaking');
        if (emojiStage) emojiStage.classList.add('vis-speaking');
        if (icon) icon.innerHTML = '<i data-lucide="volume-2" style="width: 38px; height: 38px; stroke-width: 2.2;"></i>';
        if (pill) {
          pill.innerHTML = '<i data-lucide="volume-2" class="hud-icon-xs"></i> ' + (labelText || 'BRO SPEAKING (BRO BUTLER)...');
          pill.style.color = 'var(--neon-amber)';
          pill.style.borderColor = 'var(--neon-amber)';
        }
        if (qStatus) {
          qStatus.innerText = 'BRO Speaking...';
          qStatus.style.color = '#fee440';
        }
        if (emojiStatus) {
          emojiStatus.innerText = 'BRO Speaking...';
          emojiStatus.style.color = '#fee440';
        }
        if (qMic) {
          qMic.style.borderColor = '#fee440';
          qMic.style.boxShadow = '0 0 25px rgba(254, 228, 64, 0.7)';
          qMic.style.color = '#fee440';
        }
        if (emojiMic) {
          emojiMic.style.borderColor = '#fee440';
          emojiMic.style.boxShadow = '0 0 25px rgba(254, 228, 64, 0.7)';
          emojiMic.style.color = '#fee440';
        }
        if (matrixStatus) {
          matrixStatus.innerText = 'VOCAL SYNTHESIS // BRO SPEAKING';
          matrixStatus.style.color = 'var(--neon-amber)';
        }
      } else {
        if (core) core.classList.add('vis-idle');
        if (qStage) qStage.classList.add('vis-idle');
        if (emojiStage) emojiStage.classList.add('vis-idle');
        if (icon) icon.innerHTML = '<i data-lucide="mic" style="width: 38px; height: 38px; stroke-width: 2.2;"></i>';
        if (pill) {
          pill.innerHTML = '<i data-lucide="circle" class="hud-icon-xs"></i> ' + (labelText || 'READY // CLICK TO SPEAK');
          pill.style.color = 'var(--text-muted)';
          pill.style.borderColor = 'var(--panel-border)';
        }
        if (qStatus) {
          qStatus.innerText = 'Standing By';
          qStatus.style.color = '#cbd5e1';
        }
        if (emojiStatus) {
          emojiStatus.innerText = 'Standing By';
          emojiStatus.style.color = '#cbd5e1';
        }
        if (qMic) {
          qMic.style.borderColor = 'rgba(0, 229, 255, 0.5)';
          qMic.style.boxShadow = '0 0 15px rgba(0, 229, 255, 0.3)';
          qMic.style.color = '#00e5ff';
        }
        if (emojiMic) {
          emojiMic.style.borderColor = 'rgba(254, 228, 64, 0.5)';
          emojiMic.style.boxShadow = '0 0 15px rgba(254, 228, 64, 0.3)';
          emojiMic.style.color = '#fee440';
        }
        if (matrixStatus) {
          matrixStatus.innerText = 'SPECTRUM STANDBY // CLICK TO TALK';
          matrixStatus.style.color = 'var(--neon-cyan)';
        }
      }
      isBroSpeaking = (state === 'speaking');
      renderIcons();
    }


    async function stopVoicePlayback() {
      try {
        await fetch('/api/voice/stop', { method: 'POST' });
      } catch (e) { }
      if (window.speechSynthesis) {
        window.speechSynthesis.cancel();
      }
      isBroSpeaking = false;
      playTacticalSfx('barge_in');
      updateVoiceVisualizerState('idle', '🟠 BARGE-IN // SPEECH INTERRUPTED');
      appendLog('system', '[VOICE] Speech interrupted by operator (Barge-In).');
      if (handsFreeLoopEnabled && shouldKeepListening && !isRecording && !isWhisperRecording) {
        scheduleRecognitionRestart(350);
      }
    }


    function scheduleRecognitionRestart(delayMs = 700) {
      if (recognitionRestartTimeout) {
        clearTimeout(recognitionRestartTimeout);
        recognitionRestartTimeout = null;
      }
      if (!handsFreeLoopEnabled || !shouldKeepListening || isTaskExecuting) return;

      recognitionRestartTimeout = setTimeout(() => {
        recognitionRestartTimeout = null;
        if (handsFreeLoopEnabled && shouldKeepListening && !isTaskExecuting) {
          startSpeechRecognitionSafe();
        }
      }, delayMs);
    }


    let currentSttEngine = 'browser';


    function onSttEngineChange(val) {
      currentSttEngine = val;
      const sel = document.getElementById('settings-stt-engine-select');
      if (sel && sel.value !== val) sel.value = val;
      appendLog('system', `[STT] Speech-to-text pipeline switched to: ${val === 'whisper' ? 'Local CUDA Whisper' : 'Browser Web Speech API'}`);
    }


    async function startWhisperRecording() {
      if (isWhisperRecording) return;
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream);
        audioChunks = [];

        mediaRecorder.ondataavailable = (e) => {
          if (e.data && e.data.size > 0) audioChunks.push(e.data);
        };

        mediaRecorder.onstop = async () => {
          isWhisperRecording = false;
          stream.getTracks().forEach(t => t.stop());
          const blob = new Blob(audioChunks, { type: 'audio/wav' });
          if (blob.size > 1000) {
            updateVoiceVisualizerState('processing', '⚡ TRANSCRIBING (GPU WHISPER)...');
            const fd = new FormData();
            fd.append('file', blob, 'speech.wav');
            try {
              const res = await fetch('/api/voice/transcribe', { method: 'POST', body: fd });
              const data = await res.json();
              if (data.status === 'success' && data.text && data.text.trim()) {
                const text = data.text.trim();
                if (currentConversationMode === 'audio_only') {
                  const subU = document.getElementById('sub-user-text');
                  if (subU) subU.innerText = `"${text}"`;
                } else {
                  const gi = document.getElementById('goal-input');
                  if (gi) gi.value = text;
                }
                runTask(text);
              } else {
                updateVoiceVisualizerState('idle', '⚪ READY // CLICK CORE TO SPEAK');
                if (handsFreeLoopEnabled && shouldKeepListening) scheduleRecognitionRestart(500);
              }
            } catch (err) {
              appendLog('error', '[STT] Local Whisper error: ' + err);
              updateVoiceVisualizerState('idle', '⚪ READY');
            }
          }
        };

        mediaRecorder.start();
        isWhisperRecording = true;
        playTacticalSfx('mic_start');
        updateVoiceVisualizerState('listening', '🟢 LISTENING (CUDA WHISPER)...');
      } catch (err) {
        appendLog('error', '[MIC] Microphone permission/stream error: ' + err);
      }
    }


    function stopWhisperRecording() {
      if (mediaRecorder && mediaRecorder.state !== 'inactive') {
        mediaRecorder.stop();
        playTacticalSfx('mic_stop');
      }
      isWhisperRecording = false;
    }


    function startSpeechRecognitionSafe() {
      if (!handsFreeLoopEnabled && !shouldKeepListening) return;
      if (isTaskExecuting) return;
      if (currentSttEngine === 'whisper') {
        startWhisperRecording();
        return;
      }
      if (!recognition) initSpeechRecognition();
      if (!recognition) return;

      if (recognitionRestartTimeout) {
        clearTimeout(recognitionRestartTimeout);
        recognitionRestartTimeout = null;
      }

      try {
        if (isRecording) {
          try { recognition.abort(); } catch (e) { }
          setTimeout(() => {
            if (!isTaskExecuting && shouldKeepListening) {
              try { recognition.start(); } catch (err) { console.warn("Recognition retry start err:", err); }
            }
          }, 150);
          return;
        }
        recognition.start();
      } catch (e) {
        console.warn("Recognition start caught:", e);
        if (e.name === 'InvalidStateError') {
          try { recognition.abort(); } catch (e2) { }
          setTimeout(() => {
            if (!isTaskExecuting && shouldKeepListening) {
              try { recognition.start(); } catch (e3) { }
            }
          }, 200);
        }
      }
    }


    function startSpeechRecognitionContinuous() {
      shouldKeepListening = true;
      startSpeechRecognitionSafe();
    }


    function toggleAudioOnlySession() {
      if (isBroSpeaking) {
        stopVoicePlayback();
        return;
      }

      if (currentSttEngine === 'whisper') {
        if (isWhisperRecording) {
          stopWhisperRecording();
          shouldKeepListening = false;
          updateVoiceVisualizerState('idle', '⚪ PAUSED // CLICK CORE TO RESUME');
        } else {
          shouldKeepListening = true;
          startWhisperRecording();
        }
        return;
      }

      if (!recognition) initSpeechRecognition();
      if (!recognition) {
        alert("Web Speech API is not supported in this browser. Please use Chrome or Brave, or switch to Local CUDA Whisper in Settings.");
        return;
      }
      if (isRecording || shouldKeepListening) {
        shouldKeepListening = false;
        if (recognitionRestartTimeout) {
          clearTimeout(recognitionRestartTimeout);
          recognitionRestartTimeout = null;
        }
        try { recognition.abort(); } catch (e) { }
        stopSpeechRecognitionUI();
        updateVoiceVisualizerState('idle', '⚪ PAUSED // CLICK CORE TO RESUME');
      } else {
        shouldKeepListening = true;
        startSpeechRecognitionSafe();
      }
    }


    function speakQuickPrompt(text) {
      if (currentConversationMode === 'audio_only') {
        document.getElementById('sub-user-text').innerText = `"${text}"`;
      }
      runTask(text);
    }


    function initSpeechRecognition() {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      if (SpeechRecognition) {
        recognition = new SpeechRecognition();
        recognition.continuous = true;
        recognition.interimResults = true;
        recognition.lang = 'en-US';

        recognition.onstart = () => {
          isRecording = true;
          speechFinalTranscript = '';
          if (speechSilenceTimer) {
            clearTimeout(speechSilenceTimer);
            speechSilenceTimer = null;
          }
          playTacticalSfx('mic_start');
          const micBtn = document.getElementById('mic-btn');
          if (micBtn) {
            micBtn.classList.add('listening');
            micBtn.title = "Listening... Click to pause hands-free microphone";
          }
          const goalInput = document.getElementById('goal-input');
          if (goalInput) goalInput.placeholder = "Listening... Speak your command now";
          if (currentConversationMode === 'audio_only') {
            updateVoiceVisualizerState('listening', '🟢 LISTENING... SPEAK NOW');
          }
        };

        recognition.onresult = (event) => {
          if (isBroSpeaking) {
            stopVoicePlayback();
          }

          let interimTranscript = '';
          for (let i = event.resultIndex; i < event.results.length; ++i) {
            const res = event.results[i];
            if (res.isFinal) {
              speechFinalTranscript += res[0].transcript + ' ';
            } else {
              interimTranscript += res[0].transcript;
            }
          }

          const currentLiveText = (speechFinalTranscript + interimTranscript).trim();
          if (!currentLiveText) return;

          // Stream words onto screen in real-time
          if (currentConversationMode === 'audio_only') {
            const subUser = document.getElementById('sub-user-text');
            if (subUser) subUser.innerText = `"${currentLiveText}"`;
            const qCaption = document.getElementById('quantum-hud-caption');
            if (qCaption) qCaption.innerText = currentLiveText;
          } else {
            const goalInput = document.getElementById('goal-input');
            if (goalInput) goalInput.value = currentLiveText;
          }

          // Debounce execution on silence (800ms) to ensure full multi-word utterances are captured
          if (speechSilenceTimer) clearTimeout(speechSilenceTimer);
          speechSilenceTimer = setTimeout(() => {
            const finalUtterance = (speechFinalTranscript + ' ' + interimTranscript).trim();
            if (finalUtterance && !isTaskExecuting) {
              isTaskExecuting = true;
              speechFinalTranscript = '';
              try { recognition.stop(); } catch (e) { }
              isRecording = false;
              runTask(finalUtterance);
            }
          }, 800);
        };

        recognition.onerror = (event) => {
          console.warn("Speech recognition error:", event ? event.error : "unknown");
          if (event && event.error === 'no-speech') {
            if (handsFreeLoopEnabled && shouldKeepListening && !isTaskExecuting) {
              scheduleRecognitionRestart(300);
              return;
            }
          } else if (event && event.error === 'aborted') {
            return;
          } else if (event && (event.error === 'not-allowed' || event.error === 'service-not-allowed')) {
            shouldKeepListening = false;
            stopSpeechRecognitionUI();
            appendLog('error', 'Microphone permission denied by browser.');
            return;
          }
          if (handsFreeLoopEnabled && shouldKeepListening && !isTaskExecuting) {
            scheduleRecognitionRestart(1000);
          } else {
            stopSpeechRecognitionUI();
          }
        };

        recognition.onend = () => {
          isRecording = false;
          if (isTaskExecuting) {
            return;
          }
          if (handsFreeLoopEnabled && shouldKeepListening) {
            scheduleRecognitionRestart(300);
          } else {
            stopSpeechRecognitionUI();
          }
        };
      }
    }


    function toggleVoiceRecognition() {
      if (!recognition) initSpeechRecognition();
      if (!recognition) {
        alert("Web Speech API is not supported in this browser. Please use Chrome or Brave.");
        return;
      }
      if (isRecording || shouldKeepListening) {
        shouldKeepListening = false;
        if (recognitionRestartTimeout) {
          clearTimeout(recognitionRestartTimeout);
          recognitionRestartTimeout = null;
        }
        try { recognition.abort(); } catch (e) { }
        stopSpeechRecognitionUI();
      } else {
        shouldKeepListening = true;
        startSpeechRecognitionSafe();
      }
    }


    function stopSpeechRecognitionUI() {
      isRecording = false;
      const micBtn = document.getElementById('mic-btn');
      if (micBtn) {
        micBtn.classList.remove('listening');
        micBtn.title = "Click to speak with Bro";
      }
      const goalInput = document.getElementById('goal-input');
      if (goalInput) {
        goalInput.placeholder = "Speak or type a command (e.g. 'Hello', 'Search Wikipedia', 'Open calculator')...";
      }
      if (currentConversationMode === 'audio_only' && !isRecording && !isTaskExecuting) {
        updateVoiceVisualizerState('idle', shouldKeepListening ? '⚪ READY // SPEAK NOW OR CLICK CORE' : '⚪ PAUSED // CLICK CORE TO SPEAK');
      }
    }


    function stopSpeechRecognition() {
      stopSpeechRecognitionUI();
    }


    async function toggleVoiceReply() {
      try {
        const nextMode = (currentConversationMode === 'chat_only') ? 'audio+chat' : 'chat_only';
        await setConversationMode(nextMode);
      } catch (e) { }
    }


    window.addEventListener('keydown', (e) => {
      const tag = (e.target && e.target.tagName) ? e.target.tagName.toUpperCase() : '';
      if (tag === 'INPUT' || tag === 'TEXTAREA' || (e.target && e.target.isContentEditable)) {
        if (e.key === 'Escape') {
          e.target.blur();
        }
        return;
      }

      if (e.key === '?' || (e.shiftKey && e.key === '/')) {
        e.preventDefault();
        toggleShortcutsModal();
      } else if (e.key === '1') {
        switchTab('command');
      } else if (e.key === '2') {
        switchTab('command');
        const t = document.getElementById('terminal-logs');
        if (t) t.scrollIntoView({ behavior: 'smooth' });
      } else if (e.key === '3') {
        switchTab('settings');
        const s = document.getElementById('proactive-sentinels-matrix-header');
        if (s) s.scrollIntoView({ behavior: 'smooth' });
      } else if (e.key === '4') {
        switchTab('history');
      } else if (e.key === '5') {
        switchTab('guide');
      } else if (e.key === 'f' || e.key === 'F') {
        e.preventDefault();
        toggleAudioFullscreen();
      } else if (e.key === 'm' || e.key === 'M') {
        e.preventDefault();
        if (currentConversationMode === 'audio_only') {
          toggleAudioOnlySession();
        } else {
          toggleSpeechRecognition();
        }
      } else if (e.key === 'Escape') {
        const modal = document.getElementById('shortcuts-modal');
        if (modal && modal.style.display === 'flex') {
          modal.style.display = 'none';
        } else if (isBroSpeaking) {
          stopVoicePlayback();
        }
      }
    });


    async function toggleGenZGreetings(enabled) {
      try {
        const res = await fetch('/api/voice/select', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ gen_z_greetings: enabled })
        });
        if (res.ok) {
          playTacticalSfx('toggle');
          appendLog('action', `⚡ Gen-Z Slang & Greetings: ${enabled ? 'ENABLED' : 'DISABLED'}`);
        }
      } catch (e) {
        console.error('Gen-Z toggle error:', e);
      }
    }


    window.addEventListener('load', () => {
      initThemeUI();
      initAudioVisualizerUI();
      startAudioVisualizerLoop();
      applyTerminalFontSize();
      loadVoices();
      loadModels();
      loadMemory();
      loadCalendar();
      renderIcons();

      // Check URL parameters for shortcut launcher: ?mode=audio_only&greet=1&loop=1
      const urlParams = new URLSearchParams(window.location.search);
      const reqMode = urlParams.get('mode');
      const reqGreet = urlParams.get('greet');
      const reqLoop = urlParams.get('loop');

      if (reqMode === 'audio_only' || reqMode === 'audio+chat' || reqMode === 'chat_only') {
        setConversationMode(reqMode);
      }
      if (reqLoop === '1' || reqLoop === 'true') {
        handsFreeLoopEnabled = true;
        shouldKeepListening = true;
        const loopToggle = document.getElementById('settings-handsfree-loop');
        if (loopToggle) loopToggle.checked = true;
      }
      if (reqGreet === '1' || reqGreet === 'true') {
        fetch('/api/voice/greeting')
          .then(r => r.json())
          .then(d => {
            if (d.greeting) {
              appendLog('result', '🎙️ [INITIAL GREETING] ' + d.greeting);
              if (currentConversationMode === 'audio_only') {
                updateVoiceVisualizerState('speaking', '🔊 ' + d.greeting);
                const subBro = document.getElementById('sub-bro-text');
                if (subBro) subBro.innerText = `"${d.greeting}"`;
              }
              speakVoiceResponse(d.greeting);
            }
          })
          .catch(e => console.warn('Greeting fetch failed:', e));
      }
    });
