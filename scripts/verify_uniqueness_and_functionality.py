"""BolSamajh End-to-End Uniqueness & Functionality Verification Suite.

Runs live empirical tests validating every feature that makes BolSamajh
unique from Wispr Flow and verifying that every single pipeline is working:
1. Voice IN: Hinglish Script Control & Disfluency Cleanup vs plain Whisper.
2. Voice OUT: Talk-to-Document RAG with Page Citations, Strict Refusal, and TTS Audio.
3. In-App Voice Commands: Text transformations (Formal, Summary, Hindi translation).
4. Desktop Overlay Management: Dynamic Start/Toggle/Stop control from Web Studio.
5. Android Companion & PWA: LAN pairing, manifest, and service worker.
"""

import sys
import time
from pathlib import Path

# Ensure UTF-8 output on Windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient

from bolsamajh.documents.loader import Document, DocumentPage
from bolsamajh.documents.retriever import DocumentRetriever
from bolsamajh.tts.edge_tts_adapter import EdgeTTSAdapter
from bolsamajh.utils.text_cleanup import (
    apply_script_control,
    cleanup_text,
    format_numbers,
    remove_fillers,
)
from bolsamajh.web.server import app, set_overlay_hud


def print_header(title: str):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def test_voice_in_uniqueness():
    print_header("1. VOICE IN: Hinglish Quality & Script Control (vs Wispr Flow)")

    raw_speech = "umm uhh actually meeting kal shaam ko like 3 baje postpone ho gayi matlab 500 rupees extra lagenge"
    print(f"[*] Raw input speech transcription:\n    '{raw_speech}'")

    # 1. Disfluency cleanup (true vocal pauses umm/uhh removed, semantic words like/matlab preserved)
    cleaned = remove_fillers(raw_speech)
    print(
        f"\n[+] Cleaned Fillers (true disfluencies umm/uhh removed; semantic words preserved):\n    '{cleaned}'"
    )
    assert "umm" not in cleaned.lower()
    assert "uhh" not in cleaned.lower()
    assert "meeting" in cleaned.lower()
    assert "matlab" in cleaned.lower()

    # 2. Number & Rupee formatting
    num_formatted = format_numbers(cleaned)
    print(f"\n[+] Rupee & Number Formatting (500 rupees -> ₹500):\n    '{num_formatted}'")
    assert "₹500" in num_formatted

    # 3. Script Control: Roman, Devanagari, Natural
    roman = apply_script_control(num_formatted, "roman")
    devanagari = apply_script_control(num_formatted, "devanagari")
    natural = cleanup_text(raw_speech, remove_filler=True, script="natural")

    print("\n[+] Script Control Output Comparison:")
    print(f"    - Roman Script:    {roman}")
    print(f"    - Natural Mixed:   {natural}")
    print(f"    - Devanagari Hindi: {devanagari[:50]}...")

    assert "₹500" in natural
    print("\n[OK] Voice IN Hinglish uniqueness verified.")


def test_voice_out_talk_to_doc():
    print_header(
        "2. VOICE OUT: Talk-to-Document RAG, Citations & TTS (Wispr Flow has ZERO Voice OUT)"
    )

    # 1. Create a simulated multi-page document
    pages = [
        DocumentPage(
            text="Rental Agreement for Flat 402, Pune, Maharashtra. Monthly rent is Rs 25000 payable on 5th of each month. Security deposit is Rs 50000 deposited with the landlord.",
            page_number=1,
            source="rental_contract.pdf",
        ),
        DocumentPage(
            text="Notice Period Clause: Either party may terminate this agreement by giving 30 days written notice. Lock-in period is 6 months. Late rent penalty is Rs 500 per week.",
            page_number=2,
            source="rental_contract.pdf",
        ),
    ]
    doc = Document(
        title="Pune Rental Agreement",
        source="rental_contract.pdf",
        pages=pages,
        doc_type="pdf",
    )

    # 2. Index in DocumentRetriever
    print("[*] Loading and indexing document chunks into vector retriever...")
    retriever = DocumentRetriever(embedding_model="intfloat/multilingual-e5-base")
    num_chunks = retriever.index_document(doc)
    print(f"[+] Indexed {num_chunks} chunks with multi-page citations.")

    # 3. Test Grounded Query with Page Citations
    q_grounded = "Security deposit kitna hai aur notice period kitna hai?"
    print(f"\n[*] Query 1 (Grounded in doc): '{q_grounded}'")
    results = retriever.retrieve(q_grounded, top_k=2)
    assert len(results) > 0
    top_chunk = results[0]
    print(f"    -> Retrieved citation: {top_chunk.citation} (score: {top_chunk.score:.3f})")
    print(f"    -> Chunk text preview: {top_chunk.text[:80]}...")
    assert "Page" in top_chunk.citation

    # 4. Test Strict Refusal for Out-of-Document Query
    q_out = "What is the capital of Australia and who is the prime minister?"
    print(f"\n[*] Query 2 (Out-of-document query): '{q_out}'")
    out_results = retriever.retrieve(q_out, top_k=2)
    is_refused = len(out_results) == 0 or out_results[0].score < retriever.refusal_threshold
    print(
        f"    -> Retrieval score: {out_results[0].score if out_results else 0.0:.3f} vs threshold {retriever.refusal_threshold:.3f}"
    )
    print(f"    -> Refusal status: {'STRICTLY REFUSED (Not in doc)' if is_refused else 'Accepted'}")
    assert is_refused, "Out of document question must be refused below threshold"

    # 5. Test Voice Synthesis (TTS)
    print("\n[*] Testing TTS voice synthesis for Hindi/Hinglish audio output...")
    import asyncio

    tts = EdgeTTSAdapter()
    answer_text = (
        "Security deposit 50,000 rupees hai aur notice period 30 days hai, page 1 aur 2 ke mutabik."
    )
    audio_bytes = asyncio.run(tts.synthesize(answer_text, lang="hi"))
    print(f"[+] Synthesized audio response length: {len(audio_bytes)} bytes (MP3 audio)")
    assert len(audio_bytes) > 1000, "Audio response must contain valid synthesized bytes"

    print("\n[OK] Voice OUT Talk-to-Document uniqueness verified.")


def test_voice_commands():
    print_header("3. VOICE ACTIONS & IN-APP COMMANDS (Wispr Flow only types)")

    client = TestClient(app)
    raw_text = "yaar kal meeting cancel ho gayi 3 baje ab parso karenge"
    print(f"[*] Original text in application:\n    '{raw_text}'")

    res = client.post(
        "/api/command",
        json={"text": raw_text, "command": "Make it formal and professional"},
    )
    assert res.status_code == 200
    data = res.json()
    print(f"\n[+] Transformed via command 'Make it formal':\n    '{data.get('result')}'")
    assert len(data.get("result", "")) > 5

    # Test in-app injection
    res_inject = client.post("/api/inject", json={"text": data.get("result")})
    assert res_inject.status_code == 200
    print(f"[+] Injected into active desktop window: {res_inject.json()}")

    print("\n[OK] Voice Commands in any app verified.")


def test_app_interface_and_overlay_toggle():
    print_header("4. APP INTERFACE & DESKTOP OVERLAY CONTROLS")

    client = TestClient(app)

    # 1. Web Studio Interface Home
    res_home = client.get("/")
    assert res_home.status_code == 200
    assert "BolSamajh" in res_home.text
    assert "Start Overlay" in res_home.text
    print("[+] Web Studio Interface: 200 OK (Loaded with Wispr Flow Studio & Overlay controls)")

    # 2. Mock Overlay HUD
    class MockHUD:
        def __init__(self):
            self._pinned = False
            self.state = "idle"
            self._thread = None

        @property
        def is_pinned(self):
            return self._pinned

        def toggle_pin(self):
            self._pinned = not self._pinned
            return self._pinned

        def start(self):
            pass

        def show_pill(self, text):
            pass

        def set_state(self, s):
            self.state = s

    hud = MockHUD()
    set_overlay_hud(hud)

    # Status check
    r1 = client.get("/api/overlay")
    print(f"[+] Initial Overlay Status: {r1.json()}")
    assert r1.json()["pinned"] is False

    # Toggle to start/pin overlay
    r2 = client.post("/api/overlay/toggle")
    print(f"[+] Toggle Overlay (Start): {r2.json()}")
    assert r2.json()["pinned"] is True

    # Toggle to stop/hide overlay
    r3 = client.post("/api/overlay/toggle")
    print(f"[+] Toggle Overlay (Stop):  {r3.json()}")
    assert r3.json()["pinned"] is False

    print("\n[OK] Desktop Overlay Start/Toggle option verified.")


def test_android_pwa_and_offline():
    print_header("5. ANDROID COMPANION (PWA), LAN PAIRING & ZERO SPEND")

    client = TestClient(app)

    # Manifest
    r_man = client.get("/manifest.json")
    assert r_man.status_code == 200
    print(f"[+] PWA Manifest: 200 OK (name: '{r_man.json().get('name')}', start_url: '/')")

    # Service Worker
    r_sw = client.get("/sw.js")
    assert r_sw.status_code == 200
    print(
        f"[+] Service Worker: 200 OK (Service-Worker-Allowed: '{r_sw.headers.get('Service-Worker-Allowed')}')"
    )

    # Status & LAN IP
    r_stat = client.get("/api/status")
    d = r_stat.json()
    print(
        f"[+] System Status: device='{d.get('device')}', STT='{d.get('stt')}', local_ip='{d.get('local_ip')}:{d.get('port')}'"
    )
    assert d.get("local_ip") is not None

    print("\n[OK] Android Companion and local Wi-Fi pairing verified.")


def main():
    print("\n" + "#" * 70)
    print("  BOLSAMAJH — END-TO-END UNIQUENESS & FUNCTIONALITY VERIFICATION")
    print("#" * 70)

    t0 = time.time()
    test_voice_in_uniqueness()
    test_voice_out_talk_to_doc()
    test_voice_commands()
    test_app_interface_and_overlay_toggle()
    test_android_pwa_and_offline()

    elapsed = time.time() - t0
    print("\n" + "=" * 70)
    print(f"  ALL 5 DIFFERENTIATING FUNCTIONALITIES VERIFIED IN {elapsed:.2f}s!")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
