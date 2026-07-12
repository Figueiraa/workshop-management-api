variable "cluster_name" {
  description = "Nome do cluster kind."
  type        = string
  default     = "workshop"
}

variable "node_image" {
  description = "Imagem do nó do kind (fixa a versão do Kubernetes)."
  type        = string
  default     = "kindest/node:v1.30.0"
}

variable "namespace" {
  description = "Namespace da aplicação."
  type        = string
  default     = "workshop"
}

variable "db_name" {
  description = "Nome do banco de dados PostgreSQL."
  type        = string
  default     = "workshop"
}

variable "db_user" {
  description = "Usuário do banco de dados."
  type        = string
  default     = "workshop"
}

variable "db_password" {
  description = "Senha do banco de dados (use um valor seguro; não commite valores reais)."
  type        = string
  default     = "workshop"
  sensitive   = true
}

variable "db_storage" {
  description = "Tamanho do volume persistente do banco."
  type        = string
  default     = "1Gi"
}
