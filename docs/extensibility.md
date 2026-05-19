# Extensibility Guide

Canonical extension guidance now lives in `/docs/extending.md`.

Plugin folders:
- `plugins/strategies`
- `plugins/models`
- `plugins/data`
- `plugins/indicators`
- `plugins/connectors`
- `plugins/risk`
- `plugins/reconciliation`

Rules:
1. Implement protocol from `src/algotradeplan/plugins/interfaces.py`.
2. Add tests using fakes under `tests/adapters`.
3. Register plugin metadata with unique id/version.

Examples:
- plugin examples: `src/algotradeplan/plugins/**/example_*.py`
- tests: `tests/adapters/test_plugin_examples.py`
- runbook: `docs/runbook_masterlist.md`
- detailed guide: `docs/extending.md`
