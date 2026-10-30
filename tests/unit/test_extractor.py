"""Unit tests for IntentSlotExtractor adhering to M0.2 acceptance criteria."""

import pytest
from app.core.exceptions import LLMSchemaValidationError
from app.core.llm.extractor import IntentSlotExtractor
from app.schemas.extraction import ExtractedEntity, ExtractionResult, IntentType
from tests.conftest import MockLanguageModel


@pytest.mark.asyncio
async def test_extractor_successful_parsing():
    """Verify standard intent and slot extraction from user utterance."""
    mock_llm = MockLanguageModel(
        default_response={
            "intent": "FIND_SCHEMES",
            "entities": [
                {
                    "slot": "district",
                    "raw_value": "ಧಾರವಾಡ",
                    "canonical_value": "DHARWAD",
                    "value_type": "string",
                    "assertion": "USER_STATED",
                    "requires_confirmation": True,
                },
                {
                    "slot": "land_area",
                    "raw_value": "ನಾಲ್ಕು ಎಕರೆ",
                    "canonical_value": 4.0,
                    "value_type": "number",
                    "assertion": "USER_STATED",
                    "requires_confirmation": True,
                },
            ],
            "correction_target": None,
            "unresolved_phrases": [],
            "assistant_language": "kn",
        }
    )

    extractor = IntentSlotExtractor(mock_llm)
    result = await extractor.extract("ನಾನು ಧಾರವಾಡದವನು, ನಾಲ್ಕು ಎಕರೆ ಜಮೀನಿದೆ")

    assert isinstance(result, ExtractionResult)
    assert result.intent == IntentType.FIND_SCHEMES
    assert len(result.entities) == 2
    assert result.entities[0].slot == "district"
    assert result.entities[0].canonical_value == "DHARWAD"
    assert result.entities[1].slot == "land_area"
    assert result.entities[1].canonical_value == 4.0


@pytest.mark.asyncio
async def test_extractor_enforces_safety_invariants():
    """Verify that provenance cannot be fabricated as official and critical slots require confirmation."""
    mock_llm = MockLanguageModel(
        default_response={
            "intent": "FIND_SCHEMES",
            "entities": [
                {
                    "slot": "crop",
                    "raw_value": "ಜೋಳ",
                    "canonical_value": "SORGHUM",
                    "value_type": "string",
                    "assertion": "OFFICIAL_SOURCE",  # Illegal claim by LLM
                    "requires_confirmation": False,    # Critical slot attempted unconfirmed
                }
            ],
            "correction_target": None,
            "unresolved_phrases": [],
            "assistant_language": "kn",
        }
    )

    extractor = IntentSlotExtractor(mock_llm)
    result = await extractor.extract("ಜೋಳ")

    entity = result.entities[0]
    # Invariant: LLM cannot declare official verification
    assert entity.assertion == "USER_STATED"
    # Invariant: Critical slots must require confirmation
    assert entity.requires_confirmation is True


@pytest.mark.asyncio
async def test_extractor_bounded_retry_on_schema_error():
    """Verify that extractor retries once when schema validation fails initially, then succeeds."""
    invalid_response = {
        "intent": "INVALID_UNKNOWN_INTENT_XYZ",  # Fails IntentType enum validation
        "entities": "not-a-list",
    }
    valid_response = {
        "intent": "GREETING",
        "entities": [],
        "correction_target": None,
        "unresolved_phrases": [],
        "assistant_language": "kn",
    }

    mock_llm = MockLanguageModel(responses_sequence=[invalid_response, valid_response])
    extractor = IntentSlotExtractor(mock_llm)

    result = await extractor.extract("ನಮಸ್ಕಾರ", max_validation_retries=1)

    assert mock_llm.call_count == 2
    assert result.intent == IntentType.GREETING


@pytest.mark.asyncio
async def test_extractor_fails_after_retries_exhausted():
    """Verify LLMSchemaValidationError raised when retry limit reached without valid output."""
    invalid_response = {"intent": "INVALID_INTENT", "entities": "bad"}
    mock_llm = MockLanguageModel(default_response=invalid_response)
    extractor = IntentSlotExtractor(mock_llm)

    with pytest.raises(LLMSchemaValidationError):
        await extractor.extract("ಟೆಸ್ಟ್", max_validation_retries=1)

    assert mock_llm.call_count == 2


@pytest.mark.asyncio
async def test_extractor_correction_handling():
    """Verify correction intent and target extraction."""
    mock_llm = MockLanguageModel(
        default_response={
            "intent": "CORRECT_PREVIOUS_ANSWER",
            "entities": [
                {
                    "slot": "land_area",
                    "raw_value": "ಮೂರೂವರೆ ಎಕರೆ",
                    "canonical_value": 3.5,
                    "value_type": "number",
                    "assertion": "USER_STATED",
                    "requires_confirmation": True,
                }
            ],
            "correction_target": "land_area",
            "unresolved_phrases": [],
            "assistant_language": "kn",
        }
    )

    extractor = IntentSlotExtractor(mock_llm)
    existing_context = [
        ExtractedEntity(
            slot="land_area",
            raw_value="4 ಎಕರೆ",
            canonical_value=4.0,
            value_type="number",
            assertion="USER_STATED",
        )
    ]

    result = await extractor.extract("ಇಲ್ಲ, ಮೂರೂವರೆ ಎಕರೆ", context_slots=existing_context)

    assert result.intent == IntentType.CORRECT_PREVIOUS_ANSWER
    assert result.correction_target == "land_area"
    assert result.entities[0].canonical_value == 3.5


@pytest.mark.asyncio
async def test_extractor_with_kannada_fixtures(kannada_fixtures):
    """Verify that all Kannada fixtures produce schema-conforming ExtractionResults."""
    for fixture in kannada_fixtures:
        mock_response = {
            "intent": fixture["expected_intent"],
            "entities": fixture.get("expected_entities", []),
            "correction_target": fixture.get("expected_correction_target"),
            "unresolved_phrases": [],
            "assistant_language": "kn",
        }
        mock_llm = MockLanguageModel(default_response=mock_response)
        extractor = IntentSlotExtractor(mock_llm)

        result = await extractor.extract(fixture["text"])
        assert isinstance(result, ExtractionResult)
        assert result.intent.value == fixture["expected_intent"]
