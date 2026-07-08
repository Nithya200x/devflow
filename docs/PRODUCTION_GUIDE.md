# Production Guide

## Architecture Overview

```
User (Frontend :8080)  →  Backend API (:5000)  →  External Services
                              │
                              ├── GitHub (REST API)
                              ├── Docker (Unix socket / TCP)
                              ├── Kubernetes (kubeconfig / in-cluster)
                              ├── Prometheus (HTTP API)
                              ├── Grafana (HTTP API)
                              └── Alertmanager (HTTP API / webhook)
                              │
                              └── Orchestration Engine
                                   ├── EventService (pub/sub)
                                   ├── CorrelationService (event buffer)
                                   ├── SeverityEngine (rule-based)
                                   ├── CollectorRegistry (6 collectors)
                                   └── IncidentService (lifecycle)
```

## Deployment

### Docker Compose

```bash
# Start all services
docker compose up -d --build

# Verify
docker compose ps
curl http://localhost:5000/health
```

### Environment Variables

#### Required
| Variable | Description |
|---|---|
| `JWT_SECRET_KEY` | Secret key for JWT token signing |

#### External Integrations
| Variable | Description | Default |
|---|---|---|
| `JENKINS_URL` | Jenkins server URL | `""` |
| `JENKINS_USERNAME` | Jenkins username | `""` |
| `JENKINS_API_TOKEN` | Jenkins API token | `""` |
| `DOCKER_HOST` | Docker daemon socket | `unix:///var/run/docker.sock` |
| `KUBECONFIG` | Path to kubeconfig | `""` (in-cluster fallback) |
| `PROMETHEUS_URL` | Prometheus server URL | `""` |
| `PROMETHEUS_USERNAME` | Prometheus basic auth username | `""` |
| `PROMETHEUS_PASSWORD` | Prometheus basic auth password | `""` |
| `PROMETHEUS_TOKEN` | Prometheus bearer token | `""` |
| `GRAFANA_URL` | Grafana server URL | `""` |
| `GRAFANA_API_KEY` | Grafana API key | `""` |
| `ALERTMANAGER_URL` | Alertmanager API URL | `""` |

#### Database
| Variable | Description | Default |
|---|---|---|
| `SQLALCHEMY_DATABASE_URI` | Database connection string | `sqlite:///devflow.db` |

## Health Checks

| Endpoint | Service | Response |
|---|---|---|
| `GET /api/v1/health` | Application | `{ "status": "ok", "version": "..." }` |
| `GET /api/v1/docker/health` | Docker | `{ "connected": bool, "version": "...", "containers": N }` |
| `GET /api/v1/kubernetes/health` | Kubernetes | `{ "connected": bool, "pods": N, "nodes": N }` |

| `GET /api/v1/prometheus/health` | Prometheus | `{ "connected": bool, "version": "...", "latency_ms": N }` |
| `GET /api/v1/grafana/health` | Grafana | `{ "connected": bool, "version": "...", "latency_ms": N }` |
| `GET /api/v1/alertmanager/health` | Alertmanager | `{ "connected": bool, "latency_ms": N }` |

## Alert Flow

```
Prometheus Alert Fires
       │
       ▼
Alertmanager routes to webhook
       │
       ▼
POST /api/v1/alertmanager/webhook
       │
       ▼
Alert mapped to OrchestrationEvent
(HighCPUDetected, HighMemoryDetected, HealthCheckFailed)
       │
       ▼
EventService.ingest()
       │
       ▼
CorrelationService correlates with buffer
       │
       ▼
SeverityEngine evaluates rules
       │
       ▼
CollectorRegistry collects evidence
(All 6 collectors: GitHub, Jenkins, Docker, K8s, Prometheus, Grafana)
       │
       ▼
IncidentService creates incident
       │
       ▼
Timeline populated
       │
       ▼
Frontend dashboard updates
```

## Evidence Flow

```
Incident Created
       │
       ▼
CollectorRegistry.collect_all_evidence(context)
       │
       ├── GitHubEvidenceCollector  →  repo/branch/commit
       ├── JenkinsEvidenceCollector →  build logs, metadata, metrics
       ├── DockerEvidenceCollector  →  container metadata, logs, stats
       ├── KubernetesEvidenceCollector →  pod detail, events, cluster metrics
       ├── PrometheusEvidenceCollector →  CPU/memory/disk/network metrics, alerts
       └── GrafanaEvidenceCollector →  dashboard refs, panels, datasources
       │
       ▼
All evidence attached to incident
```

## Incident Lifecycle

1. **Detection** — Event received from any source (build failure, container crash, alert)
2. **Correlation** — Event merged with buffer for cross-source context
3. **Severity Assignment** — Rules evaluated against event signals
4. **Evidence Collection** — All collectors run against correlated context
5. **Incident Creation** — Incident persisted with evidence and timeline
6. **Resolution** — Manual resolve via UI or API
7. **Timeline** — Full event history maintained per incident

## Severity Thresholds

| Score | Severity |
|---|---|
| >= 12 | CRITICAL |
| >= 8 | HIGH |
| >= 4 | MEDIUM |
| < 4 | LOW |

## Troubleshooting

### Backend won't start
```bash
# Check logs
docker compose logs backend

# Verify dependencies
docker compose run backend pip list
```

### Docker integration not working
- Verify Docker socket is mounted: `docker compose exec backend ls -la /var/run/docker.sock`
- Check `DOCKER_HOST` env var
- Verify permissions: `docker compose exec backend docker ps`

### Kubernetes integration not working
- Set `KUBECONFIG` env var to valid kubeconfig path
- Verify cluster access: `docker compose exec backend kubectl get nodes`
- Falls back to in-cluster config automatically

### Prometheus not connecting
- Set `PROMETHEUS_URL` to reachable Prometheus server
- Verify network: `docker compose exec backend curl $PROMETHEUS_URL/api/v1/status/buildinfo`
- Authentication: Use `TOKEN` or `USERNAME`+`PASSWORD`

### Grafana not connecting
- Set `GRAFANA_URL` and `GRAFANA_API_KEY`
- API key must have `Viewer` role or higher
- Verify: `docker compose exec backend curl -H "Authorization: Bearer $KEY" $GRAFANA_URL/api/health`

### Alertmanager webhook not receiving alerts
- Configure webhook in Alertmanager config
- Ensure DevFlow backend is reachable from Alertmanager
- Test: `POST /api/v1/alertmanager/webhook` with sample payload

### No incidents being created
- Verify event ingestion: `POST /api/v1/orchestration/events`
- Check orchestration dashboard: `GET /api/v1/orchestration/dashboard`
- Verify severity rules: `GET /api/v1/orchestration/severity/rules`
- Check collector registration: `GET /api/v1/orchestration/collectors`

## Performance Considerations

- Docker event subscriber uses daemon thread with auto-reconnect
- Kubernetes event watcher uses `timeout_seconds=60` with auto-reconnect
- Container logs truncated at 50K characters
- Prometheus queries have 15s timeout (instant) / 30s (range)
- Grafana dashboard list limited to 10 entries in collector evidence
- Event buffer cleared after correlation
- Incident evidence stored in-memory per session
- All external service calls wrapped in try/except with graceful degradation
