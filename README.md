# 🤖 JARVIS // MARK 2: Autonomous Personal AI Assistant for Linux X11

**JARVIS // Mark 2** is an autonomous, multi-modal personal assistant designed for Linux workstations (X11) powered by an **NVIDIA RTX 3060 (12 GB VRAM)**, **AMD Ryzen 7**, and **96 GB of RAM**.

It operates with **zero cloud billing required** using local Ollama models, featuring:
- **Vision-based Computer Use** (driving desktop apps, mouse, and keyboard)
- **Dual Browser Automation** (Everyday Chrome CDP attach vs. Isolated Playwright sandbox)
- **Decoupled Graphical UI & Tactical HUD** (`http://127.0.0.1:8765`)
- **Context-Aware Desktop Spotlight Bar** (<kbd>Alt</kbd> + <kbd>J</kbd>)
- **Two-Way Telegram Remote Control** (control workstation from mobile anywhere)
- **Interactive Voice Communication & Instant Barge-In** (Web HUD microphone, CLI `jarvis voice`, and Iron Man voice replies)
- **Obsidian Knowledge Base Hybrid RAG** (BM25 + Semantic search across ~/ai-memory and Obsidian Vault)
- **"Watch & Learn" Macro Compiler** (converts repeated visual tasks into 100x faster Python scripts)
- **Multi-Desktop Display Selection** (choose which physical monitor or virtual combined screen Jarvis sees & controls)
- **Visual Media Display** (interactive Mermaid SVG diagrams & charts via Web HUD dialog and native X11 desktop windows)
- **Proactive Watchdogs** (Hardware thermal/storage sentinel, download auto-organizer, on-demand Daily brief)
- **Master Process Lifecycle Supervisor** with Master Kill-Switch

---

## 🏗️ Architecture & How Jarvis Works

Jarvis runs on a **Perception-Reasoning-Action (ReAct)** loop powered by a tiered local model hierarchy:

```
[User Input] (Web HUD Mic / Alt+J Spotlight / Telegram / CLI)
     │
     ▼
[Tier-0 Instant Router: Llama 3.2 3B] (Sub-100ms intent classification)
     │
     ├── If Conversation ──> Direct Assistant Voice Reply (Iron Man JARVIS)
     │
     └── If Complex Task ──> [Tier-1 Logic: Gemma 4 12B] (Pinned in VRAM via keep-alive)
                                  │
                                  ├── Visual UI Grounding ──> [Qwen2.5-VL 7B]
                                  ├── High-Stakes Action? ──> [Safety Approval Overlay]
                                  └── Actuators:
                                        ├── Desktop GUI (mss + pyautogui)
                                        ├── Everyday Browser (Chrome CDP :9222)
                                        ├── Sandboxed Web (Playwright)
                                        └── Python Runner (Data crunching / Telegram)
```

### Runtime Background Processes (`jarvis start`):
When you execute `uv run jarvis start`, the central **Process Supervisor** (`jarvis/core/supervisor.py`) manages two background processes:
1. **`ui_server` (FastAPI + Uvicorn on port 8765):** Serves the Jarvis Tactical HUD dashboard and manages WebSocket streaming, telemetry, audit runs, and model selection.
2. **`worker` daemon:** Listens for the global <kbd>Alt</kbd> + <kbd>J</kbd> desktop hotkey, runs the Two-Way Telegram polling bot, and monitors hardware sentinels.

---

## 🌟 Key Capabilities in Mark 2

| Component | Capabilities |
| :--- | :--- |
| **Workstation Calendar App** | Dedicated Web UI tab with interactive monthly grid, client-side searchable pending items sidebar, and natural language voice recitation (`"How's my calendar look like today"`). Backed by human-readable markdown (`~/ai-memory/jarvis/calendar.md`). |
| **Sub-5ms Local Intent Matcher** | High-performance offline trigger engine (<0.1ms compiled regex slots + cached variations) handling common utterances (`Hey Jarvis`, `What's the time right now?`, calendar checks, and file viewers) with zero LLM latency and zero GPU compute overhead. |
| **Zero-Drop Interim Voice STT** | Overhauled speech recognition pipeline using continuous streaming Web Speech API, real-time interim word rendering on screen, and 800ms silence debouncing to eliminate dropped phrases or premature cutoffs. |
| **Autonomous Multi-Step Sidebar**| Floating glassmorphic execution panel featuring step progress bar, actuator donut/stacked distribution chart, step breadcrumbs with live status, and real-time hardware telemetry. |
| **Ubuntu GNOME Voice Shortcut** | One-touch `Super+Shift+J` shortcut to summon Jarvis HUD in Hands-Free Continuous Loop with Audio Only mode and random contextual greetings from `greetings.md`. |
| **Transparent File Viewer** | Glassmorphic line-numbered modal viewer for displaying code, markdown, and configuration files directly inside the HUD upon vocal request (`"Show content of <file>"`). |
| **System Responsiveness** | Local models (`gemma4:12b`, `qwen2.5vl:7b`) are locked into VRAM/RAM with `keep_alive: "-1"`, eliminating HDD read penalties. |
| **Tier-0 Router** | Sub-100ms classification via `llama3.2:3b`. Configurable via UI; falls back to `gemma4:12b` if disabled. |
| **Decoupled Web HUD** | Tactical dashboard on `:8765` with live WebSocket streaming, hardware telemetry, and run filmstrips. |
| **Spotlight Bar (`Alt+J`)** | Floating translucent HUD bar that automatically captures your active X11 window title and clipboard text. |
| **Interactive Voice** | 4 communication channels: Web HUD mic button, Spotlight Bar, CLI `jarvis voice`, and Telegram voice notes. |
| **Everyday Chrome CDP** | Connects to your logged-in everyday browser tabs on port 9222 to bypass 2FA and CAPTCHAs. |
| **Daily brief** | On-demand system briefing (`jarvis brief` or HUD button) spoken via the Iron Man British voice (`en-GB-RyanNeural`). |
| **Macro Recorder** | Compiles multi-step visual workflows into deterministic Python scripts in `~/ai-memory/jarvis/workflows/`. |
| **Resource Attachments** | Attach files/datasets upfront via Web HUD or `-f` in CLI. If forgotten, Jarvis prompts on-demand via an interactive modal to supply the file and seamlessly resumes. |
| **Visual Audit Trail** | Human-readable KPI cards, native SVG Actuator Donut, Latency Bar chart, Success ratio gauge, full-res screenshot lightbox, and 1-click Markdown export. |
| **Command Center Widgets**| Live Watchdogs Sentinels Matrix, Multi-Disk Storage Health (NVMe `/` & secondary HDD `/mnt/HDD-500GB/`), Recent Missions feed, and Terminal controls. |
| **Conversation Modes** | 3 Web UI modes: `audio_only` (hands-free Arc Reactor HUD with auto-listen loop), `audio+chat` (voice replies + terminal logs), and `chat_only` (silent text mode). |
| **In-UI System Manual** | Integrated 15-section tactical handbook tab inside the Web HUD with 1-click code copy and live action triggers. |
| **System Error Log** | Real-time error tracking card in the UI displaying any model disconnects, step timeouts, or unhandled exceptions. |
| **Visual Media Display**| Interactive Mermaid.js SVG architecture diagrams, SVG data charts, and image viewers displayed via Web HUD modal or native X11 desktop system windows. |
| **Multi-Desktop Support**| Designate active monitor (Display 1, Display 2, or All Combined) via HUD header dropdown or dedicated management tab with live thumbnails and automatic coordinate offset grounding. |
| **Terminal Typography & Scaler**| Enhanced JetBrains Mono monospace console with line-height 1.7, letter-spacing, categorized translucent accent badges, and dynamic font scaling stepper (`[A-] [15px] [A+] [Reset]`) persisted in `localStorage`. |
| **World-Class Glassmorphic UX**| Floating non-wrapping header with unified center control capsule, standardized button hierarchy (`.btn`, `.btn-sm`, `.btn-lg`), precision 52px prompt bar, uniform holographic tiles, and Lucide vector iconography. |

---

## 🚀 Quick Reference Commands

```bash
# 1. Master Startup (Web HUD, Spotlight, Telegram, Watchdogs)
uv run jarvis start

# 2. Check System Status & Running Daemons
uv run jarvis status

# 3. Master Kill-Switch (Cleanly terminate all background services)
uv run jarvis stop

# 4. Trigger Daily brief On-Demand
uv run jarvis brief

# 5. Run a task directly via CLI (with resource attachments)
uv run jarvis run "Analyze sales spreadsheet" -f ~/Downloads/sales_q3.csv

# 6. Speak with Jarvis via Terminal Voice Mode
uv run jarvis voice

# 7. Launch Everyday Browser with CDP Remote Debugging
uv run jarvis cdp

# 8. Inspect Audit Trail of Past Runs
uv run jarvis audit

# 9. Manage Credentials in Vault
uv run jarvis vault set telegram_bot_token "YOUR_BOT_TOKEN"
uv run jarvis vault set telegram_chat_id "YOUR_CHAT_ID"

# 10. List Structured Memory Files
uv run jarvis memory list
```

---

## 📘 User Guide & In-UI Manual

For detailed walkthroughs on every feature, voice settings, and remote mobile usage, read:
👉 **[user-guide.md](user-guide.md)** or open the **📖 System Manual** tab inside the Web HUD at [`http://127.0.0.1:8765`](http://127.0.0.1:8765).

For a complete architectural comparison of what was built in Mark 1 and upgraded in Mark 2, see:
👉 **[custom-docs/upgrades_mark1_and_mark2.md](custom-docs/upgrades_mark1_and_mark2.md)**.

---

## 🧪 Testing

Run the full automated test suite:
```bash
uv run pytest -v
```
