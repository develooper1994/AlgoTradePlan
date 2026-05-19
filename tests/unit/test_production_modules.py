"""Tests for new production-grade framework modules."""

from __future__ import annotations

import unittest

from src.algotradeplan.backtest import BacktestConfig, RealisticBacktester
from src.algotradeplan.core.canonical import (
    AssetIdentity,
    FundingRateRecord,
    MacroSnapshot,
    NewsItem,
    OHLCVRecord,
    OrderbookSnapshot,
    TradeRecord,
)
from src.algotradeplan.core.intent import OrderIntent, TradeIntent, signal_to_intent
from src.algotradeplan.portfolio.manager import PortfolioManager
from src.algotradeplan.plugins.connectors.simulated_fill_connector import (
    SimulatedFillExecutionConnectorPlugin,
)
from src.algotradeplan.plugins.risk.engine import RiskDecision, RiskEngine


# ---------------------------------------------------------------------------
# Portfolio manager
# ---------------------------------------------------------------------------

class PortfolioManagerTest(unittest.TestCase):
    def test_buy_reduces_cash_and_opens_position(self) -> None:
        pm = PortfolioManager(starting_cash=10_000.0, fee_rate=0.001)
        snap = pm.apply_execution({"symbol": "BTC/USDT", "action": "buy", "quantity": 0.1, "price": 50_000.0})
        self.assertLess(snap["cash"], 10_000.0)
        self.assertIn("BTC/USDT", snap["positions"])
        self.assertAlmostEqual(snap["positions"]["BTC/USDT"]["quantity"], 0.1)

    def test_sell_increases_cash_and_realizes_pnl(self) -> None:
        pm = PortfolioManager(starting_cash=10_000.0, fee_rate=0.0)
        pm.apply_execution({"symbol": "ETH/USDT", "action": "buy", "quantity": 1.0, "price": 2_000.0})
        snap = pm.apply_execution({"symbol": "ETH/USDT", "action": "sell", "quantity": 1.0, "price": 2_100.0})
        self.assertGreater(snap["realized_pnl"], 0.0)

    def test_snapshot_contains_all_required_keys(self) -> None:
        pm = PortfolioManager(starting_cash=5_000.0)
        snap = pm.snapshot()
        for key in ("cash", "positions", "realized_pnl", "unrealized_pnl", "nav", "exposure", "total_fees", "trade_count"):
            self.assertIn(key, snap)

    def test_nav_equals_cash_with_no_positions(self) -> None:
        pm = PortfolioManager(starting_cash=8_000.0)
        snap = pm.snapshot()
        self.assertAlmostEqual(snap["nav"], snap["cash"])

    def test_ledger_records_trades(self) -> None:
        pm = PortfolioManager(starting_cash=10_000.0, fee_rate=0.0)
        pm.apply_execution({"symbol": "BTC/USDT", "action": "buy", "quantity": 0.01, "price": 60_000.0})
        ledger = pm.ledger()
        self.assertEqual(len(ledger), 1)
        self.assertEqual(ledger[0]["action"], "buy")

    def test_reconcile_detects_cash_drift(self) -> None:
        pm = PortfolioManager(starting_cash=10_000.0)
        result = pm.reconcile({"cash": 9_000.0})
        self.assertFalse(result["in_sync"])
        self.assertIn("cash", result["diffs"])

    def test_reconcile_passes_when_in_sync(self) -> None:
        pm = PortfolioManager(starting_cash=10_000.0)
        result = pm.reconcile({"cash": 10_000.0, "positions": {}})
        self.assertTrue(result["in_sync"])

    def test_noop_execution_returns_unchanged_snapshot(self) -> None:
        pm = PortfolioManager(starting_cash=5_000.0)
        snap = pm.apply_execution(None)
        self.assertAlmostEqual(snap["cash"], 5_000.0)

    def test_ignore_invalid_action(self) -> None:
        pm = PortfolioManager(starting_cash=5_000.0)
        snap = pm.apply_execution({"symbol": "X", "action": "hold", "quantity": 1.0, "price": 100.0})
        self.assertAlmostEqual(snap["cash"], 5_000.0)


# ---------------------------------------------------------------------------
# Risk engine
# ---------------------------------------------------------------------------

class RiskEngineTest(unittest.TestCase):
    def _intent(self, action: str = "buy", qty: float = 0.01, price: float = 50_000.0, symbol: str = "BTC/USDT") -> dict:
        return {
            "symbol": symbol,
            "action": action,
            "context": {"symbol": symbol, "quantity": qty, "price": price},
        }

    def test_approved_order_passes_all_checks(self) -> None:
        engine = RiskEngine(max_notional=10_000.0)
        result = engine.evaluate(self._intent())
        self.assertTrue(result["approved"])
        self.assertEqual(result["rejected_rules"], [])
        self.assertGreater(len(result["checks"]), 0)

    def test_max_notional_exceeded_rejected(self) -> None:
        engine = RiskEngine(max_notional=100.0)
        result = engine.evaluate(self._intent(qty=1.0, price=200.0))
        self.assertFalse(result["approved"])
        self.assertIn("max_notional_exceeded", result["rejected_rules"])

    def test_kill_switch_blocks_all_orders(self) -> None:
        engine = RiskEngine()
        engine.trigger_kill_switch("test_stop")
        result = engine.evaluate(self._intent())
        self.assertFalse(result["approved"])
        self.assertEqual(result["reason"], "test_stop")

    def test_symbol_blacklist_rejects(self) -> None:
        engine = RiskEngine(symbol_blacklist=["DOGE/USDT"])
        result = engine.evaluate(self._intent(symbol="DOGE/USDT"))
        self.assertFalse(result["approved"])
        self.assertIn("symbol_blacklisted", result["rejected_rules"])

    def test_symbol_whitelist_allows_listed(self) -> None:
        engine = RiskEngine(symbol_whitelist=["BTC/USDT"], max_notional=10_000.0)
        result = engine.evaluate(self._intent(symbol="BTC/USDT"))
        self.assertTrue(result["approved"])

    def test_symbol_whitelist_blocks_unlisted(self) -> None:
        engine = RiskEngine(symbol_whitelist=["BTC/USDT"])
        result = engine.evaluate(self._intent(symbol="ETH/USDT"))
        self.assertFalse(result["approved"])

    def test_daily_loss_limit_blocks_after_threshold(self) -> None:
        engine = RiskEngine(max_daily_loss=100.0, max_notional=10_000.0)
        engine.record_loss(200.0)
        result = engine.evaluate(self._intent())
        self.assertFalse(result["approved"])
        self.assertIn("max_daily_loss_exceeded", result["rejected_rules"])

    def test_unsupported_action_rejected(self) -> None:
        engine = RiskEngine()
        result = engine.evaluate(self._intent(action="hold"))
        self.assertFalse(result["approved"])

    def test_structured_decision_fields(self) -> None:
        engine = RiskEngine(max_notional=10_000.0)
        result = engine.evaluate(self._intent())
        for key in ("approved", "reason", "checks", "rejected_rules", "adjusted_quantity", "original_quantity", "notional"):
            self.assertIn(key, result)


# ---------------------------------------------------------------------------
# Backtest engine – extended metrics
# ---------------------------------------------------------------------------

class BacktestExtendedTest(unittest.TestCase):
    def test_equity_curve_is_populated(self) -> None:
        closes = [100.0 + i * 0.5 for i in range(50)]
        positions = [1] * 50
        summary = RealisticBacktester().run(closes, positions)
        self.assertGreater(len(summary.equity_curve), 1)

    def test_max_drawdown_non_negative(self) -> None:
        closes = [100.0, 110.0, 90.0, 95.0, 80.0, 100.0]
        positions = [1, 1, 1, 1, 1, 0]
        summary = RealisticBacktester().run(closes, positions)
        self.assertGreaterEqual(summary.max_drawdown, 0.0)

    def test_trade_list_populated(self) -> None:
        closes = [100.0, 101.0, 102.0, 101.5, 103.0]
        positions = [0, 1, 1, 0, 0]
        summary = RealisticBacktester(BacktestConfig(latency_bars=0)).run(closes, positions)
        self.assertGreater(len(summary.trade_list), 0)
        self.assertIn("action", summary.trade_list[0])

    def test_to_dict_contains_extended_fields(self) -> None:
        closes = [100.0, 105.0, 102.0]
        positions = [1, 1, 0]
        summary = RealisticBacktester().run(closes, positions)
        d = summary.to_dict()
        for key in ("net_pnl", "gross_pnl", "cost", "trade_count", "max_drawdown", "sharpe_ratio", "sortino_ratio", "equity_curve", "trade_list"):
            self.assertIn(key, d)


# ---------------------------------------------------------------------------
# Canonical schema models
# ---------------------------------------------------------------------------

class CanonicalSchemaTest(unittest.TestCase):
    def test_ohlcv_record_fields(self) -> None:
        rec = OHLCVRecord(
            symbol="BTC/USDT", exchange="binance", timestamp_ms=1_700_000_000_000,
            open=50_000.0, high=51_000.0, low=49_000.0, close=50_500.0, volume=1234.5,
        )
        self.assertEqual(rec.symbol, "BTC/USDT")
        self.assertEqual(rec.volume, 1234.5)

    def test_asset_identity(self) -> None:
        asset = AssetIdentity(
            symbol="BTC/USDT", base_asset="BTC", quote_asset="USDT",
            exchange="binance", asset_class="spot",
        )
        self.assertEqual(asset.exchange, "binance")

    def test_trade_record(self) -> None:
        rec = TradeRecord(
            symbol="ETH/USDT", exchange="bybit", trade_id="t1",
            timestamp_ms=1_700_000_000_001, price=2_000.0, quantity=0.5, side="buy",
        )
        self.assertEqual(rec.side, "buy")

    def test_orderbook_snapshot(self) -> None:
        snap = OrderbookSnapshot(
            symbol="BTC/USDT", exchange="kraken", timestamp_ms=1_700_000_000_000,
            bids=[[50_000.0, 1.0]], asks=[[50_001.0, 0.5]],
        )
        self.assertEqual(len(snap.bids), 1)

    def test_funding_rate_record(self) -> None:
        rec = FundingRateRecord(symbol="BTC/USDT", exchange="binance", timestamp_ms=0, rate=0.0001)
        self.assertFalse(rec.derived)

    def test_news_item(self) -> None:
        item = NewsItem(title="BTC up", url="https://example.com", source="hn", published_at="2024-01-01")
        self.assertEqual(item.title, "BTC up")

    def test_macro_snapshot(self) -> None:
        snap = MacroSnapshot(base_currency="USD", timestamp="2024-01-01", rates={"EUR": 0.91})
        self.assertIn("EUR", snap.rates)


# ---------------------------------------------------------------------------
# Intent model
# ---------------------------------------------------------------------------

class IntentModelTest(unittest.TestCase):
    def test_trade_intent_to_order_intent(self) -> None:
        intent = TradeIntent(
            symbol="BTC/USDT", side="buy", quantity=0.01,
            order_type="market", price=50_000.0, strategy_id="ema_cross",
        )
        order = intent.to_order_intent()
        self.assertEqual(order["action"], "buy")
        self.assertEqual(order["symbol"], "BTC/USDT")
        self.assertEqual(order["context"]["quantity"], 0.01)

    def test_signal_to_intent_buy(self) -> None:
        signal = {"action": "buy", "price": 50_000.0}
        intent = signal_to_intent(signal, symbol="BTC/USDT", quantity=0.01, strategy_id="ema")
        self.assertIsNotNone(intent)
        self.assertEqual(intent.side, "buy")  # type: ignore[union-attr]

    def test_signal_to_intent_hold_returns_none(self) -> None:
        signal = {"action": "hold"}
        intent = signal_to_intent(signal, symbol="BTC/USDT", quantity=0.01, strategy_id="ema")
        self.assertIsNone(intent)

    def test_trade_intent_to_dict(self) -> None:
        intent = TradeIntent(
            symbol="ETH/USDT", side="sell", quantity=1.0,
            order_type="limit", price=2_000.0, strategy_id="my_strat",
        )
        d = intent.to_dict()
        for key in ("symbol", "side", "quantity", "order_type", "price", "strategy_id", "timestamp"):
            self.assertIn(key, d)

    def test_structured_order_intent_carries_metadata(self) -> None:
        intent = TradeIntent(
            symbol="BTC/USDT", side="buy", quantity=0.02,
            order_type="market", price=50_000.0, strategy_id="ema_cross",
            metadata={"signal_id": "abc123"},
        )
        order_intent = OrderIntent.from_trade_intent(intent)
        payload = order_intent.to_dict()
        self.assertEqual(payload["action"], "buy")
        self.assertEqual(payload["context"]["metadata"]["signal_id"], "abc123")


class SimulatedFillConnectorTest(unittest.TestCase):
    def test_fill_contains_fee_slippage_and_notional(self) -> None:
        connector = SimulatedFillExecutionConnectorPlugin()
        fill = connector.send_order(
            {
                "symbol": "BTC/USDT",
                "action": "buy",
                "price": 50_000.0,
                "quantity": 0.01,
                "context": {"price": 50_000.0, "quantity": 0.01},
            }
        )
        for key in (
            "order_id",
            "status",
            "symbol",
            "action",
            "requested_quantity",
            "filled_quantity",
            "requested_price",
            "fill_price",
            "fee",
            "slippage",
            "notional",
            "filled_at",
        ):
            self.assertIn(key, fill)
        self.assertGreater(fill["fill_price"], fill["requested_price"])


if __name__ == "__main__":
    unittest.main()
