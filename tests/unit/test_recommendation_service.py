"""Unit tests for Scheme repositories, explainability, and recommendation service helpers.

Conforms to Directive M4.5, M4.6, and maintains >= 85% coverage.
"""

from datetime import datetime, timezone
import uuid
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConversationOwnershipError
from app.core.profile.schemas import AgriculturalProfile
from app.core.scheme.catalog import PM_KISAN_SCHEME
from app.core.scheme.enums import (
    GovernmentLevel,
    LogicValue,
    RecommendationStatus,
    RuleOperator,
    SchemeClassification,
    VerificationStatus,
)
from app.core.scheme.evaluator import EligibilityEvaluator
from app.core.scheme.explainability import format_grounded_kannada_explanation
from app.core.scheme.repository import SchemeCatalogRepository, SchemeRuleRepository
from app.core.scheme.schemas import ConditionTrace, ExplanationTrace, RuleCondition, SchemeDefinition
from app.models.conversation import Conversation
from app.models.farmer import Farmer
from app.models.scheme import Scheme, SchemeRuleVersion
from app.services.recommendation_service import RecommendationService


@pytest.mark.asyncio
async def test_scheme_catalog_repository(db_session: AsyncSession):
    """Test SchemeCatalogRepository methods."""
    repo = SchemeCatalogRepository(db_session)
    scheme_id = str(uuid.uuid4())

    scheme = Scheme(
        id=uuid.uuid4(),
        scheme_id=f"TEST_SCHEME_{scheme_id[:8]}",
        classification=SchemeClassification.REAL_GOVERNMENT.value,
        display_name="Test Scheme",
        display_name_kn="ಟೆಸ್ಟ್ ಯೋಜನೆ",
        assistance_category="INCOME_SUPPORT",
        government_level=GovernmentLevel.CENTRAL.value,
        active=True,
    )
    db_session.add(scheme)
    await db_session.flush()

    # get_by_scheme_id
    found = await repo.get_by_scheme_id(scheme.scheme_id)
    assert found is not None
    assert found.display_name == "Test Scheme"

    # list_active
    all_active = await repo.list_active()
    assert len(all_active) >= 1

    by_class = await repo.list_active(classification=SchemeClassification.REAL_GOVERNMENT.value)
    assert any(s.scheme_id == scheme.scheme_id for s in by_class)

    by_cat = await repo.list_active(category="INCOME_SUPPORT")
    assert any(s.scheme_id == scheme.scheme_id for s in by_cat)


@pytest.mark.asyncio
async def test_scheme_rule_repository(db_session: AsyncSession):
    """Test SchemeRuleRepository version lookup and sha256 hashing."""
    cat_repo = SchemeCatalogRepository(db_session)
    rule_repo = SchemeRuleRepository(db_session)

    scheme_id = f"TEST_RULE_SCHEME_{uuid.uuid4().hex[:6]}"
    scheme = Scheme(
        id=uuid.uuid4(),
        scheme_id=scheme_id,
        classification=SchemeClassification.REAL_GOVERNMENT.value,
        display_name="Test Rule Scheme",
        assistance_category="CROP_INSURANCE",
        government_level=GovernmentLevel.CENTRAL.value,
        active=True,
    )
    db_session.add(scheme)
    await db_session.flush()

    def_data = {"test_rule": True, "required": ["district"]}
    computed_hash = SchemeRuleRepository.compute_definition_hash(def_data)
    assert len(computed_hash) == 64

    rv1 = SchemeRuleVersion(
        id=uuid.uuid4(),
        scheme_id=scheme.id,
        rule_version="1.0.0",
        definition=def_data,
        definition_hash=computed_hash,
        verification_status="VERIFIED",
    )
    rv2 = SchemeRuleVersion(
        id=uuid.uuid4(),
        scheme_id=scheme.id,
        rule_version="2.0.0",
        definition=def_data,
        definition_hash=computed_hash,
        verification_status="VERIFIED",
    )
    db_session.add_all([rv1, rv2])
    await db_session.flush()

    # get_latest_version
    latest = await rule_repo.get_latest_version(scheme_id)
    assert latest is not None

    # get_specific_version
    specific = await rule_repo.get_specific_version(scheme_id, "1.0.0")
    assert specific is not None
    assert specific.rule_version == "1.0.0"


@pytest.mark.asyncio
async def test_recommendation_service_bola_and_retrieval(db_session: AsyncSession):
    """Test RecommendationService get_conversation_recommendations and ownership guard."""
    rec_service = RecommendationService(db_session)
    farmer1 = uuid.uuid4()
    farmer2 = uuid.uuid4()
    conv_id = uuid.uuid4()

    f1 = Farmer(
        id=farmer1,
        phone_number_encrypted="enc1",
        phone_number_hash="hash1",
        password_hash="pwd1",
    )
    conv = Conversation(
        id=conv_id,
        farmer_id=farmer1,
        state="GREETING",
    )
    db_session.add_all([f1, conv])
    await db_session.flush()

    # Unauthorized access check
    with pytest.raises(ConversationOwnershipError):
        await rec_service.get_conversation_recommendations(
            farmer_id=farmer2,
            conversation_id=conv_id,
        )

    # Authorized access (empty list before evaluation)
    runs = await rec_service.get_conversation_recommendations(
        farmer_id=farmer1,
        conversation_id=conv_id,
    )
    assert runs == []


def test_format_grounded_kannada_explanation_all_statuses():
    """Verify explainability generator covers all RecommendationStatus outcomes."""
    # 1. RULES_NOT_VERIFIED
    trace_rnv = ExplanationTrace(
        scheme_id="PMFBY",
        display_name="PMFBY",
        display_name_kn="ಪಿಎಂಎಫ್‌ಬಿವೈ",
        classification=SchemeClassification.REAL_GOVERNMENT,
        recommendation_status=RecommendationStatus.RULES_NOT_VERIFIED,
        official_verification_required=True,
        rule_version="0.0.0",
        kannada_explanation="",
        english_summary="",
    )
    msg_rnv = format_grounded_kannada_explanation(trace_rnv)
    assert "ಪರಿಶೀಲನೆ ಹಂತದಲ್ಲಿವೆ" in msg_rnv

    # 2. NOT_MATCHED (with exclusion and condition failure)
    trace_nm = ExplanationTrace(
        scheme_id="PM_KISAN",
        display_name="PM-KISAN",
        display_name_kn="ಪಿಎಂ-ಕಿಸಾನ್",
        classification=SchemeClassification.REAL_GOVERNMENT,
        recommendation_status=RecommendationStatus.NOT_MATCHED,
        official_verification_required=True,
        rule_version="1.0.0",
        failed_conditions=[
            ConditionTrace(
                slot_key="income_tax_payer",
                operator="EQ",
                expected_value=True,
                result=LogicValue.TRUE,
                reason="Disqualified by tax",
                is_exclusion=True,
            ),
            ConditionTrace(
                slot_key="land_ownership",
                operator="IN",
                expected_value=["OWNER"],
                result=LogicValue.FALSE,
                reason="Not an owner",
                is_exclusion=False,
            ),
        ],
        kannada_explanation="",
        english_summary="",
    )
    msg_nm = format_grounded_kannada_explanation(trace_nm)
    assert "ಅರ್ಹರಾಗಿಲ್ಲ" in msg_nm
    assert "ವಿನಾಯಿತಿ" in msg_nm

    # 3. INSUFFICIENT_INFORMATION
    trace_ii = ExplanationTrace(
        scheme_id="DEMO_MICRO_IRRIGATION",
        display_name="Demo Micro Irrigation",
        display_name_kn="ಮಾದರಿ ಹನಿ ನೀರಾವರಿ",
        classification=SchemeClassification.SYNTHETIC_DEMO,
        recommendation_status=RecommendationStatus.INSUFFICIENT_INFORMATION,
        official_verification_required=False,
        rule_version="1.0.0",
        missing_slots=["district", "land_area", "irrigation"],
        kannada_explanation="",
        english_summary="",
    )
    msg_ii = format_grounded_kannada_explanation(trace_ii)
    assert "ಜಿಲ್ಲೆ" in msg_ii
    assert "ಅಗತ್ಯವಿದೆ" in msg_ii
    assert "ಡೆಮೊ" in msg_ii

    # 4. VERIFICATION_REQUIRED
    trace_vr = ExplanationTrace(
        scheme_id="PM_KISAN",
        display_name="PM-KISAN",
        display_name_kn="ಪಿಎಂ-ಕಿಸಾನ್",
        classification=SchemeClassification.REAL_GOVERNMENT,
        recommendation_status=RecommendationStatus.VERIFICATION_REQUIRED,
        official_verification_required=True,
        rule_version="1.0.0",
        kannada_explanation="",
        english_summary="",
    )
    msg_vr = format_grounded_kannada_explanation(trace_vr)
    assert "ಸಂಭಾವ್ಯವಾಗಿ" in msg_vr
    assert "ಭೂಮಿ ಪಹಣಿ" in msg_vr
    assert "ಇದು ಅಧಿಕೃತ ಮಂಜೂರಾತಿಯಲ್ಲ" in msg_vr

    # 5. POTENTIALLY_MATCHED (Real vs Demo)
    trace_pm_real = ExplanationTrace(
        scheme_id="PM_KISAN",
        display_name="PM-KISAN",
        display_name_kn="ಪಿಎಂ-ಕಿಸಾನ್",
        classification=SchemeClassification.REAL_GOVERNMENT,
        recommendation_status=RecommendationStatus.POTENTIALLY_MATCHED,
        official_verification_required=True,
        rule_version="1.0.0",
        kannada_explanation="",
        english_summary="",
    )
    msg_pm_real = format_grounded_kannada_explanation(trace_pm_real)
    assert "ಸಂಭಾವ್ಯವಾಗಿ ಅರ್ಹರಾಗಿದ್ದೀರಿ" in msg_pm_real
    assert "ಅಂತಿಮ ಮಂಜೂರಾತಿ ಅಲ್ಲ" in msg_pm_real

    trace_pm_demo = ExplanationTrace(
        scheme_id="DEMO_SOIL_IMPROVEMENT",
        display_name="Demo Soil",
        display_name_kn="ಮಾದರಿ ಮಣ್ಣು ಸುಧಾರಣೆ",
        classification=SchemeClassification.SYNTHETIC_DEMO,
        recommendation_status=RecommendationStatus.POTENTIALLY_MATCHED,
        official_verification_required=False,
        rule_version="1.0.0",
        kannada_explanation="",
        english_summary="",
    )
    msg_pm_demo = format_grounded_kannada_explanation(trace_pm_demo)
    assert "ಹೊಂದಾಣಿಕೆಯಾಗಿವೆ" in msg_pm_demo
    assert "ಡೆಮೊ" in msg_pm_demo
