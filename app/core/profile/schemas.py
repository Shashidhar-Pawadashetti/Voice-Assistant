"""Agricultural profile schemas and slot tracking state models.

Conforms to 02_PRODUCT_REQUIREMENTS.md Section 3, 06_DIALOGUE_AND_MEMORY.md Section 2, and M2.6.
Invariant: This schema stores structured facts and missing-field status.
It NEVER contains eligibility decisions or entitlement calculations.
"""

from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, Field

from app.core.normalization.corrections import SlotAuditRecord
from app.core.normalization.land_area import NormalizedLandArea
from app.core.normalization.location import DistrictInfo, TalukInfo
from app.core.normalization.ownership import NormalizedOwnership
from app.core.normalization.vocabulary import NormalizedTerm


# Critical slots declared in 02_PRODUCT_REQUIREMENTS.md Section 3
CRITICAL_SLOT_KEYS = ("district", "crop", "land_area", "land_ownership")


class AgriculturalProfile(BaseModel):
    """Normalized multi-turn agricultural profile for a farmer."""

    profile_id: str = Field(
        default_factory=lambda: uuid.uuid4().hex,
        description="Unique profile revision identifier",
    )
    farmer_id: Optional[str] = Field(default=None, description="Associated farmer ID if authenticated")
    district: Optional[DistrictInfo] = Field(default=None, description="Normalized district")
    taluk: Optional[TalukInfo] = Field(default=None, description="Normalized taluk")
    land_area: Optional[NormalizedLandArea] = Field(default=None, description="Normalized land measurement in acres")
    ownership: Optional[NormalizedOwnership] = Field(default=None, description="Land tenure classification")
    primary_crop: Optional[NormalizedTerm] = Field(default=None, description="Primary cultivated crop")
    secondary_crops: List[NormalizedTerm] = Field(default_factory=list, description="Secondary or inter-crops")
    irrigation_type: Optional[NormalizedTerm] = Field(default=None, description="Active irrigation infrastructure")
    season: Optional[NormalizedTerm] = Field(default=None, description="Agricultural cropping season")
    assistance_needs: List[NormalizedTerm] = Field(default_factory=list, description="Requested assistance categories")
    equipment: List[NormalizedTerm] = Field(default_factory=list, description="Mentioned or requested equipment")
    soil_improvements: List[NormalizedTerm] = Field(default_factory=list, description="Soil test or amendment needs")

    # Slot governance & readiness
    missing_critical_slots: List[str] = Field(
        default_factory=lambda: list(CRITICAL_SLOT_KEYS),
        description="Unfilled mandatory slots required before scheme rule evaluation",
    )
    conflicts: List[str] = Field(default_factory=list, description="Detected cross-field contradictions")
    audit_trail: List[SlotAuditRecord] = Field(default_factory=list, description="History of value revisions and corrections")
    is_ready_for_evaluation: bool = Field(
        default=False,
        description="True only when all critical slots are populated without unresolved conflicts",
    )
