"""Safe structured logging with sensitive data redaction.

Non-negotiable requirement (11_SECURITY_AND_PRIVACY.md, Section 9):
Allowed fields: request_id, route, status, duration_ms, model, error_code, turn_id.
Never log: audio bytes, transcripts, prompts, raw LLM outputs, passwords, tokens,
phone numbers, Aadhaar, bank details, or raw profile facts.
"""

import json
import logging
import re
import sys
from datetime import datetime, timezone
from typing import Any, Dict, Set


SENSITIVE_KEYS: Set[str] = {
    "password",
    "token",
    "access_token",
    "refresh_token",
    "secret",
    "authorization",
    "audio",
    "audio_bytes",
    "transcript",
    "transcript_text",
    "user_text",
    "prompt",
    "raw_llm_output",
    "phone",
    "phone_number",
    "aadhaar",
    "bank",
    "account_number",
    "profile_data",
}

PHONE_REGEX = re.compile(r"(\+91[\-\s]?)?[6-9]\d{9}")
TOKEN_REGEX = re.compile(r"Bearer\s+[A-Za-z0-9\-\._~\+\/]+=*", re.IGNORECASE)
PASSWORD_REGEX = re.compile(r"(password|secret|token|pass|pin)\s*[:=\s]\s*([^\s,]+)", re.IGNORECASE)


def redact_sensitive_value(key: str, value: Any) -> Any:
    """Redact values associated with sensitive keys or matching sensitive patterns."""
    key_lower = str(key).lower()
    for sensitive_key in SENSITIVE_KEYS:
        if sensitive_key in key_lower:
            return "[REDACTED]"

    if isinstance(value, str):
        # Scrub Bearer tokens
        scrubbed = TOKEN_REGEX.sub("Bearer [REDACTED]", value)
        # Scrub phone numbers
        scrubbed = PHONE_REGEX.sub("[PHONE_REDACTED]", scrubbed)
        # Scrub password/secret values in free-form messages
        scrubbed = PASSWORD_REGEX.sub(r"\1 [REDACTED]", scrubbed)
        return scrubbed
    elif isinstance(value, dict):
        return {k: redact_sensitive_value(k, v) for k, v in value.items()}
    elif isinstance(value, (list, tuple)):
        return [redact_sensitive_value(key, v) for v in value]
    return value


class SafeJSONFormatter(logging.Formatter):
    """Formats log records as structured JSON with safe field redaction."""

    def format(self, record: logging.LogRecord) -> str:
        log_payload: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": redact_sensitive_value("message", record.getMessage()),
        }

        # Include standard contextual attributes if attached to record
        for attr in ["request_id", "route", "method", "status_code", "duration_ms", "model", "error_code", "turn_id"]:
            if hasattr(record, attr):
                log_payload[attr] = getattr(record, attr)

        # Include extra dictionary if provided, with redaction
        if hasattr(record, "extra_data") and isinstance(record.extra_data, dict):
            for k, v in record.extra_data.items():
                log_payload[k] = redact_sensitive_value(k, v)

        if record.exc_info and not record.exc_text:
            # Format exception safely without disclosing sensitive stack variables
            record.exc_text = self.formatException(record.exc_info)

        if record.exc_text:
            log_payload["exception"] = record.exc_text

        return json.dumps(log_payload, ensure_ascii=False)


def setup_logging(level: str = "INFO", log_format: str = "json") -> logging.Logger:
    """Configure root logger with safe structured formatter."""
    root_logger = logging.getLogger()
    root_logger.setLevel(level.upper())

    # Clear existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    stream_handler = logging.StreamHandler(sys.stdout)
    if log_format.lower() == "json":
        stream_handler.setFormatter(SafeJSONFormatter())
    else:
        text_format = "%(asctime)s [%(levelname)s] [%(name)s] %(message)s"
        stream_handler.setFormatter(logging.Formatter(text_format))

    root_logger.addHandler(stream_handler)

    # Silence noisy loggers
    logging.getLogger("uvicorn.access").handlers = []
    logging.getLogger("uvicorn.access").propagate = False
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)

    return root_logger
