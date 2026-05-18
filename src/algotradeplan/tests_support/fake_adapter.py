"""Fake adapter for deterministic tests."""

from __future__ import annotations


class FakeExecutionAdapter:
    def __init__(self) -> None:
        self.sent_orders: list[dict[str, object]] = []

    def send(self, order: dict[str, object]) -> dict[str, object]:
        self.sent_orders.append(order)
        return {"status": "accepted", "order": order}
