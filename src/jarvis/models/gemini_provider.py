"""Google Gemini Cloud Provider (Free Tier compatible / Google GenAI SDK)."""

import json
import os
import re
from typing import Any, Dict, List, Optional
from jarvis.models.base import BaseLLMProvider, ChatMessage, CoordinatePrediction, ModelResponse, ToolCall

class GeminiProvider(BaseLLMProvider):
    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "gemini-2.5-flash",
    ):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model_name = model_name
        self.client = None

        if self.api_key:
            try:
                from google import genai
                self.client = genai.Client(api_key=self.api_key)
            except Exception as e:
                print(f"[Warning] Could not initialize Google GenAI Client: {e}")

    def is_available(self) -> bool:
        return self.client is not None

    def generate_text(
        self,
        messages: List[ChatMessage],
        system_prompt: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> ModelResponse:
        if not self.client:
            raise RuntimeError(
                "Gemini API key is not configured. Run `jarvis vault set gemini_api_key` "
                "or obtain a free-tier key with $0 cost at https://aistudio.google.com"
            )

        # Build contents from messages
        contents = []
        for m in messages:
            contents.append(f"{m.role.upper()}: {m.content}")

        full_prompt = "\n\n".join(contents)
        if system_prompt:
            full_prompt = f"SYSTEM INSTRUCTIONS:\n{system_prompt}\n\n" + full_prompt

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=full_prompt,
            )
            return ModelResponse(
                content=response.text or "",
                finish_reason="stop",
            )
        except Exception as e:
            raise RuntimeError(f"Gemini API request failed: {e}") from e

    def ground_coordinates(
        self,
        image_base64: str,
        instruction: str,
        display_width: int = 1920,
        display_height: int = 1080,
    ) -> CoordinatePrediction:
        if not self.client:
            raise RuntimeError(
                "Gemini API key is not configured. For free access, get a key at https://aistudio.google.com"
            )

        import base64
        image_bytes = base64.b64decode(image_base64)

        prompt = (
            f"You are a computer vision UI grounder. Screen dimensions are {display_width}x{display_height}.\n"
            f"Instruction: {instruction}\n"
            "Identify the UI element to interact with. Return JSON ONLY:\n"
            "{\n"
            '  "point": [x, y],\n'
            '  "action": "click" | "double_click" | "right_click" | "type" | "scroll" | "none",\n'
            '  "text_to_type": "string if action is type else null",\n'
            '  "confidence": 0.0 to 1.0,\n'
            '  "reasoning": "brief explanation"\n'
            "}"
        )

        try:
            from google.genai import types
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[
                    types.Part.from_bytes(data=image_bytes, mime_type="image/png"),
                    prompt,
                ],
            )
            raw_text = response.text or ""
            json_match = re.search(r"\{.*\}", raw_text, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group(0))
                point = parsed.get("point", [display_width // 2, display_height // 2])
                px = int(point[0])
                py = int(point[1])
                return CoordinatePrediction(
                    x=px,
                    y=py,
                    action=parsed.get("action", "click"),
                    text_to_type=parsed.get("text_to_type"),
                    confidence=float(parsed.get("confidence", 0.95)),
                    reasoning=parsed.get("reasoning", ""),
                )
            else:
                raise ValueError(f"Could not parse JSON from Gemini output: {raw_text}")
        except Exception as e:
            raise RuntimeError(f"Gemini vision grounding failed: {e}") from e
