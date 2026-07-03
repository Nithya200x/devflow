import logging
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from services.docker_service import DockerService

logger = logging.getLogger(__name__)

docker_bp = Blueprint("docker", __name__)

_docker = DockerService()


@docker_bp.route("/health", methods=["GET"])
@jwt_required()
def health():
    if not _docker.connected:
        _docker.connect()
    status = _docker.health_check()
    return jsonify(status), 200 if status.get("connected") else 503


@docker_bp.route("/containers", methods=["GET"])
@jwt_required()
def list_containers():
    if not _docker.connected:
        _docker.connect()
    show_all = request.args.get("all", "true").lower() == "true"
    filters = {}
    status = request.args.get("status", "")
    if status:
        filters["status"] = status
    label = request.args.get("label", "")
    if label:
        filters["label"] = label
    ancestor = request.args.get("ancestor", "")
    if ancestor:
        filters["ancestor"] = ancestor
    containers = _docker.list_containers(show_all=show_all, filters=filters)
    return jsonify({"containers": containers, "count": len(containers)}), 200


@docker_bp.route("/containers/<container_id>", methods=["GET"])
@jwt_required()
def get_container(container_id):
    if not _docker.connected:
        _docker.connect()
    container = _docker.get_container(container_id)
    if not container:
        return jsonify({"msg": "Container not found"}), 404
    return jsonify(container), 200


@docker_bp.route("/containers/<container_id>/logs", methods=["GET"])
@jwt_required()
def get_container_logs(container_id):
    if not _docker.connected:
        _docker.connect()
    tail = request.args.get("tail", 100, type=int)
    logs = _docker.get_container_logs(container_id, tail=tail)
    return jsonify(logs), 200


@docker_bp.route("/containers/<container_id>/stats", methods=["GET"])
@jwt_required()
def get_container_stats(container_id):
    if not _docker.connected:
        _docker.connect()
    stats = _docker.get_container_stats(container_id)
    return jsonify(stats), 200


@docker_bp.route("/stats", methods=["GET"])
@jwt_required()
def get_all_stats():
    if not _docker.connected:
        _docker.connect()
    stats = _docker.get_all_stats()
    return jsonify(stats), 200
