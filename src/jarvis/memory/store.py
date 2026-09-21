"""Lean and structured Markdown memory store with on-demand selective loading."""

import os
import re
from pathlib import Path
from typing import Dict, List, Optional
from jarvis.config import MemoryConfig

DEFAULT_PREFERENCES = """# User Preferences
- Name: Pritam
- System: Linux X11 (AMD Ryzen 7, NVIDIA RTX 3060 12GB)
- Assistant Persona: Jarvis (Efficient, proactive, helpful, precise)
- Safety: Confirm high-stakes actions unless autonomous_mode is on
"""

DEFAULT_SYSTEM_INFO = """# System & Desktop Environment
- Window Server: X11
- Primary Shell: /bin/bash
- GPU: NVIDIA RTX 3060 (12GB VRAM)
- Default Workspace: /home/pritam/code/ai/jarvis
"""

DEFAULT_TELEGRAM_WORKFLOW = """# Workflow: Telegram Messaging
- To send a Telegram message via Python:
  Use python requests with the Telegram Bot API:
  `url = f"https://api.telegram.org/bot{token}/sendMessage"`
  `payload = {"chat_id": chat_id, "text": message}`
- Token key in vault: `telegram_bot_token`
- Chat ID key in vault: `telegram_chat_id`
"""

class MemoryStore:
    def __init__(self, config: MemoryConfig):
        self.memory_dir = Path(config.memory_dir).expanduser()
        self.workflows_dir = self.memory_dir / "workflows"
        self._initialize_structure()

    def _initialize_structure(self) -> None:
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self.workflows_dir.mkdir(parents=True, exist_ok=True)

        pref_file = self.memory_dir / "preferences.md"
        if not pref_file.exists():
            pref_file.write_text(DEFAULT_PREFERENCES, encoding="utf-8")

        sys_file = self.memory_dir / "system.md"
        if not sys_file.exists():
            sys_file.write_text(DEFAULT_SYSTEM_INFO, encoding="utf-8")

        tg_file = self.workflows_dir / "telegram.md"
        if not tg_file.exists():
            tg_file.write_text(DEFAULT_TELEGRAM_WORKFLOW, encoding="utf-8")

        contacts_file = self.memory_dir / "contacts.md"
        if not contacts_file.exists():
            contacts_file.write_text("# Contacts & Handles\n# Format: - Name: email / handle\n", encoding="utf-8")

    def get_relevant_memory(self, prompt: str) -> str:
        """Selectively load ONLY memory files relevant to the current user prompt."""
        p_lower = prompt.lower()
        loaded_sections: List[str] = []

        # 1. Base Preferences (always load lean user profile)
        pref_path = self.memory_dir / "preferences.md"
        if pref_path.exists():
            content = pref_path.read_text(encoding="utf-8").strip()
            if content:
                loaded_sections.append(f"<!-- MEMORY: preferences.md -->\n{content}")

        # 2. System Info if asking about environment, GPU, or desktop
        if any(w in p_lower for w in ["system", "gpu", "x11", "hardware", "specs", "display"]):
            sys_path = self.memory_dir / "system.md"
            if sys_path.exists():
                loaded_sections.append(f"<!-- MEMORY: system.md -->\n{sys_path.read_text(encoding='utf-8').strip()}")

        # 3. Contacts if asking about emailing or messaging someone
        if any(w in p_lower for w in ["contact", "email", "message", "telegram", "send to", "who is"]):
            contacts_path = self.memory_dir / "contacts.md"
            if contacts_path.exists():
                content = contacts_path.read_text(encoding="utf-8").strip()
                if len(content.splitlines()) > 2:
                    loaded_sections.append(f"<!-- MEMORY: contacts.md -->\n{content}")

        # 4. Workflows directory search
        if self.workflows_dir.exists():
            for wf_file in self.workflows_dir.glob("*.md"):
                topic = wf_file.stem.lower()
                # If topic name appears in prompt or words match
                if topic in p_lower or any(part in p_lower for part in topic.split("_")):
                    loaded_sections.append(
                        f"<!-- MEMORY: workflows/{wf_file.name} -->\n{wf_file.read_text(encoding='utf-8').strip()}"
                    )

        return "\n\n".join(loaded_sections)

    def save_workflow(self, topic: str, content: str) -> Path:
        """Save or update a learned workflow."""
        filename = f"{re.sub(r'[^a-zA-Z0-9_-]', '_', topic.lower())}.md"
        path = self.workflows_dir / filename
        path.write_text(content, encoding="utf-8")
        return path

    def append_note(self, target_file: str, note: str) -> None:
        """Append a note to a specific memory file."""
        path = self.memory_dir / target_file
        if not path.exists():
            path.write_text(f"# {target_file}\n\n", encoding="utf-8")
        with open(path, "a", encoding="utf-8") as f:
            f.write(f"\n- {note}\n")
