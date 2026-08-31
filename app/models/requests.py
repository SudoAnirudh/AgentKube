from typing import Any, Dict
from pydantic import BaseModel, Field


class AgentRunRequest(BaseModel):
    task: str = Field(..., description="The primary task instruction for the multi-agent system")
    context: Dict[str, Any] = Field(default_factory=dict, description="Optional background context or input data")
