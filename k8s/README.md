# Manifestos Kubernetes — Workshop Management API

Deploy da aplicação (API + PostgreSQL) no namespace `workshop`, com autoescalonamento (HPA).

## Recursos

| Arquivo | Recurso | Descrição |
| :--- | :--- | :--- |
| `namespace.yaml` | Namespace | Isola os recursos no namespace `workshop` |
| `configmap.yaml` | ConfigMap | Config não sensível (log, CORS, JWT expiry, DB name/user) |
| `secret.yaml` | Secret | `SECRET_KEY`, senha do Postgres e `DATABASE_URL` (valores de exemplo) |
| `postgres.yaml` | StatefulSet + Service + PVC | Banco PostgreSQL com armazenamento persistente |
| `deployment.yaml` | Deployment | API (2 réplicas), probes liveness/readiness, initContainer aguardando o DB |
| `service.yaml` | Service | ClusterIP expondo a API na porta 80 → 8000 |
| `hpa.yaml` | HorizontalPodAutoscaler | Escala 2→10 réplicas por CPU (70%) e memória (80%) |

## Pré-requisitos

- Cluster Kubernetes (kind, minikube ou k3d para local).
- `metrics-server` habilitado (necessário para o HPA):
  - minikube: `minikube addons enable metrics-server`
- Imagem da API disponível no cluster. Em kind:
  ```bash
  docker build -t workshop-management-api:latest .
  kind load docker-image workshop-management-api:latest
  ```

## Aplicar

```bash
# Tudo de uma vez (kustomize embutido no kubectl):
kubectl apply -k k8s/

# Ou individualmente, na ordem:
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml -f k8s/secret.yaml
kubectl apply -f k8s/postgres.yaml
kubectl apply -f k8s/deployment.yaml -f k8s/service.yaml -f k8s/hpa.yaml
```

## Verificar

```bash
kubectl -n workshop get pods,svc,hpa
kubectl -n workshop rollout status deployment/workshop-api
```

## Acessar a API

```bash
kubectl -n workshop port-forward svc/workshop-api 8000:80
# Swagger em http://localhost:8000/docs
```

## Testar o autoescalonamento

```bash
kubectl -n workshop get hpa -w
# Em outro terminal, gere carga (ex.: hey/ab/k6) contra a API e observe as réplicas subirem.
```

> **Produção:** substitua os valores do `secret.yaml` por segredos reais gerenciados
> (Sealed Secrets / External Secrets / secret manager do provedor) e o `DATABASE_URL`
> para o banco provisionado via Terraform (ver `/infra`).
