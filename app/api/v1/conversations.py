"""API endpoints for Conversation lifecycle, multi-turn turns, and persistent history."""

import logging
from typing import Annotated, Optional
import uuid

from fastapi import APIRouter, Depends, File, Form, Header, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthenticationError, AudioValidationError, ResourceNotFoundError
from app.core.security.auth import get_current_farmer_id
from app.database import get_db_session
from app.schemas.conversation import (
    ConversationHistoryResponse,
    ConversationListResponse,
    ConversationResponse,
    CreateConversationRequest,
    TurnResponse,
    TurnTextRequest,
)
from app.services.conversation_service import ConversationService


logger = logging.getLogger("krishi.api.conversations")
router = APIRouter(prefix="/conversations", tags=["Conversations"])


# Legacy deterministic farmer UUID kept for fixture compatibility
DEV_FARMER_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")


def get_conversation_service(
    db: AsyncSession = Depends(get_db_session),
) -> ConversationService:
    """Dependency provider for ConversationService."""
    return ConversationService(db=db)


@router.post(
    "",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new conversation session",
)
async def create_conversation_endpoint(
    request: CreateConversationRequest,
    farmer_id: uuid.UUID = Depends(get_current_farmer_id),
    service: ConversationService = Depends(get_conversation_service),
) -> ConversationResponse:
    """Initialize a persistent conversation session for an authenticated farmer."""
    return await service.create_conversation(
        farmer_id=farmer_id,
        language=request.language,
        initial_intent=request.initial_intent,
    )


@router.get(
    "",
    response_model=ConversationListResponse,
    status_code=status.HTTP_200_OK,
    summary="List farmer's conversations",
)
async def list_conversations_endpoint(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    farmer_id: uuid.UUID = Depends(get_current_farmer_id),
    service: ConversationService = Depends(get_conversation_service),
) -> ConversationListResponse:
    """List conversations belonging to the authenticated farmer with pagination."""
    return await service.list_conversations(
        farmer_id=farmer_id,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/active",
    response_model=ConversationResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve active conversation",
)
async def get_active_conversation_endpoint(
    farmer_id: uuid.UUID = Depends(get_current_farmer_id),
    service: ConversationService = Depends(get_conversation_service),
) -> ConversationResponse:
    """Retrieve the farmer's most recently active conversation session."""
    active = await service.get_active_conversation(farmer_id=farmer_id)
    if not active:
        raise ResourceNotFoundError("No active conversation session found for this farmer")
    return active


@router.get(
    "/{conversation_id}",
    response_model=ConversationResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve conversation details",
)
async def get_conversation_endpoint(
    conversation_id: uuid.UUID,
    farmer_id: uuid.UUID = Depends(get_current_farmer_id),
    service: ConversationService = Depends(get_conversation_service),
) -> ConversationResponse:
    """Retrieve conversation state, current agricultural profile, and missing slots."""
    return await service.get_conversation(
        conversation_id=conversation_id,
        farmer_id=farmer_id,
    )


@router.post(
    "/{conversation_id}/turns/voice",
    response_model=TurnResponse,
    status_code=status.HTTP_200_OK,
    summary="Submit spoken voice turn to conversation",
)
async def submit_voice_turn_endpoint(
    conversation_id: uuid.UUID,
    file: Annotated[UploadFile, File(description="Uploaded audio file")],
    language: Annotated[str, Form(description="Language code")] = "kn",
    client_turn_id: Annotated[Optional[str], Form(description="Idempotency key")] = None,
    farmer_id: uuid.UUID = Depends(get_current_farmer_id),
    service: ConversationService = Depends(get_conversation_service),
) -> TurnResponse:
    """Process a voice turn within an existing conversation session."""
    if not file:
        raise AudioValidationError("Audio file upload is required")

    try:
        content = await file.read()
    except Exception as exc:
        raise AudioValidationError(f"Failed to read audio file: {exc}") from exc

    if not content:
        raise AudioValidationError("Uploaded audio file is empty (0 bytes)")

    return await service.process_turn(
        conversation_id=conversation_id,
        farmer_id=farmer_id,
        input_mode="VOICE",
        audio_bytes=content,
        client_turn_id=client_turn_id,
    )


@router.post(
    "/{conversation_id}/turns/text",
    response_model=TurnResponse,
    status_code=status.HTTP_200_OK,
    summary="Submit written text turn to conversation",
)
async def submit_text_turn_endpoint(
    conversation_id: uuid.UUID,
    request: TurnTextRequest,
    farmer_id: uuid.UUID = Depends(get_current_farmer_id),
    service: ConversationService = Depends(get_conversation_service),
) -> TurnResponse:
    """Process a written text turn within an existing conversation session."""
    return await service.process_turn(
        conversation_id=conversation_id,
        farmer_id=farmer_id,
        input_mode="TEXT",
        text_input=request.text,
        client_turn_id=request.client_turn_id,
        expected_version=request.expected_version,
    )


@router.get(
    "/{conversation_id}/turns",
    response_model=ConversationHistoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve conversation turn history",
)
async def get_conversation_turns_endpoint(
    conversation_id: uuid.UUID,
    max_turns: int = Query(default=10, ge=1, le=50),
    farmer_id: uuid.UUID = Depends(get_current_farmer_id),
    service: ConversationService = Depends(get_conversation_service),
) -> ConversationHistoryResponse:
    """Retrieve bounded chronological turn history for a conversation."""
    return await service.get_conversation_history(
        conversation_id=conversation_id,
        farmer_id=farmer_id,
        max_turns=max_turns,
    )


@router.post(
    "/{conversation_id}/resume",
    response_model=ConversationResponse,
    status_code=status.HTTP_200_OK,
    summary="Resume a paused conversation",
)
async def resume_conversation_endpoint(
    conversation_id: uuid.UUID,
    farmer_id: uuid.UUID = Depends(get_current_farmer_id),
    service: ConversationService = Depends(get_conversation_service),
) -> ConversationResponse:
    """Resume a paused conversation session."""
    return await service.resume_conversation(
        conversation_id=conversation_id,
        farmer_id=farmer_id,
    )


@router.post(
    "/{conversation_id}/complete",
    response_model=ConversationResponse,
    status_code=status.HTTP_200_OK,
    summary="Complete a conversation session",
)
async def complete_conversation_endpoint(
    conversation_id: uuid.UUID,
    farmer_id: uuid.UUID = Depends(get_current_farmer_id),
    service: ConversationService = Depends(get_conversation_service),
) -> ConversationResponse:
    """Gracefully complete a conversation session."""
    return await service.complete_conversation(
        conversation_id=conversation_id,
        farmer_id=farmer_id,
    )
