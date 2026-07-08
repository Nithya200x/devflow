import logging
import traceback
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from services.docker_service import DockerService, DockerServiceError
from utils.environment import make_service_status, get_environment_display

logger = logging.getLogger(__name__)

docker_bp = Blueprint("docker", __name__)

_docker = DockerService()


def _ensure_connected():
    if not _docker.connected:
        _docker.connect()
    return _docker.connected


def _not_configured(reason="Docker Engine not connected"):
    return jsonify({
        "configured": False,
        "reason": reason,
    }), 503


@docker_bp.route("/health", methods=["GET"])
@jwt_required()
def health():
    _ensure_connected()
    status = _docker.health_check()
    if "status" not in status:
        status_info = make_service_status(status.get("connected", False), "Docker")
        status["status"] = status_info.get("status", "unavailable")
        status["detail"] = status_info.get("detail", "")
        status["environment"] = status_info.get("environment", get_environment_display())
    return jsonify(status), 200 if status.get("connected") else 503


@docker_bp.route("/containers", methods=["GET"])
@jwt_required()
def list_containers():
    if not _ensure_connected():
        return _not_configured()
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
    try:
        containers = _docker.list_containers(show_all=show_all, filters=filters)
        return jsonify({"containers": containers, "count": len(containers)}), 200
    except DockerServiceError as e:
        return _not_configured(str(e))
    except Exception as e:
        logger.error("Docker containers error: %s\n%s", e, traceback.format_exc())
        return _not_configured(f"Failed to list containers: {e}")


@docker_bp.route("/containers/<container_id>", methods=["GET"])
@jwt_required()
def get_container(container_id):
    if not _ensure_connected():
        return _not_configured()
    try:
        container = _docker.get_container(container_id)
        if not container:
            return jsonify({"msg": "Container not found"}), 404
        return jsonify(container), 200
    except DockerServiceError as e:
        return _not_configured(str(e))
    except Exception as e:
        logger.error("Docker container error: %s\n%s", e, traceback.format_exc())
        return _not_configured(f"Failed to get container: {e}")


@docker_bp.route("/containers/<container_id>/logs", methods=["GET"])
@jwt_required()
def get_container_logs(container_id):
    if not _ensure_connected():
        return _not_configured()
    tail = request.args.get("tail", 100, type=int)
    try:
        logs = _docker.get_container_logs(container_id, tail=tail)
        return jsonify(logs), 200
    except DockerServiceError as e:
        return _not_configured(str(e))
    except Exception as e:
        logger.error("Docker container logs error: %s\n%s", e, traceback.format_exc())
        return _not_configured(f"Failed to get container logs: {e}")


@docker_bp.route("/containers/<container_id>/stats", methods=["GET"])
@jwt_required()
def get_container_stats(container_id):
    if not _ensure_connected():
        return _not_configured()
    try:
        stats = _docker.get_container_stats(container_id)
        return jsonify(stats), 200
    except DockerServiceError as e:
        return _not_configured(str(e))
    except Exception as e:
        logger.error("Docker container stats error: %s\n%s", e, traceback.format_exc())
        return _not_configured(f"Failed to get container stats: {e}")


@docker_bp.route("/stats", methods=["GET"])
@jwt_required()
def get_all_stats():
    if not _ensure_connected():
        return _not_configured()
    try:
        stats = _docker.get_all_stats()
        return jsonify(stats), 200
    except DockerServiceError as e:
        return _not_configured(str(e))
    except Exception as e:
        logger.error("Docker all stats error: %s\n%s", e, traceback.format_exc())
        return _not_configured(f"Failed to get Docker stats: {e}")
