"""Voice Activity Detection and Barge-In Monitor using Silero VAD.

Allows speech interruption (barge-in): when TTS is speaking and user begins talking,
audio playback is stopped immediately.
"""

import time
import logging
import threading
from typing import Callable, Optional

import numpy as np

try:
    import sounddevice as sd
except Exception:
    sd = None

log = logging.getLogger(__name__)


class VoiceActivityDetector:
    """Silero VAD wrapper for fast voice activity detection."""

    def __init__(self, threshold: float = 0.5):
        self.threshold = threshold
        self._model = None

    def _load_model(self):
        if self._model is not None:
            return
        from silero_vad import load_silero_vad
        log.info("Loading Silero VAD model...")
        self._model = load_silero_vad()
        log.info("Silero VAD model loaded.")

    def is_speech(self, audio_chunk: np.ndarray, sample_rate: int = 16000) -> bool:
        """Check if 16kHz float32 audio chunk contains speech."""
        import torch

        self._load_model()
        if len(audio_chunk) == 0:
            return False

        # Silero VAD accepts 512, 1024, or 1536 samples at 16000 Hz
        if len(audio_chunk) < 512:
            audio_chunk = np.pad(audio_chunk, (0, 512 - len(audio_chunk)))
        elif len(audio_chunk) > 512:
            audio_chunk = audio_chunk[:512]

        tensor = torch.from_numpy(audio_chunk.astype(np.float32))
        with torch.no_grad():
            prob = self._model(tensor, sample_rate).item()
        return prob > self.threshold


class BargeInMonitor:
    """Monitors microphone while TTS is speaking and triggers callback on speech."""

    def __init__(self, on_barge_in: Callable[[], None], sample_rate: int = 16000):
        self.on_barge_in = on_barge_in
        self.sample_rate = sample_rate
        self.vad = VoiceActivityDetector()
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def start(self):
        """Start monitoring mic for speech."""
        if sd is None:
            log.warning("sounddevice is not available in this environment; skipping BargeInMonitor")
            return
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()

    def stop(self):
        """Stop monitoring."""
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=0.5)
        self._thread = None

    def _monitor_loop(self):
        """Read microphone chunks and test for speech activity."""
        chunk_size = 512
        consecutive_speech_chunks = 0
        required_chunks = 3  # ~100ms of sustained speech to avoid clicks/pops

        try:
            with sd.InputStream(samplerate=self.sample_rate, channels=1, dtype="float32", blocksize=chunk_size) as stream:
                while self._running:
                    data, overflowed = stream.read(chunk_size)
                    if overflowed:
                        continue
                    audio = data.flatten()
                    if self.vad.is_speech(audio, sample_rate=self.sample_rate):
                        consecutive_speech_chunks += 1
                        if consecutive_speech_chunks >= required_chunks:
                            log.info("Voice barge-in detected! Halting TTS playback.")
                            self.on_barge_in()
                            break
                    else:
                        consecutive_speech_chunks = max(0, consecutive_speech_chunks - 1)
        except Exception as e:
            log.debug("BargeInMonitor exception: %s", e)
        finally:
            self._running = False
