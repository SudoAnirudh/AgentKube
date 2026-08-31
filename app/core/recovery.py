from typing import Any, Dict, Optional, Tuple
from app.core.exceptions import RecoveryExhaustedError
from app.models.execution import EvaluationResult, ExecutionError, ErrorCategory, ExecutionState, PlanStep
from app.utils.logger import log_execution_event


class RecoveryEngine:
    """Engine responsible for recovery strategies and bounded retry enforcement."""

    def __init__(self, max_retries: int = 2):
        self.max_retries = max_retries

    def handle_failure(
        self,
        step: PlanStep,
        evaluation: EvaluationResult,
        state: ExecutionState,
    ) -> Tuple[str, str]:
        """
        Evaluate retry limits and select recovery strategy.

        Returns:
            Tuple of (reformulated_task, feedback_for_agent)
        Raises:
            RecoveryExhaustedError if max_retries limit is exceeded.
        """
        attempt = state.increment_retry(step.id)

        log_execution_event(
            level="WARN",
            event="recovery_started",
            execution_id=state.execution_id,
            step_id=step.id,
            attempt=attempt,
            reason=evaluation.reason,
        )

        if attempt > self.max_retries:
            error = ExecutionError(
                code=ErrorCategory.RECOVERY_EXHAUSTED,
                message=f"Step '{step.id}' exhausted maximum recovery retries ({self.max_retries}). Last reason: {evaluation.reason}",
                step_id=step.id,
                details={"retries": attempt - 1, "last_eval_reason": evaluation.reason},
            )
            state.record_step_failure(step.id, error)
            log_execution_event(
                level="ERROR",
                event="recovery_exhausted",
                execution_id=state.execution_id,
                step_id=step.id,
                attempt=attempt,
                error_code="RECOVERY_EXHAUSTED",
            )
            raise RecoveryExhaustedError(
                message=error.message,
                step_id=step.id,
                details=error.details,
            )

        feedback = f"Evaluation failed on attempt {attempt}: {evaluation.reason or 'Output failed quality validation.'}"

        if attempt == 1:
            # Strategy 1: Include evaluator feedback directly
            reformulated_task = step.task
        else:
            # Strategy 2: Reformulate task with explicit correction guidance
            reformulated_task = (
                f"{step.task} (RECOVERY ATTEMPT {attempt}: Please pay special attention to completeness "
                f"and address feedback: {evaluation.reason})"
            )

        log_execution_event(
            level="INFO",
            event="recovery_strategy_selected",
            execution_id=state.execution_id,
            step_id=step.id,
            attempt=attempt,
            extra_details={"strategy": f"Strategy {attempt}", "reformulated_task": reformulated_task},
        )

        return reformulated_task, feedback
