# DevFlow: Internal Developer Platform

**DevFlow** is a full-stack Internal Developer Platform (IDP) with **GitHub integration** and a built-in **orchestration engine**. It provides repository management, CI/CD pipeline orchestration, cluster monitoring, and incident management through a modern React dashboard and Flask REST API.

---

## Features

### GitHub Integration
- **Repository-linked Projects** – Each project is tied to a GitHub repository URL for end-to-end traceability
- **Deployment Pipeline** – Trigger deployments per repository to Dev, Staging, or Production environments
- **Rollback Support** – One-click rollback of any previously successful deployment

### Orchestration Engine
- **Stateful Pipeline Lifecycle** – Deployments transition through `running` -> `success` / `failed` states with 30-second auto-completion
- **Cluster Telemetry** – CPU/memory metrics spike dynamically during active deployments to simulate real container startup load
- **Live Log Streaming** – Context-aware terminal logs reflect deployment activity vs baseline cluster health

### Platform Management
- **Incident Tracking** – Create, investigate, and resolve incidents with severity levels
- **RBAC** – JWT-authenticated admin/developer roles with protected API routes
- **Auto-seeded Mock Data** – Pre-populated users, projects, deployments, clusters, and incidents on first run

### UI/UX
- **Glassmorphic Design** – Dark-mode SPA with backdrop blur, fluid animations, and responsive layout
- **Real-time Dashboard** – Recharts-based CPU/Memory area chart with 5-second polling on cluster views

---

## Technology Stack

| Layer | Tech |
|-------|------|
| Frontend | React 19, Vite 8, React Router 7, Recharts, Lucide React Icons |
| Backend | Python 3.10, Flask 2.3, SQLAlchemy 2.0, Alembic |
| Database | SQLite (persistent volume in Docker) |
| Auth | Flask-JWT-Extended (Bearer tokens), bcrypt password hashing |
| DevOps | Docker Compose, Jenkins (Jenkinsfile included), Kubernetes manifests (`devflowcd/`) |

---

## Architecture

```
┌──────────┐       ┌──────────────────┐       ┌──────────┐
│  Browser │──────>│  Flask REST API   │──────>│ SQLite   │
│  :5173   │<──────│  :5000/api/v1/   │<──────│ app.db   │
└──────────┘       └──────────────────┘       └──────────┘
                          │
                    ┌─────┴──────┐
                    │ GitHub     │
                    │ Repos      │
                    └────────────┘
```

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/login` | JWT login (admin/dev) |
| GET | `/api/v1/projects` | List all projects |
| GET/POST | `/api/v1/deployments` | List / trigger deployments |
| POST | `/api/v1/deployments/:id/rollback` | Rollback a deployment |
| GET | `/api/v1/clusters` | Cluster list with live telemetry |
| GET | `/api/v1/clusters/:id/logs` | Live cluster logs |
| GET/POST | `/api/v1/incidents` | List / create incidents |
| PATCH | `/api/v1/incidents/:id` | Update incident status |

---

## Getting Started

### Docker (Recommended)

```bash
docker-compose up --build -d
open http://localhost
```

### Local Development

**Backend:**
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate    # Windows
pip install -r requirements.txt
$env:PYTHONPATH = "src"; python src/app.py
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

---

## Credentials

| Username | Password | Role |
|----------|----------|------|
| `admin` | `admin123` | admin |
| `developer` | `dev123` | developer |

---

## Project Structure

```
├── backend/
│   ├── src/
│   │   ├── app.py          # Flask app factory & routes
│   │   ├── api.py          # REST API blueprint
│   │   ├── models.py       # SQLAlchemy models
│   │   ├── templates/      # Server-rendered pages
│   │   └── static/         # CSS assets
│   ├── migrations/         # Alembic DB migrations
│   ├── tests/              # Pytest suite
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── main.jsx        # React entry point
│   │   ├── App.jsx         # Router & layout
│   │   ├── components.jsx  # All UI components
│   │   └── index.css       # Global styles
│   └── package.json
├── devflowcd/              # Kubernetes manifests
├── database/               # SQLite data (Docker volume)
├── docker-compose.yml
└── Jenkinsfile
```

---

## CI/CD Pipeline (Jenkins)

The included `Jenkinsfile` defines a multi-stage pipeline:

1. **Test** – Run backend pytest suite
2. **Build** – Build Docker images for backend & frontend
3. **Push** – Push images to registry
4. **Deploy** – Apply `devflowcd/kustomization.yml` to Kubernetes

---

## Roadmap

- [ ] Real Kubernetes client integration for live cluster management
- [ ] GitHub Webhook receiver for automated deployment triggers
- [ ] PostgreSQL support for production-scale deployments
- [ ] WebSocket-based log streaming (replace HTTP polling)
