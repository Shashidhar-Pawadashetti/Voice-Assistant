"""Unit tests for IntentSlotRegistry requirement rules and missing slot resolution."""

from decimal import Decimal
import pytest

from app.core.dialogue.intent_registry import IntentSlotResolver
from app.core.normalization.land_area import LandUnit, NormalizedLandArea
from app.core.normalization.location import DistrictInfo
from app.core.normalization.ownership import NormalizedOwnership, OwnershipType, ProvenanceAssertion
from app.core.normalization.vocabulary import NormalizedTerm, VocabularyCategory
from app.core.profile.schemas import AgriculturalProfile
from app.schemas.extraction import Intent


def test_intent_slot_requirements_definitions():
    inc_req = IntentSlotResolver.get_requirement(Intent.INCOME_SUPPORT)
    assert "district" in inc_req.required_slots
    assert "land_ownership" in inc_req.required_slots
    assert "land_area" in inc_req.required_slots

    ins_req = IntentSlotResolver.get_requirement(Intent.CROP_INSURANCE)
    assert "district" in ins_req.required_slots
    assert "crop" in ins_req.required_slots
    assert "season" in ins_req.required_slots

    irr_req = IntentSlotResolver.get_requirement(Intent.MICRO_IRRIGATION)
    assert "district" in irr_req.required_slots
    assert "irrigation" in irr_req.required_slots

    eq_req = IntentSlotResolver.get_requirement(Intent.AGRICULTURAL_EQUIPMENT)
    assert "district" in eq_req.required_slots
    assert "equipment" in eq_req.required_slots


def test_missing_slots_computation():
    profile = AgriculturalProfile()
    # Income support requires district, land_ownership, land_area
    missing = IntentSlotResolver.get_missing_slots(Intent.INCOME_SUPPORT, profile)
    assert set(missing) == {"district", "land_ownership", "land_area"}

    # Add district
    profile.district = DistrictInfo(
        district_id="DHARWAD",
        kannada_name="ಧಾರವಾಡ",
        english_name="Dharwad",
        matched_alias="ಧಾರವಾಡ",
    )
    missing = IntentSlotResolver.get_missing_slots(Intent.INCOME_SUPPORT, profile)
    assert set(missing) == {"land_ownership", "land_area"}

    # Add land_area
    profile.land_area = NormalizedLandArea(
        original_utterance="2 ಎಕರೆ",
        original_value=Decimal("2"),
        original_unit=LandUnit.ACRE,
        canonical_acres=Decimal("2.0000"),
        canonical_guntas=Decimal("80.00"),
        canonical_hectares=Decimal("0.8094"),
    )
    missing = IntentSlotResolver.get_missing_slots(Intent.INCOME_SUPPORT, profile)
    assert missing == ["land_ownership"]

    # Add land_ownership
    profile.ownership = NormalizedOwnership(
        ownership_type=OwnershipType.OWNER,
        kannada_description="ಸ್ವಂತ ಜಮೀನು",
        raw_utterance="ಸ್ವಂತ",
        assertion=ProvenanceAssertion.USER_STATED,
    )
    missing = IntentSlotResolver.get_missing_slots(Intent.INCOME_SUPPORT, profile)
    assert missing == []


def test_next_missing_slot_priority():
    profile = AgriculturalProfile()
    # Priority order for crop insurance: district -> crop -> season -> land_area
    next_slot = IntentSlotResolver.get_next_missing_slot(Intent.CROP_INSURANCE, profile)
    assert next_slot == "district"

    profile.district = DistrictInfo(
        district_id="MANDYA",
        kannada_name="ಮಂಡ್ಯ",
        english_name="Mandya",
        matched_alias="ಮಂಡ್ಯ",
    )
    next_slot = IntentSlotResolver.get_next_missing_slot(Intent.CROP_INSURANCE, profile)
    assert next_slot == "crop"
