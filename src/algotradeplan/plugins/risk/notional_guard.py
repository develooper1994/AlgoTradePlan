"""Risk plugin enforcing max-notional guardrails."""

from __future__ import annotations

from typing import Any


class NotionalGuardRiskPlugin:
    plugin_id = "notional_guard_risk"

    def __init__(self, max_notional: float) -> None:
        self.max_notional = max_notional

    def evaluate(self, order_intent: dict[str, Any]) -> dict[str, Any]:
        context = order_intent.get("context", {})
        price = float(context.get("price", 0.0))
        quantity = float(context.get("quantity", 0.0))
        notional = price * quantity
        if order_intent.get("action") not in {"buy", "sell"}:
            return {"approved": False, "reason": "unsupported_action"}
        if notional <= 0:
            return {"approved": False, "reason": "non_positive_notional"}
        if notional > self.max_notional:
            return {
                "approved": False,
                "reason": "max_notional_exceeded",
                "max_notional": self.max_notional,
                "requested_notional": notional,
            }
        return {"approved": True, "notional": notional}
