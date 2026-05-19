# Daily Data Ingestion Runbook

## Purpose
Run the approved ingestion workflow for market, news, and macro batches.

## Preconditions
- active phase allows ingestion updates
- source credentials and environment are configured
- the relevant source, quality, storage, and provenance plugins are available

## Procedure
1. confirm the target dataset and source plugin ids
2. execute the ingestion workflow
3. verify quality passed and storage receipts were produced
4. record provenance revision ids for the run

## Validation
- batch is non-empty
- join-key metadata is present
- provenance revision and storage locations are captured

## Escalation
- open the data quality incident runbook if validation fails
