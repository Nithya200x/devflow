import logging
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from services.kubernetes_service import KubernetesService

logger = logging.getLogger(__name__)

kubernetes_bp = Blueprint("kubernetes", __name__)

_k8s = KubernetesService()


@kubernetes_bp.route("/health", methods=["GET"])
@jwt_required()
def health():
    if not _k8s.connected:
        _k8s.connect()
    status = _k8s.health_check()
    return jsonify(status), 200 if status.get("connected") else 503


@kubernetes_bp.route("/pods", methods=["GET"])
@jwt_required()
def list_pods():
    if not _k8s.connected:
        _k8s.connect()
    namespace = request.args.get("namespace", "")
    label_selector = request.args.get("label_selector", "")
    field_selector = request.args.get("field_selector", "")
    pods = _k8s.list_pods(
        namespace=namespace,
        label_selector=label_selector,
        field_selector=field_selector,
    )
    return jsonify({"pods": pods, "count": len(pods)}), 200


@kubernetes_bp.route("/pods/<namespace>/<name>", methods=["GET"])
@jwt_required()
def get_pod(namespace, name):
    if not _k8s.connected:
        _k8s.connect()
    pod = _k8s.get_pod(name=name, namespace=namespace)
    if not pod:
        return jsonify({"msg": "Pod not found"}), 404
    return jsonify(pod), 200


@kubernetes_bp.route("/pods/<namespace>/<name>/logs", methods=["GET"])
@jwt_required()
def get_pod_logs(namespace, name):
    if not _k8s.connected:
        _k8s.connect()
    container = request.args.get("container", "")
    tail = request.args.get("tail", 100, type=int)
    previous = request.args.get("previous", "false").lower() == "true"
    logs = _k8s.get_pod_logs(
        name=name,
        namespace=namespace,
        container=container,
        tail=tail,
        previous=previous,
    )
    return jsonify(logs), 200


@kubernetes_bp.route("/deployments", methods=["GET"])
@jwt_required()
def list_deployments():
    if not _k8s.connected:
        _k8s.connect()
    namespace = request.args.get("namespace", "")
    label_selector = request.args.get("label_selector", "")
    deployments = _k8s.list_deployments(
        namespace=namespace,
        label_selector=label_selector,
    )
    return jsonify({"deployments": deployments, "count": len(deployments)}), 200


@kubernetes_bp.route("/deployments/<namespace>/<name>", methods=["GET"])
@jwt_required()
def get_deployment(namespace, name):
    if not _k8s.connected:
        _k8s.connect()
    dep = _k8s.get_deployment(name=name, namespace=namespace)
    if not dep:
        return jsonify({"msg": "Deployment not found"}), 404
    return jsonify(dep), 200


@kubernetes_bp.route("/nodes", methods=["GET"])
@jwt_required()
def list_nodes():
    if not _k8s.connected:
        _k8s.connect()
    nodes = _k8s.list_nodes()
    return jsonify({"nodes": nodes, "count": len(nodes)}), 200


@kubernetes_bp.route("/namespaces", methods=["GET"])
@jwt_required()
def list_namespaces():
    if not _k8s.connected:
        _k8s.connect()
    namespaces = _k8s.list_namespaces()
    return jsonify({"namespaces": namespaces, "count": len(namespaces)}), 200


@kubernetes_bp.route("/events", methods=["GET"])
@jwt_required()
def list_events():
    if not _k8s.connected:
        _k8s.connect()
    namespace = request.args.get("namespace", "")
    field_selector = request.args.get("field_selector", "")
    events = _k8s.list_events(
        namespace=namespace,
        field_selector=field_selector,
    )
    return jsonify({"events": events, "count": len(events)}), 200


@kubernetes_bp.route("/services", methods=["GET"])
@jwt_required()
def list_services():
    if not _k8s.connected:
        _k8s.connect()
    namespace = request.args.get("namespace", "")
    services = _k8s.list_services(namespace=namespace)
    return jsonify({"services": services, "count": len(services)}), 200


@kubernetes_bp.route("/ingresses", methods=["GET"])
@jwt_required()
def list_ingresses():
    if not _k8s.connected:
        _k8s.connect()
    namespace = request.args.get("namespace", "")
    ingresses = _k8s.list_ingresses(namespace=namespace)
    return jsonify({"ingresses": ingresses, "count": len(ingresses)}), 200


@kubernetes_bp.route("/metrics", methods=["GET"])
@jwt_required()
def get_metrics():
    if not _k8s.connected:
        _k8s.connect()
    metrics = _k8s.get_cluster_metrics()
    return jsonify(metrics), 200
