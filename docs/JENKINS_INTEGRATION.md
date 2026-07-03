# Jenkins Integration

DevFlow integrates with Jenkins CI/CD via REST API to trigger builds, monitor status, collect evidence, and create incidents on failure.

## Architecture

```
User (Frontend)  →  Jenkins Blueprint  →  JenkinsService  →  Jenkins REST API
                         │
                         ├── OrchestrationService
                         │       ├── EventService (BuildStarted/Succeeded/Failed)
                         │       ├── CorrelationService (build context)
                         │       ├── SeverityEngine (auto-severity)
                         │       └── IncidentService (create on failure)
                         │
                         └── JenkinsEvidenceCollector
                                 ├── collect_logs()     → consoleText
                                 ├── collect_metadata() → build info
                                 └── collect_metrics()  → duration/status
```

## Configuration

Set these environment variables:

| Variable | Description | Default |
|---|---|---|
| `JENKINS_URL` | Jenkins server URL (e.g. `http://jenkins:8080`) | `""` |
| `JENKINS_USERNAME` | Jenkins username | `""` |
| `JENKINS_API_TOKEN` | Jenkins API token (not password) | `""` |
| `JENKINS_JOB_NAME` | Jenkins job to trigger | `devflow-pipeline` |

> **Fallback**: `JENKINS_USER` / `JENKINS_TOKEN` are still accepted for backward compatibility.

## API Endpoints

### `POST /api/v1/jenkins/build`
Trigger a Jenkins build with parameters.

**Request:**
```json
{
  "repository": "my-app",
  "branch": "main",
  "commit_sha": "abc123",
  "triggered_by": "user@example.com"
}
```

**Response:** `202`
```json
{
  "message": "Build triggered",
  "data": {
    "queue_id": "42",
    "queue_url": "http://jenkins:8080/queue/item/42/",
    "job_name": "devflow-pipeline",
    "status": "queued",
    "timestamp": 1712345678.9
  }
}
```

Automatically emits `BuildStarted` event to the orchestration engine.

### `GET /api/v1/jenkins/queue/<queue_id>`
Poll queue status until a build number is assigned.

### `GET /api/v1/jenkins/build/<build_number>`
Get build info (status, result, duration, parameters).

**Response:** `200`
```json
{
  "data": {
    "build_number": 5,
    "status": "success",
    "result": "SUCCESS",
    "building": false,
    "duration_ms": 45000,
    "duration_seconds": 45.0,
    "timestamp": 1712345678000,
    "url": "http://jenkins:8080/job/devflow-pipeline/5/",
    "display_name": "#5",
    "parameters": {
      "REPOSITORY_NAME": "my-app",
      "BRANCH": "main",
      "COMMIT_SHA": "abc123",
      "TRIGGERED_BY": "user"
    }
  }
}
```

### `GET /api/v1/jenkins/build/<build_number>/console`
Get full console output text.

### `POST /api/v1/jenkins/build/<build_number>/event`
Manually emit a build event to the orchestration engine.

**Request:**
```json
{
  "event_type": "BUILD_SUCCEEDED"
}
```

`event_type` must be `BUILD_SUCCEEDED` or `BUILD_FAILED`.

On `BUILD_FAILED`, an `OrchestrationIncident` is auto-created and evidence (console log, build metadata, metrics) is attached via the JenkinsEvidenceCollector.

### `GET /api/v1/jenkins/builds`
List build history (latest 50 by default).

### `GET /api/v1/jenkins/health`
Jenkins connection health check.

**Response:**
```json
{
  "data": {
    "connected": true,
    "authenticated_user": "admin",
    "server_url": "http://jenkins:8080",
    "server_version": "Jenkins v2.440.3",
    "node_name": "",
    "job_exists": true,
    "job_name": "devflow-pipeline",
    "errors": null
  }
}
```

## Jenkins Job Configuration

The pipeline job must accept these parameters (as "This project is parameterized"):

| Parameter | Type | Description |
|---|---|---|
| `REPOSITORY_NAME` | String | Name of the repository |
| `BRANCH` | String | Branch to build |
| `COMMIT_SHA` | String | Commit SHA to build |
| `TRIGGERED_BY` | String | User or system that triggered |

The job should be configured to allow triggering via `/buildWithParameters`.

### CSRF Protection
The service automatically fetches a crumb from `/crumbIssuer/api/json` before triggering builds.

## Orchestration Integration

| Event | Trigger |
|---|---|
| `BuildStarted` | Auto-emitted on `POST /jenkins/build` |
| `BuildSucceeded` | Emitted via `POST /jenkins/build/<n>/event` |
| `BuildFailed` | Emitted via `POST /jenkins/build/<n>/event` → auto-creates incident |

When a `BuildFailed` event is processed:
1. `CorrelationService` correlates the event with recent events in the buffer.
2. `SeverityEngine` calculates severity based on configured rules.
3. `JenkinsEvidenceCollector` fetches console logs, build metadata, and metrics.
4. `IncidentService` creates an incident and attaches all evidence.
5. The incident appears on the Orchestration Dashboard.

## Frontend Integration

The Repository Detail page replaces the placeholder deploy button with a real Jenkins trigger:
- Clicking **Deploy** calls `POST /api/v1/jenkins/build`.
- Polls `GET /api/v1/jenkins/queue/<id>` until a build number is assigned.
- Polls `GET /api/v1/jenkins/build/<n>` every 3 seconds until completion.
- On success: shows green checkmark.
- On failure: shows red X and emits a `BUILD_FAILED` event.

The Repository Deployments page shows build history from `GET /api/v1/jenkins/builds` with status badges, duration, and direct links to Jenkins.

## Error Handling

All API errors return a consistent structure:
```json
{ "msg": "Human-readable error message" }
```

HTTP status codes:
- `401` — Jenkins authentication failed
- `403` — Jenkins access denied
- `404` — Jenkins resource not found
- `503` — Jenkins not configured (missing env vars)
- `500` — Jenkins server error

## Development

To test without a real Jenkins server:

1. Set `JENKINS_URL`, `JENKINS_USERNAME`, `JENKINS_API_TOKEN` in `backend/.env`
2. Restart the backend
3. Verify with `GET /api/v1/jenkins/health`
