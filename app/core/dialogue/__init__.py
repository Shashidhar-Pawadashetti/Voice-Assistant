"""Dialogue and conversation state management subsystem."""

from app.core.dialogue.confirmation import (
    ConfirmationAnalysis,
    ConfirmationDecision,
    analyze_confirmation,
)
from app.core.dialogue.intent_registry import (
    INTENT_SLOT_REGISTRY,
    IntentSlotRequirement,
    IntentSlotResolver,
)
from app.core.dialogue.prompts import (
    build_confirmation_prompt,
    generate_dialogue_response,
)
from app.core.dialogue.state_machine import (
    PERMITTED_TRANSITIONS,
    DialogueState,
    DialogueStateMachine,
)

__all__ = [
    "ConfirmationAnalysis",
    "ConfirmationDecision",
    "DialogueState",
    "DialogueStateMachine",
    "INTENT_SLOT_REGISTRY",
    "IntentSlotRequirement",
    "IntentSlotResolver",
    "PERMITTED_TRANSITIONS",
    "analyze_confirmation",
    "build_confirmation_prompt",
    "generate_dialogue_response",
]
