"""Realistic bar-based backtest with fee/slippage/latency costs."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BacktestConfig:
    fee_bps: float = 4.0
    slippage_bps: float = 3.0
    latency_bars: int = 1


@dataclass(frozen=True)
class BacktestSummary:
    net_pnl: float
    gross_pnl: float
    cost: float
    trade_count: int


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

        gross_pnl = 0.0
        for index in range(len(closes) - 1):
            gross_pnl += (float(closes[index + 1]) - float(closes[index])) * shifted_positions[index]

        total_cost = 0.0
        trade_count = 0
        previous = 0
        for index, position in enumerate(shifted_positions):
            if position == previous:
                continue
            trade_count += 1
            notional = abs(position - previous) * float(closes[min(index, len(closes) - 1)])
            total_cost += notional * ((self.config.fee_bps + self.config.slippage_bps) / 10_000.0)
            previous = position

        return BacktestSummary(
            net_pnl=round(gross_pnl - total_cost, 8),
            gross_pnl=round(gross_pnl, 8),
            cost=round(total_cost, 8),
            trade_count=trade_count,
        )
