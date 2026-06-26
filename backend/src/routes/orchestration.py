from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from orchestration import OrchestrationService
from orchestration.events.event_types import (
    BuildFailed,
    BuildStarted,
    BuildSucceeded,
    ContainerCrashed,
    DeploymentFailed,
    DeploymentRequested,
    DeploymentStarted,
    DeploymentSucceeded,
    HealthCheckFailed,
    HighCPUDetected,
    HighMemoryDetected,
    IncidentCreated,
    IncidentResolved,
    PodRestarted,
    RepositoryConnected,
)

orchestration_bp = Blueprint("orchestration", __name__)

_service = OrchestrationService()


@orchestration_bp.route("/events", methods=["POST"])
@jwt_required()
def ingest_event():
    data = request.get_json()
    if not data or "event_type" not in data:
        return jsonify({"msg": "event_type is required"}), 400

    event_type = data["event_type"]
    metadata = data.get("metadata", {})

    event_map = {
        "REPOSITORY_CONNECTED": RepositoryConnected,
        "DEPLOYMENT_REQUESTED": DeploymentRequested,
        "BUILD_STARTED": BuildStarted,
        "BUILD_SUCCEEDED": BuildSucceeded,
        "BUILD_FAILED": BuildFailed,
        "DEPLOYMENT_STARTED": DeploymentStarted,
        "DEPLOYMENT_SUCCEEDED": DeploymentSucceeded,
        "DEPLOYMENT_FAILED": DeploymentFailed,
        "CONTAINER_CRASHED": ContainerCrashed,
        "POD_RESTARTED": PodRestarted,
        "HIGH_CPU_DETECTED": HighCPUDetected,
        "HIGH_MEMORY_DETECTED": HighMemoryDetected,
        "HEALTH_CHECK_FAILED": HealthCheckFailed,
        "INCIDENT_CREATED": IncidentCreated,
        "INCIDENT_RESOLVED": IncidentResolved,
    }

    cls = event_map.get(event_type)
    if not cls:
        return jsonify({"msg": f"Unknown event_type: {event_type}"}), 400

    event = cls(**metadata)
    incident = _service.process_event(event)

    return jsonify({
        "message": "Event processed",
        "event_type": event_type,
        "incident_created": incident is not None,
        "incident_id": incident.incident_id if incident else None,
    }), 202


@orchestration_bp.route("/incidents", methods=["GET"])
@jwt_required()
def list_incidents():
    status = request.args.get("status")
    severity = request.args.get("severity")
    incidents = _service.get_all_incidents(status, severity)
    return jsonify([i.to_dict() for i in incidents]), 200


@orchestration_bp.route("/incidents/<incident_id>", methods=["GET"])
@jwt_required()
def get_incident(incident_id):
    incident = _service.get_incident(incident_id)
    if not incident:
        return jsonify({"msg": "Incident not found"}), 404
    return jsonify(incident.to_dict()), 200


@orchestration_bp.route("/incidents/<incident_id>/resolve", methods=["POST"])
@jwt_required()
def resolve_incident(incident_id):
    data = request.get_json() or {}
    incident = _service.resolve_incident(incident_id, data.get("notes", ""))
    if not incident:
        return jsonify({"msg": "Incident not found"}), 404
    return jsonify({"message": "Incident resolved", "incident": incident.to_dict()}), 200


@orchestration_bp.route("/incidents/merge", methods=["POST"])
@jwt_required()
def merge_incidents():
    data = request.get_json()
    if not data or "primary_id" not in data or "secondary_ids" not in data:
        return jsonify({"msg": "primary_id and secondary_ids are required"}), 400
    incident = _service.merge_incidents(data["primary_id"], data["secondary_ids"])
    if not incident:
        return jsonify({"msg": "Primary incident not found"}), 404
    return jsonify({"message": "Incidents merged", "incident": incident.to_dict()}), 200


@orchestration_bp.route("/history", methods=["GET"])
@jwt_required()
def get_event_history():
    event_type = request.args.get("event_type")
    source = request.args.get("source")
    limit = request.args.get("limit", 100, type=int)
    events = _service.get_event_history(event_type, source, limit)
    return jsonify(events), 200


@orchestration_bp.route("/dashboard", methods=["GET"])
@jwt_required()
def get_dashboard():
    stats = _service.get_dashboard_stats()
    return jsonify(stats), 200


@orchestration_bp.route("/collectors", methods=["GET"])
@jwt_required()
def list_collectors():
    collectors = _service.collector_registry.list_collectors()
    return jsonify({"collectors": collectors}), 200


@orchestration_bp.route("/severity/rules", methods=["GET"])
@jwt_required()
def list_severity_rules():
    rules = _service.severity_engine.list_rules()
    return jsonify({"rules": rules}), 200
