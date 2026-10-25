"""BolSamajh Web Server — FastAPI backend for browser web-call mode and REST API."""

import io
import os
import time
import uuid
import asyncio
import logging
import tempfile
from pathlib import Path
from typing import Optional, List

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from bolsamajh.config import load_config, AppConfig
from bolsamajh.documents.loader import load_document, Document
from bolsamajh.documents.retriever import DocumentRetriever
from bolsamajh.documents.chunker import Chunk
from bolsamajh.stt.faster_whisper_stt import FasterWhisperSTT
from bolsamajh.llm.ollama_adapter import OllamaAdapter
from bolsamajh.llm.google_ai import GoogleAIAdapter
from bolsamajh.tts.edge_tts_adapter import EdgeTTSAdapter

log = logging.getLogger("bolsamajh.web")

app = FastAPI(
    title="BolSamajh Voice AI API",
    description="Multilingual Hinglish Voice Assistant & Document Intelligence",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC_DIR = Path(__file__).parent / "static"
AUDIO_CACHE_DIR = Path(tempfile.gettempdir()) / "bolsamajh_web_audio"
AUDIO_CACHE_DIR.mkdir(parents=True, exist_ok=True)

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
)
tts = EdgeTTSAdapter()

if config.llm.engine == "google_ai" and os.getenv("GOOGLE_AI_API_KEY"):
    llm = GoogleAIAdapter(model=config.llm.google_ai_model)
else:
    llm = OllamaAdapter(
        model=config.llm.ollama_model,
        base_url=config.llm.ollama_base_url,
    )


# Request & Response schemas
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


@app.get("/api/status")
async def get_status():
    """Return system readiness and active model info."""
    return {
        "status": "ready",
        "stt": stt.name,
        "llm": llm.name,
        "tts": tts.name,
        "document_loaded": retriever.is_loaded,
        "document_title": retriever.document_title,
    }


@app.post("/api/documents/upload")
async def upload_document_endpoint(file: UploadFile = File(...)):
    """Upload and index a document (PDF, Word DOCX, TXT, Markdown)."""
    suffix = Path(file.filename or "doc.tmp").suffix.lower()
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        doc = load_document(tmp_path)
        chunks = retriever.index_document(doc)
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
            os.remove(tmp_path)


@app.post("/api/documents/url")
async def load_url_endpoint(req: URLDocRequest):
    """Fetch and index a webpage URL."""
    try:
        doc = load_document(req.url)
        chunks = retriever.index_document(doc)
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
    """Ask a text question against the loaded document."""
    if not retriever.is_loaded:
        raise HTTPException(status_code=400, detail="No document loaded. Please upload or provide URL first.")

    t0 = time.time()
    chunks = retriever.retrieve(req.question, top_k=config.doc_qa.top_k)

    context_str = "\n\n".join(f"[{c.citation}]\n{c.text}" for c in chunks)
    system_prompt = (
        "You are BolSamajh, an intelligent document companion. "
        "Answer the user question accurately based ONLY on the source context. "
        "Cite the section or page numbers. If not mentioned in context, clearly state so.\n\n"
        f"SOURCE CONTEXT:\n{context_str}"
    )

    try:
        answer = await llm.generate(prompt=req.question, system=system_prompt)
    except Exception as e:
        # If Ollama is not active and Google AI key missing, provide graceful offline fallback
        log.warning("LLM generation error: %s. Using contextual summary fallback.", e)
        if chunks:
            answer = f"Document ke according ({chunks[0].citation}):\n{chunks[0].text[:300]}..."
        else:
            answer = "Document mein is question ka context nahi mila."

    elapsed = time.time() - t0

    # Generate TTS audio file
    audio_id = uuid.uuid4().hex
    audio_path = AUDIO_CACHE_DIR / f"{audio_id}.mp3"
    audio_url = f"/api/audio/{audio_id}.mp3"

    try:
        import edge_tts
        lang_voice = "hi-IN-SwaraNeural" if req.language in ("hinglish", "hindi") else "en-IN-NeerjaNeural"
        comm = edge_tts.Communicate(answer, lang_voice)
        await comm.save(str(audio_path))
    except Exception as e:
        log.warning("TTS audio generation error: %s", e)
        audio_url = None

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


@app.post("/api/qa/voice", response_model=QAResponse)
async def ask_voice_question_endpoint(audio: UploadFile = File(...), language: str = Form("hinglish")):
    """Upload voice audio (WAV/WebM), transcribe with Whisper, and return spoken response."""
    audio_bytes = await audio.read()

    # Convert to 16kHz mono WAV if needed via PyAV
    try:
        import av
        container = av.open(io.BytesIO(audio_bytes))
        audio_stream = container.streams.audio[0]
        frames = []
        for frame in container.decode(audio_stream):
            arr = frame.to_ndarray()
            if arr.ndim > 1:
                arr = arr.mean(axis=0)
            frames.append(arr)
        import numpy as np
        raw = np.concatenate(frames).astype(np.float32)
        if raw.max() > 1.0:
            raw = raw / 32768.0

        # Save to temporary WAV
        import wave
        wav_buf = io.BytesIO()
        with wave.open(wav_buf, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(16000)
            raw_int16 = (np.clip(raw, -1.0, 1.0) * 32767).astype(np.int16)
            wf.writeframes(raw_int16.tobytes())
        clean_wav_bytes = wav_buf.getvalue()
    except Exception as e:
        log.warning("Audio decoding failed, attempting raw: %s", e)
        clean_wav_bytes = audio_bytes

    # STT Transcribe
    transcription = stt.transcribe(clean_wav_bytes)
    question_text = transcription.text.strip()
    if not question_text:
        raise HTTPException(status_code=400, detail="Could not understand voice audio.")

    # Call QA
    req = QuestionRequest(question=question_text, language=language)
    return await ask_question_endpoint(req)


@app.post("/api/command")
async def voice_command_endpoint(req: CommandRequest):
    """Execute editing or translation command on given text."""
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
    """Serve generated audio response."""
    filepath = AUDIO_CACHE_DIR / audio_file
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="Audio file not found")
    return FileResponse(filepath, media_type="audio/mpeg")


# Serve static web frontend
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    @app.get("/", response_class=HTMLResponse)
    async def serve_index():
        index_file = STATIC_DIR / "index.html"
        return FileResponse(index_file)
