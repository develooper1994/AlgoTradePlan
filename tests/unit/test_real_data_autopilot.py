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

            self.assertEqual(len(report.market_sources), 2)
            self.assertGreater(report.news_story_count, 0)
            self.assertGreater(report.macro_series_count, 0)
            self.assertIn(report.intent["action"], {"buy", "sell", "hold"})
            self.assertTrue(report.risk_decision["approved"])
            self.assertIn("market_symbols_total", report.metrics)
            stored = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(stored["market_sources"][0]["source"], "binance_futures")

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


if __name__ == "__main__":
    unittest.main()
