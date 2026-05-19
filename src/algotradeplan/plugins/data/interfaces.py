"""Interfaces for data ingestion, storage, quality, and provenance plugins."""

from __future__ import annotations

from typing import Protocol

from src.algotradeplan.plugins.data.contracts import (
    DataRecord,
    DataRequest,
    ProvenanceRecord,
    QualityReport,
    StorageReceipt,
)


class DataSourcePlugin(Protocol):
    plugin_id: str
    domain: str

    def fetch(self, request: DataRequest) -> list[DataRecord]:
        """Return normalized records for a given request."""


class DataStoragePlugin(Protocol):
    plugin_id: str

    def write(self, records: list[DataRecord]) -> list[StorageReceipt]:
        """Persist records to a target storage layer."""


class DataQualityPlugin(Protocol):
    plugin_id: str

    def validate(self, records: list[DataRecord]) -> QualityReport:
        """Evaluate ingestion records before they are committed."""


class ProvenancePlugin(Protocol):
    plugin_id: str

    def capture(
        self,
        *,
        request: DataRequest,
        source_plugin_id: str,
        records: list[DataRecord],
        storage_receipts: list[StorageReceipt],
    ) -> ProvenanceRecord:
        """Persist provenance metadata for replay and audit."""
