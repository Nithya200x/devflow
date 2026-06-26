from typing import Any, Dict, List

from orchestration.collectors.base_collector import BaseEvidenceCollector


class GrafanaEvidenceCollector(BaseEvidenceCollector):
    def __init__(self):
        super().__init__(source_name="grafana")

    def collect_evidence(self, context: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "source": "grafana",
            "status": "not_implemented",
            "message": "Grafana evidence collection will be implemented in a future phase.",
        }

    def collect_logs(self, context: Dict[str, Any]) -> List[str]:
        return ["Grafana log collection not yet implemented."]

    def collect_metadata(self, context: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "dashboard_uid": context.get("dashboard_uid", ""),
            "panel_id": context.get("panel_id", ""),
        }

    def collect_metrics(self, context: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "source": "grafana",
            "alert_count": 0,
            "dashboard_count": 0,
            "status": "not_implemented",
        }
