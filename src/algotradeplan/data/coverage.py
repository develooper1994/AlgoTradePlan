"""Coverage-table helpers for DataHub."""

from __future__ import annotations

from collections.abc import Iterable

from src.algotradeplan.data.capabilities import SourceCapability


DATASET_COLUMNS = {
    "Ticker": "tick",
    "OHLCV/Kline": "kline",
    "Kline/OHLCV": "kline",
    "Trades": "trade",
    "Orderbook": "orderbook",
    "Funding": "funding",
    "Macro": "macro",
    "News": "news",
    "Fundamentals": "fundamentals",
    "Corporate actions": "corporate_actions",
    "Fund NAV": "fund_nav",
    "Fund profile": "fund_profile",
    "Fund return": "fund_return",
    "Fund allocation": "fund_allocation",
    "Fund size": "fund_size",
    "Fund fee": "fund_fee",
    "Fund announcement": "fund_announcement",
    "Fund statistics": "fund_statistics",
}

ASSET_COLUMNS = {
    "Equity": "equity",
    "ETF": "etf",
    "Forex": "forex",
    "Index": "index",
    "Futures": "futures",
    "Options": "options",
    "Macro asset": "macro",
}


def _bool_status(value: bool) -> str:
    return "live" if value else "unsupported"


def _implemented(capability: SourceCapability) -> set[str]:
    return {item.lower() for item in capability.implemented_datasets}


def _metadata_only(capability: SourceCapability) -> set[str]:
    return {item.lower() for item in capability.metadata_only_datasets}


def dataset_status(capability: SourceCapability, dataset: str) -> str:
    dataset = dataset.lower()
    if dataset not in {item.lower() for item in capability.datasets}:
        return "unsupported"
    if dataset in _metadata_only(capability):
        return "metadata_only"
    if dataset in _implemented(capability):
        if capability.implementation_status in {"api_key", "api_key_or_plan", "partial", "fallback"}:
            return capability.implementation_status
        return "live"
    if capability.implementation_status == "metadata_only":
        return "metadata_only"
    if capability.requires_api_key:
        return capability.implementation_status if capability.implementation_status in {"api_key", "api_key_or_plan"} else "api_key"
    return "partial"


def asset_status(capability: SourceCapability, asset_type: str) -> str:
    asset_type = asset_type.lower()
    if asset_type not in {item.lower() for item in capability.asset_classes}:
        return "unsupported"
    if capability.implementation_status in {"api_key", "api_key_or_plan", "partial", "fallback", "metadata_only"}:
        return capability.implementation_status
    return "live"


def build_coverage_table(capabilities: Iterable[SourceCapability]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for capability in capabilities:
        rows.append(
            {
                "Source": capability.source,
                "Asset classes": ", ".join(capability.asset_classes),
                "Asset discovery": _bool_status(capability.supports_discovery),
                **{column: dataset_status(capability, dataset) for column, dataset in DATASET_COLUMNS.items()},
                "Equity": asset_status(capability, "equity"),
                "ETF": asset_status(capability, "etf"),
                "Forex": asset_status(capability, "forex"),
                "Index": asset_status(capability, "index"),
                "Futures": asset_status(capability, "futures"),
                "Options": asset_status(capability, "options"),
                "Mutual fund": asset_status(capability, "mutual_fund"),
                "Pension fund": asset_status(capability, "pension_fund"),
                "Requires API key": "yes" if capability.requires_api_key else "no",
                "API key env": capability.api_key_env or "",
                "Implementation status": capability.implementation_status,
                "Notes": capability.notes or capability.rate_limit_notes,
            }
        )
    return rows
