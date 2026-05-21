from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from src.algotradeplan.research import ExperimentRegistry, PreflightChecker, generate_data_health_report
from src.algotradeplan.strategies.catalog import recommend_strategies, strategy_summary


class _StubHub:
    def __init__(self) -> None:
        self._summaries = {
            "coingecko": {
                "source": "coingecko",
                "asset_classes": ["crypto_spot"],
                "extra_metadata": {},
                "notes": "",
            },
            "offline_fallback": {
                "source": "offline_fallback",
                "asset_classes": ["crypto_perpetual"],
                "extra_metadata": {},
                "notes": "",
            },
        }

    def dataset_status(self, source: str, dataset: str) -> str:
        if source == "coingecko" and dataset == "funding":
            return "unsupported"
        return "fallback"

    def source_summary(self, source: str) -> dict[str, object]:
        return self._summaries[source]

    def best_sources_for(self, *, dataset: str, **_kwargs: object) -> list[dict[str, str]]:
        return [{"source": "offline_fallback", "dataset_status": "fallback"}] if dataset else []

    def api_key_env(self, _source: str) -> str | None:
        return None

    def ingest(
        self,
        *,
        source: str,
        symbol: str,
        datasets: list[str],
        allow_partial: bool,
        store: bool,
    ):
        del source, symbol, allow_partial, store

        class _Ingest:
            dataset_coverage = {dataset: 1 for dataset in datasets}
            records = [object()]
            source_issues = []

            class _Quality:
                passed = True
                checks = ["records_present"]
                issues: list[str] = []

            quality_report = _Quality()

        return _Ingest()


class ResearchLabTest(unittest.TestCase):
    def test_preflight_blocks_unsupported_dataset(self) -> None:
        result = PreflightChecker(_StubHub()).check(
            source="coingecko",
            symbol="bitcoin",
            datasets=["kline", "funding"],
            strategy="ema_cross_atr_stop",
            allow_api_key=False,
        )
        self.assertFalse(result.can_run)
        self.assertTrue(any("funding unsupported" in issue for issue in result.blocking_issues))

    def test_preflight_allows_supported_offline_combo(self) -> None:
        result = PreflightChecker(_StubHub()).check(
            source="offline_fallback",
            symbol="BTCUSDT",
            datasets=["kline"],
            strategy="ema_cross_atr_stop",
            allow_api_key=False,
        )
        self.assertTrue(result.can_run)

    def test_data_health_offline_generates_score(self) -> None:
        report = generate_data_health_report(
            hub=_StubHub(),
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
