import datetime
import logging
import uuid
from typing import Any, Dict, List, Optional

from orchestration.models.incident import (
    Evidence,
    OrchestrationIncident,
    TimelineEntry,
)

logger = logging.getLogger(__name__)


class IncidentService:
    def __init__(self):
        self._incidents: Dict[str, OrchestrationIncident] = {}

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
    ) -> OrchestrationIncident:
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
            created_at=datetime.datetime.utcnow(),
        )
        self._incidents[incident_id] = incident
        self.add_timeline_event(
            incident_id, "incident_created", "system", f"Incident {incident_id} created"
        )
        logger.info(f"Incident created: {incident_id} ({severity})")
        return incident

    def get_incident(self, incident_id: str) -> Optional[OrchestrationIncident]:
        return self._incidents.get(incident_id)

    def get_all_incidents(
        self, status: str = None, severity: str = None
    ) -> List[OrchestrationIncident]:
        results = list(self._incidents.values())
        if status:
            results = [i for i in results if i.status == status]
        if severity:
            results = [i for i in results if i.severity == severity]
        return sorted(results, key=lambda i: i.created_at, reverse=True)

    def update_incident(
        self, incident_id: str, updates: Dict[str, Any]
    ) -> Optional[OrchestrationIncident]:
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
        return incident

    def resolve_incident(
        self, incident_id: str, resolution_notes: str = ""
    ) -> Optional[OrchestrationIncident]:
        incident = self._incidents.get(incident_id)
        if not incident:
            return None
        incident.status = "resolved"
        incident.resolved_at = datetime.datetime.utcnow()
        incident.resolution_notes = resolution_notes
        self.add_timeline_event(
            incident_id,
            "incident_resolved",
            "system",
            f"Incident {incident_id} resolved",
        )
        logger.info(f"Incident resolved: {incident_id}")
        return incident

    def merge_incidents(self, primary_id: str, secondary_ids: List[str]) -> Optional[OrchestrationIncident]:
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
        return primary

    def attach_evidence(self, incident_id: str, evidence: Evidence) -> bool:
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
        incident = self._incidents.get(incident_id)
        if not incident:
            return None
        incident.status = "archived"
        self.add_timeline_event(
            incident_id, "incident_archived", "system", f"Incident {incident_id} archived"
        )
        return incident

    def delete_incident(self, incident_id: str) -> bool:
        if incident_id in self._incidents:
            del self._incidents[incident_id]
            return True
        return False
