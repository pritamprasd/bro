# 🤖 Jarvis AI Assistant: Implementation & Verification Walkthrough

Jarvis is a personal AI assistant built for Linux X11 workstations with an NVIDIA RTX 3060 GPU. It operates with **zero billing required** using local models via Ollama, supports optional cloud escalation, and drives desktop applications, an isolated Playwright browser, an inline Python executor, and a voice interface.

---

## What Was Built

### 1. Unified Configuration & Project Architecture
- **Package Manager:** Configured with `uv` for ultra-fast package management and dependency isolation in `~/code/ai/jarvis`.
- **`config.yaml` & `jarvis/config.py`:** Pydantic schema supporting:
  - `model.policy`: `"local_only"` ($0, no cloud/billing needed), `"tier_fallback"`, or `"cloud_only"`.
  - `output_mode`: `"both"` (CLI + Voice), `"cli"` (Text only), or `"voice"` (Spoken only).
  - `autonomous_mode`: `false` (default) or `true`.
  - `voice`, `safety`, `browser`, and `memory` paths.

### 2. Multi-Tier Model Routing Layer (`jarvis/models/`)
- **Ollama Provider (`ollama_provider.py`):**
  - **Text & Tool Reasoning:** Uses local `gemma4:12b` (already installed in your Ollama).
  - **Visual Grounding:** Uses local `qwen2.5vl:7b` (already installed in your Ollama) to translate screenshots into `(x, y)` UI coordinates and actions.
- **Gemini Cloud Provider (`gemini_provider.py`):**
  - Integrates with Google GenAI SDK. Supports Gemini 3.8 / 2.5 Flash using Google AI Studio's $0 free tier (no credit card or billing setup required).
- **Model Router (`router.py`):**
  - Enforces policy and handles automatic fallback if local visual grounding confidence is low.

### 3. Actuators for Computer Use & Python Execution (`jarvis/actuators/`)
- **Desktop Actuator (`desktop.py`):** High-speed X11 screen capture (`mss`), mouse clicks, double clicks, right clicks, drags, scrolling, and keyboard typing (`pyautogui`). Tested natively on your 1920x1080 display.
- **Isolated Browser Actuator (`browser.py`):** Playwright Chromium browser running in a sandboxed user data profile (`~/.jarvis/browser_data`), keeping your personal everyday browser logins separate while preserving Jarvis automation cookies.
- **Python Task Runner (`python_runner.py`):** Executes arbitrary Python scripts, background data crunching, and Telegram Bot API messaging (`requests`). Injects secrets securely from the vault as environment variables.
- **Shell Actuator (`shell.py`):** Runs local bash commands safely with timeouts and output capture.

### 4. Safety Gatekeeper & On-Screen Approval Overlay (`jarvis/core/safety.py`, `jarvis/ui/overlay.py`)
- **Risk Classifier:** Classifies proposed actions into safe vs high-stakes based on destructive shell commands, payments, emails, credential handling, or file removals.
- **Floating Approval Overlay:** A modern dark-themed always-on-top dialog on X11 with `Enter` (Approve) and `Esc` (Reject) hotkeys, with automatic fallback to an interactive CLI prompt.
- **Autonomy Switch:** Fully respects `autonomous_mode: false` (requires confirmation) or `true` (unattended execution).

### 5. Lean On-Demand Markdown Memory & Vault (`jarvis/memory/`, `jarvis/security/`)
- **Memory Store (`store.py`):** Compact, topic-specific markdown files in `~/.jarvis/memory/`:
  - `preferences.md`: User profile & assistant tone.
  - `system.md`: Linux workstation hardware & display details.
  - `contacts.md`: People & email/messaging handles.
  - `workflows/`: Task recipes (e.g. `telegram.md`, `data_processing.md`).
- **Selective Loading:** Only matches and loads the specific file needed for the user's prompt, preventing context window bloat.
- **Secret Vault (`vault.py`):** Stores passwords, bot tokens, and API keys securely in the Linux Secret Service / Keyring with a secure fallback store.

### 6. Voice & CLI Interface (`jarvis/voice/`, `jarvis/ui/console.py`)
- **Text-to-Speech:** Fast, natural voice synthesis using `edge-tts` (`en-US-GuyNeural`) with non-blocking background playback.
- **Speech-to-Text:** `faster-whisper` GPU-accelerated transcription on your RTX 3060.
- **Rich Console:** Live log streaming, thought panels, action breadcrumbs, and formatted markdown results.

---

## Verification & Test Results

### 1. Automated Unit & Integration Tests
Ran `uv run pytest -v` covering all core subsystems:
```
tests/test_agent.py::test_agent_react_loop_finish PASSED                 [  8%]
tests/test_agent.py::test_agent_react_loop_with_python_action PASSED     [ 16%]
tests/test_config.py::test_default_config PASSED                         [ 25%]
tests/test_config.py::test_output_mode_options PASSED                    [ 33%]
tests/test_memory.py::test_lean_selective_memory_loading PASSED          [ 41%]
tests/test_memory.py::test_save_and_retrieve_custom_workflow PASSED      [ 50%]
tests/test_python_runner.py::test_python_runner_execution PASSED         [ 58%]
tests/test_python_runner.py::test_python_runner_env_injection PASSED     [ 66%]
tests/test_python_runner.py::test_python_runner_error_capture PASSED     [ 75%]
tests/test_safety.py::test_safe_action PASSED                            [ 83%]
tests/test_safety.py::test_high_stakes_keywords PASSED                   [ 91%]
tests/test_safety.py::test_destructive_shell_patterns PASSED             [100%]

============================== 12 passed in 0.64s ==============================
```

### 2. Live Actuator Tests
- **X11 Screen Capture:** Verified native resolution grab `(1920, 1080)` in <20ms using `mss.MSS()`.
- **Isolated Playwright Browser:** Verified Chromium launch, navigation to `example.com`, content extraction, and clean shutdown.
- **Secret Vault CLI:** Verified `uv run jarvis vault set test_key test_secret_123` and `uv run jarvis vault get test_key` (properly masked as `tes...123`).
- **Memory Inspector:** Verified `uv run jarvis memory list` automatically indexed `preferences.md`, `system.md`, `contacts.md`, and `workflows/telegram.md`.

---

## Quick Reference CLI Commands

```bash
# 1. Run a task (Desktop, Browser, or Python)
uv run jarvis run "Open calculator and compute 123 * 456"

# 2. Run with voice (Speech-to-Text + Spoken audio output)
uv run jarvis voice

# 3. Store a Telegram Bot Token & Chat ID in the vault
uv run jarvis vault set telegram_bot_token "123456:ABC-DEF..."
uv run jarvis vault set telegram_chat_id "987654321"

# 4. Configure output mode or autonomy
uv run jarvis config set output_mode both       # or "cli" or "voice"
uv run jarvis config set autonomous_mode true    # or false

# 5. List and inspect memory files
uv run jarvis memory list
```
