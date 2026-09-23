"""Abstract base class for all Enterprise LLM Gateway providers."""

import abc
import time
from typing import Any, Dict, Optional
from jarvis.gateway.config import GatewayProviderConfig
from jarvis.gateway.models import GatewayRequest, GatewayResponse

class BaseLLMProvider(abc.ABC):
    def __init__(self, config: GatewayProviderConfig):
        self.config = config
        self.id = config.id
        self.display_name = config.display_name

    @property
    def enabled(self) -> bool:
        return self.config.enabled

    @abc.abstractmethod
    def generate(self, request: GatewayRequest, resolved_api_key: Optional[str] = None) -> GatewayResponse:
        """Execute a text generation call through the provider."""
        raise NotImplementedError

    def ping(self, resolved_api_key: Optional[str] = None) -> Dict[str, Any]:
        """Test provider availability and measure roundtrip ping latency."""
        t0 = time.time()
        req = GatewayRequest(
            messages=[{"role": "user", "content": "ping"}],
            max_tokens=5,
            temperature=0.0
        )
        try:
            resp = self.generate(req, resolved_api_key=resolved_api_key)
            elapsed_ms = round((time.time() - t0) * 1000, 1)
            return {
                "success": resp.success,
                "latency_ms": elapsed_ms,
                "error": resp.error,
                "model": resp.model,
            }
        except Exception as e:
            elapsed_ms = round((time.time() - t0) * 1000, 1)
            return {
                "success": False,
                "latency_ms": elapsed_ms,
                "error": str(e),
                "model": self.config.model,
            }
