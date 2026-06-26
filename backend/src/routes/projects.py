from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from services.project_service import ProjectService

projects_bp = Blueprint('projects', __name__)

@projects_bp.route('', methods=['GET'])
@jwt_required()
def get_projects():
    projects = ProjectService.get_all()
    return jsonify([{
        "id": p.id,
        "name": p.name,
        "repository_url": p.repository_url,
        "description": p.description,
        "created_at": p.created_at.isoformat()
    } for p in projects]), 200
