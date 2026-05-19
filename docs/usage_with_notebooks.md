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

### Which notebook runs what?

- **`algotrade_e2e_demo.ipynb`**: CI-aligned smoke path (`make lint/test/smoke`)
  and full autonomous checkpoint execution (`scripts/run_all_phases.py
  --include-live-smoke`).
- **`real_data_workflow.ipynb`**: interactive workflow for discovery, ingestion,
  feature engineering, strategy/backtest optimization, and signal -> intent ->
  risk -> portfolio review.

Typical flow covered by notebooks:
- config/custom parameter selection
- asset discovery from connected sources
- market/news/macro ingestion using available public endpoints
- feature engineering preview
- rolling-window optimize/backtest with OOS split
- signal -> intent -> risk -> portfolio via `TradeFlow`
- single-asset and multi-portfolio metric summaries

## 3) Example notebook cells (real-data workflow)

```python
from pathlib import Path
from src.algotradeplan.orchestration.real_data_autopilot import run_real_data_autopilot

report = run_real_data_autopilot(
    report_path=Path("artifacts/notebooks/real_data_report.json"),
    max_symbols_per_source=3,
    allow_partial=True,
)
report.source_inventory, report.market_sources[0], report.source_issues[:2]
```

```python
# Asset discovery + ingest from registry-backed providers
from src.algotradeplan.plugins.data.market import collect_market_source_data
import json
import ssl
from urllib.parse import urlencode
from urllib.request import Request, urlopen

def get_json(url: str, params: dict[str, object]):
    query = urlencode({k: v for k, v in params.items() if v is not None})
    request_url = f"{url}?{query}" if query else url
    request = Request(request_url, headers={"Accept": "application/json", "User-Agent": "AlgoTradePlanNotebook/1.0"})
    timeout_seconds = 20  # increase/decrease per provider latency in production notebooks
    with urlopen(request, timeout=timeout_seconds, context=ssl.create_default_context()) as response:
        return json.loads(response.read().decode("utf-8"))

results, issues = collect_market_source_data(
    get_json=get_json,
    max_symbols=3,
    allow_partial=True,
)
[(r.source, r.selected_asset, len(r.datasets.get("kline", []))) for r in results], issues[:3]
```

```python
# Strategy / intent / risk / portfolio visibility from autopilot report
{
    "intent": report.intent,
    "risk_decision": report.risk_decision,
    "portfolio": report.portfolio,
    "metrics": report.metrics,
}
```

## 4) Smoke + Validation Notes

- If network or third-party APIs are unavailable, notebook cells should fail with explicit errors.
- Notebook smoke is validated by `make smoke` (including `scripts/notebook_smoke_check.py`).
- Autonomous real-data path can be executed with:

```bash
python scripts/run_all_phases.py --include-live-smoke
```
