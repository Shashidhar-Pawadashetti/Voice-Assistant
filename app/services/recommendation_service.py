"""Recommendation service managing deterministic scheme evaluation and immutable audit runs.

Conforms to Directive M4.5, M4.6, 07_SCHEME_ENGINE_AND_GOVERNANCE.md, and 10_DATA_MODEL.md.
Rules:
1. Pure Python evaluation using EligibilityEvaluator. LLM never alters evaluation results.
2. Every evaluation run is immutably recorded in PostgreSQL recommendation_runs.
3. Strict BOLA farmer ownership enforcement on all queries and trace access.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConversationOwnershipError, NotFoundError
from app.core.profile.schemas import AgriculturalProfile
from app.core.scheme.catalog import ALL_SCHEMES, SCHEMES_BY_ID
from app.core.scheme.enums import RecommendationStatus, SchemeClassification
from app.core.scheme.evaluator import EligibilityEvaluator
from app.core.scheme.explainability import format_grounded_kannada_explanation
from app.core.scheme.repository import SchemeCatalogRepository, SchemeRuleRepository
from app.core.scheme.schemas import ExplanationTrace, SchemeDefinition, SchemeRecommendationResult
from app.models.conversation import Conversation
from app.models.scheme import RecommendationRun, Scheme, SchemeRuleVersion
from app.schemas.extraction import Intent


# Intent to assistance category mapping
INTENT_TO_CATEGORIES: Dict[Intent, List[str]] = {
    Intent.INCOME_SUPPORT: ["INCOME_SUPPORT"],
    Intent.CROP_INSURANCE: ["CROP_INSURANCE"],
    Intent.MICRO_IRRIGATION: ["MICRO_IRRIGATION"],
    Intent.AGRICULTURAL_EQUIPMENT: ["AGRICULTURAL_EQUIPMENT"],
    Intent.SOIL_IMPROVEMENT: ["SOIL_IMPROVEMENT"],
    Intent.FIND_SCHEMES: ["INCOME_SUPPORT", "CROP_INSURANCE", "MICRO_IRRIGATION", "AGRICULTURAL_EQUIPMENT", "SOIL_IMPROVEMENT"],
}


class RecommendationService:
    """Orchestrates deterministic scheme evaluation, explanation generation, and persistence."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.catalog_repo = SchemeCatalogRepository(db)
        self.rule_repo = SchemeRuleRepository(db)

    async def evaluate_for_farmer(
        self,
        farmer_id: uuid.UUID,
        conversation_id: uuid.UUID,
        profile: AgriculturalProfile,
        intent: Optional[Intent] = None,
        evaluation_date: Optional[datetime] = None,
        verified_facts: Optional[Dict[str, Any]] = None,
    ) -> List[SchemeRecommendationResult]:
        """Evaluate applicable schemes for a conversation and record immutable recommendation runs."""
        # 1. BOLA Check: Verify conversation belongs to farmer
        conv_stmt = select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.farmer_id == farmer_id,
        )
        res = await self.db.execute(conv_stmt)
        conversation = res.scalar_one_or_none()
        if not conversation:
            raise ConversationOwnershipError(
                f"Conversation {conversation_id} does not belong to farmer {farmer_id}."
            )

        eval_dt = evaluation_date or datetime.now(timezone.utc)
        verified_facts = verified_facts or {}

        # 2. Identify Target Scheme Definitions
        target_categories = INTENT_TO_CATEGORIES.get(intent, None) if intent else None
        candidate_definitions: List[SchemeDefinition] = []

        if target_categories:
            for s in ALL_SCHEMES:
                if s.assistance_category in target_categories:
                    candidate_definitions.append(s)
        else:
            candidate_definitions = list(ALL_SCHEMES)

        results: List[SchemeRecommendationResult] = []

        # 3. Deterministically Evaluate Each Scheme
        for scheme_def in candidate_definitions:
            trace = EligibilityEvaluator.evaluate(
                scheme=scheme_def,
                profile=profile,
                verified_facts=verified_facts,
                evaluation_date=eval_dt,
            )

            # Re-generate grounded natural Kannada explanation
            trace.kannada_explanation = format_grounded_kannada_explanation(trace)

            # 4. Lookup Database Scheme and Rule Version Records
            db_scheme = await self.catalog_repo.get_by_scheme_id(scheme_def.scheme_id)
            scheme_rule_version_id: Optional[uuid.UUID] = None

            if db_scheme:
                latest_rv = await self.rule_repo.get_latest_version(scheme_def.scheme_id)
                if latest_rv:
                    scheme_rule_version_id = latest_rv.id
                elif db_scheme.rule_versions:
                    scheme_rule_version_id = db_scheme.rule_versions[0].id
            else:
                # Auto-provision scheme & initial rule version into DB if missing
                new_scheme = Scheme(
                    id=uuid.uuid4(),
                    scheme_id=scheme_def.scheme_id,
                    classification=scheme_def.classification.value,
                    display_name=scheme_def.display_name,
                    display_name_kn=scheme_def.display_name_kn,
                    description=scheme_def.description,
                    description_kn=scheme_def.description_kn,
                    benefit_description=scheme_def.benefit_description,
                    benefit_description_kn=scheme_def.benefit_description_kn,
                    application_portal=scheme_def.application_portal,
                    applicable_geography=scheme_def.applicable_geography,
                    dataset_version=scheme_def.dataset_version,
                    assistance_category=scheme_def.assistance_category,
                    government_level=scheme_def.government_level.value,
                    active=True,
                )
                self.db.add(new_scheme)
                await self.db.flush()

                def_dict = scheme_def.model_dump(mode="json")
                new_rv = SchemeRuleVersion(
                    id=uuid.uuid4(),
                    scheme_id=new_scheme.id,
                    rule_version=scheme_def.rule_version,
                    definition=def_dict,
                    definition_hash=SchemeRuleRepository.compute_definition_hash(def_dict),
                    verification_status=scheme_def.verification_status.value,
                )
                self.db.add(new_rv)
                await self.db.flush()
                scheme_rule_version_id = new_rv.id

            # 5. Persist Immutable Recommendation Run in PostgreSQL
            if scheme_rule_version_id:
                rec_run = RecommendationRun(
                    id=uuid.uuid4(),
                    farmer_id=farmer_id,
                    conversation_id=conversation_id,
                    profile_snapshot=profile.model_dump(mode="json"),
                    scheme_rule_version_id=scheme_rule_version_id,
                    evaluator_version=EligibilityEvaluator.EVALUATOR_VERSION,
                    outcome=trace.recommendation_status.value,
                    explanation_trace=trace.model_dump(mode="json"),
                    evaluated_at=eval_dt,
                )
                self.db.add(rec_run)

            results.append(
                SchemeRecommendationResult(
                    scheme_id=scheme_def.scheme_id,
                    display_name=scheme_def.display_name,
                    display_name_kn=scheme_def.display_name_kn,
                    classification=scheme_def.classification,
                    government_level=scheme_def.government_level,
                    assistance_category=scheme_def.assistance_category,
                    recommendation_status=trace.recommendation_status,
                    official_verification_required=trace.official_verification_required,
                    demo_only=scheme_def.demo_only,
                    explanation_trace=trace,
                    application_portal=scheme_def.application_portal,
                )
            )

        # Commit all recommendation runs in one atomic transaction
        await self.db.commit()

        return results

    async def get_conversation_recommendations(
        self,
        farmer_id: uuid.UUID,
        conversation_id: uuid.UUID,
    ) -> List[RecommendationRun]:
        """Fetch historical immutable recommendation traces for a conversation (BOLA enforced)."""
        conv_stmt = select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.farmer_id == farmer_id,
        )
        res = await self.db.execute(conv_stmt)
        if not res.scalar_one_or_none():
            raise ConversationOwnershipError(
                f"Conversation {conversation_id} does not belong to farmer {farmer_id}."
            )

        stmt = (
            select(RecommendationRun)
            .where(
                RecommendationRun.conversation_id == conversation_id,
                RecommendationRun.farmer_id == farmer_id,
            )
            .order_by(RecommendationRun.evaluated_at.asc())
        )
        runs_res = await self.db.execute(stmt)
        return list(runs_res.scalars().all())
