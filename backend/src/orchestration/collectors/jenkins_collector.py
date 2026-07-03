from typing import Any, Dict, List

from orchestration.collectors.base_collector import BaseEvidenceCollector
from services.jenkins_service import JenkinsService, JenkinsError


class JenkinsEvidenceCollector(BaseEvidenceCollector):
    def __init__(self):
        super().__init__(source_name="jenkins")
        self._jenkins = JenkinsService()

    def collect_evidence(self, context: Dict[str, Any]) -> Dict[str, Any]:
        logs = self.collect_logs(context)
        metadata = self.collect_metadata(context)
        metrics = self.collect_metrics(context)
        return {
            "source": "jenkins",
            "logs": logs,
            "metadata": metadata,
            "metrics": metrics,
        }

    def collect_logs(self, context: Dict[str, Any]) -> List[str]:
        build_number = context.get("build_number", "")
        if not build_number:
            return ["No build number provided."]
        try:
            result = self._jenkins.get_console_output(int(build_number))
            text = result.get("console_text", "")
            if result.get("truncated"):
                text += "\n... (truncated)"
            return [text] if text else ["No console output available."]
        except (JenkinsError, ValueError) as e:
            return [f"Failed to fetch console log: {e}"]

    def collect_metadata(self, context: Dict[str, Any]) -> Dict[str, Any]:
        build_number = context.get("build_number", "")
        metadata = {
            "build_number": build_number,
            "repository": context.get("repository", ""),
            "branch": context.get("branch", ""),
            "commit_sha": context.get("commit_sha", ""),
            "triggered_by": context.get("triggered_by", ""),
        }
        if build_number:
            try:
                info = self._jenkins.get_build_info(int(build_number))
                metadata.update({
                    "build_status": info.get("status", "unknown"),
                    "build_result": info.get("result"),
                    "duration_ms": info.get("duration_ms", 0),
                    "duration_seconds": info.get("duration_seconds", 0),
                    "build_url": info.get("url", ""),
                    "display_name": info.get("display_name", ""),
                    "parameters": info.get("parameters", {}),
                })
            except (JenkinsError, ValueError) as e:
                metadata["error"] = str(e)
        return metadata

    def collect_metrics(self, context: Dict[str, Any]) -> Dict[str, Any]:
        build_number = context.get("build_number", "")
        metrics = {
            "source": "jenkins",
            "build_status": "unknown",
        }
        if build_number:
            try:
                info = self._jenkins.get_build_info(int(build_number))
                metrics.update({
                    "build_status": info.get("status", "unknown"),
                    "build_duration_seconds": info.get("duration_seconds", 0),
                    "build_result": info.get("result"),
                    "building": info.get("building", False),
                })
            except (JenkinsError, ValueError) as e:
                metrics["error"] = str(e)
        return metrics
