"""Unit tests for lean Markdown MemoryStore."""

import tempfile
import pytest
from jarvis.config import MemoryConfig
from jarvis.memory.store import MemoryStore

def test_lean_selective_memory_loading():
    with tempfile.TemporaryDirectory() as tmpdir:
        config = MemoryConfig(memory_dir=tmpdir)
        store = MemoryStore(config)

        # 1. Unrelated prompt should load preferences, but NOT telegram workflow
        mem_general = store.get_relevant_memory("Calculate 25 * 4")
        assert "preferences.md" in mem_general
        assert "workflows/telegram.md" not in mem_general

        # 2. Telegram prompt should specifically load telegram workflow
        mem_tg = store.get_relevant_memory("Send a telegram message to the team")
        assert "workflows/telegram.md" in mem_tg
        assert "Telegram Bot API" in mem_tg

def test_save_and_retrieve_custom_workflow():
    with tempfile.TemporaryDirectory() as tmpdir:
        config = MemoryConfig(memory_dir=tmpdir)
        store = MemoryStore(config)

        store.save_workflow("data_processing", "# Custom data processing with pandas\ndf = pd.read_csv('...')")

        # Now query about data processing
        mem = store.get_relevant_memory("Run the data processing routine")
        assert "workflows/data_processing.md" in mem
        assert "Custom data processing with pandas" in mem
