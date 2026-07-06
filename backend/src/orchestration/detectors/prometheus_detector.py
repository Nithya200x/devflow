import logging
import threading
import time
from datetime import datetime, timezone

from services.prometheus_service import prometheus_service

logger = logging.getLogger(__name__)

TRIGGER_CONFIG = {
    "high_error_rate": {
        "query": "sum(rate(devflow_http_errors_total[5m])) / sum(rate(devflow_http_requests_total[5m])) * 100 > 5",
        "severity": "critical",
        "title": "High HTTP error rate ({value:.1f}%)",
        "description": "Prometheus detected HTTP error rate of {value:.1f}% over the last 5 minutes, exceeding the 5% threshold.",
    },
    "high_latency": {
        "query": "histogram_quantile(0.95, sum(rate(devflow_http_request_duration_seconds_bucket[5m])) by (le)) > 1.0",
        "severity": "warning",
        "title": "High p95 latency ({value:.1f}s)",
        "description": "Prometheus detected p95 latency of {value:.1f}s over the last 5 minutes, exceeding the 1s threshold.",
    },
    "service_down": {
        "query": 'count(devflow_http_requests_total offset 2m) == 0',
        "severity": "critical",
        "title": "Service appears down",
        "description": "Prometheus detected no request metrics in the last 2 minutes. The service may be down or unreachable.",
    },
}


def _extract_value(result):
    import math
    try:
        v = float(result["data"]["result"][0]["value"][1])
        return v if math.isfinite(v) else 0.0
    except (IndexError, ValueError, TypeError, KeyError):
        return -1.0


class PrometheusIncidentDetector:
    def __init__(self, interval=30):
        self._interval = interval
        self._thread = None
        self._stop = threading.Event()

    def start(self):
        if self._thread and self._thread.is_alive():
            logger.warning("Detector already running")
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, daemon=True, name="prom-detector")
        self._thread.start()
        logger.info("Prometheus incident detector started (interval=%ds)", self._interval)

    def stop(self):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("Prometheus incident detector stopped")

    def _run(self):
        time.sleep(5)
        logger.info("Prometheus detector background loop started")

        while not self._stop.is_set():
            try:
                self._check_triggers()
            except Exception:
                logger.exception("Prometheus detector check failed")
            self._stop.wait(self._interval)

    def _check_triggers(self):
        ps = prometheus_service
        if not ps._base_url:
            return
        ps._ensure_connected()
        if not ps.connected:
            logger.debug("Prometheus not connected, skipping detector check")
            return

        for trigger_key, config in TRIGGER_CONFIG.items():
            if self._stop.is_set():
                break
            try:
                result = ps.instant_query(config["query"])
                triggered = (
                    result.get("status") == "success"
                    and len(result.get("data", {}).get("result", [])) > 0
                )
                if not triggered:
                    continue

                value = _extract_value(result)
                title = config["title"].format(value=value)
                description = config["description"].format(value=value)

                if self._has_open_incident(trigger_key):
                    logger.debug("Open incident exists for %s, skipping", trigger_key)
                    continue

                self._create_incident(trigger_key, title, description, config["severity"])
            except Exception:
                logger.exception("Error checking trigger %s", trigger_key)

    def _has_open_incident(self, trigger_key):
        source_tag = f"prometheus_{trigger_key}"
        try:
            from models import Incident
            existing = Incident.query.filter(
                Incident.source == source_tag,
                Incident.status == "open",
            ).first()
            return existing is not None
        except Exception:
            logger.exception("Error checking for existing incident")
            return True

    def _create_incident(self, trigger_key, title, description, severity):
        source_tag = f"prometheus_{trigger_key}"
        try:
            from orchestration.services.orchestration_service import get_orchestrator
            from orchestration.ai.service import trigger_ai_analysis

            svc = get_orchestrator()
            incident = svc.incident_service.create_incident(
                summary=title,
                severity=severity,
                category=source_tag,
                description=description,
            )

            svc.incident_service.add_timeline_event(
                incident.incident_id,
                "prometheus_alert",
                "prometheus_detector",
                f"Trigger: {title}",
            )

            try:
                trigger_ai_analysis(incident.incident_id)
            except Exception:
                logger.exception("Failed to trigger AI analysis for %s", incident.incident_id)

            logger.info(
                "Created incident %s (%s): %s",
                incident.incident_id, severity, title,
            )
        except Exception:
            logger.exception("Failed to create incident for %s", trigger_key)
