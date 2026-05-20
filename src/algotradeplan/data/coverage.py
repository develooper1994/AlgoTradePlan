"""Coverage-table helpers for DataHub."""

from __future__ import annotations

from collections.abc import Iterable

from src.algotradeplan.data.capabilities import SourceCapability


def _bool_status(value: bool) -> str:
    return "live" if value else "unsupported"


def _effective_implemented(capability: SourceCapability) -> set[str]:
    return set(capability.implemented_datasets or capability.datasets)


def _metadata_only(capability: SourceCapability) -> set[str]:
    return set(capability.metadata_only_datasets)


def _dataset_status(capability: SourceCapability, dataset: str) -> str:
    if dataset not in capability.datasets:
        return "unsupported"
    if dataset in _metadata_only(capability):
        return "metadata_only"
    if dataset in _effective_implemented(capability):
        if capability.implementation_status in {"api_key", "api_key_or_plan"}:
            return capability.implementation_status
        if capability.implementation_status == "fallback":
            return "fallback"
        if capability.implementation_status == "partial":
            return "partial"
        return "live"
    if capability.requires_api_key:
        return "api_key"
    return "partial"


def _asset_status(capability: SourceCapability, asset_type: str) -> str:
    if asset_type not in capability.asset_classes:
        return "unsupported"
    if capability.implementation_status == "metadata_only":
        return "metadata_only"
    if capability.implementation_status in {"api_key", "api_key_or_plan"}:
        return capability.implementation_status
    if capability.implementation_status == "fallback":
        return "fallback"
    if capability.implementation_status == "partial":
        return "partial"
    return "live"


def build_coverage_table(capabilities: Iterable[SourceCapability]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for capability in capabilities:
        rows.append(
            {
                "Source": capability.source,
                "Asset classes": ", ".join(capability.asset_classes),
                "Asset discovery": _bool_status(capability.supports_discovery),
                "Ticker": _dataset_status(capability, "tick"),
                "OHLCV/Kline": _dataset_status(capability, "kline"),
                "Kline/OHLCV": _dataset_status(capability, "kline"),
                "Trades": _dataset_status(capability, "trade"),
                "Orderbook": _dataset_status(capability, "orderbook"),
                "Funding": _dataset_status(capability, "funding"),
                "Equity": _asset_status(capability, "equity"),
                "ETF": _asset_status(capability, "etf"),
                "Forex": _asset_status(capability, "forex"),
                "Index": _asset_status(capability, "index"),
                "Futures": _asset_status(capability, "futures"),
                "Options": _asset_status(capability, "options"),
                "Macro": _dataset_status(capability, "macro"),
                "News": _dataset_status(capability, "news"),
                "Fundamentals": _dataset_status(capability, "fundamentals"),
                "Corporate actions": _dataset_status(capability, "corporate_actions"),
                "Requires API key": "yes" if capability.requires_api_key else "no",
                "API key env": capability.api_key_env or "",
                "Implementation status": capability.implementation_status,
                "Notes": capability.notes or capability.rate_limit_notes,
            }
        )
    return rows
