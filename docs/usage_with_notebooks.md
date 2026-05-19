# Usage with Notebooks

This guide explains how to run the framework from notebooks for both smoke and full workflow scenarios.

## 1) Environment Setup

```bash
make bootstrap
make lint
make test
make smoke
```

To launch Jupyter:

```bash
python -m pip install jupyterlab
jupyter lab
```

## 2) Notebooks

- `notebooks/algotrade_e2e_demo.ipynb` (autonomous self-boot demo using `run_all_phases.py`)
- `notebooks/real_data_workflow.ipynb` (step-by-step real-data workflow)

Typical flow covered by notebooks:
- config/custom parameter selection
- asset discovery from connected sources
- market/news/macro ingestion using available public endpoints
- feature engineering preview
- rolling-window optimize/backtest with OOS split
- signal -> intent -> risk -> portfolio via `TradeFlow`
- single-asset and multi-portfolio metric summaries

## 3) Smoke + Validation Notes

- If network or third-party APIs are unavailable, notebook cells should fail with explicit errors.
- Notebook smoke is validated by `make smoke` (including `scripts/notebook_smoke_check.py`).
- Autonomous real-data path can be executed with:

```bash
python scripts/run_all_phases.py --include-live-smoke
```
