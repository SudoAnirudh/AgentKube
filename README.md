# Kubernetes Multi-Agent AI Execution Platform (Phase 9)

Asynchronous job-based multi-agent execution platform containerized with **Docker**, orchestrated using **Kubernetes** (`kind` / `kubectl`), packaged with **Helm** (v3.17+), provisioned with **Terraform IaC** for Cloud Kubernetes (AWS EKS), automated with **GitHub Actions CI/CD** and **Argo CD GitOps**, monitored with **Prometheus & Grafana**, and hardened for production with **Resource Management, Horizontal Pod Autoscaling (HPA), PodDisruptionBudgets (PDB), NetworkPolicy Isolation, Non-Root Container SecurityContext, RBAC, and Disaster Recovery**.

---

## 1. Hardened Production Architecture

```text
                         Developer / CI/CD / GitOps
                                     │
                                     ▼
                           AWS EKS (agent-platform)
                                     │
            ┌────────────────────────┼────────────────────────┐
            │                        │                        │
            ▼                        ▼                        ▼
        agent-api               Celery Worker             agent-redis
    (HPA: 3 → 8 Pods)        (HPA: 2 → 8 Pods)       (Isolated Port 6379)
  [ PDB: minAvailable 2 ]  [ PDB: minAvailable 1 ]  [ NetworkPolicy Gated ]
  [ Non-Root / ReadOnly ]  [ Non-Root / ReadOnly ]  [ Non-Root / ReadOnly ]
            │                        │                        │
            └────────────────────────┼────────────────────────┘
                                     │
                            Prometheus Scraper
                              (GET /metrics)
                                     │
                   ┌─────────────────┴─────────────────┐
                   ▼                                   ▼
          Grafana Dashboards                  Alertmanager Rules
```

---

## 2. Hardening & Security Features

- **Resource Limits & QoS**: CPU requests/limits (`250m` / `1000m`) & Memory requests/limits (`256Mi` / `1Gi`) preventing OOMKilled host node panics.
- **Horizontal Pod Autoscaling (HPA)**: Dynamic scaling using `autoscaling/v2` based on CPU (70%) and Memory (80%) thresholds.
- **PodDisruptionBudget (PDB)**: Guaranteed availability during node drains or voluntary cluster maintenance.
- **NetworkPolicy Isolation**: Strict L3/L4 container isolation blocking unauthenticated external ingress into Redis.
- **SecurityContext & Least-Privilege RBAC**: Container execution as Non-Root UID `1000`, `readOnlyRootFilesystem: true` with `/tmp` `emptyDir` volume mounts, dropped kernel capabilities (`ALL`), and dedicated ServiceAccounts.
- **Disaster Recovery Playbook**: Documented RTO (<15 min) and RPO (<5 min) operational recovery playbooks in `docs/disaster-recovery.md`.

---

## 3. Project Structure

```text
.
├── .github/
│   └── workflows/             # GitHub Actions CI/CD & Security Scan
├── argocd/                     # Argo CD GitOps Application Manifests
├── charts/
│   └── agent-platform/        # Parameterized Helm Chart
│       ├── templates/
│       │   ├── api-hpa.yaml       # API HorizontalPodAutoscaler
│       │   ├── worker-hpa.yaml    # Worker HorizontalPodAutoscaler
│       │   ├── api-pdb.yaml       # API PodDisruptionBudget
│       │   ├── worker-pdb.yaml    # Worker PodDisruptionBudget
│       │   ├── network-policy.yaml# NetworkPolicy rules
│       │   └── serviceaccount.yaml# Dedicated RBAC ServiceAccounts
│       ├── values.yaml        # Default values
│       └── values-prod.yaml   # Hardened production overrides
├── observability/             # Prometheus, Alertmanager, Grafana Dashboards
├── scripts/
│   └── run_failure_simulations.sh # Controlled failure simulation script
├── tests/
│   └── reliability/           # Reliability & resilience test suite
└── docs/
    ├── production-hardening.md # Hardening & QoS documentation
    ├── disaster-recovery.md   # Disaster recovery playbook
    └── learning/              # Task learning markdown documents
```

---

## 4. Quickstart & Verification

### Step 1: Run Pytest Test Suite (32 Passed)
```bash
./.venv/bin/pytest -v
```

### Step 2: Lint and Render Hardened Helm Chart
```bash
helm lint ./charts/agent-platform
helm template agentkube ./charts/agent-platform -f ./charts/agent-platform/values-prod.yaml
```

### Step 3: Run Controlled Reliability & Failure Simulations
```bash
DRY_RUN=true ./scripts/run_failure_simulations.sh
```

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

## 6. Phase Status

- **Phase 9 (Completed)**: Production Hardening & Reliability (Resource Requests/Limits, HPA, PDB, NetworkPolicies, Non-Root Container SecurityContext, RBAC, Disaster Recovery).
