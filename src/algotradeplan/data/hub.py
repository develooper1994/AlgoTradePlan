"""User-friendly source discovery and ingestion API."""

from __future__ import annotations

import json
import ssl
from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from src.algotradeplan.data.adapters import build_default_adapter_registry
from src.algotradeplan.data.capabilities import SourceCapability, canonical_dataset_name, capability_map
from src.algotradeplan.data.coverage import build_coverage_table
from src.algotradeplan.data.normalize import normalize_dataset, to_data_records
from src.algotradeplan.data.provenance import ManifestProvenanceTracker
from src.algotradeplan.data.quality import CanonicalDataQualityPlugin
from src.algotradeplan.data.storage import InMemoryStorage, LocalArtifactStorage
from src.algotradeplan.plugins.data.contracts import DataRequest, DataRecord, ProvenanceRecord, QualityReport, StorageReceipt

JsonGetter = Callable[[str, dict[str, Any]], Any]
_ALLOWED_API_PREFIXES = (
    "https://fapi.binance.com/",
    "https://api.bybit.com/",
    "https://api.kraken.com/",
    "https://api.exchange.coinbase.com/",
    "https://query1.finance.yahoo.com/",
    "https://www.alphavantage.co/",
    "https://api.twelvedata.com/",
    "https://api.polygon.io/",
    "https://finnhub.io/",
    "https://data.nasdaq.com/",
    "https://cloud.iexapis.com/",
    "https://api.frankfurter.dev/",
    "https://hn.algolia.com/",
    "https://api.coingecko.com/",
    "https://stooq.com/",
    "https://api.gdeltproject.org/",
    "https://api.worldbank.org/",
    "https://data-api.ecb.europa.eu/",
    "https://api.llama.fi/",
)


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
        except Exception:  # pragma: no cover - optional dependency fallback
            return rows
        return pd.DataFrame(rows)


class DataHub:
    def __init__(
        self,
        *,
        json_getter: JsonGetter | None = None,
        quality: CanonicalDataQualityPlugin | None = None,
        storage: InMemoryStorage | LocalArtifactStorage | None = None,
        provenance: ManifestProvenanceTracker | None = None,
        artifact_root: Path | None = None,
    ) -> None:
        self._json_getter = json_getter or _default_json_getter
        storage_root = artifact_root or Path("artifacts") / "datahub"
        self._quality = quality or CanonicalDataQualityPlugin()
        self._storage = storage or LocalArtifactStorage(storage_root / "records")
        self._provenance = provenance or ManifestProvenanceTracker(storage_root / "manifests")
        self._capabilities = capability_map()
        self._adapter_registry = build_default_adapter_registry(self._json_getter)

    def sources(self) -> list[str]:
        return sorted(self._capabilities)

    def capability(self, source: str) -> SourceCapability:
        return self._capabilities[source]

    def coverage_table(self) -> list[dict[str, str]]:
        capabilities = [self._capabilities[source] for source in self.sources()]
        return build_coverage_table(capabilities)

    def discover_assets(self, source: str, limit: int = 10, **filters: Any) -> list[str]:
        capability = self._capabilities[source]
        if not capability.supports_discovery:
            return []
        try:
            symbols = self._adapter_registry.discover_assets(source, max(1, limit), **filters)
        except KeyError:
            return []
        return symbols[:limit]

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
    ) -> IngestResult:
        capability = self._capabilities[source]
        requested = [canonical_dataset_name(dataset) for dataset in datasets]
        raw_datasets = self._fetch_raw(source=source, symbol=symbol, datasets=requested, timeframe=timeframe, limit=limit)
        normalized: dict[str, list[dict[str, Any]]] = {}
        records: list[DataRecord] = []
        issues: list[dict[str, str]] = []
        dataset_coverage: dict[str, int] = {}
        asset_type = capability.asset_classes[0] if capability.asset_classes else "unknown"

        for dataset in requested:
            if dataset not in capability.datasets:
                issues.append({"source": source, "reason": f"unsupported_dataset:{dataset}"})
                dataset_coverage[dataset] = 0
                continue
            raw_payload = raw_datasets.get(dataset)
            if raw_payload is None:
                issues.append({"source": source, "reason": f"missing_dataset:{dataset}"})
                dataset_coverage[dataset] = 0
                continue
            if isinstance(raw_payload, list):
                raw_payload = raw_payload[:limit] if dataset != "kline" else raw_payload[-limit:]
            items = normalize_dataset(dataset, source, symbol, raw_payload)
            normalized[dataset] = [asdict(item) if is_dataclass(item) else dict(item) for item in items]
            dataset_coverage[dataset] = len(items)
            records.extend(to_data_records(dataset, source, asset_type, items))

        quality_report = self._quality.validate(records)
        if quality_report.issues and not allow_partial:
            empty_errors = [issue for issue in issues if issue["reason"].startswith(("unsupported_dataset", "missing_dataset"))]
            if empty_errors and not records:
                quality_report = QualityReport(
                    passed=False,
                    checks=quality_report.checks,
                    issues=quality_report.issues + [issue["reason"] for issue in empty_errors],
                )

        storage_receipts: list[StorageReceipt] = []
        provenance: ProvenanceRecord | None = None
        if store and records:
            request = DataRequest(
                dataset=",".join(requested),
                symbol=symbol,
                parameters={"timeframe": timeframe, "limit": limit, "allow_partial": allow_partial},
            )
            storage_receipts = self._storage.write(records)
            provenance = self._provenance.capture(
                request=request,
                source_plugin_id=source,
                records=records,
                storage_receipts=storage_receipts,
            )

        return IngestResult(
            source=source,
            symbol=symbol,
            requested_datasets=requested,
            dataset_coverage=dataset_coverage,
            raw_datasets=raw_datasets,
            normalized=normalized,
            records=records,
            quality_report=quality_report,
            storage_receipts=storage_receipts,
            provenance=provenance,
            source_issues=issues,
        )

    def load_market_data(
        self,
        *,
        source: str,
        symbol: str,
        dataset: str,
        timeframe: str = "1m",
        limit: int = 500,
        allow_partial: bool = False,
    ):
        return self.ingest(
            source=source,
            symbol=symbol,
            datasets=[dataset],
            timeframe=timeframe,
            limit=limit,
            allow_partial=allow_partial,
            store=False,
        ).to_feature_frame(dataset=canonical_dataset_name(dataset))

    def _fetch_raw(
        self,
        *,
        source: str,
        symbol: str,
        datasets: list[str],
        timeframe: str = "1m",
        limit: int = 500,
    ) -> dict[str, Any]:
        try:
            return self._adapter_registry.fetch_raw(
                source=source,
                symbol=symbol,
                datasets=datasets,
                timeframe=timeframe,
                limit=limit,
            )
        except KeyError:
            return {}


def _default_json_getter(url: str, params: dict[str, Any]) -> Any:
    if not url.startswith(_ALLOWED_API_PREFIXES):
        raise RuntimeError(f"URL not in allowlist: {url}")
    query = urlencode({key: value for key, value in params.items() if value is not None})
    request_url = f"{url}?{query}" if query else url
    request = Request(
        request_url,
        headers={"Accept": "application/json", "User-Agent": "AlgoTradePlanDataHub/1.0"},
    )
    with urlopen(request, timeout=20, context=ssl.create_default_context()) as response:  # nosec B310
        return json.loads(response.read().decode("utf-8"))
