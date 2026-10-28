"""Voice Activity Detection and Barge-In Monitor using Silero VAD.

Allows speech interruption (barge-in): when TTS is speaking and user begins talking,
audio playback is stopped immediately.

Adheres strictly to Tier 5 Requirements:
- Thread-safe VoiceActivityDetector with threading.Lock protecting model inference.
- Shared VAD instance support across the application.
- Measures echo-mute suppression window from the START OF PLAYBACK (via notify_playback_start()),
  not from monitor thread start.
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

# Shared global VoiceActivityDetector singleton for the application
_SHARED_VAD: Optional["VoiceActivityDetector"] = None
_SHARED_VAD_LOCK = threading.Lock()


def get_shared_vad(threshold: float = 0.5) -> "VoiceActivityDetector":
    """Get or create the single shared VoiceActivityDetector instance."""
    global _SHARED_VAD
    if _SHARED_VAD is None:
        with _SHARED_VAD_LOCK:
            if _SHARED_VAD is None:
                _SHARED_VAD = VoiceActivityDetector(threshold=threshold)
                _SHARED_VAD.preload()
    return _SHARED_VAD


class VoiceActivityDetector:
    """Silero VAD wrapper for fast, thread-safe voice activity detection."""

    def __init__(self, threshold: float = 0.5):
        self.threshold = threshold
        self._model = None
        self._lock = threading.Lock()

    def preload(self) -> None:
        """Preload Silero VAD model into memory at startup."""
        self._load_model()

    def _load_model(self):
        if self._model is not None:
            return
        with self._lock:
            if self._model is not None:
                return
            try:
                from silero_vad import load_silero_vad
                log.info("Preloading Silero VAD model...")
                self._model = load_silero_vad()
                log.info("Silero VAD model preloaded successfully.")
            except Exception as e:
                log.warning("Silero VAD model loading failed: %s", e)
                self._model = None

    def is_speech(self, audio_chunk: np.ndarray, sample_rate: int = 16000) -> bool:
        """Check if 16kHz float32 audio chunk contains speech (thread-safe)."""
        self._load_model()
        if self._model is None or len(audio_chunk) == 0:
            return False

        import torch

        # Silero VAD accepts 512, 1024, or 1536 samples at 16000 Hz
        if len(audio_chunk) < 512:
            audio_chunk = np.pad(audio_chunk, (0, 512 - len(audio_chunk)))
        elif len(audio_chunk) > 512:
            audio_chunk = audio_chunk[:512]

        tensor = torch.from_numpy(audio_chunk.astype(np.float32))
        with self._lock:
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
        vad: Optional[VoiceActivityDetector] = None,
        device_id: Optional[int | str] = None,
    ):
        self.on_barge_in = on_barge_in
        self.sample_rate = sample_rate
        self.headphone_mode = headphone_mode
        self.mute_ms = mute_ms
        self.device_id = device_id

        # In speaker mode, use higher threshold (0.80) to prevent speaker audio reflection
        vad_thresh = 0.50 if headphone_mode else 0.80
        if vad is not None:
            self.vad = vad
            self.vad.threshold = vad_thresh
        else:
            self.vad = VoiceActivityDetector(threshold=vad_thresh)
            self.vad.preload()

        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._playback_started: bool = False
        self._playback_start_time: float = 0.0

    @property
    def is_active(self) -> bool:
        """Return True if background microphone monitoring is currently active."""
        return self._running and (self._thread is not None and self._thread.is_alive())

    def notify_playback_start(self) -> None:
        """Notify the monitor that the first audio sample has started playing."""
        self._playback_started = True
        self._playback_start_time = time.time()
        log.debug("BargeInMonitor notified: playback started (echo suppression active for %.0f ms)", self.mute_ms)

    def start(self):
        """Start monitoring mic for speech."""
        if sd is None:
            log.warning("sounddevice is not available in this environment; skipping BargeInMonitor")
            return
        if self._running:
            return
        self._running = True
        self._playback_started = False
        self._playback_start_time = 0.0
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()

    def stop(self):
        """Stop monitoring."""
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=0.5)
        self._thread = None
        self._playback_started = False

    def _monitor_loop(self):
        """Read microphone chunks and test for speech activity."""
        chunk_size = 512
        consecutive_speech_chunks = 0
        required_chunks = 3 if self.headphone_mode else 6
        min_rms = 0.005 if self.headphone_mode else 0.020

        try:
            stream_kwargs = {
                "samplerate": self.sample_rate,
                "channels": 1,
                "dtype": "float32",
                "blocksize": chunk_size,
            }
            if self.device_id is not None:
                stream_kwargs["device"] = self.device_id

            with sd.InputStream(**stream_kwargs) as stream:
                while self._running:
                    data, overflowed = stream.read(chunk_size)
                    if overflowed:
                        continue
                    audio = data.flatten()

                    # 1. Echo suppression: Mute detection until playback starts, and for mute_ms after playback start
                    if not self._playback_started:
                        continue

                    elapsed_ms = (time.time() - self._playback_start_time) * 1000.0
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
            log.warning("BargeInMonitor microphone exception: %s", e)
        finally:
            self._running = False
