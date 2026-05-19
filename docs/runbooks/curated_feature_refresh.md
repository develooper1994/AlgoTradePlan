# Curated Feature Refresh Runbook

## Purpose
Refresh curated/research feature views from approved canonical records while
preserving raw lineage and replay determinism.

## Preconditions
- canonical ingestion run for the target dataset is approved
- matching provenance revision id is available
- feature view plugin is registered under `src/algotradeplan/plugins/data/curated/`

## Procedure
1. select the canonical batch and associated `ProvenanceRecord`
2. invoke the feature view plugin's `build()` with the canonical records and
   provenance record
3. publish the resulting feature `DataRecord` objects into the curated lake zone
4. log the upstream revision id in the feature metadata

## Validation
- every feature record metadata contains `upstream_revision` and
  `upstream_source_plugin_id`
- rerunning `build()` with the same inputs produces identical output
- curated tests pass: `tests/adapters/test_curated_feature_view.py`

## Rollback / Recovery
- drop curated batch and re-run from canonical records and provenance entry

## Escalation
- if upstream revision is missing, open the data quality incident runbook
