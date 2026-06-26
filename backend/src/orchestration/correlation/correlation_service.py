import logging
from typing import Any, Dict, List, Optional

from orchestration.events.event_types import OrchestrationEvent
from orchestration.models.incident import UnifiedIncidentContext

logger = logging.getLogger(__name__)


class CorrelationService:
    def __init__(self):
        self._event_buffer: List[OrchestrationEvent] = []

    def ingest(self, event: OrchestrationEvent):
        self._event_buffer.append(event)
        logger.debug(
            f"Event ingested: {event.event_type.name} from {event.source}"
        )

    def correlate(self, events: List[OrchestrationEvent] = None) -> UnifiedIncidentContext:
        target = events or self._event_buffer
        context = UnifiedIncidentContext()

        for event in target:
            meta = event.metadata
            source = event.source

            if source == "github":
                context.repository = meta.get("repository", context.repository)
                context.branch = meta.get("branch", context.branch)
                context.commit_sha = meta.get("commit_sha", context.commit_sha)

            elif source == "jenkins":
                context.build_number = meta.get("build_number", context.build_number)
                context.repository = meta.get("repository", context.repository)

            elif source == "kubernetes":
                context.deployment = meta.get("deployment", context.deployment)
                context.pod_name = meta.get("pod_name", context.pod_name)
                context.namespace = meta.get("namespace", context.namespace)
                context.container_id = meta.get("container_id", context.container_id)

            elif source == "docker":
                context.docker_image = meta.get("image", context.docker_image)
                context.container_id = meta.get("container_id", context.container_id)

            elif source == "prometheus":
                context.cpu_usage = meta.get("cpu_percent", context.cpu_usage)
                context.memory_usage = meta.get("memory_percent", context.memory_usage)
                context.pod_name = meta.get("pod_name", context.pod_name)
                context.namespace = meta.get("namespace", context.namespace)

        context.raw_events = target
        logger.info(
            f"Correlated {len(target)} events into context for {context.repository or 'unknown'}"
        )
        return context

    def clear_buffer(self):
        self._event_buffer.clear()

    def get_buffer_size(self) -> int:
        return len(self._event_buffer)
