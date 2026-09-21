"""Configurable Folder Watchdog & Organizer for downloads and documents."""

import os
import shutil
import time
from pathlib import Path
from typing import Dict, List, Optional
from jarvis.config import OrganizerConfig

class DownloadOrganizer:
    def __init__(self, config: OrganizerConfig):
        self.config = config
        self.enabled = config.enabled
        self.watch_dir = Path(config.watch_dir).expanduser()
        self.rules = self._parse_rules(config.rules)

    def _parse_rules(self, raw_rules: Dict[str, str]) -> Dict[str, Path]:
        """Convert comma-separated extensions into normalized mapping: '.ext' -> Path."""
        parsed = {}
        for exts, dest_str in raw_rules.items():
            dest_path = Path(dest_str).expanduser()
            for ext in exts.split(","):
                clean_ext = ext.strip().lower()
                if not clean_ext.startswith("."):
                    clean_ext = "." + clean_ext
                parsed[clean_ext] = dest_path
        return parsed

    def organize_once(self) -> List[str]:
        """Scan directory and move matching files to their configured destinations."""
        if not self.enabled or not self.watch_dir.exists():
            return []

        moved_files = []
        for item in self.watch_dir.iterdir():
            if item.is_file() and not item.name.startswith("."):
                # Handle double extensions like .tar.gz
                lower_name = item.name.lower()
                matched_dest = None
                for ext, dest in self.rules.items():
                    if lower_name.endswith(ext):
                        matched_dest = dest
                        break

                if matched_dest:
                    matched_dest.mkdir(parents=True, exist_ok=True)
                    target_file = matched_dest / item.name

                    # Avoid overwrite
                    counter = 1
                    while target_file.exists():
                        target_file = matched_dest / f"{item.stem}_{counter}{item.suffix}"
                        counter += 1

                    try:
                        shutil.move(str(item), str(target_file))
                        moved_files.append(f"Moved '{item.name}' -> {matched_dest.name}/")
                    except Exception as e:
                        print(f"[Warning] Failed to move {item.name}: {e}")

        return moved_files
