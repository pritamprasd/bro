"""Tests for UI Voice selection, listing, and preview endpoints."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from bro.ui.server import app

@pytest.fixture
def client():
    return TestClient(app)

def test_get_voices(client):
    response = client.get("/api/voice/voices")
    assert response.status_code == 200
    data = response.json()
    assert "voices" in data
    assert len(data["voices"]) > 0
    assert "current_voice" in data
    
    # Check that recommended voices are included
    voice_ids = [v["short_name"] for v in data["voices"]]
    assert "en-GB-RyanNeural" in voice_ids or any("Ryan" in v for v in voice_ids)

def test_select_voice(client):
    target_voice = "en-US-GuyNeural"
    response = client.post("/api/voice/select", json={"voice": target_voice})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "updated"
    assert data["current_voice"] == target_voice

    # Check status endpoint reflects the updated voice
    status_res = client.get("/api/status")
    assert status_res.status_code == 200
    assert status_res.json()["tts_voice"] == target_voice

    # Revert back to en-GB-RyanNeural
    revert_res = client.post("/api/voice/select", json={"voice": "en-GB-RyanNeural"})
    assert revert_res.status_code == 200
    assert revert_res.json()["current_voice"] == "en-GB-RyanNeural"

def test_preview_voice(client):
    with patch("bro.voice.tts.TextToSpeech.speak") as mock_speak:
        response = client.post("/api/voice/preview", json={
            "voice": "en-GB-RyanNeural",
            "rate": "+25%",
            "text": "Testing speech synthesis"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "playing"
        assert data["voice"] == "en-GB-RyanNeural"
        assert data["rate"] == "+25%"
        mock_speak.assert_called_once_with("Testing speech synthesis", blocking=False)

def test_select_voice_speed(client):
    response = client.post("/api/voice/select", json={"rate": "+30%"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "updated"
    assert data["current_rate"] == "+30%"

    # Check status endpoint reflects updated rate
    status_res = client.get("/api/status")
    assert status_res.status_code == 200
    assert status_res.json()["tts_rate"] == "+30%"

    # Revert back to +2%
    revert_res = client.post("/api/voice/select", json={"rate": "+2%"})
    assert revert_res.status_code == 200
    assert revert_res.json()["current_rate"] == "+2%"
