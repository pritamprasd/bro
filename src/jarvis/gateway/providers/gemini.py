"""Google Gemini provider implementation for Enterprise LLM Gateway."""

import time
from typing import Optional
import requests
from jarvis.gateway.models import GatewayRequest, GatewayResponse
from jarvis.gateway.providers.base import BaseLLMProvider

class GeminiProvider(BaseLLMProvider):
    def generate(self, request: GatewayRequest, resolved_api_key: Optional[str] = None) -> GatewayResponse:
        api_key = resolved_api_key or self.config.api_key
        if not api_key:
            return GatewayResponse(
                content="",
                model=self.config.model,
                provider=self.id,
                success=False,
                error="Gemini API Key is not configured."
            )

        model = request.model or self.config.model
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        
        contents = []
        system_instruction = None
        for msg in request.messages:
            if msg.role == "system":
                system_instruction = {"parts": [{"text": msg.content}]}
            elif msg.role == "user":
                contents.append({"role": "user", "parts": [{"text": msg.content}]})
            elif msg.role == "assistant":
                contents.append({"role": "model", "parts": [{"text": msg.content}]})

        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": request.temperature,
                "maxOutputTokens": request.max_tokens,
            }
        }
        if system_instruction:
            payload["systemInstruction"] = system_instruction

        t0 = time.time()
        try:
            r = requests.post(url, json=payload, timeout=self.config.timeout)
            elapsed_ms = round((time.time() - t0) * 1000, 1)

            if r.status_code == 200:
                data = r.json()
                text = ""
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    text = "".join(p.get("text", "") for p in parts)
                usage = data.get("usageMetadata", {})
                return GatewayResponse(
                    content=text,
                    model=model,
                    provider=self.id,
                    latency_ms=elapsed_ms,
                    input_tokens=usage.get("promptTokenCount", 0),
                    output_tokens=usage.get("candidatesTokenCount", 0),
                    success=True
                )
            else:
                err_msg = f"HTTP {r.status_code}: {r.text[:200]}"
                return GatewayResponse(
                    content="",
                    model=model,
                    provider=self.id,
                    latency_ms=elapsed_ms,
                    success=False,
                    error=err_msg
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
