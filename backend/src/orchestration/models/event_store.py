import datetime

from extensions import db


class EventStore(db.Model):
    __tablename__ = "event_store"

    id = db.Column(db.Integer, primary_key=True)
    event_type = db.Column(db.String(100), nullable=False)
    source = db.Column(db.String(100), nullable=False)
    metadata_json = db.Column(db.Text, default="{}")
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def to_dict(self):
        import json
        return {
            "id": self.id,
            "event_type": self.event_type,
            "source": self.source,
            "metadata": json.loads(self.metadata_json) if self.metadata_json else {},
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }


class IncidentEvidenceStore(db.Model):
    __tablename__ = "incident_evidence"

    id = db.Column(db.Integer, primary_key=True)
    incident_id = db.Column(db.String(50), nullable=False)
    evidence_id = db.Column(db.String(50), nullable=False)
    source = db.Column(db.String(100), nullable=False)
    evidence_type = db.Column(db.String(100), default="generic")
    data_json = db.Column(db.Text, default="{}")
    collected_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def to_dict(self):
        import json
        return {
            "id": self.id,
            "incident_id": self.incident_id,
            "evidence_id": self.evidence_id,
            "source": self.source,
            "evidence_type": self.evidence_type,
            "data": json.loads(self.data_json) if self.data_json else {},
            "collected_at": self.collected_at.isoformat() if self.collected_at else None,
        }


class IncidentTimelineStore(db.Model):
    __tablename__ = "incident_timeline"

    id = db.Column(db.Integer, primary_key=True)
    incident_id = db.Column(db.String(50), nullable=False)
    event_type = db.Column(db.String(100), nullable=False)
    source = db.Column(db.String(100), default="")
    description = db.Column(db.Text, default="")
    metadata_json = db.Column(db.Text, default="{}")
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def to_dict(self):
        import json
        return {
            "id": self.id,
            "incident_id": self.incident_id,
            "event_type": self.event_type,
            "source": self.source,
            "description": self.description,
            "metadata": json.loads(self.metadata_json) if self.metadata_json else {},
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }


class AIAnalysisStore(db.Model):
    __tablename__ = "ai_analysis"

    id = db.Column(db.Integer, primary_key=True)
    incident_id = db.Column(db.String(50), nullable=False, index=True)
    summary = db.Column(db.Text, default="")
    root_cause = db.Column(db.String(255), default="")
    confidence = db.Column(db.Float, default=0.0)
    severity = db.Column(db.String(20), default="")
    affected_components_json = db.Column(db.Text, default="[]")
    possible_causes_json = db.Column(db.Text, default="[]")
    suggested_fixes_json = db.Column(db.Text, default="[]")
    preventive_actions_json = db.Column(db.Text, default="[]")
    similar_patterns_json = db.Column(db.Text, default="[]")
    risk_assessment = db.Column(db.Text, default="")
    estimated_resolution_time = db.Column(db.String(100), default="")
    requires_human = db.Column(db.Boolean, default=False)
    provider = db.Column(db.String(50), default="")
    model = db.Column(db.String(100), default="")
    prompt_version = db.Column(db.String(20), default="")
    analyzed_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def to_dict(self):
        import json
        return {
            "id": self.id,
            "incident_id": self.incident_id,
            "summary": self.summary,
            "root_cause": self.root_cause,
            "confidence": self.confidence,
            "severity": self.severity,
            "affected_components": json.loads(self.affected_components_json) if self.affected_components_json else [],
            "possible_causes": json.loads(self.possible_causes_json) if self.possible_causes_json else [],
            "suggested_fixes": json.loads(self.suggested_fixes_json) if self.suggested_fixes_json else [],
            "preventive_actions": json.loads(self.preventive_actions_json) if self.preventive_actions_json else [],
            "similar_patterns": json.loads(self.similar_patterns_json) if self.similar_patterns_json else [],
            "risk_assessment": self.risk_assessment,
            "estimated_resolution_time": self.estimated_resolution_time,
            "requires_human": self.requires_human,
            "provider": self.provider,
            "model": self.model,
            "prompt_version": self.prompt_version,
            "analyzed_at": self.analyzed_at.isoformat() if self.analyzed_at else None,
        }
