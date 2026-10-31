"""Tests for BolSamajh Web Call WebSocket endpoint, sample document loader, and benchmark API."""

import json
from pathlib import Path
import pytest
from starlette.testclient import TestClient

from bolsamajh.web.server import app

client = TestClient(app, base_url="http://127.0.0.1:8000")


def test_api_benchmark_endpoint():
    """Verify /api/benchmark serves verified JSON metrics."""
    response = client.get("/api/benchmark")
    assert response.status_code == 200
    data = response.json()
    assert "real_speech" in data or "benchmark_version" in data
    if "real_speech" in data:
        assert "medium" in data["real_speech"] or "large-v3-turbo" in data["real_speech"]


def test_api_documents_sample_loading():
    """Verify loading bundled sample document sample_policy.pdf."""
    response = client.post("/api/documents/sample?name=sample_policy.pdf")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["filename"] == "sample_policy.pdf"
    assert data["chunks"] > 0


def test_api_documents_sample_not_found():
    """Verify requesting non-existent sample document returns 404."""
    response = client.post("/api/documents/sample?name=non_existent_doc_123.pdf")
    assert response.status_code == 404


def test_api_settings_update():
    """Verify updating script mode and headphone mode."""
    response = client.post(
        "/api/settings",
        json={"script": "devanagari", "headphone_mode": True},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["script"] == "devanagari"
    assert data["headphone_mode"] is True

    # Restore to natural
    client.post("/api/settings", json={"script": "natural", "headphone_mode": False})


def test_webcall_websocket_lifecycle():
    """Verify full-duplex Web Call WebSocket connection, ready message, and query flow."""
    with client.websocket_connect("/ws/call?lang=hinglish") as ws:
        # 1. Server emits ready message upon connection
        ready_msg = ws.receive_json()
        assert ready_msg["type"] == "ready"
        assert "session_id" in ready_msg

        # 2. Configure sample document and language
        ws.send_json({
            "type": "config",
            "language": "hinglish",
            "sample_doc": "sample_policy.pdf",
        })
        config_msg = ws.receive_json()
        assert config_msg["type"] == "configured"
        assert config_msg["document_loaded"] is True

        # 3. Process a text query over the call
        ws.send_json({
            "type": "process_query",
            "text": "What is the room rent limit?",
        })

        # Expect: transcript -> thinking state -> answer -> speaking state
        events = []
        for _ in range(10):
            try:
                msg = ws.receive_json()
                events.append(msg)
                if msg.get("type") == "answer":
                    assert len(msg.get("text", "")) > 0
                    assert len(msg.get("citations", [])) > 0
                    break
            except Exception:
                break

        types = [e.get("type") for e in events]
        assert "transcript" in types
        assert "thinking" in [e.get("state") for e in events if e.get("type") == "state"]
        assert "answer" in types


def test_webcall_barge_in_cancellation():
    """Verify barge-in message sends interrupted state and halts playback."""
    with client.websocket_connect("/ws/call?lang=hinglish") as ws:
        ready = ws.receive_json()
        assert ready["type"] == "ready"

        # Send barge-in event
        ws.send_json({
            "type": "barge_in",
            "generation_id": "test_gen_123",
        })
        barge_msg = ws.receive_json()
        assert barge_msg["type"] == "state"
        assert barge_msg["state"] == "interrupted"
