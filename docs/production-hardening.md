# Production Hardening & Reliability Guide — AgentKube

## 1. Executive Summary

This document details the production hardening, security posture, autoscaling configuration, high availability mechanisms, and reliability strategies implemented for **AgentKube**.

The objective is to ensure AgentKube maintains strict operational reliability, zero-downtime during voluntary disruptions, least-privilege security boundaries, and automatic capacity elasticity under varying load profiles.

---

## 2. Resource Management & Quality of Service (QoS)

Every production workload defines explicit CPU and Memory requests and limits to guarantee predictable Kubernetes scheduling and prevent noisy-neighbor memory exhaustion.

### Workload Sizing Matrix

| Component | CPU Request | Memory Request | CPU Limit | Memory Limit | Guaranteed QoS |
|---|---|---|---|---|---|
| **API (`agent-api`)** | `250m` | `256Mi` | `1000m` | `1Gi` | Burstable |
| **Worker (`agent-worker`)** | `250m` | `256Mi` | `1000m` | `1Gi` | Burstable |
| **Redis (`agent-redis`)** | `100m` | `128Mi` | `500m` | `512Mi` | Burstable |

### OOMKilled Prevention
- If a container exceeds its memory limit (`1Gi`), Kubernetes sends `SIGKILL` to prevent host node kernel panic.
- Memory requests ensure nodes are never overcommitted beyond physical capacity.

---

## 3. Horizontal Pod Autoscaling (HPA)

AgentKube implements dual-metric horizontal autoscaling using the `autoscaling/v2` API.

### API Autoscaling Policy
- **Target CPU Utilization:** `70%`
- **Target Memory Utilization:** `80%`
- **Min Replicas:** `3` (Production)
- **Max Replicas:** `8` (Production)
- **Scaling Triggers:** Incoming HTTP request bursts dynamically spawn additional `agent-api` pods to maintain sub-100ms API latency.

### Worker Autoscaling Policy
- **Target CPU Utilization:** `75%`
- **Min Replicas:** `2` (Production)
- **Max Replicas:** `8` (Production)
- **Scaling Considerations:** Worker autoscaling scales worker pods as async AI task workloads increase CPU consumption.

---

## 4. High Availability & Disruption Handling

### PodDisruptionBudget (PDB)
To protect against voluntary disruptions (e.g. `kubectl drain`, GKE/EKS node upgrades, autoscaler scale-downs):
- **`agent-api-pdb`**: `minAvailable: 2`
- **`agent-worker-pdb`**: `minAvailable: 1`

### Pod Anti-Affinity & Topology Spread Constraints
- Workloads implement `topologySpreadConstraints` with `maxSkew: 1` across `kubernetes.io/hostname` to guarantee pods are distributed across distinct physical/virtual nodes.

### Graceful Termination Lifecycle
- **API (`terminationGracePeriodSeconds: 30`)**: Completes active HTTP responses before terminating socket listeners.
- **Worker (`terminationGracePeriodSeconds: 60`)**: Sends `SIGTERM` to Celery, allowing workers to complete active in-flight AI tasks and flush state to Redis before process shutdown.

---

## 5. Security Hardening & RBAC

### Container SecurityContext
All pods enforce non-root execution and drop Linux kernel capabilities:

```yaml
securityContext:
  runAsNonRoot: true
  runAsUser: 1000
  runAsGroup: 1000
  fsGroup: 1000

containerSecurityContext:
  allowPrivilegeEscalation: false
  readOnlyRootFilesystem: true
  capabilities:
    drop:
      - ALL
```

- Temporary storage is provided via isolated `/tmp` `emptyDir` mounts.

### Least-Privilege RBAC
- Dedicated ServiceAccounts (`agent-api-sa`, `agent-worker-sa`, `agent-redis-sa`) replace default service accounts without cluster-admin permissions.

### NetworkPolicies (Network Isolation)
- **API Policy**: Accepts ingress on port 8000; permits egress only to `agent-redis` (6379), DNS (53), and HTTPS (443).
- **Worker Policy**: Permits egress to `agent-redis` (6379), DNS (53), and HTTPS (443).
- **Redis Policy**: Accepts ingress **ONLY** from matching `app: agent-api` and `app: agent-worker` pods on port 6379. All external and unauthenticated network access is blocked.

---

## 6. Verification & Reliability Testing

Run controlled failure simulations:

```bash
DRY_RUN=true ./scripts/run_failure_simulations.sh
```

Tests include API Pod auto-recovery, Celery task queue safety during worker termination, Redis connection drop readiness gating, and manifest rendering checks.
