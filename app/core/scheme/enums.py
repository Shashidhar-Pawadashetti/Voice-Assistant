"""Enumerations for government scheme intelligence and rule evaluation.

Conforms to Directive M4, 07_SCHEME_ENGINE_AND_GOVERNANCE.md, and 08_SCHEME_CATALOG_SEED.md.
"""

from enum import Enum


class SchemeClassification(str, Enum):
    """Classification distinguishing real government entitlements from synthetic tests."""
    REAL_GOVERNMENT = "REAL_GOVERNMENT"
    SYNTHETIC_DEMO = "SYNTHETIC_DEMO"


class VerificationStatus(str, Enum):
    """Rule verification and lifecycle status."""
    INCOMPLETE = "INCOMPLETE"
    VERIFIED = "VERIFIED"
    STALE = "STALE"
    SUSPENDED = "SUSPENDED"
    VERIFIED_FOR_DEMO_ONLY = "VERIFIED_FOR_DEMO_ONLY"


class GovernmentLevel(str, Enum):
    """Jurisdiction level."""
    CENTRAL = "CENTRAL"
    STATE = "STATE"
    LOCAL = "LOCAL"
    NONE = "NONE"


class RuleOperator(str, Enum):
    """Allowed deterministic operators. Unrestricted Python eval or SQL is strictly prohibited."""
    EQ = "EQ"
    NEQ = "NEQ"
    IN = "IN"
    NOT_IN = "NOT_IN"
    GT = "GT"
    GTE = "GTE"
    LT = "LT"
    LTE = "LTE"
    EXISTS = "EXISTS"
    AND = "AND"
    OR = "OR"
    NOT = "NOT"


class LogicValue(str, Enum):
    """Three-valued logic state."""
    TRUE = "TRUE"
    FALSE = "FALSE"
    UNKNOWN = "UNKNOWN"


class RecommendationStatus(str, Enum):
    """Overall recommendation outcome. Never confers an approved entitlement."""
    POTENTIALLY_MATCHED = "POTENTIALLY_MATCHED"
    NOT_MATCHED = "NOT_MATCHED"
    INSUFFICIENT_INFORMATION = "INSUFFICIENT_INFORMATION"
    VERIFICATION_REQUIRED = "VERIFICATION_REQUIRED"
    RULES_NOT_VERIFIED = "RULES_NOT_VERIFIED"


class EvidenceLevel(str, Enum):
    """Evidence strength for fact verification."""
    SELF_REPORTED = "SELF_REPORTED"
    USER_STATED = "USER_STATED"
    USER_CONFIRMED = "USER_CONFIRMED"
    OFFICIALLY_VERIFIED = "OFFICIALLY_VERIFIED"
