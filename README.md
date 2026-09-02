# Kubernetes Multi-Agent AI Execution Platform (Phase 5)

Asynchronous job-based multi-agent execution platform containerized with **Docker**, orchestrated using **Kubernetes** (`kind` / `kubectl`), and packaged with **Helm** (v3.17+). Demonstrates declarative Kubernetes patterns and Helm package management: **Charts, Templating, Values Hierarchy (Dev, Staging, Prod), Release Lifecycle (Lint, Template, Install, Upgrade, Rollback), Probes, and Resource Management**.

---

## 1. Architecture & Helm Target Structure

```text
                                  Helm Chart (charts/agent-platform)
                                                  │
                         ┌────────────────────────┴────────────────────────┐
                         │                                                 │
                     Templates                                          Values
        (charts/agent-platform/templates/)                   (values-dev.yaml, values-prod.yaml)
                         │                                                 │
                         └────────────────────────┬────────────────────────┘
                                                  ↓
                                        Kubernetes Manifests
                                                  ↓
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ Kubernetes Cluster (kind: agent-cluster)                                               │
│ Namespace: agent-platform                                                              │
│                                                                                        │
│   ┌────────────────────────────────────────────────────────────────────────────────┐   │
│   │ agent-api Service (ClusterIP: 8000)                                            │   │
│   └──────────────────────┬──────────────────────────────────┬──────────────────────┘   │
│                          │                                  │                          │
│                          ▼                                  ▼                          │
│           ┌─────────────────────────────┐    ┌─────────────────────────────┐           │
│           │      agent-api Pod 1        │    │      agent-api Pod 2        │           │
│           │ (Image: app:v1.1.0 uvicorn) │    │ (Image: app:v1.1.0 uvicorn) │           │
│           └──────────────┬──────────────┘    └──────────────┬──────────────┘           │
│                          │                                  │                          │
│                          │ redis://agent-redis:6379/2       │                          │
│                          ▼                                  ▼                          │
│   ┌────────────────────────────────────────────────────────────────────────────────┐   │
│   │ agent-redis Service (ClusterIP: 6379)                                          │   │
│   └──────────────────────────────────────┬─────────────────────────────────────────┘   │
│                                          │                                             │
│                                          ▼                                             │
│                           ┌─────────────────────────────┐                              │
│                           │       agent-redis Pod       │                              │
│                           │       (Redis 7 Alpine)      │                              │
│                           └──────────────▲──────────────┘                              │
│                                          │                                             │
│                                          │ redis://agent-redis:6379/0 (Broker)         │
│                                          │ redis://agent-redis:6379/2 (State)          │
│                                          │                                             │
│                                          ▼                                             │
│                           ┌─────────────────────────────┐                              │
│                           │      agent-worker Pod       │                              │
│                           │  (Image: app:v1.1.0 celery) │                              │
│                           └─────────────────────────────┘                              │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Helm Chart Package Structure

```text
charts/
└── agent-platform/
    ├── Chart.yaml              # Chart metadata (version: 0.1.0, appVersion: 1.1.0)
    ├── values.yaml             # Default base configuration
    ├── values-dev.yaml         # Development overrides (api: 1, worker: 1, DEBUG)
    ├── values-staging.yaml     # Staging overrides (api: 2, worker: 2, INFO)
    ├── values-prod.yaml        # Production overrides (api: 3, worker: 2, WARNING)
    └── templates/
        ├── configmap.yaml      # Parameterized ConfigMap
        ├── secret.yaml         # Parameterized Secret (Base64 encoding)
        ├── redis-deployment.yaml# Redis 7 Alpine Deployment
        ├── redis-service.yaml   # Redis ClusterIP Service
        ├── api-deployment.yaml  # FastAPI Deployment with probes
        ├── api-service.yaml    # API ClusterIP Service
        └── worker-deployment.yaml # Celery worker Deployment
```

---

## 3. Quickstart & Helm Lifecycle Operations

### Prerequisites
- Docker Engine (v20.10+)
- `kind` (v0.27.0+)
- `kubectl` (v1.30+)
- `helm` (v3.17+)

### Step 1: Lint Chart
```bash
helm lint ./charts/agent-platform
```

### Step 2: Render Templates (Local Dry-Run)
```bash
helm template agent-platform ./charts/agent-platform -f charts/agent-platform/values-dev.yaml
```

### Step 3: Install Release (Development Environment)
```bash
helm install agent-platform ./charts/agent-platform \
  -f charts/agent-platform/values-dev.yaml \
  -n agent-platform \
  --create-namespace \
  --set-string secrets.llmApiKey="$LLM_API_KEY"
```

### Step 4: Verify Deployment & Health Probes
```bash
kubectl get pods,svc,deploy -n agent-platform

# Port-forward API service
kubectl port-forward svc/agent-api 8009:8000 -n agent-platform &

# Test probes
curl http://localhost:8009/health # {"status":"healthy"}
curl http://localhost:8009/ready  # {"status":"ready"}
```

### Step 5: Upgrade Release (Staging Environment)
```bash
helm upgrade agent-platform ./charts/agent-platform \
  -f charts/agent-platform/values-staging.yaml \
  -n agent-platform
```

### Step 6: View Release History
```bash
helm history agent-platform -n agent-platform
```

### Step 7: Rollback Release
```bash
helm rollback agent-platform 1 -n agent-platform
```

### Step 8: Uninstall Release
```bash
helm uninstall agent-platform -n agent-platform
```

---

## 4. Helm & Kubernetes Operations Guide

| Action | Command |
| --- | --- |
| **Lint Chart** | `helm lint ./charts/agent-platform` |
| **Render Dev YAML** | `helm template agent-platform ./charts/agent-platform -f charts/agent-platform/values-dev.yaml` |
| **Render Prod YAML** | `helm template agent-platform ./charts/agent-platform -f charts/agent-platform/values-prod.yaml` |
| **Install Dev** | `helm install agent-platform ./charts/agent-platform -f charts/agent-platform/values-dev.yaml -n agent-platform --create-namespace` |
| **Upgrade Staging** | `helm upgrade agent-platform ./charts/agent-platform -f charts/agent-platform/values-staging.yaml -n agent-platform` |
| **View Release History** | `helm history agent-platform -n agent-platform` |
| **Rollback to Revision 1** | `helm rollback agent-platform 1 -n agent-platform` |
| **Uninstall Release** | `helm uninstall agent-platform -n agent-platform` |

---

## 5. API Contract

### Liveness Probe
`GET /health` -> `{"status": "healthy"}`

### Readiness Probe
`GET /ready` -> `{"status": "ready"}`

### Submit Job (Asynchronous)
`POST /api/v1/agent/run`
```json
{
  "task": "Analyze job description and extract required skills.",
  "context": {}
}
```
Response: `202 Accepted {"execution_id": "exec_3523704bfe38", "status": "queued"}`

### Poll Job Status
`GET /api/v1/agent/run/{execution_id}` -> `200 OK {"status": "completed", ...}`

---

## 6. Running Automated Tests

```bash
# Run 27/27 Pytest test suite
./.venv/bin/pytest -v
```

---

## 7. Roadmap & Next Phase

- **Phase 6**: Managed Cloud Kubernetes Deployment (AWS EKS / Azure AKS with Terraform, Cloud LoadBalancers, and External Secrets Manager).
- **Phase 7**: Observability & Autoscaling (Prometheus, Grafana, and Horizontal Pod Autoscalers).
