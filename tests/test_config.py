"""Unit tests for Bro configuration."""

from bro.config import BroConfig, load_config

def test_default_config():
    cfg = BroConfig()
    assert cfg.model.policy == "local_only"
    assert cfg.model.local_text_model == "gemma4:12b"
    assert cfg.model.local_vision_model == "qwen2.5vl:7b"
    assert cfg.output_mode == "both"
    assert cfg.autonomous_mode is False
    assert cfg.voice.enabled is True

def test_output_mode_options():
    cfg = BroConfig(output_mode="cli")
    assert cfg.output_mode == "cli"
    cfg2 = BroConfig(output_mode="voice")
    assert cfg2.output_mode == "voice"

def test_conversation_mode_options():
    cfg = BroConfig()
    assert cfg.conversation_mode == "audio+chat"
    cfg_audio = BroConfig(conversation_mode="audio_only")
    assert cfg_audio.conversation_mode == "audio_only"
    cfg_chat = BroConfig(conversation_mode="chat_only")
    assert cfg_chat.conversation_mode == "chat_only"

def test_desktop_config():
    cfg = BroConfig()
    assert hasattr(cfg, "desktop")
    assert cfg.desktop.screen_index == 1
    cfg2 = BroConfig(desktop={"screen_index": 2})
    assert cfg2.desktop.screen_index == 2
