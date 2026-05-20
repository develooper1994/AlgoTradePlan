"""FRED macro adapter."""

from __future__ import annotations

import os
from typing import Any, Callable

JsonGetter = Callable[[str, dict[str, Any]], Any]

_DEFAULT_SERIES = ["FEDFUNDS", "CPIAUCSL", "UNRATE", "DGS10", "GDP"]


class FredAdapter:
    source = "fred"

    def __init__(self, json_getter: JsonGetter) -> None:
        self._json_getter = json_getter

    def discover_assets(self, limit: int = 10, **filters: Any) -> list[str]:
        requested = [str(item).upper() for item in filters.get("symbols", []) if str(item).strip()]
        return (requested or _DEFAULT_SERIES)[:limit]

    def fetch_raw(
        self,
        symbol: str,
        datasets: list[str],
        *,
        timeframe: str = "1m",  # noqa: ARG002
        limit: int = 500,
    ) -> dict[str, Any]:
        payload = self._json_getter(
            "https://api.stlouisfed.org/fred/series/observations",
            {
                "series_id": symbol.upper(),
                "file_type": "json",
                "sort_order": "desc",
                "limit": min(100, max(1, limit)),
                "api_key": os.getenv("FRED_API_KEY", ""),
            },
        )
        rows = payload.get("observations", [])
        rates = {
            str(row.get("date")): float(row.get("value"))
            for row in rows
            if isinstance(row, dict) and row.get("date") and str(row.get("value")) not in {"", "."}
        }
        snapshot = {"base": symbol.upper(), "date": rows[0].get("date") if rows else "", "rates": rates}
        return {"macro": snapshot} if "macro" in datasets else {}
