import logging
from typing import Any, Dict, List, Optional

from orchestration.events.event_types import OrchestrationEvent
from orchestration.models.incident import UnifiedIncidentContext

logger = logging.getLogger(__name__)


class CorrelationService:
    MAX_BUFFER_SIZE = 1000

    def __init__(self):
        self._event_buffer: List[OrchestrationEvent] = []

    def ingest(self, event: OrchestrationEvent):
        if len(self._event_buffer) >= self.MAX_BUFFER_SIZE:
            self._event_buffer.pop(0)
            logger.warning(
                "Event buffer at capacity (%d), discarding oldest event",
                self.MAX_BUFFER_SIZE,
            )
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
                context.branch = meta.get("branch", context.branch)
                context.commit_sha = meta.get("commit_sha", context.commit_sha)

            elif source == "kubernetes":
                context.deployment = meta.get("deployment", context.deployment)
                context.pod_name = meta.get("pod_name", context.pod_name)
                context.namespace = meta.get("namespace", context.namespace)
                context.container_id = meta.get("container_id", context.container_id)
                context.docker_image = meta.get("image", context.docker_image)
                context.build_number = meta.get("build_number", context.build_number)
                if meta.get("reason") in ("CrashLoopBackOff", "ImagePullBackOff", "OOMKilled"):
                    context.application_logs.append(
                        f"Pod {meta.get('pod_name', '')}: {meta.get('reason', '')}"
                    )

            elif source == "docker":
                context.docker_image = meta.get("image", context.docker_image)
                context.container_id = meta.get("container_id", context.container_id)
                if not context.repository:
                    context.repository = meta.get("repository", "")
                if not context.branch:
                    context.branch = meta.get("branch", "")
                if not context.commit_sha:
                    context.commit_sha = meta.get("commit_sha", "")
                if meta.get("reason") in ("exited_with_error", "oom_killed"):
                    context.application_logs.append(
                        f"Container {meta.get('container_id', '')} exited: {meta.get('reason', '')}"
                    )

            elif source == "prometheus":
                context.cpu_usage = meta.get("cpu_percent", context.cpu_usage)
                context.memory_usage = meta.get("memory_percent", context.memory_usage)
                context.pod_name = meta.get("pod_name", context.pod_name)
                context.namespace = meta.get("namespace", context.namespace)
                context.container_id = meta.get("container_id", context.container_id)
                context.deployment = meta.get("deployment", context.deployment)
                alertname = meta.get("alertname", "")
                if alertname:
                    context.application_logs.append(
                        f"Alert {alertname}: {meta.get('summary', '')}"
                    )

            elif source == "grafana":
                context.deployment = meta.get("deployment", context.deployment)
                context.namespace = meta.get("namespace", context.namespace)
                dashboard_uid = meta.get("dashboard_uid", "")
                if dashboard_uid and not hasattr(context, "_grafana_dashboards"):
                    context._grafana_dashboards = []
                if dashboard_uid:
                    if not hasattr(context, "_grafana_dashboards"):
                        context._grafana_dashboards = []
                    context._grafana_dashboards.append(dashboard_uid)

            elif source == "alertmanager":
                context.pod_name = meta.get("pod_name", context.pod_name)
                context.namespace = meta.get("namespace", context.namespace)
                context.deployment = meta.get("deployment", context.deployment)
                alertname = meta.get("alertname", "")
                status = meta.get("status", "firing")
                if alertname:
                    context.application_logs.append(
                        f"Alert {alertname} [{status}]: {meta.get('summary', '')}"
                    )
                if meta.get("alertname", "").lower() == "nodealert" or "node" in meta.get("alertname", "").lower():
                    context.cpu_usage = meta.get("cpu_usage", context.cpu_usage)
                    context.memory_usage = meta.get("memory_usage", context.memory_usage)

        context.raw_events = target
        logger.info(
            f"Correlated {len(target)} events into context for {context.repository or 'unknown'}"
        )
        return context

    def clear_buffer(self):
        self._event_buffer.clear()

    def get_buffer_size(self) -> int:
        return len(self._event_buffer)
