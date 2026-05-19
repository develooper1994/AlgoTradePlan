"""Execution connector plugin returning deterministic simulated fills."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any


class SimulatedFillExecutionConnectorPlugin:
    plugin_id = "simulated_fill_connector"

    def send_order(self, order: dict[str, Any]) -> dict[str, Any]:
        context = order.get("context", {})
        return {
            "status": "filled",
            "symbol": order.get("symbol"),
            "action": order.get("action"),
            "quantity": float(context.get("quantity", 0.0)),
            "price": float(context.get("price", 0.0)),
            "filled_at": datetime.now(UTC).isoformat(),
        }
