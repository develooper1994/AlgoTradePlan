# ONBOARDING

## 10-Minute Path
1. `make bootstrap`
2. `make lint`
3. `make test`
4. `make smoke`
5. `make runbook_check`
6. `python scripts/run_all_phases.py --include-live-smoke`

## What to Read Next
- summary of prior recommendations and phase direction: `docs/PHASE_RECAP.md`
- phase rules and decision log: `docs/MASTER_PLAN.md`
- active/next phase status: `docs/PHASE_STATUS.md`
- notebook workflow: `docs/usage_with_notebooks.md`
- extension workflow: `docs/extending.md`
- runbook index: `docs/runbook_masterlist.md`

## Data-First Extension Start
For new asset or source plugins:
1. implement under `src/algotradeplan/plugins/data/<domain>/`
2. add/update deterministic adapter tests
3. add/update dummy fixture entries in `tests/fixtures/data_ingestion_assets.json`
4. update docs in `docs/extending.md` and active phase file
5. ensure relevant runbook references are present

## Jupyter + Real Data
- Open `notebooks/algotrade_e2e_demo.ipynb` for the end-to-end notebook path.
- Notebook runs the same autonomous scripts (`run_all_phases.py` and
  `e2e_real_data_smoke.py`) and writes reports to `artifacts/`.
