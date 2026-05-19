"""Contracts for extensible data ingestion plugins."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class DataRequest:
    dataset: str
    symbol: str | None = None
    start_at: str | None = None
    end_at: str | None = None
    parameters: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class DataRecord:
    key: str
    observed_at: str
    domain: str
    source: str
    asset_type: str
    payload: dict[str, Any]
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class QualityReport:
    passed: bool
    checks: list[str]
    issues: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class StorageReceipt:
    storage_id: str
    location: str
    record_keys: list[str]


@dataclass(frozen=True)
class ProvenanceRecord:
    request: DataRequest
    source_plugin_id: str
    storage_receipts: list[StorageReceipt]
    record_keys: list[str]
    revision: str
