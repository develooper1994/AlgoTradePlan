"""Curated feature view derived from canonical ingestion outputs.

The feature view is intentionally deterministic and replayable: it consumes
canonical ``DataRecord`` batches and any matching ``ProvenanceRecord`` entries
and emits feature ``DataRecord`` objects that link back to upstream provenance.
"""

from __future__ import annotations

from dataclasses import dataclass

from src.algotradeplan.plugins.data.contracts import (
    DataRecord,
    ProvenanceRecord,
)


@dataclass(frozen=True)
class FeatureViewResult:
    feature_records: list[DataRecord]
    upstream_revisions: list[str]


class ExampleFeatureViewPlugin:
    """Compute a deterministic feature value (mean close) per symbol.

    Notes:
        - preserves raw lineage by recording upstream provenance revisions in
          each feature record's metadata
        - feature output is fully reproducible from the same input batch and
          provenance record, making the lane replay-safe
    """

    plugin_id = "example_feature_view"
    domain = "curated"
    feature_name = "mean_close"

    def build(
        self,
        canonical_records: list[DataRecord],
        provenance: ProvenanceRecord,
    ) -> FeatureViewResult:
        grouped: dict[str, list[float]] = {}
        observed_at: dict[str, str] = {}
        for record in canonical_records:
            key = str(record.metadata.get("join_key") or record.payload.get("symbol") or record.key)
            close = record.payload.get("close")
            if close is None:
                continue
            grouped.setdefault(key, []).append(float(close))
            observed_at.setdefault(key, record.observed_at)

        feature_records: list[DataRecord] = []
        for join_key, closes in sorted(grouped.items()):
            mean_close = sum(closes) / len(closes)
            feature_records.append(
                DataRecord(
                    key=f"{self.feature_name}:{join_key}:{provenance.revision}",
                    observed_at=observed_at[join_key],
                    domain=self.domain,
                    source=self.plugin_id,
                    asset_type="feature",
                    payload={
                        "feature": self.feature_name,
                        "join_key": join_key,
                        "value": mean_close,
                        "sample_size": len(closes),
                    },
                    metadata={
                        "join_key": join_key,
                        "lake_zone": "curated",
                        "upstream_revision": provenance.revision,
                        "upstream_source_plugin_id": provenance.source_plugin_id,
                    },
                )
            )

        return FeatureViewResult(
            feature_records=feature_records,
            upstream_revisions=[provenance.revision],
        )
