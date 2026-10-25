"""Unit tests for FastAPI Web Server & OpenAI-compatible gateway."""

import pytest
from fastapi.testclient import TestClient
from bolsamajh.web.server import app, is_safe_external_url


client = TestClient(app)


def test_status_endpoint():
    resp = client.get("/api/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ready"
    assert "device" in data
    assert "stt" in data
    assert "tts" in data


import socket
from unittest.mock import patch

def test_ssrf_protection_helper():
    assert not is_safe_external_url("http://localhost:8000")
    assert not is_safe_external_url("http://127.0.0.1:11434")
    assert not is_safe_external_url("http://169.254.169.254/latest/meta-data")
    assert not is_safe_external_url("http://192.168.1.1/admin")
    assert not is_safe_external_url("http://10.0.0.1")
    assert not is_safe_external_url("ftp://example.com")
    # Public domain should be allowed — mock DNS lookup for offline-safe CI testing
    with patch("socket.getaddrinfo", return_value=[(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 0))]):
        assert is_safe_external_url("https://en.wikipedia.org/wiki/India")


def test_ssrf_endpoint_blocking():
    resp = client.post("/api/documents/url", json={"url": "http://127.0.0.1:8000/internal"})
    assert resp.status_code == 400
    assert "SSRF" in resp.json()["detail"]


def test_upload_file_too_large():
    # 26 MB dummy file
    large_data = b"0" * (26 * 1024 * 1024)
    resp = client.post(
        "/api/documents/upload",
        files={"file": ("huge.txt", large_data, "text/plain")}
    )
    assert resp.status_code == 413


def test_cors_headers():
    resp = client.options(
        "/api/status",
        headers={"Origin": "http://localhost:8000", "Access-Control-Request-Method": "GET"}
    )
    assert resp.status_code == 200
    assert resp.headers.get("access-control-allow-origin") == "http://localhost:8000"
    # Credentials should be false
    assert "access-control-allow-credentials" not in resp.headers or resp.headers.get("access-control-allow-credentials") == "false"


def test_audio_path_traversal_blocking():
    """Verify that path traversal attempts against /api/audio/{audio_file} are rejected with 4xx."""
    traversal_payloads = [
        "..%2f..%2fetc%2fpasswd",
        "..%2f..%2fWindows%2fwin.ini",
        "%2e%2e%2f%2e%2e%2fetc%2fpasswd",
        "/etc/passwd",
        "C:\\Windows\\win.ini",
        "..\\..\\Windows\\win.ini",
    ]
    for payload in traversal_payloads:
        resp = client.get(f"/api/audio/{payload}")
        assert resp.status_code in (400, 403, 404), f"Payload '{payload}' was not rejected: HTTP {resp.status_code}"


def test_gateway_auth_bearer_token(monkeypatch, fake_edge_tts):
    """Verify that /v1/* endpoints enforce Authorization: Bearer <BOLSAMAJH_API_KEY> when key is set."""
    monkeypatch.setenv("BOLSAMAJH_API_KEY", "super-secret-token-123")

    # 1. Missing header -> 401
    resp_no_auth = client.post(
        "/v1/audio/speech",
        json={"model": "tts-1", "input": "Hello", "voice": "swara"},
    )
    assert resp_no_auth.status_code == 401

    # 2. Invalid token -> 401
    resp_bad_auth = client.post(
        "/v1/audio/speech",
        headers={"Authorization": "Bearer wrong-token"},
        json={"model": "tts-1", "input": "Hello", "voice": "swara"},
    )
    assert resp_bad_auth.status_code == 401

    # 3. Valid token -> 200
    resp_ok = client.post(
        "/v1/audio/speech",
        headers={"Authorization": "Bearer super-secret-token-123"},
        json={"model": "tts-1", "input": "Testing auth", "voice": "swara"},
    )
    assert resp_ok.status_code == 200


def test_bind_security_check(monkeypatch):
    """Verify server refuses to bind to non-localhost without BOLSAMAJH_API_KEY."""
    from bolsamajh.web.server import check_bind_security

    monkeypatch.delenv("BOLSAMAJH_API_KEY", raising=False)

    # Binding to 127.0.0.1 without key is allowed
    check_bind_security(host="127.0.0.1")
    check_bind_security(host="localhost")

    # Binding to 0.0.0.0 without key must raise RuntimeError
    with pytest.raises(RuntimeError) as exc_info:
        check_bind_security(host="0.0.0.0")
    assert "Security Error" in str(exc_info.value)

    # Binding to 0.0.0.0 with key set is allowed
    monkeypatch.setenv("BOLSAMAJH_API_KEY", "prod-key-xyz")
    check_bind_security(host="0.0.0.0")


def test_background_task_tracking():
    """Verify asyncio tasks are tracked and discarded upon completion."""
    import asyncio
    from bolsamajh.web.server import _BACKGROUND_TASKS, track_task

    async def _run():
        async def dummy():
            await asyncio.sleep(0.01)

        task = asyncio.create_task(dummy())
        track_task(task)
        assert task in _BACKGROUND_TASKS
        await task
        # Allow callback to run
        await asyncio.sleep(0.01)
        assert task not in _BACKGROUND_TASKS

    asyncio.run(_run())

