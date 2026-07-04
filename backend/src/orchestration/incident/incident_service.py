import datetime
import json
import logging
import uuid
from typing import Any, Dict, List, Optional

from extensions import db as _db
from models import Incident as IncidentDB
from orchestration.models.incident import (
    Evidence,
    OrchestrationIncident,
    TimelineEntry,
)
from utils.time import now

logger = logging.getLogger(__name__)


class IncidentService:
    def __init__(self):
        self._incidents: Dict[str, OrchestrationIncident] = {}
        self._loaded = False

    def _ensure_loaded(self):
        if self._loaded:
            return
        self._loaded = True
        try:
            records = IncidentDB.query.filter(
                IncidentDB.status != "resolved"
            ).all()
            for rec in records:
                try:
                    evidence_list = [
                        Evidence.from_dict(e)
                        for e in json.loads(rec.evidence_json or "[]")
                    ]
                    timeline_list = [
                        TimelineEntry.from_dict(t)
                        for t in json.loads(rec.timeline_json or "[]")
                    ]
                    created_at = rec.created_at
                    if created_at and created_at.tzinfo is None:
                        created_at = created_at.replace(tzinfo=datetime.timezone.utc)
                    resolved_at = rec.resolved_at
                    if resolved_at and resolved_at.tzinfo is None:
                        resolved_at = resolved_at.replace(tzinfo=datetime.timezone.utc)
                    incident = OrchestrationIncident(
                        incident_id=rec.incident_id,
                        summary=rec.title,
                        description=rec.description or "",
                        severity=rec.severity,
                        status=rec.status,
                        created_at=created_at,
                        resolved_at=resolved_at,
                        evidence=evidence_list,
                        timeline=timeline_list,
                    )
                    incident.project_id = getattr(rec, "project_id", None)
                    self._incidents[incident.incident_id] = incident
                except Exception:
                    logger.exception("Failed to load incident %s from DB", rec.incident_id)
            if records:
                logger.info("Loaded %d incidents from DB", len(records))
        except Exception:
            logger.exception("Failed to load incidents from DB")

    def create_incident(
        self,
        summary: str,
        severity: str = "medium",
        repository: str = "",
        project: str = "",
        environment: str = "",
        branch: str = "",
        commit_sha: str = "",
        build_number: str = "",
        deployment_id: str = "",
        category: str = "",
        description: str = "",
        assigned_to: str = "",
        project_id: int = None,
    ) -> OrchestrationIncident:
        self._ensure_loaded()
        incident_id = f"INC-{uuid.uuid4().hex[:8].upper()}"
        incident = OrchestrationIncident(
            incident_id=incident_id,
            summary=summary,
            severity=severity,
            repository=repository,
            project=project,
            environment=environment,
            branch=branch,
            commit_sha=commit_sha,
            build_number=build_number,
            deployment_id=deployment_id,
            category=category,
            description=description,
            assigned_to=assigned_to,
            status="open",
            created_at=datetime.datetime.now(datetime.timezone.utc),
        )
        incident.project_id = project_id
        self._incidents[incident_id] = incident

        self._persist_to_db(incident, project_id)

        self.add_timeline_event(
            incident_id, "incident_created", "system", f"Incident {incident_id} created"
        )
        logger.info(f"Incident created: {incident_id} ({severity})")
        return incident

    def _persist_to_db(self, incident: OrchestrationIncident, project_id: int = None):
        try:
            rec = IncidentDB.query.filter_by(incident_id=incident.incident_id).first()
            pid = project_id or getattr(incident, "project_id", None)
            if rec:
                rec.title = incident.summary
                rec.description = incident.description
                rec.status = incident.status
                rec.severity = incident.severity
                rec.source = incident.category or ""
                rec.evidence_json = json.dumps(
                    [e.to_dict() for e in incident.evidence], default=str
                )
                rec.timeline_json = json.dumps(
                    [t.to_dict() for t in incident.timeline], default=str
                )
                rec.resolved_at = incident.resolved_at
                rec.project_id = pid
            else:
                rec = IncidentDB(
                    incident_id=incident.incident_id,
                    title=incident.summary,
                    description=incident.description,
                    status=incident.status,
                    severity=incident.severity,
                    source=incident.category or "",
                    project_id=pid,
                    evidence_json=json.dumps(
                        [e.to_dict() for e in incident.evidence], default=str
                    ),
                    timeline_json=json.dumps(
                        [t.to_dict() for t in incident.timeline], default=str
                    ),
                    created_at=incident.created_at,
                    resolved_at=incident.resolved_at,
                )
                _db.session.add(rec)
            _db.session.commit()
        except Exception:
            _db.session.rollback()
            logger.exception("Failed to persist incident %s to DB", incident.incident_id)

    def get_incident(self, incident_id: str) -> Optional[OrchestrationIncident]:
        self._ensure_loaded()
        return self._incidents.get(incident_id)

    def get_all_incidents(
        self, status: str = None, severity: str = None
    ) -> List[OrchestrationIncident]:
        self._ensure_loaded()
        results = list(self._incidents.values())
        if status:
            results = [i for i in results if i.status == status]
        if severity:
            results = [i for i in results if i.severity == severity]
        return sorted(results, key=lambda i: i.created_at, reverse=True)

    def update_incident(
        self, incident_id: str, updates: Dict[str, Any]
    ) -> Optional[OrchestrationIncident]:
        self._ensure_loaded()
        incident = self._incidents.get(incident_id)
        if not incident:
            return None
        for key, value in updates.items():
            if hasattr(incident, key) and key not in (
                "incident_id",
                "created_at",
                "evidence",
                "timeline",
            ):
                setattr(incident, key, value)
        self._persist_to_db(incident)
        return incident

    def resolve_incident(
        self, incident_id: str, resolution_notes: str = ""
    ) -> Optional[OrchestrationIncident]:
        self._ensure_loaded()
        incident = self._incidents.get(incident_id)
        if not incident:
            return None
        incident.status = "resolved"
        incident.resolved_at = datetime.datetime.now(datetime.timezone.utc)
        incident.resolution_notes = resolution_notes
        self.add_timeline_event(
            incident_id,
            "incident_resolved",
            "system",
            f"Incident {incident_id} resolved",
        )
        self._persist_to_db(incident)
        logger.info(f"Incident resolved: {incident_id}")
        return incident

    def merge_incidents(self, primary_id: str, secondary_ids: List[str]) -> Optional[OrchestrationIncident]:
        self._ensure_loaded()
        primary = self._incidents.get(primary_id)
        if not primary:
            return None
        for sid in secondary_ids:
            secondary = self._incidents.pop(sid, None)
            if secondary:
                primary.related_incidents.append(sid)
                primary.timeline.extend(secondary.timeline)
                primary.evidence.extend(secondary.evidence)
                self.add_timeline_event(
                    primary_id,
                    "incident_merged",
                    "system",
                    f"Merged incident {sid} into {primary_id}",
                )
        self._persist_to_db(primary)
        return primary

    def attach_evidence(self, incident_id: str, evidence: Evidence) -> bool:
        self._ensure_loaded()
        incident = self._incidents.get(incident_id)
        if not incident:
            return False
        incident.evidence.append(evidence)
        self.add_timeline_event(
            incident_id,
            "evidence_attached",
            evidence.source,
            f"Evidence attached from {evidence.source}",
        )
        self._persist_to_db(incident)
        return True

    def attach_timeline_event(
        self, incident_id: str, entry: TimelineEntry
    ) -> bool:
        incident = self._incidents.get(incident_id)
        if not incident:
            return False
        incident.timeline.append(entry)
        return True

    def add_timeline_event(
        self,
        incident_id: str,
        event_type: str,
        source: str,
        description: str,
        metadata: Dict[str, Any] = None,
    ) -> bool:
        self._ensure_loaded()
        incident = self._incidents.get(incident_id)
        if not incident:
            return False
        entry = TimelineEntry(
            event_type=event_type,
            source=source,
            description=description,
            metadata=metadata or {},
        )
        incident.timeline.append(entry)
        return True

    def close_incident(self, incident_id: str) -> Optional[OrchestrationIncident]:
        return self.resolve_incident(incident_id, "Closed without resolution")

    def archive_incident(self, incident_id: str) -> Optional[OrchestrationIncident]:
        self._ensure_loaded()
        incident = self._incidents.get(incident_id)
        if not incident:
            return None
        incident.status = "archived"
        self.add_timeline_event(
            incident_id, "incident_archived", "system", f"Incident {incident_id} archived"
        )
        self._persist_to_db(incident)
        return incident

    def delete_incident(self, incident_id: str) -> bool:
        self._ensure_loaded()
        if incident_id in self._incidents:
            del self._incidents[incident_id]
            try:
                IncidentDB.query.filter_by(incident_id=incident_id).delete()
                _db.session.commit()
            except Exception:
                _db.session.rollback()
            return True
        return False
