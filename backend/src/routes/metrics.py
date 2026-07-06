import logging
import math

from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from services.prometheus_service import prometheus_service

logger = logging.getLogger(__name__)

metrics_bp = Blueprint("metrics", __name__)


def _extract_value(result):
    try:
        v = float(result["data"]["result"][0]["value"][1])
        return v if math.isfinite(v) else 0.0
    except (IndexError, ValueError, TypeError, KeyError):
        return 0.0


@metrics_bp.route("/summary", methods=["GET"])
@jwt_required()
def metrics_summary():
    ps = prometheus_service

    if not ps._base_url:
        return jsonify({
            "status": "not_configured",
            "requests": 0, "errors": 0,
            "errorRate": 0.0, "avgLatency": 0.0, "activeRequests": 0,
        }), 200

    ps._ensure_connected()
    if not ps.connected:
        return jsonify({
            "status": "disconnected",
            "requests": 0, "errors": 0,
            "errorRate": 0.0, "avgLatency": 0.0, "activeRequests": 0,
        }), 200

    up_raw = ps.instant_query("up")
    has_targets = bool(up_raw.get("data", {}).get("result"))

    total_requests = int(_extract_value(
        ps.instant_query("sum(devflow_http_requests_total)")
    ))
    total_errors = int(_extract_value(
        ps.instant_query("sum(devflow_http_errors_total)")
    ))

    error_rate = _extract_value(
        ps.instant_query(
            "sum(rate(devflow_http_errors_total[5m])) / "
            "sum(rate(devflow_http_requests_total[5m])) * 100"
        )
    )
    avg_latency = _extract_value(
        ps.instant_query(
            'histogram_quantile(0.95, '
            'sum(rate(devflow_http_request_duration_seconds_bucket[5m])) by (le))'
        )
    )
    active = int(_extract_value(
        ps.instant_query("devflow_active_requests")
    ))

    has_devflow = total_requests > 0
    status = "healthy" if has_devflow else ("connected" if has_targets else "no_data")

    return jsonify({
        "status": status,
        "requests": total_requests,
        "errors": total_errors,
        "errorRate": round(error_rate, 2),
        "avgLatency": round(avg_latency, 4),
        "activeRequests": active,
    }), 200
