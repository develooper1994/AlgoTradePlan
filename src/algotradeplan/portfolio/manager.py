"""Production portfolio manager with cash, positions, ledger, PnL, and reconciliation hooks."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from src.algotradeplan.portfolio.ledger import TradeLedger
from src.algotradeplan.portfolio.positions import PositionBook

_DEFAULT_FEE_RATE = 0.001  # 10 bps


class PortfolioManager:
    """Track cash, positions, realized/unrealized PnL, fees, and NAV."""

    def __init__(self, starting_cash: float = 10_000.0, fee_rate: float = _DEFAULT_FEE_RATE) -> None:
        self.cash = starting_cash
        self.fee_rate = fee_rate
        self._positions = PositionBook()
        self._ledger = TradeLedger()
        self._snapshots: list[dict[str, Any]] = []

    # ------------------------------------------------------------------
    # Core mutation
    # ------------------------------------------------------------------

    def apply_execution(self, execution: dict[str, Any] | None, *, save_snapshot: bool = True) -> dict[str, Any]:
        """Process a fill dict and update portfolio state.

        The *execution* dict is expected to have:
        - symbol (str)
        - action  "buy" | "sell"
        - quantity (float)
        - price (float)
        - fee (float, optional – computed from fee_rate if absent)
        """
        if not execution:
            return self.snapshot()

        status = str(execution.get("status", "filled")).lower()
        if status not in {"filled", "partially_filled", "partial_fill"}:
            return self.snapshot()

        symbol = str(execution.get("symbol", ""))
        action = str(execution.get("action", "")).lower()
        quantity = float(execution.get("filled_quantity", execution.get("quantity", 0.0)))
        price = float(execution.get("fill_price", execution.get("price", 0.0)))

        if action not in {"buy", "sell"} or quantity <= 0 or price <= 0:
            return self.snapshot()

        notional = quantity * price
        fee = float(execution.get("fee", notional * self.fee_rate))
        realized_pnl = 0.0

        if action == "buy":
            self.cash -= notional + fee
            self._positions.open(symbol, quantity, price, fee)
        elif action == "sell":
            _, realized_pnl = self._positions.close(symbol, quantity, price, fee)
            self.cash += notional - fee

        self._ledger.record(
            symbol=symbol,
            action=action,
            quantity=quantity,
            price=price,
            fee=fee,
            realized_pnl=realized_pnl,
            metadata={
                "order_id": execution.get("order_id"),
                "status": status,
                "requested_quantity": execution.get("requested_quantity"),
                "requested_price": execution.get("requested_price"),
                "slippage": execution.get("slippage"),
                "notional": execution.get("notional", notional),
            },
        )

        snap = self.snapshot()
        if save_snapshot:
            self._snapshots.append(snap)
        return snap

    # ------------------------------------------------------------------
    # Metrics
    # ------------------------------------------------------------------

    def unrealized_pnl(self, current_prices: dict[str, float] | None = None) -> float:
        prices = current_prices or {}
        return self._positions.unrealized_pnl(prices)

    def realized_pnl(self) -> float:
        return self._ledger.total_realized_pnl()

    def nav(self, current_prices: dict[str, float] | None = None) -> float:
        """Net Asset Value = cash + market value of open positions."""
        prices = current_prices or {}
        return self.cash + self._positions.exposure(prices)

    def exposure(self, current_prices: dict[str, float] | None = None) -> float:
        return self._positions.exposure(current_prices or {})

    # ------------------------------------------------------------------
    # Snapshot / report
    # ------------------------------------------------------------------

    def snapshot(self, current_prices: dict[str, float] | None = None) -> dict[str, Any]:
        prices = current_prices or {}
        return {
            "timestamp": datetime.now(UTC).isoformat(),
            "cash": round(self.cash, 6),
            "positions": self._positions.to_dict(),
            "realized_pnl": round(self.realized_pnl(), 8),
            "unrealized_pnl": round(self.unrealized_pnl(prices), 8),
            "nav": round(self.nav(prices), 6),
            "exposure": round(self.exposure(prices), 6),
            "total_fees": round(self._ledger.total_fees(), 8),
            "trade_count": self._ledger.trade_count(),
        }

    def ledger(self) -> list[dict[str, Any]]:
        return self._ledger.to_list()

    def history(self) -> list[dict[str, Any]]:
        return list(self._snapshots)

    # ------------------------------------------------------------------
    # Reconciliation hook (override for broker reconciliation)
    # ------------------------------------------------------------------

    def reconcile(self, broker_snapshot: dict[str, Any]) -> dict[str, Any]:
        """Basic drift check between internal state and a broker snapshot."""
        diffs: dict[str, Any] = {}
        broker_cash = float(broker_snapshot.get("cash", self.cash))
        if abs(self.cash - broker_cash) > 0.01:
            diffs["cash"] = {"internal": self.cash, "broker": broker_cash}
        broker_positions = broker_snapshot.get("positions", {})
        for symbol, pos in self._positions.to_dict().items():
            broker_qty = float(broker_positions.get(symbol, {}).get("quantity", 0.0))
            if abs(pos["quantity"] - broker_qty) > 1e-8:
                diffs[symbol] = {"internal_qty": pos["quantity"], "broker_qty": broker_qty}
        return {"in_sync": not diffs, "diffs": diffs}
