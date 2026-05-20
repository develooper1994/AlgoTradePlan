"""Programmatic source capability query helpers."""

from __future__ import annotations

from typing import Any

from src.algotradeplan.data.capabilities import SourceCapability, canonical_dataset_name
from src.algotradeplan.data.coverage import asset_status, dataset_status


def _canonical_source(source: str) -> str:
    return source.lower().strip()


def _canonical_asset_class(asset_class: str) -> str:
    return asset_class.lower().strip()


def dataset_status_for_source(capabilities: dict[str, SourceCapability], source: str, dataset: str) -> str:
    capability = capabilities[_canonical_source(source)]
    return dataset_status(capability, canonical_dataset_name(dataset))


def asset_status_for_source(capabilities: dict[str, SourceCapability], source: str, asset_class: str) -> str:
    capability = capabilities[_canonical_source(source)]
    return asset_status(capability, _canonical_asset_class(asset_class))


def supports(capabilities: dict[str, SourceCapability], source: str, dataset: str, *, require_live: bool = False) -> bool:
    status = dataset_status_for_source(capabilities, source, dataset)
    if require_live:
        return status == "live"
    return status != "unsupported" and status != "metadata_only"


def sources_for(
    capabilities: dict[str, SourceCapability],
    *,
    dataset: str | None = None,
    asset_class: str | None = None,
    require_live: bool = False,
) -> list[str]:
    matched: list[str] = []
    for source in sorted(capabilities):
        if dataset is not None:
            status = dataset_status_for_source(capabilities, source, dataset)
            if require_live and status != "live":
                continue
            if not require_live and status == "unsupported":
                continue
        if asset_class is not None:
            status = asset_status_for_source(capabilities, source, asset_class)
            if require_live and status != "live":
                continue
            if not require_live and status == "unsupported":
                continue
        matched.append(source)
    return matched


def available_datasets(capabilities: dict[str, SourceCapability], source: str, *, implemented_only: bool = False) -> list[str]:
    capability = capabilities[_canonical_source(source)]
    datasets = capability.implemented_datasets if implemented_only else capability.datasets
    return sorted({canonical_dataset_name(item) for item in datasets})


def compare_sources(
    capabilities: dict[str, SourceCapability],
    sources: list[str],
    datasets: list[str] | None = None,
) -> list[dict[str, str]]:
    dataset_names = [canonical_dataset_name(item) for item in (datasets or [])]
    if not dataset_names:
        seen: set[str] = set()
        for source in sources:
            seen.update(capabilities[_canonical_source(source)].datasets)
        dataset_names = sorted(seen)
    rows: list[dict[str, str]] = []
    for source in sources:
        capability = capabilities[_canonical_source(source)]
        row = {
            "source": capability.source,
            "implementation_status": capability.implementation_status,
            "requires_api_key": "yes" if capability.requires_api_key else "no",
        }
        for dataset in dataset_names:
            row[dataset] = dataset_status(capability, dataset)
        rows.append(row)
    return rows


def source_summary(capabilities: dict[str, SourceCapability], source: str) -> dict[str, Any]:
    capability = capabilities[_canonical_source(source)]
    dataset_statuses = {
        dataset: dataset_status(capability, dataset)
        for dataset in sorted({canonical_dataset_name(item) for item in capability.datasets})
    }
    asset_statuses = {
        asset_class: asset_status(capability, asset_class)
        for asset_class in sorted({item.lower() for item in capability.asset_classes})
    }
    return {
        "source": capability.source,
        "asset_classes": list(capability.asset_classes),
        "datasets": list(capability.datasets),
        "implemented_datasets": list(capability.implemented_datasets),
        "metadata_only_datasets": list(capability.metadata_only_datasets),
        "dataset_statuses": dataset_statuses,
        "asset_statuses": asset_statuses,
        "supports_discovery": capability.supports_discovery,
        "supports_history": capability.supports_history,
        "supports_realtime": capability.supports_realtime,
        "requires_api_key": capability.requires_api_key,
        "api_key_env": capability.api_key_env,
        "implementation_status": capability.implementation_status,
        "notes": capability.notes or capability.rate_limit_notes,
        "extra_metadata": dict(capability.extra_metadata),
    }
