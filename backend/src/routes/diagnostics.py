import logging
import time
from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required

logger = logging.getLogger(__name__)

diagnostics_bp = Blueprint("diagnostics", __name__)

CHECKS = [
    {
        "name": "Backend API",
        "key": "backend",
        "check": lambda: {"connected": True, "version": "2.0.0", "latency_ms": 0},
    },
    {
        "name": "Database",
        "key": "database",
        "check": lambda: _check_db(),
    },
    {
        "name": "GitHub",
        "key": "github",
        "check": lambda: _check_service("github"),
    },
    {
        "name": "Docker",
        "key": "docker",
        "check": lambda: _check_service("docker"),
    },
    {
        "name": "Kubernetes",
        "key": "kubernetes",
        "check": lambda: _check_service("kubernetes"),
    },
    {
        "name": "Prometheus",
        "key": "prometheus",
        "check": lambda: _check_service("prometheus"),
    },
    {
        "name": "Grafana",
        "key": "grafana",
        "check": lambda: _check_service("grafana"),
    },
    {
        "name": "Alertmanager",
        "key": "alertmanager",
        "check": lambda: _check_service("alertmanager"),
    },
    {
        "name": "Groq AI",
        "key": "ai",
        "check": lambda: _check_ai(),
    },
]


def _check_service(name):
    svc_map = {
        "github": ("services.github_service", "GitHubService"),
        "docker": ("services.docker_service", "DockerService"),
        "kubernetes": ("services.kubernetes_service", "KubernetesService"),
        "prometheus": ("services.prometheus_service", "PrometheusService"),
        "grafana": ("services.grafana_service", "GrafanaService"),
        "alertmanager": ("services.alertmanager_service", "AlertmanagerService"),
    }
    try:
        mod_path, cls_name = svc_map[name]
        import importlib
        mod = importlib.import_module(mod_path)
        svc_cls = getattr(mod, cls_name)
        svc = svc_cls()
        start = time.time()
        result = svc.health_check()
        elapsed = round((time.time() - start) * 1000, 2)
        result["latency_ms"] = elapsed
        return result
    except Exception as e:
        return {"connected": False, "error": str(e), "latency_ms": 0}


def _check_db():
    try:
        from extensions import db
        start = time.time()
        db.session.execute(db.text("SELECT 1"))
        elapsed = round((time.time() - start) * 1000, 2)
        return {"connected": True, "latency_ms": elapsed, "version": "PostgreSQL 15"}
    except Exception as e:
        return {"connected": False, "error": str(e), "latency_ms": 0}


def _check_ai():
    config = {}
    try:
        from flask import current_app
        config = {
            "provider": current_app.config.get("AI_PROVIDER", "not_set"),
            "model": current_app.config.get("GROQ_MODEL", "not_set"),
            "key_set": bool(current_app.config.get("GROQ_API_KEY")),
        }
    except Exception:
        config = {"provider": "unknown", "key_set": False}
    return {
        "connected": config.get("key_set", False),
        "provider": config.get("provider", "unknown"),
        "model": config.get("model", "unknown"),
        "key_set": config.get("key_set", False),
        "latency_ms": 0,
    }


@diagnostics_bp.route("", methods=["GET"])
@jwt_required()
def run_diagnostics():
    import datetime
    results = []
    all_ok = True
    for check in CHECKS:
        try:
            start = time.time()
            result = check["check"]()
            elapsed = round((time.time() - start) * 1000, 2)
            ok = result.get("connected", False)
            if not ok:
                all_ok = False
            results.append({
                "name": check["name"],
                "key": check["key"],
                "status": "healthy" if ok else "unhealthy",
                "connected": ok,
                "latency_ms": result.get("latency_ms", elapsed),
                "version": result.get("version", result.get("provider", "N/A")),
                "error": result.get("error"),
                "last_checked": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "recommended_fix": _get_fix(check["key"], result),
            })
        except Exception as e:
            all_ok = False
            results.append({
                "name": check["name"],
                "key": check["key"],
                "status": "error",
                "connected": False,
                "latency_ms": 0,
                "version": "N/A",
                "error": str(e),
                "last_checked": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "recommended_fix": _get_fix(check["key"], {"connected": False}),
            })
    return jsonify({
        "results": results,
        "summary": {
            "total": len(results),
            "healthy": sum(1 for r in results if r["status"] == "healthy"),
            "unhealthy": sum(1 for r in results if r["status"] != "healthy"),
            "all_healthy": all_ok,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        },
    }), 200


def _get_fix(key, result):
    fixes = {
        "backend": "Ensure the backend process is running and port 5000 is accessible",
        "database": "Check if PostgreSQL is running and DATABASE_URL is correct",
        "github": "Connect a GitHub account via Settings or set GITHUB_TOKEN env var",
        "docker": "Ensure Docker is running and /var/run/docker.sock is accessible" + (
            "" if result.get("connected") else " (add group_add: ['0'] to docker-compose.yml)"
        ),
        "kubernetes": "Ensure minikube or kubeconfig is configured correctly" + (
            "" if result.get("connected") else " (check KUBECONFIG path and cluster status)"
        ),
        "prometheus": "Ensure Prometheus is running and PROMETHEUS_URL is correct",
        "grafana": "Ensure Grafana is running and GRAFANA_URL + credentials are correct",
        "alertmanager": "Ensure Alertmanager container is running and configured in Prometheus",
        "ai": "Set AI_PROVIDER and GROQ_API_KEY (or OPENAI_API_KEY) environment variables",
    }
    return fixes.get(key, "Check service configuration and logs")
