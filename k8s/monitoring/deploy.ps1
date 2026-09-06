# Sobe a stack de observabilidade (Prometheus + Grafana) no cluster.
# As regras de alerta e o dashboard vem de /monitoring, a mesma fonte usada pelo
# Docker Compose - sem copias duplicadas no repositorio.
$ErrorActionPreference = "Stop"

$root = Resolve-Path (Join-Path $PSScriptRoot "../..")

kubectl apply -f (Join-Path $root "k8s/monitoring/namespace.yaml")

kubectl -n monitoring create configmap prometheus-rules `
  --from-file=alerts.yml=(Join-Path $root "monitoring/prometheus/rules/alerts.yml") `
  --dry-run=client -o yaml | kubectl apply -f -

kubectl -n monitoring create configmap grafana-dashboards `
  --from-file=workshop-api.json=(Join-Path $root "monitoring/grafana/dashboards/workshop-api.json") `
  --dry-run=client -o yaml | kubectl apply -f -

kubectl apply -k (Join-Path $root "k8s/monitoring")

kubectl -n monitoring rollout status deployment/prometheus --timeout=180s
kubectl -n monitoring rollout status deployment/grafana --timeout=180s

Write-Host ""
Write-Host "Stack de observabilidade no ar. Para acessar:"
Write-Host "  kubectl -n monitoring port-forward svc/prometheus 9090:9090   # http://localhost:9090"
Write-Host "  kubectl -n monitoring port-forward svc/grafana   3000:3000    # http://localhost:3000 (admin/admin)"
