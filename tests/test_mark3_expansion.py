"""Comprehensive unit tests for Bro Variant 3 feature expansions."""

import asyncio
import json
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient

from bro.config import BroConfig, ModelConfig, VoiceConfig
from bro.voice.tts import TextToSpeech
from bro.actuators.desktop import DesktopActuator
from bro.models.tier0 import Tier0Router
from bro.gateway.router import LLMGatewayRouter
from bro.gateway.models import GatewayRequest, GatewayResponse
from bro.gateway.config import GatewaySettings, GatewayProviderConfig
from bro.watchdogs.daily_brief import DailyBriefEngine
from bro.ui.server import app


# ---------------------------------------------------------------------------
# 1. Pronunciation Normalization Tests
# ---------------------------------------------------------------------------
def test_tts_pronunciation_fixes():
    tts = TextToSpeech(VoiceConfig(enabled=False))

    # Binary memory unit fixes
    text1 = "Total memory is 12 GiB, with 512 MiB swap and 64 KiB buffer."
    cleaned1 = tts._clean_for_speech(text1)
    assert "12 GB" in cleaned1
    assert "512 MB" in cleaned1
    assert "64 KB" in cleaned1
    assert "GiB" not in cleaned1
    assert "MiB" not in cleaned1
    assert "KiB" not in cleaned1

    # Terabytes
    text2 = "Storage capacity is 2 TiB NVMe."
    cleaned2 = tts._clean_for_speech(text2)
    assert "2 TB" in cleaned2

    # Latency / millisecond units
    text3 = "Model inference took 45 ms."
    cleaned3 = tts._clean_for_speech(text3)
    assert "45 milliseconds" in cleaned3

    # Common acronyms preserved naturally or hyphenated for crisp phonetic delivery
    text4 = "Active GPU VRAM usage on the HUD via the IDE CLI API."
    cleaned4 = tts._clean_for_speech(text4)
    assert "GPU" in cleaned4
    assert "V-RAM" in cleaned4
    assert "hud" in cleaned4
    assert "I-D-E" in cleaned4
    assert "C-L-I" in cleaned4
    assert "A-P-I" in cleaned4


# ---------------------------------------------------------------------------
# 2. Desktop Window Inspection Tests
# ---------------------------------------------------------------------------
def test_desktop_window_inspection_mock():
    actuator = DesktopActuator()

    def mock_subprocess_run(cmd, *args, **kwargs):
        cmd_str = " ".join(cmd) if isinstance(cmd, list) else str(cmd)
        mock_res = MagicMock()
        mock_res.returncode = 0

        if "_NET_ACTIVE_WINDOW" in cmd_str:
            mock_res.stdout = "_NET_ACTIVE_WINDOW(WINDOW): window id # 0x3400003\n"
        elif "0x3400003" in cmd_str:
            mock_res.stdout = '_NET_WM_NAME(UTF8_STRING) = "Antigravity IDE - bro"\nWM_CLASS(STRING) = "antigravity", "Antigravity"\n'
        elif "_NET_CLIENT_LIST" in cmd_str:
            mock_res.stdout = "_NET_CLIENT_LIST(WINDOW): window id # 0x3400003, 0x2200001\n"
        elif "0x2200001" in cmd_str:
            mock_res.stdout = '_NET_WM_NAME(UTF8_STRING) = "Google Chrome - Dashboard"\nWM_CLASS(STRING) = "google-chrome", "Google-chrome"\n'
        else:
            mock_res.stdout = ""
        return mock_res

    with patch("subprocess.run", side_effect=mock_subprocess_run):
        win_info = actuator.get_open_windows_info()
        assert win_info["active_window"] is not None
        assert "Antigravity" in win_info["active_window"]
        assert len(win_info["open_apps"]) == 2
        assert any("Google-chrome" in c for c in win_info["open_apps"])

        # Also verify inspect_screen incorporates the window info
        with patch.object(actuator, "capture_screenshot", return_value=(None, "mock_b64")):
            with patch.object(actuator, "get_active_monitor_info", return_value={
                "screen_index": 0, "output": "HDMI-1", "width": 1920, "height": 1080
            }):
                res = actuator.inspect_screen()
                assert "Active Focused Window: Antigravity" in res.output
                assert "Google-chrome" in res.output


# ---------------------------------------------------------------------------
# 3. Tier-0 Classifier CPU Offloading Tests
# ---------------------------------------------------------------------------
def test_tier0_cpu_device_option():
    # When tier0_device is "cpu", num_gpu must be 0
    cfg_cpu = ModelConfig(tier0_device="cpu")
    router_cpu = Tier0Router(cfg_cpu)

    with patch("requests.post") as mock_post:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "message": {"content": '{"intent": "COMMAND", "confidence": 0.95}'}
        }
        mock_post.return_value = mock_resp

        res = router_cpu.classify("Check CPU temperature")
        assert res.intent == "COMMAND"

        # Check call arguments
        call_args, call_kwargs = mock_post.call_args
        payload = call_kwargs.get("json", {})
        assert payload.get("options", {}).get("num_gpu") == 0

    # When tier0_device is "gpu", num_gpu must NOT be 0
    cfg_gpu = ModelConfig(tier0_device="gpu")
    router_gpu = Tier0Router(cfg_gpu)

    with patch("requests.post") as mock_post:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "message": {"content": '{"intent": "CONVERSATION", "confidence": 0.95}'}
        }
        mock_post.return_value = mock_resp

        res = router_gpu.classify("Hello Bro")
        assert res.intent == "CONVERSATION"

        call_args, call_kwargs = mock_post.call_args
        payload = call_kwargs.get("json", {})
        assert "num_gpu" not in payload.get("options", {})


# ---------------------------------------------------------------------------
# 4. Enterprise LLM Gateway Tests
# ---------------------------------------------------------------------------
def test_llm_gateway_router():
    router = LLMGatewayRouter()

    providers = router.get_statuses()
    provider_ids = [p["id"] for p in providers]
    assert "gemini" in provider_ids
    assert "openai" in provider_ids
    assert "groq" in provider_ids
    assert "meta" in provider_ids
    assert "ollama" in provider_ids

    # Test mock completion via gateway
    mock_provider = router.providers["ollama"]
    with patch.object(mock_provider, "generate", return_value=GatewayResponse(
        content="Enterprise gateway response",
        provider="ollama",
        model="qwen2.5:7b",
        latency_ms=120.5
    )):
        req = GatewayRequest(prompt="Explain quantum computing", preferred_provider="ollama")
        resp = router.generate(req)
        assert resp.content == "Enterprise gateway response"
        assert resp.provider == "ollama"

    # Test toggling provider
    router.toggle_provider("openai", enabled=True)
    assert router.settings.providers["openai"].enabled is True

    # Test updating provider config
    router.update_provider_config("groq", {
        "model": "llama-3.3-70b-versatile",
        "api_key": "gsk_test_key_12345",
        "temperature": 0.5
    })
    assert router.settings.providers["groq"].model == "llama-3.3-70b-versatile"
    assert router.settings.providers["groq"].api_key == "gsk_test_key_12345"


# ---------------------------------------------------------------------------
# 5. Multi-Topic Configurable Daily Brief Engine Tests
# ---------------------------------------------------------------------------
def test_daily_brief_engine(tmp_path):
    cfg_file = tmp_path / "daily_brief_config.json"
    engine = DailyBriefEngine(config_path=cfg_file)

    # Initial default configuration
    cfg = engine.get_config()
    assert "Bangalore" in cfg["city"]
    topic_map = {t["id"]: t for t in cfg["topics"]}
    assert topic_map["weather"]["weight_pct"] == 15
    assert topic_map["tech_news"]["weight_pct"] == 30

    # Test updating configuration
    updated = engine.update_config({
        "city": "San Francisco",
        "voice_style": "concise",
        "topics": [
            {"id": "weather", "name": "Weather", "enabled": True, "weight_pct": 50, "genre_or_query": "San Francisco", "timeframe": "today", "max_items": 1},
            {"id": "tech_news", "name": "Tech", "enabled": True, "weight_pct": 50, "genre_or_query": "ai", "timeframe": "24h", "max_items": 2}
        ]
    })
    assert updated["city"] == "San Francisco"
    assert updated["voice_style"] == "concise"

    # Mock topic fetches for generate_briefing
    with patch.object(engine, "fetch_weather", return_value="San Francisco: Sunny, 22°C"):
        with patch.object(engine, "fetch_tech_news", return_value=["Breakthrough in Quantum Computing", "Next-Gen AI Systems"]):
            brief_data = engine.generate_briefing()
            assert "spoken_text" in brief_data
            assert "markdown_content" in brief_data
            assert "Sunny, 22°C" in brief_data["spoken_text"]
            assert "Breakthrough in Quantum Computing" in brief_data["markdown_content"]


# ---------------------------------------------------------------------------
# 6. Variant 3 API Endpoints Tests
# ---------------------------------------------------------------------------
def test_mark3_api_endpoints():
    client = TestClient(app)

    # 1. Gateway providers list
    resp = client.get("/api/gateway/providers")
    assert resp.status_code == 200
    providers = resp.json().get("providers", [])
    assert len(providers) >= 5

    # 2. Gateway provider toggle
    resp = client.post("/api/gateway/providers/toggle", json={"provider_id": "ollama", "enabled": True})
    assert resp.status_code == 200
    assert resp.json().get("status") == "ok"

    # 3. Gateway provider config update
    resp = client.post("/api/gateway/providers/config", json={
        "provider_id": "gemini",
        "config": {"model": "gemini-2.5-flash", "temperature": 0.4}
    })
    assert resp.status_code == 200
    assert resp.json().get("status") == "ok"

    # 4. Gateway test ping (mocked)
    with patch("bro.gateway.router.LLMGatewayRouter.test_provider", return_value={"status": "ok", "latency_ms": 42.0}):
        resp = client.post("/api/gateway/test", json={"provider_id": "ollama"})
        assert resp.status_code == 200
        assert resp.json().get("status") == "ok"

    # 5. Daily brief config GET and POST
    resp = client.get("/api/brief/config")
    assert resp.status_code == 200
    brief_cfg = resp.json()
    assert "city" in brief_cfg

    resp = client.post("/api/brief/config", json={"city": "Bangalore", "voice_style": "executive"})
    assert resp.status_code == 200
    assert resp.json().get("status") in ("ok", "updated")

    # 6. Daily brief preview
    resp = client.get("/api/brief/preview")
    assert resp.status_code == 200
    preview = resp.json()
    assert "spoken_text" in preview

    # 7. Model selection with tier0_device
    resp = client.get("/api/models")
    assert resp.status_code == 200
    current_models = resp.json()
    assert "tier0_device" in current_models.get("current", {})

    resp = client.post("/api/models/select", json={"tier0_device": "cpu"})
    assert resp.status_code == 200
    assert resp.json().get("status") in ("ok", "updated")
    assert resp.json().get("current", {}).get("tier0_device") == "cpu"
