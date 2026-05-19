"""Deterministic in-memory metric sink for observability tests."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class MetricEvent:
    name: str
    value: float
    tags: dict[str, str] = field(default_factory=dict)


class InMemoryMetricsSink:
    def __init__(self) -> None:
        self.events: list[MetricEvent] = []

    def record(self, name: str, value: float, **tags: str) -> MetricEvent:
        event = MetricEvent(name=name, value=float(value), tags=dict(tags))
        self.events.append(event)
        return event

    def total(self, name: str) -> float:
        return sum(event.value for event in self.events if event.name == name)
