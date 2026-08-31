import pytest
from app.core.orchestrator import Orchestrator
from app.llm.mock import MockLLMClient
from app.models.execution import ErrorCategory, ExecutionStatus
from app.utils.config import Settings


@pytest.mark.asyncio
async def test_scenario_1_successful_execution():
    mock_llm = MockLLMClient(mode="success")
    settings = Settings(LLM_PROVIDER="mock", MAX_RETRIES=2, AGENT_TIMEOUT_SECONDS=5.0)
    orchestrator = Orchestrator(llm_client=mock_llm, settings=settings)

    state = await orchestrator.execute_task(task="Analyze job description")
    assert state.status == ExecutionStatus.COMPLETED
    assert len(state.completed_steps) == 2
    assert state.total_retries() == 0


@pytest.mark.asyncio
async def test_scenario_3_successful_recovery():
    # mode="fail_eval_once" fails step_1 evaluation on first attempt, passes on retry
    mock_llm = MockLLMClient(mode="fail_eval_once")
    settings = Settings(LLM_PROVIDER="mock", MAX_RETRIES=2, AGENT_TIMEOUT_SECONDS=5.0)
    orchestrator = Orchestrator(llm_client=mock_llm, settings=settings)

    state = await orchestrator.execute_task(task="Analyze job description")
    assert state.status == ExecutionStatus.COMPLETED
    assert len(state.completed_steps) == 2
    assert state.total_retries() == 1


@pytest.mark.asyncio
async def test_scenario_4_recovery_exhausted():
    # mode="fail_eval_always" fails evaluation continuously until retries are exhausted
    mock_llm = MockLLMClient(mode="fail_eval_always")
    settings = Settings(LLM_PROVIDER="mock", MAX_RETRIES=2, AGENT_TIMEOUT_SECONDS=5.0)
    orchestrator = Orchestrator(llm_client=mock_llm, settings=settings)

    state = await orchestrator.execute_task(task="Analyze job description")
    assert state.status == ExecutionStatus.FAILED
    assert len(state.errors) > 0
    last_err = state.errors[-1]
    assert last_err.code == ErrorCategory.RECOVERY_EXHAUSTED


@pytest.mark.asyncio
async def test_scenario_5_malformed_llm_output():
    mock_llm = MockLLMClient(mode="malformed")
    settings = Settings(LLM_PROVIDER="mock", MAX_RETRIES=2, AGENT_TIMEOUT_SECONDS=5.0)
    orchestrator = Orchestrator(llm_client=mock_llm, settings=settings)

    state = await orchestrator.execute_task(task="Analyze job description")
    assert state.status == ExecutionStatus.FAILED
    assert len(state.errors) > 0
    last_err = state.errors[-1]
    assert last_err.code == ErrorCategory.INVALID_LLM_OUTPUT


@pytest.mark.asyncio
async def test_scenario_6_operation_timeout():
    mock_llm = MockLLMClient(mode="timeout")
    settings = Settings(LLM_PROVIDER="mock", MAX_RETRIES=2, AGENT_TIMEOUT_SECONDS=5.0)
    orchestrator = Orchestrator(llm_client=mock_llm, settings=settings)

    state = await orchestrator.execute_task(task="Analyze job description")
    assert state.status == ExecutionStatus.FAILED
    assert len(state.errors) > 0
    # Planning operation times out leading to failure
    last_err = state.errors[-1]
    assert last_err.code == ErrorCategory.TIMEOUT
