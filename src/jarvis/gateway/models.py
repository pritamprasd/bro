"""Data models for Enterprise LLM Gateway requests, responses, and metrics."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class GatewayMessage(BaseModel):
    role: str  # "system", "user", "assistant"
    content: str

class GatewayRequest(BaseModel):
    messages: List[GatewayMessage] = Field(default_factory=list)
    prompt: Optional[str] = None
    model: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 2048
    stream: bool = False
    preferred_provider: Optional[str] = None

    def model_post_init(self, __context: Any) -> None:
        if self.prompt and not self.messages:
            self.messages.append(GatewayMessage(role="user", content=self.prompt))

class GatewayResponse(BaseModel):
    content: str
    model: str
    provider: str
    latency_ms: float = 0.0
    input_tokens: int = 0
    output_tokens: int = 0
    success: bool = True
    error: Optional[str] = None
    fallback_used: bool = False

class ProviderTelemetry(BaseModel):
    id: str
    display_name: str
    enabled: bool
    healthy: bool = True
    last_ping_ms: float = 0.0
    total_requests: int = 0
    total_errors: int = 0
    success_rate: float = 100.0
    consecutive_failures: int = 0
    circuit_open: bool = False
    cooldown_until: float = 0.0
