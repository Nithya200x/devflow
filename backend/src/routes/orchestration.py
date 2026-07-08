import inspect

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from extensions import db, retry_on_db_disconnect
from orchestration.models.event_store import AIAnalysisStore
from utils.time import to_iso

from orchestration.services.orchestration_service import get_orchestrator
from orchestration.detectors.detector_config import detector_config
from orchestration.events.event_types import (
    ContainerCrashed,
    ContainerExited,
    ContainerOOMKilled,
    ContainerUnhealthy,
    CrashLoopBackOff,
    DeploymentFailed,
    DeploymentRequested,
    DeploymentStarted,
    DeploymentSucceeded,
    FailedScheduling,
    HealthCheckFailed,
    HighCPUDetected,
    HighMemoryDetected,
    ImagePullBackOff,
    IncidentCreated,
    IncidentResolved,
    NodeNotReady,
    PodRestarted,
    RepositoryConnected,
)

orchestration_bp = Blueprint("orchestration", __name__)

_service = get_orchestrator()


@orchestration_bp.route("/events", methods=["POST"])
@jwt_required()
def ingest_event():
    data = request.get_json()
    if not data or "event_type" not in data:
        return jsonify({"msg": "event_type is required"}), 400

    event_type = data["event_type"]
    project_id = data.get("project_id")
    repository_owner = data.get("repository_owner")
    repository_name = data.get("repository_name")
    metadata = data.get("metadata", {})

    event_map = {
        "REPOSITORY_CONNECTED": RepositoryConnected,
        "DEPLOYMENT_REQUESTED": DeploymentRequested,
        "DEPLOYMENT_STARTED": DeploymentStarted,
        "DEPLOYMENT_SUCCEEDED": DeploymentSucceeded,
        "DEPLOYMENT_FAILED": DeploymentFailed,
        "CONTAINER_CRASHED": ContainerCrashed,
        "CONTAINER_EXITED": ContainerExited,
        "CONTAINER_UNHEALTHY": ContainerUnhealthy,
        "CONTAINER_OOM_KILLED": ContainerOOMKilled,
        "CRASH_LOOP_BACK_OFF": CrashLoopBackOff,
        "IMAGE_PULL_BACK_OFF": ImagePullBackOff,
        "FAILED_SCHEDULING": FailedScheduling,
        "NODE_NOT_READY": NodeNotReady,
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

    sig = inspect.signature(cls.__init__)
    valid_params = set(sig.parameters.keys()) - {"self"}
    clean_meta = {k: v for k, v in metadata.items() if k in valid_params}
    extra_meta = {k: v for k, v in metadata.items() if k not in valid_params}
    event = cls(**clean_meta)
    event.metadata.update(extra_meta)
    if project_id is not None:
        event.metadata["project_id"] = project_id
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


@orchestration_bp.route("/incidents/<incident_id>/analyze", methods=["POST"])
@jwt_required()
def trigger_analysis(incident_id):
    incident = _service.get_incident(incident_id)
    if not incident:
        return jsonify({"msg": "Incident not found"}), 404
    try:
        from orchestration.ai.service import trigger_ai_analysis
        trigger_ai_analysis(incident_id)
        return jsonify({"message": "AI analysis triggered", "incident_id": incident_id}), 202
    except Exception as e:
        return jsonify({"msg": f"Failed to trigger AI analysis: {str(e)}"}), 500


@orchestration_bp.route("/incidents/<incident_id>/analysis", methods=["GET"])
@jwt_required()
def get_analysis(incident_id):
    incident = _service.get_incident(incident_id)
    if not incident:
        return jsonify({"msg": "Incident not found"}), 404
    return jsonify({
        "incident_id": incident.incident_id,
        "ai_analysis": incident.ai_analysis if incident.ai_analysis else None,
        "ai_metadata": incident.ai_metadata if hasattr(incident, "ai_metadata") else {},
        "root_cause": incident.root_cause or "",
        "confidence_score": incident.confidence_score,
        "suggested_fixes": incident.suggested_fixes or [],
        "possible_causes": incident.possible_causes or [],
        "preventive_actions": incident.preventive_actions or [],
        "similar_patterns": incident.similar_patterns or [],
        "risk_assessment": incident.risk_assessment or "",
        "estimated_resolution_time": incident.estimated_resolution_time or "",
        "requires_human": incident.requires_human,
        "affected_components": incident.affected_components or [],
        "status": "completed" if incident.ai_analysis else "pending",
    }), 200


@orchestration_bp.route("/ai/analyses/db", methods=["GET"])
@jwt_required()
@retry_on_db_disconnect()
def list_db_analyses():
    records = AIAnalysisStore.query.order_by(AIAnalysisStore.analyzed_at.desc()).limit(50).all()
    return jsonify({"analyses": [r.to_dict() for r in records]}), 200


@orchestration_bp.route("/ai/analyses/db/<incident_id>", methods=["GET"])
@jwt_required()
def get_db_analysis(incident_id):
    record = AIAnalysisStore.query.filter_by(incident_id=incident_id).order_by(AIAnalysisStore.analyzed_at.desc()).first()
    if not record:
        return jsonify({"msg": "No analysis found"}), 404
    return jsonify(record.to_dict()), 200


@orchestration_bp.route("/ai/analyses", methods=["GET"])
@jwt_required()
def list_analyses():
    incidents = _service.get_all_incidents()
    results = []
    for inc in incidents:
        if inc.ai_analysis:
            results.append({
                "incident_id": inc.incident_id,
                "summary": inc.summary,
                "root_cause": inc.root_cause or "",
                "confidence_score": inc.confidence_score,
                "severity": inc.severity,
                "status": inc.status,
                "created_at": to_iso(inc.created_at),
                "suggested_fixes": inc.suggested_fixes or [],
                "affected_components": inc.affected_components or [],
                "risk_assessment": inc.risk_assessment or "",
                "estimated_resolution_time": inc.estimated_resolution_time or "",
                "requires_human": inc.requires_human,
                "possible_causes": inc.possible_causes or [],
                "preventive_actions": inc.preventive_actions or [],
                "similar_patterns": inc.similar_patterns or [],
            })
    return jsonify({"analyses": results}), 200


@orchestration_bp.route("/detector/config", methods=["GET"])
@jwt_required()
def get_detector_config():
    config = detector_config.get_all()
    return jsonify({"config": config}), 200


@orchestration_bp.route("/detector/config/<trigger_key>", methods=["PATCH"])
@jwt_required()
def update_detector_config(trigger_key):
    data = request.get_json()
    if not data:
        return jsonify({"msg": "Request body is required"}), 400

    updated = detector_config.update(trigger_key, data)
    if not updated:
        return jsonify({"msg": f"Unknown trigger: {trigger_key}"}), 404

    return jsonify({"message": "Config updated", "config": updated}), 200
