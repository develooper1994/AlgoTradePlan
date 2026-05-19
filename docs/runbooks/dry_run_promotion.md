# Dry-Run Promotion Runbook

## Purpose
Promote a replayable workflow from dry-run to simulate-live once parity with
canonical records is confirmed.

## Preconditions
- canonical batch and `ProvenanceRecord` exist for the target request
- source plugin is registered and deterministic

## Procedure
1. instantiate `ReplayHarness(source)` for the relevant source plugin
2. call `harness.replay(provenance, canonical_records)`
3. inspect `ReplayResult.parity`
4. if parity holds, call `harness.promote(result)` to record promotion approval

## Validation
- `tests/adapters/test_replay_harness.py` is green
- promotion call returns `promoted=True` with matching `revision`

## Rollback / Recovery
- if parity fails, do not promote; reopen `docs/runbooks/data_quality_incident.md`
- run `python scripts/teardown_simulation.py` to clear local simulation artifacts

## Escalation
- if drift recurs across revisions, open state recovery runbook
