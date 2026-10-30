"""Integration tests across Karnataka dialect zones and code-mixed agricultural queries."""

from decimal import Decimal
import pytest

from app.core.normalization.land_area import normalize_land_area
from app.core.normalization.location import normalize_district, normalize_taluk
from app.core.normalization.ownership import OwnershipType, normalize_ownership
from app.core.normalization.vocabulary import VocabularyCategory, normalize_term
from app.core.profile.assembler import AgriculturalProfileAssembler


# Regional Utterance Fixtures across Karnataka
REGIONAL_FIXTURES = [
    # North Karnataka (Dharwad, Belagavi, Bagalkote)
    {
        "zone": "North Karnataka",
        "utterance": "ಧಾರವಾಡ ಜಿಲ್ಲೆ ಹುಬ್ಬಳ್ಳಿ ತಾಲೂಕು ಮಾಲ್ದಂಡಿ ಜೋಳ ಎರಡೂವರೆ ಎಕರೆ ಸ್ವಂತ ಜಮೀನು ಹನಿ ನೀರಾವರಿ",
        "expected_district": "DHARWAD",
        "expected_taluk": "HUBLI_URBAN",
        "expected_crop": "SORGHUM",
        "expected_acres": Decimal("2.5000"),
        "expected_ownership": OwnershipType.OWNER,
        "expected_irrigation": "DRIP",
    },
    {
        "zone": "North Karnataka - Belagavi Sugarcane",
        "utterance": "ಬೆಳಗಾವಿ ಜಿಲ್ಲೆ ಅಥಣಿ ತಾಲೂಕಿನಲ್ಲಿ ನಾಲ್ಕು ಎಕರೆ ಗೇಣಿ ಜಮೀನಿನಲ್ಲಿ ಕಬ್ಬು ಬೆಳೆಯಲು ತುಂತುರು ನೀರಾವರಿ ಸಬ್ಸಿಡಿ ಬೇಕು",
        "expected_district": "BELAGAVI",
        "expected_taluk": "ATHANI",
        "expected_crop": "SUGARCANE",
        "expected_acres": Decimal("4.0000"),
        "expected_ownership": OwnershipType.TENANT_OR_CULTIVATOR,
        "expected_irrigation": "SPRINKLER",
    },
    # Southern Karnataka (Mandya, Mysuru, Chamarajanagara)
    {
        "zone": "Southern Karnataka - Mandya Paddy",
        "utterance": "ಮಂಡ್ಯ ಜಿಲ್ಲೆ ಮದ್ದೂರು ತಾಲೂಕು ಭತ್ತದ ಬೆಳೆ ಮೂರೂವರೆ ಎಕರೆ ಕಾಲುವೆ ನೀರು",
        "expected_district": "MANDYA",
        "expected_taluk": "MADDUR",
        "expected_crop": "PADDY",
        "expected_acres": Decimal("3.5000"),
        "expected_ownership": OwnershipType.UNKNOWN,
        "expected_irrigation": "CANAL",
    },
    {
        "zone": "Southern Karnataka - Mysuru Ragi",
        "utterance": "ಮೈಸೂರು ತಾಲೂಕಿನಲ್ಲಿ ಮುದ್ದೆ ರಾಗಿ ಎರಡು ಎಕರೆ ಇಪ್ಪತ್ತು ಗುಂಟೆ ಸ್ವಂತ ಖಾತೆ",
        "expected_district": "MYSURU",
        "expected_taluk": "MYSURU",
        "expected_crop": "FINGER_MILLET",
        "expected_acres": Decimal("2.5000"),
        "expected_ownership": OwnershipType.OWNER,
        "expected_irrigation": None,
    },
    # Kalyana Karnataka (Kalaburagi, Raichur, Bidar)
    {
        "zone": "Kalyana Karnataka - Kalaburagi Tur",
        "utterance": "ಕಲಬುರಗಿ ತಾಲೂಕು ತೊಗರಿ ಬೆಳೆ ಐದು ಎಕರೆ ಒಣಬೇಸಾಯ ಬರ ಪರಿಹಾರ ಬೇಕಾಗಿದೆ",
        "expected_district": "KALABURAGI",
        "expected_taluk": "KALABURAGI",
        "expected_crop": "PIGEON_PEA",
        "expected_acres": Decimal("5.0000"),
        "expected_ownership": OwnershipType.UNKNOWN,
        "expected_irrigation": "RAINFED",
    },
    {
        "zone": "Kalyana Karnataka - Raichur Cotton",
        "utterance": "ರಾಯಚೂರು ಜಿಲ್ಲೆ ಮಾನ್ವಿ ಹತ್ತಿ ಬೆಳೆ ಮೂರು ಎಕರೆ ಬೋರ್‌ವೆಲ್ ನೀರಾವರಿ",
        "expected_district": "RAICHUR",
        "expected_taluk": "MANVI",
        "expected_crop": "COTTON",
        "expected_acres": Decimal("3.0000"),
        "expected_ownership": OwnershipType.UNKNOWN,
        "expected_irrigation": "BOREWELL",
    },
    # Coastal Karnataka (Udupi, Dakshina Kannada)
    {
        "zone": "Coastal Karnataka - Udupi Arecanut",
        "utterance": "ಉಡುಪಿ ಜಿಲ್ಲೆ ಕುಂದಾಪುರ ತಾಲೂಕು ಅಡಿಕೆ ತೋಟ ಒಂದೂವರೆ ಎಕರೆ ಸ್ವಂತ ಜಮೀನು",
        "expected_district": "UDUPI",
        "expected_taluk": "KUNDAPURA",
        "expected_crop": "ARECANUT",
        "expected_acres": Decimal("1.5000"),
        "expected_ownership": OwnershipType.OWNER,
        "expected_irrigation": None,
    },
    # Code-Mixed Ag-English
    {
        "zone": "Code-Mixed English-Kannada",
        "utterance": "dharwad district navalgund 2 acre drip irrigation subsidy tractor loan",
        "expected_district": "DHARWAD",
        "expected_taluk": "NAVALGUND",
        "expected_crop": None,
        "expected_acres": Decimal("2.0000"),
        "expected_ownership": OwnershipType.UNKNOWN,
        "expected_irrigation": "DRIP",
    },
]


@pytest.mark.parametrize("fixture", REGIONAL_FIXTURES)
def test_regional_dialect_normalization_fixtures(fixture):
    utterance = fixture["utterance"]

    # 1. District
    if fixture["expected_district"]:
        dist = normalize_district(utterance)
        assert dist is not None, f"Failed district lookup in: {utterance}"
        assert dist.district_id == fixture["expected_district"]

    # 2. Taluk
    if fixture["expected_taluk"]:
        taluk = normalize_taluk(utterance)
        assert taluk is not None, f"Failed taluk lookup in: {utterance}"
        assert taluk.taluk_id == fixture["expected_taluk"]

    # 3. Crop
    if fixture["expected_crop"]:
        crops = normalize_term(utterance, category=VocabularyCategory.CROP)
        assert len(crops) >= 1, f"Failed crop lookup in: {utterance}"
        assert crops[0].canonical_id == fixture["expected_crop"]

    # 4. Land Area
    if fixture["expected_acres"]:
        area = normalize_land_area(utterance)
        assert area is not None, f"Failed area lookup in: {utterance}"
        assert area.canonical_acres == fixture["expected_acres"]

    # 5. Ownership
    if fixture["expected_ownership"] != OwnershipType.UNKNOWN:
        ownership = normalize_ownership(utterance)
        assert ownership.ownership_type == fixture["expected_ownership"]

    # 6. Irrigation
    if fixture["expected_irrigation"]:
        irrigation = normalize_term(utterance, category=VocabularyCategory.IRRIGATION)
        assert len(irrigation) >= 1, f"Failed irrigation lookup in: {utterance}"
        assert irrigation[0].canonical_id == fixture["expected_irrigation"]


def test_end_to_end_regional_profile_assembly():
    assembler = AgriculturalProfileAssembler()

    # Step 1: North Karnataka Dharwad Farmer
    p1 = assembler.assemble_turn(None, "ನಮಸ್ಕಾರ, ನಾನು ಧಾರವಾಡ ಜಿಲ್ಲೆ ನವಲಗುಂದ ತಾಲೂಕಿನ ರೈತ")
    assert p1.district.district_id == "DHARWAD"
    assert p1.taluk.taluk_id == "NAVALGUND"
    assert p1.is_ready_for_evaluation is False

    # Step 2: Adds Crop and Acreage in regional dialect
    p2 = assembler.assemble_turn(p1, "ನನ್ನ ಬಳಿ ಎರಡೂವರೆ ಎಕರೆ ಮಾಲ್ದಂಡಿ ಜೋಳ ಇದೆ, ಹನಿ ನೀರಾವರಿ ಮಾಡಿಸಬೇಕು")
    assert p2.primary_crop.canonical_id == "SORGHUM"
    assert p2.land_area.canonical_acres == Decimal("2.5000")
    assert p2.irrigation_type.canonical_id == "DRIP"
    assert p2.is_ready_for_evaluation is False  # ownership still missing

    # Step 3: Adds Ownership
    p3 = assembler.assemble_turn(p2, "ಖಾತೆ ನನ್ನ ಹೆಸರಲ್ಲಿದೆ, ಸ್ವಂತ ಜಮೀನು")
    assert p3.ownership.ownership_type == OwnershipType.OWNER
    assert p3.is_ready_for_evaluation is True  # Ready!
