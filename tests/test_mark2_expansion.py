"""Comprehensive unit tests for Jarvis Mark 2 feature expansions."""

import json
import time
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient

from jarvis.config import JarvisConfig, MemoryConfig
from jarvis.core.agent import JarvisAgent
from jarvis.memory.calendar_engine import CalendarEngine
from jarvis.memory.store import MemoryStore
from jarvis.models.local_matcher import LocalIntentMatcher
from jarvis.ui.server import app


@pytest.fixture
def temp_memory_dir(tmp_path):
    mem_dir = tmp_path / "ai-memory"
    mem_dir.mkdir(parents=True, exist_ok=True)
    cfg = MemoryConfig(memory_dir=str(mem_dir))
    ms = MemoryStore(cfg)
    return mem_dir


def test_calendar_engine_crud(temp_memory_dir):
    cal_file = temp_memory_dir / "calendar.md"
    engine = CalendarEngine(cal_file)

    # Initial events from store seeding
    events = engine.get_events()
    assert isinstance(events, list)

    # Add new event
    new_ev = engine.add_event(
        title="Test Mark 2 Verification Meeting",
        event_date="2026-09-24",
        event_time="11:30",
        tags=["review", "test"],
    )
    assert new_ev["title"] == "Test Mark 2 Verification Meeting"
    assert new_ev["completed"] is False
    assert "review" in new_ev["tags"]

    # Check pending events
    pending = engine.get_pending_events()
    assert any(e["title"] == "Test Mark 2 Verification Meeting" for e in pending)

    # Toggle event completion
    toggled = engine.toggle_event("Test Mark 2 Verification Meeting", completed=True)
    assert toggled is True

    # Ensure it is now marked completed
    all_events = engine.get_events()
    matching = [e for e in all_events if "Test Mark 2 Verification Meeting" in e["title"]]
    assert len(matching) == 1
    assert matching[0]["completed"] is True


def test_calendar_today_summary(temp_memory_dir):
    cal_file = temp_memory_dir / "calendar.md"
    engine = CalendarEngine(cal_file)

    # Today summary with clean schedule
    summary_empty = engine.get_today_summary("2026-01-01")
    assert "clear" in summary_empty.lower()

    # Add item for specific date
    engine.add_event("Workstation Sync", "2026-05-10", "09:00", ["standup"])
    summary_day = engine.get_today_summary("2026-05-10")
    assert "Workstation Sync" in summary_day
    assert "09:00" in summary_day


def test_local_intent_matcher_performance(temp_memory_dir):
    engine = CalendarEngine(temp_memory_dir / "calendar.md")
    matcher = LocalIntentMatcher(temp_memory_dir, calendar_engine=engine)

    # 1. Greeting utterance (<5ms)
    t0 = time.perf_counter()
    res1 = matcher.match_and_execute("Hey Jarvis")
    dt1 = (time.perf_counter() - t0) * 1000
    assert dt1 < 10.0  # Must be sub-10ms (typically <0.1ms)
    assert res1 is not None
    assert res1["pattern"] == "Greeting"
    assert len(res1["response_text"]) > 0

    # 2. Time query dynamic slot substitution
    t0 = time.perf_counter()
    res2 = matcher.match_and_execute("What's the time right now?")
    dt2 = (time.perf_counter() - t0) * 1000
    assert dt2 < 10.0
    assert res2 is not None
    assert res2["action"] == "time_now"
    assert "M" in res2["response_text"] or ":" in res2["response_text"]  # e.g. "7:45 PM"

    # 3. Calendar schedule query
    res3 = matcher.match_and_execute("How's my calendar look like today?")
    assert res3 is not None
    assert res3["action"] == "calendar_today"
    assert "calendar" in res3["response_text"].lower() or "schedule" in res3["response_text"].lower()

    # 4. File inspection trigger
    res4 = matcher.match_and_execute("Show content of pyproject.toml")
    assert res4 is not None
    assert res4["action"] == "show_file_content"
    assert res4["action_data"] is not None
    assert res4["action_data"]["file_name"] == "pyproject.toml"
    assert "dependencies" in res4["action_data"]["content"] or "project" in res4["action_data"]["content"]


def test_agent_local_fast_path(temp_memory_dir):
    config = JarvisConfig(output_mode="cli")
    config.memory.memory_dir = str(temp_memory_dir)
    agent = JarvisAgent(config)

    # Router and Tier0 should NOT be called for offline instant triggers
    agent.router.generate_text = MagicMock()
    agent.tier0.classify = MagicMock()

    result = agent.run_task("Hey Jarvis")
    assert result != ""
    agent.router.generate_text.assert_not_called()
    agent.tier0.classify.assert_not_called()


def test_ui_calendar_and_greeting_api():
    client = TestClient(app)

    # 1. Voice Greeting endpoint
    res_greet = client.get("/api/voice/greeting")
    assert res_greet.status_code == 200
    data_greet = res_greet.json()
    assert "greeting" in data_greet
    assert len(data_greet["greeting"]) > 0

    # 2. Calendar list endpoint
    res_cal = client.get("/api/calendar")
    assert res_cal.status_code == 200
    data_cal = res_cal.json()
    assert "events" in data_cal
    assert "pending" in data_cal

    # 3. Add calendar event endpoint
    res_add = client.post("/api/calendar", json={
        "title": "Automated Unit Test Event",
        "date": "2026-10-01",
        "time": "15:00",
        "tags": ["unit-test"],
    })
    assert res_add.status_code == 200
    add_data = res_add.json()
    assert add_data["status"] == "success"
    assert add_data["event"]["title"] == "Automated Unit Test Event"

    # 4. Toggle calendar event
    res_toggle = client.post("/api/calendar/toggle", json={
        "identifier": "Automated Unit Test Event",
        "completed": True,
    })
    assert res_toggle.status_code == 200
    assert res_toggle.json()["status"] == "success"

    # 5. Calendar Today summary endpoint
    res_today = client.get("/api/calendar/today")
    assert res_today.status_code == 200
    assert "summary" in res_today.json()
