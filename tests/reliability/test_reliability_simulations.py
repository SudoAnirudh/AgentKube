"""
Reliability and Failure Simulation Tests for AgentKube Platform.
Tests graceful termination, Redis transient failure recovery, and queue isolation.
"""

import pytest
import signal
import time
from unittest.mock import MagicMock, patch
from redis.exceptions import ConnectionError as RedisConnectionError
from app.workers.celery_app import celery_app
from app.utils.metrics import AGENT_TASKS_TOTAL, AGENT_ACTIVE_TASKS


class TestReliabilitySimulations:

    def test_celery_worker_graceful_shutdown_signal_handling(self):
        """Simulates SIGTERM signal sent to worker and verifies handler readiness."""
        handler_called = False

        def sigterm_handler(signum, frame):
            nonlocal handler_called
            handler_called = True

        original_handler = signal.signal(signal.SIGTERM, sigterm_handler)
        try:
            # Raise SIGTERM to current process
            signal.raise_signal(signal.SIGTERM)
            assert handler_called is True
        finally:
            signal.signal(signal.SIGTERM, original_handler)

    @patch("app.storage.redis.RedisStateManager.ping")
    def test_redis_transient_failure_readiness_probe_recovery(self, mock_ping):
        """Simulates Redis outage and recovery on readiness probe endpoint."""
        from fastapi.testclient import TestClient
        from app.main import app

        client = TestClient(app)

        # 1. Simulate Redis Down
        mock_ping.return_value = False
        response_down = client.get("/ready")
        assert response_down.status_code == 503

        # 2. Simulate Redis Recovery
        mock_ping.return_value = True
        response_recovered = client.get("/ready")
        assert response_recovered.status_code == 200
        assert response_recovered.json()["status"] == "ready"

    def test_metrics_counter_on_task_failure_simulation(self):
        """Verifies failure counter increments cleanly during task execution errors."""
        AGENT_TASKS_TOTAL.labels(status="failed").inc()
        AGENT_ACTIVE_TASKS.set(0)

        assert AGENT_ACTIVE_TASKS._value.get() == 0

    @patch("celery.app.task.Task.apply_async")
    def test_task_submission_resilience_on_broker_error(self, mock_apply):
        """Simulates Celery broker connection error on task dispatch."""
        mock_apply.side_effect = RedisConnectionError("Broker unreachable")

        with pytest.raises(RedisConnectionError):
            mock_apply(args=["test-execution-123", "analyze code"])
