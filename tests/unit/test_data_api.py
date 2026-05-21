from __future__ import annotations

import json
import subprocess
import unittest

from src.algotradeplan.data import DataHub, ETL
from src.algotradeplan.marketdata_client import MarketDataBridgeClient, MarketDataBridgeError


class _Runner:
    def __call__(self, command, *, input, capture_output, text, check):
        operation = command[1]
        payload = json.loads(input)
        responses = {
            "sources": ["offline_fallback", "coingecko"],
            "capability": {
                "source": payload.get("source", "offline_fallback"),
                "asset_classes": ["crypto_spot"],
                "datasets": ["kline", "funding"],
                "supports_discovery": True,
                "supports_history": True,
            },
            "supported_use_cases": ["offline_demo"],
            "recommend_sources": [
                {
                    "source": "offline_fallback",
                    "dataset_status": "fallback",
                    "asset_status": "fallback",
                    "requires_api_key": "no",
                    "reason": "offline-safe",
                }
            ],
            "discover_assets": ["BTCUSDT", "ETHUSDT"],
            "ingest": {
                "source": payload.get("source", "offline_fallback"),
                "symbol": payload.get("symbol", "BTCUSDT"),
                "requested_datasets": payload.get("datasets", []),
                "dataset_coverage": {"kline": 1},
                "records": [
                    {
                        "key": "k1",
                        "observed_at": "2026-01-01T00:00:00Z",
                        "domain": "market",
                        "source": payload.get("source", "offline_fallback"),
                        "asset_type": "crypto_spot",
                        "payload": {"close": 100.0},
                        "metadata": {"dataset": "kline"},
                    }
                ],
                "quality_report": {"passed": True, "checks": ["records_present"], "issues": []},
            },
            "load_market_data": [{"close": 100.0}],
        }
        body = responses.get(operation, [])
        return subprocess.CompletedProcess(command, 0, stdout=json.dumps(body), stderr="")


class DataHubShimTest(unittest.TestCase):
    def setUp(self) -> None:
        self.hub = DataHub(client=MarketDataBridgeClient(runner=_Runner()))

    def test_sources_and_recommendation_delegate_to_marketdata(self) -> None:
        self.assertIn("offline_fallback", self.hub.sources())
        recommendations = self.hub.recommend_sources("offline_demo", allow_api_key=False)
        self.assertEqual(recommendations[0]["source"], "offline_fallback")

    def test_ingest_and_load_delegate_to_marketdata(self) -> None:
        result = self.hub.ingest(source="offline_fallback", symbol="BTCUSDT", datasets=["kline"], store=False)
        self.assertTrue(result.quality_report.passed)
        self.assertEqual(result.records[0].metadata["dataset"], "kline")
        loaded = self.hub.load_market_data(source="offline_fallback", symbol="BTCUSDT", dataset="kline")
        self.assertEqual(loaded[0]["close"], 100.0)

    def test_etl_uses_hub_delegate(self) -> None:
        etl = ETL(self.hub)
        rows = (
            etl.source("offline_fallback")
            .discover_assets(limit=1)
            .select_assets(limit=1)
            .fetch(["kline"], allow_partial=True)
            .to_feature_frame()
        )
        self.assertTrue(len(rows) >= 1)

    def test_missing_bridge_for_ingest_raises(self) -> None:
        hub = DataHub(client=MarketDataBridgeClient(bridge_bin="/nonexistent/market_data_bridge"))
        with self.assertRaises(MarketDataBridgeError):
            hub.ingest(source="offline_fallback", symbol="BTCUSDT", datasets=["kline"], store=False)

    def test_ingest_handles_malformed_bridge_response(self) -> None:
        class _MalformedRunner:
            def __call__(self, command, *, input, capture_output, text, check):
                operation = command[1]
                body = [] if operation == "ingest" else []
                return subprocess.CompletedProcess(command, 0, stdout=json.dumps(body), stderr="")

        hub = DataHub(client=MarketDataBridgeClient(runner=_MalformedRunner()))
        result = hub.ingest(source="offline_fallback", symbol="BTCUSDT", datasets=["kline"], store=False)
        self.assertEqual(result.records, [])
        self.assertFalse(result.quality_report.passed)


if __name__ == "__main__":
    unittest.main()
