import logging
from typing import Any, Dict, List, Optional

from orchestration.collectors.registry import CollectorRegistry
from orchestration.correlation.correlation_service import CorrelationService
from orchestration.events.event_types import EventType, OrchestrationEvent
from orchestration.incident.incident_service import IncidentService
from orchestration.interfaces.ai_interface import AIAnalysisService
from orchestration.interfaces.notification_interface import NotificationService
from orchestration.models.incident import (
    Evidence,
    OrchestrationIncident,
    TimelineEntry,
    UnifiedIncidentContext,
)
from orchestration.severity.severity_engine import SeverityEngine
from orchestration.services.event_service import EventService

logger = logging.getLogger(__name__)


class OrchestrationService:
    def __init__(self):
        self.event_service = EventService()
        self.correlation_service = CorrelationService()
        self.severity_engine = SeverityEngine()
        self.incident_service = IncidentService()
        self.collector_registry = CollectorRegistry()
        self.notification_service = NotificationService()
        self._ai_service: Optional[AIAnalysisService] = None

        self.severity_engine.load_default_rules()

    def set_ai_service(self, ai_service: AIAnalysisService):
        self._ai_service = ai_service

    def process_event(self, event: OrchestrationEvent) -> Optional[OrchestrationIncident]:
        self.event_service.dispatch(event)
        self.correlation_service.ingest(event)

        incident = self._evaluate_and_create_incident(event)
        return incident

    def _evaluate_and_create_incident(
        self, event: OrchestrationEvent
    ) -> Optional[OrchestrationIncident]:
        failure_events = {
            EventType.BUILD_FAILED,
            EventType.DEPLOYMENT_FAILED,
            EventType.CONTAINER_CRASHED,
            EventType.HEALTH_CHECK_FAILED,
        }

        if event.event_type not in failure_events:
            return None

        context = self.correlation_service.correlate()
        severity = self.severity_engine.calculate_severity(
            context=context,
            event_types=[e.event_type for e in context.raw_events],
        )

        evidence_list = self._collect_evidence(context, event)

        summary = self._build_summary(event, context)
        incident = self.incident_service.create_incident(
            summary=summary,
            severity=severity,
            repository=context.repository,
            environment=context.namespace,
            branch=context.branch,
            commit_sha=context.commit_sha,
            build_number=context.build_number,
            deployment_id=context.deployment,
            category=event.source,
        )

        for ev in evidence_list:
            self.incident_service.attach_evidence(incident.incident_id, ev)

        return incident

    def _collect_evidence(
        self, context: UnifiedIncidentContext, event: OrchestrationEvent
    ) -> List[Evidence]:
        evidence_list = []
        all_evidence = self.collector_registry.collect_all_evidence(
            context.to_dict()
        )
        for source, data in all_evidence.items():
            ev = Evidence(
                evidence_id=f"EVID-{source}",
                source=source,
                evidence_type="generic",
                data=data,
            )
            evidence_list.append(ev)
        return evidence_list

    def _build_summary(
        self, event: OrchestrationEvent, context: UnifiedIncidentContext
    ) -> str:
        base = f"{event.source}: {event.event_type.name}"
        if context.repository:
            base += f" [{context.repository}]"
        if context.pod_name:
            base += f" pod={context.pod_name}"
        return base

    def get_incident(self, incident_id: str) -> Optional[OrchestrationIncident]:
        return self.incident_service.get_incident(incident_id)

    def get_all_incidents(
        self, status: str = None, severity: str = None
    ) -> List[OrchestrationIncident]:
        return self.incident_service.get_all_incidents(status, severity)

    def resolve_incident(
        self, incident_id: str, notes: str = ""
    ) -> Optional[OrchestrationIncident]:
        return self.incident_service.resolve_incident(incident_id, notes)

    def merge_incidents(
        self, primary_id: str, secondary_ids: List[str]
    ) -> Optional[OrchestrationIncident]:
        return self.incident_service.merge_incidents(primary_id, secondary_ids)

    def get_event_history(
        self, event_type: str = None, source: str = None, limit: int = 100
    ) -> List[Dict[str, Any]]:
        et = EventType[event_type] if event_type else None
        events = self.event_service.get_history(event_type=et, source=source, limit=limit)
        return [e.to_dict() for e in events]

    def get_dashboard_stats(self) -> Dict[str, Any]:
        incidents = self.incident_service.get_all_incidents()
        active = [i for i in incidents if i.status == "open"]
        critical = [i for i in active if i.severity == "critical"]
        resolved = [i for i in incidents if i.status == "resolved"]

        avg_resolution_time = 0.0
        resolved_with_time = [
            i
            for i in resolved
            if i.resolved_at and i.created_at
        ]
        if resolved_with_time:
            total = sum(
                (i.resolved_at - i.created_at).total_seconds()
                for i in resolved_with_time
            )
            avg_resolution_time = total / len(resolved_with_time)

        return {
            "active_incidents": len(active),
            "critical_incidents": len(critical),
            "total_incidents": len(incidents),
            "resolved_incidents": len(resolved),
            "avg_resolution_time_seconds": avg_resolution_time,
            "event_buffer_size": self.correlation_service.get_buffer_size(),
            "registered_collectors": self.collector_registry.list_collectors(),
            "registered_notification_providers": self.notification_service.list_providers(),
        }
