# Kubernetes Multi-Agent AI Execution Platform (Phase 6)

Asynchronous job-based multi-agent execution platform containerized with **Docker**, orchestrated using **Kubernetes** (`kind` / `kubectl`), packaged with **Helm** (v3.17+), and provisioned with **Terraform IaC** for Cloud Kubernetes (AWS EKS). Demonstrates production cloud architecture: **Infrastructure as Code (Terraform), Cloud Subnet Routing (Public/Private NAT), External Secrets Operator (ESO), NGINX Ingress Controller with TLS Termination, Health Probes, and Values Hierarchy (Dev, Staging, Prod)**.

---

## 1. Architecture & Production Cloud Structure

```text
                                  Public Internet
                                         │
                                       HTTPS
                                         ▼
                               ┌──────────────────┐
                               │ Cloud ELB / ALB  │
                               └────────┬─────────┘
                                        │
                                        ▼
                               ┌──────────────────┐
                               │  NGINX Ingress   │
                               │  (TLS Terminated)│
                               └────────┬─────────┘
                                        │ HTTP
                                        ▼
 ┌────────────────────────────────────────────────────────────────────────────────────────┐
 │ AWS EKS Cluster (agentkube-cluster)                                                    │
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

## 2. Helm & Terraform Project Structure

```text
.
├── terraform/                  # Infrastructure as Code (AWS EKS)
│   ├── versions.tf             # Terraform & AWS/K8s/Helm provider versions
│   ├── providers.tf            # AWS, K8s, Helm provider definitions
│   ├── variables.tf            # Region, environment, EKS cluster inputs
│   ├── networking.tf           # VPC (10.0.0.0/16), subnets, IGW, NAT GW
│   ├── main.tf                 # EKS Cluster, node groups, IAM OIDC provider
│   ├── outputs.tf              # EKS endpoint, SG ID, OIDC ARN, kubeconfig
│   ├── kubernetes.tf           # Namespace agent-platform & IRSA ServiceAccount
│   └── README.md               # Terraform deployment & state management guide
├── charts/
│   └── agent-platform/
│       ├── Chart.yaml          # Chart metadata (version: 0.1.0, appVersion: 1.1.0)
│       ├── values.yaml         # Base default values (Ingress/Secrets disabled for local dev)
│       ├── values-dev.yaml     # Dev overrides (api: 1, worker: 1)
│       ├── values-staging.yaml # Staging overrides (api: 2, worker: 2)
│       ├── values-prod.yaml    # Production overrides (api: 3, worker: 2, Ingress & ExternalSecrets enabled)
│       └── templates/
│           ├── configmap.yaml      # Parameterized ConfigMap
│           ├── secret.yaml         # Local Secret (Base64 encoding)
│           ├── external-secret.yaml# ExternalSecret (AWS Secrets Manager integration)
│           ├── ingress.yaml        # NGINX Ingress template with TLS
│           ├── redis-deployment.yaml# Redis 7 Alpine Deployment
│           ├── redis-service.yaml   # Redis ClusterIP Service
│           ├── api-deployment.yaml  # FastAPI Deployment with probes
│           ├── api-service.yaml    # API ClusterIP Service
│           └── worker-deployment.yaml # Celery worker Deployment
└── docs/learning/
    └── task-06-cloud-kubernetes-infrastructure.md # Task 06 Learning Document
```

---

## 3. Quickstart: Terraform & Helm Operations

### Prerequisites
- Docker Engine (v20.10+)
- `kind` (v0.27.0+)
- `kubectl` (v1.37.0+)
- `helm` (v3.17.1+)
- `terraform` (v1.9.8+)

### Step 1: Validate Terraform IaC
```bash
export PATH="$HOME/.local/bin:$PATH"
cd terraform
terraform fmt -check
terraform validate
```

### Step 2: Provision Cloud EKS Cluster (AWS)
```bash
cd terraform
terraform init
terraform plan -out=tfplan
terraform apply tfplan

# Configure kubectl context for EKS
aws eks update-kubeconfig --region us-east-1 --name agentkube-cluster
```

### Step 3: Lint & Render Production Helm Manifests
```bash
helm lint ./charts/agent-platform

# Render production manifests with Ingress and ExternalSecrets
helm template agent-platform ./charts/agent-platform -f charts/agent-platform/values-prod.yaml
```

### Step 4: Deploy Production Release
```bash
helm upgrade --install agent-platform ./charts/agent-platform \
  -f charts/agent-platform/values-prod.yaml \
  -n agent-platform \
  --create-namespace
```

---

## 4. Helm & Infrastructure Operations Summary

| Action | Command |
| --- | --- |
| **Validate Terraform** | `cd terraform && terraform fmt -check && terraform validate` |
| **Lint Helm Chart** | `helm lint ./charts/agent-platform` |
| **Render Dev Manifests** | `helm template agent-platform ./charts/agent-platform -f charts/agent-platform/values-dev.yaml` |
| **Render Prod Manifests** | `helm template agent-platform ./charts/agent-platform -f charts/agent-platform/values-prod.yaml` |
| **Install Local Dev Release** | `helm install agent-platform ./charts/agent-platform -f charts/agent-platform/values-dev.yaml -n agent-platform --create-namespace` |
| **Install Prod Release** | `helm upgrade --install agent-platform ./charts/agent-platform -f charts/agent-platform/values-prod.yaml -n agent-platform --create-namespace` |
| **Rollback Release** | `helm rollback agent-platform 1 -n agent-platform` |

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

- **Phase 6 (Completed)**: Cloud Kubernetes Infrastructure & Production Hardening (AWS EKS Terraform IaC, External Secrets Operator, NGINX Ingress & TLS).
- **Phase 7 (Next)**: Observability & Autoscaling (Prometheus, Grafana, and Horizontal Pod Autoscalers).

