from __future__ import annotations

import unittest

from src.algotradeplan.orchestration import TradeFlow
from src.algotradeplan.plugins.connectors.example_execution_connector import (
    ExampleExecutionConnectorPlugin,
)
from src.algotradeplan.plugins.risk.example_risk import ExampleRiskPlugin
from src.algotradeplan.plugins.strategies.example_strategy import ExampleStrategyPlugin


class _BuyStrategy:
    plugin_id = "buy_strategy"

    def generate_signal(self, context):
        return {"action": "buy", "context": context}


class _RejectingRisk:
    plugin_id = "rejecting_risk"

    def evaluate(self, order_intent):
        return {"approved": False, "reason": "daily_loss_limit"}


class _CountingExecution:
    plugin_id = "counting_execution"

    def __init__(self):
        self.calls = []

    def send_order(self, order):
        self.calls.append(order)
        return {"status": "accepted", "order": order}


class TradeFlowTest(unittest.TestCase):
    def test_hold_signal_does_not_call_risk_or_execution(self) -> None:
        execution = _CountingExecution()
        flow = TradeFlow(ExampleStrategyPlugin(), ExampleRiskPlugin(), execution)
        result = flow.run({"symbol": "BTCUSDT"})
        self.assertIsNone(result.execution)
        self.assertEqual(execution.calls, [])
        self.assertFalse(result.halted)

    def test_risk_rejection_blocks_execution(self) -> None:
        execution = _CountingExecution()
        flow = TradeFlow(_BuyStrategy(), _RejectingRisk(), execution)
        result = flow.run({"symbol": "BTCUSDT"})
        self.assertTrue(result.halted)
        self.assertEqual(result.reason, "daily_loss_limit")
        self.assertEqual(execution.calls, [])

    def test_approved_intent_reaches_execution(self) -> None:
        execution = _CountingExecution()
        flow = TradeFlow(_BuyStrategy(), ExampleRiskPlugin(), execution)
        result = flow.run({"symbol": "BTCUSDT"})
        self.assertFalse(result.halted)
        self.assertEqual(result.execution["status"], "accepted")
        self.assertEqual(len(execution.calls), 1)

    def test_emergency_stop_blocks_subsequent_runs(self) -> None:
        execution = _CountingExecution()
        flow = TradeFlow(_BuyStrategy(), ExampleRiskPlugin(), execution)
        flow.trigger_emergency_stop(reason="ops_pause")
        result = flow.run({"symbol": "BTCUSDT"})
        self.assertTrue(result.halted)
        self.assertEqual(result.reason, "ops_pause")
        self.assertEqual(execution.calls, [])


if __name__ == "__main__":
    unittest.main()
