import pytest
from app.agents.evaluator import EvaluatorAgent
from app.core.state import StateManager
from app.llm.mock import MockLLMClient
from app.models.execution import AgentResult


@pytest.mark.asyncio
async def test_evaluator_passes_valid_output():
    mock_llm = MockLLMClient(mode="success")
    evaluator = EvaluatorAgent(llm_client=mock_llm)
    state = StateManager().create_state(task="Extract requirements")
    valid_output = AgentResult(result={"skills": ["Python", "FastAPI"]})

    eval_res = await evaluator.evaluate_output(task="Extract skills", step_output=valid_output, state=state)
    assert eval_res.status == "passed"
    assert eval_res.confidence > 0.5


@pytest.mark.asyncio
async def test_evaluator_fails_empty_output():
    mock_llm = MockLLMClient(mode="success")
    evaluator = EvaluatorAgent(llm_client=mock_llm)
    state = StateManager().create_state(task="Extract requirements")
    empty_output = AgentResult(result={})

    eval_res = await evaluator.evaluate_output(task="Extract skills", step_output=empty_output, state=state)
    assert eval_res.status == "failed"
    assert "empty output" in eval_res.reason.lower()
