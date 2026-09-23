"""Meta AI provider implementation for Enterprise LLM Gateway."""

from typing import Optional
from jarvis.gateway.models import GatewayRequest, GatewayResponse
from jarvis.gateway.providers.openai import OpenAIProvider

class MetaAIProvider(OpenAIProvider):
    def generate(self, request: GatewayRequest, resolved_api_key: Optional[str] = None) -> GatewayResponse:
        if not self.config.base_url:
            self.config.base_url = "https://api.together.xyz/v1"
        return super().generate(request, resolved_api_key=resolved_api_key)
