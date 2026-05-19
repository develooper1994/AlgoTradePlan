"""In-memory event store scaffold for deterministic flows."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EventRecord:
    stream: str
    event_type: str
    payload: dict[str, object]


class InMemoryEventStore:
    def __init__(self) -> None:
        self._events: list[EventRecord] = []

    def append(self, event: EventRecord) -> None:
        self._events.append(event)

    def list_by_stream(self, stream: str) -> list[EventRecord]:
        return [event for event in self._events if event.stream == stream]
