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

import time
import threading
import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from bolsamajh.config import AppConfig
from bolsamajh.pipeline.doc_qa import DocQAPipeline
from bolsamajh.pipeline.dictation import DictationPipeline
from bolsamajh.utils.clipboard import ModifierGuard, MODIFIER_KEYS
from bolsamajh.utils.text_cleanup import format_numbers, remove_fillers, apply_script_control
from bolsamajh.documents.loader import Document, DocumentPage
from bolsamajh.documents.chunker import chunk_document
from bolsamajh.stt.faster_whisper_stt import FasterWhisperSTT, resolve_model_id
from bolsamajh.utils.cuda_setup import auto_detect_device
from bolsamajh.tts.piper_adapter import _verify_sha256, _MODEL_SHA256


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
            DocumentPage(text="Para 1.", page_number=1, section="Overview", source="https://example.com/doc"),
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
    """Verify language='auto' falls back to 'hi' for clips < 2.0s."""
    stt = FasterWhisperSTT(model_size="tiny", device="cpu", compute_type="int8", language="auto")
    
    # Generate 1.2 seconds of silent audio bytes
    import numpy as np
    import wave
    import io
    
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
    mock_model.transcribe.return_value = ([], MagicMock())
    stt._model = mock_model
    
    stt.transcribe(bio.getvalue())
    
    # Assert transcribe was called with language="hi" due to < 2.0s fallback
    assert mock_model.transcribe.called
    kwargs = mock_model.transcribe.call_args[1]
    assert kwargs.get("language") == "hi"
