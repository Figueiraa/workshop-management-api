# Observabilidade no Kubernetes (Prometheus + Grafana)

Stack de monitoramento da API, instalada num namespace `monitoring` separado da aplicação.

## O que sobe

| Recurso | Descrição |
| :--- | :--- |
| `prometheus.yaml` | Prometheus + ServiceAccount/RBAC de leitura + config de scrape por *service discovery* |
| `grafana.yaml` | Grafana com datasource e provider de dashboards já provisionados |
| `namespace.yaml` | Namespace `monitoring` |
| `kustomization.yaml` | Junta tudo e gera o secret do admin do Grafana |

O Prometheus **descobre os pods sozinho**: coleta qualquer pod anotado com
`prometheus.io/scrape: "true"` — annotation já presente em [`../deployment.yaml`](../deployment.yaml).
Não é preciso listar endereços; quando o HPA escala a API de 2 para 10 réplicas,
os novos pods entram automaticamente na coleta.

As **regras de alerta** e o **dashboard** têm fonte única em [`/monitoring`](../../monitoring),
compartilhada com o Docker Compose, e são publicadas como ConfigMap pelo script de deploy.

## Subir

```bash
# Linux / macOS / Git Bash
./k8s/monitoring/deploy.sh
```

```powershell
# Windows (PowerShell)
.\k8s\monitoring\deploy.ps1
```

O script cria o namespace, publica os ConfigMaps de regras e dashboard a partir de
`/monitoring`, aplica os manifestos e aguarda os *rollouts*.

<details>
<summary>Passo a passo manual (equivalente ao script)</summary>

```bash
kubectl apply -f k8s/monitoring/namespace.yaml

kubectl -n monitoring create configmap prometheus-rules \
  --from-file=alerts.yml=monitoring/prometheus/rules/alerts.yml \
  --dry-run=client -o yaml | kubectl apply -f -

kubectl -n monitoring create configmap grafana-dashboards \
  --from-file=workshop-api.json=monitoring/grafana/dashboards/workshop-api.json \
  --dry-run=client -o yaml | kubectl apply -f -

kubectl apply -k k8s/monitoring
```

</details>

## Acessar

```bash
kubectl -n monitoring port-forward svc/prometheus 9090:9090   # http://localhost:9090
kubectl -n monitoring port-forward svc/grafana   3000:3000    # http://localhost:3000
```

- **Prometheus** → *Status → Targets*: o alvo `kubernetes-pods` deve listar um endpoint
  `UP` por réplica da API. *Alerts* mostra as regras carregadas.
- **Grafana** (`admin` / `admin`) → pasta **Workshop** → dashboard
  **Workshop API — Observabilidade**.

> A senha do admin vem do `secretGenerator` do `kustomization.yaml`. Em ambiente real,
> troque por um Secret gerenciado fora do repositório:
> `kubectl -n monitoring create secret generic grafana-admin --from-literal=username=admin --from-literal=password='<senha forte>'`

## Verificar a coleta

```bash
# métricas cruas de um pod da API
kubectl -n workshop port-forward deploy/workshop-api 8000:8000
curl http://localhost:8000/metrics | grep workshop_http_requests_total

# consulta no Prometheus (após o port-forward da porta 9090)
curl -s 'http://localhost:9090/api/v1/query?query=up{job="workshop-api"}' | jq
```

## Remover

```bash
kubectl delete -k k8s/monitoring
kubectl delete namespace monitoring
```

## Alternativa: Prometheus Operator

Se o cluster já roda o **kube-prometheus-stack**, dispense estes manifestos e crie apenas
um `ServiceMonitor` apontando para o Service da API (que já expõe a porta `http` e as
annotations de scrape):

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: workshop-api
  namespace: monitoring
  labels:
    release: kube-prometheus-stack
spec:
  namespaceSelector:
    matchNames: [workshop]
  selector:
    matchLabels:
      app: workshop-api
  endpoints:
    - port: http
      path: /metrics
      interval: 15s
```
