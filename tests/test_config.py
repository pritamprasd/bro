"""Unit tests for Jarvis configuration."""

from jarvis.config import JarvisConfig, load_config

def test_default_config():
    cfg = JarvisConfig()
    assert cfg.model.policy == "local_only"
    assert cfg.model.local_text_model == "gemma4:12b"
    assert cfg.model.local_vision_model == "qwen2.5vl:7b"
    assert cfg.output_mode == "both"
    assert cfg.autonomous_mode is False
    assert cfg.voice.enabled is True

def test_output_mode_options():
    cfg = JarvisConfig(output_mode="cli")
    assert cfg.output_mode == "cli"
    cfg2 = JarvisConfig(output_mode="voice")
    assert cfg2.output_mode == "voice"
