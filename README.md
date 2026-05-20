# AlgoTradePlan

Production-grade, plugin-based algorithmic trading framework.

## Architecture

```
src/algotradeplan/
├── core/           # canonical schemas, intent model, contracts, types, clock
├── portfolio/      # PortfolioManager, PositionBook, TradeLedger  ← production module
├── plugins/
│   ├── data/       # market/news/macro sources, ingestion pipeline, quality, provenance
│   ├── risk/       # RiskEngine (structured decisions), NotionalGuardRiskPlugin
│   ├── strategies/ # EmaCrossAtrStop, parameter optimization
│   ├── indicators/ # EMA, ATR, Bollinger rolling-window engine
│   ├── connectors/ # SimulatedFillExecutionConnector
│   └── registry    # dynamic plugin loader
├── backtest/       # RealisticBacktester with equity curve, drawdown, Sharpe/Sortino
├── orchestration/  # TradeFlow, real-data autopilot pipeline
└── observability/  # StructuredLogger, InMemoryMetricsSink
```

### Signal → Intent → Risk → Execution → Portfolio chain
`core/intent.py` provides `TradeIntent` and `signal_to_intent()`.  
Risk decisions are structured (`RiskDecision`) with `approved`, `reason`, `checks`, `rejected_rules`, `adjusted_quantity`.

## Installation

```bash
pip install -e ".[data]"
```

## Quick Start

```bash
make bootstrap        # install dev dependencies
make lint             # compile-check all Python files
make test             # run full unit/adapter/smoke test suite
make smoke            # dry-run hello-world + notebook smoke
make runbook_check    # verify runbook index exists
python scripts/framework_status.py
python scripts/framework_status.py --next-actions-only --score
python scripts/framework_status.py --write-doc --write-plan
python scripts/tutorial_mode.py --all --offline
python scripts/tutorial_mode.py --all --offline --pretty
python scripts/tutorial_mode.py --all --offline --markdown
python scripts/tutorial_mode.py --all --offline --write-doc
python scripts/generate_data_coverage_doc.py
python scripts/refresh_framework_artifacts.py --skip-live
make refresh_artifacts
```

## DataHub / ETL

```python
from algotradeplan.data import DataHub, ETL

hub = DataHub()
hub.sources()
hub.coverage_table()
hub.dataset_status("coingecko", "kline")
hub.sources_for(dataset="news")
hub.recommend_sources("crypto_spot_kline", allow_api_key=False)
hub.recommend_sources("macro_indicators", allow_api_key=False)
hub.best_sources_for(dataset="kline", asset_class="crypto_spot", allow_api_key=False)
hub.best_sources_for(dataset="kline", asset_class="equity", allow_api_key=False)
hub.explain_source("coingecko")
hub.explain_dataset("funding")
hub.dataset_sources_matrix(["kline", "news", "macro", "fundamentals"])
hub.asset_sources_matrix(["crypto_spot", "equity", "macro"])
hub.discover_assets(source="binance_futures", limit=10)
hub.ingest(source="coingecko", symbol="bitcoin", datasets=["tick", "kline"], allow_partial=True)

etl = ETL()
df = etl.load_market_data(
    source="binance_futures",
    symbol="BTCUSDT",
    dataset="kline",
    timeframe="1m",
    limit=500,
)
```

## Real Data Smoke Pipeline

```bash
python scripts/e2e_real_data_smoke.py --interactive --allow-partial
```

Produces `artifacts/real_data_smoke_report.json` with:
- source coverage, asset count, selected asset
- human-readable source coverage table
- dataset coverage, data quality results
- provenance manifest
- normalized record count
- strategy signal (EMA/ATR)
- backtest metrics (net PnL, drawdown, Sharpe)
- risk decision (structured, extensible)
- execution fill
- portfolio snapshot (cash, positions, NAV, realized/unrealized PnL)
- ledger
- source issues

`make smoke_real` runs the same pipeline.

## API Key Options (optional — public sources work without keys)

```bash
export ALPHAVANTAGE_API_KEY="..."
export TWELVEDATA_API_KEY="..."
export POLYGON_API_KEY="..."
export FINNHUB_API_KEY="..."
export QUANDL_API_KEY="..."
export IEX_CLOUD_API_KEY="..."
export FRED_API_KEY="..."
export FMP_API_KEY="..."
```

| Variable | Source |
|---|---|
| `ALPHAVANTAGE_API_KEY` | Alpha Vantage |
| `TWELVEDATA_API_KEY` | Twelve Data |
| `POLYGON_API_KEY` | Polygon.io |
| `FINNHUB_API_KEY` | Finnhub |
| `QUANDL_API_KEY` | Nasdaq Data Link |
| `IEX_CLOUD_API_KEY` | IEX Cloud |
| `FRED_API_KEY` | FRED |
| `FMP_API_KEY` | Financial Modeling Prep |

## Notebooks

```bash
jupyter lab
```

- `notebooks/00_framework_tutorial.ipynb`
- `notebooks/01_real_data_smoke.ipynb`
- `notebooks/02_strategy_backtest_portfolio.ipynb`
- `notebooks/03_multi_source_asset_coverage.ipynb`

Notebook amaçları:
- `00_framework_tutorial`: baştan sona DataHub → ETL → strategy/backtest → risk/execution → portfolio akışı
- `01_real_data_smoke`: coverage tablosu + çoklu source ingest smoke
- `02_strategy_backtest_portfolio`: ETL + strategy/risk/execution/portfolio zinciri
- `03_multi_source_asset_coverage`: implementation status, API-key filtreleme, unsupported dataset davranışı

Coverage snapshot:

| Source | Asset discovery | Kline/OHLCV | Trades | Orderbook | Funding | Equity | ETF | Forex | Options | Macro | News | Requires API key | API key env |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| binance_futures | yes | yes | yes | yes | yes | no | no | no | no | no | no | no | |
| yahoo_unofficial | yes | yes | no | no | no | yes | yes | yes | no | no | no | no | |
| frankfurter_fx | yes | no | no | no | no | no | no | yes | no | yes | no | no | |

## Documentation

- `ONBOARDING.md` / `docs/onboarding_10min.md` — 10-min onboarding
- `docs/ARCHITECTURE.md` — component diagram and design decisions
- `docs/quickstart.md` — step-by-step usage
- `docs/tutorial.md` — CLI + notebook tutorial walkthrough
- `docs/framework_status.md` — generated framework status / next actions
- `docs/next_actions.md` — generated priority plan from framework status
- `docs/data_source_coverage.md` — source/dataset implementation coverage matrix
- `docs/source_recommendations.md` — generated use-case based source recommendation index
- `docs/extending.md` — adding new plugins
- `docs/usage_with_notebooks.md` — notebook workflow guide
- `docs/runbooks/` — operational runbooks

Artifact refresh:

```bash
python scripts/refresh_framework_artifacts.py --skip-live
```
