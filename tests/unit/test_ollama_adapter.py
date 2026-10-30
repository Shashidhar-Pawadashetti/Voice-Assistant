"""Unit tests for local Ollama client adapter."""

import json
import pytest
import httpx
from unittest.mock import AsyncMock, patch

from app.core.exceptions import LLMModelError, LLMTimeoutError, LLMUnavailableError
from app.core.llm.ollama import OllamaAdapter


@pytest.mark.asyncio
async def test_ollama_adapter_generate_structured_success():
    """Verify successful generation of structured output adhering to schema."""
    adapter = OllamaAdapter(base_url="http://127.0.0.1:11434", model_id="qwen3:4b")

    mock_response = httpx.Response(
        200,
        json={
            "model": "qwen3:4b",
            "response": '{"intent": "FIND_SCHEMES", "entities": [{"slot": "crop", "raw_value": "ಜೋಳ", "canonical_value": "SORGHUM", "value_type": "string", "assertion": "USER_STATED", "requires_confirmation": true}], "correction_target": null, "unresolved_phrases": [], "assistant_language": "kn"}',
            "done": True,
            "total_duration": 1200000000,
        },
        request=httpx.Request("POST", "http://127.0.0.1:11434/api/generate"),
    )

    with patch.object(adapter._client, "post", new_callable=AsyncMock, return_value=mock_response) as mock_post:
        result = await adapter.generate_structured(
            prompt="ನಾನು ಜೋಳ ಬೆಳೆಯುತ್ತೇನೆ",
            schema={"type": "object"},
        )

        assert mock_post.called
        assert result["intent"] == "FIND_SCHEMES"
        assert len(result["entities"]) == 1
        assert result["entities"][0]["canonical_value"] == "SORGHUM"

    await adapter.close()


@pytest.mark.asyncio
async def test_ollama_adapter_strips_markdown_code_fences():
    """Verify that JSON wrapped in markdown code fences is parsed cleanly."""
    adapter = OllamaAdapter()
    mock_response = httpx.Response(
        200,
        json={
            "response": '```json\n{"intent": "GREETING", "entities": []}\n```',
        },
        request=httpx.Request("POST", "http://127.0.0.1:11434/api/generate"),
    )

    with patch.object(adapter._client, "post", new_callable=AsyncMock, return_value=mock_response):
        result = await adapter.generate_structured(prompt="ಹಲೋ")
        assert result["intent"] == "GREETING"

    await adapter.close()


@pytest.mark.asyncio
async def test_ollama_adapter_timeout_raises_llm_timeout_error():
    """Verify timeout exception mapping."""
    adapter = OllamaAdapter(timeout=0.1, max_retries=0)

    with patch.object(adapter._client, "post", side_effect=httpx.ReadTimeout("Timeout")):
        with pytest.raises(LLMTimeoutError):
            await adapter.generate_structured(prompt="test")

    await adapter.close()


@pytest.mark.asyncio
async def test_ollama_adapter_connect_error_raises_llm_unavailable():
    """Verify connection failure mapping."""
    adapter = OllamaAdapter(max_retries=0)

    with patch.object(adapter._client, "post", side_effect=httpx.ConnectError("Connection refused")):
        with pytest.raises(LLMUnavailableError):
            await adapter.generate_structured(prompt="test")

    await adapter.close()


@pytest.mark.asyncio
async def test_ollama_adapter_malformed_json_raises_llm_model_error():
    """Verify malformed JSON handling."""
    adapter = OllamaAdapter()
    mock_response = httpx.Response(
        200,
        json={"response": "Not a valid JSON {"},
        request=httpx.Request("POST", "http://127.0.0.1:11434/api/generate"),
    )

    with patch.object(adapter._client, "post", new_callable=AsyncMock, return_value=mock_response):
        with pytest.raises(LLMModelError, match="malformed JSON"):
            await adapter.generate_structured(prompt="test")

    await adapter.close()


@pytest.mark.asyncio
async def test_ollama_health_check():
    """Verify Ollama health check when model is found and when missing."""
    adapter = OllamaAdapter(model_id="qwen3:4b")

    # 1. Model present
    mock_tags_ok = httpx.Response(
        200,
        json={"models": [{"name": "qwen3:4b"}, {"name": "other-model"}]},
    )
    with patch.object(adapter._client, "get", new_callable=AsyncMock, return_value=mock_tags_ok):
        is_healthy, err, latency = await adapter.check_health()
        assert is_healthy is True
        assert err is None
        assert latency >= 0.0

    # 2. Model missing
    mock_tags_missing = httpx.Response(
        200,
        json={"models": [{"name": "llama3:8b"}]},
    )
    with patch.object(adapter._client, "get", new_callable=AsyncMock, return_value=mock_tags_missing):
        is_healthy, err, latency = await adapter.check_health()
        assert is_healthy is False
        assert "not loaded" in err

    await adapter.close()
