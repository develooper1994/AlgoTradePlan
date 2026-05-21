# AlgoTradePlan

Production-grade, plugin-based algorithmic trading research framework.

## Install

```bash
pip install -e ".[data]"
```

## Data Layer Ownership (MarketData Cutover)

AlgoTradePlan artık data-layer implementasyonu sahibi değildir. Tüm data erişimi,
harici **MarketData** bridge/client üzerinden yapılır.

- Gerçek data kullanımı için `MARKET_DATA_BIN` ayarlanmalıdır.
- AlgoTradePlan `DataHub`/`ETL` API’leri artık ince bir uyumluluk shim’idir.
- Provider/adapter/normalize/quality/storage/provenance logic’i MarketData tarafındadır.

```bash
export MARKET_DATA_BIN=/path/to/market_data_bridge
```

## 3-Command Offline Demo

```bash
# 1. Run the interactive tutorial (no API key, no internet needed)
python -m algotradeplan tutorial --offline

# 2. Recommend data sources for a use case
python -m algotradeplan recommend --use-case crypto_spot_kline --no-api-key

# 3. Check framework status and next actions
python -m algotradeplan status
```

## Python API — 3 Examples

```python
from algotradeplan.data import DataHub

hub = DataHub()

# Which sources can I use for crypto OHLCV without an API key?
hub.recommend_sources("crypto_spot_kline", allow_api_key=False)

# Best public equity kline sources
hub.best_sources_for(dataset="kline", asset_class="equity", allow_api_key=False)

# Understand a source or dataset
hub.explain_source("coingecko")
hub.explain_dataset("funding")
```

## Main CLI

```
python -m algotradeplan --help

  status      Framework score, next actions, coverage summary
  tutorial    End-to-end offline tutorial walkthrough
  coverage    Regenerate data source coverage docs
  recommend   Source recommendations for a use case
  preflight   Check if a pipeline config can run
  health      Data health report
  recipe      Execute a YAML recipe
  refresh     Refresh all generated artifacts (--skip-live for offline)
  doctor      Environment / API key / doc health check
  examples    List recipes and use cases
  explain     Explain a source or dataset
```

### Workflow Examples

```bash
# Preflight check
python -m algotradeplan preflight \
  --source coingecko --symbol bitcoin \
  --datasets kline funding --strategy ema_cross_atr_stop

# Data health
python -m algotradeplan health \
  --source offline_fallback --symbol BTCUSDT \
  --datasets kline funding --offline

# Run a recipe (dry-run)
python -m algotradeplan recipe recipes/crypto_momentum.yaml --dry-run

# Refresh all generated artifacts (offline-safe)
python -m algotradeplan refresh --skip-live

# Explain a dataset or source
python -m algotradeplan explain dataset funding
python -m algotradeplan explain source coingecko
```

## Legacy Script Commands (still work)

```bash
python scripts/framework_status.py --score
python scripts/framework_status.py --next-actions-only
python scripts/tutorial_mode.py --all --offline --pretty
python scripts/refresh_framework_artifacts.py --skip-live
python scripts/e2e_real_data_smoke.py --interactive --allow-partial
make smoke_real
```

## Documentation

→ **[docs/README.md](docs/README.md)** — full documentation index

Key docs:
- [docs/quickstart.md](docs/quickstart.md) — step-by-step usage
- [docs/tutorial.md](docs/tutorial.md) — end-to-end tutorial
- [docs/data_source_coverage.md](docs/data_source_coverage.md) — coverage matrix *(generated)*
- [docs/source_recommendations.md](docs/source_recommendations.md) — use-case recommendations *(generated)*
- [docs/framework_status.md](docs/framework_status.md) — project status *(generated)*
- [docs/tefas_integration.md](docs/tefas_integration.md) — optional TEFAS integration
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — module design
- [docs/usage_with_notebooks.md](docs/usage_with_notebooks.md) — notebook workflow guide

## Notebooks

```bash
jupyter lab
```

- [notebooks/00_framework_tutorial.ipynb](notebooks/00_framework_tutorial.ipynb) — DataHub → ETL → strategy/backtest → risk/execution → portfolio
- [notebooks/01_real_data_smoke.ipynb](notebooks/01_real_data_smoke.ipynb) — coverage table + multi-source ingest smoke
- [notebooks/02_strategy_backtest_portfolio.ipynb](notebooks/02_strategy_backtest_portfolio.ipynb) — ETL + strategy/risk/execution/portfolio chain
- [notebooks/03_multi_source_asset_coverage.ipynb](notebooks/03_multi_source_asset_coverage.ipynb) — implementation status, API-key filtering, unsupported dataset behavior

## Development

```bash
make bootstrap        # install dev dependencies
make lint             # compile-check all Python
make test             # full test suite (109 tests)
make smoke            # dry-run hello-world + notebook smoke
make runbook_check    # verify runbook index
```

## Architecture

```
src/algotradeplan/
├── core/           # schemas, intent model, contracts, types
├── data/           # thin MarketData compatibility shim (DataHub/ETL/query surface)
├── portfolio/      # PortfolioManager, PositionBook, TradeLedger
├── plugins/
│   ├── data/       # shared DTO/contracts only
│   ├── risk/       # RiskEngine, NotionalGuardRiskPlugin
│   ├── strategies/ # EmaCrossAtrStop, parameter optimizer
│   ├── indicators/ # EMA, ATR, Bollinger
│   ├── connectors/ # SimulatedFillExecutionConnector
│   └── registry    # dynamic plugin loader
├── backtest/       # RealisticBacktester (equity curve, Sharpe/Sortino)
├── orchestration/  # TradeFlow, real-data autopilot pipeline
└── observability/  # StructuredLogger, InMemoryMetricsSink
```
