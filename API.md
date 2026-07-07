# API Documentation

Base URL: `http://localhost:5000/api/v1`
Auth: `Authorization: Bearer <jwt_token>`

---

## Authentication

### POST /auth/login
Authenticate and receive a JWT token.

**Request:**
```json
{"username": "admin", "password": "admin123"}
```
**Response:**
```json
{"access_token": "eyJ...", "user": {"id": 1, "username": "admin", "role": "admin"}}
```

---

## Docker

### GET /docker/health
Docker daemon connection status.

**Response:**
```json
{"connected": true, "container_count": 69, "image_count": 29, "api_version": "1.53"}
```

### GET /docker/containers
List all containers.

**Query:** `all=true` (include stopped)

### GET /docker/stats
Aggregate container stats.

---

## Kubernetes

### GET /kubernetes/health
Cluster connection status.

**Response:**
```json
{"connected": true, "node_count": 1, "pod_count": 16, "deployment_count": 9, "namespace_count": 6, "server_version": "v1.35.1"}
```

### GET /kubernetes/pods
List pods. **Query:** `namespace=devflow`

### GET /kubernetes/deployments
List deployments. **Query:** `namespace=devflow`

### GET /kubernetes/services
List services. **Query:** `namespace=devflow`

### GET /kubernetes/nodes
List cluster nodes.

### GET /kubernetes/ingresses
List ingresses.

---

## Prometheus

### GET /prometheus/health
Prometheus connection and build info.

### GET /prometheus/query
Run instant query. **Query:** `query=<promql>`

### GET /prometheus/metrics/cpu
### GET /prometheus/metrics/memory
### GET /prometheus/metrics/disk
### GET /prometheus/metrics/network
### GET /prometheus/metrics/pod
### GET /prometheus/metrics/node
### GET /prometheus/metrics/deployment
### GET /prometheus/metrics/error-rate
### GET /prometheus/metrics/request-rate
### GET /prometheus/metrics/latency

---

## Grafana

### GET /grafana/health
Grafana connection and version info.

### GET /grafana/datasources
List provisioned datasources.

### GET /grafana/dashboards
Search dashboards. **Query:** `query=<name>`

---

## Alertmanager

### GET /alertmanager/health
Alertmanager connection status.

### GET /alertmanager/alerts
List active alerts. **Query:** `silenced=true`, `inhibited=true`

### GET /alertmanager/silences
List active silences.

### POST /alertmanager/webhook
Webhook receiver for Alertmanager alerts.

---

## Deployments

### GET /deployments
List deployments. **Query:** `project_id=<id>`

**Response:**
```json
[{"id": 1, "deployment_id": "abc123", "project_id": 1, "repository": "owner/repo", "commit_sha": "abc...", "branch": "main", "environment": "dev", "status": "success", "started_at": "...", "completed_at": "...", "triggered_by": "admin", "rollback_available": true}]
```

### POST /deployments
Create new deployment.

**Request:**
```json
{"project_id": 1, "branch": "main", "commit_sha": "", "environment": "dev"}
```

### GET /deployments/:id
Get single deployment details.

### GET /deployments/:id/logs
Get deployment logs with searchable entries.

**Response:**
```json
{"logs": [{"stage": "build", "message": "Building image...", "timestamp": "..."}], "deployment_id": 1}
```

### POST /deployments/:id/rollback
Trigger rollback to specified deployment.

### GET /deployments/:id/rollout-status
Get K8s rollout status.

---

## Incidents

### GET /incidents
List all incidents with AI analysis.

**Response:**
```json
[{"id": 1, "title": "High CPU detected", "status": "open", "severity": "warning", "source": "prometheus_high_cpu", "description": "...", "ai_summary": "...", "root_cause": "...", "confidence_score": 0.85, "suggested_fixes": ["...", "..."], "possible_causes": ["..."], "preventive_actions": ["..."], "risk_assessment": "...", "estimated_resolution_time": "30m", "affected_components": ["backend"], "timeline": [...]}]
```

### POST /incidents
Create manual incident. **Request:** `{"title": "...", "severity": "medium"}`

### PATCH /incidents/:id
Update incident status. **Request:** `{"status": "resolved"}`

---

## Orchestration

### GET /orchestration/dashboard
Dashboard stats (incident counts, recent events).

### GET /orchestration/incidents
List orchestration incidents. **Query:** `status=open`, `severity=critical`

### GET /orchestration/incidents/:id
Get incident details with AI analysis.

### POST /orchestration/incidents/:id/resolve
Resolve incident. **Request:** `{"notes": "Fixed by scaling up"}`

### POST /orchestration/incidents/:id/analyze
Trigger AI analysis for incident.

### GET /orchestration/incidents/:id/analysis
Get detailed AI analysis results.

### POST /orchestration/events
Ingest custom event. **Request:** `{"event_type": "DEPLOYMENT_FAILED", "metadata": {...}}`

### GET /orchestration/history
Event history. **Query:** `event_type=...`, `source=...`, `limit=100`

### GET /orchestration/collectors
List registered evidence collectors.

### GET /orchestration/ai/analyses
List all AI analyses.

### GET /orchestration/ai/analyses/db
List DB-persisted analyses.

---

## Analytics

### GET /analytics/dashboard
Aggregate analytics data. **Query:** `days=7`

**Response:**
```json
{"deploymentSuccessRate": 85.0, "totalDeployments": 20, "succeededDeployments": 17, "failedDeployments": 3, "deploymentsPerDay": [{"date": "2026-07-01", "count": 2}, ...], "avgDeploymentDuration": 45.2, "incidentTrends": [...], "cpuTrend": 0.05, "memTrend": 85.3, "errorRateTrend": 0.01, "topFailedDeployments": [...], "infrastructureHealthScore": 85.0}
```

---

## Diagnostics

### GET /diagnostics
Run full system health check for all 9 services.

**Response:**
```json
{"results": [{"name": "Backend API", "key": "backend", "status": "healthy", "connected": true, "latency_ms": 2.1, "version": "2.0.0", "error": null, "last_checked": "...", "recommended_fix": "..."}, ...], "summary": {"total": 9, "healthy": 9, "unhealthy": 0, "all_healthy": true}}
```

---

## GitHub

### GET /github/status
GitHub connection status for current user.

### GET /github/repos
List connected repositories.

### GET /github/repos/:id
Get repository details.

### POST /github/connect
Connect GitHub account. **Request:** `{"token": "ghp_..."}`

### GET /github/:owner/:repo/workflows
List GitHub Actions workflows.

### POST /github/:owner/:repo/workflows/:id/dispatch
Trigger workflow dispatch.

---

## Health

### GET /health
Backend health check (no auth required).

**Response:**
```json
{"app": "DevFlow", "status": "up", "version": "2.0.0"}
```

---

## Error Responses

All endpoints return consistent error format:

```json
{"msg": "Error description"}
```

HTTP status codes:
- `200` — Success
- `201` — Created
- `202` — Accepted (async operation)
- `400` — Bad request
- `401` — Unauthorized (missing/invalid JWT)
- `404` — Not found
- `500` — Internal server error
- `502` — External service error
- `503` — Service unavailable
