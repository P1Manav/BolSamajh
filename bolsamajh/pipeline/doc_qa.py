"""Doc Q&A pipeline — voice question → RAG → LLM → TTS with citations."""

import asyncio
import logging
import threading
import time
from typing import Literal

from bolsamajh.config import AppConfig
from bolsamajh.documents.loader import Document, load_document
from bolsamajh.documents.retriever import DocumentRetriever
from bolsamajh.documents.chunker import Chunk
from bolsamajh.stt.base import SpeechToText
from bolsamajh.llm.base import LLMAdapter
from bolsamajh.tts.base import TextToSpeech
from bolsamajh.overlay.hud import OverlayHUD
from bolsamajh.utils.audio import MicRecorder

log = logging.getLogger(__name__)

# System prompt for grounded Q&A
_SYSTEM_PROMPT = """You are BolSamajh, a helpful document assistant. You explain documents in a friendly, natural Hinglish style (like how educated Indians actually speak — English technical terms stay in English, rest in natural Hindi).

STRICT RULES:
1. Answer ONLY from the provided source document context. Do NOT add information from your training data.
2. ALWAYS cite the page number or section in your answer, e.g., "Page 3 mein likha hai ki…" or "Section 'Introduction' ke according…"
3. If the answer is NOT in the provided context, say clearly: "Yeh document mein nahi hai" or "Is document mein yeh information nahi mili."
4. Keep answers concise but complete — 2-4 sentences unless the user asks for detail.
5. If the document contains legal, medical, or financial information, add a brief note: "Note: Yeh professional advice nahi hai, sirf document ka summary hai."

LANGUAGE INSTRUCTIONS:
{lang_instruction}

DOCUMENT TITLE: {doc_title}

RELEVANT CONTEXT FROM DOCUMENT:
{context}
"""

_LANG_INSTRUCTIONS = {
    "hinglish": "Respond in natural Hinglish — mix Hindi and English as Indians naturally speak. Technical terms in English, rest in natural Hindi using Roman script.",
    "hindi": "Respond in Hindi using Devanagari script. Technical terms can stay in English.",
    "gujarati": "Respond in Gujarati using Gujarati script. Technical terms can stay in English.",
    "english": "Respond in clear, simple English.",
}


class DocQAPipeline:
    """Talk to any document — voice question → RAG → LLM → spoken answer."""

    def __init__(
        self,
        config: AppConfig,
        stt: SpeechToText,
        llm: LLMAdapter,
        tts: TextToSpeech,
        hud: OverlayHUD,
    ):
        self.config = config
        self.stt = stt
        self.llm = llm
        self.tts = tts
        self.hud = hud
        self.retriever = DocumentRetriever(
            embedding_model=config.doc_qa.embedding_model,
            chunk_size=config.doc_qa.chunk_size,
            chunk_overlap=config.doc_qa.chunk_overlap,
        )
        self.recorder = MicRecorder()
        self._current_document: Document | None = None
        self._processing = False

    @property
    def has_document(self) -> bool:
        return self.retriever.is_loaded

    def load_document(self, source: str) -> str:
        """Load and index a document. Returns status message."""
        try:
            self.hud.set_state("processing", "Loading doc…")
            doc = load_document(source)
            self._current_document = doc
            n_chunks = self.retriever.index_document(doc)
            msg = f"Loaded: {doc.title} ({doc.page_count} pages, {n_chunks} chunks)"
            log.info(msg)
            self.hud.show_text(f"📄 {doc.title} loaded", duration_ms=3000)
            return msg
        except Exception as e:
            log.error("Failed to load document: %s", e)
            self.hud.set_state("error")
            return f"Error: {e}"

    def start_question(self) -> None:
        """Start recording a voice question."""
        if not self.has_document:
            self.hud.show_text("No document loaded!", duration_ms=2000)
            return
        if self.recorder.is_recording or self._processing:
            return

        log.info("🎤 Doc Q&A: recording question…")
        self.hud.set_state("listening", "Ask your question…")
        self.recorder.start()

    def stop_and_answer(self) -> None:
        """Stop recording and generate an answer."""
        if not self.recorder.is_recording:
            return

        self.hud.set_state("processing")
        wav_bytes = self.recorder.stop()

        if not wav_bytes:
            self.hud.set_state("error")
            return

        # Process in background
        thread = threading.Thread(
            target=self._process_question,
            args=(wav_bytes,),
            daemon=True,
        )
        thread.start()

    def _process_question(self, wav_bytes: bytes) -> None:
        """Background: transcribe → retrieve → generate → speak."""
        self._processing = True
        t0 = time.time()

        try:
            # 1. Transcribe question
            result = self.stt.transcribe(wav_bytes)
            question = result.text.strip()
            if not question:
                self.hud.set_state("error")
                return

            log.info("Question: %s", question)
            self.hud.set_state("processing", "Thinking…")

            # 2. Retrieve relevant chunks
            chunks = self.retriever.retrieve(
                question,
                top_k=self.config.doc_qa.top_k,
            )

            # 3. Build grounded prompt
            context = self._format_context(chunks)
            lang_key = self.config.doc_qa.response_language
            system = _SYSTEM_PROMPT.format(
                lang_instruction=_LANG_INSTRUCTIONS.get(lang_key, _LANG_INSTRUCTIONS["hinglish"]),
                doc_title=self.retriever.document_title,
                context=context,
            )

            # 4. Generate answer
            answer = asyncio.run(self.llm.generate(question, system=system))
            elapsed = time.time() - t0

            log.info("Answer (%.1fs): %s", elapsed, answer[:100])

            # 5. Speak the answer
            self.hud.set_state("processing", "Speaking…")
            lang_code = {"hinglish": "hi", "hindi": "hi", "gujarati": "gu", "english": "en"}.get(lang_key, "hi")
            asyncio.run(self.tts.speak(answer, lang=lang_code))

            self.hud.set_state("done", f"{elapsed:.1f}s")

        except Exception as e:
            log.error("Doc Q&A error: %s", e, exc_info=True)
            self.hud.set_state("error")
        finally:
            self._processing = False

    def interrupt(self) -> None:
        """Interrupt the current TTS playback."""
        self.tts.stop()
        log.info("Doc Q&A: interrupted")

    @staticmethod
    def _format_context(chunks: list[Chunk]) -> str:
        """Format retrieved chunks into context string with citations."""
        if not chunks:
            return "(No relevant content found in the document)"

        parts = []
        for i, chunk in enumerate(chunks, 1):
            parts.append(f"[Source {i} — {chunk.citation}]\n{chunk.text}")
        return "\n\n".join(parts)
