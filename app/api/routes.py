from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from app.models.execution import ExecutionStatus
from app.models.requests import AgentRunRequest
from app.models.responses import (
    ExecutionStats,
    HealthResponse,
    JobStatusResponse,
    JobSubmissionResponse,
    ReadinessResponse,
)
from app.storage.redis import RedisStateManager
from app.utils.config import Settings, get_settings
from app.utils.logger import get_logger, log_execution_event
from app.workers.tasks import run_agent_execution

logger = get_logger()
router = APIRouter()


def get_state_manager(settings: Settings = Depends(get_settings)) -> RedisStateManager:
    return RedisStateManager(redis_url=settings.REDIS_URL)


@router.get("/health", response_model=HealthResponse, tags=["Health"])
async def liveness_check():
    """Liveness probe to verify FastAPI application server process is running."""
    return HealthResponse(status="healthy")


@router.get("/ready", response_model=ReadinessResponse, tags=["Health"])
async def readiness_check(state_mgr: RedisStateManager = Depends(get_state_manager)):
    """Readiness probe verifying Redis connectivity and service readiness."""
    redis_ok = state_mgr.ping()
    if not redis_ok:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Storage connectivity check failed.",
        )
    return ReadinessResponse(status="ready")



@router.post(
    "/api/v1/agent/run",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=JobSubmissionResponse,
    responses={
        400: {"description": "Invalid task string"},
        500: {"description": "Internal server error"},
    },
    tags=["Execution Engine"],
)
async def submit_agent_task(
    request: AgentRunRequest,
    state_mgr: RedisStateManager = Depends(get_state_manager),
):
    """
    Submit an agent execution task. Enqueues job in Redis/Celery and immediately returns HTTP 202 Accepted.
    """
    if not request.task or not request.task.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Task string cannot be empty.",
        )

    # 1. Create state in Redis with status = QUEUED
    state = state_mgr.create_state(task=request.task, context=request.context)

    log_execution_event(
        "INFO",
        "job_queued",
        execution_id=state.execution_id,
        status=state.status.value,
    )

    # 2. Enqueue Celery background task
    run_agent_execution.delay(state.execution_id)

    return JobSubmissionResponse(
        execution_id=state.execution_id,
        status="queued",
    )


@router.get(
    "/api/v1/agent/run/{execution_id}",
    response_model=JobStatusResponse,
    responses={
        404: {"description": "Execution ID not found"},
    },
    tags=["Execution Engine"],
)
async def get_agent_job_status(
    execution_id: str,
    state_mgr: RedisStateManager = Depends(get_state_manager),
):
    """
    Query the status and outputs of an asynchronous agent execution job.
    """
    state = state_mgr.get_state(execution_id)
    if not state:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "error": {
                    "code": "EXECUTION_NOT_FOUND",
                    "message": f"Execution '{execution_id}' was not found.",
                }
            },
        )

    exec_stats = ExecutionStats(
        steps_executed=len(state.completed_steps),
        retries=state.total_retries(),
    )

    last_error = state.errors[-1] if state.errors else None

    return JobStatusResponse(
        execution_id=state.execution_id,
        status=state.status,
        task=state.task,
        current_step=state.current_step,
        result=state.outputs if state.status == ExecutionStatus.COMPLETED else None,
        execution=exec_stats,
        error=last_error if state.status == ExecutionStatus.FAILED else None,
    )
