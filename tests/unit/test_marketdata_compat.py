from __future__ import annotations

import unittest

from src.marketdata import DataHub, ETL, SourceCapability
from src.marketdata.contracts import DataRecord, DataRequest, ProvenanceRecord, QualityReport, StorageReceipt
from src.marketdata.curated import ExampleFeatureViewPlugin, FeatureViewResult
from src.marketdata.ingestion import IngestResult
from src.marketdata.providers import (
    DataAdapterRegistry,
    DataSourceAdapter,
    MarketSourceAdapter,
    MarketSourceIssue,
    MarketSourceResult,
    build_market_source_registry,
)


def _fake_getter(url: str, params: dict[str, object]):
    if url.endswith("/fapi/v1/exchangeInfo"):
        return {"symbols": [{"symbol": "BTCUSDT", "status": "TRADING", "quoteAsset": "USDT"}]}
    if url.endswith("/fapi/v1/ticker/price"):
        return {"symbol": params["symbol"], "price": "105"}
    if url.endswith("/fapi/v1/klines"):
        return [[1_700_000_000_000, "100", "101", "99", "100", "10"]]
    if url.endswith("/fapi/v1/trades"):
        return [{"id": 1, "price": "105", "qty": "0.25", "time": 1_700_000_000_001}]
    if url.endswith("/fapi/v1/depth"):
        return {"bids": [["100", "1"]], "asks": [["101", "1"]]}
    if url.endswith("/fapi/v1/fundingRate"):
        return [{"fundingRate": "0.0001", "fundingTime": 1_700_000_000_002}]
    raise AssertionError(f"Unexpected URL: {url}")


class MarketDataCompatTest(unittest.TestCase):
    def test_top_level_exports(self) -> None:
        hub = DataHub(json_getter=_fake_getter)
        etl = ETL(hub)
        self.assertIsInstance(hub, DataHub)
        self.assertIsInstance(etl, ETL)
        self.assertTrue(issubclass(SourceCapability, object))
        self.assertTrue(issubclass(IngestResult, object))

    def test_contract_exports(self) -> None:
        request = DataRequest(dataset="kline", symbol="BTCUSDT")
        record = DataRecord(
            key="k",
            observed_at="2026-01-01T00:00:00Z",
            domain="market",
            source="offline_fallback",
            asset_type="crypto_perpetual",
            payload={"close": 100.0},
        )
        quality = QualityReport(passed=True, checks=["records_present"])
        receipt = StorageReceipt(storage_id="1", location="memory://1", record_keys=["k"])
        provenance = ProvenanceRecord(
            request=request,
            source_plugin_id="offline_fallback",
            storage_receipts=[receipt],
            record_keys=["k"],
            revision="rev-1",
        )
        self.assertEqual(request.symbol, "BTCUSDT")
        self.assertEqual(record.key, "k")
        self.assertTrue(quality.passed)
        self.assertEqual(receipt.storage_id, "1")
        self.assertEqual(provenance.revision, "rev-1")

    def test_datahub_ingest_parity_smoke(self) -> None:
        hub = DataHub(json_getter=_fake_getter)
        result = hub.ingest(
            source="binance_futures",
            symbol="BTCUSDT",
            datasets=["kline", "trade", "orderbook", "funding"],
            store=False,
            allow_partial=True,
        )
        self.assertGreater(len(result.records), 0)
        self.assertTrue(result.quality_report.passed)
        self.assertEqual(result.dataset_coverage["kline"], 1)
        self.assertEqual(result.dataset_coverage["trade"], 1)
        self.assertEqual(result.dataset_coverage["orderbook"], 1)
        self.assertEqual(result.dataset_coverage["funding"], 1)

    def test_provider_exports(self) -> None:
        self.assertTrue(issubclass(DataAdapterRegistry, object))
        self.assertTrue(hasattr(DataSourceAdapter, "__class__"))
        self.assertTrue(issubclass(MarketSourceAdapter, object))
        self.assertTrue(issubclass(MarketSourceResult, object))
        self.assertTrue(issubclass(MarketSourceIssue, object))
        self.assertGreater(len(build_market_source_registry()), 0)

    def test_curated_exports(self) -> None:
        self.assertTrue(issubclass(FeatureViewResult, object))
        self.assertTrue(issubclass(ExampleFeatureViewPlugin, object))


if __name__ == "__main__":
    unittest.main()
