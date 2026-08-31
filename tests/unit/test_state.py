from app.core.state import StateManager
from app.models.execution import ErrorCategory, ExecutionError, ExecutionStatus


def test_state_manager_lifecycle():
    mgr = StateManager()
    state = mgr.create_state(task="Sample Job Analysis", context={"job_id": 101})

    assert state.execution_id.startswith("exec_")
    assert state.status == ExecutionStatus.RUNNING
    assert state.task == "Sample Job Analysis"

    state.record_step_completion("step_1", {"skills": ["Python"]})
    assert "step_1" in state.completed_steps
    assert state.outputs["step_1"] == {"skills": ["Python"]}

    err = ExecutionError(code=ErrorCategory.AGENT_EXECUTION_ERROR, message="Execution error")
    state.record_step_failure("step_2", err)
    assert "step_2" in state.failed_steps
    assert len(state.errors) == 1

    assert state.increment_retry("step_2") == 1
    assert state.increment_retry("step_2") == 2
    assert state.total_retries() == 2
