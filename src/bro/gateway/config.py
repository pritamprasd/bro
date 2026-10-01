"""Configuration schema for Enterprise LLM Gateway."""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field

class GatewayProviderConfig(BaseModel):
    id: str
    display_name: str
    enabled: bool = False
    model: str
    available_models: List[str] = Field(default_factory=list)
    api_key: Optional[str] = None
    vault_key: Optional[str] = None
    base_url: Optional[str] = None
    priority: int = 10  # Lower number = higher priority
    timeout: float = 15.0
    is_local: bool = False

class GatewaySettings(BaseModel):
    enabled: bool = True
    active_provider: str = "ollama"
    fallback_enabled: bool = True
    circuit_breaker_threshold: int = 3
    circuit_breaker_cooldown_sec: float = 60.0
    providers: Dict[str, GatewayProviderConfig] = Field(default_factory=dict)

def get_default_gateway_settings() -> GatewaySettings:
    return GatewaySettings(
        enabled=True,
        active_provider="ollama",
        fallback_enabled=True,
        circuit_breaker_threshold=3,
        circuit_breaker_cooldown_sec=60.0,
        providers={
            "gemini": GatewayProviderConfig(
                id="gemini",
                display_name="Google Gemini (AI Studio Pro / Flash)",
                enabled=True,
                model="gemini-2.5-flash",
                available_models=["gemini-3.6-flash","gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-pro", "gemini-2.5-pro"],
                vault_key="gemini_api_key",
                priority=1,
                timeout=15.0,
            ),
            "openai": GatewayProviderConfig(
                id="openai",
                display_name="OpenAI (ChatGPT / GPT-4o)",
                enabled=False,
                model="gpt-4o-mini",
                available_models=["gpt-4o", "gpt-4o-mini", "o1-mini", "gpt-4-turbo"],
                vault_key="openai_api_key",
                priority=2,
                timeout=20.0,
            ),
            "groq": GatewayProviderConfig(
                id="groq",
                display_name="Groq / Grok (Ultra-Fast Inference)",
                enabled=False,
                model="llama-3.3-70b-versatile",
                available_models=["llama-3.3-70b-versatile", "grok-2", "mixtral-8x7b-32768"],
                vault_key="groq_api_key",
                priority=3,
                timeout=10.0,
            ),
            "meta": GatewayProviderConfig(
                id="meta",
                display_name="Meta AI (Llama 3.3 via Cloud)",
                enabled=False,
                model="meta-llama/Llama-3.3-70B-Instruct",
                available_models=["meta-llama/Llama-3.3-70B-Instruct", "meta-llama/Llama-3.2-3B-Instruct"],
                vault_key="meta_api_key",
                priority=4,
                timeout=15.0,
            ),
            "ollama": GatewayProviderConfig(
                id="ollama",
                display_name="Local Workstation (Ollama)",
                enabled=True,
                model="gemma4:12b",
                available_models=["gemma4:12b", "qwen2.5vl:7b", "llama3.2:3b"],
                base_url="http://localhost:11434",
                priority=5,
                timeout=30.0,
                is_local=True,
            ),
        }
    )
