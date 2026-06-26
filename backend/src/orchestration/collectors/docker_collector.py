from typing import Any, Dict, List

from orchestration.collectors.base_collector import BaseEvidenceCollector


class DockerEvidenceCollector(BaseEvidenceCollector):
    def __init__(self):
        super().__init__(source_name="docker")

    def collect_evidence(self, context: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "source": "docker",
            "status": "not_implemented",
            "message": "Docker evidence collection will be implemented in a future phase.",
        }

    def collect_logs(self, context: Dict[str, Any]) -> List[str]:
        return ["Docker log collection not yet implemented."]

    def collect_metadata(self, context: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "image": context.get("docker_image", ""),
            "container_id": context.get("container_id", ""),
        }

    def collect_metrics(self, context: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "source": "docker",
            "container_count": 0,
            "image_count": 0,
            "status": "not_implemented",
        }
