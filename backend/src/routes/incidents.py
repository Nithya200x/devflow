import json

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from models import Incident
from services.incident_service import IncidentService
from utils.time import to_iso

incidents_bp = Blueprint('incidents', __name__)

@incidents_bp.route('', methods=['GET', 'POST'])
@jwt_required()
def handle_incidents():
    if request.method == 'GET':
        incidents = IncidentService.get_all()
        result = []
        for i in incidents:
            item = {
                "id": i.id,
                "title": i.title,
                "status": i.status,
                "severity": i.severity,
                "source": i.source or "",
                "description": i.description or "",
                "created_at": to_iso(i.created_at),
                "resolved_at": to_iso(i.resolved_at),
                "resolution_reason": i.resolution_reason or "",
                "ai_summary": "",
                "suggested_fixes": [],
                "timeline": [],
            }
            if i.timeline_json:
                try:
                    item["timeline"] = json.loads(i.timeline_json)
                except Exception:
                    pass
            if i.ai_analysis_id:
                try:
                    from orchestration.models.event_store import AIAnalysisStore
                    analysis = AIAnalysisStore.query.get(i.ai_analysis_id)
                    if analysis:
                        item["ai_summary"] = analysis.summary or ""
                        item["root_cause"] = analysis.root_cause or ""
                        item["confidence_score"] = analysis.confidence or 0.0
                        item["suggested_fixes"] = json.loads(analysis.suggested_fixes_json) if analysis.suggested_fixes_json else []
                        item["possible_causes"] = json.loads(analysis.possible_causes_json) if analysis.possible_causes_json else []
                        item["preventive_actions"] = json.loads(analysis.preventive_actions_json) if analysis.preventive_actions_json else []
                        item["risk_assessment"] = analysis.risk_assessment or ""
                        item["estimated_resolution_time"] = analysis.estimated_resolution_time or ""
                        item["requires_human"] = analysis.requires_human or False
                        item["affected_components"] = json.loads(analysis.affected_components_json) if analysis.affected_components_json else []
                except Exception:
                    pass
            result.append(item)
        return jsonify(result), 200

    elif request.method == 'POST':
        data = request.get_json()
        if not data or not data.get('title'):
            return jsonify({"msg": "title is required"}), 400
        i = IncidentService.create(
            title=data.get('title'),
            severity=data.get('severity', 'medium'),
            project_id=data.get('project_id'),
        )
        if i.project_id:
            from services.repository_health_service import get_health_service
            get_health_service().invalidate(i.project_id)
        return jsonify({"message": "Incident created", "id": i.id}), 201

@incidents_bp.route('/<int:incident_id>', methods=['PATCH'])
@jwt_required()
def update_incident(incident_id):
    data = request.get_json()
    if not data:
        return jsonify({"msg": "Request body is required"}), 400
    i = IncidentService.update(incident_id, data.get('status'))
    if i and i.project_id:
        from services.repository_health_service import get_health_service
        get_health_service().invalidate(i.project_id)
    return jsonify({"message": "Incident updated"}), 200
