from typing import Any, Dict, Optional
from app.models.execution import ErrorCategory, ExecutionError


class BaseEngineException(Exception):
    """Base exception for all execution engine errors."""

    def __init__(
        self,
        code: ErrorCategory,
        message: str,
        step_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.code = code
        self.message = message
        self.step_id = step_id
        self.details = details or {}

    def to_execution_error(self) -> ExecutionError:
        return ExecutionError(
            code=self.code,
            message=self.message,
            step_id=self.step_id,
            details=self.details,
        )


class InvalidRequestError(BaseEngineException):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(ErrorCategory.INVALID_REQUEST, message, details=details)


class InvalidPlanError(BaseEngineException):
    def __init__(self, message: str, step_id: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(ErrorCategory.INVALID_PLAN, message, step_id=step_id, details=details)


class AgentExecutionException(BaseEngineException):
    def __init__(self, message: str, step_id: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(ErrorCategory.AGENT_EXECUTION_ERROR, message, step_id=step_id, details=details)


class LLMProviderError(BaseEngineException):
    def __init__(self, message: str, step_id: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(ErrorCategory.LLM_ERROR, message, step_id=step_id, details=details)


class InvalidLLMOutputError(BaseEngineException):
    def __init__(self, message: str, step_id: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(ErrorCategory.INVALID_LLM_OUTPUT, message, step_id=step_id, details=details)


class EvaluationFailureError(BaseEngineException):
    def __init__(self, message: str, step_id: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(ErrorCategory.EVALUATION_FAILURE, message, step_id=step_id, details=details)


class RecoveryExhaustedError(BaseEngineException):
    def __init__(self, message: str, step_id: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(ErrorCategory.RECOVERY_EXHAUSTED, message, step_id=step_id, details=details)


class TimeoutExecutionError(BaseEngineException):
    def __init__(self, message: str, step_id: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(ErrorCategory.TIMEOUT, message, step_id=step_id, details=details)


class InternalEngineError(BaseEngineException):
    def __init__(self, message: str, step_id: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(ErrorCategory.INTERNAL_ERROR, message, step_id=step_id, details=details)
