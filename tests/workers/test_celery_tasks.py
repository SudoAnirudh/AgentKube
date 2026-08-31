import pytest
from app.models.execution import ExecutionStatus
from app.storage.redis import RedisStateManager
from app.workers.tasks import run_agent_execution


def test_celery_task_execution_eager():
    state_mgr = RedisStateManager()
    state = state_mgr.create_state(task="Celery Worker Task Test", context={"job_desc": "Developer"})

    result = run_agent_execution.delay(state.execution_id).get()
    assert result["status"] == "completed"
    assert result["steps_executed"] >= 1

    final_state = state_mgr.get_state(state.execution_id)
    assert final_state.status == ExecutionStatus.COMPLETED
    assert len(final_state.completed_steps) >= 1


def test_celery_task_idempotency_skip():
    state_mgr = RedisStateManager()
    state = state_mgr.create_state(task="Idempotency Test", context={})
    state.status = ExecutionStatus.COMPLETED
    state_mgr.save_state(state)

    result = run_agent_execution.delay(state.execution_id).get()
    assert result["status"] == "completed"
    assert result.get("skipped") is True
