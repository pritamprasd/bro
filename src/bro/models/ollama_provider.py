"""Ollama Provider supporting Gemma 4 (Text/Logic) and Qwen2.5-VL (Vision/Computer Use)."""

import json
import re
from typing import Any, Dict, List, Optional, Union
import requests
from bro.models.base import BaseLLMProvider, ChatMessage, CoordinatePrediction, ModelResponse, ToolCall

def normalize_keep_alive(val: Any) -> Any:
    """Normalize keep_alive value for Ollama API.
    
    Ollama requires either an integer duration in seconds (-1 for permanent),
    or a string with duration units (e.g. '24h', '5m', '-1m').
    Passing plain string '-1' causes Go's time.ParseDuration to fail with 400 Bad Request.
    """
    if isinstance(val, (int, float)):
        return int(val) if isinstance(val, int) or (isinstance(val, float) and val.is_integer()) else val
    if isinstance(val, str):
        cleaned = val.strip().strip("'\"")
        try:
            return int(cleaned)
        except ValueError:
            return cleaned
    return -1

class OllamaProvider(BaseLLMProvider):
    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        text_model: str = "gemma4:12b",
        vision_model: str = "qwen2.5vl:7b",
        keep_alive: Any = -1,
        timeout: int = 120,
    ):
        self.base_url = base_url.rstrip("/")
        self.text_model = text_model
        self.vision_model = vision_model
        self.keep_alive = normalize_keep_alive(keep_alive)
        self.timeout = timeout

    def check_health(self) -> bool:
        """Check if Ollama server is reachable."""
        try:
            r = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return r.status_code == 200
        except Exception:
            return False

    def warmup(self) -> None:
        """Pre-warm model into RAM/VRAM with keep_alive."""
        try:
            requests.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.text_model,
                    "messages": [{"role": "user", "content": "ping"}],
                    "keep_alive": normalize_keep_alive(self.keep_alive),
                    "stream": False,
                },
                timeout=180,
            )
        except Exception as e:
            print(f"[Warning] Ollama warmup for {self.text_model} encountered: {e}")

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
            "keep_alive": normalize_keep_alive(self.keep_alive),
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
            if resp.status_code >= 400:
                err_detail = resp.text
                try:
                    err_json = resp.json()
                    if "error" in err_json:
                        err_detail = err_json["error"]
                except Exception:
                    pass

                # If Ollama rejected tools parameter with 400, retry once without tools
                if tools and resp.status_code == 400 and ("tool" in err_detail.lower() or "schema" in err_detail.lower() or "invalid" in err_detail.lower()):
                    payload_no_tools = dict(payload)
                    payload_no_tools.pop("tools", None)
                    retry_resp = requests.post(
                        f"{self.base_url}/api/chat",
                        json=payload_no_tools,
                        timeout=self.timeout,
                    )
                    if retry_resp.status_code < 400:
                        resp = retry_resp
                    else:
                        raise RuntimeError(f"Ollama API returned HTTP {resp.status_code}: {err_detail}")
                else:
                    raise RuntimeError(f"Ollama API returned HTTP {resp.status_code}: {err_detail}")

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
            "keep_alive": normalize_keep_alive(self.keep_alive),
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
            if resp.status_code >= 400:
                err_detail = resp.text
                try:
                    err_json = resp.json()
                    if "error" in err_json:
                        err_detail = err_json["error"]
                except Exception:
                    pass
                raise RuntimeError(f"Ollama vision API returned HTTP {resp.status_code}: {err_detail}")

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
