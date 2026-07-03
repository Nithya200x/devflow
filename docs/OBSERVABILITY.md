# Observability Integration

DevFlow integrates with Prometheus, Alertmanager, and Grafana as first-class evidence providers in the orchestration engine.

## Architecture

```
Prometheus API  →  PrometheusService  →  Prometheus Blueprint
     │                                        │
     │                                 PrometheusEvidenceCollector
     │                                        │
     ├── Query (instant, range)               ├── collect_evidence()
     ├── CPU, Memory, Disk, Network            │   → metrics + alerts
     ├── Pod, Container, Node                  │
     ├── Deployment, Service                  ├── collect_metrics()
     └── Error rate, Latency, Request rate     │   → structured metric data
                                               │
Alertmanager Webhook  →  Alertmanager Route   │
     │                        │               │
     ├── /webhook POST        │               │
     ├── Alert → Event        ▼               ▼
     └── HighCPUDetected  Orchestration Engine
         HighMemoryDetected  (EventService → Correlation → Severity → Incident)
         HealthCheckFailed           │
                                     │
Grafana API  →  GrafanaService  →  Grafana Blueprint
                     │                    │
                     │            GrafanaEvidenceCollector
                     │                    │
                     ├── Dashboards       ├── collect_evidence()
                     ├── Dashboard UID     │   → dashboard refs + panels
                     ├── Panels           ├── collect_metadata()
                     └── Datasources       │   → UID, title, datasource info
```

## Configuration

### Prometheus

| Variable | Description | Default |
|---|---|---|
| `PROMETHEUS_URL` | Prometheus server URL | `""` |
| `PROMETHEUS_USERNAME` | Basic auth username | `""` |
| `PROMETHEUS_PASSWORD` | Basic auth password | `""` |
| `PROMETHEUS_TOKEN` | Bearer token (overrides basic auth) | `""` |

Supports both basic auth (`USERNAME` + `PASSWORD`) and bearer token (`TOKEN`) authentication.

### Grafana

| Variable | Description | Default |
|---|---|---|
| `GRAFANA_URL` | Grafana server URL | `""` |
| `GRAFANA_API_KEY` | Grafana API key (Service Account token) | `""` |

### Alertmanager

| Variable | Description | Default |
|---|---|---|
| `ALERTMANAGER_URL` | Alertmanager API URL | `""` |

Alerts can also be pushed via webhook at `POST /api/v1/alertmanager/webhook`.

## API Endpoints

### Prometheus (`/api/v1/prometheus`)

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Connection status, version, latency |
| POST | `/query` | Instant query (`{ "query": "..." }`) |
| POST | `/query_range` | Range query (`{ "query": "...", "start": "...", "end": "...", "step": "15s" }`) |
| GET | `/metrics/cpu` | CPU metrics (query params: `namespace`, `pod`) |
| GET | `/metrics/memory` | Memory metrics |
| GET | `/metrics/disk` | Disk read/write rates |
| GET | `/metrics/network` | Network RX/TX bytes |
| GET | `/metrics/pod` | All pod-level metrics |
| GET | `/metrics/node` | Node metrics (`node` param) |
| GET | `/metrics/deployment` | Deployment replica counts |
| GET | `/metrics/service` | Service up/down status |
| GET | `/metrics/error-rate` | HTTP 5xx error rate |
| GET | `/metrics/request-rate` | HTTP request rate |
| GET | `/metrics/latency` | P99 latency |
| GET | `/alerts` | Active Prometheus alerts |

### Grafana (`/api/v1/grafana`)

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Connection status, version, latency |
| GET | `/dashboards` | List all dashboards |
| GET | `/dashboards/<uid>` | Get dashboard with panels |
| GET | `/dashboards/by-name/<name>` | Find dashboard by title |
| GET | `/datasources` | List configured datasources |

### Alertmanager (`/api/v1/alertmanager`)

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Connection status, latency |
| GET | `/alerts` | List alerts (`silenced`, `inhibited` params) |
| GET | `/silences` | List active silences |
| POST | `/webhook` | Receive Alertmanager webhook payload |

## Alertmanager Webhook

Receive alerts from Alertmanager via its webhook feature.

**Alertmanager config:**
```yaml
receivers:
  - name: devflow
    webhook_configs:
      - url: 'http://devflow-backend:5000/api/v1/alertmanager/webhook'
        send_resolved: true
```

**Alert-to-Event Mapping:**

| Alert Type | Orchestration Event |
|---|---|
| High CPU usage | `HighCPUDetected` |
| High Memory usage | `HighMemoryDetected` |
| Application Down | `HealthCheckFailed` (ApplicationDown) |
| Disk Pressure | `HealthCheckFailed` (DiskPressure) |
| Network Latency | `HealthCheckFailed` (NetworkLatency) |
| Other alerts | `HealthCheckFailed` (Alert: name) |

## Orchestration Integration

### Evidence Collectors

| Collector | Source | Evidence |
|---|---|---|
| `PrometheusEvidenceCollector` | prometheus | Metrics (CPU, memory, disk, network, error rate, latency), alerts |
| `GrafanaEvidenceCollector` | grafana | Dashboard references, panel metadata, datasource info |
| `AlertmanagerWebhook` | alertmanager | Alert payloads via webhook endpoint |

### Severity Rules (New)

| Rule | Condition | Severity |
|---|---|---|
| `node_unreachable` | NodeNotReady / NodeUnreachable / NodeDown | CRITICAL |
| `application_unavailable` | ApplicationDown / ServiceUnavailable | CRITICAL |
| `repeated_alert` | >5 alert events | CRITICAL |
| `oom_and_high_memory` | OOMKilled + memory > 80% | CRITICAL |
| `crashloop_and_high_cpu` | CrashLoopBackOff + CPU > 80% | CRITICAL |
| `pod_unavailable` | PodUnavailable | HIGH |
| `disk_pressure` | DiskPressure / DiskUnavailable | CRITICAL |
| `network_latency` | NetworkLatency / HighLatency | HIGH |
| `cpu_warning` | CPU 80-90% | MEDIUM |
| `memory_warning` | Memory 80-90% | MEDIUM |
| `disk_warning` | Disk 80-90% | MEDIUM |
| `informational_alert` | Severity = info/warning | LOW |
| `production_alert` | Production environment + any alert | CRITICAL |

### Correlation Enhancements

The `CorrelationService` now extracts from:

- **prometheus**: `cpu_percent`, `memory_percent`, `pod_name`, `namespace`, `container_id`, `deployment`, alert summaries
- **grafana**: `dashboard_uid`, `deployment`, `namespace`
- **alertmanager**: `alertname`, `status`, `pod_name`, `namespace`, `deployment`, `summary`, `cpu_usage`, `memory_usage`

### Incident Enrichment

When an incident is created, the system automatically attaches:
- Prometheus metrics (CPU, memory, disk, network)
- Grafana dashboard references (UID, panels, datasources)
- Alert labels and metadata
- Node/container/pod-level metrics

## Health Checks

All three services return a consistent health response:

```json
{
  "connected": true,
  "version": "2.53.0",
  "latency_ms": 12.34,
  "error": null
}
```

On failure:
```json
{
  "connected": false,
  "version": "",
  "latency_ms": 0,
  "error": "Connection refused"
}
```

## Frontend Pages

| Path | Page | Description |
|---|---|---|
| `/monitoring` | Monitoring Dashboard | Service health overview, quick metric navigation |
| `/monitoring/metrics` | Prometheus Metrics | Query CPU/memory/disk/network metrics by namespace and pod |
| `/monitoring/dashboards` | Grafana Dashboards | Browse dashboards, view panel details |
| `/monitoring/alerts` | Active Alerts | View firing/resolved alerts from Alertmanager |

## Error Handling

All endpoints return consistent error structure:

```json
{ "msg": "Human-readable error message" }
```

HTTP status codes:
- `401` — Authentication required
- `503` — Service not connected (graceful degraded response)
- `500` — Internal error

Services degrade gracefully when not configured — returns `connected: false` with descriptive error.
