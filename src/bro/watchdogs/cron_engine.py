"""Cron/schedule engine for Bro — supports multi-slot daily briefings (Variant 4)."""

import datetime
from typing import Any, Callable, Dict, Optional
from bro.config import CronConfig


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
        # Track last briefing date per slot key (e.g. "07:30", "12:00")
        self.last_briefing_dates: Dict[str, str] = {}

    def trigger_brief(self, topic_ids: Optional[list] = None) -> str:
        """Manually trigger the Daily brief (optionally filtered to specific topic IDs)."""
        if self.daily_brief_engine:
            if topic_ids is not None:
                res = self.daily_brief_engine.generate_briefing_for_topics(topic_ids)
            else:
                res = self.daily_brief_engine.generate_briefing()
            briefing = res.get("spoken_text", "")
        else:
            now = datetime.datetime.now()
            briefing = self._generate_briefing(now)

        if self.briefing_callback:
            self.briefing_callback(briefing)
        return briefing

    def check_schedule(self) -> Optional[str]:
        """Check if any brief slot is due to fire right now.

        Called once per minute (e.g., from the watchdog polling loop).
        Iterates all enabled slots from DailyBriefEngine.brief_slots and fires
        the appropriate topic-filtered briefing for each matched slot.
        Only fires once per slot per day.
        """
        if not self.enabled:
            return None

        now = datetime.datetime.now()
        today_str = now.strftime("%Y-%m-%d")
        current_time_str = now.strftime("%H:%M")

        # --- Multi-slot mode (Variant 4) ---
        if self.daily_brief_engine:
            active_slots = self.daily_brief_engine.get_active_slots()
            for slot in active_slots:
                slot_key = slot.time
                last_date = self.last_briefing_dates.get(slot_key)
                if current_time_str == slot_key and last_date != today_str:
                    self.last_briefing_dates[slot_key] = today_str
                    return self.trigger_brief(topic_ids=slot.topics)
            return None

        # --- Legacy single-slot fallback ---
        last_date = self.last_briefing_dates.get("legacy")
        if current_time_str == self.config.briefing_time and last_date != today_str:
            self.last_briefing_dates["legacy"] = today_str
            return self.trigger_brief()

        return None

    def _generate_briefing(self, now: datetime.datetime) -> str:
        date_str = now.strftime("%A, %B %d")
        time_str = now.strftime("%I:%M %p")
        return (
            f"Daily brief for {date_str}, {time_str}. All Bro Variant 4 systems are operational. "
            "Local GPU VRAM is primed, local reasoning models are active, and memory subsystems are synchronized. "
            "Standing by for your instructions."
        )

