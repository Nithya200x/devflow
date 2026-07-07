# DevFlow Kubernetes Deployment

Deploy DevFlow on a local Kubernetes cluster (e.g., Minikube, kind, Docker Desktop, or k3s).

## Prerequisites

- Docker
- kubectl
- A local Kubernetes cluster (Minikube / kind / Docker Desktop)
- Node.js 20+ (for building frontend)

## 1. Enable Local Cluster

### Docker Desktop
Enable Kubernetes in Settings > Kubernetes > Enable Kubernetes.

### Minikube
```bash
minikube start --cpus 4 --memory 8192
```

### kind
```bash
kind create cluster --name devflow
```

Verify the cluster is running:
```bash
kubectl cluster-info
kubectl get nodes
```

## 2. Build Images

Build images so they are available to the local cluster:

### Backend
```bash
docker build -t devflow-backend:latest ./backend
```

### Frontend
```bash
docker build -t devflow-frontend:latest ./frontend
```

For `kind`, load images into the cluster:
```bash
kind load docker-image devflow-backend:latest
kind load docker-image devflow-frontend:latest
```

For `Minikube`, use the Docker daemon inside the cluster:
```bash
eval $(minikube docker-env)
docker build -t devflow-backend:latest ./backend
docker build -t devflow-frontend:latest ./frontend
```

## 3. Deploy

```bash
# From the repository root
kubectl apply -f k8s/
```

Or use the deploy script:
```bash
chmod +x scripts/k8s-deploy.sh
./scripts/k8s-deploy.sh
```

This creates:
- `devflow` namespace
- Backend deployment + service on port 5000
- Frontend deployment + service on port 80
- PostgreSQL deployment + service on port 5432 with persistent storage
- Prometheus deployment + service on NodePort 30090

## 4. Check Pods

```bash
kubectl get pods -n devflow
```

Expected output:
```
NAME                        READY   STATUS    RESTARTS   AGE
backend-xxxxxxxxxx-xxxxx    1/1     Running   0          XXs
frontend-xxxxxxxxxx-xxxxx   1/1     Running   0          XXs
postgres-xxxxxxxxxx-xxxxx   1/1     Running   0          XXs
prometheus-xxxxxxxxxx-xxxx  1/1     Running   0          XXs
```

## 5. View Logs

```bash
# Backend
kubectl logs -n devflow -l app=backend --tail=100

# Frontend
kubectl logs -n devflow -l app=frontend --tail=100

# PostgreSQL
kubectl logs -n devflow -l app=postgres --tail=100

# Prometheus
kubectl logs -n devflow -l app=prometheus --tail=100

# Follow a specific pod
kubectl logs -n devflow deployment/backend -f
```

## Verification

### Health endpoint
```bash
# Port-forward backend
kubectl port-forward -n devflow svc/backend 5000:5000

# In another terminal
curl http://localhost:5000/health
```
Expected: `{"status":"up"}`

### Metrics endpoint
```bash
curl http://localhost:5000/metrics
```
Expected: Prometheus metrics output.

### Frontend
```bash
kubectl port-forward -n devflow svc/frontend 8080:80
```
Visit http://localhost:8080 in a browser.

### Prometheus
```bash
kubectl port-forward -n devflow svc/prometheus 9090:9090
```
Visit http://localhost:9090 in a browser.

## Cleanup

```bash
kubectl delete -f k8s/
```

Or use the delete script:
```bash
chmod +x scripts/k8s-delete.sh
./scripts/k8s-delete.sh
```

This deletes all DevFlow resources but preserves the cluster itself.

## Troubleshooting

### Pod stuck in Pending
```bash
kubectl describe pod -n devflow <pod-name>
```
Common causes: insufficient resources, missing storage class for PVC.

### Pod stuck in CrashLoopBackOff
```bash
kubectl logs -n devflow <pod-name>
```

### Backend cannot connect to PostgreSQL
Ensure the `postgres` pod is healthy and the `DATABASE_URL` in the backend deployment matches the Postgres service name and credentials.

### Images not found
If using `kind` or a remote cluster, ensure images are available:
- `kind`: run `kind load docker-image devflow-backend:latest`
- Remote: push images to a registry and update `image:` in the deployment manifests
