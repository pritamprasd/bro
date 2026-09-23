"""Text-to-Speech engine using edge-tts and local audio playback."""

import asyncio
import os
import subprocess
import tempfile
import threading
from typing import Optional
from jarvis.config import VoiceConfig

class TextToSpeech:
    def __init__(self, config: VoiceConfig):
        self.config = config
        self.voice = config.tts_voice
        self.rate = config.tts_rate
        self.pitch = config.tts_pitch
        self.volume = getattr(config, "tts_volume", 100)
        self.enabled = config.enabled
        self._playback_lock = threading.Lock()
        self._current_player_process: Optional[subprocess.Popen] = None

    def stop(self) -> None:
        """Halt ongoing audio playback immediately (Barge-In)."""
        proc = self._current_player_process
        if proc and proc.poll() is None:
            try:
                proc.terminate()
                proc.kill()
            except Exception:
                pass
        self._current_player_process = None

    def speak(self, text: str, blocking: bool = False) -> None:
        """Synthesize and play audio response."""
        if not self.enabled or not text.strip():
            return

        # Clean markdown/code symbols from spoken text for natural flow
        clean_text = self._clean_for_speech(text)
        if not clean_text:
            return

        if blocking:
            self._speak_sync(clean_text)
        else:
            threading.Thread(target=self._speak_sync, args=(clean_text,), daemon=True).start()

    def _speak_sync(self, text: str) -> None:
        with self._playback_lock:
            try:
                try:
                    loop = asyncio.get_running_loop()
                except RuntimeError:
                    loop = None

                if loop and loop.is_running():
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                        future = executor.submit(asyncio.run, self._generate_and_play(text))
                        future.result()
                else:
                    asyncio.run(self._generate_and_play(text))
            except Exception as e:
                # Non-fatal audio playback error
                pass

    async def _generate_and_play(self, text: str) -> None:
        import edge_tts

        with tempfile.NamedTemporaryFile("wb", suffix=".mp3", delete=False) as f:
            temp_path = f.name

        try:
            vol_val = max(0, min(100, int(self.volume)))
            vol_str = f"{vol_val - 100:+d}%" if vol_val != 100 else "+0%"
            communicate = edge_tts.Communicate(text, self.voice, rate=self.rate, pitch=self.pitch, volume=vol_str)
            await communicate.save(temp_path)

            # Play using available Linux audio player (ffplay, aplay, or mpv) with volume control
            players = [
                ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", "-volume", str(vol_val), temp_path],
                ["mpv", "--no-video", "--really-quiet", f"--volume={vol_val}", temp_path],
                ["aplay", temp_path],
            ]

            played = False
            for cmd in players:
                try:
                    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    self._current_player_process = proc
                    proc.wait()
                    if proc.returncode in (0, -9, -15):  # 0 normal, -9/-15 killed by stop()
                        played = True
                        break
                except FileNotFoundError:
                    continue
                finally:
                    self._current_player_process = None

        finally:
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception:
                    pass

    def _clean_for_speech(self, text: str) -> str:
        import re
        if not text:
            return ""

        # 1. Replace multi-line code blocks
        text = re.sub(r"```[\s\S]*?```", " Code snippet omitted. ", text)

        # 2. Extract inline code (keep text inside backticks, e.g. `cat` -> cat)
        text = re.sub(r"`([^`]+)`", r"\1", text)

        # 3. Images and links: ![alt](url) -> alt, [title](url) -> title
        text = re.sub(r"!\[(.*?)\]\(.*?\)", r"\1", text)
        text = re.sub(r"\[(.*?)\]\(.*?\)", r"\1", text)

        # 4. Remove HTML tags but keep text: <b>text</b> -> text
        text = re.sub(r"<[^>]+>", " ", text)

        # 5. Bold & Italics: ***text***, **text**, *text*, __text__, _text_
        text = re.sub(r"(\*{3}|_{3})(.*?)\1", r"\2", text)
        text = re.sub(r"(\*{2}|_{2})(.*?)\1", r"\2", text)
        text = re.sub(r"(\*|_)(.*?)\1", r"\2", text)

        # 6. Strikethrough: ~~text~~ -> text
        text = re.sub(r"~~(.*?)~~", r"\1", text)

        # 7. Horizontal rules: ---, ***, ___
        text = re.sub(r"^\s*[-*_]{3,}\s*$", "", text, flags=re.MULTILINE)

        # 8. Headers: # Heading -> Heading
        text = re.sub(r"^\s*#{1,6}\s*", "", text, flags=re.MULTILINE)

        # 9. Blockquotes: > quote -> quote
        text = re.sub(r"^\s*>\s*", "", text, flags=re.MULTILINE)

        # 10. Table separator rows: |---|---|
        text = re.sub(r"^\s*\|?[-:| ]+\|?\s*$", "", text, flags=re.MULTILINE)
        # Table cell pipes: replace with space
        text = re.sub(r"\|", " ", text)

        # 11. Bullet points and numbered lists
        text = re.sub(r"^\s*[-*+]\s+", "", text, flags=re.MULTILINE)
        text = re.sub(r"^\s*\d+\.\s+", "", text, flags=re.MULTILINE)

        # 12. Remove any remaining stray formatting symbols (asterisks, underscores, backticks, tildes)
        text = re.sub(r"[*_`~]", "", text)

        # 13. Collapse multiple whitespace into a single space
        text = re.sub(r"\s+", " ", text)

        return text.strip()
