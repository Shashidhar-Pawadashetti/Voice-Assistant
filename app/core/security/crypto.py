"""Cryptographic utilities for phone number normalization, blind indexing, and encryption."""

import base64
import hashlib
import hmac
import os
import re
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes

PHONE_REGEX = re.compile(r"^(?:\+91|91|0)?([6-9]\d{9})$")


def normalize_phone_number(raw_phone: str) -> str:
    """Normalize Indian mobile phone number into canonical E.164 (+91XXXXXXXXXX) format.

    Validates:
    - 10 digits starting with 6, 7, 8, or 9
    - Optional prefixes: +91, 91, 0
    - Strips all whitespace, hyphens, and parentheses
    """
    if not raw_phone:
        raise ValueError("Phone number cannot be empty")

    cleaned = re.sub(r"[\s\-\(\)\.]", "", raw_phone)
    match = PHONE_REGEX.match(cleaned)
    if not match:
        raise ValueError(f"Invalid Indian mobile phone number format: '{raw_phone}'")

    ten_digit = match.group(1)
    return f"+91{ten_digit}"


def _derive_key(secret_key: str, salt: bytes, length: int = 32) -> bytes:
    """Derive a fixed-length key from an application secret using HKDF-SHA256."""
    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=length,
        salt=salt,
        info=b"krishi-mitra-field-encryption",
    )
    return hkdf.derive(secret_key.encode("utf-8"))


def compute_phone_hash(phone_number: str, secret_key: str) -> str:
    """Compute an HMAC-SHA256 blind index for exact match database lookups.

    This permits indexing and unique lookups on phone numbers without storing
    unencrypted personal phone numbers in the database.
    """
    normalized = normalize_phone_number(phone_number)
    key = _derive_key(secret_key, salt=b"krishi-mitra-phone-index-salt")
    h = hmac.new(key, normalized.encode("utf-8"), hashlib.sha256)
    return h.hexdigest()


def encrypt_phone_number(phone_number: str, secret_key: str) -> str:
    """Encrypt normalized phone number using AES-256-GCM authenticated encryption.

    Output format: base64(nonce [12 bytes] + ciphertext [variable] + tag [16 bytes]).
    """
    normalized = normalize_phone_number(phone_number)
    key = _derive_key(secret_key, salt=b"krishi-mitra-phone-encryption-salt")
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, normalized.encode("utf-8"), associated_data=b"phone_encryption")
    combined = nonce + ciphertext
    return base64.b64encode(combined).decode("ascii")


def decrypt_phone_number(encrypted_data: str, secret_key: str) -> str:
    """Decrypt an AES-256-GCM encrypted phone number."""
    key = _derive_key(secret_key, salt=b"krishi-mitra-phone-encryption-salt")
    aesgcm = AESGCM(key)
    raw_combined = base64.b64decode(encrypted_data.encode("ascii"))
    if len(raw_combined) < 28:
        raise ValueError("Invalid encrypted data length")
    nonce = raw_combined[:12]
    ciphertext = raw_combined[12:]
    decrypted_bytes = aesgcm.decrypt(nonce, ciphertext, associated_data=b"phone_encryption")
    return decrypted_bytes.decode("utf-8")
