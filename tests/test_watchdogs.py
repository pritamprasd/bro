"""Unit tests for Watchdog Sentinels and Download Organizer."""

import tempfile
from pathlib import Path
from jarvis.config import OrganizerConfig, SentinelConfig
from jarvis.watchdogs.organizer import DownloadOrganizer
from jarvis.watchdogs.sentinel import HardwareSentinel

def test_hardware_sentinel_metrics():
    cfg = SentinelConfig(enabled=True)
    sentinel = HardwareSentinel(cfg)
    metrics = sentinel.get_hardware_metrics()

    assert "cpu_percent" in metrics
    assert "ram_percent" in metrics
    assert "disk_percent" in metrics
    assert metrics["ram_percent"] > 0

def test_download_organizer():
    with tempfile.TemporaryDirectory() as tmpdir:
        watch_dir = Path(tmpdir) / "Downloads"
        docs_dir = Path(tmpdir) / "Documents"
        watch_dir.mkdir()
        docs_dir.mkdir()

        # Create dummy PDF
        dummy_pdf = watch_dir / "report.pdf"
        dummy_pdf.write_text("dummy pdf content")

        cfg = OrganizerConfig(
            enabled=True,
            watch_dir=str(watch_dir),
            rules={"pdf": str(docs_dir)},
        )
        organizer = DownloadOrganizer(cfg)
        moved = organizer.organize_once()

        assert len(moved) == 1
        assert not dummy_pdf.exists()
        assert (docs_dir / "report.pdf").exists()
