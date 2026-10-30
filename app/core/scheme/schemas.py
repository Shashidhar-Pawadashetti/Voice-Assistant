"""Pydantic schemas for scheme definitions, rule conditions, evidence, and explanation traces.

Conforms to Directive M4, 07_SCHEME_ENGINE_AND_GOVERNANCE.md, and 08_SCHEME_CATALOG_SEED.md.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field

from app.core.scheme.enums import (
    EvidenceLevel,
    GovernmentLevel,
    LogicValue,
    RecommendationStatus,
    RuleOperator,
    SchemeClassification,
    VerificationStatus,
)


class EvidenceReference(BaseModel):
    """Authoritative government publication citation supporting a rule or condition."""
    source_title: str
    source_url: str
    publisher: str
    publication_date: Optional[str] = None
    access_date: str
    section: Optional[str] = None
    paragraph: Optional[str] = None
    summary: Optional[str] = None


class RuleCondition(BaseModel):
    """Controlled declarative rule condition evaluated deterministically in Python."""
    slot_key: str
    operator: RuleOperator
    expected_value: Any
    unit: Optional[str] = None
    required_provenance: Optional[EvidenceLevel] = None
    evidence_reference: Optional[str] = None
    condition_explanation: Optional[str] = None
    condition_explanation_kn: Optional[str] = None
    is_exclusion: bool = False


class RuleGroup(BaseModel):
    """Boolean compound expression tree of conditions or nested groups."""
    operator: RuleOperator  # AND, OR, NOT
    conditions: List[Union[RuleCondition, "RuleGroup"]] = Field(default_factory=list)


RuleGroup.model_rebuild()


class SchemeDefinition(BaseModel):
    """Complete, validated scheme catalogue entry and rule specification."""
    scheme_id: str
    official_name: str
    display_name: str
    display_name_kn: str
    classification: SchemeClassification
    government_level: GovernmentLevel
    assistance_category: str
    description: str
    description_kn: str
    benefit_description: str
    benefit_description_kn: str
    application_portal: Optional[str] = None
    application_procedure: Optional[str] = None
    application_procedure_kn: Optional[str] = None
    applicable_geography: Optional[Dict[str, Any]] = None
    required_slots: List[str] = Field(default_factory=list)
    eligibility_conditions: List[RuleCondition] = Field(default_factory=list)
    rule_group: Optional[RuleGroup] = None
    exclusions: List[RuleCondition] = Field(default_factory=list)
    required_documents: List[str] = Field(default_factory=list)
    required_documents_kn: List[str] = Field(default_factory=list)
    effective_from: Optional[datetime] = None
    effective_to: Optional[datetime] = None
    verification_status: VerificationStatus = VerificationStatus.INCOMPLETE
    evidence_references: List[EvidenceReference] = Field(default_factory=list)
    rule_version: str = "1.0.0"
    dataset_version: str = "2026.1"
    demo_only: bool = False
    official_verification_required: bool = True
    notes: Optional[str] = None


class ConditionTrace(BaseModel):
    """Auditable evaluation record for a single rule condition."""
    slot_key: str
    operator: str
    expected_value: Any
    actual_value: Any = None
    actual_provenance: Optional[str] = None
    required_provenance: Optional[str] = None
    result: LogicValue
    reason: str
    evidence_reference: Optional[str] = None
    is_exclusion: bool = False


class ExplanationTrace(BaseModel):
    """Machine-readable and human-interpretable explanation of an eligibility evaluation."""
    scheme_id: str
    display_name: str
    display_name_kn: str
    classification: SchemeClassification
    recommendation_status: RecommendationStatus
    official_verification_required: bool = True
    rule_version: str
    evaluator_version: str = "v1.0.0"
    matched_conditions: List[ConditionTrace] = Field(default_factory=list)
    failed_conditions: List[ConditionTrace] = Field(default_factory=list)
    unknown_conditions: List[ConditionTrace] = Field(default_factory=list)
    missing_slots: List[str] = Field(default_factory=list)
    unverified_conditions: List[ConditionTrace] = Field(default_factory=list)
    evidence_references: List[EvidenceReference] = Field(default_factory=list)
    kannada_explanation: str
    english_summary: str
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SchemeRecommendationResult(BaseModel):
    """API-facing result for a scheme recommendation."""
    scheme_id: str
    display_name: str
    display_name_kn: str
    classification: SchemeClassification
    government_level: GovernmentLevel
    assistance_category: str
    recommendation_status: RecommendationStatus
    official_verification_required: bool = True
    demo_only: bool = False
    explanation_trace: ExplanationTrace
    application_portal: Optional[str] = None
