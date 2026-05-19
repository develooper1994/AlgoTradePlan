"""Storage backends for DataHub ingestion artifacts."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from src.algotradeplan.plugins.data.contracts import DataRecord, StorageReceipt


class InMemoryStorage:
    plugin_id = "datahub_in_memory_storage"

    def __init__(self) -> None:
        self.batches: list[list[DataRecord]] = []

    def write(self, records: list[DataRecord]) -> list[StorageReceipt]:
        self.batches.append(list(records))
        batch_id = str(len(self.batches))
        return [
            StorageReceipt(
                storage_id=batch_id,
                location=f"memory://normalized/{batch_id}",
                record_keys=[record.key for record in records],
            )
        ]


class LocalArtifactStorage:
    plugin_id = "datahub_local_artifact_storage"

    def __init__(self, root_path: Path) -> None:
        self.root_path = root_path

    def write(self, records: list[DataRecord]) -> list[StorageReceipt]:
        self.root_path.mkdir(parents=True, exist_ok=True)
        batch_id = datetime.now(UTC).strftime("%Y%m%d%H%M%S%f")
        target = self.root_path / f"ingestion-{batch_id}.jsonl"
        with target.open("w", encoding="utf-8") as handle:
            for record in records:
                handle.write(
                    json.dumps(
                        {
                            "key": record.key,
                            "observed_at": record.observed_at,
                            "domain": record.domain,
                            "source": record.source,
                            "asset_type": record.asset_type,
                            "payload": record.payload,
                            "metadata": record.metadata,
                        }
                    )
                    + "\n"
                )
        return [
            StorageReceipt(
                storage_id=batch_id,
                location=str(target),
                record_keys=[record.key for record in records],
            )
        ]
