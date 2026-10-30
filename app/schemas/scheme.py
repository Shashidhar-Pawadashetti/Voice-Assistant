"""API Pydantic models for Scheme Catalog and Recommendation endpoints.

Conforms to Directive M4.1, M4.5, and 09_API_CONTRACT.md.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, Field

from app.core.scheme.enums import (
    GovernmentLevel,
    RecommendationStatus,
    SchemeClassification,
    VerificationStatus,
)
from app.core.scheme.schemas import (
    EvidenceReference,
    ExplanationTrace,
    RuleCondition,
    SchemeRecommendationResult,
)


class SchemeSummaryResponse(BaseModel):
    """Catalog summary representation of a government or demo scheme."""
    scheme_id: str
    official_name: str
    display_name: str
    display_name_kn: str
    classification: SchemeClassification
    government_level: GovernmentLevel
    assistance_category: str
    verification_status: VerificationStatus
    demo_only: bool
    application_portal: Optional[str] = None


class SchemeDetailResponse(SchemeSummaryResponse):
    """Full detail specification of a scheme including rules and evidence references."""
    description: str
    description_kn: str
    benefit_description: str
    benefit_description_kn: str
    application_procedure: Optional[str] = None
    application_procedure_kn: Optional[str] = None
    applicable_geography: Optional[Dict[str, Any]] = None
    required_slots: List[str] = Field(default_factory=list)
    eligibility_conditions: List[RuleCondition] = Field(default_factory=list)
    exclusions: List[RuleCondition] = Field(default_factory=list)
    required_documents: List[str] = Field(default_factory=list)
    required_documents_kn: List[str] = Field(default_factory=list)
    evidence_references: List[EvidenceReference] = Field(default_factory=list)
    rule_version: str
    dataset_version: str
    official_verification_required: bool = True
    notes: Optional[str] = None


class RecommendationRunResponse(BaseModel):
    """Immutable recommendation run trace representation."""
    id: uuid.UUID
    conversation_id: uuid.UUID
    farmer_id: uuid.UUID
    scheme_rule_version_id: uuid.UUID
    evaluator_version: str
    outcome: str
    explanation_trace: ExplanationTrace
    evaluated_at: datetime


class RecommendationEvaluationResponse(BaseModel):
    """Response returned upon evaluating schemes for a farmer conversation."""
    conversation_id: uuid.UUID
    farmer_id: uuid.UUID
    total_evaluated: int
    recommendations: List[SchemeRecommendationResult]
