# Kubernetes Multi-Agent AI Execution Platform (Phase 7)

Asynchronous job-based multi-agent execution platform containerized with **Docker**, orchestrated using **Kubernetes** (`kind` / `kubectl`), packaged with **Helm** (v3.17+), provisioned with **Terraform IaC** for Cloud Kubernetes (AWS EKS), and automated with **GitHub Actions CI/CD** and **Argo CD GitOps**. Demonstrates production cloud delivery: **Automated Testing, Docker Build & Trivy Vulnerability Scanning, Amazon ECR Registry Publishing, AWS OIDC Passwordless Authentication, and Argo CD GitOps Continuous Reconciliation**.

---

## 1. Automated CI/CD & GitOps Delivery Architecture

```text
                       Developer
                           │
                           │ git push
                           ▼
                    ┌─────────────┐
                    │   GitHub    │
                    └──────┬──────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │ GitHub Actions  │
                  │                 │
                  │ Tests (Pytest)  │
                  │ Lint (Helm)     │
                  │ Helm Validate   │
                  │ Docker Build    │
                  │ Security Scan   │
                  └────────┬────────┘
                           │
                           ▼
                     ┌──────────┐
                     │   ECR    │
                     │ Image    │
                     └────┬─────┘
                          │
                          ▼
                 Deployment Config
                      in Git
                          │
                          ▼
                     ┌─────────┐
                     │ Argo CD │
                     └────┬────┘
                          │
                     GitOps Sync
                          │
                          ▼
                 ┌──────────────────┐
                 │      AWS EKS     │
                 │                  │
                 │  NGINX Ingress   │
                 │        │         │
                 │   agent-api      │
                 │        │         │
                 │   Celery Worker  │
                 │        │         │
                 │      Redis       │
                 └──────────────────┘
                          │
                          ▼
                 External Secrets
                          │
                          ▼
                  AWS Secrets Manager
```

---

## 2. Helm, Terraform & GitOps Project Structure

```text
.
├── .github/
│   └── workflows/
│       ├── ci.yaml             # CI pipeline: Pytest, Helm lint, Helm template
│       └── build.yaml          # Build pipeline: AWS OIDC, Docker build, Trivy scan, ECR push
├── argocd/
│   ├── project.yaml            # Argo CD AppProject definition
│   ├── application-dev.yaml    # Argo CD Application (Dev environment sync)
│   └── application-prod.yaml   # Argo CD Application (Prod environment sync)
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
│       ├── values.yaml         # Base default values
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
    ├── task-06-cloud-kubernetes-infrastructure.md # Task 06 Learning Document
    └── task-07-cicd-gitops-agent-delivery.md      # Task 07 Learning Document
```

---

## 3. Quickstart: CI/CD & Argo CD Operations

### Prerequisites
- Docker Engine (v20.10+)
- `kind` (v0.27.0+)
- `kubectl` (v1.37.0+)
- `helm` (v3.17.1+)
- `terraform` (v1.9.8+)

### Step 1: Run Local CI Validation Suite
```bash
# Run Python Pytest test suite (27 passed)
./.venv/bin/pytest -v

# Run Helm Lint & Production Dry-Run Template
export PATH="$HOME/.local/bin:$PATH"
helm lint ./charts/agent-platform
helm template agent-platform ./charts/agent-platform -f charts/agent-platform/values-prod.yaml
```

### Step 2: Build & Scan Docker Image
```bash
docker build -t agent-platform:${{ github.sha }} .
```

### Step 3: Deploy Argo CD Applications (GitOps)
```bash
# Apply Argo CD AppProject and Applications
kubectl apply -f argocd/project.yaml
kubectl apply -f argocd/application-dev.yaml
kubectl apply -f argocd/application-prod.yaml

# Verify Argo CD Application Status
kubectl get applications -n argocd
```

---

## 4. Operations & CI/CD Command Summary

| Action | Command |
| --- | --- |
| **Run Pytest Suite** | `./.venv/bin/pytest` |
| **Lint Helm Chart** | `helm lint ./charts/agent-platform` |
| **Validate Terraform IaC** | `cd terraform && terraform fmt -check && terraform validate` |
| **Render Prod Manifests** | `helm template agent-platform ./charts/agent-platform -f charts/agent-platform/values-prod.yaml` |
| **Apply Argo CD Manifests** | `kubectl apply -f argocd/` |
| **Check Argo CD Applications** | `kubectl get applications -n argocd` |

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

- **Phase 7 (Completed)**: CI/CD & GitOps Agent Delivery (GitHub Actions Workflows, AWS OIDC, ECR Push, Trivy Scanning, Argo CD GitOps).
- **Phase 8 (Next)**: Observability, Monitoring & Production Telemetry (Prometheus, Grafana, and Horizontal Pod Autoscalers).
