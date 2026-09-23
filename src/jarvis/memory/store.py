"""Lean and structured Markdown memory store with on-demand selective loading."""

import os
import re
from pathlib import Path
from typing import Dict, List, Optional
from jarvis.config import MemoryConfig

DEFAULT_PREFERENCES = """# User Preferences
- Name: User
- System: Linux X11 (AMD Ryzen 7, NVIDIA RTX 3060 12GB)
- Assistant Persona: Jarvis (Efficient, proactive, helpful, precise)
- Safety: Confirm high-stakes actions unless autonomous_mode is on
"""

DEFAULT_SYSTEM_INFO = """# System & Desktop Environment
- Window Server: X11
- Primary Shell: /bin/bash
- GPU: NVIDIA RTX 3060 (12GB VRAM)
- Default Workspace: ~/code/ai/jarvis
"""

DEFAULT_TELEGRAM_WORKFLOW = """# Workflow: Telegram Messaging
- To send a Telegram message via Python:
  Use python requests with the Telegram Bot API:
  `url = f"https://api.telegram.org/bot{token}/sendMessage"`
  `payload = {"chat_id": chat_id, "text": message}`
- Token key in vault: `telegram_bot_token`
- Chat ID key in vault: `telegram_chat_id`
"""

DEFAULT_GREETINGS = """# Jarvis Mark 4 Vocal Greetings & Salutations

## General Greetings
- Greetings, Sir. All systems armed and operational. What is our objective today?
- Jarvis Mark 4 online. Neural pathways cleared and ready for your command, Sir.
- Hello Sir. Hardware telemetry is nominal, standing by for instructions.
- Good day, Sir. How may I be of service to you today?
- At your service, Sir. Ready to execute whenever you are.

## Morning Greetings
- Good morning, Sir. All diagnostic systems report optimal status. How can I assist you?
- Good morning. Workstation is armed, standing by for today's mission.
- Good morning, Sir. Coffee status unknown, but neural core is fully operational.

## Afternoon Greetings
- Good afternoon, Sir. Systems standing by for your next directive.
- Good afternoon. Telemetry stable, ready for your commands.

## Evening Greetings
- Good evening, Sir. Jarvis Mark 4 standing by for your evening workflow.
- Good evening. All defensive watchdogs and sentinels remain active. What shall we tackle?

## Gen-Z Greetings & Slang
- Yo, what's good! Jarvis in the building, no cap.
- Vibe check passed. All systems bussin and ready to slay, boss.
- Sup! Neural core is locked in, highkey ready for whatever you got.
- Ayo, we're live fr fr. What's the move today?
- Main character energy loaded. What are we cookin up?
- Sheesh, workstation is running clean. What's the play?
- Bet. All systems go, let's get this bread.
- Aura points at maximum, ready to assist on god.
- Lowkey ready to crush today's tasks, let's do this.
- Big tech energy activated, what's on your radar?
"""

DEFAULT_CALENDAR = """# Workstation Calendar & Tasks

## Pending Events & Tasks
- [ ] 2026-09-24 10:00 - Team standup and sprint demo #meeting
- [ ] 2026-09-24 14:30 - Deploy Jarvis Mark 2 to staging #task
- [ ] 2026-09-25 11:00 - Architecture review & security audit #meeting
- [ ] 2026-09-26 16:00 - Workstation backup and GPU benchmark #maintenance

## Completed Events & Tasks
- [x] 2026-09-23 18:00 - Jarvis Mark 2 evolution verification #release
"""

DEFAULT_LOCAL_INTENTS = """# Local Instant Workflows & Fast Utterances

## Pattern: Greeting
- Triggers: "Hey Jarvis", "Hello Jarvis", "Hi Jarvis", "Greetings Jarvis", "Good morning Jarvis", "Wake up Jarvis", "Are you there Jarvis"
- Response Templates:
  - "Hello Sir, how can I assist you today?"
  - "At your service, Sir. What is your goal?"
  - "Greetings. All systems operational. How may I help?"
  - "Online and listening, Sir. What is our objective?"

## Pattern: Current Time
- Triggers: "What's the time right now?", "Tell me the time", "What time is it", "Current time", "Check time", "Time please", "What is the time"
- Dynamic Action: time_now
- Dynamic Response:
  - "It's {time} in the {period}."
  - "The time is currently {time}."

## Pattern: Calendar Today
- Triggers: "How's my calendar look like today", "What is on my schedule today", "Show today's calendar", "Do I have any meetings today", "Check my schedule"
- Dynamic Action: calendar_today
- Dynamic Response:
  - "Today's calendar looks like: {calendar_events}"

## Pattern: Show File Content
- Triggers: "Show content of {file}", "Display file {file}", "View file {file}", "Read {file} in {path}", "Open and show {file}"
- Dynamic Action: show_file_content
- Parameters: file, path
"""

class MemoryStore:
    def __init__(self, config: MemoryConfig):
        self.config = config
        self.memory_dir = Path(config.memory_dir).expanduser()
        self.workflows_dir = self.memory_dir / "workflows"
        self._initialize_structure()

        from jarvis.memory.rag import HybridRAGEngine
        self.rag = HybridRAGEngine(
            memory_dir=str(self.memory_dir),
            obsidian_vault_dir=getattr(config, "obsidian_vault_dir", None),
            embedding_model=getattr(config, "embedding_model", "nomic-embed-text"),
            enabled=getattr(config, "semantic_search_enabled", True),
        )

    def _initialize_structure(self) -> None:
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self.workflows_dir.mkdir(parents=True, exist_ok=True)

        # Auto-migration: If this target directory is empty, migrate from legacy ~/.jarvis/memory if it exists
        legacy_dir = Path.home() / ".jarvis" / "memory"
        if legacy_dir.exists() and legacy_dir.is_dir() and legacy_dir.resolve() != self.memory_dir.resolve():
            self._migrate_legacy_memory(legacy_dir)

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

        greetings_file = self.memory_dir / "greetings.md"
        if not greetings_file.exists():
            greetings_file.write_text(DEFAULT_GREETINGS, encoding="utf-8")

        calendar_file = self.memory_dir / "calendar.md"
        if not calendar_file.exists():
            calendar_file.write_text(DEFAULT_CALENDAR, encoding="utf-8")

        local_intents_file = self.memory_dir / "local_intents.md"
        if not local_intents_file.exists():
            local_intents_file.write_text(DEFAULT_LOCAL_INTENTS, encoding="utf-8")

    def get_random_greeting(self, gen_z_mode: bool = False) -> str:
        """Read greetings.md and pick a random greeting line according to gen_z_mode, or return default."""
        import random
        greetings_file = self.memory_dir / "greetings.md"
        standard_candidates: List[str] = []
        genz_candidates: List[str] = []
        
        if greetings_file.exists():
            try:
                current_section = ""
                for line in greetings_file.read_text(encoding="utf-8").splitlines():
                    line_str = line.strip()
                    if line_str.startswith("## "):
                        current_section = line_str.lower()
                        continue
                    if line_str.startswith("- "):
                        greeting = line_str[2:].strip().strip('"').strip("'")
                        if greeting:
                            if "gen-z" in current_section or "slang" in current_section:
                                genz_candidates.append(greeting)
                            else:
                                standard_candidates.append(greeting)
            except Exception:
                pass

        if gen_z_mode and genz_candidates:
            return random.choice(genz_candidates)
        if standard_candidates:
            return random.choice(standard_candidates)
        if genz_candidates:
            return random.choice(genz_candidates)
        return "Hello Sir. All systems operational and standing by for your command."

    def _migrate_legacy_memory(self, legacy_dir: Path) -> None:
        """Migrate existing markdown files from legacy directory to new memory directory."""
        try:
            for item in legacy_dir.rglob("*.md"):
                rel_path = item.relative_to(legacy_dir)
                dest_path = self.memory_dir / rel_path
                if not dest_path.exists():
                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                    text = item.read_text(encoding="utf-8")
                    text = re.sub(r'Name:\s*[A-Za-z\s]+', 'Name: User', text)
                    text = re.sub(r'/home/[^/\s]+/code/ai/jarvis', '~/code/ai/jarvis', text)
                    dest_path.write_text(text, encoding="utf-8")
        except Exception:
            pass

    def get_relevant_memory(self, prompt: str) -> str:
        """Selectively load relevant memory and Obsidian notes using hybrid search."""
        p_lower = prompt.lower()
        loaded_sections: List[str] = []

        # 1. Base Preferences (always load lean user profile)
        pref_path = self.memory_dir / "preferences.md"
        if pref_path.exists():
            content = pref_path.read_text(encoding="utf-8").strip()
            if content:
                loaded_sections.append(f"<!-- MEMORY: preferences.md -->\n{content}")

        # 2. Hybrid RAG Context (BM25 + Semantic Search across memory & Obsidian Vault)
        rag_context = ""
        if hasattr(self, "rag") and self.rag and self.rag.enabled:
            try:
                rag_context = self.rag.format_context(prompt, top_k=3)
            except Exception:
                pass

        if rag_context:
            loaded_sections.append(rag_context)
        else:
            # Fallback to keyword matching if RAG finds no strong signals
            if any(w in p_lower for w in ["system", "gpu", "x11", "hardware", "specs", "display"]):
                sys_path = self.memory_dir / "system.md"
                if sys_path.exists():
                    loaded_sections.append(f"<!-- MEMORY: system.md -->\n{sys_path.read_text(encoding='utf-8').strip()}")

            if any(w in p_lower for w in ["contact", "email", "message", "telegram", "send to", "who is"]):
                contacts_path = self.memory_dir / "contacts.md"
                if contacts_path.exists():
                    content = contacts_path.read_text(encoding="utf-8").strip()
                    if len(content.splitlines()) > 2:
                        loaded_sections.append(f"<!-- MEMORY: contacts.md -->\n{content}")

        # 3. Workflows directory check (guarantees direct retrieval for named routines)
        if self.workflows_dir.exists():
            for wf_file in self.workflows_dir.glob("*.md"):
                topic = wf_file.stem.lower()
                if topic in p_lower or any(part in p_lower for part in topic.split("_") if len(part) > 2):
                    tag = f"<!-- MEMORY: workflows/{wf_file.name} -->"
                    if not any(tag in s for s in loaded_sections):
                        loaded_sections.append(
                            f"{tag}\n{wf_file.read_text(encoding='utf-8').strip()}"
                        )

        return "\n\n".join(loaded_sections)

    def save_workflow(self, topic: str, content: str) -> Path:
        """Save or update a learned workflow."""
        filename = f"{re.sub(r'[^a-zA-Z0-9_-]', '_', topic.lower())}.md"
        path = self.workflows_dir / filename
        path.write_text(content, encoding="utf-8")
        if hasattr(self, "rag") and self.rag:
            try:
                self.rag.refresh_index()
            except Exception:
                pass
        return path

    def append_note(self, target_file: str, note: str) -> None:
        """Append a note to a specific memory file."""
        path = self.memory_dir / target_file
        if not path.exists():
            path.write_text(f"# {target_file}\n\n", encoding="utf-8")
        with open(path, "a", encoding="utf-8") as f:
            f.write(f"\n- {note}\n")
        if hasattr(self, "rag") and self.rag:
            try:
                self.rag.refresh_index()
            except Exception:
                pass
