"""Example risk plugin."""

from __future__ import annotations


class ExampleRiskPlugin:
    plugin_id = "example_risk"

    def evaluate(self, order_intent: dict[str, object]) -> dict[str, object]:
        return {"approved": True, "order_intent": order_intent}
