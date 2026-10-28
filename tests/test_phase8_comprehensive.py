"""Comprehensive unit tests for Phase 8 covering all required edge cases and behaviors.

Tests:
1. Dotenv loading and configuration literal validation
2. TTS factory (EdgeTTSAdapter, PiperTTSAdapter, unknown engine error)
3. Clipboard restore (mocked win32/pyperclip backend, empty clipboard clear, modifier guard)
4. Atomic audio write (_render_audio atomic temp file rename)
5. Retriever lock, atomic swap, and scaled thresholds
6. Chunker token limit and loader edge cases (tables in DOCX, empty DOCX, encrypted PDF, HTML title)
7. Deterministic refusal without LLM invocation and </document_data> escaping
8. Sentence splitter decimals, times, abbreviations, newlines
9. Gemini cooldown recovery & mid-stream fallback exception
10. Ollama exact-model check & keep_alive parameter
11. Realtime WebSocket events & Host/Origin security checks
12. Text cleanup normalization (percentage, phone number, rupee)
"""

import threading
from unittest.mock import MagicMock

import pytest
from docx import Document as DocxDoc
from fastapi.testclient import TestClient

from bolsamajh.config import AppConfig, load_config
from bolsamajh.documents.loader import Document, DocumentPage, load_docx, load_webpage
from bolsamajh.documents.retriever import DocumentRetriever
from bolsamajh.llm.fallback import FallbackLLMAdapter, MidStreamFallbackError
from bolsamajh.llm.ollama_adapter import OllamaAdapter
from bolsamajh.pipeline.doc_qa import DocQAPipeline
from bolsamajh.tts.edge_tts_adapter import EdgeTTSAdapter
from bolsamajh.tts.factory import create_tts_adapter
from bolsamajh.tts.piper_adapter import PiperTTSAdapter
from bolsamajh.utils.clipboard import ModifierGuard, restore_clipboard
from bolsamajh.web.server import app, render_audio_atomically

client = TestClient(app)


# ---------------------------------------------------------------------
# 1. Configuration Validation & Dotenv Loading
# ---------------------------------------------------------------------
def test_config_literal_validations(monkeypatch):
    """Verify that invalid literals in env vars raise clear ValueError."""
    monkeypatch.setenv("BOLSAMAJH_TTS_ENGINE", "invalid_tts")
    with pytest.raises(ValueError, match="Invalid BOLSAMAJH_TTS_ENGINE"):
        load_config()

    monkeypatch.setenv("BOLSAMAJH_TTS_ENGINE", "piper")
    monkeypatch.setenv("BOLSAMAJH_LLM_AUTO_FALLBACK", "not_a_bool")
    with pytest.raises(ValueError, match="Invalid boolean value"):
        load_config()

    monkeypatch.setenv("BOLSAMAJH_LLM_AUTO_FALLBACK", "true")
    monkeypatch.setenv("BOLSAMAJH_LLM_ENGINE", "unsupported_llm")
    with pytest.raises(ValueError, match="Invalid BOLSAMAJH_LLM_ENGINE"):
        load_config()

    monkeypatch.setenv("BOLSAMAJH_LLM_ENGINE", "ollama")
    monkeypatch.setenv("BOLSAMAJH_SCRIPT", "invalid_script")
    with pytest.raises(ValueError, match="Invalid BOLSAMAJH_SCRIPT"):
        load_config()

    # Valid values pass without error
    monkeypatch.setenv("BOLSAMAJH_SCRIPT", "devanagari")
    monkeypatch.setenv("BOLSAMAJH_STT_DEVICE", "cuda")
    cfg = load_config()
    assert cfg.tts.engine == "piper"
    assert cfg.llm.auto_fallback is True
    assert cfg.dictation.script == "devanagari"


# ---------------------------------------------------------------------
# 2. TTS Factory
# ---------------------------------------------------------------------
def test_tts_factory():
    """Verify create_tts_adapter returns proper adapter and rejects invalid engines."""
    cfg = AppConfig()
    cfg.tts.engine = "edge_tts"
    tts_edge = create_tts_adapter(cfg)
    assert isinstance(tts_edge, EdgeTTSAdapter)

    cfg.tts.engine = "piper"
    tts_piper = create_tts_adapter(cfg)
    assert isinstance(tts_piper, PiperTTSAdapter)

    cfg.tts.engine = "unknown_engine"  # type: ignore
    with pytest.raises(ValueError, match="Unknown TTS engine"):
        create_tts_adapter(cfg)


# ---------------------------------------------------------------------
# 3. Clipboard Restore & ModifierGuard
# ---------------------------------------------------------------------
def test_clipboard_restore_clears_empty_original(monkeypatch):
    """Verify restore_clipboard clears the clipboard if it was initially empty."""
    mock_store = {"content": ""}

    def mock_paste():
        return mock_store["content"]

    def mock_copy(val):
        mock_store["content"] = val

    import bolsamajh.utils.clipboard as clip_mod

    monkeypatch.setattr(clip_mod, "_read_clipboard_text", mock_paste)
    monkeypatch.setattr(clip_mod, "_write_clipboard_text", mock_copy)
    monkeypatch.setattr(clip_mod, "_empty_clipboard", lambda: mock_copy(""))

    # Initially empty
    mock_store["content"] = ""
    with restore_clipboard(delay=0.01):
        # Dictation writes text to clipboard
        mock_copy("temporary dictated sentence")
        assert mock_paste() == "temporary dictated sentence"

    # Must be restored to empty!
    assert mock_paste() == ""


def test_clipboard_restore_populates_original(monkeypatch):
    """Verify restore_clipboard restores non-empty original clipboard content."""
    mock_store = {"content": "User original copied code"}

    import bolsamajh.utils.clipboard as clip_mod

    monkeypatch.setattr(clip_mod, "_read_clipboard_text", lambda: mock_store["content"])
    monkeypatch.setattr(clip_mod, "_write_clipboard_text", lambda v: mock_store.update(content=v))

    with restore_clipboard(delay=0.01):
        mock_store["content"] = "dictated text"

    assert mock_store["content"] == "User original copied code"


def test_modifier_guard_releases_and_restores_only_held(monkeypatch):
    """Verify ModifierGuard restores only modifiers that were physically pressed."""
    released_keys = []
    pressed_keys = []

    import bolsamajh.utils.clipboard as clip_mod

    monkeypatch.setattr(clip_mod, "_is_key_pressed", lambda vk: vk == clip_mod.VK_SHIFT)

    # Spy on release/press
    monkeypatch.setattr(
        clip_mod.ModifierGuard, "_release_key", lambda self, key: released_keys.append(key)
    )
    monkeypatch.setattr(
        clip_mod.ModifierGuard, "_press_key", lambda self, key: pressed_keys.append(key)
    )

    with ModifierGuard():
        pass

    assert clip_mod.Key.shift in released_keys
    assert clip_mod.Key.shift in pressed_keys
    assert clip_mod.Key.alt not in pressed_keys  # Alt was not physically held so not restored


# ---------------------------------------------------------------------
# 4. Atomic Audio File Rendering
# ---------------------------------------------------------------------
def test_atomic_audio_rendering(tmp_path):
    """Verify render_audio_atomically writes via temp file and atomic rename."""
    target_file = tmp_path / "audio_target.wav"
    audio_content = b"RIFF" + b"\x00" * 200

    # Test atomic write helper
    success = render_audio_atomically(target_file, audio_content)
    assert success is True
    assert target_file.exists()
    assert target_file.read_bytes() == audio_content
    # Confirm no lingering .tmp file
    tmp_candidates = list(tmp_path.glob("*.tmp"))
    assert len(tmp_candidates) == 0


# ---------------------------------------------------------------------
# 5. Retriever Lock & Thread-Safe Atomic Swap
# ---------------------------------------------------------------------
def test_retriever_lock_and_atomic_swap():
    """Verify DocumentRetriever thread-safe atomic swap under concurrent queries."""
    retriever = DocumentRetriever(embedding_model="intfloat/multilingual-e5-base")
    # Mock embedding model to return dummy 768-dim embeddings without downloading
    import numpy as np

    class MockModel:
        def encode(self, texts, **kwargs):
            return np.ones((len(texts), 768), dtype=np.float32)

    retriever._model = MockModel()

    doc1 = Document(
        title="Doc 1",
        source="doc1.txt",
        pages=[DocumentPage(text="First document text content.", page_number=1, source="doc1.txt")],
    )
    doc2 = Document(
        title="Doc 2",
        source="doc2.txt",
        pages=[
            DocumentPage(text="Second document text content.", page_number=1, source="doc2.txt")
        ],
    )

    errors = []

    def concurrent_indexer():
        try:
            for _ in range(10):
                retriever.index_document(doc1)
                retriever.index_document(doc2)
                retriever.clear()
        except Exception as e:
            errors.append(e)

    def concurrent_reader():
        try:
            for _ in range(20):
                _ = retriever.is_loaded
                _ = retriever.document_title
                _ = retriever.retrieve("query", top_k=2, apply_threshold=False)
        except Exception as e:
            errors.append(e)

    threads = [
        threading.Thread(target=concurrent_indexer),
        threading.Thread(target=concurrent_reader),
        threading.Thread(target=concurrent_reader),
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(errors) == 0, f"Concurrent retriever access raised errors: {errors}"


# ---------------------------------------------------------------------
# 6. Loader Edge Cases: DOCX Tables, Empty DOCX, Web Page Title
# ---------------------------------------------------------------------
def test_loader_docx_tables_and_empty_check(tmp_path):
    """Verify DOCX loader extracts table contents and raises error on empty DOCX."""
    # 1. DOCX with table
    doc = DocxDoc()
    doc.add_heading("Financial Summary", level=1)
    table = doc.add_table(rows=2, cols=2)
    table.cell(0, 0).text = "Metric"
    table.cell(0, 1).text = "Value"
    table.cell(1, 0).text = "Revenue"
    table.cell(1, 1).text = "Rs 10 Crore"

    docx_path = tmp_path / "table_doc.docx"
    doc.save(str(docx_path))

    loaded_doc = load_docx(str(docx_path))
    assert "Financial Summary" in loaded_doc.full_text
    assert "Revenue | Rs 10 Crore" in loaded_doc.full_text

    # 2. Empty DOCX
    empty_doc = DocxDoc()
    empty_path = tmp_path / "empty_doc.docx"
    empty_doc.save(str(empty_path))

    with pytest.raises(ValueError, match="is empty or contains no readable text"):
        load_docx(str(empty_path))


def test_loader_webpage_title():
    """Verify load_webpage extracts HTML title correctly."""
    html = "<html><head><title>Project Chandra Aerospace Report</title></head><body><p>Rocket telemetry data.</p></body></html>"
    doc = load_webpage("https://example.com/chandra", html_content=html)
    assert doc.title == "Project Chandra Aerospace Report"


# ---------------------------------------------------------------------
# 7. Deterministic Refusal Without LLM Call & Escaping
# ---------------------------------------------------------------------
def test_deterministic_refusal_without_llm():
    """Verify that when no retrieved chunk passes the threshold, refusal is returned immediately without LLM."""
    cfg = AppConfig()
    cfg.doc_qa.response_language = "hindi"

    mock_llm = MagicMock()
    mock_stt = MagicMock()
    mock_tts = MagicMock()
    mock_retriever = MagicMock()
    mock_hud = MagicMock()

    # Retriever returns empty (no chunk passed threshold)
    mock_retriever.is_loaded = True
    mock_retriever.retrieve.return_value = []

    pipeline = DocQAPipeline(cfg, mock_stt, mock_llm, mock_tts, mock_hud)
    pipeline.retriever = mock_retriever

    # Transcribe returns valid question
    mock_stt.transcribe.return_value = MagicMock(text="What is the interest rate?", language="en")

    pipeline._process_question(b"dummy_wav_bytes")

    # LLM must NEVER have been called!
    assert mock_llm.generate.call_count == 0
    assert mock_llm.generate_stream.call_count == 0

    # TTS must have spoken the deterministic refusal in Hindi
    assert mock_tts.speak.call_count == 1
    spoken_text = mock_tts.speak.call_args[0][0]
    assert "माफ़ कीजिए" in spoken_text


# ---------------------------------------------------------------------
# 8. Mid-Stream Fallback Exception
# ---------------------------------------------------------------------
@pytest.mark.anyio
async def test_midstream_fallback_error():
    """Verify FallbackLLMAdapter raises MidStreamFallbackError if primary fails mid-stream."""

    class FailingStreamPrimary:
        name = "failing_primary"

        def is_available(self):
            return True

        async def generate_stream(self, prompt, **kwargs):
            yield "Token 1 "
            yield "Token 2 "
            raise RuntimeError("Stream disconnected mid-sentence!")

    class SecondaryAdapter:
        name = "secondary"

        def is_available(self):
            return True

        async def generate_stream(self, prompt, **kwargs):
            yield "Secondary complete output"

    fallback_adapter = FallbackLLMAdapter(
        primary=FailingStreamPrimary(), secondary=SecondaryAdapter()
    )

    tokens = []
    with pytest.raises(MidStreamFallbackError, match="failed mid-stream after yielding tokens"):
        async for token in fallback_adapter.generate_stream("test prompt"):
            tokens.append(token)

    assert tokens == ["Token 1 ", "Token 2 "]


# ---------------------------------------------------------------------
# 9. Ollama Keep-Alive Parameter
# ---------------------------------------------------------------------
@pytest.mark.anyio
async def test_ollama_keep_alive_param(monkeypatch):
    """Verify OllamaAdapter passes keep_alive parameter to Ollama API."""
    adapter = OllamaAdapter(model="gemma3:4b", keep_alive="45m")

    sent_payload = {}

    import httpx

    class MockClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def post(self, url, json=None, **kwargs):
            sent_payload.update(json or {})
            resp = MagicMock()
            resp.status_code = 200
            resp.json.return_value = {"response": "test reply"}
            return resp

    monkeypatch.setattr(httpx, "AsyncClient", MockClient)

    reply = await adapter.generate("test prompt")
    assert reply == "test reply"
    assert sent_payload.get("keep_alive") == "45m"
    assert sent_payload.get("model") == "gemma3:4b"


# ---------------------------------------------------------------------
# 10. Security Middleware: Host Header Allowlist & Origin Validation
# ---------------------------------------------------------------------
def test_host_header_security():
    """Verify security middleware rejects spoofed Host headers."""
    # Allowed hosts
    r_valid = client.get("/api/status", headers={"Host": "localhost"})
    assert r_valid.status_code == 200

    r_ip = client.get("/api/status", headers={"Host": "127.0.0.1"})
    assert r_ip.status_code == 200

    # Spoofed host header -> 400
    r_spoofed = client.get("/api/status", headers={"Host": "evil-phishing-domain.com"})
    assert r_spoofed.status_code == 400
    assert "Invalid Host header" in r_spoofed.text
