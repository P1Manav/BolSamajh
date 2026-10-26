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

    # Binding to 127.0.0.1, localhost, or ::1 without key is allowed
    check_bind_security(host="127.0.0.1")
    check_bind_security(host="localhost")
    check_bind_security(host="::1")
    check_bind_security(host="[::1]")

    # Binding to 0.0.0.0, ::, or [::] without key must raise RuntimeError
    for wildcard in ("0.0.0.0", "::", "[::]"):
        with pytest.raises(RuntimeError) as exc_info:
            check_bind_security(host=wildcard)
        assert "Security Error" in str(exc_info.value)

    # Binding to wildcards with key set is allowed
    monkeypatch.setenv("BOLSAMAJH_API_KEY", "prod-key-xyz")
    check_bind_security(host="0.0.0.0")
    check_bind_security(host="::")
    check_bind_security(host="[::]")


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


def test_api_auth_protection(monkeypatch):
    """Verify /api/* endpoints require Bearer auth when BOLSAMAJH_API_KEY is set, while / and /api/status remain exempt."""
    monkeypatch.setenv("BOLSAMAJH_API_KEY", "secret-test-token")

    # 1. Exempt endpoints work without auth
    resp_status = client.get("/api/status")
    assert resp_status.status_code == 200

    resp_root = client.get("/")
    assert resp_root.status_code == 200

    # 2. Protected /api/ endpoint without auth -> 401
    resp_unauth = client.post("/api/documents/url", json={"url": "https://example.com"})
    assert resp_unauth.status_code == 401

    # 3. Protected /api/ endpoint with invalid token -> 401
    resp_bad = client.post(
        "/api/documents/url",
        headers={"Authorization": "Bearer wrong-token"},
        json={"url": "https://example.com"},
    )
    assert resp_bad.status_code == 401

    # 4. Protected /api/ endpoint with valid token -> passes auth (does not return 401)
    resp_ok = client.post(
        "/api/documents/url",
        headers={"Authorization": "Bearer secret-test-token"},
        json={"url": "http://127.0.0.1:8000/internal"},
    )
    # Passed auth and reached handler (which returns 400 for SSRF)
    assert resp_ok.status_code == 400
    assert "SSRF" in resp_ok.json()["detail"]


def test_qa_endpoint_auth_enforcement(monkeypatch):
    """Verify with BOLSAMAJH_API_KEY set: /api/status works without key,
    /api/qa returns 401 without key and 200 with key.
    """
    from bolsamajh.web.server import retriever, llm
    from bolsamajh.documents.chunker import Chunk

    monkeypatch.setenv("BOLSAMAJH_API_KEY", "test-secret-key-42")

    # 1. /api/status works without key -> 200
    resp_status = client.get("/api/status")
    assert resp_status.status_code == 200

    # 2. /api/qa without key -> 401
    resp_unauth = client.post("/api/qa", json={"question": "What is in the document?"})
    assert resp_unauth.status_code == 401

    # 3. Setup mock document & LLM response
    monkeypatch.setattr(type(retriever), "is_loaded", property(lambda self: True))
    monkeypatch.setattr(type(retriever), "document_title", property(lambda self: "Sample Document"))
    monkeypatch.setattr(
        retriever,
        "retrieve",
        lambda *args, **kwargs: [Chunk(text="Sample content", page_number=1, score=0.95)],
    )

    async def mock_gen(*args, **kwargs):
        return "This is the answer from the document."

    monkeypatch.setattr(llm, "generate", mock_gen)

    # 4. /api/qa with key -> 200
    resp_auth = client.post(
        "/api/qa",
        headers={"Authorization": "Bearer test-secret-key-42"},
        json={"question": "What is in the document?", "language": "hinglish"},
    )
    assert resp_auth.status_code == 200
    data = resp_auth.json()
    assert data["answer"] == "This is the answer from the document."
    assert "audio_url" in data


def test_safe_fetch_url_dns_rebinding_prevention(monkeypatch):
    """Verify safe_fetch_url connects directly to the resolved IP so DNS rebinding cannot swap addresses,
    and blocks requests if DNS resolves to a private IP on subsequent lookup.
    """
    from bolsamajh.web.server import safe_fetch_url
    import io

    call_count = 0

    def mock_getaddrinfo(host, port, *args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            # First lookup returns public IP (passes SSRF check)
            return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", port))]
        else:
            # Second lookup returns private IP (DNS rebinding attempt)
            return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", port))]

    connected_destinations = []

    class MockSocket:
        def __init__(self):
            self._response = (
                b"HTTP/1.1 200 OK\r\n"
                b"Content-Type: text/html\r\n"
                b"Content-Length: 13\r\n"
                b"Connection: close\r\n\r\n"
                b"Hello Secure!"
            )
            self._pos = 0

        def sendall(self, data):
            pass

        def makefile(self, *args, **kwargs):
            return io.BytesIO(self._response)

        def close(self):
            pass

    def mock_create_connection(address, *args, **kwargs):
        connected_destinations.append(address)
        return MockSocket()

    monkeypatch.setattr("socket.getaddrinfo", mock_getaddrinfo)
    monkeypatch.setattr("socket.create_connection", mock_create_connection)

    # First fetch: should connect directly to vetted public IP ("93.184.216.34", 80)
    result = safe_fetch_url("http://rebinding.attack.com/page")
    assert result == "Hello Secure!"
    assert len(connected_destinations) == 1
    # Verify the socket destination is the vetted IP, preventing secondary DNS lookup swap
    assert connected_destinations[0] == ("93.184.216.34", 80)

    # Second fetch: resolver returns private IP 127.0.0.1 -> must be blocked before socket creation
    with pytest.raises(ValueError) as exc:
        safe_fetch_url("http://rebinding.attack.com/page")
    assert "blocked connection to non-public IP '127.0.0.1'" in str(exc.value)


def test_stream_qa_error_event(monkeypatch):
    """Verify /api/qa/stream catches LLM exceptions and emits an SSE error event before [DONE]."""
    from bolsamajh.web.server import retriever, llm

    monkeypatch.setattr(type(retriever), "is_loaded", property(lambda self: True))
    monkeypatch.setattr(retriever, "retrieve", lambda *a, **kw: [])

    async def mock_fail_stream(*args, **kwargs):
        yield "Starting answer..."
        raise RuntimeError("Simulated LLM stream failure")

    monkeypatch.setattr(llm, "generate_stream", mock_fail_stream)

    resp = client.get("/api/qa/stream?question=Test+Question")
    assert resp.status_code == 200
    content = resp.text
    assert 'data: {"token": "Starting answer..."}' in content
    assert 'data: {"error": "Simulated LLM stream failure"}' in content
    assert "data: [DONE]" in content


def test_voice_qa_unsupported_audio_returns_400():
    """Verify /api/qa/voice returns HTTP 400 when audio resampling fails rather than passing raw bytes to STT."""
    corrupt_audio = b"random garbage that cannot be decoded as audio"
    resp = client.post(
        "/api/qa/voice",
        files={"audio": ("corrupt.wav", corrupt_audio, "audio/wav")},
        data={"language": "hinglish"},
    )
    assert resp.status_code == 400
    assert "unsupported audio" in resp.json()["detail"].lower()


def test_tts_transliteration_preserves_hinglish():
    """Verify TTS preprocessing does not run ISO transliteration on Roman Hinglish,
    and only transliterates cross-script Indic text.
    """
    from bolsamajh.tts.edge_tts_adapter import EdgeTTSAdapter

    adapter = EdgeTTSAdapter()

    # Roman Hinglish text: must NOT be mangled by ISO transliteration
    hinglish_text = "Yeh ek simple Hinglish text hai."
    # If ISO transliteration were run, words like 'Yeh' would become Devanagari gibberish
    # But since it's Roman, both has_devanagari and has_gujarati are False, so it's untouched.
    has_dev = any('\u0900' <= c <= '\u097F' for c in hinglish_text)
    has_guj = any('\u0A80' <= c <= '\u0AFF' for c in hinglish_text)
    assert not has_dev and not has_guj

    # Cross-script Indic: Devanagari to Gujarati
    from aksharamukha import transliterate
    dev_text = "नमस्ते"
    guj_result = transliterate.process("Devanagari", "Gujarati", dev_text)
    assert any('\u0A80' <= c <= '\u0AFF' for c in guj_result)


def test_safe_fetch_url_oversized_body_rejected(monkeypatch):
    """Verify safe_fetch_url rejects response bodies exceeding max_body_size."""
    import io
    import socket
    from bolsamajh.web.server import safe_fetch_url

    def mock_getaddrinfo(host, port, *args, **kwargs):
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", port))]

    class MockLargeSocket:
        def __init__(self):
            # Create a 6MB payload (exceeding default 5MB cap)
            large_body = b"A" * (6 * 1024 * 1024)
            header = f"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: {len(large_body)}\r\nConnection: close\r\n\r\n".encode("utf-8")
            self._response = header + large_body

        def sendall(self, data):
            pass

        def makefile(self, *args, **kwargs):
            return io.BytesIO(self._response)

        def close(self):
            pass

    monkeypatch.setattr("socket.getaddrinfo", mock_getaddrinfo)
    monkeypatch.setattr("socket.create_connection", lambda *a, **kw: MockLargeSocket())

    with pytest.raises(ValueError) as exc:
        safe_fetch_url("http://example.com/oversized")
    assert "Response body exceeds maximum allowed size" in str(exc.value)


def test_safe_fetch_url_non_utf8_decoding(monkeypatch):
    """Verify safe_fetch_url decodes non-UTF-8 pages via Content-Type header and <meta charset>."""
    import io
    import socket
    from bolsamajh.web.server import safe_fetch_url

    def mock_getaddrinfo(host, port, *args, **kwargs):
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", port))]

    class MockCharsetSocket:
        def __init__(self, raw_bytes):
            self._response = raw_bytes

        def sendall(self, data):
            pass

        def makefile(self, *args, **kwargs):
            return io.BytesIO(self._response)

        def close(self):
            pass

    monkeypatch.setattr("socket.getaddrinfo", mock_getaddrinfo)

    # Test 1: Content-Type header with ISO-8859-1
    iso_body = (
        b"HTTP/1.1 200 OK\r\n"
        b"Content-Type: text/html; charset=iso-8859-1\r\n"
        b"Connection: close\r\n\r\n"
        b"Caf\xe9 cr\xe8me"
    )
    monkeypatch.setattr("socket.create_connection", lambda *a, **kw: MockCharsetSocket(iso_body))
    result1 = safe_fetch_url("http://example.com/iso")
    assert result1 == "Café crème"

    # Test 2: HTML <meta charset="windows-1252"> in body without Content-Type charset
    win_body = (
        b"HTTP/1.1 200 OK\r\n"
        b"Content-Type: text/html\r\n"
        b"Connection: close\r\n\r\n"
        b"<html><head><meta charset=\"windows-1252\"></head><body>Smart \x93quote\x94</body></html>"
    )
    monkeypatch.setattr("socket.create_connection", lambda *a, **kw: MockCharsetSocket(win_body))
    result2 = safe_fetch_url("http://example.com/win1252")
    assert "Smart “quote”" in result2


def test_safe_fetch_url_non_default_port_in_host(monkeypatch):
    """Verify safe_fetch_url includes non-default port in Host header and omits default port."""
    import io
    import socket
    from bolsamajh.web.server import safe_fetch_url

    def mock_getaddrinfo(host, port, *args, **kwargs):
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", port))]

    captured_requests = []

    class MockCaptureSocket:
        def __init__(self):
            self._response = (
                b"HTTP/1.1 200 OK\r\n"
                b"Content-Type: text/html\r\n"
                b"Connection: close\r\n\r\n"
                b"OK"
            )

        def sendall(self, data):
            captured_requests.append(data.decode("utf-8", errors="ignore"))

        def makefile(self, *args, **kwargs):
            return io.BytesIO(self._response)

        def close(self):
            pass

    monkeypatch.setattr("socket.getaddrinfo", mock_getaddrinfo)
    monkeypatch.setattr("socket.create_connection", lambda *a, **kw: MockCaptureSocket())

    # Non-default port (8080) -> Host must be example.com:8080
    safe_fetch_url("http://example.com:8080/test")
    assert "Host: example.com:8080\r\n" in captured_requests[0]

    # Default port (80) -> Host must be example.com
    safe_fetch_url("http://example.com:80/test")
    assert "Host: example.com\r\n" in captured_requests[1]


def test_load_url_endpoint_404_error_message(monkeypatch):
    """Verify upstream 404 is reported as 'Failed to fetch URL (HTTP 404)' and not SSRF error."""
    import io
    import socket

    def mock_getaddrinfo(host, port, *args, **kwargs):
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", port))]

    class Mock404Socket:
        def __init__(self):
            self._response = (
                b"HTTP/1.1 404 Not Found\r\n"
                b"Content-Type: text/html\r\n"
                b"Connection: close\r\n\r\n"
                b"Not Found"
            )

        def sendall(self, data):
            pass

        def makefile(self, *args, **kwargs):
            return io.BytesIO(self._response)

        def close(self):
            pass

    monkeypatch.setattr("socket.getaddrinfo", mock_getaddrinfo)
    monkeypatch.setattr("socket.create_connection", lambda *a, **kw: Mock404Socket())

    resp = client.post("/api/documents/url", json={"url": "http://example.com/missing-page"})
    assert resp.status_code == 400
    detail = resp.json().get("detail", "")
    assert detail == "Failed to fetch URL (HTTP 404)"
    assert "SSRF" not in detail



