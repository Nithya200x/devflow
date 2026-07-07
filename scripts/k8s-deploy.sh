#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "=== DevFlow Kubernetes Deployment ==="

echo ""
echo "--- Step 1: Creating namespace and resources ---"
kubectl apply -f "$PROJECT_ROOT/k8s/"

echo ""
echo "--- Step 2: Checking pods ---"
kubectl get pods -n devflow

echo ""
echo "--- Step 3: Checking services ---"
kubectl get services -n devflow

echo ""
echo "=== Deployment complete ==="
echo ""
echo "To check status:"
echo "  kubectl get pods -n devflow -w"
echo ""
echo "To view logs:"
echo "  kubectl logs -n devflow deployment/backend"
echo "  kubectl logs -n devflow deployment/frontend"
echo "  kubectl logs -n devflow deployment/postgres"
echo "  kubectl logs -n devflow deployment/prometheus"
