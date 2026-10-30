"""Unit tests for Argon2id password hashing, verification, timing mitigation, and strength."""

import pytest
from app.core.security.password import (
    dummy_verify_password,
    hash_password,
    validate_password_strength,
    verify_password,
)


def test_password_hashing_and_verification():
    raw_pwd = "kannada_farmer_password_123"
    hashed = hash_password(raw_pwd)

    # Invariant: Password hash is not plaintext
    assert hashed != raw_pwd
    assert hashed.startswith("$argon2id$")

    # Correct password verifies
    assert verify_password(raw_pwd, hashed) is True

    # Incorrect password fails
    assert verify_password("wrong_password", hashed) is False
    assert verify_password("", hashed) is False
    assert verify_password(raw_pwd, "") is False


def test_unique_salts_for_same_password():
    pwd = "consistent_password_123"
    hash1 = hash_password(pwd)
    hash2 = hash_password(pwd)

    # Argon2id must use distinct cryptographic salt each time
    assert hash1 != hash2
    assert verify_password(pwd, hash1) is True
    assert verify_password(pwd, hash2) is True


def test_dummy_verify_password_does_not_raise():
    # Timing defense helper should execute silently without crashing
    dummy_verify_password("any_unmatched_password")
    dummy_verify_password("")


def test_validate_password_strength():
    # Too short (< 8 chars)
    is_valid, msg = validate_password_strength("short")
    assert is_valid is False
    assert "at least 8" in msg

    # Empty
    is_valid, msg = validate_password_strength("")
    assert is_valid is False

    # Leading/trailing whitespace
    is_valid, msg = validate_password_strength(" validpassword123 ")
    assert is_valid is False
    assert "whitespace" in msg

    # Too long (> 128 chars, DoS defense)
    is_valid, msg = validate_password_strength("a" * 129)
    assert is_valid is False
    assert "exceed 128" in msg

    # Valid farmer password
    is_valid, msg = validate_password_strength("validFarmerPwd!2026")
    assert is_valid is True
    assert msg == ""
