from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.deployment_service import DeploymentService

deployments_bp = Blueprint('deployments', __name__)

@deployments_bp.route('', methods=['GET', 'POST'])
@jwt_required()
def handle_deployments():
    if request.method == 'GET':
        deployments = DeploymentService.get_all()
        return jsonify([{
            "id": d.id,
            "project_id": d.project_id,
            "environment": d.environment,
            "status": d.status,
            "deployed_by": d.deployed_by,
            "created_at": d.created_at.isoformat()
        } for d in deployments]), 200

    elif request.method == 'POST':
        data = request.get_json()
        if not data or not data.get('project_id'):
            return jsonify({"msg": "project_id is required"}), 400
        current_username = get_jwt_identity()
        d = DeploymentService.create(
            project_id=data.get('project_id'),
            environment=data.get('environment', 'dev'),
            deployed_by=current_username
        )
        return jsonify({
            "status": "success",
            "message": f"Deployment triggered for project {d.project_id} to {d.environment}",
            "deployment_id": d.id
        }), 201

@deployments_bp.route('/<int:deployment_id>/rollback', methods=['POST'])
@jwt_required()
def rollback_deployment(deployment_id):
    current_username = get_jwt_identity()
    rollback_dep = DeploymentService.rollback(deployment_id, current_username)
    return jsonify({
        "status": "success",
        "message": f"Rollback triggered for project {rollback_dep.project_id}",
        "deployment_id": rollback_dep.id
    }), 201
