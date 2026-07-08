import logging
from typing import Any, Dict, List, Optional

from orchestration.collectors.registry import CollectorRegistry
from orchestration.correlation.correlation_service import CorrelationService
from orchestration.events.event_types import (
    EventType,
    IncidentCreated,
    OrchestrationEvent,
)
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


_singleton = None


def get_orchestrator():
    global _singleton
    if _singleton is None:
        _singleton = OrchestrationService()
    return _singleton


class OrchestrationService:
    def __init__(self):
        if getattr(self, '_initialized', False):
            return
        self.event_service = EventService()
        self.correlation_service = CorrelationService()
        self.severity_engine = SeverityEngine()
        self.incident_service = IncidentService()
        self.collector_registry = CollectorRegistry()
        self.notification_service = NotificationService()
        self._ai_service: Optional[AIAnalysisService] = None

        self.severity_engine.load_default_rules()
        self._initialized = True

    def set_ai_service(self, ai_service: AIAnalysisService):
        self._ai_service = ai_service

    def process_event(self, event: OrchestrationEvent) -> Optional[OrchestrationIncident]:
        self._add_timeline_entry(event)
        self.event_service.dispatch(event)
        self.correlation_service.ingest(event)

        incident = self._evaluate_and_create_incident(event)
        return incident

    def _add_timeline_entry(self, event: OrchestrationEvent):
        meta = event.metadata
        desc = f"{event.source}: {event.event_type.name}"
        if meta.get("repository"):
            desc += f" [{meta['repository']}]"
        if meta.get("branch"):
            desc += f" ({meta['branch']})"

        self.event_service.dispatch(event)
        logger.info(f"Timeline: {desc}")

    def _evaluate_and_create_incident(
        self, event: OrchestrationEvent
    ) -> Optional[OrchestrationIncident]:
        failure_events = {
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

        meta = event.metadata
        build_info = meta.get("build_info", {})

        evidence_list = self._collect_evidence(context, event)

        summary = self._build_summary(event, context)
        description = self._build_description(event, context, build_info)

        project_id = event.metadata.get("project_id")

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
            description=description,
            project_id=project_id,
        )

        logger.info("=== EXECUTION ORDER: Incident created (%s) [1. Event → 2. Correlation → 3. Severity → 4. Incident creation] ===", incident.incident_id)

        for ev in evidence_list:
            self.incident_service.attach_evidence(incident.incident_id, ev)

        logger.info("=== EXECUTION ORDER: Evidence attached [5. Persistence] ===")

        self.incident_service.add_timeline_event(
            incident.incident_id,
            "severity_assigned",
            "severity_engine",
            f"Severity classified as {severity}",
        )

        self.incident_service.add_timeline_event(
            incident.incident_id,
            "evidence_collected",
            "collector_registry",
            f"Collected evidence from {len(evidence_list)} collector(s)",
        )

        self.incident_service.add_timeline_event(
            incident.incident_id,
            "incident_created",
            "orchestration",
            f"Incident {incident.incident_id} created",
        )

        logger.info("=== EXECUTION ORDER: Timeline entries added [6. Timeline] ===")
        logger.info("=== EXECUTION ORDER: Incident store has %d incidents [PERSISTED] ===", len(self.incident_service._incidents))

        try:
            created_event = IncidentCreated(
                incident_id=incident.incident_id,
                summary=summary,
                severity=severity,
                metadata={
                    "repository": context.repository,
                    "build_number": context.build_number,
                    "project_id": project_id,
                },
            )
            self.event_service.dispatch(created_event)
            logger.info(f"IncidentCreated event published for {incident.incident_id}")
        except Exception as e:
            logger.warning(f"Failed to publish IncidentCreated event: {e}")

        logger.info("=== EXECUTION ORDER: Triggering AI analysis [7. AI thread start] ===")
        try:
            from orchestration.ai.service import trigger_ai_analysis
            trigger_ai_analysis(incident.incident_id)
        except Exception as e:
            logger.warning(f"Failed to trigger AI analysis: {e}")

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
                evidence_id=f"EVID-{source}-{event.timestamp.strftime('%H%M%S')}",
                source=source,
                evidence_type="generic",
                data=data,
            )
            evidence_list.append(ev)
        return evidence_list

    def _build_summary(
        self, event: OrchestrationEvent, context: UnifiedIncidentContext
    ) -> str:
        meta = event.metadata
        base = f"{event.source}: {event.event_type.name}"
        if context.repository:
            base += f" [{context.repository}]"
        build_num = context.build_number or meta.get("build_number", "")
        if build_num:
            base += f" build #{build_num}"
        if context.branch:
            base += f" ({context.branch})"
        if context.pod_name:
            base += f" pod={context.pod_name}"
        if context.container_id:
            base += f" container={context.container_id}"
        if context.deployment:
            base += f" deployment={context.deployment}"
        reason = meta.get("reason", "")
        if reason:
            base += f" [{reason}]"
        return base

    def _build_description(
        self, event: OrchestrationEvent, context: UnifiedIncidentContext, build_info: dict
    ) -> str:
        lines = []
        meta = event.metadata
        if context.repository:
            lines.append(f"Repository: {context.repository}")
        if context.branch:
            lines.append(f"Branch: {context.branch}")
        if context.commit_sha:
            lines.append(f"Commit: {context.commit_sha}")
        build_num = context.build_number or event.metadata.get("build_number", "")
        if build_num:
            lines.append(f"Build: #{build_num}")
        if build_info:
            url = build_info.get("url", "")
            if url:
                lines.append(f"Build URL: {url}")
            result = build_info.get("result", "")
            if result:
                lines.append(f"Result: {result}")
            duration = build_info.get("duration_ms", 0)
            if duration:
                lines.append(f"Duration: {duration / 1000:.1f}s")
            params = build_info.get("parameters", {})
            if params:
                triggered = params.get("TRIGGERED_BY", "")
                if triggered:
                    lines.append(f"Triggered by: {triggered}")
        if context.container_id:
            lines.append(f"Container: {context.container_id}")
            lines.append(f"Image: {context.docker_image or 'N/A'}")
        if context.pod_name:
            lines.append(f"Pod: {context.pod_name}")
        if context.namespace:
            lines.append(f"Namespace: {context.namespace}")
        if context.deployment:
            lines.append(f"Deployment: {context.deployment}")
        reason = meta.get("reason", "")
        if reason:
            lines.append(f"Reason: {reason}")
        exit_code = meta.get("exit_code", "")
        if exit_code:
            lines.append(f"Exit Code: {exit_code}")
        restart_count = meta.get("restart_count", 0)
        if restart_count:
            lines.append(f"Restart Count: {restart_count}")
        image = meta.get("image", "")
        if image:
            lines.append(f"Image: {image}")
        alertname = meta.get("alertname", "")
        if alertname:
            lines.append(f"Alert: {alertname}")
            summary = meta.get("summary", "")
            if summary:
                lines.append(f"Summary: {summary}")
        if context.cpu_usage:
            lines.append(f"CPU Usage: {context.cpu_usage:.1f}%")
        if context.memory_usage:
            lines.append(f"Memory Usage: {context.memory_usage:.1f}%")
        return "\n".join(lines) if lines else f"Automatically detected {event.event_type.name}"

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
