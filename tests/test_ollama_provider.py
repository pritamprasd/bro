"""Unit tests for OllamaProvider and keep_alive normalization."""

from unittest.mock import MagicMock, patch
import pytest
import requests
from jarvis.models.base import ChatMessage
from jarvis.models.ollama_provider import OllamaProvider, normalize_keep_alive

def test_normalize_keep_alive():
    """Ensure keep_alive values are properly normalized for Ollama's Go API."""
    assert normalize_keep_alive(-1) == -1
    assert normalize_keep_alive("-1") == -1
    assert normalize_keep_alive(" -1 ") == -1
    assert normalize_keep_alive("'-1'") == -1
    assert normalize_keep_alive('"-1"') == -1
    assert normalize_keep_alive(-1.0) == -1
    assert normalize_keep_alive("24h") == "24h"
    assert normalize_keep_alive("-1m") == "-1m"
    assert normalize_keep_alive("5m") == "5m"
    assert normalize_keep_alive(None) == -1

def test_ollama_provider_init_normalization():
    """Ensure OllamaProvider normalizes string '-1' to integer -1."""
    provider = OllamaProvider(keep_alive="-1")
    assert provider.keep_alive == -1

    provider2 = OllamaProvider(keep_alive="24h")
    assert provider2.keep_alive == "24h"

def test_ollama_generate_text_success():
    """Verify OllamaProvider generate_text sends keep_alive and parses response."""
    provider = OllamaProvider(text_model="gemma4:12b", keep_alive="-1")

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "message": {"content": "Hello user"},
        "done_reason": "stop",
    }

    with patch("requests.post", return_value=mock_resp) as mock_post:
        messages = [ChatMessage(role="user", content="Hi")]
        resp = provider.generate_text(messages)
        assert resp.content == "Hello user"
        assert resp.finish_reason == "stop"

        # Check payload passed to requests.post
        call_kwargs = mock_post.call_args[1]
        payload = call_kwargs["json"]
        assert payload["keep_alive"] == -1
        assert payload["model"] == "gemma4:12b"
        assert payload["stream"] is False

def test_ollama_generate_text_error_detail():
    """Ensure OllamaProvider surfaces Ollama's exact JSON error on HTTP 400."""
    provider = OllamaProvider(text_model="gemma4:12b")

    mock_resp = MagicMock()
    mock_resp.status_code = 400
    mock_resp.text = '{"error": "time: missing unit in duration \\"-1\\""}'
    mock_resp.json.return_value = {"error": 'time: missing unit in duration "-1"'}

    with patch("requests.post", return_value=mock_resp):
        messages = [ChatMessage(role="user", content="Hi")]
        with pytest.raises(RuntimeError) as exc_info:
            provider.generate_text(messages)
        
        # Verify the specific error message is surfaced
        assert "time: missing unit in duration" in str(exc_info.value)
        assert "400" in str(exc_info.value)

def test_ollama_tool_rejection_retry():
    """Ensure OllamaProvider retries without tools if tools cause HTTP 400."""
    provider = OllamaProvider(text_model="gemma4:12b")

    mock_fail_resp = MagicMock()
    mock_fail_resp.status_code = 400
    mock_fail_resp.text = '{"error": "invalid tool schema"}'
    mock_fail_resp.json.return_value = {"error": "invalid tool schema"}

    mock_success_resp = MagicMock()
    mock_success_resp.status_code = 200
    mock_success_resp.json.return_value = {
        "message": {"content": "Fallback text without tools"},
        "done_reason": "stop",
    }

    with patch("requests.post", side_effect=[mock_fail_resp, mock_success_resp]) as mock_post:
        messages = [ChatMessage(role="user", content="Hi")]
        resp = provider.generate_text(messages, tools=[{"name": "test_tool"}])
        assert resp.content == "Fallback text without tools"
        assert mock_post.call_count == 2
        # First call had tools
        assert "tools" in mock_post.call_args_list[0][1]["json"]
        # Second call stripped tools
        assert "tools" not in mock_post.call_args_list[1][1]["json"]
