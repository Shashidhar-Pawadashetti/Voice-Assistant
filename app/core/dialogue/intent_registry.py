"""Intent-dependent slot requirements registry for Krishi Mitra dialogue.

Conforms to Directive M3.3, 06_DIALOGUE_AND_MEMORY.md Section 5, and 08_SCHEME_CATALOG_SEED.md.
Principle:
Do NOT force every farmer to provide every agricultural field.
Different assistance categories declare specific required slots.
General guidance remains available even when eligibility fields are incomplete.
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field

from app.core.normalization.ownership import OwnershipType
from app.core.profile.schemas import AgriculturalProfile
from app.schemas.extraction import Intent


class IntentSlotRequirement(BaseModel):
    """Specification of required and optional slots for an agricultural intent."""

    intent: Intent
    required_slots: List[str] = Field(
        description="Mandatory slot keys required before evaluation readiness",
    )
    optional_slots: List[str] = Field(
        default_factory=list,
        description="Beneficial contextual slots that do not block initial guidance",
    )
    priority_order: List[str] = Field(
        description="Order in which missing slots should be asked from the farmer",
    )


# Intent to slot requirement configuration
INTENT_SLOT_REGISTRY: Dict[Intent, IntentSlotRequirement] = {
    Intent.INCOME_SUPPORT: IntentSlotRequirement(
        intent=Intent.INCOME_SUPPORT,
        required_slots=["district", "land_ownership", "land_area"],
        optional_slots=["crop"],
        priority_order=["district", "land_ownership", "land_area"],
    ),
    Intent.CROP_INSURANCE: IntentSlotRequirement(
        intent=Intent.CROP_INSURANCE,
        required_slots=["district", "crop", "season"],
        optional_slots=["land_area", "land_ownership"],
        priority_order=["district", "crop", "season", "land_area"],
    ),
    Intent.MICRO_IRRIGATION: IntentSlotRequirement(
        intent=Intent.MICRO_IRRIGATION,
        required_slots=["district", "irrigation", "land_area", "land_ownership"],
        optional_slots=["crop"],
        priority_order=["district", "irrigation", "land_area", "land_ownership"],
    ),
    Intent.AGRICULTURAL_EQUIPMENT: IntentSlotRequirement(
        intent=Intent.AGRICULTURAL_EQUIPMENT,
        required_slots=["district", "equipment", "land_area"],
        optional_slots=["land_ownership", "crop"],
        priority_order=["district", "equipment", "land_area", "land_ownership"],
    ),
    Intent.SOIL_IMPROVEMENT: IntentSlotRequirement(
        intent=Intent.SOIL_IMPROVEMENT,
        required_slots=["district", "soil_improvement"],
        optional_slots=["crop", "land_area"],
        priority_order=["district", "soil_improvement", "crop"],
    ),
    Intent.FIND_SCHEMES: IntentSlotRequirement(
        intent=Intent.FIND_SCHEMES,
        required_slots=["district", "crop"],
        optional_slots=["land_area", "land_ownership", "irrigation"],
        priority_order=["district", "crop", "land_area", "land_ownership"],
    ),
    # Explanatory and Informational intents have no mandatory slots
    Intent.EXPLAIN_SCHEME: IntentSlotRequirement(
        intent=Intent.EXPLAIN_SCHEME,
        required_slots=[],
        optional_slots=["district", "crop"],
        priority_order=["district"],
    ),
    Intent.APPLICATION_STEPS: IntentSlotRequirement(
        intent=Intent.APPLICATION_STEPS,
        required_slots=[],
        optional_slots=["district", "crop"],
        priority_order=["district"],
    ),
    Intent.GREETING: IntentSlotRequirement(
        intent=Intent.GREETING,
        required_slots=[],
        optional_slots=[],
        priority_order=[],
    ),
    Intent.HELP: IntentSlotRequirement(
        intent=Intent.HELP,
        required_slots=[],
        optional_slots=[],
        priority_order=[],
    ),
    Intent.UNKNOWN: IntentSlotRequirement(
        intent=Intent.UNKNOWN,
        required_slots=["district"],
        optional_slots=["crop", "assistance_need"],
        priority_order=["district", "crop"],
    ),
}


class IntentSlotResolver:
    """Evaluates missing slots and determines the next question to ask a farmer."""

    @staticmethod
    def get_requirement(intent: Intent) -> IntentSlotRequirement:
        """Fetch requirement for an intent, defaulting to general discovery if unknown."""
        return INTENT_SLOT_REGISTRY.get(intent, INTENT_SLOT_REGISTRY[Intent.FIND_SCHEMES])

    @classmethod
    def get_missing_slots(
        cls,
        intent: Intent,
        profile: Optional[AgriculturalProfile],
    ) -> List[str]:
        """Compute list of missing required slots for an intent given the current profile."""
        req = cls.get_requirement(intent)
        if not req.required_slots:
            return []

        if profile is None:
            return list(req.required_slots)

        missing: List[str] = []
        for slot in req.required_slots:
            if not cls._is_slot_populated(slot, profile):
                missing.append(slot)

        return missing

    @classmethod
    def get_next_missing_slot(
        cls,
        intent: Intent,
        profile: Optional[AgriculturalProfile],
    ) -> Optional[str]:
        """Pick the highest-priority missing slot to prompt the farmer next."""
        req = cls.get_requirement(intent)
        if not req.required_slots:
            return None

        if profile is None:
            return req.priority_order[0] if req.priority_order else None

        for slot in req.priority_order:
            if slot in req.required_slots and not cls._is_slot_populated(slot, profile):
                return slot

        return None

    @staticmethod
    def _is_slot_populated(slot_key: str, profile: AgriculturalProfile) -> bool:
        """Check whether a specific agricultural profile slot is populated and valid."""
        if slot_key == "district":
            return profile.district is not None
        if slot_key == "taluk":
            return profile.taluk is not None
        if slot_key == "crop":
            return profile.primary_crop is not None
        if slot_key == "land_area":
            return profile.land_area is not None and not profile.land_area.is_ambiguous
        if slot_key == "land_ownership":
            return profile.ownership is not None and profile.ownership.ownership_type != OwnershipType.UNKNOWN
        if slot_key == "irrigation":
            return profile.irrigation_type is not None
        if slot_key == "season":
            return profile.season is not None
        if slot_key == "equipment":
            return len(profile.equipment) > 0
        if slot_key == "soil_improvement":
            return len(profile.soil_improvements) > 0
        if slot_key == "assistance_need":
            return len(profile.assistance_needs) > 0
        return False
