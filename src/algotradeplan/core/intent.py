"""Intent model: structured signal-to-execution handoff.

The Intent represents a *desired* trade that has been validated by strategy
logic. It flows through: Signal → Intent → Risk → Execution → Portfolio.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass(frozen=True)
class TradeIntent:
    symbol: str
    side: str                     # "buy" | "sell"
    quantity: float
    order_type: str               # "market" | "limit"
    price: float                  # limit price or last known price for market
    strategy_id: str
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_structured_order_intent(self) -> "OrderIntent":
        return OrderIntent(
            symbol=self.symbol,
            action=self.side,
            quantity=self.quantity,
            price=self.price,
            order_type=self.order_type,
            strategy_id=self.strategy_id,
            metadata=dict(self.metadata),
        )

    def to_order_intent(self) -> dict[str, Any]:
        """Convert to the order_intent dict expected by risk/execution plugins."""
        return self.to_structured_order_intent().to_dict()

    def to_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "side": self.side,
            "quantity": self.quantity,
            "order_type": self.order_type,
            "price": self.price,
            "strategy_id": self.strategy_id,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class OrderIntent:
    symbol: str
    action: str
    quantity: float
    price: float
    order_type: str = "market"
    strategy_id: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    @classmethod
    def from_trade_intent(
        cls,
        intent: TradeIntent,
        *,
        metadata: dict[str, Any] | None = None,
    ) -> "OrderIntent":
        merged_metadata = dict(intent.metadata)
        if metadata:
            merged_metadata.update(metadata)
        return cls(
            symbol=intent.symbol,
            action=intent.side,
            quantity=intent.quantity,
            price=intent.price,
            order_type=intent.order_type,
            strategy_id=intent.strategy_id,
            metadata=merged_metadata,
        )

    def with_quantity(self, quantity: float) -> "OrderIntent":
        return OrderIntent(
            symbol=self.symbol,
            action=self.action,
            quantity=quantity,
            price=self.price,
            order_type=self.order_type,
            strategy_id=self.strategy_id,
            metadata=dict(self.metadata),
            created_at=self.created_at,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "action": self.action,
            "price": self.price,
            "quantity": self.quantity,
            "context": {
                "symbol": self.symbol,
                "price": self.price,
                "quantity": self.quantity,
                "order_type": self.order_type,
                "strategy_id": self.strategy_id,
                "metadata": self.metadata,
                "created_at": self.created_at,
            },
        }


def signal_to_intent(
    signal: dict[str, Any],
    *,
    symbol: str,
    quantity: float,
    strategy_id: str,
    order_type: str = "market",
    price: float | None = None,
) -> TradeIntent | None:
    """Convert a raw strategy signal dict into a TradeIntent.

    Returns *None* for hold signals.
    """
    action = str(signal.get("action", "hold")).lower()
    if action == "hold":
        return None
    resolved_price = price if price is not None else float(signal.get("price", 0.0))
    return TradeIntent(
        symbol=symbol,
        side=action,
        quantity=quantity,
        order_type=order_type,
        price=resolved_price,
        strategy_id=strategy_id,
        metadata={
            "strategy_params": signal.get("strategy", {}),
            "features": signal.get("features", {}),
        },
    )
