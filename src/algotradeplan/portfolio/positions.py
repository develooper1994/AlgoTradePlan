"""Position tracking with average entry price and unrealized PnL."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Position:
    symbol: str
    quantity: float = 0.0
    avg_entry_price: float = 0.0
    realized_pnl: float = 0.0
    fees_paid: float = 0.0

    def open(self, quantity: float, price: float, fee: float = 0.0) -> None:
        """Add to or open a long position."""
        if quantity <= 0:
            return
        total_cost = self.quantity * self.avg_entry_price + quantity * price
        self.quantity += quantity
        self.avg_entry_price = total_cost / self.quantity if self.quantity else 0.0
        self.fees_paid += fee

    def close(self, quantity: float, price: float, fee: float = 0.0) -> float:
        """Reduce or close position; returns realized PnL for the closed portion."""
        if quantity <= 0 or self.quantity <= 0:
            return 0.0
        closed_qty = min(quantity, self.quantity)
        pnl = (price - self.avg_entry_price) * closed_qty - fee
        self.realized_pnl += pnl
        self.quantity -= closed_qty
        self.fees_paid += fee
        if self.quantity == 0.0:
            self.avg_entry_price = 0.0
        return pnl

    def unrealized_pnl(self, current_price: float) -> float:
        if self.quantity == 0:
            return 0.0
        return (current_price - self.avg_entry_price) * self.quantity

    def exposure(self, current_price: float) -> float:
        return self.quantity * current_price

    def to_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "quantity": self.quantity,
            "avg_entry_price": self.avg_entry_price,
            "realized_pnl": round(self.realized_pnl, 8),
            "fees_paid": round(self.fees_paid, 8),
        }


@dataclass
class PositionBook:
    _positions: dict[str, Position] = field(default_factory=dict)

    def get(self, symbol: str) -> Position:
        if symbol not in self._positions:
            self._positions[symbol] = Position(symbol=symbol)
        return self._positions[symbol]

    def open(self, symbol: str, quantity: float, price: float, fee: float = 0.0) -> Position:
        pos = self.get(symbol)
        pos.open(quantity, price, fee)
        return pos

    def close(self, symbol: str, quantity: float, price: float, fee: float = 0.0) -> tuple[Position, float]:
        pos = self.get(symbol)
        pnl = pos.close(quantity, price, fee)
        return pos, pnl

    def unrealized_pnl(self, prices: dict[str, float]) -> float:
        return sum(pos.unrealized_pnl(prices.get(pos.symbol, pos.avg_entry_price)) for pos in self._positions.values())

    def exposure(self, prices: dict[str, float]) -> float:
        return sum(pos.exposure(prices.get(pos.symbol, pos.avg_entry_price)) for pos in self._positions.values())

    def to_dict(self) -> dict[str, Any]:
        return {symbol: pos.to_dict() for symbol, pos in self._positions.items() if pos.quantity != 0.0}
