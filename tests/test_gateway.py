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
