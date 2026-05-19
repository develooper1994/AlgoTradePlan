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
```

## DataHub / ETL

```python
from algotradeplan.data import DataHub, ETL

hub = DataHub()
hub.sources()
hub.coverage_table()
hub.discover_assets(source="binance_futures", limit=10)

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
```

| Variable | Source |
|---|---|
| `ALPHAVANTAGE_API_KEY` | Alpha Vantage |
| `TWELVEDATA_API_KEY` | Twelve Data |
| `POLYGON_API_KEY` | Polygon.io |
| `FINNHUB_API_KEY` | Finnhub |
| `QUANDL_API_KEY` | Nasdaq Data Link |
| `IEX_CLOUD_API_KEY` | IEX Cloud |

## Notebooks

```bash
jupyter lab
```

- `notebooks/01_real_data_smoke.ipynb`
- `notebooks/02_strategy_backtest_portfolio.ipynb`
- `notebooks/03_multi_source_asset_coverage.ipynb`

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
- `docs/extending.md` — adding new plugins
- `docs/usage_with_notebooks.md` — notebook workflow guide
- `docs/runbooks/` — operational runbooks
