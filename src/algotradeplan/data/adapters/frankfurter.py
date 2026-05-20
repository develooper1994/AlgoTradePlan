"""Frankfurter FX adapter."""

from __future__ import annotations

from typing import Any, Callable

JsonGetter = Callable[[str, dict[str, Any]], Any]


class FrankfurterAdapter:
    source = "frankfurter_fx"

    def __init__(self, json_getter: JsonGetter) -> None:
        self._json_getter = json_getter

    def discover_assets(self, limit: int = 10, **filters: Any) -> list[str]:  # noqa: ARG002
        payload = self._json_getter("https://api.frankfurter.dev/v1/currencies", {})
        return sorted(str(item) for item in payload.keys())[:limit]

    def fetch_raw(
        self,
        symbol: str,
        datasets: list[str],  # noqa: ARG002
        *,
        timeframe: str = "1m",  # noqa: ARG002
        limit: int = 500,  # noqa: ARG002
    ) -> dict[str, Any]:
        return {
            "macro": self._json_getter("https://api.frankfurter.dev/v1/latest", {"base": symbol}),
            "tick": [{"symbol": symbol, "price": 1.0}],
        }
