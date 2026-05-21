"""Thin MarketData-backed source discovery and ingestion API."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from src.algotradeplan.data.capabilities import SourceCapability, canonical_dataset_name
from src.algotradeplan.marketdata_client import MarketDataBridgeClient
from src.algotradeplan.plugins.data.contracts import DataRecord, DataRequest, ProvenanceRecord, QualityReport, StorageReceipt

JsonGetter = Callable[[str, dict[str, Any]], Any]


@dataclass(frozen=True)
class IngestResult:
    source: str
    symbol: str | None
    requested_datasets: list[str]
    dataset_coverage: dict[str, int]
    raw_datasets: dict[str, Any]
    normalized: dict[str, list[dict[str, Any]]]
    records: list[DataRecord]
    quality_report: QualityReport
    storage_receipts: list[StorageReceipt] = field(default_factory=list)
    provenance: ProvenanceRecord | None = None
    source_issues: list[dict[str, str]] = field(default_factory=list)

    def to_feature_frame(self, dataset: str | None = None):
        rows = []
        for record in self.records:
            if dataset and record.metadata.get("dataset") != dataset:
                continue
            rows.append(record.payload)
        try:
            import pandas as pd  # type: ignore
        except Exception:
            return rows
        return pd.DataFrame(rows)


class DataHub:
    def __init__(
        self,
        *,
        json_getter: JsonGetter | None = None,
        quality: object | None = None,
        storage: object | None = None,
        provenance: object | None = None,
        artifact_root: Path | None = None,
        client: MarketDataBridgeClient | None = None,
    ) -> None:
        # Deprecated compatibility parameters are kept to avoid breaking callers
        # during MarketData bridge migration.
        del json_getter, quality, storage, provenance, artifact_root
        self._client = client or MarketDataBridgeClient()

    def sources(self) -> list[str]:
        rows = self._client.query("sources", default=[])
        return [str(item) for item in rows] if isinstance(rows, list) else []

    def capability(self, source: str) -> SourceCapability:
        row = self._client.query("capability", {"source": source}, default={})
        if not isinstance(row, dict):
            row = {}
        return SourceCapability(
            source=str(row.get("source", source)),
            asset_classes=[str(item) for item in row.get("asset_classes", []) if isinstance(item, str)],
            datasets=[canonical_dataset_name(str(item)) for item in row.get("datasets", []) if isinstance(item, str)],
            supports_discovery=bool(row.get("supports_discovery", False)),
            supports_history=bool(row.get("supports_history", False)),
            supports_realtime=bool(row.get("supports_realtime", False)),
            requires_api_key=bool(row.get("requires_api_key", False)),
            api_key_env=row.get("api_key_env") if isinstance(row.get("api_key_env"), str) else None,
            rate_limit_notes=str(row.get("rate_limit_notes", "")),
            quality_level=str(row.get("quality_level", "")),
            implemented_datasets=[canonical_dataset_name(str(item)) for item in row.get("implemented_datasets", []) if isinstance(item, str)],
            metadata_only_datasets=[canonical_dataset_name(str(item)) for item in row.get("metadata_only_datasets", []) if isinstance(item, str)],
            implementation_status=str(row.get("implementation_status", "")),
            notes=str(row.get("notes", "")),
            extra_metadata=row.get("extra_metadata") if isinstance(row.get("extra_metadata"), dict) else {},
        )

    def coverage_table(self) -> list[dict[str, str]]:
        rows = self._client.query("coverage_table", default=[])
        return [item for item in rows if isinstance(item, dict)] if isinstance(rows, list) else []

    def dataset_status(self, source: str, dataset: str) -> str:
        result = self._client.query("dataset_status", {"source": source, "dataset": dataset}, default="unsupported")
        return str(result)

    def asset_status(self, source: str, asset_class: str) -> str:
        result = self._client.query("asset_status", {"source": source, "asset_class": asset_class}, default="unsupported")
        return str(result)

    def supports(self, source: str, dataset: str, *, require_live: bool = False) -> bool:
        result = self._client.query(
            "supports",
            {"source": source, "dataset": dataset, "require_live": require_live},
            default=False,
        )
        return bool(result)

    def sources_for(
        self,
        dataset: str | None = None,
        asset_class: str | None = None,
        require_live: bool = False,
    ) -> list[str]:
        rows = self._client.query(
            "sources_for",
            {"dataset": dataset, "asset_class": asset_class, "require_live": require_live},
            default=[],
        )
        return [str(item) for item in rows] if isinstance(rows, list) else []

    def available_datasets(self, source: str, *, implemented_only: bool = False) -> list[str]:
        rows = self._client.query(
            "available_datasets",
            {"source": source, "implemented_only": implemented_only},
            default=[],
        )
        return [str(item) for item in rows] if isinstance(rows, list) else []

    def requires_api_key(self, source: str) -> bool:
        return self.capability(source).requires_api_key

    def api_key_env(self, source: str) -> str | None:
        return self.capability(source).api_key_env

    def compare_sources(self, sources: list[str], datasets: list[str] | None = None) -> list[dict[str, str]]:
        rows = self._client.query(
            "compare_sources",
            {"sources": sources, "datasets": datasets},
            default=[],
        )
        return [item for item in rows if isinstance(item, dict)] if isinstance(rows, list) else []

    def source_summary(self, source: str) -> dict[str, Any]:
        row = self._client.query("source_summary", {"source": source}, default={})
        return row if isinstance(row, dict) else {}

    def best_sources_for(
        self,
        *,
        dataset: str,
        asset_class: str | None = None,
        prefer_live: bool = True,
        allow_api_key: bool = True,
        include_metadata_only: bool = False,
        limit: int | None = None,
    ) -> list[dict[str, str]]:
        rows = self._client.query(
            "best_sources_for",
            {
                "dataset": dataset,
                "asset_class": asset_class,
                "prefer_live": prefer_live,
                "allow_api_key": allow_api_key,
                "include_metadata_only": include_metadata_only,
                "limit": limit,
            },
            default=[],
        )
        return [item for item in rows if isinstance(item, dict)] if isinstance(rows, list) else []

    def explain_source(self, source: str) -> dict[str, Any]:
        row = self._client.query("explain_source", {"source": source}, default={})
        return row if isinstance(row, dict) else {}

    def explain_dataset(self, dataset: str) -> dict[str, Any]:
        row = self._client.query("explain_dataset", {"dataset": dataset}, default={})
        return row if isinstance(row, dict) else {}

    def recommend_sources(
        self,
        use_case: str,
        *,
        allow_api_key: bool = True,
        prefer_live: bool = True,
        limit: int | None = None,
    ) -> list[dict[str, str]]:
        rows = self._client.query(
            "recommend_sources",
            {
                "use_case": use_case,
                "allow_api_key": allow_api_key,
                "prefer_live": prefer_live,
                "limit": limit,
            },
            default=[],
        )
        return [item for item in rows if isinstance(item, dict)] if isinstance(rows, list) else []

    def supported_use_cases(self) -> list[str]:
        rows = self._client.query("supported_use_cases", default=[])
        return [str(item) for item in rows] if isinstance(rows, list) else []

    def dataset_sources_matrix(self, datasets: list[str] | None = None) -> list[dict[str, str]]:
        rows = self._client.query("dataset_sources_matrix", {"datasets": datasets}, default=[])
        return [item for item in rows if isinstance(item, dict)] if isinstance(rows, list) else []

    def asset_sources_matrix(self, asset_classes: list[str] | None = None) -> list[dict[str, str]]:
        rows = self._client.query("asset_sources_matrix", {"asset_classes": asset_classes}, default=[])
        return [item for item in rows if isinstance(item, dict)] if isinstance(rows, list) else []

    def discover_assets(self, source: str, limit: int = 10, **filters: Any) -> list[str]:
        rows = self._client.query(
            "discover_assets",
            {"source": source, "limit": limit, "filters": filters},
            default=[],
        )
        if not isinstance(rows, list):
            return []
        return [str(item) for item in rows[:max(1, limit)]]

    def ingest(
        self,
        *,
        source: str,
        symbol: str,
        datasets: list[str],
        timeframe: str = "1m",
        limit: int = 500,
        allow_partial: bool = False,
        store: bool = True,
        **fetch_options: Any,
    ) -> IngestResult:
        payload = {
            "source": source,
            "symbol": symbol,
            "datasets": datasets,
            "timeframe": timeframe,
            "limit": limit,
            "allow_partial": allow_partial,
            "store": store,
            "fetch_options": fetch_options,
        }
        row = self._client.invoke("ingest", payload)
        return _parse_ingest_result(source=source, symbol=symbol, requested_datasets=datasets, row=row)

    def load_market_data(
        self,
        *,
        source: str,
        symbol: str,
        dataset: str,
        timeframe: str = "1m",
        limit: int = 500,
        allow_partial: bool = False,
        **fetch_options: Any,
    ):
        row = self._client.invoke(
            "load_market_data",
            {
                "source": source,
                "symbol": symbol,
                "dataset": dataset,
                "timeframe": timeframe,
                "limit": limit,
                "allow_partial": allow_partial,
                "fetch_options": fetch_options,
            },
        )
        if isinstance(row, list):
            return row
        if isinstance(row, dict) and isinstance(row.get("rows"), list):
            return row["rows"]
        return []


def _parse_ingest_result(*, source: str, symbol: str, requested_datasets: list[str], row: Any) -> IngestResult:
    if not isinstance(row, dict):
        row = {}
    records = [_parse_data_record(item) for item in row.get("records", []) if isinstance(item, dict)]
    quality = _parse_quality_report(row.get("quality_report"))
    storage_receipts = [_parse_storage_receipt(item) for item in row.get("storage_receipts", []) if isinstance(item, dict)]
    provenance = _parse_provenance(row.get("provenance"))
    source_issues = [item for item in row.get("source_issues", []) if isinstance(item, dict)] if isinstance(row.get("source_issues"), list) else []
    normalized = row.get("normalized") if isinstance(row.get("normalized"), dict) else {}
    raw_datasets = row.get("raw_datasets") if isinstance(row.get("raw_datasets"), dict) else {}
    dataset_coverage = {
        str(name): int(count)
        for name, count in (row.get("dataset_coverage") or {}).items()
        if isinstance(name, str)
    } if isinstance(row.get("dataset_coverage"), dict) else {}

    return IngestResult(
        source=str(row.get("source", source)),
        symbol=row.get("symbol") if isinstance(row.get("symbol"), str) else symbol,
        requested_datasets=[str(item) for item in row.get("requested_datasets", requested_datasets)],
        dataset_coverage=dataset_coverage,
        raw_datasets=raw_datasets,
        normalized=normalized,
        records=records,
        quality_report=quality,
        storage_receipts=storage_receipts,
        provenance=provenance,
        source_issues=[{"source": str(item.get("source", "")), "reason": str(item.get("reason", ""))} for item in source_issues],
    )


def _parse_data_record(row: dict[str, Any]) -> DataRecord:
    return DataRecord(
        key=str(row.get("key", "")),
        observed_at=str(row.get("observed_at", "")),
        domain=str(row.get("domain", "")),
        source=str(row.get("source", "")),
        asset_type=str(row.get("asset_type", "")),
        payload=row.get("payload") if isinstance(row.get("payload"), dict) else {},
        metadata=row.get("metadata") if isinstance(row.get("metadata"), dict) else {},
    )


def _parse_quality_report(row: Any) -> QualityReport:
    if not isinstance(row, dict):
        row = {}
    return QualityReport(
        passed=bool(row.get("passed", False)),
        checks=[str(item) for item in row.get("checks", []) if isinstance(item, str)],
        issues=[str(item) for item in row.get("issues", []) if isinstance(item, str)],
    )


def _parse_storage_receipt(row: dict[str, Any]) -> StorageReceipt:
    return StorageReceipt(
        storage_id=str(row.get("storage_id", "")),
        location=str(row.get("location", "")),
        record_keys=[str(item) for item in row.get("record_keys", []) if isinstance(item, str)],
    )


def _parse_provenance(row: Any) -> ProvenanceRecord | None:
    if not isinstance(row, dict):
        return None
    request_row = row.get("request") if isinstance(row.get("request"), dict) else {}
    request = DataRequest(
        dataset=str(request_row.get("dataset", "")),
        symbol=request_row.get("symbol") if isinstance(request_row.get("symbol"), str) else None,
        start_at=request_row.get("start_at") if isinstance(request_row.get("start_at"), str) else None,
        end_at=request_row.get("end_at") if isinstance(request_row.get("end_at"), str) else None,
        parameters=request_row.get("parameters") if isinstance(request_row.get("parameters"), dict) else {},
    )
    storage_receipts = [_parse_storage_receipt(item) for item in row.get("storage_receipts", []) if isinstance(item, dict)]
    return ProvenanceRecord(
        request=request,
        source_plugin_id=str(row.get("source_plugin_id", "")),
        storage_receipts=storage_receipts,
        record_keys=[str(item) for item in row.get("record_keys", []) if isinstance(item, str)],
        revision=str(row.get("revision", "")),
    )
