import pytest


@pytest.mark.asyncio
async def test_health_endpoint(async_client):
    response = await async_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data == {"status": "healthy"}


@pytest.mark.asyncio
async def test_readiness_endpoint(async_client):
    response = await async_client.get("/ready")
    assert response.status_code == 200
    data = response.json()
    assert data == {"status": "ready"}


@pytest.mark.asyncio
async def test_prometheus_metrics_endpoint(async_client):
    response = await async_client.get("/metrics")
    assert response.status_code == 200
    content = response.text
    assert "agent_http_requests_total" in content
    assert "agent_tasks_total" in content


@pytest.mark.asyncio
async def test_submit_agent_task_returns_202(async_client):
    payload = {
        "task": "Analyze this job description and identify required technical skills.",
        "context": {
            "job_description": "Senior Python Developer with FastAPI and Docker experience."
        }
    }
    response = await async_client.post("/api/v1/agent/run", json=payload)
    assert response.status_code == 202
    data = response.json()
    assert data["status"] == "queued"
    assert "execution_id" in data


@pytest.mark.asyncio
async def test_get_job_status(async_client):
    payload = {"task": "Analyze job posting", "context": {}}
    sub_resp = await async_client.post("/api/v1/agent/run", json=payload)
    assert sub_resp.status_code == 202
    exec_id = sub_resp.json()["execution_id"]

    status_resp = await async_client.get(f"/api/v1/agent/run/{exec_id}")
    assert status_resp.status_code == 200
    status_data = status_resp.json()
    assert status_data["execution_id"] == exec_id
    assert status_data["status"] in ("queued", "running", "completed")


@pytest.mark.asyncio
async def test_get_unknown_job_returns_404(async_client):
    response = await async_client.get("/api/v1/agent/run/exec_non_existent_999")
    assert response.status_code == 404
    data = response.json()
    assert data["error"]["code"] == "EXECUTION_NOT_FOUND"


@pytest.mark.asyncio
async def test_run_agent_empty_task_returns_400(async_client):
    payload = {"task": "", "context": {}}
    response = await async_client.post("/api/v1/agent/run", json=payload)
    assert response.status_code == 400
