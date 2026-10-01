"""Audit Trail & Session Recording for full action replay and filmstrips."""

import base64
import html
import json
import os
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel

RUNS_DIR = Path.home() / ".bro" / "runs"

class StepRecord(BaseModel):
    step_num: int
    thought: str
    action: str
    params: Dict[str, Any]
    observation: str
    success: bool
    screenshot_file: Optional[str] = None
    timestamp: float
    # Variant 4: per-step timing breakdown for the debug waterfall view
    started_at: Optional[float] = None   # Unix timestamp when this step began
    duration_ms: Optional[float] = None  # Total step wall-clock time (ms)
    llm_ms: Optional[float] = None       # LLM round-trip time (ms)
    tool_ms: Optional[float] = None      # Tool/actuator execution time (ms)

class RunRecord(BaseModel):
    run_id: str
    goal: str
    start_time: float
    end_time: Optional[float] = None
    status: str = "running"  # "running", "success", "failed"
    result: Optional[str] = None
    steps: List[StepRecord] = []

class AuditManager:
    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = base_dir or RUNS_DIR
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.current_run: Optional[RunRecord] = None
        self.current_run_dir: Optional[Path] = None

    def start_run(self, goal: str) -> RunRecord:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        slug = re.sub(r"[^a-zA-Z0-9_-]", "_", goal[:30]).strip("_")
        run_id = f"{timestamp}_{slug}"
        self.current_run_dir = self.base_dir / run_id
        self.current_run_dir.mkdir(parents=True, exist_ok=True)
        (self.current_run_dir / "screenshots").mkdir(exist_ok=True)

        self.current_run = RunRecord(
            run_id=run_id,
            goal=goal,
            start_time=time.time(),
            steps=[],
        )
        self._save_state()
        return self.current_run

    def record_step(
        self,
        step_num: int,
        thought: str,
        action: str,
        params: Dict[str, Any],
        observation: str,
        success: bool = True,
        screenshot_b64: Optional[str] = None,
        llm_ms: Optional[float] = None,
        tool_ms: Optional[float] = None,
        duration_ms: Optional[float] = None,
        started_at: Optional[float] = None,
    ) -> None:
        if not self.current_run or not self.current_run_dir:
            return

        screenshot_file = None
        if screenshot_b64:
            filename = f"step_{step_num}_{action}.png"
            shot_path = self.current_run_dir / "screenshots" / filename
            try:
                with open(shot_path, "wb") as f:
                    f.write(base64.b64decode(screenshot_b64))
                screenshot_file = f"screenshots/{filename}"
            except Exception:
                pass

        step = StepRecord(
            step_num=step_num,
            thought=thought,
            action=action,
            params=params,
            observation=observation,
            success=success,
            screenshot_file=screenshot_file,
            timestamp=time.time(),
            started_at=started_at,
            duration_ms=duration_ms,
            llm_ms=llm_ms,
            tool_ms=tool_ms,
        )
        self.current_run.steps.append(step)
        self._save_state()

    def complete_run(self, result: str, status: str = "success") -> None:
        if not self.current_run:
            return
        self.current_run.end_time = time.time()
        self.current_run.status = status
        self.current_run.result = result
        self._save_state()

    def _save_state(self) -> None:
        if not self.current_run or not self.current_run_dir:
            return
        meta_file = self.current_run_dir / "run.json"
        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump(self.current_run.model_dump(), f, indent=2)

    def list_recent_runs(self, limit: int = 20) -> List[Dict[str, Any]]:
        runs = []
        if not self.base_dir.exists():
            return []
        for run_path in sorted(self.base_dir.iterdir(), reverse=True):
            if run_path.is_dir():
                meta_file = run_path / "run.json"
                if meta_file.exists():
                    try:
                        with open(meta_file, "r", encoding="utf-8") as f:
                            data = json.load(f)
                        runs.append(data)
                        if len(runs) >= limit:
                            break
                    except Exception:
                        pass
        return runs

    def get_run(self, run_id: str) -> Optional[Dict[str, Any]]:
        run_path = self.base_dir / run_id / "run.json"
        if run_path.exists():
            try:
                with open(run_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return None
        return None

    def backup_and_clear(self, backup_dir: Optional[Path] = None) -> Dict[str, Any]:
        """Backup all runs to ~/ai-memory/bro/backups/audit_backup_<timestamp>/ and clear audit history."""
        import shutil
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        if backup_dir is None:
            backup_root = Path.home() / "ai-memory" / "bro" / "backups"
            backup_dir = backup_root / f"audit_backup_{timestamp}"
        else:
            backup_dir = Path(backup_dir).expanduser()

        backup_dir.mkdir(parents=True, exist_ok=True)
        backed_up_count = 0

        if self.base_dir.exists():
            for item in list(self.base_dir.iterdir()):
                try:
                    if item.is_dir():
                        shutil.copytree(item, backup_dir / item.name, dirs_exist_ok=True)
                        shutil.rmtree(item)
                        backed_up_count += 1
                    elif item.is_file():
                        shutil.copy2(item, backup_dir / item.name)
                        item.unlink()
                except Exception:
                    pass

        self.current_run = None
        self.current_run_dir = None
        return {
            "status": "cleared",
            "backup_dir": str(backup_dir),
            "backed_up_runs": backed_up_count,
            "cleared_runs": backed_up_count,
        }

    def get_analytics(self) -> Dict[str, Any]:
        """Compute human-friendly analytics and actuator breakdown across past runs."""
        runs = self.list_recent_runs(limit=100)
        total_runs = len(runs)
        if total_runs == 0:
            return {
                "total_runs": 0,
                "success_count": 0,
                "failed_count": 0,
                "success_rate": 100.0,
                "avg_duration_sec": 0.0,
                "total_steps": 0,
                "avg_steps_per_run": 0.0,
                "fastest_duration_sec": 0.0,
                "longest_duration_sec": 0.0,
                "actuator_breakdown": {"desktop": 0, "browser": 0, "python": 0, "shell": 0, "macro": 0, "other": 0},
                "actuator_percentages": {"desktop": 0, "browser": 0, "python": 0, "shell": 0, "macro": 0, "other": 0},
                "recent_timeline": [],
            }

        success_count = sum(1 for r in runs if r.get("status") == "success")
        failed_count = sum(1 for r in runs if r.get("status") in ["failed", "timeout"])

        durations = []
        actuator_counts = {"desktop": 0, "browser": 0, "python": 0, "shell": 0, "macro": 0, "other": 0}
        total_steps = 0
        recent_timeline = []

        for r in runs:
            start = r.get("start_time")
            end = r.get("end_time")
            run_dur = round(end - start, 1) if (start and end and end >= start) else 0.0
            if run_dur > 0:
                durations.append(run_dur)

            steps = r.get("steps", [])
            total_steps += len(steps)

            for step in steps:
                act = step.get("action", "").lower()
                if "desktop" in act:
                    actuator_counts["desktop"] += 1
                elif "browser" in act:
                    actuator_counts["browser"] += 1
                elif "python" in act:
                    actuator_counts["python"] += 1
                elif "shell" in act or "bash" in act:
                    actuator_counts["shell"] += 1
                elif "macro" in act:
                    actuator_counts["macro"] += 1
                else:
                    actuator_counts["other"] += 1

            if len(recent_timeline) < 15:
                time_label = time.strftime("%H:%M:%S", time.localtime(start)) if start else "Unknown"
                recent_timeline.append({
                    "run_id": r.get("run_id", ""),
                    "goal": r.get("goal", ""),
                    "status": r.get("status", "unknown"),
                    "duration_sec": run_dur,
                    "step_count": len(steps),
                    "time_str": time_label,
                })

        avg_dur = round(sum(durations) / len(durations), 1) if durations else 0.0
        fastest_dur = min(durations) if durations else 0.0
        longest_dur = max(durations) if durations else 0.0
        success_rate = round((success_count / total_runs) * 100, 1) if total_runs > 0 else 100.0
        avg_steps = round(total_steps / total_runs, 1) if total_runs > 0 else 0.0

        total_actions = sum(actuator_counts.values())
        actuator_percentages = {
            k: round((v / total_actions) * 100, 1) if total_actions > 0 else 0.0
            for k, v in actuator_counts.items()
        }

        return {
            "total_runs": total_runs,
            "success_count": success_count,
            "failed_count": failed_count,
            "success_rate": success_rate,
            "avg_duration_sec": avg_dur,
            "total_steps": total_steps,
            "avg_steps_per_run": avg_steps,
            "fastest_duration_sec": fastest_dur,
            "longest_duration_sec": longest_dur,
            "actuator_breakdown": actuator_counts,
            "actuator_percentages": actuator_percentages,
            "recent_timeline": recent_timeline,
        }

    def export_run_markdown(self, run_id: str) -> str:
        """Export a full human-readable markdown report of an audit run."""
        data = self.get_run(run_id)
        if not data:
            return f"# Run Not Found: {run_id}"

        start_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(data.get("start_time", time.time())))
        dur = ""
        if data.get("start_time") and data.get("end_time"):
            dur = f"{round(data['end_time'] - data['start_time'], 1)} seconds"

        md = [
            f"# 🎞️ Mission Audit Report: {data.get('run_id')}",
            f"- **Goal**: {data.get('goal')}",
            f"- **Status**: `{data.get('status', 'unknown').upper()}`",
            f"- **Started**: {start_str}",
            f"- **Execution Duration**: {dur}",
            f"- **Total Steps**: {len(data.get('steps', []))}",
            "",
            "## Final Result / Outcome",
            f"> {data.get('result', 'No final outcome recorded.')}",
            "",
            "## Execution Steps Timeline",
        ]

        for s in data.get("steps", []):
            status_icon = "✔" if s.get("success") else "✖"
            md.append(f"### {status_icon} Step {s.get('step_num')}: `{s.get('action')}`")
            md.append(f"- **Thought**: *{s.get('thought')}*")
            md.append(f"- **Parameters**: `{json.dumps(s.get('params', {}))}`")
            md.append(f"- **Observation**: {s.get('observation', '')}")
            if s.get("screenshot_file"):
                md.append(f"- **Screenshot**: `{s.get('screenshot_file')}`")
            md.append("")

        return "\n".join(md)

    def export_run_json(self, run_id: str) -> str:
        """Export raw run data formatted as JSON."""
        data = self.get_run(run_id)
        if not data:
            return json.dumps({"error": f"Run not found: {run_id}"}, indent=2)
        return json.dumps(data, indent=2)

    def export_run_html(self, run_id: str) -> str:
        """Export a self-contained, standalone HTML executive report."""
        data = self.get_run(run_id)
        if not data:
            return f"<html><body><h1>Run Not Found: {html.escape(run_id)}</h1></body></html>"

        start_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(data.get("start_time", time.time())))
        dur = "N/A"
        if data.get("start_time") and data.get("end_time"):
            dur = f"{round(data['end_time'] - data['start_time'], 1)}s"

        goal_esc = html.escape(data.get("goal", "Mission"))
        status = data.get("status", "unknown").upper()
        status_color = "#00ff9d" if status == "SUCCESS" else ("#ff3860" if status in ("FAILED", "TIMEOUT") else "#00f0ff")
        result_esc = html.escape(data.get("result", "No final outcome recorded."))

        step_cards = []
        for s in data.get("steps", []):
            s_num = s.get("step_num", 0)
            act = html.escape(s.get("action", ""))
            thought = html.escape(s.get("thought", ""))
            obs = html.escape(s.get("observation", ""))
            params_str = html.escape(json.dumps(s.get("params", {}), indent=2))
            succ = s.get("success", True)
            step_badge_color = "#00ff9d" if succ else "#ff3860"
            step_status_text = "SUCCESS" if succ else "FAILED"

            shot_html = ""
            if s.get("screenshot_file"):
                shot_path = f"/api/history/{run_id}/{s.get('screenshot_file')}"
                shot_html = f'''
                <div style="margin-top: 0.75rem;">
                    <span style="font-size: 0.75rem; color: #94a3b8;">Screenshot Observation:</span>
                    <div style="margin-top: 0.35rem;">
                        <a href="{shot_path}" target="_blank" style="color: #00f0ff; text-decoration: underline; font-size: 0.82rem;">View Full 1080p Screenshot ({html.escape(s.get("screenshot_file"))})</a>
                    </div>
                </div>
                '''

            step_cards.append(f'''
            <div class="step-card">
                <div class="step-header">
                    <span class="step-num">STEP {s_num}</span>
                    <span class="step-action">{act}</span>
                    <span class="step-status" style="border-color: {step_badge_color}; color: {step_badge_color};">{step_status_text}</span>
                </div>
                <div class="step-body">
                    <div class="field-label">Thought & Planning</div>
                    <div class="field-value" style="font-style: italic;">"{thought}"</div>

                    <div class="field-label" style="margin-top: 0.75rem;">Action Parameters</div>
                    <pre><code>{params_str}</code></pre>

                    <div class="field-label" style="margin-top: 0.75rem;">Observation & Outcome</div>
                    <div class="field-value">{obs}</div>

                    {shot_html}
                </div>
            </div>
            ''')

        steps_html = "\n".join(step_cards) if step_cards else '<p style="color: #94a3b8;">No execution steps recorded for this mission.</p>'

        return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Bro Mission Report - {goal_esc}</title>
  <style>
    :root {{
      --bg: #050814;
      --card-bg: rgba(11, 19, 38, 0.9);
      --border: rgba(0, 240, 255, 0.22);
      --cyan: #00f0ff;
      --green: #00ff9d;
      --amber: #ffb703;
      --red: #ff3860;
      --text: #f1f5f9;
      --muted: #94a3b8;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
      background: var(--bg);
      color: var(--text);
      line-height: 1.55;
      padding: 2.5rem 1.5rem;
    }}
    .container {{ max-width: 920px; margin: 0 auto; }}
    .header {{
      background: linear-gradient(135deg, rgba(6, 14, 30, 0.95), rgba(3, 7, 18, 0.95));
      border: 1px solid var(--border);
      border-top: 2px solid var(--cyan);
      border-radius: 12px;
      padding: 1.75rem;
      margin-bottom: 1.75rem;
      box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
    }}
    .brand {{
      font-size: 0.75rem;
      font-weight: 700;
      letter-spacing: 2px;
      color: var(--cyan);
      font-family: monospace;
      margin-bottom: 0.5rem;
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }}
    .goal {{ font-size: 1.45rem; font-weight: 700; color: #ffffff; margin-bottom: 1rem; line-height: 1.3; }}
    .kpi-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
      gap: 0.85rem;
      margin-top: 1.25rem;
    }}
    .kpi-card {{
      background: rgba(4, 9, 20, 0.7);
      border: 1px solid rgba(255, 255, 255, 0.08);
      border-radius: 8px;
      padding: 0.85rem 1rem;
    }}
    .kpi-label {{ font-size: 0.72rem; color: var(--muted); text-transform: uppercase; letter-spacing: 1px; }}
    .kpi-val {{ font-size: 1.05rem; font-weight: 700; color: #ffffff; margin-top: 0.25rem; font-family: monospace; }}
    .outcome-box {{
      background: rgba(0, 240, 255, 0.08);
      border-left: 4px solid var(--cyan);
      border-radius: 6px;
      padding: 1.25rem;
      margin-bottom: 2rem;
    }}
    .outcome-title {{ font-size: 0.8rem; font-weight: 700; letter-spacing: 1px; color: var(--cyan); text-transform: uppercase; }}
    .outcome-text {{ font-size: 1.05rem; color: #ffffff; margin-top: 0.4rem; font-weight: 500; }}
    .section-title {{ font-size: 1.15rem; font-weight: 700; color: #ffffff; margin-bottom: 1rem; display: flex; align-items: center; gap: 0.5rem; }}
    .step-card {{
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 10px;
      margin-bottom: 1.25rem;
      overflow: hidden;
      box-shadow: 0 4px 16px rgba(0,0,0,0.3);
    }}
    .step-header {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 1rem;
      padding: 0.85rem 1.25rem;
      background: rgba(4, 9, 22, 0.8);
      border-bottom: 1px solid rgba(255, 255, 255, 0.06);
    }}
    .step-num {{ font-size: 0.75rem; font-weight: 700; font-family: monospace; color: var(--cyan); }}
    .step-action {{ font-size: 0.9rem; font-weight: 700; color: #ffffff; font-family: monospace; flex: 1; }}
    .step-status {{ font-size: 0.7rem; font-weight: 700; font-family: monospace; border: 1px solid; border-radius: 4px; padding: 0.15rem 0.5rem; }}
    .step-body {{ padding: 1.25rem; }}
    .field-label {{ font-size: 0.72rem; color: var(--muted); text-transform: uppercase; font-weight: 600; letter-spacing: 0.5px; }}
    .field-value {{ font-size: 0.92rem; color: #e2e8f0; margin-top: 0.25rem; }}
    pre {{
      background: #02040a;
      border: 1px solid rgba(0, 240, 255, 0.15);
      border-radius: 6px;
      padding: 0.75rem;
      margin-top: 0.35rem;
      overflow-x: auto;
      font-size: 0.82rem;
      color: #a6e3a1;
      font-family: "JetBrains Mono", Consolas, monospace;
    }}
    .footer {{
      margin-top: 3rem;
      text-align: center;
      font-size: 0.75rem;
      color: var(--muted);
      border-top: 1px solid rgba(255, 255, 255, 0.08);
      padding-top: 1.5rem;
    }}
    @media print {{
      body {{ background: #ffffff; color: #0f172a; padding: 1rem; }}
      .header, .step-card, .outcome-box, .kpi-card {{
        background: #ffffff !important;
        border: 1px solid #cbd5e1 !important;
        box-shadow: none !important;
        color: #0f172a !important;
      }}
      .goal, .step-action, .outcome-text {{ color: #0f172a !important; }}
      pre {{ background: #f8fafc !important; color: #0f172a !important; border: 1px solid #cbd5e1 !important; }}
    }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <div class="brand">⚡ BRO VARIANT 2 // MISSION AUDIT REPORT</div>
      <div class="goal">"{goal_esc}"</div>
      <div class="kpi-grid">
        <div class="kpi-card">
          <div class="kpi-label">Status</div>
          <div class="kpi-val" style="color: {status_color};">{status}</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-label">Duration</div>
          <div class="kpi-val">{dur}</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-label">Execution Steps</div>
          <div class="kpi-val">{len(data.get("steps", []))}</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-label">Timestamp</div>
          <div class="kpi-val" style="font-size: 0.85rem;">{start_str}</div>
        </div>
      </div>
    </div>

    <div class="outcome-box">
      <div class="outcome-title">Final Mission Outcome</div>
      <div class="outcome-text">{result_esc}</div>
    </div>

    <div class="section-title">
      <span>Execution Steps Timeline</span>
    </div>
    {steps_html}

    <div class="footer">
      Generated automatically by Bro Variant 3 Tactical Assistant • Run ID: {html.escape(run_id)}
    </div>
  </div>
</body>
</html>'''

