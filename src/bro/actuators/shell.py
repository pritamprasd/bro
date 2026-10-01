"""Local Shell execution actuator."""

import os
import subprocess
import time
from typing import Optional
from bro.actuators.base import ActionResult, BaseActuator

class ShellActuator(BaseActuator):
    def __init__(self, default_timeout: int = 60):
        self.default_timeout = default_timeout

    def reset(self) -> None:
        pass

    def run_command(self, command: str, cwd: Optional[str] = None, timeout: Optional[int] = None) -> ActionResult:
        """Run a bash shell command."""
        exec_timeout = timeout or self.default_timeout
        start_time = time.time()
        try:
            process = subprocess.run(
                command,
                shell=True,
                executable="/bin/bash",
                capture_output=True,
                text=True,
                timeout=exec_timeout,
                cwd=cwd or os.getcwd(),
            )
            elapsed = time.time() - start_time
            success = process.returncode == 0
            output_parts = []
            if process.stdout:
                output_parts.append(process.stdout.strip())
            if process.stderr:
                output_parts.append(f"[STDERR]\n{process.stderr.strip()}")

            return ActionResult(
                success=success,
                output="\n".join(output_parts) if output_parts else "(No output)",
                error=process.stderr if not success else None,
                data={"returncode": process.returncode, "elapsed_sec": round(elapsed, 2)},
            )
        except subprocess.TimeoutExpired:
            return ActionResult(
                success=False,
                error=f"Command timed out after {exec_timeout} seconds.",
            )
        except Exception as e:
            return ActionResult(success=False, error=f"Command failed: {e}")
