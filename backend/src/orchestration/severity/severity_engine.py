import logging
from enum import Enum
from typing import Any, Dict, List, Optional

from orchestration.events.event_types import EventType
from orchestration.models.incident import UnifiedIncidentContext

logger = logging.getLogger(__name__)


class SeverityLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

    @classmethod
    def values(cls) -> List[str]:
        return [s.value for s in cls]


class SeverityEngine:
    def __init__(self):
        self._rules: List[Dict[str, Any]] = []

    def add_rule(self, name: str, condition: str, severity: str, weight: int = 1):
        self._rules.append(
            {
                "name": name,
                "condition": condition,
                "severity": severity,
                "weight": weight,
            }
        )

    def load_default_rules(self):
        self._rules = [
            {
                "name": "repeated_build_failures",
                "condition": "build_failure_count > 3",
                "severity": SeverityLevel.HIGH.value,
                "weight": 3,
            },
            {
                "name": "container_crash_loop",
                "condition": "restart_count > 5",
                "severity": SeverityLevel.CRITICAL.value,
                "weight": 5,
            },
            {
                "name": "deployment_failure",
                "condition": "deployment_status == failed",
                "severity": SeverityLevel.HIGH.value,
                "weight": 4,
            },
            {
                "name": "high_cpu",
                "condition": "cpu_percent > 90",
                "severity": SeverityLevel.HIGH.value,
                "weight": 2,
            },
            {
                "name": "high_memory",
                "condition": "memory_percent > 90",
                "severity": SeverityLevel.HIGH.value,
                "weight": 2,
            },
            {
                "name": "service_unavailable",
                "condition": "health_check_failed > 2",
                "severity": SeverityLevel.CRITICAL.value,
                "weight": 5,
            },
            {
                "name": "multiple_pod_failures",
                "condition": "failed_pods > 3",
                "severity": SeverityLevel.CRITICAL.value,
                "weight": 4,
            },
        ]

    def calculate_severity(
        self,
        context: UnifiedIncidentContext = None,
        event_types: List[EventType] = None,
        signals: Dict[str, Any] = None,
    ) -> str:
        if not self._rules:
            self.load_default_rules()

        score = 0
        matched_rules = []

        event_signals = self._extract_signals(context, event_types, signals)

        for rule in self._rules:
            if self._evaluate_condition(rule["condition"], event_signals):
                score += rule["weight"]
                matched_rules.append(rule["name"])
                logger.debug(f"Severity rule matched: {rule['name']} (+{rule['weight']})")

        return self._map_score_to_severity(score)

    def _extract_signals(
        self,
        context: Optional[UnifiedIncidentContext],
        event_types: Optional[List[EventType]],
        signals: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        result = {}

        if context:
            result["cpu_percent"] = context.cpu_usage
            result["memory_percent"] = context.memory_usage
            result["deployment_status"] = "failed" if context.deployment else "unknown"

        if signals:
            result.update(signals)

        if event_types:
            result["build_failure_count"] = sum(
                1 for e in event_types if e == EventType.BUILD_FAILED
            )
            result["health_check_failed"] = sum(
                1 for e in event_types if e == EventType.HEALTH_CHECK_FAILED
            )
            result["restart_count"] = sum(
                1 for e in event_types if e == EventType.POD_RESTARTED
            )

        return result

    def _evaluate_condition(self, condition: str, signals: Dict[str, Any]) -> bool:
        try:
            return bool(eval(condition, {"__builtins__": {}}, signals))
        except Exception:
            return False

    def _map_score_to_severity(self, score: int) -> str:
        if score >= 12:
            return SeverityLevel.CRITICAL.value
        elif score >= 8:
            return SeverityLevel.HIGH.value
        elif score >= 4:
            return SeverityLevel.MEDIUM.value
        else:
            return SeverityLevel.LOW.value

    def list_rules(self) -> List[Dict[str, Any]]:
        return list(self._rules)

    def clear_rules(self):
        self._rules.clear()
