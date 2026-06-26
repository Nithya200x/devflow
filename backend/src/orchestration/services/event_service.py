import logging
from typing import Any, Callable, Dict, List, Optional

from orchestration.events.event_types import (
    EventType,
    OrchestrationEvent,
)

logger = logging.getLogger(__name__)


class EventService:
    def __init__(self):
        self._handlers: Dict[EventType, List[Callable]] = {}
        self._history: List[OrchestrationEvent] = []

    def subscribe(self, event_type: EventType, handler: Callable):
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
        logger.debug(f"Handler subscribed to {event_type.name}")

    def unsubscribe(self, event_type: EventType, handler: Callable):
        handlers = self._handlers.get(event_type, [])
        if handler in handlers:
            handlers.remove(handler)

    def dispatch(self, event: OrchestrationEvent):
        self._history.append(event)
        handlers = self._handlers.get(event.event_type, [])
        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                logger.error(
                    f"Handler failed for {event.event_type.name}: {e}"
                )
        logger.info(f"Event dispatched: {event.event_type.name} ({len(handlers)} handlers)")

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

    def clear_history(self):
        self._history.clear()
