import os

with open('scratch_main.js') as f:
    lines = f.readlines()

themes_js = ''.join(lines[334:413])

visualizer_js = ''.join(lines[413:761]) + '\n\n' + ''.join(lines[1935:2021])

voice_js = (
    '// =========================================================================\n'
    '// BRO VOICE ENGINE: VOLUME, SPEECH RECOGNITION, TTS & CONVERSATION LOOP\n'
    '// =========================================================================\n\n'
    + ''.join(lines[145:198]) + '\n\n'
    + ''.join(lines[1460:1627]) + '\n\n'
    + ''.join(lines[1689:1935]) + '\n\n'
    + ''.join(lines[2021:2420]) + '\n\n'
    + ''.join(lines[4630:4649])
)

settings_js = (
    '// =========================================================================\n'
    '// BRO SETTINGS & CONFIGURATION ENGINE\n'
    '// =========================================================================\n\n'
    + ''.join(lines[62:145]) + '\n\n'
    + ''.join(lines[198:232]) + '\n\n'
    + ''.join(lines[960:974]) + '\n\n'
    + ''.join(lines[2450:2935]) + '\n\n'
    + ''.join(lines[3400:3505]) + '\n\n'
    + ''.join(lines[4944:4975])
)

tabs_js = (
    '// =========================================================================\n'
    '// BRO TAB MODULES: DISPLAYS, HISTORY, MEMORY, CALENDAR, ALERTS, RESOURCES\n'
    '// =========================================================================\n\n'
    + ''.join(lines[951:960]) + '\n\n'
    + ''.join(lines[1341:1460]) + '\n\n'
    + ''.join(lines[3036:3400]) + '\n\n'
    + ''.join(lines[3506:3708]) + '\n\n'
    + ''.join(lines[3708:4188]) + '\n\n'
    + ''.join(lines[4299:4630]) + '\n\n'
    + ''.join(lines[4649:4786])
)

core_prefix = '''// =========================================================================
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
'''

core_js = (
    core_prefix + '\n\n'
    + ''.join(lines[232:334]) + '\n\n'
    + ''.join(lines[761:951]) + '\n\n'
    + ''.join(lines[974:1341]) + '\n\n'
    + ''.join(lines[1627:1689]) + '\n\n'
    + ''.join(lines[2420:2450]) + '\n\n'
    + ''.join(lines[2935:3036]) + '\n\n'
    + ''.join(lines[4188:4299]) + '\n\n'
    + ''.join(lines[4786:4944]) + '\n\n'
    + ''.join(lines[4975:])
)

os.makedirs('src/bro/ui/web/js', exist_ok=True)
with open('src/bro/ui/web/js/themes.js', 'w') as f: f.write(themes_js)
with open('src/bro/ui/web/js/visualizer.js', 'w') as f: f.write(visualizer_js)
with open('src/bro/ui/web/js/voice.js', 'w') as f: f.write(voice_js)
with open('src/bro/ui/web/js/settings.js', 'w') as f: f.write(settings_js)
with open('src/bro/ui/web/js/tabs.js', 'w') as f: f.write(tabs_js)
with open('src/bro/ui/web/js/core.js', 'w') as f: f.write(core_js)

print('Successfully created all 6 modular JS files!')
