"""Pytest fixtures and test configuration for BolSamajh."""

import pytest


@pytest.fixture
def fake_edge_tts(monkeypatch):
    """Fixture that intercepts edge_tts.Communicate to return a synthetic MP3 stream without network calls."""
    import edge_tts

    fake_mp3_payload = b"ID3\x04\x00\x00\x00\x00\x00\x00\xff\xfb\x90\x64" + b"\xaa" * 1500

    class MockCommunicate:
        def __init__(self, text, voice, **kwargs):
            self.text = text
            self.voice = voice

        async def stream(self):
            yield {"type": "audio", "data": fake_mp3_payload}

    monkeypatch.setattr(edge_tts, "Communicate", MockCommunicate)
    return MockCommunicate
