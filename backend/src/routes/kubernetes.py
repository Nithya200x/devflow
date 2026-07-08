import logging
import traceback
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from services.kubernetes_service import KubernetesService, KubernetesServiceError
from utils.environment import make_service_status, get_environment_display

logger = logging.getLogger(__name__)

kubernetes_bp = Blueprint("kubernetes", __name__)

_k8s = KubernetesService()


def _ensure_connected():
    if not _k8s.connected:
        _k8s.connect()
    if not _k8s.connected:
        return False
    return True


def _not_configured(reason="Kubernetes not connected"):
    return jsonify({
        "configured": False,
        "reason": reason,
    }), 503


def _wrap(fn, *args, **kwargs):
    if not _ensure_connected():
        return _not_configured()
    try:
        result = fn(*args, **kwargs)
        return result
    except KubernetesServiceError as e:
        return _not_configured(str(e))
    except Exception as e:
        logger.error("Kubernetes API error: %s\n%s", e, traceback.format_exc())
        return jsonify({
            "configured": False,
            "reason": f"Kubernetes API error: {e}",
        }), 503


@kubernetes_bp.route("/health", methods=["GET"])
@jwt_required()
def health():
    _ensure_connected()
    status = _k8s.health_check()
    if "status" not in status:
        status_info = make_service_status(status.get("connected", False), "Kubernetes")
        status["status"] = status_info.get("status", "unavailable")
        status["detail"] = status_info.get("detail", "")
        status["environment"] = status_info.get("environment", get_environment_display())
    return jsonify(status), 200 if status.get("connected") else 503


@kubernetes_bp.route("/pods", methods=["GET"])
@jwt_required()
def list_pods():
    if not _ensure_connected():
        return _not_configured()
    namespace = request.args.get("namespace", "")
    label_selector = request.args.get("label_selector", "")
    field_selector = request.args.get("field_selector", "")
    try:
        pods = _k8s.list_pods(
            namespace=namespace,
            label_selector=label_selector,
            field_selector=field_selector,
        )
        return jsonify({"pods": pods, "count": len(pods)}), 200
    except KubernetesServiceError as e:
        return _not_configured(str(e))
    except Exception as e:
        logger.error("Kubernetes pods error: %s\n%s", e, traceback.format_exc())
        return _not_configured(f"Failed to list pods: {e}")


@kubernetes_bp.route("/pods/<namespace>/<name>", methods=["GET"])
@jwt_required()
def get_pod(namespace, name):
    if not _ensure_connected():
        return _not_configured()
    try:
        pod = _k8s.get_pod(name=name, namespace=namespace)
        if not pod:
            return jsonify({"msg": "Pod not found"}), 404
        return jsonify(pod), 200
    except KubernetesServiceError as e:
        return _not_configured(str(e))
    except Exception as e:
        logger.error("Kubernetes get pod error: %s\n%s", e, traceback.format_exc())
        return _not_configured(f"Failed to get pod: {e}")


@kubernetes_bp.route("/pods/<namespace>/<name>/logs", methods=["GET"])
@jwt_required()
def get_pod_logs(namespace, name):
    if not _ensure_connected():
        return _not_configured()
    container = request.args.get("container", "")
    tail = request.args.get("tail", 100, type=int)
    previous = request.args.get("previous", "false").lower() == "true"
    try:
        logs = _k8s.get_pod_logs(
            name=name,
            namespace=namespace,
            container=container,
            tail=tail,
            previous=previous,
        )
        return jsonify(logs), 200
    except KubernetesServiceError as e:
        return _not_configured(str(e))
    except Exception as e:
        logger.error("Kubernetes pod logs error: %s\n%s", e, traceback.format_exc())
        return _not_configured(f"Failed to get pod logs: {e}")


@kubernetes_bp.route("/deployments", methods=["GET"])
@jwt_required()
def list_deployments():
    if not _ensure_connected():
        return _not_configured()
    namespace = request.args.get("namespace", "")
    label_selector = request.args.get("label_selector", "")
    try:
        deployments = _k8s.list_deployments(
            namespace=namespace,
            label_selector=label_selector,
        )
        return jsonify({"deployments": deployments, "count": len(deployments)}), 200
    except KubernetesServiceError as e:
        return _not_configured(str(e))
    except Exception as e:
        logger.error("Kubernetes deployments error: %s\n%s", e, traceback.format_exc())
        return _not_configured(f"Failed to list deployments: {e}")


@kubernetes_bp.route("/deployments/<namespace>/<name>", methods=["GET"])
@jwt_required()
def get_deployment(namespace, name):
    if not _ensure_connected():
        return _not_configured()
    try:
        dep = _k8s.get_deployment(name=name, namespace=namespace)
        if not dep:
            return jsonify({"msg": "Deployment not found"}), 404
        return jsonify(dep), 200
    except KubernetesServiceError as e:
        return _not_configured(str(e))
    except Exception as e:
        logger.error("Kubernetes get deployment error: %s\n%s", e, traceback.format_exc())
        return _not_configured(f"Failed to get deployment: {e}")


@kubernetes_bp.route("/nodes", methods=["GET"])
@jwt_required()
def list_nodes():
    if not _ensure_connected():
        return _not_configured()
    try:
        nodes = _k8s.list_nodes()
        return jsonify({"nodes": nodes, "count": len(nodes)}), 200
    except KubernetesServiceError as e:
        return _not_configured(str(e))
    except Exception as e:
        logger.error("Kubernetes nodes error: %s\n%s", e, traceback.format_exc())
        return _not_configured(f"Failed to list nodes: {e}")


@kubernetes_bp.route("/namespaces", methods=["GET"])
@jwt_required()
def list_namespaces():
    if not _ensure_connected():
        return _not_configured()
    try:
        namespaces = _k8s.list_namespaces()
        return jsonify({"namespaces": namespaces, "count": len(namespaces)}), 200
    except KubernetesServiceError as e:
        return _not_configured(str(e))
    except Exception as e:
        logger.error("Kubernetes namespaces error: %s\n%s", e, traceback.format_exc())
        return _not_configured(f"Failed to list namespaces: {e}")


@kubernetes_bp.route("/events", methods=["GET"])
@jwt_required()
def list_events():
    if not _ensure_connected():
        return _not_configured()
    namespace = request.args.get("namespace", "")
    field_selector = request.args.get("field_selector", "")
    try:
        events = _k8s.list_events(
            namespace=namespace,
            field_selector=field_selector,
        )
        return jsonify({"events": events, "count": len(events)}), 200
    except KubernetesServiceError as e:
        return _not_configured(str(e))
    except Exception as e:
        logger.error("Kubernetes events error: %s\n%s", e, traceback.format_exc())
        return _not_configured(f"Failed to list events: {e}")


@kubernetes_bp.route("/services", methods=["GET"])
@jwt_required()
def list_services():
    if not _ensure_connected():
        return _not_configured()
    namespace = request.args.get("namespace", "")
    try:
        services = _k8s.list_services(namespace=namespace)
        return jsonify({"services": services, "count": len(services)}), 200
    except KubernetesServiceError as e:
        return _not_configured(str(e))
    except Exception as e:
        logger.error("Kubernetes services error: %s\n%s", e, traceback.format_exc())
        return _not_configured(f"Failed to list services: {e}")


@kubernetes_bp.route("/ingresses", methods=["GET"])
@jwt_required()
def list_ingresses():
    if not _ensure_connected():
        return _not_configured()
    namespace = request.args.get("namespace", "")
    try:
        ingresses = _k8s.list_ingresses(namespace=namespace)
        return jsonify({"ingresses": ingresses, "count": len(ingresses)}), 200
    except KubernetesServiceError as e:
        return _not_configured(str(e))
    except Exception as e:
        logger.error("Kubernetes ingresses error: %s\n%s", e, traceback.format_exc())
        return _not_configured(f"Failed to list ingresses: {e}")


@kubernetes_bp.route("/cluster-health", methods=["GET"])
@jwt_required()
def cluster_health():
    if not _ensure_connected():
        return _not_configured()
    try:
        health = _k8s.get_cluster_health()
        return jsonify(health), 200 if health.get("connected") else 503
    except KubernetesServiceError as e:
        return _not_configured(str(e))
    except Exception as e:
        logger.error("Kubernetes cluster health error: %s\n%s", e, traceback.format_exc())
        return _not_configured(f"Failed to get cluster health: {e}")


@kubernetes_bp.route("/metrics", methods=["GET"])
@jwt_required()
def get_metrics():
    if not _ensure_connected():
        return _not_configured()
    try:
        metrics = _k8s.get_cluster_metrics()
        return jsonify(metrics), 200
    except KubernetesServiceError as e:
        return _not_configured(str(e))
    except Exception as e:
        logger.error("Kubernetes metrics error: %s\n%s", e, traceback.format_exc())
        return _not_configured(f"Failed to get cluster metrics: {e}")
