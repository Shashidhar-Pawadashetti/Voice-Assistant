"""Integration tests for NLU extraction API endpoint."""

import pytest
import httpx
from unittest.mock import AsyncMock, patch
from app.api.v1.extraction import get_extractor
from app.core.llm.extractor import IntentSlotExtractor
from app.main import app
from app.schemas.extraction import ExtractedEntity, ExtractionResult, IntentType
from tests.conftest import MockLanguageModel


@pytest.mark.asyncio
async def test_api_extract_endpoint(client: httpx.AsyncClient):
    """Verify POST /api/v1/nlu/extract endpoint."""
    mock_response = {
        "intent": "MICRO_IRRIGATION",
        "entities": [
            {
                "slot": "irrigation_type",
                "raw_value": "drip",
                "canonical_value": "DRIP",
                "value_type": "string",
                "assertion": "USER_STATED",
                "requires_confirmation": True,
            }
        ],
        "correction_target": None,
        "unresolved_phrases": [],
        "assistant_language": "kn",
    }

    with patch(
        "app.core.llm.ollama.OllamaAdapter.generate_structured",
        new_callable=AsyncMock,
        return_value=mock_response,
    ):
        response = await client.post(
            "/api/v1/nlu/extract",
            json={
                "text": "ನನಗೆ drip irrigation ಸಬ್ಸಿಡಿ ಬೇಕು",
                "language": "kn",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["intent"] == "MICRO_IRRIGATION"
        assert len(data["entities"]) == 1
        assert data["entities"][0]["slot"] == "irrigation_type"
        assert data["entities"][0]["canonical_value"] == "DRIP"


@pytest.mark.asyncio
async def test_api_extract_validation_error(client: httpx.AsyncClient):
    """Verify that invalid payload to /api/v1/nlu/extract returns 422 standard error envelope."""
    response = await client.post(
        "/api/v1/nlu/extract",
        json={"wrong_field": "invalid"},
    )
    assert response.status_code == 422
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert data["error"]["retryable"] is False
