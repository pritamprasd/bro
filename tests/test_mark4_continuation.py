"""Unit tests for Bro Variant 4 continuation features:
1. Gen-Z greetings toggle, GreetingMatcher & Memory store
2. Technical design document endpoint (/api/docs/design)
3. Calendar clear all events & endpoint
4. Voice settings persistence
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock
import pytest
from fastapi.testclient import TestClient

from bro.config import BroConfig, VoiceConfig
from bro.models.local_matcher import GreetingMatcher, _GEN_Z_GREETING_REPLIES, _GEN_Z_THANKS_REPLIES, _GEN_Z_BYE_REPLIES, _GEN_Z_ACK_REPLIES
from bro.memory.calendar_engine import CalendarEngine
from bro.memory.store import MemoryStore
from bro.ui.server import app


def test_greeting_matcher_standard_and_gen_z():
    # Standard greeting
    std_reply = GreetingMatcher.match("Hello", gen_z=False)
    assert std_reply is not None
    assert std_reply not in _GEN_Z_GREETING_REPLIES

    # Gen-Z greeting
    genz_reply = GreetingMatcher.match("Hello", gen_z=True)
    assert genz_reply is not None
    assert genz_reply in _GEN_Z_GREETING_REPLIES

    # Thanks standard vs Gen-Z
    std_thanks = GreetingMatcher.match("thank you", gen_z=False)
    assert std_thanks is not None
    genz_thanks = GreetingMatcher.match("thank you", gen_z=True)
    assert genz_thanks in _GEN_Z_THANKS_REPLIES

    # Goodbye standard vs Gen-Z
    std_bye = GreetingMatcher.match("bye bro", gen_z=False)
    assert std_bye is not None
    genz_bye = GreetingMatcher.match("bye bro", gen_z=True)
    assert genz_bye in _GEN_Z_BYE_REPLIES

    # Acknowledgment standard vs Gen-Z
    std_ack = GreetingMatcher.match("ok", gen_z=False)
    assert std_ack is not None
    genz_ack = GreetingMatcher.match("ok", gen_z=True)
    assert genz_ack in _GEN_Z_ACK_REPLIES


def test_memory_store_gen_z_greetings(tmp_path):
    from bro.config import MemoryConfig
    mem_dir = tmp_path / "sub_mem"
    cfg = MemoryConfig(memory_dir=str(mem_dir), semantic_search_enabled=False)
    store = MemoryStore(cfg)

    # Standard greeting
    std_g = store.get_random_greeting(gen_z_mode=False)
    assert std_g is not None

    # Gen-Z greeting
    genz_g = store.get_random_greeting(gen_z_mode=True)
    assert genz_g is not None
    assert any(w in genz_g.lower() for w in ["cap", "vibe", "slay", "bussin", "fr fr", "sheesh", "bet", "energy", "aura", "lowkey", "radar"])


def test_calendar_clear_all_events(tmp_path):
    cal_file = tmp_path / "calendar.md"
    engine = CalendarEngine(cal_file)
    engine.add_event(title="Sprint planning", event_date="2026-09-24", event_time="10:00")
    engine.add_event(title="Security audit", event_date="2026-09-25", event_time="14:00")
    assert len(engine.get_events()) == 2

    cleared = engine.clear_all_events()
    assert cleared == 2
    assert len(engine.get_events()) == 0
    assert len(engine.get_pending_events()) == 0


def test_api_design_document_endpoint():
    client = TestClient(app)
    res = client.get("/api/docs/design")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert "BRO Variant 4" in data["content"]
    assert "GreetingMatcher" in data["content"]
    assert "design.md" in data["filename"]


def test_api_calendar_clear_endpoint():
    client = TestClient(app)
    # Add an event
    add_res = client.post("/api/calendar", json={"title": "Test Clear Event", "date": "2026-09-24"})
    assert add_res.status_code == 200

    # Delete all events
    del_res = client.delete("/api/calendar")
    assert del_res.status_code == 200
    del_data = del_res.json()
    assert del_data["status"] == "cleared"

    # Verify empty
    get_res = client.get("/api/calendar")
    assert get_res.status_code == 200
    assert len(get_res.json()["events"]) == 0


def test_api_voice_gen_z_setting_and_greeting():
    client = TestClient(app)
    # Toggle Gen-Z greetings on
    sel_res = client.post("/api/voice/select", json={"gen_z_greetings": True})
    assert sel_res.status_code == 200
    assert sel_res.json()["gen_z_greetings"] is True

    # Check status endpoint
    stat_res = client.get("/api/status")
    assert stat_res.status_code == 200
    assert stat_res.json()["gen_z_greetings"] is True

    # Check voice greeting returns Gen-Z
    g_res = client.get("/api/voice/greeting")
    assert g_res.status_code == 200
    assert "greeting" in g_res.json()

    # Toggle Gen-Z greetings off
    sel_res2 = client.post("/api/voice/select", json={"gen_z_greetings": False})
    assert sel_res2.status_code == 200
    assert sel_res2.json()["gen_z_greetings"] is False
