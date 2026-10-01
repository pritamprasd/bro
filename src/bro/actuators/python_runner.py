"""Python Task Runner for executing background scripts, data processing, Telegram bot messaging, etc."""

import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, Optional
from bro.actuators.base import ActionResult, BaseActuator

class PythonRunner(BaseActuator):
    def __init__(self, default_timeout: int = 180):
        self.default_timeout = default_timeout
        self.python_bin = sys.executable

    def reset(self) -> None:
        pass

    def run_code(
        self,
        code: str,
        env_vars: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None,
        cwd: Optional[str] = None,
    ) -> ActionResult:
        """Execute a Python snippet in an isolated subprocess."""
        exec_timeout = timeout or self.default_timeout

        # Prepare environment
        run_env = os.environ.copy()
        if env_vars:
            run_env.update(env_vars)

        start_time = time.time()
        # Write to temporary file
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
            f.write(code)
            temp_path = f.name

        try:
            process = subprocess.run(
                [self.python_bin, temp_path],
                capture_output=True,
                text=True,
                timeout=exec_timeout,
                env=run_env,
                cwd=cwd or os.getcwd(),
            )
            elapsed = time.time() - start_time
            success = process.returncode == 0

            output_parts = []
            if process.stdout:
                output_parts.append(f"[STDOUT]\n{process.stdout.strip()}")
            if process.stderr:
                output_parts.append(f"[STDERR]\n{process.stderr.strip()}")

            full_output = "\n".join(output_parts) if output_parts else "(No output returned)"

            return ActionResult(
                success=success,
                output=full_output,
                error=process.stderr if not success else None,
                data={
                    "returncode": process.returncode,
                    "elapsed_sec": round(elapsed, 2),
                },
            )
        except subprocess.TimeoutExpired:
            return ActionResult(
                success=False,
                error=f"Python execution timed out after {exec_timeout} seconds.",
            )
        except Exception as e:
            return ActionResult(success=False, error=f"Python runner error: {e}")
        finally:
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception:
                    pass

    def run_file(
        self,
        script_path: str,
        args: Optional[list] = None,
        env_vars: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None,
    ) -> ActionResult:
        """Execute an existing Python script file."""
        path = Path(script_path).expanduser().resolve()
        if not path.exists():
            return ActionResult(success=False, error=f"Script file not found: {path}")

        cmd = [self.python_bin, str(path)]
        if args:
            cmd.extend([str(a) for a in args])

        run_env = os.environ.copy()
        if env_vars:
            run_env.update(env_vars)

        start_time = time.time()
        try:
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout or self.default_timeout,
                env=run_env,
            )
            elapsed = time.time() - start_time
            success = process.returncode == 0
            output = process.stdout if success else f"{process.stdout}\n{process.stderr}"
            return ActionResult(
                success=success,
                output=output.strip() or "(Executed with no output)",
                error=process.stderr if not success else None,
                data={"returncode": process.returncode, "elapsed_sec": round(elapsed, 2)},
            )
        except Exception as e:
            return ActionResult(success=False, error=f"Execution failed: {e}")
