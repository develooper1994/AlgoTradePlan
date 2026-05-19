# Data Strategy

## Goals
- support multi-lake, multi-source, multi-asset growth without rewriting ingestion contracts
- normalize market, news, and macro records behind shared schemas and join-key conventions
- make quality, revisioning, provenance, replay, and audit mandatory in the ingestion path

## Lake Layout
| Layer | Purpose | Example Contents |
| --- | --- | --- |
| Landing | immutable source capture | raw API payloads, vendor files, headlines, release dumps |
| Canonical | normalized records | bars, news events, macro releases with common metadata |
| Curated | research and serving views | joined features, factor tables, model-ready datasets |
| Audit | replay and lineage | provenance records, revisions, run ids, quality outcomes |

## Supported Source Families
| Domain | Examples | Primary Join Keys | Extension Root |
| --- | --- | --- | --- |
| Market | OHLCV, order book, trades, corporate actions | `symbol`, venue, timestamp | `/src/algotradeplan/plugins/data/market` |
| News | headlines, filings, transcripts, sentiment | `symbol`, issuer, event time | `/src/algotradeplan/plugins/data/news` |
| Macro | CPI, rates, payrolls, calendar events | series id, country, release time | `/src/algotradeplan/plugins/data/macro` |

## Canonical Schema Policy
Every normalized record should carry:
- `key`: deterministic record identifier
- `observed_at`: source event timestamp
- `domain`: market, news, or macro
- `source`: upstream adapter name
- `asset_type`: asset or dataset class
- `payload`: normalized business fields
- `metadata`: join key, lake zone, revision, provenance hooks

## Ingestion Protocol
1. source plugin fetches normalized `DataRecord` batches from a `DataRequest`
2. quality plugin validates batch presence and required metadata
3. storage plugin persists the accepted batch to a raw or canonical target
4. provenance plugin records request, source plugin id, storage receipts, and revision id
5. downstream research/strategy phases can consume only approved canonical outputs

## Quality Standards
- reject empty batches for approved production ingestion paths
- require join-key metadata for cross-domain linking
- keep validation results as explicit artifacts, not only logs
- add domain-specific checks incrementally per phase (freshness, schema drift, duplicates, null policy)

## Revision, Audit, and Replay
- each committed batch receives a revision id
- provenance must retain request parameters and storage receipt locations
- replay consumers should be able to reconstruct a batch from canonical storage plus provenance records
- quality outcomes are part of the audit trail

## Storage Policy
- phase 1 uses lightweight in-memory or local placeholder storage abstractions
- later phases may back storage plugins with object stores, databases, or lakehouse tables
- storage backends must preserve append-only raw history even when canonical views are re-derived

## Extension Guide Summary
To add a new source or asset family:
1. implement `DataSourcePlugin` in the appropriate domain root
2. return normalized `DataRecord` objects with stable join-key metadata
3. wire the plugin through the shared quality, storage, and provenance pipeline
4. add deterministic tests for the example or production adapter
5. document the new source in the active phase file and decision log if the contract changes

## Phase-1 Deliverables Present in Code
- shared contracts: `/src/algotradeplan/plugins/data/contracts.py`
- shared interfaces: `/src/algotradeplan/plugins/data/interfaces.py`
- ingestion pipeline scaffold: `/src/algotradeplan/plugins/data/pipeline.py`
- domain examples: market, news, macro under `/src/algotradeplan/plugins/data/`
