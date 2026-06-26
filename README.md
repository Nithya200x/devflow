# DevFlow: Cloud-Native Microservices-based DevOps Automation and Issue Orchestration Platform

**DevFlow** is a modern, full-stack Internal Developer Platform (IDP) that showcases platform engineering, observability, and infrastructure automation patterns. It features JWT-authenticated project management, CI/CD orchestration, cluster monitoring, and incident management.

---

## Features

- **JWT Authentication** with auto-logout and 401 redirect
- **Project Management** for connected repositories
- **Deployments & Rollbacks** with simulated CI/CD pipelines
- **Cluster Monitoring** with real-time CPU/Memory metrics and live logs
- **Incident Management** with severity tracking and resolution
- **Dashboard** with aggregated platform metrics and resource charts
- **Glassmorphic UI** with dark theme and fluid animations

---

## Technology Stack

### Frontend
- **Framework:** React 19 (Vite)
- **Routing:** React Router DOM v7
- **Charts:** Recharts
- **Icons:** React Icons (Feather)
- **Styling:** Vanilla CSS with CSS Variables

### Backend
- **Framework:** Python 3.11 / Flask 2.3
- **Database:** SQLite (SQLAlchemy ORM)
- **Migrations:** Alembic (Flask-Migrate)
- **Authentication:** Flask-JWT-Extended
- **Server:** Gunicorn

### Infrastructure
- **Containerization:** Docker & Docker Compose
- **CI/CD:** Jenkins Pipeline
- **Orchestration:** Kubernetes Manifests
- **Reverse Proxy:** Nginx

---

## Project Structure

```
devflow-main/
├── backend/
│   ├── src/
│   │   ├── config/
│   │   │   └── config.py              # Environment-based configuration
│   │   ├── models/
│   │   │   └── __init__.py            # User, Project, Cluster, Deployment, Incident
│   │   ├── routes/
│   │   │   ├── auth.py                # Login endpoint
│   │   │   ├── projects.py            # Project CRUD
│   │   │   ├── deployments.py         # Deploy & rollback
│   │   │   ├── clusters.py            # Cluster metrics & logs
│   │   │   ├── incidents.py           # Incident management
│   │   │   └── health.py              # Health check
│   │   ├── services/
│   │   │   ├── auth_service.py        # Authentication business logic
│   │   │   ├── project_service.py     # Project business logic
│   │   │   ├── deployment_service.py  # Deployment & rollback logic
│   │   │   ├── cluster_service.py     # Cluster metrics & logs
│   │   │   └── incident_service.py    # Incident business logic
│   │   ├── utils/
│   │   │   ├── logging.py             # Logging configuration
│   │   │   └── seed.py                # Mock data seeding
│   │   ├── extensions.py              # Flask extension initialization
│   │   ├── app.py                     # Application factory
│   │   ├── static/
│   │   └── templates/
│   ├── migrations/                    # Alembic migrations
│   ├── tests/
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Sidebar/               # Navigation sidebar
│   │   │   ├── Navbar/                # Top navigation
│   │   │   ├── Cards/                 # StatCard component
│   │   │   ├── Charts/                # ResourceChart component
│   │   │   ├── Tables/                # DataTable component
│   │   │   ├── Terminal/              # LogViewer component
│   │   │   └── Common/                # Loading, Error, EmptyState components
│   │   ├── pages/
│   │   │   ├── Dashboard/             # Platform overview with metrics
│   │   │   ├── Projects/              # Project listing
│   │   │   ├── Deployments/           # Deployment & rollback
│   │   │   ├── Clusters/              # Cluster monitoring & logs
│   │   │   ├── Incidents/             # Incident management
│   │   │   └── Login/                 # Authentication
│   │   ├── services/
│   │   │   ├── api.js                 # Axios instance with interceptors
│   │   │   ├── authService.js         # Login API
│   │   │   ├── projectService.js      # Projects API
│   │   │   ├── deploymentService.js   # Deployments API
│   │   │   ├── clusterService.js      # Clusters API
│   │   │   └── incidentService.js     # Incidents API
│   │   ├── hooks/
│   │   │   ├── useAuth.js             # Auth context hook
│   │   │   └── usePolling.js          # Generic polling hook
│   │   ├── contexts/
│   │   │   └── AuthContext.jsx        # Auth provider with JWT management
│   │   ├── layouts/
│   │   │   └── AppLayout.jsx          # Protected layout with sidebar
│   │   ├── utils/
│   │   │   ├── constants.js           # Route paths, status constants
│   │   │   └── helpers.js             # Formatting utilities
│   │   ├── config/
│   │   │   └── config.js              # Frontend configuration
│   │   ├── styles/                    # Additional styles
│   │   ├── App.jsx                    # Root with routing
│   │   ├── App.css
│   │   ├── main.jsx                   # Entry point
│   │   └── index.css                  # Global styles
│   ├── public/
│   ├── .env.example
   ├── Dockerfile
│   └── package.json
├── database/                          # SQLite database (auto-created)
├── devflowcd/                         # CI/CD configuration
├── docker-compose.yml
├── Jenkinsfile
└── README.md
```

---

## Getting Started

### Option 1: Docker (Recommended)

```bash
docker-compose up --build -d
```

Open **http://localhost** in your browser.

### Option 2: Run Locally (Development)

**1. Backend**

```bash
cd backend
python -m venv .venv
.\.venv\Scripts\activate      # Windows
pip install -r requirements.txt
flask db upgrade
python src/app.py
```

The API will listen on `http://localhost:5000`.

**2. Frontend**

```bash
cd frontend
npm install
npm run dev
```

The UI will listen on `http://localhost:5173`.

---

## Environment Variables

### Backend (`backend/.env`)

| Variable | Default | Description |
|----------|---------|-------------|
| `FLASK_DEBUG` | `false` | Enable debug mode |
| `PORT` | `5000` | Server port |
| `JWT_SECRET_KEY` | *(change in prod)* | JWT signing secret |
| `JWT_EXPIRY_HOURS` | `24` | Token expiration |
| `DATABASE_URL` | `sqlite:///../database/app.db` | Database connection string |

### Future Integration Variables (optional)

| Variable | Description |
|----------|-------------|
| `GITHUB_TOKEN` | GitHub Personal Access Token |
| `JENKINS_URL` | Jenkins server URL |
| `KUBE_CONFIG_PATH` | Kubernetes config file path |
| `PROMETHEUS_URL` | Prometheus endpoint |
| `GRAFANA_URL` / `GRAFANA_API_KEY` | Grafana credentials |
| `JIRA_URL` / `JIRA_EMAIL` / `JIRA_API_TOKEN` | Jira credentials |
| `SLACK_WEBHOOK_URL` | Slack notification webhook |
| `SMTP_*` | Email notification credentials |
| `OPENAI_API_KEY` | AI feature API key |

### Frontend (`frontend/.env`)

| Variable | Default | Description |
|----------|---------|-------------|
| `VITE_API_BASE_URL` | `http://localhost:5000/api/v1` | Backend API URL |

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
| GET | `/health` | Health check |

---

## Testing

```bash
cd backend
pytest tests/
```

Frontend lint:
```bash
cd frontend
npm run lint
```
