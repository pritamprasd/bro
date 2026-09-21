"""Error and System Failure Logging for Jarvis Mark 1."""

import time
import traceback
from typing import Any, Dict, List, Optional
from pydantic import BaseModel

class SystemErrorRecord(BaseModel):
    timestamp: float
    time_str: str
    error_type: str
    message: str
    context: Optional[str] = None
    stack_trace: Optional[str] = None

class ErrorTracker:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ErrorTracker, cls).__new__(cls)
            cls._instance.errors = []
        return cls._instance

    def log_error(self, error_type: str, message: str, context: Optional[str] = None, exc: Optional[Exception] = None) -> SystemErrorRecord:
        record = SystemErrorRecord(
            timestamp=time.time(),
            time_str=time.strftime("%Y-%m-%d %H:%M:%S"),
            error_type=error_type,
            message=str(message),
            context=context,
            stack_trace=traceback.format_exc() if exc else None,
        )
        self.errors.insert(0, record)
        # Keep last 50 errors
        if len(self.errors) > 50:
            self.errors.pop()
        return record

    def get_errors(self) -> List[Dict[str, Any]]:
        return [e.model_dump() for e in self.errors]

    def clear(self) -> None:
        self.errors.clear()

error_tracker = ErrorTracker()
