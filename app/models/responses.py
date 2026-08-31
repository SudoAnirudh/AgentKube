from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from app.models.execution import ExecutionError, ExecutionStatus


class ExecutionStats(BaseModel):
    steps_executed: int = Field(..., description="Total steps completed")
    retries: int = Field(..., description="Total retry attempts across all steps")


class JobSubmissionResponse(BaseModel):
    execution_id: str
    status: str = "queued"


class JobStatusResponse(BaseModel):
    execution_id: str
    status: ExecutionStatus
    task: Optional[str] = None
    current_step: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    execution: Optional[ExecutionStats] = None
    error: Optional[ExecutionError] = None


class AgentRunResponseSuccess(BaseModel):
    execution_id: str
    status: str = "completed"
    result: Dict[str, Any] = Field(default_factory=dict)
    execution: ExecutionStats


class AgentRunResponseFailure(BaseModel):
    execution_id: str
    status: str = "failed"
    error: ExecutionError


class HealthResponse(BaseModel):
    status: str = "healthy"


class ReadinessResponse(BaseModel):
    status: str = "ready"

