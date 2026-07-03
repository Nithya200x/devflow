# Kubernetes Integration

DevFlow integrates with Kubernetes via the official Kubernetes Python Client (`kubernetes` package) to monitor cluster health, watch pod events, and create incidents on failures.

## Architecture

```
Kubernetes API  →  KubernetesService (client wrapper)  →  Kubernetes Blueprint
                            │
                            ├── KubernetesEvidenceCollector
                            │       ├── collect_metadata() → pod/deployment detail
                            │       ├── collect_logs()     → pod logs (with previous)
                            │       └── collect_metrics()  → cluster metrics
                            │
                            └── Event Watcher (daemon thread)
                                    ├── CrashLoopBackOff → crash_loop_back_off
                                    ├── ImagePullBackOff → image_pull_back_off
                                    ├── FailedScheduling  → failed_scheduling
                                    ├── NodeNotReady     → node_not_ready
                                    ├── OOMKilled        → oom_killed
                                    ├── BackOff          → pod_restarting
                                    └── Unhealthy        → pod_unhealthy
                                            │
                                            ▼
                                    Orchestration Engine
                                    (EventService → Correlation → Severity → Incident)
```

## Configuration

Configured via environment variables:

| Variable | Description | Default |
|---|---|---|
| `KUBECONFIG` | Path to kubeconfig file | `~/.kube/config` |

If `KUBECONFIG` is set, the service loads that specific file.
If not set, it attempts `load_incluster_config()` (for in-cluster use), then falls back to `load_kube_config()` (default path).

## API Endpoints

### `GET /api/v1/kubernetes/health`
Kubernetes cluster connection health check.

**Response (connected):**
```json
{
  "data": {
    "connected": true,
    "cluster_name": "docker-desktop",
    "server_version": "1.32.0",
    "nodes": 2,
    "namespaces": 12,
    "deployments": 8,
    "pods": 45,
    "errors": null
  }
}
```

**Response (disconnected — expected without kubeconfig):**
```json
{
  "data": {
    "connected": false,
    "cluster_name": null,
    "server_version": null,
    "nodes": 0,
    "namespaces": 0,
    "deployments": 0,
    "pods": 0,
    "errors": "No Kubernetes connection available"
  }
}
```

### `GET /api/v1/kubernetes/pods`
List pods across all namespaces.

**Query params:** `namespace=default`, `label=app=nginx`

### `GET /api/v1/kubernetes/pods/<namespace>/<name>`
Get pod detail with container states.

### `GET /api/v1/kubernetes/pods/<namespace>/<name>/logs`
Get pod logs.

**Query params:** `tail_lines=100`, `previous=true`

### `GET /api/v1/kubernetes/deployments`
List deployments across all namespaces.

### `GET /api/v1/kubernetes/deployments/<namespace>/<name>`
Get deployment detail with replica status.

### `GET /api/v1/kubernetes/nodes`
List cluster nodes with status, capacity, and allocatable resources.

### `GET /api/v1/kubernetes/namespaces`
List all namespaces.

### `GET /api/v1/kubernetes/events`
List cluster events with type, reason, and message.

### `GET /api/v1/kubernetes/services`
List services across all namespaces with type, cluster IP, and ports.

### `GET /api/v1/kubernetes/ingresses`
List ingresses across all namespaces with rules and TLS.

### `GET /api/v1/kubernetes/metrics`
Cluster health metrics.

**Response:**
```json
{
  "data": {
    "total_pods": 45,
    "running_pods": 40,
    "pending_pods": 1,
    "failed_pods": 2,
    "succeeded_pods": 2,
    "unknown_pods": 0,
    "pod_phases": {"Running": 40, "Pending": 1, "Failed": 2, "Succeeded": 2},
    "container_states": {
      "running": 80,
      "waiting": 3,
      "terminated": 2,
      "waiting_reasons": {"CrashLoopBackOff": 2, "ImagePullBackOff": 1},
      "terminated_reasons": {"OOMKilled": 2},
      "total_restarts": 12
    },
    "total_nodes": 2,
    "ready_nodes": 2,
    "not_ready_nodes": 0,
    "total_deployments": 8,
    "available_deployments": 7,
    "unavailable_deployments": 1,
    "unhealthy_deployments": ["nginx-prod"]
  }
}
```

## Orchestration Integration

| Event | Trigger | Severity |
|---|---|---|
| `CRASH_LOOP_BACK_OFF` | Pod in CrashLoopBackOff | CRITICAL |
| `IMAGE_PULL_BACK_OFF` | Image pull failure | HIGH |
| `FAILED_SCHEDULING` | Pod cannot be scheduled | HIGH |
| `NODE_NOT_READY` | Node becomes unhealthy | CRITICAL |
| `OOM_KILLED` | Container OOM killed | CRITICAL |

### Event Watcher

The Kubernetes watcher runs as a daemon thread watching `list_event_for_all_namespaces`. When it detects matching event reasons, it creates the corresponding orchestration event and publishes it through the pipeline:

1. Watcher receives event → matches reason against watch list
2. Maps to concrete event class (`CrashLoopBackOff`, `ImagePullBackOff`, etc.)
3. Event published to `EventService.ingest()` with pod metadata
4. `CorrelationService` extracts `pod_name`, `namespace`, `deployment`, `reason`, `restart_count`
5. `SeverityEngine` evaluates rules — `crash_loop_back_off` (CRITICAL), `oom_killed` (CRITICAL), `node_not_ready` (CRITICAL), `deployment_unavailable` (CRITICAL)
6. `KubernetesEvidenceCollector.collect_evidence()` fetches pod detail, cluster metrics, events
7. `IncidentService` creates incident with all evidence attached

### Evidence Collectors

Evidence references use the collector registry prefix:
- `kubernetes_metadata` — Pod or deployment detail
- `kubernetes_logs` — Pod logs (with `previous=true` support)
- `kubernetes_metrics` — Cluster health metrics

## Error Handling

| HTTP Status | Meaning |
|---|---|
| `401` | Authentication required |
| `404` | Resource not found |
| `500` | Kubernetes API error |
| `503` | Kubernetes not connected (returns graceful response with `connected: false`) |

All errors return: `{ "msg": "Human-readable error message" }`
