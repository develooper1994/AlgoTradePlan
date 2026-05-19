"""Provenance helpers for DataHub ingestion manifests."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from src.algotradeplan.plugins.data.contracts import DataRecord, DataRequest, ProvenanceRecord, StorageReceipt


class ManifestProvenanceTracker:
    plugin_id = "datahub_provenance_manifest"

    def __init__(self, manifest_root: Path | None = None) -> None:
        self.manifest_root = manifest_root
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
            revision=f"manifest-{len(self.entries) + 1}",
        )
        self.entries.append(entry)
        if self.manifest_root is not None:
            self.manifest_root.mkdir(parents=True, exist_ok=True)
            target = self.manifest_root / f"{entry.revision}.json"
            target.write_text(json.dumps(provenance_to_dict(entry), indent=2), encoding="utf-8")
        return entry


def provenance_to_dict(record: ProvenanceRecord | None) -> dict[str, object]:
    if record is None:
        return {}
    return {
        "request": asdict(record.request),
        "source_plugin_id": record.source_plugin_id,
        "storage_receipts": [asdict(receipt) for receipt in record.storage_receipts],
        "record_keys": list(record.record_keys),
        "revision": record.revision,
    }
