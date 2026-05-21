from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

from src.algotradeplan.orchestration.real_data_autopilot import run_real_data_autopilot


class RealDataAutopilotTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._tmp_dir = tempfile.TemporaryDirectory()
        cls._bridge = Path(cls._tmp_dir.name) / "market_data_bridge_stub.py"
        cls._bridge.write_text(
            textwrap.dedent(
                """
                import json
                import sys

                operation = sys.argv[1] if len(sys.argv) > 1 else ""
                payload = json.loads(sys.stdin.read() or "{}")
                source = payload.get("source", "")

                if operation == "sources":
                    out = ["binance_futures", "offline_fallback"]
                elif operation == "coverage_table":
                    out = [{"Source": "binance_futures", "OHLCV/Kline": "live"}]
                elif operation == "capability":
                    out = {
                        "source": source,
                        "datasets": ["tick", "kline", "trade", "orderbook", "funding", "news", "macro"],
                        "asset_classes": ["crypto_perpetual", "macro"],
                        "supports_discovery": True,
                    }
                elif operation == "discover_assets":
                    if source == "hacker_news":
                        out = ["BITCOIN"]
                    elif source == "frankfurter_fx":
                        out = ["USD"]
                    else:
                        out = ["BTCUSDT", "ETHUSDT"]
                elif operation == "ingest":
                    requested = payload.get("datasets", [])
                    symbol = payload.get("symbol", "BTCUSDT")
                    records = []
                    coverage = {}
                    normalized = {}
                    for dataset in requested:
                        coverage[dataset] = 1
                        normalized[dataset] = [{"dataset": dataset}]
                        row = {
                            "key": f"{dataset}-1",
                            "observed_at": "2026-01-01T00:00:00Z",
                            "domain": "market",
                            "source": source,
                            "asset_type": "crypto_perpetual",
                            "payload": {"close": 100.0, "dataset": dataset, "rates": {"EUR": 0.9}},
                            "metadata": {"dataset": dataset},
                        }
                        if dataset == "news":
                            row["payload"] = {"title": "Bitcoin market update"}
                        if dataset == "macro":
                            row["payload"] = {"rates": {"EUR": 0.9}}
                        records.append(row)
                    out = {
                        "source": source,
                        "symbol": symbol,
                        "requested_datasets": requested,
                        "dataset_coverage": coverage,
                        "normalized": normalized,
                        "records": records,
                        "quality_report": {"passed": True, "checks": ["records_present"], "issues": []},
                        "storage_receipts": [],
                        "provenance": {
                            "request": {"dataset": ",".join(requested), "symbol": symbol, "parameters": {}},
                            "source_plugin_id": source,
                            "storage_receipts": [],
                            "record_keys": [item["key"] for item in records],
                            "revision": "rev-1",
                        },
                        "source_issues": [],
                    }
                else:
                    out = []

                print(json.dumps(out))
                """
            ).strip()
            + "\n",
            encoding="utf-8",
        )

    @classmethod
    def tearDownClass(cls) -> None:
        cls._tmp_dir.cleanup()

    def test_pipeline_report_contains_expected_coverage(self) -> None:
        env = dict(os.environ)
        env["MARKET_DATA_BIN"] = f"{sys.executable} {self._bridge}"
        with tempfile.TemporaryDirectory() as tmp_dir:
            report_path = Path(tmp_dir) / "report.json"
            previous = os.environ.get("MARKET_DATA_BIN")
            os.environ["MARKET_DATA_BIN"] = env["MARKET_DATA_BIN"]
            try:
                report = run_real_data_autopilot(report_path=report_path, max_symbols_per_source=2)
            finally:
                if previous is None:
                    os.environ.pop("MARKET_DATA_BIN", None)
                else:
                    os.environ["MARKET_DATA_BIN"] = previous

            self.assertGreaterEqual(len(report.market_sources), 1)
            self.assertGreater(report.news_story_count, 0)
            self.assertGreater(report.macro_series_count, 0)
            self.assertIn("source_issue_count", report.metrics)
            self.assertIn("binance_futures", report.source_inventory)
            self.assertTrue(report.data_quality["passed"])
            stored = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertIn("coverage_table", stored)


if __name__ == "__main__":
    unittest.main()
