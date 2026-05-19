from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from src.algotradeplan.orchestration.real_data_autopilot import (
    RealDataSmokeError,
    run_real_data_autopilot,
)


def _klines(length: int = 60) -> list[list[object]]:
    return [
        [
            1_700_000_000_000 + (index * 60_000),
            "100",
            "101",
            "99",
            str(100 + (index * 0.1)),
            "10",
        ]
        for index in range(length)
    ]


def _fake_getter(url: str, params: dict[str, object]):
    if url.endswith("/fapi/v1/exchangeInfo"):
        return {
            "symbols": [
                {"symbol": "BTCUSDT", "status": "TRADING", "quoteAsset": "USDT"},
                {"symbol": "ETHUSDT", "status": "TRADING", "quoteAsset": "USDT"},
            ]
        }
    if url.endswith("/fapi/v1/ticker/price"):
        return {"symbol": params["symbol"], "price": "105"}
    if url.endswith("/fapi/v1/klines"):
        return _klines()
    if url.endswith("/fapi/v1/trades"):
        return [{"id": 1}, {"id": 2}]
    if url.endswith("/fapi/v1/depth"):
        return {"bids": [["100", "1"]], "asks": [["101", "1"]]}
    if url.endswith("/fapi/v1/fundingRate"):
        return [{"fundingRate": "0.0001"}]

    if url.endswith("/v5/market/instruments-info"):
        return {
            "result": {
                "list": [
                    {"symbol": "BTCUSDT", "status": "Trading", "quoteCoin": "USDT"},
                    {"symbol": "SOLUSDT", "status": "Trading", "quoteCoin": "USDT"},
                ]
            }
        }
    if url.endswith("/v5/market/tickers"):
        return {"result": {"list": [{"symbol": params["symbol"], "lastPrice": "105"}]}}
    if url.endswith("/v5/market/kline"):
        return {"result": {"list": [["1700000000000", "100", "101", "99", "105", "1000"]]}}
    if url.endswith("/v5/market/recent-trade"):
        return {"result": {"list": [{"i": "1"}]}}
    if url.endswith("/v5/market/orderbook"):
        return {"result": {"a": [["101", "1"]], "b": [["100", "1"]]}}
    if url.endswith("/v5/market/funding/history"):
        return {"result": {"list": [{"fundingRate": "0.0002"}]}}

    if url.endswith("/0/public/AssetPairs"):
        return {
            "result": {
                "XXBTZUSD": {"wsname": "XBT/USD"},
                "XETHZUSD": {"wsname": "ETH/USD"},
            }
        }
    if url.endswith("/0/public/Ticker"):
        return {"result": {str(params.get("pair", "XXBTZUSD")): {"c": ["105", "1"]}}}
    if url.endswith("/0/public/OHLC"):
        pair = str(params.get("pair", "XXBTZUSD"))
        return {"result": {pair: _klines()}}
    if url.endswith("/0/public/Trades"):
        pair = str(params.get("pair", "XXBTZUSD"))
        return {"result": {pair: [{"price": "105"}]}}
    if url.endswith("/0/public/Depth"):
        pair = str(params.get("pair", "XXBTZUSD"))
        return {"result": {pair: {"bids": [["100", "1"]], "asks": [["101", "1"]]}}}

    if url.endswith("/products"):
        return [
            {
                "id": "BTC-USD",
                "quote_currency": "USD",
                "status": "online",
                "trading_disabled": False,
            },
            {
                "id": "ETH-USD",
                "quote_currency": "USD",
                "status": "online",
                "trading_disabled": False,
            },
        ]
    if "/products/" in url and url.endswith("/ticker"):
        return {"price": "105", "product_id": "BTC-USD"}
    if "/products/" in url and url.endswith("/candles"):
        return _klines()
    if "/products/" in url and url.endswith("/trades"):
        return [{"trade_id": 1}]
    if "/products/" in url and url.endswith("/book"):
        return {"bids": [["100", "1"]], "asks": [["101", "1"]]}

    if url.endswith("/v1/finance/search"):
        return {"quotes": [{"symbol": "BTC-USD"}, {"symbol": "ETH-USD"}]}
    if "/v8/finance/chart/" in url:
        candles = _klines()
        return {
            "chart": {
                "result": [
                    {
                        "timestamp": [int(row[0] / 1000) for row in candles],
                        "indicators": {
                            "quote": [
                                {
                                    "open": [float(row[1]) for row in candles],
                                    "high": [float(row[2]) for row in candles],
                                    "low": [float(row[3]) for row in candles],
                                    "close": [float(row[4]) for row in candles],
                                }
                            ]
                        },
                        "meta": {"regularMarketPrice": 105.0, "bid": 104.9, "ask": 105.1},
                    }
                ]
            }
        }

    if url.endswith("/api/v1/search"):
        query = str(params.get("query", "")).lower()
        if query == "bitcoin":
            return {"hits": [{"title": "Bitcoin jumps"}, {"title": "Ethereum follows"}]}
        return {"hits": [{"title": "Bitcoin market outlook"}]}

    if url.endswith("/v1/currencies"):
        return {"USD": "US Dollar", "EUR": "Euro"}
    if url.endswith("/v1/latest"):
        return {"base": params.get("base", "USD"), "rates": {"EUR": 0.9, "JPY": 150.0}}

    raise AssertionError(f"Unexpected URL: {url}")


class RealDataAutopilotTest(unittest.TestCase):
    def test_pipeline_report_contains_expected_coverage(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            report_path = Path(tmp_dir) / "report.json"
            report = run_real_data_autopilot(
                report_path=report_path,
                max_symbols_per_source=2,
                json_getter=_fake_getter,
            )

            self.assertGreaterEqual(len(report.market_sources), 5)
            self.assertGreater(report.news_story_count, 0)
            self.assertGreater(report.macro_series_count, 0)
            self.assertIn("source_issue_count", report.metrics)
            self.assertIn("binance_futures", report.source_inventory)
            self.assertIn("coinbase_spot", report.source_inventory)
            self.assertIn("yahoo_unofficial", report.source_inventory)
            self.assertIn(report.intent["action"], {"buy", "sell", "hold"})
            self.assertTrue(report.risk_decision["approved"])
            self.assertIn("market_symbols_total", report.metrics)
            stored = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(stored["market_sources"][0]["source"], "binance_futures")
            self.assertIn("source_issues", stored)
            self.assertIn("source_inventory", stored)

    def test_missing_dataset_coverage_raises(self) -> None:
        def fake_getter_missing(url: str, params: dict[str, object]):
            payload = _fake_getter(url, params)
            if url.endswith("/fapi/v1/fundingRate"):
                return []
            return payload

        with tempfile.TemporaryDirectory() as tmp_dir:
            report_path = Path(tmp_dir) / "report.json"
            with self.assertRaisesRegex(RealDataSmokeError, "missing dataset coverage"):
                run_real_data_autopilot(
                    report_path=report_path,
                    max_symbols_per_source=2,
                    json_getter=fake_getter_missing,
                )

    def test_allow_partial_records_news_and_macro_issues(self) -> None:
        def fake_getter_partial(url: str, params: dict[str, object]):
            if url.endswith("/api/v1/search") or url.endswith("/v1/currencies"):
                raise RuntimeError("upstream down")
            return _fake_getter(url, params)

        with tempfile.TemporaryDirectory() as tmp_dir:
            report = run_real_data_autopilot(
                report_path=Path(tmp_dir) / "report.json",
                max_symbols_per_source=2,
                allow_partial=True,
                json_getter=fake_getter_partial,
            )

            sources = {issue["source"] for issue in report.source_issues}
            self.assertIn("hacker_news", sources)
            self.assertIn("frankfurter", sources)
            self.assertEqual(report.news_story_count, 0)
            self.assertEqual(report.macro_series_count, 0)

    def test_news_failure_raises_without_partial(self) -> None:
        def fake_getter_news_failure(url: str, params: dict[str, object]):
            if url.endswith("/api/v1/search"):
                raise RuntimeError("news unavailable")
            return _fake_getter(url, params)

        with tempfile.TemporaryDirectory() as tmp_dir:
            with self.assertRaisesRegex(RealDataSmokeError, "news source failure"):
                run_real_data_autopilot(
                    report_path=Path(tmp_dir) / "report.json",
                    max_symbols_per_source=2,
                    allow_partial=False,
                    json_getter=fake_getter_news_failure,
                )


if __name__ == "__main__":
    unittest.main()
