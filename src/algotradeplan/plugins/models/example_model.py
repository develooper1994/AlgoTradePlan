"""Example model plugin."""

from __future__ import annotations


class ExampleModelPlugin:
    plugin_id = "example_model"

    def predict(self, features: dict[str, object]) -> dict[str, object]:
        return {"score": 0.0, "features": features}
