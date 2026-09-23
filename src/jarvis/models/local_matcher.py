"""Local Intent Matcher for sub-millisecond offline execution of common voice triggers."""

import hashlib
import json
import os
import random
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from jarvis.memory.calendar_engine import CalendarEngine


class LocalIntentMatcher:
    def __init__(self, memory_dir: Union[str, Path], calendar_engine: Optional[CalendarEngine] = None):
        self.memory_dir = Path(memory_dir).expanduser()
        self.intents_file = self.memory_dir / "local_intents.md"
        self.cache_file = self.memory_dir / "local_intents_cache.json"
        self.calendar_engine = calendar_engine or CalendarEngine(self.memory_dir / "calendar.md")
        self.patterns: List[Dict[str, Any]] = []
        self._compiled_regexes: List[Tuple[re.Pattern, Dict[str, Any]]] = []
        self._exact_lookup: Dict[str, Dict[str, Any]] = {}
        self.load_intents()

    def _normalize(self, text: str) -> str:
        """Strip punctuation and whitespace, lowercase."""
        text = text.lower().strip()
        text = re.sub(r"[?!.,'\"]+", "", text)
        return re.sub(r"\s+", " ", text).strip()

    def load_intents(self) -> None:
        """Parse local_intents.md into structured pattern rules and compile matchers."""
        if not self.intents_file.exists():
            return

        content = self.intents_file.read_text(encoding="utf-8")
        current_pattern: Optional[Dict[str, Any]] = None
        current_section = ""
        patterns: List[Dict[str, Any]] = []

        for line in content.splitlines():
            line_str = line.strip()
            if line_str.startswith("## Pattern:"):
                if current_pattern:
                    patterns.append(current_pattern)
                name = line_str.replace("## Pattern:", "").strip()
                current_pattern = {
                    "name": name,
                    "triggers": [],
                    "responses": [],
                    "dynamic_action": None,
                    "parameters": [],
                }
                current_section = ""
                continue

            if not current_pattern:
                continue

            if line_str.startswith("- Triggers:"):
                current_section = "triggers"
                raw = line_str.replace("- Triggers:", "").strip()
                # Extract quoted strings
                found = re.findall(r'"([^"]*)"', raw)
                if found:
                    current_pattern["triggers"].extend(found)
                continue

            if line_str.startswith("- Dynamic Action:"):
                current_pattern["dynamic_action"] = line_str.replace("- Dynamic Action:", "").strip()
                continue

            if line_str.startswith("- Parameters:"):
                raw = line_str.replace("- Parameters:", "").strip()
                current_pattern["parameters"] = [p.strip() for p in raw.split(",") if p.strip()]
                continue

            if line_str.startswith("- Dynamic Response:") or line_str.startswith("- Responses:") or line_str.startswith("- Response Templates:"):
                current_section = "responses"
                continue

            if line_str.startswith("- ") and current_section == "responses":
                resp = line_str[2:].strip().strip('"').strip("'")
                if resp:
                    current_pattern["responses"].append(resp)
                continue

        if current_pattern:
            patterns.append(current_pattern)

        # Infer dynamic action if missing but template tokens present
        for pat in patterns:
            if not pat.get("dynamic_action"):
                for r in pat.get("responses", []):
                    if "{time}" in r:
                        pat["dynamic_action"] = "time_now"
                        break
                    elif "{calendar_events}" in r:
                        pat["dynamic_action"] = "calendar_today"
                        break

        self.patterns = patterns
        self._build_matchers(content)

    def _build_matchers(self, raw_content: str) -> None:
        """Compile regexes and build exact match lookup dictionaries."""
        self._exact_lookup.clear()
        self._compiled_regexes.clear()

        # Check cache
        content_hash = hashlib.md5(raw_content.encode("utf-8")).hexdigest()
        cached_variations: Dict[str, List[str]] = {}
        if self.cache_file.exists():
            try:
                data = json.loads(self.cache_file.read_text(encoding="utf-8"))
                if data.get("hash") == content_hash:
                    cached_variations = data.get("variations", {})
            except Exception:
                pass

        updated_variations: Dict[str, List[str]] = dict(cached_variations)

        for pat in self.patterns:
            pat_name = pat["name"]
            all_triggers = list(pat["triggers"])
            if pat_name in cached_variations:
                all_triggers.extend(cached_variations[pat_name])

            for trig in all_triggers:
                trig_clean = trig.strip()
                if "{" in trig_clean and "}" in trig_clean:
                    # Parameterized trigger -> compile regex
                    # Convert "{file}" to "(?P<file>[^/\\<>:\"|?*]+)" or "(?P<file>.+)"
                    regex_str = re.escape(trig_clean)
                    # Replace escaped braces
                    regex_str = re.sub(r"\\\{([a-zA-Z0-9_]+)\\\}", r"(?P<\1>.+)", regex_str)
                    regex_pattern = re.compile(rf"^{regex_str}$", re.IGNORECASE)
                    self._compiled_regexes.append((regex_pattern, pat))
                else:
                    norm = self._normalize(trig_clean)
                    self._exact_lookup[norm] = pat

            if pat_name not in updated_variations:
                # Store base trigger variants
                base_variants = [self._normalize(t) for t in pat["triggers"] if "{" not in t]
                updated_variations[pat_name] = base_variants

        # Save cache
        try:
            self.cache_file.write_text(
                json.dumps({"hash": content_hash, "variations": updated_variations}, indent=2),
                encoding="utf-8",
            )
        except Exception:
            pass

    def match_and_execute(self, user_goal: str) -> Optional[Dict[str, Any]]:
        """Attempt fast local matching (<5ms). Returns dict with response or None."""
        if not user_goal or not user_goal.strip():
            return None

        clean_goal = self._normalize(user_goal)
        matched_pat: Optional[Dict[str, Any]] = None
        slots: Dict[str, str] = {}

        # 1. Exact / normalized lookup
        if clean_goal in self._exact_lookup:
            matched_pat = self._exact_lookup[clean_goal]

        # 2. Check compiled regexes (e.g. parameter extractions)
        if not matched_pat:
            raw_goal = user_goal.strip()
            for pattern_re, pat in self._compiled_regexes:
                m = pattern_re.search(raw_goal)
                if not m:
                    # Try searching on normalized goal
                    m = pattern_re.search(clean_goal)
                if m:
                    matched_pat = pat
                    slots = m.groupdict()
                    break

        if not matched_pat:
            return None

        # Execute dynamic action if present
        action = matched_pat.get("dynamic_action")
        response_text = ""
        action_data: Optional[Dict[str, Any]] = None

        if action == "time_now":
            now = datetime.now()
            time_str = now.strftime("%I:%M %p").lstrip("0")
            hour = now.hour
            if 5 <= hour < 12:
                period = "morning"
            elif 12 <= hour < 17:
                period = "afternoon"
            elif 17 <= hour < 21:
                period = "evening"
            else:
                period = "night"

            templates = matched_pat.get("responses") or ["It's {time}."]
            chosen = random.choice(templates)
            response_text = chosen.replace("{time}", time_str).replace("{period}", period)

        elif action == "calendar_today":
            summary = self.calendar_engine.get_today_summary()
            templates = matched_pat.get("responses") or ["{calendar_events}"]
            chosen = random.choice(templates)
            response_text = chosen.replace("{calendar_events}", summary)

        elif action == "show_file_content":
            file_name = slots.get("file", "").strip()
            path_name = slots.get("path", "").strip()
            target_path: Optional[Path] = None

            if path_name:
                target_path = Path(path_name).expanduser() / file_name
            else:
                p = Path(file_name).expanduser()
                if p.exists() and p.is_file():
                    target_path = p
                else:
                    # Search common locations: current dir, home dir, memory dir
                    candidates = [
                        Path.cwd() / file_name,
                        self.memory_dir / file_name,
                        Path.home() / file_name,
                    ]
                    for cand in candidates:
                        if cand.exists() and cand.is_file():
                            target_path = cand
                            break

            if target_path and target_path.exists() and target_path.is_file():
                try:
                    content_text = target_path.read_text(encoding="utf-8", errors="replace")
                    # Limit to first 300 lines or 20KB for display
                    lines = content_text.splitlines()[:300]
                    preview = "\n".join(lines)
                    response_text = f"Displaying content of {target_path.name} ({len(lines)} lines)."
                    action_data = {
                        "action": "show_file_content",
                        "file_path": str(target_path.resolve()),
                        "file_name": target_path.name,
                        "content": preview,
                        "line_count": len(lines),
                    }
                except Exception as e:
                    response_text = f"Could not read {file_name}: {e}"
            else:
                response_text = f"I could not locate the file '{file_name}' on the filesystem, Sir."

        else:
            templates = matched_pat.get("responses")
            if templates:
                response_text = random.choice(templates)
            else:
                response_text = f"Executed {matched_pat['name']}."

        return {
            "pattern": matched_pat["name"],
            "response_text": response_text,
            "action": action,
            "action_data": action_data,
        }
