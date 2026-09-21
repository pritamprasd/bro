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
