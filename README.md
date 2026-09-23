# 🤖 JARVIS // MARK 3: Autonomous Personal AI Assistant for Linux X11

**JARVIS // Mark 3** is an autonomous, multi-modal personal assistant designed for Linux workstations (X11) powered by an **NVIDIA RTX 3060 (12 GB VRAM)**, **AMD Ryzen 7**, and **96 GB of RAM**.

It operates with **zero cloud billing required** using local Ollama models with enterprise hybrid escalation, featuring:
- **Vision-based Computer Use** (driving desktop apps, mouse, and keyboard)
- **Deep Desktop Window Inspection** (`_NET_ACTIVE_WINDOW` & `_NET_CLIENT_LIST` via X11 `xprop`)
- **Tier-0 CPU Offloading** (zero GPU VRAM usage for sub-100ms intent classification)
- **Enterprise Multi-Provider LLM Gateway** (Gemini, OpenAI, Groq/Grok, Meta AI, Local Ollama with circuit breaking and auto-failover)
- **Contextual 90% Screen Explanation Dialog** (2-tier summary first + interactive Mermaid diagram stage & streaming sidebar)
- **Configurable Multi-Topic Daily Brief Matrix** (weighted percentages for weather, calendar, tech news, world news, and hardware health)
- **Overhauled Audit & History Visualizer** (compact KPI grid + interactive clickable/hoverable SVG charts)
- **Natural Technical Speech Synthesis** (natural pronunciation of memory units `GiB` $\rightarrow$ `GB`, `MiB` $\rightarrow$ `MB`, latencies, and acronyms)
- **Ergonomic Audio-Only Quick-Action Strip** (quick tiles positioned directly above Hardware Telemetry)
- **Workstation Calendar App** (interactive calendar tab with searchable pending items and markdown sync)
- **Sub-5ms Local Intent Matcher** (instant offline pattern matching without GPU invocation)
- **Decoupled Graphical UI & Tactical HUD** (`http://127.0.0.1:8765`)
- **Context-Aware Desktop Spotlight Bar** (<kbd>Alt</kbd> + <kbd>J</kbd>)
- **Two-Way Telegram Remote Control** (control workstation from mobile anywhere)
- **Interactive Voice Communication & Instant Barge-In** (Web HUD microphone, CLI `jarvis voice`, and Iron Man voice replies)
- **Obsidian Knowledge Base Hybrid RAG** (BM25 + Semantic search across ~/ai-memory and Obsidian Vault)
- **"Watch & Learn" Macro Compiler** (converts repeated visual tasks into 100x faster Python scripts)
- **Multi-Desktop Display Selection** (choose which physical monitor or virtual combined screen Jarvis sees & controls)
- **Master Process Lifecycle Supervisor** with Master Kill-Switch

---

## 🏗️ Architecture & How Jarvis Works

Jarvis runs on a **Perception-Reasoning-Action (ReAct)** loop powered by a tiered local model hierarchy with optional enterprise gateway cascading:

```
[User Input] (Web HUD Mic / Alt+J Spotlight / Telegram / CLI)
     │
     ▼
[Sub-5ms Local Matcher] ──(Matched Greeting/Time/Utterance)──> Instant Voice Reply (<1ms)
     │ (Unmatched)
     ▼
[Tier-0 Fast Classifier: Llama 3.2 3B] (Runs on CPU or GPU in <100ms)
     │
     ├── If Conversation ──> Direct Assistant Voice Reply (Iron Man JARVIS)
     │
     └── If Complex Task ──> [Tier-1 Logic: Gemma 4 12B] (Pinned in VRAM via keep-alive)
                                  │
                                  ├── Visual UI Grounding ──> [Qwen2.5-VL 7B]
                                  │    └── Screen Inspection ──> X11 Window Hierarchy (_NET_ACTIVE_WINDOW)
                                  │
                                  ├── Enterprise Escalation? ──> [LLM Gateway Router]
                                  │    └── Fallback: Gemini ⇄ OpenAI ⇄ Groq ⇄ Meta ⇄ Ollama
                                  │
                                  ├── High-Stakes Action? ──> [Safety Approval Overlay]
                                  │
                                  └── Actuators:
                                        ├── Desktop GUI (mss + pyautogui)
                                        ├── Everyday Browser (Chrome CDP :9222)
                                        ├── Sandboxed Web (Playwright)
                                        └── Python Runner (Data crunching / Telegram)
```

### Runtime Background Processes (`jarvis start`):
When you execute `uv run jarvis start`, the central **Process Supervisor** (`jarvis/core/supervisor.py`) manages two background processes:
1. **`ui_server` (FastAPI + Uvicorn on port 8765):** Serves the Jarvis Tactical HUD dashboard and manages WebSocket streaming, telemetry, audit runs, model selection, LLM gateway routing, and daily briefing matrix.
2. **`worker` daemon:** Listens for the global <kbd>Alt</kbd> + <kbd>J</kbd> desktop hotkey, runs the Two-Way Telegram polling bot, and monitors hardware sentinels.

---

## 🌟 Key Capabilities in Mark 3

| Component | Capabilities |
| :--- | :--- |
| **Enterprise LLM Gateway** | Built-in multi-provider LLM gateway (`src/jarvis/gateway/`) supporting Google Gemini, OpenAI, Groq, Meta AI, and Local Ollama with priority cascading, automatic circuit breaking, Vault credential resolution, and real-time latency telemetry. |
| **Tier-0 CPU Offloading** | Ability to force Tier-0 intent classification (`llama3.2:3b`) onto CPU (`tier0_device: cpu`), saving 100% GPU VRAM for the primary `gemma4:12b` reasoning model and `qwen2.5-vl:7b` vision model. |
| **Deep Screen Inspection** | Desktop actuator interrogates X11 window hierarchy via `xprop` for `_NET_ACTIVE_WINDOW` (focused app & title) and `_NET_CLIENT_LIST` (all open tabs & apps), allowing Jarvis to describe the user's active environment in real-time. |
| **Explanation Persona & 90% Dialog**| Two-tier explanation protocol (2-3 sentence executive summary first, followed by invitation to dig deeper). Renders interactive Mermaid SVG architecture diagrams in an expansive 90vw $\times$ 90vh modal with streaming sidebar and SVG export. |
| **Interactive Audit & History** | Compact KPI grid with new Tier-0 Classification Ratio widget, interactive SVG Actuator Donut (click to filter history list), and Velocity Bar Chart (hover tooltips + click to inspect mission filmstrip). |
| **Configurable Daily Brief Matrix** | Multi-topic briefing engine (`daily_brief_config.json`) with weighted interest percentages, live weather, Hacker News tech feed, Google News world RSS, workstation calendar agenda, and hardware health. |
| **Technical Speech Normalization** | Phonetic pronunciation rules normalizing binary units (`GiB` $\rightarrow$ `GB`, `MiB` $\rightarrow$ `MB`), latencies (`ms` $\rightarrow$ `milliseconds`), and acronyms without letter spelling. |
| **Audio-Only Quick-Action Strip** | Ergonomic quick action tiles ("Daily Brief", "Paste Clip", "Clear History") relocated directly above the Hardware Telemetry card for rapid access. |
| **Workstation Calendar App** | Dedicated Web UI tab with interactive monthly grid, client-side searchable pending items sidebar, and natural language voice recitation (`"How's my calendar look like today"`). Backed by human-readable markdown (`~/ai-memory/jarvis/calendar.md`). |
| **Sub-5ms Local Intent Matcher** | High-performance offline trigger engine (<0.1ms compiled regex slots + cached variations) handling common utterances (`Hey Jarvis`, `What's the time right now?`, calendar checks, and file viewers) with zero LLM latency and zero GPU compute overhead. |
| **Zero-Drop Interim Voice STT** | Overhauled speech recognition pipeline using continuous streaming Web Speech API, real-time interim word rendering on screen, and 800ms silence debouncing to eliminate dropped phrases or premature cutoffs. |
| **Autonomous Multi-Step Sidebar**| Floating glassmorphic execution panel featuring step progress bar, actuator donut/stacked distribution chart, step breadcrumbs with live status, and real-time hardware telemetry. |
| **Ubuntu GNOME Voice Shortcut** | One-touch `Super+Shift+J` shortcut to summon Jarvis HUD in Hands-Free Continuous Loop with Audio Only mode and random contextual greetings from `greetings.md`. |
| **Transparent File Viewer** | Glassmorphic line-numbered modal viewer for displaying code, markdown, and configuration files directly inside the HUD upon vocal request (`"Show content of <file>"`). |
| **System Responsiveness** | Local models (`gemma4:12b`, `qwen2.5vl:7b`) are locked into VRAM/RAM with `keep_alive: "-1"`, eliminating HDD read penalties. |
| **Decoupled Web HUD** | Tactical dashboard on `:8765` with live WebSocket streaming, hardware telemetry, and run filmstrips. |
| **Spotlight Bar (`Alt+J`)** | Floating translucent HUD bar that automatically captures your active X11 window title and clipboard text. |
| **Interactive Voice** | 4 communication channels: Web HUD mic button, Spotlight Bar, CLI `jarvis voice`, and Telegram voice notes. |
| **Everyday Chrome CDP** | Connects to your logged-in everyday browser tabs on port 9222 to bypass 2FA and CAPTCHAs. |
| **Macro Recorder** | Compiles multi-step visual workflows into deterministic Python scripts in `~/ai-memory/jarvis/workflows/`. |
| **Resource Attachments** | Attach files/datasets upfront via Web HUD or `-f` in CLI. If forgotten, Jarvis prompts on-demand via an interactive modal to supply the file and seamlessly resumes. |
| **Visual Audit Trail** | Human-readable KPI cards, native SVG Actuator Donut, Latency Bar chart, Success ratio gauge, full-res screenshot lightbox, and 1-click Markdown export. |

---

## 🚀 Quick Reference Commands

```bash
# 1. Master Startup (Web HUD, Spotlight, Telegram, Watchdogs)
uv run jarvis start

# 2. Check System Status & Running Daemons
uv run jarvis status

# 3. Master Kill-Switch (Cleanly terminate all background services)
uv run jarvis stop

# 4. Trigger Daily Brief On-Demand
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
uv run jarvis vault set gemini_api_key "YOUR_GEMINI_KEY"

# 10. List Structured Memory Files
uv run jarvis memory list
```

---

## 📘 User Guide & In-UI Manual

For detailed walkthroughs on every feature, voice settings, and remote mobile usage, read:
👉 **[user-guide.md](user-guide.md)** or open the **📖 System Manual** tab inside the Web HUD at [`http://127.0.0.1:8765`](http://127.0.0.1:8765).

---

## 🧪 Testing

Run the full automated test suite:
```bash
uv run pytest -v
```
