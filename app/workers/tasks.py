import asyncio
import concurrent.futures
from typing import Any, Dict, Optional
from app.core.orchestrator import Orchestrator
from app.llm.factory import create_llm_client
from app.models.execution import ExecutionStatus
from app.storage.redis import RedisStateManager
from app.utils.config import get_settings
from app.utils.logger import get_logger, log_execution_event
from app.workers.celery_app import celery_app

logger = get_logger()


def run_coroutine_sync(coro):
    """Safely run an async coroutine from a synchronous context or active event loop."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(lambda: asyncio.run(coro))
            return future.result()
    else:
        return asyncio.run(coro)


@celery_app.task(bind=True, name="run_agent_execution")
def run_agent_execution(self, execution_id: str) -> Dict[str, Any]:
    """
    Celery background worker task to execute the multi-agent orchestration engine.
    """
    settings = get_settings()
    state_mgr = RedisStateManager(redis_url=settings.REDIS_URL)
    state = state_mgr.get_state(execution_id)

    if not state:
        logger.error(f"worker_task_failed message='Execution ID not found in Redis' execution_id={execution_id}")
        return {"status": "error", "reason": f"Execution ID '{execution_id}' not found"}

    # Idempotency Guard (PRD Section 20 & 21)
    if state.status in (ExecutionStatus.RUNNING, ExecutionStatus.COMPLETED):
        log_execution_event(
            "WARN",
            "duplicate_execution_skipped",
            execution_id=execution_id,
            status=state.status.value,
            reason="Execution is already running or completed",
        )
        return {"status": state.status.value, "skipped": True}

    log_execution_event("INFO", "worker_received_task", execution_id=execution_id)

    # Initialize LLM client and orchestrator
    llm_client = create_llm_client(settings)
    orchestrator = Orchestrator(llm_client=llm_client, settings=settings, state_manager=state_mgr)

    # Execute orchestrator lifecycle asynchronously
    final_state = run_coroutine_sync(
        orchestrator.execute_task(task=state.task, context=state.context, existing_state=state)
    )

    log_execution_event(
        "INFO",
        "worker_execution_finished",
        execution_id=execution_id,
        status=final_state.status.value,
    )

    return {
        "execution_id": final_state.execution_id,
        "status": final_state.status.value,
        "steps_executed": len(final_state.completed_steps),
        "retries": final_state.total_retries(),
    }
