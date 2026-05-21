from __future__ import annotations

import unittest

from src.algotradeplan.backtest import ReplayHarness
from src.algotradeplan.plugins.data.contracts import DataRecord, DataRequest, ProvenanceRecord


class _DeterministicSource:
    def fetch(self, request: DataRequest) -> list[DataRecord]:
        symbol = request.symbol or "X"
        return [
            DataRecord(
                key="k1",
                observed_at="2026-01-01T00:00:00Z",
                domain="market",
                source="stub",
                asset_type="equity",
                payload={"symbol": symbol, "close": 10.0},
                metadata={"join_key": symbol},
            )
        ]


class _DriftingSource:
    def fetch(self, request: DataRequest) -> list[DataRecord]:
        symbol = request.symbol or "X"
        return [
            DataRecord(
                key="k1",
                observed_at="2026-01-01T00:00:00Z",
                domain="market",
                source="stub",
                asset_type="equity",
                payload={"symbol": symbol, "close": 999.0},
                metadata={"join_key": symbol},
            )
        ]


class ReplayHarnessTest(unittest.TestCase):
    def setUp(self) -> None:
        self.request = DataRequest(dataset="daily_bars", symbol="AAPL")
        self.records = _DeterministicSource().fetch(self.request)
        self.provenance = ProvenanceRecord(
            request=self.request,
            source_plugin_id="stub",
            storage_receipts=[],
            record_keys=[item.key for item in self.records],
            revision="rev-1",
        )

    def test_parity_succeeds_against_deterministic_source(self) -> None:
        harness = ReplayHarness(_DeterministicSource())
        replay = harness.replay(self.provenance, self.records)
        self.assertTrue(replay.parity)
        promotion = harness.promote(replay)
        self.assertTrue(promotion["promoted"])
        self.assertEqual(promotion["revision"], self.provenance.revision)

    def test_parity_failure_blocks_promotion(self) -> None:
        harness = ReplayHarness(_DriftingSource())
        replay = harness.replay(self.provenance, self.records)
        self.assertFalse(replay.parity)
        with self.assertRaisesRegex(ValueError, "Replay parity check failed"):
            harness.promote(replay)


if __name__ == "__main__":
    unittest.main()
