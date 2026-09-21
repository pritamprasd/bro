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
        self.enabled = config.enabled

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
        try:
            asyncio.run(self._generate_and_play(text))
        except Exception as e:
            # Non-fatal audio playback error
            pass

    async def _generate_and_play(self, text: str) -> None:
        import edge_tts

        with tempfile.NamedTemporaryFile("wb", suffix=".mp3", delete=False) as f:
            temp_path = f.name

        try:
            communicate = edge_tts.Communicate(text, self.voice, rate=self.rate, pitch=self.pitch)
            await communicate.save(temp_path)

            # Play using available Linux audio player (ffplay, aplay, or mpv)
            players = [
                ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", temp_path],
                ["mpv", "--no-video", "--really-quiet", temp_path],
                ["aplay", temp_path],
            ]

            played = False
            for cmd in players:
                try:
                    res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    if res.returncode == 0:
                        played = True
                        break
                except FileNotFoundError:
                    continue

        finally:
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception:
                    pass

    def _clean_for_speech(self, text: str) -> str:
        import re
        # Remove code blocks
        text = re.sub(r"```[\s\S]*?```", " Code snippet omitted. ", text)
        # Remove inline code
        text = re.sub(r"`.*?`", " ", text)
        # Remove markdown urls [title](url) -> title
        text = re.sub(r"\[(.*?)\]\(.*?\)", r"\1", text)
        # Remove headers #
        text = re.sub(r"#+\s*", "", text)
        # Remove bullet points
        text = re.sub(r"^[\s*-]+", "", text, flags=re.MULTILINE)
        return text.strip()
