resource "kubernetes_namespace" "agent_platform" {
  metadata {
    name = "agent-platform"
    labels = {
      "app.kubernetes.io/name"       = "agent-platform"
      "app.kubernetes.io/managed-by" = "terraform"
    }
  }

  depends_on = [aws_eks_node_group.main]
}

resource "kubernetes_service_account" "agent_sa" {
  metadata {
    name      = "agent-service-account"
    namespace = kubernetes_namespace.agent_platform.metadata[0].name
    annotations = {
      "eks.amazonaws.com/role-arn" = aws_iam_role.cluster.arn
    }
  }

  depends_on = [kubernetes_namespace.agent_platform]
}
