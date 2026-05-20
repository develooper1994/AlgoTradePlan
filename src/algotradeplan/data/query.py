"""Programmatic source capability query helpers."""

from __future__ import annotations

from typing import Any

from src.algotradeplan.data.capabilities import SourceCapability, canonical_dataset_name
from src.algotradeplan.data.coverage import asset_status, dataset_status


def _canonical_source(source: str) -> str:
    return source.lower().strip()


def _canonical_asset_class(asset_class: str) -> str:
    return asset_class.lower().strip()


def _get_capability(capabilities: dict[str, SourceCapability], source: str) -> SourceCapability:
    normalized = _canonical_source(source)
    try:
        return capabilities[normalized]
    except KeyError as exc:
        raise KeyError(f"Unknown source: {source}") from exc


def dataset_status_for_source(capabilities: dict[str, SourceCapability], source: str, dataset: str) -> str:
    capability = _get_capability(capabilities, source)
    return dataset_status(capability, canonical_dataset_name(dataset))


def asset_status_for_source(capabilities: dict[str, SourceCapability], source: str, asset_class: str) -> str:
    capability = _get_capability(capabilities, source)
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
    capability = _get_capability(capabilities, source)
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
        capability = _get_capability(capabilities, source)
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
    capability = _get_capability(capabilities, source)
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


def best_sources_for(
    capabilities: dict[str, SourceCapability],
    *,
    dataset: str,
    asset_class: str | None = None,
    prefer_live: bool = True,
    allow_api_key: bool = True,
    include_metadata_only: bool = False,
    limit: int | None = None,
) -> list[dict[str, str]]:
    canonical_dataset = canonical_dataset_name(dataset)
    canonical_asset = _canonical_asset_class(asset_class) if asset_class else None
    dataset_priority = {
        "live": 0 if prefer_live else 1,
        "partial": 1 if prefer_live else 0,
        "fallback": 2,
        "api_key": 3,
        "api_key_or_plan": 4,
        "metadata_only": 5,
    }
    rows: list[tuple[int, str, dict[str, str]]] = []
    for source_name in sorted(capabilities):
        capability = capabilities[source_name]
        dataset_value = dataset_status(capability, canonical_dataset)
        if dataset_value == "unsupported":
            continue
        if dataset_value in {"api_key", "api_key_or_plan"} and not allow_api_key:
            continue
        if dataset_value == "metadata_only" and not include_metadata_only:
            continue
        if dataset_value not in dataset_priority:
            continue
        asset_value = asset_status(capability, canonical_asset) if canonical_asset else "n/a"
        if canonical_asset and asset_value == "unsupported":
            continue
        row = {
            "source": capability.source,
            "dataset_status": dataset_value,
            "asset_status": asset_value,
            "requires_api_key": "yes" if capability.requires_api_key else "no",
            "implementation_status": capability.implementation_status,
            "notes": capability.notes or capability.rate_limit_notes,
        }
        rows.append((dataset_priority[dataset_value], capability.source, row))

    ranked = [item[2] for item in sorted(rows, key=lambda item: (item[0], item[1]))]
    if limit is None:
        return ranked
    return ranked[: max(0, limit)]


def explain_source(capabilities: dict[str, SourceCapability], source: str) -> dict[str, Any]:
    summary = source_summary(capabilities, source)
    capability = _get_capability(capabilities, source)
    summary["dataset_rankings"] = best_sources_for(
        capabilities,
        dataset="kline",
        asset_class=capability.asset_classes[0] if capability.asset_classes else None,
        include_metadata_only=True,
        limit=10,
    )
    return summary


def explain_dataset(capabilities: dict[str, SourceCapability], dataset: str) -> dict[str, Any]:
    canonical = canonical_dataset_name(dataset)
    by_status: dict[str, list[str]] = {
        "live": [],
        "partial": [],
        "fallback": [],
        "api_key": [],
        "api_key_or_plan": [],
        "metadata_only": [],
    }
    for source_name in sorted(capabilities):
        status = dataset_status_for_source(capabilities, source_name, canonical)
        if status in by_status:
            by_status[status].append(source_name)
    return {
        "dataset": canonical,
        "status_index": by_status,
        "best_sources_no_api_key": best_sources_for(
            capabilities,
            dataset=canonical,
            allow_api_key=False,
            include_metadata_only=False,
            limit=5,
        ),
        "best_sources_with_api_key": best_sources_for(
            capabilities,
            dataset=canonical,
            allow_api_key=True,
            include_metadata_only=False,
            limit=5,
        ),
    }


def dataset_sources_matrix(
    capabilities: dict[str, SourceCapability],
    datasets: list[str] | None = None,
) -> list[dict[str, str]]:
    names = (
        sorted({canonical_dataset_name(dataset) for dataset in datasets})
        if datasets
        else sorted({canonical_dataset_name(item) for capability in capabilities.values() for item in capability.datasets})
    )
    rows: list[dict[str, str]] = []
    for source_name in sorted(capabilities):
        capability = capabilities[source_name]
        row = {
            "source": capability.source,
            "implementation_status": capability.implementation_status,
            "requires_api_key": "yes" if capability.requires_api_key else "no",
        }
        for name in names:
            row[name] = dataset_status(capability, name)
        rows.append(row)
    return rows


def asset_sources_matrix(
    capabilities: dict[str, SourceCapability],
    asset_classes: list[str] | None = None,
) -> list[dict[str, str]]:
    names = (
        sorted({_canonical_asset_class(asset_class) for asset_class in asset_classes})
        if asset_classes
        else sorted({item.lower() for capability in capabilities.values() for item in capability.asset_classes})
    )
    rows: list[dict[str, str]] = []
    for source_name in sorted(capabilities):
        capability = capabilities[source_name]
        row = {
            "source": capability.source,
            "implementation_status": capability.implementation_status,
            "requires_api_key": "yes" if capability.requires_api_key else "no",
        }
        for name in names:
            row[name] = asset_status(capability, name)
        rows.append(row)
    return rows
