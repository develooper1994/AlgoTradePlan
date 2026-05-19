# Extending AlgoTradePlan

## Plugin Points
- `src/algotradeplan/plugins/strategies`
- `src/algotradeplan/plugins/models`
- `src/algotradeplan/plugins/data`
- `src/algotradeplan/plugins/indicators`
- `src/algotradeplan/plugins/connectors`
- `src/algotradeplan/plugins/risk`
- `src/algotradeplan/plugins/reconciliation`

## Data Extension Flow
1. choose the domain root (`market`, `news`, `macro`, or a future approved domain)
2. implement a source adapter returning normalized `DataRecord` objects
3. reuse or extend quality, storage, and provenance plugins
4. add deterministic tests in `tests/adapters`
5. update the active phase file and data strategy doc when contracts or policies change

## Example Extension
- market example: `/src/algotradeplan/plugins/data/market/example_market_source.py`
- news example: `/src/algotradeplan/plugins/data/news/example_news_source.py`
- macro example: `/src/algotradeplan/plugins/data/macro/example_macro_source.py`
- pipeline test: `/tests/adapters/test_data_ingestion_pipeline_examples.py`

## Test and Migration Guidance
- tests should cover successful ingestion and failed quality validation
- contract changes require migration notes before downstream plugins are updated
- preserve backwards compatibility within a phase when practical; otherwise document the upgrade path

## Upgrade Checklist
- document the contract delta
- update example plugins
- update adapter and smoke tests
- refresh runbooks and decision log entries
