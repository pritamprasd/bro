"""Audit Trail & Session Recording for full action replay and filmstrips."""

import base64
import json
import os
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel

RUNS_DIR = Path.home() / ".jarvis" / "runs"

class StepRecord(BaseModel):
    step_num: int
    thought: str
    action: str
    params: Dict[str, Any]
    observation: str
    success: bool
    screenshot_file: Optional[str] = None
    timestamp: float

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

