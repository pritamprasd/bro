"""Unit tests for AuditManager."""

import tempfile
from pathlib import Path
from bro.core.audit import AuditManager

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

        # Verify html export
        html_doc = am.export_run_html(run.run_id)
        assert "<!DOCTYPE html>" in html_doc
        assert "Open calculator and compute 5 * 5" in html_doc
        assert "desktop_click" in html_doc
        assert "Result is 25" in html_doc
        assert "STEP 1" in html_doc

        # Verify json export
        json_doc = am.export_run_json(run.run_id)
        assert "Open calculator and compute 5 * 5" in json_doc
        assert "desktop_click" in json_doc


def test_download_report_endpoints():
    from fastapi.testclient import TestClient
    from bro.ui.server import app, audit
    
    # Create a dummy run if none exists
    run = audit.start_run("Test Download Functionality")
    audit.complete_run("Download completed successfully", status="success")
    
    client = TestClient(app)
    
    # Test markdown download
    res_md = client.get(f"/api/history/{run.run_id}/download?format=md")
    assert res_md.status_code == 200
    assert "attachment;" in res_md.headers.get("content-disposition", "")
    assert ".md" in res_md.headers.get("content-disposition", "")
    assert "Test Download Functionality" in res_md.text

    # Test html download
    res_html = client.get(f"/api/history/{run.run_id}/download?format=html")
    assert res_html.status_code == 200
    assert "attachment;" in res_html.headers.get("content-disposition", "")
    assert ".html" in res_html.headers.get("content-disposition", "")
    assert "<!DOCTYPE html>" in res_html.text

    # Test json download
    res_json = client.get(f"/api/history/{run.run_id}/download?format=json")
    assert res_json.status_code == 200
    assert "attachment;" in res_json.headers.get("content-disposition", "")
    assert ".json" in res_json.headers.get("content-disposition", "")
    assert run.run_id in res_json.text

