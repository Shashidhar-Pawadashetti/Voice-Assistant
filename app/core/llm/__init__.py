"""LLM core package initialization."""

from app.core.llm.interface import LanguageModel
from app.core.llm.ollama import OllamaAdapter
from app.core.llm.prompts import EXTRACTION_SYSTEM_PROMPT, build_extraction_prompt
from app.core.llm.extractor import IntentSlotExtractor

__all__ = [
    "LanguageModel",
    "OllamaAdapter",
    "EXTRACTION_SYSTEM_PROMPT",
    "build_extraction_prompt",
    "IntentSlotExtractor",
]
