"""Audio capture utilities — mic recording via sounddevice."""

import io
import wave
import logging
import threading
import numpy as np
import sounddevice as sd

log = logging.getLogger(__name__)

# Audio settings
SAMPLE_RATE = 16000      # 16 kHz for Whisper
CHANNELS = 1             # Mono
DTYPE = "int16"          # 16-bit PCM


class MicRecorder:
    """Push-to-talk microphone recorder.

    Usage:
        recorder = MicRecorder()
        recorder.start()       # Begin recording
        wav_bytes = recorder.stop()  # Stop and get WAV bytes
    """

    def __init__(self, sample_rate: int = SAMPLE_RATE):
        self.sample_rate = sample_rate
        self._frames: list[np.ndarray] = []
        self._stream: sd.InputStream | None = None
        self._recording = False
        self._lock = threading.Lock()

    @property
    def is_recording(self) -> bool:
        return self._recording

    def start(self) -> None:
        """Start recording from default microphone."""
        with self._lock:
            if self._recording:
                return
            self._frames = []
            self._recording = True

        log.debug("Mic recording started (rate=%d)", self.sample_rate)

        def callback(indata, frames, time_info, status):
            if status:
                log.warning("Sounddevice status: %s", status)
            if self._recording:
                self._frames.append(indata.copy())

        self._stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=CHANNELS,
            dtype=DTYPE,
            callback=callback,
            blocksize=1024,
        )
        self._stream.start()

    def stop(self) -> bytes:
        """Stop recording and return WAV bytes."""
        with self._lock:
            self._recording = False

        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None

        if not self._frames:
            log.warning("No audio frames captured")
            return b""

        audio_data = np.concatenate(self._frames, axis=0)
        duration = len(audio_data) / self.sample_rate
        log.info("Recorded %.1f seconds of audio (%d samples)",
                 duration, len(audio_data))

        return self._to_wav_bytes(audio_data)

    def cancel(self) -> None:
        """Cancel recording immediately, discarding captured audio."""
        with self._lock:
            self._recording = False
            self._frames = []
        if self._stream is not None:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception:
                pass
            self._stream = None
        log.info("Mic recording cancelled.")

    def _to_wav_bytes(self, audio: np.ndarray) -> bytes:
        """Convert numpy audio to WAV bytes."""
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(2)  # 16-bit = 2 bytes
            wf.setframerate(self.sample_rate)
            wf.writeframes(audio.tobytes())
        return buf.getvalue()


def list_audio_devices() -> str:
    """List available audio input devices (for debugging)."""
    return str(sd.query_devices())
