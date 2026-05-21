"""Tests for the unified ``python -m algotradeplan`` CLI entry point."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


class CLIEntryPointTest(unittest.TestCase):
    """Test that ``python -m src.algotradeplan`` subcommands work correctly."""

    @classmethod
    def setUpClass(cls) -> None:
        cls._tmp_dir = tempfile.TemporaryDirectory()
        cls._bridge_path = Path(cls._tmp_dir.name) / "market_data_bridge_stub.py"
        cls._bridge_path.write_text(
            textwrap.dedent(
                """
                import json
                import sys

                operation = sys.argv[1] if len(sys.argv) > 1 else ""
                payload = {}
                try:
                    payload = json.loads(sys.stdin.read() or "{}")
                except json.JSONDecodeError:
                    payload = {}

                source = payload.get("source", "offline_fallback")
                if operation == "supported_use_cases":
                    out = ["crypto_spot_kline", "tefas_fund_screener", "offline_demo"]
                elif operation == "recommend_sources":
                    use_case = payload.get("use_case", "")
                    source_name = "tefas_public" if use_case == "tefas_fund_screener" else "offline_fallback"
                    out = [{"source": source_name, "dataset": "kline", "dataset_status": "fallback", "asset_status": "fallback", "requires_api_key": "no", "reason": "offline-safe"}]
                elif operation == "dataset_status":
                    dataset = payload.get("dataset", "")
                    out = "unsupported" if source == "coingecko" and dataset == "funding" else "fallback"
                elif operation == "source_summary":
                    out = {"source": source, "asset_classes": ["crypto_perpetual"], "extra_metadata": {}, "notes": "", "implementation_status": "fallback", "metadata_only_datasets": []}
                elif operation == "best_sources_for":
                    out = [{"source": "offline_fallback", "dataset": "kline", "dataset_status": "fallback", "asset_status": "fallback", "requires_api_key": "no", "reason": "offline-safe"}]
                elif operation == "explain_source":
                    out = {"source": source, "implementation_status": "fallback"}
                elif operation == "explain_dataset":
                    out = {"dataset": payload.get("dataset", ""), "sources": ["offline_fallback"]}
                elif operation == "sources":
                    out = ["offline_fallback", "coingecko"]
                elif operation == "coverage_table":
                    out = [{"Source": "offline_fallback", "OHLCV/Kline": "fallback"}]
                elif operation == "ingest":
                    out = {
                        "source": source,
                        "symbol": payload.get("symbol", "BTCUSDT"),
                        "requested_datasets": payload.get("datasets", []),
                        "dataset_coverage": {"kline": 1},
                        "records": [{"key": "k1", "observed_at": "2026-01-01T00:00:00Z", "domain": "market", "source": source, "asset_type": "crypto", "payload": {"close": 100.0}, "metadata": {"dataset": "kline"}}],
                        "quality_report": {"passed": True, "checks": ["records_present"], "issues": []},
                        "storage_receipts": [],
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

    def _run(self, *args: str) -> subprocess.CompletedProcess[str]:
        env = dict(os.environ)
        env["MARKET_DATA_BIN"] = sys.executable
        env["MARKET_DATA_BIN_ARGS"] = json.dumps([str(self._bridge_path)])
        return subprocess.run(
            [sys.executable, "-m", "src.algotradeplan", *args],
            capture_output=True,
            text=True,
            check=False,
            env=env,
        )

    def test_help_exits_zero(self) -> None:
        result = self._run("--help")
        self.assertEqual(result.returncode, 0)
        self.assertIn("status", result.stdout)
        self.assertIn("tutorial", result.stdout)
        self.assertIn("recommend", result.stdout)

    def test_no_subcommand_prints_help(self) -> None:
        result = self._run()
        self.assertEqual(result.returncode, 0)
        self.assertIn("subcommand", result.stdout)

    def test_status_compact(self) -> None:
        result = self._run("status")
        self.assertEqual(result.returncode, 0)
        self.assertIn("framework_score:", result.stdout)
        self.assertIn("sources:", result.stdout)

    def test_status_score_only(self) -> None:
        result = self._run("status", "--score")
        self.assertEqual(result.returncode, 0)
        self.assertIn("framework_score:", result.stdout)

    def test_status_next_actions(self) -> None:
        result = self._run("status", "--next-actions")
        self.assertEqual(result.returncode, 0)
        self.assertIn("[P0]", result.stdout)

    def test_status_json(self) -> None:
        result = self._run("status", "--json")
        self.assertEqual(result.returncode, 0)
        payload = json.loads(result.stdout)
        self.assertIn("framework_score", payload)
        self.assertIn("priority_actions", payload)

    def test_recommend_use_case(self) -> None:
        result = self._run("recommend", "--use-case", "crypto_spot_kline", "--no-api-key")
        self.assertEqual(result.returncode, 0)
        self.assertIn("crypto_spot_kline", result.stdout)

    def test_recommend_no_use_case_lists_cases(self) -> None:
        result = self._run("recommend")
        self.assertEqual(result.returncode, 0)
        self.assertIn("crypto_spot_kline", result.stdout)

    def test_recommend_json_output(self) -> None:
        result = self._run("recommend", "--use-case", "crypto_spot_kline", "--json")
        self.assertEqual(result.returncode, 0)
        payload = json.loads(result.stdout)
        self.assertIsInstance(payload, list)
        self.assertGreater(len(payload), 0)
        self.assertIn("source", payload[0])

    def test_recommend_tefas_use_case(self) -> None:
        result = self._run("recommend", "--use-case", "tefas_fund_screener", "--no-api-key")
        self.assertEqual(result.returncode, 0)
        self.assertIn("tefas_public", result.stdout)

    def test_preflight_offline(self) -> None:
        result = self._run(
            "preflight",
            "--source", "offline_fallback",
            "--symbol", "BTCUSDT",
            "--datasets", "kline", "funding",
            "--strategy", "ema_cross_atr_stop",
        )
        # offline_fallback with kline+funding should pass preflight
        self.assertEqual(result.returncode, 0)
        self.assertIn("can_run:", result.stdout)

    def test_doctor_exits_clean(self) -> None:
        result = self._run("doctor")
        # May have issues with missing artifacts in CI, but should not crash
        self.assertIn("AlgoTradePlan Doctor", result.stdout)
        self.assertIn("TEFAS integration", result.stdout)

    def test_examples_lists_use_cases_and_recipes(self) -> None:
        result = self._run("examples")
        self.assertEqual(result.returncode, 0)
        self.assertIn("crypto_spot_kline", result.stdout)
        self.assertIn("Use Cases", result.stdout)
        self.assertIn("Recipes", result.stdout)

    def test_explain_source(self) -> None:
        result = self._run("explain", "source", "coingecko")
        self.assertEqual(result.returncode, 0)
        self.assertIn("coingecko", result.stdout)
        self.assertIn("implementation_status", result.stdout)

    def test_explain_dataset(self) -> None:
        result = self._run("explain", "dataset", "funding")
        self.assertEqual(result.returncode, 0)
        self.assertIn("funding", result.stdout)

    def test_explain_source_json(self) -> None:
        result = self._run("explain", "source", "coingecko", "--json")
        self.assertEqual(result.returncode, 0)
        payload = json.loads(result.stdout)
        self.assertIn("source", payload)
        self.assertEqual(payload["source"], "coingecko")

    def test_explain_invalid_kind_exits_nonzero(self) -> None:
        result = self._run("explain", "badkind", "coingecko")
        self.assertNotEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
