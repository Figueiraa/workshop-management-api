# Observabilidade — Prometheus e Grafana

Fonte única das configurações de monitoramento, compartilhada entre **Docker Compose**
(desenvolvimento local) e **Kubernetes** (via [`k8s/monitoring`](../k8s/monitoring)).

```
monitoring/
├── prometheus/
│   ├── prometheus.yml          # scrape da API (job workshop-api) a cada 15s
│   └── rules/alerts.yml        # 6 regras de alerta (RED + negócio)
└── grafana/
    ├── provisioning/
    │   ├── datasources/        # datasource Prometheus (uid: prometheus)
    │   └── dashboards/         # provider que carrega os dashboards do repositório
    └── dashboards/
        └── workshop-api.json   # dashboard "Workshop API — Observabilidade"
```

## Usar

```bash
docker compose up --build
```

| Serviço | URL | Credenciais |
| :--- | :--- | :--- |
| Métricas da API | http://localhost:8000/metrics | — |
| Prometheus | http://localhost:9090 | — |
| Grafana | http://localhost:3000 | `admin` / `admin` |

O datasource e o dashboard são provisionados automaticamente na subida do Grafana — não é
preciso importar nada pela interface.

## Editar o dashboard

Ajustes feitos na interface do Grafana **não são persistidos** (o container monta a pasta como
somente-leitura). Para versionar uma mudança: edite o painel na UI → *Share → Export → Save to
file* → substitua `grafana/dashboards/workshop-api.json` e faça commit.

## Alterar as regras de alerta

Edite `prometheus/rules/alerts.yml` e recarregue sem reiniciar o container:

```bash
curl -X POST http://localhost:9090/-/reload
```

As regras carregadas aparecem em http://localhost:9090/alerts.

## Métricas disponíveis

Catálogo completo (nome, tipo, labels e finalidade) na seção
[Observabilidade e monitoramento](../README.md#observabilidade-e-monitoramento) do README
principal. A instrumentação vive em
[`app/infrastructure/observability/metrics.py`](../app/infrastructure/observability/metrics.py).
