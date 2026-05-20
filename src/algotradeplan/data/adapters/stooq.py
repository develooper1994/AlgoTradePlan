"""Stooq adapter."""

from __future__ import annotations

from typing import Any, Callable

JsonGetter = Callable[[str, dict[str, Any]], Any]


class StooqAdapter:
    source = "stooq"

    def __init__(self, json_getter: JsonGetter) -> None:
        self._json_getter = json_getter

    def discover_assets(self, limit: int = 10, **filters: Any) -> list[str]:
        seed = [str(item).lower() for item in filters.get("symbols", []) if str(item).strip()]
        if not seed:
            seed = ["aapl.us", "spy.us", "eurusd", "wig20"]
        return seed[:limit]

    def fetch_raw(
        self,
        symbol: str,
        datasets: list[str],  # noqa: ARG002
        *,
        timeframe: str = "1m",  # noqa: ARG002
        limit: int = 500,
    ) -> dict[str, Any]:
        payload = self._json_getter(
            "https://stooq.com/q/l/",
            {"s": symbol.lower(), "f": "sd2t2ohlcv", "h": "", "e": "json"},
        )
        rows = payload.get("data", payload if isinstance(payload, list) else [])
        klines: list[list[Any]] = []
        for index, row in enumerate(rows[:limit], start=1):
            date_value = str(row.get("date", "")).replace("-", "")
            timestamp = 1_700_000_000_000 + (index * 86_400_000)
            if date_value.isdigit() and len(date_value) == 8:
                timestamp = int(date_value) * 1000
            klines.append(
                [
                    timestamp,
                    row.get("open", 0),
                    row.get("high", 0),
                    row.get("low", 0),
                    row.get("close", 0),
                    row.get("volume", 0),
                ]
            )
        return {"kline": klines}
