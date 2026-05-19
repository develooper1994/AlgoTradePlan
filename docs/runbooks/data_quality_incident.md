# Data Quality Incident Runbook

## Purpose
Handle empty batches, schema drift, or missing join-key metadata during ingestion.

## Detection
- quality plugin fails validation
- downstream join or replay checks detect incomplete metadata

## Immediate Actions
1. stop promotion of the affected batch
2. preserve source request parameters and failure evidence
3. capture the impacted plugin id, dataset, and environment

## Recovery
1. inspect the failing source payload
2. patch or roll back the adapter or mapping
3. re-run ingestion and confirm a new provenance revision was created

## Post-Incident
- update phase documentation if the contract or checklist changed
- add or strengthen tests reproducing the failure
