# Kubernetes Multi-Agent AI Execution Platform (Phase 8)

Asynchronous job-based multi-agent execution platform containerized with **Docker**, orchestrated using **Kubernetes** (`kind` / `kubectl`), packaged with **Helm** (v3.17+), provisioned with **Terraform IaC** for Cloud Kubernetes (AWS EKS), automated with **GitHub Actions CI/CD** and **Argo CD GitOps**, and monitored with **Prometheus, Grafana, Alertmanager & Structured Telemetry**. Demonstrates production observability: **Application & HTTP Metrics (`GET /metrics`), JSON Structured Logging with `execution_id` Correlation IDs, Prometheus Scraping, Alertmanager PromQL Threshold Rules, Grafana Operational Dashboards, and K8s State Monitoring**.

---

## 1. Full Production Telemetry & Observability Architecture

```text
                         Developer / CI/CD
                                 │
                                 ▼
                       AWS EKS (agent-platform)
                                 │
        ┌────────────────────────┼────────────────────────┐
        │                        │                        │
        ▼                        ▼                        ▼
    agent-api               Celery Worker             agent-redis
 (HTTP Metrics)            (Task Metrics)           (Broker/State)
        │                        │                        │
        └────────────────────────┼────────────────────────┘
                                 │
                        Prometheus Scraper
                          (GET /metrics)
                                 │
               ┌─────────────────┴─────────────────┐
               ▼                                   ▼
      Grafana Dashboards                  Alertmanager Rules
 ┌───────────────────────────┐           ┌───────────────────────────┐
 │ 1. Platform Overview      │           │ 1. WorkerUnavailable      │
 │ 2. API Performance        │           │ 2. ApiReplicasUnavailable │
 │ 3. Agent Execution        │           │ 3. HighTaskFailureRate    │
 │ 4. K8s Infrastructure     │           │ 4. RedisUnavailable       │
 └───────────────────────────┘           └───────────────────────────┘
```

---

## 2. Helm, Terraform, GitOps & Observability Project Structure

```text
.
├── .github/
│   └── workflows/
│       ├── ci.yaml             # CI pipeline: Pytest, Helm lint, Helm template
│       └── build.yaml          # Build pipeline: AWS OIDC, Docker build, Trivy scan, ECR push
├── argocd/
│   ├── project.yaml            # Argo CD AppProject definition
│   ├── application-dev.yaml    # Argo CD Application (Dev environment sync)
│   ├── application-prod.yaml   # Argo CD Application (Prod environment sync)
│   └── application-observability.yaml # Argo CD Application (Monitoring stack sync)
├── observability/
│   ├── prometheus/
│   │   └── prometheus.yaml     # Prometheus scrape configuration
│   ├── alertmanager/
│   │   └── rules.yaml          # Alertmanager alert rules (PromQL)
│   └── dashboards/
│       ├── platform-overview.json  # Grafana Platform Overview dashboard
│       ├── api-performance.json    # Grafana API Performance dashboard
│       ├── agent-execution.json    # Grafana Agent Execution dashboard
│       └── k8s-infrastructure.json # Grafana K8s Infrastructure dashboard
├── terraform/                  # Infrastructure as Code (AWS EKS)
├── charts/
│   └── agent-platform/        # Parameterized Helm Chart
└── docs/learning/
    ├── task-06-cloud-kubernetes-infrastructure.md # Task 06 Learning Document
    ├── task-07-cicd-gitops-agent-delivery.md      # Task 07 Learning Document
    └── task-08-observability-monitoring.md        # Task 08 Learning Document
```

---

## 3. Quickstart: Metrics, Dashboards & Alerting

### Prerequisites
- Docker Engine (v20.10+)
- `kind` (v0.27.0+)
- `kubectl` (v1.37.0+)
- `helm` (v3.17.1+)

### Step 1: Run Pytest Test Suite (28 Passed)
```bash
./.venv/bin/pytest -v
```

### Step 2: Test Local Prometheus Metrics Endpoint
```bash
curl -s http://localhost:8000/metrics | grep agent_
```

### Step 3: Simulate Worker Outage & Alertmanager Firing
```bash
# 1. Scale Celery worker to 0 replicas
kubectl scale deploy/agent-worker --replicas=0 -n agent-platform

# 2. Submit agent task to queue
curl -X POST http://localhost:8000/api/v1/agent/run -H "Content-Type: application/json" -d '{"task":"test"}'

# 3. Observe Prometheus & Alertmanager firing WorkerUnavailable alert!

# 4. Restore Celery worker to 2 replicas
kubectl scale deploy/agent-worker --replicas=2 -n agent-platform
```

---

## 4. Operational Telemetry Command Summary

| Action | Command |
| --- | --- |
| **Scrape Prometheus Metrics** | `curl -s http://localhost:8000/metrics` |
| **Run Pytest Suite** | `./.venv/bin/pytest` |
| **Lint Helm Chart** | `helm lint ./charts/agent-platform` |
| **Apply Observability GitOps Manifests** | `kubectl apply -f argocd/application-observability.yaml` |
| **Simulate Worker Outage** | `kubectl scale deploy/agent-worker --replicas=0 -n agent-platform` |
| **Restore Worker** | `kubectl scale deploy/agent-worker --replicas=2 -n agent-platform` |

---

## 5. API & Telemetry Contract

### Liveness Probe
`GET /health` -> `{"status": "healthy"}`

### Readiness Probe
`GET /ready` -> `{"status": "ready"}`

### Prometheus Metrics Endpoint
`GET /metrics` -> Raw Prometheus formatted TSDB telemetry (`agent_http_requests_total`, `agent_tasks_total`, `agent_active_tasks`, `agent_task_duration_seconds`).

### Submit Job (Asynchronous)
`POST /api/v1/agent/run` -> `202 Accepted {"execution_id": "exec_3523704bfe38", "status": "queued"}`

---

## 6. Running Automated Tests

```bash
# Run 28/28 Pytest test suite
./.venv/bin/pytest -v
```

---

## 7. Roadmap & Next Phase

- **Phase 8 (Completed)**: Observability, Monitoring & Production Telemetry (Prometheus Metrics, JSON Structured Logging, Grafana Dashboards, Alertmanager Rules).
- **Phase 9 (Next)**: Autoscaling, Performance Optimization & Production Reliability (Horizontal Pod Autoscalers, Load Testing, SLA/SLO Enforcement).
