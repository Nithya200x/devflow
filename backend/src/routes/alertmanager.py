import logging
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from services.alertmanager_service import AlertmanagerService
from orchestration.events.event_types import (
    HighCPUDetected,
    HighMemoryDetected,
    HealthCheckFailed,
    OrchestrationEvent,
)

logger = logging.getLogger(__name__)

alertmanager_bp = Blueprint("alertmanager", __name__)

_am = AlertmanagerService()


@alertmanager_bp.route("/health", methods=["GET"])
@jwt_required()
def health():
    result = _am.health_check()
    status = result.get("status", "unknown")
    logger.info("Alertmanager health endpoint: status=%s, environment=%s", status, result.get("environment"))
    return jsonify(result), 200


@alertmanager_bp.route("/alerts", methods=["GET"])
@jwt_required()
def get_alerts():
    silenced = request.args.get("silenced", "false").lower() == "true"
    inhibited = request.args.get("inhibited", "false").lower() == "true"
    alerts = _am.get_alerts(silenced=silenced, inhibited=inhibited)
    return jsonify({"alerts": alerts, "count": len(alerts)}), 200


@alertmanager_bp.route("/silences", methods=["GET"])
@jwt_required()
def get_silences():
    silences = _am.get_silences()
    return jsonify({"silences": silences, "count": len(silences)}), 200


@alertmanager_bp.route("/webhook", methods=["POST"])
def webhook():
    payload = request.get_json()
    if not payload:
        return jsonify({"msg": "Invalid payload"}), 400

    processed = _am.process_webhook(payload)
    logger.info(f"Alertmanager webhook received: {len(processed)} alerts")

    for alert in processed:
        event = _map_alert_to_event(alert)
        if event:
            try:
                from routes.orchestration import _service
                _service.process_event(event)
            except Exception as e:
                logger.warning(f"Failed to process alert event: {e}")

    return jsonify({"received": len(processed), "status": "ok"}), 200


def _map_alert_to_event(alert: dict) -> OrchestrationEvent:
    alertname = alert.get("alertname", "")
    severity = alert.get("severity", "info")
    namespace = alert.get("namespace", "")
    pod = alert.get("pod", "")
    instance = alert.get("instance", "")
    summary = alert.get("summary", "")
    metadata = {
        "alertname": alertname,
        "severity": severity,
        "namespace": namespace,
        "pod": pod,
        "instance": instance,
        "summary": summary,
        "source": "alertmanager",
        "status": alert.get("status", "firing"),
        "fingerprint": alert.get("fingerprint", ""),
    }

    alert_lower = alertname.lower()
    if "cpu" in alert_lower and ("high" in alert_lower or "usage" in alert_lower):
        return HighCPUDetected(pod_name=pod, namespace=namespace, metadata=metadata)
    elif "memory" in alert_lower and ("high" in alert_lower or "usage" in alert_lower):
        return HighMemoryDetected(pod_name=pod, namespace=namespace, metadata=metadata)
    elif any(k in alert_lower for k in ("down", "unavailable", "unreachable")):
        return HealthCheckFailed(
            pod_name=pod or instance,
            namespace=namespace,
            check_type="service_health",
            reason=f"ApplicationDown: {alertname}",
            metadata=metadata,
        )
    elif "disk" in alert_lower and "pressure" in alert_lower:
        return HealthCheckFailed(
            pod_name=pod or instance,
            namespace=namespace,
            check_type="disk_pressure",
            reason=f"DiskPressure: {alertname}",
            metadata=metadata,
        )
    elif "latency" in alert_lower:
        return HealthCheckFailed(
            pod_name=pod or instance,
            namespace=namespace,
            check_type="network_latency",
            reason=f"NetworkLatency: {alertname}",
            metadata=metadata,
        )
    else:
        return HealthCheckFailed(
            pod_name=pod or instance,
            namespace=namespace,
            check_type="alertmanager",
            reason=f"Alert: {alertname}",
            metadata=metadata,
        )
