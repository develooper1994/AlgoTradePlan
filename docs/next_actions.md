# Next Actions

## P0 - Validation / Artifacts
- Run framework status (`python scripts/framework_status.py --write-doc --write-plan`).
- Regenerate coverage docs (`python scripts/generate_data_coverage_doc.py`).
- Run offline tutorial walkthrough (`python scripts/tutorial_mode.py --all --offline --write-doc`).
- Generate offline data health (`python scripts/data_health_report.py --source offline_fallback --symbol BTCUSDT --datasets kline funding --offline`).
- Record offline demo experiment (`python scripts/run_experiment.py --source offline_fallback --symbol BTCUSDT --strategy ema_cross_atr_stop --offline`).
- Dry-run executable recipe (`python scripts/run_recipe.py recipes/crypto_momentum.yaml --dry-run`).
- Refresh stale or missing artifacts listed in the artifact state section.
- Run real-data smoke (`python scripts/e2e_real_data_smoke.py --interactive --allow-partial`).

## P1 - Capability UX
- Add and document recommend_sources / best_sources_for query recipes in tutorial and quickstart docs.
- Expose source and dataset explanation snippets in user-facing docs/notebooks.
- Keep capability, recommendation, and coverage indices synchronized with generated docs.
- Keep strategy catalog metadata synchronized with preflight checks and recipes.
- Document preflight/data-health/experiment workflow in tutorial and README.

## P2 - Reduce metadata-only adapters
- Improve CoinGecko synthetic OHLCV transparency and dataset notes.
- Improve DefiLlama TVL/protocol metadata clarity for macro/fundamentals.
- Reduce metadata-only adapters in priority order: coingecko, defillama, quandl.
- Complete missing strategy metadata entries in strategy catalog.

## P3 - Production hardening
- Expand data-quality checks and monitor quality issues over time.
- Harden backtest/risk/portfolio integration scenarios.
- Refine storage/provenance artifact layout and retention policy.
- Expand recipe coverage for additional multi-source and asset-class workflows.

## P1 - Use-case coverage gaps

- _none_
