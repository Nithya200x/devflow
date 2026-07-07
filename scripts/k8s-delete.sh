#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "=== DevFlow Kubernetes Teardown ==="

kubectl delete -f "$PROJECT_ROOT/k8s/"

echo ""
echo "=== Teardown complete ==="
