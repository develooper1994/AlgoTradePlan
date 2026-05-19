"""Realistic bar-based backtest with fee/slippage/latency costs."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class BacktestConfig:
    fee_bps: float = 4.0
    slippage_bps: float = 3.0
    latency_bars: int = 1


@dataclass(frozen=True)
class TradeFill:
    bar_index: int
    action: str  # "buy" | "sell"
    price: float
    quantity: int
    fee: float


@dataclass(frozen=True)
class BacktestSummary:
    net_pnl: float
    gross_pnl: float
    cost: float
    trade_count: int
    # Extended metrics
    equity_curve: list[float] = field(default_factory=list)
    max_drawdown: float = 0.0
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    trade_list: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "net_pnl": self.net_pnl,
            "gross_pnl": self.gross_pnl,
            "cost": self.cost,
            "trade_count": self.trade_count,
            "max_drawdown": self.max_drawdown,
            "sharpe_ratio": self.sharpe_ratio,
            "sortino_ratio": self.sortino_ratio,
            "equity_curve": self.equity_curve,
            "trade_list": self.trade_list,
        }


def _compute_drawdown(equity_curve: list[float]) -> float:
    if not equity_curve:
        return 0.0
    peak = equity_curve[0]
    max_dd = 0.0
    for value in equity_curve:
        if value > peak:
            peak = value
        dd = (peak - value) / peak if peak > 0 else 0.0
        if dd > max_dd:
            max_dd = dd
    return round(max_dd, 8)


def _compute_sharpe(returns: list[float], risk_free: float = 0.0) -> float:
    if len(returns) < 2:
        return 0.0
    mean = sum(returns) / len(returns)
    variance = sum((r - mean) ** 2 for r in returns) / (len(returns) - 1)
    std = math.sqrt(variance)
    if std == 0:
        return 0.0
    return round((mean - risk_free) / std * math.sqrt(252), 4)


def _compute_sortino(returns: list[float], risk_free: float = 0.0) -> float:
    if len(returns) < 2:
        return 0.0
    mean = sum(returns) / len(returns)
    downside = [r for r in returns if r < risk_free]
    if not downside:
        return 0.0
    downside_variance = sum((r - risk_free) ** 2 for r in downside) / len(downside)
    downside_std = math.sqrt(downside_variance)
    if downside_std == 0:
        return 0.0
    return round((mean - risk_free) / downside_std * math.sqrt(252), 4)


class RealisticBacktester:
    def __init__(self, config: BacktestConfig | None = None) -> None:
        self.config = config or BacktestConfig()

    def run(self, closes: list[float], positions: list[int]) -> BacktestSummary:
        if len(closes) < 2 or not positions:
            return BacktestSummary(net_pnl=0.0, gross_pnl=0.0, cost=0.0, trade_count=0)

        shifted_positions = [0] * len(positions)
        for index, position in enumerate(positions):
            shifted_index = index + max(0, self.config.latency_bars)
            if shifted_index < len(shifted_positions):
                shifted_positions[shifted_index] = position

        # Build bar-by-bar returns, equity curve, and trade list
        cost_factor = (self.config.fee_bps + self.config.slippage_bps) / 10_000.0
        equity = 0.0
        equity_curve: list[float] = [0.0]
        bar_returns: list[float] = []
        trade_list: list[dict[str, Any]] = []
        total_cost = 0.0
        trade_count = 0
        previous = 0

        for index in range(len(closes) - 1):
            pos = shifted_positions[index]
            bar_return = (float(closes[index + 1]) - float(closes[index])) * pos
            equity += bar_return
            equity_curve.append(round(equity, 8))
            if closes[index] > 0:
                bar_returns.append(bar_return / float(closes[index]))

        for index, position in enumerate(shifted_positions):
            if position == previous:
                continue
            trade_count += 1
            price = float(closes[min(index, len(closes) - 1)])
            notional = abs(position - previous) * price
            fee = notional * cost_factor
            total_cost += fee
            action = "buy" if position > previous else "sell"
            trade_list.append(
                {
                    "bar_index": index,
                    "action": action,
                    "price": round(price, 8),
                    "quantity": abs(position - previous),
                    "fee": round(fee, 8),
                }
            )
            previous = position

        gross_pnl = equity_curve[-1] if equity_curve else 0.0
        net_pnl = round(gross_pnl - total_cost, 8)

        # Net equity curve: apply trade costs at the exact bar where each trade occurs
        cost_by_bar: dict[int, float] = {}
        for trade in trade_list:
            bar = int(trade["bar_index"])
            cost_by_bar[bar] = cost_by_bar.get(bar, 0.0) + float(trade["fee"])

        cumulative_cost = 0.0
        net_equity_curve: list[float] = []
        for i, v in enumerate(equity_curve):
            cumulative_cost += cost_by_bar.get(i, 0.0)
            net_equity_curve.append(round(v - cumulative_cost, 8))

        return BacktestSummary(
            net_pnl=net_pnl,
            gross_pnl=round(gross_pnl, 8),
            cost=round(total_cost, 8),
            trade_count=trade_count,
            equity_curve=net_equity_curve,
            max_drawdown=_compute_drawdown(net_equity_curve),
            sharpe_ratio=_compute_sharpe(bar_returns),
            sortino_ratio=_compute_sortino(bar_returns),
            trade_list=trade_list,
        )
