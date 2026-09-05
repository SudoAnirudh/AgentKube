# Disaster Recovery & Backup Strategy — AgentKube

## 1. Overview & Recovery Objectives

This document establishes the **Disaster Recovery (DR)** and Backup specification for the **AgentKube** multi-agent AI execution platform.

### Target Recovery Objectives

| Metric | Target Objective | Definition |
|---|---|---|
| **Recovery Time Objective (RTO)** | $< 15 \text{ minutes}$ | Maximum acceptable duration of infrastructure or service downtime during a catastrophic regional outage. |
| **Recovery Point Objective (RPO)** | $< 5 \text{ minutes}$ | Maximum acceptable data loss window for state and execution logs. |

---

## 2. Classification of System Assets

| Asset Category | Storage Location | Backup Mechanism | Recovery Method |
|---|---|---|---|
| **Infrastructure as Code (IaC)** | Git Repository | Git Versioning (`main` branch) | `terraform apply` / AWS EKS reprovisioning |
| **Kubernetes & Helm State** | Git Repository (`argocd/`) | GitOps Sync via Argo CD | Argo CD automated reconciliation |
| **Container Images** | AWS ECR / Registry | Immutable Image Tags (`v1.1.0`, Git SHA) | Pull image from ECR manifest |
| **Secrets & Keys** | AWS Secrets Manager | AWS KMS / Secrets Manager Replicas | ExternalSecrets Operator sync |
| **Queue & Transient State** | Redis in-memory / AOF | Redis AOF / Snapshot to S3 | Snapshot restore to Redis PVC / ElastiCache |

---

## 3. Disaster Recovery Playbook

### Scenario A: Single Worker Node Failure
1. **Detection**: Kubernetes node health check marks Node `NotReady`.
2. **Automated Recovery**:
   - `PodDisruptionBudget` ensures remaining replicas maintain service availability.
   - Kubernetes master reschedules evicted pods onto healthy nodes within 30 seconds.
3. **Manual Action**: None required (EKS Auto Scaling Group replaces failed EC2 instance).

---

### Scenario B: Complete Redis Cache & Queue Corruption
1. **Symptom**: API readiness probe fails (`HTTP 503`), worker tasks pause.
2. **Recovery Steps**:
   ```bash
   # 1. Restart Redis Deployment
   kubectl rollout restart deployment/agent-redis -n agent-platform

   # 2. Verify Redis Connectivity
   kubectl exec -it deployment/agent-redis -n agent-platform -- redis-cli ping

   # 3. Verify API Readiness Recovery
   kubectl get pods -n agent-platform -l app=agent-api
   ```

---

### Scenario C: Total Cluster / Regional Outage
1. **Rebuild Infrastructure**:
   ```bash
   cd terraform
   terraform init
   terraform apply -var-file="environments/prod.tfvars"
   ```
2. **Re-establish GitOps Reconciliation**:
   ```bash
   kubectl apply -f argocd/project.yaml
   kubectl apply -f argocd/application-prod.yaml
   ```
3. **Validation**: Confirm all deployments (`agent-api`, `agent-worker`, `agent-redis`), HPAs, PDBs, and NetworkPolicies reach `Synced` and `Healthy` status in Argo CD.
