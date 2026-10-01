// =========================================================================
// BRO TABS ENGINE
// =========================================================================

    function showManualSection(secId, btn) {
      document.querySelectorAll('.manual-nav-btn').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.manual-section').forEach(s => s.classList.remove('active'));
      if (btn) btn.classList.add('active');
      const target = document.getElementById('sec-' + secId);
      if (target) target.classList.add('active');
    }


    async function loadDesktopMonitors(forceRefresh = false) {
      try {
        const res = await fetch('/api/desktop/monitors');
        const data = await res.json();
        detectedMonitors = data.monitors || [];
        currentMainScreenIndex = (typeof data.current_screen_index === 'number') ? data.current_screen_index : 1;

        // 1. Update dropdown in Header and Settings
        ['desktop-select-dropdown', 'settings-desktop-select'].forEach(id => {
          const dropdown = document.getElementById(id);
          if (dropdown) {
            dropdown.innerHTML = '';
            detectedMonitors.forEach(m => {
              const opt = document.createElement('option');
              opt.value = m.index;
              opt.innerText = m.label;
              if (m.index === currentMainScreenIndex) opt.selected = true;
              dropdown.appendChild(opt);
            });
          }
        });

        // 2. Render Cards in Main Desktop Tab if present
        const container = document.getElementById('display-cards-container');
        if (container) {
          container.innerHTML = '';
          detectedMonitors.forEach(m => {
            const isCurrent = (m.index === currentMainScreenIndex);
            const card = document.createElement('div');
            card.className = 'display-card' + (isCurrent ? ' active-desktop' : '');

            const badgeText = m.is_primary ? 'PRIMARY DISPLAY' : (m.index === 0 ? 'ALL DISPLAYS COMBINED' : 'SECONDARY DISPLAY');
            const badgeColor = isCurrent ? 'var(--neon-cyan)' : 'var(--text-muted)';
            const borderGlow = isCurrent ? 'border: 1px solid var(--neon-cyan);' : '';
            const previewUrl = `/api/desktop/preview?screen_index=${m.index}&t=${Date.now()}`;

            card.innerHTML = `
              <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                <div>
                  <div style="font-weight: 700; color: #ffffff; font-size: 0.95rem; display: flex; align-items: center; gap: 0.4rem;">
                    <i data-lucide="monitor" class="hud-icon-sm text-cyan"></i> ${m.name}
                  </div>
                  <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; color: var(--neon-cyan); margin-top: 0.2rem;">
                    Output: <b>${m.output}</b> • Resolution: <b>${m.width}×${m.height}</b>
                  </div>
                  <div style="font-size: 0.72rem; color: var(--text-muted);">
                    Offset: +${m.left}+${m.top}
                  </div>
                </div>
                <span style="font-size: 0.68rem; padding: 0.2rem 0.5rem; border-radius: 4px; font-weight: bold; background: rgba(0,0,0,0.4); color: ${badgeColor}; ${borderGlow}">
                  ${badgeText}
                </span>
              </div>

              <!-- Live Preview Thumbnail -->
              <div style="position: relative; margin: 0.4rem 0;">
                <img src="${previewUrl}" class="display-preview-thumbnail" alt="${m.label}" onclick="openLightbox('${previewUrl}', '${m.label}')" title="Click to view full 1080p resolution in Lightbox">
                <span style="position: absolute; bottom: 6px; right: 6px; background: rgba(0,0,0,0.75); color: var(--neon-cyan); font-size: 0.68rem; padding: 0.15rem 0.4rem; border-radius: 4px; pointer-events: none; display: inline-flex; align-items: center; gap: 0.25rem;"><i data-lucide="zoom-in" class="hud-icon-xs"></i> Zoom</span>
              </div>

              <!-- Action Bar -->
              <div style="display: flex; justify-content: space-between; align-items: center; margin-top: auto;">
                ${isCurrent ?
                `<span style="color: var(--neon-cyan); font-size: 0.8rem; font-weight: bold; display: flex; align-items: center; gap: 0.35rem;"><i data-lucide="check-circle" class="hud-icon-sm text-cyan"></i> CURRENT MAIN DESKTOP</span>` :
                `<button class="btn btn-cyan" style="font-size: 0.78rem; padding: 0.4rem 0.85rem;" onclick="changeMainDesktop(${m.index})"><i data-lucide="check" class="hud-icon-xs"></i> Set as Main Desktop</button>`
              }
                <button class="btn" style="background: rgba(255,255,255,0.08); font-size: 0.75rem; padding: 0.4rem 0.75rem;" onclick="openLightbox('${previewUrl}', '${m.label}')"><i data-lucide="maximize-2" class="hud-icon-xs"></i> Fullscreen</button>
              </div>
            `;
            container.appendChild(card);
          });
          renderIcons();
        }

        // 3. Update live perception viewer
        const activeMon = detectedMonitors.find(m => m.index === currentMainScreenIndex) || detectedMonitors[0];
        if (activeMon) {
          const t = document.getElementById('active-desktop-title');
          const st = document.getElementById('active-desktop-subtitle');
          if (t) t.innerText = `Active Main Desktop: Display ${activeMon.index} (${activeMon.output} - ${activeMon.width}×${activeMon.height})`;
          if (st) st.innerText = `Bro perception grounded at physical coordinates (+${activeMon.left}, +${activeMon.top})`;
        }
      } catch (e) {
        console.error("Failed to load desktop monitors:", e);
      }
    }


    async function changeMainDesktop(screenIndex) {
      try {
        const res = await fetch('/api/desktop/select', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ screen_index: screenIndex })
        });
        const data = await res.json();
        currentMainScreenIndex = data.screen_index;
        await loadDesktopMonitors();
        refreshActivePreview();
        appendLog('step', `🖥️ Main Desktop perception switched to Display ${screenIndex}.`);
      } catch (e) {
        alert("Failed to change desktop: " + e);
      }
    }


    function refreshActivePreview() {
      const img = document.getElementById('active-desktop-live-img');
      if (img) {
        img.src = `/api/desktop/preview?screen_index=${currentMainScreenIndex}&t=${Date.now()}`;
      }
    }


    function previewActiveDesktop() {
      const previewUrl = `/api/desktop/preview?screen_index=${currentMainScreenIndex}&full=1&t=${Date.now()}`;
      openLightbox(previewUrl, `Main Desktop Display ${currentMainScreenIndex} Perception Preview`);
    }


    async function loadErrors() {
      const container = document.getElementById('errors-container');
      try {
        const res = await fetch('/api/errors');
        const errs = await res.json();
        const badge = document.getElementById('error-badge');
        if (errs.length) {
          badge.style.display = 'inline';
          badge.innerText = errs.length;
          container.innerHTML = '';
          errs.forEach(e => {
            const div = document.createElement('div');
            div.className = 'error-card';
            div.innerHTML = `
              <div class="error-header">
                <span>[${e.error_type}] ${e.time_str}</span>
              </div>
              <div style="font-weight: 600; color: #ffffff; font-size: 0.9rem;">${e.message}</div>
              ${e.context ? `<div style="font-size: 0.8rem; color: var(--text-muted); margin-top: 0.25rem;">Context: ${e.context}</div>` : ''}
              ${e.stack_trace ? `<pre style="font-size: 0.75rem; color: #fab387; margin-top: 0.5rem; overflow-x: auto;">${e.stack_trace.substring(0, 400)}</pre>` : ''}
            `;
            container.appendChild(div);
          });
        } else {
          badge.style.display = 'none';
          container.innerHTML = '<p style="color: var(--text-muted);">No system errors currently logged. System operational.</p>';
        }
      } catch (e) { }
    }


    async function clearErrors() {
      await fetch('/api/errors/clear', { method: 'POST' });
      loadErrors();
    }


    function filterHistoryByActuator(key) {
      const search = document.getElementById('history-search');
      if (search) {
        search.value = key;
        filterHistoryList();
      }
      showToast(`Filtered missions by actuator: ${key}`, 'info');
    }


    function renderActuatorDonut(breakdown, percentages) {
      const svg = document.getElementById('donut-svg');
      const legend = document.getElementById('donut-legend');
      if (!svg || !legend) return;

      const colors = {
        desktop: '#00e5ff',
        browser: '#2979ff',
        python: '#00e676',
        shell: '#ffab00',
        macro: '#b388ff',
        other: '#8492a6'
      };

      const labels = {
        desktop: 'Desktop GUI',
        browser: 'Browser Web',
        python: 'Python Data',
        shell: 'Shell Bash',
        macro: 'Compiled Macro',
        other: 'System/Other'
      };

      const total = Object.values(breakdown || {}).reduce((a, b) => a + b, 0);

      svg.innerHTML = '';
      legend.innerHTML = '';

      if (total === 0) {
        svg.innerHTML = `
          <circle cx="90" cy="90" r="68" fill="none" stroke="rgba(255,255,255,0.08)" stroke-width="22"/>
          <text x="90" y="95" text-anchor="middle" fill="#8492a6" font-size="12" font-family="Inter">No Actions</text>
        `;
        legend.innerHTML = '<span style="color: var(--text-muted);">Execute missions to populate distribution.</span>';
        return;
      }

      const radius = 68;
      const circumference = 2 * Math.PI * radius;
      let offset = 0;
      let circlesHtml = '';

      for (const [key, val] of Object.entries(breakdown || {})) {
        if (val <= 0) continue;
        const pct = val / total;
        const dash = pct * circumference;
        const color = colors[key] || '#8492a6';

        circlesHtml += `
          <circle cx="90" cy="90" r="${radius}" fill="none" stroke="${color}" stroke-width="22"
            stroke-dasharray="${dash} ${circumference}"
            stroke-dashoffset="${-offset}"
            transform="rotate(-90 90 90)"
            style="cursor: pointer; transition: stroke-width 0.2s, opacity 0.2s;"
            onmouseover="this.setAttribute('stroke-width', '26'); this.style.filter='drop-shadow(0 0 8px ${color})';"
            onmouseout="this.setAttribute('stroke-width', '22'); this.style.filter='none';"
            onclick="filterHistoryByActuator('${key}')"
          >
            <title>Click to filter: ${labels[key] || key} - ${val} actions (${Math.round(pct * 100)}%)</title>
          </circle>
        `;
        offset += dash;

        const legItem = document.createElement('div');
        legItem.className = 'legend-item';
        legItem.style.cursor = 'pointer';
        legItem.style.padding = '3px 6px';
        legItem.style.borderRadius = '4px';
        legItem.style.transition = 'background 0.2s';
        legItem.onmouseover = () => { legItem.style.background = 'rgba(255,255,255,0.08)'; };
        legItem.onmouseout = () => { legItem.style.background = 'transparent'; };
        legItem.onclick = () => filterHistoryByActuator(key);
        legItem.innerHTML = `
          <div class="legend-color" style="background: ${color};"></div>
          <span>${labels[key] || key}: <b>${val}</b> (${Math.round(pct * 100)}%)</span>
        `;
        legend.appendChild(legItem);
      }

      circlesHtml += `
        <text x="90" y="86" text-anchor="middle" fill="#ffffff" font-size="18" font-weight="700" font-family="Inter">${total}</text>
        <text x="90" y="103" text-anchor="middle" fill="#8492a6" font-size="9" font-family="Inter">ACTIONS</text>
      `;

      svg.innerHTML = circlesHtml;
    }


    function renderVelocityChart(recentTimeline) {
      const svg = document.getElementById('velocity-svg');
      if (!svg) return;
      if (!recentTimeline || !recentTimeline.length) {
        svg.innerHTML = '<text x="50%" y="60" text-anchor="middle" fill="#8492a6" font-size="11" font-family="Inter">Awaiting mission runs...</text>';
        return;
      }

      const items = recentTimeline.slice(0, 10).reverse(); // chronological order
      const maxDur = Math.max(...items.map(i => i.duration_sec), 1);
      const width = svg.clientWidth || 360;
      const height = 90;
      const barWidth = Math.max(16, Math.floor((width - (items.length * 8) - 30) / items.length));

      let svgHtml = '';
      items.forEach((item, idx) => {
        const barH = Math.max(8, Math.round((item.duration_sec / maxDur) * (height - 30)));
        const x = 16 + (idx * (barWidth + 8));
        const y = height - barH - 18;
        const color = item.status === 'success' ? 'var(--neon-green)' : 'var(--neon-red)';
        const runId = item.run_id || '';

        svgHtml += `
          <g style="cursor: pointer;" onclick="if ('${runId}') { selectRun('${runId}'); showToast('Mission ${runId.slice(0, 8)} selected', 'info'); }">
            <rect x="${x}" y="${y}" width="${barWidth}" height="${barH}" rx="3" fill="${color}" opacity="0.85"
              style="transition: opacity 0.2s, transform 0.2s;"
              onmouseover="this.setAttribute('opacity', '1.0'); this.style.filter='drop-shadow(0 0 6px ${color})';"
              onmouseout="this.setAttribute('opacity', '0.85'); this.style.filter='none';"
            >
              <title>Mission #${idx + 1} [${item.status.toUpperCase()}]\nGoal: ${item.goal}\nDuration: ${item.duration_sec}s (${item.step_count || 0} steps)\nClick to inspect filmstrip details</title>
            </rect>
            <text x="${x + barWidth / 2}" y="${y - 4}" text-anchor="middle" fill="#8492a6" font-size="9" font-family="JetBrains Mono">${item.duration_sec}s</text>
            <text x="${x + barWidth / 2}" y="${height - 4}" text-anchor="middle" fill="#8492a6" font-size="9" font-family="JetBrains Mono">#${idx + 1}</text>
          </g>
        `;
      });

      svg.innerHTML = svgHtml;
    }


    function setHistoryFilter(filter, elem) {
      activeFilter = filter;
      document.querySelectorAll('.filter-pill').forEach(p => p.classList.remove('active'));
      if (elem) elem.classList.add('active');
      renderFilteredHistory();
    }


    function filterHistoryList() {
      renderFilteredHistory();
    }


    function renderFilteredHistory() {
      const container = document.getElementById('history-items');
      const query = (document.getElementById('history-search')?.value || '').toLowerCase().trim();

      const filtered = cachedRuns.filter(r => {
        const matchesFilter = (activeFilter === 'all') ||
          (activeFilter === 'success' && r.status === 'success') ||
          (activeFilter === 'failed' && (r.status === 'failed' || r.status === 'timeout'));
        const matchesQuery = !query || (r.goal || '').toLowerCase().includes(query);
        return matchesFilter && matchesQuery;
      });

      if (!filtered.length) {
        container.innerHTML = '<p style="color: var(--text-muted); padding: 1rem;">No matching missions found.</p>';
        return;
      }

      container.innerHTML = '';
      filtered.forEach((r, idx) => {
        const div = document.createElement('div');
        div.className = 'history-item' + (r.run_id === selectedRunId ? ' selected' : '');
        const dur = (r.start_time && r.end_time) ? `${Math.round(r.end_time - r.start_time)}s` : '';
        div.innerHTML = `
          <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 0.5rem;">
            <div style="font-weight: 700; font-size: 0.85rem; color: var(--neon-cyan); line-height: 1.3;">${r.goal.substring(0, 36)}...</div>
            <div style="display: flex; gap: 0.3rem; flex-shrink: 0;">
              <button class="btn btn-sm" style="background: rgba(255,171,0,0.12); color: var(--neon-amber); border: 1px solid rgba(255,171,0,0.3); font-size: 0.68rem; padding: 0.15rem 0.45rem;" onclick="event.stopPropagation(); openTimingModal('${r.run_id}')" title="Timing debug waterfall"><i data-lucide="timer" class="hud-icon-xs"></i></button>
              <button class="btn btn-sm" style="background: rgba(0, 240, 255, 0.12); color: var(--neon-cyan); border: 1px solid rgba(0, 240, 255, 0.3); font-size: 0.68rem; padding: 0.15rem 0.45rem;" onclick="event.stopPropagation(); downloadMissionReport('${r.run_id}', 'md')" title="Download Markdown report"><i data-lucide="download" class="hud-icon-xs"></i> .md</button>
            </div>
          </div>
          <div style="font-size: 0.75rem; color: var(--text-muted); margin-top: 0.3rem;">
            Status: <b style="color: ${r.status === 'success' ? 'var(--neon-green)' : 'var(--neon-red)'};">${r.status.toUpperCase()}</b> • Steps: ${r.steps ? r.steps.length : 0} ${dur ? '• ' + dur : ''}
          </div>
        `;
        div.onclick = () => selectRun(r.run_id, div);
        container.appendChild(div);
        if (idx === 0 && !selectedRunId) selectRun(r.run_id, div);
      });
    }


    function downloadMissionReport(runId = null, format = 'md') {
      const targetRunId = runId || selectedRunId || (cachedRuns && cachedRuns.length ? cachedRuns[0].run_id : null);
      if (!targetRunId) {
        alert("No mission selected to download. Please select a mission from the list.");
        return;
      }

      // Method: Direct browser download via server attachment endpoint.
      // 100% reliable across all browsers & mobile devices, avoids blob revocation issues,
      // and provides clean OS file naming.
      const downloadUrl = `/api/history/${encodeURIComponent(targetRunId)}/download?format=${encodeURIComponent(format)}`;
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.setAttribute('download', '');
      link.style.display = 'none';
      document.body.appendChild(link);
      link.click();

      setTimeout(() => {
        if (link.parentNode) link.parentNode.removeChild(link);
      }, 1500);

      appendLog('step', `📥 Downloaded mission report (${format.toUpperCase()}) for: ${targetRunId}`);
    }


    function exportCurrentRunMarkdown(runId = null) {
      downloadMissionReport(runId, 'md');
    }


    async function openTimingModal(runId) {
      document.getElementById('timing-debug-modal').style.display = 'flex';
      document.getElementById('timing-modal-subtitle').textContent = `Run: ${runId}`;
      const stepsEl = document.getElementById('timing-modal-steps');
      stepsEl.innerHTML = '<div style="color: var(--text-muted); text-align: center; padding: 2rem;">Loading...</div>';
      document.getElementById('timing-context-panel').style.display = 'none';

      try {
        const res = await fetch('/api/history/' + encodeURIComponent(runId));
        if (!res.ok) throw new Error('Not found');
        const run = await res.json();

        const steps = run.steps || [];
        if (!steps.length) {
          stepsEl.innerHTML = '<div style="color: var(--text-muted); text-align: center; padding: 2rem;">No execution steps recorded for this run.</div>';
          return;
        }

        // Find max duration for bar scaling
        const maxDur = Math.max(...steps.map(s => s.duration_ms || 0), 1);

        let html = `<div style="font-size: 0.75rem; color: var(--text-muted); margin-bottom: 1rem; font-family: 'JetBrains Mono', monospace;">Goal: ${escapeHtml(run.goal)}</div>`;

        steps.forEach(s => {
          const durMs = s.duration_ms || 0;
          const llmMs = s.llm_ms || 0;
          const toolMs = s.tool_ms || 0;
          const durSec = durMs / 1000;
          const barColor = durSec < 1 ? 'var(--neon-green)' : (durSec < 5 ? 'var(--neon-amber)' : '#ff3860)');
          const llmWidth = maxDur > 0 ? Math.min(100, (llmMs / maxDur) * 100) : 0;
          const toolWidth = maxDur > 0 ? Math.min(100, (toolMs / maxDur) * 100) : 0;
          const totalWidth = maxDur > 0 ? Math.min(100, (durMs / maxDur) * 100) : 0;

          html += `
            <div style="background: rgba(3,8,18,0.75); border: 1px solid rgba(0,240,255,0.12); border-radius: 8px; padding: 0.85rem 1rem; margin-bottom: 0.75rem;">
              <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.6rem;">
                <div style="display: flex; align-items: center; gap: 0.5rem;">
                  <span style="font-family: 'JetBrains Mono', monospace; font-size: 0.7rem; color: var(--neon-cyan);">STEP ${s.step_num}</span>
                  <span style="font-family: 'JetBrains Mono', monospace; font-weight: 700; font-size: 0.82rem; color: #ffffff;">${escapeHtml(s.action)}</span>
                  <span style="font-size: 0.65rem; font-family: 'JetBrains Mono', monospace; border: 1px solid ${s.success ? 'var(--neon-green)' : '#ff3860'}; color: ${s.success ? 'var(--neon-green)' : '#ff3860'}; padding: 0.1rem 0.4rem; border-radius: 4px;">${s.success ? 'OK' : 'FAIL'}</span>
                </div>
                <span style="font-family: 'JetBrains Mono', monospace; font-size: 0.8rem; font-weight: 700; color: ${barColor}">${durMs ? durMs.toFixed(0) + ' ms' : 'N/A'}</span>
              </div>

              ${llmMs ? `
              <div style="margin-bottom: 0.4rem;">
                <div style="display: flex; justify-content: space-between; font-size: 0.68rem; color: var(--text-muted); margin-bottom: 0.2rem;">
                  <span>🧠 LLM Round-trip</span><span style="font-family: 'JetBrains Mono', monospace;">${llmMs.toFixed(0)} ms</span>
                </div>
                <div style="background: rgba(255,255,255,0.08); border-radius: 4px; height: 6px; overflow: hidden;">
                  <div style="height: 100%; width: ${llmWidth}%; background: linear-gradient(90deg, #00f0ff, #0080ff); border-radius: 4px; transition: width 0.5s ease;"></div>
                </div>
              </div>` : ''}

              ${toolMs ? `
              <div style="margin-bottom: 0.4rem;">
                <div style="display: flex; justify-content: space-between; font-size: 0.68rem; color: var(--text-muted); margin-bottom: 0.2rem;">
                  <span>🔧 Tool Execution</span><span style="font-family: 'JetBrains Mono', monospace;">${toolMs.toFixed(0)} ms</span>
                </div>
                <div style="background: rgba(255,255,255,0.08); border-radius: 4px; height: 6px; overflow: hidden;">
                  <div style="height: 100%; width: ${toolWidth}%; background: linear-gradient(90deg, #00ff9d, #00b56e); border-radius: 4px; transition: width 0.5s ease;"></div>
                </div>
              </div>` : ''}

              <div>
                <div style="display: flex; justify-content: space-between; font-size: 0.68rem; color: var(--text-muted); margin-bottom: 0.2rem;">
                  <span>⏱ Total Step</span><span style="font-family: 'JetBrains Mono', monospace; color: ${barColor};">${durMs ? durMs.toFixed(0) + ' ms' : 'N/A'}</span>
                </div>
                <div style="background: rgba(255,255,255,0.08); border-radius: 4px; height: 8px; overflow: hidden;">
                  <div style="height: 100%; width: ${totalWidth}%; background: ${barColor}; border-radius: 4px; opacity: 0.7; transition: width 0.5s ease;"></div>
                </div>
              </div>

              <div style="font-size: 0.68rem; color: var(--text-muted); margin-top: 0.55rem; font-style: italic; border-top: 1px solid rgba(255,255,255,0.06); padding-top: 0.4rem;">${escapeHtml((s.thought || '').substring(0, 100))}${(s.thought || '').length > 100 ? '...' : ''}</div>
            </div>
          `;
        });

        stepsEl.innerHTML = html;

        // Context audit panel
        const contextInfo = `Goal: ${run.goal}\n\nSteps: ${steps.length}\nStatus: ${run.status}\n\nSystem prompt: (see SYSTEM_PROMPT in agent.py)\nMessages sent to LLM: ${steps.length * 2 + 1} approximate (system + alternating user/assistant turns)\n\nNOTE: Bro uses local Ollama models by default. Cloud routing depends on Gateway config.`;
        document.getElementById('timing-context-content').textContent = contextInfo;

        lucide.createIcons();
      } catch (e) {
        stepsEl.innerHTML = `<div style="color: #ff3860; text-align: center; padding: 2rem;">Failed to load run data: ${e.message}</div>`;
      }
    }


    function closeTimingModal() {
      document.getElementById('timing-debug-modal').style.display = 'none';
    }


    function toggleContextPanel() {
      const panel = document.getElementById('timing-context-panel');
      panel.style.display = panel.style.display === 'none' ? 'block' : 'none';
    }


    async function copyMissionMarkdown(runId = null) {
      const targetRunId = runId || selectedRunId || (cachedRuns && cachedRuns.length ? cachedRuns[0].run_id : null);
      if (!targetRunId) {
        alert("No mission selected to copy.");
        return;
      }
      try {
        const res = await fetch(`/api/history/${encodeURIComponent(targetRunId)}/markdown`);
        const data = await res.json();
        if (data && data.markdown) {
          await navigator.clipboard.writeText(data.markdown);
          appendLog('step', `📋 Copied mission report Markdown for ${targetRunId} to clipboard`);
          alert("Mission Markdown report copied to clipboard!");
        }
      } catch (e) {
        alert("Failed to copy markdown: " + e);
      }
    }


    function toggleReportDropdown(e) {
      if (e) e.stopPropagation();
      const menu = document.getElementById('report-dropdown-menu');
      if (menu) menu.classList.toggle('show');
    }


    function closeReportDropdown() {
      const menu = document.getElementById('report-dropdown-menu');
      if (menu) menu.classList.remove('show');
    }


    function renderHomepageRecentFeed(runs) {
      const container = document.getElementById('homepage-recent-feed');
      if (!container) return;
      if (!runs || !runs.length) {
        container.innerHTML = '<div style="font-size: 0.75rem; color: var(--text-muted); padding: 0.4rem 0;">No missions recorded yet.</div>';
        return;
      }
      container.innerHTML = '';
      runs.slice(0, 3).forEach(r => {
        const dur = (r.start_time && r.end_time) ? `${Math.round(r.end_time - r.start_time)}s` : '';
        const item = document.createElement('div');
        item.className = 'recent-feed-item';
        item.innerHTML = `
          <div style="display: flex; align-items: center; gap: 0.5rem; overflow: hidden;">
            <span class="status-dot ${r.status === 'success' ? 'dot-green' : 'dot-amber'}"></span>
            <span style="white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 220px; color: #ffffff;">${r.goal}</span>
          </div>
          <div style="display: flex; align-items: center; gap: 0.4rem;">
            <span style="color: var(--text-muted); font-size: 0.72rem; font-family: 'JetBrains Mono', monospace;">${dur}</span>
            <button class="btn btn-cyan" style="padding: 0.15rem 0.45rem; font-size: 0.7rem;" onclick="inspectRun('${r.run_id}')">Inspect</button>
          </div>
        `;
        container.appendChild(item);
      });
    }


    function inspectRun(runId) {
      switchTab('history');
      setTimeout(() => {
        selectRun(runId);
      }, 100);
    }


    async function loadHistory() {
      // Fetch analytics for KPI widgets and charts
      try {
        const aRes = await fetch('/api/history/analytics');
        const analytics = await aRes.json();
        document.getElementById('kpi-total-runs').innerText = analytics.total_runs;
        document.getElementById('kpi-success-rate').innerText = analytics.success_rate + '%';
        document.getElementById('kpi-avg-duration').innerText = analytics.avg_duration_sec + 's';
        if (document.getElementById('kpi-total-steps')) {
          document.getElementById('kpi-total-steps').innerText = analytics.total_steps || 0;
        }

        let topAct = 'None';
        let topCount = -1;
        for (const [k, v] of Object.entries(analytics.actuator_breakdown || {})) {
          if (v > topCount) { topCount = v; topAct = k.charAt(0).toUpperCase() + k.slice(1); }
        }
        document.getElementById('kpi-top-actuator').innerText = topAct;

        // Render charts
        renderActuatorDonut(analytics.actuator_breakdown, analytics.actuator_percentages);
        renderVelocityChart(analytics.recent_timeline);

        // Update ratio bar
        const sPct = analytics.success_rate;
        document.getElementById('ratio-bar-success').style.width = sPct + '%';
        document.getElementById('ratio-bar-failed').style.width = (100 - sPct) + '%';
        document.getElementById('ratio-label').innerText = `${sPct}% Success (${analytics.success_count}/${analytics.total_runs})`;
      } catch (e) { }

      // Fetch runs
      try {
        const res = await fetch('/api/history');
        cachedRuns = await res.json();
        renderFilteredHistory();
        renderHomepageRecentFeed(cachedRuns);
      } catch (e) { }
    }


    async function selectRun(runId, elem) {
      selectedRunId = runId;
      document.querySelectorAll('.history-item').forEach(i => i.classList.remove('selected'));
      if (elem) elem.classList.add('selected');
      const exportBtn = document.getElementById('btn-export-md');
      if (exportBtn) exportBtn.style.display = 'inline-flex';

      const viewer = document.getElementById('history-details');
      viewer.innerHTML = '<p style="color: var(--text-muted);">Loading mission details...</p>';
      try {
        const res = await fetch('/api/history/' + runId);
        const data = await res.json();
        const duration = (data.start_time && data.end_time) ? `${Math.round(data.end_time - data.start_time)}s` : 'In Progress';
        viewer.innerHTML = `
          <div style="margin-bottom: 1.25rem; padding-bottom: 0.75rem; border-bottom: 1px solid rgba(255,255,255,0.08);">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 1rem; flex-wrap: wrap;">
              <h3 style="color: #ffffff; font-size: 1.05rem; flex: 1; min-width: 250px;">Goal: "${data.goal}"</h3>
              <div style="display: flex; gap: 0.4rem; align-items: center; flex-wrap: wrap;">
                <button class="btn btn-cyan btn-sm" onclick="downloadMissionReport('${data.run_id}', 'md')" title="Download Markdown Summary (.md)">
                  <i data-lucide="download" class="hud-icon-xs"></i> Markdown (.md)
                </button>
                <button class="btn btn-sm" style="background: rgba(0, 240, 255, 0.12); color: var(--neon-cyan); border: 1px solid rgba(0, 240, 255, 0.35); font-size: 0.72rem; padding: 0.25rem 0.55rem;" onclick="downloadMissionReport('${data.run_id}', 'html')" title="Download Standalone HTML Report (.html)">
                  <i data-lucide="globe" class="hud-icon-xs"></i> HTML Report
                </button>
                <button class="btn btn-sm" style="background: rgba(255, 255, 255, 0.08); font-size: 0.72rem; padding: 0.25rem 0.55rem;" onclick="downloadMissionReport('${data.run_id}', 'json')" title="Download Raw JSON Data">
                  <i data-lucide="code" class="hud-icon-xs"></i> JSON
                </button>
                <button class="btn btn-sm" style="background: rgba(255, 255, 255, 0.08); font-size: 0.72rem; padding: 0.25rem 0.55rem;" onclick="copyMissionMarkdown('${data.run_id}')" title="Copy Markdown to Clipboard">
                  <i data-lucide="copy" class="hud-icon-xs"></i> Copy
                </button>
              </div>
            </div>
            <div style="font-size: 0.8rem; color: var(--text-muted); margin-top: 0.35rem;">
              <span style="color: var(--neon-cyan); font-weight: 600;">ID: ${data.run_id}</span> • Status: <b style="color: ${data.status === 'success' ? 'var(--neon-green)' : 'var(--neon-red)'};">${data.status.toUpperCase()}</b> • Duration: ${duration} • Steps: ${data.steps ? data.steps.length : 0}
            </div>
            ${data.result ? `<div style="background: rgba(0, 230, 118, 0.08); border-left: 3px solid var(--neon-green); padding: 0.65rem; border-radius: 4px; margin-top: 0.75rem; font-size: 0.85rem; color: #e2e8f0;"><b>Final Outcome:</b> ${data.result}</div>` : ''}
          </div>
        `;
        if (data.steps && data.steps.length) {
          data.steps.forEach(s => {
            const stepDiv = document.createElement('div');
            stepDiv.className = 'step-card';
            let shotHtml = '';
            if (s.screenshot_file) {
              const shotUrl = `/api/history/${runId}/${s.screenshot_file}`;
              shotHtml = `
                <div style="position: relative; margin-top: 0.75rem;">
                  <img src="${shotUrl}" class="step-img" alt="Step Screenshot" title="Click to view full 1080p resolution in Lightbox" onclick="openLightbox('${shotUrl}', 'Step ${s.step_num}: ${s.action}')">
                  <span style="position: absolute; bottom: 8px; right: 8px; background: rgba(0,0,0,0.75); color: var(--neon-cyan); font-size: 0.7rem; padding: 0.2rem 0.5rem; border-radius: 4px; pointer-events: none; display: inline-flex; align-items: center; gap: 0.25rem;"><i data-lucide="zoom-in" class="hud-icon-xs"></i> Zoom (1080p)</span>
                </div>
              `;
            }

            let badgeClass = 'step-badge-desktop';
            let badgeIcon = '<i data-lucide="mouse-pointer" class="hud-icon-xs"></i>';
            if (s.action.includes('browser')) { badgeClass = 'step-badge-browser'; badgeIcon = '<i data-lucide="globe" class="hud-icon-xs"></i>'; }
            else if (s.action.includes('python')) { badgeClass = 'step-badge-python'; badgeIcon = '<i data-lucide="code" class="hud-icon-xs"></i>'; }
            else if (s.action.includes('shell')) { badgeClass = 'step-badge-shell'; badgeIcon = '<i data-lucide="terminal" class="hud-icon-xs"></i>'; }

            // Format params as clean chips
            let paramsChips = '';
            if (s.params && typeof s.params === 'object') {
              for (const [pk, pv] of Object.entries(s.params)) {
                const valStr = typeof pv === 'object' ? JSON.stringify(pv) : String(pv);
                paramsChips += `<span style="display: inline-block; background: rgba(255,255,255,0.06); padding: 0.15rem 0.45rem; border-radius: 4px; font-size: 0.72rem; color: #cbd5e1; margin-right: 0.3rem; margin-top: 0.25rem;"><b>${pk}:</b> ${valStr.substring(0, 40)}</span>`;
              }
            }

            stepDiv.innerHTML = `
              <div style="display: flex; justify-content: space-between; align-items: center;">
                <span class="step-badge ${badgeClass}">${badgeIcon} Step ${s.step_num}: ${s.action}</span>
                <span style="font-size: 0.75rem; color: ${s.success ? 'var(--neon-green)' : 'var(--neon-red)'}; font-family: 'JetBrains Mono', monospace; font-weight: bold; display: inline-flex; align-items: center; gap: 0.25rem;">${s.success ? '<i data-lucide="check-circle" class="hud-icon-xs"></i> COMPLETED' : '<i data-lucide="x-circle" class="hud-icon-xs"></i> FAILED'}</span>
              </div>
              <div style="font-size: 0.85rem; color: #89b4fa; font-style: italic; margin-top: 0.5rem; display: flex; align-items: center; gap: 0.35rem;"><i data-lucide="brain" class="hud-icon-xs text-cyan"></i> ${s.thought}</div>
              ${paramsChips ? `<div style="margin-top: 0.4rem;">${paramsChips}</div>` : ''}
              <div style="font-size: 0.8rem; color: var(--text-muted); margin-top: 0.4rem; background: rgba(0,0,0,0.3); padding: 0.5rem; border-radius: 4px; font-family: 'JetBrains Mono', monospace;"><b>Observation:</b> ${s.observation.substring(0, 350)}</div>
              ${shotHtml}
            `;
            viewer.appendChild(stepDiv);
          });
          renderIcons();
        } else {
          viewer.innerHTML += '<p style="color: var(--text-muted);">No visual steps recorded for this mission.</p>';
        }
      } catch (e) { }
    }


    async function loadMemoryConfig() {
      try {
        const res = await fetch('/api/memory/config');
        if (!res.ok) return;
        const data = await res.json();
        const input = document.getElementById('memory-dir-input');
        const resolved = document.getElementById('memory-dir-resolved');
        if (input) input.value = data.memory_dir;
        if (resolved) {
          resolved.innerText = data.resolved_path;
          currentResolvedMemoryDir = data.resolved_path;
        }
      } catch (e) {
        console.error('Failed to load memory config', e);
      }
    }


    async function saveMemoryConfig() {
      const input = document.getElementById('memory-dir-input');
      const resolved = document.getElementById('memory-dir-resolved');
      const newDir = input ? input.value.trim() : '';
      if (!newDir) {
        showMemoryStatus('Path cannot be empty', 'error');
        return;
      }
      try {
        const res = await fetch('/api/memory/config', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ memory_dir: newDir })
        });
        if (res.ok) {
          const data = await res.json();
          if (resolved) resolved.innerText = data.resolved_path;
          currentResolvedMemoryDir = data.resolved_path;
          showMemoryStatus('Directory updated & saved to config.yaml', 'success');
          loadMemory();
        } else {
          const err = await res.json();
          showMemoryStatus(err.detail || 'Failed to update directory', 'error');
        }
      } catch (e) {
        showMemoryStatus('Network error while saving directory', 'error');
      }
    }


    async function resetMemoryConfig() {
      const input = document.getElementById('memory-dir-input');
      if (input) input.value = '~/ai-memory/bro';
      await saveMemoryConfig();
    }


    function showMemoryStatus(msg, type) {
      const el = document.getElementById('memory-dir-status');
      if (!el) return;
      el.innerText = msg;
      el.style.display = 'inline-block';
      if (type === 'success') {
        el.style.background = 'rgba(16, 185, 129, 0.2)';
        el.style.color = '#10b981';
        el.style.border = '1px solid rgba(16, 185, 129, 0.4)';
      } else {
        el.style.background = 'rgba(239, 68, 68, 0.2)';
        el.style.color = '#ef4444';
        el.style.border = '1px solid rgba(239, 68, 68, 0.4)';
      }
      setTimeout(() => {
        if (el) el.style.display = 'none';
      }, 4000);
    }


    async function loadMemory() {
      await loadMemoryConfig();
      const treeContainer = document.getElementById('memory-tree-files');
      if (treeContainer) {
        treeContainer.innerHTML = '<p style="color: var(--text-muted); font-size: 0.8rem; padding: 0.5rem;">Loading memory tree...</p>';
      }
      try {
        const res = await fetch('/api/memory');
        memoryFiles = await res.json();
        renderMemoryTree();
        if (currentMemoryView === 'editor') {
          if (!memoryFiles.some(f => f.name === currentActiveMemoryFile) && memoryFiles.length > 0) {
            currentActiveMemoryFile = memoryFiles[0].name;
          }
          selectMemoryFile(currentActiveMemoryFile);
        } else {
          selectMemoryView('vault');
        }
      } catch (e) {
        console.error('Failed to load memory files', e);
        if (treeContainer) {
          treeContainer.innerHTML = '<p style="color: var(--neon-red); font-size: 0.8rem; padding: 0.5rem;">Failed to load memory tree.</p>';
        }
      }
    }


    function renderMemoryTree() {
      const container = document.getElementById('memory-tree-files');
      if (!container) return;
      container.innerHTML = '';

      const rootFiles = memoryFiles.filter(f => !f.name.includes('/'));
      const subFiles = memoryFiles.filter(f => f.name.includes('/'));

      const folders = {};
      subFiles.forEach(f => {
        const parts = f.name.split('/');
        const folderName = parts.slice(0, -1).join('/');
        if (!folders[folderName]) folders[folderName] = [];
        folders[folderName].push(f);
      });

      // Root files
      if (rootFiles.length > 0) {
        const rootHeader = document.createElement('div');
        rootHeader.style.cssText = 'font-size: 0.68rem; color: var(--text-muted); font-family: "JetBrains Mono", monospace; text-transform: uppercase; margin-top: 0.35rem; margin-bottom: 0.2rem; padding-left: 0.4rem;';
        rootHeader.innerText = 'Root Files';
        container.appendChild(rootHeader);

        rootFiles.forEach(f => {
          const btn = document.createElement('button');
          btn.className = 'tree-item-btn' + (currentMemoryView === 'editor' && f.name === currentActiveMemoryFile ? ' active' : '');
          btn.id = 'tree-file-' + f.name.replace(/[^a-zA-Z0-9_-]/g, '_');
          btn.onclick = () => selectMemoryFile(f.name);
          btn.innerHTML = `<i data-lucide="file-text" class="hud-icon-xs text-cyan"></i> <span>${f.name}</span>`;
          container.appendChild(btn);
        });
      }

      // Subfolders
      Object.keys(folders).sort().forEach(folderName => {
        const folderHeader = document.createElement('div');
        folderHeader.style.cssText = 'font-size: 0.68rem; color: var(--neon-cyan); font-family: "JetBrains Mono", monospace; text-transform: uppercase; margin-top: 0.75rem; margin-bottom: 0.2rem; padding-left: 0.4rem; display: flex; align-items: center; gap: 0.25rem;';
        folderHeader.innerHTML = `<i data-lucide="folder" class="hud-icon-xs text-amber"></i> ${folderName}/`;
        container.appendChild(folderHeader);

        folders[folderName].forEach(f => {
          const btn = document.createElement('button');
          btn.className = 'tree-item-btn' + (currentMemoryView === 'editor' && f.name === currentActiveMemoryFile ? ' active' : '');
          btn.id = 'tree-file-' + f.name.replace(/[^a-zA-Z0-9_-]/g, '_');
          btn.style.paddingLeft = '1.25rem';
          btn.onclick = () => selectMemoryFile(f.name);
          const baseName = f.name.split('/').pop();
          btn.innerHTML = `<i data-lucide="file-code" class="hud-icon-xs text-cyan"></i> <span>${baseName}</span>`;
          container.appendChild(btn);
        });
      });

      renderIcons();
    }


    function selectMemoryView(view) {
      currentMemoryView = view;
      const editorView = document.getElementById('memory-editor-view');
      const vaultView = document.getElementById('memory-vault-view');
      const obsidianView = document.getElementById('memory-obsidian-view');
      const vaultBtn = document.getElementById('btn-tree-vault');
      const obsidianBtn = document.getElementById('btn-tree-obsidian');

      document.querySelectorAll('.tree-item-btn').forEach(b => b.classList.remove('active'));

      if (view === 'vault') {
        if (vaultBtn) vaultBtn.classList.add('active');
        if (editorView) editorView.style.display = 'none';
        if (obsidianView) obsidianView.style.display = 'none';
        if (vaultView) vaultView.style.display = 'flex';
        loadVaultKeys();
      } else if (view === 'obsidian') {
        if (obsidianBtn) obsidianBtn.classList.add('active');
        if (editorView) editorView.style.display = 'none';
        if (vaultView) vaultView.style.display = 'none';
        if (obsidianView) obsidianView.style.display = 'flex';
        loadObsidianConfig();
      } else {
        if (vaultView) vaultView.style.display = 'none';
        if (obsidianView) obsidianView.style.display = 'none';
        if (editorView) editorView.style.display = 'flex';
      }
      renderIcons();
    }


    async function loadObsidianConfig() {
      try {
        const res = await fetch('/api/memory/config');
        const data = await res.json();
        const pInput = document.getElementById('obsidian-vault-path');
        const chunkBadge = document.getElementById('obsidian-chunk-count');
        const resolvedEl = document.getElementById('obsidian-resolved-path');
        if (pInput && data.obsidian_vault_dir) pInput.value = data.obsidian_vault_dir;
        if (chunkBadge) chunkBadge.innerText = `${data.total_chunks || 0} Chunks Indexed`;
        if (resolvedEl) resolvedEl.innerText = data.resolved_obsidian_path || data.obsidian_vault_dir || '~/obsidian/KnowledgeBase/ai-memory';
      } catch (e) { }
    }


    async function saveObsidianVault() {
      const pInput = document.getElementById('obsidian-vault-path');
      if (!pInput) return;
      const pathVal = pInput.value.trim();
      const statusEl = document.getElementById('obsidian-save-status');
      try {
        const res = await fetch('/api/memory/obsidian', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ obsidian_vault_dir: pathVal })
        });
        const data = await res.json();
        if (data.status === 'updated') {
          if (statusEl) {
            statusEl.style.display = 'inline';
            statusEl.innerText = `✓ Vault linked & ${data.total_chunks} chunks indexed`;
            setTimeout(() => { statusEl.style.display = 'none'; }, 3500);
          }
          const chunkBadge = document.getElementById('obsidian-chunk-count');
          if (chunkBadge) chunkBadge.innerText = `${data.total_chunks || 0} Chunks Indexed`;
          const resolvedEl = document.getElementById('obsidian-resolved-path');
          if (resolvedEl) resolvedEl.innerText = data.resolved_obsidian_path || pathVal;
          playTacticalSfx('success');
        }
      } catch (e) {
        alert('Failed to update Obsidian Vault: ' + e);
      }
    }


    async function reindexKnowledgeVault() {
      const btn = document.getElementById('btn-reindex-obsidian');
      if (btn) btn.innerHTML = '<i data-lucide="loader-2" class="hud-icon-xs spin"></i> Indexing...';
      try {
        const res = await fetch('/api/memory/reindex', { method: 'POST' });
        const data = await res.json();
        const chunkBadge = document.getElementById('obsidian-chunk-count');
        if (chunkBadge) chunkBadge.innerText = `${data.total_chunks || 0} Chunks Indexed`;
        playTacticalSfx('success');
        appendLog('step', `🧠 Real-time knowledge re-index complete: ${data.total_chunks} section chunks indexed across memory & Obsidian.`);
      } catch (e) {
        alert('Re-indexing error: ' + e);
      } finally {
        if (btn) btn.innerHTML = '<i data-lucide="refresh-cw" class="hud-icon-xs"></i> Re-Index Knowledge Base';
        renderIcons();
      }
    }


    async function testRagQuery() {
      const input = document.getElementById('rag-test-input');
      const box = document.getElementById('rag-test-results');
      if (!input || !box) return;
      const q = input.value.trim();
      if (!q) return;

      box.style.display = 'block';
      box.innerHTML = '<span style="color: var(--neon-cyan);">Searching knowledge graph across memory & Obsidian...</span>';
      try {
        const res = await fetch('/api/memory/config');
        const data = await res.json();
        box.innerHTML = `
          <div style="color: var(--neon-green); font-weight: 700; margin-bottom: 0.35rem;">✔ RAG Knowledge Evaluation for "${q}":</div>
          <div style="color: var(--text-muted); font-size: 0.72rem; margin-bottom: 0.5rem;">Total Knowledge Chunks: ${data.total_chunks} | Semantic Mode: ${data.semantic_search_enabled ? 'Active (BM25 + Embeddings)' : 'BM25 Lexical Only'}</div>
          <div style="background: rgba(0,0,0,0.5); border: 1px solid rgba(0, 240, 255, 0.2); padding: 0.5rem; border-radius: 4px; color: #cbd5e1; font-size: 0.72rem;">
            Context injections anchor matching sections directly above Tier-1 system prompt during execution.
          </div>
        `;
        playTacticalSfx('success');
      } catch (e) {
        box.innerHTML = `<span style="color: var(--neon-red);">Query failed: ${e}</span>`;
      }
    }


    function toggleShortcutsModal() {
      const modal = document.getElementById('shortcuts-modal');
      if (!modal) return;
      const isVisible = (modal.style.display === 'flex');
      modal.style.display = isVisible ? 'none' : 'flex';
      renderIcons();
    }


    function selectMemoryFile(filename) {
      currentActiveMemoryFile = filename;
      selectMemoryView('editor');

      document.querySelectorAll('.tree-item-btn').forEach(b => b.classList.remove('active'));
      const activeBtn = document.getElementById('tree-file-' + filename.replace(/[^a-zA-Z0-9_-]/g, '_'));
      if (activeBtn) activeBtn.classList.add('active');

      const fileObj = memoryFiles.find(f => f.name === filename);
      const content = fileObj ? fileObj.content : '';

      const nameEl = document.getElementById('active-memory-filename');
      const pathEl = document.getElementById('active-memory-filepath');
      const textEl = document.getElementById('active-memory-content');

      if (nameEl) nameEl.innerHTML = `<i data-lucide="file-text" class="hud-icon-xs text-cyan"></i> ${filename}`;
      if (pathEl) pathEl.innerText = `${currentResolvedMemoryDir}/${filename}`;
      if (textEl) {
        textEl.value = content;
        updateMemoryStats(content);
        textEl.oninput = () => updateMemoryStats(textEl.value);
      }
      renderIcons();
    }


    function updateMemoryStats(text) {
      const statsEl = document.getElementById('active-memory-stats');
      if (!statsEl) return;
      const lines = text ? text.split('\n').length : 0;
      const chars = text ? text.length : 0;
      statsEl.innerText = `${lines} lines • ${chars} characters`;
    }


    async function saveActiveMemoryFile() {
      const textEl = document.getElementById('active-memory-content');
      const statusEl = document.getElementById('active-memory-save-status');
      if (!textEl || !currentActiveMemoryFile) return;
      const content = textEl.value;

      try {
        const res = await fetch('/api/memory', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ filename: currentActiveMemoryFile, content })
        });
        if (res.ok) {
          const fileObj = memoryFiles.find(f => f.name === currentActiveMemoryFile);
          if (fileObj) fileObj.content = content;
          if (statusEl) {
            statusEl.innerText = '✓ Changes saved to disk';
            statusEl.style.display = 'inline-block';
            setTimeout(() => { if (statusEl) statusEl.style.display = 'none'; }, 3000);
          }
          appendLog('step', `💾 Memory file saved: ${currentActiveMemoryFile}`);
        } else {
          alert('Failed to save file');
        }
      } catch (e) {
        console.error('Failed to save memory file:', e);
        alert('Error saving memory file: ' + e.message);
      }
    }


    function revertActiveMemoryFile() {
      const fileObj = memoryFiles.find(f => f.name === currentActiveMemoryFile);
      if (!fileObj) return;
      const textEl = document.getElementById('active-memory-content');
      if (textEl) {
        textEl.value = fileObj.content;
        updateMemoryStats(fileObj.content);
      }
    }


    async function promptNewMemoryFile() {
      const name = prompt("Enter new memory filename (e.g. notes.md or workflows/custom_task.md):");
      if (!name || !name.trim()) return;
      const trimmed = name.trim();
      const initialContent = `# ${trimmed}\n\n`;
      try {
        const res = await fetch('/api/memory', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ filename: trimmed, content: initialContent })
        });
        if (res.ok) {
          currentActiveMemoryFile = trimmed;
          await loadMemory();
          selectMemoryFile(trimmed);
        } else {
          alert('Failed to create file');
        }
      } catch (e) {
        alert('Error creating file: ' + e.message);
      }
    }


    async function loadVaultKeys() {
      const container = document.getElementById('vault-keys-list');
      if (!container) return;
      container.innerHTML = '<p style="color: var(--text-muted); font-size: 0.8rem;">Loading vault keys...</p>';
      try {
        const res = await fetch('/api/vault');
        const data = await res.json();
        const keys = data.keys || [];
        if (keys.length === 0) {
          container.innerHTML = '<p style="color: var(--text-muted); font-size: 0.8rem;">No keys currently stored in workstation keyring vault.</p>';
          return;
        }
        container.innerHTML = '';
        keys.forEach(k => {
          const item = document.createElement('div');
          item.style.cssText = 'display: flex; justify-content: space-between; align-items: center; background: rgba(3,8,18,0.7); border: 1px solid var(--panel-border); border-radius: 6px; padding: 0.65rem 0.85rem;';
          item.innerHTML = `
            <div style="display: flex; align-items: center; gap: 0.5rem;">
              <i data-lucide="key" class="hud-icon-xs text-purple"></i>
              <span style="font-family: 'JetBrains Mono', monospace; font-size: 0.82rem; color: #ffffff; font-weight: 700;">${k}</span>
              <span class="badge" style="background: rgba(168,85,247,0.15); border: 1px solid rgba(168,85,247,0.4); color: #c084fc; font-size: 0.68rem;">ENCRYPTED</span>
            </div>
            <div style="font-size: 0.75rem; color: var(--text-muted); font-family: 'JetBrains Mono', monospace;">••••••••••••••••</div>
          `;
          container.appendChild(item);
        });
        renderIcons();
      } catch (e) {
        console.error('Failed to load vault keys:', e);
        container.innerHTML = '<p style="color: var(--neon-red); font-size: 0.8rem;">Failed to load vault keys.</p>';
      }
    }


    async function saveVaultSecret() {
      const keyInput = document.getElementById('vault-new-key');
      const valInput = document.getElementById('vault-new-val');
      const key = keyInput ? keyInput.value.trim() : '';
      const val = valInput ? valInput.value.trim() : '';
      if (!key || !val) {
        alert('Please specify both key name and secret value.');
        return;
      }
      try {
        const res = await fetch('/api/vault', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ key, value: val })
        });
        if (res.ok) {
          keyInput.value = '';
          valInput.value = '';
          loadVaultKeys();
          appendLog('step', `🔑 Stored encrypted secret for key: ${key}`);
        } else {
          alert('Failed to store secret');
        }
      } catch (e) {
        alert('Error storing secret: ' + e.message);
      }
    }


    let calendarEvents = [];


    let pendingEvents = [];


    let currentCalYear = new Date().getFullYear();


    let currentCalMonth = new Date().getMonth(); // 0-indexed


    async function loadCalendar() {
      try {
        const res = await fetch('/api/calendar');
        if (!res.ok) return;
        const data = await res.json();
        calendarEvents = data.events || [];
        pendingEvents = data.pending || [];
        renderCalendarGrid();
        renderPendingList();
      } catch (e) {
        console.error("Failed to load calendar data:", e);
      }
    }


    function prevCalMonth() {
      currentCalMonth--;
      if (currentCalMonth < 0) {
        currentCalMonth = 11;
        currentCalYear--;
      }
      renderCalendarGrid();
    }


    function nextCalMonth() {
      currentCalMonth++;
      if (currentCalMonth > 11) {
        currentCalMonth = 0;
        currentCalYear++;
      }
      renderCalendarGrid();
    }


    function goToTodayCal() {
      const now = new Date();
      currentCalYear = now.getFullYear();
      currentCalMonth = now.getMonth();
      renderCalendarGrid();
    }


    function renderCalendarGrid() {
      const label = document.getElementById('cal-month-year-label');
      if (label) label.innerText = `${MONTH_NAMES[currentCalMonth]} ${currentCalYear}`;

      const grid = document.getElementById('calendar-grid-cells');
      if (!grid) return;
      grid.innerHTML = '';

      const today = new Date();
      const todayStr = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`;

      // First day of current month (0=Sun, 1=Mon, ..., 6=Sat)
      const firstDay = new Date(currentCalYear, currentCalMonth, 1).getDay();
      // Total days in current month
      const daysInMonth = new Date(currentCalYear, currentCalMonth + 1, 0).getDate();
      // Days in previous month
      const daysInPrevMonth = new Date(currentCalYear, currentCalMonth, 0).getDate();

      // Prev month filler cells
      for (let i = firstDay - 1; i >= 0; i--) {
        const d = daysInPrevMonth - i;
        const cell = document.createElement('div');
        cell.className = 'cal-day-cell other-month';
        cell.innerHTML = `<div class="cal-day-number">${d}</div>`;
        grid.appendChild(cell);
      }

      // Current month days
      for (let d = 1; d <= daysInMonth; d++) {
        const dateStr = `${currentCalYear}-${String(currentCalMonth + 1).padStart(2, '0')}-${String(d).padStart(2, '0')}`;
        const isToday = dateStr === todayStr;

        const cell = document.createElement('div');
        cell.className = `cal-day-cell${isToday ? ' today' : ''}`;
        cell.onclick = (e) => {
          if (!e.target.closest('.cal-event-chip')) {
            openAddEventModal(dateStr);
          }
        };

        const dayEvents = calendarEvents.filter(ev => ev.date === dateStr);

        let chipsHtml = '';
        dayEvents.slice(0, 3).forEach(ev => {
          const timeLabel = ev.time ? `<span style="color:var(--neon-cyan);">${ev.time}</span> ` : '';
          const tagClass = (ev.tags && ev.tags.length) ? `tag-${ev.tags[0].toLowerCase()}` : '';
          chipsHtml += `
            <div class="cal-event-chip${ev.completed ? ' done' : ''} ${tagClass}" onclick="event.stopPropagation(); toggleCalendarEvent(${ev.id}, ${!ev.completed})" title="${escapeHtml(ev.title)} (${ev.completed ? 'Completed' : 'Pending'})">
              ${timeLabel}${escapeHtml(ev.title)}
            </div>
          `;
        });
        if (dayEvents.length > 3) {
          chipsHtml += `<div style="font-size: 0.62rem; color: var(--neon-cyan); font-family: 'JetBrains Mono', monospace;">+${dayEvents.length - 3} more</div>`;
        }

        cell.innerHTML = `
          <div class="cal-day-number">
            <span>${d}</span>
            ${isToday ? '<span style="font-size:0.6rem; color:var(--neon-cyan); text-transform:uppercase;">TODAY</span>' : ''}
          </div>
          ${chipsHtml}
        `;
        grid.appendChild(cell);
      }

      // Next month filler cells to complete 35 or 42 grid
      const totalCellsSoFar = firstDay + daysInMonth;
      const remaining = (totalCellsSoFar <= 35) ? (35 - totalCellsSoFar) : (42 - totalCellsSoFar);
      for (let d = 1; d <= remaining; d++) {
        const cell = document.createElement('div');
        cell.className = 'cal-day-cell other-month';
        cell.innerHTML = `<div class="cal-day-number">${d}</div>`;
        grid.appendChild(cell);
      }
    }


    function renderPendingList(items = null) {
      const list = document.getElementById('pending-events-list');
      const badge = document.getElementById('pending-count-badge');
      if (!list) return;

      const eventsToShow = items !== null ? items : pendingEvents;
      if (badge) badge.innerText = `${pendingEvents.length} Pending`;

      if (eventsToShow.length === 0) {
        list.innerHTML = `
          <div style="color: var(--text-muted); font-size: 0.78rem; text-align: center; padding: 2.5rem 1rem; font-family: 'JetBrains Mono', monospace;">
            <i data-lucide="check-circle" class="hud-icon-lg text-green" style="margin-bottom: 0.5rem; display: block; margin-left: auto; margin-right: auto;"></i>
            All clear! No pending tasks found.
          </div>
        `;
        renderIcons();
        return;
      }

      let html = '';
      eventsToShow.forEach(ev => {
        let tagPills = '';
        if (ev.tags && ev.tags.length) {
          ev.tags.forEach(t => {
            const cls = `tag-${t.toLowerCase()}`;
            tagPills += `<span class="tag-pill ${cls}">#${escapeHtml(t)}</span> `;
          });
        }

        html += `
          <div class="pending-item">
            <input type="checkbox" ${ev.completed ? 'checked' : ''} onchange="toggleCalendarEvent(${ev.id}, this.checked)" style="margin-top: 3px; cursor: pointer; accent-color: var(--neon-cyan);">
            <div style="flex: 1; min-width: 0;">
              <div style="font-size: 0.82rem; font-weight: 600; color: #ffffff; white-space: normal; line-height: 1.35; margin-bottom: 0.25rem;">
                ${escapeHtml(ev.title)}
              </div>
              <div style="display: flex; flex-wrap: wrap; align-items: center; gap: 0.4rem; font-size: 0.72rem; font-family: 'JetBrains Mono', monospace; color: var(--text-muted);">
                <span style="color: var(--neon-cyan);">${ev.date}${ev.time ? ' ' + ev.time : ''}</span>
                ${tagPills}
              </div>
            </div>
          </div>
        `;
      });

      list.innerHTML = html;
      renderIcons();
    }


    function filterPendingEvents(query) {
      const q = (query || '').toLowerCase().trim();
      if (!q) {
        renderPendingList(pendingEvents);
        return;
      }
      const filtered = pendingEvents.filter(ev => {
        const titleMatch = ev.title.toLowerCase().includes(q);
        const dateMatch = ev.date.toLowerCase().includes(q);
        const tagMatch = ev.tags && ev.tags.some(t => t.toLowerCase().includes(q));
        return titleMatch || dateMatch || tagMatch;
      });
      renderPendingList(filtered);
    }


    function openAddEventModal(defaultDate = null) {
      const modal = document.getElementById('calendar-add-modal');
      const dateInp = document.getElementById('cal-new-date');
      const titleInp = document.getElementById('cal-new-title');
      const timeInp = document.getElementById('cal-new-time');
      const tagsInp = document.getElementById('cal-new-tags');

      if (titleInp) titleInp.value = '';
      if (timeInp) timeInp.value = '';
      if (tagsInp) tagsInp.value = '';

      if (dateInp) {
        if (defaultDate) {
          dateInp.value = defaultDate;
        } else {
          const now = new Date();
          dateInp.value = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`;
        }
      }

      if (modal) modal.style.display = 'flex';
      if (titleInp) setTimeout(() => titleInp.focus(), 50);
      renderIcons();
    }


    function closeAddEventModal() {
      const modal = document.getElementById('calendar-add-modal');
      if (modal) modal.style.display = 'none';
    }


    async function submitNewCalendarEvent() {
      const title = document.getElementById('cal-new-title').value.trim();
      const date = document.getElementById('cal-new-date').value.trim();
      const time = document.getElementById('cal-new-time').value.trim();
      const rawTags = document.getElementById('cal-new-tags').value.trim();
      const tags = rawTags ? rawTags.split(',').map(t => t.trim().replace(/^#/, '')).filter(Boolean) : [];

      if (!title || !date) {
        alert("Please enter both a title and date for the event.");
        return;
      }

      try {
        const res = await fetch('/api/calendar', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ title, date, time, tags })
        });
        if (res.ok) {
          closeAddEventModal();
          playTacticalSfx('success');
          appendLog('action', `📅 Added schedule event: ${title} (${date})`);
          await loadCalendar();
        } else {
          alert("Failed to save calendar event.");
        }
      } catch (e) {
        console.error("Calendar save error:", e);
      }
    }


    async function toggleCalendarEvent(id, completed) {
      try {
        const res = await fetch('/api/calendar/toggle', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ identifier: id, completed })
        });
        if (res.ok) {
          playTacticalSfx('toggle');
          await loadCalendar();
        }
      } catch (e) {
        console.error("Calendar toggle error:", e);
      }
    }


    async function speakTodayCalendar() {
      try {
        const res = await fetch('/api/calendar/today');
        const data = await res.json();
        if (data.summary) {
          appendLog('thought', `📅 [SCHEDULE SUMMARY] ${data.summary}`);
          speakVoiceResponse(data.summary);
          if (currentConversationMode === 'audio_only') {
            document.getElementById('sub-bro-text').innerText = `"${data.summary}"`;
            updateVoiceVisualizerState('speaking', 'CALENDAR RECITED');
          }
        }
      } catch (e) {
        console.error("Recite calendar error:", e);
      }
    }


    function promptClearAllCalendar() {
      const modal = document.getElementById('calendar-clear-modal');
      const step1 = document.getElementById('cal-clear-step1');
      const step2 = document.getElementById('cal-clear-step2');
      if (step1) step1.style.display = 'block';
      if (step2) step2.style.display = 'none';
      if (modal) modal.style.display = 'flex';
      renderIcons();
    }


    function closeClearCalendarModal() {
      const modal = document.getElementById('calendar-clear-modal');
      if (modal) modal.style.display = 'none';
    }


    function proceedToClearStep2() {
      const step1 = document.getElementById('cal-clear-step1');
      const step2 = document.getElementById('cal-clear-step2');
      if (step1) step1.style.display = 'none';
      if (step2) step2.style.display = 'block';
      renderIcons();
    }


    async function executeClearCalendar() {
      try {
        const res = await fetch('/api/calendar', {
          method: 'DELETE'
        });
        if (res.ok) {
          closeClearCalendarModal();
          playTacticalSfx('success');
          appendLog('action', '🗑️ Cleared all scheduled events & tasks from memory (calendar.md)');
          await loadCalendar();
        } else {
          alert('Failed to clear calendar events.');
        }
      } catch (e) {
        console.error('Calendar clear error:', e);
      }
    }


    let cachedDesignMarkdown = '';


    function renderBasicMarkdownFallback(md) {
      if (!md) return '';
      let html = escapeHtml(md);
      // Code blocks
      html = html.replace(/```([a-z]*)\n([\s\S]*?)```/g, '<pre style="background:rgba(2,6,14,0.9);border:1px solid rgba(0,240,255,0.2);border-radius:6px;padding:1rem;overflow-x:auto;margin:1rem 0;font-family:\'JetBrains Mono\',monospace;color:#a6e3a1;"><code>$2</code></pre>');
      // Inline code
      html = html.replace(/`([^`]+)`/g, '<code style="background:rgba(0,240,255,0.1);color:var(--neon-cyan);padding:0.15rem 0.35rem;border-radius:4px;font-family:\'JetBrains Mono\',monospace;font-size:0.85em;">$1</code>');
      // Headers
      html = html.replace(/^### (.*$)/gim, '<h3 style="color:var(--neon-cyan);margin:1.25rem 0 0.5rem 0;font-size:1.05rem;">$1</h3>');
      html = html.replace(/^## (.*$)/gim, '<h2 style="color:#ffffff;border-bottom:1px solid rgba(0,240,255,0.2);padding-bottom:0.4rem;margin:1.75rem 0 0.75rem 0;font-size:1.2rem;">$1</h2>');
      html = html.replace(/^# (.*$)/gim, '<h1 style="color:var(--neon-cyan);font-size:1.5rem;margin:0 0 1rem 0;">$1</h1>');
      // Bullet lists
      html = html.replace(/^\* (.*$)/gim, '<li style="margin-left:1.5rem;margin-bottom:0.3rem;">$1</li>');
      html = html.replace(/^- (.*$)/gim, '<li style="margin-left:1.5rem;margin-bottom:0.3rem;">$1</li>');
      // Bold & Italic
      html = html.replace(/\*\*([^*]+)\*\*/g, '<strong style="color:#ffffff;">$1</strong>');
      html = html.replace(/\*([^*]+)\*/g, '<em>$1</em>');
      // Paragraphs
      html = html.replace(/\n\n+/g, '<br><br>');
      return html;
    }


    async function loadDesignDocument() {
      const container = document.getElementById('resources-markdown-viewer');
      if (!container) return;
      try {
        container.innerHTML = '<div style="display:flex;align-items:center;gap:0.75rem;padding:2rem;color:var(--neon-cyan);"><i data-lucide="loader" class="hud-icon spin"></i> Loading Technical Design Specification (design.md)...</div>';
        renderIcons();
        const res = await fetch('/api/docs/design');
        if (!res.ok) throw new Error('Failed to fetch design document');
        const data = await res.json();
        cachedDesignMarkdown = data.content;

        if (typeof marked !== 'undefined' && marked.parse) {
          container.innerHTML = marked.parse(data.content);
        } else {
          container.innerHTML = renderBasicMarkdownFallback(data.content);
        }

        buildResourcesTOC();

        const sizeBadge = document.getElementById('resources-doc-size');
        if (sizeBadge) sizeBadge.innerText = `${Math.round(data.size_bytes / 1024 * 10) / 10} KB`;

        renderIcons();
      } catch (e) {
        container.innerHTML = `<div style="padding:2rem;color:#ff6b6b;"><i data-lucide="alert-triangle" class="hud-icon-sm"></i> Error loading design specification: ${escapeHtml(e.message)}</div>`;
        renderIcons();
      }
    }


    function buildResourcesTOC() {
      const toc = document.getElementById('resources-toc-list');
      const container = document.getElementById('resources-markdown-viewer');
      if (!toc || !container) return;
      toc.innerHTML = '<div style="font-size:0.75rem;color:var(--text-muted);text-transform:uppercase;font-weight:700;margin-bottom:0.4rem;padding-left:0.5rem;letter-spacing:0.8px;">Table of Contents</div>';
      const headings = container.querySelectorAll('h1, h2, h3');
      headings.forEach((h, idx) => {
        const id = 'spec-sec-' + idx;
        h.id = id;
        const btn = document.createElement('button');
        btn.className = 'manual-nav-btn';
        btn.style.fontSize = h.tagName === 'H1' ? '0.78rem' : h.tagName === 'H2' ? '0.74rem' : '0.7rem';
        btn.style.padding = h.tagName === 'H3' ? '0.3rem 0.5rem 0.3rem 1.4rem' : h.tagName === 'H2' ? '0.35rem 0.5rem 0.35rem 0.8rem' : '0.4rem 0.5rem';
        btn.style.textAlign = 'left';
        btn.innerText = h.innerText.replace(/^#+\s*/, '');
        btn.onclick = () => {
          document.querySelectorAll('#resources-toc-list .manual-nav-btn').forEach(b => b.classList.remove('active'));
          btn.classList.add('active');
          h.scrollIntoView({ behavior: 'smooth', block: 'start' });
        };
        toc.appendChild(btn);
      });
      const firstNav = toc.querySelector('.manual-nav-btn');
      if (firstNav) firstNav.classList.add('active');
    }


    function copyDesignDoc() {
      if (cachedDesignMarkdown) {
        navigator.clipboard.writeText(cachedDesignMarkdown).then(() => {
          playTacticalSfx('success');
          alert('design.md technical specification copied to clipboard!');
        });
      }
    }


    function showFileViewerModal(filename, content, path = '') {
      currentViewerContent = content || '';
      const modal = document.getElementById('file-viewer-modal');
      const nameEl = document.getElementById('file-viewer-filename');
      const pathEl = document.getElementById('file-viewer-filepath');
      const badgeEl = document.getElementById('file-viewer-lines-badge');
      const codeEl = document.getElementById('file-viewer-content');

      if (nameEl) nameEl.innerText = filename || 'file.txt';
      if (pathEl) pathEl.innerText = path || filename || '';

      const lines = (content || '').split('\n');
      if (badgeEl) badgeEl.innerText = `${lines.length} lines`;

      if (codeEl) {
        let linesHtml = '';
        lines.forEach((line, idx) => {
          linesHtml += `
            <div style="display: flex; gap: 0.85rem; padding: 1px 0;">
              <span style="color: var(--text-muted); min-width: 38px; text-align: right; user-select: none; opacity: 0.6;">${idx + 1}</span>
              <span style="flex: 1; white-space: pre-wrap; word-break: break-all;">${escapeHtml(line)}</span>
            </div>
          `;
        });
        codeEl.innerHTML = linesHtml;
      }

      if (modal) modal.style.display = 'flex';
      renderIcons();
    }


    function closeFileViewerModal() {
      const modal = document.getElementById('file-viewer-modal');
      if (modal) modal.style.display = 'none';
    }


    function copyFileViewerContent() {
      if (navigator.clipboard && currentViewerContent) {
        navigator.clipboard.writeText(currentViewerContent).then(() => {
          appendLog('step', '📋 File content copied to clipboard.');
          playTacticalSfx('success');
        });
      }
    }
