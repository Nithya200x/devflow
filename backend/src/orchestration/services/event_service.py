import logging
from typing import List, Optional

from orchestration.events.event_types import (
    EventType,
    OrchestrationEvent,
)

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
