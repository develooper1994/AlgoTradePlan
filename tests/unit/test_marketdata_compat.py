from __future__ import annotations

import unittest

from src.marketdata import DataHub, ETL, SourceCapability
from src.marketdata.contracts import DataRecord, DataRequest, ProvenanceRecord, QualityReport, StorageReceipt


class MarketDataCompatTest(unittest.TestCase):
    def test_top_level_exports(self) -> None:
        hub = DataHub()
        etl = ETL(hub)
        self.assertIsInstance(hub, DataHub)
        self.assertIsInstance(etl, ETL)
        self.assertTrue(issubclass(SourceCapability, object))

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


if __name__ == "__main__":
    unittest.main()
