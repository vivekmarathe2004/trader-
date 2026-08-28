"""
Tests for Asynchronous Event Bus pub/sub routing.
"""
import pytest
from app.events.bus import event_bus
from app.events.types import SystemEvent, EventType


@pytest.mark.asyncio
async def test_event_bus_publish_and_subscribe():
    received_events = []

    def test_handler(event: SystemEvent):
        received_events.append(event)

    event_bus.subscribe(EventType.SYSTEM_EVENT, test_handler)

    evt = SystemEvent(
        subsystem="TEST_RUNNER",
        status="HEALTHY",
        message="Test event published",
    )

    await event_bus.publish(evt)
    assert len(received_events) == 1
    assert received_events[0].subsystem == "TEST_RUNNER"

    event_bus.unsubscribe(EventType.SYSTEM_EVENT, test_handler)
