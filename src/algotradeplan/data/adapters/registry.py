"""Registry for DataHub source adapters."""

from __future__ import annotations

from typing import Any

from src.algotradeplan.data.adapters.base import DataSourceAdapter


class DataAdapterRegistry:
    def __init__(self, adapters: list[DataSourceAdapter]) -> None:
        self._adapters = {adapter.source: adapter for adapter in adapters}

    def sources(self) -> list[str]:
        return sorted(self._adapters)

    def get(self, source: str) -> DataSourceAdapter:
        return self._adapters[source]

    def discover_assets(self, source: str, limit: int = 10, **filters: Any) -> list[str]:
        return self.get(source).discover_assets(limit=limit, **filters)

    def fetch_raw(
        self,
        source: str,
        symbol: str,
        datasets: list[str],
        *,
        timeframe: str = "1m",
        limit: int = 500,
        **filters: Any,
    ) -> dict[str, Any]:
        return self.get(source).fetch_raw(symbol, datasets, timeframe=timeframe, limit=limit, **filters)
