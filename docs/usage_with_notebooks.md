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

- `notebooks/00_framework_tutorial.ipynb` — new-user tutorial for DataHub → ETL → feature → strategy → backtest → risk → execution → portfolio → report.
- `notebooks/01_real_data_smoke.ipynb` — `DataHub`-first workflow for source listing, coverage table, asset discovery, ingest, quality, and provenance.
- `notebooks/02_strategy_backtest_portfolio.ipynb` — `ETL` → features → strategy/backtest → signal -> intent -> risk -> execution -> portfolio.
- `notebooks/03_multi_source_asset_coverage.ipynb` — cross-source coverage comparison, API-key awareness, and unsupported dataset behaviour.

Legacy notebook snapshots were moved under `examples/legacy/`.

## 3) Example notebook cells

```python
from algotradeplan.data import DataHub

hub = DataHub()
hub.sources()[:5], hub.coverage_table()[:2]
```

```python
from algotradeplan.data import ETL

etl = ETL()
frame = etl.load_market_data(
    source="binance_futures",
    symbol="BTCUSDT",
    dataset="kline",
    timeframe="1m",
    limit=120,
)
frame.head() if hasattr(frame, "head") else frame[:2]
```

```python
from pathlib import Path
from src.algotradeplan.orchestration.real_data_autopilot import run_real_data_autopilot

report = run_real_data_autopilot(
    report_path=Path("artifacts/notebooks/real_data_report.json"),
    max_symbols_per_source=3,
    allow_partial=True,
)
report.data_quality, report.provenance_manifest, report.execution_fill
```

## 4) Smoke + Validation Notes

- If network or third-party APIs are unavailable, notebook cells should fail with explicit errors.
- Notebook smoke is validated by `make smoke` (including `scripts/notebook_smoke_check.py`).
- Autonomous real-data path can be executed with:

```bash
python scripts/run_all_phases.py --include-live-smoke
```
