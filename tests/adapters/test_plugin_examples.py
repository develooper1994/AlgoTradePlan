from __future__ import annotations

import unittest

from src.algotradeplan.plugins.connectors.example_execution_connector import (
    ExampleExecutionConnectorPlugin,
)
from src.algotradeplan.plugins.data.example_data_source import ExampleDataPlugin
from src.algotradeplan.plugins.indicators.example_indicator import ExampleIndicatorPlugin
from src.algotradeplan.plugins.models.example_model import ExampleModelPlugin
from src.algotradeplan.plugins.reconciliation.example_reconciler import ExampleReconciliationPlugin
from src.algotradeplan.plugins.risk.example_risk import ExampleRiskPlugin
from src.algotradeplan.plugins.strategies.example_strategy import ExampleStrategyPlugin


class PluginExamplesTest(unittest.TestCase):
    def test_strategy_example(self) -> None:
        payload = ExampleStrategyPlugin().generate_signal({"symbol": "BTCUSDT"})
        self.assertEqual(payload["action"], "hold")

    def test_risk_example(self) -> None:
        decision = ExampleRiskPlugin().evaluate({"symbol": "BTCUSDT"})
        self.assertTrue(decision["approved"])

    def test_connector_example(self) -> None:
        response = ExampleExecutionConnectorPlugin().send_order({"id": "1"})
        self.assertEqual(response["status"], "accepted")

    def test_data_model_indicator_and_reconciler_examples(self) -> None:
        data = ExampleDataPlugin().fetch("BTCUSDT")
        score = ExampleModelPlugin().predict({"price": data["price"]})
        metric = ExampleIndicatorPlugin().compute([{"close": 1.0}, {"close": 2.0}])
        sync = ExampleReconciliationPlugin().reconcile({"pos": 1}, {"pos": 1})

        self.assertEqual(data["symbol"], "BTCUSDT")
        self.assertEqual(score["score"], 0.0)
        self.assertEqual(metric["value"], 2.0)
        self.assertTrue(sync["in_sync"])


if __name__ == "__main__":
    unittest.main()
