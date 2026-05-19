# State Recovery Runbook

## Purpose
Repair drift between local and remote state snapshots after an incident.

## Inputs and Systems
- `src/algotradeplan/plugins/reconciliation/drift_reconciler.py`
- structured logger for audit entries
- venue snapshot export and local event store

## Procedure
1. capture local state and remote snapshot for the same correlation id
2. call `DriftDetectingReconciliationPlugin.reconcile(local, remote)`
3. for each `recovery_action`:
   - `resend`: re-submit the local entry to the venue
   - `ingest`: import the remote entry into local state
   - `investigate`: open an incident before mutating either side
4. re-run reconciliation; expect `in_sync=True`

## Validation
- `tests/adapters/test_drift_reconciler.py` is green
- final reconciliation result has `in_sync=True`

## Rollback / Recovery
- if a recovery action causes new drift, restore from event store snapshot
  before reapplying

## Escalation
- engage emergency-stop runbook if value mismatches affect open positions
