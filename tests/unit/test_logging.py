"""Unit tests for safe structured logging and redaction."""

import json
import logging
from app.logging import SafeJSONFormatter, redact_sensitive_value


def test_redact_sensitive_keys():
    """Verify that sensitive keys are replaced with [REDACTED]."""
    test_dict = {
        "password": "super-secret-password",
        "access_token": "eyJhbGciOi...",
        "audio_bytes": b"fake-audio-content",
        "transcript_text": "ನನ್ನ ಹೆಸರು ರಮೇಶ್",
        "farmer_phone": "9876543210",
        "safe_field": "public_value",
    }

    redacted = redact_sensitive_value("context", test_dict)
    assert redacted["password"] == "[REDACTED]"
    assert redacted["access_token"] == "[REDACTED]"
    assert redacted["audio_bytes"] == "[REDACTED]"
    assert redacted["transcript_text"] == "[REDACTED]"
    assert redacted["farmer_phone"] == "[REDACTED]"
    assert redacted["safe_field"] == "public_value"


def test_redact_phone_and_bearer_in_strings():
    """Verify regex scrubbing of phone numbers and authorization headers."""
    message = "Request with Bearer abc123secretToken received from 9876543210 or +919876543210"
    scrubbed = redact_sensitive_value("message", message)

    assert "Bearer [REDACTED]" in scrubbed
    assert "abc123secretToken" not in scrubbed
    assert "9876543210" not in scrubbed
    assert "[PHONE_REDACTED]" in scrubbed


def test_safe_json_formatter():
    """Verify that log record formats into valid JSON containing expected attributes."""
    formatter = SafeJSONFormatter()
    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="test.py",
        lineno=10,
        msg="Turn processed for user with password secret_pass",
        args=(),
        exc_info=None,
    )
    record.request_id = "req_12345"
    record.duration_ms = 45.2

    output = formatter.format(record)
    parsed = json.loads(output)

    assert parsed["level"] == "INFO"
    assert parsed["logger"] == "test_logger"
    assert parsed["request_id"] == "req_12345"
    assert parsed["duration_ms"] == 45.2
    assert "secret_pass" not in parsed["message"]
    assert "timestamp" in parsed
