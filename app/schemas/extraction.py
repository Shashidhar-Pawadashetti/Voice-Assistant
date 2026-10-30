"""NLU Extraction schemas conforming to 02_PRODUCT_REQUIREMENTS.md and 05_VOICE_AI_PIPELINE.md."""

from enum import Enum
from typing import Any, List, Optional
from pydantic import BaseModel, Field, ConfigDict


class IntentType(str, Enum):
    """Initial NLU Intent taxonomy (02_PRODUCT_REQUIREMENTS.md, Section 2)."""

    GREETING = "GREETING"
    HELP = "HELP"
    FIND_SCHEMES = "FIND_SCHEMES"
    INCOME_SUPPORT = "INCOME_SUPPORT"
    CROP_INSURANCE = "CROP_INSURANCE"
    MICRO_IRRIGATION = "MICRO_IRRIGATION"
    AGRICULTURAL_EQUIPMENT = "AGRICULTURAL_EQUIPMENT"
    SOIL_IMPROVEMENT = "SOIL_IMPROVEMENT"
    PROFILE_UPDATE = "PROFILE_UPDATE"
    CORRECT_PREVIOUS_ANSWER = "CORRECT_PREVIOUS_ANSWER"
    REPEAT_LAST_RESPONSE = "REPEAT_LAST_RESPONSE"
    EXPLAIN_SCHEME = "EXPLAIN_SCHEME"
    APPLICATION_STEPS = "APPLICATION_STEPS"
    UNKNOWN = "UNKNOWN"


class ExtractedEntity(BaseModel):
    """Individual agricultural entity/slot extracted from farmer utterance."""

    model_config = ConfigDict(extra="ignore")

    slot: str = Field(
        description="Canonical slot key: district, crop, land_area, season, irrigation_type, land_ownership, etc."
    )
    raw_value: Optional[str] = Field(
        default=None,
        description="Exact spoken/written phrase in Kannada or code-mixed language",
    )
    canonical_value: Any = Field(
        description="Normalized value, canonical entity ID, or structured representation",
    )
    value_type: str = Field(
        default="string",
        description="Type descriptor: string, number, boolean",
    )
    assertion: str = Field(
        default="USER_STATED",
        description="Provenance of the assertion: USER_STATED, USER_CONFIRMED",
    )
    requires_confirmation: bool = Field(
        default=True,
        description="Whether critical slot requires verbal confirmation before rule evaluation",
    )


class ExtractionResult(BaseModel):
    """Schema-constrained NLU extraction output.

    Non-negotiable requirement (05_VOICE_AI_PIPELINE.md, Section 5):
    The LLM extracts candidate entities and intents into typed facts only.
    It never decides scheme eligibility or sets verified=true.
    """

    model_config = ConfigDict(extra="ignore")

    intent: IntentType = Field(
        default=IntentType.UNKNOWN,
        description="Classified user intent",
    )
    entities: List[ExtractedEntity] = Field(
        default_factory=list,
        description="List of extracted agricultural slots",
    )
    correction_target: Optional[str] = Field(
        default=None,
        description="Target slot key if the utterance is explicitly correcting a previous answer",
    )
    unresolved_phrases: List[str] = Field(
        default_factory=list,
        description="Spoken phrases that could not be mapped to any known slot",
    )
    assistant_language: str = Field(
        default="kn",
        description="Identified dialogue language code (default 'kn')",
    )


class ExtractionRequest(BaseModel):
    """Request model for testing/executing text-based extraction."""

    text: str = Field(description="Farmer input text or ASR transcript in Kannada/code-mixed")
    language: str = Field(default="kn", description="Expected language code")
    context_slots: Optional[List[ExtractedEntity]] = Field(
        default=None,
        description="Active slots from conversation memory to assist disambiguation/corrections",
    )


def get_ollama_extraction_schema() -> dict:
    """Return an inlined JSON Schema without $defs or $ref, compatible with Ollama's grammar engine."""
    return {
        "type": "object",
        "properties": {
            "intent": {
                "type": "string",
                "enum": [i.value for i in IntentType],
            },
            "entities": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "slot": {"type": "string"},
                        "raw_value": {"type": "string"},
                        "canonical_value": {},
                        "value_type": {"type": "string"},
                        "assertion": {"type": "string"},
                        "requires_confirmation": {"type": "boolean"},
                    },
                    "required": ["slot", "canonical_value"],
                },
            },
            "correction_target": {"type": "string"},
            "unresolved_phrases": {
                "type": "array",
                "items": {"type": "string"},
            },
            "assistant_language": {"type": "string"},
        },
        "required": ["intent", "entities"],
    }

