"""REST API endpoints for Government Scheme Catalog and Recommendation Engine.

Conforms to Directive M4.1, M4.5, 07_SCHEME_ENGINE_AND_GOVERNANCE.md, and 09_API_CONTRACT.md.
"""

from typing import List, Optional
import uuid
from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConversationOwnershipError, NotFoundError
from app.core.profile.assembler import AgriculturalProfileAssembler
from app.core.scheme.catalog import ALL_SCHEMES, SCHEMES_BY_ID
from app.core.scheme.enums import SchemeClassification
from app.core.security.auth import get_current_farmer
from app.database import get_db_session
from app.models.farmer import Farmer
from app.schemas.scheme import (
    RecommendationEvaluationResponse,
    RecommendationRunResponse,
    SchemeDetailResponse,
    SchemeSummaryResponse,
)
from app.services.conversation_service import ConversationService
from app.services.recommendation_service import RecommendationService


router = APIRouter(tags=["Schemes & Recommendations"])


@router.get(
    "/schemes",
    response_model=List[SchemeSummaryResponse],
    summary="List active schemes in catalog",
)
async def list_schemes(
    classification: Optional[str] = Query(None, description="REAL_GOVERNMENT or SYNTHETIC_DEMO"),
    category: Optional[str] = Query(None, description="Assistance category"),
) -> List[SchemeSummaryResponse]:
    """List available government and demonstration schemes."""
    candidates = ALL_SCHEMES
    if classification:
        candidates = [s for s in candidates if s.classification.value == classification]
    if category:
        candidates = [s for s in candidates if s.assistance_category == category]

    return [
        SchemeSummaryResponse(
            scheme_id=s.scheme_id,
            official_name=s.official_name,
            display_name=s.display_name,
            display_name_kn=s.display_name_kn,
            classification=s.classification,
            government_level=s.government_level,
            assistance_category=s.assistance_category,
            verification_status=s.verification_status,
            demo_only=s.demo_only,
            application_portal=s.application_portal,
        )
        for s in candidates
    ]


@router.get(
    "/schemes/{scheme_id}",
    response_model=SchemeDetailResponse,
    summary="Get detailed scheme definition and evidence citations",
)
async def get_scheme_detail(
    scheme_id: str,
) -> SchemeDetailResponse:
    """Retrieve full scheme definition, conditions, exclusions, documents and citations."""
    scheme = SCHEMES_BY_ID.get(scheme_id)
    if not scheme:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scheme '{scheme_id}' was not found in catalog.",
        )

    return SchemeDetailResponse(
        scheme_id=scheme.scheme_id,
        official_name=scheme.official_name,
        display_name=scheme.display_name,
        display_name_kn=scheme.display_name_kn,
        classification=scheme.classification,
        government_level=scheme.government_level,
        assistance_category=scheme.assistance_category,
        verification_status=scheme.verification_status,
        demo_only=scheme.demo_only,
        application_portal=scheme.application_portal,
        description=scheme.description,
        description_kn=scheme.description_kn,
        benefit_description=scheme.benefit_description,
        benefit_description_kn=scheme.benefit_description_kn,
        application_procedure=scheme.application_procedure,
        application_procedure_kn=scheme.application_procedure_kn,
        applicable_geography=scheme.applicable_geography,
        required_slots=scheme.required_slots,
        eligibility_conditions=scheme.eligibility_conditions,
        exclusions=scheme.exclusions,
        required_documents=scheme.required_documents,
        required_documents_kn=scheme.required_documents_kn,
        evidence_references=scheme.evidence_references,
        rule_version=scheme.rule_version,
        dataset_version=scheme.dataset_version,
        official_verification_required=scheme.official_verification_required,
        notes=scheme.notes,
    )


@router.post(
    "/conversations/{conversation_id}/recommendations",
    response_model=RecommendationEvaluationResponse,
    summary="Evaluate applicable schemes for a conversation profile",
)
async def evaluate_conversation_recommendations(
    conversation_id: uuid.UUID,
    current_farmer: Farmer = Depends(get_current_farmer),
    db: AsyncSession = Depends(get_db_session),
) -> RecommendationEvaluationResponse:
    """Evaluate applicable government schemes against conversation agricultural profile."""
    farmer_uuid = current_farmer.id
    conv_service = ConversationService(db)
    rec_service = RecommendationService(db)

    # 1. Fetch conversation and verify farmer ownership
    conversation = await conv_service.get_conversation(
        conversation_id=conversation_id,
        farmer_id=farmer_uuid,
    )

    # 2. Extract agricultural profile and current intent
    profile = await conv_service._load_or_assemble_profile(conversation)
    current_intent = conv_service._extract_intent_from_summary(conversation.summary)

    # 3. Evaluate schemes
    results = await rec_service.evaluate_for_farmer(
        farmer_id=farmer_uuid,
        conversation_id=conversation_id,
        profile=profile,
        intent=current_intent,
    )

    return RecommendationEvaluationResponse(
        conversation_id=conversation_id,
        farmer_id=farmer_uuid,
        total_evaluated=len(results),
        recommendations=results,
    )


@router.get(
    "/conversations/{conversation_id}/recommendations",
    response_model=List[RecommendationRunResponse],
    summary="List historical recommendation runs for a conversation",
)
async def list_conversation_recommendation_history(
    conversation_id: uuid.UUID,
    current_farmer: Farmer = Depends(get_current_farmer),
    db: AsyncSession = Depends(get_db_session),
) -> List[RecommendationRunResponse]:
    """Retrieve immutable historical recommendation runs for a conversation."""
    farmer_uuid = current_farmer.id
    rec_service = RecommendationService(db)
    try:
        runs = await rec_service.get_conversation_recommendations(
            farmer_id=farmer_uuid,
            conversation_id=conversation_id,
        )
    except ConversationOwnershipError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Conversation {conversation_id} does not belong to farmer {farmer_uuid}.",
        )

    return [
        RecommendationRunResponse(
            id=r.id,
            conversation_id=r.conversation_id,
            farmer_id=r.farmer_id,
            scheme_rule_version_id=r.scheme_rule_version_id,
            evaluator_version=r.evaluator_version,
            outcome=r.outcome,
            explanation_trace=r.explanation_trace,
            evaluated_at=r.evaluated_at,
        )
        for r in runs
    ]
