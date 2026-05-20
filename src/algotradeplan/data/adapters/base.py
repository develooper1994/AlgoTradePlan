"""Base protocol for DataHub source adapters."""

from __future__ import annotations

from typing import Any, Protocol


class DataSourceAdapter(Protocol):
    source: str

    def discover_assets(self, limit: int = 10, **filters: Any) -> list[str]:
        ...

    def fetch_raw(
        self,
        symbol: str,
        datasets: list[str],
        *,
        timeframe: str = "1m",
        limit: int = 500,
        **filters: Any,
    ) -> dict[str, Any]:
        ...
