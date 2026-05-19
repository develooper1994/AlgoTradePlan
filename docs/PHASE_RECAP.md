# Prior Recommendations Recap and Next-Phase Direction

This recap consolidates prior guidance from planning, onboarding, core, test,
plugin, phase docs, runbooks, ingestion abstractions, extension guides, and the
decision log.

## Consolidated Guidance
- delivery is phase-gated: each phase must ship code, docs, tests, and checklist evidence
- data-first contracts are mandatory: ingestion + storage + quality + provenance
- core flows remain plugin-based for data, strategy, risk, execution, and reconciliation
- every new asset/source extension ships with deterministic tests and dummy fixtures
- runbooks are part of the deliverable, not post-release documentation

## Next Phase Focus (Phase 17)
Treat data ingestion/storage abstraction as a first-class expansion lane with:
- at least market, news, and macro ingestion adapter examples
- pluggable asset ingestion workflow documented and checklist-enforced
- fixture-backed adapter tests under `tests/fixtures/`
- onboarding and Makefile commands that include runbook integration checks
