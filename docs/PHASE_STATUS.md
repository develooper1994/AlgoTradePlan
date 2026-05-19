# Phase Status Snapshot (2026-05-19)

This snapshot compares the approved phased roadmap with the current
repository/docs state.

## Summary

### Completed (phases 01-16)
- **Phase 01**: planning/governance baseline docs and runbook scaffolding.
- **Phase 02**: core contracts/runtime scaffolding and deterministic unit tests.
- **Phase 03**: lint/test/smoke path is active and green.
- **Phase 04**: shared data contracts + market/news/macro source abstractions.
- **Phase 05**: ingestion pipeline (quality/storage/provenance) implemented and tested.
- **Phase 06**: curated/research feature lane with replay-safe provenance metadata
  (`src/algotradeplan/plugins/data/curated/`).
- **Phase 07**: strategy/model plugin skeletons and example adapter tests.
- **Phase 08**: runtime config loader + environment switching documentation.
- **Phase 09**: structured logger with PII redaction, in-memory metrics sink,
  observability runbook (`src/algotradeplan/observability/`).
- **Phase 10**: risk-before-execution `TradeFlow` orchestrator with emergency
  stop and runbook (`src/algotradeplan/orchestration/trade_flow.py`).
- **Phase 11**: deterministic drift-detecting reconciler with recovery actions
  and state-recovery runbook (`src/algotradeplan/plugins/reconciliation/drift_reconciler.py`).
- **Phase 12**: provenance-driven replay harness gating dry-run promotion
  (`src/algotradeplan/backtest/replay.py`).
- **Phase 13**: `scripts/deploy_check.py` + deployment/rollback runbook.
- **Phase 14**: `scripts/security_check.py` + dependency allowlist policy.
- **Phase 15**: `docs/extending.md` lists all current plugin roots and a
  contributor PR checklist.
- **Phase 16**: production acceptance documented at
  `docs/production_acceptance.md`.

### Active / Next
- **Phase 17 (active)**: data-first ingestion/storage abstraction hardening for
  asset/source extensibility with fixture-backed adapter coverage and onboarding
  runbook integration (`docs/phases/17.md`,
  `tests/fixtures/data_ingestion_assets.json`, `ONBOARDING.md`).

## Acceptance Validation Commands
Run these in order before tagging a release:
1. `make lint`
2. `make test`
3. `make smoke`
4. `python scripts/deploy_check.py --repo-root .`
5. `python scripts/security_check.py --repo-root .`

## Continuous Governance
- update this file whenever a phase advances, regresses, or adds new evidence
- record material decisions in `/docs/MASTER_PLAN.md` decision log
- ensure every new incident class lands in `/docs/runbooks/`
