# Framework Status

Generated: 2026-05-20T08:31:45.457148+00:00
framework_score: 70/100

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

## Pending Components
- _none_

## Priority Next Actions
### P0
- Run framework status (`python scripts/framework_status.py --write-doc --write-plan`).
- Regenerate coverage docs (`python scripts/generate_data_coverage_doc.py`).
- Run offline tutorial walkthrough (`python scripts/tutorial_mode.py --all --offline --write-doc`).
- Refresh stale or missing artifacts listed in the artifact state section.
- Run real-data smoke (`python scripts/e2e_real_data_smoke.py --interactive --allow-partial`).
### P1
- Add and document best_sources_for query recipes in tutorial and quickstart docs.
- Expose source and dataset explanation snippets in user-facing docs/notebooks.
- Keep capability and coverage indices synchronized with generated docs.
### P2
- Improve CoinGecko synthetic OHLCV transparency and dataset notes.
- Improve DefiLlama TVL/protocol metadata clarity for macro/fundamentals.
- Reduce metadata-only adapters in priority order: finnhub, iex_cloud, polygon_io, quandl, alpha_vantage.
### P3
- Expand data-quality checks and monitor quality issues over time.
- Harden backtest/risk/portfolio integration scenarios.
- Refine storage/provenance artifact layout and retention policy.

## Top Metadata-only Adapter Candidates
- finnhub (metadata_only_datasets=2, status=api_key)
- iex_cloud (metadata_only_datasets=2, status=api_key)
- polygon_io (metadata_only_datasets=2, status=api_key_or_plan)
- quandl (metadata_only_datasets=2, status=api_key)
- alpha_vantage (metadata_only_datasets=1, status=api_key)
- coingecko (metadata_only_datasets=1, status=partial)
- defillama (metadata_only_datasets=1, status=partial)

## Artifact State
- docs/framework_status.md: fresh (0d old)
- docs/next_actions.md: fresh (0d old)
- docs/data_source_coverage.md: fresh (0d old)
- artifacts/tutorial/tutorial_walkthrough.md: fresh (0d old)
- artifacts/real_data_smoke_report.json: missing

## Risks / Technical Debt
- API-key and plan-scoped providers can report broader theoretical coverage than current implemented datasets.
- Real-data examples remain sensitive to upstream API availability and throttling.

## Coverage Summary
- source count: 23
- live sources count: 10
- api_key sources count: 8
- metadata_only sources count: 7
- fallback sources count: 1
- unsupported dataset requests behavior: [{"source": "offline_fallback", "reason": "unsupported_dataset:news"}]

## Validation Commands
- `make lint`
- `make test`
- `make smoke`
- `make runbook_check`
- `python scripts/framework_status.py --write-doc --write-plan`
- `python scripts/generate_data_coverage_doc.py`
- `python scripts/tutorial_mode.py --all --offline --write-doc`
- `python scripts/e2e_real_data_smoke.py --interactive --allow-partial`
