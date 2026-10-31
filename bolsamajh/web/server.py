"""BolSamajh Web Server — FastAPI backend for browser web-call mode, SSE streaming, and OpenAI-compatible API.

Features:
- Audio resampler: Resamples arbitrary browser audio (48kHz/44.1kHz) to clean 16kHz mono PCM via PyAV AudioResampler.
- Thread pool execution: Offloads STT, indexing, and web fetching via asyncio.to_thread.
- Security: CORS restricted to localhost, SSRF protection blocking internal/private IP addresses, 25 MB streaming upload limit.
- Document handling: Preserves real document filenames, uses shared prompt-hardened QA engine.
- Latency & Streaming: Returns text immediately; provides Server-Sent Events (SSE) streaming; reports TTFA.
- Voice & Language: Maps Gujarati to gu-IN-DhwaniNeural, Hindi/Hinglish to hi-IN-SwaraNeural, English to en-IN-NeerjaNeural.
- Dynamic hardware status: Detects real GPU/CPU dynamically (no hardcoded strings).
- Sponsor Alignment: Exposes OpenAI-compatible /v1/audio/transcriptions and /v1/audio/speech endpoints for Bolna agent integration.
- Audio cache cleanup: Automatically sweeps expired temporary audio files.
"""

import asyncio
import base64
import codecs
import hmac
import io
import ipaddress
import logging
import os
import re
import socket
import sys

# Windows GUI / --noconsole safety
if sys.stdout is None or not hasattr(sys.stdout, "isatty"):

    class _SafeNull(io.StringIO):
        def isatty(self) -> bool:
            return False

        def flush(self) -> None:
            pass

        def write(self, s: str) -> int:
            return len(s)

    sys.stdout = _SafeNull()
if sys.stderr is None or not hasattr(sys.stderr, "isatty"):
    sys.stderr = sys.stdout
import tempfile
import threading
import time
import uuid
import wave
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator, List, Optional
from urllib.parse import unquote, urljoin, urlparse

import numpy as np
from dotenv import load_dotenv
from fastapi import (
    FastAPI,
    File,
    Form,
    HTTPException,
    Query,
    Request,
    UploadFile,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import (
    FileResponse,
    HTMLResponse,
    JSONResponse,
    PlainTextResponse,
    StreamingResponse,
)
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

load_dotenv()

from bolsamajh import __version__
from bolsamajh.config import AppConfig, load_config
from bolsamajh.documents.loader import load_document, load_webpage
from bolsamajh.documents.retriever import DocumentRetriever
from bolsamajh.llm.factory import create_llm_adapter
from bolsamajh.llm.fallback import FallbackLLMAdapter
from bolsamajh.prompts import _LANG_INSTRUCTIONS, _SYSTEM_PROMPT
from bolsamajh.stt.faster_whisper_stt import FasterWhisperSTT
from bolsamajh.tts.factory import create_tts_adapter

log = logging.getLogger("bolsamajh.web")

# Track strong references to background asyncio tasks to prevent premature garbage collection
_BACKGROUND_TASKS: set[asyncio.Task] = set()

# Module-level cached PiperTTSAdapter instance (lazy, thread-safe)
_piper_adapter_instance = None
_piper_adapter_lock = threading.Lock()


def get_piper_adapter(model_path: str = ""):
    """Lazy, thread-safe singleton cache for PiperTTSAdapter."""
    global _piper_adapter_instance
    if _piper_adapter_instance is None:
        with _piper_adapter_lock:
            if _piper_adapter_instance is None:
                from bolsamajh.tts.piper_adapter import PiperTTSAdapter

                _piper_adapter_instance = PiperTTSAdapter(model_path=model_path)
    return _piper_adapter_instance


def reset_piper_adapter() -> None:
    """Reset module-level cached PiperTTSAdapter instance (used in tests)."""
    global _piper_adapter_instance
    with _piper_adapter_lock:
        _piper_adapter_instance = None


class HTTPFetchError(Exception):
    """Raised when upstream server returns HTTP 4xx or 5xx."""

    def __init__(self, status_code: int, reason: str = ""):
        self.status_code = status_code
        self.reason = reason
        super().__init__(f"Failed to fetch URL (HTTP {status_code})")


def track_task(task: asyncio.Task) -> asyncio.Task:
    """Store strong reference to background task until it completes."""
    _BACKGROUND_TASKS.add(task)
    task.add_done_callback(_BACKGROUND_TASKS.discard)
    return task


def get_local_ip() -> str:
    """Detect local LAN IP for mobile/Android PWA companion connection."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def check_bind_security(host: Optional[str] = None) -> None:
    """Refuse to start if server binds to public addresses without an API key set.
    Supports loopback (127.0.0.1/localhost/::1) and private local network addresses.
    """
    api_key = os.getenv("BOLSAMAJH_API_KEY", "").strip()
    if api_key:
        return

    # If -h or --help was passed, let argparse display help without raising security error
    if "-h" in sys.argv or "--help" in sys.argv:
        return

    allow_lan = os.getenv("BOLSAMAJH_ALLOW_LAN", "0").strip().lower() in ("1", "true", "yes")

    target_host = (
        host or os.getenv("BOLSAMAJH_HOST") or os.getenv("UVICORN_HOST") or os.getenv("HOST")
    )
    if not target_host:
        for i, arg in enumerate(sys.argv):
            if arg == "--host" and i + 1 < len(sys.argv):
                target_host = sys.argv[i + 1]
                break
            elif arg.startswith("--host="):
                target_host = arg.split("=", 1)[1]
                break

    if target_host:
        clean = target_host.strip().lower()
        if clean in ("127.0.0.1", "localhost", "::1", "[::1]"):
            return
        if allow_lan:
            try:
                ip = ipaddress.ip_address(clean.strip("[]"))
                if ip.is_private and not ip.is_unspecified:
                    return
            except ValueError:
                pass
        raise RuntimeError(
            f"Security Error: Server configured to bind to '{target_host}' without BOLSAMAJH_API_KEY set. "
            f"Binding to non-loopback addresses exposes the gateway publicly. "
            f"Either set BOLSAMAJH_API_KEY or bind strictly to 127.0.0.1."
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: perform bind security check on startup, cancel tasks on shutdown."""
    check_bind_security()
    if not os.getenv("GOOGLE_AI_API_KEY"):
        log.warning(
            "GOOGLE_AI_API_KEY not set; Gemini cloud fallback disabled. Running local Ollama only."
        )
    yield
    for task in list(_BACKGROUND_TASKS):
        task.cancel()


app = FastAPI(
    title="BolSamajh Voice AI API",
    description="Multilingual Hinglish Voice Assistant, Document Intelligence & OpenAI-compatible Voice Gateway",
    version=__version__,
    lifespan=lifespan,
)

ALLOWED_HOSTS: set[str] = {
    "localhost",
    "127.0.0.1",
    "::1",
    "[::1]",
    "testserver",
}
if os.getenv("BOLSAMAJH_HOST"):
    ALLOWED_HOSTS.add(os.getenv("BOLSAMAJH_HOST").strip().lower())
if os.getenv("BOLSAMAJH_ALLOWED_HOSTS"):
    for h in os.getenv("BOLSAMAJH_ALLOWED_HOSTS").split(","):
        if h.strip():
            ALLOWED_HOSTS.add(h.strip().lower())


def _is_allowed_host(host_name: str) -> bool:
    """Validate host header against allowlist and private network addresses for mobile access."""
    if host_name in ALLOWED_HOSTS:
        return True
    try:
        ip = ipaddress.ip_address(host_name)
        if ip.is_private or ip.is_loopback:
            return True
    except ValueError:
        pass
    return False


# Security Middleware: Host header allowlist, Bearer auth, and Origin/CSRF validation
@app.middleware("http")
async def security_middleware(request: Request, call_next):
    # 1. Host header validation
    raw_host = request.headers.get("host", "").strip()
    if raw_host:
        host_name = raw_host.split(":")[0].strip().lower()
        if raw_host.startswith("["):
            bracket_end = raw_host.find("]")
            if bracket_end != -1:
                host_name = raw_host[: bracket_end + 1].lower()
        if not _is_allowed_host(host_name):
            return JSONResponse(
                status_code=400,
                content={"detail": f"Invalid Host header: '{raw_host}'"},
            )

    # 2. Bearer token authentication when BOLSAMAJH_API_KEY is configured
    expected_key = os.getenv("BOLSAMAJH_API_KEY", "").strip()
    path = request.url.path

    if expected_key:
        is_exempt = (
            path == "/"
            or path.startswith("/static")
            or path == "/api/status"
            or path in ("/manifest.json", "/sw.js", "/favicon.ico")
        )
        if not is_exempt and (path.startswith("/api/") or path.startswith("/v1/")):
            auth_header = request.headers.get("authorization", "")
            scheme, _, token = auth_header.partition(" ")
            token = token.strip()
            if (
                scheme.lower() != "bearer"
                or not token
                or not hmac.compare_digest(token, expected_key)
            ):
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Unauthorized: invalid or missing Bearer token"},
                    headers={"WWW-Authenticate": "Bearer"},
                )
    else:
        # When no API key is configured, enforce Origin / CSRF check on state-changing requests
        if request.method in ("POST", "PUT", "DELETE", "PATCH"):
            origin = request.headers.get("origin")
            if origin:
                parsed_origin = urlparse(origin)
                orig_host = (parsed_origin.hostname or "").lower()
                if orig_host and orig_host not in ALLOWED_HOSTS:
                    return JSONResponse(
                        status_code=403,
                        content={"detail": f"Forbidden: untrusted origin '{origin}'"},
                    )

    response = await call_next(request)

    # Ensure session cookie is attached if not present
    if "bolsamajh_session_id" not in request.cookies:
        sid = request.headers.get("x-session-id") or uuid.uuid4().hex
        response.set_cookie("bolsamajh_session_id", sid, httponly=True, samesite="lax")

    return response


# Restrict CORS to localhost with no credentials (SSRF / CSRF hardening)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:3000",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


def _resolve_static_dir() -> Path:
    """Resolve static directory safely in both standard Python and PyInstaller frozen builds."""
    if getattr(sys, "frozen", False):
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            cand = Path(meipass) / "bolsamajh" / "web" / "static"
            if cand.exists():
                return cand
        exe_dir = Path(sys.executable).parent
        cand = exe_dir / "_internal" / "bolsamajh" / "web" / "static"
        if cand.exists():
            return cand
        cand = exe_dir / "bolsamajh" / "web" / "static"
        if cand.exists():
            return cand
    cand = Path(__file__).parent / "static"
    if cand.exists():
        return cand
    # Fallback to repo root if run from elsewhere
    repo_cand = Path(__file__).resolve().parent.parent.parent / "bolsamajh" / "web" / "static"
    if repo_cand.exists():
        return repo_cand
    return cand


STATIC_DIR = _resolve_static_dir()
AUDIO_CACHE_DIR = Path(tempfile.gettempdir()) / "bolsamajh_web_audio"
AUDIO_CACHE_DIR.mkdir(parents=True, exist_ok=True)
MAX_UPLOAD_SIZE = 25 * 1024 * 1024  # 25 MB

# Global shared state
config: AppConfig = load_config()

stt = FasterWhisperSTT(
    model_size=config.stt.model_size,
    device=config.stt.device,
    compute_type=config.stt.compute_type,
    language=config.stt.language,
)
retriever = DocumentRetriever(
    embedding_model=config.doc_qa.embedding_model,
    chunk_size=config.doc_qa.chunk_size,
    chunk_overlap=config.doc_qa.chunk_overlap,
    refusal_threshold=config.doc_qa.refusal_threshold,
)


def render_audio_atomically(target_path: Path, audio_bytes: bytes) -> bool:
    """Atomically write audio data to a temp file and rename to avoid serving partial reads."""
    temp_path = target_path.parent / f"{target_path.stem}.tmp"
    try:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        temp_path.write_bytes(audio_bytes)
        temp_path.replace(target_path)
        return True
    except Exception as e:
        log.warning("Atomic audio write failed: %s", e)
        if temp_path.exists():
            try:
                temp_path.unlink()
            except Exception:
                pass
        return False


# Per-session document retriever registry
_SESSION_RETRIEVERS: dict[str, tuple[float, DocumentRetriever]] = {
    "default": (time.time(), retriever)
}
_SESSION_LOCK = threading.Lock()


def get_session_id(request: Request) -> str:
    """Extract session ID from request headers or cookies."""
    sid = request.headers.get("x-session-id") or request.cookies.get("bolsamajh_session_id")
    if sid and sid.strip():
        return sid.strip()
    return "default"


def get_retriever_for_session(session_id: str) -> DocumentRetriever:
    """Retrieve or instantiate a DocumentRetriever for a specific session."""
    now = time.time()
    with _SESSION_LOCK:
        if len(_SESSION_RETRIEVERS) > 100:
            stale = [
                s
                for s, (t, _) in _SESSION_RETRIEVERS.items()
                if s != "default" and (now - t) > 7200
            ]
            for s in stale:
                _SESSION_RETRIEVERS.pop(s, None)

        if session_id in _SESSION_RETRIEVERS:
            _, r = _SESSION_RETRIEVERS[session_id]
            _SESSION_RETRIEVERS[session_id] = (now, r)
            return r

        new_retriever = DocumentRetriever(
            embedding_model=config.doc_qa.embedding_model,
            chunk_size=config.doc_qa.chunk_size,
            chunk_overlap=config.doc_qa.chunk_overlap,
            refusal_threshold=config.doc_qa.refusal_threshold,
        )
        _SESSION_RETRIEVERS[session_id] = (now, new_retriever)
        return new_retriever


tts = create_tts_adapter(config)
llm = create_llm_adapter(config)


# --- Helper Functions ---


def clean_old_audio_cache(max_age_seconds: int = 1800) -> None:
    """Clean audio files in cache older than max_age_seconds (30 minutes)."""
    now = time.time()
    try:
        for f in AUDIO_CACHE_DIR.iterdir():
            if f.is_file() and (now - f.stat().st_mtime) > max_age_seconds:
                try:
                    f.unlink()
                except Exception:
                    pass
    except Exception as e:
        log.debug("Audio cache cleanup warning: %s", e)


def is_safe_ip(ip_str: str) -> bool:
    """Validate that an IP is not private, loopback, link-local, reserved, multicast, or mapped."""
    try:
        ip = ipaddress.ip_address(ip_str)
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
            return False
        if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped:
            mapped = ip.ipv4_mapped
            if (
                mapped.is_private
                or mapped.is_loopback
                or mapped.is_link_local
                or mapped.is_reserved
                or mapped.is_multicast
            ):
                return False
        return True
    except Exception:
        return False


def is_safe_external_url(url: str) -> bool:
    """SSRF protection: verify URL points to a legitimate external public address."""
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return False
        hostname = parsed.hostname
        if not hostname:
            return False
        if hostname.lower() in ("localhost", "127.0.0.1", "::1", "0.0.0.0", "169.254.169.254"):
            return False

        # Resolve hostname to check for private or loopback IP ranges
        addr_infos = socket.getaddrinfo(hostname, None)
        for addr in addr_infos:
            ip_str = addr[4][0]
            if not is_safe_ip(ip_str):
                return False
        return True
    except Exception:
        return False


def detect_charset(content_type_header: str, raw_bytes: bytes) -> str:
    """Detect text encoding from Content-Type header or HTML <meta charset>, falling back to UTF-8."""
    if content_type_header:
        m = re.search(r"charset=['\"]?([a-zA-Z0-9_\-]+)", content_type_header, re.IGNORECASE)
        if m:
            candidate = m.group(1).strip()
            try:
                codecs.lookup(candidate)
                return candidate
            except LookupError:
                pass

    head = raw_bytes[:4096]
    m = re.search(rb'<meta[^>]+charset=[\'"]?([a-zA-Z0-9_\-]+)', head, re.IGNORECASE)
    if m:
        try:
            candidate = m.group(1).decode("ascii", errors="ignore").strip()
            codecs.lookup(candidate)
            return candidate
        except (LookupError, UnicodeDecodeError):
            pass

    m2 = re.search(
        rb'<meta[^>]+http-equiv=[\'"]?content-type[\'"]?[^>]+content=[\'"][^;]*;\s*charset=([a-zA-Z0-9_\-]+)',
        head,
        re.IGNORECASE,
    )
    if m2:
        try:
            candidate = m2.group(1).decode("ascii", errors="ignore").strip()
            codecs.lookup(candidate)
            return candidate
        except (LookupError, UnicodeDecodeError):
            pass

    return "utf-8"


def safe_fetch_url(
    url: str,
    max_redirects: int = 3,
    timeout: float = 10.0,
    max_body_size: int = 5 * 1024 * 1024,
) -> str:
    """Fetch URL safely: resolves hostname to IP, verifies IP is public/safe against SSRF,
    connects socket directly to the vetted IP (preserving Host header and TLS SNI) to prevent
    DNS rebinding, enforces body size cap while reading, auto-detects charset, and validates redirect hops.
    """
    import http.client
    import ssl

    current_url = url
    for _ in range(max_redirects + 1):
        parsed = urlparse(current_url)
        if parsed.scheme not in ("http", "https"):
            raise ValueError(f"SSRF protection: forbidden scheme '{parsed.scheme}'")
        hostname = parsed.hostname
        if not hostname or hostname.lower() in (
            "localhost",
            "127.0.0.1",
            "::1",
            "0.0.0.0",
            "169.254.169.254",
        ):
            raise ValueError(f"SSRF protection: forbidden host '{hostname}'")

        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        try:
            addr_infos = socket.getaddrinfo(hostname, port, proto=socket.IPPROTO_TCP)
        except Exception as e:
            raise ValueError(f"SSRF protection: could not resolve host '{hostname}': {e}")

        vetted_ip = None
        for addr in addr_infos:
            ip_str = addr[4][0]
            if not is_safe_ip(ip_str):
                raise ValueError(f"SSRF protection: blocked connection to non-public IP '{ip_str}'")
            if vetted_ip is None:
                vetted_ip = ip_str

        if not vetted_ip:
            raise ValueError(
                f"SSRF protection: no valid IP addresses resolved for host '{hostname}'"
            )

        # Connect socket directly to vetted IP address to eliminate DNS rebinding risks
        sock = socket.create_connection((vetted_ip, port), timeout=timeout)
        try:
            if parsed.scheme == "https":
                ctx = ssl.create_default_context()
                sock = ctx.wrap_socket(sock, server_hostname=hostname)

            path = parsed.path or "/"
            if parsed.query:
                path += f"?{parsed.query}"

            # Include port in Host header when non-default
            is_default_port = (parsed.scheme == "https" and port == 443) or (
                parsed.scheme == "http" and port == 80
            )
            host_header = hostname if is_default_port else f"{hostname}:{port}"

            req_msg = (
                f"GET {path} HTTP/1.1\r\n"
                f"Host: {host_header}\r\n"
                f"User-Agent: BolSamajh-DocLoader/1.0\r\n"
                f"Accept-Encoding: gzip, deflate\r\n"
                f"Connection: close\r\n\r\n"
            )
            sock.sendall(req_msg.encode("utf-8"))

            resp = http.client.HTTPResponse(sock)
            resp.begin()

            if resp.status in (301, 302, 303, 307, 308):
                location = resp.getheader("location")
                if not location:
                    raise ValueError("SSRF protection: redirect missing Location header")
                current_url = urljoin(current_url, location)
                continue

            if resp.status < 200 or resp.status >= 400:
                raise HTTPFetchError(resp.status, resp.reason)

            encoding = resp.getheader("content-encoding", "").lower()
            decompressor = None
            if encoding == "gzip":
                import zlib

                decompressor = zlib.decompressobj(wbits=16 + zlib.MAX_WBITS)
            elif encoding == "deflate":
                import zlib

                decompressor = zlib.decompressobj()

            # Stream response body chunk-by-chunk and enforce size caps on both compressed input
            # and decompressed output as chunks arrive to prevent gzip/deflate bombs.
            decompressed_chunks = []
            total_decompressed = 0
            raw_read = 0
            chunk_size = 65536

            while True:
                chunk = resp.read(chunk_size)
                if not chunk:
                    break
                raw_read += len(chunk)
                if raw_read > max_body_size:
                    raise ValueError(
                        f"Response body exceeds maximum allowed size of {max_body_size // (1024 * 1024)} MB"
                    )

                if decompressor is not None:
                    decompressed = decompressor.decompress(chunk)
                    if decompressed:
                        total_decompressed += len(decompressed)
                        if total_decompressed > max_body_size:
                            raise ValueError(
                                f"Decompressed response body exceeds maximum allowed size of {max_body_size // (1024 * 1024)} MB"
                            )
                        decompressed_chunks.append(decompressed)
                else:
                    decompressed_chunks.append(chunk)

            if decompressor is not None:
                tail = decompressor.flush()
                if tail:
                    total_decompressed += len(tail)
                    if total_decompressed > max_body_size:
                        raise ValueError(
                            f"Decompressed response body exceeds maximum allowed size of {max_body_size // (1024 * 1024)} MB"
                        )
                    decompressed_chunks.append(tail)

            body_bytes = b"".join(decompressed_chunks)

            charset = detect_charset(resp.getheader("content-type", ""), body_bytes)
            try:
                return body_bytes.decode(charset)
            except (UnicodeDecodeError, LookupError):
                return body_bytes.decode("utf-8", errors="replace")
        finally:
            sock.close()

    raise ValueError(f"SSRF protection: exceeded maximum redirect hops ({max_redirects})")


async def stream_upload_to_file(
    file: UploadFile, dest_path: Path, max_size: int = MAX_UPLOAD_SIZE
) -> int:
    """Stream an upload directly to a destination file, enforcing max_size in real time without buffering in memory."""
    total_bytes = 0
    chunk_size = 64 * 1024  # 64 KB
    try:
        with open(dest_path, "wb") as out_f:
            while True:
                chunk = await file.read(chunk_size)
                if not chunk:
                    break
                total_bytes += len(chunk)
                if total_bytes > max_size:
                    raise HTTPException(
                        status_code=413,
                        detail=f"File exceeds maximum upload size of {max_size // (1024 * 1024)} MB.",
                    )
                out_f.write(chunk)
    except Exception:
        if dest_path.exists():
            try:
                dest_path.unlink()
            except Exception:
                pass
        raise
    return total_bytes


async def stream_upload_bytes(file: UploadFile, max_size: int = MAX_UPLOAD_SIZE) -> bytes:
    """Stream an upload into memory, enforcing max_size in real time to prevent memory exhaustion."""
    chunks = []
    total_bytes = 0
    chunk_size = 64 * 1024  # 64 KB
    while True:
        chunk = await file.read(chunk_size)
        if not chunk:
            break
        total_bytes += len(chunk)
        if total_bytes > max_size:
            raise HTTPException(
                status_code=413,
                detail=f"File exceeds maximum upload size of {max_size // (1024 * 1024)} MB.",
            )
        chunks.append(chunk)
    return b"".join(chunks)


def resample_audio_to_16k_mono(audio_bytes: bytes) -> bytes:
    """Decode and resample arbitrary browser audio (e.g. 48kHz WebM/WAV) to 16kHz mono 16-bit PCM."""
    import av
    import av.audio.resampler

    container = av.open(io.BytesIO(audio_bytes))
    if not container.streams.audio:
        raise ValueError("No audio stream found in submitted audio data")

    audio_stream = container.streams.audio[0]
    resampler = av.audio.resampler.AudioResampler(
        format="s16",
        layout="mono",
        rate=16000,
    )

    wav_buf = io.BytesIO()
    with wave.open(wav_buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16000)

        for frame in container.decode(audio_stream):
            resampled_frames = resampler.resample(frame)
            if resampled_frames:
                for rf in resampled_frames:
                    wf.writeframes(rf.to_ndarray().tobytes())

    return wav_buf.getvalue()


def convert_wav_to_mp3(wav_bytes: bytes) -> bytes:
    """Encode 16-bit PCM WAV to MP3 using PyAV."""
    import av

    in_container = av.open(io.BytesIO(wav_bytes), "r")
    if not in_container.streams.audio:
        raise ValueError("No audio stream found in WAV data for MP3 conversion")
    in_stream = in_container.streams.audio[0]

    out_buf = io.BytesIO()
    out_container = av.open(out_buf, "w", format="mp3")
    out_stream = out_container.add_stream("libmp3lame", rate=in_stream.rate or 22050)
    out_stream.layout = "mono"

    for frame in in_container.decode(in_stream):
        for packet in out_stream.encode(frame):
            out_container.mux(packet)
    for packet in out_stream.encode(None):
        out_container.mux(packet)
    out_container.close()
    return out_buf.getvalue()


# --- Request & Response schemas ---


class URLDocRequest(BaseModel):
    url: str


class QuestionRequest(BaseModel):
    question: str
    language: str = "hinglish"


class CommandRequest(BaseModel):
    text: str
    command: str


class CitationModel(BaseModel):
    citation: str
    text: str
    score: float


class QAResponse(BaseModel):
    question: str
    answer: str
    elapsed_sec: float
    citations: List[CitationModel]
    audio_url: Optional[str] = None


class OpenAISpeechRequest(BaseModel):
    model: str = "tts-1"
    input: str
    voice: str = "alloy"
    response_format: str = "mp3"
    speed: float = 1.0


# --- API Endpoints ---

# Cache for live LLM readiness checks (60 second TTL to avoid network calls in /api/status)
_STATUS_LIVE_CHECK_CACHE: tuple[float, bool] = (0.0, False)


async def check_llm_ready_cached(ttl_seconds: float = 60.0) -> bool:
    """Cached live LLM check with 60-second TTL to eliminate repeated network calls."""
    global _STATUS_LIVE_CHECK_CACHE
    now = time.time()
    last_time, last_result = _STATUS_LIVE_CHECK_CACHE
    if now - last_time < ttl_seconds:
        return last_result

    # If Google AI is active but no key configured, report false without network call
    if config.llm.engine == "google_ai" and not os.getenv("GOOGLE_AI_API_KEY"):
        _STATUS_LIVE_CHECK_CACHE = (now, False)
        return False

    try:
        ready = await llm.is_available()
    except Exception:
        ready = False
    _STATUS_LIVE_CHECK_CACHE = (now, ready)
    return ready


# Explicit voice mapping for OpenAI /v1/audio/speech endpoint (no text heuristics)
VOICE_MAP = {
    "swara": "hi-IN-SwaraNeural",
    "hi-in-swaraneural": "hi-IN-SwaraNeural",
    "hi": "hi-IN-SwaraNeural",
    "hindi": "hi-IN-SwaraNeural",
    "neerja": "en-IN-NeerjaNeural",
    "en-in-neerjaneural": "en-IN-NeerjaNeural",
    "en": "en-IN-NeerjaNeural",
    "english": "en-IN-NeerjaNeural",
    "alloy": "en-IN-NeerjaNeural",
    "echo": "en-IN-NeerjaNeural",
    "fable": "en-IN-NeerjaNeural",
    "onyx": "en-IN-NeerjaNeural",
    "nova": "en-IN-NeerjaNeural",
    "shimmer": "en-IN-NeerjaNeural",
    "dhwani": "gu-IN-DhwaniNeural",
    "gu-in-dhwanineural": "gu-IN-DhwaniNeural",
    "gu": "gu-IN-DhwaniNeural",
    "gujarati": "gu-IN-DhwaniNeural",
    "piper": "piper",
    "piper-pratham": "piper",
    "hi_in-pratham-medium": "piper",
}


# --- API Endpoints ---


@app.get("/api/status")
async def get_status(request: Request):
    """Return system health and hardware without leaking loaded document title."""
    clean_old_audio_cache()
    session_id = get_session_id(request)
    session_retriever = get_retriever_for_session(session_id)

    # Detect hardware name
    gpu_name = "CPU (int8)"
    if config.stt.device == "cuda":
        try:
            import torch

            if torch.cuda.is_available():
                gpu_name = torch.cuda.get_device_name(0)
            else:
                gpu_name = "CUDA GPU"
        except Exception:
            gpu_name = "CUDA GPU"

    # Fast configuration check without network calls
    llm_configured = (
        bool(os.getenv("GOOGLE_AI_API_KEY")) if config.llm.engine == "google_ai" else True
    )
    llm_ready = await check_llm_ready_cached(ttl_seconds=60.0)

    llm_fallback_msg = "LLM fallback unavailable"
    if isinstance(llm, FallbackLLMAdapter):
        llm_fallback_msg = llm.fallback_status
    elif config.llm.engine == "google_ai" and not os.getenv("GOOGLE_AI_API_KEY"):
        llm_fallback_msg = "LLM fallback unavailable"
    elif config.llm.engine == "ollama" and not config.llm.auto_fallback:
        llm_fallback_msg = "disabled"
    elif getattr(llm, "disabled", False):
        llm_fallback_msg = "LLM fallback unavailable"

    return {
        "status": "ready",
        "device": gpu_name,
        "stt": stt.name,
        "llm": llm.name,
        "llm_ready": llm_ready,
        "llm_configured": llm_configured,
        "llm_fallback": llm_fallback_msg,
        "tts": tts.name,
        "document_loaded": session_retriever.is_loaded,
        "refusal_threshold": session_retriever.refusal_threshold,
        "local_ip": get_local_ip(),
        "port": getattr(config.web, "port", 8000),
        "script": getattr(config.dictation, "script", "natural"),
        "hotkeys": {
            "dictation": getattr(config.hotkeys, "dictation", "alt+shift+space"),
            "voice_command": getattr(config.hotkeys, "voice_command", "alt+shift+c"),
            "doc_qa": getattr(config.hotkeys, "doc_qa", "alt+shift+a"),
            "doc_load": getattr(config.hotkeys, "doc_load", "alt+shift+d"),
        },
    }


@app.delete("/api/document")
async def delete_document_endpoint(request: Request):
    """Clear active loaded document from memory for the caller's session."""
    session_id = get_session_id(request)
    with _SESSION_LOCK:
        if session_id in _SESSION_RETRIEVERS:
            _, r = _SESSION_RETRIEVERS[session_id]
            r.clear()
            if session_id != "default":
                _SESSION_RETRIEVERS.pop(session_id, None)
        else:
            retriever.clear()
    return {"success": True, "message": "Document cleared for session"}


@app.post("/api/documents/upload")
async def upload_document_endpoint(request: Request, file: UploadFile = File(...)):
    """Upload and index a document with streaming size enforcement, session isolation, and real filename preservation."""
    session_id = get_session_id(request)
    session_retriever = get_retriever_for_session(session_id)

    suffix = Path(file.filename or "doc.tmp").suffix.lower()
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp_path = Path(tmp.name)

    try:
        # Stream directly to disk enforcing MAX_UPLOAD_SIZE without full buffering in RAM
        await stream_upload_to_file(file, tmp_path, MAX_UPLOAD_SIZE)

        # Load document on background thread
        doc = await asyncio.to_thread(load_document, str(tmp_path))

        # Preserve the real user filename rather than temp path
        real_title = Path(file.filename).stem if file.filename else "Document"
        doc.title = real_title
        doc.source = file.filename or "Uploaded Document"
        for p in doc.pages:
            p.source = file.filename or "Uploaded Document"

        # Index document on thread pool for this specific session
        chunks = await asyncio.to_thread(session_retriever.index_document, doc)

        return {
            "success": True,
            "title": doc.title,
            "pages": doc.page_count,
            "chunks": chunks,
            "filename": file.filename,
        }
    except HTTPException:
        raise
    except Exception as e:
        log.error("Failed to upload document: %s", e)
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        if tmp_path.exists():
            try:
                tmp_path.unlink()
            except Exception:
                pass


@app.post("/api/documents/url")
async def load_url_endpoint(request: Request, req: URLDocRequest):
    """Fetch and index a webpage URL with strict SSRF validation and redirect protection."""
    session_id = get_session_id(request)
    session_retriever = get_retriever_for_session(session_id)

    try:
        html_content = await asyncio.to_thread(safe_fetch_url, req.url)
    except HTTPFetchError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to fetch URL (HTTP {e.status_code})",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Forbidden URL (SSRF protection): {e}",
        )
    except Exception as e:
        log.error("Failed to fetch URL: %s", e)
        raise HTTPException(status_code=400, detail=f"Failed to fetch URL: {e}")

    try:
        doc = await asyncio.to_thread(load_webpage, req.url, html_content)
        chunks = await asyncio.to_thread(session_retriever.index_document, doc)
        return {
            "success": True,
            "title": doc.title,
            "chunks": chunks,
            "url": req.url,
        }
    except Exception as e:
        log.error("Failed to parse and index URL: %s", e)
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/qa", response_model=QAResponse)
async def ask_question_endpoint(request: Request, req: QuestionRequest):
    """Ask a question: uses shared prompt-hardened QA engine, returns text immediately, generates audio asynchronously."""
    session_id = get_session_id(request)
    session_retriever = get_retriever_for_session(session_id)

    if not session_retriever.is_loaded:
        raise HTTPException(
            status_code=400, detail="No document loaded. Please upload a document or URL first."
        )

    t0 = time.time()

    # 1. Retrieve chunks with calibrated refusal threshold
    chunks = await asyncio.to_thread(
        session_retriever.retrieve, req.question, config.doc_qa.top_k, True
    )

    # 2. Build hardened prompt using shared template
    context_str = "\n\n".join(
        f"[Source {i + 1} — {c.citation}]\n{c.text}" for i, c in enumerate(chunks)
    )
    if not chunks:
        context_str = (
            "(No relevant content found in the document that exceeds the relevance threshold)"
        )

    lang_key = req.language.lower()
    system_prompt = _SYSTEM_PROMPT.format(
        lang_instruction=_LANG_INSTRUCTIONS.get(lang_key, _LANG_INSTRUCTIONS["hinglish"]),
        doc_title=session_retriever.document_title,
        history_context="",
        context=context_str,
    )

    # 3. Generate answer
    try:
        answer = await llm.generate(prompt=req.question, system=system_prompt)
    except Exception as e:
        log.warning("LLM generation error: %s", e)
        if chunks:
            answer = f"Document ke according ({chunks[0].citation}):\n{chunks[0].text[:300]}..."
        else:
            answer = "Is document mein yeh information nahi mili."

    elapsed = time.time() - t0

    # 4. Generate audio response asynchronously
    audio_id = uuid.uuid4().hex
    audio_path = AUDIO_CACHE_DIR / f"{audio_id}.mp3"
    temp_audio_path = AUDIO_CACHE_DIR / f"{audio_id}.tmp"
    audio_url = f"/api/audio/{audio_id}.mp3"

    async def _render_audio():
        try:
            import edge_tts

            if lang_key in ("gujarati", "gu"):
                voice_code = config.tts.edge_voice_gu
            elif lang_key in ("english", "en"):
                voice_code = config.tts.edge_voice_en
            else:
                voice_code = config.tts.edge_voice_hi

            clean_text = answer
            has_devanagari = any("\u0900" <= c <= "\u097f" for c in clean_text)
            has_gujarati = any("\u0a80" <= c <= "\u0aff" for c in clean_text)

            if lang_key in ("gujarati", "gu"):
                if has_devanagari and not has_gujarati:
                    try:
                        from aksharamukha import transliterate

                        clean_text = transliterate.process("Devanagari", "Gujarati", clean_text)
                    except Exception as e:
                        log.debug("Transliteration to Gujarati skipped: %s", e)
            elif lang_key in ("hindi", "hi"):
                if has_gujarati and not has_devanagari:
                    try:
                        from aksharamukha import transliterate

                        clean_text = transliterate.process("Gujarati", "Devanagari", clean_text)
                    except Exception as e:
                        log.debug("Transliteration to Devanagari skipped: %s", e)

            comm = edge_tts.Communicate(clean_text, voice_code)
            # Write to temp file first, then atomically rename to prevent partial reads
            await comm.save(str(temp_audio_path))
            temp_audio_path.replace(audio_path)
        except Exception as e:
            log.warning("Audio synthesis warning: %s", e)
            if temp_audio_path.exists():
                try:
                    temp_audio_path.unlink()
                except Exception:
                    pass

    # Fire audio generation in tracked background task
    track_task(asyncio.create_task(_render_audio()))

    citations_resp = [
        CitationModel(citation=c.citation, text=c.text[:250], score=round(c.score, 3))
        for c in chunks
    ]

    return QAResponse(
        question=req.question,
        answer=answer,
        elapsed_sec=round(elapsed, 2),
        citations=citations_resp,
        audio_url=audio_url,
    )


@app.get("/api/qa/stream")
async def stream_qa_endpoint(
    request: Request, question: str = Query(...), language: str = Query("hinglish")
):
    """Server-Sent Events (SSE) endpoint for token-by-token streaming."""
    session_id = get_session_id(request)
    session_retriever = get_retriever_for_session(session_id)

    if not session_retriever.is_loaded:
        raise HTTPException(status_code=400, detail="No document loaded.")

    chunks = await asyncio.to_thread(
        session_retriever.retrieve, question, config.doc_qa.top_k, True
    )
    context_str = "\n\n".join(
        f"[Source {i + 1} — {c.citation}]\n{c.text}" for i, c in enumerate(chunks)
    )
    if not chunks:
        context_str = "(No relevant content found exceeding the relevance threshold)"

    lang_key = language.lower()
    system_prompt = _SYSTEM_PROMPT.format(
        lang_instruction=_LANG_INSTRUCTIONS.get(lang_key, _LANG_INSTRUCTIONS["hinglish"]),
        doc_title=session_retriever.document_title,
        history_context="",
        context=context_str,
    )

    async def event_generator() -> AsyncIterator[str]:
        import json

        try:
            async for token in llm.generate_stream(question, system=system_prompt):
                yield f"data: {json.dumps({'token': token})}\n\n"

            citations = [{"citation": c.citation, "score": round(c.score, 3)} for c in chunks]
            yield f"data: {json.dumps({'citations': citations})}\n\n"
        except Exception as e:
            log.error("Streaming LLM error: %s", e)
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
        finally:
            yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.post("/api/qa/voice", response_model=QAResponse)
async def ask_voice_question_endpoint(
    request: Request, audio: UploadFile = File(...), language: str = Form("hinglish")
):
    """Voice QA endpoint: streams audio enforcing size limit, resamples to 16kHz via PyAV, and transcribes with Whisper."""
    audio_bytes = await stream_upload_bytes(audio, MAX_UPLOAD_SIZE)

    # 1. Resample browser audio to clean 16kHz mono WAV
    try:
        clean_wav_bytes = await asyncio.to_thread(resample_audio_to_16k_mono, audio_bytes)
    except Exception as e:
        log.warning("Audio resampling failed: %s", e)
        raise HTTPException(
            status_code=400, detail=f"unsupported audio: could not decode or resample audio ({e})"
        )

    # 2. STT Transcription on thread pool
    transcription = await asyncio.to_thread(stt.transcribe, clean_wav_bytes)
    question_text = transcription.text.strip()
    if not question_text:
        raise HTTPException(
            status_code=400, detail="Could not understand voice audio. Please speak clearly."
        )

    # 3. Query Document
    req = QuestionRequest(question=question_text, language=language)
    return await ask_question_endpoint(request, req)


@app.post("/api/command")
async def voice_command_endpoint(req: CommandRequest):
    """Execute text transformations or translation commands, returning clean HTTP status codes."""
    if not req.command or not req.command.strip():
        raise HTTPException(status_code=400, detail="Command cannot be empty")
    if not req.text or not req.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")

    system_prompt = (
        "You are BolSamajh text editor. "
        "Apply the requested command to the text. "
        "Return ONLY the modified text with no conversational filler."
    )
    prompt = f"COMMAND: {req.command}\n\nORIGINAL TEXT:\n{req.text}\n\nMODIFIED TEXT:"
    try:
        modified = await llm.generate(prompt=prompt, system=system_prompt)
    except Exception as e:
        log.error("Command processing failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Command processing failed: {e}")

    return {"command": req.command, "result": modified.strip()}


class DictateResponse(BaseModel):
    raw_text: str
    clean_text: str
    script: str
    duration_seconds: float
    latency_ms: float
    fillers_removed: int


@app.post("/api/dictate", response_model=DictateResponse)
async def api_dictate(
    file: UploadFile = File(...),
    script: str = Form("natural"),
    remove_fillers: bool = Form(True),
):
    """Voice dictation endpoint with filler removal, number formatting, and script control."""
    t0 = time.time()
    audio_bytes = await stream_upload_bytes(file, MAX_UPLOAD_SIZE)
    clean_wav = await asyncio.to_thread(resample_audio_to_16k_mono, audio_bytes)
    res = await asyncio.to_thread(stt.transcribe, clean_wav)
    raw_text = res.text.strip()

    from bolsamajh.utils.text_cleanup import (
        cleanup_text,
    )
    from bolsamajh.utils.text_cleanup import (
        remove_fillers as clean_fillers_only,
    )

    clean_text = cleanup_text(
        raw_text,
        remove_filler=remove_fillers,
        script=script,
    )
    fillers_removed = 0
    if remove_fillers and raw_text:
        text_without_fillers = clean_fillers_only(raw_text)
        fillers_removed = max(0, len(raw_text.split()) - len(text_without_fillers.split()))

    latency_ms = round((time.time() - t0) * 1000, 1)
    return DictateResponse(
        raw_text=raw_text,
        clean_text=clean_text,
        script=script,
        duration_seconds=round(res.duration_seconds, 2),
        latency_ms=latency_ms,
        fillers_removed=fillers_removed,
    )


class InjectRequest(BaseModel):
    text: str


@app.post("/api/inject")
async def api_inject(req: InjectRequest):
    """Inject text directly into the active desktop application window via clipboard simulator."""
    try:
        from bolsamajh.utils.clipboard import insert_text

        await asyncio.to_thread(insert_text, req.text)
        return {"status": "ok", "injected_length": len(req.text)}
    except Exception as e:
        log.warning("Inject failed: %s", e)
        return {"status": "error", "message": str(e)}


_OVERLAY_HUD = None


def set_overlay_hud(hud) -> None:
    """Set global reference to OverlayHUD instance."""
    global _OVERLAY_HUD
    _OVERLAY_HUD = hud


def get_overlay_hud(create_if_missing: bool = False):
    """Retrieve global reference to OverlayHUD instance, optionally creating if requested."""
    global _OVERLAY_HUD
    if _OVERLAY_HUD is None and create_if_missing:
        try:
            from bolsamajh.overlay.hud import OverlayHUD

            _OVERLAY_HUD = OverlayHUD()
            _OVERLAY_HUD.start()
        except Exception as e:
            log.debug("Could not lazily initialize OverlayHUD: %s", e)
    return _OVERLAY_HUD


@app.get("/api/overlay")
async def get_overlay():
    """Return overlay HUD live status and whether it is active/pinned."""
    hud = get_overlay_hud(create_if_missing=False)
    if hud is None:
        return {"status": "idle", "running": False, "pinned": False}
    running = bool(hud._thread and hud._thread.is_alive())
    return {
        "status": getattr(hud, "state", "idle"),
        "running": running,
        "pinned": getattr(hud, "is_pinned", False),
    }


@app.post("/api/overlay/toggle")
async def toggle_overlay():
    """Toggle persistent pinned visible state of the desktop floating overlay."""
    hud = get_overlay_hud(create_if_missing=True)
    if hud is None:
        return {"status": "error", "message": "Overlay HUD not attached to server"}
    pinned = hud.toggle_pin()
    return {
        "status": "ok",
        "pinned": pinned,
        "message": (
            "Desktop overlay pinned on top of all windows"
            if pinned
            else "Desktop overlay hidden (idle)"
        ),
    }


@app.post("/api/overlay/start")
async def start_overlay():
    """Start and show the desktop overlay HUD."""
    hud = get_overlay_hud(create_if_missing=True)
    if hud is None:
        return {"status": "error", "message": "Overlay HUD not attached to server"}
    hud.start()
    hud.show_pill("BolSamajh Overlay Active")
    return {"status": "ok", "message": "Desktop overlay started"}


@app.post("/api/overlay/stop")
async def stop_overlay():
    """Hide desktop overlay HUD."""
    hud = get_overlay_hud(create_if_missing=False)
    if hud is None:
        return {"status": "error", "message": "Overlay HUD not attached to server"}
    hud.set_state("idle")
    return {"status": "ok", "message": "Desktop overlay hidden"}


@app.post("/api/install-shortcuts")
async def install_desktop_shortcuts():
    """Create or refresh Windows desktop and start menu shortcuts."""
    try:
        from scripts.create_desktop_shortcut import create_shortcut

        create_shortcut()
        return {
            "status": "ok",
            "message": "Desktop shortcut created successfully at Desktop/BolSamajh.lnk",
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to create shortcut: {e}"}


@app.get("/api/audio/{audio_file}")
async def get_audio_file(audio_file: str):
    """Serve synthesized audio file with streaming support and strict path traversal protection."""
    base_dir = AUDIO_CACHE_DIR.resolve()
    unquoted = unquote(audio_file)

    # Reject absolute paths or directory traversal attempts
    if Path(unquoted).is_absolute() or unquoted.startswith("/") or unquoted.startswith("\\"):
        raise HTTPException(status_code=403, detail="Forbidden: path traversal detected")

    try:
        target_path = (base_dir / unquoted).resolve()
        if not target_path.is_relative_to(base_dir) or target_path == base_dir:
            raise HTTPException(status_code=403, detail="Forbidden: path traversal detected")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid audio filename")

    # Wait up to 5 seconds if audio is still generating in background
    for _ in range(50):
        if target_path.exists() and target_path.stat().st_size > 0:
            break
        await asyncio.sleep(0.1)

    if not target_path.exists():
        raise HTTPException(status_code=404, detail="Audio file not found or generation timed out")
    return FileResponse(target_path, media_type="audio/mpeg")


# --- Tier 4 Sponsor Alignment: OpenAI-Compatible Gateway ---


@app.post("/v1/audio/transcriptions")
async def openai_compatible_transcription(
    file: UploadFile = File(...),
    model: str = Form("whisper-1"),
    language: Optional[str] = Form(None),
    prompt: Optional[str] = Form(None),
    response_format: str = Form("json"),
):
    """OpenAI-compatible STT endpoint for Bolna agent integration.

    Honors language, prompt, and response_format (json, text, verbose_json, srt, vtt).
    Returns 400 immediately on corrupt audio rather than passing raw bytes to STT.
    """
    audio_bytes = await stream_upload_bytes(file, MAX_UPLOAD_SIZE)
    try:
        clean_wav = await asyncio.to_thread(resample_audio_to_16k_mono, audio_bytes)
    except Exception as e:
        log.warning("Audio decoding or resampling failed: %s", e)
        raise HTTPException(
            status_code=400, detail=f"Unsupported audio: could not decode or resample audio ({e})"
        )

    transcribe_kwargs = {}
    if language and language.strip():
        transcribe_kwargs["language"] = language.strip()
    if prompt and prompt.strip():
        transcribe_kwargs["prompt"] = prompt.strip()

    res = await asyncio.to_thread(stt.transcribe, clean_wav, **transcribe_kwargs)
    text = res.text.strip()

    fmt = (response_format or "json").lower().strip()
    if fmt == "text":
        return PlainTextResponse(text)
    elif fmt == "verbose_json":
        return {
            "task": "transcribe",
            "language": res.language or (language or "hi"),
            "duration": round(res.duration_seconds, 2),
            "text": text,
            "segments": [
                {
                    "id": 0,
                    "seek": 0,
                    "start": 0.0,
                    "end": round(res.duration_seconds, 2),
                    "text": text,
                }
            ]
            if text
            else [],
        }
    elif fmt == "srt":
        srt_text = (
            f"1\n00:00:00,000 --> 00:00:{int(res.duration_seconds):02d},000\n{text}\n"
            if text
            else ""
        )
        return PlainTextResponse(srt_text, media_type="text/plain")
    elif fmt == "vtt":
        vtt_text = (
            f"WEBVTT\n\n1\n00:00:00.000 --> 00:00:{int(res.duration_seconds):02d}.000\n{text}\n"
            if text
            else "WEBVTT\n"
        )
        return PlainTextResponse(vtt_text, media_type="text/plain")
    else:
        return {"text": text}


@app.post("/v1/audio/speech")
async def openai_compatible_speech(req: OpenAISpeechRequest):
    """OpenAI-compatible TTS endpoint for Bolna agent integration.

    Generates natural Indian speech proxying Microsoft Edge-TTS (Swara/Neerja/Dhwani - unofficial cloud service)
    or local offline Piper TTS (voice='piper' or model='piper' - 100% offline ONNX).
    Honors explicitly requested voice, response_format (mp3, wav), and speed.
    Enforces maximum input length of 4,000 characters and returns clean HTTP 502 on upstream/offline failure.
    """
    if not req.input or not req.input.strip():
        raise HTTPException(status_code=400, detail="Input text cannot be empty.")

    if len(req.input) > 4000:
        raise HTTPException(
            status_code=400,
            detail=f"Input text exceeds maximum allowed length of 4,000 characters (received {len(req.input)}).",
        )

    fmt = (req.response_format or "mp3").strip().lower()
    if fmt not in ("mp3", "wav"):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported response_format '{req.response_format}'. Supported formats: 'mp3', 'wav'.",
        )

    requested_voice = req.voice.strip().lower()
    req_model = (req.model or "").strip().lower()

    # Route to local offline Piper TTS if requested
    if requested_voice in ("piper", "piper-pratham", "hi_in-pratham-medium") or req_model in (
        "piper",
        "piper-tts",
    ):
        try:
            piper_tts = get_piper_adapter(model_path=getattr(config.tts, "piper_model_path", ""))
            wav_bytes = await asyncio.to_thread(piper_tts.synthesize_to_bytes, req.input)
            if not wav_bytes:
                raise RuntimeError("Piper offline TTS returned empty audio stream.")
        except Exception as e:
            log.error("Piper offline TTS speech synthesis failed: %s", e)
            raise HTTPException(
                status_code=502,
                detail={"error": "Piper TTS offline synthesis failed", "message": str(e)},
            )

        if fmt == "wav":
            return StreamingResponse(io.BytesIO(wav_bytes), media_type="audio/wav")

        try:
            mp3_bytes = await asyncio.to_thread(convert_wav_to_mp3, wav_bytes)
            return StreamingResponse(io.BytesIO(mp3_bytes), media_type="audio/mpeg")
        except Exception as e:
            log.error("Failed to convert synthesized Piper WAV audio to MP3: %s", e)
            raise HTTPException(
                status_code=502,
                detail={"error": "Audio format conversion to MP3 failed", "message": str(e)},
            )

    # Default path: Microsoft Edge-TTS (unofficial cloud endpoint)
    import edge_tts

    # Compute rate string from speed (OpenAI API accepts speed from 0.25 to 4.0)
    clamped_speed = max(0.25, min(req.speed, 4.0))
    speed_pct = int(round((clamped_speed - 1.0) * 100))
    rate_str = f"+{speed_pct}%" if speed_pct >= 0 else f"{speed_pct}%"

    voice = VOICE_MAP.get(requested_voice, config.tts.edge_voice_hi)

    try:
        comm = edge_tts.Communicate(req.input, voice, rate=rate_str)
        audio_buf = io.BytesIO()
        async for chunk in comm.stream():
            if chunk["type"] == "audio":
                audio_buf.write(chunk["data"])
        mp3_bytes = audio_buf.getvalue()
        if not mp3_bytes:
            raise RuntimeError("Edge-TTS service returned empty audio data stream.")
    except Exception as e:
        log.error("Edge-TTS speech synthesis failed: %s", e)
        raise HTTPException(
            status_code=502,
            detail={"error": "Edge-TTS upstream synthesis failed", "message": str(e)},
        )

    if fmt == "wav":
        try:
            wav_bytes = await asyncio.to_thread(resample_audio_to_16k_mono, mp3_bytes)
            return StreamingResponse(io.BytesIO(wav_bytes), media_type="audio/wav")
        except Exception as e:
            log.error("Failed to convert synthesized audio to WAV format: %s", e)
            raise HTTPException(
                status_code=502,
                detail={"error": "Audio format conversion to WAV failed", "message": str(e)},
            )

    return StreamingResponse(io.BytesIO(mp3_bytes), media_type="audio/mpeg")


@app.websocket("/v1/realtime")
async def openai_realtime_transcription_websocket(
    websocket: WebSocket, intent: str = "transcription"
):
    """OpenAI Realtime-compatible WebSocket transcription endpoint for Bolna agent integration.

    Supports:
    - Origin verification against allowed hosts
    - API key authentication when configured
    - session.created emitted upon connection
    - session.update -> session.updated
    - input_audio_buffer.append with 10MB memory cap
    - input_audio_buffer.commit -> input_audio_buffer.committed
    - Public STT transcribe method (no private _model access)
    - conversation.item.input_audio_transcription.completed
    - Clean error handling and error events
    """
    # 1. Validate Origin header
    origin = websocket.headers.get("origin")
    if origin:
        parsed_origin = urlparse(origin)
        orig_host = (parsed_origin.hostname or "").lower()
        if orig_host and orig_host not in ALLOWED_HOSTS:
            await websocket.close(code=1008, reason="Forbidden: untrusted origin")
            return

    # 2. Require API key when configured
    expected_key = os.getenv("BOLSAMAJH_API_KEY", "").strip()
    if expected_key:
        auth_header = websocket.headers.get("authorization", "")
        scheme, _, token = auth_header.partition(" ")
        query_token = websocket.query_params.get("api_key") or websocket.query_params.get("token")
        effective_token = (token or query_token or "").strip()
        if not effective_token or not hmac.compare_digest(effective_token, expected_key):
            await websocket.close(code=1008, reason="Unauthorized: invalid or missing Bearer token")
            return

    await websocket.accept()

    import json

    import scipy.signal

    # 3. Emit session.created event
    session_id = f"sess_{uuid.uuid4().hex[:12]}"
    await websocket.send_text(
        json.dumps(
            {
                "type": "session.created",
                "session": {
                    "id": session_id,
                    "model": "whisper-1",
                    "modalities": ["audio", "text"],
                    "instructions": "",
                    "voice": "alloy",
                    "input_audio_format": "pcm16",
                    "output_audio_format": "pcm16",
                },
            }
        )
    )

    MAX_WS_BUFFER = 10 * 1024 * 1024  # 10 MB cap
    audio_buffer = bytearray()
    language = "auto"
    item_counter = 0

    try:
        while True:
            msg_text = await websocket.receive_text()
            data = json.loads(msg_text)
            event_type = data.get("type", "")

            if event_type == "session.update":
                session_cfg = data.get("session", {})
                audio_input = session_cfg.get("audio", {}).get("input", {})
                transcription_cfg = audio_input.get("transcription", {})
                language = transcription_cfg.get("language", language)
                await websocket.send_text(
                    json.dumps(
                        {
                            "type": "session.updated",
                            "session": session_cfg,
                        }
                    )
                )

            elif event_type == "input_audio_buffer.append":
                b64_audio = data.get("audio", "")
                if b64_audio:
                    pcm_chunk = base64.b64decode(b64_audio)
                    if len(audio_buffer) + len(pcm_chunk) > MAX_WS_BUFFER:
                        await websocket.send_text(
                            json.dumps(
                                {
                                    "type": "error",
                                    "error": {
                                        "type": "invalid_request_error",
                                        "message": f"Buffer size exceeded {MAX_WS_BUFFER} bytes limit",
                                    },
                                }
                            )
                        )
                        await websocket.close(code=1009, reason="Buffer size exceeded")
                        return
                    audio_buffer.extend(pcm_chunk)

            elif event_type == "input_audio_buffer.commit":
                item_counter += 1
                item_id = f"item_{item_counter}"
                committed_bytes = bytes(audio_buffer)
                audio_buffer.clear()

                # Emit input_audio_buffer.committed event
                await websocket.send_text(
                    json.dumps(
                        {
                            "type": "input_audio_buffer.committed",
                            "item_id": item_id,
                        }
                    )
                )

                transcript = ""
                if len(committed_bytes) > 0:
                    audio_np = (
                        np.frombuffer(committed_bytes, dtype=np.int16).astype(np.float32) / 32768.0
                    )
                    gcd = int(np.gcd(24000, 16000))
                    audio_16k = scipy.signal.resample_poly(
                        audio_np, 16000 // gcd, 24000 // gcd
                    ).astype(np.float32)
                    lang_param = None if language in ("auto", "", None) else language

                    # Use public STT transcribe method
                    res = await asyncio.to_thread(
                        stt.transcribe,
                        audio_16k,
                        language=lang_param,
                    )
                    transcript = res.text.strip()

                await websocket.send_text(
                    json.dumps(
                        {
                            "type": "conversation.item.input_audio_transcription.completed",
                            "item_id": item_id,
                            "transcript": transcript,
                        }
                    )
                )

    except (WebSocketDisconnect, asyncio.CancelledError):
        pass
    except Exception as e:
        log.error("Realtime WebSocket error: %s", e)
        try:
            await websocket.send_text(
                json.dumps(
                    {
                        "type": "error",
                        "error": {
                            "type": "server_error",
                            "message": str(e),
                        },
                    }
                )
            )
            await websocket.close(code=1011, reason=str(e)[:100])
        except Exception:
            pass


# --- Static Web Frontend ---

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    @app.get("/", response_class=HTMLResponse)
    async def serve_index():
        index_file = STATIC_DIR / "index.html"
        return FileResponse(index_file)

    @app.get("/manifest.json")
    async def serve_manifest():
        manifest_file = STATIC_DIR / "manifest.json"
        if manifest_file.exists():
            return FileResponse(manifest_file, media_type="application/manifest+json")
        raise HTTPException(status_code=404, detail="Manifest not found")

    @app.get("/sw.js")
    async def serve_sw():
        sw_file = STATIC_DIR / "sw.js"
        if sw_file.exists():
            return FileResponse(
                sw_file,
                media_type="application/javascript",
                headers={"Service-Worker-Allowed": "/"},
            )
        raise HTTPException(status_code=404, detail="Service worker not found")


if __name__ == "__main__":
    import argparse

    import uvicorn

    parser = argparse.ArgumentParser(description="BolSamajh Web Server & API Gateway")
    parser.add_argument("--host", default="127.0.0.1", help="Bind host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="Bind port (default: 8000)")
    args = parser.parse_args()

    check_bind_security(host=args.host)
    uvicorn.run("bolsamajh.web.server:app", host=args.host, port=args.port)
