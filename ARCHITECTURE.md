# Architecture

## High-Level Planes
- **Offline Plane**: ingest -> normalize -> store -> backtest/research
- **Online Plane**: live ingest -> strategy -> risk -> execution -> reconciliation
- **Side Systems**: monitoring, audit, alerts, emergency stop, metadata and policy checks

## Canonical Module Boundaries
- `core`: ids, types, contracts, clock
- `data_ingestion`: csv/excel/tabular adapters
- `plugins`: strategy/model/data/indicator/connector/risk extension points
- `tests_support`: fake/mock adapters for deterministic testing

## State Safety
- explicit order intent model
- deterministic ids
- reconciliation-first workflow before live promotion
