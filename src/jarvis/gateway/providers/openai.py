"""OpenAI provider implementation for Enterprise LLM Gateway."""

import time
from typing import Optional
import requests
from jarvis.gateway.models import GatewayRequest, GatewayResponse
from jarvis.gateway.providers.base import BaseLLMProvider

class OpenAIProvider(BaseLLMProvider):
    def generate(self, request: GatewayRequest, resolved_api_key: Optional[str] = None) -> GatewayResponse:
        api_key = resolved_api_key or self.config.api_key
        if not api_key:
            return GatewayResponse(
                content="",
                model=self.config.model,
                provider=self.id,
                success=False,
                error="OpenAI API Key is not configured."
            )

        model = request.model or self.config.model
        base_url = (self.config.base_url or "https://api.openai.com/v1").rstrip("/")
        url = f"{base_url}/chat/completions"

        messages = [{"role": m.role, "content": m.content} for m in request.messages]
        payload = {
            "model": model,
            "messages": messages,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
        }

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        t0 = time.time()
        try:
            r = requests.post(url, json=payload, headers=headers, timeout=self.config.timeout)
            elapsed_ms = round((time.time() - t0) * 1000, 1)

            if r.status_code == 200:
                data = r.json()
                choices = data.get("choices", [])
                text = choices[0].get("message", {}).get("content", "") if choices else ""
                usage = data.get("usage", {})
                return GatewayResponse(
                    content=text,
                    model=model,
                    provider=self.id,
                    latency_ms=elapsed_ms,
                    input_tokens=usage.get("prompt_tokens", 0),
                    output_tokens=usage.get("completion_tokens", 0),
                    success=True
                )
            else:
                return GatewayResponse(
                    content="",
                    model=model,
                    provider=self.id,
                    latency_ms=elapsed_ms,
                    success=False,
                    error=f"HTTP {r.status_code}: {r.text[:200]}"
                )
        except Exception as e:
            elapsed_ms = round((time.time() - t0) * 1000, 1)
            return GatewayResponse(
                content="",
                model=model,
                provider=self.id,
                latency_ms=elapsed_ms,
                success=False,
                error=str(e)
            )
