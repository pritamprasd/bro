"""Configuration loader and schema for Jarvis Phase 2."""

import os
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Union
import yaml
from pydantic import BaseModel, Field

DEFAULT_CONFIG_DIR = Path.home() / ".jarvis"
DEFAULT_MEMORY_DIR = Path.home() / "ai-memory" / "jarvis"
DEFAULT_CONFIG_PATH = DEFAULT_CONFIG_DIR / "config.yaml"
LOCAL_CONFIG_PATH = Path("config.yaml")

class ModelConfig(BaseModel):
    policy: Literal["local_only", "tier_fallback", "cloud_only"] = "local_only"
    tier0_enabled: bool = True
    tier0_model: str = "llama3.2:3b"
    tier0_timeout: float = 5.0
    tier0_device: Literal["gpu", "cpu"] = "cpu"
    local_text_model: str = "gemma4:12b"
    local_vision_model: str = "qwen2.5vl:7b"
    cloud_model: str = "gemini-2.5-flash"
    ollama_url: str = "http://localhost:11434"
    keep_alive: Union[int, str] = -1  # -1 keeps models in RAM/VRAM permanently (int -1 or duration "24h")
    gemini_api_key: Optional[str] = None

class VoiceConfig(BaseModel):
    enabled: bool = True
    whisper_model: str = "base"
    device: str = "cuda"
    compute_type: str = "float16"
    tts_voice: str = "en-GB-RyanNeural"  # Iron Man JARVIS British voice
    tts_rate: str = "+2%"
    tts_pitch: str = "-4Hz"
    tts_volume: int = 100  # 0 to 100%
    always_voice_response: bool = False
    voice_reply_on_chat: bool = True
    stt_engine: Literal["browser", "whisper_local"] = "browser"
    sfx_enabled: bool = True

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
    cdp_port: int = 9222

class MemoryConfig(BaseModel):
    memory_dir: str = str(DEFAULT_MEMORY_DIR)
    obsidian_vault_dir: Optional[str] = "~/obsidian/KnowledgeBase/ai-memory"
    semantic_search_enabled: bool = True
    embedding_model: str = "nomic-embed-text"

class SentinelConfig(BaseModel):
    enabled: bool = True
    check_interval_seconds: int = 30
    gpu_temp_threshold: int = 80
    disk_threshold_percent: int = 90

class OrganizerConfig(BaseModel):
    enabled: bool = False
    watch_dir: str = "~/Downloads"
    rules: Dict[str, str] = Field(
        default_factory=lambda: {
            "pdf": "~/Documents/PDFs",
            "csv,xlsx,json": "~/Documents/Data",
            "tar.gz,zip,rar,7z": "~/Downloads/Archives",
            "mp4,mkv,avi": "~/Media/Videos",
            "png,jpg,jpeg,webp": "~/Media/Images",
        }
    )

class CronConfig(BaseModel):
    enabled: bool = False
    briefing_time: str = "08:30"

class WatchdogsConfig(BaseModel):
    sentinel: SentinelConfig = Field(default_factory=SentinelConfig)
    organizer: OrganizerConfig = Field(default_factory=OrganizerConfig)
    cron: CronConfig = Field(default_factory=CronConfig)

class WebUIConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8765

class SpotlightConfig(BaseModel):
    enabled: bool = True
    hotkey: str = "<alt>+j"

class DesktopConfig(BaseModel):
    screen_index: int = 1  # 0: All combined virtual canvas, 1: Display 1 (default primary), 2: Display 2, etc.

class JarvisConfig(BaseModel):
    conversation_mode: Literal["audio_only", "audio+chat", "chat_only"] = "audio+chat"
    output_mode: Literal["both", "cli", "voice"] = "both"
    autonomous_mode: bool = False
    model: ModelConfig = Field(default_factory=ModelConfig)
    voice: VoiceConfig = Field(default_factory=VoiceConfig)
    safety: SafetyConfig = Field(default_factory=SafetyConfig)
    browser: BrowserConfig = Field(default_factory=BrowserConfig)
    memory: MemoryConfig = Field(default_factory=MemoryConfig)
    watchdogs: WatchdogsConfig = Field(default_factory=WatchdogsConfig)
    web_ui: WebUIConfig = Field(default_factory=WebUIConfig)
    spotlight: SpotlightConfig = Field(default_factory=SpotlightConfig)
    desktop: DesktopConfig = Field(default_factory=DesktopConfig)

def load_config(config_path: Optional[Path] = None) -> JarvisConfig:
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
    path = target_path or LOCAL_CONFIG_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(config.model_dump(), f, default_flow_style=False, sort_keys=False)
    return path
