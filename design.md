# JARVIS Mark 4: System Architecture & Technical Design Specification

## 1. System Overview & Operating Environment

JARVIS Mark 4 is an autonomous, multi-modal cognitive agent designed for local-first execution on Linux workstations.

### Target Hardware & Host Environment
* **Workstation OS**: Linux X11 (Ubuntu / GNOME 42+)
* **GPU**: NVIDIA GeForce RTX 3060 (12 GB GDDR6 VRAM, CUDA Compute 8.6)
* **CPU**: AMD Ryzen 7 (8 cores / 16 threads, x86_64)
* **System RAM**: 96 GB DDR4
* **Local Inference Runtime**: Ollama daemon (`http://localhost:11434`)
* **Audio Synthesis & Recognition**: Edge-TTS Neural Pipeline (`en-GB-RyanNeural`) + Browser Web Speech API / Faster-Whisper GPU (`base`, `float16`)
* **Display Server**: X11 with multi-monitor perception (`mss` + `python-xlib` screen coordinate indexing)

---

## 2. Cognitive Processing Pipeline & Latency Optimization

Jarvis executes an asynchronous **Perception-Reasoning-Action (ReAct)** loop. Every user utterance traverses a deterministic multi-tier cascade optimized for sub-millisecond to sub-second response times:

```
[User Utterance (Voice / Web HUD / Alt+J / Telegram / CLI)]
                       │
                       ▼
    [Tier -1: GreetingMatcher (<1ms CPU Regex)]
      ├─ Match: Returns Instant Voice/Text Greeting (Standard or Gen-Z) ──► Output Delivered (<1ms)
      └─ No Match
           │
           ▼
    [Tier -0b: LocalIntentMatcher (<5ms MD Cache)]
      ├─ Match: Instant Dynamic Execution (time, calendar, file preview) ──► Output Delivered (<5ms)
      └─ No Match
           │
           ▼
    [Acoustic Pre-Response Engine (<200ms)]
      └─ Fires non-blocking verbal ack ("Processing your command...", "On it...")
           │
           ▼
    [Tier-0: Fast Intent Router (Llama 3.2 3B CPU/GPU) (<100ms)]
      ├─ CONVERSATION / DIRECT_QA: Instant explanation/QA reply ──────────► Output Delivered (<150ms)
      └─ COMPLEX_PLAN / SYSTEM_ACTION
           │
           ▼
    [Tier-1: Deep Reasoning Engine (Gemma 4 12B pinned in VRAM) (1-3s)]
      ├─ Step-by-step Tool Calling (JSON Action Schema)
      ├─ Multimodal Visual Verification (Qwen2.5-VL 7B)
      ├─ High-Stakes Action Intercept (Safety Gatekeeper)
      └─ ReAct Loop Execution (Max 15 iterations) ──────────────────────► Task Completed
```

### Multi-Tier Classification Hierarchy
1. **Tier -1 (`GreetingMatcher`)**: Zero-network CPU regex matcher. Evaluates 40+ compiled expressions for greetings, thanks, farewells, and acknowledgments. Resolves in <1ms without invoking LLM or disk I/O. Supports time-bucketed salutations (morning, afternoon, evening, night) and a configurable Gen-Z mode.
2. **Tier -0b (`LocalIntentMatcher`)**: Sub-5ms deterministic pattern matcher for frequent operational commands defined in `local_intents.md`. Uses MD5 hash caching in `local_intents_cache.json` and parameterized regex groups (e.g., `{file}`). Supports dynamic local actions: `time_now`, `calendar_today`, and `show_file_content`.
3. **Acoustic Pre-Response Engine**: Immediately dispatches random non-blocking speech acknowledgments ("Looking into that now...", "One moment, Sir...") before Tier-0 begins inference. Eliminates the perceived silence gap between speech completion and LLM execution.
4. **Tier-0 Fast Classifier (`llama3.2:3b`)**: Lightweight model (offloaded to CPU or GPU) determining if the query is a simple question (`CONVERSATION`) or a multi-step workflow (`COMPLEX_PLAN`). Conversational answers are generated and returned immediately.
5. **Tier-1 Deep Reasoner (`gemma4:12b`)**: Primary reasoning engine pinned in VRAM via `keep_alive: -1`. Generates structured JSON action payloads adhering to the ReAct protocol.
6. **Vision Perceiver (`qwen2.5vl:7b` / `mss`)**: Multimodal screen inspection model analyzing desktop state, UI buttons, browser layouts, and bounding coordinates.
7. **Cloud Fallback Gateway (`gemini-2.5-flash`)**: Cascading failover provider when local models encounter context limits or when cloud routing is explicitly enabled.

---

## 3. Actuator Subsystems & Tool Protocol

Jarvis tools return structured `ActionResult` objects containing `success: bool`, `output: str`, and optional `screenshot_base64`, `media`, or `step_timings`.

### 1. Desktop GUI Actuator (`src/jarvis/actuators/desktop.py`)
* **Screen Coordinate Mapping**: Interacts via `mss` and `pyautogui` with safety pause (0.1s) and fail-safe corners.
* **Multi-Display Perception**: Supports display indices:
  * `0`: Combined virtual canvas across all physical monitors.
  * `1`: Primary workstation monitor (e.g., DP-1, 1920x1080).
  * `2..N`: Secondary monitors (e.g., DP-2, HDMI-1).
* **Core Actions**: `desktop_click(x, y, button)`, `desktop_double_click(x, y)`, `desktop_type(text, interval)`, `desktop_press_key(key)`, `desktop_hotkey(keys)`, `desktop_scroll(clicks, direction)`, `desktop_drag(x1, y1, x2, y2)`, `desktop_inspect_screen(screen_index)`, `desktop_switch_monitor(screen_index)`.

### 2. Dual-Browser Automation Architecture
* **Everyday Chrome via CDP (`src/jarvis/actuators/cdp_browser.py`)**: Attaches directly to the user's running Chrome instance on port `9222` using Chrome DevTools Protocol (`aiohttp` WebSocket client). Preserves active logins, sessions, cookies, and tabs.
  * Actions: `cdp_navigate(url)`, `cdp_click(selector)`, `cdp_type(selector, text)`, `cdp_evaluate(expression)`, `cdp_list_tabs()`, `cdp_screenshot()`.
* **Isolated Playwright Sandbox (`src/jarvis/actuators/browser.py`)**: Headless/headful sandboxed Chromium instance with dedicated user data directory (`~/.jarvis/browser_data`) for untrusted or isolated web scraping.

### 3. Python Execution Sandbox (`src/jarvis/actuators/python_runner.py`)
* Executes arbitrary Python code via subprocess in isolated working directory.
* Captures standard output, standard error, execution return code, and wall-clock execution time.

### 4. Visual Media & Diagram Actuator (`show_media`)
* Renders interactive visual artifacts directly inside the Web HUD:
  * Mermaid JS Diagrams (`graph TD`, `sequenceDiagram`, `stateDiagram`)
  * Chart.js dynamic data visualizations
  * Syntax-highlighted code viewers with line numbers
  * File content visualizers

### 5. Macro Automation Recorder (`src/jarvis/actuators/recorder.py`)
* Records mouse clicks, keyboard strokes, and timing intervals to `~/.jarvis/macros/<name>.json`.
* Replays automated workstation sequences at native or accelerated speeds.

---

## 4. Security, Secrets Vault & Safety Gatekeeper

### Keyring Vault with Index Registry (`src/jarvis/security/vault.py`)
* **Storage Engine**: System Keyring (`secretstorage` / FreeDesktop Secret Service API) with AES-256 fallback.
* **Key Registry (`~/.jarvis/.vault_index`)**: Dedicated JSON registry tracking stored keys, metadata, timestamps, and description tags without exposing sensitive values.
* **Batch Secret Retrieval (`get_secrets(keys=[...])`)**: Allows the agent to fetch multiple vault keys (e.g., `telegram_bot_token` and `telegram_chat_id`) in a single atomic tool call, reducing round-trip latency by 50%.

### Safety Gatekeeper & High-Stakes Intercept (`src/jarvis/security/safety.py`)
* Scans all planned actions against high-stakes keyword blacklists:
  `["rm -rf", "delete", "destroy", "wipe", "format", "sudo", "passwd", "shutdown", "reboot", "payment", "buy", "purchase", "transfer", "bank", "credit card", "telegram send"]`
* When triggered, pauses execution, generates an approval token, broadcasts a WebSocket modal to the Web HUD, and requires explicit user authorization before continuing.

---

## 5. Timing Telemetry, Observability & Waterfall Debugger

### Microsecond StepRecord Telemetry (`src/jarvis/core/audit.py`)
Each step in an agent run tracks exact timing metrics:
* `tts_ms`: Wall time spent generating or speaking TTS audio.
* `llm_inference_ms`: Time spent in Ollama/Gateway text generation.
* `network_ms`: Network round-trip latency for cloud or remote APIs.
* `tool_ms`: Duration of actuator/tool execution.
* `total_step_ms`: End-to-end duration of the individual step.

### Waterfall Debug Modal (`index.html`)
* An interactive Gantt-style visual timeline modal showing the breakdown of TTS, LLM inference, network latency, and tool execution for every step of a task.
* Displays aggregate runtime metrics, average step latency, and bottleneck classification.

---

## 6. Scheduled Automation, Daily Brief & Memory Engine

### Multi-Slot Daily Brief Engine (`src/jarvis/models/daily_brief.py`)
* Configured in `~/ai-memory/jarvis/daily_brief_config.json`.
* Supports multiple independent briefing slots per day (e.g., `08:00` Morning Standup Brief with Weather + Calendar, `14:00` Midday Markets Brief, `18:00` Evening Summary).
* Each slot configures: `time: "HH:MM"`, `enabled: bool`, `label: str`, and `topics: ["weather", "calendar", "tech_news", "world_news", "hardware"]`.
* Scheduled via `CronEngine` background daemon.

### Workstation Calendar Engine (`src/jarvis/memory/calendar_engine.py`)
* Backed by human-readable markdown file: `~/ai-memory/jarvis/calendar.md`.
* Format: `- [ ] YYYY-MM-DD HH:MM - Event Title #tag1 #tag2`.
* Provides atomic add, toggle, natural language recitation ("How's my calendar today"), and a two-step confirmation complete clear (`DELETE /api/calendar`).

### Lean Markdown Memory Store (`src/jarvis/memory/store.py`)
* Reads structured markdown documents on demand: `preferences.md`, `system.md`, `contacts.md`, `greetings.md`, `workflows/`.
* Integrates optional semantic vector embeddings via `nomic-embed-text` for RAG-augmented recall.

---

## 7. Web HUD Dashboard & Interfaces

### World-Class Glassmorphic Architecture (`src/jarvis/ui/web/index.html`)
* Built with pure HTML5, Vanilla CSS, and WebSocket client — no Node/React build pipeline overhead.
* Dark cybernetic HUD palette: Neon Cyan (`#00f0ff`), Electric Purple (`#9d4edd`), Amber (`#ffaa00`), Carbon Glass backgrounds (`rgba(7, 14, 27, 0.85)`).
* Primary Master Tabs:
  1. **Command Center**: Mission Control input, speech recognition, quick action tiles, live terminal stream, active neural settings container, and hardware telemetry meters.
  2. **Calendar**: Interactive monthly grid, pending task list, voice recital, and atomic task wipe.
  3. **Main Desktop**: Multi-display perception preview, screen index switcher, and resolution metrics.
  4. **Audit & History**: Real-time task logs, interactive SVG velocity flow, step records, and timing waterfall debugger.
  5. **System Alerts**: Sentinel warning logs, watchdog errors, and system health status.
  6. **Memory & Secrets**: Markdown memory file editor, RAG vector stats, and encrypted Keyring Vault manager.
  7. **Settings**: Modular configuration matrix (Model, Voice, Display, Safety, Memory, Watchdogs, Gateway).
  8. **Resources**: Interactive Technical Design Document viewer and system blueprints.
  9. **System Manual**: In-UI tactical handbook and operating guide.

### Dedicated Desktop & Voice Access Modalities
* **Spotlight Bar (`Alt+J`)**: Floating lightweight desktop overlay powered by Tkinter / PyQt for immediate voice/text task execution without opening the browser.
* **Ubuntu GNOME Shortcut (`Super+Shift+J`)**: System-wide keybinding launching the HUD in Audio-Only continuous loop mode.
* **Two-Way Telegram Bot (`jarvis/watchdogs/telegram_bot.py`)**: Remote task dispatch, screenshot retrieval, and audio voice-note processing from mobile.

---

## 8. REST & WebSocket API Reference

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/run` | Execute user task through ReAct loop |
| `GET` | `/api/status` | System health, active models, hardware & settings state |
| `GET` | `/api/models` | List Ollama local models and active selections |
| `POST` | `/api/models/select` | Switch active Tier-0, Text, Vision, or Cloud model |
| `GET` | `/api/voice/greeting` | Fetch contextual random greeting from `greetings.md` |
| `POST` | `/api/voice/select` | Update TTS voice, rate, pitch, volume, STT engine, Gen-Z mode |
| `POST` | `/api/voice/stop` | Barge-in voice stop / halt speech playback |
| `GET` | `/api/calendar` | List calendar schedule events and pending tasks |
| `POST` | `/api/calendar` | Add new scheduled task to `calendar.md` |
| `POST` | `/api/calendar/toggle` | Toggle task completion status |
| `DELETE` | `/api/calendar` | Clear all tasks from memory (`calendar.md`) |
| `GET` | `/api/calendar/today` | Natural language vocal summary of today's schedule |
| `GET` | `/api/brief/slots` | Fetch all scheduled daily brief time slots |
| `POST` | `/api/brief/slots` | Save updated daily brief slot matrix |
| `POST` | `/api/brief/trigger` | Manually generate and speak daily briefing |
| `GET` | `/api/vault/list` | List vault secrets using `.vault_index` registry |
| `POST` | `/api/vault/set` | Set secret key in system vault |
| `DELETE` | `/api/vault/delete` | Remove secret key from vault and index |
| `GET` | `/api/docs/design` | Serve this technical design document |
| `WS` | `/ws` | Real-time bi-directional streaming for terminal, logs, audio & HUD events |

---

## 9. Configuration Schema (`config.yaml`)

```yaml
conversation_mode: audio+chat      # Options: audio_only | audio+chat | chat_only
output_mode: both                  # Options: both | cli | voice
autonomous_mode: false             # Bypasses high-stakes confirmation if true

model:
  policy: local_only               # Options: local_only | tier_fallback | cloud_only
  tier0_enabled: true
  tier0_model: llama3.2:3b
  tier0_timeout: 5.0
  tier0_device: cpu                # Options: cpu | gpu
  local_text_model: gemma4:12b
  local_vision_model: qwen2.5vl:7b
  cloud_model: gemini-2.5-flash
  ollama_url: http://localhost:11434
  keep_alive: -1                   # -1 keeps weights locked in VRAM

voice:
  enabled: true
  whisper_model: base
  device: cuda
  compute_type: float16
  tts_voice: en-GB-RyanNeural
  tts_rate: +2%
  tts_pitch: -4Hz
  tts_volume: 100
  always_voice_response: false
  voice_reply_on_chat: true
  stt_engine: browser              # Options: browser | whisper_local
  sfx_enabled: true
  gen_z_greetings: false           # Enables Gen-Z slang & salutations

safety:
  prompt_on_high_stakes: true
  high_stakes_keywords: ["rm -rf", "delete", "destroy", "wipe", "format", "sudo", "passwd", "shutdown", "reboot", "payment", "buy", "purchase", "transfer", "bank", "credit card"]

desktop:
  screen_index: 1                  # 0: Combined canvas, 1: Primary, 2: Secondary

web_ui:
  host: 0.0.0.0
  port: 8765
```
