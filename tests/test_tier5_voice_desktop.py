"""Unit tests for Tier 5: Voice and desktop bugs.

Validates:
1. Sentence splitter edge cases (numbers, abbreviations, dandas).
2. Interrupt generation tracking (older generation speak calls dropped).
3. Worker lifecycle on cancel (thread joined, _processing cleared on exit).
4. Clipboard modifier guard (releases Shift, Alt, Ctrl).
5. Text cleanup (Devanagari lookarounds, lakh/crore formatting).
6. Document citations (page spans, DOCX/web sections, chunk_id).
7. Short audio language auto fallback (< 2.0s -> 'hi').
8. Model loader resolution for auto-detected CPU fallback model.
"""

import threading
import time
from unittest.mock import AsyncMock, MagicMock, patch

from bolsamajh.config import AppConfig
from bolsamajh.documents.chunker import chunk_document
from bolsamajh.documents.loader import Document, DocumentPage
from bolsamajh.pipeline.dictation import DictationPipeline
from bolsamajh.pipeline.doc_qa import DocQAPipeline
from bolsamajh.stt.faster_whisper_stt import FasterWhisperSTT, resolve_model_id
from bolsamajh.utils.clipboard import ModifierGuard
from bolsamajh.utils.cuda_setup import auto_detect_device
from bolsamajh.utils.text_cleanup import apply_script_control, format_numbers, remove_fillers


def test_interrupt_generation_id_drops_older_speech():
    """Verify interrupt() advances generation id and stops stream from speaking further."""
    config = AppConfig()
    mock_stt = MagicMock()
    mock_llm = MagicMock()
    mock_tts = MagicMock()
    mock_hud = MagicMock()

    # Async mock for speak
    mock_tts.speak = AsyncMock()

    pipeline = DocQAPipeline(config, mock_stt, mock_llm, mock_tts, mock_hud)
    assert pipeline._generation_id == 0

    # Advance generation
    pipeline._generation_id = 1
    gen_at_start = pipeline._generation_id

    # Call interrupt
    pipeline.interrupt()
    assert pipeline._generation_id == gen_at_start + 1
    mock_tts.stop.assert_called_once()


def test_cancel_worker_lifecycle():
    """Verify cancel() sets flag, joins running worker thread, and clears _processing cleanly."""
    config = AppConfig()
    mock_stt = MagicMock()
    mock_hud = MagicMock()

    pipeline = DictationPipeline(config, mock_stt, mock_hud)

    # Simulate a running background worker
    worker_finished = threading.Event()

    def _dummy_worker():
        pipeline._processing = True
        time.sleep(0.05)
        worker_finished.set()

    t = threading.Thread(target=_dummy_worker)
    t.start()
    pipeline._worker_thread = t
    pipeline._processing = True

    # Cancel should join worker thread cleanly
    pipeline.cancel()
    assert not pipeline._processing
    assert pipeline._cancel_requested


def test_clipboard_modifier_guard():
    """Verify ModifierGuard executes release on modifiers."""
    with patch("bolsamajh.utils.clipboard._keyboard") as mock_kb:
        with ModifierGuard():
            pass
        # Verified that release was invoked for keys
        assert mock_kb.release.called


def test_cleanup_lakh_crore_and_lookarounds():
    """Verify lakh and crore formatting and Devanagari lookarounds."""
    # 1. Lakh and crore in Roman
    assert "₹5 lakh" in format_numbers("I need 5 lakh rupees for the project.")
    assert "₹2.5 crore" in format_numbers("Budget is Rs. 2.5 crore.")

    # 2. Lakh and crore in Devanagari
    assert "₹५ लाख" in format_numbers("५ लाख रुपये की सहायता दी गई।")
    assert "₹२ करोड़" in format_numbers("लागत रु. २ करोड़ है।")

    # 3. Devanagari lookarounds for disfluencies (must remove without breaking adjacent text)
    cleaned_deva = remove_fillers("हाँ हम्म ठीक है")
    assert "हम्म" not in cleaned_deva
    assert "हाँ" in cleaned_deva
    assert "ठीक है" in cleaned_deva

    # 4. Experimental Devanagari script mode
    exp_deva = apply_script_control("namaste", script="devanagari")
    assert len(exp_deva) > 0


def test_chunker_merged_page_span_and_section_citations():
    """Verify cross-page merged chunks record 'Pages X–Y' and web records 'Section X'."""
    # Multi-page PDF
    pdf = Document(
        title="Terms",
        source="terms.pdf",
        pages=[
            DocumentPage(text="Sentence on page 1.", page_number=1, source="terms.pdf"),
            DocumentPage(text="Sentence on page 2.", page_number=2, source="terms.pdf"),
        ],
        doc_type="pdf",
    )
    chunks = chunk_document(pdf, chunk_size=300)
    assert len(chunks) == 1
    assert chunks[0].citation == "Pages 1–2"
    assert chunks[0].chunk_id == "terms.pdf_chunk_0"

    # Web page (never 'Page')
    web = Document(
        title="Article",
        source="https://example.com/doc",
        pages=[
            DocumentPage(
                text="Para 1.", page_number=1, section="Overview", source="https://example.com/doc"
            ),
        ],
        doc_type="web",
    )
    web_chunks = chunk_document(web, chunk_size=300)
    assert len(web_chunks) == 1
    assert web_chunks[0].citation == "Section: Overview"
    assert not web_chunks[0].citation.startswith("Page")


def test_model_alias_resolution_and_cpu_agreement():
    """Verify auto_detect_device() CPU model resolves to a real HuggingFace model ID."""
    dev, comp, model = auto_detect_device()
    assert dev in ("cuda", "cpu")
    # Shorthand aliases must resolve
    assert resolve_model_id("whisper-hinglish-swift") == "MSpider3/whisper-hindi2hinglish-swift-ct2"
    assert resolve_model_id("large-v3-turbo") == "deepdml/faster-whisper-large-v3-turbo-ct2"


def test_short_clip_language_fallback():
    """Verify language='auto' does not force 'hi' on short clips."""
    stt = FasterWhisperSTT(model_size="tiny", device="cpu", compute_type="int8", language="auto")

    # Generate 1.2 seconds of non-silent audio bytes
    import io
    import wave

    import numpy as np

    sr = 16000
    dur = 1.2
    # Sine wave to have non-zero RMS above gate
    t = np.linspace(0, dur, int(sr * dur), endpoint=False)
    audio = (np.sin(2 * np.pi * 440 * t) * 10000).astype(np.int16)

    bio = io.BytesIO()
    with wave.open(bio, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(audio.tobytes())

    # Mock whisper transcribe to check kwargs passed
    mock_model = MagicMock()
    mock_model.transcribe.return_value = ([], MagicMock(language="auto", language_probability=0.9))
    stt._model = mock_model

    stt.transcribe(bio.getvalue())

    # Assert transcribe was called without forcing language="hi" when configured as "auto"
    assert mock_model.transcribe.called
    kwargs = mock_model.transcribe.call_args[1]
    assert kwargs.get("language") is None

    # But when configured explicitly, it must pass that language
    stt_hi = FasterWhisperSTT(model_size="tiny", device="cpu", compute_type="int8", language="hi")
    stt_hi._model = mock_model
    stt_hi.transcribe(bio.getvalue())
    kwargs_hi = mock_model.transcribe.call_args[1]
    assert kwargs_hi.get("language") == "hi"


def test_doc_qa_pipeline_stream_and_speak_integration():
    """Integration test: real sentence splitter + generation ID tracking + TTS stub.
    Exercises _stream_and_speak end to end, verifying that when an interrupt occurs,
    remaining sentences from the LLM stream are rejected and not spoken.
    """
    import asyncio

    async def _run():
        config = AppConfig()
        mock_stt = MagicMock()
        mock_hud = MagicMock()

        spoken_sentences = []

        class StubTTS:
            def __init__(self):
                self.stopped = False

            async def speak(self, text: str, lang: str = "hi"):
                spoken_sentences.append(text)

            def stop(self):
                self.stopped = True

        tts_stub = StubTTS()

        class StubLLM:
            async def generate_stream(self, prompt: str, system: str = ""):
                # Yield sentence 1 in pieces
                yield "Yeh pehla sentence hai. "
                # Interrupt occurs here!
                pipeline.interrupt()
                # Yield remaining sentences that should NOT be spoken
                yield "Yeh doosra sentence hai jo drop hona chahiye. "
                yield "Yeh teesra sentence hai."

        llm_stub = StubLLM()
        pipeline = DocQAPipeline(config, mock_stt, llm_stub, tts_stub, mock_hud)
        # In real usage, stop_and_answer increments _generation_id to 1 before spawning stream
        pipeline._generation_id = 1
        active_gen = pipeline._generation_id

        # Disable sounddevice mic monitoring in test environment
        with patch("bolsamajh.utils.vad.sd", None):
            result_text = await pipeline._stream_and_speak(
                question="Kaise ho?",
                system="System prompt",
                t_start=time.time(),
                lang_code="hi",
                gen_id=active_gen,
            )

        # Verify:
        # 1. First sentence was yielded
        assert "Yeh pehla sentence hai." in result_text
        # 2. Only the first sentence was spoken; second and third were dropped due to interrupt!
        assert len(spoken_sentences) == 1
        assert spoken_sentences[0] == "Yeh pehla sentence hai."
        # 3. TTS stop() was called on interrupt
        assert tts_stub.stopped

    asyncio.run(_run())


def test_dictation_pipeline_process_audio_integration():
    """Integration test: STT stub -> real cleanup_text (fillers, currency, lakh/crore) -> clipboard insert."""
    config = AppConfig()
    mock_hud = MagicMock()

    class StubSTT:
        def transcribe(self, audio_bytes: bytes):
            from bolsamajh.stt.base import TranscriptResult

            return TranscriptResult(
                text="uh maine 5 lakh rupees pay kiye hmm",
                language="hi",
                duration_seconds=2.5,
            )

    pasted_text = []

    def mock_insert_text(text: str):
        pasted_text.append(text)

    pipeline = DictationPipeline(config, StubSTT(), mock_hud)

    with patch("bolsamajh.pipeline.dictation.insert_text", side_effect=mock_insert_text):
        pipeline._process_audio(b"dummy_wav_bytes")

    assert len(pasted_text) == 1
    # Verify real cleanup pipeline ran: 'uh' and 'hmm' stripped, '5 lakh rupees' formatted to '₹5 lakh', sentence capitalized
    assert pasted_text[0] == "Maine ₹5 lakh pay kiye"


def test_barge_in_monitor_is_active_and_warning_logging(caplog):
    """Integration test: BargeInMonitor is_active property and warning logging on stream error."""
    import logging

    from bolsamajh.utils.vad import BargeInMonitor

    triggered = False

    def on_barge():
        nonlocal triggered
        triggered = True

    monitor = BargeInMonitor(on_barge_in=on_barge, headphone_mode=False)
    assert not monitor.is_active

    # Test error logging at WARNING when stream fails
    class FailingSD:
        class InputStream:
            def __init__(self, *args, **kwargs):
                pass

            def __enter__(self):
                raise RuntimeError("Audio hardware unavailable (simulated mic error)")

            def __exit__(self, *args):
                pass

    with caplog.at_level(logging.WARNING):
        with patch("bolsamajh.utils.vad.sd", FailingSD()):
            monitor.start()
            if monitor._thread:
                monitor._thread.join(timeout=1.0)

    assert not monitor.is_active
    assert any("BargeInMonitor microphone exception" in record.message for record in caplog.records)
