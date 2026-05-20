# Framework Status

Generated: 2026-05-20T10:20:58.477359+00:00
framework_score: 78/100

## Module Status
- [x] **DataHub** — Capability query API and ETL facade are available.
- [x] **adapters** — 23 registered sources via adapter registry.
- [x] **coverage docs** — Generated data source coverage document is present.
- [x] **notebooks** — Required tutorial/smoke notebooks present.
- [x] **strategy** — Example strategy/backtest integration exists.
- [x] **backtest** — Realistic backtester with summary metrics exists.
- [x] **risk** — Structured RiskEngine exists.
- [x] **execution** — Simulated execution connector exists.
- [x] **portfolio** — PortfolioManager and ledger exist.
- [x] **docs** — Tutorial guide present.
- [x] **research/preflight** — Preflight runnability checks available.
- [x] **data_health_report** — Dataset health report CLI available.
- [x] **strategy_catalog** — Strategy capability catalog document available.
- [x] **experiment_registry** — Experiment artifact registry available.
- [x] **recipes** — Executable recipe runner and sample recipe folder available.

## Completed Components
- DataHub
- adapters
- coverage docs
- notebooks
- strategy
- backtest
- risk
- execution
- portfolio
- docs
- research/preflight
- data_health_report
- strategy_catalog
- experiment_registry
- recipes

## Pending Components
- _none_

## Priority Next Actions
### P0
- Run framework status (`python scripts/framework_status.py --write-doc --write-plan`).
- Regenerate coverage docs (`python scripts/generate_data_coverage_doc.py`).
- Run offline tutorial walkthrough (`python scripts/tutorial_mode.py --all --offline --write-doc`).
- Generate offline data health (`python scripts/data_health_report.py --source offline_fallback --symbol BTCUSDT --datasets kline funding --offline`).
- Record offline demo experiment (`python scripts/run_experiment.py --source offline_fallback --symbol BTCUSDT --strategy ema_cross_atr_stop --offline`).
- Dry-run executable recipe (`python scripts/run_recipe.py recipes/crypto_momentum.yaml --dry-run`).
- Refresh stale or missing artifacts listed in the artifact state section.
- Run real-data smoke (`python scripts/e2e_real_data_smoke.py --interactive --allow-partial`).
### P1
- Add and document recommend_sources / best_sources_for query recipes in tutorial and quickstart docs.
- Expose source and dataset explanation snippets in user-facing docs/notebooks.
- Keep capability, recommendation, and coverage indices synchronized with generated docs.
- Keep strategy catalog metadata synchronized with preflight checks and recipes.
- Document preflight/data-health/experiment workflow in tutorial and README.
### P2
- Improve CoinGecko synthetic OHLCV transparency and dataset notes.
- Improve DefiLlama TVL/protocol metadata clarity for macro/fundamentals.
- Reduce metadata-only adapters in priority order: coingecko, defillama, quandl.
- Complete missing strategy metadata entries in strategy catalog.
### P3
- Expand data-quality checks and monitor quality issues over time.
- Harden backtest/risk/portfolio integration scenarios.
- Refine storage/provenance artifact layout and retention policy.
- Expand recipe coverage for additional multi-source and asset-class workflows.

## Top Metadata-only Adapter Candidates
- coingecko (metadata_only_datasets=1, status=partial)
- defillama (metadata_only_datasets=1, status=partial)
- quandl (metadata_only_datasets=1, status=api_key)

## Recommended next adapter work
- _none_

## Use-case coverage gaps
- _none_

## Artifact State
- docs/framework_status.md: fresh (0d old)
- docs/next_actions.md: fresh (0d old)
- docs/data_source_coverage.md: fresh (0d old)
- docs/source_recommendations.md: fresh (0d old)
- artifacts/tutorial/tutorial_walkthrough.md: fresh (0d old)
- artifacts/real_data_smoke_report.json: missing
- artifacts/data_health/offline_fallback_BTCUSDT_health.md: fresh (0d old)
- artifacts/experiments: fresh (0d old)

## Risks / Technical Debt
- API-key and plan-scoped providers can report broader theoretical coverage than current implemented datasets.
- Real-data examples remain sensitive to upstream API availability and throttling.

## Coverage Summary
- source count: 23
- live sources count: 10
- api_key sources count: 8
- metadata_only sources count: 3
- fallback sources count: 1
- public/fallback use-case coverage count: 10
- unsupported dataset requests behavior: [{"source": "offline_fallback", "reason": "unsupported_dataset:news"}]

## Validation Commands
- `make lint`
- `make test`
- `make smoke`
- `make runbook_check`
- `python scripts/framework_status.py --write-doc --write-plan`
- `python scripts/generate_data_coverage_doc.py`
- `python scripts/tutorial_mode.py --all --offline --write-doc`
- `python scripts/preflight_check.py --source coingecko --symbol bitcoin --datasets kline funding --strategy ema_cross_atr_stop`
- `python scripts/data_health_report.py --source offline_fallback --symbol BTCUSDT --datasets kline funding --offline`
- `python scripts/run_experiment.py --source offline_fallback --symbol BTCUSDT --strategy ema_cross_atr_stop --offline`
- `python scripts/run_recipe.py recipes/crypto_momentum.yaml --dry-run`
- `python scripts/e2e_real_data_smoke.py --interactive --allow-partial`
