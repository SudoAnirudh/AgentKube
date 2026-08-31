import json
from typing import Any, Dict, Optional
from app.agents.base import BaseAgent
from app.core.exceptions import InvalidPlanError
from app.llm.base import BaseLLMClient
from app.models.execution import AgentResult, ExecutionPlan, ExecutionState, PlanStep


class PlannerAgent(BaseAgent):
    """Planner agent responsible for decomposing complex user tasks into structured execution plans."""

    def __init__(self, llm_client: BaseLLMClient):
        super().__init__(name="planner", llm_client=llm_client)

    def validate_plan(self, plan: ExecutionPlan) -> None:
        """Validate structural constraints of the generated ExecutionPlan."""
        if not plan.goal or not plan.goal.strip():
            raise InvalidPlanError("Execution plan goal cannot be empty.")

        if not plan.steps or len(plan.steps) == 0:
            raise InvalidPlanError("Execution plan must contain at least one step.")

        step_ids = set()
        for idx, step in enumerate(plan.steps):
            if not step.id or not step.id.strip():
                raise InvalidPlanError(f"Step at index {idx} has an empty step ID.")
            if step.id in step_ids:
                raise InvalidPlanError(f"Duplicate step ID '{step.id}' found in plan.")
            step_ids.add(step.id)

            if not step.agent or not step.agent.strip():
                raise InvalidPlanError(f"Step '{step.id}' missing target agent designation.")
            if not step.task or not step.task.strip():
                raise InvalidPlanError(f"Step '{step.id}' has empty task description.")

    async def execute(
        self,
        task: str,
        context: Dict[str, Any],
        state: ExecutionState,
        feedback: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> AgentResult:
        system_prompt = (
            "You are an expert AI Execution Planner. Your job is to decompose user tasks into a clear, "
            "sequential, and executable plan consisting of distinct steps for specialized worker agents."
        )

        prompt_content = (
            f"User Task: {task}\n"
            f"Context: {json.dumps(context, indent=2)}\n"
        )
        if feedback:
            prompt_content += f"\nPrevious Plan Rejected Feedback: {feedback}\nPlease reformulate a valid plan."

        plan: ExecutionPlan = await self.llm_client.generate_structured(
            prompt=prompt_content,
            response_model=ExecutionPlan,
            system_prompt=system_prompt,
            timeout=timeout,
        )

        self.validate_plan(plan)

        return AgentResult(
            status="success",
            result=plan.model_dump(),
            metadata={"planner": self.name, "step_count": len(plan.steps)},
        )
