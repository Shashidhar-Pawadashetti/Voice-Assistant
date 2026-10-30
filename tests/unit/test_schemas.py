"""Unit tests for Pydantic schemas and serialization."""

import pytest
from pydantic import ValidationError
from app.schemas.extraction import ExtractedEntity, ExtractionResult, IntentType
from app.schemas.health import DependencyHealth, LivenessResponse, ReadinessResponse
from app.schemas.error import APIErrorResponse, ErrorDetail


def test_extraction_result_json_schema():
    """Verify JSON schema generation for Ollama format parameter."""
    schema = ExtractionResult.model_json_schema()
    assert "properties" in schema
    assert "intent" in schema["properties"]
    assert "entities" in schema["properties"]


def test_extracted_entity_validation():
    """Verify entity model validation and defaults."""
    entity = ExtractedEntity(
        slot="crop",
        raw_value="ರಾಗಿ",
        canonical_value="FINGER_MILLET",
    )
    assert entity.slot == "crop"
    assert entity.canonical_value == "FINGER_MILLET"
    assert entity.value_type == "string"
    assert entity.assertion == "USER_STATED"
    assert entity.requires_confirmation is True


def test_invalid_intent_rejected():
    """Verify that unapproved intents fail validation."""
    with pytest.raises(ValidationError):
        ExtractionResult(intent="UNAPPROVED_RANDOM_INTENT", entities=[])


def test_error_envelope_structure():
    """Verify API error model conforms to 09_API_CONTRACT.md."""
    err = APIErrorResponse(
        error=ErrorDetail(
            code="TEST_CODE",
            message="Test message",
            retryable=True,
            request_id="req_123",
            details={"key": "val"},
        )
    )
    data = err.model_dump()
    assert data["error"]["code"] == "TEST_CODE"
    assert data["error"]["retryable"] is True
    assert data["error"]["request_id"] == "req_123"
