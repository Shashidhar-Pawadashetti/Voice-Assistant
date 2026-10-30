"""Deterministic dialogue state machine for Krishi Mitra conversational intelligence.

Conforms to Directive M3.2, 06_DIALOGUE_AND_MEMORY.md Section 2, and 15_IMPLEMENTATION_PLAN.md.
Non-negotiable rule:
State transitions are deterministic application logic governed by an explicit transition graph.
Unrestricted LLM agents cannot directly dictate dialogue state transitions.
"""

from enum import Enum
from typing import Dict, Set
from pydantic import BaseModel, Field

from app.core.exceptions import InvalidStateTransitionError


class DialogueState(str, Enum):
    """Permitted conversational dialogue states."""

    GREETING = "GREETING"
    COLLECTING_SLOTS = "COLLECTING_SLOTS"
    CLARIFYING = "CLARIFYING"
    CONFIRMING = "CONFIRMING"
    EVALUATION_READY = "EVALUATION_READY"
    RESPONDING = "RESPONDING"
    COMPLETED = "COMPLETED"
    PAUSED = "PAUSED"


# Explicit directed transition graph. Any transition not listed is strictly prohibited.
PERMITTED_TRANSITIONS: Dict[DialogueState, Set[DialogueState]] = {
    DialogueState.GREETING: {
        DialogueState.COLLECTING_SLOTS,
        DialogueState.CLARIFYING,
        DialogueState.CONFIRMING,
        DialogueState.RESPONDING,
        DialogueState.PAUSED,
        DialogueState.COMPLETED,
    },
    DialogueState.COLLECTING_SLOTS: {
        DialogueState.COLLECTING_SLOTS,  # Multi-turn slot ingestion
        DialogueState.CLARIFYING,        # Ambiguous input requiring follow-up
        DialogueState.CONFIRMING,        # Critical slot proposed, awaiting confirmation
        DialogueState.EVALUATION_READY,  # All required slots present and valid
        DialogueState.RESPONDING,        # General query or immediate reply
        DialogueState.PAUSED,            # Interruption / session paused
        DialogueState.COMPLETED,         # Finished session
    },
    DialogueState.CLARIFYING: {
        DialogueState.COLLECTING_SLOTS,  # Disambiguated, continuing slot collection
        DialogueState.CLARIFYING,        # Repeated ambiguity
        DialogueState.CONFIRMING,        # Disambiguated value needs confirmation
        DialogueState.EVALUATION_READY,  # Ambiguity resolved and profile complete
        DialogueState.RESPONDING,
        DialogueState.PAUSED,
        DialogueState.COMPLETED,
    },
    DialogueState.CONFIRMING: {
        DialogueState.CONFIRMING,        # Confirming next pending critical slot
        DialogueState.COLLECTING_SLOTS,  # Rejected/corrected, returning to collection
        DialogueState.CLARIFYING,        # Rejection was ambiguous
        DialogueState.EVALUATION_READY,  # All critical slots confirmed
        DialogueState.RESPONDING,
        DialogueState.PAUSED,
        DialogueState.COMPLETED,
    },
    DialogueState.EVALUATION_READY: {
        DialogueState.EVALUATION_READY,  # Self-transition when updating non-blocking facts
        DialogueState.RESPONDING,        # Explaining results or presenting guidance
        DialogueState.COLLECTING_SLOTS,  # Farmer supplies additional crop/area facts
        DialogueState.CONFIRMING,        # Farmer modified a critical fact
        DialogueState.PAUSED,
        DialogueState.COMPLETED,
    },
    DialogueState.RESPONDING: {
        DialogueState.COLLECTING_SLOTS,  # Follow-up question on agricultural facts
        DialogueState.CLARIFYING,
        DialogueState.CONFIRMING,
        DialogueState.EVALUATION_READY,
        DialogueState.RESPONDING,
        DialogueState.PAUSED,
        DialogueState.COMPLETED,
    },
    DialogueState.PAUSED: {
        DialogueState.GREETING,          # Resumed with new greeting
        DialogueState.COLLECTING_SLOTS,  # Resumed at slot collection
        DialogueState.CLARIFYING,        # Resumed at pending clarification
        DialogueState.CONFIRMING,        # Resumed at pending confirmation
        DialogueState.EVALUATION_READY,  # Resumed at ready state
        DialogueState.RESPONDING,
        DialogueState.COMPLETED,
    },
    # COMPLETED is terminal.
    DialogueState.COMPLETED: set(),
}


class DialogueStateMachine:
    """Manages deterministic validation and execution of conversation state transitions."""

    @staticmethod
    def can_transition(current_state: DialogueState, next_state: DialogueState) -> bool:
        """Check if transition from current_state to next_state is valid."""
        if current_state == DialogueState.COMPLETED:
            return False
        if current_state == next_state:
            return True
        allowed = PERMITTED_TRANSITIONS.get(current_state, set())
        return next_state in allowed

    @classmethod
    def transition(cls, current_state: DialogueState, next_state: DialogueState) -> DialogueState:
        """Validate and execute state transition, raising InvalidStateTransitionError if prohibited."""
        if not cls.can_transition(current_state, next_state):
            raise InvalidStateTransitionError(
                from_state=current_state.value,
                to_state=next_state.value,
                details={
                    "permitted_next_states": [s.value for s in PERMITTED_TRANSITIONS.get(current_state, set())]
                },
            )
        return next_state
