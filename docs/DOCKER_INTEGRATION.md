# Docker Integration

DevFlow integrates with Docker via the official Docker SDK for Python (`docker` package) to monitor container health, collect evidence, and create incidents on container failures.

## Architecture

```
Docker Daemon  →  DockerService (SDK wrapper)  →  Docker Blueprint
                            │
                            ├── DockerEvidenceCollector
                            │       ├── collect_metadata() → container inspect
                            │       ├── collect_logs()     → container stdout/stderr
                            │       └── collect_metrics()  → CPU/memory/network/IO
                            │
                            └── Event Subscriber (daemon thread)
                                    ├── die/destroy/kill → container_stopped
                                    ├── oom              → container_oomkilled
                                    └── health_status    → container_unhealthy
                                            │
                                            ▼
                                    Orchestration Engine
                                    (EventService → Correlation → Severity → Incident)
```

## Configuration

Configured via environment variables (standard Docker SDK env vars):

| Variable | Description | Default |
|---|---|---|
| `DOCKER_HOST` | Docker daemon socket URL | `unix:///var/run/docker.sock` |
| `DOCKER_TLS_VERIFY` | Enable TLS verification | `""` |
| `DOCKER_CERT_PATH` | Path to TLS certificate files | `""` |

In `docker-compose.yml`, the Docker socket is mounted:
```yaml
services:
  backend:
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
    environment:
      - DOCKER_HOST=unix:///var/run/docker.sock
```

## API Endpoints

### `GET /api/v1/docker/health`
Docker daemon connection health check.

**Response:**
```json
{
  "data": {
    "connected": true,
    "docker_version": "29.2.0",
    "api_version": "1.53",
    "os": "linux",
    "kernel": "6.10.0-linuxkit",
    "server_name": "",
    "server_version": "29.2.0",
    "driver": "overlay2",
    "containers": 65,
    "images": 24,
    "errors": null
  }
}
```

### `GET /api/v1/docker/containers`
List all containers with status and basic info.

**Query params:** `all=true` (include stopped, default), `status=running`, `label=com.example.key=val`, `ancestor=nginx:latest`

**Response:**
```json
{
  "data": {
    "containers": [
      {
        "id": "abc123def456",
        "name": "my_container",
        "image": "nginx:latest",
        "status": "running",
        "state": "running",
        "created": "2026-07-03T10:00:00",
        "ports": ["0.0.0.0:80->80/tcp"],
        "labels": {"com.example.key": "val"}
      }
    ],
    "total": 23,
    "running": 4,
    "stopped": 17,
    "paused": 0,
    "unknown": 2
  }
}
```

### `GET /api/v1/docker/containers/<container_id>`
Get detailed container info (inspect output).

### `GET /api/v1/docker/containers/<container_id>/logs`
Get container logs.

**Query params:** `tail=100` (number of lines), `timestamps=true`

### `GET /api/v1/docker/containers/<container_id>/stats`
Get live container stats.

**Response:**
```json
{
  "data": {
    "container_id": "abc123def456",
    "container_name": "my_container",
    "cpu_percent": 0.43,
    "memory_usage_mb": 64.2,
    "memory_limit_mb": 8192.0,
    "memory_percent": 0.78,
    "network_rx_bytes": 1048576,
    "network_tx_bytes": 524288,
    "block_read_mb": 12.5,
    "block_write_mb": 3.2,
    "pids": 12
  }
}
```

### `GET /api/v1/docker/stats`
Aggregate stats across all running containers.

**Response:**
```json
{
  "data": {
    "total_containers": 23,
    "running_containers": 4,
    "container_stats": [
      { "container_id": "abc...", "container_name": "my_container", "cpu_percent": 0.43, ... }
    ]
  }
}
```

## Orchestration Integration

| Event | Trigger | Severity |
|---|---|---|
| `CONTAINER_EXITED` | Container exits with non-zero code | HIGH (exit > 0) / CRITICAL (exit 137 = OOM) |
| `CONTAINER_OOM_KILLED` | OOM kill detected | CRITICAL |
| `CONTAINER_UNHEALTHY` | Health check failure | CRITICAL |

### Event Processing Pipeline

1. Docker daemon emits event → `DockerService.subscribe_events()` daemon thread receives it
2. Event mapped to concrete event class (`ContainerExited`, `ContainerOOMKilled`, etc.)
3. Event published to orchestration engine via `EventService.ingest()`
4. `CorrelationService` correlates with recent events (extracts `container_id`, `image`, `exit_code`, `reason`)
5. `SeverityEngine` evaluates rules against event metadata (exit code, reason)
6. `DockerEvidenceCollector.collect_evidence()` fetches logs + metadata + stats
7. `IncidentService` creates incident with all evidence attached
8. Timeline populated with all event timestamps

### Response Format

All evidence references use the collector registry prefix:
- `docker_metadata` — `DockerEvidenceCollector.collect_metadata()`
- `docker_logs` — `DockerEvidenceCollector.collect_logs()`
- `docker_metrics` — `DockerEvidenceCollector.collect_metrics()`

## Security

Environment variables containing secrets are masked in container metadata:
- `TOKEN`, `SECRET`, `PASSWORD`, `PASS`, `KEY`, `API_KEY`, `ACCESS_KEY` values replaced with `***MASKED***`

## Error Handling

| HTTP Status | Meaning |
|---|---|
| `401` | Authentication required |
| `404` | Container not found |
| `500` | Docker daemon error |
| `503` | Docker not connected |

All errors return: `{ "msg": "Human-readable error message" }`
