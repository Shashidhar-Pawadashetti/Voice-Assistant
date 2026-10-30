"""Integration tests for end-to-end voice pipeline orchestration and privacy invariants."""

import logging
from pathlib import Path
import pytest

from app.core.asr.mock import MockSpeechRecognizer
from app.core.llm.extractor import SchemeExtractor
from app.core.llm.interface import LanguageModel
from app.core.tts.mock import MockSpeechSynthesizer
from app.core.tts.storage import EphemeralAudioStore
from app.schemas.extraction import ExtractedEntity, ExtractionResult, Intent
from app.services.voice_pipeline import VoicePipelineService
from tests.fixtures.audio_generator import make_test_wav


class DummyLanguageModel(LanguageModel):
    """Deterministic LLM for pipeline integration tests."""

    async def generate_structured(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        schema: dict | None = None,
        temperature: float = 0.1,
        timeout: float | None = None,
        **kwargs,
    ) -> dict:
        return {
            "intent": "FIND_SCHEMES",
            "entities": [
                {
                    "slot": "district",
                    "raw_value": "ಧಾರವಾಡ",
                    "canonical_value": "DHARWAD",
                    "value_type": "string",
                    "assertion": "USER_STATED",
                    "requires_confirmation": True,
                },
                {
                    "slot": "crop",
                    "raw_value": "ಜೋಳ",
                    "canonical_value": "SORGHUM",
                    "value_type": "string",
                    "assertion": "USER_STATED",
                    "requires_confirmation": False,
                },
            ],
            "unresolved_phrases": [],
            "correction_target": None,
            "assistant_language": "kn",
        }

    async def check_health(self) -> bool:
        return True


@pytest.mark.asyncio
async def test_voice_pipeline_successful_end_to_end(tmp_path: Path):
    audio_store = EphemeralAudioStore(storage_dir=tmp_path / "tts_out")
    asr = MockSpeechRecognizer(default_transcript="ಧಾರವಾಡ ಜಿಲ್ಲೆಯಲ್ಲಿ ಜೋಳ ಬೆಳೆಯಲು ಸಹಾಯಧನ ಬೇಕು")
    extractor = SchemeExtractor(llm=DummyLanguageModel())
    tts = MockSpeechSynthesizer()

    service = VoicePipelineService(
        speech_recognizer=asr,
        extractor=extractor,
        speech_synthesizer=tts,
        audio_store=audio_store,
    )

    wav_input = make_test_wav(duration_seconds=1.0)
    response = await service.process_voice_turn(wav_input, language="kn")

    assert response.transcript == "ಧಾರವಾಡ ಜಿಲ್ಲೆಯಲ್ಲಿ ಜೋಳ ಬೆಳೆಯಲು ಸಹಾಯಧನ ಬೇಕು"
    assert response.intent == Intent.FIND_SCHEMES
    assert len(response.entities) == 2
    assert response.entities[0].slot == "district"
    assert response.entities[0].canonical_value == "DHARWAD"
    assert response.speech_available is True
    assert response.audio_id is not None
    assert response.audio_url == f"/api/v1/voice/audio/{response.audio_id}"
    assert "ಕೃಷಿ ವಿವರಗಳನ್ನು ಸ್ವೀಕರಿಸಲಾಗಿದೆ" in response.response_text
    assert response.turn_latency_ms > 0

    # Verify ephemeral response audio was saved and is readable
    stored_audio = await audio_store.get(response.audio_id)
    assert stored_audio is not None
    assert len(stored_audio) > 44


@pytest.mark.asyncio
async def test_voice_pipeline_graceful_tts_degradation(tmp_path: Path):
    audio_store = EphemeralAudioStore(storage_dir=tmp_path / "tts_out")
    asr = MockSpeechRecognizer(default_transcript="ನನಗೆ ಎರಡು ಎಕರೆ ಜಮೀನಿದೆ")
    extractor = SchemeExtractor(llm=DummyLanguageModel())
    # Failing TTS
    failing_tts = MockSpeechSynthesizer(simulate_error=True)

    service = VoicePipelineService(
        speech_recognizer=asr,
        extractor=extractor,
        speech_synthesizer=failing_tts,
        audio_store=audio_store,
    )

    wav_input = make_test_wav(duration_seconds=1.0)
    response = await service.process_voice_turn(wav_input, language="kn")

    # Turn succeeds even though TTS failed
    assert response.transcript == "ನನಗೆ ಎರಡು ಎಕರೆ ಜಮೀನಿದೆ"
    assert response.intent == Intent.FIND_SCHEMES
    assert response.speech_available is False
    assert response.audio_id is None
    assert response.audio_url is None
    assert response.response_text is not None


@pytest.mark.asyncio
async def test_voice_pipeline_silence_handling(tmp_path: Path):
    audio_store = EphemeralAudioStore(storage_dir=tmp_path / "tts_out")
    asr = MockSpeechRecognizer(default_transcript="")
    extractor = SchemeExtractor(llm=DummyLanguageModel())
    tts = MockSpeechSynthesizer()

    service = VoicePipelineService(
        speech_recognizer=asr,
        extractor=extractor,
        speech_synthesizer=tts,
        audio_store=audio_store,
    )

    wav_input = make_test_wav(duration_seconds=1.0)
    response = await service.process_voice_turn(wav_input, language="kn")

    assert response.transcript == ""
    assert "ಸ್ಪಷ್ಟವಾಗಿ ಕೇಳಿಸಲಿಲ್ಲ" in response.response_text
    assert response.speech_available is False


@pytest.mark.asyncio
async def test_voice_pipeline_privacy_logging(tmp_path: Path, caplog: pytest.LogCaptureFixture):
    audio_store = EphemeralAudioStore(storage_dir=tmp_path / "tts_out")
    secret_transcript = "ಗೌಪ್ಯ ರೈತನ ವಿವರ ಧಾರವಾಡ"
    asr = MockSpeechRecognizer(default_transcript=secret_transcript)
    extractor = SchemeExtractor(llm=DummyLanguageModel())
    tts = MockSpeechSynthesizer()

    service = VoicePipelineService(
        speech_recognizer=asr,
        extractor=extractor,
        speech_synthesizer=tts,
        audio_store=audio_store,
    )

    wav_input = make_test_wav(duration_seconds=1.0)

    with caplog.at_level(logging.INFO):
        await service.process_voice_turn(wav_input, language="kn")

    log_text = caplog.text
    # Raw transcript and audio payload must NEVER appear in the log output
    assert secret_transcript not in log_text
    assert "RIFF" not in log_text
