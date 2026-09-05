"""
Integration tests for AgentKube Web UI & API integration.
"""

import os
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestUIIntegration:

    def test_ui_static_files_exist_in_repository(self):
        """Verifies Web UI static files are present in ui/ directory."""
        ui_dir = os.path.join(os.path.dirname(__file__), "../../ui")
        assert os.path.exists(os.path.join(ui_dir, "index.html"))
        assert os.path.exists(os.path.join(ui_dir, "style.css"))
        assert os.path.exists(os.path.join(ui_dir, "app.js"))
        assert os.path.exists(os.path.join(ui_dir, "nginx.conf"))
        assert os.path.exists(os.path.join(ui_dir, "Dockerfile"))

    def test_api_health_endpoint_accessible_for_ui(self):
        """Verifies UI can query API health endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_api_task_submission_and_status_query_flow(self):
        """Verifies UI end-to-end task submission and status retrieval contract."""
        # 1. Submit task
        sub_resp = client.post(
            "/api/v1/agent/run",
            json={"task": "UI Integration Verification Test"}
        )
        assert sub_resp.status_code == 202
        exec_id = sub_resp.json()["execution_id"]
        assert exec_id.startswith("exec_")

        # 2. Query Status
        status_resp = client.get(f"/api/v1/agent/run/{exec_id}")
        assert status_resp.status_code == 200
        assert status_resp.json()["execution_id"] == exec_id
        assert status_resp.json()["status"] in ["queued", "running", "completed", "failed"]
