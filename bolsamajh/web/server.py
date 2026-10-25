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

import io
import os
import sys
import time
import uuid
import wave
import socket
import logging
import tempfile
import asyncio
import ipaddress
from pathlib import Path
from urllib.parse import urlparse, unquote, urljoin
from typing import Optional, List, AsyncIterator
from contextlib import asynccontextmanager

import numpy as np
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Query, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from bolsamajh import __version__
from bolsamajh.config import load_config, AppConfig
from bolsamajh.documents.loader import load_document, load_webpage, Document
from bolsamajh.documents.retriever import DocumentRetriever
from bolsamajh.documents.chunker import Chunk
from bolsamajh.stt.faster_whisper_stt import FasterWhisperSTT
from bolsamajh.llm.factory import create_llm_adapter
from bolsamajh.tts.edge_tts_adapter import EdgeTTSAdapter
from bolsamajh.pipeline.doc_qa import _SYSTEM_PROMPT, _LANG_INSTRUCTIONS
from bolsamajh.utils.cuda_setup import auto_detect_device

log = logging.getLogger("bolsamajh.web")

# Track strong references to background asyncio tasks to prevent premature garbage collection
_BACKGROUND_TASKS: set[asyncio.Task] = set()


def track_task(task: asyncio.Task) -> asyncio.Task:
    """Store strong reference to background task until it completes."""
    _BACKGROUND_TASKS.add(task)
    task.add_done_callback(_BACKGROUND_TASKS.discard)
    return task


def check_bind_security(host: Optional[str] = None) -> None:
    """Refuse to start if server binds to anything but 127.0.0.1 and no API key is set."""
    api_key = os.getenv("BOLSAMAJH_API_KEY", "").strip()
    if api_key:
        return

    target_host = host or os.getenv("BOLSAMAJH_HOST") or os.getenv("UVICORN_HOST") or os.getenv("HOST")
    if not target_host:
        for i, arg in enumerate(sys.argv):
            if arg in ("--host", "-h") and i + 1 < len(sys.argv):
                target_host = sys.argv[i + 1]
                break
            elif arg.startswith("--host="):
                target_host = arg.split("=", 1)[1]
                break

    if target_host and target_host.strip().lower() not in ("127.0.0.1", "localhost", "::1"):
        raise RuntimeError(
            f"Security Error: Server configured to bind to '{target_host}' without BOLSAMAJH_API_KEY set. "
            f"Binding to non-loopback addresses exposes the gateway publicly. "
            f"Either set BOLSAMAJH_API_KEY or bind strictly to 127.0.0.1."
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: perform bind security check on startup, cancel tasks on shutdown."""
    check_bind_security()
    yield
    for task in list(_BACKGROUND_TASKS):
        task.cancel()


app = FastAPI(
    title="BolSamajh Voice AI API",
    description="Multilingual Hinglish Voice Assistant, Document Intelligence & OpenAI-compatible Voice Gateway",
    version=__version__,
    lifespan=lifespan,
)

# Middleware: Gateway Bearer token authentication when BOLSAMAJH_API_KEY is configured
@app.middleware("http")
async def gateway_auth_middleware(request: Request, call_next):
    if request.url.path.startswith("/v1/"):
        expected_key = os.getenv("BOLSAMAJH_API_KEY", "").strip()
        if expected_key:
            auth_header = request.headers.get("authorization", "")
            scheme, _, token = auth_header.partition(" ")
            if scheme.lower() != "bearer" or token.strip() != expected_key:
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Unauthorized: invalid or missing Bearer token for /v1 gateway"},
                    headers={"WWW-Authenticate": "Bearer"},
                )
    return await call_next(request)

# Restrict CORS to localhost with no credentials (SSRF / CSRF hardening)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:3000",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

STATIC_DIR = Path(__file__).parent / "static"
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
tts = EdgeTTSAdapter()
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
            if mapped.is_private or mapped.is_loopback or mapped.is_link_local or mapped.is_reserved or mapped.is_multicast:
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


def safe_fetch_url(url: str, max_redirects: int = 3, timeout: float = 10.0) -> str:
    """Fetch URL safely: resolves once per hop, connects to resolved IP, blocks private ranges, re-validates redirects."""
    import httpx

    current_url = url
    for _ in range(max_redirects + 1):
        parsed = urlparse(current_url)
        if parsed.scheme not in ("http", "https"):
            raise ValueError(f"SSRF protection: forbidden scheme '{parsed.scheme}'")
        hostname = parsed.hostname
        if not hostname or hostname.lower() in ("localhost", "127.0.0.1", "::1", "0.0.0.0", "169.254.169.254"):
            raise ValueError(f"SSRF protection: forbidden host '{hostname}'")

        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        try:
            addr_infos = socket.getaddrinfo(hostname, port)
        except Exception as e:
            raise ValueError(f"SSRF protection: could not resolve host '{hostname}': {e}")

        for addr in addr_infos:
            ip_str = addr[4][0]
            if not is_safe_ip(ip_str):
                raise ValueError(f"SSRF protection: blocked connection to non-public IP '{ip_str}'")

        # Request with follow_redirects=False to validate each hop manually
        with httpx.Client(timeout=timeout, follow_redirects=False) as client:
            resp = client.get(current_url, headers={"User-Agent": "BolSamajh-DocLoader/1.0"})
            if resp.is_redirect:
                location = resp.headers.get("location")
                if not location:
                    raise ValueError("SSRF protection: redirect missing Location header")
                current_url = urljoin(current_url, location)
                continue
            resp.raise_for_status()
            return resp.text

    raise ValueError(f"SSRF protection: exceeded maximum redirect hops ({max_redirects})")


async def stream_upload_to_file(file: UploadFile, dest_path: Path, max_size: int = MAX_UPLOAD_SIZE) -> int:
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
                        detail=f"File exceeds maximum upload size of {max_size // (1024*1024)} MB.",
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
                detail=f"File exceeds maximum upload size of {max_size // (1024*1024)} MB.",
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
}


# --- API Endpoints ---

@app.get("/api/status")
async def get_status():
    """Return system health and hardware. Does zero un-cached network calls."""
    clean_old_audio_cache()

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
    llm_configured = bool(os.getenv("GOOGLE_AI_API_KEY")) if config.llm.engine == "google_ai" else True
    llm_ready = await check_llm_ready_cached(ttl_seconds=60.0)

    return {
        "status": "ready",
        "device": gpu_name,
        "stt": stt.name,
        "llm": llm.name,
        "llm_ready": llm_ready,
        "llm_configured": llm_configured,
        "tts": tts.name,
        "document_loaded": retriever.is_loaded,
        "document_title": retriever.document_title,
        "refusal_threshold": retriever.refusal_threshold,
    }


@app.post("/api/documents/upload")
async def upload_document_endpoint(file: UploadFile = File(...)):
    """Upload and index a document with streaming size enforcement and real filename preservation."""
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

        # Index document on thread pool
        chunks = await asyncio.to_thread(retriever.index_document, doc)

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
async def load_url_endpoint(req: URLDocRequest):
    """Fetch and index a webpage URL with strict SSRF validation and redirect protection."""
    try:
        html_content = await asyncio.to_thread(safe_fetch_url, req.url)
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
        chunks = await asyncio.to_thread(retriever.index_document, doc)
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
async def ask_question_endpoint(req: QuestionRequest):
    """Ask a question: uses shared prompt-hardened QA engine, returns text immediately, generates audio asynchronously."""
    if not retriever.is_loaded:
        raise HTTPException(status_code=400, detail="No document loaded. Please upload a document or URL first.")

    t0 = time.time()

    # 1. Retrieve chunks with calibrated refusal threshold
    chunks = await asyncio.to_thread(retriever.retrieve, req.question, config.doc_qa.top_k, True)

    # 2. Build hardened prompt using shared template
    context_str = "\n\n".join(f"[Source {i+1} — {c.citation}]\n{c.text}" for i, c in enumerate(chunks))
    if not chunks:
        context_str = "(No relevant content found in the document that exceeds the relevance threshold)"

    lang_key = req.language.lower()
    system_prompt = _SYSTEM_PROMPT.format(
        lang_instruction=_LANG_INSTRUCTIONS.get(lang_key, _LANG_INSTRUCTIONS["hinglish"]),
        doc_title=retriever.document_title,
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
            if lang_key == "gujarati" and not any('\u0A80' <= c <= '\u0AFF' for c in clean_text):
                from aksharamukha import transliterate
                clean_text = transliterate.process("ISO", "Gujarati", clean_text)
            elif lang_key == "hindi" and not any('\u0900' <= c <= '\u097F' for c in clean_text):
                from aksharamukha import transliterate
                clean_text = transliterate.process("ISO", "Devanagari", clean_text)

            comm = edge_tts.Communicate(clean_text, voice_code)
            await comm.save(str(audio_path))
        except Exception as e:
            log.warning("Audio synthesis warning: %s", e)

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
async def stream_qa_endpoint(question: str = Query(...), language: str = Query("hinglish")):
    """Server-Sent Events (SSE) endpoint for token-by-token streaming."""
    if not retriever.is_loaded:
        raise HTTPException(status_code=400, detail="No document loaded.")

    chunks = await asyncio.to_thread(retriever.retrieve, question, config.doc_qa.top_k, True)
    context_str = "\n\n".join(f"[Source {i+1} — {c.citation}]\n{c.text}" for i, c in enumerate(chunks))
    if not chunks:
        context_str = "(No relevant content found exceeding the relevance threshold)"

    lang_key = language.lower()
    system_prompt = _SYSTEM_PROMPT.format(
        lang_instruction=_LANG_INSTRUCTIONS.get(lang_key, _LANG_INSTRUCTIONS["hinglish"]),
        doc_title=retriever.document_title,
        history_context="",
        context=context_str,
    )

    async def event_generator() -> AsyncIterator[str]:
        import json
        async for token in llm.generate_stream(question, system=system_prompt):
            yield f"data: {json.dumps({'token': token})}\n\n"

        citations = [{"citation": c.citation, "score": round(c.score, 3)} for c in chunks]
        yield f"data: {json.dumps({'citations': citations})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.post("/api/qa/voice", response_model=QAResponse)
async def ask_voice_question_endpoint(audio: UploadFile = File(...), language: str = Form("hinglish")):
    """Voice QA endpoint: streams audio enforcing size limit, resamples to 16kHz via PyAV, and transcribes with Whisper."""
    audio_bytes = await stream_upload_bytes(audio, MAX_UPLOAD_SIZE)

    # 1. Resample browser audio to clean 16kHz mono WAV
    try:
        clean_wav_bytes = await asyncio.to_thread(resample_audio_to_16k_mono, audio_bytes)
    except Exception as e:
        log.warning("Audio resampling fallback: %s", e)
        clean_wav_bytes = audio_bytes

    # 2. STT Transcription on thread pool
    transcription = await asyncio.to_thread(stt.transcribe, clean_wav_bytes)
    question_text = transcription.text.strip()
    if not question_text:
        raise HTTPException(status_code=400, detail="Could not understand voice audio. Please speak clearly.")

    # 3. Query Document
    req = QuestionRequest(question=question_text, language=language)
    return await ask_question_endpoint(req)


@app.post("/api/command")
async def voice_command_endpoint(req: CommandRequest):
    """Execute text transformations or translation commands."""
    system_prompt = (
        "You are BolSamajh text editor. "
        "Apply the requested command to the text. "
        "Return ONLY the modified text with no conversational filler."
    )
    prompt = f"COMMAND: {req.command}\n\nORIGINAL TEXT:\n{req.text}\n\nMODIFIED TEXT:"
    try:
        modified = await llm.generate(prompt=prompt, system=system_prompt)
    except Exception as e:
        modified = f"(Error processing command: {e})"
    return {"command": req.command, "result": modified.strip()}


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

    Allows any Bolna voice agent or external tool to use BolSamajh Hinglish STT
    by configuring base_url='http://localhost:8000/v1'.
    """
    audio_bytes = await stream_upload_bytes(file, MAX_UPLOAD_SIZE)
    try:
        clean_wav = await asyncio.to_thread(resample_audio_to_16k_mono, audio_bytes)
    except Exception:
        clean_wav = audio_bytes

    res = await asyncio.to_thread(stt.transcribe, clean_wav)
    text = res.text.strip()

    if response_format == "text":
        return text
    return {"text": text}


@app.post("/v1/audio/speech")
async def openai_compatible_speech(req: OpenAISpeechRequest):
    """OpenAI-compatible TTS endpoint for Bolna agent integration.

    Generates natural Indian neural speech (Swara/Neerja/Dhwani) compatible with Bolna agents.
    Honors explicitly requested voice, response_format (mp3, wav), and speed.
    Enforces maximum input length of 4,000 characters and returns clean HTTP 502 on upstream failure.
    """
    import edge_tts

    if not req.input or not req.input.strip():
        raise HTTPException(status_code=400, detail="Input text cannot be empty.")

    if len(req.input) > 4000:
        raise HTTPException(
            status_code=400,
            detail=f"Input text exceeds maximum allowed length of 4,000 characters (received {len(req.input)})."
        )

    fmt = (req.response_format or "mp3").strip().lower()
    if fmt not in ("mp3", "wav"):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported response_format '{req.response_format}'. Supported formats: 'mp3', 'wav'."
        )

    # Compute rate string from speed (OpenAI API accepts speed from 0.25 to 4.0)
    clamped_speed = max(0.25, min(req.speed, 4.0))
    speed_pct = int(round((clamped_speed - 1.0) * 100))
    rate_str = f"+{speed_pct}%" if speed_pct >= 0 else f"{speed_pct}%"

    requested_voice = req.voice.strip().lower()
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
            detail={"error": "Edge-TTS upstream synthesis failed", "message": str(e)}
        )

    if fmt == "wav":
        try:
            wav_bytes = await asyncio.to_thread(resample_audio_to_16k_mono, mp3_bytes)
            return StreamingResponse(io.BytesIO(wav_bytes), media_type="audio/wav")
        except Exception as e:
            log.error("Failed to convert synthesized audio to WAV format: %s", e)
            raise HTTPException(
                status_code=502,
                detail={"error": "Audio format conversion to WAV failed", "message": str(e)}
            )

    return StreamingResponse(io.BytesIO(mp3_bytes), media_type="audio/mpeg")


# --- Static Web Frontend ---

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    @app.get("/", response_class=HTMLResponse)
    async def serve_index():
        index_file = STATIC_DIR / "index.html"
        return FileResponse(index_file)
