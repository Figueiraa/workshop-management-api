# Infraestrutura como Código (Terraform) — `/infra`

Provisiona a infraestrutura base para rodar a Workshop Management API em Kubernetes.

## O que é criado

| Recurso | Provider | Descrição |
| :--- | :--- | :--- |
| `kind_cluster.this` | `tehcyx/kind` | Cluster Kubernetes local (em Docker) |
| `kubernetes_namespace.workshop` | `hashicorp/kubernetes` | Namespace `workshop` |
| `helm_release.metrics_server` | `hashicorp/helm` | metrics-server (necessário para o **HPA**) |
| `helm_release.postgres` | `hashicorp/helm` | **Banco PostgreSQL** (chart bitnami), service `workshop-postgres` |

> O service do banco é fixado em `workshop-postgres` (`fullnameOverride`), o mesmo host
> usado pelo `DATABASE_URL` dos manifestos em [`/k8s`](../k8s). Assim, o banco pode vir
> **deste Terraform** (caminho IaC) **ou** do StatefulSet em `/k8s` (caminho local rápido) —
> nunca os dois ao mesmo tempo.

## Pré-requisitos

- [Terraform](https://developer.hashicorp.com/terraform/downloads) >= 1.5
- [Docker](https://www.docker.com/) em execução (o kind cria o cluster em containers)
- [kind](https://kind.sigs.k8s.io/) e `kubectl`

## Como aplicar

```bash
cd infra
cp terraform.tfvars.example terraform.tfvars   # ajuste a senha do banco

terraform init      # baixa os providers
terraform plan      # revisa o que será criado
terraform apply      # provisiona cluster + metrics-server + PostgreSQL

# Exporte o kubeconfig gerado (caminho no output kubeconfig_path):
export KUBECONFIG=$(terraform output -raw kubeconfig_path)
kubectl get nodes
```

Depois de provisionada a infraestrutura, faça o deploy da **aplicação** (sem o
`postgres.yaml`, já que o banco vem do Terraform):

```bash
kubectl apply -f ../k8s/namespace.yaml
kubectl apply -f ../k8s/configmap.yaml -f ../k8s/secret.yaml
kubectl apply -f ../k8s/deployment.yaml -f ../k8s/service.yaml -f ../k8s/hpa.yaml
```

## Destruir

```bash
terraform destroy
```

## Outputs

| Output | Descrição |
| :--- | :--- |
| `cluster_name` / `cluster_endpoint` | Identificação e endpoint do cluster |
| `kubeconfig_path` | Caminho do kubeconfig gerado |
| `namespace` | Namespace da aplicação |
| `database_host` | FQDN do service do PostgreSQL no cluster |
| `database_url` | `DATABASE_URL` completa (sensível) |

## Alternativa em cloud

Para provisionar em nuvem, troque o provider/módulo do cluster por EKS/GKE/AKS
(ex.: módulo `terraform-aws-modules/eks/aws`) e o `helm_release.postgres` por um
banco gerenciado (RDS/Cloud SQL/Azure Database), mantendo o mesmo `DATABASE_URL`
como saída para a aplicação. Os providers `kubernetes`/`helm` e o namespace
permanecem iguais.
