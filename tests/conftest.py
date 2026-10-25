"""Pytest fixtures and test configuration for BolSamajh."""

import pytest


@pytest.fixture
def fake_edge_tts(monkeypatch):
    """Fixture that intercepts edge_tts.Communicate to return a synthetic MP3 stream without network calls."""
    import io
    import edge_tts
    import av
    import numpy as np

    buf = io.BytesIO()
    with av.open(buf, mode="w", format="mp3") as container:
        stream = container.add_stream("mp3", rate=24000)
        stream.bit_rate = 64000
        frame = av.AudioFrame.from_ndarray(np.zeros((1, 1152), dtype=np.int16), format="s16p", layout="mono")
        frame.rate = 24000
        for p in stream.encode(frame):
            container.mux(p)
        for p in stream.encode():
            container.mux(p)
    valid_mp3_payload = buf.getvalue()
    if len(valid_mp3_payload) < 1000:
        valid_mp3_payload += b"\x00" * (1000 - len(valid_mp3_payload))

    class MockCommunicate:
        def __init__(self, text, voice, rate="+0%", **kwargs):
            self.text = text
            self.voice = voice
            self.rate = rate

        async def stream(self):
            yield {"type": "audio", "data": valid_mp3_payload}

    monkeypatch.setattr(edge_tts, "Communicate", MockCommunicate)
    return MockCommunicate
