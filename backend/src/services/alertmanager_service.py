import logging
import os
import time
from typing import Any, Dict, List, Optional
import requests

logger = logging.getLogger(__name__)


class AlertmanagerServiceError(Exception):
    pass


class AlertmanagerService:
    def __init__(self):
        self._base_url = os.getenv("ALERTMANAGER_URL", "").rstrip("/")
        self._connected = False
        self._session: Optional[requests.Session] = None

    def connect(self) -> bool:
        if not self._base_url:
            logger.warning("ALERTMANAGER_URL not set")
            self._connected = False
            return False
        try:
            self._session = requests.Session()
            self._session.headers.update({"Accept": "application/json"})

            resp = self._session.get(f"{self._base_url}/api/v2/status", timeout=10)
            if resp.status_code == 200:
                self._connected = True
                logger.info(f"Alertmanager connected: {self._base_url}")
                return True
            logger.warning(f"Alertmanager status check failed: HTTP {resp.status_code}")
            self._connected = False
            return False
        except requests.RequestException as e:
            self._connected = False
            logger.info("Alertmanager connection failed: %s", e)
            return False

    @property
    def connected(self) -> bool:
        return self._connected

    def _ensure_connected(self):
        if not self._connected or not self._session:
            self.connect()

    def health_check(self) -> Dict[str, Any]:
        if not self._base_url:
            return {"connected": False, "error": "ALERTMANAGER_URL not configured", "latency_ms": 0}
        try:
            start = time.time()
            resp = requests.get(f"{self._base_url}/api/v2/status", timeout=5)
            elapsed = (time.time() - start) * 1000
            if resp.status_code == 200:
                return {"connected": True, "latency_ms": round(elapsed, 2), "error": None}
            return {"connected": False, "latency_ms": round(elapsed, 2), "error": f"HTTP {resp.status_code}"}
        except requests.RequestException as e:
            return {"connected": False, "latency_ms": 0, "error": str(e)}

    def get_alerts(self, silenced: bool = False, inhibited: bool = False) -> List[Dict[str, Any]]:
        self._ensure_connected()
        if not self._connected or not self._session:
            return []
        try:
            params = {}
            if silenced:
                params["silenced"] = "true"
            if inhibited:
                params["inhibited"] = "true"
            resp = self._session.get(f"{self._base_url}/api/v2/alerts", params=params, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            logger.warning(f"Failed to get alerts: {e}")
            return []

    def get_alert_groups(self) -> List[Dict[str, Any]]:
        self._ensure_connected()
        if not self._connected or not self._session:
            return []
        try:
            resp = self._session.get(f"{self._base_url}/api/v2/alerts/groups", timeout=10)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            logger.warning(f"Failed to get alert groups: {e}")
            return []

    def get_silences(self) -> List[Dict[str, Any]]:
        self._ensure_connected()
        if not self._connected or not self._session:
            return []
        try:
            resp = self._session.get(f"{self._base_url}/api/v2/silences", timeout=10)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            logger.warning(f"Failed to get silences: {e}")
            return []

    def process_webhook(self, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        alerts = payload.get("alerts", [])
        processed = []
        for alert in alerts:
            labels = alert.get("labels", {})
            annotations = alert.get("annotations", {})
            status = alert.get("status", "firing")
            processed.append({
                "fingerprint": alert.get("fingerprint", ""),
                "status": status,
                "alertname": labels.get("alertname", ""),
                "severity": labels.get("severity", "info"),
                "instance": labels.get("instance", ""),
                "job": labels.get("job", ""),
                "namespace": labels.get("namespace", ""),
                "pod": labels.get("pod", ""),
                "deployment": labels.get("deployment", ""),
                "container": labels.get("container", ""),
                "summary": annotations.get("summary", ""),
                "description": annotations.get("description", ""),
                "runbook_url": annotations.get("runbook_url", ""),
                "starts_at": alert.get("startsAt", ""),
                "ends_at": alert.get("endsAt", ""),
                "generator_url": alert.get("generatorURL", ""),
            })
        return processed
