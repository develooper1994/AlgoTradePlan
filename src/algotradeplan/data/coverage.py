"""Coverage-table helpers for DataHub."""

from __future__ import annotations

from collections.abc import Iterable

from src.algotradeplan.data.capabilities import SourceCapability


def _yes_no(value: bool) -> str:
    return "yes" if value else "no"


def build_coverage_table(capabilities: Iterable[SourceCapability]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for capability in capabilities:
        dataset_set = set(capability.datasets)
        asset_set = set(capability.asset_classes)
        rows.append(
            {
                "Source": capability.source,
                "Asset discovery": _yes_no(capability.supports_discovery),
                "Kline/OHLCV": _yes_no("kline" in dataset_set),
                "Trades": _yes_no("trade" in dataset_set),
                "Orderbook": _yes_no("orderbook" in dataset_set),
                "Funding": _yes_no("funding" in dataset_set),
                "Equity": _yes_no("equity" in asset_set),
                "ETF": _yes_no("etf" in asset_set),
                "Forex": _yes_no("forex" in asset_set),
                "Options": _yes_no("options" in asset_set),
                "Macro": _yes_no("macro" in dataset_set or "macro" in asset_set),
                "News": _yes_no("news" in dataset_set or "news" in asset_set),
                "Requires API key": _yes_no(capability.requires_api_key),
                "API key env": capability.api_key_env or "",
            }
        )
    return rows
