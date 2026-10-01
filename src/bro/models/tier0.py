"""Tier-0 Instant Router for sub-100ms intent classification using Llama 3.2 3B."""

import json
import re
import time
from typing import Any, Dict, Optional
from pydantic import BaseModel
import requests
from bro.config import ModelConfig
from bro.models.ollama_provider import normalize_keep_alive

class IntentClassification(BaseModel):
    intent: str  # CONVERSATION, DESKTOP_GUI, BROWSER, PYTHON_TASK, SYSTEM_SHELL, WATCHDOG
    confidence: float = 1.0
    summary: str = ""
    can_execute_directly: bool = False
    direct_response: Optional[str] = None
    direct_action: Optional[str] = None
    direct_params: Optional[Dict[str, Any]] = None
    elapsed_ms: float = 0.0

TIER0_PROMPT = """You are Tier-0 Fast Classifier & Instant Assistant. Classify the user goal into ONE category:
- CONVERSATION (answering questions, greetings, explanations, chit-chat, math, reasoning)
- DESKTOP_GUI (clicking UI, opening desktop apps, taking desktop screenshots)
- BROWSER (opening websites, web search, web scraping, visiting URLs)
- PYTHON_TASK (running python scripts, data processing, telegram bot messaging)
- SYSTEM_SHELL (bash commands, listing files, system stats)
- WATCHDOG (checking hardware sentinel, download organizer)

CRITICAL INSTRUCTION:
- If intent is CONVERSATION: directly answer the user's question, greeting, or explanation naturally, concisely, and accurately in "direct_response". Set "can_execute_directly": true.
- If intent is DESKTOP_GUI, BROWSER, PYTHON_TASK, SYSTEM_SHELL, or WATCHDOG: set "direct_response": null and "can_execute_directly": false.

Respond with ONLY valid JSON:
{
  "intent": "CATEGORY",
  "summary": "one-line summary",
  "can_execute_directly": false,
  "direct_response": null
}
"""

class Tier0Router:
    def __init__(self, config: ModelConfig):
        self.config = config
        self.enabled = config.tier0_enabled
        self.model_name = config.tier0_model
        self.base_url = config.ollama_url.rstrip("/")

    def classify(self, user_goal: str, relevant_memory: Optional[str] = None) -> IntentClassification:
        """Classify user intent in <100ms and directly answer conversational queries using Tier-0 fast model."""
        if not self.enabled:
            return IntentClassification(
                intent="COMPLEX_PLAN",
                summary="Tier-0 disabled, falling back to main model",
                confidence=1.0,
            )

        start_time = time.time()
        prompt = TIER0_PROMPT
        if relevant_memory:
            prompt += f"\n\nContext & Relevant Memory:\n{relevant_memory}"

        timeout_sec = getattr(self.config, "tier0_timeout", 3.0) or 3.0
        options = {"temperature": 0.2, "num_predict": 256}
        if getattr(self.config, "tier0_device", "gpu") == "cpu":
            options["num_gpu"] = 0

        try:
            resp = requests.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model_name,
                    "messages": [
                        {"role": "system", "content": prompt},
                        {"role": "user", "content": user_goal},
                    ],
                    "format": "json",
                    "keep_alive": normalize_keep_alive(self.config.keep_alive),
                    "stream": False,
                    "options": options,
                },
                timeout=max(3.0, float(timeout_sec)),
            )
            elapsed_ms = (time.time() - start_time) * 1000

            if resp.status_code == 200:
                content = resp.json().get("message", {}).get("content", "")
                match = re.search(r"\{.*\}", content, re.DOTALL)
                if match:
                    data = json.loads(match.group(0))
                    intent = data.get("intent", "COMPLEX_PLAN")
                    direct_resp = data.get("direct_response")
                    can_exec = data.get("can_execute_directly", False) or (intent == "CONVERSATION" and bool(direct_resp))
                    
                    return IntentClassification(
                        intent=intent,
                        summary=data.get("summary", ""),
                        can_execute_directly=can_exec,
                        direct_response=direct_resp if (direct_resp and str(direct_resp).strip()) else None,
                        confidence=0.95,
                        elapsed_ms=round(elapsed_ms, 1),
                    )

        except Exception as e:
            # Non-blocking fallback to main model
            pass

        return IntentClassification(
            intent="COMPLEX_PLAN",
            summary="Fallback to main model",
            confidence=0.8,
            elapsed_ms=round((time.time() - start_time) * 1000, 1),
        )

    def respond_direct(self, user_goal: str, relevant_memory: Optional[str] = None) -> Optional[str]:
        """Generate a fast direct response using Tier-0 model if classify didn't output direct_response."""
        if not self.enabled:
            return None
        system_content = "You are Bro, an elite, witty, and concise tactical AI assistant. Answer directly and concisely."
        if relevant_memory:
            system_content += f"\n\nContext & Relevant Memory:\n{relevant_memory}"
        try:
            resp = requests.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model_name,
                    "messages": [
                        {"role": "system", "content": system_content},
                        {"role": "user", "content": user_goal},
                    ],
                    "keep_alive": normalize_keep_alive(self.config.keep_alive),
                    "stream": False,
                    "options": {"temperature": 0.4, "num_predict": 300},
                },
                timeout=4.0,
            )
            if resp.status_code == 200:
                return resp.json().get("message", {}).get("content", "").strip()
        except Exception:
            pass
        return None
