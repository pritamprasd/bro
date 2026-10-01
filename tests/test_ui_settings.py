"""Unit tests for UI settings, volume control, watchdog toggles, and audit clear/backup."""

import tempfile
from pathlib import Path
from fastapi.testclient import TestClient
from bro.core.audit import AuditManager
from bro.ui.server import app, audit, config


def test_audit_backup_and_clear():
    with tempfile.TemporaryDirectory() as tmp_runs, tempfile.TemporaryDirectory() as tmp_backup:
        am = AuditManager(base_dir=Path(tmp_runs))
        run = am.start_run("Autonomous Test Run 1")
        am.record_step(1, "Thought 1", "click", {"x": 10, "y": 20}, "Success", True)
        am.complete_run("Result", "success")

        assert len(am.list_recent_runs()) == 1
        analytics = am.get_analytics()
        assert analytics["total_runs"] == 1

        # Perform backup and clear
        res = am.backup_and_clear(backup_dir=Path(tmp_backup))
        assert res["cleared_runs"] == 1
        assert Path(res["backup_dir"]).exists()
        assert (Path(res["backup_dir"]) / run.run_id).exists()

        # Check that runs are cleared and metrics reset
        assert len(am.list_recent_runs()) == 0
        cleared_analytics = am.get_analytics()
        assert cleared_analytics["total_runs"] == 0
        assert cleared_analytics["success_count"] == 0


def test_api_history_clear_endpoint():
    client = TestClient(app)
    # Start and complete a test run
    audit.start_run("Test Mission for Clearing")
    audit.complete_run("Finished", status="success")

    res = client.post("/api/history/clear")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "cleared"
    assert "backup_dir" in data
    assert "cleared_runs" in data

    # Verify runs are now empty
    history_res = client.get("/api/history")
    assert history_res.status_code == 200
    assert len(history_res.json()) == 0


def test_api_watchdogs_toggle():
    client = TestClient(app)

    # Toggle sentinel
    initial_sentinel = config.watchdogs.sentinel.enabled
    res = client.post("/api/watchdogs/toggle", json={"target": "sentinel"})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["target"] == "sentinel"
    assert data["state"] == (not initial_sentinel)

    # Toggle back
    res2 = client.post("/api/watchdogs/toggle", json={"target": "sentinel"})
    assert res2.status_code == 200
    assert res2.json()["state"] == initial_sentinel

    # Toggle organizer
    initial_org = config.watchdogs.organizer.enabled
    res_org = client.post("/api/watchdogs/toggle", json={"target": "organizer"})
    assert res_org.status_code == 200
    assert res_org.json()["state"] == (not initial_org)
    client.post("/api/watchdogs/toggle", json={"target": "organizer"})

    # Toggle invalid target
    bad_res = client.post("/api/watchdogs/toggle", json={"target": "non_existent_sentinel"})
    assert bad_res.status_code == 400


def test_api_settings_autonomous():
    client = TestClient(app)

    # Enable autonomous mode
    res1 = client.post("/api/settings/autonomous", json={"autonomous_mode": True})
    assert res1.status_code == 200
    assert res1.json()["autonomous_mode"] is True
    assert "ON" in res1.json()["label"]
    assert config.autonomous_mode is True

    # Disable autonomous mode
    res2 = client.post("/api/settings/autonomous", json={"autonomous_mode": False})
    assert res2.status_code == 200
    assert res2.json()["autonomous_mode"] is False
    assert "OFF" in res2.json()["label"]
    assert config.autonomous_mode is False


def test_api_voice_volume():
    client = TestClient(app)

    # Set volume
    res = client.post("/api/voice/select", json={"volume": 75})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "updated"
    assert config.voice.tts_volume == 75

    # Check status endpoint exposes volume
    status_res = client.get("/api/status")
    assert status_res.status_code == 200
    assert status_res.json()["tts_volume"] == 75
