"""Pydantic schemas for data privacy, export, and DPDP erasure workflows."""

from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, Field


class DataExportResponse(BaseModel):
    """Complete, portable export of farmer personal and conversational data."""

    export_generated_at: datetime
    farmer_id: uuid.UUID
    preferred_language: str
    account_status: str
    created_at: datetime
    last_login_at: Optional[datetime] = None
    profile_data: Dict[str, Any]
    consent_history: List[Dict[str, Any]]
    conversations: List[Dict[str, Any]]
    recommendation_runs: List[Dict[str, Any]]


class DeletionRequestPayload(BaseModel):
    """Farmer account erasure verification request."""

    password: str = Field(description="Account password required to confirm deletion")
    reason: Optional[str] = Field(default=None, description="Optional deletion reason")


class DeletionResponse(BaseModel):
    """Proof of deletion execution conforming to DPDP erasure standards."""

    status: str = Field(description="Outcome: COMPLETED")
    message: str
    requested_at: datetime
    completed_at: datetime
    deletion_request_id: uuid.UUID
    records_erased: Dict[str, int]
