"""NLU Intent and slot extraction endpoint."""

from fastapi import APIRouter, Depends
from app.core.llm.extractor import IntentSlotExtractor
from app.core.llm.ollama import OllamaAdapter
from app.schemas.extraction import ExtractionRequest, ExtractionResult


router = APIRouter(prefix="/nlu", tags=["NLU"])


def get_extractor() -> IntentSlotExtractor:
    """Dependency provider for IntentSlotExtractor."""
    adapter = OllamaAdapter()
    return IntentSlotExtractor(adapter)


@router.post(
    "/extract",
    response_model=ExtractionResult,
    summary="Extract intent and slots from Kannada/code-mixed text",
    description="Schema-constrained NLU extraction using local Qwen3 4B. Does not make scheme eligibility decisions.",
)
async def extract_intent_and_slots(
    request: ExtractionRequest,
    extractor: IntentSlotExtractor = Depends(get_extractor),
) -> ExtractionResult:
    """Extract agricultural slots and dialogue intent from user utterance."""
    try:
        return await extractor.extract(
            utterance=request.text,
            context_slots=request.context_slots,
        )
    finally:
        if hasattr(extractor.llm, "close"):
            await extractor.llm.close()
