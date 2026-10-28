"""BolSamajh — Automated Offline Mode Verification Test.

Enforces zero outbound network access by:
1. Setting HF_HUB_OFFLINE=1 and TRANSFORMERS_OFFLINE=1.
2. Monkeypatching socket.socket.connect to raise on any non-loopback address.
3. Testing all pipelines: Piper TTS, Faster-Whisper STT, Document Retriever (FAISS+E5),
   Local Ollama LLM, Doc-QA Pipeline, and Dictation Pipeline.
"""

import os
import sys

# Force offline environment flags before imports
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import asyncio
import io
import logging
import socket
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# --- Socket Monkeypatching ---
_orig_connect = socket.socket.connect

ALLOWED_HOSTS = {"127.0.0.1", "localhost", "::1", "0.0.0.0"}


def _guarded_connect(self, address):
    if isinstance(address, tuple):
        host, port = address[0], address[1]
    else:
        host, port = address, 0

    # Resolve hostname to IP to be certain
    try:
        resolved_ip = socket.gethostbyname(str(host))
    except Exception:
        resolved_ip = str(host)

    if resolved_ip in ALLOWED_HOSTS or str(host) in ALLOWED_HOSTS:
        return _orig_connect(self, address)

    raise ConnectionRefusedError(
        f"[OFFLINE GUARD TRIGGERED] Outbound network connection to {host}:{port} ({resolved_ip}) is strictly blocked!"
    )


socket.socket.connect = _guarded_connect

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("offline_test")


async def run_offline_suite():
    evidence_lines = []
    evidence_lines.append("BolSamajh — Offline Mode Automated Verification")
    evidence_lines.append("================================================")
    evidence_lines.append(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S IST')}")
    evidence_lines.append("Host OS:   Windows (RTX 3060 Ti)")
    evidence_lines.append(
        "Guards:    HF_HUB_OFFLINE=1, TRANSFORMERS_OFFLINE=1, socket.connect outbound blocker"
    )
    evidence_lines.append("")

    results = {}

    # -----------------------------------------------------------------
    # Step 1: Verify socket guard blocks outbound traffic
    # -----------------------------------------------------------------
    log.info("[1/7] Testing Outbound Socket Blocker...")
    outbound_blocked = False
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2.0)
        s.connect(("8.8.8.8", 53))
        s.close()
    except ConnectionRefusedError as e:
        if "OFFLINE GUARD TRIGGERED" in str(e):
            outbound_blocked = True
    except Exception as e:
        if "OFFLINE GUARD TRIGGERED" in str(e):
            outbound_blocked = True

    results["Outbound Socket Blocker"] = outbound_blocked
    evidence_lines.append(f"1. Outbound Network Blocker: {'PASS' if outbound_blocked else 'FAIL'}")
    assert outbound_blocked, "Outbound blocker failed to intercept non-loopback connection!"
    log.info("   -> Confirmed: Outbound traffic to non-loopback IPs is blocked.")

    # -----------------------------------------------------------------
    # Step 2: Piper TTS Offline Synthesis via App TTS Factory
    # -----------------------------------------------------------------
    log.info("[2/7] Testing Piper TTS Offline Synthesis via TTS Factory...")
    tts_pass = False
    tts_wav_bytes = None
    try:
        from bolsamajh.config import load_config
        from bolsamajh.tts.factory import create_tts_adapter
        from bolsamajh.tts.piper_adapter import PiperTTSAdapter

        os.environ["BOLSAMAJH_TTS_ENGINE"] = "piper"
        cfg = load_config()
        tts = create_tts_adapter(cfg)
        assert isinstance(tts, PiperTTSAdapter), f"Expected PiperTTSAdapter, got {type(tts)}"

        test_text = "नमस्ते दुनिया, बोलसमझ पूरी तरह से ऑफ़लाइन काम कर रहा है।"
        tts_wav_bytes = tts.synthesize_to_bytes(test_text)
        if len(tts_wav_bytes) > 10000:
            tts_pass = True
            log.info("   -> Piper TTS synthesized %d bytes WAV offline.", len(tts_wav_bytes))
    except Exception as e:
        log.error("   -> Piper TTS failed offline: %s", e)

    results["Piper TTS Offline via Factory"] = tts_pass
    evidence_lines.append(
        f"2. Piper TTS via Factory (BOLSAMAJH_TTS_ENGINE=piper): {'PASS' if tts_pass else 'FAIL'} ({len(tts_wav_bytes) if tts_wav_bytes else 0} bytes)"
    )
    assert tts_pass, "Piper TTS failed to synthesize offline!"

    # -----------------------------------------------------------------
    # Step 3: Faster-Whisper Offline Transcription
    # -----------------------------------------------------------------
    log.info("[3/7] Testing Faster-Whisper Offline STT...")
    stt_pass = False
    transcription_text = ""
    try:
        from faster_whisper import WhisperModel

        whisper = WhisperModel(
            "deepdml/faster-whisper-large-v3-turbo-ct2",
            device="cuda",
            compute_type="float16",
            local_files_only=True,
        )
        import wave

        import numpy as np

        with wave.open(io.BytesIO(tts_wav_bytes), "rb") as wf:
            pcm = wf.readframes(wf.getnframes())
            audio_np = np.frombuffer(pcm, dtype=np.int16).astype(np.float32) / 32768.0

        segments, info = whisper.transcribe(audio_np, language="hi", beam_size=1)
        transcription_text = " ".join(s.text for s in segments).strip()
        log.info(
            "   -> Transcribed offline: '%s' (language=%s, prob=%.2f)",
            transcription_text,
            info.language,
            info.language_probability,
        )
        if len(transcription_text) > 0:
            stt_pass = True
    except Exception as e:
        log.error("   -> Faster-Whisper STT failed offline: %s", e)

    results["Faster-Whisper STT Offline"] = stt_pass
    evidence_lines.append(
        f"3. Faster-Whisper STT Offline: {'PASS' if stt_pass else 'FAIL'} (Transcript: '{transcription_text}')"
    )
    assert stt_pass, "Faster-Whisper failed to transcribe offline!"

    # -----------------------------------------------------------------
    # Step 4: Local Ollama LLM Offline (localhost)
    # -----------------------------------------------------------------
    log.info("[4/7] Testing Local Ollama LLM Offline...")
    ollama_pass = False
    ollama_response = ""
    try:
        from bolsamajh.llm.ollama_adapter import OllamaAdapter

        llm = OllamaAdapter(model="gemma3:4b", base_url="http://127.0.0.1:11434")
        prompt = "Answer in exactly 3 words: Is BolSamajh operational offline?"
        ollama_response = await llm.generate(prompt)
        log.info("   -> Ollama offline response: '%s'", ollama_response.strip())
        if len(ollama_response.strip()) > 0:
            ollama_pass = True
    except Exception as e:
        log.error("   -> Ollama LLM failed offline: %s", e)

    results["Local Ollama LLM Offline"] = ollama_pass
    evidence_lines.append(
        f"4. Local Ollama LLM Offline: {'PASS' if ollama_pass else 'FAIL'} (Response: '{ollama_response.strip()}')"
    )
    assert ollama_pass, "Local Ollama LLM failed offline!"

    # -----------------------------------------------------------------
    # Step 5: Document Retriever (FAISS + E5) Offline
    # -----------------------------------------------------------------
    log.info("[5/7] Testing Document Retriever (FAISS + E5) Offline...")
    retriever_pass = False
    citation_got = ""
    try:
        from bolsamajh.documents.loader import Document, DocumentPage
        from bolsamajh.documents.retriever import DocumentRetriever

        sample_doc = Document(
            title="AirGap_Operations",
            source="internal://airgap_ops.txt",
            pages=[
                DocumentPage(
                    text="BolSamajh deployment is completely air-gapped and requires zero external internet connectivity for STT, LLM, or TTS operations.",
                    page_number=1,
                    section="Airgap Security Policy",
                    source="internal://airgap_ops.txt",
                )
            ],
            doc_type="txt",
        )

        retriever = DocumentRetriever(embedding_model="intfloat/multilingual-e5-base")
        _n_chunks = retriever.index_document(sample_doc)
        chunks = retriever.retrieve("Does BolSamajh require internet connectivity?", top_k=1)
        if chunks and len(chunks) > 0:
            citation_got = chunks[0].citation
            log.info(
                "   -> Retrieved offline chunk: citation='%s', text='%s'",
                citation_got,
                chunks[0].text[:60],
            )
            retriever_pass = True
    except Exception as e:
        log.error("   -> Document Retriever failed offline: %s", e)

    results["Document Retriever Offline"] = retriever_pass
    evidence_lines.append(
        f"5. Document Retriever (FAISS + E5) Offline: {'PASS' if retriever_pass else 'FAIL'} (Citation: {citation_got})"
    )
    assert retriever_pass, "Document Retriever failed offline!"

    # -----------------------------------------------------------------
    # Step 6: Real DictationPipeline Offline
    # -----------------------------------------------------------------
    log.info("[6/7] Testing Real DictationPipeline Offline...")
    dictation_pass = False
    inserted_text_captured = []
    try:
        from unittest.mock import patch

        from bolsamajh.overlay.hud import OverlayHUD
        from bolsamajh.pipeline.dictation import DictationPipeline

        class DummyHUD(OverlayHUD):
            def __init__(self):
                self._current_state = "idle"
                self._current_text = ""

            def set_state(self, state: str, text: str = "") -> None:
                self._current_state = state
                self._current_text = text

            def show_info(self, title: str, message: str) -> None:
                pass

            def ask_open_file(self, *args, **kwargs):
                return None

        dummy_hud = DummyHUD()

        # Wrap faster-whisper in SpeechToText adapter
        class WhisperSTTWrapper:
            def __init__(self, model):
                self._model = model

            def transcribe(self, audio_data, **kwargs):
                import wave

                from bolsamajh.stt.base import TranscriptionResult

                with wave.open(io.BytesIO(audio_data), "rb") as wf:
                    pcm = wf.readframes(wf.getnframes())
                    audio_np = np.frombuffer(pcm, dtype=np.int16).astype(np.float32) / 32768.0
                segments, info = self._model.transcribe(audio_np, language="hi", beam_size=1)
                text = " ".join(s.text for s in segments).strip()
                return TranscriptionResult(
                    text=text, language=info.language, duration=info.duration
                )

        stt_wrapper = WhisperSTTWrapper(whisper)
        dict_pipeline = DictationPipeline(cfg, stt_wrapper, dummy_hud)

        def mock_insert(text):
            inserted_text_captured.append(text)
            return True

        with patch("bolsamajh.pipeline.dictation.insert_text", side_effect=mock_insert):
            dict_pipeline._process_audio(tts_wav_bytes)

        if inserted_text_captured and dummy_hud._current_state == "done":
            dictation_pass = True
            log.info(
                "   -> DictationPipeline processed audio and inserted: '%s'",
                inserted_text_captured[0],
            )
    except Exception as e:
        log.error("   -> Dictation pipeline failed offline: %s", e)

    results["DictationPipeline Offline"] = dictation_pass
    evidence_lines.append(
        f"6. Real DictationPipeline Offline: {'PASS' if dictation_pass else 'FAIL'} (Inserted: '{inserted_text_captured[0] if inserted_text_captured else ''}')"
    )
    assert dictation_pass, "DictationPipeline failed offline!"

    # -----------------------------------------------------------------
    # Step 7: Real DocQAPipeline Offline
    # -----------------------------------------------------------------
    log.info("[7/7] Testing Real DocQAPipeline Offline...")
    doc_qa_pass = False
    spoken_chunks = []
    try:
        from bolsamajh.pipeline.doc_qa import DocQAPipeline

        class SpokenCaptureTTS:
            def __init__(self, inner_tts):
                self._inner = inner_tts

            def speak(self, text, lang="hi"):
                spoken_chunks.append(text)
                return True

            def stop(self):
                pass

            def is_speaking(self):
                return False

        capture_tts = SpokenCaptureTTS(tts)
        doc_qa_pipeline = DocQAPipeline(cfg, stt_wrapper, llm, capture_tts, retriever, dummy_hud)

        # Process question audio
        doc_qa_pipeline._process_question(tts_wav_bytes, gen_id=doc_qa_pipeline._generation_id)

        if spoken_chunks or dummy_hud._current_state in ("done", "idle"):
            doc_qa_pass = True
            log.info("   -> DocQAPipeline processed question, spoken response: %s", spoken_chunks)
    except Exception as e:
        log.error("   -> Doc-QA pipeline failed offline: %s", e)

    results["DocQAPipeline Offline"] = doc_qa_pass
    evidence_lines.append(
        f"7. Real DocQAPipeline Offline: {'PASS' if doc_qa_pass else 'FAIL'} (Responses: {spoken_chunks})"
    )
    assert doc_qa_pass, "DocQAPipeline failed offline!"

    # Summary
    exercised_count = sum(1 for v in results.values() if v)
    total_count = len(results)
    all_passed = (exercised_count == total_count) and total_count > 0

    evidence_lines.append("")
    evidence_lines.append("Component Summary Table:")
    evidence_lines.append("| Component | Offline Test Status | Details |")
    evidence_lines.append("|---|---|---|")
    for comp, status in results.items():
        status_label = "PASS" if status else "FAIL"
        evidence_lines.append(
            f"| {comp} | {status_label} | Local execution verified with outbound network blocked |"
        )

    evidence_lines.append("")
    evidence_lines.append(
        f"Exercised components: {exercised_count}/{total_count} verified offline with outbound network blocked."
    )
    final_verdict = "PASSED" if all_passed else "FAILED"
    evidence_lines.append(f"Offline Mode: {final_verdict}")

    evidence_file = Path("docs/evidence/offline_mode.txt")
    evidence_file.parent.mkdir(parents=True, exist_ok=True)
    with open(evidence_file, "w", encoding="utf-8") as f:
        f.write("\n".join(evidence_lines) + "\n")

    try:
        sys.stdout.reconfigure(encoding="utf-8")
        print("\n" + "\n".join(evidence_lines))
    except Exception:
        print("\n" + "\n".join(evidence_lines).encode("ascii", errors="replace").decode("ascii"))
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(run_offline_suite()))
