import datetime
from enum import Enum, auto

from utils.time import to_iso


class EventType(Enum):
    REPOSITORY_CONNECTED = auto()
    DEPLOYMENT_REQUESTED = auto()
    DEPLOYMENT_STARTED = auto()
    DEPLOYMENT_SUCCEEDED = auto()
    DEPLOYMENT_FAILED = auto()
    CONTAINER_CRASHED = auto()
    POD_RESTARTED = auto()
    HIGH_CPU_DETECTED = auto()
    HIGH_MEMORY_DETECTED = auto()
    HEALTH_CHECK_FAILED = auto()
    INCIDENT_CREATED = auto()
    INCIDENT_RESOLVED = auto()


class OrchestrationEvent:
    def __init__(
        self,
        event_type: EventType,
        source: str,
        metadata: dict = None,
        timestamp: datetime.datetime = None,
    ):
        self.event_type = event_type
        self.source = source
        self.metadata = metadata or {}
        self.timestamp = timestamp or datetime.datetime.now(datetime.timezone.utc)

    def to_dict(self):
        return {
            "event_type": self.event_type.name,
            "source": self.source,
            "metadata": self.metadata,
            "timestamp": to_iso(self.timestamp),
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            event_type=EventType[data["event_type"]],
            source=data["source"],
            metadata=data.get("metadata", {}),
            timestamp=datetime.datetime.fromisoformat(data["timestamp"])
            if "timestamp" in data
            else None,
        )


class RepositoryConnected(OrchestrationEvent):
    def __init__(self, repository: str, branch: str = "main", metadata: dict = None):
        super().__init__(
            event_type=EventType.REPOSITORY_CONNECTED,
            source="github",
            metadata={"repository": repository, "branch": branch, **(metadata or {})},
        )


class DeploymentRequested(OrchestrationEvent):
    def __init__(
        self, repository: str, branch: str, environment: str, metadata: dict = None
    ):
        super().__init__(
            event_type=EventType.DEPLOYMENT_REQUESTED,
            source="github",
            metadata={
                "repository": repository,
                "branch": branch,
                "environment": environment,
                **(metadata or {}),
            },
        )


class DeploymentStarted(OrchestrationEvent):
    def __init__(
        self,
        deployment_id: str,
        repository: str,
        environment: str,
        image: str = "",
        metadata: dict = None,
    ):
        super().__init__(
            event_type=EventType.DEPLOYMENT_STARTED,
            source="kubernetes",
            metadata={
                "deployment_id": deployment_id,
                "repository": repository,
                "environment": environment,
                "image": image,
                **(metadata or {}),
            },
        )


class DeploymentSucceeded(OrchestrationEvent):
    def __init__(self, deployment_id: str, metadata: dict = None):
        super().__init__(
            event_type=EventType.DEPLOYMENT_SUCCEEDED,
            source="kubernetes",
            metadata={"deployment_id": deployment_id, **(metadata or {})},
        )


class DeploymentFailed(OrchestrationEvent):
    def __init__(
        self, deployment_id: str, reason: str = "", metadata: dict = None
    ):
        super().__init__(
            event_type=EventType.DEPLOYMENT_FAILED,
            source="kubernetes",
            metadata={
                "deployment_id": deployment_id,
                "reason": reason,
                **(metadata or {}),
            },
        )


class ContainerCrashed(OrchestrationEvent):
    def __init__(
        self,
        container_id: str,
        pod_name: str,
        namespace: str,
        exit_code: int = 0,
        metadata: dict = None,
    ):
        super().__init__(
            event_type=EventType.CONTAINER_CRASHED,
            source="kubernetes",
            metadata={
                "container_id": container_id,
                "pod_name": pod_name,
                "namespace": namespace,
                "exit_code": exit_code,
                **(metadata or {}),
            },
        )


class PodRestarted(OrchestrationEvent):
    def __init__(
        self,
        pod_name: str,
        namespace: str,
        restart_count: int = 0,
        metadata: dict = None,
    ):
        super().__init__(
            event_type=EventType.POD_RESTARTED,
            source="kubernetes",
            metadata={
                "pod_name": pod_name,
                "namespace": namespace,
                "restart_count": restart_count,
                **(metadata or {}),
            },
        )


class HighCPUDetected(OrchestrationEvent):
    def __init__(
        self,
        pod_name: str,
        namespace: str,
        cpu_percent: float = 0.0,
        threshold: float = 80.0,
        metadata: dict = None,
    ):
        super().__init__(
            event_type=EventType.HIGH_CPU_DETECTED,
            source="prometheus",
            metadata={
                "pod_name": pod_name,
                "namespace": namespace,
                "cpu_percent": cpu_percent,
                "threshold": threshold,
                **(metadata or {}),
            },
        )


class HighMemoryDetected(OrchestrationEvent):
    def __init__(
        self,
        pod_name: str,
        namespace: str,
        memory_percent: float = 0.0,
        threshold: float = 80.0,
        metadata: dict = None,
    ):
        super().__init__(
            event_type=EventType.HIGH_MEMORY_DETECTED,
            source="prometheus",
            metadata={
                "pod_name": pod_name,
                "namespace": namespace,
                "memory_percent": memory_percent,
                "threshold": threshold,
                **(metadata or {}),
            },
        )


class HealthCheckFailed(OrchestrationEvent):
    def __init__(
        self,
        pod_name: str,
        namespace: str,
        check_type: str = "liveness",
        reason: str = "",
        metadata: dict = None,
    ):
        super().__init__(
            event_type=EventType.HEALTH_CHECK_FAILED,
            source="kubernetes",
            metadata={
                "pod_name": pod_name,
                "namespace": namespace,
                "check_type": check_type,
                "reason": reason,
                **(metadata or {}),
            },
        )


class IncidentCreated(OrchestrationEvent):
    def __init__(self, incident_id: str, summary: str, severity: str, metadata: dict = None):
        super().__init__(
            event_type=EventType.INCIDENT_CREATED,
            source="orchestration",
            metadata={
                "incident_id": incident_id,
                "summary": summary,
                "severity": severity,
                **(metadata or {}),
            },
        )


class IncidentResolved(OrchestrationEvent):
    def __init__(
        self, incident_id: str, resolution_notes: str = "", metadata: dict = None
    ):
        super().__init__(
            event_type=EventType.INCIDENT_RESOLVED,
            source="orchestration",
            metadata={
                "incident_id": incident_id,
                "resolution_notes": resolution_notes,
                **(metadata or {}),
            },
        )


class ContainerExited(OrchestrationEvent):
    def __init__(
        self,
        container_id: str = "",
        container_name: str = "",
        image: str = "",
        exit_code: int = 0,
        reason: str = "",
        metadata: dict = None,
    ):
        super().__init__(
            event_type=EventType.CONTAINER_CRASHED,
            source="docker",
            metadata={
                "container_id": container_id,
                "container_name": container_name,
                "image": image,
                "exit_code": exit_code,
                "reason": reason or "exited_with_error",
                **(metadata or {}),
            },
        )


class ContainerUnhealthy(OrchestrationEvent):
    def __init__(
        self,
        container_id: str = "",
        container_name: str = "",
        image: str = "",
        metadata: dict = None,
    ):
        super().__init__(
            event_type=EventType.HEALTH_CHECK_FAILED,
            source="docker",
            metadata={
                "container_id": container_id,
                "container_name": container_name,
                "image": image,
                "check_type": "container_health",
                "reason": "unhealthy",
                **(metadata or {}),
            },
        )


class ContainerOOMKilled(OrchestrationEvent):
    def __init__(
        self,
        container_id: str = "",
        container_name: str = "",
        image: str = "",
        metadata: dict = None,
    ):
        super().__init__(
            event_type=EventType.CONTAINER_CRASHED,
            source="docker",
            metadata={
                "container_id": container_id,
                "container_name": container_name,
                "image": image,
                "exit_code": 137,
                "reason": "oom_killed",
                **(metadata or {}),
            },
        )


class CrashLoopBackOff(OrchestrationEvent):
    def __init__(
        self,
        pod_name: str = "",
        namespace: str = "",
        container_name: str = "",
        restart_count: int = 0,
        metadata: dict = None,
    ):
        super().__init__(
            event_type=EventType.CONTAINER_CRASHED,
            source="kubernetes",
            metadata={
                "pod_name": pod_name,
                "namespace": namespace,
                "container_name": container_name,
                "restart_count": restart_count,
                "reason": "CrashLoopBackOff",
                **(metadata or {}),
            },
        )


class ImagePullBackOff(OrchestrationEvent):
    def __init__(
        self,
        pod_name: str = "",
        namespace: str = "",
        image: str = "",
        metadata: dict = None,
    ):
        super().__init__(
            event_type=EventType.DEPLOYMENT_FAILED,
            source="kubernetes",
            metadata={
                "pod_name": pod_name,
                "namespace": namespace,
                "image": image,
                "reason": "ImagePullBackOff",
                **(metadata or {}),
            },
        )


class FailedScheduling(OrchestrationEvent):
    def __init__(
        self,
        pod_name: str = "",
        namespace: str = "",
        reason: str = "",
        metadata: dict = None,
    ):
        super().__init__(
            event_type=EventType.HEALTH_CHECK_FAILED,
            source="kubernetes",
            metadata={
                "pod_name": pod_name,
                "namespace": namespace,
                "reason": reason or "FailedScheduling",
                "check_type": "scheduling",
                **(metadata or {}),
            },
        )


class NodeNotReady(OrchestrationEvent):
    def __init__(
        self,
        node_name: str = "",
        reason: str = "",
        metadata: dict = None,
    ):
        super().__init__(
            event_type=EventType.HEALTH_CHECK_FAILED,
            source="kubernetes",
            metadata={
                "node_name": node_name,
                "reason": reason or "NodeNotReady",
                "check_type": "node_health",
                **(metadata or {}),
            },
        )
