"""Unit tests for ASR provider interface, IndicConformer adapter, and mock recognizer."""

from pathlib import Path
from unittest.mock import patch
import httpx
import pytest

from app.core.asr.indic_conformer import IndicConformerAdapter
from app.core.asr.mock import MockSpeechRecognizer
from app.core.exceptions import ASRModelError, ASRTimeoutError, ASRUnavailableError
from tests.fixtures.audio_generator import make_test_wav


@pytest.mark.asyncio
async def test_indic_conformer_transcribe_success(tmp_path: Path):
    wav_bytes = make_test_wav(duration_seconds=1.5, sample_rate=16000)
    audio_path = tmp_path / "audio.wav"
    audio_path.write_bytes(wav_bytes)

    adapter = IndicConformerAdapter(service_url="http://mock-asr:8001", timeout_seconds=5.0)

    mock_resp = httpx.Response(
        status_code=200,
        json={
            "transcript": "ಧಾರವಾಡ ಜಿಲ್ಲೆಯಲ್ಲಿ ಜೋಳ ಬೆಳೆಯಲು ಸಹಾಯಧನ ಬೇಕು",
            "language": "kn",
            "duration_ms": 1500,
            "confidence": 0.94,
            "warnings": [],
        },
        request=httpx.Request("POST", "http://mock-asr:8001/transcribe"),
    )

    with patch("httpx.AsyncClient.post", return_value=mock_resp):
        result = await adapter.transcribe(audio_path, language="kn")

    assert result.text == "ಧಾರವಾಡ ಜಿಲ್ಲೆಯಲ್ಲಿ ಜೋಳ ಬೆಳೆಯಲು ಸಹಾಯಧನ ಬೇಕು"
    assert result.language == "kn"
    assert result.duration_ms == 1500
    assert result.confidence == 0.94
    assert result.provider == "indic_conformer"
    assert result.diagnostic_metadata["service_url"] == "http://mock-asr:8001"


@pytest.mark.asyncio
async def test_indic_conformer_server_error(tmp_path: Path):
    audio_path = tmp_path / "audio.wav"
    audio_path.write_bytes(make_test_wav(0.5))

    adapter = IndicConformerAdapter(service_url="http://mock-asr:8001")

    mock_resp = httpx.Response(
        status_code=500,
        json={"error": "Inference crash"},
        request=httpx.Request("POST", "http://mock-asr:8001/transcribe"),
    )

    with patch("httpx.AsyncClient.post", return_value=mock_resp):
        with pytest.raises(ASRModelError) as exc:
            await adapter.transcribe(audio_path)
    assert exc.value.status_code == 502


@pytest.mark.asyncio
async def test_indic_conformer_timeout(tmp_path: Path):
    audio_path = tmp_path / "audio.wav"
    audio_path.write_bytes(make_test_wav(0.5))

    adapter = IndicConformerAdapter(service_url="http://mock-asr:8001", timeout_seconds=1.0)

    with patch("httpx.AsyncClient.post", side_effect=httpx.TimeoutException("Timeout")):
        with pytest.raises(ASRTimeoutError) as exc:
            await adapter.transcribe(audio_path)
    assert exc.value.status_code == 504


@pytest.mark.asyncio
async def test_indic_conformer_service_unavailable(tmp_path: Path):
    audio_path = tmp_path / "audio.wav"
    audio_path.write_bytes(make_test_wav(0.5))

    adapter = IndicConformerAdapter(service_url="http://mock-asr:8001")

    with patch("httpx.AsyncClient.post", side_effect=httpx.ConnectError("Connection refused")):
        with pytest.raises(ASRUnavailableError) as exc:
            await adapter.transcribe(audio_path)
    assert exc.value.status_code == 503


@pytest.mark.asyncio
async def test_indic_conformer_health_check():
    adapter = IndicConformerAdapter(service_url="http://mock-asr:8001")

    healthy_resp = httpx.Response(
        status_code=200,
        request=httpx.Request("GET", "http://mock-asr:8001/health"),
    )
    with patch("httpx.AsyncClient.get", return_value=healthy_resp):
        assert await adapter.check_health() is True

    with patch("httpx.AsyncClient.get", side_effect=httpx.ConnectError("Down")):
        assert await adapter.check_health() is False


@pytest.mark.asyncio
async def test_mock_speech_recognizer(tmp_path: Path):
    audio_path = tmp_path / "test.wav"
    audio_path.write_bytes(make_test_wav(duration_seconds=1.2))

    mock = MockSpeechRecognizer(default_transcript="ನನಗೆ ಎರಡು ಎಕರೆ ಜಮೀನಿದೆ")
    res = await mock.transcribe(audio_path, language="kn")

    assert res.text == "ನನಗೆ ಎರಡು ಎಕರೆ ಜಮೀನಿದೆ"
    assert res.provider == "mock"
    assert res.language == "kn"
    assert 1100 <= res.duration_ms <= 1300
