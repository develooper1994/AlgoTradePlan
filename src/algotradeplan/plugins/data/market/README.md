# Market Data Plugins

- CCXT live discovery/ingestion: `/src/algotradeplan/plugins/data/market/ccxt_market_source.py`
- Static deterministic source: `/src/algotradeplan/plugins/data/market/static_market_batch_source.py`
- Runtime demo: `python scripts/e2e_real_data_smoke.py --max-symbols 5 --interactive`
- Extension note: add new exchange IDs in `CcxtMarketDataAgent` without changing orchestration flow.
