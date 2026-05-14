# DevFlow

DevFlow is a cloud-native DevOps automation sample that shows a complete path from a Flask application to a Docker image, Jenkins pipeline, Docker Hub, and Kubernetes rollout.

## What It Does

- Runs a Flask web app with a polished dashboard at `/`.
- Exposes runtime pod/container metadata at `/details`.
- Exposes a health endpoint at `/health`.
- Builds a production Docker image with Gunicorn and a container health check.
- Deploys to Kubernetes with 2 replicas, rolling updates, probes, resource limits, a NodePort service, and an optional ingress.
- Includes a Jenkins pipeline for test, build, push, and Kubernetes deploy.
- Supports Kustomize overlays for dev, staging, and prod.
- Includes optional cert-manager TLS, Prometheus alerts, a Grafana dashboard, Trivy scanning, and Cosign signing hooks.

## Architecture

Developer -> GitHub -> Jenkins -> Docker -> Docker Hub -> Kubernetes -> DevFlow app

## Project Structure

```text
devflow/
|-- Jenkinsfile
|-- README.md
|-- devflowci/
|   |-- Dockerfile
|   |-- requirements.txt
|   |-- src/
|   |   |-- app.py
|   |   |-- static/styles.css
|   |   `-- templates/
|   `-- tests/
`-- devflowcd/
    |-- kustomization.yml
    |-- base/
    |   |-- namespace.yml
    |   |-- deployment.yml
    |   |-- service.yml
    |   `-- ingress.yml
    |-- monitoring/
    |-- overlays/
    `-- tls/
```

## Local Development

```bash
cd devflowci
pip install -r requirements.txt
python src/app.py
```

Open `http://localhost:5000`.

## Run Tests

```bash
cd devflowci
python -m pytest
```

## Build Docker Image

```bash
cd devflowci
docker build -t nithya200x/devflow-app:latest .
```

## Deploy to Kubernetes

```bash
kubectl apply -k devflowcd/overlays/dev
```

The NodePort service exposes the app on port `30007`.

For production, update `devflowcd/overlays/prod/kustomization.yml` and `devflowcd/tls/certificate.yml` with your real host name, then run:

```bash
kubectl apply -k devflowcd/overlays/prod
```

## Jenkins Requirements

Create these Jenkins credentials before running the pipeline:

- `dockerhub-credentials`: Docker Hub username/password credential.
- `kubeconfig`: file credential containing a kubeconfig with deploy access.
- `cosign-private-key`: optional Cosign private key file credential.
- `cosign-password`: optional Cosign password secret text credential.

The Jenkins agent must have `docker`, `kubectl`, `trivy`, and `cosign` installed. The pipeline builds and pushes both `latest` and the Jenkins build-number tag, scans the image for high/critical vulnerabilities, optionally signs the image, then updates the Kubernetes deployment to the build-number tag.

## Production Values To Replace

- Replace `devflow.example.com` with your real DNS name.
- Replace `devops@example.com` in `devflowcd/tls/cluster-issuer.example.yml`.
- Install cert-manager before applying the production certificate manifest.
- Install Prometheus Operator and Grafana sidecar dashboard loading before applying `devflowcd/monitoring`.
- Set Jenkins parameters for the target image repository, namespace, and Kustomize overlay.
- Enable image signing after Cosign credentials are created in Jenkins.
