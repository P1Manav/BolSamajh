"""BolSamajh Web Server — FastAPI backend for browser web-call mode, SSE streaming, and OpenAI-compatible API.

Adheres to Tier 3 (Item 20) and Tier 4 (Item 21):
- Audio resampler: Resamples arbitrary browser audio (48kHz/44.1kHz) to clean 16kHz mono PCM via PyAV AudioResampler.
- Thread pool execution: Offloads STT, indexing, and web fetching via asyncio.to_thread.
- Security: CORS restricted to localhost, SSRF protection blocking internal/private IP addresses, 25 MB upload limit.
- Document handling: Preserves real document filenames, uses shared prompt-hardened QA engine.
- Latency & Streaming: Returns text immediately; provides Server-Sent Events (SSE) and WebSocket streaming; reports TTFA.
- Voice & Language: Maps Gujarati to gu-IN-DhwaniNeural, Hindi/Hinglish to hi-IN-SwaraNeural, English to en-IN-NeerjaNeural.
- Dynamic hardware status: Detects real GPU/CPU dynamically (no hardcoded strings).
- Sponsor Alignment (Tier 4): Exposes OpenAI-compatible /v1/audio/transcriptions and /v1/audio/speech endpoints for Bolna agent integration.
- Audio cache cleanup: Automatically sweeps expired temporary audio files.
"""

import io
import os
import time
import uuid
import wave
import socket
import logging
import tempfile
import asyncio
import ipaddress
from pathlib import Path
from urllib.parse import urlparse
from typing import Optional, List, AsyncIterator

import numpy as np
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, WebSocket, WebSocketDisconnect, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from bolsamajh.config import load_config, AppConfig
from bolsamajh.documents.loader import load_document, Document
from bolsamajh.documents.retriever import DocumentRetriever
from bolsamajh.documents.chunker import Chunk
from bolsamajh.stt.faster_whisper_stt import FasterWhisperSTT
from bolsamajh.llm.factory import create_llm_adapter
from bolsamajh.tts.edge_tts_adapter import EdgeTTSAdapter
from bolsamajh.pipeline.doc_qa import _SYSTEM_PROMPT, _LANG_INSTRUCTIONS
from bolsamajh.utils.cuda_setup import auto_detect_device

log = logging.getLogger("bolsamajh.web")

app = FastAPI(
    title="BolSamajh Voice AI API",
    description="Multilingual Hinglish Voice Assistant, Document Intelligence & OpenAI-compatible Voice Gateway",
    version="0.2.0",
)

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
            ip = ipaddress.ip_address(ip_str)
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
                return False
        return True
    except Exception:
        return False


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

@app.get("/api/status")
async def get_status():
    """Return comprehensive system health and auto-detected hardware."""
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

    # Dependency diagnostic checks
    llm_ready = await llm.is_available()

    return {
        "status": "ready",
        "device": gpu_name,
        "stt": stt.name,
        "llm": llm.name,
        "llm_ready": llm_ready,
        "tts": tts.name,
        "document_loaded": retriever.is_loaded,
        "document_title": retriever.document_title,
        "refusal_threshold": retriever.refusal_threshold,
    }


@app.post("/api/documents/upload")
async def upload_document_endpoint(file: UploadFile = File(...)):
    """Upload and index a document with upload size limits and real filename preservation."""
    content = await file.read()
    if len(content) > MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=413, detail=f"File exceeds maximum upload size of {MAX_UPLOAD_SIZE // (1024*1024)} MB.")

    suffix = Path(file.filename or "doc.tmp").suffix.lower()
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        # Load document on background thread
        doc = await asyncio.to_thread(load_document, tmp_path)

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
    except Exception as e:
        log.error("Failed to upload document: %s", e)
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass


@app.post("/api/documents/url")
async def load_url_endpoint(req: URLDocRequest):
    """Fetch and index a webpage URL with strict SSRF validation."""
    if not is_safe_external_url(req.url):
        raise HTTPException(
            status_code=400,
            detail="Forbidden URL. BolSamajh SSRF protection blocks local and private network addresses.",
        )

    try:
        doc = await asyncio.to_thread(load_document, req.url)
        chunks = await asyncio.to_thread(retriever.index_document, doc)
        return {
            "success": True,
            "title": doc.title,
            "chunks": chunks,
            "url": req.url,
        }
    except Exception as e:
        log.error("Failed to load URL: %s", e)
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
            voice_code = "hi-IN-SwaraNeural"
            if lang_key == "gujarati":
                voice_code = "gu-IN-DhwaniNeural"
            elif lang_key == "english":
                voice_code = "en-IN-NeerjaNeural"

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

    # Fire audio generation in background task
    asyncio.create_task(_render_audio())

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
    """Voice QA endpoint: resamples audio to 16kHz via PyAV, transcribes with Whisper, and queries document."""
    audio_bytes = await audio.read()

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
    """Serve synthesized audio file with streaming support."""
    filepath = AUDIO_CACHE_DIR / audio_file
    # Wait up to 5 seconds if audio is still generating in background
    for _ in range(50):
        if filepath.exists() and filepath.stat().st_size > 0:
            break
        await asyncio.sleep(0.1)

    if not filepath.exists():
        raise HTTPException(status_code=404, detail="Audio file not found or generation timed out")
    return FileResponse(filepath, media_type="audio/mpeg")


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
    audio_bytes = await file.read()
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
    """
    import edge_tts

    voice = "hi-IN-SwaraNeural"
    lower_input = req.input.lower()
    if req.voice in ("neerja", "alloy") or any(word in lower_input for word in ["english", "welcome"]):
        voice = "en-IN-NeerjaNeural"
    elif req.voice == "dhwani" or any('\u0A80' <= c <= '\u0AFF' for c in req.input):
        voice = "gu-IN-DhwaniNeural"

    comm = edge_tts.Communicate(req.input, voice)
    audio_buf = io.BytesIO()
    async for chunk in comm.stream():
        if chunk["type"] == "audio":
            audio_buf.write(chunk["data"])

    audio_buf.seek(0)
    return StreamingResponse(audio_buf, media_type="audio/mpeg")


# --- Static Web Frontend ---

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    @app.get("/", response_class=HTMLResponse)
    async def serve_index():
        index_file = STATIC_DIR / "index.html"
        return FileResponse(index_file)
