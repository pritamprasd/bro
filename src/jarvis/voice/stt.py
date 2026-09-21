"""Speech-to-Text engine using faster-whisper with CUDA acceleration."""

import io
import os
import tempfile
import wave
from typing import Optional
from jarvis.config import VoiceConfig

class SpeechToText:
    def __init__(self, config: VoiceConfig):
        self.config = config
        self._model = None

    def _ensure_model(self):
        if self._model is None:
            from faster_whisper import WhisperModel
            device = self.config.device
            compute_type = self.config.compute_type
            try:
                self._model = WhisperModel(
                    self.config.whisper_model,
                    device=device,
                    compute_type=compute_type,
                )
            except Exception:
                # Fallback to CPU if CUDA initialization fails
                self._model = WhisperModel(
                    self.config.whisper_model,
                    device="cpu",
                    compute_type="int8",
                )

    def record_and_transcribe(self, duration_seconds: int = 5, sample_rate: int = 16000) -> str:
        """Record audio from default microphone and transcribe."""
        import numpy as np
        import sounddevice as sd

        self._ensure_model()

        # Record from microphone
        recording = sd.rec(
            int(duration_seconds * sample_rate),
            samplerate=sample_rate,
            channels=1,
            dtype="int16",
        )
        sd.wait()

        # Save to temporary WAV
        with tempfile.NamedTemporaryFile("wb", suffix=".wav", delete=False) as f:
            wav_path = f.name
            with wave.open(f, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(sample_rate)
                wf.writeframes(recording.tobytes())

        try:
            return self.transcribe_file(wav_path)
        finally:
            if os.path.exists(wav_path):
                try:
                    os.remove(wav_path)
                except Exception:
                    pass

    def transcribe_file(self, audio_path: str) -> str:
        """Transcribe an audio file."""
        self._ensure_model()
        segments, _ = self._model.transcribe(
            audio_path,
            beam_size=5,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=500),
        )
        text = " ".join([segment.text for segment in segments]).strip()
        return text
