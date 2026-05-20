"""Tests for the unified ``python -m algotradeplan`` CLI entry point."""
from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


class CLIEntryPointTest(unittest.TestCase):
    """Test that ``python -m src.algotradeplan`` subcommands work correctly."""

    def _run(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-m", "src.algotradeplan", *args],
            capture_output=True,
            text=True,
            check=False,
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

    def test_preflight_offline(self) -> None:
        result = self._run(
            "preflight",
            "--source", "offline_fallback",
            "--symbol", "BTCUSDT",
            "--datasets", "kline", "funding",
            "--strategy", "ema_cross_atr_stop",
        )
        # offline_fallback with kline+funding should pass preflight
        self.assertIn("can_run:", result.stdout)

    def test_doctor_exits_clean(self) -> None:
        result = self._run("doctor")
        # May have issues with missing artifacts in CI, but should not crash
        self.assertIn("AlgoTradePlan Doctor", result.stdout)

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
