"""Doc Q&A pipeline — voice question → RAG → LLM → TTS with citations.

Adheres to Tier 2 Requirements 12, 15, and 16:
- Long-context multilingual embeddings with calibrated refusal threshold.
- Prompt-injection hardening (<document_data> passive data barrier).
- Conversational memory for multi-turn follow-ups.
- Sentence-by-sentence streaming into TTS with Time-To-First-Audio (TTFA) reporting.
- Voice barge-in interruption via Silero VAD.
- Escape cancels active recording and TTS.
"""

import asyncio
import logging
import re
import threading
import time
from typing import List, Optional, Tuple

from bolsamajh.config import AppConfig
from bolsamajh.documents.chunker import Chunk
from bolsamajh.documents.loader import Document, load_document
from bolsamajh.documents.retriever import DocumentRetriever
from bolsamajh.llm.base import LLMAdapter
from bolsamajh.overlay.hud import OverlayHUD
from bolsamajh.stt.base import SpeechToText
from bolsamajh.tts.base import TextToSpeech
from bolsamajh.utils.audio import MicRecorder
from bolsamajh.utils.sentence_splitter import extract_next_sentence
from bolsamajh.utils.vad import BargeInMonitor, get_shared_vad

log = logging.getLogger(__name__)

from bolsamajh.prompts import _LANG_INSTRUCTIONS, _SYSTEM_PROMPT

# Deterministic refusal messages per language (returned without calling LLM)
_DETERMINISTIC_REFUSALS = {
    "hindi": "माफ़ कीजिए, मुझे दस्तावेज़ में इस सवाल का कोई प्रासंगिक उत्तर नहीं मिला।",
    "gujarati": "માફ કરશો, મને દસ્તાવેજમાં આ પ્રશ્નનો કોઈ સુસંગત જવાબ મળ્યો નથી.",
    "hinglish": "Maaf kijiye, mujhe document mein is sawaal ka koi relevant jawab nahi mila.",
    "english": "I apologize, but I could not find relevant information in the document to answer your question.",
}

_HINGLISH_KEYWORDS = {
    "kya",
    "kyun",
    "kaise",
    "kahan",
    "kab",
    "kitna",
    "kitne",
    "kitni",
    "kaun",
    "batao",
    "bataiye",
    "karo",
    "kariye",
    "hai",
    "hain",
    "nahi",
    "nahin",
    "mera",
    "meri",
    "mere",
    "mujhe",
    "apna",
    "apni",
    "apne",
    "yeh",
    "woh",
    "kuch",
    "dastavej",
    "yojana",
    "sawaal",
    "jawab",
    "chahiye",
    "hoga",
    "hogi",
    "hoge",
    "mein",
    "bhi",
    "aap",
    "unka",
    "iske",
    "iski",
}


class DocQAPipeline:
    """Talk to any document — voice question → RAG → LLM → streaming TTS."""

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
            refusal_threshold=config.doc_qa.refusal_threshold,
        )
        self.recorder = MicRecorder()
        self._current_document: Document | None = None
        self._history: List[Tuple[str, str]] = []  # List of (question, answer) pairs
        self._processing = False
        self._processing_lock = threading.Lock()
        self._worker_thread: Optional[threading.Thread] = None
        self._generation_id: int = 0
        self._cancel_requested: bool = False

    @property
    def has_document(self) -> bool:
        return self.retriever.is_loaded

    def load_document(self, source: str) -> str:
        """Load and index a document. Clears conversation memory."""
        try:
            self.hud.set_state("processing", "Loading doc…")
            doc = load_document(source)
            self._current_document = doc
            self._history.clear()
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
        with self._processing_lock:
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

        self._cancel_requested = False
        self._generation_id += 1
        active_gen = self._generation_id

        thread = threading.Thread(
            target=self._process_question,
            args=(wav_bytes, active_gen),
            daemon=True,
        )
        self._worker_thread = thread
        thread.start()

    def cancel(self) -> None:
        """Cancel recording or TTS playback immediately and join worker thread."""
        self._cancel_requested = True
        self._generation_id += 1
        if self.recorder.is_recording:
            self.recorder.cancel()
        self.tts.stop()

        # Join worker thread
        if self._worker_thread and self._worker_thread.is_alive():
            self._worker_thread.join(timeout=0.5)
            if not self._worker_thread.is_alive():
                self._worker_thread = None
        with self._processing_lock:
            self._processing = False

        self.hud.set_state("idle")
        log.info("Doc Q&A: cancelled by user")

    def interrupt(self) -> None:
        """Interrupt active TTS playback and stop entire remaining answer."""
        self._generation_id += 1
        self.tts.stop()
        self.hud.set_state("idle", "Interrupted")
        log.info("Doc Q&A: playback interrupted (generation advanced to %d)", self._generation_id)

    def _detect_language(self, text: str) -> str:
        """Detect language from question text when config is 'auto'."""
        if any("\u0a80" <= c <= "\u0aff" for c in text):
            return "gujarati"
        if any("\u0900" <= c <= "\u097f" for c in text):
            return "hindi"
        words = set(re.findall(r"\b[a-zA-Z]+\b", text.lower()))
        if words & _HINGLISH_KEYWORDS:
            return "hinglish"
        return "english"

    def _resolve_response_language(self, question: str) -> str:
        """Determine effective response language key from config and question."""
        config_lang = getattr(self.config.doc_qa, "response_language", "auto").lower()
        if config_lang == "auto":
            return self._detect_language(question)
        return config_lang

    def _process_question(self, wav_bytes: bytes, gen_id: int = 0) -> None:
        """Background: transcribe → retrieve → stream LLM into TTS."""
        with self._processing_lock:
            self._processing = True
        t0 = time.time()

        try:
            if self._cancel_requested or (gen_id and gen_id != self._generation_id):
                log.info("Process question aborted early (cancelled or superseded).")
                return

            # 1. Transcribe question
            result = self.stt.transcribe(wav_bytes)
            question = result.text.strip()
            if not question:
                self.hud.set_state("error")
                return

            if self._cancel_requested or (gen_id and gen_id != self._generation_id):
                return

            log.info("Question: %s", question)
            self.hud.set_state("processing", "Thinking…")

            # Resolve target response language (auto-detected or configured)
            lang_key = self._resolve_response_language(question)
            lang_code = {"hinglish": "hi", "hindi": "hi", "gujarati": "gu", "english": "en"}.get(
                lang_key, "hi"
            )

            # 2. Augment retrieval query with conversational history for follow-ups
            retrieval_query = question
            if self._history:
                recent_history_context = " ".join(q for q, _ in self._history[-2:])
                retrieval_query = f"{question} {recent_history_context}".strip()
                log.debug("Augmented retrieval query for follow-up: %s", retrieval_query)

            # Retrieve relevant chunks with calibrated threshold
            chunks = self.retriever.retrieve(
                retrieval_query,
                top_k=self.config.doc_qa.top_k,
                apply_threshold=True,
            )

            if self._cancel_requested or (gen_id and gen_id != self._generation_id):
                return

            # Deterministic refusal: if no chunk passes threshold, refuse WITHOUT calling LLM
            if not chunks:
                refusal_text = _DETERMINISTIC_REFUSALS.get(
                    lang_key, _DETERMINISTIC_REFUSALS["hinglish"]
                )
                log.info(
                    "Refusal triggered: no chunk exceeded threshold. Returning deterministic refusal: %s",
                    refusal_text,
                )
                self.hud.set_state("processing", "Speaking…")
                asyncio.run(self.tts.speak(refusal_text, lang=lang_code))
                elapsed = time.time() - t0
                self.hud.set_state("done", f"{elapsed:.1f}s")
                return

            # 3. Build grounded prompt with conversational memory
            context = self._format_context(chunks)

            history_str = ""
            if self._history:
                h_lines = ["RECENT CONVERSATION (for follow-up context):"]
                for q_prev, a_prev in self._history[-3:]:
                    h_lines.append(f"User: {q_prev}\nBolSamajh: {a_prev}")
                history_str = "\n".join(h_lines) + "\n"

            system = _SYSTEM_PROMPT.format(
                lang_instruction=_LANG_INSTRUCTIONS.get(lang_key, _LANG_INSTRUCTIONS["hinglish"]),
                doc_title=self.retriever.document_title,
                history_context=history_str,
                context=context,
            )

            # 4. Stream LLM output sentence-by-sentence into TTS with prefetching & voice barge-in
            answer = asyncio.run(
                self._stream_and_speak(question, system, lang_code, t_start=t0, gen_id=gen_id)
            )

            if self._cancel_requested or (gen_id and gen_id != self._generation_id):
                return

            elapsed = time.time() - t0
            log.info("Complete Answer (%.1fs): %s", elapsed, answer[:120])

            # Update conversational history
            if answer.strip():
                self._history.append((question, answer.strip()))
                if len(self._history) > 3:
                    self._history.pop(0)

            self.hud.set_state("done", f"{elapsed:.1f}s")

        except Exception as e:
            log.error("Doc Q&A error: %s", e, exc_info=True)
            self.hud.set_state("error")
        finally:
            with self._processing_lock:
                self._processing = False

    async def _stream_and_speak(
        self,
        question: str,
        system: str,
        lang_code: str,
        t_start: float,
        gen_id: int = 0,
    ) -> str:
        """Stream tokens from LLM, prefetch TTS synthesis (sentence N+1 during sentence N), and play."""
        buffer = ""
        full_tokens = []
        first_audio_logged = False

        # Load shared VAD singleton once; degrade gracefully (no barge-in) if unavailable
        shared_vad = get_shared_vad()
        headphone_mode = getattr(self.config, "headphone_mode", False)
        barge_in: Optional[BargeInMonitor] = None
        if shared_vad is not None:
            try:
                barge_in = BargeInMonitor(
                    on_barge_in=self.interrupt,
                    headphone_mode=headphone_mode,
                    vad=shared_vad,
                )
                if hasattr(self.tts, "set_playback_start_callback"):
                    self.tts.set_playback_start_callback(barge_in.notify_playback_start)
                barge_in.start()
            except Exception as e:
                log.warning(
                    "Silero VAD barge-in initialization failed (degraded without barge-in): %s", e
                )
                barge_in = None

        has_synthesize = hasattr(self.tts, "synthesize") and hasattr(self.tts, "play")

        if has_synthesize:
            # Bounded prefetch queue: holds up to 2 items (sentence_text, audio_bytes_or_none)
            tts_queue: asyncio.Queue[Optional[Tuple[str, Optional[bytes]]]] = asyncio.Queue(
                maxsize=2
            )

            async def _playback_worker():
                nonlocal first_audio_logged
                while True:
                    item = await tts_queue.get()
                    if item is None:
                        tts_queue.task_done()
                        break
                    sentence_text, audio_bytes = item
                    if self._cancel_requested or (gen_id and gen_id != self._generation_id):
                        tts_queue.task_done()
                        break

                    if not first_audio_logged:
                        ttfa = time.time() - t_start
                        log.info(
                            "⚡ Time-To-First-Audio (TTFA): %.2fs (first chunk: '%s')",
                            ttfa,
                            sentence_text[:40],
                        )
                        self.hud.set_state("processing", f"Speaking (TTFA {ttfa:.1f}s)")
                        first_audio_logged = True

                    try:
                        if audio_bytes:
                            await self.tts.play(audio_bytes)
                        else:
                            await self.tts.speak(sentence_text, lang=lang_code)
                    except Exception as ex:
                        log.error(
                            "TTS playback error for sentence '%s': %s", sentence_text[:30], ex
                        )
                    finally:
                        tts_queue.task_done()

            playback_task = asyncio.create_task(_playback_worker())

            try:
                async for token in self.llm.generate_stream(question, system=system):
                    if self._cancel_requested or (gen_id and gen_id != self._generation_id):
                        log.info(
                            "Doc Q&A stream stopped: generation %d interrupted/superseded", gen_id
                        )
                        break

                    buffer += token
                    full_tokens.append(token)

                    sentence, remaining = extract_next_sentence(buffer)
                    if sentence:
                        buffer = remaining
                        if self._cancel_requested or (gen_id and gen_id != self._generation_id):
                            break

                        # Prefetch synthesis
                        audio_bytes = None
                        try:
                            audio_bytes = await self.tts.synthesize(sentence, lang=lang_code)
                        except Exception as e:
                            log.warning("TTS prefetch synthesis failed: %s", e)
                        await tts_queue.put((sentence, audio_bytes))

                # Flush any remaining text in buffer
                if (
                    buffer.strip()
                    and not self._cancel_requested
                    and (not gen_id or gen_id == self._generation_id)
                ):
                    final_sentence = buffer.strip()
                    audio_bytes = None
                    try:
                        audio_bytes = await self.tts.synthesize(final_sentence, lang=lang_code)
                    except Exception as e:
                        log.warning("TTS prefetch synthesis failed: %s", e)
                    await tts_queue.put((final_sentence, audio_bytes))

                # Signal EOF to playback worker
                await tts_queue.put(None)
                await playback_task

            finally:
                if barge_in:
                    barge_in.stop()
                if not playback_task.done():
                    playback_task.cancel()
                    try:
                        await playback_task
                    except asyncio.CancelledError:
                        pass
        else:
            # Direct sequential synthesis for basic/mock TTS adapters
            try:
                async for token in self.llm.generate_stream(question, system=system):
                    if self._cancel_requested or (gen_id and gen_id != self._generation_id):
                        log.info(
                            "Doc Q&A stream stopped: generation %d interrupted/superseded", gen_id
                        )
                        break

                    buffer += token
                    full_tokens.append(token)

                    sentence, remaining = extract_next_sentence(buffer)
                    if sentence:
                        buffer = remaining
                        if self._cancel_requested or (gen_id and gen_id != self._generation_id):
                            break

                        if not first_audio_logged:
                            ttfa = time.time() - t_start
                            log.info(
                                "⚡ Time-To-First-Audio (TTFA): %.2fs (first chunk: '%s')",
                                ttfa,
                                sentence[:40],
                            )
                            self.hud.set_state("processing", f"Speaking (TTFA {ttfa:.1f}s)")
                            first_audio_logged = True

                        await self.tts.speak(sentence, lang=lang_code)

                # Flush any remaining text
                if (
                    buffer.strip()
                    and not self._cancel_requested
                    and (not gen_id or gen_id == self._generation_id)
                ):
                    if not first_audio_logged:
                        ttfa = time.time() - t_start
                        log.info("⚡ Time-To-First-Audio (TTFA): %.2fs", ttfa)
                        first_audio_logged = True
                    await self.tts.speak(buffer.strip(), lang=lang_code)

            finally:
                if barge_in:
                    barge_in.stop()

        return "".join(full_tokens)

    @staticmethod
    def _format_context(chunks: list[Chunk]) -> str:
        """Format retrieved chunks into context string with document-type-aware citations.

        Neutralizes </document_data> and closing tags within document text to prevent
        prompt injection from escaping the passive barrier.
        """
        if not chunks:
            return (
                "(No relevant content found in the document that exceeds the relevance threshold)"
            )

        parts = []
        for i, chunk in enumerate(chunks, 1):
            safe_text = chunk.text.replace("</document_data>", "<\\/document_data>")
            safe_text = safe_text.replace("</doc", "<\\/doc")
            parts.append(f"[Source {i} — {chunk.citation}]\n{safe_text}")
        return "\n\n".join(parts)
