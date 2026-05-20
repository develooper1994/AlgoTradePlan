# Tutorial Mode

Bu doküman framework'ü baştan sona anlamak için en hızlı yolu anlatır.

## Kurulum

```bash
pip install -e ".[data]"
make lint
make test
make smoke
```

## Offline tutorial

Deterministic ve internet gerektirmeyen akış:

```bash
python scripts/tutorial_mode.py --list
python scripts/tutorial_mode.py --all --offline
python scripts/tutorial_mode.py --step 4 --offline
python scripts/tutorial_mode.py --all --offline --pretty
python scripts/tutorial_mode.py --all --offline --markdown
python scripts/tutorial_mode.py --all --offline --write-doc
```

Adımlar:
1. DataHub oluştur, kaynakları listele.
2. Coverage / capability / recommendation query API kullan.
3. Asset discovery yap.
4. Veri ingest et.
5. Normalize, quality ve provenance incele.
6. Strategy sinyalini üret.
7. Backtest metriklerini göster.
8. Risk kararını göster.
9. Simulated execution fill üret.
10. Portfolio snapshot ve ledger incele.
11. Report dosyasını aç.

## DataHub basics

```python
from algotradeplan.data import DataHub, ETL

hub = DataHub()
hub.sources()
hub.dataset_status("coingecko", "kline")
hub.sources_for(dataset="news")
hub.compare_sources(["binance_futures", "coingecko", "stooq", "world_bank"])
hub.recommend_sources("crypto_spot_kline", allow_api_key=False)
hub.recommend_sources("macro_indicators", allow_api_key=False)

etl = ETL(hub)
frame = etl.load_market_data(source="offline_fallback", symbol="BTCUSDT", dataset="kline", limit=50)
```

## Coverage query examples

```python
hub.available_datasets("binance_futures", implemented_only=True)
hub.asset_status("world_bank", "macro")
hub.supports("binance_futures", "funding", require_live=True)
hub.source_summary("coingecko")
hub.recommend_sources("crypto_spot_kline", allow_api_key=False)
hub.recommend_sources("crypto_perp_funding", allow_api_key=False)
hub.recommend_sources("macro_indicators", allow_api_key=False)
hub.recommend_sources("public_news", allow_api_key=False)
hub.best_sources_for(dataset="kline", asset_class="equity", allow_api_key=False)
hub.best_sources_for(dataset="kline", asset_class="crypto_spot", allow_api_key=False)
hub.explain_source("coingecko")
hub.explain_dataset("funding")
hub.dataset_sources_matrix(["kline", "news", "macro", "fundamentals"])
hub.asset_sources_matrix(["crypto_spot", "equity", "macro"])
```

## Research preflight / health / experiment / recipe

```bash
python scripts/preflight_check.py --source coingecko --symbol bitcoin --datasets kline funding --strategy ema_cross_atr_stop
python scripts/data_health_report.py --source offline_fallback --symbol BTCUSDT --datasets kline funding --offline
python scripts/run_experiment.py --source offline_fallback --symbol BTCUSDT --strategy ema_cross_atr_stop --offline
python scripts/run_recipe.py recipes/crypto_momentum.yaml
python scripts/run_recipe.py recipes/funding_carry.yaml --dry-run
```

- **Preflight**: source + dataset + strategy kombinasyonu çalıştırılabilir mi?
- **Data health**: ingest sonrası kalite ve issue sayaçları.
- **Strategy catalog**: `docs/strategy_catalog.md` ve `src/algotradeplan/strategies/catalog.py`.
- **Experiment registry**: `artifacts/experiments/<experiment_id>/`.
- **Recipes**: `recipes/*.yaml` ile tekrar çalıştırılabilir araştırma akışları.

CLI output modes:
- Default: JSON (backward compatible, machine-friendly).
- `--pretty`: human-friendly terminal walkthrough.
- `--markdown`: markdown walkthrough on stdout.
- `--write-doc`: generate `artifacts/tutorial/tutorial_walkthrough.md`.
- Step 2 now includes **Source recommendation examples** for no-key/public-first workflows.

## ETL → Strategy/Backtest → Risk/Execution/Portfolio

- `DataHub` veya `ETL` ile veri çek.
- `EmaCrossAtrStopStrategyPlugin` ile sinyal üret.
- `TradeFlow` veya `RiskEngine` + `SimulatedFillExecutionConnectorPlugin` ile risk/execution zincirini çalıştır.
- `PortfolioManager` ile ledger ve NAV incele.

## Notebook önerileri

- `notebooks/00_framework_tutorial.ipynb`
- `notebooks/01_real_data_smoke.ipynb`
- `notebooks/02_strategy_backtest_portfolio.ipynb`
- `notebooks/03_multi_source_asset_coverage.ipynb`

## Sık sorunlar

- Canlı kaynaklar rate-limit verebilir; önce `--offline` ile başlayın.
- API-key gerektiren kaynakları `hub.api_key_env(source)` ile kontrol edin.
- Kaynak bir dataset'i desteklemiyorsa `source_issues` içinde `unsupported_dataset:*` veya `metadata_only_dataset:*` görürsünüz.
