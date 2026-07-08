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
            # ── Build failure rules ──
            {
                "name": "repeated_build_failures",
                "condition": "build_failure_count > 3",
                "severity": SeverityLevel.CRITICAL.value,
                "weight": 5,
            },
            {
                "name": "build_failed",
                "condition": "build_result == 'FAILURE'",
                "severity": SeverityLevel.HIGH.value,
                "weight": 3,
            },
            {
                "name": "build_aborted",
                "condition": "build_result == 'ABORTED'",
                "severity": SeverityLevel.HIGH.value,
                "weight": 2,
            },
            {
                "name": "build_unstable",
                "condition": "build_result == 'UNSTABLE'",
                "severity": SeverityLevel.MEDIUM.value,
                "weight": 1,
            },
            # ── Container rules ──
            {
                "name": "container_crash_loop",
                "condition": "restart_count > 5",
                "severity": SeverityLevel.CRITICAL.value,
                "weight": 5,
            },
            # ── Deployment rules ──
            {
                "name": "deployment_failure",
                "condition": "deployment_status == 'failed'",
                "severity": SeverityLevel.HIGH.value,
                "weight": 4,
            },
            {
                "name": "production_pipeline_failure",
                "condition": "environment == 'production' and build_result == 'FAILURE'",
                "severity": SeverityLevel.CRITICAL.value,
                "weight": 5,
            },
            # ── Resource rules ──
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
            # ── Service health rules ──
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
            # ── Docker rules ──
            {
                "name": "container_oom_killed",
                "condition": "exit_code == 137",
                "severity": SeverityLevel.CRITICAL.value,
                "weight": 12,
            },
            {
                "name": "container_exit_error",
                "condition": "exit_code > 0 and exit_code != 137",
                "severity": SeverityLevel.HIGH.value,
                "weight": 8,
            },
            {
                "name": "container_unhealthy",
                "condition": "reason == 'unhealthy'",
                "severity": SeverityLevel.CRITICAL.value,
                "weight": 12,
            },
            # ── Kubernetes rules ──
            {
                "name": "crash_loop_back_off",
                "condition": "reason == 'CrashLoopBackOff'",
                "severity": SeverityLevel.CRITICAL.value,
                "weight": 12,
            },
            {
                "name": "oom_killed",
                "condition": "reason == 'OOMKilled'",
                "severity": SeverityLevel.CRITICAL.value,
                "weight": 12,
            },
            {
                "name": "node_not_ready",
                "condition": "reason == 'NodeNotReady'",
                "severity": SeverityLevel.CRITICAL.value,
                "weight": 12,
            },
            {
                "name": "deployment_unavailable",
                "condition": "deployment_status == 'unavailable'",
                "severity": SeverityLevel.CRITICAL.value,
                "weight": 12,
            },
            {
                "name": "image_pull_back_off",
                "condition": "reason == 'ImagePullBackOff'",
                "severity": SeverityLevel.HIGH.value,
                "weight": 8,
            },
            {
                "name": "production_pod_failure",
                "condition": "environment == 'production' and reason in ['CrashLoopBackOff', 'OOMKilled', 'NodeNotReady']",
                "severity": SeverityLevel.CRITICAL.value,
                "weight": 12,
            },
            # ── Observability rules ──
            {
                "name": "node_unreachable",
                "condition": "reason in ['NodeNotReady', 'NodeUnreachable', 'NodeDown']",
                "severity": SeverityLevel.CRITICAL.value,
                "weight": 12,
            },
            {
                "name": "application_unavailable",
                "condition": "reason in ['ApplicationDown', 'ServiceUnavailable', 'PodUnavailable']",
                "severity": SeverityLevel.CRITICAL.value,
                "weight": 12,
            },
            {
                "name": "repeated_alert",
                "condition": "alert_count > 5",
                "severity": SeverityLevel.CRITICAL.value,
                "weight": 8,
            },
            {
                "name": "oom_and_high_memory",
                "condition": "reason == 'OOMKilled' and memory_percent > 80",
                "severity": SeverityLevel.CRITICAL.value,
                "weight": 12,
            },
            {
                "name": "crashloop_and_high_cpu",
                "condition": "reason == 'CrashLoopBackOff' and cpu_percent > 80",
                "severity": SeverityLevel.CRITICAL.value,
                "weight": 12,
            },
            {
                "name": "pod_unavailable",
                "condition": "reason == 'PodUnavailable'",
                "severity": SeverityLevel.HIGH.value,
                "weight": 8,
            },
            {
                "name": "container_unhealthy_alert",
                "condition": "reason in ['ContainerUnhealthy', 'Unhealthy']",
                "severity": SeverityLevel.HIGH.value,
                "weight": 8,
            },
            {
                "name": "deployment_unavailable_alert",
                "condition": "reason == 'DeploymentUnavailable'",
                "severity": SeverityLevel.HIGH.value,
                "weight": 8,
            },
            {
                "name": "disk_pressure",
                "condition": "reason in ['DiskPressure', 'DiskUnavailable']",
                "severity": SeverityLevel.CRITICAL.value,
                "weight": 8,
            },
            {
                "name": "network_latency",
                "condition": "reason in ['NetworkLatency', 'HighLatency']",
                "severity": SeverityLevel.HIGH.value,
                "weight": 6,
            },
            {
                "name": "cpu_warning",
                "condition": "cpu_percent > 80 and cpu_percent <= 90",
                "severity": SeverityLevel.MEDIUM.value,
                "weight": 3,
            },
            {
                "name": "memory_warning",
                "condition": "memory_percent > 80 and memory_percent <= 90",
                "severity": SeverityLevel.MEDIUM.value,
                "weight": 3,
            },
            {
                "name": "disk_warning",
                "condition": "disk_percent > 80 and disk_percent <= 90",
                "severity": SeverityLevel.MEDIUM.value,
                "weight": 2,
            },
            {
                "name": "informational_alert",
                "condition": "severity == 'info' or severity == 'warning'",
                "severity": SeverityLevel.LOW.value,
                "weight": 1,
            },
            {
                "name": "production_alert",
                "condition": "environment == 'production' and alertname != ''",
                "severity": SeverityLevel.CRITICAL.value,
                "weight": 8,
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
            if self._safe_eval(rule["condition"], event_signals):
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
            result["environment"] = context.namespace or ""
            result["build_number"] = context.build_number or ""

        if signals:
            result.update(signals)

        if context and context.raw_events:
            for evt in context.raw_events:
                meta = evt.metadata
                if evt.source == "docker":
                    result["exit_code"] = meta.get("exit_code", result.get("exit_code", 0))
                    result["reason"] = meta.get("reason", result.get("reason", ""))
                    result["container_id"] = meta.get("container_id", result.get("container_id", ""))
                elif evt.source == "kubernetes":
                    result["reason"] = meta.get("reason", result.get("reason", ""))
                    result["restart_count"] = meta.get("restart_count", result.get("restart_count", 0))
                    result["pod_name"] = meta.get("pod_name", result.get("pod_name", ""))
                    result["namespace"] = meta.get("namespace", result.get("namespace", ""))
                    result["environment"] = meta.get("environment",
                                                     meta.get("namespace",
                                                              result.get("environment", "")))
                    result["deployment_status"] = "unavailable" if meta.get("reason") in ("CrashLoopBackOff", "ImagePullBackOff") else result.get("deployment_status", "")
                elif evt.source == "prometheus":
                    result["cpu_percent"] = meta.get("cpu_percent", result.get("cpu_percent", 0))
                    result["memory_percent"] = meta.get("memory_percent", result.get("memory_percent", 0))
                    result["pod_name"] = meta.get("pod_name", result.get("pod_name", ""))
                    result["namespace"] = meta.get("namespace", result.get("namespace", ""))
                elif evt.source == "alertmanager":
                    result["reason"] = meta.get("reason", result.get("reason", ""))
                    result["alertname"] = meta.get("alertname", result.get("alertname", ""))
                    result["severity"] = meta.get("severity", result.get("severity", "info"))
                    result["namespace"] = meta.get("namespace", result.get("namespace", ""))
                    result["pod_name"] = meta.get("pod_name", result.get("pod_name", ""))
                    result["environment"] = meta.get("environment",
                                                     meta.get("namespace",
                                                              result.get("environment", "")))
                    result["container_id"] = meta.get("container_id", result.get("container_id", ""))

        if event_types:
            result["health_check_failed"] = sum(
                1 for e in event_types if e == EventType.HEALTH_CHECK_FAILED
            )
            result["restart_count"] = sum(
                1 for e in event_types if e == EventType.POD_RESTARTED
            )
            result["alert_count"] = sum(
                1 for e in event_types if e in (
                    EventType.HIGH_CPU_DETECTED,
                    EventType.HIGH_MEMORY_DETECTED,
                    EventType.HEALTH_CHECK_FAILED,
                )
            )

        return result

    @staticmethod
    def _safe_eval(condition: str, signals: Dict[str, Any]) -> bool:
        import ast
        ALLOWED_NODE_TYPES = {
            ast.Expression, ast.BoolOp, ast.Compare,
            ast.Name, ast.Constant, ast.List, ast.Tuple,
            ast.And, ast.Or, ast.Not, ast.UnaryOp, ast.USub,
            ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE,
            ast.In, ast.NotIn, ast.Load,
        }
        try:
            tree = ast.parse(condition.strip(), mode="eval")
            for node in ast.walk(tree):
                if type(node) not in ALLOWED_NODE_TYPES:
                    return False
        except SyntaxError:
            return False
        allowed_names = {
            "True": True, "False": False, "None": None,
            **{k: v for k, v in signals.items() if isinstance(v, (int, float, str, bool))},
        }
        allowed_names["alertname"] = str(allowed_names.get("alertname", ""))
        allowed_names["alert_count"] = int(allowed_names.get("alert_count", 0))
        try:
            code = compile(tree, "<severity_rule>", "eval")
            result = eval(code, {"__builtins__": {}}, allowed_names)
            return bool(result)
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
