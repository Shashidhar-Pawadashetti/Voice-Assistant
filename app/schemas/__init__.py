"""Pydantic schemas package initialization."""

from app.schemas.health import LivenessResponse, ReadinessResponse, DependencyHealth
from app.schemas.error import APIErrorResponse, ErrorDetail
from app.schemas.extraction import (
    IntentType,
    ExtractedEntity,
    ExtractionResult,
    ExtractionRequest,
)

from app.schemas.voice import VoiceTurnResponse
from app.schemas.conversation import (
    CreateConversationRequest,
    ConversationResponse,
    ConversationListResponse,
    TurnTextRequest,
    ConversationTurnDTO,
    ConversationHistoryResponse,
    TurnResponse,
)

from app.schemas.scheme import (
    SchemeSummaryResponse,
    SchemeDetailResponse,
    RecommendationRunResponse,
    RecommendationEvaluationResponse,
)

from app.schemas.auth import (
    RegisterRequest,
    RegisterResponse,
    LoginRequest,
    TokenResponse,
    RefreshTokenRequest,
    LogoutRequest,
    ChangePasswordRequest,
    FarmerResponse,
)

from app.schemas.privacy import (
    DataExportResponse,
    DeletionRequestPayload,
    DeletionResponse,
)

__all__ = [
    "LivenessResponse",
    "ReadinessResponse",
    "DependencyHealth",
    "APIErrorResponse",
    "ErrorDetail",
    "IntentType",
    "ExtractedEntity",
    "ExtractionResult",
    "ExtractionRequest",
    "VoiceTurnResponse",
    "CreateConversationRequest",
    "ConversationResponse",
    "ConversationListResponse",
    "TurnTextRequest",
    "ConversationTurnDTO",
    "ConversationHistoryResponse",
    "TurnResponse",
    "SchemeSummaryResponse",
    "SchemeDetailResponse",
    "RecommendationRunResponse",
    "RecommendationEvaluationResponse",
]
