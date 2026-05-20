"""Adapter that wraps plugin-level market source registry adapters."""

from __future__ import annotations

from typing import Any, Callable

from src.algotradeplan.plugins.data.market import build_market_source_registry
from src.algotradeplan.plugins.data.market.public_source_registry import JsonGetter, MarketSourceAdapter


class MarketRegistrySourceAdapter:
    def __init__(self, market_adapter: MarketSourceAdapter, json_getter: JsonGetter) -> None:
        self.source = market_adapter.source
        self._adapter = market_adapter
        self._json_getter = json_getter

    def discover_assets(self, limit: int = 10, **filters: Any) -> list[str]:
        symbols = self._adapter.discover_assets(self._json_getter, max(1, limit))
        quotes = {str(item).upper() for item in filters.get("quote", [])}
        if quotes:
            symbols = [
                symbol
                for symbol in symbols
                if any(symbol.upper().endswith(quote) for quote in quotes)
            ] or symbols
        return symbols[:limit]

    def fetch_raw(
        self,
        symbol: str,
        datasets: list[str],  # noqa: ARG002
        *,
        timeframe: str = "1m",  # noqa: ARG002
        limit: int = 500,
    ) -> dict[str, Any]:
        payload = self._adapter.fetch_datasets(self._json_getter, symbol)
        trimmed: dict[str, Any] = {}
        for key, value in payload.items():
            if isinstance(value, list):
                trimmed[key] = value[:limit]
            else:
                trimmed[key] = value
        return trimmed


def build_market_registry_adapters(json_getter: JsonGetter) -> list[MarketRegistrySourceAdapter]:
    return [MarketRegistrySourceAdapter(item, json_getter) for item in build_market_source_registry()]
