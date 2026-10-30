"""REST API endpoints for Farmer Data Portability, Export, and Verified Deletion.

Conforms to Directive M5.4 and DPDP Act 2023 Principles.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security.auth import get_current_farmer
from app.core.tts.storage import EphemeralAudioStore, get_ephemeral_audio_store
from app.database import get_db_session
from app.models.farmer import Farmer
from app.schemas.privacy import (
    DataExportResponse,
    DeletionRequestPayload,
    DeletionResponse,
)
from app.services.privacy_service import PrivacyService

router = APIRouter(prefix="/privacy", tags=["Privacy & Data Rights"])


@router.get(
    "/export",
    response_model=DataExportResponse,
    status_code=status.HTTP_200_OK,
    summary="Export all farmer personal and conversation data",
)
async def export_data(
    current_farmer: Farmer = Depends(get_current_farmer),
    db: AsyncSession = Depends(get_db_session),
    audio_store: EphemeralAudioStore = Depends(get_ephemeral_audio_store),
) -> DataExportResponse:
    """Download a complete, machine-readable export of all records belonging to the authenticated farmer."""
    service = PrivacyService(db, audio_store=audio_store)
    return await service.export_farmer_data(current_farmer)


@router.post(
    "/delete",
    response_model=DeletionResponse,
    status_code=status.HTTP_200_OK,
    summary="Request complete erasure of farmer account and personal data",
)
async def delete_account(
    payload: DeletionRequestPayload,
    current_farmer: Farmer = Depends(get_current_farmer),
    db: AsyncSession = Depends(get_db_session),
    audio_store: EphemeralAudioStore = Depends(get_ephemeral_audio_store),
) -> DeletionResponse:
    """Execute complete erasure of personal profile, conversations, audio files, and credentials."""
    service = PrivacyService(db, audio_store=audio_store)
    return await service.execute_data_deletion(current_farmer, payload)
