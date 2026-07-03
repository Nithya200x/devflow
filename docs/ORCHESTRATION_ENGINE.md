# DevFlow Issue Orchestration Engine

## Architecture Overview

The Issue Orchestration Engine transforms DevFlow from a deployment dashboard into an event-driven incident lifecycle management platform. It correlates events across multiple DevOps tools (GitHub, Jenkins, Docker, Kubernetes, Prometheus, Grafana) and manages the complete incident flow from detection through resolution.

The engine is designed with **zero direct dependencies** on any external tool. All integrations are behind abstract interfaces, making the system future-proof and extensible.

---

## Module Structure

```
backend/src/orchestration/
├── __init__.py                    # Public API exports
├── events/
│   ├── __init__.py
│   └── event_types.py             # 15 event types + concrete event classes
├── interfaces/
│   ├── __init__.py
│   ├── collector_interface.py     # BaseCollector ABC
│   ├── notification_interface.py  # NotificationProvider ABC + NotificationService
│   └── ai_interface.py            # AIAnalysisService ABC
├── models/
│   ├── __init__.py
│   ├── incident.py                # OrchestrationIncident, TimelineEntry, Evidence, UnifiedIncidentContext
│   └── event_store.py             # EventStore, IncidentEvidenceStore, IncidentTimelineStore (SQLAlchemy)
├── collectors/
│   ├── __init__.py
│   ├── base_collector.py          # BaseEvidenceCollector
│   ├── github_collector.py        # GitHubEvidenceCollector
│   ├── jenkins_collector.py       # JenkinsEvidenceCollector
│   ├── docker_collector.py        # DockerEvidenceCollector
│   ├── kubernetes_collector.py    # KubernetesEvidenceCollector
│   ├── prometheus_collector.py    # PrometheusEvidenceCollector
│   ├── grafana_collector.py       # GrafanaEvidenceCollector
│   └── registry.py                # CollectorRegistry
├── correlation/
│   ├── __init__.py
│   └── correlation_service.py     # CorrelationService
├── severity/
│   ├── __init__.py
│   └── severity_engine.py         # SeverityEngine (rule-based, configurable)
├── incident/
│   ├── __init__.py
│   └── incident_service.py        # IncidentService (full lifecycle)
└── services/
    ├── __init__.py
    ├── event_service.py           # EventService (pub/sub dispatch)
    └── orchestration_service.py   # OrchestrationService (top-level coordinator)
```

### Frontend Pages

```
frontend/src/pages/
├── OrchestrationDashboard/        # /orchestration — Active/critical incidents, trend cards
├── OrchestrationIncidents/        # /orchestration/incidents — Full incident table
├── IncidentDetails/               # /orchestration/incidents/:id — Detail with context
├── EvidenceViewer/                # /orchestration/evidence/:id — Collector evidence grid
├── TimelineViewer/                # /orchestration/timeline/:id — Event timeline
├── RootCauseAnalysis/             # /orchestration/root-cause — AI analysis placeholder
└── Notifications/                 # /orchestration/notifications — Provider config
```

### API Endpoints

```
POST   /api/v1/orchestration/events               — Ingest a DevOps event
GET    /api/v1/orchestration/incidents              — List incidents (filter by status, severity)
GET    /api/v1/orchestration/incidents/:id          — Get incident details
POST   /api/v1/orchestration/incidents/:id/resolve  — Resolve an incident
POST   /api/v1/orchestration/incidents/merge        — Merge multiple incidents
GET    /api/v1/orchestration/history                — Event history
GET    /api/v1/orchestration/dashboard              — Dashboard statistics
GET    /api/v1/orchestration/collectors             — List registered collectors
GET    /api/v1/orchestration/severity/rules         — List severity rules
```

### Database Tables

| Table | Purpose |
|-------|---------|
| `event_store` | Persistent event log |
| `incident_evidence` | Evidence attached to incidents |
| `incident_timeline` | Timeline entries per incident |

---

## Event Flow

```
Repository Updated (GitHub)
       │
       ▼
Deployment Requested
       │
       ▼
Build Started (Jenkins) ──────┐
       │                       │
       ▼                       │
Build Succeeded/Failed         │  EventService dispatches
       │                       │  to subscribed handlers
       ▼                       │
Deployment Started (K8s)       │
       │                       │
       ▼                       │
Deployment Succeeded/Failed ───┘
       │
       ▼
Monitoring (Prometheus/K8s)
  ├── Container Crashed
  ├── Pod Restarted
  ├── High CPU/Memory
  └── Health Check Failed
       │
       ▼
CorrelationService combines evidence from all sources
       │
       ▼
SeverityEngine classifies (Low/Medium/High/Critical)
       │
       ▼
IncidentService creates incident + attaches evidence
       │
       ▼
Timeline populated with all event timestamps
       │
       ▼
Future: AI Analysis → Notification → Resolution
```

---

## Component Responsibilities

### Event Types (`event_types.py`)

15 standard events covering the complete DevOps lifecycle:

| Event | Source | Trigger |
|-------|--------|---------|
| `RepositoryConnected` | github | Repo connection |
| `DeploymentRequested` | github | Deploy trigger |
| `BuildStarted` | jenkins | Build start |
| `BuildSucceeded` | jenkins | Build pass |
| `BuildFailed` | jenkins | Build fail |
| `DeploymentStarted` | kubernetes | Deploy start |
| `DeploymentSucceeded` | kubernetes | Deploy success |
| `DeploymentFailed` | kubernetes | Deploy failure |
| `ContainerCrashed` | kubernetes | Container exit |
| `PodRestarted` | kubernetes | Pod restart |
| `HighCPUDetected` | prometheus | CPU threshold |
| `HighMemoryDetected` | prometheus | Memory threshold |
| `HealthCheckFailed` | kubernetes | Health check |
| `IncidentCreated` | orchestration | Auto-created |
| `IncidentResolved` | orchestration | Resolution |

Events follow a consistent interface: `event_type`, `source`, `metadata`, `timestamp`.

### Collector Framework

Each external system has a dedicated collector implementing `BaseCollector`:

```python
class BaseCollector(ABC):
    def collect_evidence(context) -> dict
    def collect_logs(context) -> list[str]
    def collect_metadata(context) -> dict
    def collect_metrics(context) -> dict
```

Registered via `CollectorRegistry`:
```python
registry.register("github", GitHubEvidenceCollector())
registry.register("prometheus", PrometheusEvidenceCollector())
```

Collectors return structured data even in their stub state, making the pipeline testable end-to-end.

### Correlation Engine (`CorrelationService`)

- `ingest(event)` — Adds events to an internal buffer
- `correlate()` — Merges all buffered events into a `UnifiedIncidentContext`
- `clear_buffer()` — Resets the buffer

The context aggregates:
- Repository + branch + commit SHA (GitHub)
- Build number (Jenkins)
- Docker image + container ID (Docker)
- Pod name + namespace + deployment (Kubernetes)
- CPU + memory metrics (Prometheus)

The service is source-agnostic. Adding a new source requires no changes to the correlation logic.

### Severity Engine (`SeverityEngine`)

Rule-based engine with configurable rules:

```python
engine.add_rule("container_crash_loop", "restart_count > 5", "critical", weight=5)
engine.add_rule("high_cpu", "cpu_percent > 90", "high", weight=2)
```

Default rules cover:
- Repeated build failures (>=3 → HIGH)
- Container crash loops (>=5 restarts → CRITICAL)
- Deployment failure (→ HIGH)
- High CPU/memory (>90% → HIGH)
- Service unavailability (→ CRITICAL)
- Multiple pod failures (>3 → CRITICAL)

Severity mapping: 0-3 LOW, 4-7 MEDIUM, 8-11 HIGH, 12+ CRITICAL.

### Incident Lifecycle

| Action | Method |
|--------|--------|
| Create | `create_incident()` |
| Update | `update_incident()` |
| Resolve | `resolve_incident()` |
| Merge | `merge_incidents()` |
| Attach Evidence | `attach_evidence()` |
| Attach Timeline | `add_timeline_event()` |
| Close | `close_incident()` |
| Archive | `archive_incident()` |
| Delete | `delete_incident()` |

The `OrchestrationIncident` model includes all fields specified in the design (incident_id, repository, project, environment, branch, commit_sha, build_number, deployment_id, status, severity, category, summary, description, evidence, timeline, assigned_to, resolution_notes, root_cause, related_incidents, ai_analysis, confidence_score, suggested_fixes, created_at, resolved_at).

### Timeline Model

Each incident maintains an ordered list of `TimelineEntry` objects:

```python
TimelineEntry(timestamp, event_type, source, description, metadata)
```

Example:
```
10:00 Deployment Started (kubernetes)
10:01 Build Started (jenkins)
10:03 Docker Build Completed (docker)
10:05 K8s Deployment Started (kubernetes)
10:06 Pod CrashLoopBackOff (kubernetes)
10:06 Incident Created (system)
```

### Notification Layer (Interface Only)

```python
class NotificationProvider(ABC):
    def send_incident_notification(incident, recipient) -> bool
    def send_severity_alert(incident, severity, recipient) -> bool
    def send_resolution_notification(incident, recipient) -> bool
    def send_bulk_notification(incident, recipients) -> dict
```

Future providers: Email, Slack, Microsoft Teams, Discord, Webhooks.

All registered through `NotificationService` for unified management.

### AI Layer (Interface Only)

```python
class AIAnalysisService(ABC):
    def analyze_incident(incident, evidence) -> dict
    def summarize_logs(logs) -> str
    def suggest_fixes(incident, context) -> list[str]
    def estimate_confidence(incident, analysis) -> float
    def classify_root_cause(incident, evidence) -> str
```

To be implemented in a future phase. The `OrchestrationService.set_ai_service()` method allows plugging in any implementation.

---

## Design Principles

1. **SOLID**: Single-responsibility for each module, dependency inversion via interfaces
2. **No hardcoded provider logic**: All external integrations behind abstract interfaces
3. **Event-driven**: The entire pipeline is driven by `OrchestrationEvent` objects
4. **Testable**: All services work with in-memory data structures, no real API calls
5. **Configurable**: Severity rules are defined as data (add/remove at runtime)
6. **Independent from deployments**: Orchestration module has zero imports from deployment, cluster, or project services

---

## Future Integration Checklist

### Jenkins Integration
- [ ] Implement `collect_evidence()` in `JenkinsEvidenceCollector` using Jenkins API
- [ ] Register Jenkins webhook receiver
- [ ] Map Jenkins build events to `BuildStarted`, `BuildSucceeded`, `BuildFailed`

### Docker Integration
- [x] Implement `DockerEvidenceCollector` with Docker SDK
- [x] Monitor container crash events (die, oom, health_status)
- [x] Map to `CONTAINER_EXITED`, `CONTAINER_OOM_KILLED`, `CONTAINER_UNHEALTHY`
- [x] Real-time event subscriber (daemon thread)
- [x] Container stats API (CPU, memory, network, block IO, PIDs)
- [x] Environment variable masking for secrets

### Kubernetes Integration
- [x] Implement `KubernetesEvidenceCollector` with Kubernetes API
- [x] Watch pod events via `list_event_for_all_namespaces`
- [x] Map to `CRASH_LOOP_BACK_OFF`, `IMAGE_PULL_BACK_OFF`, `FAILED_SCHEDULING`, `NODE_NOT_READY`, `OOM_KILLED`
- [x] Real-time event watcher (daemon thread)
- [x] Cluster metrics (pod phases, container states, node/deployment health)
- [x] kubeconfig + in-cluster config fallback

### Prometheus Integration
- [ ] Implement `PrometheusEvidenceCollector` with Prometheus HTTP API
- [ ] Query for CPU/memory thresholds
- [ ] Map to `HighCPUDetected`, `HighMemoryDetected`

### AI Analysis (Future Phase)
- [ ] Implement `AIAnalysisService` with LLM
- [ ] Call `orchestration_service.set_ai_service(ai_service)`
- [ ] Wire up root cause analysis endpoint

### Notifications (Future Phase)
- [ ] Implement `NotificationProvider` for each channel
- [ ] Register with `NotificationService`
- [ ] Trigger on incident create, resolve, and severity escalation

The orchestration engine requires **zero architectural changes** to accept any of these integrations. Each integration maps to an existing interface and event type.

---

## Verification

To confirm the orchestration engine is operational:

```bash
# Start the backend
cd backend
flask run

# Verify health
curl http://localhost:5000/health

# Ingest a test event
curl -X POST http://localhost:5000/api/v1/orchestration/events \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"event_type": "BUILD_FAILED", "metadata": {"build_number": "42", "repository": "test/repo", "branch": "main"}}'

# Check dashboard
curl http://localhost:5000/api/v1/orchestration/dashboard \
  -H "Authorization: Bearer <token>"
```

The engine is ready to accept Jenkins, Docker, Kubernetes, Prometheus, and AI integrations without major refactoring.
