"""Provenance-driven replay harness for dry-run promotion (Phase 12)."""

from __future__ import annotations

from dataclasses import dataclass

from src.algotradeplan.plugins.data.contracts import (
    DataRecord,
    DataRequest,
    ProvenanceRecord,
)


@dataclass(frozen=True)
class ReplayResult:
    request: DataRequest
    canonical_records: list[DataRecord]
    replayed_records: list[DataRecord]
    parity: bool
    revision: str


class ReplayHarness:
    """Re-run an ingestion request against a source and verify parity.

    The harness enforces the Phase-12 promotion gate: a dry-run promotion
    is only approved when the replayed records are identical to the canonical
    records originally captured for the same provenance revision.
    """

    def __init__(self, source: object) -> None:
        self.source = source

    def replay(
        self,
        provenance: ProvenanceRecord,
        canonical_records: list[DataRecord],
    ) -> ReplayResult:
        replayed = list(self.source.fetch(provenance.request))  # type: ignore[attr-defined]
        parity = replayed == canonical_records
        return ReplayResult(
            request=provenance.request,
            canonical_records=canonical_records,
            replayed_records=replayed,
            parity=parity,
            revision=provenance.revision,
        )

    def promote(self, result: ReplayResult) -> dict[str, object]:
        if not result.parity:
            raise ValueError(
                f"Replay parity check failed for revision {result.revision}; "
                "promotion blocked."
            )
        return {
            "promoted": True,
            "revision": result.revision,
            "record_count": len(result.canonical_records),
        }
