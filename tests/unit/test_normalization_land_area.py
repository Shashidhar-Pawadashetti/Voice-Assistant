"""Unit tests for land measurement normalization, colloquial Kannada fractions, and Decimal conversions."""

from decimal import Decimal
import pytest

from app.core.normalization.land_area import (
    LandUnit,
    normalize_land_area,
)


def test_standard_numeric_acres():
    res = normalize_land_area("ನನ್ನ ಬಳಿ 4 ಎಕರೆ ಜಮೀನಿದೆ")
    assert res is not None
    assert res.canonical_acres == Decimal("4.0000")
    assert res.original_unit == LandUnit.ACRE
    assert res.is_ambiguous is False


def test_decimal_acres():
    res = normalize_land_area("2.5 ಎಕರೆ ಜಮೀನು")
    assert res is not None
    assert res.canonical_acres == Decimal("2.5000")
    assert res.canonical_guntas == Decimal("100.00")
    assert res.is_ambiguous is False


def test_kannada_colloquial_fractions():
    # ಒಂದೂವರೆ (1.5)
    res_1_5 = normalize_land_area("ನನಗೆ ಒಂದೂವರೆ ಎಕರೆ ಇದೆ")
    assert res_1_5 is not None
    assert res_1_5.canonical_acres == Decimal("1.5000")

    # ಎರಡೂವರೆ (2.5)
    res_2_5 = normalize_land_area("ಎರಡೂವರೆ ಎಕರೆ")
    assert res_2_5 is not None
    assert res_2_5.canonical_acres == Decimal("2.5000")

    # ಮೂರನ್ನರೆ (3.5)
    res_3_5 = normalize_land_area("ಮೂರನ್ನರೆ ಎಕರೆ ಕೃಷಿ ಭೂಮಿ")
    assert res_3_5 is not None
    assert res_3_5.canonical_acres == Decimal("3.5000")

    # ನಾಲ್ಕೂವರೆ (4.5)
    res_4_5 = normalize_land_area("ನಾಲ್ಕೂವರೆ ಎಕರೆ")
    assert res_4_5 is not None
    assert res_4_5.canonical_acres == Decimal("4.5000")

    # ಅರ್ಧ (0.5)
    res_half = normalize_land_area("ಅರ್ಧ ಎಕರೆ ಜಮೀನು")
    assert res_half is not None
    assert res_half.canonical_acres == Decimal("0.5000")
    assert res_half.canonical_guntas == Decimal("20.00")

    # ಮುಕ್ಕಾಲು (0.75)
    res_three_quarter = normalize_land_area("ಮುಕ್ಕಾಲು ಎಕರೆ")
    assert res_three_quarter is not None
    assert res_three_quarter.canonical_acres == Decimal("0.7500")

    # ಕಾಲು (0.25)
    res_quarter = normalize_land_area("ಕಾಲು ಎಕರೆ")
    assert res_quarter is not None
    assert res_quarter.canonical_acres == Decimal("0.2500")


def test_gunta_conversion():
    # 40 guntas = 1 acre
    res_40 = normalize_land_area("40 ಗುಂಟೆ ಜಮೀನಿದೆ")
    assert res_40 is not None
    assert res_40.canonical_acres == Decimal("1.0000")
    assert res_40.canonical_guntas == Decimal("40.00")

    # 20 guntas = 0.5 acre
    res_20 = normalize_land_area("ಇಪ್ಪತ್ತು ಗುಂಟೆ")
    assert res_20 is not None
    assert res_20.canonical_acres == Decimal("0.5000")


def test_hectare_conversion():
    # 1 hectare = 2.4711 acres
    res = normalize_land_area("1 ಹೆಕ್ಟೇರ್ ಜಮೀನು")
    assert res is not None
    assert res.original_unit == LandUnit.HECTARE
    assert Decimal("2.4710") <= res.canonical_acres <= Decimal("2.4712")


def test_composite_acre_and_gunta():
    # 2 ಎಕರೆ 20 ಗುಂಟೆ = 2 + 20/40 = 2.5 acres
    res = normalize_land_area("ನನ್ನ ಬಳಿ 2 ಎಕರೆ 20 ಗುಂಟೆ ಜಮೀನಿದೆ")
    assert res is not None
    assert res.canonical_acres == Decimal("2.5000")
    assert res.canonical_guntas == Decimal("100.00")


def test_ambiguous_land_area_requires_clarification():
    # Farmer gives bare number without unit ("ನನ್ನ ಹತ್ತಿರ 5 ಇದೆ")
    res = normalize_land_area("ನನ್ನ ಹತ್ತಿರ 5 ಇದೆ")
    assert res is not None
    assert res.is_ambiguous is True
    assert "ಎಕರೆ, ಗುಂಟೆ ಅಥವಾ ಹೆಕ್ಟೇರ್" in res.clarification_prompt
