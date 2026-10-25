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
