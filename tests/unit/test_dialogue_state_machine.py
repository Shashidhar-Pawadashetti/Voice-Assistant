"""Unit tests for DialogueStateMachine deterministic transition rules and rejection."""

import pytest
from app.core.dialogue.state_machine import DialogueState, DialogueStateMachine
from app.core.exceptions import InvalidStateTransitionError


def test_valid_transitions():
    # GREETING -> COLLECTING_SLOTS
    assert (
        DialogueStateMachine.transition(DialogueState.GREETING, DialogueState.COLLECTING_SLOTS)
        == DialogueState.COLLECTING_SLOTS
    )

    # COLLECTING_SLOTS -> CONFIRMING
    assert (
        DialogueStateMachine.transition(DialogueState.COLLECTING_SLOTS, DialogueState.CONFIRMING)
        == DialogueState.CONFIRMING
    )

    # CONFIRMING -> EVALUATION_READY
    assert (
        DialogueStateMachine.transition(DialogueState.CONFIRMING, DialogueState.EVALUATION_READY)
        == DialogueState.EVALUATION_READY
    )

    # EVALUATION_READY -> RESPONDING
    assert (
        DialogueStateMachine.transition(DialogueState.EVALUATION_READY, DialogueState.RESPONDING)
        == DialogueState.RESPONDING
    )

    # Any active state -> PAUSED
    assert (
        DialogueStateMachine.transition(DialogueState.COLLECTING_SLOTS, DialogueState.PAUSED)
        == DialogueState.PAUSED
    )

    # PAUSED -> COLLECTING_SLOTS (Resumed)
    assert (
        DialogueStateMachine.transition(DialogueState.PAUSED, DialogueState.COLLECTING_SLOTS)
        == DialogueState.COLLECTING_SLOTS
    )

    # Active -> COMPLETED
    assert (
        DialogueStateMachine.transition(DialogueState.RESPONDING, DialogueState.COMPLETED)
        == DialogueState.COMPLETED
    )


def test_invalid_transitions_rejected():
    # COMPLETED is terminal; cannot transition anywhere
    with pytest.raises(InvalidStateTransitionError) as exc_info:
        DialogueStateMachine.transition(DialogueState.COMPLETED, DialogueState.GREETING)
    assert exc_info.value.code == "INVALID_STATE_TRANSITION"

    with pytest.raises(InvalidStateTransitionError):
        DialogueStateMachine.transition(DialogueState.COMPLETED, DialogueState.COLLECTING_SLOTS)

    # GREETING cannot jump directly to EVALUATION_READY
    with pytest.raises(InvalidStateTransitionError):
        DialogueStateMachine.transition(DialogueState.GREETING, DialogueState.EVALUATION_READY)


def test_can_transition_predicate():
    assert DialogueStateMachine.can_transition(DialogueState.GREETING, DialogueState.COLLECTING_SLOTS) is True
    assert DialogueStateMachine.can_transition(DialogueState.COMPLETED, DialogueState.COLLECTING_SLOTS) is False
