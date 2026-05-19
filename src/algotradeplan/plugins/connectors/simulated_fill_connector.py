"""Execution connector plugin returning deterministic simulated fills."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4


@dataclass(frozen=True)
class SimulatedFillConfig:
    fee_rate: float = 0.001
    slippage_bps: float = 5.0


class SimulatedFillExecutionConnectorPlugin:
    plugin_id = "simulated_fill_connector"

    def __init__(self, config: SimulatedFillConfig | None = None) -> None:
        self.config = config or SimulatedFillConfig()

    def send_order(self, order: dict[str, Any]) -> dict[str, Any]:
        context = order.get("context", {})
        side = str(order.get("action") or context.get("action") or "").lower()
        requested_quantity = float(order.get("quantity", context.get("quantity", 0.0)))
        requested_price = float(order.get("price", context.get("price", 0.0)))
        slippage = requested_price * (self.config.slippage_bps / 10_000.0) if requested_price > 0 else 0.0
        fill_price = requested_price + slippage if side == "buy" else requested_price - slippage
        filled_quantity = requested_quantity
        notional = fill_price * filled_quantity
        fee = notional * self.config.fee_rate
        return {
            "order_id": f"sim-{uuid4().hex[:12]}",
            "status": "filled",
            "symbol": order.get("symbol"),
            "action": side,
            "side": side,
            "requested_quantity": requested_quantity,
            "filled_quantity": filled_quantity,
            "quantity": filled_quantity,
            "requested_price": requested_price,
            "fill_price": fill_price,
            "price": fill_price,
            "fee": fee,
            "slippage": slippage,
            "notional": notional,
            "filled_at": datetime.now(UTC).isoformat(),
        }
