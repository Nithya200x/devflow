import logging

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from orchestration.events.event_types import (
    BuildStarted,
    BuildSucceeded,
    BuildFailed,
)
from services.jenkins_service import JenkinsService, JenkinsError

logger = logging.getLogger(__name__)

jenkins_bp = Blueprint("jenkins", __name__)

_jenkins = JenkinsService()


def _get_orchestration():
    from routes.orchestration import _service
    return _service


@jenkins_bp.route("/build", methods=["POST"])
@jwt_required()
def trigger_build():
    user = get_jwt_identity()
    data = request.get_json() or {}
    repository_name = data.get("repository", "")
    branch = data.get("branch", "main")
    commit_sha = data.get("commit_sha", "")
    triggered_by = data.get("triggered_by", user)

    try:
        result = _jenkins.trigger_build(
            repository_name=repository_name,
            branch=branch,
            commit_sha=commit_sha,
            triggered_by=triggered_by,
        )
    except JenkinsError as e:
        return jsonify({
            "success": False,
            "error": {
                "type": "JENKINS_ERROR",
                "message": e.message,
                "details": getattr(e, "details", None),
                "retryable": e.status_code in (502, 503, 504),
            }
        }), e.status_code

    try:
        event = BuildStarted(
            repository=repository_name,
            branch=branch,
            commit_sha=commit_sha,
            triggered_by=triggered_by,
            metadata={"queue_id": result.get("queue_id", "")},
        )
        _get_orchestration().process_event(event)
    except Exception as e:
        logger.warning(f"Failed to emit BuildStarted event: {e}")

    return jsonify({
        "success": True,
        "message": "Build triggered",
        "data": result,
    }), 202


@jenkins_bp.route("/queue/<queue_id>", methods=["GET"])
@jwt_required()
def get_queue_status(queue_id):
    try:
        status = _jenkins.get_queue_status(queue_id)
        return jsonify({"success": True, "data": status}), 200
    except JenkinsError as e:
        return jsonify({
            "success": False,
            "error": {
                "type": "JENKINS_ERROR",
                "message": e.message,
                "retryable": e.status_code in (502, 503, 504),
            }
        }), e.status_code


@jenkins_bp.route("/build/<int:build_number>", methods=["GET"])
@jwt_required()
def get_build_status(build_number):
    try:
        info = _jenkins.get_build_status(build_number)
        return jsonify({"success": True, "data": info}), 200
    except JenkinsError as e:
        return jsonify({
            "success": False,
            "error": {
                "type": "JENKINS_ERROR",
                "message": e.message,
                "retryable": e.status_code in (502, 503, 504),
            }
        }), e.status_code


@jenkins_bp.route("/build/<int:build_number>/console", methods=["GET"])
@jwt_required()
def get_console_output(build_number):
    try:
        output = _jenkins.get_console_output(build_number)
        return jsonify({"success": True, "data": output}), 200
    except JenkinsError as e:
        return jsonify({
            "success": False,
            "error": {
                "type": "JENKINS_ERROR",
                "message": e.message,
                "retryable": e.status_code in (502, 503, 504),
            }
        }), e.status_code


@jenkins_bp.route("/build/<int:build_number>/check", methods=["POST"])
@jwt_required()
def check_build(build_number):
    try:
        info = _jenkins.get_build_info(build_number)
    except JenkinsError as e:
        return jsonify({
            "success": False,
            "error": {
                "type": "JENKINS_ERROR",
                "message": e.message,
                "retryable": e.status_code in (502, 503, 504),
            }
        }), e.status_code

    status = info.get("status", "unknown")
    result = info.get("result")
    params = info.get("parameters", {})

    if status in ("running", "queued", "unknown"):
        return jsonify({
            "success": True,
            "data": {"build_number": build_number, "status": status, "complete": False},
        }), 200

    event_type = None
    if status == "success":
        event_type = "BUILD_SUCCEEDED"
    elif status in ("failed", "aborted") or (result and result in ("FAILURE", "ABORTED", "UNSTABLE")):
        event_type = "BUILD_FAILED"

    if not event_type:
        return jsonify({
            "success": True,
            "data": {"build_number": build_number, "status": status, "complete": True, "event_emitted": False},
        }), 200

    if event_type == "BUILD_SUCCEEDED":
        event = BuildSucceeded(
            build_number=str(build_number),
            repository=params.get("REPOSITORY_NAME", ""),
            branch=params.get("BRANCH", ""),
            commit_sha=params.get("COMMIT_SHA", ""),
            triggered_by=params.get("TRIGGERED_BY", ""),
            metadata={"build_info": info},
        )
    else:
        event = BuildFailed(
            build_number=str(build_number),
            repository=params.get("REPOSITORY_NAME", ""),
            branch=params.get("BRANCH", ""),
            commit_sha=params.get("COMMIT_SHA", ""),
            triggered_by=params.get("TRIGGERED_BY", ""),
            reason=result or status,
            metadata={"build_info": info},
        )

    try:
        incident = _get_orchestration().process_event(event)
        return jsonify({
            "success": True,
            "data": {
                "build_number": build_number,
                "status": status,
                "complete": True,
                "event_type": event_type,
                "event_emitted": True,
                "incident_created": incident is not None,
                "incident_id": incident.incident_id if incident else None,
            },
        }), 202
    except Exception as e:
        logger.exception("Failed to process auto-check event")
        return jsonify({
            "success": False,
            "error": {
                "type": "EVENT_PROCESSING_ERROR",
                "message": f"Failed to process event: {str(e)}",
                "retryable": False,
            }
        }), 500


@jenkins_bp.route("/build/<int:build_number>/event", methods=["POST"])
@jwt_required()
def emit_build_event(build_number):
    data = request.get_json() or {}
    event_type = data.get("event_type", "")
    repository_name = data.get("repository", "")
    branch = data.get("branch", "")
    commit_sha = data.get("commit_sha", "")
    triggered_by = data.get("triggered_by", "")

    try:
        info = _jenkins.get_build_info(build_number)
    except JenkinsError as e:
        return jsonify({
            "success": False,
            "error": {
                "type": "JENKINS_ERROR",
                "message": e.message,
                "retryable": e.status_code in (502, 503, 504),
            }
        }), e.status_code

    params = info.get("parameters", {})
    effective_branch = branch or params.get("BRANCH", "")
    effective_commit = commit_sha or params.get("COMMIT_SHA", "")
    effective_repo = repository_name or params.get("REPOSITORY_NAME", "")
    effective_triggered = triggered_by or params.get("TRIGGERED_BY", "")

    if event_type == "BUILD_SUCCEEDED":
        event = BuildSucceeded(
            build_number=str(build_number),
            repository=effective_repo,
            branch=effective_branch,
            commit_sha=effective_commit,
            triggered_by=effective_triggered,
            metadata={"build_info": info},
        )
    elif event_type == "BUILD_FAILED":
        event = BuildFailed(
            build_number=str(build_number),
            repository=effective_repo,
            branch=effective_branch,
            commit_sha=effective_commit,
            triggered_by=effective_triggered,
            reason=info.get("result", "FAILURE"),
            metadata={"build_info": info},
        )
    else:
        return jsonify({
            "success": False,
            "error": {
                "type": "INVALID_EVENT_TYPE",
                "message": "event_type must be BUILD_SUCCEEDED or BUILD_FAILED",
                "retryable": False,
            }
        }), 400

    try:
        incident = _get_orchestration().process_event(event)
        return jsonify({
            "success": True,
            "message": "Event processed",
            "event_type": event_type,
            "build_number": build_number,
            "incident_created": incident is not None,
            "incident_id": incident.incident_id if incident else None,
        }), 202
    except Exception as e:
        logger.exception("Failed to process build event")
        return jsonify({
            "success": False,
            "error": {
                "type": "EVENT_PROCESSING_ERROR",
                "message": f"Failed to process event: {str(e)}",
                "retryable": False,
            }
        }), 500


@jenkins_bp.route("/builds", methods=["GET"])
@jwt_required()
def get_builds_history():
    limit = request.args.get("limit", 50, type=int)
    try:
        builds = _jenkins.get_build_history(limit=limit)
        return jsonify({"success": True, "data": builds}), 200
    except JenkinsError as e:
        return jsonify({
            "success": False,
            "error": {
                "type": "JENKINS_ERROR",
                "message": e.message,
                "retryable": e.status_code in (502, 503, 504),
            }
        }), e.status_code


@jenkins_bp.route("/health", methods=["GET"])
@jwt_required()
def health():
    try:
        status = _jenkins.health_check()
        return jsonify({"success": True, "data": status}), 200
    except JenkinsError as e:
        return jsonify({
            "success": False,
            "data": {"connected": False, "error": e.message},
        }), e.status_code
