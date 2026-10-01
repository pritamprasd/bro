# ⚙️ BRO Configuration & Environment Variables Reference

This document provides a comprehensive technical specification for all configuration properties, environment variables, schema models, and override behaviors in **BRO**.

---

## 📑 Table of Contents
1. [Configuration Hierarchy & Resolution Order](#1-configuration-hierarchy--resolution-order)
2. [Environment Variables (`.env` / `.env.example`)](#2-environment-variables-env--envexample)
3. [Schema Reference (`src/bro/config.py` & `config.yaml`)](#3-schema-reference-srcbroconfigpy--configyaml)
   - [Model Configuration (`ModelConfig`)](#modelconfig)
   - [Voice & Acoustic Configuration (`VoiceConfig`)](#voiceconfig)
   - [Safety & High-Stakes Interception (`SafetyConfig`)](#safetyconfig)
   - [Browser Automation (`BrowserConfig`)](#browserconfig)
   - [Memory & Hybrid RAG (`MemoryConfig`)](#memoryconfig)
   - [Watchdogs & Proactive Sentinels (`WatchdogsConfig`)](#watchdogsconfig)
   - [Web Tactical HUD (`WebUIConfig`)](#webuiconfig)
   - [Desktop Spotlight (`SpotlightConfig`)](#spotlightconfig)
   - [Desktop Multi-Monitor Display (`DesktopConfig`)](#desktopconfig)
   - [Top-Level Runtime Configuration (`BroConfig`)](#broconfig)
4. [Deployment Profiles & Example Recipes](#4-deployment-profiles--example-recipes)

---

## 1. Configuration Hierarchy & Resolution Order

When Bro initializes via CLI (`bro start`, `bro run`), Python scripts, or the Web HUD daemon, configuration is dynamically compiled in the following precedence order (highest to lowest):

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Explicit CLI Flags (e.g., --policy, --autonomous, -f)    │ ◄ Highest Precedence
├─────────────────────────────────────────────────────────────┤
│ 2. System Environment Variables & .env Overrides            │
├─────────────────────────────────────────────────────────────┤
│ 3. Project-Local Configuration (./config.yaml)              │
├─────────────────────────────────────────────────────────────┤
│ 4. User Global Configuration (~/.bro/config.yaml)           │
├─────────────────────────────────────────────────────────────┤
│ 5. Hardcoded Pydantic Defaults                              │ ◄ Lowest Precedence
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Environment Variables (`.env` / `.env.example`)

Environment variables take precedence over YAML values and are loaded automatically via `python-dotenv`.

| Variable | Type | Default Value | Description |
| :--- | :--- | :--- | :--- |
| `BRO_CONFIG_DIR` | `string` (Path) | `~/.bro` | Root directory for application state, browser profile data, key index, and fallback secrets. |
| `BRO_MEMORY_DIR` | `string` (Path) | `~/ai-memory/bro` | Storage location for persistent markdown memory (`preferences.md`, `calendar.md`, `greetings.md`). |
| `OBSIDIAN_VAULT_DIR` | `string` (Path) | `~/obsidian/KnowledgeBase/ai-memory` | Path to Obsidian vault root for Hybrid BM25 + dense embedding context retrieval. Set to empty string or `null` to disable Obsidian integration. |
| `ORGANIZER_WATCH_DIR` | `string` (Path) | `~/Downloads` | Monitored directory for the automated file sorting watchdog. |
| `WEB_UI_HOST` | `string` | `0.0.0.0` | Network binding interface for the Web HUD server. |
| `WEB_UI_PORT` | `integer` | `8765` | Port for the Web HUD dashboard and WebSocket streaming. |
| `GEMINI_API_KEY` | `string` | `None` | Google Gemini API Studio key for cloud model fallback and multimodal vision. |
| `OPENAI_API_KEY` | `string` | `None` | OpenAI API key for GPT-4o / o-series gateway routing. |
| `GROQ_API_KEY` | `string` | `None` | Groq API key for low-latency Llama-3 cloud inference. |
| `TELEGRAM_BOT_TOKEN` | `string` | `None` | Telegram Bot token for mobile two-way companion bridge. |
| `TELEGRAM_CHAT_ID` | `string` / `int` | `None` | Authorized Telegram user or chat ID for security verification. |

---

## 3. Schema Reference (`src/bro/config.py` & `config.yaml`)

### `ModelConfig`
Defines the local and cloud LLM execution tiers, model tags, and offloading policy.

```yaml
model:
  policy: local_only
  tier0_enabled: true
  tier0_model: llama3.2:3b
  tier0_timeout: 5.0
  tier0_device: cpu
  local_text_model: gemma4:12b
  local_vision_model: qwen2.5-vl:7b
  cloud_model: gemini-2.5-flash
  ollama_url: http://localhost:11434
  keep_alive: -1
  gemini_api_key: null
```

| Property | Type | Default | Options / Details |
| :--- | :--- | :--- | :--- |
| `policy` | `Literal` | `"local_only"` | • `"local_only"`: 100% offline local inference via Ollama.<br>• `"tier_fallback"`: Escalates to cloud providers if local inference errors or exceeds context limits.<br>• `"cloud_only"`: Routes all queries directly through cloud gateway providers. |
| `tier0_enabled` | `bool` | `true` | Enables Tier-0 sub-100ms intent classification before invoking deep reasoning models. |
| `tier0_model` | `string` | `"llama3.2:3b"` | Ollama model identifier used for fast binary classification (`CONVERSATION` vs `COMPLEX_PLAN`). |
| `tier0_timeout` | `float` | `5.0` | Maximum latency window (in seconds) allowed for Tier-0 classification before bypassing. |
| `tier0_device` | `Literal` | `"cpu"` | • `"cpu"`: Enforces `num_gpu: 0` in Ollama, running Tier-0 purely on CPU threads to preserve 100% of GPU VRAM for Tier-1 models.<br>• `"gpu"`: Runs Tier-0 on GPU CUDA cores. |
| `local_text_model` | `string` | `"gemma4:12b"` | Primary Tier-1 reasoning and tool-calling model hosted on Ollama. |
| `local_vision_model` | `string` | `"qwen2.5-vl:7b"` | Multimodal vision model for analyzing screen captures, UI elements, and documents. |
| `cloud_model` | `string` | `"gemini-2.5-flash"` | Default cloud provider model when escalating or running in cloud-first mode. |
| `ollama_url` | `string` | `"http://localhost:11434"` | Base HTTP endpoint for the local Ollama daemon. |
| `keep_alive` | `Union[int, str]`| `-1` | Duration to keep models pinned in VRAM (`-1` for indefinite, or string duration like `"24h"`). |
| `gemini_api_key` | `Optional[str]` | `null` | API key for Google Gemini (can also be set via `GEMINI_API_KEY` env var). |

---

### `VoiceConfig`
Controls speech recognition (STT), neural speech synthesis (TTS), audio rate, and vocal personality.

```yaml
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
  stt_engine: browser
  sfx_enabled: true
  gen_z_greetings: false
```

| Property | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `enabled` | `bool` | `true` | Master toggle for all audio and voice pipelines. |
| `whisper_model` | `string` | `"base"` | Faster-Whisper model size (`tiny`, `base`, `small`, `medium`, `large-v3`). |
| `device` | `string` | `"cuda"` | Execution device for local Whisper transcription (`"cuda"` or `"cpu"`). |
| `compute_type` | `string` | `"float16"` | Quantization precision for Whisper (`"float16"`, `"int8"`, `"float32"`). |
| `tts_voice` | `string` | `"en-GB-RyanNeural"` | Edge-TTS neural voice model identifier. |
| `tts_rate` | `string` | `"+2%"` | Speech tempo modifier (e.g. `"+0%"`, `"+10%"`). |
| `tts_pitch` | `string` | `"-4Hz"` | Speech pitch modifier for tone modulation. |
| `tts_volume` | `integer` | `100` | Playback output volume (0% to 100%). |
| `always_voice_response`| `bool` | `false` | When true, Bro speaks all outputs aloud regardless of input modality. |
| `voice_reply_on_chat` | `bool` | `true` | Allows Bro to reply with voice when interacting via Web HUD chat. |
| `stt_engine` | `Literal` | `"browser"` | • `"browser"`: Low-latency continuous streaming via Web Speech API in HUD.<br>• `"whisper_local"`: Offline local audio processing using `faster-whisper`. |
| `sfx_enabled` | `bool` | `true` | Plays tactical Web Audio audio-cue chimes on state transitions. |
| `gen_z_greetings` | `bool` | `false` | When enabled, activates informal slang salutations from `greetings.md`. |

---

### `SafetyConfig`
Guards against destructive or sensitive shell, file, and network operations.

```yaml
safety:
  prompt_on_high_stakes: true
  high_stakes_keywords:
    - rm -rf
    - delete
    - destroy
    - sudo
    - passwd
    - shutdown
    - payment
```

| Property | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `prompt_on_high_stakes` | `bool` | `true` | When true, halts execution and prompts the user via a floating X11 Approval Overlay or Web Modal before executing dangerous commands. |
| `high_stakes_keywords` | `List[str]` | *Standard dangerous list* | Substring keyword triggers that intercept tool executions for human approval. |

---

### `BrowserConfig`
Configures sandboxed Playwright browser instances and Chrome DevTools Protocol (CDP) connectivity.

```yaml
browser:
  headless: false
  viewport_width: 1280
  viewport_height: 800
  user_data_dir: ~/.bro/browser_data
  cdp_port: 9222
```

| Property | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `headless` | `bool` | `false` | Controls whether Playwright browser instances display a visible window. |
| `viewport_width` | `integer` | `1280` | Default browser viewport pixel width. |
| `viewport_height` | `integer` | `800` | Default browser viewport pixel height. |
| `user_data_dir` | `string` | `"~/.bro/browser_data"` | Persistent storage path for browser cache, cookies, and local session data. |
| `cdp_port` | `integer` | `9222` | TCP port used to connect to your active Chrome browser session. |

---

### `MemoryConfig`
Defines markdown memory paths, vector embedding models, and Obsidian Vault integration.

```yaml
memory:
  memory_dir: ~/ai-memory/bro
  obsidian_vault_dir: ~/obsidian/KnowledgeBase/ai-memory
  semantic_search_enabled: true
  embedding_model: nomic-embed-text
```

| Property | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `memory_dir` | `string` | `"~/ai-memory/bro"` | Primary directory containing `preferences.md`, `calendar.md`, `greetings.md`, and workflows. |
| `obsidian_vault_dir` | `Optional[str]` | `"~/obsidian/..."` | Path to your personal Obsidian Vault for hybrid BM25 and vector context retrieval. |
| `semantic_search_enabled`| `bool` | `true` | Enables dense vector embedding similarity search in addition to BM25 keyword matching. |
| `embedding_model` | `string` | `"nomic-embed-text"`| Ollama model used for generating dense memory embeddings. |

---

### `WatchdogsConfig`
Defines proactive background services: Hardware Sentinels, Download Organizer, and Scheduled Briefings.

```yaml
watchdogs:
  sentinel:
    enabled: true
    check_interval_seconds: 30
    gpu_temp_threshold: 80
    disk_threshold_percent: 90
  organizer:
    enabled: false
    watch_dir: ~/Downloads
    rules:
      pdf: ~/Documents/PDFs
      csv,xlsx,json: ~/Documents/Data
      tar.gz,zip,rar,7z: ~/Downloads/Archives
      mp4,mkv,avi: ~/Media/Videos
      png,jpg,jpeg,webp: ~/Media/Images
  cron:
    enabled: false
    briefing_time: 08:30
```

| Property | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `sentinel.enabled` | `bool` | `true` | Monitors host hardware telemetry in the background. |
| `sentinel.check_interval_seconds` | `integer` | `30` | Polling frequency for hardware health checks. |
| `sentinel.gpu_temp_threshold` | `integer` | `80` | GPU temperature alert threshold in Celsius. |
| `sentinel.disk_threshold_percent` | `integer` | `90` | Disk usage alert threshold percentage. |
| `organizer.enabled` | `bool` | `false` | Enables automatic sorting of newly downloaded files. |
| `organizer.watch_dir` | `string` | `"~/Downloads"` | Monitored directory path for file organization. |
| `organizer.rules` | `Dict[str, str]` | *MIME map* | Mapping of comma-separated extensions to target destination directories. |
| `cron.enabled` | `bool` | `false` | Enables scheduled daily briefings. |
| `cron.briefing_time` | `string` | `"08:30"` | Time of day (`HH:MM`) to deliver the automated workstation briefing. |

---

### `WebUIConfig`, `SpotlightConfig`, & `DesktopConfig`

```yaml
web_ui:
  host: 0.0.0.0
  port: 8765
spotlight:
  enabled: true
  hotkey: <alt>+j
desktop:
  screen_index: 1
```

| Property | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `web_ui.host` | `string` | `"0.0.0.0"` | Network interface for FastAPI and WebSockets. |
| `web_ui.port` | `integer` | `8765` | Web HUD HTTP port. |
| `spotlight.enabled` | `bool` | `true` | Enables global desktop hotkey listener. |
| `spotlight.hotkey` | `string` | `"<alt>+j"` | Global X11 keyboard shortcut to summon the Spotlight search bar. |
| `desktop.screen_index` | `integer` | `1` | • `0`: Combined virtual canvas across all monitors.<br>• `1`: Primary Display 1 (default).<br>• `2`: Secondary Display 2. |

---

### `BroConfig` (Top-Level)

```yaml
conversation_mode: audio+chat
output_mode: both
autonomous_mode: false
```

| Property | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `conversation_mode` | `Literal` | `"audio+chat"` | • `"audio_only"`: Minimalist fullscreen Arc Reactor HUD with voice interaction.<br>• `"audio+chat"`: Hybrid interface with voice waveform and interactive chat stream.<br>• `"chat_only"`: Text-based interface without auto-listening. |
| `output_mode` | `Literal` | `"both"` | • `"both"`: Outputs text to terminal/web and speaks response via TTS.<br>• `"cli"`: Output to terminal/web only.<br>• `"voice"`: Speaks response aloud only. |
| `autonomous_mode` | `bool` | `false` | When true, skips confirmation prompts for high-stakes actions. |

---

## 4. Deployment Profiles & Example Recipes

### Profile A: Low-VRAM Laptop (8 GB GPU or CPU Only)
Optimized to conserve GPU memory by offloading Tier-0 to CPU and utilizing Cloud Gateway fallback for heavy coding:
```yaml
# config.yaml
model:
  policy: tier_fallback
  tier0_device: cpu
  local_text_model: llama3.2:3b
  cloud_model: gemini-2.5-flash
voice:
  stt_engine: browser
  compute_type: int8
```

### Profile B: Workstation Powerhouse (12 GB+ VRAM, e.g., Local GPU/4070)
Full local reasoning with concurrent vision perceiver and Tier-0 CPU isolation:
```yaml
# config.yaml
model:
  policy: local_only
  tier0_device: cpu
  local_text_model: gemma4:12b
  local_vision_model: qwen2.5-vl:7b
  keep_alive: -1
voice:
  stt_engine: browser
  tts_rate: +2%
```
