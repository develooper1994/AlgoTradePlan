from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.algotradeplan.data import DataHub, ETL


def _klines(length: int = 10) -> list[list[object]]:
    return [
        [
            1_700_000_000_000 + (index * 60_000),
            "100",
            "101",
            "99",
            str(100 + index),
            "10",
        ]
        for index in range(length)
    ]


def _fake_getter(url: str, params: dict[str, object]):
    if url.endswith("/fapi/v1/exchangeInfo"):
        return {"symbols": [{"symbol": "BTCUSDT", "status": "TRADING", "quoteAsset": "USDT"}]}
    if url.endswith("/fapi/v1/ticker/price"):
        return {"symbol": params["symbol"], "price": "105"}
    if url.endswith("/fapi/v1/klines"):
        return _klines()
    if url.endswith("/fapi/v1/trades"):
        return [{"id": 1, "price": "105", "qty": "0.25", "time": 1_700_000_000_001}]
    if url.endswith("/fapi/v1/depth"):
        return {"bids": [["100", "1"]], "asks": [["101", "1"]]}
    if url.endswith("/fapi/v1/fundingRate"):
        return [{"fundingRate": "0.0001", "fundingTime": 1_700_000_000_002}]
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


class DataHubApiTest(unittest.TestCase):
    def test_sources_and_coverage_table_shape(self) -> None:
        hub = DataHub(json_getter=_fake_getter)
        self.assertIn("binance_futures", hub.sources())
        self.assertIn("frankfurter_fx", hub.sources())
        coverage = hub.coverage_table()
        self.assertGreater(len(coverage), 5)
        for key in (
            "Source",
            "Asset discovery",
            "Kline/OHLCV",
            "Trades",
            "Orderbook",
            "Funding",
            "Equity",
            "ETF",
            "Forex",
            "Options",
            "Macro",
            "News",
            "Requires API key",
            "API key env",
        ):
            self.assertIn(key, coverage[0])

    def test_unsupported_dataset_reports_issue(self) -> None:
        hub = DataHub(json_getter=_fake_getter)
        result = hub.ingest(
            source="binance_futures",
            symbol="BTCUSDT",
            datasets=["news"],
            allow_partial=True,
        )
        self.assertEqual(result.dataset_coverage["news"], 0)
        self.assertIn("unsupported_dataset:news", {issue["reason"] for issue in result.source_issues})

    def test_ingest_normalizes_quality_storage_and_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            hub = DataHub(json_getter=_fake_getter, artifact_root=Path(tmp_dir))
            result = hub.ingest(
                source="binance_futures",
                symbol="BTCUSDT",
                datasets=["kline", "trade", "orderbook", "funding"],
            )
            self.assertGreater(len(result.records), 0)
            self.assertTrue(result.quality_report.passed)
            self.assertIsNotNone(result.provenance)
            self.assertGreater(len(result.storage_receipts), 0)
            self.assertTrue(Path(result.storage_receipts[0].location).exists())
            datasets = {record.metadata["dataset"] for record in result.records}
            self.assertIn("kline", datasets)
            self.assertIn("trade", datasets)
            self.assertIn("orderbook", datasets)
            self.assertIn("funding", datasets)

    def test_etl_shortcut_load_market_data(self) -> None:
        etl = ETL(DataHub(json_getter=_fake_getter))
        frame = etl.load_market_data(
            source="binance_futures",
            symbol="BTCUSDT",
            dataset="kline",
            limit=5,
        )
        if hasattr(frame, "columns"):
            self.assertIn("close", frame.columns)
        else:
            self.assertGreater(len(frame), 0)
            self.assertIn("close", frame[0])


if __name__ == "__main__":
    unittest.main()
