"""Smart Model Router managing local vs cloud tiering policy."""

from typing import Any, Dict, List, Optional
from jarvis.config import ModelConfig
from jarvis.models.base import BaseLLMProvider, ChatMessage, CoordinatePrediction, ModelResponse
from jarvis.models.gemini_provider import GeminiProvider
from jarvis.models.ollama_provider import OllamaProvider

class ModelRouter:
    def __init__(self, config: ModelConfig):
        self.config = config
        self.local_provider = OllamaProvider(
            base_url=config.ollama_url,
            text_model=config.local_text_model,
            vision_model=config.local_vision_model,
        )
        self.cloud_provider = GeminiProvider(
            api_key=config.gemini_api_key,
            model_name=config.cloud_model,
        )

    def generate_text(
        self,
        messages: List[ChatMessage],
        system_prompt: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> ModelResponse:
        policy = self.config.policy

        if policy == "cloud_only":
            return self.cloud_provider.generate_text(messages, system_prompt, tools)

        if policy == "local_only":
            return self.local_provider.generate_text(messages, system_prompt, tools)

        # "tier_fallback": Try local first, fallback to cloud
        try:
            return self.local_provider.generate_text(messages, system_prompt, tools)
        except Exception as local_err:
            if self.cloud_provider.is_available():
                return self.cloud_provider.generate_text(messages, system_prompt, tools)
            raise RuntimeError(
                f"Local generation failed: {local_err}. Cloud provider is not available."
            ) from local_err

    def ground_coordinates(
        self,
        image_base64: str,
        instruction: str,
        display_width: int = 1920,
        display_height: int = 1080,
    ) -> CoordinatePrediction:
        policy = self.config.policy

        if policy == "cloud_only":
            return self.cloud_provider.ground_coordinates(
                image_base64, instruction, display_width, display_height
            )

        if policy == "local_only":
            return self.local_provider.ground_coordinates(
                image_base64, instruction, display_width, display_height
            )

        # "tier_fallback": Try local vision model first
        try:
            prediction = self.local_provider.ground_coordinates(
                image_base64, instruction, display_width, display_height
            )
            # If local confidence is high, return it
            if prediction.confidence >= 0.7:
                return prediction
            
            # If confidence is low and cloud is available, escalate
            if self.cloud_provider.is_available():
                return self.cloud_provider.ground_coordinates(
                    image_base64, instruction, display_width, display_height
                )
            return prediction
        except Exception as local_err:
            if self.cloud_provider.is_available():
                return self.cloud_provider.ground_coordinates(
                    image_base64, instruction, display_width, display_height
                )
            raise RuntimeError(
                f"Local visual grounding failed: {local_err}. Cloud provider is not available."
            ) from local_err
