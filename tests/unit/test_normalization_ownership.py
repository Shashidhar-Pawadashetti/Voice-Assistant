"""Unit tests for land ownership classification, legal assertion boundaries, and provenance."""

import pytest

from app.core.normalization.ownership import (
    NormalizedOwnership,
    OwnershipType,
    ProvenanceAssertion,
    normalize_ownership,
)


def test_explicit_owner():
    res = normalize_ownership("ನನ್ನ ಸ್ವಂತ ಜಮೀನಿನಲ್ಲಿ ಬೆಳೆಯುತ್ತಿದ್ದೇನೆ")
    assert res.ownership_type == OwnershipType.OWNER
    assert res.requires_confirmation is True
    assert res.is_legal_ownership_proven is False


def test_co_owner():
    res = normalize_ownership("ಇದು ಅಣ್ಣ ತಮ್ಮಂದಿರ ಜಂಟಿ ಖಾತೆ ಜಮೀನು")
    assert res.ownership_type == OwnershipType.CO_OWNER
    assert res.requires_confirmation is True


def test_leased_land():
    res = normalize_ownership("ನಾನು ಗುತ್ತಿಗೆಗೆ ತಗೊಂಡಿದ್ದೇನೆ")
    assert res.ownership_type == OwnershipType.LEASED
    assert res.requires_confirmation is True


def test_tenant_cultivator_does_not_infer_owner():
    # Invariant: cultivation ('ಸಾಗುವಳಿ') must NOT infer legal ownership (OWNER)
    res = normalize_ownership("ನಾನು ಎರಡು ಎಕರೆ ಸಾಗುವಳಿ ಮಾಡುತ್ತಿದ್ದೇನೆ")
    assert res.ownership_type == OwnershipType.TENANT_OR_CULTIVATOR
    assert res.ownership_type != OwnershipType.OWNER
    assert res.is_legal_ownership_proven is False


def test_unknown_ownership():
    res = normalize_ownership("ಕೇವಲ ಬೆಳೆ ಮಾಹಿತಿ ತಿಳಿಸಿ")
    assert res.ownership_type == OwnershipType.UNKNOWN
    assert res.requires_confirmation is True


def test_provenance_preservation():
    res = normalize_ownership("ಖಾತೆದಾರ ನಾನು", assertion=ProvenanceAssertion.USER_CONFIRMED)
    assert res.assertion == ProvenanceAssertion.USER_CONFIRMED
    assert res.ownership_type == OwnershipType.OWNER
