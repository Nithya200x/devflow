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
