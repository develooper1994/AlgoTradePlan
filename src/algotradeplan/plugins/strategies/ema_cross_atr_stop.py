"""EMA cross strategy with ATR stop and parameter optimization."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.algotradeplan.backtest import BacktestSummary, RealisticBacktester
from src.algotradeplan.plugins.indicators import RollingWindowFeatureEngine, atr, ema


@dataclass(frozen=True)
class EmaAtrParams:
    short_window: int
    long_window: int
    atr_window: int
    atr_stop_multiple: float


class EmaCrossAtrStopStrategyPlugin:
    plugin_id = "ema_cross_atr_stop_strategy"

    def __init__(self, parameter_grid: list[EmaAtrParams] | None = None) -> None:
        self.parameter_grid = parameter_grid or [
            EmaAtrParams(5, 13, 14, 1.5),
            EmaAtrParams(8, 21, 14, 2.0),
            EmaAtrParams(13, 34, 21, 2.5),
        ]
        self.feature_engine = RollingWindowFeatureEngine()
        self.backtester = RealisticBacktester()

    def _positions_from_params(self, closes: list[float], highs: list[float], lows: list[float], params: EmaAtrParams) -> list[int]:
        ema_short = ema(closes, params.short_window)
        ema_long = ema(closes, params.long_window)
        atr_series = atr(highs, lows, closes, params.atr_window)
        if not ema_short or not ema_long or not atr_series:
            return [0] * len(closes)

        positions: list[int] = []
        in_position = False
        entry_price = 0.0
        for index, close in enumerate(closes):
            signal_long = ema_short[index] >= ema_long[index]
            atr_value = atr_series[index]
            stop_price = entry_price - (atr_value * params.atr_stop_multiple)

            if not in_position and signal_long:
                in_position = True
                entry_price = close
            elif in_position and (not signal_long or close <= stop_price):
                in_position = False
                entry_price = 0.0
            positions.append(1 if in_position else 0)
        return positions

    def optimize(self, closes: list[float], highs: list[float], lows: list[float]) -> tuple[EmaAtrParams, BacktestSummary]:
        best_params = self.parameter_grid[0]
        best_summary = self.backtester.run(closes, self._positions_from_params(closes, highs, lows, best_params))
        for params in self.parameter_grid[1:]:
            summary = self.backtester.run(closes, self._positions_from_params(closes, highs, lows, params))
            if summary.net_pnl > best_summary.net_pnl:
                best_params = params
                best_summary = summary
        return best_params, best_summary

    def generate_signal(self, context: dict[str, Any]) -> dict[str, Any]:
        candles = context.get("candles", [])
        if len(candles) < 5:
            return {"action": "hold", "reason": "insufficient_candles"}

        highs = [float(candle["high"]) for candle in candles]
        lows = [float(candle["low"]) for candle in candles]
        closes = [float(candle["close"]) for candle in candles]

        best_params, summary = self.optimize(closes, highs, lows)
        positions = self._positions_from_params(closes, highs, lows, best_params)
        action = "buy" if positions[-1] == 1 else "sell"
        features = self.feature_engine.compute(
            highs=highs,
            lows=lows,
            closes=closes,
            ema_fast_window=best_params.short_window,
            ema_slow_window=best_params.long_window,
            atr_window=best_params.atr_window,
        )
        return {
            "action": action,
            "strategy": {
                "short_window": best_params.short_window,
                "long_window": best_params.long_window,
                "atr_window": best_params.atr_window,
                "atr_stop_multiple": best_params.atr_stop_multiple,
            },
            "backtest": {
                "net_pnl": summary.net_pnl,
                "gross_pnl": summary.gross_pnl,
                "cost": summary.cost,
                "trade_count": summary.trade_count,
            },
            "features": {
                "ema_fast": features.ema_fast,
                "ema_slow": features.ema_slow,
                "atr": features.atr,
                "bollinger_mid": features.bollinger_mid,
                "bollinger_upper": features.bollinger_upper,
                "bollinger_lower": features.bollinger_lower,
            },
        }
