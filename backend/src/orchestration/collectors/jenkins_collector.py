from typing import Any, Dict, List

from orchestration.collectors.base_collector import BaseEvidenceCollector


class JenkinsEvidenceCollector(BaseEvidenceCollector):
    def __init__(self):
        super().__init__(source_name="jenkins")

    def collect_evidence(self, context: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "source": "jenkins",
            "status": "not_implemented",
            "message": "Jenkins evidence collection will be implemented in a future phase.",
        }

    def collect_logs(self, context: Dict[str, Any]) -> List[str]:
        return ["Jenkins log collection not yet implemented."]

    def collect_metadata(self, context: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "build_number": context.get("build_number", ""),
            "repository": context.get("repository", ""),
            "branch": context.get("branch", ""),
        }

    def collect_metrics(self, context: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "source": "jenkins",
            "build_duration_seconds": 0,
            "build_status": "unknown",
            "status": "not_implemented",
        }
