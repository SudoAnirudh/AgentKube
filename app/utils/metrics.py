import time
from fastapi import Request, Response
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)

# Prometheus Metrics Definitions
HTTP_REQUESTS_TOTAL = Counter(
    "agent_http_requests_total",
    "Total count of HTTP requests received",
    ["method", "endpoint", "status"],
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "agent_http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)

AGENT_TASKS_TOTAL = Counter(
    "agent_tasks_total",
    "Total count of agent task execution state transitions",
    ["status"],
)

AGENT_TASK_DURATION_SECONDS = Histogram(
    "agent_task_duration_seconds",
    "Agent task execution duration in seconds",
    buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0],
)

AGENT_ACTIVE_TASKS = Gauge(
    "agent_active_tasks",
    "Number of agent tasks currently actively executing in worker",
)


async def prometheus_metrics_middleware(request: Request, call_next):
    """FastAPI Middleware to track HTTP request rates, status codes, and latencies."""
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time

    # Normalize endpoint path for Prometheus metrics to prevent cardinality explosion
    endpoint = request.url.path
    if endpoint.startswith("/api/v1/agent/run/"):
        endpoint = "/api/v1/agent/run/{execution_id}"

    HTTP_REQUESTS_TOTAL.labels(
        method=request.method,
        endpoint=endpoint,
        status=str(response.status_code),
    ).inc()

    HTTP_REQUEST_DURATION_SECONDS.labels(
        method=request.method,
        endpoint=endpoint,
    ).observe(duration)

    return response


def get_metrics_response() -> Response:
    """Return raw Prometheus metrics payload for scrapers."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
