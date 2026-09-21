# 🤖 Jarvis: Autonomous Personal AI Assistant for Linux X11

Jarvis is a powerful, cost-effective personal AI assistant tailored for Linux workstations (X11). It combines **Vision-based Computer Use** (driving desktop apps and mouse/keyboard), an **isolated sandboxed Playwright browser**, an **inline Python runner** (for background scripts, data processing, and Telegram bot messaging), a **voice interface** with speech-to-text and text-to-speech, a **safety approval overlay**, and an **on-demand lean Markdown memory store**.

---

## 🌟 Key Highlights

- **100% Zero-Billing Local AI Support:** Runs locally on your NVIDIA RTX 3060 GPU using Ollama:
  - **Reasoning & Planning:** `gemma4:12b`
  - **Vision UI Grounding:** `qwen2.5vl:7b`
- **Optional Cloud Escalation:** Configurable fallback to Google Gemini 3.8 / 2.5 Flash (compatible with Google AI Studio's $0 free tier).
- **Vision Computer Use:** Real-time X11 screen capture (`mss`), visual coordinate prediction, and human-like mouse/keyboard interaction (`pyautogui`).
- **Isolated Web Automation:** Headless or visual Playwright browser with persistent sandboxed user session.
- **Python Task Runner:** Runs arbitrary Python tasks, heavy data processing routines, and Telegram bot messaging without leaving the assistant.
- **Configurable Output Modality:** Get responses in `cli`, `voice`, or `both`.
- **Safety Gatekeeper & Approval Overlay:** Automatically classifies actions into safe vs high-stakes (e.g. deletions, payments, emails). High-stakes actions trigger an always-on-top approval overlay with `Enter` (Approve) / `Esc` (Reject) hotkeys.
- **Lean Markdown Memory:** Selective, on-demand loading of memory files (`preferences.md`, `system.md`, `contacts.md`, `workflows/*.md`) keeps context lean and token-efficient.
- **Secure Secret Vault:** Stores tokens, passwords, and API keys securely using Linux Secret Service / Keyring.

---

## 🚀 Quickstart

### 1. Requirements
- Linux X11
- Python 3.11+
- `uv` package manager (`snap install astral-uv` or `curl -LsSf https://astral.sh/uv/install.sh | sh`)
- Ollama with `gemma4:12b` and `qwen2.5vl:7b`

### 2. Installation
```bash
# Clone or navigate to the directory
cd /home/pritam/code/ai/jarvis

# Install dependencies and sync virtual environment
uv sync

# Install Playwright browser
uv run playwright install chromium
```

---

## 🛠️ Usage

### Run a Task via CLI
```bash
# Run a desktop or browser task
uv run jarvis run "Open calculator and compute 987 * 654"

# Run a web automation task
uv run jarvis run "Search Wikipedia for James Webb Telescope and summarize the first paragraph"

# Run with full autonomy (disables confirmation overlay)
uv run jarvis run "Process the data in /tmp/data.csv" --autonomous

# Override model policy for a specific run
uv run jarvis run "Analyze complex UI layout" --policy tier_fallback
```

### Voice Mode
```bash
# Record for 5 seconds and execute recognized command
uv run jarvis voice

# Custom recording duration
uv run jarvis voice --duration 8
```

### Python Script & Telegram Bot Execution
Jarvis can directly execute Python routines. Store your Telegram Bot Token and Chat ID in the vault:
```bash
uv run jarvis vault set telegram_bot_token "YOUR_TELEGRAM_BOT_TOKEN"
uv run jarvis vault set telegram_chat_id "YOUR_CHAT_ID"

# Then instruct Jarvis:
uv run jarvis run "Send a telegram message saying 'Build complete!' using the python runner"
```

---

## ⚙️ Configuration (`config.yaml`)

Manage configuration easily via CLI or by editing `config.yaml`:
```bash
# Show configuration
uv run jarvis config show

# Switch output mode to CLI-only or voice-only
uv run jarvis config set output_mode cli
uv run jarvis config set output_mode voice
uv run jarvis config set output_mode both

# Switch model policy: "local_only", "tier_fallback", or "cloud_only"
uv run jarvis config set model.policy local_only
```

---

## 🧠 Lean Markdown Memory

Memory is stored in `~/.jarvis/memory/`. Jarvis only loads specific files when relevant:
- `preferences.md`: User persona and rules.
- `system.md`: Workstation specifications and display configuration.
- `contacts.md`: People and handles.
- `workflows/`: Task recipes (e.g. `telegram.md`, `data_processing.md`).

```bash
# Inspect stored memory files
uv run jarvis memory list
```

---

## 🧪 Running Tests

```bash
uv run pytest -v
```
