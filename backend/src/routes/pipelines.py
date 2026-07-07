from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import User, ConnectedProject
from services.github_auth import PATGitHubAuth
from services.github_actions_service import GitHubActionsService
from utils.encryption import decrypt_token
import logging

logger = logging.getLogger(__name__)

pipelines_bp = Blueprint('pipelines', __name__)


def _get_service(project_id, username):
    project = ConnectedProject.query.filter_by(id=project_id, connected_by=username).first()
    if not project:
        return None, jsonify({"msg": "Project not found or access denied"}), 404
    user = User.query.filter_by(username=username).first()
    if not user or not user.github_token:
        return None, jsonify({"msg": "GitHub not connected"}), 400
    token = decrypt_token(user.github_token)
    auth = PATGitHubAuth(token)
    svc = GitHubActionsService(auth)
    return (svc, project), None, None


@pipelines_bp.route('/github/<int:project_id>/runs', methods=['GET'])
@jwt_required()
def get_workflow_runs(project_id):
    username = get_jwt_identity()
    result, err, status = _get_service(project_id, username)
    if err:
        return err, status
    svc, project = result
    try:
        runs = svc.get_workflow_runs(project.github_owner, project.github_repo)
        return jsonify(runs), 200
    except PermissionError as e:
        return jsonify({"msg": str(e)}), 401
    except FileNotFoundError:
        return jsonify({"msg": "Repository not found on GitHub", "runs": []}), 200
    except Exception as e:
        logger.error(f"Failed to fetch workflow runs: {e}")
        return jsonify({"msg": "Failed to fetch workflow runs", "runs": []}), 200


@pipelines_bp.route('/github/<int:project_id>/latest', methods=['GET'])
@jwt_required()
def get_latest_run(project_id):
    username = get_jwt_identity()
    result, err, status = _get_service(project_id, username)
    if err:
        return err, status
    svc, project = result
    try:
        run = svc.get_latest_run(project.github_owner, project.github_repo)
        return jsonify(run), 200
    except PermissionError as e:
        return jsonify({"msg": str(e)}), 401
    except Exception as e:
        logger.error(f"Failed to fetch latest run: {e}")
        return jsonify({}), 200


@pipelines_bp.route('/github/<int:project_id>/runs/<int:run_id>/jobs', methods=['GET'])
@jwt_required()
def get_workflow_jobs(project_id, run_id):
    username = get_jwt_identity()
    result, err, status = _get_service(project_id, username)
    if err:
        return err, status
    svc, project = result
    try:
        jobs = svc.get_workflow_jobs(project.github_owner, project.github_repo, run_id)
        return jsonify(jobs), 200
    except PermissionError as e:
        return jsonify({"msg": str(e)}), 401
    except Exception as e:
        logger.error(f"Failed to fetch workflow jobs: {e}")
        return jsonify([]), 200
