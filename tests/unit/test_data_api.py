from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.algotradeplan.data import DataHub, ETL
from src.algotradeplan.data.quality import CanonicalDataQualityPlugin
from src.algotradeplan.data.normalize import normalize_dataset
from src.algotradeplan.plugins.data.contracts import DataRecord
from scripts.generate_data_coverage_doc import generate as generate_data_coverage_doc


def _klines(length: int = 10) -> list[list[object]]:
    return [
        [
            1_700_000_000_000 + (row_index * 60_000),
            "100",
            str(101 + row_index),
            "99",
            str(100 + row_index),
            "10",
        ]
        for row_index in range(length)
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


def _api_key_getter(url: str, params: dict[str, object]):
    if url == "https://www.alphavantage.co/query":
        function = params.get("function")
        if function == "TIME_SERIES_INTRADAY":
            return {
                "Time Series (1min)": {
                    "2025-01-02 10:00:00": {
                        "1. open": "100",
                        "2. high": "101",
                        "3. low": "99",
                        "4. close": "100.5",
                    }
                }
            }
        if function == "TIME_SERIES_DAILY":
            return {
                "Time Series (Daily)": {
                    "2025-01-02": {
                        "1. open": "100",
                        "2. high": "101",
                        "3. low": "99",
                        "4. close": "100.5",
                    }
                }
            }
        if function == "GLOBAL_QUOTE":
            return {"Global Quote": {"01. symbol": "IBM", "05. price": "100.5", "07. latest trading day": "2025-01-02"}}
        if function == "OVERVIEW":
            return {"Symbol": "IBM", "Name": "IBM", "MarketCapitalization": "1000"}
    if url.startswith("https://api.polygon.io/v2/aggs/ticker/"):
        return {"results": [{"t": 1_700_000_000_000, "o": 100, "h": 101, "l": 99, "c": 100.5}]}
    if url == "https://api.polygon.io/v2/reference/news":
        return {"results": [{"title": "Polygon news", "url": "https://example.com/polygon-news", "published_at": "2025-01-02"}]}
    if url == "https://api.polygon.io/v3/reference/splits":
        return {"results": [{"execution_date": "2025-01-02", "type": "split", "ticker": "AAPL"}]}
    if url == "https://finnhub.io/api/v1/quote":
        return {"symbol": "AAPL", "c": 189.5, "t": 1_700_000_000}
    if url == "https://finnhub.io/api/v1/stock/candle":
        return {"c": [189.5], "h": [190.0], "l": [188.0], "o": [189.0], "t": [1_700_000_000]}
    if url == "https://finnhub.io/api/v1/company-news":
        return [{"headline": "Finnhub news", "url": "https://example.com/finnhub-news", "datetime": 1_700_000_000}]
    if url == "https://finnhub.io/api/v1/stock/profile2":
        return {"ticker": "AAPL", "name": "Apple Inc"}
    if url.startswith("https://data.nasdaq.com/api/v3/datasets/CHRIS/CME_"):
        return {"dataset": {"database_code": "CHRIS", "data": [["2025-01-02", 100, 101, 99, 100.5]]}}
    if url.startswith("https://cloud.iexapis.com/stable/stock/") and url.endswith("/quote"):
        return {"symbol": "AAPL", "latestPrice": 190, "price": 190, "latestUpdate": 1_700_000_000_000}
    if url.startswith("https://cloud.iexapis.com/stable/stock/") and url.endswith("/chart/1d"):
        return [{"date": "2025-01-02", "minute": "10:00", "open": 100, "high": 101, "low": 99, "close": 100.5}]
    if url.startswith("https://cloud.iexapis.com/stable/stock/") and "/news/last/5" in url:
        return [{"headline": "IEX news", "url": "https://example.com/iex-news", "datetime": 1_700_000_000_000}]
    if url.startswith("https://cloud.iexapis.com/stable/stock/") and url.endswith("/dividends/1y"):
        return [{"exDate": "2025-01-02", "type": "dividend", "amount": 0.1}]
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
        self.assertEqual(
            hub.available_datasets("polygon_io", implemented_only=True),
            ["corporate_actions", "kline", "news", "tick", "trade"],
        )
        comparison = hub.compare_sources(["binance_futures", "coingecko", "stooq", "world_bank"], ["kline", "news", "macro"])
        self.assertEqual(comparison[0]["source"], "binance_futures")
        self.assertEqual(comparison[1]["kline"], "partial")
        self.assertEqual(comparison[2]["news"], "unsupported")
        summary = hub.source_summary("coingecko")
        self.assertTrue(summary["extra_metadata"]["kline"]["synthetic_ohlcv"])
        self.assertIn("note", summary["extra_metadata"]["kline"])
        self.assertEqual(summary["dataset_statuses"]["news"], "metadata_only")
        best = hub.best_sources_for(dataset="kline", asset_class="crypto_spot", allow_api_key=False, limit=5)
        self.assertGreater(len(best), 0)
        self.assertEqual(best[0]["requires_api_key"], "no")
        with self.assertRaisesRegex(ValueError, "non-negative"):
            hub.best_sources_for(dataset="kline", limit=-1)
        source_explain = hub.explain_source("coingecko")
        self.assertEqual(source_explain["source"], "coingecko")
        self.assertIn("dataset_rankings", source_explain)
        dataset_explain = hub.explain_dataset("funding")
        self.assertEqual(dataset_explain["dataset"], "funding")
        self.assertIn("best_sources_no_api_key", dataset_explain)
        recommendations = hub.recommend_sources("crypto_spot_kline", allow_api_key=False, limit=5)
        self.assertGreater(len(recommendations), 0)
        self.assertTrue(all(item["requires_api_key"] == "no" for item in recommendations))
        self.assertEqual(recommendations[0]["use_case"], "crypto_spot_kline")
        funding_recommendations = hub.recommend_sources("crypto_perp_funding", allow_api_key=False)
        self.assertIn("binance_futures", [item["source"] for item in funding_recommendations])
        self.assertIn("bybit_linear", [item["source"] for item in funding_recommendations])
        macro_recommendations = hub.recommend_sources("macro_indicators", allow_api_key=False)
        self.assertTrue({"world_bank", "ecb", "frankfurter_fx"}.issubset({item["source"] for item in macro_recommendations}))
        with self.assertRaisesRegex(ValueError, "Unknown use_case"):
            hub.recommend_sources("unknown_case")

    def test_dataset_and_asset_sources_matrix(self) -> None:
        hub = DataHub(json_getter=_fake_getter)
        dataset_matrix = hub.dataset_sources_matrix(["kline", "news"])
        self.assertGreater(len(dataset_matrix), 0)
        self.assertIn("kline", dataset_matrix[0])
        self.assertIn("news", dataset_matrix[0])
        asset_matrix = hub.asset_sources_matrix(["crypto_spot", "macro"])
        self.assertGreater(len(asset_matrix), 0)
        self.assertIn("crypto_spot", asset_matrix[0])
        self.assertIn("macro", asset_matrix[0])

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

    def test_api_key_required_dataset_reports_issue_without_fetch(self) -> None:
        def raising_getter(url: str, params: dict[str, object]):  # pragma: no cover - should never run
            raise AssertionError(f"unexpected fetch: {url} {params}")

        hub = DataHub(json_getter=raising_getter)
        scenarios = [
            ("alpha_vantage", "IBM", ["kline"], "ALPHAVANTAGE_API_KEY"),
            ("finnhub", "AAPL", ["news"], "FINNHUB_API_KEY"),
            ("polygon_io", "AAPL", ["news"], "POLYGON_API_KEY"),
            ("iex_cloud", "AAPL", ["corporate_actions"], "IEX_CLOUD_API_KEY"),
            ("quandl", "ES", ["macro"], "QUANDL_API_KEY"),
        ]
        for source, symbol, datasets, env_name in scenarios:
            with self.subTest(source=source):
                result = hub.ingest(
                    source=source,
                    symbol=symbol,
                    datasets=datasets,
                    allow_partial=True,
                    store=False,
                )
                self.assertEqual(result.dataset_coverage[datasets[0]], 0)
                self.assertIn(f"api_key_required:{env_name}", {issue["reason"] for issue in result.source_issues})

    def test_api_key_adapters_fetch_minimal_supported_datasets_when_key_present(self) -> None:
        env = {
            "ALPHAVANTAGE_API_KEY": "test-alpha",
            "FINNHUB_API_KEY": "test-finnhub",
            "POLYGON_API_KEY": "test-polygon",
            "IEX_CLOUD_API_KEY": "test-iex",
            "QUANDL_API_KEY": "test-quandl",
        }
        with patch.dict(os.environ, env, clear=False):
            hub = DataHub(json_getter=_api_key_getter)
            alpha = hub.ingest(source="alpha_vantage", symbol="IBM", datasets=["tick", "kline", "fundamentals"], allow_partial=True, store=False)
            finnhub = hub.ingest(source="finnhub", symbol="AAPL", datasets=["news", "fundamentals"], allow_partial=True, store=False)
            polygon = hub.ingest(source="polygon_io", symbol="AAPL", datasets=["news", "corporate_actions"], allow_partial=True, store=False)
            iex = hub.ingest(source="iex_cloud", symbol="AAPL", datasets=["news", "corporate_actions"], allow_partial=True, store=False)
            quandl = hub.ingest(source="quandl", symbol="ES", datasets=["kline", "macro"], allow_partial=True, store=False)

        self.assertEqual(alpha.dataset_coverage["tick"], 1)
        self.assertEqual(alpha.dataset_coverage["fundamentals"], 1)
        self.assertEqual(finnhub.dataset_coverage["news"], 1)
        self.assertEqual(finnhub.dataset_coverage["fundamentals"], 1)
        self.assertEqual(polygon.dataset_coverage["news"], 1)
        self.assertEqual(polygon.dataset_coverage["corporate_actions"], 1)
        self.assertEqual(iex.dataset_coverage["news"], 1)
        self.assertEqual(iex.dataset_coverage["corporate_actions"], 1)
        self.assertEqual(quandl.dataset_coverage["kline"], 1)
        self.assertEqual(quandl.dataset_coverage["macro"], 1)

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
            recommendations_path = Path(tmp_dir) / "source_recommendations.md"
            content = generate_data_coverage_doc(path, source_recommendations_path=recommendations_path)
            self.assertIn("Data Source Coverage", content)
            self.assertIn("## Dataset → Sources index", content)
            self.assertIn("## Asset class → Sources index", content)
            self.assertIn("## Recommended Sources by Use Case", content)
            self.assertIn("API key env", content)
            self.assertIn("## Live fetch sources", content)
            self.assertIn("## Public / no-key providers", content)
            self.assertIn("## API-key providers", content)
            self.assertIn("## Metadata-only sources", content)
            self.assertIn("## Fallback / offline providers", content)
            self.assertTrue(path.exists())
            self.assertTrue(recommendations_path.exists())
            self.assertGreater(path.stat().st_size, 100)

    def test_quality_checks_ohlc_duplicate_and_negative_values(self) -> None:
        quality = CanonicalDataQualityPlugin()
        records = [
            DataRecord(
                key="k1",
                observed_at="2024-01-01T00:00:00+00:00",
                domain="market",
                source="test",
                asset_type="crypto_spot",
                payload={"timestamp_ms": 1_700_000_000_000, "open": 100, "high": 90, "low": 101, "close": 98, "volume": -1},
                metadata={"dataset": "kline", "join_key": "BTCUSDT"},
            ),
            DataRecord(
                key="k2",
                observed_at="2024-01-01T00:01:00+00:00",
                domain="market",
                source="test",
                asset_type="crypto_spot",
                payload={"timestamp_ms": 1_700_000_000_000, "open": 99, "high": 100, "low": 98, "close": 99, "volume": 1},
                metadata={"dataset": "kline", "join_key": "BTCUSDT"},
            ),
        ]
        report = quality.validate(records)
        self.assertFalse(report.passed)
        issues_text = " ".join(report.issues)
        self.assertIn("Inconsistent OHLC high", issues_text)
        self.assertIn("Inconsistent OHLC low", issues_text)
        self.assertIn("Inconsistent OHLC range", issues_text)
        self.assertIn("Negative volume", issues_text)
        self.assertIn("Duplicate timestamp", issues_text)


if __name__ == "__main__":
    unittest.main()
