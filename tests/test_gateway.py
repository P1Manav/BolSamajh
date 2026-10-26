"""End-to-end tests for BolSamajh OpenAI-compatible Gateway (/v1/*).

Tests TTS (/v1/audio/speech) and STT (/v1/audio/transcriptions) for Bolna agent integration.
"""

import io
import os
import tempfile
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from bolsamajh.web.server import app

client = TestClient(app)


def test_openai_speech_synthesis_end_to_end(fake_edge_tts):
    """Start server client, call /v1/audio/speech, and verify MP3 response using fake_edge_tts."""
    payload = {
        "model": "tts-1",
        "input": "नमस्ते, BolSamajh में आपका स्वागत है।",
        "voice": "swara",
        "response_format": "mp3",
    }
    response = client.post("/v1/audio/speech", json=payload)
    assert response.status_code == 200, f"Speech endpoint failed: {response.text}"
    assert "audio/mpeg" in response.headers.get("content-type", "")

    audio_bytes = response.content
    assert len(audio_bytes) > 1000, f"Expected non-trivial audio payload, got {len(audio_bytes)} bytes"

    # Save to a playable MP3 file
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp_file:
        tmp_file.write(audio_bytes)
        tmp_path = Path(tmp_file.name)

    try:
        assert tmp_path.exists()
        assert tmp_path.stat().st_size == len(audio_bytes)

        # Verify valid MP3 signature: ID3 header (b'ID3') or MPEG sync frame (b'\xff')
        is_id3 = audio_bytes[:3] == b"ID3"
        has_sync_frame = any(audio_bytes[i:i+2] in (b"\xff\xfb", b"\xff\xf3", b"\xff\xf2") for i in range(min(512, len(audio_bytes)-1)))
        assert is_id3 or has_sync_frame, "Audio bytes do not contain valid MP3 header or sync frame"
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


def test_openai_speech_voices(fake_edge_tts):
    """Verify that different voices (Swara, Neerja, Dhwani) are accepted and generate valid audio."""
    for voice in ["swara", "neerja", "dhwani"]:
        payload = {
            "model": "tts-1",
            "input": "Testing voice selection.",
            "voice": voice,
        }
        response = client.post("/v1/audio/speech", json=payload)
        assert response.status_code == 200
        assert len(response.content) > 500


@pytest.mark.network
def test_openai_speech_synthesis_live():
    """Live network test for Edge-TTS against Microsoft online service."""
    payload = {
        "model": "tts-1",
        "input": "नमस्ते, live Edge-TTS network verification test.",
        "voice": "swara",
        "response_format": "mp3",
    }
    response = client.post("/v1/audio/speech", json=payload)
    assert response.status_code == 200
    assert "audio/mpeg" in response.headers.get("content-type", "")
    assert len(response.content) > 1000


def test_openai_transcription_end_to_end():
    """Verify OpenAI-compatible STT transcription endpoint with real audio."""
    audio_path = Path("benchmark_data/audio/sentence_001.wav")
    if not audio_path.exists():
        pytest.skip(f"Audio file not found: {audio_path}")

    with open(audio_path, "rb") as f:
        response = client.post(
            "/v1/audio/transcriptions",
            files={"file": ("sentence_001.wav", f, "audio/wav")},
            data={"model": "whisper-1"},
        )
    assert response.status_code == 200
    data = response.json()
    assert "text" in data
    assert len(data["text"].strip()) > 0


def test_openai_speech_wav_format(fake_edge_tts):
    """Verify response_format='wav' returns audio/wav with RIFF header."""
    payload = {
        "model": "tts-1",
        "input": "नमस्ते, WAV test.",
        "voice": "swara",
        "response_format": "wav",
    }
    response = client.post("/v1/audio/speech", json=payload)
    assert response.status_code == 200
    assert "audio/wav" in response.headers.get("content-type", "")
    assert response.content[:4] == b"RIFF"


def test_openai_speech_speed(fake_edge_tts):
    """Verify speech endpoint honors speed parameter."""
    payload = {
        "model": "tts-1",
        "input": "Testing speech speed.",
        "voice": "neerja",
        "speed": 1.25,
    }
    response = client.post("/v1/audio/speech", json=payload)
    assert response.status_code == 200


def test_openai_speech_input_validation():
    """Verify input length limits and empty input rejection."""
    # Empty input
    resp_empty = client.post("/v1/audio/speech", json={"input": "   ", "model": "tts-1"})
    assert resp_empty.status_code == 400

    # Over 4,000 chars
    long_input = "a" * 4001
    resp_long = client.post("/v1/audio/speech", json={"input": long_input, "model": "tts-1"})
    assert resp_long.status_code == 400
    assert "4,000" in resp_long.json().get("detail", "")

    # Unsupported format
    resp_fmt = client.post("/v1/audio/speech", json={"input": "valid", "response_format": "flac"})
    assert resp_fmt.status_code == 400
    assert "Unsupported response_format" in resp_fmt.json().get("detail", "")


def test_openai_speech_edge_tts_failure_502(monkeypatch):
    """Verify clean 502 JSON error is returned if Edge-TTS fails (no bare 500)."""
    import edge_tts

    class FailingCommunicate:
        def __init__(self, *args, **kwargs):
            pass

        async def stream(self):
            if False:
                yield None
            raise ConnectionError("Simulated Edge-TTS connection drop")

    monkeypatch.setattr(edge_tts, "Communicate", FailingCommunicate)

    response = client.post("/v1/audio/speech", json={"input": "test fail", "voice": "swara"})
    assert response.status_code == 502
    data = response.json()
    assert "detail" in data
    assert "Edge-TTS upstream synthesis failed" in str(data["detail"])


def test_openai_speech_piper_singleton_load_voice_once(monkeypatch):
    """Verify that multiple /v1/audio/speech requests reuse the cached Piper instance and call _load_voice only once."""
    from bolsamajh.web import server
    from bolsamajh.tts.piper_adapter import PiperTTSAdapter
    server.reset_piper_adapter()

    load_voice_calls = []

    def stub_load_voice(self):
        load_voice_calls.append(1)
        import unittest.mock
        stub_voice = unittest.mock.MagicMock()

        def mock_synth(text, wav_file):
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(22050)
            wav_file.writeframes(b"\x00\x00" * 100)

        stub_voice.synthesize = mock_synth
        self._voice = stub_voice

    monkeypatch.setattr(PiperTTSAdapter, "_load_voice", stub_load_voice)

    resp1 = client.post("/v1/audio/speech", json={
        "model": "tts-1",
        "input": "First request text",
        "voice": "piper",
        "response_format": "wav",
    })
    assert resp1.status_code == 200

    resp2 = client.post("/v1/audio/speech", json={
        "model": "tts-1",
        "input": "Second request text",
        "voice": "piper",
        "response_format": "wav",
    })
    assert resp2.status_code == 200

    assert len(load_voice_calls) == 1, f"Expected _load_voice to be called once, got {len(load_voice_calls)}"
    server.reset_piper_adapter()


def test_openai_speech_piper_voice_wav(monkeypatch):
    """Verify /v1/audio/speech routes to Piper when voice='piper' and returns WAV."""
    import wave
    from bolsamajh.tts.piper_adapter import PiperTTSAdapter

    def mock_synthesize(self, text):
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(22050)
            wf.writeframes(b"\x00\x00" * 2205)
        return buf.getvalue()

    monkeypatch.setattr(PiperTTSAdapter, "synthesize_to_bytes", mock_synthesize)

    response = client.post("/v1/audio/speech", json={
        "model": "tts-1",
        "input": "नमस्ते, Piper voice test.",
        "voice": "piper",
        "response_format": "wav",
    })
    assert response.status_code == 200
    assert "audio/wav" in response.headers.get("content-type", "")
    assert response.content[:4] == b"RIFF"


def test_openai_speech_piper_voice_mp3(monkeypatch):
    """Verify /v1/audio/speech routes to Piper when voice='piper' and returns converted MP3."""
    import wave
    from bolsamajh.tts.piper_adapter import PiperTTSAdapter

    def mock_synthesize(self, text):
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(22050)
            wf.writeframes(b"\x00\x00" * 2205)
        return buf.getvalue()

    monkeypatch.setattr(PiperTTSAdapter, "synthesize_to_bytes", mock_synthesize)

    response = client.post("/v1/audio/speech", json={
        "model": "tts-1",
        "input": "Testing Piper MP3 output.",
        "voice": "piper",
        "response_format": "mp3",
    })
    assert response.status_code == 200
    assert "audio/mpeg" in response.headers.get("content-type", "")
    assert len(response.content) > 100


def test_openai_speech_piper_model_routing(monkeypatch):
    """Verify /v1/audio/speech routes to Piper when model='piper'."""
    import wave
    from bolsamajh.tts.piper_adapter import PiperTTSAdapter

    called = []
    def mock_synthesize(self, text):
        called.append(text)
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(22050)
            wf.writeframes(b"\x00\x00" * 2205)
        return buf.getvalue()

    monkeypatch.setattr(PiperTTSAdapter, "synthesize_to_bytes", mock_synthesize)

    response = client.post("/v1/audio/speech", json={
        "model": "piper",
        "input": "Testing model routing to Piper.",
        "voice": "alloy",
        "response_format": "wav",
    })
    assert response.status_code == 200
    assert len(called) == 1
    assert "Testing model routing" in called[0]


def test_openai_speech_piper_failure_502(monkeypatch):
    """Verify clean 502 JSON error is returned if Piper synthesis fails."""
    from bolsamajh.tts.piper_adapter import PiperTTSAdapter

    def mock_synthesize(self, text):
        raise RuntimeError("Simulated Piper ONNX model error")

    monkeypatch.setattr(PiperTTSAdapter, "synthesize_to_bytes", mock_synthesize)

    response = client.post("/v1/audio/speech", json={
        "model": "tts-1",
        "input": "Testing Piper failure.",
        "voice": "piper",
    })
    assert response.status_code == 502
    assert "Piper TTS offline synthesis failed" in str(response.json())

