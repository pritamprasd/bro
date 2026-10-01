"""Groq / Grok ultra-fast inference provider for Enterprise LLM Gateway."""

from typing import Optional
from bro.gateway.models import GatewayRequest, GatewayResponse
from bro.gateway.providers.openai import OpenAIProvider

class GroqProvider(OpenAIProvider):
    def generate(self, request: GatewayRequest, resolved_api_key: Optional[str] = None) -> GatewayResponse:
        if not self.config.base_url:
            self.config.base_url = "https://api.groq.com/openai/v1"
        return super().generate(request, resolved_api_key=resolved_api_key)
