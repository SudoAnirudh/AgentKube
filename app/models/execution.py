from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class StepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    RECOVERED = "recovered"
    EXHAUSTED = "exhausted"
    SKIPPED = "skipped"


class ExecutionStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    RECOVERING = "recovering"
    COMPLETED = "completed"
    FAILED = "failed"


class ErrorCategory(str, Enum):
    INVALID_REQUEST = "INVALID_REQUEST"
    INVALID_PLAN = "INVALID_PLAN"
    AGENT_EXECUTION_ERROR = "AGENT_EXECUTION_ERROR"
    LLM_ERROR = "LLM_ERROR"
    INVALID_LLM_OUTPUT = "INVALID_LLM_OUTPUT"
    EVALUATION_FAILURE = "EVALUATION_FAILURE"
    RECOVERY_EXHAUSTED = "RECOVERY_EXHAUSTED"
    TIMEOUT = "TIMEOUT"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class ExecutionError(BaseModel):
    code: ErrorCategory
    message: str
    step_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class PlanStep(BaseModel):
    id: str = Field(..., description="Unique identifier for the step (e.g. step_1)")
    agent: str = Field(..., description="Target agent assigned to execute this step (e.g. researcher)")
    task: str = Field(..., description="Specific instruction for the agent")
    params: Dict[str, Any] = Field(default_factory=dict, description="Optional step execution parameters")


class ExecutionPlan(BaseModel):
    goal: str = Field(..., description="High-level goal for the plan")
    steps: List[PlanStep] = Field(..., description="List of plan steps in execution order")


class AgentResult(BaseModel):
    status: str = Field(default="success", description="Status of the agent execution")
    result: Dict[str, Any] = Field(default_factory=dict, description="Structured agent output data")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata such as execution timing or model info")


class EvaluationResult(BaseModel):
    status: str = Field(..., description="Evaluation outcome: 'passed' or 'failed'")
    reason: Optional[str] = Field(default=None, description="Detailed explanation if evaluation failed")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Confidence score of evaluation")


class ExecutionState(BaseModel):
    execution_id: str
    task: str
    context: Dict[str, Any] = Field(default_factory=dict)
    status: ExecutionStatus = ExecutionStatus.RUNNING
    current_step: Optional[str] = None
    plan: Optional[ExecutionPlan] = None
    completed_steps: List[str] = Field(default_factory=list)
    failed_steps: List[str] = Field(default_factory=list)
    retry_count: Dict[str, int] = Field(default_factory=dict)
    outputs: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    errors: List[ExecutionError] = Field(default_factory=list)
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None

    def record_step_completion(self, step_id: str, output: Dict[str, Any]) -> None:
        if step_id not in self.completed_steps:
            self.completed_steps.append(step_id)
        self.outputs[step_id] = output

    def record_step_failure(self, step_id: str, error: ExecutionError) -> None:
        if step_id not in self.failed_steps:
            self.failed_steps.append(step_id)
        self.errors.append(error)

    def increment_retry(self, step_id: str) -> int:
        current = self.retry_count.get(step_id, 0)
        self.retry_count[step_id] = current + 1
        return self.retry_count[step_id]

    def total_retries(self) -> int:
        return sum(self.retry_count.values())
