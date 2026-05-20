from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.algotradeplan.data import DataHub, ETL
from src.algotradeplan.data.normalize import normalize_dataset
from scripts.generate_data_coverage_doc import generate as generate_data_coverage_doc


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
        self.assertIn("sec_edgar", hub.sources())
        coverage = hub.coverage_table()
        self.assertGreater(len(coverage), 5)
        for key in (
            "Source",
            "Asset classes",
            "Asset discovery",
            "Ticker",
            "OHLCV/Kline",
            "Kline/OHLCV",
            "Trades",
            "Orderbook",
            "Funding",
            "Equity",
            "ETF",
            "Forex",
            "Index",
            "Futures",
            "Options",
            "Macro",
            "News",
            "Fundamentals",
            "Corporate actions",
            "Requires API key",
            "API key env",
            "Implementation status",
            "Notes",
        ):
            self.assertIn(key, coverage[0])
        statuses = {row["Implementation status"] for row in coverage}
        self.assertTrue(statuses.issubset({"live", "partial", "api_key", "api_key_or_plan", "metadata_only", "fallback"}))

    def test_capability_query_api(self) -> None:
        hub = DataHub(json_getter=_fake_getter)
        self.assertEqual(hub.dataset_status("coingecko", "kline"), "partial")
        self.assertEqual(hub.dataset_status("coingecko", "orderbook"), "unsupported")
        self.assertTrue(hub.supports("binance_futures", "funding", require_live=True))
        self.assertIn("gdelt", hub.sources_for(dataset="news", require_live=True))
        self.assertIn("world_bank", hub.sources_for(asset_class="macro"))
        self.assertEqual(hub.available_datasets("polygon_io", implemented_only=True), ["kline", "tick", "trade"])
        comparison = hub.compare_sources(["binance_futures", "coingecko", "stooq", "world_bank"], ["kline", "news", "macro"])
        self.assertEqual(comparison[0]["source"], "binance_futures")
        self.assertEqual(comparison[1]["kline"], "partial")
        self.assertEqual(comparison[2]["news"], "unsupported")
        summary = hub.source_summary("coingecko")
        self.assertTrue(summary["extra_metadata"]["kline"]["synthetic_ohlcv"])
        self.assertEqual(summary["dataset_statuses"]["news"], "metadata_only")

    def test_unsupported_dataset_reports_issue_without_fetch(self) -> None:
        def raising_getter(url: str, params: dict[str, object]):  # pragma: no cover - should never run
            raise AssertionError(f"unexpected fetch: {url} {params}")

        hub = DataHub(json_getter=raising_getter)
        result = hub.ingest(
            source="coingecko",
            symbol="bitcoin",
            datasets=["orderbook"],
            allow_partial=True,
            store=False,
        )
        self.assertEqual(result.dataset_coverage["orderbook"], 0)
        self.assertIn("unsupported_dataset:orderbook", {issue["reason"] for issue in result.source_issues})

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

    def test_coingecko_adapter_discovery_and_fetch_marks_synthetic_ohlcv(self) -> None:
        def fake_getter(url: str, params: dict[str, object]):
            if url.endswith("/coins/markets") and params.get("ids"):
                return [{"id": "bitcoin", "current_price": 70000}]
            if url.endswith("/coins/markets"):
                return [{"id": "bitcoin"}, {"id": "ethereum"}]
            if "/market_chart" in url:
                return {"prices": [[1_700_000_000_000, 70000]], "total_volumes": [[1_700_000_000_000, 1_000_000]]}
            raise AssertionError(f"Unexpected URL: {url}")

        hub = DataHub(json_getter=fake_getter)
        assets = hub.discover_assets("coingecko", limit=2)
        self.assertEqual(assets[0], "bitcoin")
        result = hub.ingest(source="coingecko", symbol="bitcoin", datasets=["tick", "kline"], allow_partial=True, store=False)
        self.assertGreater(result.dataset_coverage["kline"], 0)
        self.assertTrue(result.normalized["kline"][0]["metadata"]["synthetic_ohlcv"])

    def test_macro_and_news_normalization_from_new_sources(self) -> None:
        gdelt = normalize_dataset("news", "gdelt", "bitcoin", [{"title": "BTC", "url": "u", "created_at": "2025-01-01"}])
        world_bank = normalize_dataset("macro", "world_bank", "NY.GDP.MKTP.CD", {"base": "GDP", "date": "2024", "rates": {"2024": 1.0}})
        ecb = normalize_dataset("macro", "ecb", "EUR", {"base": "EUR", "date": "2024-01-01", "rates": {"USD": 1.08}})
        actions = normalize_dataset("corporate_actions", "sec_edgar", "AAPL", [{"form": "8-K", "filed_at": "2024-01-01"}])
        self.assertEqual(len(gdelt), 1)
        self.assertEqual(len(world_bank), 1)
        self.assertEqual(len(ecb), 1)
        self.assertEqual(actions[0]["action"], "8-K")

    def test_stooq_timestamp_parsing(self) -> None:
        def fake_getter(url: str, params: dict[str, object]):
            self.assertEqual(url, "https://stooq.com/q/l/")
            return {"data": [{"date": "2024-05-10", "time": "15:30:00", "open": "1", "high": "2", "low": "0.5", "close": "1.5", "volume": "10"}]}

        hub = DataHub(json_getter=fake_getter)
        result = hub.ingest(source="stooq", symbol="aapl.us", datasets=["kline"], allow_partial=True, store=False)
        self.assertEqual(result.normalized["kline"][0]["timestamp_ms"], 1715355000000)

    def test_ecb_dynamic_symbol(self) -> None:
        seen: list[str] = []

        def fake_getter(url: str, params: dict[str, object]):
            seen.append(url)
            return {"dataSets": [{"series": {"0:0:0:0:0": {"observations": {"0": [1.08], "1": [1.07]}}}}]}

        hub = DataHub(json_getter=fake_getter)
        result = hub.ingest(source="ecb", symbol="GBP", datasets=["tick", "macro"], allow_partial=True, store=False)
        self.assertIn("EXR/D.GBP.EUR.SP00.A", seen[0])
        self.assertEqual(result.dataset_coverage["tick"], 1)
        self.assertEqual(result.dataset_coverage["macro"], 1)

    def test_world_bank_country_param(self) -> None:
        seen: list[str] = []

        def fake_getter(url: str, params: dict[str, object]):
            seen.append(url)
            return [{}, [{"date": "2024", "value": 1.5}, {"date": "2023", "value": 1.4}]]

        hub = DataHub(json_getter=fake_getter)
        result = hub.ingest(
            source="world_bank",
            symbol="NY.GDP.MKTP.CD",
            datasets=["macro"],
            allow_partial=True,
            store=False,
            country="TUR",
        )
        self.assertIn("/country/TUR/indicator/NY.GDP.MKTP.CD", seen[0])
        self.assertEqual(result.normalized["macro"][0]["metadata"]["raw"]["country"], "TUR")

    def test_generate_data_source_coverage_doc(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "coverage.md"
            content = generate_data_coverage_doc(path)
            self.assertIn("Data Source Coverage", content)
            self.assertIn("## Dataset → Sources index", content)
            self.assertIn("## Live fetch sources", content)
            self.assertIn("## API-key required sources", content)
            self.assertIn("## Metadata-only sources", content)
            self.assertIn("## Fallback sources", content)
            self.assertTrue(path.exists())
            self.assertGreater(path.stat().st_size, 100)


if __name__ == "__main__":
    unittest.main()
