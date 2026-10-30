"""Unit tests for JWT access token creation, validation, expiration, and tampering defenses."""

from datetime import timedelta
import uuid
import pytest
from app.core.exceptions import AuthenticationError
from app.core.security.jwt import (
    create_access_token,
    decode_access_token,
    generate_refresh_token_pair,
)

SECRET = "super_secure_jwt_secret_key_32chars_long!!"


def test_access_token_creation_and_decoding():
    farmer_id = uuid.uuid4()
    token = create_access_token(farmer_id, secret_key=SECRET)

    payload = decode_access_token(token, secret_key=SECRET)
    assert payload["sub"] == str(farmer_id)
    assert payload["type"] == "access"
    assert payload["role"] == "FARMER"
    assert "exp" in payload
    assert "iat" in payload


def test_expired_token_rejected():
    farmer_id = uuid.uuid4()
    # Expired 10 seconds ago
    token = create_access_token(farmer_id, expires_delta=timedelta(seconds=-10), secret_key=SECRET)

    with pytest.raises(AuthenticationError) as exc_info:
        decode_access_token(token, secret_key=SECRET)
    assert "expired" in str(exc_info.value).lower()


def test_tampered_token_signature_rejected():
    farmer_id = uuid.uuid4()
    token = create_access_token(farmer_id, secret_key=SECRET)

    # Tamper with signature
    tampered = token[:-4] + "xxxx"
    with pytest.raises(AuthenticationError):
        decode_access_token(tampered, secret_key=SECRET)


def test_token_with_wrong_secret_rejected():
    farmer_id = uuid.uuid4()
    token = create_access_token(farmer_id, secret_key=SECRET)

    with pytest.raises(AuthenticationError):
        decode_access_token(token, secret_key="wrong_secret_key_that_does_not_match")


def test_generate_refresh_token_pair():
    plain, token_hash = generate_refresh_token_pair()
    assert len(plain) > 30
    assert len(token_hash) == 64  # SHA-256 hex
    assert plain != token_hash
