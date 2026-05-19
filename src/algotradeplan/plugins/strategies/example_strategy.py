"""Example strategy plugin."""

from __future__ import annotations


class ExampleStrategyPlugin:
    plugin_id = "example_strategy"

    def generate_signal(self, context: dict[str, object]) -> dict[str, object]:
        return {"action": "hold", "context": context}
