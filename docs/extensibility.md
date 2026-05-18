# Extensibility Guide

Plugin folders:
- `plugins/strategies`
- `plugins/models`
- `plugins/data`
- `plugins/indicators`
- `plugins/connectors`
- `plugins/risk`

Rules:
1. Implement protocol from `src/algotradeplan/plugins/interfaces.py`.
2. Add tests using fakes under `tests/adapters`.
3. Register plugin metadata with unique id/version.
