# ─── Cluster Kubernetes (kind, local) ────────────────────────────────────────
resource "kind_cluster" "this" {
  name           = var.cluster_name
  node_image     = var.node_image
  wait_for_ready = true
}

# ─── Namespace da aplicação ──────────────────────────────────────────────────
resource "kubernetes_namespace" "workshop" {
  metadata {
    name = var.namespace
  }
}

# ─── metrics-server (necessário para o HPA funcionar) ────────────────────────
resource "helm_release" "metrics_server" {
  name       = "metrics-server"
  repository = "https://kubernetes-sigs.github.io/metrics-server/"
  chart      = "metrics-server"
  namespace  = "kube-system"

  # Em kind os kubelets usam certificados self-signed.
  set {
    name  = "args[0]"
    value = "--kubelet-insecure-tls"
  }

  depends_on = [kind_cluster.this]
}

# ─── Banco de dados PostgreSQL (chart bitnami) ───────────────────────────────
# fullnameOverride fixa o nome do service em "workshop-postgres", o mesmo host
# usado pelo DATABASE_URL dos manifestos em /k8s.
resource "helm_release" "postgres" {
  name       = "workshop-postgres"
  repository = "https://charts.bitnami.com/bitnami"
  chart      = "postgresql"
  namespace  = kubernetes_namespace.workshop.metadata[0].name

  set {
    name  = "fullnameOverride"
    value = "workshop-postgres"
  }
  set {
    name  = "auth.username"
    value = var.db_user
  }
  set {
    name  = "auth.password"
    value = var.db_password
  }
  set {
    name  = "auth.database"
    value = var.db_name
  }
  set {
    name  = "primary.persistence.size"
    value = var.db_storage
  }
}
