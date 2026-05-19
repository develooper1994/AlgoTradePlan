from __future__ import annotations

import importlib
import sys
import tempfile
from pathlib import Path
import unittest

from src.algotradeplan.plugins.registry import discovery_issues, discover_plugins, load_plugin_class


class PluginRegistryTest(unittest.TestCase):
    def test_discover_plugins_includes_core_agent_integrations(self) -> None:
        registry, issues = discover_plugins()
        self.assertIsInstance(issues, list)

        expected = {
            "example_data_source",
            "rolling_window_feature_engine",
            "ema_cross_atr_stop_strategy",
            "notional_guard_risk",
            "simulated_fill_connector",
            "drift_detecting_reconciler",
        }
        self.assertTrue(expected.issubset(set(registry)))
        self.assertEqual(registry["example_data_source"].category, "data")
        self.assertEqual(registry["ema_cross_atr_stop_strategy"].category, "strategy")
        self.assertEqual(registry["rolling_window_feature_engine"].category, "indicators")
        self.assertEqual(registry["notional_guard_risk"].category, "risk")
        self.assertEqual(registry["simulated_fill_connector"].category, "execution_connector")
        self.assertEqual(registry["drift_detecting_reconciler"].category, "reconciliation")

    def test_dynamic_loader_returns_plugin_class(self) -> None:
        plugin_cls = load_plugin_class("ema_cross_atr_stop_strategy")
        plugin = plugin_cls()
        self.assertEqual(plugin.plugin_id, "ema_cross_atr_stop_strategy")
        self.assertTrue(callable(getattr(plugin, "generate_signal")))

    def test_missing_plugin_raises_key_error(self) -> None:
        with self.assertRaisesRegex(KeyError, "plugin_id 'does_not_exist' not found"):
            load_plugin_class("does_not_exist")

    def test_discovery_issues_api_returns_list(self) -> None:
        self.assertIsInstance(discovery_issues(), list)

    def test_duplicate_plugin_ids_raise_value_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir) / "tmp_plugins"
            root.mkdir()
            (root / "__init__.py").write_text("", encoding="utf-8")
            (root / "first.py").write_text(
                "class FirstPlugin:\n"
                "    plugin_id = 'duplicate_plugin'\n",
                encoding="utf-8",
            )
            (root / "second.py").write_text(
                "class SecondPlugin:\n"
                "    plugin_id = 'duplicate_plugin'\n",
                encoding="utf-8",
            )

            sys.path.insert(0, tmp_dir)
            importlib.invalidate_caches()
            try:
                with self.assertRaisesRegex(ValueError, "duplicate plugin_id"):
                    discover_plugins(root_package="tmp_plugins")
            finally:
                sys.path.remove(tmp_dir)
                sys.modules.pop("tmp_plugins", None)
                sys.modules.pop("tmp_plugins.first", None)
                sys.modules.pop("tmp_plugins.second", None)


if __name__ == "__main__":
    unittest.main()
