"""Desktop Spotlight Bar Manager for X11."""

import json
import subprocess
import sys
import threading
from typing import Callable, Optional
from pynput import keyboard
from bro.config import SpotlightConfig

class SpotlightBar:
    def __init__(self, config: SpotlightConfig, task_callback: Optional[Callable[[str], None]] = None):
        self.config = config
        self.task_callback = task_callback
        self.listener: Optional[keyboard.GlobalHotKeys] = None
        self._proc: Optional[subprocess.Popen] = None
        self._lock = threading.Lock()

    def start_listener(self) -> None:
        """Start listening for global hotkey (e.g. <alt>+j)."""
        hotkey_map = {
            self.config.hotkey: self.show_spotlight,
        }
        self.listener = keyboard.GlobalHotKeys(hotkey_map)
        self.listener.daemon = True
        self.listener.start()

    def stop_listener(self) -> None:
        if self.listener:
            try:
                self.listener.stop()
            except Exception:
                pass
        if self._proc and self._proc.poll() is None:
            try:
                self._proc.terminate()
            except Exception:
                pass

    def show_spotlight(self) -> None:
        """Summon the floating spotlight search bar via isolated subprocess."""
        with self._lock:
            if self._proc and self._proc.poll() is None:
                return

            threading.Thread(target=self._launch_subprocess, daemon=True).start()

    def _launch_subprocess(self) -> None:
        try:
            cmd = [sys.executable, "-m", "bro.ui.spotlight_window"]
            self._proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            stdout, _ = self._proc.communicate()

            if stdout.strip():
                try:
                    data = json.loads(stdout.strip())
                    text = data.get("text", "")
                    active_window = data.get("active_window", "")
                    clipboard = data.get("clipboard", "")

                    full_goal = f"[Context: Active Window '{active_window}'] {text}"
                    if clipboard:
                        full_goal += f"\n[Clipboard]:\n{clipboard}"

                    if self.task_callback:
                        self.task_callback(full_goal)
                except Exception as e:
                    print(f"[Spotlight] Error handling input: {e}")

        except Exception as e:
            print(f"[Spotlight] Failed to launch spotlight window: {e}")
        finally:
            self._proc = None
