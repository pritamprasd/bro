"""Tests for UI Model selection, policy switching, and Cloud Gemini integration."""

import pytest
from fastapi.testclient import TestClient
from bro.ui.server import app

@pytest.fixture
def client():
    return TestClient(app)

def test_get_models(client):
    response = client.get("/api/models")
    assert response.status_code == 200
    data = response.json()
    assert "models" in data
    assert "cloud_models" in data
    assert "current" in data
    
    # Verify cloud models list includes Gemini 3.8 / 2.5 Flash
    cloud_ids = [m["id"] for m in data["cloud_models"]]
    assert "gemini-2.5-flash" in cloud_ids
    assert "gemini-2.0-flash" in cloud_ids
    
    # Verify current model settings
    curr = data["current"]
    assert "policy" in curr
    assert "cloud_model" in curr
    assert "has_gemini_api_key" in curr

def test_switch_model_policy_quick(client):
    # Test switching to cloud_only
    res = client.post("/api/models/policy", json={"policy": "cloud_only", "cloud_model": "gemini-2.5-flash"})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "updated"
    assert data["policy"] == "cloud_only"
    assert data["cloud_model"] == "gemini-2.5-flash"

    # Status reflects change
    status_res = client.get("/api/status")
    assert status_res.status_code == 200
    assert status_res.json()["policy"] == "cloud_only"
    assert status_res.json()["cloud_model"] == "gemini-2.5-flash"

    # Test switching to tier_fallback (Hybrid)
    res_hybrid = client.post("/api/models/policy", json={"policy": "tier_fallback"})
    assert res_hybrid.status_code == 200
    assert res_hybrid.json()["policy"] == "tier_fallback"

    # Test switching back to local_only
    res_local = client.post("/api/models/policy", json={"policy": "local_only"})
    assert res_local.status_code == 200
    assert res_local.json()["policy"] == "local_only"

    # Status reflects local_only
    status_res = client.get("/api/status")
    assert status_res.status_code == 200
    assert status_res.json()["policy"] == "local_only"

def test_select_models_full(client):
    payload = {
        "policy": "cloud_only",
        "cloud_model": "gemini-2.5-flash",
        "local_text_model": "gemma4:12b",
        "local_vision_model": "qwen2.5-vl:7b",
        "tier0_model": "llama3.2:3b",
    }
    res = client.post("/api/models/select", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "updated"
    assert data["current"]["policy"] == "cloud_only"
    assert data["current"]["cloud_model"] == "gemini-2.5-flash"
    assert data["current"]["local_text_model"] == "gemma4:12b"

    # Revert back to local_only
    client.post("/api/models/policy", json={"policy": "local_only"})
