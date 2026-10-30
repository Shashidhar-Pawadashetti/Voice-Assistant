"""Integration tests for Voice API HTTP endpoints."""

import io
from unittest.mock import patch
import pytest
from httpx import ASGITransport, AsyncClient

from app.api.v1.voice import get_voice_pipeline
from app.core.asr.mock import MockSpeechRecognizer
from app.core.llm.extractor import SchemeExtractor
from app.core.tts.mock import MockSpeechSynthesizer
from app.core.tts.storage import EphemeralAudioStore, get_ephemeral_audio_store
from app.main import create_app
from app.services.voice_pipeline import VoicePipelineService
from tests.fixtures.audio_generator import make_test_wav
from tests.integration.test_voice_pipeline import DummyLanguageModel


@pytest.fixture
def mock_voice_service(tmp_path):
    audio_store = EphemeralAudioStore(storage_dir=tmp_path / "tts_responses")
    asr = MockSpeechRecognizer(default_transcript="ಧಾರವಾಡ ಜಿಲ್ಲೆಯಲ್ಲಿ ಜೋಳ ಬೆಳೆಯಲು ಸಹಾಯಧನ ಬೇಕು")
    extractor = SchemeExtractor(llm=DummyLanguageModel())
    tts = MockSpeechSynthesizer()

    return VoicePipelineService(
        speech_recognizer=asr,
        extractor=extractor,
        speech_synthesizer=tts,
        audio_store=audio_store,
    )


@pytest.mark.asyncio
async def test_api_voice_turn_endpoint_success(mock_voice_service):
    app = create_app()
    app.dependency_overrides[get_voice_pipeline] = lambda: mock_voice_service

    wav_bytes = make_test_wav(duration_seconds=1.0)
    files = {"file": ("farmer_speech.wav", io.BytesIO(wav_bytes), "audio/wav")}
    data = {"language": "kn"}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/v1/voice/turn", files=files, data=data)

    assert resp.status_code == 200
    body = resp.json()
    assert body["transcript"] == "ಧಾರವಾಡ ಜಿಲ್ಲೆಯಲ್ಲಿ ಜೋಳ ಬೆಳೆಯಲು ಸಹಾಯಧನ ಬೇಕು"
    assert body["intent"] == "FIND_SCHEMES"
    assert len(body["entities"]) == 2
    assert body["speech_available"] is True
    assert body["audio_id"] is not None
    assert body["audio_url"] == f"/api/v1/voice/audio/{body['audio_id']}"


@pytest.mark.asyncio
async def test_api_voice_turn_invalid_audio_rejected(mock_voice_service):
    app = create_app()
    app.dependency_overrides[get_voice_pipeline] = lambda: mock_voice_service

    # Upload non-audio script payload
    files = {"file": ("malicious.sh", io.BytesIO(b"#!/bin/bash\nrm -rf /\n"), "text/plain")}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/v1/voice/turn", files=files)

    assert resp.status_code == 400
    body = resp.json()
    assert body["error"]["code"] == "AUDIO_VALIDATION_FAILED"


@pytest.mark.asyncio
async def test_api_voice_audio_retrieval(mock_voice_service):
    app = create_app()
    app.dependency_overrides[get_voice_pipeline] = lambda: mock_voice_service
    app.dependency_overrides[get_ephemeral_audio_store] = lambda: mock_voice_service.audio_store

    wav_bytes = make_test_wav(duration_seconds=0.5)
    audio_id = await mock_voice_service.audio_store.save(wav_bytes)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Successful retrieval
        resp = await client.get(f"/api/v1/voice/audio/{audio_id}")
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "audio/wav"
        assert resp.content == wav_bytes

        # Nonexistent retrieval
        missing_resp = await client.get("/api/v1/voice/audio/00000000000000000000000000000000")
        assert missing_resp.status_code == 404
        missing_body = missing_resp.json()
        assert missing_body["error"]["code"] == "RESOURCE_NOT_FOUND"
