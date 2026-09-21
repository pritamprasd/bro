"""Configuration loader and schema for Jarvis."""

import os
from pathlib import Path
from typing import List, Literal, Optional
import yaml
from pydantic import BaseModel, Field

DEFAULT_CONFIG_DIR = Path.home() / ".jarvis"
DEFAULT_CONFIG_PATH = DEFAULT_CONFIG_DIR / "config.yaml"
LOCAL_CONFIG_PATH = Path("config.yaml")

class ModelConfig(BaseModel):
    policy: Literal["local_only", "tier_fallback", "cloud_only"] = "local_only"
    local_text_model: str = "gemma4:12b"
    local_vision_model: str = "qwen2.5vl:7b"
    cloud_model: str = "gemini-2.5-flash"
    ollama_url: str = "http://localhost:11434"
    gemini_api_key: Optional[str] = None

class VoiceConfig(BaseModel):
    enabled: bool = True
    whisper_model: str = "base"
    device: str = "cuda"  # or "cpu"
    compute_type: str = "float16"  # or "int8"
    tts_voice: str = "en-US-GuyNeural"
    tts_rate: str = "+0%"

class SafetyConfig(BaseModel):
    prompt_on_high_stakes: bool = True
    high_stakes_keywords: List[str] = Field(
        default_factory=lambda: [
            "rm -rf", "delete", "destroy", "wipe", "format",
            "sudo", "passwd", "shutdown", "reboot",
            "send email", "payment", "buy", "purchase", "checkout", "order",
            "transfer", "bank", "credit card", "telegram send", "post to"
        ]
    )

class BrowserConfig(BaseModel):
    headless: bool = False
    viewport_width: int = 1280
    viewport_height: int = 800
    user_data_dir: str = str(DEFAULT_CONFIG_DIR / "browser_data")

class MemoryConfig(BaseModel):
    memory_dir: str = str(DEFAULT_CONFIG_DIR / "memory")

class JarvisConfig(BaseModel):
    output_mode: Literal["both", "cli", "voice"] = "both"
    autonomous_mode: bool = False
    model: ModelConfig = Field(default_factory=ModelConfig)
    voice: VoiceConfig = Field(default_factory=VoiceConfig)
    safety: SafetyConfig = Field(default_factory=SafetyConfig)
    browser: BrowserConfig = Field(default_factory=BrowserConfig)
    memory: MemoryConfig = Field(default_factory=MemoryConfig)

def load_config(config_path: Optional[Path] = None) -> JarvisConfig:
    """Load configuration from local or default global path, falling back to defaults."""
    candidates = []
    if config_path:
        candidates.append(config_path)
    candidates.extend([LOCAL_CONFIG_PATH, DEFAULT_CONFIG_PATH])

    for path in candidates:
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f) or {}
                return JarvisConfig(**data)
            except Exception as e:
                print(f"[Warning] Failed to load config from {path}: {e}. Using defaults.")

    return JarvisConfig()

def save_config(config: JarvisConfig, target_path: Optional[Path] = None) -> Path:
    """Save configuration to disk."""
    path = target_path or LOCAL_CONFIG_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(config.model_dump(), f, default_flow_style=False, sort_keys=False)
    return path
