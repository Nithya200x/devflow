import logging
from typing import Any, Dict, List

from orchestration.collectors.base_collector import BaseEvidenceCollector
from services.grafana_service import GrafanaService

logger = logging.getLogger(__name__)


class GrafanaEvidenceCollector(BaseEvidenceCollector):
    def __init__(self):
        super().__init__(source_name="grafana")
        self._grafana = GrafanaService()
        self._grafana.connect()

    def collect_evidence(self, context: Dict[str, Any]) -> Dict[str, Any]:
        dashboard_uid = context.get("dashboard_uid", "")
        dashboard_title = context.get("dashboard_title", "")

        dashboard_ref = {}
        if dashboard_uid:
            dashboard_ref = self._grafana.get_dashboard_references(dashboard_uid)
        elif dashboard_title:
            dashboard_ref = self._grafana.find_dashboard_by_title(dashboard_title)

        dashboards = self._grafana.list_dashboards()
        datasources = self._grafana.list_datasources()

        return {
            "source": "grafana",
            "dashboard": dashboard_ref,
            "dashboards": dashboards[:10],
            "datasources": datasources[:5],
            "metadata": self.collect_metadata(context),
        }

    def collect_logs(self, context: Dict[str, Any]) -> List[str]:
        return ["Grafana does not provide log collection"]

    def collect_metadata(self, context: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "dashboard_uid": context.get("dashboard_uid", ""),
            "dashboard_title": context.get("dashboard_title", ""),
            "panel_id": context.get("panel_id", ""),
            "connected": self._grafana.connected,
        }

    def collect_metrics(self, context: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "source": "grafana",
            "dashboards_count": len(self._grafana.list_dashboards()),
            "datasources_count": len(self._grafana.list_datasources()),
        }

    def health_check(self) -> Dict[str, Any]:
        return self._grafana.health_check()

    def list_dashboards(self) -> List[Dict[str, Any]]:
        return self._grafana.list_dashboards()

    def get_dashboard(self, uid: str) -> Dict[str, Any]:
        return self._grafana.get_dashboard_references(uid)

    def list_datasources(self) -> List[Dict[str, Any]]:
        return self._grafana.list_datasources()
