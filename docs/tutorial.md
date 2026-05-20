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
```

Adımlar:
1. DataHub oluştur, kaynakları listele.
2. Coverage / capability query API kullan.
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

etl = ETL(hub)
frame = etl.load_market_data(source="offline_fallback", symbol="BTCUSDT", dataset="kline", limit=50)
```

## Coverage query examples

```python
hub.available_datasets("binance_futures", implemented_only=True)
hub.asset_status("world_bank", "macro")
hub.supports("binance_futures", "funding", require_live=True)
hub.source_summary("coingecko")
```

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
