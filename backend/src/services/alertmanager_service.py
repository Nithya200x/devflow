import datetime
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
        self._seen_fingerprints: set = set()
        self._max_seen = 10000
        self._alert_history: List[Dict[str, Any]] = []
        self._max_history = 500

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
        from utils.environment import make_service_status, get_environment_display
        if not self._base_url:
            logger.info("Alertmanager health: ALERTMANAGER_URL not set, returning NOT_CONFIGURED")
            base = make_service_status(False, "Alertmanager", status_override="not_configured")
            base.update({"connected": False, "latency_ms": 0})
            return base
        try:
            start = time.time()
            resp = requests.get(f"{self._base_url}/api/v2/status", timeout=5)
            elapsed = (time.time() - start) * 1000
            if resp.status_code == 200:
                logger.info("Alertmanager health: connected, environment=%s", get_environment_display())
                base = make_service_status(True, "Alertmanager")
                base.update({"connected": True, "latency_ms": round(elapsed, 2)})
                return base
            logger.info("Alertmanager health: HTTP %s, environment=%s", resp.status_code, get_environment_display())
            base = make_service_status(False, "Alertmanager", error=f"HTTP {resp.status_code}")
            base.update({"connected": False, "latency_ms": round(elapsed, 2)})
            return base
        except requests.RequestException as e:
            logger.info("Alertmanager health: error='%s', environment=%s", e, get_environment_display())
            base = make_service_status(False, "Alertmanager", error=str(e))
            base.update({"connected": False, "latency_ms": 0})
            return base

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
            fingerprint = alert.get("fingerprint", "")
            alertname = labels.get("alertname", "")
            severity = labels.get("severity", "info")

            if status == "firing" and fingerprint:
                if fingerprint in self._seen_fingerprints:
                    logger.debug("Skipping duplicate alert: %s (%s)", alertname, fingerprint)
                    continue
                self._seen_fingerprints.add(fingerprint)
                if len(self._seen_fingerprints) > self._max_seen:
                    self._seen_fingerprints = set(list(self._seen_fingerprints)[-self._max_seen // 2:])

            entry = {
                "fingerprint": fingerprint,
                "status": status,
                "alertname": alertname,
                "severity": severity,
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
            }
            processed.append(entry)

            self._alert_history.append({
                **entry,
                "received_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            })
            if len(self._alert_history) > self._max_history:
                self._alert_history = self._alert_history[-self._max_history:]

        return processed

    def get_alert_history(self, limit: int = 100, offset: int = 0) -> Dict[str, Any]:
        total = len(self._alert_history)
        entries = list(reversed(self._alert_history))
        page = entries[offset:offset + limit]
        return {
            "alerts": page,
            "total": total,
            "limit": limit,
            "offset": offset,
        }

    def get_alert_stats(self) -> Dict[str, Any]:
        total = len(self._alert_history)
        firing = sum(1 for a in self._alert_history if a["status"] == "firing")
        resolved = sum(1 for a in self._alert_history if a["status"] == "resolved")
        by_severity: Dict[str, int] = {}
        by_alertname: Dict[str, int] = {}
        for a in self._alert_history:
            sev = a.get("severity", "unknown")
            by_severity[sev] = by_severity.get(sev, 0) + 1
            name = a.get("alertname", "unknown")
            by_alertname[name] = by_alertname.get(name, 0) + 1
        top_alerts = sorted(by_alertname.items(), key=lambda x: -x[1])[:10]
        return {
            "total_alerts": total,
            "firing": firing,
            "resolved": resolved,
            "by_severity": by_severity,
            "top_alerts": [{"name": k, "count": v} for k, v in top_alerts],
        }

    def get_alert_detail(self, fingerprint: str) -> Optional[Dict[str, Any]]:
        for a in self._alert_history:
            if a["fingerprint"] == fingerprint:
                return a
        return None

    def create_silence(self, matchers: List[Dict[str, str]], duration: str = "1h", comment: str = "", created_by: str = "devflow") -> Optional[Dict[str, Any]]:
        self._ensure_connected()
        if not self._connected or not self._session:
            return None
        try:
            payload = {
                "matchers": matchers,
                "starts_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "ends_at": (datetime.datetime.now(datetime.timezone.utc) + self._parse_duration(duration)).isoformat(),
                "comment": comment or f"Created by {created_by}",
                "created_by": created_by,
            }
            resp = self._session.post(f"{self._base_url}/api/v2/silences", json=payload, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            logger.warning(f"Failed to create silence: {e}")
            return None

    def expire_silence(self, silence_id: str) -> bool:
        self._ensure_connected()
        if not self._connected or not self._session:
            return False
        try:
            resp = self._session.delete(f"{self._base_url}/api/v2/silence/{silence_id}", timeout=10)
            resp.raise_for_status()
            return True
        except requests.RequestException as e:
            logger.warning(f"Failed to expire silence {silence_id}: {e}")
            return False

    def get_notification_config(self) -> Dict[str, Any]:
        receivers = []
        raw_receivers = os.getenv("ALERTMANAGER_RECEIVERS", "")
        if raw_receivers:
            for r in raw_receivers.split(","):
                r = r.strip()
                if r:
                    receivers.append(r)
        return {
            "webhook_url": os.getenv("SLACK_WEBHOOK_URL", "") or "",
            "slack_enabled": bool(os.getenv("SLACK_WEBHOOK_URL")),
            "smtp_enabled": bool(os.getenv("SMTP_HOST") and os.getenv("SMTP_FROM")),
            "smtp_host": os.getenv("SMTP_HOST", ""),
            "smtp_from": os.getenv("SMTP_FROM", ""),
            "receivers": receivers,
            "configured": bool(os.getenv("SLACK_WEBHOOK_URL") or (os.getenv("SMTP_HOST") and os.getenv("SMTP_FROM"))),
        }

    @staticmethod
    def _parse_duration(duration_str: str) -> datetime.timedelta:
        import re
        m = re.match(r"^(\d+)([smhd])$", duration_str.strip())
        if not m:
            return datetime.timedelta(hours=1)
        val = int(m.group(1))
        unit = m.group(2)
        if unit == "s":
            return datetime.timedelta(seconds=val)
        elif unit == "m":
            return datetime.timedelta(minutes=val)
        elif unit == "h":
            return datetime.timedelta(hours=val)
        elif unit == "d":
            return datetime.timedelta(days=val)
        return datetime.timedelta(hours=1)
