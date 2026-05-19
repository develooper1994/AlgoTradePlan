"""Deterministic drift-detecting reconciler with recovery plan (Phase 11)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class DriftEntry:
    key: str
    local: Any
    remote: Any
    kind: str  # "missing_remote", "missing_local", "value_mismatch"


@dataclass(frozen=True)
class ReconciliationResult:
    in_sync: bool
    drift: list[DriftEntry] = field(default_factory=list)
    recovery_actions: list[dict[str, Any]] = field(default_factory=list)


class DriftDetectingReconciliationPlugin:
    plugin_id = "drift_detecting_reconciler"

    def reconcile(
        self,
        local_state: dict[str, Any],
        remote_state: dict[str, Any],
    ) -> ReconciliationResult:
        drift: list[DriftEntry] = []
        actions: list[dict[str, Any]] = []

        all_keys = sorted(set(local_state) | set(remote_state))
        for key in all_keys:
            if key not in remote_state:
                drift.append(
                    DriftEntry(
                        key=key, local=local_state[key], remote=None, kind="missing_remote"
                    )
                )
                actions.append({"action": "resend", "key": key, "value": local_state[key]})
            elif key not in local_state:
                drift.append(
                    DriftEntry(
                        key=key, local=None, remote=remote_state[key], kind="missing_local"
                    )
                )
                actions.append({"action": "ingest", "key": key, "value": remote_state[key]})
            elif local_state[key] != remote_state[key]:
                drift.append(
                    DriftEntry(
                        key=key,
                        local=local_state[key],
                        remote=remote_state[key],
                        kind="value_mismatch",
                    )
                )
                actions.append(
                    {
                        "action": "investigate",
                        "key": key,
                        "local": local_state[key],
                        "remote": remote_state[key],
                    }
                )

        return ReconciliationResult(
            in_sync=not drift,
            drift=drift,
            recovery_actions=actions,
        )
