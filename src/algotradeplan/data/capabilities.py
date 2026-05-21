"""Compatibility capability DTOs delegated to MarketData bridge."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.algotradeplan.marketdata_client import MarketDataBridgeClient

STATUS_VALUES = (
    "live",
    "partial",
    "api_key",
    "api_key_or_plan",
    "metadata_only",
    "fallback",
    "unsupported",
)


_DATASET_ALIASES = {
    "ohlcv": "kline",
    "ticker": "tick",
    "trades": "trade",
    "book": "orderbook",
    "macro_snapshot": "macro",
    "macro_series": "macro",
}


@dataclass(frozen=True)
class SourceCapability:
    source: str
    asset_classes: list[str] = field(default_factory=list)
    datasets: list[str] = field(default_factory=list)
    supports_discovery: bool = False
    supports_history: bool = False
    supports_realtime: bool = False
    requires_api_key: bool = False
    api_key_env: str | None = None
    rate_limit_notes: str = ""
    quality_level: str = ""
    implemented_datasets: list[str] = field(default_factory=list)
    metadata_only_datasets: list[str] = field(default_factory=list)
    implementation_status: str = ""
    notes: str = ""
    extra_metadata: dict[str, Any] = field(default_factory=dict)


def canonical_dataset_name(dataset: str) -> str:
    normalized = dataset.strip().lower()
    return _DATASET_ALIASES.get(normalized, normalized)


def capability_map(*, client: MarketDataBridgeClient | None = None) -> dict[str, SourceCapability]:
    bridge = client or MarketDataBridgeClient()
    rows = bridge.query("capabilities", default=[])
    mapping: dict[str, SourceCapability] = {}
    if not isinstance(rows, list):
        return mapping
    for row in rows:
        if not isinstance(row, dict):
            continue
        source = str(row.get("source", "")).strip()
        if not source:
            continue
        mapping[source] = SourceCapability(
            source=source,
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
    return mapping


CAPABILITIES: tuple[SourceCapability, ...] = tuple()


__all__ = [
    "STATUS_VALUES",
    "SourceCapability",
    "CAPABILITIES",
    "canonical_dataset_name",
    "capability_map",
]
