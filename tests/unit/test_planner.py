import pytest
from app.agents.planner import PlannerAgent
from app.core.exceptions import InvalidPlanError
from app.core.state import StateManager
from app.llm.mock import MockLLMClient
from app.models.execution import ExecutionPlan, PlanStep


@pytest.mark.asyncio
async def test_planner_generates_valid_plan():
    mock_llm = MockLLMClient(mode="success")
    planner = PlannerAgent(llm_client=mock_llm)
    state_mgr = StateManager()
    state = state_mgr.create_state(task="Analyze job description")

    result = await planner.execute(task=state.task, context={}, state=state)
    assert result.status == "success"
    plan = ExecutionPlan.model_validate(result.result)
    assert len(plan.steps) >= 1
    assert plan.steps[0].id == "step_1"
    assert plan.steps[0].agent == "researcher"


@pytest.mark.asyncio
async def test_planner_validates_empty_goal():
    planner = PlannerAgent(llm_client=MockLLMClient())
    invalid_plan = ExecutionPlan(goal="", steps=[PlanStep(id="step_1", agent="researcher", task="task")])
    with pytest.raises(InvalidPlanError, match="goal cannot be empty"):
        planner.validate_plan(invalid_plan)


@pytest.mark.asyncio
async def test_planner_validates_duplicate_step_ids():
    planner = PlannerAgent(llm_client=MockLLMClient())
    invalid_plan = ExecutionPlan(
        goal="Valid Goal",
        steps=[
            PlanStep(id="step_1", agent="researcher", task="task 1"),
            PlanStep(id="step_1", agent="researcher", task="task 2"),
        ],
    )
    with pytest.raises(InvalidPlanError, match="Duplicate step ID"):
        planner.validate_plan(invalid_plan)
