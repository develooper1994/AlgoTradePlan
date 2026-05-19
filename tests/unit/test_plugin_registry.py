from __future__ import annotations

import unittest

from src.algotradeplan.plugins.registry import discover_plugins, load_plugin_class


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
        self.assertEqual(registry["ema_cross_atr_stop_strategy"].category, "strategies")
        self.assertEqual(registry["notional_guard_risk"].category, "risk")

    def test_dynamic_loader_returns_plugin_class(self) -> None:
        plugin_cls = load_plugin_class("ema_cross_atr_stop_strategy")
        plugin = plugin_cls()
        self.assertEqual(plugin.plugin_id, "ema_cross_atr_stop_strategy")
        self.assertTrue(callable(getattr(plugin, "generate_signal")))

    def test_missing_plugin_raises_key_error(self) -> None:
        with self.assertRaises(KeyError):
            load_plugin_class("does_not_exist")


if __name__ == "__main__":
    unittest.main()
