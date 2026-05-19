"""Trade ledger: append-only record of all fills and cash flows."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass(frozen=True)
class LedgerEntry:
    timestamp: str
    symbol: str
    action: str  # "buy" | "sell"
    quantity: float
    price: float
    fee: float
    realized_pnl: float
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "symbol": self.symbol,
            "action": self.action,
            "quantity": self.quantity,
            "price": self.price,
            "fee": self.fee,
            "realized_pnl": round(self.realized_pnl, 8),
            "metadata": self.metadata,
        }


class TradeLedger:
    def __init__(self) -> None:
        self._entries: list[LedgerEntry] = []

    def record(
        self,
        *,
        symbol: str,
        action: str,
        quantity: float,
        price: float,
        fee: float = 0.0,
        realized_pnl: float = 0.0,
        metadata: dict[str, Any] | None = None,
    ) -> LedgerEntry:
        entry = LedgerEntry(
            timestamp=datetime.now(UTC).isoformat(),
            symbol=symbol,
            action=action,
            quantity=quantity,
            price=price,
            fee=fee,
            realized_pnl=realized_pnl,
            metadata=metadata or {},
        )
        self._entries.append(entry)
        return entry

    @property
    def entries(self) -> list[LedgerEntry]:
        return list(self._entries)

    def total_fees(self) -> float:
        return sum(e.fee for e in self._entries)

    def total_realized_pnl(self) -> float:
        return sum(e.realized_pnl for e in self._entries)

    def trade_count(self) -> int:
        return len(self._entries)

    def to_list(self) -> list[dict[str, Any]]:
        return [e.to_dict() for e in self._entries]
