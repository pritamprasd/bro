"""Background Worker Process hosting Hotkey Listener, Telegram Daemon, and Watchdogs."""

import signal
import sys
import time
from jarvis.config import load_config
from jarvis.core.agent import JarvisAgent
from jarvis.remote.telegram_bot import TelegramRemoteDaemon
from jarvis.ui.spotlight import SpotlightBar
from jarvis.voice.tts import TextToSpeech
from jarvis.watchdogs.cron_engine import CronEngine
from jarvis.watchdogs.sentinel import HardwareSentinel

running = True

def handle_sigterm(signum, frame):
    global running
    running = False
    sys.exit(0)

def main():
    global running
    signal.signal(signal.SIGTERM, handle_sigterm)
    signal.signal(signal.SIGINT, handle_sigterm)

    config = load_config()
    tts = TextToSpeech(config.voice)

    # Helper to run a task
    def run_task_sync(goal: str) -> str:
        agent = JarvisAgent(config)
        return agent.run_task(goal)

    # 1. Hotkey Spotlight Bar
    spotlight = SpotlightBar(config.spotlight, task_callback=run_task_sync)
    spotlight.start_listener()

    # 2. Telegram Daemon
    telegram = TelegramRemoteDaemon(config, task_runner_cb=run_task_sync)
    telegram.start()

    # 3. Watchdogs
    sentinel = HardwareSentinel(config.watchdogs.sentinel, alert_callback=lambda msg: telegram.send_message(f"⚠️ {msg}"))
    cron = CronEngine(config.watchdogs.cron, briefing_callback=lambda b: (tts.speak(b), telegram.send_message(f"☀️ {b}")))

    while running:
        try:
            sentinel.check_and_alert()
            cron.check_schedule()
        except Exception:
            pass
        time.sleep(15)

if __name__ == "__main__":
    main()
