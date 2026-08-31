import uuid
from typing import Dict, Optional
from app.models.execution import ExecutionState


class StateManager:
    """In-memory state manager for execution sessions."""

    def __init__(self):
        self._states: Dict[str, ExecutionState] = {}

    def create_state(self, task: str, context: Optional[Dict] = None) -> ExecutionState:
        execution_id = f"exec_{uuid.uuid4().hex[:12]}"
        state = ExecutionState(
            execution_id=execution_id,
            task=task,
            context=context or {},
        )
        self._states[execution_id] = state
        return state

    def get_state(self, execution_id: str) -> Optional[ExecutionState]:
        return self._states.get(execution_id)

    def save_state(self, state: ExecutionState) -> None:
        self._states[state.execution_id] = state
