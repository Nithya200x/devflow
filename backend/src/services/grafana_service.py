import logging
import os
import time
from typing import Any, Dict, List, Optional
import requests

logger = logging.getLogger(__name__)


class GrafanaServiceError(Exception):
    pass


class GrafanaService:
    def __init__(self):
        self._base_url = os.getenv("GRAFANA_URL", "").rstrip("/")
        self._api_key = os.getenv("GRAFANA_API_KEY", "")
        self._basic_user = os.getenv("GRAFANA_USER")
        self._basic_pass = os.getenv("GRAFANA_PASSWORD")
        self._connected = False
        self._version = ""
        self._session: Optional[requests.Session] = None

    def connect(self) -> bool:
        if not self._base_url:
            logger.warning("GRAFANA_URL not set")
            self._connected = False
            return False
        try:
            self._session = requests.Session()
            if self._api_key:
                self._session.headers.update({"Authorization": f"Bearer {self._api_key}"})
            elif self._basic_user and self._basic_pass:
                from requests.auth import HTTPBasicAuth
                self._session.auth = HTTPBasicAuth(self._basic_user, self._basic_pass)

            resp = self._session.get(f"{self._base_url}/api/health", timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                self._version = data.get("version", "")
                self._connected = True
                logger.info(f"Grafana connected: {self._base_url} v{self._version}")
                return True
            logger.warning(f"Grafana health check failed: HTTP {resp.status_code}")
            self._connected = False
            return False
        except requests.RequestException as e:
            self._connected = False
            logger.warning(f"Grafana connection failed: {e}")
            return False

    @property
    def connected(self) -> bool:
        return self._connected

    @property
    def base_url(self) -> str:
        return self._base_url

    def _ensure_connected(self):
        if not self._connected or not self._session:
            self.connect()

    def health_check(self) -> Dict[str, Any]:
        if not self._base_url:
            return {"connected": False, "error": "GRAFANA_URL not configured", "version": "", "latency_ms": 0}
        try:
            start = time.time()
            auth = None
            headers = {}
            if self._api_key:
                headers["Authorization"] = f"Bearer {self._api_key}"
            elif self._basic_user and self._basic_pass:
                from requests.auth import HTTPBasicAuth
                auth = HTTPBasicAuth(self._basic_user, self._basic_pass)
            resp = requests.get(f"{self._base_url}/api/health", timeout=5, headers=headers, auth=auth)
            elapsed = (time.time() - start) * 1000
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "connected": True,
                    "version": data.get("version", ""),
                    "latency_ms": round(elapsed, 2),
                    "error": None,
                }
            return {"connected": False, "version": "", "latency_ms": round(elapsed, 2), "error": f"HTTP {resp.status_code}"}
        except requests.RequestException as e:
            return {"connected": False, "version": "", "latency_ms": 0, "error": str(e)}

    def list_dashboards(self) -> List[Dict[str, Any]]:
        self._ensure_connected()
        if not self._connected or not self._session:
            return []
        try:
            resp = self._session.get(f"{self._base_url}/api/search", params={"type": "dash-db"}, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            logger.warning(f"Failed to list dashboards: {e}")
            return []

    def get_dashboard(self, uid: str) -> Dict[str, Any]:
        self._ensure_connected()
        if not self._connected or not self._session:
            return {}
        try:
            resp = self._session.get(f"{self._base_url}/api/dashboards/uid/{uid}", timeout=10)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            logger.warning(f"Failed to get dashboard {uid}: {e}")
            return {}

    def get_dashboard_by_name(self, name: str) -> Dict[str, Any]:
        self._ensure_connected()
        if not self._connected or not self._session:
            return {}
        try:
            resp = self._session.get(f"{self._base_url}/api/dashboards/db/{name}", timeout=10)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            logger.warning(f"Failed to get dashboard by name {name}: {e}")
            return {}

    def list_datasources(self) -> List[Dict[str, Any]]:
        self._ensure_connected()
        if not self._connected or not self._session:
            return []
        try:
            resp = self._session.get(f"{self._base_url}/api/datasources", timeout=10)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            logger.warning(f"Failed to list datasources: {e}")
            return []

    def get_dashboard_references(self, uid: str) -> Dict[str, Any]:
        dashboard = self.get_dashboard(uid)
        if not dashboard:
            return {}
        dash = dashboard.get("dashboard", {})
        panels = []
        for panel in dash.get("panels", []):
            panels.append({
                "id": panel.get("id", 0),
                "title": panel.get("title", ""),
                "type": panel.get("type", ""),
                "datasource": panel.get("datasource", ""),
                "grid_pos": {"x": panel.get("gridPos", {}).get("x", 0), "y": panel.get("gridPos", {}).get("y", 0)},
            })
        return {
            "uid": uid,
            "title": dash.get("title", ""),
            "url": f"{self._base_url}/d/{uid}",
            "panels": panels,
            "tags": dash.get("tags", []),
            "timezone": dash.get("timezone", ""),
        }

    def find_dashboard_by_title(self, title: str) -> Optional[Dict[str, Any]]:
        dashboards = self.list_dashboards()
        for d in dashboards:
            if d.get("title", "").lower() == title.lower():
                return self.get_dashboard_references(d.get("uid", ""))
        return None
