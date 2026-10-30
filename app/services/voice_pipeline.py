"""Voice pipeline orchestration: Audio -> Validation -> Normalization -> ASR -> NLU -> Grounded Response -> TTS."""

import logging
import time
from pathlib import Path
from typing import Optional

from app.config import get_settings
from app.core.asr import SpeechRecognizer, get_speech_recognizer
from app.core.audio import normalize_to_wav_16k, transient_audio_file, validate_audio_file
from app.core.exceptions import AudioValidationError
from app.core.llm.extractor import SchemeExtractor, get_scheme_extractor
from app.core.tts import EphemeralAudioStore, SpeechSynthesizer, get_ephemeral_audio_store, get_speech_synthesizer
from app.schemas.extraction import Intent
from app.schemas.voice import VoiceTurnResponse


logger = logging.getLogger(__name__)


def generate_grounded_response_text(intent: Intent, entities_count: int) -> str:
    """Generate grounded, deterministic Kannada response text without LLM hallucination."""
    if intent in (
        Intent.FIND_SCHEMES,
        Intent.INCOME_SUPPORT,
        Intent.CROP_INSURANCE,
        Intent.MICRO_IRRIGATION,
        Intent.AGRICULTURAL_EQUIPMENT,
        Intent.SOIL_IMPROVEMENT,
    ):
        if entities_count > 0:
            return "ಧನ್ಯವಾದಗಳು. ನಿಮ್ಮ ಕೃಷಿ ವಿವರಗಳನ್ನು ಸ್ವೀಕರಿಸಲಾಗಿದೆ. ಸೂಕ್ತ ಯೋಜನೆಗಳ ಪಟ್ಟಿಯನ್ನು ಸಿದ್ಧಪಡಿಸಲಾಗುತ್ತಿದೆ."
        return "ಕೃಷಿ ಯೋಜನೆಗಳನ್ನು ಹುಡುಕಲು ದಯವಿಟ್ಟು ನಿಮ್ಮ ಬೆಳೆ, ಜಿಲ್ಲೆ ಮತ್ತು ಜಮೀನಿನ ವಿಸ್ತೀರ್ಣ ತಿಳಿಸಿ."

    if intent == Intent.EXPLAIN_SCHEME:
        return "ಯೋಜನೆಯ ವಿವರಗಳು ಮತ್ತು ನಿಯಮಾವಳಿಗಳನ್ನು ಪರಿಶೀಲಿಸಲಾಗುತ್ತಿದೆ."

    if intent == Intent.APPLICATION_STEPS:
        return "ಅರ್ಜಿ ಸಲ್ಲಿಸುವ ಹಂತಗಳು ಮತ್ತು ಅಗತ್ಯ ದಾಖಲೆಗಳನ್ನು ಪರಿಶೀಲಿಸಲಾಗುತ್ತಿದೆ."

    if intent == Intent.GREETING:
        return "ನಮಸ್ಕಾರ, ಕೃಷಿ ಮಿತ್ರ ಸಹಾಯವಾಣಿಗೆ ಸ್ವಾಗತ. ಯೋಜನೆಗಳ ಮಾಹಿತಿ ಪಡೆಯಲು ನಿಮ್ಮ ಬೆಳೆ ಅಥವಾ ಜಿಲ್ಲೆಯನ್ನು ತಿಳಿಸಿ."

    if intent == Intent.HELP:
        return "ಕೃಷಿ ಮಿತ್ರ ಸರ್ಕಾರಿ ಯೋಜನೆಗಳ ಮಾಹಿತಿ ನೀಡುತ್ತದೆ. ನಿಮ್ಮ ಬೆಳೆ, ಜಿಲ್ಲೆ ಅಥವಾ ಸಹಾಯದ ಅಗತ್ಯವನ್ನು ತಿಳಿಸಿ."

    # General / Unknown Fallback
    return "ನಮಸ್ಕಾರ, ಕೃಷಿ ಮಿತ್ರ ಸಹಾಯವಾಣಿಗೆ ಸ್ವಾಗತ. ಯೋಜನೆಗಳ ಮಾಹಿತಿ ಅಥವಾ ಸಹಾಯಕ್ಕಾಗಿ ನಿಮ್ಮ ವಿವರಗಳನ್ನು ತಿಳಿಸಿ."


class VoicePipelineService:
    """Orchestrates end-to-end voice turn processing while enforcing privacy invariants."""

    def __init__(
        self,
        speech_recognizer: Optional[SpeechRecognizer] = None,
        extractor: Optional[SchemeExtractor] = None,
        speech_synthesizer: Optional[SpeechSynthesizer] = None,
        audio_store: Optional[EphemeralAudioStore] = None,
    ):
        self.speech_recognizer = speech_recognizer or get_speech_recognizer()
        self.extractor = extractor or get_scheme_extractor()
        self.speech_synthesizer = speech_synthesizer or get_speech_synthesizer()
        self.audio_store = audio_store or get_ephemeral_audio_store()
        self.settings = get_settings()

    async def process_voice_turn(
        self,
        audio_bytes: bytes,
        *,
        language: str = "kn",
    ) -> VoiceTurnResponse:
        """Process an uploaded voice turn end-to-end.

        Invariants:
        1. Raw uploaded audio and normalized audio are deleted in finally blocks.
        2. Audio bytes and transcripts are never logged.
        3. TTS failures gracefully fall back to text-only output.
        4. No LLM scheme eligibility decisions.
        """
        turn_start = time.perf_counter()

        # Step 1: Validate audio upload constraints (size, duration, magic bytes)
        metadata = validate_audio_file(
            audio_bytes,
            max_bytes=self.settings.AUDIO_MAX_BYTES,
            max_seconds=self.settings.AUDIO_MAX_SECONDS,
        )

        transcript = ""
        asr_duration_ms = 0
        asr_provider = "unknown"

        # Step 2: Transient audio processing with guaranteed cleanup
        async with transient_audio_file(audio_bytes, suffix=f".{metadata.format}") as raw_path:
            norm_path = raw_path.with_name(f"norm_{raw_path.name}.wav")
            try:
                # Step 3: Normalize to 16 kHz mono 16-bit PCM WAV
                await normalize_to_wav_16k(
                    raw_path,
                    norm_path,
                    max_duration_seconds=float(self.settings.AUDIO_MAX_SECONDS),
                )

                # Step 4: Transcribe using SpeechRecognizer
                asr_result = await self.speech_recognizer.transcribe(norm_path, language=language)
                transcript = asr_result.text
                asr_duration_ms = asr_result.duration_ms
                asr_provider = asr_result.provider

            finally:
                # Guaranteed cleanup of normalized audio file
                if norm_path.exists():
                    try:
                        norm_path.unlink(missing_ok=True)
                    except OSError:
                        pass
        # Raw uploaded audio is now deleted by transient_audio_file context manager!

        # Check if ASR produced empty transcript (e.g. silence)
        if not transcript.strip():
            empty_turn_latency = int((time.perf_counter() - turn_start) * 1000)
            return VoiceTurnResponse(
                transcript="",
                language=language,
                intent=Intent.UNKNOWN,
                entities=[],
                unresolved_phrases=["ಧ್ವನಿ ಸ್ಪಷ್ಟವಾಗಿಲ್ಲ"],
                response_text="ಕ್ಷಮಿಸಿ, ನಿಮ್ಮ ಧ್ವನಿ ಸ್ಪಷ್ಟವಾಗಿ ಕೇಳಿಸಲಿಲ್ಲ. ದಯವಿಟ್ಟು ಮತ್ತೊಮ್ಮೆ ಮಾತನಾಡಿ.",
                audio_id=None,
                audio_url=None,
                speech_available=False,
                asr_duration_ms=asr_duration_ms,
                tts_duration_ms=None,
                turn_latency_ms=empty_turn_latency,
                diagnostic_metadata={"silence": True, "asr_provider": asr_provider},
            )

        # Step 5: NLU Slot & Intent extraction using existing SchemeExtractor
        extraction_result = await self.extractor.extract(transcript)

        # Step 6: Formulate grounded Kannada response text
        response_text = generate_grounded_response_text(
            extraction_result.intent,
            len(extraction_result.entities),
        )

        # Step 7: TTS speech synthesis (graceful degradation on failure)
        audio_id: Optional[str] = None
        audio_url: Optional[str] = None
        speech_available = False
        tts_duration_ms: Optional[int] = None
        tts_error_detail: Optional[str] = None

        try:
            tts_result = await self.speech_synthesizer.synthesize(
                response_text,
                language=language,
                voice_gender=self.settings.TTS_VOICE_GENDER,
            )
            audio_id = await self.audio_store.save(
                tts_result.audio_bytes,
                ttl_seconds=self.settings.AUDIO_RESPONSE_TTL_SECONDS,
            )
            audio_url = f"/api/v1/voice/audio/{audio_id}"
            speech_available = True
            tts_duration_ms = tts_result.duration_ms

        except Exception as exc:
            # TTS is best effort; do not fail the turn if synthesis is unavailable or fails
            logger.warning("TTS speech synthesis unavailable or failed: %s; falling back to text-only", exc)
            tts_error_detail = type(exc).__name__

        turn_latency_ms = int((time.perf_counter() - turn_start) * 1000)

        logger.info(
            "Voice turn completed: intent=%s entities=%d speech_available=%s turn_latency_ms=%d",
            extraction_result.intent.value,
            len(extraction_result.entities),
            speech_available,
            turn_latency_ms,
        )

        return VoiceTurnResponse(
            transcript=transcript,
            language=language,
            intent=extraction_result.intent,
            entities=extraction_result.entities,
            unresolved_phrases=extraction_result.unresolved_phrases,
            correction_target=extraction_result.correction_target,
            response_text=response_text,
            audio_id=audio_id,
            audio_url=audio_url,
            speech_available=speech_available,
            asr_duration_ms=asr_duration_ms,
            tts_duration_ms=tts_duration_ms,
            turn_latency_ms=turn_latency_ms,
            diagnostic_metadata={
                "asr_provider": asr_provider,
                "tts_provider": self.settings.TTS_PROVIDER,
                "tts_fallback": tts_error_detail is not None,
            },
        )
