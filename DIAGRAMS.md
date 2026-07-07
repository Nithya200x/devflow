# DevFlow Architecture Diagrams

## System Architecture

```mermaid
graph TB
    subgraph Frontend
        REACT[React SPA<br/>Vite + Recharts]
    end

    subgraph Backend
        API[Flask REST API<br/>gunicorn]
        DB[(PostgreSQL)]
        ORCH[Orchestration Engine]
        AI[AI Analysis<br/>Groq Provider]
    end

    subgraph Monitoring
        PROM[Prometheus]
        ALERT[Alertmanager]
        GRAF[Grafana]
    end

    subgraph Infrastructure
        DOCKER[Docker Engine]
        K8S[Kubernetes<br/>minikube]
    end

    subgraph External
        GH[GitHub API]
        GHACTIONS[GitHub Actions]
    end

    REACT -->|HTTP/REST| API
    API --> DB
    API --> ORCH
    ORCH --> AI
    API --> PROM
    API --> ALERT
    API --> GRAF
    API --> DOCKER
    API --> K8S
    API --> GH
    API --> GHACTIONS
    PROM -->|alerts| ALERT
    ALERT -->|webhook| API
```

## Sequence Diagram

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant API
    participant Prometheus
    participant Alertmanager
    participant AI
    participant K8s

    User->>Frontend: View Dashboard
    Frontend->>API: GET /api/v1/docker/health
    Frontend->>API: GET /api/v1/kubernetes/health
    Frontend->>API: GET /api/v1/prometheus/health
    Frontend->>API: GET /api/v1/grafana/health
    API->>Prometheus: Health check
    API->>K8s: Health check
    API-->>Frontend: All health statuses
    Frontend-->>User: Dashboard rendered

    Note over Prometheus,Alertmanager: Alert fires
    Prometheus->>Alertmanager: POST alert
    Alertmanager->>API: POST /webhook
    API->>API: Create incident
    API->>AI: Trigger analysis
    AI->>AI: Analyze root cause
    AI-->>API: Analysis result
    API-->>Frontend: Incident update
    Frontend-->>User: AI recommendation displayed
```

## Deployment Workflow

```mermaid
graph LR
    A[Code Push] --> B[GitHub Event]
    B --> C[GitHub Actions<br/>Workflow]
    C --> D[Docker Build<br/>& Push]
    D --> E[K8s Rollout]
    E --> F[Health Checks]
    F --> G{Success?}
    G -->|Yes| H[Deployment<br/>Complete]
    G -->|No| I[Rollback]
    I --> J[Previous<br/>Version]
```

## CI/CD Pipeline

```mermaid
graph TB
    subgraph Source
        CODE[Git Repository]
        PR[Pull Request]
    end

    subgraph Build
        COMPILE[Build]
        TEST[Test]
        LINT[Lint]
    end

    subgraph Package
        DOCKER_BUILD[Docker Build]
        PUSH[Push to Registry]
    end

    subgraph Deploy
        DEV[Dev Environment]
        STAGING[Staging]
        PROD[Production]
    end

    subgraph Monitor
        METRICS[Prometheus]
        DASHBOARD[Grafana]
        ALERTS[Alertmanager]
    end

    CODE --> COMPILE
    PR --> COMPILE
    COMPILE --> TEST
    TEST --> LINT
    LINT --> DOCKER_BUILD
    DOCKER_BUILD --> PUSH
    PUSH --> DEV
    DEV --> STAGING
    STAGING --> PROD
    PROD --> METRICS
    METRICS --> DASHBOARD
    METRICS --> ALERTS
```

## AI RCA Flow

```mermaid
graph TB
    A[Incident Created] --> B[Collect Evidence]
    B --> C[Docker Stats]
    B --> D[K8s Events]
    B --> E[Prometheus Metrics]
    B --> F[Grafana Dashboards]
    B --> G[GitHub Logs]
    C --> H[Build Incident Context]
    D --> H
    E --> H
    F --> H
    G --> H
    H --> I[Groq AI Analysis]
    I --> J[Root Cause]
    I --> K[Confidence Score]
    I --> L[Suggested Fixes]
    I --> M[Risk Assessment]
    I --> N[Preventive Actions]
    J --> O[Recommendation Panel]
    K --> O
    L --> O
    M --> O
    N --> O
```

## Incident Lifecycle

```mermaid
stateDiagram-v2
    [*] --> Open: Alert Fires
    Open --> Analyzing: AI Triggered
    Analyzing --> Open: Rate Limited
    Analyzing --> AI_Analyzed: Analysis Complete
    AI_Analyzed --> Resolved: Manually Resolved
    AI_Analyzed --> Resolved: Auto-resolved (metrics normal)
    Resolved --> [*]

    state Open {
        [*] --> Unacknowledged
        Unacknowledged --> Acknowledged: User views
    }

    state AI_Analyzed {
        [*] --> Recommendation_Ready
        Recommendation_Ready --> Fix_Applied
        Fix_Applied --> Verified
    }
```

## Monitoring Architecture

```mermaid
graph TB
    subgraph Scrape Targets
        BACKEND[DevFlow Backend<br/>:5000/metrics]
        PROM_SELF[Prometheus Self<br/>:9090/metrics]
    end

    subgraph Prometheus
        SCRAPE[Scrape Manager<br/>interval: 10-15s]
        TSDB[TSDB Storage]
        RULES[Alert Rules<br/>evaluation: 15s]
    end

    subgraph Alertmanager
        ROUTE[Alert Routing]
        INHIBIT[Inhibition Rules]
        WEBHOOK[Webhook Receiver]
    end

    subgraph Visualization
        GRAFANA_DB[Grafana<br/>Dashboards]
        DEVELOW_UI[DevFlow UI<br/>Metrics Pages]
    end

    subgraph Backend Processing
        DETECTOR[Prometheus Detector<br/>poll: 30s]
        ORCH_ENGINE[Orchestration Engine]
    end

    BACKEND --> SCRAPE
    PROM_SELF --> SCRAPE
    SCRAPE --> TSDB
    RULES -->|alert| WEBHOOK
    WEBHOOK --> DETECTOR
    DETECTOR --> ORCH_ENGINE
    TSDB --> GRAFANA_DB
    TSDB --> DEVELOW_UI
```

## Microservice Interaction

```mermaid
graph TB
    subgraph Services
        AUTH[Auth Service]
        DOCKER_SVC[Docker Service]
        K8S_SVC[Kubernetes Service]
        PROM_SVC[Prometheus Service]
        GRAF_SVC[Grafana Service]
        ALERT_SVC[Alertmanager Service]
        GH_SVC[GitHub Service]
        INC_SVC[Incident Service]
        DEP_SVC[Deployment Service]
    end

    subgraph Routes
        AUTH_R["/auth/*"]
        DOCKER_R["/docker/*"]
        K8S_R["/kubernetes/*"]
        PROM_R["/prometheus/*"]
        GRAF_R["/grafana/*"]
        ALERT_R["/alertmanager/*"]
        GH_R["/github/*"]
        INC_R["/incidents/*"]
        DEP_R["/deployments/*"]
        ORCH_R["/orchestration/*"]
        ANALYTICS_R["/analytics/*"]
        DIAG_R["/diagnostics/*"]
    end

    AUTH_R --> AUTH
    DOCKER_R --> DOCKER_SVC
    K8S_R --> K8S_SVC
    PROM_R --> PROM_SVC
    GRAF_R --> GRAF_SVC
    ALERT_R --> ALERT_SVC
    GH_R --> GH_SVC
    INC_R --> INC_SVC
    DEP_R --> DEP_SVC

    ORCH_R --> INC_SVC
    ORCH_R --> K8S_SVC
    ORCH_R --> PROM_SVC
    ORCH_R --> DOCKER_SVC

    ANALYTICS_R --> DEP_SVC
    ANALYTICS_R --> INC_SVC
    ANALYTICS_R --> K8S_SVC

    DIAG_R --> AUTH
    DIAG_R --> DOCKER_SVC
    DIAG_R --> K8S_SVC
    DIAG_R --> PROM_SVC
    DIAG_R --> GRAF_SVC
    DIAG_R --> ALERT_SVC
    DIAG_R --> GH_SVC
```

## Database ER Diagram

```mermaid
erDiagram
    User ||--o{ ConnectedProject : connects
    ConnectedProject ||--o{ Deployment : triggers
    ConnectedProject ||--o{ Incident : relates
    Incident ||--o| AIAnalysisStore : analyzed_by
    AIAnalysisStore ||--o{ AIAnalysisCache : cached

    User {
        int id PK
        string username
        string email
        string role
        string github_token
        datetime created_at
    }

    ConnectedProject {
        int id PK
        int user_id FK
        string full_name
        string github_owner
        string github_repo
        string kubernetes_namespace
        string kubernetes_deployment
        datetime created_at
    }

    Deployment {
        int id PK
        string deployment_id UK
        int project_id FK
        string repository
        string commit_sha
        string branch
        string environment
        string status
        int workflow_run_id
        datetime started_at
        datetime completed_at
        string triggered_by
        boolean rollback_available
        text logs_json
        datetime created_at
    }

    Incident {
        int id PK
        string incident_id
        string title
        string description
        string status
        string severity
        string source
        int project_id FK
        int ai_analysis_id FK
        text timeline_json
        datetime created_at
        datetime resolved_at
        string resolution_reason
    }

    AIAnalysisStore {
        int id PK
        string incident_id FK
        text summary
        string root_cause
        float confidence
        text possible_causes_json
        text suggested_fixes_json
        text preventive_actions_json
        text risk_assessment
        string estimated_resolution_time
        boolean requires_human
        datetime analyzed_at
    }

    EventStore {
        int id PK
        int project_id FK
        string event_type
        string source
        text metadata_json
        datetime timestamp
    }

    Cluster {
        int id PK
        string name
        string status
        int node_count
        datetime created_at
    }
```

## Component Diagram

```mermaid
graph TB
    subgraph Pages
        DASHBOARD[Dashboard]
        DEPLOY[Deployments]
        CLUSTER[Kubernetes]
        INCIDENTS[Incidents]
        MONITOR[Observability]
        METRICS[Metrics]
        GRAFANA[Grafana Dashboards]
        ALERTS[Active Alerts]
        ANALYTICS[Analytics]
        DIAGNOSTICS[Diagnostics]
        ARCHITECTURE[Architecture]
        TIMELINE[Activity Timeline]
        GITHUB[GitHub]
        REPOS[Repositories]
        RCA[AI Analysis]
    end

    subgraph Components
        STATCARD[StatCard]
        DATATABLE[DataTable]
        LOGVIEWER[LogViewer]
        EMPTYSTATE[EmptyState]
        LOADING[LoadingSpinner]
        SKELETON[LoadingSkeleton]
        TOAST[ToastContainer]
        NETERROR[NetworkError]
        SIDEBAR[Sidebar]
        CHART[ResourceChart]
    end

    subgraph Services
        API_SVC[api.js]
        DOCKER_SVC[dockerService.js]
        K8S_SVC[kubernetesService.js]
        PROM_SVC[prometheusService.js]
        GRAF_SVC[grafanaService.js]
        ALERT_SVC[alertmanagerService.js]
        DEPLOY_SVC[deploymentService.js]
        INC_SVC[incidentService.js]
        ANAL_SVC[analyticsService.js]
        DIAG_SVC[diagnosticsService.js]
        ORCH_SVC[orchestrationService.js]
    end

    DASHBOARD --> STATCARD
    DASHBOARD --> NETERROR
    DASHBOARD --> LOADING
    DASHBOARD --> API_SVC

    DEPLOY --> DATATABLE
    DEPLOY --> STATCARD
    DEPLOY --> LOGVIEWER
    DEPLOY --> DEPLOY_SVC

    CLUSTER --> DATATABLE
    CLUSTER --> K8S_SVC

    INCIDENTS --> INC_SVC

    MONITOR --> STATCARD
    MONITOR --> PROM_SVC
    MONITOR --> GRAF_SVC
    MONITOR --> ALERT_SVC

    ANALYTICS --> ANAL_SVC
    ANALYTICS --> CHART

    DIAGNOSTICS --> DIAG_SVC

    TIMELINE --> ORCH_SVC

    SIDEBAR -->|Navigation| PAGES
    TOAST -->|Notifications| PAGES
    LOADING -->|Loading| PAGES
    SKELETON -->|Skeleton| PAGES
    EMPTYSTATE -->|Empty| PAGES
    NETERROR -->|Error| PAGES
```

## Container Architecture (Docker Compose)

```mermaid
graph TB
    subgraph docker-compose.yml
        NET[devflow_net<br/>bridge network]

        subgraph Services
            POSTGRES[postgres:15-alpine<br/>:5432]
            BACKEND[backend<br/>:5000]
            FRONTEND[frontend<br/>:8081]
            PROM[prom/prometheus:latest<br/>:9090]
            GRAF[grafana/grafana:latest<br/>:3000]
            ALERTMAN[prom/alertmanager:latest<br/>:9093]
        end

        subgraph Volumes
            PG_DATA[postgres_data]
            DEVFLOW_DB[devflow_db]
            PROM_DATA[prometheus_data]
            GRAF_DATA[grafana_data]
            ALERT_DATA[alertmanager_data]
        end

        subgraph Config
            PROM_YML[./monitoring/prometheus.yml]
            RULES_YML[./monitoring/prometheus-alert-rules.yml]
            AM_YML[./monitoring/alertmanager/alertmanager.yml]
            DS_YML[./monitoring/grafana/datasources/prometheus.yml]
            KUBECONFIG[./monitoring/kubeconfig-docker.yml]
            ENV_FILE[./backend/.env]
            DOCKER_SOCK[/var/run/docker.sock]
        end
    end

    POSTGRES --> NET
    BACKEND --> NET
    FRONTEND --> NET
    PROM --> NET
    GRAF --> NET
    ALERTMAN --> NET

    BACKEND --> PG_DATA
    BACKEND --> DEVFLOW_DB
    BACKEND --> DOCKER_SOCK
    BACKEND --> KUBECONFIG
    BACKEND --> ENV_FILE

    PROM --> PROM_DATA
    PROM --> PROM_YML
    PROM --> RULES_YML

    GRAF --> GRAF_DATA
    GRAF --> DS_YML

    ALERTMAN --> ALERT_DATA
    ALERTMAN --> AM_YML

    BACKEND -.->|healthcheck| POSTGRES
    BACKEND -.->|healthcheck| PROM
    BACKEND -.->|healthcheck| GRAF
    BACKEND -.->|healthcheck| ALERTMAN
    FRONTEND -.->|depends_on| BACKEND
    PROM -.->|scrape| BACKEND
    PROM -.->|alerts| ALERTMAN
    ALERTMAN -.->|webhook| BACKEND
```
