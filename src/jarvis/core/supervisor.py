"""Central Process Supervisor & Lifecycle Manager (Master ON / Kill-Switch)."""

import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
import psutil
from jarvis.config import JarvisConfig, load_config

PID_FILE = Path.home() / ".jarvis" / "supervisor.pid"

def get_lan_ip() -> str:
    """Find primary local LAN IPv4 address for remote/mobile access."""
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        s.close()

class Supervisor:
    def __init__(self, config: Optional[JarvisConfig] = None):
        self.config = config or load_config()
        self.pid_file = PID_FILE
        self.pid_file.parent.mkdir(parents=True, exist_ok=True)

    def is_running(self) -> bool:
        """Check if Jarvis supervisor or UI server is active."""
        if not self.pid_file.exists():
            return False
        try:
            with open(self.pid_file, "r") as f:
                data = json.load(f)
            main_pid = data.get("main_pid")
            if main_pid and psutil.pid_exists(main_pid):
                return True
        except Exception:
            pass
        return False

    def start(self) -> Dict[str, Any]:
        """Start all background components."""
        if self.is_running():
            return {"status": "already_running", "message": "Jarvis is already running."}

        pids: Dict[str, int] = {}
        python_bin = sys.executable

        # 1. Start Web UI Server (FastAPI + Uvicorn)
        cmd_ui = [
            python_bin,
            "-m", "uvicorn",
            "jarvis.ui.server:app",
            "--host", self.config.web_ui.host,
            "--port", str(self.config.web_ui.port),
            "--log-level", "warning",
        ]
        proc_ui = subprocess.Popen(cmd_ui, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
        pids["ui_server"] = proc_ui.pid

        # 2. Start Background Hotkey & Daemon Worker
        cmd_worker = [
            python_bin,
            "-m", "jarvis.core.worker",
        ]
        proc_worker = subprocess.Popen(cmd_worker, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
        pids["worker"] = proc_worker.pid

        lan_ip = get_lan_ip()
        web_url = f"http://localhost:{self.config.web_ui.port}"
        network_url = f"http://{lan_ip}:{self.config.web_ui.port}"
        state = {
            "main_pid": proc_ui.pid,
            "pids": pids,
            "start_time": time.time(),
            "web_url": web_url,
            "network_url": network_url,
            "host": self.config.web_ui.host,
            "port": self.config.web_ui.port,
        }
        with open(self.pid_file, "w") as f:
            json.dump(state, f)

        # Wait a moment for UI server to bind
        time.sleep(1)

        return {
            "status": "started",
            "web_url": web_url,
            "network_url": network_url,
            "pids": pids,
        }

    def stop(self) -> Dict[str, Any]:
        """Trigger Master Kill-Switch to terminate all running components."""
        terminated = []
        if self.pid_file.exists():
            try:
                with open(self.pid_file, "r") as f:
                    data = json.load(f)
                pids = data.get("pids", {})
                for name, pid in pids.items():
                    if psutil.pid_exists(pid):
                        try:
                            os.kill(pid, signal.SIGTERM)
                            terminated.append(f"{name} (PID {pid})")
                        except Exception:
                            pass
            except Exception:
                pass
            try:
                os.remove(self.pid_file)
            except Exception:
                pass

        # Cleanup any lingering uvicorn or jarvis processes
        for proc in psutil.process_iter(["pid", "cmdline"]):
            try:
                cmdline = " ".join(proc.info["cmdline"] or [])
                if "jarvis.ui.server:app" in cmdline or "jarvis.core.worker" in cmdline:
                    proc.terminate()
                    terminated.append(f"Cleaned PID {proc.pid}")
            except Exception:
                pass

        return {"status": "terminated", "processes": terminated}

    def status(self) -> Dict[str, Any]:
        running = self.is_running()
        info = {"running": running}
        if running and self.pid_file.exists():
            try:
                with open(self.pid_file, "r") as f:
                    info.update(json.load(f))
            except Exception:
                pass
        return info
