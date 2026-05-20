# Quickstart

## Terminal
```bash
bash scripts/bootstrap.sh
make lint
make test
make smoke
make runbook_check
python scripts/framework_status.py
python scripts/tutorial_mode.py --all --offline
python scripts/run_all_phases.py --include-live-smoke
```

## Notebook
Open `notebooks/00_framework_tutorial.ipynb` first, then continue with:
- `notebooks/01_real_data_smoke.ipynb`
- `notebooks/02_strategy_backtest_portfolio.ipynb`
- `notebooks/03_multi_source_asset_coverage.ipynb`
