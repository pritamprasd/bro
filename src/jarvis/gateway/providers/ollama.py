"""Local Ollama provider implementation for Enterprise LLM Gateway."""

import time
from typing import Optional
import requests
from jarvis.gateway.models import GatewayRequest, GatewayResponse
from jarvis.gateway.providers.base import BaseLLMProvider

class OllamaGatewayProvider(BaseLLMProvider):
    def generate(self, request: GatewayRequest, resolved_api_key: Optional[str] = None) -> GatewayResponse:
        model = request.model or self.config.model
        base_url = (self.config.base_url or "http://localhost:11434").rstrip("/")
        url = f"{base_url}/api/chat"

        messages = [{"role": m.role, "content": m.content} for m in request.messages]
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": request.temperature,
                "num_predict": request.max_tokens,
            }
        }

        t0 = time.time()
        try:
            r = requests.post(url, json=payload, timeout=self.config.timeout)
            elapsed_ms = round((time.time() - t0) * 1000, 1)

            if r.status_code == 200:
                data = r.json()
                content = data.get("message", {}).get("content", "")
                prompt_tokens = data.get("prompt_eval_count", 0)
                eval_tokens = data.get("eval_count", 0)
                return GatewayResponse(
                    content=content,
                    model=model,
                    provider=self.id,
                    latency_ms=elapsed_ms,
                    input_tokens=prompt_tokens,
                    output_tokens=eval_tokens,
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
