output "cluster_name" {
  description = "Nome do cluster kind provisionado."
  value       = kind_cluster.this.name
}

output "cluster_endpoint" {
  description = "Endpoint da API do cluster Kubernetes."
  value       = kind_cluster.this.endpoint
}

output "kubeconfig_path" {
  description = "Caminho do kubeconfig gerado pelo kind."
  value       = kind_cluster.this.kubeconfig_path
}

output "namespace" {
  description = "Namespace da aplicação."
  value       = kubernetes_namespace.workshop.metadata[0].name
}

output "database_host" {
  description = "Host (service) do PostgreSQL dentro do cluster."
  value       = "workshop-postgres.${kubernetes_namespace.workshop.metadata[0].name}.svc.cluster.local"
}

output "database_url" {
  description = "DATABASE_URL para a aplicação (contém a senha)."
  value       = "postgresql+asyncpg://${var.db_user}:${var.db_password}@workshop-postgres:5432/${var.db_name}"
  sensitive   = true
}
