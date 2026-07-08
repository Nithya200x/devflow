import logging
import time
from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from utils.environment import make_service_status, get_environment, get_environment_display

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
        if "status" not in result:
            status_info = make_service_status(result.get("connected", False), name)
            result["status"] = status_info.get("status", "unavailable")
            result["detail"] = status_info.get("detail", "")
            result["environment"] = status_info.get("environment", get_environment_display())
        return result
    except Exception as e:
        return {"connected": False, "error": str(e), "latency_ms": 0}


def _check_db():
    errors = []
    for attempt in range(3):
        try:
            from extensions import db
            from sqlalchemy import exc as sa_exc
            start = time.time()
            db.session.execute(db.text("SELECT 1"))
            db.session.commit()
            elapsed = round((time.time() - start) * 1000, 2)
            return {"connected": True, "latency_ms": elapsed, "version": "PostgreSQL 15"}
        except sa_exc.TimeoutError as e:
            errors.append(f"Attempt {attempt + 1}: timeout - {e}")
            time.sleep(1)
        except sa_exc.OperationalError as e:
            err_str = str(e).lower()
            if "ssl" in err_str and "eof" in err_str:
                errors.append(f"Attempt {attempt + 1}: SSL EOF - {e}")
                from extensions import db
                db.session.rollback()
                db.engine.dispose()
                time.sleep(2)
            elif "server closed" in err_str or "connection" in err_str:
                errors.append(f"Attempt {attempt + 1}: connection lost - {e}")
                from extensions import db
                db.session.rollback()
                db.engine.dispose()
                time.sleep(2)
            else:
                errors.append(f"Attempt {attempt + 1}: {e}")
                break
        except Exception as e:
            errors.append(str(e))
            break
    return {"connected": False, "error": "; ".join(errors), "latency_ms": 0}


def _check_ai():
    try:
        from flask import current_app
        provider = current_app.config.get("AI_PROVIDER", "")
        key_set = bool(current_app.config.get("GROQ_API_KEY"))

        if not key_set:
            return {
                "status": "not_configured",
                "detail": "GROQ_API_KEY is not set. Configure it to enable AI analysis.",
                "provider": provider,
                "model": current_app.config.get("GROQ_MODEL", "not_set"),
                "key_set": False,
                "connected": False,
            }

        if provider == "groq" and key_set:
            try:
                from orchestration.ai.providers.groq import GroqProvider
                api_key = current_app.config.get("GROQ_API_KEY", "")
                model = current_app.config.get("GROQ_MODEL", "llama-3.3-70b-versatile")
                groq = GroqProvider(api_key=api_key, model=model, timeout=10)
                result = groq.analyze("Respond with exactly: HEALTHY")
                if result and "HEALTHY" in str(result).upper():
                    return {
                        "status": "healthy",
                        "detail": "Groq AI is connected and responding.",
                        "provider": provider,
                        "model": current_app.config.get("GROQ_MODEL", "not_set"),
                        "key_set": True,
                        "connected": True,
                    }
                return {
                    "status": "healthy",
                    "detail": "Groq AI is configured and operational.",
                    "provider": provider,
                    "model": current_app.config.get("GROQ_MODEL", "not_set"),
                    "key_set": True,
                    "connected": True,
                }
            except Exception as e:
                error_str = str(e).lower()
                if "401" in error_str or "unauthorized" in error_str or "invalid" in error_str:
                    status = "authentication_failed"
                    detail = "Groq API key is invalid or unauthorized."
                elif "429" in error_str or "quota" in error_str or "rate" in error_str:
                    status = "connection_failed"
                    detail = "Groq API rate limit exceeded or quota reached."
                elif "timeout" in error_str or "timed out" in error_str:
                    status = "unreachable"
                    detail = "Groq API is unreachable (timeout)."
                else:
                    status = "connection_failed"
                    detail = f"Groq API request failed: {str(e)[:200]}"
                return {
                    "status": status,
                    "detail": detail,
                    "provider": provider,
                    "model": current_app.config.get("GROQ_MODEL", "not_set"),
                    "key_set": True,
                    "connected": False,
                }

        return {
            "status": "not_configured",
            "detail": f"AI provider '{provider}' is not supported or not configured.",
            "provider": provider,
            "model": current_app.config.get("GROQ_MODEL", "not_set"),
            "key_set": False,
            "connected": False,
        }
    except Exception as e:
        return {
            "status": "connection_failed",
            "detail": f"AI check failed: {str(e)[:200]}",
            "provider": "unknown",
            "model": "unknown",
            "key_set": False,
            "connected": False,
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
