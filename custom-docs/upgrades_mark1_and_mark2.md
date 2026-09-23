# ⚡ JARVIS Architectural Evolution: Mark 1 vs. Mark 2

Comprehensive technical comparison and capability documentation detailing the architecture, features, and operational improvements introduced in **JARVIS Mark 1** and extended in **JARVIS Mark 2**.

---

## 📊 High-Level Comparison Matrix

| Architectural Subsystem | 🛡️ JARVIS Mark 1 | ⚡ JARVIS Mark 2 |
| :--- | :--- | :--- |
| **Product Designation** | `JARVIS // Mark 1` | `JARVIS // Mark 2` |
| **Cognitive Core Loop** | Asynchronous Perception-Reasoning-Action (ReAct) with Tier-0 fast router and Tier-1 Gemma 4 12B | ReAct loop enhanced with real-time Knowledge Graph RAG context injection |
| **Voice Synthesis (TTS)** | Microsoft Edge Neural (`en-GB-RyanNeural`), speed/pitch/volume controls | Edge Neural + **Subprocess tracking** with instantaneous player termination |
| **Audio Barge-In** | None (User had to wait for speech synthesis audio to finish completely) | **Sub-10ms Instant Barge-In** via Arc Reactor click, operator speech detection, or <kbd>Esc</kbd> key (`POST /api/voice/stop`) |
| **Speech-to-Text (STT)** | Browser Web Speech API only | **Dual STT Pipeline:** Browser Web Speech API + **Offline CUDA Faster-Whisper** (`POST /api/voice/transcribe`) |
| **Knowledge & Memory** | Static file keyword matching (`preferences.md`, `system.md`, `contacts.md`, `workflows/`) | **Hybrid Semantic RAG Engine:** Heading-anchored chunking, BM25 statistical ranking, and local Ollama vector embeddings |
| **Obsidian Integration** | None | Full recursive vault indexing (`~/obsidian/KnowledgeBase/ai-memory/`), 1-click reindexing, and real-time query testbench |
| **Sound Effects (SFX)** | None (Silent UI transitions) | **Real-Time Web Audio API Synthesis** (Zero external downloads, dynamic oscillators for chimes, pulses, alerts) |
| **HUD Keyboard Ergonomics** | Basic tab navigation | **Tactical Shortcuts HUD Modal** (<kbd>?</kbd>), direct keys (<kbd>1</kbd>-<kbd>5</kbd>, <kbd>F</kbd>, <kbd>M</kbd>, <kbd>Esc</kbd>) |
| **Code Snippet Utility** | Plain monospace text blocks | **1-Click Floating Copy Button** with clipboard integration, audio cue, and visual confirmation |
| **Test Suite Coverage** | 55 unit/integration tests | 60 unit/integration tests (100% passing) |

---

## 🛡️ JARVIS Mark 1: Foundational Architecture & Capabilities

JARVIS Mark 1 was designed from the ground up for a Linux workstation (X11) powered by an **AMD Ryzen 7**, **NVIDIA RTX 3060 (12 GB VRAM)**, and **96 GB of RAM**, running completely local with zero cloud subscription requirements.

### 1. Multi-Tier Cognitive ReAct Hierarchy
- **Tier-0 Intent Classifier:** Sub-100ms intent routing via `llama3.2:3b`. Distinguishes conversational questions from high-stakes computer actions.
- **Tier-1 Reasoning Core:** `gemma4:12b` pinned permanently into VRAM using `keep_alive: "-1"` to eliminate model loading disk latency.
- **Visual Grounding Perceptor:** `qwen2.5-vl:7b` for screenshot perception, coordinate bounding, and UI element targeting.

### 2. Four Seamless Communication Modalities
1. **Tactical Glassmorphic Web HUD (`:8765`):** Monospace terminal stream, system status, hardware gauges, and live run inspection.
2. **Context-Aware Spotlight Bar (<kbd>Alt</kbd> + <kbd>J</kbd>):** Native translucent X11 overlay capturing active window titles and clipboard buffers.
3. **CLI Terminal Interface (`jarvis voice`):** Interactive terminal and voice command runner.
4. **Two-Way Telegram Remote Bot:** Remote workstation execution and voice note replies while away from the desk.

### 3. Everyday Browser CDP vs. Sandboxed Web
- **Everyday Chrome CDP (:9222):** Direct connection to active, logged-in workstation browser sessions to bypass 2FA, session cookies, and CAPTCHAs.
- **Isolated Playwright Sandbox:** Headless, quarantined browser for untrusted web scraping and exploratory tasks.

### 4. Autonomous Execution & Safety Gatekeeper
- Visual approval overlay on X11 when terminal commands or actions match high-risk patterns (`rm -rf`, `sudo`, `dd`, `chmod`).
- 60-second automatic fallback timeout to prevent orphaned background states.

### 5. Multi-Desktop Display Perception
- Physical and virtual monitor enumeration using `xrandr` and `mss`.
- Allows the user to dictate which display screen Jarvis inspects and interacts with.

### 6. Proactive Sentinels Matrix
- **Hardware Sentinel:** Continuous background watchdog tracking GPU VRAM, temperatures, and storage thresholds.
- **Download Auto-Organizer:** Periodic cleanup and rule-based sorting of `~/Downloads`.
- **Morning Workstation Brief:** On-demand or scheduled briefing delivered via the Iron Man British butler voice (`en-GB-RyanNeural`).

### 7. Dedicated Fullscreen Audio HUD Stage
- Symmetrical Arc Reactor holographic core with multi-ring animation (`ring-outer`, `ring-middle`, `ring-inner`).
- Hands-Free continuous microphone loop automatically re-arming after Jarvis finishes speaking.

---

## ⚡ JARVIS Mark 2: Evolutionary Upgrades & Innovations

JARVIS Mark 2 advances the platform into a fluid, enterprise-grade personal operating assistant with immediate voice responsiveness, offline neural STT, deep personal knowledge retrieval, and tactile audio-visual ergonomics.

```
                           JARVIS MARK 2 ARCHITECTURE
  
       ┌────────────────────────────────────────────────────────┐
       │                  USER INPUT CHANNELS                   │
       │   Web HUD Mic  •  Alt+J Spotlight  •  Telegram  •  CLI  │
       └───────────────────────────┬────────────────────────────┘
                                   │
                      ┌────────────┴────────────┐
                      ▼                         ▼
         [Browser Cloud STT]       [Offline CUDA Faster-Whisper]
                      │                         │
                      └────────────┬────────────┘
                                   │
       ┌───────────────────────────▼────────────────────────────┐
       │          HYBRID SEMANTIC RAG KNOWLEDGE ENGINE          │
       │   ~/ai-memory/jarvis  +  ~/obsidian/KnowledgeBase/...  │
       │       BM25 Keyword Scoring + Ollama Embeddings         │
       └───────────────────────────┬────────────────────────────┘
                                   │ (Enriched System Prompt)
                                   ▼
       ┌────────────────────────────────────────────────────────┐
       │              TIERED COGNITIVE REACT LOOP               │
       │  Tier-0 (Llama 3.2 3B)  ──>  Tier-1 (Gemma 4 12B)       │
       │  Qwen2.5-VL Grounding   ──>  Safety Gatekeeper          │
       └───────────────────────────┬────────────────────────────┘
                                   │
                      ┌────────────┴────────────┐
                      ▼                         ▼
            [Actuators & Runners]    [Voice Synthesis Engine]
            • Desktop GUI (pyautogui) • Edge-TTS (en-GB-Ryan)
            • Chrome CDP / Playwright • Subprocess PID Tracking
            • Python Data Runner      • ⚡ Instant Barge-In Stop
```

### 1. Instant Voice Barge-In & Subprocess Cancellation
- **The Problem in Mark 1:** When Jarvis was reciting long explanations or system statuses, the operator had to wait until audio playback completed or mute system volume.
- **The Mark 2 Solution:**
  - `TextToSpeech` in [tts.py](file:///home/pritam/code/ai/jarvis/src/jarvis/voice/tts.py) now maintains reference to `self._current_player_process: Optional[subprocess.Popen]`.
  - Added `stop()` method to kill active `ffplay` or `mpv` processes in sub-10ms.
  - Exposed via `POST /api/voice/stop` in [server.py](file:///home/pritam/code/ai/jarvis/src/jarvis/ui/server.py).
  - In the Tactical HUD, clicking the Arc Reactor core while speaking, pressing <kbd>Esc</kbd>, or speaking into the mic immediately triggers a low punchy reactor cutoff tone and resets the system to `LISTENING`.

### 2. Dual STT Pipeline (Browser Cloud vs. Local GPU Faster-Whisper)
- **The Problem in Mark 1:** Speech recognition relied entirely on the browser's Web Speech API, requiring an internet connection to Google/browser cloud servers.
- **The Mark 2 Solution:**
  - Integrated `SpeechToText.transcribe_bytes()` utilizing local CUDA `faster-whisper` (`base.en` or `small.en`) on the workstation's RTX 3060.
  - Added `POST /api/voice/transcribe` endpoint for multipart audio buffer processing.
  - Operator can select between **Browser Cloud Streaming** and **Local GPU Faster-Whisper** directly in **Settings -> Voice & Speech Matrix**.

### 3. Obsidian Knowledge Base Hybrid Semantic RAG Engine
- **The Problem in Mark 1:** Memory retrieval was constrained to exact keyword checks across hardcoded files (`preferences.md`, `system.md`, `contacts.md`).
- **The Mark 2 Solution:**
  - Created [rag.py](file:///home/pritam/code/ai/jarvis/src/jarvis/memory/rag.py) featuring `HybridRAGEngine`.
  - Recursively indexes both `~/ai-memory/jarvis` and the operator's entire Obsidian Vault (`~/obsidian/KnowledgeBase/ai-memory/`).
  - Chunks documents by markdown header boundaries (`#`, `##`, `###`), preserving semantic context.
  - Combines BM25 term frequency / inverse document frequency (TF-IDF) scoring with local vector embeddings (`nomic-embed-text` via Ollama).
  - Context is formatted as clean section markdown comments and injected directly into the LLM system prompt:
    ```markdown
    <!-- KNOWLEDGE: career/cdac-pune.md | Section: Deployment Architecture -->
    ### Deployment Architecture (from `career/cdac-pune.md`)
    Deployed microservices using Docker Swarm and Kubernetes...
    ```

### 4. Interactive Obsidian Management Studio
- Located in **Memory & Secrets -> KNOWLEDGE RAG -> Obsidian Vault RAG**:
  - Live display of indexed knowledge chunks badge.
  - Form to update and persist the Obsidian Vault folder path.
  - **Re-Index Knowledge Base** button that rescans all notes in real time.
  - **Test Real-Time Knowledge Retrieval** input field to test queries against the knowledge base and inspect matches before running missions.

### 5. Tactical Web Audio SFX Synthesis
- **Zero Asset Overhead:** Synthesizes sound frequencies dynamically in JavaScript using the browser's native `AudioContext` and oscillators.
- **Sound Palette:**
  - `mic_start`: Dual-tone rising chime (587Hz -> 880Hz).
  - `mic_stop`: Dual-tone falling chime (784Hz -> 440Hz).
  - `barge_in`: Punchy low-frequency reactor cutoff pulse (180Hz -> 40Hz exponential decay).
  - `success`: Upbeat tactical harmonic triad (C5, E5, G5).
  - `warning`: Dual-tone sawtooth alert pulse (320Hz / 440Hz).
- Toggleable via **Settings -> Tactical Web Audio SFX** with a **Test SFX** button.

### 6. Tactical Keyboard Shortcuts HUD Modal
- Pressing <kbd>?</kbd> or clicking the top header `[?]` button opens the **Tactical Keyboard Shortcuts Modal**:
  - <kbd>1</kbd>: Command Center Cockpit
  - <kbd>2</kbd>: Agent Terminal Console
  - <kbd>3</kbd>: Sentinels & Safety Matrix
  - <kbd>4</kbd>: System Telemetry & KPIs
  - <kbd>5</kbd>: Tactical Manual & Documentation
  - <kbd>F</kbd>: Fullscreen Audio HUD Stage
  - <kbd>M</kbd>: Toggle Microphone / Hands-Free Loop
  - <kbd>Esc</kbd>: Instant Barge-In / Dismiss Overlays

### 7. 1-Click Code Block Copying
- All terminal output lines containing code fences (```` ```python ... ``` ````) automatically render as stylized syntax blocks with a floating **COPY** button.
- Clicking the button writes the snippet to the system clipboard, plays the `success` audio chime, and displays a green **COPIED!** indicator.

---

## 📂 Source Code Modifications Reference

| Subsystem | File Path | Scope of Enhancement |
| :--- | :--- | :--- |
| **RAG Engine** | [src/jarvis/memory/rag.py](file:///home/pritam/code/ai/jarvis/src/jarvis/memory/rag.py) | **[NEW]** `HybridRAGEngine`, markdown section chunking, BM25 scoring, and Ollama embedding integration |
| **Memory Store** | [src/jarvis/memory/store.py](file:///home/pritam/code/ai/jarvis/src/jarvis/memory/store.py) | Upgraded `get_relevant_memory()` to query `HybridRAGEngine`, auto-reindexing on `save_workflow()` |
| **Voice Playback** | [src/jarvis/voice/tts.py](file:///home/pritam/code/ai/jarvis/src/jarvis/voice/tts.py) | Subprocess PID tracking (`self._current_player_process`), `stop()` termination method |
| **Voice STT** | [src/jarvis/voice/stt.py](file:///home/pritam/code/ai/jarvis/src/jarvis/voice/stt.py) | Added `transcribe_bytes()` for memory buffer transcription |
| **Configuration** | [src/jarvis/config.py](file:///home/pritam/code/ai/jarvis/src/jarvis/config.py) & [config.yaml](file:///home/pritam/code/ai/jarvis/config.yaml) | Added `stt_engine`, `sfx_enabled`, `obsidian_vault_dir`, `semantic_search_enabled`, `embedding_model` |
| **API Server** | [src/jarvis/ui/server.py](file:///home/pritam/code/ai/jarvis/src/jarvis/ui/server.py) | Added `/api/voice/stop`, `/api/voice/transcribe`, `/api/memory/obsidian`, `/api/memory/reindex` |
| **Tactical HUD** | [src/jarvis/ui/web/index.html](file:///home/pritam/code/ai/jarvis/src/jarvis/ui/web/index.html) | Mark 2 branding, Web Audio SFX, Shortcuts modal, Obsidian RAG UI, STT selector, code copy buttons |
| **Testing** | [tests/test_mark2_features.py](file:///home/pritam/code/ai/jarvis/tests/test_mark2_features.py) | **[NEW]** Unit tests for RAG chunking, BM25, `/api/voice/stop`, `/api/voice/transcribe`, and Obsidian config |
| **User Guide** | [user-guide.md](file:///home/pritam/code/ai/jarvis/user-guide.md) | Comprehensive Mark 2 manual updates |
| **README** | [README.md](file:///home/pritam/code/ai/jarvis/README.md) | Mark 2 architecture and capabilities summary |
