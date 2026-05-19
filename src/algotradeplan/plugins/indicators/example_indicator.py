"""Example indicator plugin."""

from __future__ import annotations


class ExampleIndicatorPlugin:
    plugin_id = "example_indicator"

    def compute(self, candles: list[dict[str, float]]) -> dict[str, float]:
        return {"value": float(len(candles))}
