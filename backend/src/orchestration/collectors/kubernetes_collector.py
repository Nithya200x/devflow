import logging
from typing import Any, Dict, List

from orchestration.collectors.base_collector import BaseEvidenceCollector
from services.kubernetes_service import KubernetesService

logger = logging.getLogger(__name__)


class KubernetesEvidenceCollector(BaseEvidenceCollector):
    def __init__(self):
        super().__init__(source_name="kubernetes")
        self._k8s = KubernetesService()
        self._k8s.connect()

    def collect_evidence(self, context: Dict[str, Any]) -> Dict[str, Any]:
        pod_name = context.get("pod_name", "")
        namespace = context.get("namespace", "")
        deployment = context.get("deployment", "")

        metadata = {}
        logs_data = []
        metrics = {}

        if pod_name and namespace:
            pod = self._k8s.get_pod(name=pod_name, namespace=namespace)
            if pod:
                metadata = pod
                logs_data = self.collect_logs(context)
        elif deployment and namespace:
            pods = self._k8s.find_pods_by_deployment(deployment, namespace)
            if pods:
                metadata = {"deployment": deployment, "namespace": namespace, "pods": pods}
                first_pod = pods[0]
                pod_ctx = {"pod_name": first_pod.get("name", ""), "namespace": namespace}
                logs_data = self.collect_logs(pod_ctx)
        elif deployment:
            pods = self._k8s.find_pods_by_deployment(deployment)
            if pods:
                metadata = {"deployment": deployment, "pods": pods}
        elif namespace:
            pods = self._k8s.list_pods(namespace=namespace)
            metadata = {"namespace": namespace, "pods": pods}
        else:
            metrics = self._k8s.get_cluster_metrics()
            pods = self._k8s.list_pods()
            metadata = {"pods": pods[:10]}

        events = self._k8s.list_events(namespace=namespace or None)
        cluster_metrics = self._k8s.get_cluster_metrics()

        return {
            "source": "kubernetes",
            "metadata": metadata,
            "logs": logs_data,
            "events": events[:50],
            "cluster_metrics": cluster_metrics,
            "metrics": cluster_metrics,
        }

    def collect_logs(self, context: Dict[str, Any]) -> List[str]:
        pod_name = context.get("pod_name", "")
        namespace = context.get("namespace", "default")
        if not pod_name:
            return ["No pod name provided"]
        result = self._k8s.get_pod_logs(name=pod_name, namespace=namespace, tail=100)
        return [result.get("logs", "")]

    def collect_metadata(self, context: Dict[str, Any]) -> Dict[str, Any]:
        pod_name = context.get("pod_name", "")
        namespace = context.get("namespace", "default")
        deployment = context.get("deployment", "")

        if pod_name and namespace:
            pod = self._k8s.get_pod(name=pod_name, namespace=namespace)
            if pod:
                return pod

        if deployment and namespace:
            dep = self._k8s.get_deployment(name=deployment, namespace=namespace)
            if dep:
                return dep
            pods = self._k8s.find_pods_by_deployment(deployment, namespace)
            if pods:
                return {"deployment": deployment, "namespace": namespace, "pods": pods}

        return {
            "pod_name": pod_name,
            "namespace": namespace,
            "deployment": deployment,
        }

    def collect_metrics(self, context: Dict[str, Any]) -> Dict[str, Any]:
        return self._k8s.get_cluster_metrics()

    def health_check(self) -> Dict[str, Any]:
        return self._k8s.health_check()

    def list_pods(self, namespace: str = "") -> List[Dict[str, Any]]:
        return self._k8s.list_pods(namespace=namespace)

    def get_pod(self, name: str, namespace: str = "default") -> Dict[str, Any]:
        return self._k8s.get_pod(name=name, namespace=namespace) or {}

    def get_pod_logs(
        self, name: str, namespace: str = "default", tail: int = 100
    ) -> Dict[str, Any]:
        return self._k8s.get_pod_logs(name=name, namespace=namespace, tail=tail)

    def list_deployments(self, namespace: str = "") -> List[Dict[str, Any]]:
        return self._k8s.list_deployments(namespace=namespace)

    def get_cluster_metrics(self) -> Dict[str, Any]:
        return self._k8s.get_cluster_metrics()

    def list_events(self, namespace: str = "") -> List[Dict[str, Any]]:
        return self._k8s.list_events(namespace=namespace)

    def list_nodes(self) -> List[Dict[str, Any]]:
        return self._k8s.list_nodes()
