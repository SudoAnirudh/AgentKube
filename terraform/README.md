# AgentKube Terraform Infrastructure (AWS EKS)

This directory defines Infrastructure as Code (IaC) for provisioning a production-ready AWS EKS Kubernetes cluster, VPC networking, managed node groups, and IAM OIDC integrations using **Terraform**.

---

## 1. Architecture

```text
AWS VPC (10.0.0.0/16)
 ├── Internet Gateway
 ├── NAT Gateway (EIP)
 ├── 2 Public Subnets (10.0.1.0/24, 10.0.2.0/24) ── ELB Public Ingress
 └── 2 Private Subnets (10.0.10.0/24, 10.0.11.0/24) ── EKS Managed Node Group (2x t3.medium)
       │
       └── AWS EKS Cluster (agentkube-cluster)
             ├── OIDC Identity Provider (IRSA for Secrets Manager)
             └── Namespace: agent-platform
```

---

## 2. Terraform Operations Workflow

### Prerequisites
- AWS CLI configured (`aws configure`)
- Terraform v1.5.0+

### Step 1: Initialize Terraform
```bash
terraform init
```

### Step 2: Validate Configuration
```bash
terraform fmt -check
terraform validate
```

### Step 3: Plan Infrastructure
```bash
terraform plan -out=tfplan
```

### Step 4: Apply Infrastructure
```bash
terraform apply tfplan
```

### Step 5: Configure Kubeconfig
```bash
aws eks update-kubeconfig --region us-east-1 --name agentkube-cluster
```

### Step 6: Teardown Infrastructure
```bash
terraform destroy
```

---

## 3. Terraform State Management Note
For production multi-developer teams, store `terraform.tfstate` in an S3 Bucket with DynamoDB state locking:

```hcl
terraform {
  backend "s3" {
    bucket         = "agentkube-terraform-state"
    key            = "prod/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "agentkube-terraform-locks"
    encrypt        = true
  }
}
```
