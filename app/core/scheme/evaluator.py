"""Deterministic, three-valued scheme eligibility evaluation engine in pure Python.

Conforms strictly to Directive M4.3, M4.4, 07_SCHEME_ENGINE_AND_GOVERNANCE.md, and 15_IMPLEMENTATION_PLAN.md.
Rules:
1. Python-only deterministic evaluation. Zero LLM involvement in logic decisions.
2. Zero unrestricted Python eval, exec, arbitrary SQL or dynamic imports.
3. Three-valued logic: TRUE, FALSE, UNKNOWN.
4. AND: any FALSE -> FALSE; all TRUE -> TRUE; otherwise UNKNOWN.
5. OR: any TRUE -> TRUE; all FALSE -> FALSE; otherwise UNKNOWN.
6. NOT: TRUE -> FALSE; FALSE -> TRUE; UNKNOWN -> UNKNOWN.
7. Unverified facts cannot satisfy conditions requiring official verification.
8. Decisive contradiction or hard exclusion match yields NOT_MATCHED.
9. Missing required facts yield INSUFFICIENT_INFORMATION.
10. Unverified or incomplete rules yield RULES_NOT_VERIFIED.
11. Real schemes with self-reported matches yield VERIFICATION_REQUIRED or POTENTIALLY_MATCHED with official_verification_required: true.
"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple, Union

from app.core.normalization.ownership import ProvenanceAssertion
from app.core.profile.schemas import AgriculturalProfile
from app.core.scheme.enums import (
    EvidenceLevel,
    LogicValue,
    RecommendationStatus,
    RuleOperator,
    SchemeClassification,
    VerificationStatus,
)
from app.core.scheme.schemas import (
    ConditionTrace,
    ExplanationTrace,
    RuleCondition,
    RuleGroup,
    SchemeDefinition,
)


class EligibilityEvaluator:
    """Evaluates declarative scheme rules against structured farmer facts deterministically."""

    EVALUATOR_VERSION: str = "v1.0.0"

    @classmethod
    def evaluate(
        cls,
        scheme: SchemeDefinition,
        profile: AgriculturalProfile,
        verified_facts: Optional[Dict[str, Any]] = None,
        evaluation_date: Optional[datetime] = None,
    ) -> ExplanationTrace:
        """Evaluate a scheme definition against a farmer's agricultural profile and verified facts."""
        eval_dt = evaluation_date or datetime.now(timezone.utc)
        verified_facts = verified_facts or {}

        matched: List[ConditionTrace] = []
        failed: List[ConditionTrace] = []
        unknown: List[ConditionTrace] = []
        unverified: List[ConditionTrace] = []
        missing_slots: List[str] = []

        # 1. Scheme Rule Governance Pre-check (Section 7, 07_SCHEME_ENGINE_AND_GOVERNANCE.md)
        if scheme.verification_status in (
            VerificationStatus.INCOMPLETE,
            VerificationStatus.STALE,
            VerificationStatus.SUSPENDED,
        ):
            reason_msg = (
                f"Scheme '{scheme.scheme_id}' rules are marked {scheme.verification_status.value}. "
                "Official seasonal notifications or rules have not been independently verified."
            )
            kannada_msg = (
                f"'{scheme.display_name_kn}' ಯೋಜನೆಯ ಪ್ರಸ್ತುತ ಸರ್ಕಾರದ ನಿಯಮಾವಳಿಗಳು ಪರಿಶೀಲನೆ ಹಂತದಲ್ಲಿವೆ (ಅಪೂರ್ಣ). "
                "ಅಧಿಕೃತ ಮಾಹಿತಿ ಇಲ್ಲದೆ ಅರ್ಹತೆಯನ್ನು ನಿರ್ಣಯಿಸಲಾಗುವುದಿಲ್ಲ."
            )
            return ExplanationTrace(
                scheme_id=scheme.scheme_id,
                display_name=scheme.display_name,
                display_name_kn=scheme.display_name_kn,
                classification=scheme.classification,
                recommendation_status=RecommendationStatus.RULES_NOT_VERIFIED,
                official_verification_required=scheme.official_verification_required,
                rule_version=scheme.rule_version,
                evaluator_version=cls.EVALUATOR_VERSION,
                matched_conditions=[],
                failed_conditions=[],
                unknown_conditions=[],
                missing_slots=scheme.required_slots,
                unverified_conditions=[],
                evidence_references=scheme.evidence_references,
                kannada_explanation=kannada_msg,
                english_summary=reason_msg,
                evaluated_at=eval_dt,
            )

        # 2. Check Effective Date Range
        if scheme.effective_from and eval_dt < scheme.effective_from:
            return cls._not_matched_result(
                scheme=scheme,
                reason="Scheme is not yet effective.",
                kannada_reason="ಈ ಯೋಜನೆ ಇನ್ನೂ ಜಾರಿಗೆ ಬಂದಿಲ್ಲ.",
                eval_dt=eval_dt,
            )
        if scheme.effective_to and eval_dt > scheme.effective_to:
            return cls._not_matched_result(
                scheme=scheme,
                reason="Scheme effective period has expired.",
                kannada_reason="ಈ ಯೋಜನೆಯ ಅವಧಿ ಮುಕ್ತಾಯಗೊಂಡಿದೆ.",
                eval_dt=eval_dt,
            )

        # 3. Evaluate Hard Exclusions
        unknown_exclusions: List[ConditionTrace] = []
        for excl in scheme.exclusions:
            trace = cls.eval_condition(excl, profile, verified_facts)
            if trace.result == LogicValue.TRUE:
                # Disqualifying exclusion satisfied!
                failed.append(trace)
                reason_en = f"Disqualified by exclusion: {trace.reason}"
                reason_kn = (
                    f"ಯೋಜನೆಯ ವಿನಾಯಿತಿ ಷರತ್ತಿನನ್ವಯ ಅನರ್ಹತೆ: {excl.condition_explanation_kn or trace.reason}"
                )
                return ExplanationTrace(
                    scheme_id=scheme.scheme_id,
                    display_name=scheme.display_name,
                    display_name_kn=scheme.display_name_kn,
                    classification=scheme.classification,
                    recommendation_status=RecommendationStatus.NOT_MATCHED,
                    official_verification_required=scheme.official_verification_required,
                    rule_version=scheme.rule_version,
                    evaluator_version=cls.EVALUATOR_VERSION,
                    matched_conditions=matched,
                    failed_conditions=failed,
                    unknown_conditions=unknown + unknown_exclusions,
                    missing_slots=missing_slots,
                    unverified_conditions=unverified,
                    evidence_references=scheme.evidence_references,
                    kannada_explanation=reason_kn,
                    english_summary=reason_en,
                    evaluated_at=eval_dt,
                )
            elif trace.result == LogicValue.UNKNOWN:
                # Exclusion cannot be safely ruled out from conversational input
                unknown_exclusions.append(trace)

        # 4. Check Missing Required Slots
        for slot in scheme.required_slots:
            val, _ = cls._extract_slot_value_and_provenance(slot, profile, verified_facts)
            if val is None:
                missing_slots.append(slot)

        # 5. Evaluate Eligibility Conditions (Individual Conditions & RuleGroup)
        all_condition_traces: List[ConditionTrace] = []
        for cond in scheme.eligibility_conditions:
            trace = cls.eval_condition(cond, profile, verified_facts)
            all_condition_traces.append(trace)
            if trace.result == LogicValue.TRUE:
                matched.append(trace)
            elif trace.result == LogicValue.FALSE:
                failed.append(trace)
            else:
                unknown.append(trace)
                if trace.required_provenance == EvidenceLevel.OFFICIALLY_VERIFIED.value:
                    unverified.append(trace)

        # If a nested RuleGroup exists, evaluate it as well
        if scheme.rule_group:
            group_val, group_traces = cls.eval_rule_group(scheme.rule_group, profile, verified_facts)
            for trace in group_traces:
                all_condition_traces.append(trace)
                if trace.result == LogicValue.TRUE and trace not in matched:
                    matched.append(trace)
                elif trace.result == LogicValue.FALSE and trace not in failed:
                    failed.append(trace)
                elif trace.result == LogicValue.UNKNOWN and trace not in unknown:
                    unknown.append(trace)

        # 6. Determine Final Recommendation Outcome
        if failed:
            status = RecommendationStatus.NOT_MATCHED
            en_summary = (
                f"Did not match {scheme.display_name}. "
                f"Failed condition(s): {', '.join(t.slot_key for t in failed)}."
            )
            kn_summary = (
                f"ನಿಮ್ಮ ವಿವರಗಳು '{scheme.display_name_kn}' ಯೋಜನೆಗೆ ಸರಿಹೊಂದುತ್ತಿಲ್ಲ. "
                f"ಕಾರಣ: {failed[0].reason}."
            )
        elif missing_slots:
            status = RecommendationStatus.INSUFFICIENT_INFORMATION
            en_summary = (
                f"Insufficient information to determine eligibility for {scheme.display_name}. "
                f"Missing required slot(s): {', '.join(missing_slots)}."
            )
            kn_summary = (
                f"'{scheme.display_name_kn}' ಯೋಜನೆಯ ಪರಿಶೀಲನೆಗೆ ಹೆಚ್ಚಿನ ಮಾಹಿತಿ ಅಗತ್ಯವಿದೆ. "
                f"ದಯವಿಟ್ಟು ಉಳಿದ ಕೃಷಿ ವಿವರಗಳನ್ನು ತಿಳಿಸಿ."
            )
        elif unknown or unverified:
            # All known facts match, but conditions requiring official government verification remain
            status = RecommendationStatus.VERIFICATION_REQUIRED
            en_summary = (
                f"Potentially eligible for {scheme.display_name} based on self-reported details, "
                "but official government document verification (e.g. land records/Bhoomi or e-KYC) is required."
            )
            kn_summary = (
                f"ನೀವು ತಿಳಿಸಿರುವ ವಿವರಗಳ ಪ್ರಕಾರ '{scheme.display_name_kn}' ಯೋಜನೆಗೆ ಸಂಭಾವ್ಯವಾಗಿ ಅರ್ಹರಾಗಿದ್ದೀರಿ. "
                "ಆದರೆ ಸರ್ಕಾರದ ಅಧಿಕೃತ ದಾಖಲೆಗಳು (ಭೂಮಿ ಪಹಣಿ/ಆಧಾರ್ ಇ-ಕೆವೈಸಿ) ಪರಿಶೀಲನೆಯಾಗಬೇಕಾಗಿದೆ."
            )
        else:
            status = RecommendationStatus.POTENTIALLY_MATCHED
            if scheme.demo_only:
                en_summary = f"Potentially matched for synthetic test {scheme.display_name} (DEMO ONLY)."
                kn_summary = f"ಮಾದರಿ ಪರೀಕ್ಷಾ ಯೋಜನೆ '{scheme.display_name_kn}'ಗೆ ವಿವರಗಳು ಹೊಂದಾಣಿಕೆಯಾಗಿವೆ (ಡೆಮೊ ಮಾತ್ರ)."
            else:
                en_summary = (
                    f"Potentially matched for {scheme.display_name}. "
                    "Official application and portal verification required."
                )
                kn_summary = (
                    f"ನಿಮ್ಮ ವಿವರಗಳ ಆಧಾರದ ಮೇಲೆ ನೀವು '{scheme.display_name_kn}' ಯೋಜನೆಗೆ ಸಂಭಾವ್ಯವಾಗಿ ಅರ್ಹರಾಗಿದ್ದೀರಿ. "
                    "ಅಂತಿಮ ಮಂಜೂರಾತಿಗಾಗಿ ಅಧಿಕೃತ ಪೋರ್ಟಲ್‌ನಲ್ಲಿ ಪರಿಶೀಲನೆ ಅಗತ್ಯ."
                )

        return ExplanationTrace(
            scheme_id=scheme.scheme_id,
            display_name=scheme.display_name,
            display_name_kn=scheme.display_name_kn,
            classification=scheme.classification,
            recommendation_status=status,
            official_verification_required=scheme.official_verification_required,
            rule_version=scheme.rule_version,
            evaluator_version=cls.EVALUATOR_VERSION,
            matched_conditions=matched,
            failed_conditions=failed,
            unknown_conditions=unknown + unknown_exclusions,
            missing_slots=missing_slots,
            unverified_conditions=unverified,
            evidence_references=scheme.evidence_references,
            kannada_explanation=kn_summary,
            english_summary=en_summary,
            evaluated_at=eval_dt,
        )

    @classmethod
    def eval_condition(
        cls,
        condition: RuleCondition,
        profile: AgriculturalProfile,
        verified_facts: Dict[str, Any],
    ) -> ConditionTrace:
        """Evaluate a single declarative condition using three-valued logic."""
        actual_val, provenance = cls._extract_slot_value_and_provenance(
            condition.slot_key, profile, verified_facts
        )

        # 1. Missing actual value produces UNKNOWN
        if actual_val is None:
            return ConditionTrace(
                slot_key=condition.slot_key,
                operator=condition.operator.value,
                expected_value=condition.expected_value,
                actual_value=None,
                actual_provenance=None,
                required_provenance=condition.required_provenance.value if condition.required_provenance else None,
                result=LogicValue.UNKNOWN,
                reason=f"Slot '{condition.slot_key}' is missing or not provided.",
                evidence_reference=condition.evidence_reference,
                is_exclusion=condition.is_exclusion,
            )

        # 2. Check provenance if condition demands official verification
        if condition.required_provenance == EvidenceLevel.OFFICIALLY_VERIFIED:
            is_verified = (
                provenance == EvidenceLevel.OFFICIALLY_VERIFIED.value
                or verified_facts.get(f"{condition.slot_key}_verified") is True
            )
            # If not officially verified, value alone cannot satisfy verified requirement
            if not is_verified:
                # Check if value matches anyway
                val_matches = cls._eval_op(condition.operator, actual_val, condition.expected_value, condition.unit)
                if val_matches == LogicValue.TRUE:
                    return ConditionTrace(
                        slot_key=condition.slot_key,
                        operator=condition.operator.value,
                        expected_value=condition.expected_value,
                        actual_value=actual_val,
                        actual_provenance=provenance,
                        required_provenance=EvidenceLevel.OFFICIALLY_VERIFIED.value,
                        result=LogicValue.UNKNOWN,
                        reason=(
                            f"Slot '{condition.slot_key}' matches value '{actual_val}' ({provenance}), "
                            "but requires authoritative official verification."
                        ),
                        evidence_reference=condition.evidence_reference,
                        is_exclusion=condition.is_exclusion,
                    )
                elif val_matches == LogicValue.FALSE:
                    return ConditionTrace(
                        slot_key=condition.slot_key,
                        operator=condition.operator.value,
                        expected_value=condition.expected_value,
                        actual_value=actual_val,
                        actual_provenance=provenance,
                        required_provenance=EvidenceLevel.OFFICIALLY_VERIFIED.value,
                        result=LogicValue.FALSE,
                        reason=f"Slot '{condition.slot_key}' value '{actual_val}' does not satisfy condition.",
                        evidence_reference=condition.evidence_reference,
                        is_exclusion=condition.is_exclusion,
                    )

        # 3. Standard operator evaluation
        logic_res = cls._eval_op(condition.operator, actual_val, condition.expected_value, condition.unit)
        reason_text = (
            f"Condition '{condition.slot_key}' {condition.operator.value} '{condition.expected_value}' "
            f"evaluated to {logic_res.value} (actual: '{actual_val}')."
        )
        return ConditionTrace(
            slot_key=condition.slot_key,
            operator=condition.operator.value,
            expected_value=condition.expected_value,
            actual_value=actual_val,
            actual_provenance=provenance,
            required_provenance=condition.required_provenance.value if condition.required_provenance else None,
            result=logic_res,
            reason=reason_text,
            evidence_reference=condition.evidence_reference,
            is_exclusion=condition.is_exclusion,
        )

    @classmethod
    def eval_rule_group(
        cls,
        group: RuleGroup,
        profile: AgriculturalProfile,
        verified_facts: Dict[str, Any],
    ) -> Tuple[LogicValue, List[ConditionTrace]]:
        """Evaluate a compound RuleGroup using three-valued logic truth tables."""
        child_traces: List[ConditionTrace] = []
        child_results: List[LogicValue] = []

        for item in group.conditions:
            if isinstance(item, RuleCondition):
                trace = cls.eval_condition(item, profile, verified_facts)
                child_traces.append(trace)
                child_results.append(trace.result)
            elif isinstance(item, RuleGroup):
                sub_res, sub_traces = cls.eval_rule_group(item, profile, verified_facts)
                child_traces.extend(sub_traces)
                child_results.append(sub_res)

        op = group.operator
        if op == RuleOperator.AND:
            final_res = cls._three_valued_and(child_results)
        elif op == RuleOperator.OR:
            final_res = cls._three_valued_or(child_results)
        elif op == RuleOperator.NOT:
            first_res = child_results[0] if child_results else LogicValue.UNKNOWN
            final_res = cls._three_valued_not(first_res)
        else:
            final_res = LogicValue.UNKNOWN

        return final_res, child_traces

    # --- Three-Valued Logic Truth Table Implementations ---

    @staticmethod
    def _three_valued_and(values: List[LogicValue]) -> LogicValue:
        """AND: any FALSE -> FALSE; all TRUE -> TRUE; otherwise UNKNOWN."""
        if not values:
            return LogicValue.TRUE
        if any(v == LogicValue.FALSE for v in values):
            return LogicValue.FALSE
        if all(v == LogicValue.TRUE for v in values):
            return LogicValue.TRUE
        return LogicValue.UNKNOWN

    @staticmethod
    def _three_valued_or(values: List[LogicValue]) -> LogicValue:
        """OR: any TRUE -> TRUE; all FALSE -> FALSE; otherwise UNKNOWN."""
        if not values:
            return LogicValue.FALSE
        if any(v == LogicValue.TRUE for v in values):
            return LogicValue.TRUE
        if all(v == LogicValue.FALSE for v in values):
            return LogicValue.FALSE
        return LogicValue.UNKNOWN

    @staticmethod
    def _three_valued_not(value: LogicValue) -> LogicValue:
        """NOT: TRUE -> FALSE; FALSE -> TRUE; UNKNOWN -> UNKNOWN."""
        if value == LogicValue.TRUE:
            return LogicValue.FALSE
        if value == LogicValue.FALSE:
            return LogicValue.TRUE
        return LogicValue.UNKNOWN

    # --- Operator Logic (Pure Deterministic Python) ---

    @classmethod
    def _eval_op(
        cls,
        op: RuleOperator,
        actual: Any,
        expected: Any,
        unit: Optional[str] = None,
    ) -> LogicValue:
        """Execute safe binary comparison between actual and expected value."""
        if actual is None:
            return LogicValue.UNKNOWN

        # Numeric conversions when comparing quantities
        if op in (RuleOperator.GT, RuleOperator.GTE, RuleOperator.LT, RuleOperator.LTE):
            try:
                act_num = Decimal(str(actual))
                exp_num = Decimal(str(expected))
            except Exception:
                return LogicValue.UNKNOWN

            if op == RuleOperator.GT:
                return LogicValue.TRUE if act_num > exp_num else LogicValue.FALSE
            elif op == RuleOperator.GTE:
                return LogicValue.TRUE if act_num >= exp_num else LogicValue.FALSE
            elif op == RuleOperator.LT:
                return LogicValue.TRUE if act_num < exp_num else LogicValue.FALSE
            elif op == RuleOperator.LTE:
                return LogicValue.TRUE if act_num <= exp_num else LogicValue.FALSE

        if op == RuleOperator.EQ:
            # String comparison case-insensitive if strings
            if isinstance(actual, str) and isinstance(expected, str):
                return LogicValue.TRUE if actual.strip().lower() == expected.strip().lower() else LogicValue.FALSE
            return LogicValue.TRUE if actual == expected else LogicValue.FALSE

        if op == RuleOperator.NEQ:
            if isinstance(actual, str) and isinstance(expected, str):
                return LogicValue.TRUE if actual.strip().lower() != expected.strip().lower() else LogicValue.FALSE
            return LogicValue.TRUE if actual != expected else LogicValue.FALSE

        if op == RuleOperator.IN:
            if isinstance(expected, (list, tuple, set)):
                # Case-insensitive if string list
                if isinstance(actual, str):
                    exp_lower = [str(x).strip().lower() for x in expected]
                    return LogicValue.TRUE if actual.strip().lower() in exp_lower else LogicValue.FALSE
                return LogicValue.TRUE if actual in expected else LogicValue.FALSE
            return LogicValue.FALSE

        if op == RuleOperator.NOT_IN:
            if isinstance(expected, (list, tuple, set)):
                if isinstance(actual, str):
                    exp_lower = [str(x).strip().lower() for x in expected]
                    return LogicValue.TRUE if actual.strip().lower() not in exp_lower else LogicValue.FALSE
                return LogicValue.TRUE if actual not in expected else LogicValue.FALSE
            return LogicValue.TRUE

        if op == RuleOperator.EXISTS:
            is_present = actual is not None and actual != "" and actual != []
            if expected is True:
                return LogicValue.TRUE if is_present else LogicValue.FALSE
            else:
                return LogicValue.FALSE if is_present else LogicValue.TRUE

        return LogicValue.UNKNOWN

    # --- Profile Slot Value Extraction ---

    @classmethod
    def _extract_slot_value_and_provenance(
        cls,
        slot_key: str,
        profile: AgriculturalProfile,
        verified_facts: Dict[str, Any],
    ) -> Tuple[Any, Optional[str]]:
        """Extract canonical slot value and provenance level from profile or verified facts."""
        # 1. Check verified facts dictionary first
        if slot_key in verified_facts:
            return verified_facts[slot_key], EvidenceLevel.OFFICIALLY_VERIFIED.value

        # 2. Map slot keys to AgriculturalProfile
        if slot_key == "district":
            if profile.district:
                return profile.district.district_id, EvidenceLevel.USER_STATED.value
            return None, None

        if slot_key == "taluk":
            if profile.taluk:
                return profile.taluk.taluk_id, EvidenceLevel.USER_STATED.value
            return None, None

        if slot_key == "crop":
            if profile.primary_crop:
                return profile.primary_crop.canonical_id, EvidenceLevel.USER_STATED.value
            return None, None

        if slot_key == "land_ownership":
            if profile.ownership:
                prov = (
                    EvidenceLevel.USER_CONFIRMED.value
                    if profile.ownership.assertion == ProvenanceAssertion.USER_CONFIRMED
                    else EvidenceLevel.USER_STATED.value
                )
                return profile.ownership.ownership_type.value, prov
            return None, None

        if slot_key == "land_area":
            if profile.land_area and not profile.land_area.is_ambiguous:
                return float(profile.land_area.canonical_acres), EvidenceLevel.USER_STATED.value
            return None, None

        if slot_key == "irrigation":
            if profile.irrigation_type:
                return profile.irrigation_type.canonical_id, EvidenceLevel.USER_STATED.value
            return None, None

        if slot_key == "season":
            if profile.season:
                return profile.season.canonical_id, EvidenceLevel.USER_STATED.value
            return None, None

        if slot_key == "equipment":
            if profile.equipment:
                return profile.equipment[0].canonical_id, EvidenceLevel.USER_STATED.value
            return None, None

        if slot_key == "soil_improvement":
            if profile.soil_improvements:
                return profile.soil_improvements[0].canonical_id, EvidenceLevel.USER_STATED.value
            return None, None

        # Check negative exclusion flags (defaults to None if not explicitly stated)
        if slot_key in ("income_tax_payer", "govt_employee", "constitutional_post_holder", "pensioner_above_10k"):
            return None, None

        return None, None

    @classmethod
    def _not_matched_result(
        cls,
        scheme: SchemeDefinition,
        reason: str,
        kannada_reason: str,
        eval_dt: datetime,
    ) -> ExplanationTrace:
        return ExplanationTrace(
            scheme_id=scheme.scheme_id,
            display_name=scheme.display_name,
            display_name_kn=scheme.display_name_kn,
            classification=scheme.classification,
            recommendation_status=RecommendationStatus.NOT_MATCHED,
            official_verification_required=scheme.official_verification_required,
            rule_version=scheme.rule_version,
            evaluator_version=cls.EVALUATOR_VERSION,
            matched_conditions=[],
            failed_conditions=[],
            unknown_conditions=[],
            missing_slots=[],
            unverified_conditions=[],
            evidence_references=scheme.evidence_references,
            kannada_explanation=kannada_reason,
            english_summary=reason,
            evaluated_at=eval_dt,
        )
