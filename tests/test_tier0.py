"""Unit tests for Tier-0 Instant Router."""

from unittest.mock import MagicMock, patch
import pytest
from jarvis.config import ModelConfig
from jarvis.models.tier0 import Tier0Router

def test_tier0_disabled_fallback():
    cfg = ModelConfig(tier0_enabled=False)
    router = Tier0Router(cfg)
    res = router.classify("What is the capital of France?")
    assert res.intent == "COMPLEX_PLAN"
    assert "Tier-0 disabled" in res.summary

def test_tier0_mock_classification():
    cfg = ModelConfig(tier0_enabled=True)
    router = Tier0Router(cfg)

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "message": {"content": '{"intent": "CONVERSATION", "summary": "General question"}'}
    }

    with patch("requests.post", return_value=mock_resp):
        res = router.classify("Tell me a joke")
        assert res.intent == "CONVERSATION"
        assert res.summary == "General question"
