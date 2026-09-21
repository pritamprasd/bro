"""Ollama Provider supporting Gemma 4 (Text/Logic) and Qwen2.5-VL (Vision/Computer Use)."""

import json
import re
from typing import Any, Dict, List, Optional
import requests
from jarvis.models.base import BaseLLMProvider, ChatMessage, CoordinatePrediction, ModelResponse, ToolCall

class OllamaProvider(BaseLLMProvider):
    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        text_model: str = "gemma4:12b",
        vision_model: str = "qwen2.5vl:7b",
        timeout: int = 120,
    ):
        self.base_url = base_url.rstrip("/")
        self.text_model = text_model
        self.vision_model = vision_model
        self.timeout = timeout

    def check_health(self) -> bool:
        """Check if Ollama server is reachable."""
        try:
            r = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return r.status_code == 200
        except Exception:
            return False

    def generate_text(
        self,
        messages: List[ChatMessage],
        system_prompt: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> ModelResponse:
        """Generate text using local model (e.g. Gemma 4)."""
        formatted_messages = []
        if system_prompt:
            formatted_messages.append({"role": "system", "content": system_prompt})

        for m in messages:
            msg_dict = {"role": m.role, "content": m.content}
            if m.images:
                msg_dict["images"] = m.images
            formatted_messages.append(msg_dict)

        payload: Dict[str, Any] = {
            "model": self.text_model,
            "messages": formatted_messages,
            "stream": False,
            "options": {
                "temperature": 0.2,
            },
        }

        if tools:
            payload["tools"] = tools

        try:
            resp = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=self.timeout,
            )
            resp.raise_for_status()
            data = resp.json()
            message_data = data.get("message", {})
            content = message_data.get("content", "")

            # Parse tool calls if present
            tool_calls = None
            if "tool_calls" in message_data and message_data["tool_calls"]:
                tool_calls = []
                for tc in message_data["tool_calls"]:
                    func = tc.get("function", {})
                    tool_calls.append(
                        ToolCall(
                            name=func.get("name", ""),
                            arguments=func.get("arguments", {}),
                        )
                    )

            return ModelResponse(
                content=content,
                tool_calls=tool_calls,
                finish_reason=data.get("done_reason", "stop"),
                raw_response=data,
            )
        except Exception as e:
            raise RuntimeError(f"Ollama text generation failed on model '{self.text_model}': {e}") from e

    def ground_coordinates(
        self,
        image_base64: str,
        instruction: str,
        display_width: int = 1920,
        display_height: int = 1080,
    ) -> CoordinatePrediction:
        """Use local vision model (Qwen2.5-VL / LLaVA) to locate UI elements."""
        system_prompt = (
            "You are a computer vision UI grounder for desktop automation. "
            "Given a screenshot and a user instruction, identify the exact (x, y) coordinates of the UI element to interact with. "
            f"Screen dimensions are {display_width}x{display_height}. "
            "You must return ONLY a valid JSON object with the following schema:\n"
            "{\n"
            '  "point": [x, y],\n'
            '  "action": "click" | "double_click" | "right_click" | "type" | "scroll" | "none",\n'
            '  "text_to_type": "string if action is type else null",\n'
            '  "confidence": 0.0 to 1.0,\n'
            '  "reasoning": "brief explanation"\n'
            "}"
        )

        prompt = f"Instruction: {instruction}\nReturn the JSON location on screen {display_width}x{display_height}:"

        payload = {
            "model": self.vision_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": prompt,
                    "images": [image_base64],
                },
            ],
            "format": "json",
            "stream": False,
            "options": {
                "temperature": 0.1,
            },
        }

        try:
            resp = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=self.timeout,
            )
            resp.raise_for_status()
            data = resp.json()
            raw_text = data.get("message", {}).get("content", "")

            # Attempt to extract JSON from response
            json_match = re.search(r"\{.*\}", raw_text, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group(0))
                point = parsed.get("point", [display_width // 2, display_height // 2])
                px = int(point[0]) if len(point) > 0 else display_width // 2
                py = int(point[1]) if len(point) > 1 else display_height // 2

                # If model returned normalized [0, 1000] range instead of pixel range:
                if px <= 1000 and py <= 1000 and (display_width > 1000 or display_height > 1000):
                    # Check if likely normalized:
                    norm_x = int((px / 1000.0) * display_width)
                    norm_y = int((py / 1000.0) * display_height)
                else:
                    norm_x = px
                    norm_y = py

                return CoordinatePrediction(
                    x=norm_x,
                    y=norm_y,
                    action=parsed.get("action", "click"),
                    text_to_type=parsed.get("text_to_type"),
                    confidence=float(parsed.get("confidence", 0.9)),
                    reasoning=parsed.get("reasoning", ""),
                )
            else:
                raise ValueError(f"Could not parse JSON from model output: {raw_text}")

        except Exception as e:
            raise RuntimeError(f"Ollama vision grounding failed on '{self.vision_model}': {e}") from e
