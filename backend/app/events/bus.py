"""
Asynchronous Pub/Sub Event Bus with WebSocket streaming integration.
"""
import asyncio
import inspect
from typing import Dict, List, Callable, Any, Optional
from app.events.types import BaseEvent, EventType
from app.core.logging import logger


class EventBus:
    def __init__(self):
        self._subscribers: Dict[EventType, List[Callable]] = {
            e_type: [] for e_type in EventType
        }
        self._ws_broadcaster: Optional[Callable[[Dict[str, Any]], Any]] = None
        self._event_history: List[Dict[str, Any]] = []
        self._max_history: int = 500

    def register_ws_broadcaster(self, broadcaster_fn: Callable[[Dict[str, Any]], Any]):
        self._ws_broadcaster = broadcaster_fn

    def subscribe(self, event_type: EventType, handler: Callable):
        if handler not in self._subscribers[event_type]:
            self._subscribers[event_type].append(handler)

    def unsubscribe(self, event_type: EventType, handler: Callable):
        if handler in self._subscribers[event_type]:
            self._subscribers[event_type].remove(handler)

    async def publish(self, event: BaseEvent):
        event_dict = event.model_dump()
        self._event_history.append(event_dict)
        if len(self._event_history) > self._max_history:
            self._event_history.pop(0)

        # Dispatch to local subscribers
        handlers = self._subscribers.get(event.event_type, [])
        for handler in handlers:
            try:
                if inspect.iscoroutinefunction(handler):
                    asyncio.create_task(handler(event))
                else:
                    handler(event)
            except Exception as e:
                logger.error(f"Error in event handler {handler} for {event.event_type}: {e}")

        # Broadcast to connected WebSockets
        if self._ws_broadcaster:
            try:
                if inspect.iscoroutinefunction(self._ws_broadcaster):
                    asyncio.create_task(self._ws_broadcaster(event_dict))
                else:
                    self._ws_broadcaster(event_dict)
            except Exception as e:
                logger.error(f"Error broadcasting event to WebSockets: {e}")

    def get_recent_events(self, limit: int = 50, event_type: Optional[EventType] = None) -> List[Dict[str, Any]]:
        events = self._event_history
        if event_type:
            events = [e for e in events if e.get("event_type") == event_type.value]
        return events[-limit:][::-1]


event_bus = EventBus()
