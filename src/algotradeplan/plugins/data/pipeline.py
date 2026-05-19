"""Composable pipeline for data ingestion scaffolding."""

from __future__ import annotations

from dataclasses import dataclass

from src.algotradeplan.plugins.data.contracts import (
    DataRecord,
    DataRequest,
    ProvenanceRecord,
    QualityReport,
    StorageReceipt,
)
from src.algotradeplan.plugins.data.interfaces import (
    DataQualityPlugin,
    DataSourcePlugin,
    DataStoragePlugin,
    ProvenancePlugin,
)


@dataclass(frozen=True)
class IngestionResult:
    records: list[DataRecord]
    quality_report: QualityReport
    storage_receipts: list[StorageReceipt]
    provenance: ProvenanceRecord


class DataIngestionPipeline:
    def __init__(
        self,
        source: DataSourcePlugin,
        storage: DataStoragePlugin,
        quality: DataQualityPlugin,
        provenance: ProvenancePlugin,
    ) -> None:
        self.source = source
        self.storage = storage
        self.quality = quality
        self.provenance = provenance

    def ingest(self, request: DataRequest) -> IngestionResult:
        records = self.source.fetch(request)
        quality_report = self.quality.validate(records)
        if not quality_report.passed:
            raise ValueError("Data quality validation failed")

        storage_receipts = self.storage.write(records)
        provenance_record = self.provenance.capture(
            request=request,
            source_plugin_id=self.source.plugin_id,
            records=records,
            storage_receipts=storage_receipts,
        )
        return IngestionResult(
            records=records,
            quality_report=quality_report,
            storage_receipts=storage_receipts,
            provenance=provenance_record,
        )
