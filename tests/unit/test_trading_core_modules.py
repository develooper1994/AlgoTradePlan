from __future__ import annotations

import unittest

from src.algotradeplan.backtest import BacktestConfig, RealisticBacktester
from src.algotradeplan.plugins.indicators import RollingWindowFeatureEngine
from src.algotradeplan.plugins.strategies import EmaCrossAtrStopStrategyPlugin


def _candles(length: int = 80) -> list[dict[str, float]]:
    candles: list[dict[str, float]] = []
    for index in range(length):
        close = 100.0 + (index * 0.3)
        candles.append({"open": close - 0.2, "high": close + 0.4, "low": close - 0.5, "close": close})
    return candles


class TradingCoreModulesTest(unittest.TestCase):
    def test_rolling_feature_engine_outputs_non_zero_values(self) -> None:
        candles = _candles(40)
        highs = [candle["high"] for candle in candles]
        lows = [candle["low"] for candle in candles]
        closes = [candle["close"] for candle in candles]
        snapshot = RollingWindowFeatureEngine().compute(highs=highs, lows=lows, closes=closes)

        self.assertGreater(snapshot.ema_fast, 0.0)
        self.assertGreater(snapshot.ema_slow, 0.0)
        self.assertGreater(snapshot.atr, 0.0)
        self.assertGreater(snapshot.bollinger_upper, snapshot.bollinger_lower)

    def test_ema_cross_strategy_returns_tradeable_signal(self) -> None:
        signal = EmaCrossAtrStopStrategyPlugin().generate_signal({"candles": _candles()})
        self.assertIn(signal["action"], {"buy", "sell"})
        self.assertIn("strategy", signal)
        self.assertIn("backtest", signal)
        self.assertIn("features", signal)

    def test_realistic_backtester_applies_cost_model(self) -> None:
        closes = [100.0, 101.0, 102.0, 101.5, 103.0]
        positions = [0, 1, 1, 0, 0]
        summary = RealisticBacktester(
            BacktestConfig(fee_bps=5.0, slippage_bps=5.0, latency_bars=1)
        ).run(closes, positions)

        self.assertGreaterEqual(summary.trade_count, 1)
        self.assertGreater(summary.cost, 0.0)
        self.assertLess(summary.net_pnl, summary.gross_pnl)


if __name__ == "__main__":
    unittest.main()
