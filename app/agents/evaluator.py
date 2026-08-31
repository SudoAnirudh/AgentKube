import json
from typing import Any, Dict, Optional
from app.agents.base import BaseAgent
from app.llm.base import BaseLLMClient
from app.models.execution import AgentResult, EvaluationResult, ExecutionState


class EvaluatorAgent(BaseAgent):
    """Evaluator agent responsible for assessing intermediate agent outputs."""

    def __init__(self, llm_client: BaseLLMClient):
        super().__init__(name="evaluator", llm_client=llm_client)

    async def evaluate_output(
        self,
        task: str,
        step_output: AgentResult,
        state: ExecutionState,
        timeout: Optional[float] = None,
    ) -> EvaluationResult:
        # Deterministic check 1: Check if output is empty
        if not step_output.result:
            return EvaluationResult(
                status="failed",
                reason="Agent produced an empty output dictionary.",
                confidence=1.0,
            )

        system_prompt = (
            "You are an objective Evaluator Agent. Your job is to strictly evaluate whether a worker agent's output "
            "satisfies the requirements of its assigned task. Provide a JSON response indicating whether it passed or failed."
        )

        prompt_payload = {
            "assigned_task": task,
            "agent_output": step_output.result,
            "overall_goal": state.task,
        }

        prompt_text = (
            f"Evaluate the following output against the task requirements:\n"
            f"{json.dumps(prompt_payload, indent=2)}"
        )

        return await self.llm_client.generate_structured(
            prompt=prompt_text,
            response_model=EvaluationResult,
            system_prompt=system_prompt,
            timeout=timeout,
        )

    async def execute(
        self,
        task: str,
        context: Dict[str, Any],
        state: ExecutionState,
        feedback: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> AgentResult:
        # Generic execute method wrapping evaluate_output if invoked as a regular agent step
        dummy_result = AgentResult(result=context.get("output", {}))
        eval_res = await self.evaluate_output(task=task, step_output=dummy_result, state=state, timeout=timeout)
        return AgentResult(
            status=eval_res.status,
            result=eval_res.model_dump(),
            metadata={"evaluator": self.name},
        )
