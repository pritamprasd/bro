# 🤖 JARVIS: Autonomous Personal AI Assistant for Linux X11

JARVIS is an autonomous, multi-modal personal assistant designed for Linux workstations (X11) powered by an **NVIDIA RTX 3060 (12 GB VRAM)**, **AMD Ryzen 7**, and **96 GB of RAM**.

It operates with **zero cloud billing required** using local Ollama models, supports **Vision-based Computer Use**, an **isolated Playwright browser**, an **everyday Chrome CDP bridge**, an **interactive decoupled Web UI (Stark Industries HUD)**, a **desktop Spotlight Bar (`Alt+J`)**, a **Two-Way Telegram Bot daemon**, **Proactive Watchdogs**, a **"Watch & Learn" Macro Recorder**, and an **Iron Man voice persona**.

---

## 🌟 Major Highlights (Phase 2)

### 1. Zero-Billing Local AI + Latency Optimizations
- **Persistent Keep-Alive (`keep_alive: "-1"`):** Eliminates HDD cold-start latency by pinning `gemma4:12b` and `qwen2.5vl:7b` directly in RAM/VRAM.
- **Configurable Tier-0 Instant Router (`llama3.2:3b`):** Sub-100ms intent classification and query routing with automatic fallback to `gemma4:12b`.
- **Cloud Escalation:** Optional fallback to Gemini 3.8 / 2.5 Flash via Google AI Studio's $0 free tier.

### 2. Decoupled Graphical UI & Tactical HUD
- Standalone web dashboard running on `http://127.0.0.1:8765`.
- Designed with a **Stark Industries / Iron Man HUD aesthetic** (deep space obsidian, neon cyan arc-reactor glow, glassmorphic panels).
- **Features:**
  - Real-time token and thought streaming over WebSockets.
  - Live hardware telemetry (RTX 3060 VRAM bar, GPU temperature, CPU load, RAM usage).
  - Visual Audit & Filmstrip viewer: inspect past runs with before/after screenshots for every action.
  - Quick action buttons (Attach Chrome CDP, Organize Downloads, Kill Switch).
  - Markdown Memory & Secret Vault manager.

### 3. Desktop Spotlight Bar (`Alt+J`)
- Minimalist, floating translucent search bar on X11.
- **Context-Aware:** Automatically captures the active window title and current clipboard text, injecting them into your prompt.

### 4. Two-Way Telegram Remote Daemon
- Control your workstation from your phone anywhere via your private Telegram bot.
- Commands: `/run <goal>`, `/status` (telemetry), `/screen` (sends desktop screenshot to your phone), `/kill`.
- Proactive push notifications when hardware sentinels trigger or jobs finish.

### 5. Desktop & Web Automation: Dual Browser & Macro Recorder
- **Everyday Browser CDP Attach:** One-click button to launch Chrome/Brave with `--remote-debugging-port=9222`, allowing Jarvis to automate your already logged-in accounts without 2FA / CAPTCHA hassles.
- **Isolated Playwright Sandbox:** Dedicated browser profile for disposable or privacy-focused tasks.
- **"Watch & Learn" Macro Recorder:** Compiles successful multi-step visual workflows into deterministic, instant Python macros (`~/.jarvis/memory/workflows/<name>.py`).

### 6. Proactive Background Watchdogs
- **Hardware Sentinel:** Monitors GPU thermal limits (>80°C) and root disk saturation (>90%).
- **Configurable Download Organizer:** Watches `~/Downloads` and organizes files into categorized folders (`~/Documents/PDFs`, `~/Documents/Data`, `~/Downloads/Archives`, `~/Media/`).
- **Morning Briefing:** Speaks a morning system health briefing at 08:30 AM using the Iron Man British voice.

### 7. Master Process Lifecycle & Kill-Switch
- One command to start all services: `uv run jarvis start`
- Master Kill-Switch to cleanly terminate everything: `uv run jarvis stop` (or one-click UI button)

### 8. Iron Man Voice Profile
- Refined British AI butler voice (`en-GB-RyanNeural`) with tuned cadence (`+2%` rate, `-4Hz` pitch).

---

## 🚀 Quick Reference Commands

```bash
# 1. Master Startup (Web UI, Spotlight, Telegram, Watchdogs)
uv run jarvis start

# 2. Check System Status & Running Daemons
uv run jarvis status

# 3. Master Kill-Switch (Cleanly terminate all background services)
uv run jarvis stop

# 4. Run a task directly via CLI
uv run jarvis run "Open calculator and calculate 987 * 654"

# 5. Run with Voice (STT + Iron Man Spoken Response)
uv run jarvis voice

# 6. Launch Everyday Browser with CDP Remote Debugging
uv run jarvis cdp

# 7. Inspect Audit Trail of Past Runs
uv run jarvis audit

# 8. Manage Credentials in Vault
uv run jarvis vault set telegram_bot_token "YOUR_BOT_TOKEN"
uv run jarvis vault set telegram_chat_id "YOUR_CHAT_ID"
uv run jarvis vault list

# 9. List Structured Memory Files
uv run jarvis memory list
```

---

## 🧪 Testing

Run the full automated test suite (18 unit and integration tests):
```bash
uv run pytest -v
```
