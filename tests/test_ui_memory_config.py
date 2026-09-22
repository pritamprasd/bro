"""Tests for UI Memory directory configuration endpoints."""

import tempfile
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from jarvis.ui.server import app, config, memory_store

@pytest.fixture
def client():
    return TestClient(app)

def test_get_memory_config(client):
    response = client.get("/api/memory/config")
    assert response.status_code == 200
    data = response.json()
    assert "memory_dir" in data
    assert "resolved_path" in data
    assert "default_memory_dir" in data

def test_update_memory_config_valid(client):
    original_dir = config.memory.memory_dir
    with tempfile.TemporaryDirectory() as tmpdir:
        response = client.post("/api/memory/config", json={"memory_dir": tmpdir})
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "updated"
        assert data["memory_dir"] == tmpdir
        assert Path(data["resolved_path"]).exists()

        # Check GET reflects the update
        get_res = client.get("/api/memory/config")
        assert get_res.json()["memory_dir"] == tmpdir

    # Restore original dir
    client.post("/api/memory/config", json={"memory_dir": original_dir})

def test_update_memory_config_empty(client):
    response = client.post("/api/memory/config", json={"memory_dir": "   "})
    assert response.status_code == 400
    assert "cannot be empty" in response.json()["detail"]
