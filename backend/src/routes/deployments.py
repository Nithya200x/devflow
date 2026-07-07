from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.deployment_service import DeploymentService, DeploymentServiceError
from models import ConnectedProject

deployments_bp = Blueprint('deployments', __name__)


@deployments_bp.route('', methods=['GET'])
@jwt_required()
def list_deployments():
    project_id = request.args.get('project_id', type=int)
    try:
        deployments = DeploymentService.get_all(project_id=project_id)
        return jsonify(deployments), 200
    except DeploymentServiceError as e:
        return jsonify({"msg": str(e)}), 400


@deployments_bp.route('', methods=['POST'])
@jwt_required()
def create_deployment():
    current_username = get_jwt_identity()
    data = request.get_json() or {}
    project_id = data.get('project_id')
    branch = data.get('branch', 'main')
    commit_sha = data.get('commit_sha', '')
    environment = data.get('environment', 'dev')

    if not project_id:
        return jsonify({"msg": "project_id is required"}), 400

    project = ConnectedProject.query.filter_by(id=project_id, connected_by=current_username).first()
    if not project:
        return jsonify({"msg": "Project not found"}), 404

    try:
        dep = DeploymentService.trigger_deployment(
            project_id=project.id,
            branch=branch,
            commit_sha=commit_sha,
            environment=environment,
            triggered_by=current_username,
        )
        return jsonify(dep), 201
    except DeploymentServiceError as e:
        return jsonify({"msg": str(e)}), 502


@deployments_bp.route('/<int:deployment_id>', methods=['GET'])
@jwt_required()
def get_deployment(deployment_id):
    current_username = get_jwt_identity()
    try:
        dep = DeploymentService.get_by_id(deployment_id)
        project = ConnectedProject.query.filter_by(id=dep["project_id"], connected_by=current_username).first()
        if not project:
            return jsonify({"msg": "Deployment not found for this user"}), 404
        return jsonify(dep), 200
    except DeploymentServiceError as e:
        return jsonify({"msg": str(e)}), 404


@deployments_bp.route('/<int:deployment_id>/rollback', methods=['POST'])
@jwt_required()
def rollback_deployment(deployment_id):
    current_username = get_jwt_identity()
    try:
        dep = DeploymentService.get_by_id(deployment_id)
        project = ConnectedProject.query.filter_by(id=dep["project_id"], connected_by=current_username).first()
        if not project:
            return jsonify({"msg": "Deployment not found for this user"}), 404

        result = DeploymentService.rollback_deployment(deployment_id, current_username)
        return jsonify(result), 201
    except DeploymentServiceError as e:
        return jsonify({"msg": str(e)}), 502


@deployments_bp.route('/<int:deployment_id>/rollout-status', methods=['GET'])
@jwt_required()
def deployment_rollout_status(deployment_id):
    current_username = get_jwt_identity()
    try:
        dep = DeploymentService.get_by_id(deployment_id)
        project = ConnectedProject.query.filter_by(id=dep["project_id"], connected_by=current_username).first()
        if not project:
            return jsonify({"msg": "Deployment not found for this user"}), 404

        status = DeploymentService.get_rollout_status(deployment_id)
        return jsonify(status), 200
    except DeploymentServiceError as e:
        return jsonify({"msg": str(e)}), 400
