from __future__ import annotations

import unittest

from src.algotradeplan.backtest import ReplayHarness
from src.algotradeplan.plugins.data.contracts import DataRecord, DataRequest
from src.algotradeplan.plugins.data.example_data_storage import InMemoryDataStoragePlugin
from src.algotradeplan.plugins.data.example_provenance import ExampleProvenancePlugin
from src.algotradeplan.plugins.data.example_quality_check import RequiredFieldsQualityPlugin
from src.algotradeplan.plugins.data.market.example_market_source import ExampleMarketDataSource
from src.algotradeplan.plugins.data.pipeline import DataIngestionPipeline


class _DriftingSource:
    plugin_id = "drifting_source"
    domain = "market"

    def fetch(self, request: DataRequest) -> list[DataRecord]:
        return [
            DataRecord(
                key="drift",
                observed_at="2026-01-01T00:00:00Z",
                domain=self.domain,
                source="drift",
                asset_type="equity",
                payload={"symbol": request.symbol or "X", "close": 999.0},
                metadata={"join_key": request.symbol or "X"},
            )
        ]


class ReplayHarnessTest(unittest.TestCase):
    def setUp(self) -> None:
        self.pipeline = DataIngestionPipeline(
            source=ExampleMarketDataSource(),
            storage=InMemoryDataStoragePlugin(),
            quality=RequiredFieldsQualityPlugin(),
            provenance=ExampleProvenancePlugin(),
        )
        self.result = self.pipeline.ingest(DataRequest(dataset="daily_bars", symbol="AAPL"))

    def test_parity_succeeds_against_deterministic_source(self) -> None:
        harness = ReplayHarness(ExampleMarketDataSource())
        replay = harness.replay(self.result.provenance, self.result.records)
        self.assertTrue(replay.parity)
        promotion = harness.promote(replay)
        self.assertTrue(promotion["promoted"])
        self.assertEqual(promotion["revision"], self.result.provenance.revision)

    def test_parity_failure_blocks_promotion(self) -> None:
        harness = ReplayHarness(_DriftingSource())
        replay = harness.replay(self.result.provenance, self.result.records)
        self.assertFalse(replay.parity)
        with self.assertRaisesRegex(ValueError, "Replay parity check failed"):
            harness.promote(replay)


if __name__ == "__main__":
    unittest.main()
