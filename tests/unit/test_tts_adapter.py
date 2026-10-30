"""Unit tests for TTS provider interface, Indic-TTS adapter, and mock synthesizer."""

import base64
from unittest.mock import patch
import httpx
import pytest

from app.core.exceptions import TTSModelError, TTSTimeoutError, TTSUnavailableError
from app.core.tts.indic_tts import IndicTTSAdapter
from app.core.tts.mock import MockSpeechSynthesizer
from app.core.tts.sanitizer import sanitize_tts_text
from tests.fixtures.audio_generator import make_test_wav


def test_sanitize_tts_text_strips_html_and_expands_terms():
    raw = "<p>ನನ್ನ ಬಳಿ 2 ಎಕರೆ ಜಮೀನಿದೆ. PM-KISAN ಸಹಾಯಧನ ಬೇಕು.</p>"
    clean = sanitize_tts_text(raw)

    assert "<p>" not in clean
    assert "</p>" not in clean
    assert "ಪಿಎಂ ಕಿಸಾನ್" in clean
    assert "ಎರಡು" in clean


def test_sanitize_tts_text_truncates_long_input():
    long_str = "ಕೃಷಿ " * 500
    cleaned = sanitize_tts_text(long_str, max_chars=100)
    assert len(cleaned) <= 100


@pytest.mark.asyncio
async def test_indic_tts_binary_stream_success():
    adapter = IndicTTSAdapter(service_url="http://mock-tts:8002", timeout_seconds=5.0)
    wav_bytes = make_test_wav(duration_seconds=1.0)

    mock_resp = httpx.Response(
        status_code=200,
        content=wav_bytes,
        headers={"content-type": "audio/wav"},
        request=httpx.Request("POST", "http://mock-tts:8002/synthesize"),
    )

    with patch("httpx.AsyncClient.post", return_value=mock_resp):
        res = await adapter.synthesize("ಧನ್ಯವಾದಗಳು", language="kn")

    assert res.audio_bytes == wav_bytes
    assert res.content_type == "audio/wav"
    assert res.provider == "indic_tts"


@pytest.mark.asyncio
async def test_indic_tts_json_base64_success():
    adapter = IndicTTSAdapter(service_url="http://mock-tts:8002")
    wav_bytes = make_test_wav(duration_seconds=1.0)
    b64_audio = base64.b64encode(wav_bytes).decode("ascii")

    mock_resp = httpx.Response(
        status_code=200,
        json={"audio": b64_audio, "sample_rate": 22050, "duration_ms": 1000},
        headers={"content-type": "application/json"},
        request=httpx.Request("POST", "http://mock-tts:8002/synthesize"),
    )

    with patch("httpx.AsyncClient.post", return_value=mock_resp):
        res = await adapter.synthesize("ಧನ್ಯವಾದಗಳು")

    assert res.audio_bytes == wav_bytes
    assert res.duration_ms == 1000


@pytest.mark.asyncio
async def test_indic_tts_timeout():
    adapter = IndicTTSAdapter(service_url="http://mock-tts:8002")

    with patch("httpx.AsyncClient.post", side_effect=httpx.TimeoutException("Timeout")):
        with pytest.raises(TTSTimeoutError) as exc:
            await adapter.synthesize("ನಮಸ್ಕಾರ")
    assert exc.value.status_code == 504


@pytest.mark.asyncio
async def test_indic_tts_connection_unavailable():
    adapter = IndicTTSAdapter(service_url="http://mock-tts:8002")

    with patch("httpx.AsyncClient.post", side_effect=httpx.ConnectError("Down")):
        with pytest.raises(TTSUnavailableError) as exc:
            await adapter.synthesize("ನಮಸ್ಕಾರ")
    assert exc.value.status_code == 503


@pytest.mark.asyncio
async def test_mock_speech_synthesizer():
    mock = MockSpeechSynthesizer()
    res = await mock.synthesize("ಕೃಷಿ ಯೋಜನೆಗಳು")

    assert len(res.audio_bytes) > 44
    assert res.audio_bytes.startswith(b"RIFF")
    assert res.provider == "mock"
    assert res.duration_ms > 0


@pytest.mark.asyncio
async def test_mock_speech_synthesizer_simulated_error():
    mock = MockSpeechSynthesizer(simulate_error=True)
    with pytest.raises(TTSModelError):
        await mock.synthesize("ಟೆಸ್ಟ್")
