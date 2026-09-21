"""Two-Way Telegram Bot Remote Control Daemon using Long-Polling."""

import io
import json
import os
import threading
import time
from typing import Callable, Optional
import requests
from jarvis.actuators.desktop import DesktopActuator
from jarvis.config import JarvisConfig
from jarvis.security.vault import SecretVault
from jarvis.watchdogs.sentinel import HardwareSentinel

class TelegramRemoteDaemon:
    def __init__(self, config: JarvisConfig, task_runner_cb: Optional[Callable[[str], str]] = None, kill_cb: Optional[Callable[[], None]] = None):
        self.config = config
        self.vault = SecretVault()
        self.task_runner_cb = task_runner_cb
        self.kill_cb = kill_cb
        self.desktop = DesktopActuator()
        self.sentinel = HardwareSentinel(config.watchdogs.sentinel)
        self.running = False
        self._thread = None
        self.last_update_id = 0

    @property
    def token(self) -> Optional[str]:
        return self.vault.get_secret("telegram_bot_token")

    @property
    def authorized_chat_id(self) -> Optional[str]:
        return self.vault.get_secret("telegram_chat_id")

    def is_configured(self) -> bool:
        return bool(self.token and self.authorized_chat_id)

    def start(self) -> None:
        if not self.is_configured():
            print("[Telegram] Bot token or chat_id not configured in vault. Telegram remote is standby.")
            return

        self.running = True
        self._thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._thread.start()
        self.send_message("🤖 *Jarvis Remote Online*\nWorkstation is connected and listening for commands.")

    def stop(self) -> None:
        self.running = False

    def send_message(self, text: str) -> bool:
        if not self.token or not self.authorized_chat_id:
            return False
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        try:
            r = requests.post(url, json={"chat_id": self.authorized_chat_id, "text": text, "parse_mode": "Markdown"}, timeout=10)
            return r.status_code == 200
        except Exception:
            return False

    def send_photo(self, photo_bytes: bytes, caption: str = "") -> bool:
        if not self.token or not self.authorized_chat_id:
            return False
        url = f"https://api.telegram.org/bot{self.token}/sendPhoto"
        try:
            files = {"photo": ("screenshot.png", photo_bytes, "image/png")}
            data = {"chat_id": self.authorized_chat_id, "caption": caption}
            r = requests.post(url, data=data, files=files, timeout=15)
            return r.status_code == 200
        except Exception:
            return False

    def _poll_loop(self) -> None:
        url = f"https://api.telegram.org/bot{self.token}/getUpdates"
        while self.running:
            try:
                params = {"offset": self.last_update_id + 1, "timeout": 20}
                resp = requests.get(url, params=params, timeout=25)
                if resp.status_code == 200:
                    data = resp.json()
                    for update in data.get("result", []):
                        self.last_update_id = update["update_id"]
                        self._handle_update(update)
            except Exception:
                time.sleep(3)

    def _handle_update(self, update: dict) -> None:
        msg = update.get("message", {})
        chat_id = str(msg.get("chat", {}).get("id", ""))
        text = msg.get("text", "").strip()

        # Security check: only authorized user
        if chat_id != str(self.authorized_chat_id):
            return

        if text.startswith("/run "):
            goal = text[5:].strip()
            self.send_message(f"▶ *Executing:* `{goal}`")
            if self.task_runner_cb:
                threading.Thread(target=self._run_async_task, args=(goal,), daemon=True).start()

        elif text == "/status":
            m = self.sentinel.get_hardware_metrics()
            status_text = (
                f"🖥️ *Workstation Telemetry*\n"
                f"• CPU: {m['cpu_percent']}%\n"
                f"• RAM: {m['ram_used_gb']} / {m['ram_total_gb']} GB ({m['ram_percent']}%)\n"
                f"• GPU: {m['gpu_name']}\n"
                f"• GPU Temp: {m['gpu_temp']}°C\n"
                f"• VRAM: {m['vram_used_mb']} / {m['vram_total_mb']} MB\n"
                f"• Disk: {m['disk_percent']}% used"
            )
            self.send_message(status_text)

        elif text == "/screen":
            self.send_message("📸 Capturing X11 screen...")
            img, _ = self.desktop.capture_screenshot(max_dimension=1920)
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            self.send_photo(buf.getvalue(), caption="Current Desktop Display")

        elif text == "/kill":
            self.send_message("🛑 Initiating Master Kill Switch via Telegram...")
            if self.kill_cb:
                self.kill_cb()

        elif text == "/help" or text == "/start":
            self.send_message(
                "🤖 *Jarvis Telegram Commands:*\n"
                "• `/run <task>` - Run desktop, web, or python task\n"
                "• `/status` - Hardware & telemetry stats\n"
                "• `/screen` - Current desktop screenshot\n"
                "• `/kill` - Emergency process kill switch"
            )

    def _run_async_task(self, goal: str) -> None:
        try:
            result = self.task_runner_cb(goal)
            self.send_message(f"✔ *Task Finished:*\n{result[:1500]}")
        except Exception as e:
            self.send_message(f"✖ *Task Failed:* {e}")
