import json
import logging
from datetime import datetime, timedelta, timezone

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from sqlalchemy import func, text

from extensions import db
from models import Deployment, Incident, ConnectedProject, User
from services.prometheus_service import prometheus_service

logger = logging.getLogger(__name__)

analytics_bp = Blueprint("analytics", __name__)

def _extract_value(result):
    try:
        v = float(result["data"]["result"][0]["value"][1])
        return v
    except (IndexError, ValueError, TypeError, KeyError):
        return 0.0


@analytics_bp.route("/dashboard", methods=["GET"])
@jwt_required()
def dashboard():
    days = request.args.get("days", 7, type=int)
    since = datetime.now(timezone.utc) - timedelta(days=days)

    total = Deployment.query.filter(Deployment.created_at >= since).count()
    succeeded = Deployment.query.filter(Deployment.created_at >= since, Deployment.status == "success").count()
    failed = Deployment.query.filter(Deployment.created_at >= since, Deployment.status == "failed").count()
    success_rate = round((succeeded / total * 100) if total > 0 else 0, 1)

    deployments_per_day = []
    for i in range(days):
        day = since + timedelta(days=i)
        next_day = day + timedelta(days=1)
        count = Deployment.query.filter(Deployment.created_at >= day, Deployment.created_at < next_day).count()
        deployments_per_day.append({"date": day.strftime("%Y-%m-%d"), "count": count})

    avg_duration = db.session.execute(
        text("""
            SELECT AVG(EXTRACT(EPOCH FROM (completed_at - started_at)))
            FROM deployment
            WHERE completed_at IS NOT NULL AND started_at IS NOT NULL
              AND created_at >= :since
        """),
        {"since": since}
    ).scalar() or 0

    incident_trends = []
    for i in range(days):
        day = since + timedelta(days=i)
        next_day = day + timedelta(days=1)
        count = Incident.query.filter(Incident.created_at >= day, Incident.created_at < next_day).count()
        incident_trends.append({"date": day.strftime("%Y-%m-%d"), "count": count})

    top_failed = db.session.execute(
        text("""
            SELECT repository, COUNT(*) as count
            FROM deployment
            WHERE status = 'failed' AND created_at >= :since
            GROUP BY repository
            ORDER BY count DESC
            LIMIT 5
        """),
        {"since": since}
    ).fetchall()

    top_repos = db.session.execute(
        text("""
            SELECT repository, COUNT(*) as count
            FROM deployment
            WHERE created_at >= :since
            GROUP BY repository
            ORDER BY count DESC
            LIMIT 5
        """),
        {"since": since}
    ).fetchall()

    health = {"github": False, "docker": False, "kubernetes": False, "prometheus": False, "grafana": False, "alertmanager": False}
    try:
        from services.alertmanager_service import AlertmanagerService
        am = AlertmanagerService()
        h = am.health_check()
        health["alertmanager"] = h.get("connected", False)
    except Exception:
        pass
    try:
        from services.grafana_service import GrafanaService
        gs = GrafanaService()
        h = gs.health_check()
        health["grafana"] = h.get("connected", False)
    except Exception:
        pass
    try:
        from services.docker_service import DockerService
        ds = DockerService()
        h = ds.health_check()
        health["docker"] = h.get("connected", False)
    except Exception:
        pass
    try:
        from services.kubernetes_service import KubernetesService
        ks = KubernetesService()
        h = ks.health_check()
        health["kubernetes"] = h.get("connected", False)
    except Exception:
        pass
    health_score = round(sum(1 for v in health.values() if v) / len(health) * 100, 0) if health else 0

    cpu_raw = prometheus_service.instant_query('rate(devflow_http_request_duration_seconds_sum[5m])')
    cpu_trend = round(_extract_value(cpu_raw) if cpu_raw.get("status") == "success" else 0, 4)

    mem_raw = prometheus_service.instant_query('process_resident_memory_bytes{job="devflow-backend"}')
    mem_trend = round(_extract_value(mem_raw) / (1024*1024) if mem_raw.get("status") == "success" else 0, 2)

    err_raw = prometheus_service.instant_query('rate(devflow_http_requests_total{status=~"5.."}[5m])')
    err_trend = round(_extract_value(err_raw) if err_raw.get("status") == "success" else 0, 4)

    return jsonify({
        "deploymentSuccessRate": success_rate,
        "totalDeployments": total,
        "succeededDeployments": succeeded,
        "failedDeployments": failed,
        "deploymentsPerDay": deployments_per_day,
        "avgDeploymentDuration": round(avg_duration, 1) if avg_duration else 0,
        "incidentTrends": incident_trends,
        "totalIncidents": Incident.query.filter(Incident.created_at >= since).count(),
        "cpuTrend": cpu_trend,
        "memTrend": mem_trend,
        "errorRateTrend": err_trend,
        "topFailedDeployments": [{"repository": r[0], "count": r[1]} for r in top_failed],
        "topActiveRepositories": [{"repository": r[0], "count": r[1]} for r in top_repos],
        "infrastructureHealthScore": health_score,
        "healthBreakdown": health,
    }), 200
