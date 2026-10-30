"""Unit tests for deterministic three-valued logic scheme evaluator.

Tests all operators, truth tables, provenance, exclusions, and lifecycle statuses.
"""

from datetime import datetime, timezone
from decimal import Decimal
import pytest

from app.core.normalization.land_area import normalize_land_area
from app.core.normalization.location import DistrictInfo, TalukInfo
from app.core.normalization.ownership import NormalizedOwnership, OwnershipType, ProvenanceAssertion
from app.core.normalization.vocabulary import NormalizedTerm, VocabularyCategory
from app.core.profile.schemas import AgriculturalProfile
from app.core.scheme.catalog import (
    DEMO_EQUIPMENT_SCHEME,
    DEMO_MICRO_IRRIGATION_SCHEME,
    DEMO_SOIL_SCHEME,
    PM_KISAN_SCHEME,
    PMFBY_SCHEME,
)
from app.core.scheme.enums import (
    EvidenceLevel,
    LogicValue,
    RecommendationStatus,
    RuleOperator,
    SchemeClassification,
    VerificationStatus,
)
from app.core.scheme.evaluator import EligibilityEvaluator
from app.core.scheme.schemas import RuleCondition, RuleGroup, SchemeDefinition


def test_truth_table_and():
    """Verify three-valued AND truth table matches 07_SCHEME_ENGINE_AND_GOVERNANCE.md."""
    # TRUE AND TRUE -> TRUE
    assert EligibilityEvaluator._three_valued_and([LogicValue.TRUE, LogicValue.TRUE]) == LogicValue.TRUE
    # TRUE AND UNKNOWN -> UNKNOWN
    assert EligibilityEvaluator._three_valued_and([LogicValue.TRUE, LogicValue.UNKNOWN]) == LogicValue.UNKNOWN
    # FALSE AND UNKNOWN -> FALSE
    assert EligibilityEvaluator._three_valued_and([LogicValue.FALSE, LogicValue.UNKNOWN]) == LogicValue.FALSE
    # FALSE AND TRUE -> FALSE
    assert EligibilityEvaluator._three_valued_and([LogicValue.FALSE, LogicValue.TRUE]) == LogicValue.FALSE
    # UNKNOWN AND UNKNOWN -> UNKNOWN
    assert EligibilityEvaluator._three_valued_and([LogicValue.UNKNOWN, LogicValue.UNKNOWN]) == LogicValue.UNKNOWN


def test_truth_table_or():
    """Verify three-valued OR truth table matches 07_SCHEME_ENGINE_AND_GOVERNANCE.md."""
    # TRUE OR UNKNOWN -> TRUE
    assert EligibilityEvaluator._three_valued_or([LogicValue.TRUE, LogicValue.UNKNOWN]) == LogicValue.TRUE
    # FALSE OR UNKNOWN -> UNKNOWN
    assert EligibilityEvaluator._three_valued_or([LogicValue.FALSE, LogicValue.UNKNOWN]) == LogicValue.UNKNOWN
    # FALSE OR FALSE -> FALSE
    assert EligibilityEvaluator._three_valued_or([LogicValue.FALSE, LogicValue.FALSE]) == LogicValue.FALSE
    # TRUE OR FALSE -> TRUE
    assert EligibilityEvaluator._three_valued_or([LogicValue.TRUE, LogicValue.FALSE]) == LogicValue.TRUE
    # UNKNOWN OR UNKNOWN -> UNKNOWN
    assert EligibilityEvaluator._three_valued_or([LogicValue.UNKNOWN, LogicValue.UNKNOWN]) == LogicValue.UNKNOWN


def test_truth_table_not():
    """Verify three-valued NOT truth table."""
    assert EligibilityEvaluator._three_valued_not(LogicValue.TRUE) == LogicValue.FALSE
    assert EligibilityEvaluator._three_valued_not(LogicValue.FALSE) == LogicValue.TRUE
    assert EligibilityEvaluator._three_valued_not(LogicValue.UNKNOWN) == LogicValue.UNKNOWN


def test_numeric_comparison_operators():
    """Verify GT, GTE, LT, LTE operators with numbers and decimals."""
    # GT
    assert EligibilityEvaluator._eval_op(RuleOperator.GT, 3.5, 2.0) == LogicValue.TRUE
    assert EligibilityEvaluator._eval_op(RuleOperator.GT, 2.0, 3.5) == LogicValue.FALSE
    assert EligibilityEvaluator._eval_op(RuleOperator.GT, 2.0, 2.0) == LogicValue.FALSE

    # GTE
    assert EligibilityEvaluator._eval_op(RuleOperator.GTE, 2.0, 2.0) == LogicValue.TRUE
    assert EligibilityEvaluator._eval_op(RuleOperator.GTE, 1.9, 2.0) == LogicValue.FALSE

    # LT
    assert EligibilityEvaluator._eval_op(RuleOperator.LT, 1.5, 2.0) == LogicValue.TRUE
    assert EligibilityEvaluator._eval_op(RuleOperator.LT, 2.0, 1.5) == LogicValue.FALSE

    # LTE
    assert EligibilityEvaluator._eval_op(RuleOperator.LTE, 2.0, 2.0) == LogicValue.TRUE
    assert EligibilityEvaluator._eval_op(RuleOperator.LTE, 2.1, 2.0) == LogicValue.FALSE


def test_membership_and_equality_operators():
    """Verify EQ, NEQ, IN, NOT_IN, EXISTS operators."""
    # EQ / NEQ
    assert EligibilityEvaluator._eval_op(RuleOperator.EQ, "Dharwad", "Dharwad") == LogicValue.TRUE
    assert EligibilityEvaluator._eval_op(RuleOperator.EQ, "Dharwad", "Belagavi") == LogicValue.FALSE
    assert EligibilityEvaluator._eval_op(RuleOperator.NEQ, "Dharwad", "Belagavi") == LogicValue.TRUE

    # IN / NOT_IN
    assert EligibilityEvaluator._eval_op(RuleOperator.IN, "OWNER", ["OWNER", "CO_OWNER"]) == LogicValue.TRUE
    assert EligibilityEvaluator._eval_op(RuleOperator.IN, "TENANT_OR_CULTIVATOR", ["OWNER", "CO_OWNER"]) == LogicValue.FALSE
    assert EligibilityEvaluator._eval_op(RuleOperator.NOT_IN, "TENANT_OR_CULTIVATOR", ["OWNER", "CO_OWNER"]) == LogicValue.TRUE

    # EXISTS
    assert EligibilityEvaluator._eval_op(RuleOperator.EXISTS, "jowar", True) == LogicValue.TRUE
    assert EligibilityEvaluator._eval_op(RuleOperator.EXISTS, None, True) == LogicValue.UNKNOWN
    assert EligibilityEvaluator._eval_op(RuleOperator.EXISTS, "", True) == LogicValue.FALSE


def make_district(d_id="DHARWAD", name_en="Dharwad", name_kn="ಧಾರವಾಡ"):
    return DistrictInfo(district_id=d_id, english_name=name_en, kannada_name=name_kn, matched_alias=name_kn)


def test_pmfby_incomplete_status_produces_rules_not_verified():
    """Directive M4.2 invariant: PMFBY with INCOMPLETE status must block eligibility."""
    profile = AgriculturalProfile(
        district=make_district("DHARWAD", "Dharwad", "ಧಾರವಾಡ"),
        primary_crop=NormalizedTerm(
            canonical_id="jowar",
            category=VocabularyCategory.CROP,
            kannada_name="ಜೋಳ",
            english_name="Sorghum",
            matched_alias="ಜೋಳ",
        ),
        season=NormalizedTerm(
            canonical_id="kharif",
            category=VocabularyCategory.SEASON,
            kannada_name="ಮುಂಗಾರು",
            english_name="Kharif",
            matched_alias="ಮುಂಗಾರು",
        ),
    )
    trace = EligibilityEvaluator.evaluate(PMFBY_SCHEME, profile)
    assert trace.recommendation_status == RecommendationStatus.RULES_NOT_VERIFIED
    assert trace.classification == SchemeClassification.REAL_GOVERNMENT
    assert "ಅಧಿಕೃತ ಮಾಹಿತಿ ಇಲ್ಲದೆ" in trace.kannada_explanation


def test_pm_kisan_self_reported_owner_requires_verification():
    """Self-reported ownership matches condition value but requires official verification."""
    profile = AgriculturalProfile(
        district=make_district("DHARWAD", "Dharwad", "ಧಾರವಾಡ"),
        ownership=NormalizedOwnership(
            ownership_type=OwnershipType.OWNER,
            assertion=ProvenanceAssertion.USER_STATED,
            kannada_description="ಸ್ವಂತ ಜಮೀನು",
            raw_utterance="ನನ್ನ ಸ್ವಂತ ಜಮೀನು",
        ),
    )
    trace = EligibilityEvaluator.evaluate(PM_KISAN_SCHEME, profile)
    # Self-reported facts produce VERIFICATION_REQUIRED for conditions demanding OFFICIALLY_VERIFIED
    assert trace.recommendation_status == RecommendationStatus.VERIFICATION_REQUIRED
    assert trace.official_verification_required is True
    assert len(trace.unverified_conditions) == 1
    assert trace.unverified_conditions[0].slot_key == "land_ownership"
    assert "ಭೂಮಿ ಪಹಣಿ/ಆಧಾರ್ ಇ-ಕೆವೈಸಿ" in trace.kannada_explanation


def test_pm_kisan_officially_verified_owner_potentially_matched():
    """When Bhoomi state record is officially verified, PM-KISAN produces POTENTIALLY_MATCHED."""
    profile = AgriculturalProfile(
        district=make_district("DHARWAD", "Dharwad", "ಧಾರವಾಡ"),
        ownership=NormalizedOwnership(
            ownership_type=OwnershipType.OWNER,
            assertion=ProvenanceAssertion.USER_CONFIRMED,
            kannada_description="ಸ್ವಂತ ಜಮೀನು",
            raw_utterance="ಸ್ವಂತ",
        ),
    )
    verified_facts = {"land_ownership": "OWNER", "land_ownership_verified": True}
    trace = EligibilityEvaluator.evaluate(PM_KISAN_SCHEME, profile, verified_facts=verified_facts)
    assert trace.recommendation_status == RecommendationStatus.POTENTIALLY_MATCHED
    assert trace.official_verification_required is True
    assert len(trace.matched_conditions) == 1
    assert len(trace.unverified_conditions) == 0


def test_pm_kisan_hard_exclusion_income_tax_disqualifies():
    """Positive match on hard exclusion leads directly to NOT_MATCHED."""
    profile = AgriculturalProfile(
        district=make_district("DHARWAD", "Dharwad", "ಧಾರವಾಡ"),
        ownership=NormalizedOwnership(
            ownership_type=OwnershipType.OWNER,
            assertion=ProvenanceAssertion.USER_CONFIRMED,
            kannada_description="ಸ್ವಂತ ಜಮೀನು",
            raw_utterance="ಸ್ವಂತ",
        ),
    )
    verified_facts = {"income_tax_payer": True}
    trace = EligibilityEvaluator.evaluate(PM_KISAN_SCHEME, profile, verified_facts=verified_facts)
    assert trace.recommendation_status == RecommendationStatus.NOT_MATCHED
    assert len(trace.failed_conditions) == 1
    assert trace.failed_conditions[0].slot_key == "income_tax_payer"
    assert "ವಿನಾಯಿತಿ" in trace.kannada_explanation


def test_pm_kisan_tenant_fails_ownership_condition():
    """Tenant/leased farmer fails PM-KISAN ownership condition."""
    profile = AgriculturalProfile(
        district=make_district("MANDYA", "Mandya", "ಮಂಡ್ಯ"),
        ownership=NormalizedOwnership(
            ownership_type=OwnershipType.TENANT_OR_CULTIVATOR,
            assertion=ProvenanceAssertion.USER_STATED,
            kannada_description="ಗೇಣಿ ರೈತ",
            raw_utterance="ಗೇಣಿ",
        ),
    )
    trace = EligibilityEvaluator.evaluate(PM_KISAN_SCHEME, profile)
    assert trace.recommendation_status == RecommendationStatus.NOT_MATCHED
    assert len(trace.failed_conditions) == 1
    assert trace.failed_conditions[0].slot_key == "land_ownership"


def test_demo_micro_irrigation_missing_slots_insufficient_information():
    """Missing land area or irrigation yields INSUFFICIENT_INFORMATION."""
    profile = AgriculturalProfile(
        district=make_district("BELAGAVI", "Belagavi", "ಬೆಳಗಾವಿ"),
        # Missing land_area and irrigation
    )
    trace = EligibilityEvaluator.evaluate(DEMO_MICRO_IRRIGATION_SCHEME, profile)
    assert trace.recommendation_status == RecommendationStatus.INSUFFICIENT_INFORMATION
    assert "land_area" in trace.missing_slots
    assert "irrigation" in trace.missing_slots
    assert "ಹೆಚ್ಚಿನ ಮಾಹಿತಿ ಅಗತ್ಯವಿದೆ" in trace.kannada_explanation


def test_demo_micro_irrigation_potential_match():
    """Complete profile matches synthetic demo micro irrigation."""
    profile = AgriculturalProfile(
        district=make_district("BELAGAVI", "Belagavi", "ಬೆಳಗಾವಿ"),
        land_area=normalize_land_area("3 acres"),
        irrigation_type=NormalizedTerm(
            canonical_id="DRIP",
            category=VocabularyCategory.IRRIGATION,
            kannada_name="ಹನಿ ನೀರಾವರಿ",
            english_name="Drip",
            matched_alias="ಹನಿ",
        ),
    )
    trace = EligibilityEvaluator.evaluate(DEMO_MICRO_IRRIGATION_SCHEME, profile)
    assert trace.recommendation_status == RecommendationStatus.POTENTIALLY_MATCHED
    assert trace.classification == SchemeClassification.SYNTHETIC_DEMO
    assert "ಡೆಮೊ ಮಾತ್ರ" in trace.kannada_explanation


def test_rule_group_compound_evaluation():
    """Test compound RuleGroup with AND / OR nesting."""
    cond_district = RuleCondition(slot_key="district", operator=RuleOperator.EXISTS, expected_value=True)
    cond_crop = RuleCondition(slot_key="crop", operator=RuleOperator.EQ, expected_value="cotton")
    cond_irrigation = RuleCondition(slot_key="irrigation", operator=RuleOperator.EQ, expected_value="drip")

    # (district EXISTS AND (crop == 'cotton' OR irrigation == 'drip'))
    or_group = RuleGroup(operator=RuleOperator.OR, conditions=[cond_crop, cond_irrigation])
    root_group = RuleGroup(operator=RuleOperator.AND, conditions=[cond_district, or_group])

    profile = AgriculturalProfile(
        district=make_district("HAVERI", "Haveri", "ಹಾವೇರಿ"),
        primary_crop=NormalizedTerm(
            canonical_id="maize",
            category=VocabularyCategory.CROP,
            kannada_name="ಮೆಕ್ಕೆಜೋಳ",
            english_name="Maize",
            matched_alias="ಮೆಕ್ಕೆಜೋಳ",
        ),
        irrigation_type=NormalizedTerm(
            canonical_id="drip",
            category=VocabularyCategory.IRRIGATION,
            kannada_name="ಹನಿ ನೀರಾವರಿ",
            english_name="Drip",
            matched_alias="ಹನಿ",
        ),
    )

    res, traces = EligibilityEvaluator.eval_rule_group(root_group, profile, {})
    assert res == LogicValue.TRUE
    assert len(traces) == 3


def test_scheme_effective_date_validation():
    """Verify effective date boundary checks."""
    now = datetime.now(timezone.utc)
    profile = AgriculturalProfile(district=make_district())

    # Future scheme (not yet effective)
    future_scheme = PM_KISAN_SCHEME.model_copy(
        update={"effective_from": datetime(2099, 1, 1, tzinfo=timezone.utc)}
    )
    res_future = EligibilityEvaluator.evaluate(future_scheme, profile, evaluation_date=now)
    assert res_future.recommendation_status == RecommendationStatus.NOT_MATCHED
    assert "ಇನ್ನೂ ಜಾರಿಗೆ ಬಂದಿಲ್ಲ" in res_future.kannada_explanation

    # Expired scheme
    past_scheme = PM_KISAN_SCHEME.model_copy(
        update={"effective_to": datetime(2020, 1, 1, tzinfo=timezone.utc)}
    )
    res_past = EligibilityEvaluator.evaluate(past_scheme, profile, evaluation_date=now)
    assert res_past.recommendation_status == RecommendationStatus.NOT_MATCHED
    assert "ಮುಕ್ತಾಯಗೊಂಡಿದೆ" in res_past.kannada_explanation


def test_evaluator_operator_edge_cases():
    """Verify operator edge cases (None values, type mismatch, invalid numeric)."""
    assert EligibilityEvaluator._eval_op(RuleOperator.EQ, None, "test") == LogicValue.UNKNOWN
    assert EligibilityEvaluator._eval_op(RuleOperator.GT, "invalid_num", 5.0) == LogicValue.UNKNOWN
    assert EligibilityEvaluator._eval_op(RuleOperator.IN, "drip", "not_a_list") == LogicValue.FALSE
    assert EligibilityEvaluator._eval_op(RuleOperator.NOT_IN, "drip", "not_a_list") == LogicValue.TRUE

