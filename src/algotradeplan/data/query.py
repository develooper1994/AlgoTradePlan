"""Compatibility query helpers delegated to MarketData bridge."""

from __future__ import annotations

from typing import Any

from src.algotradeplan.marketdata_client import MarketDataBridgeClient


def _client() -> MarketDataBridgeClient:
    return MarketDataBridgeClient()


def supported_use_cases() -> list[str]:
    rows = _client().query("supported_use_cases", default=[])
    return [str(item) for item in rows] if isinstance(rows, list) else []


def dataset_status_for_source(_capabilities: Any, source: str, dataset: str) -> str:
    result = _client().query("dataset_status", {"source": source, "dataset": dataset}, default="unsupported")
    return str(result)


def asset_status_for_source(_capabilities: Any, source: str, asset_class: str) -> str:
    result = _client().query("asset_status", {"source": source, "asset_class": asset_class}, default="unsupported")
    return str(result)


def supports(_capabilities: Any, source: str, dataset: str, *, require_live: bool = False) -> bool:
    result = _client().query(
        "supports",
        {"source": source, "dataset": dataset, "require_live": require_live},
        default=False,
    )
    return bool(result)


def sources_for(
    _capabilities: Any,
    dataset: str | None = None,
    asset_class: str | None = None,
    require_live: bool = False,
) -> list[str]:
    result = _client().query(
        "sources_for",
        {"dataset": dataset, "asset_class": asset_class, "require_live": require_live},
        default=[],
    )
    return [str(item) for item in result] if isinstance(result, list) else []


def available_datasets(_capabilities: Any, source: str, *, implemented_only: bool = False) -> list[str]:
    result = _client().query(
        "available_datasets",
        {"source": source, "implemented_only": implemented_only},
        default=[],
    )
    return [str(item) for item in result] if isinstance(result, list) else []


def compare_sources(_capabilities: Any, sources: list[str], datasets: list[str] | None = None) -> list[dict[str, str]]:
    result = _client().query(
        "compare_sources",
        {"sources": sources, "datasets": datasets},
        default=[],
    )
    return [item for item in result if isinstance(item, dict)] if isinstance(result, list) else []


def source_summary(_capabilities: Any, source: str) -> dict[str, Any]:
    result = _client().query("source_summary", {"source": source}, default={})
    return result if isinstance(result, dict) else {}


def best_sources_for(
    _capabilities: Any,
    *,
    dataset: str,
    asset_class: str | None = None,
    prefer_live: bool = True,
    allow_api_key: bool = True,
    include_metadata_only: bool = False,
    limit: int | None = None,
) -> list[dict[str, str]]:
    result = _client().query(
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
    return [item for item in result if isinstance(item, dict)] if isinstance(result, list) else []


def explain_source(_capabilities: Any, source: str) -> dict[str, Any]:
    result = _client().query("explain_source", {"source": source}, default={})
    return result if isinstance(result, dict) else {}


def explain_dataset(_capabilities: Any, dataset: str) -> dict[str, Any]:
    result = _client().query("explain_dataset", {"dataset": dataset}, default={})
    return result if isinstance(result, dict) else {}


def recommend_sources(
    _capabilities: Any,
    use_case: str,
    *,
    allow_api_key: bool = True,
    prefer_live: bool = True,
    limit: int | None = None,
) -> list[dict[str, str]]:
    result = _client().query(
        "recommend_sources",
        {
            "use_case": use_case,
            "allow_api_key": allow_api_key,
            "prefer_live": prefer_live,
            "limit": limit,
        },
        default=[],
    )
    return [item for item in result if isinstance(item, dict)] if isinstance(result, list) else []


def dataset_sources_matrix(_capabilities: Any, datasets: list[str] | None = None) -> list[dict[str, str]]:
    result = _client().query("dataset_sources_matrix", {"datasets": datasets}, default=[])
    return [item for item in result if isinstance(item, dict)] if isinstance(result, list) else []


def asset_sources_matrix(_capabilities: Any, asset_classes: list[str] | None = None) -> list[dict[str, str]]:
    result = _client().query("asset_sources_matrix", {"asset_classes": asset_classes}, default=[])
    return [item for item in result if isinstance(item, dict)] if isinstance(result, list) else []
