import asyncio
import json
from typing import Any, Dict, List, Optional
from app.core.exceptions import InvalidLLMOutputError, TimeoutExecutionError
from app.llm.base import BaseLLMClient


class MockLLMClient(BaseLLMClient):
    """Mock LLM Client for deterministic offline testing and scenario injection."""

    def __init__(
        self,
        mode: str = "success",
        custom_responses: Optional[List[str]] = None,
        delay_seconds: float = 0.0,
    ):
        self.mode = mode
        self.custom_responses = custom_responses or []
        self.delay_seconds = delay_seconds
        self.call_count = 0
        self.attempt_counts: Dict[str, int] = {}

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        timeout: Optional[float] = 30.0,
    ) -> str:
        self.call_count += 1

        if self.delay_seconds > 0:
            await asyncio.sleep(self.delay_seconds)

        if self.mode == "timeout":
            raise TimeoutExecutionError("Simulated LLM operation timeout")

        if self.mode == "malformed":
            return "This is not valid JSON output at all..."

        if self.custom_responses:
            idx = (self.call_count - 1) % len(self.custom_responses)
            return self.custom_responses[idx]

        prompt_lower = prompt.lower()
        sys_lower = (system_prompt or "").lower()

        # 1. Test sample schema detection
        if "sampleschema" in sys_lower:
            return json.dumps({"name": "test_sample", "count": 42})

        # 2. Evaluator request detection
        if "evaluationresult" in sys_lower or "evaluator agent" in sys_lower or "evaluate the following" in prompt_lower:
            step_id = "step_1"
            if "step_2" in prompt_lower:
                step_id = "step_2"

            attempts = self.attempt_counts.get(step_id, 0) + 1
            self.attempt_counts[step_id] = attempts

            if self.mode == "fail_eval_once" and step_id == "step_1" and attempts == 1:
                return json.dumps({
                    "status": "failed",
                    "reason": "Output appears incomplete. Missing details on cloud platforms.",
                    "confidence": 0.85
                })

            if self.mode == "fail_eval_always":
                return json.dumps({
                    "status": "failed",
                    "reason": "Simulated permanent evaluation failure.",
                    "confidence": 0.95
                })

            return json.dumps({
                "status": "passed",
                "reason": "Output meets all task requirements cleanly.",
                "confidence": 0.95
            })

        # 3. Planner request detection
        if "executionplan" in sys_lower or "execution planner" in sys_lower or "decompose user tasks" in sys_lower:
            if self.mode == "invalid_plan":
                return json.dumps({"goal": "Invalid Goal", "steps": []})
            return json.dumps({
                "goal": "Analyze job description and extract requirements",
                "steps": [
                    {
                        "id": "step_1",
                        "agent": "researcher",
                        "task": "Extract required technical skills",
                        "params": {}
                    },
                    {
                        "id": "step_2",
                        "agent": "researcher",
                        "task": "Identify key responsibilities",
                        "params": {}
                    }
                ]
            })

        # 4. Researcher / Worker agent request detection
        if "skills" in prompt_lower or "step_1" in prompt_lower:
            return json.dumps({
                "status": "success",
                "result": {
                    "technical_skills": ["Python", "FastAPI", "PostgreSQL", "Docker", "Kubernetes"],
                    "experience_level": "Senior"
                },
                "metadata": {"extracted_count": 5}
            })

        return json.dumps({
            "status": "success",
            "result": {
                "responsibilities": [
                    "Design microservice architecture",
                    "Implement backend APIs using FastAPI",
                    "Maintain unit test suites"
                ]
            },
            "metadata": {"responsibility_count": 3}
        })
