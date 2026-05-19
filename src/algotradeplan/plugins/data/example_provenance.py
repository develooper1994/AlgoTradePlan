"""Example provenance plugin for audit-ready data ingestion."""

from __future__ import annotations

from src.algotradeplan.plugins.data.contracts import (
    DataRecord,
    DataRequest,
    ProvenanceRecord,
    StorageReceipt,
)


class ExampleProvenancePlugin:
    plugin_id = "example_provenance"

    def __init__(self) -> None:
        self.entries: list[ProvenanceRecord] = []

    def capture(
        self,
        *,
        request: DataRequest,
        source_plugin_id: str,
        records: list[DataRecord],
        storage_receipts: list[StorageReceipt],
    ) -> ProvenanceRecord:
        entry = ProvenanceRecord(
            request=request,
            source_plugin_id=source_plugin_id,
            storage_receipts=storage_receipts,
            record_keys=[record.key for record in records],
            revision=f"rev-{len(self.entries) + 1}",
        )
        self.entries.append(entry)
        return entry
