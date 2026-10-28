"""Unit tests covering Phase 3 API, Security, and Gateway enhancements."""

import io
import json
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient

from bolsamajh.web.server import app, check_bind_security
from bolsamajh.documents.loader import Document, DocumentPage

client = TestClient(app)


def test_status_endpoint_does_not_leak_document_title():
    """Verify /api/status does not leak document title."""
    resp = client.get("/api/status")
    assert resp.status_code == 200
    data = resp.json()
    assert "document_title" not in data
    assert "document_loaded" in data
    assert "hotkeys" in data
    assert "dictation" in data["hotkeys"]


def test_command_endpoint_validation_and_errors(monkeypatch):
    """Verify /api/command returns 400 on empty inputs and 500 on LLM failure."""
    # 1. Empty command -> 400
    r1 = client.post("/api/command", json={"command": "", "text": "hello"})
    assert r1.status_code == 400
    assert "Command cannot be empty" in r1.json()["detail"]

    # 2. Empty text -> 400
    r2 = client.post("/api/command", json={"command": "translate", "text": "  "})
    assert r2.status_code == 400
    assert "Text cannot be empty" in r2.json()["detail"]

    # 3. LLM exception -> 500
    from bolsamajh.web.server import llm
    async def _fail_llm(*args, **kwargs):
        raise RuntimeError("LLM exploded")

    monkeypatch.setattr(llm, "generate", _fail_llm)
    r3 = client.post("/api/command", json={"command": "summarize", "text": "Long text"})
    assert r3.status_code == 500
    assert "Command processing failed" in r3.json()["detail"]


def test_transcriptions_text_format_and_params(monkeypatch):
    """Verify /v1/audio/transcriptions honors response_format='text' returning plain text, and passes language/prompt."""
    from bolsamajh.web.server import stt
    from bolsamajh.stt.base import TranscriptResult

    called_kwargs = {}
    def mock_transcribe(audio_bytes, **kwargs):
        called_kwargs.update(kwargs)
        return TranscriptResult(
            text="Transcribed voice prompt content",
            language="hi",
            confidence=0.98,
            duration_seconds=2.5,
            processing_seconds=0.1,
        )

    monkeypatch.setattr(stt, "transcribe", mock_transcribe)
    # Mock audio resampling to return valid WAV bytes
    monkeypatch.setattr("bolsamajh.web.server.resample_audio_to_16k_mono", lambda b: b)

    dummy_audio = b"RIFF" + b"\x00" * 100

    # Test text format
    resp_text = client.post(
        "/v1/audio/transcriptions",
        files={"file": ("test.wav", dummy_audio, "audio/wav")},
        data={"response_format": "text", "language": "hi", "prompt": "Special vocab hint"},
    )
    assert resp_text.status_code == 200
    assert "text/plain" in resp_text.headers.get("content-type", "")
    assert resp_text.text == "Transcribed voice prompt content"
    assert called_kwargs.get("language") == "hi"
    assert called_kwargs.get("prompt") == "Special vocab hint"

    # Test verbose_json format
    resp_vjson = client.post(
        "/v1/audio/transcriptions",
        files={"file": ("test.wav", dummy_audio, "audio/wav")},
        data={"response_format": "verbose_json"},
    )
    assert resp_vjson.status_code == 200
    vdata = resp_vjson.json()
    assert vdata["task"] == "transcribe"
    assert vdata["text"] == "Transcribed voice prompt content"
    assert "duration" in vdata


def test_transcriptions_corrupt_audio_returns_400(monkeypatch):
    """Verify corrupt audio cannot decode/resample and returns HTTP 400 rather than passing raw bytes to STT."""
    def _fail_resample(b):
        raise ValueError("Cannot decode corrupt MP3")

    monkeypatch.setattr("bolsamajh.web.server.resample_audio_to_16k_mono", _fail_resample)

    resp = client.post(
        "/v1/audio/transcriptions",
        files={"file": ("bad.mp3", b"garbage corrupt bytes", "audio/mp3")},
    )
    assert resp.status_code == 400
    assert "Unsupported audio" in resp.json()["detail"]


def test_per_session_retriever_isolation_and_delete(monkeypatch):
    """Verify different sessions maintain separate retrievers, and DELETE /api/document resets state."""
    from bolsamajh.web.server import get_retriever_for_session

    r1 = get_retriever_for_session("session-alice")
    r2 = get_retriever_for_session("session-bob")

    assert r1 is not r2

    doc_alice = Document(
        title="Alice Doc",
        source="alice.txt",
        pages=[DocumentPage(text="Alice policy details", page_number=1, source="alice.txt")],
        doc_type="txt",
    )
    r1.index_document(doc_alice)

    assert r1.is_loaded
    assert not r2.is_loaded

    # DELETE /api/document clears caller's session
    resp_del = client.delete("/api/document", headers={"X-Session-ID": "session-alice"})
    assert resp_del.status_code == 200
    assert resp_del.json()["success"] is True

    # Alice retriever is now cleared
    assert not r1.is_loaded


def test_security_middleware_host_allowlist():
    """Verify requests with untrusted Host header are rejected with 400."""
    resp = client.get("/api/status", headers={"Host": "malicious-phishing.com"})
    assert resp.status_code == 400
    assert "Invalid Host header" in resp.json()["detail"]

    # Allowed host works
    resp_ok = client.get("/api/status", headers={"Host": "localhost:8000"})
    assert resp_ok.status_code == 200


def test_security_middleware_origin_csrf():
    """Verify state-changing requests from untrusted origins are rejected with 403 when no API key is set."""
    resp = client.post(
        "/api/command",
        headers={"Origin": "http://evil-site.com"},
        json={"command": "test", "text": "test"},
    )
    assert resp.status_code == 403
    assert "Forbidden: untrusted origin" in resp.json()["detail"]


def test_check_bind_security_help_flag(monkeypatch):
    """Verify passing -h or --help does not trigger security exception."""
    monkeypatch.delenv("BOLSAMAJH_API_KEY", raising=False)
    monkeypatch.setattr("sys.argv", ["server.py", "-h"])
    check_bind_security()

    monkeypatch.setattr("sys.argv", ["server.py", "--help"])
    check_bind_security()


def test_realtime_websocket_events_and_origin():
    """Verify WebSocket realtime events: session.created, input_audio_buffer.committed."""
    with client.websocket_connect("/v1/realtime", headers={"Origin": "http://localhost:8000"}) as ws:
        # First message must be session.created
        created_msg = json.loads(ws.receive_text())
        assert created_msg["type"] == "session.created"

        # Commit empty audio
        ws.send_text(json.dumps({"type": "input_audio_buffer.commit"}))

        committed_msg = json.loads(ws.receive_text())
        assert committed_msg["type"] == "input_audio_buffer.committed"

        completed_msg = json.loads(ws.receive_text())
        assert completed_msg["type"] == "conversation.item.input_audio_transcription.completed"
        assert completed_msg["transcript"] == ""
