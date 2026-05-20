from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from src.algotradeplan.data import DataHub
from src.algotradeplan.research import ExperimentRegistry, PreflightChecker, generate_data_health_report
from src.algotradeplan.strategies.catalog import recommend_strategies, strategy_summary


class ResearchLabTest(unittest.TestCase):
    def test_preflight_blocks_unsupported_dataset(self) -> None:
        result = PreflightChecker(DataHub()).check(
            source="coingecko",
            symbol="bitcoin",
            datasets=["kline", "funding"],
            strategy="ema_cross_atr_stop",
            allow_api_key=False,
        )
        self.assertFalse(result.can_run)
        self.assertTrue(any("funding unsupported" in issue for issue in result.blocking_issues))

    def test_preflight_allows_supported_offline_combo(self) -> None:
        result = PreflightChecker(DataHub()).check(
            source="offline_fallback",
            symbol="BTCUSDT",
            datasets=["kline"],
            strategy="ema_cross_atr_stop",
            allow_api_key=False,
        )
        self.assertTrue(result.can_run)

    def test_data_health_offline_generates_score(self) -> None:
        report = generate_data_health_report(
            hub=DataHub(),
            source="offline_fallback",
            symbol="BTCUSDT",
            datasets=["kline", "funding"],
            allow_partial=True,
        )
        self.assertGreaterEqual(report.health_score, 0)
        self.assertLessEqual(report.health_score, 100)
        self.assertGreater(report.record_count, 0)

    def test_strategy_catalog_and_recommend_filters(self) -> None:
        ema = strategy_summary("ema_cross_atr_stop")
        self.assertIn("kline", ema["required_datasets"])
        recommended = recommend_strategies(asset_class="crypto_perpetual", datasets=["kline", "funding"])
        strategy_ids = {item["strategy_id"] for item in recommended}
        self.assertIn("ema_cross_atr_stop", strategy_ids)
        self.assertIn("funding_carry", strategy_ids)

    def test_experiment_registry_writes_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            registry = ExperimentRegistry(root=tmp_dir)
            record = registry.record(
                name="offline_ema_atr_demo",
                config={"strategy": "ema_cross_atr_stop"},
                data_manifest={"dataset_coverage": {"kline": 10}},
                backtest={"net_pnl": 1.23},
                risk={"approved": True},
                portfolio={"nav": 10001.0},
            )
            root = Path(record.root)
            self.assertTrue((root / "config.json").exists())
            self.assertTrue((root / "data_manifest.json").exists())
            self.assertTrue((root / "backtest.json").exists())
            self.assertTrue((root / "risk.json").exists())
            self.assertTrue((root / "portfolio.json").exists())
            self.assertTrue((root / "summary.md").exists())

    def test_recipe_runner_dry_run(self) -> None:
        run = subprocess.run(
            [
                sys.executable,
                "scripts/run_recipe.py",
                "recipes/crypto_momentum.yaml",
                "--dry-run",
                "--json",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(run.returncode, 0)
        payload = json.loads(run.stdout)
        self.assertIn("preflight", payload)
        self.assertIn("data_health", payload)

    def test_recipe_runner_dry_run_without_yaml_parser(self) -> None:
        env = dict(os.environ)
        env["ALGOTRADEPLAN_DISABLE_YAML"] = "1"
        run = subprocess.run(
            [
                sys.executable,
                "scripts/run_recipe.py",
                "recipes/crypto_momentum.yaml",
                "--dry-run",
                "--json",
            ],
            capture_output=True,
            text=True,
            check=False,
            env=env,
        )
        self.assertEqual(run.returncode, 0)
        payload = json.loads(run.stdout)
        self.assertIn("preflight", payload)
        self.assertIn("data_health", payload)


if __name__ == "__main__":
    unittest.main()
