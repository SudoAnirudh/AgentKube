import abc
from typing import Any, Dict, Optional
from app.llm.base import BaseLLMClient
from app.models.execution import AgentResult, ExecutionState


class BaseAgent(abc.ABC):
    """Abstract Base Class for specialized agents."""

    def __init__(self, name: str, llm_client: BaseLLMClient):
        self.name = name
        self.llm_client = llm_client

    @abc.abstractmethod
    async def execute(
        self,
        task: str,
        context: Dict[str, Any],
        state: ExecutionState,
        feedback: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> AgentResult:
        """Execute the agent's task given context, execution state, and optional feedback."""
        pass
