#!/usr/bin/env bash
# Sobe a stack de observabilidade (Prometheus + Grafana) no cluster.
# As regras de alerta e o dashboard vêm de /monitoring, a mesma fonte usada pelo
# Docker Compose — sem cópias duplicadas no repositório.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

kubectl apply -f "$ROOT/k8s/monitoring/namespace.yaml"

kubectl -n monitoring create configmap prometheus-rules \
  --from-file=alerts.yml="$ROOT/monitoring/prometheus/rules/alerts.yml" \
  --dry-run=client -o yaml | kubectl apply -f -

kubectl -n monitoring create configmap grafana-dashboards \
  --from-file=workshop-api.json="$ROOT/monitoring/grafana/dashboards/workshop-api.json" \
  --dry-run=client -o yaml | kubectl apply -f -

kubectl apply -k "$ROOT/k8s/monitoring"

kubectl -n monitoring rollout status deployment/prometheus --timeout=180s
kubectl -n monitoring rollout status deployment/grafana --timeout=180s

cat <<'MSG'

Stack de observabilidade no ar. Para acessar:
  kubectl -n monitoring port-forward svc/prometheus 9090:9090   # http://localhost:9090
  kubectl -n monitoring port-forward svc/grafana   3000:3000    # http://localhost:3000 (admin/admin)
MSG
