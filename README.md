# DevFlow

> AI-Powered DevOps Incident Detection & Resolution Platform

DevFlow is a comprehensive DevOps platform that integrates GitHub, Docker, Kubernetes, Prometheus, Grafana, and Alertmanager into a unified dashboard with AI-driven root cause analysis and incident management.

---

## Problem Statement

Modern DevOps teams face challenges in correlating alerts across fragmented monitoring tools, identifying root causes during incidents, and maintaining visibility across the entire deployment pipeline from code commit to production.

## Objectives

- **Unified Observability** — Single dashboard for GitHub, Docker, Kubernetes, Prometheus, Grafana, and Alertmanager
- **Automated Incident Detection** — Prometheus-based alert rules with automatic incident creation
- **AI Root Cause Analysis** — Groq-powered analysis of incidents with fix suggestions and risk assessment
- **CI/CD Orchestration** — GitHub Actions workflow dispatch, Kubernetes rollout tracking, rollback support
- **Real-time Monitoring** — Live metrics, deployment history, and activity timeline

## Novelty

- **Orchestration Engine** — Unified event system that correlates signals across 6 collectors (GitHub, Docker, K8s, Prometheus, Grafana, Jenkins) into actionable incidents
- **AI-Enhanced RCA** — Integration with Groq (Llama 3.3 70B) for automated root cause analysis, confidence scoring, and fix recommendation
- **Containerized Stack** — Full observability stack (Prometheus + Grafana + Alertmanager) deployable in a single Docker Compose command
- **Auto-Provisioned Monitoring** — Grafana datasources and Alertmanager routes configured at startup with no manual setup

---

## System Architecture

```
Frontend (React + Vite)
    │
    ▼
Backend API (Flask + gunicorn)
    │
    ├──► PostgreSQL
    ├──► Orchestration Engine
    │       ├── GitHub Collector
    │       ├── Docker Collector
    │       ├── Kubernetes Collector
    │       ├── Prometheus Collector
    │       ├── Grafana Collector
    │       └── Jenkins Collector
    ├──► Prometheus ──► Alertmanager ──► Webhook
    ├──► Grafana
    └──► Groq AI (RCA)
```

## Technology Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | React 19, Vite 8, Recharts, react-icons, React Router 7 |
| **Backend** | Flask, gunicorn, SQLAlchemy, Flask-JWT-Extended, Flask-CORS |
| **Database** | PostgreSQL 15 (production), SQLite (development) |
| **Container** | Docker, Docker Compose |
| **Orchestration** | Kubernetes (minikube) |
| **Monitoring** | Prometheus 3.x, Grafana 13.x, Alertmanager |
| **AI** | Groq API (Llama 3.3 70B) |
| **CI/CD** | GitHub Actions |
| **Auth** | JWT (JSON Web Tokens), bcrypt |

## Folder Structure

```
devflow/
├── backend/
│   ├── src/
│   │   ├── app.py              # Flask application factory
│   │   ├── config/             # Configuration classes
│   │   ├── routes/             # API route handlers
│   │   ├── services/           # Service integrations
│   │   ├── orchestration/      # Event engine & AI analysis
│   │   ├── models/             # Database models
│   │   ├── utils/              # Utilities (encryption, time, metrics)
│   │   └── extensions.py       # Flask extensions (db, jwt, migrate)
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── pages/              # Route pages (23 pages)
│   │   ├── components/         # Reusable components
│   │   ├── services/           # API service layer
│   │   ├── contexts/           # Auth context
│   │   ├── hooks/              # Custom hooks (usePolling, useAuth)
│   │   └── utils/              # Helper functions
│   ├── Dockerfile
│   └── package.json
├── monitoring/
│   ├── prometheus.yml
│   ├── prometheus-alert-rules.yml
│   ├── alertmanager/alertmanager.yml
│   ├── grafana/datasources/prometheus.yml
│   └── kubeconfig-docker.yml
├── k8s/                        # Kubernetes manifests
├── docker-compose.yml          # Full stack orchestration
└── .env.example
```

## Features

### Observability
- **Prometheus Integration** — Query metrics, view scrape targets, alert rules
- **Grafana Integration** — Dashboard management, datasource provisioning
- **Alertmanager** — Alert routing, silencing, webhook to orchestration engine
- **Live Dashboard** — Real-time metrics with auto-refresh

### Kubernetes
- **Cluster Monitoring** — Nodes, pods, deployments, services, ingresses
- **Cluster Topology** — Visual hierarchy (Cluster → Namespace → Deployment → Pod)
- **Rollout Tracking** — Deployment status, rollback support

### Incident Management
- **Auto-Detection** — Prometheus alert rules trigger incidents automatically
- **AI Root Cause Analysis** — Groq-powered analysis with confidence scoring
- **Timeline** — Full event chain from detection to resolution
- **Evidence Collection** — 6 collectors gather context from all integrated services

### CI/CD
- **GitHub Actions** — Workflow dispatch, commit tracking
- **Deployment History** — Full log viewer with search and download
- **Rollback** — One-click rollback with Kubernetes patch support

### Analytics & Diagnostics
- **Analytics Dashboard** — Deployment success rate, incident trends, CPU/memory/error trends
- **System Diagnostics** — One-click health check for all 9 services
- **Activity Timeline** — Chronological event feed with filtering

## Installation

### Prerequisites

- Docker Desktop 4.x+
- Node.js 18+ (for frontend development)
- Python 3.11+ (for backend development)
- Git

### Quick Start (Docker Compose)

```bash
# Clone the repository
git clone https://github.com/Nithya200x/devflow.git
cd devflow

# Create environment file
cp .env.example .env
# Edit .env with your API keys (Groq, GitHub token)

# Start all services
docker compose up -d

# Access the application
# Frontend: http://localhost:8081
# Backend API: http://localhost:5000
# Prometheus: http://localhost:9090
# Grafana: http://localhost:3000 (admin/devflow)
# Alertmanager: http://localhost:9093
```

### Kubernetes Deployment

```bash
# Deploy to minikube
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `JWT_SECRET_KEY` | Secret for JWT token signing | `devflow-super-secret-key-change-in-prod` |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://devflow:devflow@postgres:5432/devflow` |
| `GROQ_API_KEY` | Groq API key for AI analysis | — |
| `AI_PROVIDER` | AI provider (groq/openai/ollama) | `groq` |
| `GITHUB_TOKEN` | GitHub Personal Access Token | — |
| `PROMETHEUS_URL` | Prometheus server URL | `http://prometheus:9090` |
| `GRAFANA_URL` | Grafana server URL | `http://grafana:3000` |
| `GRAFANA_USER` | Grafana admin username | `admin` |
| `GRAFANA_PASSWORD` | Grafana admin password | `devflow` |
| `ALERTMANAGER_URL` | Alertmanager API URL | `http://alertmanager:9093` |

## API Overview

| Endpoint | Description |
|----------|-------------|
| `GET /health` | Backend health check |
| `POST /api/v1/auth/login` | User authentication |
| `GET /api/v1/docker/*` | Docker operations |
| `GET /api/v1/kubernetes/*` | Kubernetes operations |
| `GET /api/v1/prometheus/*` | Prometheus queries |
| `GET /api/v1/grafana/*` | Grafana management |
| `GET /api/v1/alertmanager/*` | Alertmanager management |
| `GET /api/v1/deployments/*` | Deployment lifecycle |
| `GET /api/v1/incidents/*` | Incident management |
| `GET /api/v1/orchestration/*` | Orchestration engine |
| `GET /api/v1/analytics/*` | Analytics dashboard |
| `GET /api/v1/diagnostics` | System diagnostics |
| `GET /api/v1/github/*` | GitHub integration |

## Screenshots

*Dashboard* — System health matrix, recent activity, connected projects
*Observability* — Prometheus/Grafana/Alertmanager status, metric navigation
*Kubernetes* — Cluster health, topology, pods/deployments/services tables
*Incidents* — Expandable incident list with AI recommendations
*Analytics* — Deployment stats, incident trends, performance metrics
*Architecture* — Interactive system component diagram
*Activity Timeline* — Chronological event feed with filtering

## Database Schema

- **User** — Authentication, roles, GitHub token
- **ConnectedProject** — GitHub repository connections
- **Deployment** — CI/CD deployment records with logs
- **Incident** — Auto-detected incidents with timeline
- **EventStore** — Orchestration event history
- **AIAnalysisStore** — AI analysis results with root cause, confidence, fixes
- **DetectorConfig** — Prometheus alert rule configurations
- **Cluster** — Kubernetes cluster definitions

## API Documentation

Full API documentation with request/response examples is available in [API.md](./API.md).

## Deployment Guide

See [DEPLOYMENT.md](./DEPLOYMENT.md) for detailed setup instructions including:
- Local development setup
- Docker Compose deployment
- Kubernetes deployment
- Production considerations
- Common errors and troubleshooting

## Future Scope

- **Notification Channels** — Slack, email, PagerDuty integration
- **Multi-cluster Support** — Monitor multiple Kubernetes clusters
- **Custom Dashboards** — User-defined Grafana dashboards
- **Pipeline as Code** — Custom deployment pipeline definitions
- **RBAC** — Role-based access control per project
- **SLA Tracking** — Service level agreement monitoring
- **Cost Analytics** — Cloud resource cost tracking

## License

MIT License — see [LICENSE](./LICENSE)

## Contributors

- [Nithya200x](https://github.com/Nithya200x) — Lead Developer
- [Barath-s-05](https://github.com/Barath-s-05) — Infrastructure & DevOps

## Troubleshooting

### Docker socket permission denied
Add `group_add: ["0"]` to the backend service in docker-compose.yml.

### Kubernetes connection refused
Ensure minikube is running (`minikube status`). The kubeconfig must point to `host.docker.internal:PORT` inside containers.

### Grafana login failed
Default credentials: `admin` / `devflow`. Reset via `GF_SECURITY_ADMIN_PASSWORD` environment variable.

### Alertmanager shows disconnected
Ensure the Alertmanager container is running (`docker ps | grep alertmanager`). Check config at `monitoring/alertmanager/alertmanager.yml`.

### AI analysis not triggering
Verify `GROQ_API_KEY` is set in the environment. Check backend logs for AI provider initialization.
