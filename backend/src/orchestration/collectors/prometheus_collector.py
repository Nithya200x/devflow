import logging
from typing import Any, Dict, List

from orchestration.collectors.base_collector import BaseEvidenceCollector
from services.prometheus_service import PrometheusService

logger = logging.getLogger(__name__)


class PrometheusEvidenceCollector(BaseEvidenceCollector):
    def __init__(self):
        super().__init__(source_name="prometheus")
        self._prom = PrometheusService()
        self._prom.connect()

    def collect_evidence(self, context: Dict[str, Any]) -> Dict[str, Any]:
        pod_name = context.get("pod_name", "")
        namespace = context.get("namespace", "")
        container_id = context.get("container_id", "")

        metrics = self.collect_metrics(context)
        alerts = self._prom.list_active_alerts()

        metadata = self.collect_metadata(context)

        return {
            "source": "prometheus",
            "metrics": metrics,
            "alerts": alerts[:20],
            "metadata": metadata,
        }

    def collect_logs(self, context: Dict[str, Any]) -> List[str]:
        return ["Prometheus does not provide log collection"]

    def collect_metadata(self, context: Dict[str, Any]) -> Dict[str, Any]:
        pod_name = context.get("pod_name", "")
        namespace = context.get("namespace", "")
        return {
            "pod_name": pod_name,
            "namespace": namespace,
            "container_id": context.get("container_id", ""),
            "deployment": context.get("deployment", ""),
            "connected": self._prom.connected,
        }

    def collect_metrics(self, context: Dict[str, Any]) -> Dict[str, Any]:
        if not self._prom.connected:
            return {"status": "disconnected", "message": "Prometheus not connected"}

        pod_name = context.get("pod_name", "")
        namespace = context.get("namespace", "")
        container_id = context.get("container_id", "")
        deployment = context.get("deployment", "")

        result = {
            "cpu": self._prom.get_cpu_metrics(namespace, pod_name),
            "memory": self._prom.get_memory_metrics(namespace, pod_name),
            "disk": self._prom.get_disk_metrics(namespace, pod_name),
            "network": self._prom.get_network_metrics(namespace, pod_name),
        }

        if pod_name or namespace:
            result["error_rate"] = self._prom.get_error_rate(namespace, pod_name)
            result["request_rate"] = self._prom.get_request_rate(namespace, pod_name)
            result["latency"] = self._prom.get_latency(namespace, pod_name)

        if deployment and namespace:
            result["deployment"] = self._prom.get_deployment_metrics(namespace, deployment)

        if container_id:
            result["container"] = self._prom.get_container_metrics(container_id)

        return result

    def query(self, query: str) -> Dict[str, Any]:
        return self._prom.query(query)

    def range_query(self, query: str, start: str, end: str, step: str = "15s") -> Dict[str, Any]:
        return self._prom.range_query(query, start, end, step)

    def health_check(self) -> Dict[str, Any]:
        return self._prom.health_check()
