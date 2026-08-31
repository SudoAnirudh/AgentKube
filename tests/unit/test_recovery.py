import pytest
from app.core.exceptions import RecoveryExhaustedError
from app.core.recovery import RecoveryEngine
from app.core.state import StateManager
from app.models.execution import EvaluationResult, PlanStep


def test_recovery_engine_retries_and_exhausts():
    recovery = RecoveryEngine(max_retries=2)
    state = StateManager().create_state(task="Test task")
    step = PlanStep(id="step_1", agent="researcher", task="Initial Task")

    failed_eval = EvaluationResult(status="failed", reason="Incomplete analysis")

    # Retry 1 (Attempt 1)
    task1, feedback1 = recovery.handle_failure(step=step, evaluation=failed_eval, state=state)
    assert feedback1 is not None
    assert state.retry_count["step_1"] == 1

    # Retry 2 (Attempt 2)
    task2, feedback2 = recovery.handle_failure(step=step, evaluation=failed_eval, state=state)
    assert "RECOVERY ATTEMPT 2" in task2
    assert state.retry_count["step_1"] == 2

    # Retry 3 (Attempt 3 - exceeds max_retries=2)
    with pytest.raises(RecoveryExhaustedError, match="exhausted maximum recovery retries"):
        recovery.handle_failure(step=step, evaluation=failed_eval, state=state)
