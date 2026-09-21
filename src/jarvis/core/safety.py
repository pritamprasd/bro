"""Safety classification and guardrails for Jarvis."""

import re
from typing import List, Optional
from pydantic import BaseModel
from jarvis.config import SafetyConfig

class RiskAssessment(BaseModel):
    is_high_stakes: bool
    risk_level: str  # "safe", "moderate", "critical"
    reason: str
    action_type: str
    action_details: str

class SafetyClassifier:
    def __init__(self, config: SafetyConfig):
        self.config = config
        self.keywords = [k.lower() for k in config.high_stakes_keywords]

    def assess_action(
        self,
        action_type: str,
        details: str,
        target_name: Optional[str] = None,
    ) -> RiskAssessment:
        """Evaluate whether an action requires explicit user authorization."""
        combined_text = f"{action_type} {details} {target_name or ''}".lower()

        # Check for critical keywords
        for kw in self.keywords:
            if re.search(r"\b" + re.escape(kw) + r"\b", combined_text) or kw in combined_text:
                return RiskAssessment(
                    is_high_stakes=True,
                    risk_level="critical" if any(c in kw for c in ["rm", "wipe", "format", "sudo", "payment", "buy"]) else "moderate",
                    reason=f"Detected high-stakes keyword or operation: '{kw}'",
                    action_type=action_type,
                    action_details=details,
                )

        # Check dangerous shell commands
        if action_type in ["shell", "bash"]:
            dangerous_patterns = [
                r"\brm\b\s+-[a-zA-Z]*r",  # rm -r / rm -rf
                r"\bmkfs\b",
                r"\bdd\b\s+if=",
                r">\s*/dev/sd",
                r":\(\)\s*\{\s*:\|:&\s*\};:",  # forkbomb
                r"\bchmod\b\s+-[a-zA-Z]*R\s+777\s+/",
            ]
            for pat in dangerous_patterns:
                if re.search(pat, details):
                    return RiskAssessment(
                        is_high_stakes=True,
                        risk_level="critical",
                        reason=f"Destructive shell pattern detected: '{pat}'",
                        action_type=action_type,
                        action_details=details,
                    )

        # Default safe
        return RiskAssessment(
            is_high_stakes=False,
            risk_level="safe",
            reason="Action conforms to standard automated operations.",
            action_type=action_type,
            action_details=details,
        )
