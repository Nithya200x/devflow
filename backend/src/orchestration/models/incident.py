from __future__ import annotations

import datetime
from typing import Any, Dict, List, Optional

from orchestration.events.event_types import OrchestrationEvent


class OrchestrationIncident:
    def __init__(
        self,
        incident_id: str = "",
        repository: str = "",
        project: str = "",
        environment: str = "",
        branch: str = "",
        commit_sha: str = "",
        build_number: str = "",
        deployment_id: str = "",
        status: str = "open",
        severity: str = "medium",
        category: str = "",
        summary: str = "",
        description: str = "",
        assigned_to: str = "",
        resolution_notes: str = "",
        root_cause: str = "",
        related_incidents: List[str] = None,
        evidence: List[Any] = None,
        timeline: List[Any] = None,
        ai_analysis: str = "",
        confidence_score: float = 0.0,
        suggested_fixes: List[str] = None,
        ai_metadata: Dict[str, Any] = None,
        created_at: datetime.datetime = None,
        resolved_at: datetime.datetime = None,
        possible_causes: List[str] = None,
        preventive_actions: List[str] = None,
        similar_patterns: List[str] = None,
        risk_assessment: str = "",
        estimated_resolution_time: str = "",
        requires_human: bool = False,
        affected_components: List[str] = None,
        prompt_version: str = "",
    ):
        self.incident_id = incident_id
        self.repository = repository
        self.project = project
        self.environment = environment
        self.branch = branch
        self.commit_sha = commit_sha
        self.build_number = build_number
        self.deployment_id = deployment_id
        self.status = status
        self.severity = severity
        self.category = category
        self.summary = summary
        self.description = description
        self.assigned_to = assigned_to
        self.resolution_notes = resolution_notes
        self.root_cause = root_cause
        self.related_incidents = related_incidents or []
        self.evidence = evidence or []
        self.timeline = timeline or []
        self.ai_analysis = ai_analysis
        self.confidence_score = confidence_score
        self.suggested_fixes = suggested_fixes or []
        self.ai_metadata = ai_metadata or {}
        self.created_at = created_at or datetime.datetime.utcnow()
        self.resolved_at = resolved_at
        self.possible_causes = possible_causes or []
        self.preventive_actions = preventive_actions or []
        self.similar_patterns = similar_patterns or []
        self.risk_assessment = risk_assessment
        self.estimated_resolution_time = estimated_resolution_time
        self.requires_human = requires_human
        self.affected_components = affected_components or []
        self.prompt_version = prompt_version

    def to_dict(self) -> Dict[str, Any]:
        return {
            "incident_id": self.incident_id,
            "repository": self.repository,
            "project": self.project,
            "environment": self.environment,
            "branch": self.branch,
            "commit_sha": self.commit_sha,
            "build_number": self.build_number,
            "deployment_id": self.deployment_id,
            "status": self.status,
            "severity": self.severity,
            "category": self.category,
            "summary": self.summary,
            "description": self.description,
            "assigned_to": self.assigned_to,
            "resolution_notes": self.resolution_notes,
            "root_cause": self.root_cause,
            "related_incidents": self.related_incidents,
            "evidence": [e.to_dict() if hasattr(e, "to_dict") else e for e in self.evidence],
            "timeline": [t.to_dict() if hasattr(t, "to_dict") else t for t in self.timeline],
            "ai_analysis": self.ai_analysis,
            "ai_metadata": self.ai_metadata,
            "confidence_score": self.confidence_score,
            "suggested_fixes": self.suggested_fixes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "possible_causes": self.possible_causes,
            "preventive_actions": self.preventive_actions,
            "similar_patterns": self.similar_patterns,
            "risk_assessment": self.risk_assessment,
            "estimated_resolution_time": self.estimated_resolution_time,
            "requires_human": self.requires_human,
            "affected_components": self.affected_components,
            "prompt_version": self.prompt_version,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OrchestrationIncident":
        evidence = [
            Evidence.from_dict(e) if isinstance(e, dict) else e
            for e in data.get("evidence", [])
        ]
        timeline = [
            TimelineEntry.from_dict(t) if isinstance(t, dict) else t
            for t in data.get("timeline", [])
        ]
        return cls(
            incident_id=data.get("incident_id", ""),
            repository=data.get("repository", ""),
            project=data.get("project", ""),
            environment=data.get("environment", ""),
            branch=data.get("branch", ""),
            commit_sha=data.get("commit_sha", ""),
            build_number=data.get("build_number", ""),
            deployment_id=data.get("deployment_id", ""),
            status=data.get("status", "open"),
            severity=data.get("severity", "medium"),
            category=data.get("category", ""),
            summary=data.get("summary", ""),
            description=data.get("description", ""),
            assigned_to=data.get("assigned_to", ""),
            resolution_notes=data.get("resolution_notes", ""),
            root_cause=data.get("root_cause", ""),
            related_incidents=data.get("related_incidents", []),
            evidence=evidence,
            timeline=timeline,
            ai_analysis=data.get("ai_analysis", ""),
            confidence_score=data.get("confidence_score", 0.0),
            suggested_fixes=data.get("suggested_fixes", []),
            ai_metadata=data.get("ai_metadata", {}),
            created_at=datetime.datetime.fromisoformat(data["created_at"])
            if "created_at" in data
            else None,
            resolved_at=datetime.datetime.fromisoformat(data["resolved_at"])
            if data.get("resolved_at")
            else None,
            possible_causes=data.get("possible_causes", []),
            preventive_actions=data.get("preventive_actions", []),
            similar_patterns=data.get("similar_patterns", []),
            risk_assessment=data.get("risk_assessment", ""),
            estimated_resolution_time=data.get("estimated_resolution_time", ""),
            requires_human=data.get("requires_human", False),
            affected_components=data.get("affected_components", []),
            prompt_version=data.get("prompt_version", ""),
        )


class TimelineEntry:
    def __init__(
        self,
        timestamp: datetime.datetime = None,
        event_type: str = "",
        source: str = "",
        description: str = "",
        metadata: Dict[str, Any] = None,
    ):
        self.timestamp = timestamp or datetime.datetime.utcnow()
        self.event_type = event_type
        self.source = source
        self.description = description
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type,
            "source": self.source,
            "description": self.description,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TimelineEntry":
        return cls(
            timestamp=datetime.datetime.fromisoformat(data["timestamp"])
            if "timestamp" in data
            else None,
            event_type=data.get("event_type", ""),
            source=data.get("source", ""),
            description=data.get("description", ""),
            metadata=data.get("metadata", {}),
        )


class Evidence:
    def __init__(
        self,
        evidence_id: str = "",
        source: str = "",
        evidence_type: str = "",
        data: Dict[str, Any] = None,
        collected_at: datetime.datetime = None,
    ):
        self.evidence_id = evidence_id
        self.source = source
        self.evidence_type = evidence_type
        self.data = data or {}
        self.collected_at = collected_at or datetime.datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "source": self.source,
            "evidence_type": self.evidence_type,
            "data": self.data,
            "collected_at": self.collected_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Evidence":
        return cls(
            evidence_id=data.get("evidence_id", ""),
            source=data.get("source", ""),
            evidence_type=data.get("evidence_type", ""),
            data=data.get("data", {}),
            collected_at=datetime.datetime.fromisoformat(data["collected_at"])
            if "collected_at" in data
            else None,
        )


class UnifiedIncidentContext:
    def __init__(
        self,
        repository: str = "",
        branch: str = "",
        commit_sha: str = "",
        build_number: str = "",
        docker_image: str = "",
        container_id: str = "",
        pod_name: str = "",
        namespace: str = "",
        deployment: str = "",
        cpu_usage: float = 0.0,
        memory_usage: float = 0.0,
        recent_deployments: List[str] = None,
        application_logs: List[str] = None,
        raw_events: List[OrchestrationEvent] = None,
    ):
        self.repository = repository
        self.branch = branch
        self.commit_sha = commit_sha
        self.build_number = build_number
        self.docker_image = docker_image
        self.container_id = container_id
        self.pod_name = pod_name
        self.namespace = namespace
        self.deployment = deployment
        self.cpu_usage = cpu_usage
        self.memory_usage = memory_usage
        self.recent_deployments = recent_deployments or []
        self.application_logs = application_logs or []
        self.raw_events = raw_events or []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "repository": self.repository,
            "branch": self.branch,
            "commit_sha": self.commit_sha,
            "build_number": self.build_number,
            "docker_image": self.docker_image,
            "container_id": self.container_id,
            "pod_name": self.pod_name,
            "namespace": self.namespace,
            "deployment": self.deployment,
            "cpu_usage": self.cpu_usage,
            "memory_usage": self.memory_usage,
            "recent_deployments": self.recent_deployments,
            "application_logs": self.application_logs,
        }
