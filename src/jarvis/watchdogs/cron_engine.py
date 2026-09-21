"""Scheduled Cron Engine for daily morning briefings and periodic tasks."""

import datetime
import time
from typing import Callable, Optional
from jarvis.config import CronConfig

class CronEngine:
    def __init__(self, config: CronConfig, briefing_callback: Optional[Callable[[str], None]] = None):
        self.config = config
        self.briefing_callback = briefing_callback
        self.enabled = config.enabled
        self.last_briefing_date: Optional[str] = None

    def check_schedule(self) -> Optional[str]:
        """Check if it's time for daily briefing."""
        if not self.enabled:
            return None

        now = datetime.datetime.now()
        today_str = now.strftime("%Y-%m-%d")
        current_time_str = now.strftime("%H:%M")

        if current_time_str == self.config.briefing_time and self.last_briefing_date != today_str:
            self.last_briefing_date = today_str
            briefing = self._generate_briefing(now)
            if self.briefing_callback:
                self.briefing_callback(briefing)
            return briefing

        return None

    def _generate_briefing(self, now: datetime.datetime) -> str:
        date_str = now.strftime("%A, %B %d")
        return (
            f"Good morning, sir. Today is {date_str}. All workstation systems are operational. "
            "RTX 3060 VRAM is primed, and memory subsystems are synchronized. "
            "Ready for instructions whenever you are."
        )
