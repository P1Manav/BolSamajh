"""Voice Activity Detection and Barge-In Monitor using Silero VAD.

Allows speech interruption (barge-in): when TTS is speaking and user begins talking,
audio playback is stopped immediately.

Adheres strictly to Tier 5 Requirements:
- Preloads Silero VAD model at initialization/startup rather than stalling inside monitor thread.
- Barge-in echo suppression: mutes detection for the first ~300 ms of playback.
- Configurable headphone mode:
  * In headphone mode (headphone_mode=True): standard threshold (0.50) and quick response (~100 ms).
  * In speaker mode (headphone_mode=False): elevated VAD threshold (0.80), longer sustained run (~200 ms),
    and RMS energy gate to suppress acoustic speaker echo and bleed.
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

    def preload(self) -> None:
        """Preload Silero VAD model into memory at startup."""
        self._load_model()

    def _load_model(self):
        if self._model is not None:
            return
        from silero_vad import load_silero_vad
        log.info("Preloading Silero VAD model...")
        self._model = load_silero_vad()
        log.info("Silero VAD model preloaded successfully.")

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

    def __init__(
        self,
        on_barge_in: Callable[[], None],
        sample_rate: int = 16000,
        headphone_mode: bool = False,
        mute_ms: float = 300.0,
    ):
        self.on_barge_in = on_barge_in
        self.sample_rate = sample_rate
        self.headphone_mode = headphone_mode
        self.mute_ms = mute_ms

        # In speaker mode, use higher threshold (0.80) to prevent speaker audio reflection
        vad_thresh = 0.50 if headphone_mode else 0.80
        self.vad = VoiceActivityDetector(threshold=vad_thresh)
        self.vad.preload()  # Preload Silero at startup, NOT inside monitor thread

        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._t_start: float = 0.0

    def start(self):
        """Start monitoring mic for speech."""
        if sd is None:
            log.warning("sounddevice is not available in this environment; skipping BargeInMonitor")
            return
        if self._running:
            return
        self._running = True
        self._t_start = time.time()
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
        # Longer sustained run in speaker mode to avoid echo triggers (~200ms vs ~100ms)
        required_chunks = 3 if self.headphone_mode else 6

        # Minimum RMS energy threshold in speaker mode to filter speaker bleed
        min_rms = 0.005 if self.headphone_mode else 0.020

        try:
            with sd.InputStream(samplerate=self.sample_rate, channels=1, dtype="float32", blocksize=chunk_size) as stream:
                while self._running:
                    data, overflowed = stream.read(chunk_size)
                    if overflowed:
                        continue
                    audio = data.flatten()

                    # 1. Mute detection for the first ~300 ms of playback
                    elapsed_ms = (time.time() - self._t_start) * 1000.0
                    if elapsed_ms < self.mute_ms:
                        continue

                    # 2. RMS energy check: ignore ambient speaker bleed below threshold
                    rms = float(np.sqrt(np.mean(audio ** 2))) if len(audio) > 0 else 0.0
                    if rms < min_rms:
                        consecutive_speech_chunks = max(0, consecutive_speech_chunks - 1)
                        continue

                    # 3. Silero VAD check
                    if self.vad.is_speech(audio, sample_rate=self.sample_rate):
                        consecutive_speech_chunks += 1
                        if consecutive_speech_chunks >= required_chunks:
                            log.info("Voice barge-in detected (sustained %d chunks, RMS=%.4f)! Halting TTS playback.",
                                     consecutive_speech_chunks, rms)
                            self.on_barge_in()
                            break
                    else:
                        consecutive_speech_chunks = max(0, consecutive_speech_chunks - 1)
        except Exception as e:
            log.debug("BargeInMonitor exception: %s", e)
        finally:
            self._running = False
