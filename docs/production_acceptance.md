# Production Acceptance Review (Phase 16)

## Phase Approvals
| Phase | Status | Evidence |
| --- | --- | --- |
| 01 | approved | `/docs/MASTER_PLAN.md`, `/docs/GOVERNANCE.md`, `/docs/runbooks/` |
| 02 | approved | `tests/unit/test_core_ids.py`, `tests/unit/test_foundation_modules.py` |
| 03 | approved | `make lint`, `make test`, `make smoke` green |
| 04 | approved | `src/algotradeplan/plugins/data/{market,news,macro}` |
| 05 | approved | `tests/adapters/test_data_ingestion_pipeline_examples.py` |
| 06 | approved | `src/algotradeplan/plugins/data/curated/`, `tests/adapters/test_curated_feature_view.py` |
| 07 | approved | `tests/adapters/test_plugin_examples.py` |
| 08 | approved | `tests/unit/test_foundation_modules.py::test_load_runtime_config_reads_json_file` |
| 09 | approved | `src/algotradeplan/observability/`, `tests/unit/test_observability.py` |
| 10 | approved | `src/algotradeplan/orchestration/trade_flow.py`, `tests/adapters/test_trade_flow.py` |
| 11 | approved | `src/algotradeplan/plugins/reconciliation/drift_reconciler.py`, `tests/adapters/test_drift_reconciler.py` |
| 12 | approved | `src/algotradeplan/backtest/replay.py`, `tests/adapters/test_replay_harness.py` |
| 13 | approved | `scripts/deploy_check.py`, `tests/unit/test_deploy_check.py` |
| 14 | approved | `scripts/security_check.py`, `tests/unit/test_security_check.py` |
| 15 | approved | `docs/extending.md` updated, contributor checklist embedded |
| 16 | approved | this document |

## Acceptance Validation Commands
Run, in order, before tagging a release:
1. `make lint`
2. `make test`
3. `make smoke`
4. `python scripts/deploy_check.py --repo-root .`
5. `python scripts/security_check.py --repo-root .`

All five commands must exit with status 0.

## Continuous Governance Cadence
- review the decision log in `/docs/MASTER_PLAN.md` at least monthly
- refresh `/docs/PHASE_STATUS.md` whenever a phase advances or regresses
- audit runbooks after every incident; create a new entry under `/docs/runbooks/`
  for previously unseen incident classes
- treat any contract or plugin-root change as a Phase-15 contributor PR even
  after Phase 16 approval, and update this acceptance document accordingly

## Rollback / Revocation
If acceptance evidence regresses, mark the relevant phase as `partial` in
`docs/PHASE_STATUS.md` and pause production promotion until evidence is
re-established.
