import logging
import threading
import time
from datetime import datetime, timezone

from services.prometheus_service import prometheus_service
from orchestration.detectors.detector_config import detector_config, DEFAULT_TRIGGERS

logger = logging.getLogger(__name__)

# Kept for backward compatibility in tests
TRIGGER_CONFIG = dict(DEFAULT_TRIGGERS)


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
        self._app = None
        self._lock = threading.Lock()
        self._started = False

    def start(self, app=None):
        with self._lock:
            if self._started:
                logger.warning("Detector already started")
                return
            self._started = True

        if app is None:
            app = self._find_app()
        self._app = app
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, daemon=True, name="prom-detector")
        self._thread.start()
        logger.info("Prometheus incident detector started (interval=%ds)", self._interval)

    def stop(self):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=5)
        self._started = False
        logger.info("Prometheus incident detector stopped")

    @staticmethod
    def _find_app():
        try:
            from flask import current_app
            return current_app._get_current_object()
        except Exception:
            from app import app as _app
            return _app

    def _run(self):
        time.sleep(5)
        logger.info("Prometheus detector background loop started")

        with self._app.app_context():
            self._run_loop()

    def _run_loop(self):
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

        configs = detector_config.get_active_triggers()

        for trigger_key, config in configs.items():
            if self._stop.is_set():
                break
            try:
                result = ps.instant_query(config["query"])
                triggered = (
                    result.get("status") == "success"
                    and len(result.get("data", {}).get("result", [])) > 0
                )

                open_incident = self._find_open_incident(trigger_key)

                if triggered and not open_incident:
                    value = _extract_value(result)
                    title = config["title"].format(value=value)
                    description = config["description"].format(value=value)
                    self._create_incident(trigger_key, title, description, config["severity"])

                elif not triggered and open_incident:
                    self._resolve_incident(open_incident, trigger_key)

            except Exception:
                logger.exception("Error checking trigger %s", trigger_key)

    def _find_open_incident(self, trigger_key):
        import flask
        logger.debug(
            "has_app_context in _find_open_incident: %s (thread=%s)",
            flask.has_app_context(), threading.current_thread().name,
        )
        source_tag = f"prometheus_{trigger_key}"
        try:
            from models import Incident
            existing = Incident.query.filter(
                Incident.source == source_tag,
                Incident.status == "open",
            ).first()
            return existing
        except Exception:
            logger.exception("Error finding incident for %s", trigger_key)
            return None

    def _has_open_incident(self, trigger_key):
        return self._find_open_incident(trigger_key) is not None

    def _resolve_incident(self, incident, trigger_key):
        import flask
        logger.debug(
            "has_app_context in _resolve_incident: %s (thread=%s)",
            flask.has_app_context(), threading.current_thread().name,
        )
        try:
            from orchestration.services.orchestration_service import get_orchestrator

            reason = f"Metrics returned to normal for {trigger_key.replace('_', ' ')}"

            svc = get_orchestrator()
            orchestration_incident = svc.incident_service.get_incident(incident.incident_id)
            if orchestration_incident:
                svc.incident_service.resolve_incident(
                    incident.incident_id,
                    resolution_notes=reason,
                )
                svc.incident_service.add_timeline_event(
                    incident.incident_id,
                    "auto_resolved",
                    "prometheus_detector",
                    reason,
                )

            incident.resolved_at = datetime.now(timezone.utc)
            incident.status = "resolved"
            incident.resolution_reason = reason
            from extensions import db
            db.session.commit()

            logger.info(
                "Auto-resolved incident %s (%s): %s",
                incident.incident_id, trigger_key, reason,
            )
        except Exception:
            logger.exception("Failed to auto-resolve incident for %s", trigger_key)

    def _create_incident(self, trigger_key, title, description, severity):
        import flask
        logger.debug(
            "has_app_context in _create_incident: %s (thread=%s)",
            flask.has_app_context(), threading.current_thread().name,
        )
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
