"""Unit tests for lean Markdown MemoryStore."""

import tempfile
import pytest
from bro.config import MemoryConfig
from bro.memory.store import MemoryStore

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

def test_default_memory_dir_in_config():
    from bro.config import DEFAULT_MEMORY_DIR
    config = MemoryConfig()
    assert str(DEFAULT_MEMORY_DIR) in config.memory_dir or "ai-memory/bro" in config.memory_dir

def test_memory_store_migration_from_legacy():
    import pathlib
    with tempfile.TemporaryDirectory() as tmp_legacy:
        legacy_path = pathlib.Path(tmp_legacy)
        (legacy_path / "workflows").mkdir(parents=True)
        (legacy_path / "preferences.md").write_text("# User Preferences\n- Name: Alice\n", encoding="utf-8")
        (legacy_path / "workflows" / "custom.md").write_text("# Custom Routine\nDo things", encoding="utf-8")

        with tempfile.TemporaryDirectory() as tmp_new:
            new_path = pathlib.Path(tmp_new) / "bro_mem"
            config = MemoryConfig(memory_dir=str(new_path))
            store = MemoryStore(config)

            # Manually invoke legacy migration to simulate legacy ~/.bro/memory
            store._migrate_legacy_memory(legacy_path)

            assert (new_path / "preferences.md").exists()
            assert (new_path / "workflows" / "custom.md").exists()
            assert "Custom Routine" in (new_path / "workflows" / "custom.md").read_text(encoding="utf-8")
