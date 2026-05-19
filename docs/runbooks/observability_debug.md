# Observability and Debug Runbook

## Purpose
Investigate operational issues using structured logs, correlation ids, and
metric snapshots emitted by the platform.

## Inputs and Systems
- `src/algotradeplan/observability/structured_log.py` for structured log entries
- `src/algotradeplan/observability/metrics.py` for metric counters
- correlation ids propagated from the entry point that initiated the workflow

## Procedure
1. capture the correlation id reported by the failing workflow
2. filter structured log entries by `correlation_id`
3. correlate the matching metric events for the same time range
4. cross-reference provenance revisions for any data-related failure

## Validation
- structured log entries redact sensitive keys
  (`password`, `token`, `secret`, `api_key`, `authorization`)
- metric totals reconcile with log counts for the workflow
- `tests/unit/test_observability.py` is green

## Escalation
- if data integrity is affected, open `docs/runbooks/data_quality_incident.md`
- if an emergency stop is required, open the emergency-stop runbook
