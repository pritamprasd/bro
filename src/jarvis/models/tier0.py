"""Tier-0 Instant Router for sub-100ms intent classification using Llama 3.2 3B."""

import json
import re
import time
from typing import Any, Dict, Optional
from pydantic import BaseModel
import requests
from jarvis.config import ModelConfig
from jarvis.models.ollama_provider import normalize_keep_alive

class IntentClassification(BaseModel):
    intent: str  # CONVERSATION, DESKTOP_GUI, BROWSER, PYTHON_TASK, SYSTEM_SHELL, WATCHDOG
    confidence: float = 1.0
    summary: str = ""
    direct_action: Optional[str] = None
    direct_params: Optional[Dict[str, Any]] = None
    elapsed_ms: float = 0.0

TIER0_PROMPT = """You are Tier-0 Fast Classifier. Classify the user goal into ONE category:
- CONVERSATION (answering questions, greetings, explanations, math)
- DESKTOP_GUI (clicking UI, opening desktop apps, taking desktop screenshots)
- BROWSER (opening websites, web search, web scraping, visiting URLs)
- PYTHON_TASK (running python scripts, data processing, telegram bot messaging)
- SYSTEM_SHELL (bash commands, listing files, system stats)
- WATCHDOG (checking hardware sentinel, download organizer)

Respond with ONLY valid JSON:
{
  "intent": "CATEGORY",
  "summary": "one-line summary",
  "can_execute_directly": false
}
"""

class Tier0Router:
    def __init__(self, config: ModelConfig):
        self.config = config
        self.enabled = config.tier0_enabled
        self.model_name = config.tier0_model
        self.base_url = config.ollama_url.rstrip("/")

    def classify(self, user_goal: str) -> IntentClassification:
        """Classify user intent in <100ms. Falls back to Gemma 4 if disabled or on error."""
        if not self.enabled:
            return IntentClassification(
                intent="COMPLEX_PLAN",
                summary="Tier-0 disabled, falling back to Gemma 4",
                confidence=1.0,
            )

        start_time = time.time()
        try:
            resp = requests.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model_name,
                    "messages": [
                        {"role": "system", "content": TIER0_PROMPT},
                        {"role": "user", "content": user_goal},
                    ],
                    "format": "json",
                    "keep_alive": normalize_keep_alive(self.config.keep_alive),
                    "stream": False,
                    "options": {"temperature": 0.0, "num_predict": 120},
                },
                timeout=3,
            )
            elapsed_ms = (time.time() - start_time) * 1000

            if resp.status_code == 200:
                content = resp.json().get("message", {}).get("content", "")
                match = re.search(r"\{.*\}", content, re.DOTALL)
                if match:
                    data = json.loads(match.group(0))
                    return IntentClassification(
                        intent=data.get("intent", "COMPLEX_PLAN"),
                        summary=data.get("summary", ""),
                        confidence=0.95,
                        elapsed_ms=round(elapsed_ms, 1),
                    )

        except Exception as e:
            # Non-blocking fallback to Gemma 4
            pass

        return IntentClassification(
            intent="COMPLEX_PLAN",
            summary="Fallback to Gemma 4",
            confidence=0.8,
            elapsed_ms=round((time.time() - start_time) * 1000, 1),
        )
