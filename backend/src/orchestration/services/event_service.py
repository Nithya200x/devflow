import json
import logging
from typing import List, Optional

from extensions import db
from orchestration.events.event_types import (
    EventType,
    OrchestrationEvent,
)
from orchestration.models.event_store import EventStore

logger = logging.getLogger(__name__)


class EventService:
    MAX_HISTORY_SIZE = 1000

    def __init__(self):
        self._history: List[OrchestrationEvent] = []

    def dispatch(self, event: OrchestrationEvent):
        if len(self._history) >= self.MAX_HISTORY_SIZE:
            self._history.pop(0)
            logger.warning(
                "Event history at capacity (%d), discarding oldest event",
                self.MAX_HISTORY_SIZE,
            )
        self._history.append(event)
        try:
            record = EventStore(
                project_id=event.metadata.get("project_id"),
                event_type=event.event_type.name,
                source=event.source,
                metadata_json=json.dumps(event.metadata, default=str),
                timestamp=event.timestamp,
            )
            db.session.add(record)
            db.session.commit()
        except Exception:
            db.session.rollback()
            logger.exception("Failed to persist event to DB")
        logger.info(f"Event dispatched: {event.event_type.name}")

    def get_history(
        self,
        event_type: EventType = None,
        source: str = None,
        limit: int = 100,
    ) -> List[OrchestrationEvent]:
        results = list(self._history)
        if event_type:
            results = [e for e in results if e.event_type == event_type]
        if source:
            results = [e for e in results if e.source == source]
        return results[-limit:]
