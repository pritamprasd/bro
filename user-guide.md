# 📘 JARVIS // Mark 2: Comprehensive User Guide

Welcome to **JARVIS // Mark 2**, your autonomous, multi-modal personal AI assistant built for Linux X11 workstations powered by an **NVIDIA RTX 3060 (12 GB VRAM)**, **AMD Ryzen 7 (16 threads)**, and **96 GB of RAM**.

This guide covers everything you need to operate, customize, and communicate with Jarvis across voice, desktop GUI, terminal, and mobile remote control.

---

## Table of Contents
1. [How Jarvis Works: Architecture & Runtime Processes](#1-how-jarvis-works)
2. [Lifecycle: Starting & Stopping Jarvis (Kill-Switch)](#2-lifecycle-management)
3. [Command Center Homepage Widgets](#3-command-center-homepage-widgets)
4. [How to Communicate with Jarvis (4 Modalities)](#4-communication-modalities)
   - [A. Web HUD Dashboard (Interactive Microphone)](#a-web-hud-dashboard)
   - [B. Desktop Spotlight Bar (Alt + J)](#b-desktop-spotlight-bar-alt--j)
   - [C. Terminal CLI & Voice (`jarvis voice`)](#c-terminal-cli--voice)
   - [D. Telegram Remote Control from Phone](#d-telegram-remote-control)
5. [Resource Attachments & On-Demand Missing File Prompting](#5-resource-attachments--on-demand-prompting)
6. [Conversational Voice Assistant & Voice Reply Toggle](#6-conversational-voice-assistant)
7. [Daily Brief: On-Demand & Scheduled](#7-daily-brief)
8. [Selecting Local Models from Ollama](#8-selecting-local-models)
9. [Desktop & Web Automation Capabilities](#9-automation-capabilities)
   - [Vision-based Computer Use](#vision-based-computer-use)
   - [Dual Browser Strategy (Everyday Chrome CDP vs Isolated Sandbox)](#dual-browser-strategy)
   - [Python Runner & Telegram Bot Tasks](#python-runner)
   - ["Watch & Learn" Macro Recorder](#watch--learn-macro-recorder)
10. [Safety Gatekeeper & Approval Overlay](#10-safety-gatekeeper)
11. [Audit Trail, Visual Analytics & Lightbox Inspection](#11-audit-trail--visual-analytics)
12. [System Failure Alerts & Error Logs](#12-system-alerts--error-logs)
13. [Lean Memory & Vault Secrets](#13-lean-memory--vault-secrets)
14. [In-UI System Manual & Documentation Handbook](#14-in-ui-system-manual)
15. [Visual Media Display: Diagrams, Charts & System Windows](#15-visual-media-display)
16. [Multi-Desktop & Display Perception Setup](#16-multi-desktop--display-perception-setup)
17. [Terminal Typography & Interactive Font Scaling](#17-terminal-typography--interactive-font-scaling)
18. [World-Class Glassmorphic HUD Design & Layout Architecture](#18-world-class-glassmorphic-hud-design--layout-architecture)
19. [Architectural Evolution: Mark 1 vs. Mark 2](custom-docs/upgrades_mark1_and_mark2.md)

---

## 1. How Jarvis Works

Jarvis operates on an asynchronous **Perception-Reasoning-Action (ReAct)** cognitive loop with multi-tier intelligence:

```
[User Input] (Voice / Web HUD / Alt+J / Telegram / CLI)
     │
     ▼
[Tier-0 Instant Router: Llama 3.2 3B] (<100ms intent classification)
     │
     ├── If Conversation ──> Direct Assistant Voice Reply (Iron Man JARVIS)
     │
     └── If Complex Task ──> [Tier-1 Logic: Gemma 4 12B] (Kept pinned in VRAM)
                                  │
                                  ├── Visual Inspection ──> [Qwen2.5-VL 7B]
                                  ├── Missing Resource? ──> [On-Demand File Modal]
                                  ├── High-Stakes Action? ──> [Approval Overlay]
                                  └── Actuators:
                                        ├── Desktop GUI (mss + pyautogui)
                                        ├── Everyday Browser (Chrome CDP :9222)
                                        ├── Sandboxed Web (Playwright)
                                        └── Python Runner (Data/Telegram)
```

### Runtime Processes When Jarvis is Running (`jarvis start`):
When you run `jarvis start`, a centralized **Process Supervisor** (`jarvis/core/supervisor.py`) coordinates two background processes:
1. **`ui_server` (FastAPI + Uvicorn on port 8765):** Serves the Jarvis Tactical HUD dashboard and manages WebSocket streaming, hardware telemetry, audit runs, and model switching.
2. **`worker` daemon:** Listens for the global <kbd>Alt</kbd> + <kbd>J</kbd> desktop hotkey, runs the Two-Way Telegram polling bot, and manages hardware sentinels.

---

## 2. Lifecycle Management

### Starting Jarvis
To start all background components (Web HUD, Spotlight Bar, Telegram Bot, Watchdogs):
```bash
uv run jarvis start
```
* The Web HUD will be accessible at: [`http://127.0.0.1:8765`](http://127.0.0.1:8765)
* The Spotlight Bar is armed: press <kbd>Alt</kbd> + <kbd>J</kbd> anywhere on your desktop.

### Checking System Status
```bash
uv run jarvis status
```
Displays running PIDs, Web HUD address, and hardware health.

### Stopping Jarvis (Master Kill-Switch)
To immediately and cleanly terminate all Jarvis services:
- **Via CLI:**
  ```bash
  uv run jarvis stop
  ```
- **Via Web HUD:** Click the red **🛑 KILL SWITCH** button in the top right header.
- **Via Telegram:** Send `/kill` to your bot.

---

## 3. Command Center Homepage Widgets & UI Controls

The Command Center ([`http://127.0.0.1:8765`](http://127.0.0.1:8765)) serves as your tactical mission control with precision-aligned controls, real-time hardware intelligence, and live task execution:

1. **Precision 52px Prompt Input Bar:**
   - Seamlessly integrated 52px control bar with matching 12px border radius.
   - Text input supporting instant speech-to-text or typed instructions (<kbd>Enter</kbd> to execute).
   - Reactive **🎙️ Microphone Button** with active pulse animation during voice recording.
   - Bold **🚀 Execute Button** aligned with surgical precision.

2. **Holographic Quick Action Launchers (6 Uniform Tiles):**
   - **☀️ Daily brief:** Spoken workstation health summary via Iron Man Ryan voice.
   - **📋 Paste Clip:** Instantly injects current desktop clipboard into the task prompt.
   - **🌐 Attach Chrome:** One-click launch of everyday Chrome with remote debugging on `:9222`.
   - **📁 Organize Files:** Triggers rule-based categorization of `~/Downloads`.
   - **📷 Inspect Screen:** Captures active desktop and analyzes open windows via Qwen2.5-VL.
   - **📊 Show Diagram:** Opens the Jarvis Mark 2 Tactical Architecture diagram in high-res SVG.

3. **Resource Attachment Bar:**
   - Easily attach local files (`.csv`, `.pdf`, `.png`, `.py`, `.json`) directly to your mission before execution.
   - One-click removal chips with file paths.

4. **Terminal Console & Font Scaler Controls:**
   - **Live WebSocket Stream Active:** Real-time bi-directional telemetry streaming.
   - **Interactive Font Size Stepper (`Font: [A-] [15px] [A+] [Reset]`):** Scale terminal font dynamically between 12px and 26px on the fly. Font preference is automatically saved in browser `localStorage`.
   - **📋 Copy:** Copies the full terminal output to your clipboard.
   - **🧹 Clear:** Clears log lines while preserving the live connection.
   - **Enhanced Legibility:** Powered by JetBrains Mono 500 weight, relaxed 1.7 line height, 0.022em letter spacing, and distinct translucent badge accents for thoughts, actions, steps, results, and errors.

5. **Mission Progress Indicator:** Animated glowing progress bar displaying active mission step title (e.g. `Step 2/5`) and percentage during autonomous execution.

6. **Recent Missions Activity Feed:** Live activity stream on the homepage displaying the last 3 completed missions with duration, status tag, and an **Inspect** button linking directly into the Audit tab.

7. **Hardware Telemetry & Multi-Disk Storage Health:**
   - GPU Temperature (°C) with safety threshold alert (>80°C).
   - Dedicated VRAM meter (`/ 12288 MB`).
   - 96 GB System RAM usage.
   - 16-thread Ryzen CPU load.
   - **Root Storage (NVMe `/`):** Used vs total GB and percent bar.
   - **Secondary Storage (`/mnt/HDD-500GB/`):** Live capacity tracking.

8. **Live Watchdogs Sentinels Matrix:** Real-time status cards for:
   - 🛡️ **Thermal Sentinel** (Active <80°C)
   - 📁 **Download Auto-Sort** (Watching `~/Downloads`)
   - 🌐 **CDP Everyday Chrome** (Port 9222 status)
   - ⚡ **Tier-0 Fast Classifier** (<100ms Llama 3.2 3B)
   - ⌨️ **Spotlight Hotkey** (<kbd>Alt</kbd> + <kbd>J</kbd> Armed)
   - 📱 **Telegram Remote** (Bot Polling Active)

---

## 4. Communication Modalities

You can communicate with Jarvis using four distinct methods:

### A. Web HUD Dashboard (Interactive Microphone)
1. Open [`http://127.0.0.1:8765`](http://127.0.0.1:8765) in Chrome or Brave.
2. Click the 🎙️ **Microphone Button** next to the input box.
3. Speak your command (e.g. *"Hello Jarvis"*, *"Open calculator and compute 123 times 456"*).
4. The HUD transcribes your voice in real time and executes the task automatically.

### B. Desktop Spotlight Bar (<kbd>Alt</kbd> + <kbd>J</kbd>)
Press <kbd>Alt</kbd> + <kbd>J</kbd> from any window (VS Code, terminal, browser, desktop):
* A floating translucent HUD appears in the center of your screen.
* **Context-Aware:** It automatically captures the title of your active window and any text in your clipboard.
* Type your goal and hit <kbd>Enter</kbd>. Press <kbd>Esc</kbd> to dismiss.

### C. Terminal CLI & Voice
* **Direct Task Execution:**
  ```bash
  uv run jarvis run "Summarize Wikipedia article on Artemis II" -f ~/Downloads/paper.pdf
  ```
* **Dedicated Voice Mode:**
  ```bash
  uv run jarvis voice
  ```
  Listens to your microphone for 5 seconds using `faster-whisper` on your RTX 3060, transcribes the speech, and executes.

### D. Telegram Remote Control
Message your private bot from your phone anywhere:
* `/run <goal>`: Executes tasks on your workstation and streams results back.
* `/status`: Returns live CPU, RAM, GPU temperature, and VRAM telemetry.
* `/screen`: Captures a high-resolution screenshot of your workstation display and sends the image to your phone.
* `/kill`: Emergency kill-switch.

---

## 5. Resource Attachments & On-Demand Prompting

Jarvis Mark 2 can ingest and analyze documents, datasets, and scripts:

### Attaching Files Upfront
- **In Web HUD:** Click **📎 Attach File / Resource** or drag & drop files into the resource bar. Files are uploaded to `~/.jarvis/attachments/` and previewed for the model.
- **In CLI:** Pass one or more files with `-f` or `--file`:
  ```bash
  uv run jarvis run "Analyze sales trends" -f ./q3_sales.csv -f ./q4_sales.csv
  ```

### On-Demand Missing File Prompting
If you ask Jarvis to perform a task requiring a file that you forgot to attach (e.g., *"Summarize the financial projection spreadsheet"*), Jarvis detects the missing resource during reasoning and calls `request_file`:
1. **Interactive Prompt Modal Appears:** Execution pauses safely.
2. **Supply Options:**
   - **Option 1:** Pick or drop the required file to upload.
   - **Option 2:** Enter an existing local file path on your system (e.g. `~/finances/proj.xlsx`).
   - **Option 3:** Click **File Unavailable / Skip** to gracefully let Jarvis know the file cannot be provided so it can try an alternative plan.
3. Once supplied, Jarvis immediately resumes execution with the file loaded into context.

---

## 6. Conversational Voice Assistant & Web UI Modes

Jarvis Mark 2 speaks with the **Iron Man British AI persona** (`en-GB-RyanNeural`, tuned pitch `-4Hz`, rate `+2%`).

### Web UI Conversation Modes:
You can choose your conversational modality at any time using the header segmented selector or settings:
1. **🎙️ Audio Only (`audio_only`):**
   - Immersive hands-free voice dialogue!
   - Reveals an animated **Iron Man Arc Reactor Voice Interface** with dynamic soundwave equalizers.
   - **Hands-Free Continuous Loop:** When enabled, the microphone automatically re-arms after Jarvis finishes speaking, enabling fluid, continuous back-and-forth verbal dialogue without touching the keyboard or mouse.
   - Live visual subtitle captions show both user speech and Jarvis replies.
2. **⚡ Audio + Chat (`audio+chat` - Default):**
   - The ideal operational hybrid.
   - Real-time terminal streaming, ReAct thoughts, and action chips alongside spoken voice replies for all conversational interactions and task finishes.
3. **💬 Chat Only (`chat_only`):**
   - Silent text-only interaction.
   - Spoken audio playback is completely muted.
   - Jarvis executes commands and replies silently in the terminal and chat console.

### Configuration in `config.yaml`:
```yaml
# Conversation mode: "audio_only", "audio+chat", or "chat_only"
conversation_mode: "audio+chat"

voice:
  enabled: true
  voice_reply_on_chat: true    # Speak answers to conversational chat
  always_voice_response: false  # Speak answers to all tasks
```

* **Chat & Greetings:** If you say *"Hello"*, *"Who are you?"*, or ask general questions, Jarvis recognizes this as a conversational intent and speaks back as your AI butler.
* **Header Toggle:** Click **🔊 Voice Reply: ON / OFF** or the mode pills in the top header to cycle modes instantly.

### Edge-TTS Neural Voice Persona & Speed Rate Controls:
You can dynamically customize Jarvis's spoken voice persona and playback speed directly from the Web HUD:
* **Header Controls Capsule:**
  - **Voice Dropdown (`VOICE:`):** Switch between curated neural voices (British male `en-GB-RyanNeural`, American male `en-US-GuyNeural`, American female `en-US-JennyNeural`, Sonia, Christopher, etc.) or any installed Edge-TTS language voice.
  - **Speech Speed Slider (`SPD:`):** Interactive range slider from **0.50x (Slow)** to **2.00x (Hyper)** with real-time numeric multiplier badge (`1.00x` = `+0%`, `1.25x` = `+25%`, `1.50x` = `+50%`, etc.). Dragging adjusts speed on the fly.
  - **Instant Voice & Speed Preview (`🔊 Test`):** Click to hear a vocal greeting synthesized at the exact voice persona and speed currently selected.
* **Audio-Only HUD & Model Selection:**
  - Dedicated speed sliders and badges are also integrated into the continuous Audio-Only Mission Control HUD and under Tab 2 (**Model Selection** -> **Card 4: Voice Persona & Speech Speed**).
  - A convenient **Reset** button in the Model Selection tab returns voice speed to the standard `1.00x (+0%)` default with one click.
* **Instant Hot-Swap & Configuration Persistence:**
  - Changing voice or speed immediately updates runtime TTS and writes to `config.yaml` (`tts_voice` and `tts_rate`), broadcasting updates across all open browsers and devices without requiring a server restart.

---

## 7. Daily Brief

The Daily Brief delivers a spoken and visual summary of workstation readiness, memory synchronization, and date/time.

* **On-Demand via CLI:**
  ```bash
  uv run jarvis brief
  ```
* **On-Demand via Web HUD:** Click the yellow **☀️ Daily brief** button in the top navigation bar.
* **Auto-Start:** By default, auto-start is **disabled** so Jarvis never interrupts you unexpectedly. If you want scheduled morning briefings at 08:30 AM, toggle it in `config.yaml` (`watchdogs.cron.enabled: true`).

---

## 8. Selecting AI Execution Engine (Local LLM vs Cloud Gemini 3.8 Flash vs Hybrid)

Jarvis Mark 2 supports flexible, zero-friction AI execution across local hardware and cloud intelligence:

```
                  ┌──────────────────────────────────────────────┐
                  │          AI Execution Engine Policy          │
                  └───────┬──────────────┬──────────────┬────────┘
                          │              │              │
           ┌──────────────▼────┐   ┌─────▼────────┐   ┌─▼──────────────────┐
           │ 🖥️ Local LLM Only  │   │ ☁️ Cloud Only │   │  ⚡ Hybrid Fallback │
           │ (RTX 3060 / Ollama│   │ (Gemini 3.8  │   │  (Local first,     │
           │  100% Private, $0)│   │  Flash API)  │   │   auto-escalates)  │
           └───────────────────┘   └──────────────┘   └────────────────────┘
```

### 1. Instant 1-Click Header Capsule
In the top navigation controls bar, you can instantly toggle the active AI backend without leaving your mission:
* **🖥️ Local LLM:** Direct offline execution pinned to your RTX 3060 via Ollama (`gemma4:12b`, `qwen2.5vl:7b`).
* **☁️ Gemini 3.8:** Ultra-fast multimodal reasoning via Google AI Studio Free Tier API (`gemini-2.5-flash`).
* **⚡ Hybrid:** Executes locally first; seamlessly escalates to Cloud Gemini Flash if local models encounter errors or low confidence.

The active engine is displayed in real time in the **Mission Control Header Badge** (`🖥️ LOCAL LLM` vs `☁️ GEMINI 3.8 FLASH` vs `⚡ HYBRID FALLBACK`) and broadcast to all connected web clients and mobile devices.

### 2. Primary AI Routing Policy Hero Switcher (Model Selection Tab)
Under Tab 2 (**Model Selection**):
1. **Interactive Hero Cards:** Click any of the 3 large visual policy cards to switch execution strategy on the fly.
2. **Cloud Gemini Model Target:** Choose between:
   - `gemini-2.5-flash`: Gemini 3.8 / 2.5 Flash (Google AI Studio Free Tier, default)
   - `gemini-2.0-flash`: Fast multimodal reasoning
   - `gemini-1.5-flash`: Standard lightweight reasoning
   - `gemini-2.5-pro`: Deep reasoning & coding
3. **Gemini API Key:** Enter or update your Google AI Studio API key directly from the UI with password masking and visibility toggle. If left blank, Jarvis automatically falls back to the `GEMINI_API_KEY` system environment variable.
4. **Local Subsystem Model Assignments:**
   - **Text & Reasoning Model** (Default: `gemma4:12b`)
   - **Vision UI Grounding Model** (Default: `qwen2.5vl:7b`)
   - **Tier-0 Fast Classifier Model** (Default: `llama3.2:3b`)
5. Click **Save Model Preferences** to persist changes across reboots in `config.yaml`.

---

## 9. Automation Capabilities

### Vision-Based Computer Use
Jarvis captures your physical X11 display (1920×1080) in <20ms using `mss` and feeds it to `qwen2.5vl:7b` to calculate pixel coordinates and click/type using `pyautogui`.

### Dual Browser Strategy
* **Everyday Chrome (CDP Mode):**
  Click **Attach Chrome (CDP :9222)** or run `uv run jarvis cdp`. Jarvis connects directly to your active, logged-in browser session—allowing it to interact with GitHub, Gmail, or Jira without 2FA or CAPTCHAs.
* **Isolated Sandbox:**
  When performing disposable or privacy-sensitive web automation, Jarvis spins up an isolated Playwright browser with its own sandbox directory (`~/.jarvis/browser_data`).

### Python Runner
Jarvis can execute background Python scripts, data processing algorithms, and Telegram messages via `requests`. Passwords and API tokens in the secret vault are automatically injected as environment variables.

### "Watch & Learn" Macro Recorder
Whenever Jarvis executes a multi-step workflow, it compiles the action sequence into a clean, deterministic Python script in `~/ai-memory/jarvis/workflows/<name>.py`. Subsequent runs execute in <0.5 seconds without LLM visual grounding.

---

## 10. Safety Gatekeeper

By default, `autonomous_mode: false`:
* Any destructive command (e.g. `rm -rf`, `sudo`, database drops, payments, email sending) pauses execution and summons an on-screen **Floating Approval Overlay**.
* Press <kbd>Enter</kbd> to authorize or <kbd>Esc</kbd> to reject.
* To run unattended, toggle autonomous mode via `uv run jarvis run "<task>" --autonomous` or in the Web HUD.

---

## 11. Audit Trail & Visual Analytics

Every mission is recorded in `~/.jarvis/runs/` with metadata, step observations, and full-resolution screenshot filmstrips.

In the **🎞️ Audit & History** tab:
1. **Human-Readable KPI Cards:** Total Missions, Success Rate (%), Average Duration (s), Total Steps Executed, and Primary Actuator.
2. **Native SVG Charts:**
   - **Actuator Breakdown Donut:** Color-coded distribution of actions across Desktop GUI, Browser, Python, Shell, and Macros with hover values.
   - **Mission Velocity & Latency Bar Chart:** Execution duration across recent missions.
   - **Success / Failure Metric Gauge:** Visual ratio progress bar.
3. **Search & Filter Controls:**
   - Filter by status (`All`, `✔ Success`, `✖ Failed`).
   - Real-time keyword search across mission goals.
4. **Step-by-Step Interactive Timeline:**
   - Formatted "Thinking & Intent" bubbles.
   - Clean parameter key-value tags.
   - Action badges and observation output.
5. **Full-Resolution Screenshot Lightbox:** Click any step screenshot to open a high-res 1080p lightbox viewer with zoom.
6. **Multi-Format Mission Report Download & Export:**
   - **Markdown Document (`.md`):** Complete, portable markdown report with goal, status, duration, final outcome, and step timeline.
   - **Interactive HTML Report (`.html`):** Standalone, styled executive report with dark glassmorphic layout, KPI badges, parameter code blocks, and print-to-PDF styles (<kbd>Ctrl+P</kbd>).
   - **Raw Audit JSON (`.json`):** Full serialized execution history for programmatic parsing.
   - **Copy to Clipboard:** One-click copy of the formatted Markdown report to your system clipboard.
   - **Direct Downloads:** Native browser attachments (`/api/history/{run_id}/download?format=md|html|json`) ensuring 100% reliability across all desktop and mobile browsers.

---

## 12. System Failure Alerts & Error Logs

Jarvis Mark 2 tracks all system exceptions, model connection failures, timeouts, and hardware sentinel warnings:
1. In the Web HUD, click **⚠️ System Alerts**.
2. If an error occurs, an error badge in the navigation bar highlights the count.
3. Each log displays timestamp, error classification, context, and full stack trace.
4. Click **Clear Error History** once resolved.

---

## 13. Lean Memory & Vault Secrets

* **Structured Memory:** Files are stored in `~/ai-memory/jarvis/` (omitted from git commit, configurable via the Web UI in the **Memory & Secrets** tab):
  - `preferences.md`: Personal guidelines and persona rules.
  - `system.md`: Linux workstation hardware details.
  - `contacts.md`: People and messaging handles.
  - `workflows/`: Application recipes and compiled macros.
* **Secret Vault:** Store tokens safely in Linux Keyring:
  ```bash
  uv run jarvis vault set telegram_bot_token "YOUR_TOKEN"
  uv run jarvis vault set telegram_chat_id "YOUR_CHAT_ID"
  uv run jarvis vault list
  ```

---

## 14. In-UI System Manual

Jarvis features a built-in **📖 System Manual** tab directly inside the Web HUD (`http://127.0.0.1:8765`):
* Searchable 13-section sidebar.
* Formatted code blocks with one-click copy buttons.
* Embedded quick-action triggers to test features (Daily brief, Attach Chrome, Spotlight, Voice Toggle, Diagrams) directly from the documentation!

---

## 15. Visual Media Display: Diagrams, Charts & System Windows

When interacting with Jarvis, any requested or generated visual artifact—including system architecture diagrams, data charts, and screenshots—can be displayed via an interactive in-HUD dialog or a native X11 desktop window.

### Supported Visual Artifacts:
1. **Mermaid Diagrams:** Interactive SVG rendering of flowcharts, sequence diagrams, and architecture graphs powered by Mermaid.js.
2. **Data & Math Charts:** Inline SVG vector graphics or generated matplotlib/seaborn plots.
3. **Screenshots & Local Images:** High-resolution 1080p desktop captures, crops, or workstation image files with click-to-zoom in Lightbox.

### Dual Display Delivery Targets:
* **Web HUD Dialog Modal (`#media-display-modal`):**
  - Appears seamlessly on the Web HUD dashboard.
  - Interactive SVG diagram viewer with pan and zoom.
  - **View Raw Syntax** button to inspect Mermaid code.
  - **Copy to Clipboard** button to grab raw syntax or file path.
  - **Open in System Window (X11)** button to project directly onto your desktop.
* **Native X11 Desktop System Window (`SystemWindowManager`):**
  - High-performance desktop Tkinter window running in a non-blocking background thread.
  - High-quality image scaling via Pillow (`LANCZOS`), native resolution labels, and keyboard clipboard copy.

### How to Trigger:
* **Automatic Detection:** Simply ask Jarvis to generate a diagram (e.g., *"Draw an architecture diagram of your ReAct loop"*). When Jarvis finishes with a ` ```mermaid ` block or an image markdown tag, the visual modal appears automatically.
* **Explicit Action:** In ReAct loop, Jarvis uses action 19:
  ```json
  Action: show_media
  Action Input: {"media_type": "diagram", "content": "graph TD; A-->B", "title": "Flow", "target": "both"}
  ```
* **Command Center Quick Tile:** Click **📊 Show Diagram** in the Web HUD to view the Jarvis Mark 2 Tactical Architecture diagram instantly.

---

## 16. Multi-Desktop & Display Perception Setup

Workstations running Linux X11 often utilize multiple physical monitors or virtual desktop arrangements. Jarvis allows you to designate a **Main Desktop** so its vision-based actuators (`mss`, `pyautogui`, and `Qwen2.5-VL`) ground their vision and mouse clicks accurately on the screen you are working on.

### Multi-Monitor Topologies
On Linux X11 systems, the display actuator detects:
* **Display 0 (Virtual Combined Canvas):** A single bounding box encompassing all connected screens (e.g., `3840×1080` if using two `1920×1080` monitors).
* **Display 1 (Physical Screen 1):** The primary monitor (e.g., `HDMI-1` at `1920×1080`, offset `left: 1920, top: 0`).
* **Display 2 (Physical Screen 2):** The secondary monitor (e.g., `HDMI-0` at `1920×1080`, offset `left: 0, top: 0`).

### Coordinate Grounding & Calibration
When Jarvis captures a screenshot of an individual display, vision models reason over local coordinates `(0 <= x <= width, 0 <= y <= height)`.
Jarvis's **DesktopActuator** automatically maps these coordinates to global X11 space:
$$\text{Global } X = \text{Local } X + \text{Monitor Left Offset}$$
$$\text{Global } Y = \text{Local } Y + \text{Monitor Top Offset}$$
This ensures clicks, double clicks, and drag operations land exactly on target regardless of whether your active monitor is placed to the left, right, top, or bottom.

### Selecting the Main Desktop
You can change Jarvis's main desktop in four convenient ways:

1. **Top Header Selector (Web HUD):**
   * Use the **DESKTOP** dropdown in the top navigation bar to switch between `Display 1`, `Display 2`, or `Display 0 (All)`.
   * Click **👁️ Inspect** to view the active screen in the Lightbox immediately.

2. **Dedicated `🖥️ Main Desktop` Management Tab:**
   * Navigate to the **🖥️ Main Desktop** tab (`#tab-displays`) in the Web HUD.
   * View live, high-resolution thumbnail cards for every detected screen with resolution, aspect ratio, primary badge, and bounds offset.
   * Click **✔ Set as Main Desktop** to switch.
   * Click **👁️ Fullscreen** on any card to zoom in and inspect fine details on that screen.
   * Review the **Active Desktop Perception** live panel with real-time coordinate offset status and click **📸 Refresh Perception** anytime.

3. **Persistent Configuration (`config.yaml`):**
   * The selected desktop is saved to `~/.jarvis/config.yaml`:
     ```yaml
     desktop:
       screen_index: 1  # 1 for primary physical monitor, 2 for secondary, 0 for all combined
     ```

4. **Agent ReAct Actions:**
   * Jarvis can switch or inspect monitors during autonomous task execution:
     - **Action 20 (`desktop_switch_monitor`):** Sets the active perception screen index for subsequent visual reasoning and clicks.
     - **Action 21 (`desktop_inspect_screen`):** Captures and displays any monitor in the visual modal without permanently changing the primary desktop setting.

### REST API Endpoints:
* `GET /api/desktop/monitors`: Returns list of all connected displays, resolutions, offsets, and currently selected index.
* `POST /api/desktop/select`: Sets active desktop (`{"screen_index": 1}`), updates live agent instance, and broadcasts change via WebSockets.
* `GET /api/desktop/preview?screen_index=1`: Generates and streams a real-time JPEG snapshot of the specified screen.

---

## 17. Terminal Typography & Interactive Font Scaling

To ensure optimal readability across varied workstation displays, DPI settings, and viewing distances, Jarvis Mark 2 features an enhanced, high-contrast monospace console with interactive font size scaling.

### Typography Specifications
* **Font Family:** `JetBrains Mono` (with fallbacks to `Fira Code`, `Cascadia Code`, and system monospace).
* **Font Weight:** `500` (Medium) for default lines; `600` for actions/results; `700` (Bold) for steps and errors.
* **Line Height:** Relaxed `1.7` to prevent congested or cramped lines during dense multi-step code logs.
* **Letter Spacing:** `0.022em` for crisp character glyph separation on high-resolution Linux screens.
* **Deck Background:** Obsidian void `rgba(3, 7, 18, 0.92)` with specular border highlights and deep inset shadows.

### Interactive Stepper Controls
Located in the terminal controls bar directly beneath the console window:
* **`[A-]` Button:** Decreases the terminal font size by 1px (minimum 12px).
* **Font Indicator (`[15px]`):** Displays current font size in glowing neon cyan.
* **`[A+]` Button:** Increases the terminal font size by 1px (maximum 26px).
* **`[Reset]` Button:** Restores the recommended default size (15px).

> **Persistence:** Your selected font size is automatically stored in your browser's `localStorage` (`jarvis_terminal_font_size`). It persists across browser restarts, page reloads, and tab navigation without requiring code edits.

### Categorized Log Accent Badges
Each output type in the ReAct execution loop is rendered with distinct styling:
* **Thoughts (`.log-thought`):** Italicized sky blue text (`#93c5fd`) with subtle cyan border badge (`3.5px solid #38bdf8`) and translucent background.
* **Actions (`.log-action`):** Bold warm amber (`#fed7aa`) with orange border badge (`#fb923c`).
* **Step Headers (`.log-step`):** Bold neon cyan (`#00f0ff`) with 4px solid left badge and glowing cyan outline box.
* **Results (`.log-result`):** High-visibility emerald green (`#4ade80`) with green border badge and glow.
* **Errors (`.log-error`):** Bold crimson alert (`#fca5a5`) with red border badge and red text shadow.

---

## 18. World-Class Glassmorphic HUD Design & Layout Architecture

Jarvis Mark 2 features an uncompromising, futuristic glassmorphic design system modeled after advanced tactical HUD interfaces.

### Core Layout Architecture
1. **Floating Symmetrical Glass Header:**
   - **Left Zone:** Pulsing Arc Reactor core and `JARVIS // MARK 2` brand title with live hardware status (`● SYSTEM READY // RTX 3060 ARMED`).
   - **Center Capsule:** A unified glass pill bar grouping the **Conversation Mode segmented controls** (`Audio` | `Audio+Chat` | `Chat`) and the **Desktop Monitor Selector** (`SCREEN: [Display 1] [👁️]`).
   - **Right Zone:** Quick action pills: **Daily brief** (warm amber), **Voice Reply** toggle (neon cyan), and the master emergency **KILL SWITCH** (crimson alert).
   - **Non-Wrapping Design:** Keeps all header controls strictly on a single row from 1280px up to 4K resolutions.

2. **Standardized Button Hierarchy:**
   - `.btn`: Standard 36px height with 8px border radius.
   - `.btn-sm`: Compact 28px height with 6px border radius (used for header dropdowns, audit filters, and terminal buttons).
   - `.btn-lg`: Prominent 48px height with 10px border radius (used for saving model settings and primary actions).
   - `.btn-execute`: Surgical 52px height matching the prompt input box and circular mic button.

3. **Curated Futuristic Palette:**
   - **Obsidian Dark Void:** `#030712`, `#040916`, `#070d1d`
   - **Neon Arc Cyan:** `#00f0ff` (Primary highlights, focus states, specular borders)
   - **Tactical Amber:** `#ffb703` (Daily brief, warnings, action badges)
   - **Hyper Green:** `#00ff9d` (Success rates, online status, watchdogs)
   - **Reactor Crimson:** `#ff2a5f` (Kill-switch, error logs, emergency stops)

4. **Lucide Vector Iconography:**
   - All legacy emojis and inconsistent symbols have been replaced with sharp, scalable SVG vector icons from the Lucide design library.


