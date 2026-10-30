"""Agricultural understanding and normalization subsystem exports."""

from app.core.normalization.corrections import (
    CorrectionDetectionResult,
    SlotAuditRecord,
    detect_correction,
)
from app.core.normalization.land_area import (
    LandUnit,
    NormalizedLandArea,
    normalize_land_area,
)
from app.core.normalization.location import (
    DistrictInfo,
    TalukInfo,
    get_taluks_for_district,
    normalize_district,
    normalize_taluk,
    validate_taluk_in_district,
)
from app.core.normalization.ownership import (
    NormalizedOwnership,
    OwnershipType,
    ProvenanceAssertion,
    normalize_ownership,
)
from app.core.normalization.vocabulary import (
    NormalizedTerm,
    VocabularyCategory,
    get_canonical_term,
    normalize_term,
)

__all__ = [
    "NormalizedTerm",
    "VocabularyCategory",
    "normalize_term",
    "get_canonical_term",
    "DistrictInfo",
    "TalukInfo",
    "normalize_district",
    "normalize_taluk",
    "validate_taluk_in_district",
    "get_taluks_for_district",
    "LandUnit",
    "NormalizedLandArea",
    "normalize_land_area",
    "OwnershipType",
    "ProvenanceAssertion",
    "NormalizedOwnership",
    "normalize_ownership",
    "CorrectionDetectionResult",
    "SlotAuditRecord",
    "detect_correction",
]
