# Walkthrough: Web UI Voice Selection Dropdown & Persona Switching

We have integrated a real-time Voice Selection dropdown into the Jarvis Web UI HUD, allowing the user to select and preview available neural speech synthesis voices on the fly.

## Changes Implemented

### 1. Backend Endpoints ([`src/jarvis/ui/server.py`](src/jarvis/ui/server.py))
- **`GET /api/voice/voices`**: Queries Edge-TTS voices dynamically (with curated offline fallback) and prioritizes recommended personas (`en-GB-RyanNeural`, `en-US-GuyNeural`, `en-US-JennyNeural`, `en-US-ChristopherNeural`, `en-GB-SoniaNeural`, etc.).
- **`POST /api/voice/select`**: Updates the active voice persona in memory, saves the preference permanently to `config.yaml`, hot-swaps the active `TextToSpeech` engine without needing a system restart, and broadcasts `voice_changed` to connected clients via WebSockets.
- **`POST /api/voice/preview`**: Plays on-demand audio samples using the selected neural voice so the user can test different personas without changing conversation modes.
- **`GET /api/status`**: Now exposes `tts_voice` to keep UI clients synchronized across browser tabs or mobile devices.

### 2. Frontend HUD Controls ([`src/jarvis/ui/web/index.html`](src/jarvis/ui/web/index.html))
- **Header Controls Capsule**: Added a glassmorphic `.voice-selector-wrapper` alongside Conversation Mode pills and Desktop selector. Contains `#voice-select-dropdown` and the `#btn-voice-preview` (Test) button.
- **Audio-Only Mission Control HUD**: Integrated `#audio-hud-voice-select` inside the continuous voice interface header bar.
- **Model Selection Tab**: Added a dedicated **Step 4: Voice Persona & Synthesis** configuration card.
- **State Synchronization**: All three dropdown locations stay synchronized via WebSocket notifications and status polling.

### 3. Documentation ([`user-guide.md`](user-guide.md))
- Updated Section 6 with complete instructions on Edge-TTS voice persona selection, previewing voices, and automatic configuration persistence.

---

## Verification & Results

### Automated Unit Tests
Executed the test suite with our new voice endpoint tests ([`tests/test_ui_voice.py`](tests/test_ui_voice.py)):
```bash
uv run pytest
```
**Result**: All 37 unit tests passed cleanly (including 3 new voice API tests and 6 TTS formatting tests).

### Interactive Browser Verification
Using the browser subagent, we performed end-to-end testing on `http://localhost:8765`:
1. Verified that `#voice-select-dropdown` and the Test button render in the header with cyan glassmorphic styling.
2. Verified that voices are populated with categorized groups (`RECOMMENDED PERSONAS` and `ALL VOICES`).
3. Selected `Guy - English (United States) [Male]` and triggered the `Test` preview button:
   - Verified that the terminal logged:
     - `[SYSTEM] 🎙️ Jarvis vocal persona switched to: Guy - English (United States) (en-US-GuyNeural).`
     - `🔊 Previewing voice persona: Guy - English (United States)...`
4. Switched to `Audio` mode: verified that the dedicated Arc Reactor Audio-Only HUD displayed `#audio-hud-voice-select`.
5. Navigated to `Model Selection` tab: verified that card 4 (*Voice Persona & Synthesis*) rendered with `#sel-voice-model`.

### Visual Verification
*Voice Selector on Web HUD verified.*
