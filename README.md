# DevFlow — Cloud-Native DevOps Automation & Incident Orchestration Platform

**DevFlow** is a full-stack Internal Developer Platform (IDP) that connects your GitHub repositories to a unified DevOps pipeline — collecting events from Jenkins, Docker, Kubernetes, Prometheus, Grafana, and Alertmanager, then performing AI-driven root cause analysis via Groq AI.

---

## Architecture

```
GitHub Repo
    │
    ▼
┌─────────────────┐
│   Collectors    │  ← GitHub, Jenkins, Docker, K8s, Prometheus, Grafana, Alertmanager
└────────┬────────┘
         │ Events
         ▼
┌─────────────────┐
│  Event Store    │  → Typed events with severity scoring
└────────┬────────┘
         │ Correlation
         ▼
┌─────────────────┐
│   Incidents     │  → Deduplicated, aggregated, status-tracked
└────────┬────────┘
         │ Evidence + Timeline
         ▼
┌─────────────────┐
│  Groq AI RCA    │  → Llama 3.3 70B generates root cause analysis
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Dashboard     │  → Glass UI with metrics, charts, alerts
└─────────────────┘
```

### Repository Onboarding Flow

1. **Connect GitHub** → Authenticate with a personal access token
2. **Select a repository** → DevFlow fetches metadata, branches, commits, PRs
3. **Map DevOps services** → Optionally link Jenkins jobs, Docker containers, K8s namespaces, Prometheus alerts, Grafana dashboards
4. **Webhook registration** → GitHub webhooks forward push/PR/issue events to DevFlow
5. **Event ingestion** → Collectors push events to the EventStore
6. **Incident creation** → Correlated events become tracked incidents
7. **AI analysis** → Groq AI (Llama 3.3 70B) produces root cause analysis with evidence

---

## Features

- **GitHub Integration** — Connect repos, view commits, branches, PRs, manage webhooks
- **Event Orchestration** — Collect, correlate, and score events from 7 data sources
- **Incident Management** — Create, track, severity-score, and resolve incidents
- **AI Root Cause Analysis** — Groq-powered RCA with evidence and timeline context
- **Jenkins CI/CD** — Trigger builds, view pipeline status, job history
- **Docker Management** — Container lifecycle, image registry, compose stacks
- **Kubernetes Monitoring** — Namespaces, deployments, pods, services, events
- **Prometheus Metrics** — Query and visualize metrics from Prometheus
- **Grafana Dashboards** — Embed and link Grafana dashboards
- **Alertmanager** — View and manage alerts
- **Dashboard** — Aggregated metrics, resource charts, real-time monitoring
- **Glass UI** — Dark-themed glassmorphic design with fluid animations

---

## Tech Stack

### Backend
| Technology | Purpose |
|-----------|---------|
| Python 3.11 + Flask 2.3 | REST API framework |
| SQLAlchemy + SQLite | ORM and database |
| Flask-Migrate / Alembic | Schema migrations |
| Flask-JWT-Extended | JWT authentication |
| Gunicorn | Production WSGI server |
| Docker SDK | Container management |
| Kubernetes client | K8s API integration |
| Prometheus API client | Metrics queries |
| Grafana API client | Dashboard embedding |
| Jenkins API client | CI/CD pipeline control |
| Groq AI SDK | AI root cause analysis |

### Frontend
| Technology | Purpose |
|-----------|---------|
| React 19 + Vite | UI framework and build |
| React Router DOM v7 | Client-side routing |
| Recharts | Charts and graphs |
| React Icons (Feather) | Icon set |
| Axios | HTTP client |
| Glass UI (CSS) | Dark glassmorphic theme |

### Infrastructure
| Technology | Purpose |
|-----------|---------|
| Docker / Docker Compose | Containerization |
| Jenkins | CI/CD pipeline |
| Minikube / Kubernetes | Container orchestration |
| Prometheus | Metrics collection |
| Grafana | Metrics visualization |
| Alertmanager | Alert management |
| Nginx | Reverse proxy |

---

## Setup

### 1. Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate      # Linux/Mac
# .\.venv\Scripts\activate     # Windows
pip install -r requirements.txt
cp .env.example .env            # Edit with your credentials
flask db upgrade
python src/app.py
```

API runs on `http://localhost:5000`.

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

UI runs on `http://localhost:5173`.

### 3. Infrastructure (Docker)

```bash
docker compose up --build -d
```

- Backend: `http://localhost:5000`
- Frontend: `http://localhost:8081`
- Jenkins: `http://localhost:8080`

### 4. Kubernetes (Minikube)

```bash
minikube start
kubectl apply -f devflowcd/k8s/
```

### 5. Prometheus, Grafana, Alertmanager (on K8s)

Deploy via manifests in `devflowcd/` or your existing `monitoring` namespace.

---

## Demo

### 1. Connect a Repository
1. Log in with `admin` / `admin123`
2. Navigate to **GitHub → Connect Repository**
3. Enter a GitHub personal access token and select a repository
4. Optionally map Jenkins job, Docker container, K8s namespace

### 2. View the DevOps Dashboard
1. The **Dashboard** shows:
   - Active incidents and their severity distribution
   - Deployment health and recent deploys
   - Cluster CPU/memory utilization
   - Recent events from all collectors

### 3. Trigger a Failure
1. Push a commit to your connected repository (or use the Jenkins pipeline)
2. DevFlow collectors detect the event and create an incident
3. View it under **Incidents** with severity scoring

### 4. AI Root Cause Analysis
1. Open an incident detail page
2. Click **Analyze** → Groq AI processes evidence + timeline
3. Review the generated root cause, impact summary, and remediation steps
4. View the full evidence and timeline on dedicated pages

---

## Demo Credentials

- **Username:** `admin`
- **Password:** `admin123`

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/login` | Authenticate user |
| GET | `/api/v1/projects` | List projects |
| GET | `/api/v1/deployments` | List deployments |
| POST | `/api/v1/deployments` | Trigger deployment |
| POST | `/api/v1/deployments/:id/rollback` | Rollback deployment |
| GET | `/api/v1/clusters` | List clusters with metrics |
| GET | `/api/v1/clusters/:id/logs` | Get cluster logs |
| GET | `/api/v1/incidents` | List incidents |
| POST | `/api/v1/incidents` | Create incident |
| PATCH | `/api/v1/incidents/:id` | Update incident status |
| GET | `/api/v1/github/repos` | List connected repos |
| POST | `/api/v1/github/connect` | Connect a GitHub repo |
| GET | `/api/v1/orchestration/incidents` | Orchestration incidents |
| POST | `/api/v1/orchestration/analyze` | Trigger AI analysis |
| POST | `/api/v1/jenkins/build` | Trigger Jenkins build |
| GET | `/api/v1/docker/containers` | List Docker containers |
| GET | `/api/v1/kubernetes/namespaces` | List K8s namespaces |
| GET | `/api/v1/prometheus/query` | Query Prometheus metrics |
| GET | `/api/v1/grafana/dashboards` | List Grafana dashboards |
| GET | `/api/v1/alertmanager/alerts` | List Alertmanager alerts |
| GET | `/health` | Health check |

---

## Testing

```bash
cd backend
pytest tests/
# Or run the full acceptance suite:
python src/acceptance_test.py
```

---

## Environment Variables

See `backend/.env.example` for all configuration options. Key variables:

| Variable | Description |
|----------|-------------|
| `JWT_SECRET_KEY` | JWT signing secret (change in production) |
| `GITHUB_TOKEN` | GitHub personal access token |
| `JENKINS_URL` | Jenkins server URL |
| `PROMETHEUS_URL` | Prometheus endpoint |
| `GRAFANA_URL` | Grafana endpoint |
| `ALERTMANAGER_URL` | Alertmanager endpoint |
| `AI_PROVIDER` | `groq`, `openai`, `ollama`, or `openai-compatible` |
| `GROQ_API_KEY` | Groq API key (for `groq` provider) |

Frontend: set `VITE_API_BASE_URL` in `frontend/.env` to point to your backend.

---

## Project Structure

```
devflow/
├── backend/
│   ├── src/
│   │   ├── config/              # Environment-based configuration
│   │   ├── models/              # SQLAlchemy models
│   │   ├── routes/              # API route blueprints
│   │   ├── services/            # Business logic layer
│   │   ├── orchestration/       # Event collectors, AI, correlation engine
│   │   ├── utils/               # Logging, time helpers, seed data
│   │   ├── extensions.py        # Flask extension init
│   │   └── app.py               # Application factory
│   ├── migrations/              # Alembic schema migrations
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/          # Reusable UI components
│   │   ├── pages/               # Page-level components
│   │   ├── services/            # API service layer
│   │   ├── hooks/               # Custom React hooks
│   │   ├── contexts/            # React context providers
│   │   ├── layouts/             # Layout components
│   │   └── App.jsx              # Root with routing
│   ├── Dockerfile
│   └── package.json
├── database/                    # SQLite DB (auto-created)
├── devflowcd/                   # K8s manifests
├── docker-compose.yml
├── Jenkinsfile
└── README.md
```
