"""Example execution connector plugin."""

from __future__ import annotations


class ExampleExecutionConnectorPlugin:
    plugin_id = "example_execution_connector"

    def send_order(self, order: dict[str, object]) -> dict[str, object]:
        return {"status": "accepted", "order": order}
