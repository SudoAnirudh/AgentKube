import json
from typing import Any, Dict, Optional
from app.agents.base import BaseAgent
from app.llm.base import BaseLLMClient
from app.models.execution import AgentResult, ExecutionState


class ResearchAgent(BaseAgent):
    """Research / Analysis worker agent for executing analytical sub-tasks."""

    def __init__(self, llm_client: BaseLLMClient):
        super().__init__(name="researcher", llm_client=llm_client)

    async def execute(
        self,
        task: str,
        context: Dict[str, Any],
        state: ExecutionState,
        feedback: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> AgentResult:
        system_prompt = (
            "You are a specialized Research and Analysis AI Agent. Your role is to perform deep, "
            "accurate analysis on provided information, extract required data points, and return structured analysis."
        )

        prompt_payload = {
            "step_task": task,
            "global_task": state.task,
            "context": context,
            "prior_step_outputs": state.outputs,
        }
        if feedback:
            prompt_payload["evaluator_feedback"] = feedback

        prompt_text = (
            f"Perform the following sub-task:\n"
            f"{json.dumps(prompt_payload, indent=2)}\n\n"
            f"Provide a structured JSON object containing your analysis results."
        )

        # Call LLM for generation
        raw_output = await self.llm_client.generate(
            prompt=prompt_text,
            system_prompt=system_prompt,
            timeout=timeout,
        )

        try:
            parsed_result = json.loads(raw_output)
            if not isinstance(parsed_result, dict):
                parsed_result = {"analysis": str(parsed_result)}
        except json.JSONDecodeError:
            parsed_result = {"analysis": raw_output}

        return AgentResult(
            status="success",
            result=parsed_result,
            metadata={"agent": self.name, "task": task},
        )
