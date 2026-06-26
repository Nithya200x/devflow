from typing import Any, Dict, List

from orchestration.collectors.base_collector import BaseEvidenceCollector


class PrometheusEvidenceCollector(BaseEvidenceCollector):
    def __init__(self):
        super().__init__(source_name="prometheus")

    def collect_evidence(self, context: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "source": "prometheus",
            "status": "not_implemented",
            "message": "Prometheus evidence collection will be implemented in a future phase.",
        }

    def collect_logs(self, context: Dict[str, Any]) -> List[str]:
        return ["Prometheus log collection not yet implemented."]

    def collect_metadata(self, context: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "pod_name": context.get("pod_name", ""),
            "namespace": context.get("namespace", ""),
        }

    def collect_metrics(self, context: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "source": "prometheus",
            "cpu_usage_percent": context.get("cpu_usage", 0),
            "memory_usage_percent": context.get("memory_usage", 0),
            "status": "not_implemented",
        }
