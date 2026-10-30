"""Unit tests for Karnataka geographic normalization and taluk-district parentage validation."""

import pytest

from app.core.normalization.location import (
    get_taluks_for_district,
    normalize_district,
    normalize_taluk,
    validate_taluk_in_district,
)


def test_normalize_districts_across_regions():
    # North Karnataka
    dharwad = normalize_district("ನಾನು ಧಾರವಾಡ ಜಿಲ್ಲೆಯವನು")
    assert dharwad is not None
    assert dharwad.district_id == "DHARWAD"

    belagavi = normalize_district("ಬೆಳಗಾವಿ ಜಿಲ್ಲೆ ಅಥಣಿ")
    assert belagavi is not None
    assert belagavi.district_id == "BELAGAVI"

    # Historic alias: Belgaum
    belgaum = normalize_district("Farmer from Belgaum district")
    assert belgaum is not None
    assert belgaum.district_id == "BELAGAVI"

    # Kalyana Karnataka
    kalaburagi = normalize_district("ಕಲಬುರಗಿ ತಾಲೂಕು")
    assert kalaburagi is not None
    assert kalaburagi.district_id == "KALABURAGI"

    # Historic alias: Gulbarga
    gulbarga = normalize_district("Gulbarga region farmers")
    assert gulbarga is not None
    assert gulbarga.district_id == "KALABURAGI"

    # Southern Karnataka
    mandya = normalize_district("ಮಂಡ್ಯ ಜಿಲ್ಲೆಯಲ್ಲಿ ಕಬ್ಬು")
    assert mandya is not None
    assert mandya.district_id == "MANDYA"

    mysuru = normalize_district("ಮೈಸೂರು ತಾಲೂಕು")
    assert mysuru is not None
    assert mysuru.district_id == "MYSURU"

    # Historic alias: Mysore
    mysore = normalize_district("mysore district")
    assert mysore is not None
    assert mysore.district_id == "MYSURU"

    # Historic alias: Bijapur
    bijapur = normalize_district("bijapur district horticulture")
    assert bijapur is not None
    assert bijapur.district_id == "VIJAYAPURA"


def test_normalize_taluk_and_parentage():
    # Athani belongs to Belagavi
    athani = normalize_taluk("ಅಥಣಿ ತಾಲೂಕು")
    assert athani is not None
    assert athani.taluk_id == "ATHANI"
    assert athani.parent_district_id == "BELAGAVI"

    # Hubballi belongs to Dharwad
    hubli = normalize_taluk("ಹುಬ್ಬಳ್ಳಿ ನಗರ")
    assert hubli is not None
    assert hubli.taluk_id == "HUBLI_URBAN"
    assert hubli.parent_district_id == "DHARWAD"

    # Sindagi belongs to Vijayapura
    sindagi = normalize_taluk("ಸಿಂದಗಿ ತಾಲೂಕು")
    assert sindagi is not None
    assert sindagi.taluk_id == "SINDAGI"
    assert sindagi.parent_district_id == "VIJAYAPURA"


def test_validate_taluk_in_district_correctness():
    # Valid parentage
    assert validate_taluk_in_district("HUBLI_URBAN", "DHARWAD") is True
    assert validate_taluk_in_district("ATHANI", "BELAGAVI") is True
    assert validate_taluk_in_district("MADDUR", "MANDYA") is True
    assert validate_taluk_in_district("JEWARGI", "KALABURAGI") is True

    # Invalid cross-district relationships
    assert validate_taluk_in_district("ATHANI", "MANDYA") is False
    assert validate_taluk_in_district("HUBLI_URBAN", "KALABURAGI") is False
    assert validate_taluk_in_district("MADDUR", "BELAGAVI") is False


def test_reject_invented_or_unknown_locations():
    # Non-existent locations must return None
    assert normalize_district("ಕಾಲ್ಪನಿಕ ಜಿಲ್ಲೆ") is None
    assert normalize_district("Wonderland district") is None
    assert normalize_taluk("ಅಜ್ಞಾತ ಊರು") is None
    assert validate_taluk_in_district("FICTIONAL_TALUK", "DHARWAD") is False


def test_get_taluks_for_district():
    taluks = get_taluks_for_district("DHARWAD")
    assert len(taluks) >= 5
    taluk_ids = [t.taluk_id for t in taluks]
    assert "DHARWAD" in taluk_ids
    assert "HUBLI_URBAN" in taluk_ids
    assert "KUNDGOL" in taluk_ids
