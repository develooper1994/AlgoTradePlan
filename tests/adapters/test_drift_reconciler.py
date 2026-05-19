from __future__ import annotations

import unittest

from src.algotradeplan.plugins.reconciliation.drift_reconciler import (
    DriftDetectingReconciliationPlugin,
)


class DriftReconcilerTest(unittest.TestCase):
    def test_in_sync_states(self) -> None:
        reconciler = DriftDetectingReconciliationPlugin()
        result = reconciler.reconcile({"A": 1}, {"A": 1})
        self.assertTrue(result.in_sync)
        self.assertEqual(result.drift, [])
        self.assertEqual(result.recovery_actions, [])

    def test_detects_three_drift_kinds_and_actions(self) -> None:
        reconciler = DriftDetectingReconciliationPlugin()
        result = reconciler.reconcile(
            {"A": 1, "B": 2}, {"A": 1, "C": 3, "B": 99}
        )
        self.assertFalse(result.in_sync)
        kinds = sorted(d.kind for d in result.drift)
        self.assertEqual(kinds, ["missing_local", "value_mismatch"])
        actions = [a["action"] for a in result.recovery_actions]
        self.assertIn("ingest", actions)
        self.assertIn("investigate", actions)

    def test_deterministic_output_ordering(self) -> None:
        reconciler = DriftDetectingReconciliationPlugin()
        first = reconciler.reconcile({"B": 1, "A": 2}, {})
        second = reconciler.reconcile({"A": 2, "B": 1}, {})
        self.assertEqual(
            [d.key for d in first.drift], [d.key for d in second.drift]
        )


if __name__ == "__main__":
    unittest.main()
