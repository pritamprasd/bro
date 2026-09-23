"""Daily brief engine for on-demand and scheduled briefings."""

import datetime
from typing import Any, Callable, Optional
from jarvis.config import CronConfig

class CronEngine:
    def __init__(
        self,
        config: CronConfig,
        briefing_callback: Optional[Callable[[str], None]] = None,
        daily_brief_engine: Optional[Any] = None
    ):
        self.config = config
        self.briefing_callback = briefing_callback
        self.daily_brief_engine = daily_brief_engine
        self.enabled = config.enabled
        self.last_briefing_date: Optional[str] = None

    def trigger_brief(self) -> str:
        """Manually trigger the Daily brief."""
        if self.daily_brief_engine:
            res = self.daily_brief_engine.generate_briefing()
            briefing = res.get("spoken_text", "")
        else:
            now = datetime.datetime.now()
            briefing = self._generate_briefing(now)

        if self.briefing_callback:
            self.briefing_callback(briefing)
        return briefing

    def check_schedule(self) -> Optional[str]:
        """Check if it's time for scheduled daily brief if enabled."""
        if not self.enabled:
            return None

        now = datetime.datetime.now()
        today_str = now.strftime("%Y-%m-%d")
        current_time_str = now.strftime("%H:%M")

        if current_time_str == self.config.briefing_time and self.last_briefing_date != today_str:
            self.last_briefing_date = today_str
            return self.trigger_brief()

        return None

    def _generate_briefing(self, now: datetime.datetime) -> str:
        date_str = now.strftime("%A, %B %d")
        time_str = now.strftime("%I:%M %p")
        return (
            f"Daily brief for {date_str}, {time_str}. All Jarvis Mark 3 systems are operational. "
            "RTX 3060 VRAM is primed, local reasoning models are active, and memory subsystems are synchronized. "
            "Standing by for your instructions."
        )
