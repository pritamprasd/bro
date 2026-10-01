"""Abstract base classes and data structures for Model Providers."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class ChatMessage(BaseModel):
    role: str  # "system", "user", "assistant", "tool"
    content: str
    images: Optional[List[str]] = None  # Base64 encoded or paths

class ToolCall(BaseModel):
    name: str
    arguments: Dict[str, Any]

class ModelResponse(BaseModel):
    content: str
    tool_calls: Optional[List[ToolCall]] = None
    finish_reason: str = "stop"
    raw_response: Optional[Dict[str, Any]] = None

class CoordinatePrediction(BaseModel):
    x: int  # 0 to 1000 normalized or physical pixel coordinate
    y: int  # 0 to 1000 normalized or physical pixel coordinate
    action: str = "click"  # "click", "double_click", "right_click", "type", "scroll", "none"
    text_to_type: Optional[str] = None
    confidence: float = 1.0
    reasoning: str = ""

class BaseLLMProvider(ABC):
    """Abstract interface for LLM/VLM providers."""

    @abstractmethod
    def generate_text(
        self,
        messages: List[ChatMessage],
        system_prompt: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> ModelResponse:
        """Generate response from chat messages."""
        pass

    @abstractmethod
    def ground_coordinates(
        self,
        image_base64: str,
        instruction: str,
        display_width: int = 1920,
        display_height: int = 1080,
    ) -> CoordinatePrediction:
        """Analyze a screenshot and predict the target UI coordinate and action."""
        pass
