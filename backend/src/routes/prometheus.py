import logging
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from services.prometheus_service import PrometheusService

logger = logging.getLogger(__name__)

prometheus_bp = Blueprint("prometheus", __name__)

_prom = PrometheusService()


@prometheus_bp.route("/health", methods=["GET"])
@jwt_required()
def health():
    status = _prom.health_check()
    return jsonify(status), 200 if status.get("connected") else 503


@prometheus_bp.route("/query", methods=["POST"])
@jwt_required()
def query():
    data = request.get_json()
    if not data or "query" not in data:
        return jsonify({"msg": "query is required"}), 400
    result = _prom.query(data["query"])
    return jsonify(result), 200


@prometheus_bp.route("/query_range", methods=["POST"])
@jwt_required()
def query_range():
    data = request.get_json()
    if not data or "query" not in data:
        return jsonify({"msg": "query is required"}), 400
    result = _prom.range_query(
        query=data["query"],
        start=data.get("start", ""),
        end=data.get("end", ""),
        step=data.get("step", "15s"),
    )
    return jsonify(result), 200


@prometheus_bp.route("/metrics/cpu", methods=["GET"])
@jwt_required()
def cpu_metrics():
    namespace = request.args.get("namespace", "")
    pod = request.args.get("pod", "")
    return jsonify(_prom.get_cpu_metrics(namespace, pod)), 200


@prometheus_bp.route("/metrics/memory", methods=["GET"])
@jwt_required()
def memory_metrics():
    namespace = request.args.get("namespace", "")
    pod = request.args.get("pod", "")
    return jsonify(_prom.get_memory_metrics(namespace, pod)), 200


@prometheus_bp.route("/metrics/disk", methods=["GET"])
@jwt_required()
def disk_metrics():
    namespace = request.args.get("namespace", "")
    pod = request.args.get("pod", "")
    return jsonify(_prom.get_disk_metrics(namespace, pod)), 200


@prometheus_bp.route("/metrics/network", methods=["GET"])
@jwt_required()
def network_metrics():
    namespace = request.args.get("namespace", "")
    pod = request.args.get("pod", "")
    return jsonify(_prom.get_network_metrics(namespace, pod)), 200


@prometheus_bp.route("/metrics/pod", methods=["GET"])
@jwt_required()
def pod_metrics():
    namespace = request.args.get("namespace", "")
    pod = request.args.get("pod", "")
    return jsonify(_prom.get_pod_metrics(namespace, pod)), 200


@prometheus_bp.route("/metrics/node", methods=["GET"])
@jwt_required()
def node_metrics():
    node = request.args.get("node", "")
    return jsonify(_prom.get_node_metrics(node)), 200


@prometheus_bp.route("/metrics/deployment", methods=["GET"])
@jwt_required()
def deployment_metrics():
    namespace = request.args.get("namespace", "")
    deployment = request.args.get("deployment", "")
    return jsonify(_prom.get_deployment_metrics(namespace, deployment)), 200


@prometheus_bp.route("/metrics/service", methods=["GET"])
@jwt_required()
def service_metrics():
    namespace = request.args.get("namespace", "")
    service = request.args.get("service", "")
    return jsonify(_prom.get_service_metrics(namespace, service)), 200


@prometheus_bp.route("/metrics/error-rate", methods=["GET"])
@jwt_required()
def error_rate():
    namespace = request.args.get("namespace", "")
    pod = request.args.get("pod", "")
    return jsonify(_prom.get_error_rate(namespace, pod)), 200


@prometheus_bp.route("/metrics/request-rate", methods=["GET"])
@jwt_required()
def request_rate():
    namespace = request.args.get("namespace", "")
    pod = request.args.get("pod", "")
    return jsonify(_prom.get_request_rate(namespace, pod)), 200


@prometheus_bp.route("/metrics/latency", methods=["GET"])
@jwt_required()
def latency():
    namespace = request.args.get("namespace", "")
    pod = request.args.get("pod", "")
    return jsonify(_prom.get_latency(namespace, pod)), 200


@prometheus_bp.route("/alerts", methods=["GET"])
@jwt_required()
def list_alerts():
    alerts = _prom.list_active_alerts()
    return jsonify({"alerts": alerts, "count": len(alerts)}), 200
