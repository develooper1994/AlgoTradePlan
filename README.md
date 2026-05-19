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

## Real Data Smoke Pipeline

```bash
python scripts/e2e_real_data_smoke.py --interactive --allow-partial
```

Produces `artifacts/real_data_smoke_report.json` with:
- source coverage, asset count, selected asset
- dataset coverage, data quality results
- provenance manifest
- strategy signal (EMA/ATR)
- backtest metrics (net PnL, drawdown, Sharpe)
- risk decision (structured, extensible)
- execution fill
- portfolio snapshot (cash, positions, NAV, realized/unrealized PnL)
- source issues

`make smoke_real` runs the same pipeline.

## API Key Options (optional — public sources work without keys)

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

- `notebooks/real_data_workflow.ipynb` — real-data ingest, features, strategy, backtest
- `notebooks/algotrade_e2e_demo.ipynb` — full Signal→Intent→Risk→Execution→Portfolio demo

## Documentation

- `ONBOARDING.md` / `docs/onboarding_10min.md` — 10-min onboarding
- `docs/ARCHITECTURE.md` — component diagram and design decisions
- `docs/quickstart.md` — step-by-step usage
- `docs/extending.md` — adding new plugins
- `docs/usage_with_notebooks.md` — notebook workflow guide
- `docs/runbooks/` — operational runbooks

