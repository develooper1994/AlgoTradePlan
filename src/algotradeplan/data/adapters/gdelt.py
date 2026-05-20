"""GDELT news adapter."""

from __future__ import annotations

from typing import Any, Callable

JsonGetter = Callable[[str, dict[str, Any]], Any]


class GdeltAdapter:
    source = "gdelt"

    def __init__(self, json_getter: JsonGetter) -> None:
        self._json_getter = json_getter

    def discover_assets(self, limit: int = 10, **filters: Any) -> list[str]:  # noqa: ARG002
        return ["bitcoin", "ethereum", "fed", "inflation"][:limit]

    def fetch_raw(
        self,
        symbol: str,
        datasets: list[str],  # noqa: ARG002
        *,
        timeframe: str = "1m",  # noqa: ARG002
        limit: int = 500,
    ) -> dict[str, Any]:
        payload = self._json_getter(
            "https://api.gdeltproject.org/api/v2/doc/doc",
            {"query": symbol, "mode": "artlist", "maxrecords": min(limit, 50), "format": "json"},
        )
        return {"news": payload.get("articles", [])[:limit]}
