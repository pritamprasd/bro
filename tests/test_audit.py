"""Unit tests for AuditManager."""

import tempfile
from pathlib import Path
from jarvis.core.audit import AuditManager

def test_audit_manager_lifecycle():
    with tempfile.TemporaryDirectory() as tmpdir:
        am = AuditManager(base_dir=Path(tmpdir))

        run = am.start_run("Open calculator and compute 5 * 5")
        assert run.run_id is not None
        assert run.goal == "Open calculator and compute 5 * 5"

        am.record_step(
            step_num=1,
            thought="Click calculator icon",
            action="desktop_click",
            params={"x": 50, "y": 100},
            observation="Calculator launched",
            success=True,
        )

        am.complete_run("Result is 25", status="success")

        # Verify listing
        runs = am.list_recent_runs()
        assert len(runs) == 1
        assert runs[0]["run_id"] == run.run_id
        assert len(runs[0]["steps"]) == 1
        assert runs[0]["status"] == "success"

        # Verify analytics
        analytics = am.get_analytics()
        assert analytics["total_runs"] == 1
        assert analytics["success_count"] == 1
        assert analytics["failed_count"] == 0
        assert analytics["success_rate"] == 100.0
        assert analytics["total_steps"] == 1
        assert analytics["actuator_breakdown"]["desktop"] == 1
        assert len(analytics["recent_timeline"]) == 1
        assert analytics["recent_timeline"][0]["goal"] == "Open calculator and compute 5 * 5"

        # Verify markdown export
        md = am.export_run_markdown(run.run_id)
        assert f"Mission Audit Report: {run.run_id}" in md
        assert "Open calculator and compute 5 * 5" in md
        assert "desktop_click" in md
        assert "Result is 25" in md
