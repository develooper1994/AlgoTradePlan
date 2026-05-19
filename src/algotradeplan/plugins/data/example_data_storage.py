"""Example storage plugin for phase-gated data ingestion."""

from __future__ import annotations

from src.algotradeplan.plugins.data.contracts import DataRecord, StorageReceipt


class InMemoryDataStoragePlugin:
    plugin_id = "in_memory_data_storage"

    def __init__(self) -> None:
        self.batches: list[list[DataRecord]] = []

    def write(self, records: list[DataRecord]) -> list[StorageReceipt]:
        self.batches.append(records)
        batch_id = str(len(self.batches))
        return [
            StorageReceipt(
                storage_id=batch_id,
                location=f"memory://raw/{batch_id}",
                record_keys=[record.key for record in records],
            )
        ]
