# Framework Status

Generated: 2026-05-20T07:23:02.637345+00:00

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

## Next Actions
- Reduce metadata-only coverage by extending adapters for: alpha_vantage, coingecko, defillama, finnhub, iex_cloud.
- Run `python scripts/e2e_real_data_smoke.py --interactive --allow-partial` to refresh the E2E smoke artifact.

## Risks / Technical Debt
- API-key and plan-scoped providers can report broader theoretical coverage than current implemented datasets.
- Real-data examples remain sensitive to upstream API availability and throttling.

## Coverage Summary
- live sources count: 10
- api_key sources count: 8
- metadata_only sources count: 0
- fallback sources count: 1
- unsupported dataset requests behavior: [{"source": "offline_fallback", "reason": "unsupported_dataset:news"}]
