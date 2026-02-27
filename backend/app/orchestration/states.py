"""State machine states and transitions."""

from enum import Enum


class WorkflowState(str, Enum):
    INGESTED = "INGESTED"
    INITIAL_REVIEW = "INITIAL_REVIEW"
    DEBATE = "DEBATE"
    CONSENSUS = "CONSENSUS"
    FINALIZED = "FINALIZED"


VALID_TRANSITIONS: dict[WorkflowState, list[WorkflowState]] = {
    WorkflowState.INGESTED: [WorkflowState.INITIAL_REVIEW],
    WorkflowState.INITIAL_REVIEW: [WorkflowState.DEBATE, WorkflowState.CONSENSUS, WorkflowState.FINALIZED],
    WorkflowState.DEBATE: [WorkflowState.CONSENSUS],
    WorkflowState.CONSENSUS: [WorkflowState.FINALIZED],
    WorkflowState.FINALIZED: [],
}


def can_transition(from_state: WorkflowState, to_state: WorkflowState) -> bool:
    """Check if transition is valid."""
    return to_state in VALID_TRANSITIONS.get(from_state, [])
