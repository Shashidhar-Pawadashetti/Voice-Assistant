"""Unit tests for phone number normalization, blind index hashing, and AES-256-GCM encryption."""

import pytest
from app.core.security.crypto import (
    compute_phone_hash,
    decrypt_phone_number,
    encrypt_phone_number,
    normalize_phone_number,
)

TEST_SECRET = "test_cryptographic_secret_key_32chars_min!"


def test_normalize_phone_number():
    # Various valid Indian mobile phone formats
    assert normalize_phone_number("9876543210") == "+919876543210"
    assert normalize_phone_number("+91 98765 43210") == "+919876543210"
    assert normalize_phone_number("91-9876543210") == "+919876543210"
    assert normalize_phone_number("09876543210") == "+919876543210"
    assert normalize_phone_number("+91-8123456789") == "+918123456789"

    # Invalid formats
    with pytest.raises(ValueError):
        normalize_phone_number("123456")  # Too short
    with pytest.raises(ValueError):
        normalize_phone_number("5876543210")  # Invalid start digit (not 6, 7, 8, or 9)
    with pytest.raises(ValueError):
        normalize_phone_number("")


def test_blind_index_deterministic():
    phone1 = "+91 98765 43210"
    phone2 = "9876543210"

    hash1 = compute_phone_hash(phone1, TEST_SECRET)
    hash2 = compute_phone_hash(phone2, TEST_SECRET)

    # Invariant: Normalization makes hash identical for identical phone numbers
    assert hash1 == hash2
    assert len(hash1) == 64  # SHA-256 hex digest

    # Different phone numbers yield different hashes
    hash3 = compute_phone_hash("9876543211", TEST_SECRET)
    assert hash1 != hash3


def test_aes_gcm_phone_encryption_and_decryption():
    phone = "9876543210"
    encrypted = encrypt_phone_number(phone, TEST_SECRET)

    # Invariant: Encrypted value is not plaintext
    assert phone not in encrypted
    assert "+91" not in encrypted

    # Decrypt restores canonical normalized phone
    decrypted = decrypt_phone_number(encrypted, TEST_SECRET)
    assert decrypted == "+919876543210"

    # Nonces ensure identical inputs produce distinct ciphertexts
    encrypted2 = encrypt_phone_number(phone, TEST_SECRET)
    assert encrypted != encrypted2
    assert decrypt_phone_number(encrypted2, TEST_SECRET) == "+919876543210"


def test_key_rotation_fallback_support(monkeypatch):
    """Verify that ciphertexts encrypted with an older key can still be decrypted after key rotation."""
    from app.config import get_settings

    old_key = "old_secret_key_rotation_123456789012"
    new_key = "new_active_secret_key_098765432109"

    phone = "9876543210"
    # Encrypted with old key
    encrypted_old = encrypt_phone_number(phone, old_key)

    # Configure active settings with new_key as primary, and old_key in previous list
    settings = get_settings()
    monkeypatch.setattr(settings, "ENCRYPTION_KEY", new_key)
    monkeypatch.setattr(settings, "ENCRYPTION_KEY_PREVIOUS", f"dummy_prev,{old_key}")

    # Decryption without specifying secret_key should automatically fall back through previous keys!
    decrypted = decrypt_phone_number(encrypted_old)
    assert decrypted == "+919876543210"
