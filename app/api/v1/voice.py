"""API endpoints for Voice Turn processing and Ephemeral Audio streaming."""

import logging
from typing import Annotated
from fastapi import APIRouter, Depends, File, Form, Response, UploadFile, status

from app.core.exceptions import AudioValidationError, ResourceNotFoundError
from app.core.security.auth import get_current_farmer
from app.core.tts.storage import EphemeralAudioStore, get_ephemeral_audio_store
from app.models.farmer import Farmer
from app.schemas.voice import VoiceTurnResponse
from app.services.voice_pipeline import VoicePipelineService


logger = logging.getLogger("krishi.api.voice")
router = APIRouter(prefix="/voice", tags=["Voice Pipeline"])


def get_voice_pipeline() -> VoicePipelineService:
    """Dependency injector for VoicePipelineService."""
    return VoicePipelineService()


@router.post(
    "/turn",
    response_model=VoiceTurnResponse,
    status_code=status.HTTP_200_OK,
    summary="Process spoken voice turn",
    description="Accepts an audio file upload (WAV/OGG/WEBM), transcribes via IndicConformer ASR, extracts NLU facts, and generates grounded Kannada response with optional TTS playback audio.",
)
async def process_voice_turn_endpoint(
    file: Annotated[UploadFile, File(description="Uploaded audio file")],
    language: Annotated[str, Form(description="ISO-639-1 language code (default 'kn')")] = "kn",
    current_farmer: Farmer = Depends(get_current_farmer),
    service: VoicePipelineService = Depends(get_voice_pipeline),
) -> VoiceTurnResponse:
    """Process voice turn and return transcript, entities, and speech response."""
    if not file:
        raise AudioValidationError("Audio file upload is required")

    try:
        content = await file.read()
    except Exception as exc:
        raise AudioValidationError(f"Failed to read audio file: {exc}") from exc

    if not content:
        raise AudioValidationError("Uploaded audio file is empty (0 bytes)")

    return await service.process_voice_turn(
        content,
        language=language,
        owner_id=str(current_farmer.id),
    )


@router.get(
    "/audio/{audio_id}",
    summary="Retrieve ephemeral response audio",
    description="Streams the synthesized playback audio for a voice turn if unexpired (10 min TTL).",
    responses={
        200: {
            "content": {"audio/wav": {}},
            "description": "PCM WAV audio stream",
        },
        401: {"description": "Missing or invalid authentication"},
        404: {"description": "Audio not found or expired"},
    },
)
async def get_response_audio_endpoint(
    audio_id: str,
    current_farmer: Farmer = Depends(get_current_farmer),
    store: EphemeralAudioStore = Depends(get_ephemeral_audio_store),
) -> Response:
    """Retrieve temporary playback audio by audio_id with strict owner authorization."""
    audio_bytes = await store.get(audio_id, owner_id=str(current_farmer.id))

    if audio_bytes is None:
        raise ResourceNotFoundError(
            f"Response audio '{audio_id}' has expired or does not exist",
            details={"audio_id": audio_id},
        )

    return Response(
        content=audio_bytes,
        media_type="audio/wav",
        headers={
            "Content-Type": "audio/wav",
            "Content-Disposition": f'inline; filename="response_{audio_id}.wav"',
            "Cache-Control": "private, max-age=600",
        },
    )
