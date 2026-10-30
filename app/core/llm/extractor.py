"""Intent and slot extraction engine orchestrating LLM inference and Pydantic validation."""

import asyncio
import logging
from typing import Any, Dict, List, Optional
from pydantic import ValidationError

from app.core.exceptions import LLMSchemaValidationError
from app.core.llm.interface import LanguageModel
from app.core.llm.prompts import EXTRACTION_SYSTEM_PROMPT, build_extraction_prompt
from app.schemas.extraction import (
    ExtractedEntity,
    ExtractionResult,
    IntentType,
    get_ollama_extraction_schema,
)


logger = logging.getLogger(__name__)

CRITICAL_SLOTS = {"district", "crop", "land_area", "season", "land_ownership"}


class IntentSlotExtractor:
    """Extracts typed agricultural facts and intent using schema-constrained LLM generation."""

    def __init__(self, llm_adapter: Optional[LanguageModel] = None, llm: Optional[LanguageModel] = None):
        adapter = llm_adapter or llm
        if adapter is None:
            raise ValueError("An LLM adapter instance must be provided")
        self.llm = adapter
        # Use inlined JSON schema optimized for Ollama's grammar engine
        self.schema: Dict[str, Any] = get_ollama_extraction_schema()

    async def extract(
        self,
        utterance: str,
        *,
        context_slots: Optional[List[ExtractedEntity]] = None,
        max_validation_retries: int = 1,
    ) -> ExtractionResult:
        """Extract intent and entities from utterance with strict Pydantic validation.

        Args:
            utterance: Spoken or text Kannada/code-mixed input.
            context_slots: Existing slots from conversation context.
            max_validation_retries: Number of retry attempts if schema validation fails.

        Returns:
            Validated ExtractionResult.

        Raises:
            LLMSchemaValidationError: If output fails Pydantic schema validation after retries.
            LLMTimeoutError: If inference times out.
            LLMUnavailableError: If model service is down.
        """
        context_summary = self._format_context_summary(context_slots) if context_slots else None
        prompt = build_extraction_prompt(utterance, context_summary)

        attempts = 0
        last_error = None

        while attempts <= max_validation_retries:
            attempts += 1
            raw_data = await self.llm.generate_structured(
                prompt=prompt,
                system_prompt=EXTRACTION_SYSTEM_PROMPT,
                schema=self.schema,
            )

            try:
                # Offload Pydantic model validation outside the asyncio event loop
                result: ExtractionResult = await asyncio.to_thread(
                    ExtractionResult.model_validate, raw_data
                )

                # Post-validation safety enforcement (05_VOICE_AI_PIPELINE.md & 17_ANTIGRAVITY_BUILD_INSTRUCTIONS.md)
                self._enforce_safety_invariants(result)
                return result

            except ValidationError as err:
                logger.warning(
                    "Pydantic validation failed for extraction (attempt %d/%d): %s",
                    attempts,
                    max_validation_retries + 1,
                    err.error_count(),
                )
                last_error = err
                # If retry budget remains, add explicit error hint
                if attempts <= max_validation_retries:
                    prompt += f"\nPrevious attempt had schema errors: {err.errors()[0].get('msg', 'invalid format')}. Please fix."

        raise LLMSchemaValidationError(
            f"Extraction failed schema validation after {attempts} attempts",
            details={"validation_errors": str(last_error)},
        )

    def _enforce_safety_invariants(self, result: ExtractionResult) -> None:
        """Enforce strict safety rules on validated extraction output.

        - All entities must have provenance USER_STATED or USER_CONFIRMED.
        - Critical slots (district, crop, land_area, season, land_ownership) must require confirmation.
        - No entitlement or eligibility decisions may be injected.
        """
        for entity in result.entities:
            # Force provenance: LLM output can never claim government verification
            if entity.assertion not in ("USER_STATED", "USER_CONFIRMED"):
                entity.assertion = "USER_STATED"

            # Critical slots require confirmation
            if entity.slot in CRITICAL_SLOTS:
                entity.requires_confirmation = True

    @staticmethod
    def _format_context_summary(slots: List[ExtractedEntity]) -> str:
        """Format existing conversation slots as concise trusted context."""
        lines = []
        for s in slots:
            lines.append(f"- {s.slot}: {s.canonical_value} (status: {s.assertion})")
        return "\n".join(lines)


# Alias and helper factory for dependency injection
SchemeExtractor = IntentSlotExtractor


def get_scheme_extractor() -> IntentSlotExtractor:
    """Return default IntentSlotExtractor configured with Ollama adapter."""
    from app.core.llm.ollama import OllamaAdapter

    return IntentSlotExtractor(OllamaAdapter())

