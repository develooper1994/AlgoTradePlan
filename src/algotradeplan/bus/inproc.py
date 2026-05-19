"""In-process pub/sub bus scaffold."""

from __future__ import annotations

from collections.abc import Callable

EventHandler = Callable[[dict[str, object]], None]


class InProcBus:
    def __init__(self) -> None:
        self._handlers: dict[str, list[EventHandler]] = {}

    def subscribe(self, topic: str, handler: EventHandler) -> None:
        self._handlers.setdefault(topic, []).append(handler)

    def publish(self, topic: str, event: dict[str, object]) -> None:
        for handler in self._handlers.get(topic, []):
            handler(event)
