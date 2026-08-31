import pytest
from app.models.execution import ExecutionStatus


@pytest.mark.asyncio
async def test_e2e_async_agent_workflow(async_client):
    # 1. Client submits job
    payload = {
        "task": "Analyze this job description and identify required technical skills.",
        "context": {
            "job_description": "We are seeking a Senior Python Developer with FastAPI, PostgreSQL, and Docker."
        }
    }
    submit_response = await async_client.post("/api/v1/agent/run", json=payload)
    assert submit_response.status_code == 202
    sub_data = submit_response.json()
    assert sub_data["status"] == "queued"
    execution_id = sub_data["execution_id"]

    # 2. Client queries job status (since eager execution runs synchronously in test fixture)
    status_response = await async_client.get(f"/api/v1/agent/run/{execution_id}")
    assert status_response.status_code == 200
    job_data = status_response.json()

    assert job_data["execution_id"] == execution_id
    assert job_data["status"] == ExecutionStatus.COMPLETED.value
    assert job_data["result"] is not None
    assert "step_1" in job_data["result"]
    assert job_data["execution"]["steps_executed"] >= 1
