# Extending AlgoTradePlan

## Plugin Points
- `src/algotradeplan/plugins/strategies`
- `src/algotradeplan/plugins/models`
- `src/algotradeplan/plugins/data`
- `src/algotradeplan/plugins/data/curated`
- `src/algotradeplan/plugins/indicators`
- `src/algotradeplan/plugins/connectors`
- `src/algotradeplan/plugins/risk`
- `src/algotradeplan/plugins/reconciliation`
- `src/algotradeplan/orchestration`
- `src/algotradeplan/observability`
- `src/algotradeplan/backtest`

## Data Extension Flow
1. choose the domain root (`market`, `news`, `macro`, `curated`, or a future approved domain)
2. implement a source adapter returning normalized `DataRecord` objects
3. reuse or extend quality, storage, and provenance plugins
4. add deterministic tests in `tests/adapters`
5. add/update dummy fixture coverage in `tests/fixtures/data_ingestion_assets.json`
6. update the active phase file and data strategy doc when contracts or policies change

## Example Extension
- market example: `/src/algotradeplan/plugins/data/market/example_market_source.py`
- production market source registry: `/src/algotradeplan/plugins/data/market/public_source_registry.py`
- news example: `/src/algotradeplan/plugins/data/news/example_news_source.py`
- macro example: `/src/algotradeplan/plugins/data/macro/example_macro_source.py`
- curated feature view: `/src/algotradeplan/plugins/data/curated/feature_view.py`
- pipeline test: `/tests/adapters/test_data_ingestion_pipeline_examples.py`
- trade flow orchestrator: `/src/algotradeplan/orchestration/trade_flow.py`
- replay harness: `/src/algotradeplan/backtest/replay.py`
- drift reconciler: `/src/algotradeplan/plugins/reconciliation/drift_reconciler.py`
- dynamic auto-register loader: `/src/algotradeplan/plugins/registry.py`

## Test and Migration Guidance
- tests should cover successful ingestion and failed quality validation
- each new asset/source plugin should have at least one dummy fixture entry and adapter assertion
- contract changes require migration notes before downstream plugins are updated
- preserve backwards compatibility within a phase when practical; otherwise document the upgrade path

## Upgrade Checklist
- document the contract delta
- update example plugins
- update adapter and smoke tests
- refresh runbooks and decision log entries

## Contributor Checklist (Phase 15)
Before opening a PR, confirm:
- [ ] active phase doc allows the change
- [ ] new plugin root has at least one example and deterministic test
- [ ] each new asset/source plugin has dummy fixture coverage in `tests/fixtures/`
- [ ] `make lint` succeeds
- [ ] `make test` succeeds
- [ ] `make smoke` succeeds
- [ ] `make runbook_check` succeeds
- [ ] `python scripts/deploy_check.py --repo-root .` succeeds
- [ ] `python scripts/security_check.py --repo-root .` succeeds
- [ ] relevant runbook(s) updated under `/docs/runbooks/`
- [ ] phase doc validation checklist updated
