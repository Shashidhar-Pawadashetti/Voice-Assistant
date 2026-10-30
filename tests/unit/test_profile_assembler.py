"""Unit tests for AgriculturalProfileAssembler multi-turn integration, conflicts, and audit trail."""

from decimal import Decimal
import pytest

from app.core.normalization.ownership import OwnershipType
from app.core.profile.assembler import AgriculturalProfileAssembler
from app.core.profile.schemas import AgriculturalProfile


def test_multi_turn_profile_assembly():
    assembler = AgriculturalProfileAssembler()
    profile: AgriculturalProfile | None = None

    # Turn 1: Location statement
    profile = assembler.assemble_turn(profile, "ನಾನು ಧಾರವಾಡ ಜಿಲ್ಲೆ ಹುಬ್ಬಳ್ಳಿ ತಾಲೂಕಿನ ರೈತ")
    assert profile.district is not None
    assert profile.district.district_id == "DHARWAD"
    assert profile.taluk is not None
    assert profile.taluk.taluk_id == "HUBLI_URBAN"
    assert "district" not in profile.missing_critical_slots
    assert "crop" in profile.missing_critical_slots
    assert profile.is_ready_for_evaluation is False

    # Turn 2: Crop and land area statement
    profile = assembler.assemble_turn(profile, "ನನ್ನ ಬಳಿ ಎರಡೂವರೆ ಎಕರೆ ಜಮೀನಿದೆ, ಜೋಳ ಬೆಳೆಯುತ್ತಿದ್ದೇನೆ")
    assert profile.land_area is not None
    assert profile.land_area.canonical_acres == Decimal("2.5000")
    assert profile.primary_crop is not None
    assert profile.primary_crop.canonical_id == "SORGHUM"
    assert "crop" not in profile.missing_critical_slots
    assert "land_area" not in profile.missing_critical_slots
    assert "land_ownership" in profile.missing_critical_slots
    assert profile.is_ready_for_evaluation is False

    # Turn 3: Ownership and irrigation statement
    profile = assembler.assemble_turn(profile, "ಇದು ನನ್ನ ಸ್ವಂತ ಜಮೀನು, ಹನಿ ನೀರಾವರಿ ಇದೆ")
    assert profile.ownership is not None
    assert profile.ownership.ownership_type == OwnershipType.OWNER
    assert profile.irrigation_type is not None
    assert profile.irrigation_type.canonical_id == "DRIP"

    # All critical slots populated, no conflicts -> Ready for evaluation!
    assert len(profile.missing_critical_slots) == 0
    assert profile.is_ready_for_evaluation is True


def test_profile_correction_updates_slot_and_records_audit():
    assembler = AgriculturalProfileAssembler()

    # Initial turn with crop and area
    profile = assembler.assemble_turn(None, "ಧಾರವಾಡದಲ್ಲಿ ನಾಲ್ಕು ಎಕರೆ ಜೋಳ ಬೆಳೆಯುತ್ತಿದ್ದೇನೆ, ಸ್ವಂತ ಜಮೀನು")
    assert profile.primary_crop.canonical_id == "SORGHUM"
    assert profile.land_area.canonical_acres == Decimal("4.0000")

    # Correction turn: 'ನಾಲ್ಕು ಎಕರೆ ಅಲ್ಲ, ಮೂರೂವರೆ ಎಕರೆ'
    profile = assembler.assemble_turn(profile, "ನಾಲ್ಕು ಎಕರೆ ಅಲ್ಲ, ಮೂರೂವರೆ ಎಕರೆ")
    assert profile.land_area.canonical_acres == Decimal("3.5000")
    assert len(profile.audit_trail) == 1
    assert profile.audit_trail[0].slot == "land_area"
    assert profile.audit_trail[0].previous_value == "4.0000"
    assert profile.audit_trail[0].new_value == "3.5000"

    # Correction turn for crop: 'ಜೋಳ ಅಲ್ಲ ರಾಗಿ'
    profile = assembler.assemble_turn(profile, "ಜೋಳ ಅಲ್ಲ ರಾಗಿ")
    assert profile.primary_crop.canonical_id == "FINGER_MILLET"
    assert len(profile.audit_trail) == 2
    assert profile.audit_trail[1].slot == "crop"
    assert profile.audit_trail[1].previous_value == "SORGHUM"
    assert profile.audit_trail[1].new_value == "FINGER_MILLET"


def test_profile_geographic_conflict_detection():
    assembler = AgriculturalProfileAssembler()

    # Turn 1: District Mandya
    profile = assembler.assemble_turn(None, "ಮಂಡ್ಯ ಜಿಲ್ಲೆ")
    assert profile.district.district_id == "MANDYA"

    # Turn 2: Farmer states taluk Athani (which belongs to Belagavi, not Mandya!)
    profile = assembler.assemble_turn(profile, "ಅಥಣಿ ತಾಲೂಕು")
    # Conflict should be flagged!
    assert len(profile.conflicts) > 0
    assert "ಅಥಣಿ" in profile.conflicts[0]
    assert profile.is_ready_for_evaluation is False


def test_profile_assembler_does_not_calculate_eligibility():
    # Invariant check: AgriculturalProfile schema must have no eligibility fields
    profile = AgriculturalProfile()
    assert not hasattr(profile, "eligible_schemes")
    assert not hasattr(profile, "decision")
    assert not hasattr(profile, "entitlement_amount")
