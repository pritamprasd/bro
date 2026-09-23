"""Calendar engine for parsing, adding, and toggling markdown-based schedule events."""

import os
import re
from datetime import datetime, date
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

EVENT_REGEX = re.compile(
    r"^-\s*\[(?P<status>[ xX])\]\s*(?P<date>\d{4}-\d{2}-\d{2})(?:\s+(?P<time>\d{1,2}:\d{2}))?\s*-\s*(?P<title>[^#\n]+?)(?:\s+(?P<tags>#[\w\-#\s]+))?$",
    re.UNICODE,
)

class CalendarEngine:
    def __init__(self, calendar_file: Union[str, Path]):
        self.calendar_file = Path(calendar_file).expanduser()
        self._ensure_file_exists()

    def _ensure_file_exists(self) -> None:
        if not self.calendar_file.exists():
            self.calendar_file.parent.mkdir(parents=True, exist_ok=True)
            self.calendar_file.write_text(
                "# Jarvis Calendar & Schedule\n\n## Scheduled Events & Deadlines\n",
                encoding="utf-8",
            )

    def get_events(self, completed: Optional[bool] = None) -> List[Dict[str, Any]]:
        """Parse all events from the markdown calendar file."""
        events: List[Dict[str, Any]] = []
        if not self.calendar_file.exists():
            return events

        lines = self.calendar_file.read_text(encoding="utf-8").splitlines()
        for idx, line in enumerate(lines):
            match = EVENT_REGEX.match(line.strip())
            if match:
                is_done = match.group("status").lower() == "x"
                if completed is not None and is_done != completed:
                    continue

                event_date = match.group("date")
                event_time = match.group("time") or ""
                title = match.group("title").strip()
                raw_tags = match.group("tags") or ""
                tags = [t.strip("#").strip() for t in raw_tags.split() if t.startswith("#")]

                events.append({
                    "id": idx,
                    "date": event_date,
                    "time": event_time,
                    "title": title,
                    "completed": is_done,
                    "tags": tags,
                    "raw_line": line,
                })
        return events

    def get_pending_events(self) -> List[Dict[str, Any]]:
        """Return all uncompleted events sorted by date and time."""
        events = self.get_events(completed=False)
        events.sort(key=lambda x: (x["date"], x["time"] or "23:59"))
        return events

    def add_event(self, title: str, event_date: str, event_time: str = "", tags: Optional[List[str]] = None) -> Dict[str, Any]:
        """Add a new event to the calendar file."""
        self._ensure_file_exists()
        tag_str = " ".join([f"#{t.strip('#')}" for t in (tags or [])])
        time_part = f" {event_time.strip()}" if event_time and event_time.strip() else ""
        tags_part = f" {tag_str}" if tag_str else ""
        new_line = f"- [ ] {event_date.strip()}{time_part} - {title.strip()}{tags_part}"

        content = self.calendar_file.read_text(encoding="utf-8")
        if not content.endswith("\n"):
            content += "\n"
        content += f"{new_line}\n"
        self.calendar_file.write_text(content, encoding="utf-8")

        all_events = self.get_events()
        return all_events[-1] if all_events else {
            "id": -1,
            "date": event_date,
            "time": event_time,
            "title": title,
            "completed": False,
            "tags": tags or [],
            "raw_line": new_line,
        }

    def toggle_event(self, identifier: Union[int, str], completed: Optional[bool] = None) -> bool:
        """Toggle or set completion status of an event by line index or partial title match."""
        if not self.calendar_file.exists():
            return False

        lines = self.calendar_file.read_text(encoding="utf-8").splitlines()
        target_idx: Optional[int] = None

        if isinstance(identifier, int) and 0 <= identifier < len(lines):
            if EVENT_REGEX.match(lines[identifier].strip()):
                target_idx = identifier
        else:
            q = str(identifier).lower()
            for idx, line in enumerate(lines):
                if EVENT_REGEX.match(line.strip()) and q in line.lower():
                    target_idx = idx
                    break

        if target_idx is None:
            return False

        target_line = lines[target_idx]
        if completed is True:
            new_line = re.sub(r"^-\s*\[\s*\]", "- [x]", target_line)
        elif completed is False:
            new_line = re.sub(r"^-\s*\[[xX]\]", "- [ ]", target_line)
        else:
            # Toggle
            if "- [ ]" in target_line:
                new_line = target_line.replace("- [ ]", "- [x]", 1)
            else:
                new_line = target_line.replace("- [x]", "- [ ]", 1).replace("- [X]", "- [ ]", 1)

        lines[target_idx] = new_line
        self.calendar_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return True

    def get_today_summary(self, target_date: Optional[str] = None) -> str:
        """Return a voice-ready natural summary of events for the specified date (default today)."""
        if not target_date:
            target_date = date.today().strftime("%Y-%m-%d")

        all_events = self.get_events()
        today_events = [e for e in all_events if e["date"] == target_date]

        if not today_events:
            return "Your schedule is clear for today, Sir."

        pending = [e for e in today_events if not e["completed"]]
        done = [e for e in today_events if e["completed"]]

        if not pending and done:
            return f"All {len(done)} items on your schedule for today have already been completed, Sir."

        parts = []
        for e in pending:
            time_desc = f" at {e['time']}" if e["time"] else ""
            parts.append(f"{e['title']}{time_desc}")

        summary = f"You have {len(pending)} item{'s' if len(pending) > 1 else ''} scheduled for today: "
        if len(parts) == 1:
            summary += parts[0] + "."
        elif len(parts) == 2:
            summary += f"{parts[0]}, and {parts[1]}."
        else:
            summary += ", ".join(parts[:-1]) + f", and {parts[-1]}."

        return summary

    def clear_all_events(self) -> int:
        """Clear all scheduled events and tasks from the calendar markdown file."""
        events_count = len(self.get_events())
        self._ensure_file_exists()
        self.calendar_file.write_text(
            "# Jarvis Calendar & Schedule\n\n## Scheduled Events & Deadlines\n",
            encoding="utf-8",
        )
        return events_count
