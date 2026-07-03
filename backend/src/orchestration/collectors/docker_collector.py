import logging
from typing import Any, Dict, List

from orchestration.collectors.base_collector import BaseEvidenceCollector
from services.docker_service import DockerService

logger = logging.getLogger(__name__)


class DockerEvidenceCollector(BaseEvidenceCollector):
    def __init__(self):
        super().__init__(source_name="docker")
        self._docker = DockerService()
        self._docker.connect()

    def collect_evidence(self, context: Dict[str, Any]) -> Dict[str, Any]:
        container_id = context.get("container_id", "")
        image = context.get("docker_image", "")

        metadata = {}
        logs_data = []
        metrics = {}

        if container_id:
            meta = self.collect_metadata(context)
            metadata = meta
            logs_data = self.collect_logs(context)
            metrics = self.collect_metrics(context)
        elif image:
            containers = self._docker.find_containers_by_image(image)
            if containers:
                c = containers[0]
                cid = c.get("container_id", "")
                meta = self._docker.get_container(cid) or {}
                metadata = meta
                logs_data = self.collect_logs({"container_id": cid})
                metrics = self._docker.get_container_stats(cid)

        return {
            "source": "docker",
            "metadata": metadata,
            "logs": logs_data,
            "metrics": metrics,
        }

    def collect_logs(self, context: Dict[str, Any]) -> List[str]:
        container_id = context.get("container_id", "")
        if not container_id:
            return ["No container ID provided"]
        result = self._docker.get_container_logs(container_id, tail=100)
        return [result.get("logs", "")]

    def collect_metadata(self, context: Dict[str, Any]) -> Dict[str, Any]:
        container_id = context.get("container_id", "")
        if container_id:
            container = self._docker.get_container(container_id)
            if container:
                return container

        image = context.get("docker_image", "")
        if image:
            containers = self._docker.find_containers_by_image(image)
            if containers:
                return containers[0]

        return {
            "container_id": container_id,
            "container_name": "",
            "status": "unknown",
            "image_name": context.get("docker_image", ""),
        }

    def collect_metrics(self, context: Dict[str, Any]) -> Dict[str, Any]:
        container_id = context.get("container_id", "")
        if container_id:
            stats = self._docker.get_container_stats(container_id)
            if stats:
                return stats

        image = context.get("docker_image", "")
        if image:
            containers = self._docker.find_containers_by_image(image)
            if containers:
                cid = containers[0].get("container_id", "")
                return self._docker.get_container_stats(cid)

        return self._docker.get_all_stats()

    def list_containers(self, show_all: bool = True) -> List[Dict[str, Any]]:
        return self._docker.list_containers(show_all=show_all)

    def get_container(self, container_id: str) -> Dict[str, Any]:
        return self._docker.get_container(container_id) or {}

    def get_container_logs(
        self, container_id: str, tail: int = 100
    ) -> Dict[str, Any]:
        return self._docker.get_container_logs(container_id, tail=tail)

    def get_container_stats(self, container_id: str) -> Dict[str, Any]:
        return self._docker.get_container_stats(container_id)

    def get_all_stats(self) -> Dict[str, Any]:
        return self._docker.get_all_stats()

    def health_check(self) -> Dict[str, Any]:
        return self._docker.health_check()
