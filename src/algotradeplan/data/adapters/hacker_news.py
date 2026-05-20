"""Hacker News adapter."""

from __future__ import annotations

from typing import Any, Callable

JsonGetter = Callable[[str, dict[str, Any]], Any]


class HackerNewsAdapter:
    source = "hacker_news"

    def __init__(self, json_getter: JsonGetter) -> None:
        self._json_getter = json_getter

    def discover_assets(self, limit: int = 10, **filters: Any) -> list[str]:  # noqa: ARG002
        payload = self._json_getter(
            "https://hn.algolia.com/api/v1/search", {"query": "bitcoin", "tags": "story"}
        )
        symbols: list[str] = []
        for row in payload.get("hits", []):
            title = str(row.get("title") or "").lower()
            if "bitcoin" in title:
                symbols.append("BITCOIN")
            if "ethereum" in title:
                symbols.append("ETHEREUM")
        return sorted(set(symbols or ["BITCOIN"]))[:limit]

    def fetch_raw(
        self,
        symbol: str,
        datasets: list[str],  # noqa: ARG002
        *,
        timeframe: str = "1m",  # noqa: ARG002
        limit: int = 500,
    ) -> dict[str, Any]:
        payload = self._json_getter(
            "https://hn.algolia.com/api/v1/search",
            {"query": symbol.lower(), "tags": "story", "hitsPerPage": min(limit, 50)},
        )
        return {"news": payload.get("hits", [])[:limit]}
