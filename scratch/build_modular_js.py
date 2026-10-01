import os
import re
from playwright.sync_api import sync_playwright

with open('scratch_main.js') as f:
    text = f.read()

def parse_blocks(source):
    blocks = []
    lines = source.splitlines(keepends=True)
    current_block = []
    brace_depth = 0
    
    for line in lines:
        current_block.append(line)
        # Count braces
        brace_depth += line.count('{') - line.count('}')
        if brace_depth == 0 and current_block:
            block_str = ''.join(current_block)
            if block_str.strip():
                blocks.append(block_str)
            current_block = []
            
    if current_block:
        blocks.append(''.join(current_block))
    return blocks

blocks = parse_blocks(text)
print(f"Parsed {len(blocks)} blocks.")

module_map = {
    'themes': [],
    'visualizer': [],
    'voice': [],
    'settings': [],
    'tabs': [],
    'core': []
}

# Explicit function assignments for 100% precision
THEMES_FUNCS = {'setSystemTheme', 'initThemeUI'}

VISUALIZER_FUNCS = {
    'initQuantumParticles', 'setAudioVisualizerStyle', 'initAudioVisualizerUI',
    'startAudioVisualizerLoop', 'renderLoop', 'renderQuantumSphereFrame',
    'getParticleColor', 'renderEqualizerMatrixFrame', 'toggleAudioFullscreen',
    'enterAudioFullscreen', 'exitAudioFullscreen'
}

VOICE_FUNCS = {
    'syncVolumeUI', 'onVolumeInput', 'onVolumeChange', 'testBroVolume',
    'parseRateToMultiplier', 'multiplierToRateStr', 'syncSpeedUI',
    'onVoiceSpeedInput', 'onVoiceSpeedChange', 'resetVoiceSpeed',
    'loadVoices', 'populateVoiceDropdown', 'onVoiceSelectChange',
    'previewSelectedVoice', 'toggleHandsFreeLoop', 'setConversationMode',
    'syncConversationModeUI', 'updateVoiceVisualizerState', 'stopVoicePlayback',
    'scheduleRecognitionRestart', 'onSttEngineChange', 'startWhisperRecording',
    'stopWhisperRecording', 'startSpeechRecognitionSafe', 'startSpeechRecognitionContinuous',
    'toggleAudioOnlySession', 'speakQuickPrompt', 'initSpeechRecognition',
    'toggleVoiceRecognition', 'stopSpeechRecognitionUI', 'stopSpeechRecognition',
    'toggleVoiceReply', 'toggleGenZGreetings'
}

SETTINGS_FUNCS = {
    'testApprovalOverlay', 'toggleWatchdogCard', 'syncAutonomousUI', 'toggleAutonomousSetting',
    'promptClearAuditHistory', 'closeAuditClearModal', 'confirmClearAuditHistory',
    'showSettingsSection', 'getPolicyLabel', 'syncPolicyUI', 'setAIBackendPolicy',
    'quickSetModelPolicy', 'onCloudModelChange', 'toggleApiKeyVisibility',
    'loadModels', 'saveModelSelection', 'loadGatewayProviders', 'renderGatewayProviders',
    'toggleGatewayProvider', 'saveGatewayProviderConfig', 'testGatewayProvider',
    'loadDailyBriefConfig', 'renderDailyBriefConfig', 'toggleBriefTopic',
    'onBriefSliderInput', 'onBriefSliderChange', 'saveDailyBriefConfig',
    'previewDailyBrief', 'loadBriefSlots', 'renderBriefSlots', 'toggleSlotTopic',
    'addBriefSlot', 'removeBriefSlot', 'saveBriefSlots', 'previewSlotBrief',
    'setupUbuntuShortcut'
}

TABS_FUNCS = {
    'loadDesktopMonitors', 'changeMainDesktop', 'refreshActivePreview', 'previewActiveDesktop',
    'loadErrors', 'clearErrors', 'filterHistoryByActuator', 'renderActuatorDonut',
    'renderVelocityChart', 'setHistoryFilter', 'filterHistoryList', 'renderFilteredHistory',
    'downloadMissionReport', 'exportCurrentRunMarkdown', 'openTimingModal', 'closeTimingModal',
    'toggleContextPanel', 'copyMissionMarkdown', 'toggleReportDropdown', 'closeReportDropdown',
    'renderHomepageRecentFeed', 'inspectRun', 'loadHistory', 'selectRun',
    'loadMemoryConfig', 'saveMemoryConfig', 'resetMemoryConfig', 'showMemoryStatus',
    'loadMemory', 'renderMemoryTree', 'selectMemoryView', 'loadObsidianConfig',
    'saveObsidianVault', 'reindexKnowledgeVault', 'testRagQuery', 'toggleShortcutsModal',
    'selectMemoryFile', 'updateMemoryStats', 'saveActiveMemoryFile', 'revertActiveMemoryFile',
    'promptNewMemoryFile', 'loadVaultKeys', 'saveVaultSecret',
    'loadCalendar', 'prevCalMonth', 'nextCalMonth', 'goToTodayCal', 'renderCalendarGrid',
    'renderPendingList', 'filterPendingEvents', 'openAddEventModal', 'closeAddEventModal',
    'submitNewCalendarEvent', 'toggleCalendarEvent', 'speakTodayCalendar',
    'promptClearAllCalendar', 'closeClearCalendarModal', 'proceedToClearStep2', 'executeClearCalendar',
    'renderBasicMarkdownFallback', 'loadDesignDocument', 'buildResourcesTOC',
    'copyDesignDoc', 'showFileViewerModal', 'closeFileViewerModal', 'copyFileViewerContent',
    'showManualSection'
}

CORE_FUNCS = {
    'setGoal', 'getAudioContext', 'toggleTacticalSfx', 'playTacticalSfx',
    'appendLog', 'handleFileUpload', 'renderAttachmentChips', 'removeAttachment',
    'handleModalFileUpload', 'submitSuppliedFile', 'cancelSuppliedFile',
    'openLightbox', 'closeLightbox', 'applyTerminalFontSize', 'adjustTerminalFont',
    'resetTerminalFont', 'clearTerminalLogs', 'copyTerminalLogs', 'copySnippet',
    'pasteClipboard', 'connectWS', 'showVisualMediaModal', 'closeMediaModal',
    'toggleRawMediaCode', 'copyMediaContent', 'spawnDesktopWindowFromModal',
    'showArchitectureDiagram', 'showFileRequestModal', 'updateMissionProgress',
    'hideMissionProgress', 'updateTelemetry', 'runTask', 'triggerBrief',
    'launchCDP', 'runOrganizer', 'killSwitch', 'openContextualExplanation',
    'zoomExplanationDiagram', 'resetExplanationZoom', 'exportExplanationSvg',
    'closeExplanationModal', 'askFollowUpExplanation', 'pollStatus',
    'updateSentinelCard', 'toggleMultiStepSidebar', 'showMultiStepSidebar',
    'startMultiStepSession', 'updateMultiStepSidebar', 'recordActuatorAction',
    'renderActuatorBreakdown', 'finishMultiStepSession'
}

for b in blocks:
    s = b.strip()
    # Check if block is a function definition
    m = re.match(r'^(?:async\s+)?function\s+([a-zA-Z0-9_$]+)', s)
    if m:
        func_name = m.group(1)
        if func_name in ['escapeHtml', 'renderIcons', 'switchTab']:
            # Handled in core_prefix
            continue
        elif func_name in THEMES_FUNCS:
            module_map['themes'].append(b)
        elif func_name in VISUALIZER_FUNCS:
            module_map['visualizer'].append(b)
        elif func_name in VOICE_FUNCS:
            module_map['voice'].append(b)
        elif func_name in SETTINGS_FUNCS:
            module_map['settings'].append(b)
        elif func_name in TABS_FUNCS:
            module_map['tabs'].append(b)
        elif func_name in CORE_FUNCS:
            module_map['core'].append(b)
        else:
            module_map['core'].append(b)
    else:
        # Check comments / variable blocks by keywords
        if any(k in s for k in ['quantumParticles', 'activeVisualizerStyle', 'NUM_QUANTUM_PARTICLES', 'FULLSCREEN HUD']):
            module_map['visualizer'].append(b)
        elif any(k in s for k in ['currentActiveVolume', 'currentAudioRate', 'continuousVoiceActive', 'isSpeaking', 'currentSttEngine', 'whisperMediaRecorder', 'recognitionRestartTimer', 'isAudioOnlySession', 'isHandsFreeLoopActive', 'currentConversationMode']):
            module_map['voice'].append(b)
        elif any(k in s for k in ['currentAutonomousMode', 'currentCloudModel', 'currentPolicy', 'briefScheduleSlots']):
            module_map['settings'].append(b)
        elif any(k in s for k in ['calendarEvents', 'pendingEvents', 'currentCalYear', 'currentCalMonth', 'selectedCalendarDay', 'activeMemoryFile', 'activeMemoryOriginalContent', 'cachedDesignMarkdown', 'historyRuns', 'activeRunId', 'donutChartInstance', 'velocityChartInstance', 'historyFilterType']):
            module_map['tabs'].append(b)
        elif any(k in s for k in ['audioCtx', 'sfxEnabled', 'terminalFontSize', 'attachedFiles', 'multiStepState', 'ACTUATOR_COLORS', 'currentExplanationSvg', 'explanationZoomLevel', 'wsConnection']):
            module_map['core'].append(b)
        elif 'DOMContentLoaded' in s or 'addEventListener(\'keydown\'' in s or 'window.addEventListener(\'load\'' in s:
            module_map['core'].append(b)
        elif s.startswith('//') and len(s) < 100:
            # Short comment
            pass
        else:
            module_map['core'].append(b)

core_prefix = """// =========================================================================
// BRO CORE ENGINE: DOM, TAB LAZY LOADER, SFX, TERMINAL, WS TELEMETRY & INIT
// =========================================================================

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/\"/g, '&quot;')
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
"""

themes_out = "// =========================================================================\n// BRO THEME ENGINE\n// =========================================================================\n\n" + '\n\n'.join(module_map['themes'])
visualizer_out = "// =========================================================================\n// BRO AUDIO VISUALIZERS ENGINE\n// =========================================================================\n\n" + '\n\n'.join(module_map['visualizer'])
voice_out = "// =========================================================================\n// BRO VOICE ENGINE\n// =========================================================================\n\n" + '\n\n'.join(module_map['voice'])
settings_out = "// =========================================================================\n// BRO SETTINGS ENGINE\n// =========================================================================\n\n" + '\n\n'.join(module_map['settings'])
tabs_out = "// =========================================================================\n// BRO TABS ENGINE\n// =========================================================================\n\n" + '\n\n'.join(module_map['tabs'])
core_out = core_prefix + '\n\n' + '\n\n'.join(module_map['core'])

os.makedirs('src/bro/ui/web/js', exist_ok=True)
files_dict = {
    'themes.js': themes_out,
    'visualizer.js': visualizer_out,
    'voice.js': voice_out,
    'settings.js': settings_out,
    'tabs.js': tabs_out,
    'core.js': core_out,
}

for fname, content in files_dict.items():
    p = os.path.join('src/bro/ui/web/js', fname)
    with open(p, 'w') as fp:
        fp.write(content)
    print(f"Wrote {fname} ({len(content)} chars)")

# Validate each file with Chromium
print("\n--- Validating all 6 JS files with Chromium ---")
with sync_playwright() as p:
    browser = p.chromium.launch()
    for fname, content in files_dict.items():
        page = browser.new_page()
        page_err = []
        page.on('pageerror', lambda err: page_err.append(str(err)))
        page.set_content(f"<script>{content}</script>")
        if page_err:
            print(f"FAILED {fname}: {page_err}")
        else:
            print(f"PASSED {fname} [100% VALID SYNTAX]")
        page.close()
    browser.close()
