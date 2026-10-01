"""Base definitions for Bro actuators."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from pydantic import BaseModel

class ActionResult(BaseModel):
    success: bool
    output: str = ""
    error: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    screenshot_base64: Optional[str] = None

class BaseActuator(ABC):
    @abstractmethod
    def reset(self) -> None:
        """Reset state if necessary."""
        pass
