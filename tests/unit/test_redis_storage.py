import pytest
from app.models.execution import ExecutionStatus
from app.storage.redis import RedisStateManager


def test_redis_state_manager_ping():
    state_mgr = RedisStateManager()
    assert state_mgr.ping() is True


def test_redis_state_manager_lifecycle():
    state_mgr = RedisStateManager()
    state = state_mgr.create_state(task="Redis Test Task", context={"test_key": "val"})

    assert state.execution_id.startswith("exec_")
    assert state.status == ExecutionStatus.QUEUED

    fetched = state_mgr.get_state(state.execution_id)
    assert fetched is not None
    assert fetched.task == "Redis Test Task"
    assert fetched.status == ExecutionStatus.QUEUED

    # Update state and save
    state.status = ExecutionStatus.RUNNING
    state.record_step_completion("step_1", {"skills": ["Python"]})
    state_mgr.save_state(state)

    updated = state_mgr.get_state(state.execution_id)
    assert updated.status == ExecutionStatus.RUNNING
    assert "step_1" in updated.completed_steps
    assert updated.outputs["step_1"] == {"skills": ["Python"]}


def test_redis_state_manager_non_existent():
    state_mgr = RedisStateManager()
    assert state_mgr.get_state("non_existent_id") is None
