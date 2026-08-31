import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from app.agents.base import BaseAgent
from app.agents.evaluator import EvaluatorAgent
from app.agents.planner import PlannerAgent
from app.agents.researcher import ResearchAgent
from app.core.exceptions import (
    AgentExecutionException,
    BaseEngineException,
    EvaluationFailureError,
    InternalEngineError,
    InvalidPlanError,
    RecoveryExhaustedError,
    TimeoutExecutionError,
)
from app.core.recovery import RecoveryEngine
from app.core.state import StateManager
from app.llm.base import BaseLLMClient
from app.models.execution import (
    AgentResult,
    ErrorCategory,
    EvaluationResult,
    ExecutionError,
    ExecutionPlan,
    ExecutionState,
    ExecutionStatus,
    PlanStep,
)
from app.storage.redis import RedisStateManager
from app.utils.config import Settings, get_settings
from app.utils.logger import log_execution_event


class Orchestrator:
    """Central Orchestrator controlling plan creation, step execution, evaluation, and recovery."""

    def __init__(
        self,
        llm_client: BaseLLMClient,
        settings: Optional[Settings] = None,
        state_manager: Optional[Any] = None,
    ):
        self.settings = settings or get_settings()
        self.llm_client = llm_client
        self.state_manager = state_manager or StateManager()

        # Initialize agents
        self.planner = PlannerAgent(llm_client=llm_client)
        self.evaluator = EvaluatorAgent(llm_client=llm_client)

        # Worker agent registry
        self.workers: Dict[str, BaseAgent] = {
            "researcher": ResearchAgent(llm_client=llm_client),
            "evaluator": self.evaluator,
        }

        self.recovery_engine = RecoveryEngine(max_retries=self.settings.MAX_RETRIES)

    def register_worker(self, name: str, agent: BaseAgent) -> None:
        self.workers[name.lower()] = agent

    async def execute_task(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None,
        existing_state: Optional[ExecutionState] = None,
    ) -> ExecutionState:
        """Run the end-to-end multi-agent execution lifecycle."""
        if existing_state:
            state = existing_state
            state.status = ExecutionStatus.RUNNING
        else:
            state = self.state_manager.create_state(task=task, context=context)

        self.state_manager.save_state(state)
        log_execution_event("INFO", "execution_started", execution_id=state.execution_id)

        try:
            # 1. Planning Phase
            log_execution_event("INFO", "planning_started", execution_id=state.execution_id)
            planner_result: AgentResult = await self._run_with_timeout(
                self.planner.execute(task=task, context=state.context, state=state),
                timeout=self.settings.AGENT_TIMEOUT_SECONDS,
                step_id="planning",
            )
            plan = ExecutionPlan.model_validate(planner_result.result)
            state.plan = plan
            self.state_manager.save_state(state)
            log_execution_event("INFO", "planning_completed", execution_id=state.execution_id)

            # 2. Execution Loop
            for step in plan.steps:
                state.current_step = step.id
                await self._execute_plan_step(step=step, state=state)

            # 3. Assemble Final Response
            state.status = ExecutionStatus.COMPLETED
            state.completed_at = datetime.now(timezone.utc)
            log_execution_event("INFO", "execution_completed", execution_id=state.execution_id)

        except BaseEngineException as engine_err:
            state.status = ExecutionStatus.FAILED
            state.completed_at = datetime.now(timezone.utc)
            exec_err = engine_err.to_execution_error()
            state.errors.append(exec_err)
            log_execution_event(
                "ERROR",
                "execution_failed",
                execution_id=state.execution_id,
                step_id=state.current_step,
                error_code=exec_err.code.value,
                reason=exec_err.message,
            )
        except Exception as unhandled_err:
            state.status = ExecutionStatus.FAILED
            state.completed_at = datetime.now(timezone.utc)
            exec_err = ExecutionError(
                code=ErrorCategory.INTERNAL_ERROR,
                message=f"Unhandled engine failure: {str(unhandled_err)}",
                step_id=state.current_step,
            )
            state.errors.append(exec_err)
            log_execution_event(
                "ERROR",
                "execution_failed",
                execution_id=state.execution_id,
                step_id=state.current_step,
                error_code="INTERNAL_ERROR",
                reason=str(unhandled_err),
            )

        self.state_manager.save_state(state)
        return state

    async def _execute_plan_step(self, step: PlanStep, state: ExecutionState) -> None:
        agent_name = step.agent.lower()
        worker_agent = self.workers.get(agent_name)
        if not worker_agent:
            worker_agent = self.workers["researcher"]

        log_execution_event(
            "INFO",
            "step_started",
            execution_id=state.execution_id,
            step_id=step.id,
            agent=worker_agent.name,
        )
        self.state_manager.save_state(state)

        current_task = step.task
        feedback: Optional[str] = None
        step_passed = False

        while not step_passed:
            try:
                agent_output: AgentResult = await self._run_with_timeout(
                    worker_agent.execute(
                        task=current_task,
                        context=state.context,
                        state=state,
                        feedback=feedback,
                    ),
                    timeout=self.settings.AGENT_TIMEOUT_SECONDS,
                    step_id=step.id,
                )
            except TimeoutExecutionError as timeout_err:
                state.status = ExecutionStatus.RECOVERING
                dummy_eval = EvaluationResult(
                    status="failed",
                    reason=f"Step execution timed out after {self.settings.AGENT_TIMEOUT_SECONDS}s",
                    confidence=1.0,
                )
                current_task, feedback = self.recovery_engine.handle_failure(
                    step=step, evaluation=dummy_eval, state=state
                )
                self.state_manager.save_state(state)
                continue

            # Execute Evaluator
            log_execution_event(
                "INFO",
                "evaluation_started",
                execution_id=state.execution_id,
                step_id=step.id,
            )

            eval_result: EvaluationResult = await self._run_with_timeout(
                self.evaluator.evaluate_output(
                    task=step.task,
                    step_output=agent_output,
                    state=state,
                ),
                timeout=self.settings.AGENT_TIMEOUT_SECONDS,
                step_id=step.id,
            )

            if eval_result.status.lower() == "passed":
                step_passed = True
                state.status = ExecutionStatus.RUNNING
                state.record_step_completion(step_id=step.id, output=agent_output.result)
                self.state_manager.save_state(state)
                log_execution_event(
                    "INFO",
                    "evaluation_passed",
                    execution_id=state.execution_id,
                    step_id=step.id,
                )
            else:
                state.status = ExecutionStatus.RECOVERING
                log_execution_event(
                    "WARN",
                    "evaluation_failed",
                    execution_id=state.execution_id,
                    step_id=step.id,
                    reason=eval_result.reason,
                )
                current_task, feedback = self.recovery_engine.handle_failure(
                    step=step, evaluation=eval_result, state=state
                )
                self.state_manager.save_state(state)

    async def _run_with_timeout(self, coro, timeout: float, step_id: Optional[str] = None) -> Any:
        try:
            return await asyncio.wait_for(coro, timeout=timeout)
        except asyncio.TimeoutError as err:
            raise TimeoutExecutionError(
                message=f"Operation timed out after {timeout} seconds.",
                step_id=step_id,
            ) from err
