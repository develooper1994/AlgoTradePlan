# AlgoTradePlan

Minimal, plugin-based algorithmic trading framework skeleton.

## Core Modules (keep stable)
- `src/algotradeplan/core`: ids/contracts/types/clock
- `src/algotradeplan/plugins`: strategy, data, risk, reconciliation, execution interfaces + registry
- `src/algotradeplan/orchestration`: end-to-end trading flow and real-data autopilot
- `src/algotradeplan/backtest`: replay and realistic cost modeling

## Critical Workflows
- Terminal smoke: `python scripts/hello_world_e2e.py --mode terminal --dry-run`
- Notebook smoke: `python scripts/notebook_smoke_check.py`
- Full phase runner: `python scripts/run_all_phases.py --include-live-smoke`
- Validation path: `make lint && make test && make smoke && make runbook_check`

## Quick Start
```bash
make bootstrap
make lint
make test
make smoke
make runbook_check
```

## Documentation Map
- Start here: `docs/README.md`
- Onboarding: `ONBOARDING.md`, `docs/onboarding_10min.md`
- Notebook usage: `docs/usage_with_notebooks.md`
- Architecture: `docs/ARCHITECTURE.md`
- Plugin extension guide: `docs/extending.md`
- Operational runbooks: `docs/runbook_masterlist.md`, `docs/runbooks/`

## Notes on Cleanup
- Duplicate/stale docs are removed when a canonical file already exists.
- New changes should land in canonical docs, not parallel copies.
- Repo-facing documentation is intentionally concentrated in `docs/` plus this file
  and `ONBOARDING.md`.
