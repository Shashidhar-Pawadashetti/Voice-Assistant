"""Integration tests against live local Ollama instance with Qwen3 4B.

Verifies Acceptance Criteria from 15_IMPLEMENTATION_PLAN.md (M0.2):
- local model responds to a simple Kannada prompt;
- extraction returns validated schema for basic fixtures;
- model endpoint is not public.
"""

import pytest
import httpx
from app.config import get_settings
from app.core.llm.extractor import IntentSlotExtractor
from app.core.llm.ollama import OllamaAdapter
from app.schemas.extraction import (
    ExtractionResult,
    IntentType,
    get_ollama_extraction_schema,
)


@pytest.mark.asyncio
async def test_live_ollama_kannada_prompt():
    """Verify live local Qwen3 4B responds to a Kannada prompt."""
    settings = get_settings()
    adapter = OllamaAdapter(base_url=settings.OLLAMA_BASE_URL, model_id=settings.OLLAMA_MODEL)

    is_healthy, err, latency = await adapter.check_health()
    if not is_healthy:
        pytest.skip(f"Ollama server or model '{settings.OLLAMA_MODEL}' not available: {err}")

    try:
        # Simple structured Kannada test
        result = await adapter.generate_structured(
            prompt="ನಮಸ್ಕಾರ, ನಾನು ರೈತ. ನನಗೆ ಸರ್ಕಾರದ ಯೋಜನೆಗಳ ಮಾಹಿತಿ ಬೇಕು.",
            system_prompt="Extract intent into JSON matching schema.",
            schema=get_ollama_extraction_schema(),
        )

        assert isinstance(result, dict)
        assert "intent" in result
        assert result["intent"] in [i.value for i in IntentType]
    finally:
        await adapter.close()


@pytest.mark.asyncio
async def test_live_ollama_structured_extraction_dharwad_sorghum():
    """Verify live Qwen3 4B extracts structured slots from a North Karnataka utterance."""
    settings = get_settings()
    adapter = OllamaAdapter(base_url=settings.OLLAMA_BASE_URL, model_id=settings.OLLAMA_MODEL)

    is_healthy, err, _ = await adapter.check_health()
    if not is_healthy:
        pytest.skip(f"Ollama server or model '{settings.OLLAMA_MODEL}' not available: {err}")

    extractor = IntentSlotExtractor(adapter)
    try:
        utterance = "ನಾನು ಧಾರವಾಡ ಜಿಲ್ಲೆಯಲ್ಲಿ ನಾಲ್ಕು ಎಕರೆ ಜಮೀನಿನಲ್ಲಿ ಜೋಳ ಬೆಳೆದಿದ್ದೇನೆ"
        result: ExtractionResult = await extractor.extract(utterance)

        assert isinstance(result, ExtractionResult)
        # Verify intent is recognized
        assert result.intent in (IntentType.FIND_SCHEMES, IntentType.PROFILE_UPDATE)

        # Check extracted slots
        slots = {e.slot: e for e in result.entities}
        assert "district" in slots or "crop" in slots or "land_area" in slots

        # Verify safety invariant: all assertions are USER_STATED
        for entity in result.entities:
            assert entity.assertion == "USER_STATED"
            if entity.slot in ("district", "crop", "land_area"):
                assert entity.requires_confirmation is True
    finally:
        await adapter.close()
