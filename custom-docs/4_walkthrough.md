# Walkthrough: Web UI Decluttering & Modernization

Bro Variant 1 has completed the comprehensive overhaul outlined in [`custom-docs/ui_improvement_plan.md`](file://custom-docs/ui_improvement_plan.md), including the dedicated Fullscreen Audio HUD controller.

---

## Key Changes & Completed Features

### 1. Dedicated Settings Tab & Topbar Decluttering
- **Topbar Streamlining**: Removed the screen selector, voice selector, speed slider, AI model policy pills, and Daily Brief button from the header navigation bar. The topbar is now focused on status, core connectivity, conversation mode pills, and the master kill-switch.
- **Unified Master Settings Panel (`#tab-settings`)**: Built a structured 5-section settings panel:
  1. **AI Brain & Execution Policy**: 1-click segmented switching between 100% Local LLM (Local GPU), Cloud Gemini 3.8/2.5 Flash, and Hybrid Fallback Tier, plus dynamic model dropdowns and API key management.
  2. **Autonomous Execution & Safety Gatekeeper**: Real-time toggle switch with status badge (`APPROVAL OVERLAY ACTIVE` vs `FULL AUTONOMY UNLOCKED`).
  3. **Voice Persona, Speech Speed & Bro Volume**: Neural Edge-TTS voice actor dropdown, speed rate slider (0.50x – 2.00x), and master volume slider (0% – 100%).
  4. **Workstation Perception & Active Display**: Multi-monitor selection dropdown with display inspect and screen capture capabilities.
  5. **Watchdogs & Telemetry Thresholds**: Thermal Sentinel, Download Auto-Organizer, and Alt+J Spotlight shortcuts.

### 2. Bro Master Volume Control (0% – 100%)
- Added `tts_volume: int = 100` in [`src/bro/config.py`](file://src/bro/config.py) and [`config.yaml`](file://config.yaml).
- Updated [`src/bro/voice/tts.py`](file://src/bro/voice/tts.py) to pass volume percentages into `edge_tts.Communicate(..., volume=vol_str)` and `-volume <pct>` flags to `ffplay`/`mpv`.
- Added volume sliders in `#tab-settings` with live percentage badges and interactive **Play / Test** triggers.

### 3. Fullscreen Audio-Only HUD Experience (Cinematic Mode)
- Fixed and implemented the **Fullscreen HUD** controller for **Audio Only** mode:
  - Added `.audio-only-card.hud-fullscreen` styling with dark holographic radial glow, scaled Arc Reactor core (220px), rotating dashed rings, responsive waveform equalizers, large subtitle transcript, and quick prompt chips.
  - Implemented `toggleAudioFullscreen()`, `enterAudioFullscreen()`, and `exitAudioFullscreen()` with browser Fullscreen API integration.
  - Added native `fullscreenchange`, `webkitfullscreenchange`, and <kbd>Esc</kbd> key listeners so exiting fullscreen via keyboard or browser gestures stays synchronized.
  - Added a clear red **Exit Fullscreen** button pinned to the header in fullscreen mode.

### 4. Interactive Proactive Sentinels Matrix
- All 6 watchdog cards in the Proactive Sentinels Matrix (Thermal Sentinel, Download Auto-Organizer, Tier-0 Classifier, Alt+J Spotlight, Everyday Chrome CDP, Telegram Remote) are now interactive.
- Clicking any card sends a toggle request to `POST /api/watchdogs/toggle` and instantly updates daemon configuration and UI status dots.

### 5. Consolidated Model Selection & Telemetry Tabs
- Retired the standalone **Model Selection** and **Telemetry & Watchdogs** tabs.
- Existing internal navigation links automatically route into the centralized **Settings** tab.

### 6. Audit & History Clear with Automatic Safety Backup
- Added a **Clear Audit & Reset Metrics** button in the Audit Trail header.
- Clicking prompts a dark glassmorphic confirmation modal.
- On confirmation, `POST /api/history/clear` calls [`AuditManager.backup_and_clear()`](file://src/bro/core/audit.py#L138-L172):
  - Copies all past runs and step screenshots to timestamped backup: `~/ai-memory/bro/backups/audit_backup_<timestamp>/`.
  - Clears history runs from disk and resets live KPI analytics (Total Missions, Success Rate, Execution Time, Steps) to zero.

### 7. Two-Column Memory Tree & Keyring Vault Browser
- Redesigned `#tab-memory` into a glassmorphic two-column layout:
  - **Left Sidebar**: Renders folder and file hierarchy (Root Files: `preferences.md`, `system.md`, `contacts.md`; Folders: `workflows/telegram.md`) with New File creation, plus a `Keyring Vault (Secrets)` navigation button.
  - **Right Viewport**:
    - **Active Markdown Document Editor**: Live character and line counter, auto-path resolution, Revert, and Save buttons.
    - **Keyring Vault View**: Displays encrypted secrets stored in the workstation keyring (`vault.list_keys()`) and an input form to store/update secrets.

---

## Visual Verification & Screenshots

### Fullscreen Audio-Only HUD (Cinematic View)
![Fullscreen Audio HUD](docs/assets/fullscreen_audio_hud_1790068406738.png)

### Restored Normal Layout (After Exiting Fullscreen)
![Restored Normal HUD](docs/assets/restored_normal_hud_1790068543435.png)

### Settings Master Control Tab
![Settings Tab](docs/assets/settings_tab_1790066721108.png)

### Audit & History Tab (Clear Confirmation Modal)
![Audit & History Tab](docs/assets/audit_history_tab_1790066847837.png)

### Memory & Secrets Tab (Two-Column Tree Layout)
![Memory & Secrets Tab](docs/assets/memory_secrets_tab_1790067069043.png)

### Audio Fullscreen HUD Test Recording
![Audio Fullscreen HUD Test](docs/assets/fullscreen_audio_hud_test_1790068048974.webp)

---

## Automated Test Results

Ran `uv run pytest` covering the entire test suite including [`tests/test_ui_settings.py`](file://tests/test_ui_settings.py):

```bash
platform linux -- Python 3.11.15, pytest-9.1.1, pluggy-1.6.0
collected 52 items                                                             

tests/test_agent.py .....                                                [  9%]
tests/test_audit.py ..                                                   [ 13%]
tests/test_config.py ....                                                [ 21%]
tests/test_memory.py ....                                                [ 28%]
tests/test_ollama_provider.py .....                                      [ 38%]
tests/test_python_runner.py ...                                          [ 44%]
tests/test_recorder.py .                                                 [ 46%]
tests/test_safety.py ...                                                 [ 51%]
tests/test_tier0.py ..                                                   [ 55%]
tests/test_tts.py ......                                                 [ 67%]
tests/test_ui_memory_config.py ...                                       [ 73%]
tests/test_ui_models.py ...                                              [ 78%]
tests/test_ui_settings.py .....                                          [ 88%]
tests/test_ui_voice.py ....                                              [ 96%]
tests/test_watchdogs.py ..                                               [100%]

======================== 52 passed, 2 warnings in 3.18s ========================
```

---

## Hands-Free Continuous Microphone Loop

### Root Cause Analysis & Solution
- **The Issue**: Previously, speech recognition only attempted to re-arm inside `audio_only` mode, and used an artificial delay calculation (`words * 380ms`, up to 15 seconds) which blocked users while the UI was stuck in "BRO SPEAKING". In `audio+chat` mode, speech recognition never re-armed at all, and any silence timeout caused Chrome's `webkitSpeechRecognition` to fire `onend` and die silently without restarting.
- **Architectural Fix**:
  1. **Synchronous Speech & Voice State Broadcasting**: Updated [`src/bro/core/agent.py`](file://src/bro/core/agent.py) so `self.tts.speak(text, blocking=True)` executes and blocks until local audio playback finishes, broadcasting `self.console.action("voice", "Speaking response...")`. WebSocket `task_finish` now deterministically signifies that speech has completed.
  2. **Event-Loop Safe Audio Synthesis**: Updated [`src/bro/voice/tts.py`](file://src/bro/voice/tts.py) to check for running event loops in caller threads before invoking `asyncio.run`.
  3. **Robust Re-Arming Protocol in Web UI**: Updated [`src/bro/ui/web/index.html`](file://src/bro/ui/web/index.html):
     - Added `isTaskExecuting`, `shouldKeepListening`, and `scheduleRecognitionRestart(delayMs)` with clean state transitions.
     - Automatically schedules safe re-arming (700ms acoustic clearance buffer) upon `task_finish` in both **Audio Only** mode and standard **Command Center** input bar (`#mic-btn`).
     - Added silence timeout recovery on `onerror ('no-speech')` and `onend` so natural pauses do not disconnect the microphone.
     - Added synchronized `Hands-Free Continuous Microphone Loop` checkbox in Settings Tab (Card 3) alongside the Audio HUD switch.

### Visual Verification: Hands-Free Dialogue & Arc Reactor Re-Arming
![Audio Only Arc Reactor HUD](docs/assets/audio_only_hud_1790070426982.png)

### Settings Tab Synchronized Hands-Free Toggle
![Settings Hands-Free Toggle](docs/assets/settings_voice_card_1790071411144.png)

### Browser Test Recording
![Hands-Free Continuous Loop Test](docs/assets/test_handsfree_loop_1790070266857.webp)

---

## Phase 5: Tactical UI, Sentinel Matrix, Overlay & Auth Modernization

### 1. Memory Storage Directory Relocated to Settings Tab
- **Moved to Settings Tab**: Relocated the persistent Memory & Knowledge Storage Directory configuration (`preferences.md`, `system.md`, `contacts.md`, etc., default `~/ai-memory/bro`) into [`src/bro/ui/web/index.html`](file://src/bro/ui/web/index.html) under `#tab-settings` as **CARD 6**.
- **Cleaner Memory Tab**: Removed the redundant config card from `#tab-memory`, keeping that view 100% focused on the glassmorphic 2-column Neural Tree and Keyring Vault browser.
- **Dynamic Real-time Binding**: Wired `loadMemoryConfig()` into `switchTab('settings')` and page boot. Users can configure the path, click "Save & Migrate", and verify directory contents immediately.

### 2. Cloud Gemini Model & Google AI Pro Authentication
- **Why Antigravity IDE differs from Standalone Python**: Antigravity IDE connects to internal Google Cloud endpoints via IDE-managed OAuth session cookies and developer credentials. Standalone Python daemons calling `google-genai` communicate via public Google GenAI endpoints.
- **Flexible Dual-Auth Provider Support**: In [`src/bro/models/gemini_provider.py`](file://src/bro/models/gemini_provider.py), enhanced `GeminiProvider.__init__` to automatically detect:
  1. `GEMINI_API_KEY` (configured via UI or environment)
  2. `GOOGLE_API_KEY`
  3. Google Cloud Vertex AI Application Default Credentials (ADC) via `gcloud auth application-default login` (`~/.config/gcloud/application_default_credentials.json`).
- **Free-Tier Solution**: Even with Google AI Pro, obtaining a dedicated API Key from [Google AI Studio](https://aistudio.google.com/apikey) takes 1 click, is completely free ($0 / 15 RPM / 1M TPM / 1500 RPD), and does not require paid credit card billing.

### 3. Tier-0 Fast Classifier Phase & Configuration
- **Execution Phase**: Runs at **Phase 0 (Pre-Planning & Triage)** in [`src/bro/core/agent.py`](file://src/bro/core/agent.py#L123-L125). Before engaging the deep planner or invoking Cloud Gemini, the user's prompt is routed through Tier-0 in sub-100ms via `llama3.2:3b`. If classified as simple chit-chat, status, or basic query, Tier-0 answers instantly, bypassing heavy planning loops and saving token latency.
- **Configuration Locations**:
  1. [`config.yaml`](file://config.yaml): `model.tier0_enabled: true`, `model.tier0_model: "llama3.2:3b"`, `model.tier0_timeout: 0.8`.
  2. **Settings Tab (Card 1)**: `#sel-tier0-model` dropdown allows dynamically choosing the classifier model (`llama3.2:3b`, `qwen2.5:1.5b`, etc.).
  3. **Proactive Sentinels Matrix (Card 4)**: Real-time interactive toggle switch to enable/disable Tier-0 on the fly.

### 4. Overhauled Minimalist Approval Overlay
- **Modern Minimalist Window**: Completely redesigned [`src/bro/ui/overlay.py`](file://src/bro/ui/overlay.py):
  - Expanded fixed dimensions from cramped `520x300` to a spacious `640x420`.
  - Upgraded typography using clean system fonts (`Inter`, `SF Pro Display`, `Segoe UI`) and monospace (`JetBrains Mono`, `Fira Code`) with generous line spacing.
  - Deep space dark theme (`#070c18` background, `#0b1326` card, subtle `#162544` border) matching the HUD.
  - Added dynamic risk pill (`CRITICAL RISK` vs `HIGH RISK`), clear risk reason explanation, and an elevated syntax-highlighted command codeblock (`#030712`, `#00f0ff` text).
  - Minimalist shortcut action buttons: `[Esc] Reject Operation` (subtle red outline) and `[↵ Enter] Authorize Execution` (cyan/emerald gradient with dark text).
- **Preview & Test Endpoint**: Added `POST /api/safety/test-overlay` in [`src/bro/ui/server.py`](file://src/bro/ui/server.py) and a **Preview Approval Dialog** button in Settings (Card 2).

### 5. Proactive Sentinels Matrix UX Overhaul
- **Luminous Active States**:
  - Added `.watchdog-card.is-active`: Glowing cyan/emerald border (`rgba(0, 240, 255, 0.45)`), luminous radial gradient glow, and vibrant badge text.
  - Added `.watchdog-card.is-inactive`: Dimmed, low-opacity card with dark borders (`rgba(255, 255, 255, 0.05)`).
- **Dedicated Toggle Switches**: Added compact, glassmorphic toggle slider switches (`.matrix-toggle`) inside each card header alongside the title. Clicking either the toggle switch or the card toggles state via `POST /api/watchdogs/toggle`.
- **Live Sync**: `updateSentinelCard()` synchronizes all 6 cards with live daemon status on every polling tick.

---

## Visual Verification: Phase 5 Enhancements

### Proactive Sentinels Matrix with Toggles & Glow Borders
![Sentinels Matrix with Toggles](docs/assets/sentinels_matrix_toggled_1790073061309.png)

### Settings Tab (Card 6: Memory & Knowledge Storage Directory)
![Settings Tab Memory Storage](docs/assets/settings_tab_memory_storage_1790073775583.png)

### Clean Two-Column Neural Memory & Keyring Vault
![Clean Memory Tab](docs/assets/memory_secrets_tab_clean_1790073908352.png)

### Settings Tab (Top Controls & Safety Gatekeeper Preview)
![Settings Tab Top](docs/assets/settings_tab_top_1790073674922.png)


