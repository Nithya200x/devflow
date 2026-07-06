import logging
import threading
from typing import Any, Dict, List, Optional

from models import DetectorConfig as DetectorConfigDB
from extensions import db

logger = logging.getLogger(__name__)

DEFAULT_TRIGGERS = {
    "high_error_rate": {
        "query": "sum(rate(devflow_http_errors_total[5m])) / sum(rate(devflow_http_requests_total[5m])) * 100 > 5",
        "severity": "critical",
        "title": "High HTTP error rate ({value:.1f}%)",
        "description": "Prometheus detected HTTP error rate of {value:.1f}% over the last 5 minutes, exceeding the 5% threshold.",
        "threshold": 5.0,
    },
    "high_latency": {
        "query": "histogram_quantile(0.95, sum(rate(devflow_http_request_duration_seconds_bucket[5m])) by (le)) > 1.0",
        "severity": "warning",
        "title": "High p95 latency ({value:.1f}s)",
        "description": "Prometheus detected p95 latency of {value:.1f}s over the last 5 minutes, exceeding the 1s threshold.",
        "threshold": 1.0,
    },
    "service_down": {
        "query": "count(devflow_http_requests_total offset 2m) == 0",
        "severity": "critical",
        "title": "Service appears down",
        "description": "Prometheus detected no request metrics in the last 2 minutes. The service may be down or unreachable.",
        "threshold": None,
    },
}


class DetectorConfigManager:
    def __init__(self):
        self._lock = threading.Lock()
        self._config: Dict[str, Dict[str, Any]] = {}
        self._loaded = False

    def _ensure_loaded(self):
        if self._loaded:
            return
        self._loaded = True
        try:
            records = DetectorConfigDB.query.all()
            if not records:
                self._seed_defaults()
                records = DetectorConfigDB.query.all()
            for rec in records:
                self._config[rec.trigger_key] = {
                    "enabled": rec.enabled,
                    "query": rec.promql,
                    "severity": rec.severity,
                    "title": rec.title_template,
                    "description": rec.description_template,
                    "threshold": rec.threshold,
                }
            logger.info("Loaded %d detector trigger configs", len(self._config))
        except Exception:
            logger.exception("Failed to load detector config, using defaults")
            self._config = {}
            for key, cfg in DEFAULT_TRIGGERS.items():
                self._config[key] = {
                    "enabled": True,
                    "query": cfg["query"],
                    "severity": cfg["severity"],
                    "title": cfg["title"],
                    "description": cfg["description"],
                    "threshold": cfg.get("threshold"),
                }

    def _seed_defaults(self):
        for key, cfg in DEFAULT_TRIGGERS.items():
            rec = DetectorConfigDB(
                trigger_key=key,
                enabled=True,
                promql=cfg["query"],
                severity=cfg["severity"],
                title_template=cfg["title"],
                description_template=cfg["description"],
                threshold=cfg.get("threshold"),
            )
            db.session.add(rec)
        db.session.commit()
        logger.info("Seeded default detector config (%d triggers)", len(DEFAULT_TRIGGERS))

    def get_all(self) -> Dict[str, Dict[str, Any]]:
        with self._lock:
            self._ensure_loaded()
            result = {}
            for key, cfg in self._config.items():
                result[key] = dict(cfg)
            return result

    def get(self, trigger_key: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            self._ensure_loaded()
            cfg = self._config.get(trigger_key)
            return dict(cfg) if cfg else None

    def update(self, trigger_key: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        with self._lock:
            self._ensure_loaded()
            if trigger_key not in self._config:
                return None

            allowed = {"enabled", "query", "severity", "title", "description", "threshold"}
            for k, v in updates.items():
                if k in allowed:
                    if k == "enabled":
                        self._config[trigger_key][k] = bool(v)
                    elif k == "threshold":
                        self._config[trigger_key][k] = float(v) if v is not None else None
                    else:
                        self._config[trigger_key][k] = str(v)

            try:
                rec = DetectorConfigDB.query.filter_by(trigger_key=trigger_key).first()
                if rec:
                    mapping = {
                        "enabled": "enabled",
                        "query": "query",
                        "severity": "severity",
                        "title": "title_template",
                        "description": "description_template",
                        "threshold": "threshold",
                    }
                    for k, v in updates.items():
                        col = mapping.get(k)
                        if col:
                            setattr(rec, col, self._config[trigger_key][k])
                    db.session.commit()
            except Exception:
                db.session.rollback()
                logger.exception("Failed to persist detector config update")

            return dict(self._config[trigger_key])

    def get_active_triggers(self) -> Dict[str, Dict[str, Any]]:
        all_config = self.get_all()
        return {k: v for k, v in all_config.items() if v.get("enabled", True)}


detector_config = DetectorConfigManager()
