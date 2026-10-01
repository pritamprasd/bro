// =========================================================================
// BRO SETTINGS ENGINE
// =========================================================================

    async function testApprovalOverlay() {
      try {
        appendLog('step', '🛡️ Summoning Safety Gatekeeper Approval Overlay on desktop display...');
        const res = await fetch('/api/safety/test-overlay', { method: 'POST' });
        const data = await res.json();
        appendLog(data.approved ? 'result' : 'warning', `🛡️ Safety Gatekeeper Result: ${data.approved ? 'ACTION AUTHORIZED' : 'ACTION REJECTED'}`);
      } catch (e) {
        console.error("Failed to test safety overlay:", e);
      }
    }


    async function toggleWatchdogCard(target) {
      try {
        const res = await fetch('/api/watchdogs/toggle', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ target })
        });
        const data = await res.json();
        if (data.status === 'success') {
          appendLog('step', `🛡️ Proactive Matrix: ${data.message}`);
          pollStatus();
        }
      } catch (e) {
        console.error("Failed to toggle watchdog sentinel:", e);
      }
    }


    let currentAutonomousMode = false;


    function syncAutonomousUI(isAuto) {
      currentAutonomousMode = isAuto;
      const labelText = isAuto ? 'ON (Full Autonomy)' : 'OFF (Approval Overlay Active)';
      const badgeText = isAuto ? 'FULL AUTONOMY UNLOCKED' : 'APPROVAL OVERLAY ACTIVE';
      const badgeColor = isAuto ? '#ef4444' : '#10b981';
      const badgeBg = isAuto ? 'rgba(239, 68, 68, 0.15)' : 'rgba(16, 185, 129, 0.15)';
      const badgeBorder = isAuto ? '1px solid rgba(239, 68, 68, 0.4)' : '1px solid rgba(16, 185, 129, 0.4)';

      const valAuto = document.getElementById('val-auto');
      if (valAuto) valAuto.innerText = labelText;

      const setBadge = document.getElementById('settings-auto-badge');
      if (setBadge) {
        setBadge.innerText = badgeText;
        setBadge.style.color = badgeColor;
        setBadge.style.background = badgeBg;
        setBadge.style.borderColor = badgeBorder;
      }

      const setLabel = document.getElementById('settings-auto-label');
      if (setLabel) {
        setLabel.innerText = labelText;
        setLabel.style.color = isAuto ? 'var(--neon-amber)' : 'var(--neon-cyan)';
      }

      const btnToggle = document.getElementById('btn-toggle-auto');
      if (btnToggle) {
        btnToggle.innerHTML = isAuto
          ? '<i data-lucide="toggle-right" class="hud-icon-xs"></i> Disable Autonomy'
          : '<i data-lucide="toggle-left" class="hud-icon-xs"></i> Enable Autonomy';
      }
      renderIcons();
    }


    async function toggleAutonomousSetting() {
      const nextMode = !currentAutonomousMode;
      try {
        const res = await fetch('/api/settings/autonomous', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ autonomous_mode: nextMode })
        });
        const data = await res.json();
        syncAutonomousUI(data.autonomous_mode);
        appendLog('step', `🛡️ Security policy updated: Autonomous Mode set to ${data.label}.`);
      } catch (e) {
        console.error("Failed to toggle autonomous mode:", e);
      }
    }


    function promptClearAuditHistory() {
      const modal = document.getElementById('audit-clear-modal');
      if (modal) modal.classList.add('active');
    }


    function closeAuditClearModal() {
      const modal = document.getElementById('audit-clear-modal');
      if (modal) modal.classList.remove('active');
    }


    async function confirmClearAuditHistory() {
      const btn = document.getElementById('btn-confirm-audit-clear');
      if (btn) {
        btn.disabled = true;
        btn.innerText = 'Backing up & clearing...';
      }
      try {
        const res = await fetch('/api/history/clear', { method: 'POST' });
        const data = await res.json();
        closeAuditClearModal();
        appendLog('step', `🗑️ Audit history cleared (${data.cleared_runs} missions archived to ${data.backup_dir}).`);
        await loadHistory();
      } catch (e) {
        console.error("Failed to clear audit history:", e);
        alert("Failed to clear audit history: " + e.message);
      } finally {
        if (btn) {
          btn.disabled = false;
          btn.innerHTML = '<i data-lucide="trash-2" class="hud-icon-xs"></i> Confirm & Reset';
          renderIcons();
        }
      }
    }


    function showSettingsSection(secId, btn) {
      document.querySelectorAll('.settings-nav-btn').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.settings-section').forEach(s => s.classList.remove('active'));
      if (btn) {
        btn.classList.add('active');
      } else {
        const found = document.querySelector(`.settings-nav-btn[data-target="${secId}"]`);
        if (found) found.classList.add('active');
      }
      const target = document.getElementById('sec-settings-' + secId);
      if (target) target.classList.add('active');
      renderIcons();
    }


    let currentCloudModel = 'gemini-2.5-flash';


    function getPolicyLabel(policy) {
      if (policy === 'cloud_only') return 'CLOUD GEMINI 3.8 FLASH';
      if (policy === 'tier_fallback') return 'HYBRID (LOCAL + GEMINI)';
      return 'LOCAL LLM';
    }


    function syncPolicyUI(policy, cloudModel = null, logChange = false) {
      const policyChanged = (currentModelPolicy !== policy);
      currentModelPolicy = policy || currentModelPolicy;
      if (cloudModel) currentCloudModel = cloudModel;

      // Update Header segmented pills
      document.querySelectorAll('#backend-policy-segmented .mode-pill').forEach(btn => btn.classList.remove('active'));
      let activeHeaderBtn = null;
      if (currentModelPolicy === 'local_only') activeHeaderBtn = document.getElementById('btn-engine-local');
      else if (currentModelPolicy === 'cloud_only') activeHeaderBtn = document.getElementById('btn-engine-cloud');
      else if (currentModelPolicy === 'tier_fallback') activeHeaderBtn = document.getElementById('btn-engine-hybrid');
      if (activeHeaderBtn) activeHeaderBtn.classList.add('active');

      // Update Mission Control Header Badge
      const engineBadge = document.getElementById('current-engine-badge');
      const engineText = document.getElementById('current-engine-text');
      if (engineBadge && engineText) {
        if (currentModelPolicy === 'cloud_only') {
          engineText.innerText = 'GEMINI 3.8 FLASH';
          engineBadge.style.borderColor = 'var(--neon-cyan)';
          engineBadge.style.color = '#ffffff';
          engineBadge.style.background = 'rgba(0, 240, 255, 0.2)';
        } else if (currentModelPolicy === 'tier_fallback') {
          engineText.innerText = 'HYBRID FALLBACK';
          engineBadge.style.borderColor = '#cba6f7';
          engineBadge.style.color = '#cba6f7';
          engineBadge.style.background = 'rgba(203, 166, 247, 0.15)';
        } else {
          engineText.innerText = 'LOCAL LLM';
          engineBadge.style.borderColor = 'rgba(0, 240, 255, 0.4)';
          engineBadge.style.color = 'var(--neon-cyan)';
          engineBadge.style.background = 'rgba(0, 229, 255, 0.1)';
        }
      }

      // Update Tab 2 Model Selection Hero Switcher
      const activeBadge = document.getElementById('policy-active-badge');
      if (activeBadge) {
        activeBadge.innerText = (currentModelPolicy || 'LOCAL_ONLY').toUpperCase();
        if (currentModelPolicy === 'cloud_only') {
          activeBadge.style.borderColor = 'var(--neon-cyan)';
          activeBadge.style.color = 'var(--neon-cyan)';
        } else if (currentModelPolicy === 'tier_fallback') {
          activeBadge.style.borderColor = '#cba6f7';
          activeBadge.style.color = '#cba6f7';
        } else {
          activeBadge.style.borderColor = 'var(--neon-cyan)';
          activeBadge.style.color = 'var(--neon-cyan)';
        }
      }

      // Hero Cards
      ['local_only', 'cloud_only', 'tier_fallback'].forEach(p => {
        const card = document.getElementById('card-policy-' + p);
        if (card) {
          if (p === currentModelPolicy) card.classList.add('active');
          else card.classList.remove('active');
        }
      });

      const dotLocal = document.getElementById('dot-policy-local');
      const dotCloud = document.getElementById('dot-policy-cloud');
      const dotHybrid = document.getElementById('dot-policy-hybrid');
      if (dotLocal) dotLocal.className = 'status-dot ' + (currentModelPolicy === 'local_only' ? 'dot-green' : 'dot-gray');
      if (dotCloud) dotCloud.className = 'status-dot ' + (currentModelPolicy === 'cloud_only' ? 'dot-green' : 'dot-gray');
      if (dotHybrid) dotHybrid.className = 'status-dot ' + (currentModelPolicy === 'tier_fallback' ? 'dot-green' : 'dot-gray');

      // Update Cloud Model Select dropdown
      const selCloud = document.getElementById('sel-cloud-model');
      if (selCloud && currentCloudModel && selCloud.value !== currentCloudModel) {
        selCloud.value = currentCloudModel;
      }

      if (policyChanged && logChange) {
        appendLog('step', `🤖 AI Brain Engine: ${getPolicyLabel(currentModelPolicy)}`);
      }
      renderIcons();
    }


    async function setAIBackendPolicy(policy) {
      if (currentModelPolicy === policy) return;
      syncPolicyUI(policy, currentCloudModel, true);
      try {
        const selCloud = document.getElementById('sel-cloud-model');
        const cloudModel = selCloud ? selCloud.value : currentCloudModel;
        const res = await fetch('/api/models/policy', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ policy: policy, cloud_model: cloudModel })
        });
        const data = await res.json();
        if (data && data.policy) {
          syncPolicyUI(data.policy, data.cloud_model, false);
        }
      } catch (e) {
        console.warn("Failed to set AI backend policy:", e);
      }
    }


    function quickSetModelPolicy(policy) {
      setAIBackendPolicy(policy);
    }


    async function onCloudModelChange(modelId) {
      currentCloudModel = modelId;
      appendLog('step', `☁️ Cloud Model Target: ${modelId}`);
      if (currentModelPolicy === 'cloud_only' || currentModelPolicy === 'tier_fallback') {
        try {
          await fetch('/api/models/policy', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ policy: currentModelPolicy, cloud_model: modelId })
          });
        } catch (e) { }
      }
    }


    function toggleApiKeyVisibility() {
      const input = document.getElementById('input-gemini-api-key');
      if (input) {
        input.type = input.type === 'password' ? 'text' : 'password';
      }
    }


    async function loadModels() {
      try {
        const res = await fetch('/api/models');
        const data = await res.json();
        const selText = document.getElementById('sel-text-model');
        const selVision = document.getElementById('sel-vision-model');
        const selTier0 = document.getElementById('sel-tier0-model');
        const selCloud = document.getElementById('sel-cloud-model');
        const selTier0Device = document.getElementById('sel-tier0-device');

        if (selText && selVision && selTier0 && data.models) {
          selText.innerHTML = '';
          selVision.innerHTML = '';
          selTier0.innerHTML = '';

          data.models.forEach(m => {
            selText.add(new Option(`${m.name} (${m.size})`, m.name));
            selVision.add(new Option(`${m.name} (${m.size})`, m.name));
            selTier0.add(new Option(`${m.name} (${m.size})`, m.name));
          });

          if (data.current.local_text_model) selText.value = data.current.local_text_model;
          if (data.current.local_vision_model) selVision.value = data.current.local_vision_model;
          if (data.current.tier0_model) selTier0.value = data.current.tier0_model;
        }

        if (selTier0Device && data.current.tier0_device) {
          selTier0Device.value = data.current.tier0_device;
        }
        const kpiTier0 = document.getElementById('kpi-tier0-ratio');
        if (kpiTier0 && data.current.tier0_device) {
          kpiTier0.innerText = data.current.tier0_device === 'cpu' ? 'CPU (0 VRAM)' : 'GPU (CUDA)';
        }

        if (selCloud && data.cloud_models) {
          selCloud.innerHTML = '';
          data.cloud_models.forEach(cm => {
            const opt = new Option(cm.name, cm.id);
            selCloud.add(opt);
          });
          if (data.current.cloud_model) {
            selCloud.value = data.current.cloud_model;
            currentCloudModel = data.current.cloud_model;
          }
        }

        if (data.current && data.current.policy) {
          syncPolicyUI(data.current.policy, data.current.cloud_model, false);
        }

        const apiKeyInput = document.getElementById('input-gemini-api-key');
        if (apiKeyInput && data.current.has_gemini_api_key) {
          apiKeyInput.placeholder = '•••••••••••••••• (API Key Active)';
        }
      } catch (e) {
        console.warn("Failed to load models:", e);
      }
    }


    async function saveModelSelection() {
      const apiKeyInput = document.getElementById('input-gemini-api-key');
      const apiKeyVal = apiKeyInput ? apiKeyInput.value.trim() : '';
      const payload = {
        policy: currentModelPolicy,
        local_text_model: document.getElementById('sel-text-model') ? document.getElementById('sel-text-model').value : undefined,
        local_vision_model: document.getElementById('sel-vision-model') ? document.getElementById('sel-vision-model').value : undefined,
        tier0_model: document.getElementById('sel-tier0-model') ? document.getElementById('sel-tier0-model').value : undefined,
        tier0_device: document.getElementById('sel-tier0-device') ? document.getElementById('sel-tier0-device').value : undefined,
        cloud_model: document.getElementById('sel-cloud-model') ? document.getElementById('sel-cloud-model').value : currentCloudModel,
      };
      if (apiKeyVal) {
        payload.gemini_api_key = apiKeyVal;
      }
      try {
        const res = await fetch('/api/models/select', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });
        const data = await res.json();
        if (data.current && data.current.policy) {
          syncPolicyUI(data.current.policy, data.current.cloud_model, true);
        }
        if (apiKeyVal && apiKeyInput) {
          apiKeyInput.value = '';
          apiKeyInput.placeholder = '•••••••••••••••• (API Key Active)';
        }
        alert('AI Model & Routing configuration saved successfully!');
      } catch (e) {
        alert('Failed to save model configuration: ' + e);
      }
    }


    async function loadGatewayProviders() {
      const container = document.getElementById('gateway-providers-container');
      if (!container) return;
      try {
        const res = await fetch('/api/gateway/providers');
        const data = await res.json();
        cachedGatewayProviders = data.providers || [];
        renderGatewayProviders();
      } catch (e) {
        container.innerHTML = `<div style="color: var(--neon-red); padding: 1rem;">Failed to load Gateway: ${e}</div>`;
      }
    }


    function renderGatewayProviders() {
      const container = document.getElementById('gateway-providers-container');
      if (!container) return;
      if (!cachedGatewayProviders.length) {
        container.innerHTML = '<div style="color: var(--text-muted); padding: 1rem;">No enterprise providers configured.</div>';
        return;
      }

      container.innerHTML = cachedGatewayProviders.map(p => {
        const enabledClass = p.enabled ? 'enabled' : '';
        const badgeColor = p.healthy ? 'var(--neon-green)' : 'var(--neon-red)';
        const badgeText = p.circuit_open ? 'CIRCUIT TRIPPED' : (p.healthy ? 'HEALTHY' : 'DEGRADED');
        const pingText = p.last_ping_ms ? `${p.last_ping_ms}ms` : '-- ms';

        return `
          <div class="gateway-card ${enabledClass}">
            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
              <div>
                <div style="font-weight: 700; color: #ffffff; font-size: 0.88rem; display: flex; align-items: center; gap: 0.4rem;">
                  <i data-lucide="${p.is_local ? 'hard-drive' : 'cloud'}" class="hud-icon-xs text-cyan"></i> ${p.display_name}
                </div>
                <div style="font-size: 0.72rem; color: var(--text-muted); margin-top: 2px;">
                  Priority: <b style="color: var(--neon-cyan);">#${p.priority}</b> • Latency: <b style="color: #cbd5e1;">${pingText}</b> • Success: <b>${p.success_rate}%</b>
                </div>
              </div>
              <label class="handsfree-toggle" title="Enable or disable this LLM provider">
                <input type="checkbox" ${p.enabled ? 'checked' : ''} onchange="toggleGatewayProvider('${p.id}', this.checked)">
                <span class="toggle-slider"></span>
              </label>
            </div>

            <div style="display: flex; align-items: center; gap: 0.5rem; justify-content: space-between; font-size: 0.74rem;">
              <span class="badge" style="background: rgba(0,0,0,0.4); border: 1px solid ${badgeColor}; color: ${badgeColor}; font-size: 0.68rem;">● ${badgeText}</span>
              <span style="color: var(--text-muted); font-size: 0.7rem;">Reqs: <b>${p.total_requests}</b> | Errs: <b>${p.total_errors}</b></span>
            </div>

            <div style="display: flex; flex-direction: column; gap: 0.4rem;">
              <div style="display: flex; align-items: center; gap: 0.5rem;">
                <label style="font-size: 0.72rem; color: var(--text-muted); width: 60px;">Model:</label>
                <select id="gw-model-${p.id}" style="flex: 1; height: 26px; font-size: 0.74rem; padding: 0 0.4rem;" onchange="saveGatewayProviderConfig('${p.id}')">
                  ${p.available_models.map(m => `<option value="${m}" ${m === p.model ? 'selected' : ''}>${m}</option>`).join('')}
                </select>
              </div>

              ${!p.is_local ? `
                <div style="display: flex; align-items: center; gap: 0.5rem;">
                  <label style="font-size: 0.72rem; color: var(--text-muted); width: 60px;">API Key:</label>
                  <input type="password" id="gw-key-${p.id}" placeholder="${p.has_api_key ? '•••••••••••••••• (Active)' : 'Enter API Key...'}" style="flex: 1; height: 26px; font-size: 0.74rem; background: rgba(0,0,0,0.4); border: 1px solid rgba(255,255,255,0.1); border-radius: 4px; padding: 0 0.5rem; color: #ffffff;">
                  <button class="btn btn-sm" onclick="saveGatewayProviderConfig('${p.id}')" title="Save API Key to Linux Vault" style="font-size: 0.7rem; padding: 0.2rem 0.5rem;"><i data-lucide="save" class="hud-icon-xs"></i> Save</button>
                </div>
              ` : ''}
            </div>

            <div style="display: flex; justify-content: flex-end; gap: 0.5rem; margin-top: 0.2rem;">
              <button class="btn btn-outline btn-sm" onclick="testGatewayProvider('${p.id}')" id="btn-gw-test-${p.id}" style="font-size: 0.72rem; padding: 0.25rem 0.65rem;">
                <i data-lucide="activity" class="hud-icon-xs"></i> Test Ping
              </button>
            </div>
          </div>
        `;
      }).join('');
      if (window.lucide) lucide.createIcons();
    }


    async function toggleGatewayProvider(providerId, enabled) {
      try {
        await fetch('/api/gateway/providers/toggle', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ provider_id: providerId, enabled: enabled })
        });
        loadGatewayProviders();
      } catch (e) {
        alert("Failed to toggle provider: " + e);
      }
    }


    async function saveGatewayProviderConfig(providerId) {
      const modelElem = document.getElementById(`gw-model-${providerId}`);
      const keyElem = document.getElementById(`gw-key-${providerId}`);
      const payload = { provider_id: providerId };
      if (modelElem) payload.model = modelElem.value;
      if (keyElem && keyElem.value.trim()) payload.api_key = keyElem.value.trim();

      try {
        await fetch('/api/gateway/providers/config', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        if (keyElem && keyElem.value.trim()) {
          keyElem.value = '';
          keyElem.placeholder = '•••••••••••••••• (Active)';
        }
        loadGatewayProviders();
        alert(`Gateway provider '${providerId}' updated!`);
      } catch (e) {
        alert("Failed to save provider config: " + e);
      }
    }


    async function testGatewayProvider(providerId) {
      const btn = document.getElementById(`btn-gw-test-${providerId}`);
      if (btn) btn.innerText = 'Pinging...';
      try {
        const res = await fetch('/api/gateway/test', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ provider_id: providerId })
        });
        const data = await res.json();
        if (data.success) {
          alert(`✅ Provider '${providerId}' ping successful! Latency: ${data.latency_ms}ms (Model: ${data.model})`);
        } else {
          alert(`❌ Provider '${providerId}' test failed: ${data.error}`);
        }
        loadGatewayProviders();
      } catch (e) {
        alert("Ping error: " + e);
      } finally {
        if (btn) btn.innerHTML = '<i data-lucide="activity" class="hud-icon-xs"></i> Test Ping';
        if (window.lucide) lucide.createIcons();
      }
    }


    async function loadDailyBriefConfig() {
      try {
        const res = await fetch('/api/brief/config');
        cachedBriefConfig = await res.json();
        renderDailyBriefConfig();
      } catch (e) {
        console.warn("Failed to load daily brief config:", e);
      }
    }


    function renderDailyBriefConfig() {
      if (!cachedBriefConfig) return;
      const cityInput = document.getElementById('brief-city-input');
      if (cityInput && cachedBriefConfig.city) {
        cityInput.value = cachedBriefConfig.city;
      }
      const listContainer = document.getElementById('brief-topics-list');
      if (!listContainer) return;

      let totalWeight = 0;
      listContainer.innerHTML = (cachedBriefConfig.topics || []).map((t, idx) => {
        if (t.enabled) totalWeight += Number(t.weight_pct);
        return `
          <div class="brief-topic-row">
            <div style="display: flex; align-items: center; gap: 0.6rem; min-width: 220px;">
              <input type="checkbox" ${t.enabled ? 'checked' : ''} onchange="toggleBriefTopic(${idx}, this.checked)">
              <div>
                <div style="font-size: 0.82rem; font-weight: 700; color: #ffffff;">${t.name}</div>
                <div style="font-size: 0.7rem; color: var(--text-muted);">${t.genre_or_query || 'Default feed'} • ${t.timeframe}</div>
              </div>
            </div>

            <div style="display: flex; align-items: center; gap: 0.75rem; flex: 1; max-width: 450px;">
              <span style="font-size: 0.72rem; color: var(--text-muted); width: 85px;">Focus Weight:</span>
              <input type="range" class="brief-slider" min="0" max="100" step="5" value="${t.weight_pct}" oninput="onBriefSliderInput(${idx}, this.value)" onchange="onBriefSliderChange(${idx}, this.value)">
              <span id="brief-topic-pct-${idx}" style="font-family: 'JetBrains Mono', monospace; font-size: 0.78rem; font-weight: 700; color: var(--neon-cyan); width: 40px; text-align: right;">${t.weight_pct}%</span>
            </div>
          </div>
        `;
      }).join('');

      const totalElem = document.getElementById('brief-total-weight');
      if (totalElem) {
        totalElem.innerText = `${totalWeight}%`;
        totalElem.style.color = (totalWeight === 100) ? 'var(--neon-green)' : 'var(--neon-amber)';
      }
    }


    function toggleBriefTopic(idx, enabled) {
      if (cachedBriefConfig && cachedBriefConfig.topics[idx]) {
        cachedBriefConfig.topics[idx].enabled = enabled;
        renderDailyBriefConfig();
      }
    }


    function onBriefSliderInput(idx, val) {
      const span = document.getElementById(`brief-topic-pct-${idx}`);
      if (span) span.innerText = `${val}%`;
      if (cachedBriefConfig && cachedBriefConfig.topics[idx]) {
        cachedBriefConfig.topics[idx].weight_pct = parseInt(val);
      }
      let sum = 0;
      cachedBriefConfig.topics.forEach(t => { if (t.enabled) sum += Number(t.weight_pct); });
      const totalElem = document.getElementById('brief-total-weight');
      if (totalElem) {
        totalElem.innerText = `${sum}%`;
        totalElem.style.color = (sum === 100) ? 'var(--neon-green)' : 'var(--neon-amber)';
      }
    }


    function onBriefSliderChange(idx, val) {
      onBriefSliderInput(idx, val);
    }


    async function saveDailyBriefConfig() {
      if (!cachedBriefConfig) return;
      const cityInput = document.getElementById('brief-city-input');
      if (cityInput) cachedBriefConfig.city = cityInput.value.trim() || 'Bangalore';

      try {
        const res = await fetch('/api/brief/config', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(cachedBriefConfig)
        });
        const data = await res.json();
        alert("Daily Brief configuration saved successfully!");
      } catch (e) {
        alert("Failed to save Daily Brief configuration: " + e);
      }
    }


    async function previewDailyBrief() {
      try {
        const res = await fetch('/api/brief/preview');
        const data = await res.json();
        openContextualExplanation(
          `☀️ Daily Brief Preview // ${data.city}`,
          `graph TD\n  A[☀️ Daily Briefing] --> B[⛅ Weather: ${data.city}]\n  A --> C[📅 Calendar Agenda]\n  A --> D[💻 Tech & AI News]\n  A --> E[🌐 World Headlines]\n  A --> F[⚡ Workstation Status]`,
          data.spoken_text
        );
      } catch (e) {
        alert("Failed to preview daily brief: " + e);
      }
    }


    async function loadBriefSlots() {
      try {
        const res = await fetch('/api/brief/slots');
        const data = await res.json();
        briefSlotsData = data.slots || [];
        renderBriefSlots();
      } catch (e) {
        console.warn('Brief slots load failed:', e);
        briefSlotsData = [];
        renderBriefSlots();
      }
    }


    function renderBriefSlots() {
      const container = document.getElementById('brief-slots-list');
      if (!container) return;
      if (!briefSlotsData.length) {
        container.innerHTML = '<div style="color: var(--text-muted); font-size: 0.8rem; padding: 0.5rem;">No scheduled slots. Click "Add Slot" to create one.</div>';
        return;
      }
      container.innerHTML = briefSlotsData.map((slot, i) => `
        <div style="background: rgba(3,8,18,0.75); border: 1px solid ${slot.enabled ? 'rgba(0,240,255,0.2)' : 'rgba(255,255,255,0.08)'}; border-radius: 8px; padding: 0.85rem 1rem; display: flex; flex-wrap: wrap; gap: 0.75rem; align-items: center;">
          <!-- Enable toggle -->
          <label style="display: flex; align-items: center; gap: 0.4rem; cursor: pointer; flex-shrink: 0;">
            <input type="checkbox" ${slot.enabled ? 'checked' : ''} onchange="briefSlotsData[${i}].enabled=this.checked; renderBriefSlots()" style="accent-color: var(--neon-cyan);">
            <span style="font-size: 0.75rem; color: ${slot.enabled ? 'var(--neon-cyan)' : 'var(--text-muted)'}; font-weight: 700;">${slot.enabled ? 'ENABLED' : 'DISABLED'}</span>
          </label>

          <!-- Time picker -->
          <div style="display: flex; align-items: center; gap: 0.4rem;">
            <i data-lucide="clock" class="hud-icon-xs text-amber"></i>
            <input type="time" value="${slot.time}" onchange="briefSlotsData[${i}].time=this.value" style="background: rgba(6,12,26,0.9); color: #ffffff; border: 1px solid rgba(255,171,0,0.3); border-radius: 6px; padding: 0.25rem 0.5rem; font-family: 'JetBrains Mono', monospace; font-size: 0.8rem;">
          </div>

          <!-- Label -->
          <input type="text" placeholder="Label (e.g. Morning Brief)" value="${escapeHtml(slot.label || '')}" oninput="briefSlotsData[${i}].label=this.value" style="background: rgba(6,12,26,0.9); color: #ffffff; border: 1px solid rgba(255,255,255,0.12); border-radius: 6px; padding: 0.25rem 0.6rem; font-size: 0.78rem; width: 170px;">

          <!-- Topics -->
          <div style="display: flex; flex-wrap: wrap; gap: 0.3rem;">
            ${TOPIC_OPTIONS.map(t => `
              <label style="display: flex; align-items: center; gap: 0.25rem; cursor: pointer;">
                <input type="checkbox" ${(slot.topics || []).includes(t) ? 'checked' : ''} onchange="toggleSlotTopic(${i},'${t}',this.checked)" style="accent-color: var(--neon-cyan);">
                <span style="font-size: 0.7rem; color: var(--text-muted); font-family: 'JetBrains Mono', monospace;">${t}</span>
              </label>
            `).join('')}
          </div>

          <!-- Actions -->
          <div style="display: flex; gap: 0.4rem; margin-left: auto;">
            <button class="btn btn-sm" style="background: rgba(0,240,255,0.1); border: 1px solid rgba(0,240,255,0.2); color: var(--neon-cyan); font-size: 0.7rem;" onclick="previewSlotBrief(${i})" title="Test this slot now"><i data-lucide="play" class="hud-icon-xs"></i></button>
            <button class="btn btn-sm" style="background: rgba(255,0,80,0.12); border: 1px solid rgba(255,0,80,0.25); color: #ff3860; font-size: 0.7rem;" onclick="removeBriefSlot(${i})" title="Remove slot"><i data-lucide="trash-2" class="hud-icon-xs"></i></button>
          </div>
        </div>
      `).join('');
      lucide.createIcons();
    }


    function toggleSlotTopic(slotIdx, topic, enabled) {
      const topics = briefSlotsData[slotIdx].topics || [];
      if (enabled && !topics.includes(topic)) topics.push(topic);
      if (!enabled) briefSlotsData[slotIdx].topics = topics.filter(t => t !== topic);
      else briefSlotsData[slotIdx].topics = topics;
    }


    function addBriefSlot() {
      briefSlotsData.push({ time: '08:00', enabled: true, label: '', topics: ['weather', 'calendar'] });
      renderBriefSlots();
    }


    function removeBriefSlot(idx) {
      briefSlotsData.splice(idx, 1);
      renderBriefSlots();
    }


    async function saveBriefSlots() {
      try {
        const res = await fetch('/api/brief/slots', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ slots: briefSlotsData })
        });
        const data = await res.json();
        briefSlotsData = data.slots || briefSlotsData;
        renderBriefSlots();
        appendLog('step', '☀️ Brief schedule slots saved.');
      } catch (e) {
        appendLog('step', '❌ Failed to save brief slots: ' + e.message);
      }
    }


    async function previewSlotBrief(slotIdx) {
      const slot = briefSlotsData[slotIdx];
      if (!slot) return;
      try {
        const res = await fetch('/api/brief/trigger-slot', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ topic_ids: slot.topics })
        });
        const data = await res.json();
        appendLog('step', `☀️ Slot brief delivered: ${(data.briefing || '').substring(0, 80)}...`);
      } catch (e) {
        appendLog('step', '❌ Slot preview failed: ' + e.message);
      }
    }


    async function setupUbuntuShortcut() {
      const btn = document.getElementById('btn-setup-shortcut');
      if (btn) btn.innerHTML = '<i data-lucide="loader" class="hud-icon-xs spin"></i> Configuring...';
      try {
        const res = await fetch('/api/system/setup-shortcut', { method: 'POST' });
        const data = await res.json();
        if (data.status === 'success') {
          playTacticalSfx('success');
          appendLog('result', '⌨️ Ubuntu GNOME shortcut Super+Shift+J registered for Bro Voice HUD.');
          alert("Success! Ubuntu shortcut registered.\n\nPress Super+Shift+J anywhere on your desktop to summon Bro with auto-greeting in hands-free voice loop.");
        } else {
          appendLog('warning', 'Shortcut configuration output: ' + (data.output || data.message));
          alert("Shortcut setup output:\n" + (data.output || data.message));
        }
      } catch (e) {
        console.error("Failed to setup Ubuntu shortcut:", e);
        alert("Failed to configure shortcut: " + e.message);
      } finally {
        if (btn) {
          btn.innerHTML = '<i data-lucide="command" class="hud-icon-xs"></i> Ubuntu Shortcut (Super+Shift+J)';
          renderIcons();
        }
      }
    }
