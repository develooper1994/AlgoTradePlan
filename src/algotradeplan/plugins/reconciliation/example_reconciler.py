"""Example reconciliation plugin."""

from __future__ import annotations


class ExampleReconciliationPlugin:
    plugin_id = "example_reconciler"

    def reconcile(self, local_state: dict[str, object], remote_state: dict[str, object]) -> dict[str, object]:
        return {"in_sync": local_state == remote_state}
