# Deployment Guide

## Prerequisites

- Docker Desktop 4.29+ with Docker Compose
- minikube v1.35+ (for Kubernetes features)
- Git
- GitHub Personal Access Token with `repo` and `workflow` scopes
- Groq API Key (for AI Root Cause Analysis)

---

## Quick Start (Docker Compose)

### 1. Clone and Configure

```bash
git clone https://github.com/Nithya200x/devflow.git
cd devflow
cp .env.example .env
```

### 2. Edit `.env`

```bash
# Required for AI analysis
GROQ_API_KEY=gsk_your_key_here
AI_PROVIDER=groq

# Required for GitHub integration
GITHUB_TOKEN=ghp_your_token_here

# Change in production
JWT_SECRET_KEY=your-strong-secret-key
TOKEN_ENCRYPTION_KEY=your-encryption-key
```

### 3. Start the Stack

```bash
docker compose up -d
```

### 4. Verify All Services

```bash
# Check container status
docker compose ps

# Expected output:
# Name                    Status
# devflow-backend         Up (healthy)
# devflow-frontend        Up
# devflow-postgres        Up (healthy)
# devflow-prometheus      Up
# devflow-grafana         Up
# devflow-alertmanager    Up
```

### 5. Access Services

| Service | URL | Credentials |
|---------|-----|-------------|
| DevFlow UI | http://localhost:8081 | Login via JWT |
| Backend API | http://localhost:5000 | — |
| Prometheus | http://localhost:9090 | — |
| Grafana | http://localhost:3000 | `admin` / `devflow` |
| Alertmanager | http://localhost:9093 | — |

### 6. Login

Default admin credentials:
- Username: `admin`
- Password: `admin123`

---

## Kubernetes Deployment (minikube)

### 1. Start minikube

```bash
minikube start --cpus=4 --memory=8g
```

### 2. Deploy the Stack

```bash
# Create namespace
kubectl apply -f backend/k8s/01-namespace.yaml

# Deploy PostgreSQL
kubectl apply -f backend/k8s/02-postgres.yaml

# Deploy backend
kubectl apply -f backend/k8s/03-backend.yaml

# Deploy frontend
kubectl apply -f backend/k8s/04-frontend.yaml

# Deploy monitoring stack
kubectl apply -f backend/k8s/prometheus/
```

---

## Production Deployment

### Docker Compose (Single Host)

1. **Set strong secrets** in `.env`:
   - `JWT_SECRET_KEY` — minimum 32 characters
   - `TOKEN_ENCRYPTION_KEY` — minimum 32 characters
   - `POSTGRES_PASSWORD` — strong password

2. **Configure CORS**:
   - Set `VITE_API_URL` to your backend domain
   - The backend auto-restricts CORS when `FRONTEND_URL` is set

3. **Enable HTTPS**:
   - Add a reverse proxy (nginx/traefik) in front of the frontend
   - Configure SSL certificates via Let's Encrypt

4. **Persistent Storage**:
   - PostgreSQL, Prometheus, and Grafana data persists in Docker volumes
   - Backup `postgres_data` volume regularly

5. **Health Checks**:
   - Backend: `GET /health` returns `{"status": "up"}`
   - Docker healthcheck configured at container level
   - Prometheus scrapes every 10s

### Production Security Checklist

- [ ] Change all default passwords
- [ ] Set `JWT_SECRET_KEY` to a strong random value
- [ ] Restrict CORS origins via `FRONTEND_URL`
- [ ] Store secrets in `.env` (not in docker-compose.yml)
- [ ] Run backend as non-root user (already configured)
- [ ] Enable Docker BuildKit for secure builds
- [ ] Use `DOCKER_HOST: unix:///var/run/docker.sock` (not TCP)

---

## Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `JWT_SECRET_KEY` | Yes | `devflow-super-secret-key-change-in-prod` | JWT signing secret |
| `DATABASE_URL` | No | `postgresql://devflow:devflow@postgres:5432/devflow` | DB connection string |
| `GROQ_API_KEY` | For AI | — | Groq API key for AI analysis |
| `AI_PROVIDER` | No | `groq` | AI provider (groq/openai/ollama) |
| `AI_TIMEOUT` | No | `120` | AI analysis timeout in seconds |
| `GITHUB_TOKEN` | For CI/CD | — | GitHub PAT for workflow dispatch |
| `PROMETHEUS_URL` | No | `http://prometheus:9090` | Prometheus server URL |
| `GRAFANA_URL` | No | `http://grafana:3000` | Grafana server URL |
| `GRAFANA_USER` | No | `admin` | Grafana admin username |
| `GRAFANA_PASSWORD` | No | `devflow` | Grafana admin password |
| `ALERTMANAGER_URL` | No | `http://alertmanager:9093` | Alertmanager URL |
| `FLASK_ENV` | No | `production` | Flask environment |
| `ADMIN_USERNAME` | First run | — | Initial admin username |
| `ADMIN_EMAIL` | First run | — | Initial admin email |
| `ADMIN_PASSWORD` | First run | — | Initial admin password |

---

## Secrets Management

### GitHub Token

1. Go to GitHub Settings → Developer settings → Personal access tokens → Fine-grained tokens
2. Create token with permissions: `Contents: read`, `Actions: read/write`, `Metadata: read`
3. Set `GITHUB_TOKEN` in `.env`

### Groq API Key

1. Visit https://console.groq.com/keys
2. Create an API key
3. Set `GROQ_API_KEY` in `.env`

### Encryption Key

The `TOKEN_ENCRYPTION_KEY` is used to encrypt stored GitHub tokens in the database.
Generate a 32-character key:
```bash
python -c "import secrets; print(secrets.token_hex(16))"
```

---

## Common Errors

### Docker socket permission denied

**Error**: `PermissionError: [Errno 13] Permission denied: /var/run/docker.sock`

**Fix**: The docker-compose.yml already includes `group_add: ["0"]`. Ensure the backend container runs as a user with Docker socket access.

### Kubernetes connection refused

**Error**: `Connection refused` when accessing K8s API

**Fix**:
1. Verify minikube is running: `minikube status`
2. Check kubeconfig: `kubectl cluster-info`
3. Inside container, use `host.docker.internal:PORT` instead of `127.0.0.1:PORT`
4. Mount kubeconfig and minikube certs in docker-compose.yml

### Grafana "Invalid Username or Password"

**Fix**: Default credentials are `admin` / `devflow`. Reset password via:
```bash
docker compose exec grafana grafana-cli admin reset-admin-password
```

### Alertmanager not connected

**Fix**:
1. Ensure Alertmanager container is running: `docker compose ps alertmanager`
2. Check config: `docker compose exec alertmanager amtool check-config /etc/alertmanager/alertmanager.yml`
3. Verify Prometheus can reach it: Check Prometheus targets at http://localhost:9090/targets

### Worker timeout

Backend workers being killed after ~6 minutes:
1. Increase gunicorn `--timeout` (currently 300s)
2. Reduce AI `AI_TIMEOUT` or increase `AI_MAX_CONCURRENT_REQUESTS`

### Frontend build fails

**Error**: `Module not found: FiWebhook`

**Fix**: The FiWebhook icon was removed from react-icons/fi. Replace with `FiLink` in `RepositorySettings/index.jsx`.

---

## Architecture Diagram

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│  Frontend    │────▶│  Backend API │────▶│  PostgreSQL  │
│  (React)     │     │  (Flask)     │     │              │
└─────────────┘     └──────┬───────┘     └──────────────┘
                           │
                    ┌──────┴───────┐
                    │ Orchestration│
                    │  Engine      │
                    └──────┬───────┘
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
  ┌──────────┐      ┌──────────┐      ┌──────────┐
  │Prometheus│──────▶│Alertman. │──────▶│  Groq AI │
  └──────────┘      └──────────┘      └──────────┘
        ▼                  ▼
  ┌──────────┐      ┌──────────┐
  │ Grafana  │      │  Docker  │
  └──────────┘      └──────────┘
                           │
                    ┌──────┴───────┐
                    │ Kubernetes   │
                    └──────────────┘
```

## Monitoring Stack

```
┌─────────────────────────────────────────────────────┐
│                    Prometheus                        │
│  scrape_interval: 10s (backend), 15s (self)         │
│  evaluation_interval: 15s                           │
│  rule_files: prometheus-alert-rules.yml             │
│  alertmanagers: alertmanager:9093                   │
└─────────────────────┬───────────────────────────────┘
                      │ alerts
                      ▼
┌─────────────────────────────────────────────────────┐
│                  Alertmanager                        │
│  route: severity-based routing                      │
│  receiver: webhook → http://backend:5000/.../webhook │
│  inhibit_rules: critical inhibits warning           │
└─────────────────────┬───────────────────────────────┘
                      │ webhook
                      ▼
┌─────────────────────────────────────────────────────┐
│           Backend Webhook Handler                    │
│  → Maps alerts to OrchestrationEvent                │
│  → Creates incidents via orchestration engine       │
│  → Triggers AI analysis                              │
└─────────────────────────────────────────────────────┘
```

## Prometheus Alert Rules

| Alert | Severity | Condition | For |
|-------|----------|-----------|-----|
| DevFlowHighCPU | Warning | Request processing rate > 0.1 | 1m |
| DevFlowHighMemory | Warning | Resident memory > 100 MB | 1m |
| DevFlowHighErrorRate | Critical | 5xx rate > 0.05 req/s | 1m |
| DevFlowServiceDown | Critical | Backend up == 0 | 15s |
| DevFlowHTTPLatencyHigh | Warning | P95 latency > 2s | 1m |
| PrometheusTargetMissing | Critical | Any target down | 30s |
| DevFlowPodCrashLoopBackOff | Critical | Pod in CrashLoopBackOff | 15s |
| DevFlowDeploymentFailure | Critical | Unavailable replicas > 0 | 15s |
| DevFlowNodeDown | Critical | Node not ready | 1m |
| DevFlowPodRestarting | Warning | Restart rate > 1/15m | 1m |

## Health Check Endpoints

| Service | Endpoint | Expected |
|---------|----------|----------|
| Backend | `GET /health` | `{"status": "up"}` |
| Docker | `GET /api/v1/docker/health` | `{"connected": true}` |
| Kubernetes | `GET /api/v1/kubernetes/health` | `{"connected": true}` |
| Prometheus | `GET /api/v1/prometheus/health` | `{"connected": true}` |
| Grafana | `GET /api/v1/grafana/health` | `{"connected": true}` |
| Alertmanager | `GET /api/v1/alertmanager/health` | `{"connected": true}` |
| GitHub | `GET /api/v1/github/status` | `{"connected": true}` |

## Troubleshooting Commands

```bash
# View all logs
docker compose logs -f

# View backend logs only
docker compose logs -f backend

# Restart a service
docker compose restart backend

# Rebuild a service
docker compose build backend
docker compose up -d backend

# Check Prometheus targets
curl http://localhost:9090/api/v1/targets | jq

# Check Alertmanager status
curl http://localhost:9093/api/v2/status | jq

# Run system diagnostics (authenticated)
curl -H "Authorization: Bearer <token>" http://localhost:5000/api/v1/diagnostics
```
