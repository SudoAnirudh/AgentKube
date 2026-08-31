# Kubernetes Multi-Agent AI Execution Platform (Phase 4)

Asynchronous job-based multi-agent execution platform containerized with **Docker** and orchestrated using **Kubernetes** (`kind` / `kubectl`). Demonstrates declarative Kubernetes patterns: **Pods, Deployments, Services, ConfigMaps, Secrets, Namespaces, Liveness/Readiness Probes, Resource Requests & Limits, Horizontal Pod Scaling, Self-Healing, and Zero-Downtime Rolling Updates**.

---

## 1. Architecture Overview

```text
Host System / Client
         │
         │ kubectl port-forward svc/agent-api 8009:8000 -n agent-platform
         ▼
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
│           │ (Image: app:v1.0.0 uvicorn) │    │ (Image: app:v1.0.0 uvicorn) │           │
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
│                           ┌──────────────┴──────────────┐                              │
│                           │      agent-worker Pod       │                              │
│                           │  (Image: app:v1.0.0 celery) │                              │
│                           └─────────────────────────────┘                              │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

### Core Kubernetes Orchestration Features
1. **CoreDNS Service Discovery**: Workloads resolve `agent-redis:6379` directly via internal Kubernetes DNS (`agent-redis.agent-platform.svc.cluster.local`).
2. **Health vs Readiness Probes**:
   - **`/health` (Liveness)**: Fast probe returning `200 OK {"status": "healthy"}` without dependency calls (restarts Pod if broken).
   - **`/ready` (Readiness)**: Verifies Redis connectivity (`200 OK {"status": "ready"}` or `503 Service Unavailable`). Removes unready pods from Service endpoint pools without restarting.
3. **Horizontal Scaling & Self-Healing**: Deployments maintain desired replica counts (`replicas: 2`). Deleting a pod triggers instant self-healing pod replacement.
4. **Zero-Downtime Rolling Updates**: Image tag updates (`v1.0.0` -> `v1.1.0`) perform incremental pod rollouts tracked via `kubectl rollout status`.
5. **Secret Security Note**: Kubernetes Secrets Base64 values are **encoding, NOT encryption** (`echo <data> | base64 -d`). Production deployment requires KMS envelope encryption or external secret managers (Vault / AWS Secrets Manager).

---

## 2. Quickstart with Local Kubernetes (`kind`)

### Prerequisites
- Docker Engine (v20.10+)
- `kind` (Kubernetes in Docker v0.27.0+)
- `kubectl` (v1.30+)

### Step 1: Create Kind Kubernetes Cluster
```bash
kind create cluster --name agent-cluster
```

### Step 2: Build & Load Shared Application Container Image
```bash
docker build -t ai_infra-kuber-app:v1.0.0 .
kind load docker-image ai_infra-kuber-app:v1.0.0 --name agent-cluster
```

### Step 3: Apply Kubernetes Declarative Manifests
```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/ -n agent-platform
```

### Step 4: Verify Workload Status
```bash
kubectl get pods,svc,deploy -n agent-platform
```
Expected output:
```text
NAME                                READY   STATUS    RESTARTS   AGE
pod/agent-api-7b89f84894-9xk2m     1/1     Running   0          20s
pod/agent-api-7b89f84894-m4l8n     1/1     Running   0          20s
pod/agent-redis-6d8b9d4f8-p2q9x    1/1     Running   0          20s
pod/agent-worker-5c94d9f67-r7k3w   1/1     Running   0          20s
```

### Step 5: Port-Forward API & Test Probes
```bash
kubectl port-forward svc/agent-api 8009:8000 -n agent-platform &

curl http://localhost:8009/health
# {"status":"healthy"}

curl http://localhost:8009/ready
# {"status":"ready"}
```

---

## 3. Kubernetes Operations & Debugging Guide

| Action | Command |
| --- | --- |
| **Get all resources** | `kubectl get all -n agent-platform` |
| **View cluster events** | `kubectl get events -n agent-platform --sort-by='.metadata.creationTimestamp'` |
| **View API pod logs** | `kubectl logs -l app=agent-api -n agent-platform -f` |
| **View Worker pod logs** | `kubectl logs -l app=agent-worker -n agent-platform -f` |
| **Scale worker replicas** | `kubectl scale deployment agent-worker --replicas=2 -n agent-platform` |
| **Scale API replicas** | `kubectl scale deployment agent-api --replicas=3 -n agent-platform` |
| **Test Self-Healing** | `kubectl delete pod <api-pod-name> -n agent-platform` |
| **Rollout Image Update** | `kubectl set image deployment/agent-api agent-api=ai_infra-kuber-app:v1.1.0 -n agent-platform` |
| **Check Rollout Status** | `kubectl rollout status deployment/agent-api -n agent-platform` |
| **Teardown Cluster** | `kind delete cluster --name agent-cluster` |

---

## 4. API Contract

### Liveness Probe
`GET /health`
```json
{
  "status": "healthy"
}
```

### Readiness Probe
`GET /ready`
```json
{
  "status": "ready"
}
```

### Submit Job (Asynchronous)
`POST /api/v1/agent/run`

#### Request
```json
{
  "task": "Analyze this job description and identify required technical skills.",
  "context": {
    "job_description": "We are seeking a Senior Python Developer with experience in FastAPI, PostgreSQL, and Kubernetes."
  }
}
```

#### Response — Job Accepted (202 Accepted)
```json
{
  "execution_id": "exec_a1b2c3d4e5f6",
  "status": "queued"
}
```

---

### Poll Job Status
`GET /api/v1/agent/run/{execution_id}`

#### Response — Completed (200 OK)
```json
{
  "execution_id": "exec_a1b2c3d4e5f6",
  "status": "completed",
  "task": "Analyze this job description and identify required technical skills.",
  "current_step": "step_2",
  "result": {
    "step_1": {
      "status": "success",
      "result": {
        "technical_skills": ["Python", "FastAPI", "PostgreSQL", "Kubernetes"]
      }
    }
  },
  "execution": {
    "steps_executed": 2,
    "retries": 0
  }
}
```

---

## 5. Running Automated Tests

### Host Execution
```bash
./.venv/bin/pytest -v
```

### In-Container Execution
```bash
docker compose run --rm api pytest
```

---

## 6. Execution Job States

- `QUEUED`: Task submitted via API, enqueued in Redis.
- `RUNNING`: Celery worker pod actively executing orchestrator.
- `RECOVERING`: Worker step failed evaluation, recovery engine applying feedback/reformulation.
- `COMPLETED`: Workflow finished successfully.
- `FAILED`: Execution failed (unhandled error or recovery exhausted).

---

## 7. Roadmap & Next Phase

- **Phase 5**: Managed Cloud Kubernetes Deployment (AWS EKS / Azure AKS with Terraform, Helm Charts, and Secrets Manager).
- **Phase 6**: Observability & Autoscaling (Prometheus, Grafana, and Horizontal Pod Autoscalers).
