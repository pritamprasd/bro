"""Unit tests for JARVIS Mark 2 features:
- Hybrid RAG Engine across memory & Obsidian Vault
- Instant Voice Barge-In (/api/voice/stop)
- Audio transcription endpoint (/api/voice/transcribe)
- Obsidian vault configuration & reindexing (/api/memory/obsidian, /api/memory/reindex)
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient

from jarvis.memory.rag import HybridRAGEngine, KnowledgeChunk
from jarvis.ui.server import app
from jarvis.voice.tts import TextToSpeech
from jarvis.config import VoiceConfig

@pytest.fixture
def client():
    return TestClient(app)

def test_hybrid_rag_engine_chunking_and_bm25():
    with tempfile.TemporaryDirectory() as tmp_mem, tempfile.TemporaryDirectory() as tmp_obs:
        mem_dir = Path(tmp_mem)
        obs_dir = Path(tmp_obs)

        # Create markdown in memory
        (mem_dir / "system.md").write_text(
            "# System Profile\nHardware is AMD Ryzen 7 with NVIDIA RTX 3060 12GB VRAM on Linux X11.\n\n"
            "## Storage Details\nNVMe root with secondary SSD mount at /data.",
            encoding="utf-8"
        )

        # Create markdown in obsidian vault
        (obs_dir / "projects").mkdir(parents=True)
        (obs_dir / "projects" / "cdac.md").write_text(
            "# CDAC Pune Mission\nWorked on clinical diagnostics and hospital cloud frameworks.\n\n"
            "## Deployment Architecture\nDeployed microservices using Docker Swarm and Kubernetes.",
            encoding="utf-8"
        )

        rag = HybridRAGEngine(
            memory_dir=str(mem_dir),
            obsidian_vault_dir=str(obs_dir),
            enabled=True,
        )

        assert len(rag.chunks) >= 4

        # Query hardware / RTX
        hw_results = rag.query("Tell me about my RTX 3060 and Ryzen CPU", top_k=2)
        assert len(hw_results) > 0
        top_chunk, score = hw_results[0]
        assert "RTX 3060" in top_chunk.content or "System Profile" in top_chunk.heading

        # Query Obsidian note
        obs_results = rag.query("What was the CDAC hospital cloud architecture?", top_k=2)
        assert len(obs_results) > 0
        top_obs, _ = obs_results[0]
        assert "CDAC" in top_obs.heading or "clinical diagnostics" in top_obs.content

        # Test context formatting
        formatted = rag.format_context("CDAC hospital framework")
        assert "<!-- KNOWLEDGE:" in formatted
        assert "CDAC" in formatted

def test_voice_stop_barge_in_endpoint(client):
    with patch("jarvis.ui.server.tts.stop") as mock_stop:
        resp = client.post("/api/voice/stop")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "stopped"
        mock_stop.assert_called_once()

def test_voice_transcribe_endpoint(client):
    with patch("jarvis.voice.stt.SpeechToText.transcribe_bytes", return_value="hello jarvis mark 2") as mock_stt:
        fake_audio = b"RIFF....WAVEfmt ...."
        resp = client.post("/api/voice/transcribe", files={"file": ("speech.wav", fake_audio, "audio/wav")})
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert data["text"] == "hello jarvis mark 2"
        mock_stt.assert_called_once()

def test_obsidian_vault_config_and_reindex(client):
    with tempfile.TemporaryDirectory() as tmp_obs:
        # Update obsidian vault dir
        resp = client.post("/api/memory/obsidian", json={"obsidian_vault_dir": tmp_obs})
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "updated"
        assert data["obsidian_vault_dir"] == tmp_obs

        # Test reindex
        reindex_resp = client.post("/api/memory/reindex")
        assert reindex_resp.status_code == 200
        reindex_data = reindex_resp.json()
        assert reindex_data["status"] == "reindexed"
        assert "total_chunks" in reindex_data

def test_tts_stop_terminates_player_process():
    tts = TextToSpeech(VoiceConfig())
    mock_proc = MagicMock()
    mock_proc.poll.return_value = None
    tts._current_player_process = mock_proc

    tts.stop()
    mock_proc.terminate.assert_called_once()
    assert tts._current_player_process is None
