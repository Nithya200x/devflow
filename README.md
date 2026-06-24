# DevFlow: Internal Developer Platform Simulator

**DevFlow** is a modern, full-stack Internal Developer Platform (IDP) simulator. Designed as a portable demonstration environment, it showcases platform engineering, observability, and infrastructure automation patterns without requiring expensive, live cloud infrastructure.

This project is built to demonstrate modern full-stack development, API design, JWT-based security, stateful telemetry simulation, and Docker orchestration—making it a perfect portfolio piece for DevOps, SRE, and Full-Stack Engineering roles.

---

## 🚀 Features

### 1. Telemetry & Observability Simulation
- **Live Metrics Dashboard:** A React-powered dashboard utilizing `recharts` to render real-time, simulated telemetry data (CPU/Memory utilization).
- **Dynamic Workload Responses:** When a deployment is triggered, the backend statefully spikes cluster CPU and Memory metrics to >85% for exactly 30 seconds to simulate container startup loads.
- **Streaming Log Terminal:** A custom glassmorphic terminal UI that polls contextual, deployment-specific lifecycle logs during active deployments, reverting to generic cluster health logs during baseline operations.

### 2. CI/CD Pipeline Orchestration (Mocked)
- **Deployment Triggers:** Users can trigger deployments for specific repositories to specific environments (Dev, Staging, Prod).
- **Rollbacks:** Includes the ability to instantly trigger rollback deployments for previously successful pipelines.
- **Auto-completion:** The backend maintains an asynchronous state, automatically transitioning running pipelines to "success" after a defined timeout.

### 3. Enterprise-Grade Security & Access
- **JWT Authentication:** Secure stateless authentication powered by `Flask-JWT-Extended`.
- **Role-Based Access Control (RBAC):** Users are assigned `admin` or `developer` roles.
- **Password Hashing:** Passwords are cryptographically hashed using `bcrypt` before database storage.

### 4. Modern Glassmorphic UX
- **Custom UI System:** Built entirely with Vanilla CSS (no bloated UI libraries) featuring deep dark-mode aesthetics, backdrop-blur "glassmorphism", and fluid micro-animations.
- **Responsive Layout:** Engineered with CSS Grid and Flexbox for seamless use across different viewport sizes.

---

## 🛠️ Technology Stack

### Frontend
- **Framework:** React 18 (Bootstrapped with Vite for instant HMR)
- **Routing:** React Router DOM v6
- **Data Visualization:** Recharts
- **Icons:** React Icons (Lucide / Feather)
- **Styling:** Custom CSS with CSS Variables

### Backend
- **Framework:** Python 3.11 / Flask
- **Database:** SQLite3
- **ORM & Migrations:** SQLAlchemy + Alembic (Flask-Migrate)
- **Authentication:** Flask-JWT-Extended (Bearer Tokens)
- **Web Server:** Gunicorn

### Infrastructure / DevOps
- **Containerization:** Docker & Docker Compose
- **Reverse Proxy:** Nginx (Multi-stage build serving static assets)

---

## 🏗️ Architecture

DevFlow uses a decoupled client-server architecture:
1. **Frontend Container (`nginx:alpine`)**: Serves the compiled, optimized React SPA on port `80`.
2. **Backend Container (`python:3.11-slim`)**: Runs the Flask REST API via Gunicorn on port `5000`. Exposes endpoints like `/api/v1/clusters` and `/api/v1/deployments`.
3. **Database Volume**: A persistent Docker volume mapped to the `database/` folder ensures the SQLite data and Alembic migration history survive container restarts.

---

## ⚙️ Getting Started

### Option 1: Run with Docker (Recommended)

The easiest way to run the entire stack is using Docker Compose.

1. Clone the repository and navigate to the project root.
2. Run the build command:
   ```bash
   docker-compose up --build -d
   ```
3. Open your browser and navigate to: **`http://localhost`**

*(Note: The backend container will automatically run `flask db upgrade` on startup to prepare and seed the database).*

### Option 2: Run Locally (Development Mode)

If you wish to edit the code and utilize hot-reloading:

**1. Start the Backend:**
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .\.venv\Scripts\activate
pip install -r requirements.txt
flask db upgrade
python src/app.py
```
*The backend API will listen on `http://127.0.0.1:5000`.*

**2. Start the Frontend:**
```bash
cd frontend
npm install
npm run dev
```
*The React UI will listen on `http://localhost:5173`.*

---

## 🔑 Demo Credentials

Upon initialization, the database automatically seeds mock data. You can log in using:

- **Username:** `admin`
- **Password:** `admin123`

---

## 🔮 Future Roadmap (Stretch Goals)
- [ ] Connect the backend to a real Kubernetes cluster via the Python `kubernetes` client.
- [ ] Implement GitHub Webhooks to display real repository PRs and commits.
- [ ] Replace SQLite with PostgreSQL for higher concurrency.
- [ ] Implement WebSocket (Socket.io) connections to replace the current HTTP polling for log streams.
