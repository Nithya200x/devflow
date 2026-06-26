from typing import Any, Dict, List

from orchestration.collectors.base_collector import BaseEvidenceCollector


class GitHubEvidenceCollector(BaseEvidenceCollector):
    def __init__(self):
        super().__init__(source_name="github")

    def collect_evidence(self, context: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "source": "github",
            "status": "not_implemented",
            "message": "GitHub evidence collection will be implemented in a future phase.",
        }

    def collect_logs(self, context: Dict[str, Any]) -> List[str]:
        return ["GitHub log collection not yet implemented."]

    def collect_metadata(self, context: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "repository": context.get("repository", ""),
            "branch": context.get("branch", ""),
            "commit_sha": context.get("commit_sha", ""),
        }

    def collect_metrics(self, context: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "source": "github",
            "commits_last_24h": 0,
            "open_pulls": 0,
            "status": "not_implemented",
        }
