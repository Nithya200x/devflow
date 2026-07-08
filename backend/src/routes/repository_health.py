import logging

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import ConnectedProject, User

logger = logging.getLogger(__name__)

repository_health_bp = Blueprint("repository_health", __name__)


@repository_health_bp.route("/health/score/<int:project_id>", methods=["GET"])
@jwt_required()
def get_health_score(project_id: int):
    username = get_jwt_identity()
    project = ConnectedProject.query.filter_by(id=project_id, connected_by=username).first()
    if not project:
        return jsonify({"msg": "Project not found"}), 404

    from services.repository_health_service import get_health_service
    hs = get_health_service()

    from routes.projects import _build_project_overview
    overview = _build_project_overview(project, username)
    result = hs.calculate_score(project_id, overview)

    return jsonify(result), 200


@repository_health_bp.route("/health/score", methods=["GET"])
@jwt_required()
def list_health_scores():
    username = get_jwt_identity()
    projects = ConnectedProject.query.filter_by(connected_by=username).all()
    if not projects:
        return jsonify({"scores": []}), 200

    from services.repository_health_service import get_health_service
    from routes.projects import _build_project_overview

    hs = get_health_service()
    scores = []
    for project in projects:
        try:
            overview = _build_project_overview(project, username)
            result = hs.calculate_score(project.id, overview)
            scores.append({
                "project_id": project.id,
                "project_name": project.name,
                "full_name": project.full_name,
                "score": result["score"],
                "trend": result["trend"],
                "color": result["color"],
                "label": result["label"],
                "breakdown": result["breakdown"],
                "calculated_at": result["calculated_at"],
            })
        except Exception as e:
            logger.warning("Failed to calculate score for project %s: %s", project.id, e)
            scores.append({
                "project_id": project.id,
                "project_name": project.name,
                "score": 0,
                "trend": "stable",
                "color": "#6b7280",
                "label": "Unknown",
                "breakdown": {},
                "calculated_at": None,
            })

    return jsonify({"scores": scores}), 200


@repository_health_bp.route("/health/score/invalidate", methods=["POST"])
@jwt_required()
def invalidate_cache():
    data = request.get_json() or {}
    project_id = data.get("project_id")
    from services.repository_health_service import get_health_service
    hs = get_health_service()
    hs.invalidate(project_id)
    return jsonify({"msg": "Cache invalidated"}), 200
