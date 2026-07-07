import json
import logging
import os
import threading
from datetime import datetime, timezone

_request_id = threading.local()


def set_request_id(request_id: str):
    _request_id.value = request_id


def get_request_id() -> str:
    return getattr(_request_id, "value", "")


class StructuredFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "level": record.levelname,
            "service": record.name,
            "message": record.getMessage(),
        }
        request_id = get_request_id()
        if request_id:
            log_entry["request_id"] = request_id
        if record.exc_info and record.exc_info[0]:
            log_entry["error"] = self.formatException(record.exc_info)
        for key in ("deployment_id", "incident_id", "duration", "status"):
            val = getattr(record, key, None)
            if val:
                log_entry[key] = val
        return json.dumps(log_entry, default=str)


def setup_logging():
    handler = logging.StreamHandler()
    if os.getenv("DEVFLOW_JSON_LOG", "").lower() in ("1", "true"):
        handler.setFormatter(StructuredFormatter())
    else:
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
    logging.basicConfig(level=logging.INFO, handlers=[handler])
    return logging.getLogger(__name__)
