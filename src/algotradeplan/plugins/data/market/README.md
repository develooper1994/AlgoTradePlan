# Market Data Plugins

- CCXT live discovery/ingestion: `/src/algotradeplan/plugins/data/market/ccxt_market_source.py`
- Public/API-key provider registry (Binance, Bybit, Kraken, Coinbase, Yahoo, Alpha Vantage, Twelve Data, Polygon, Finnhub, Quandl, IEX): `/src/algotradeplan/plugins/data/market/public_source_registry.py`
- Static deterministic source: `/src/algotradeplan/plugins/data/market/static_market_batch_source.py`
- Runtime demo: `python scripts/e2e_real_data_smoke.py --max-symbols 5 --interactive`
- Extension note: add new adapters in `public_source_registry.py` (or new ccxt exchange IDs in `CcxtMarketDataAgent`) without changing orchestration flow.
