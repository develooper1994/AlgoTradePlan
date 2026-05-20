"""Stooq adapter."""

from __future__ import annotations

from datetime import UTC, datetime
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
        timeframe: str = "1d",  # noqa: ARG002
        limit: int = 500,
    ) -> dict[str, Any]:
        payload = self._json_getter(
            "https://stooq.com/q/l/",
            {"s": symbol.lower(), "f": "sd2t2ohlcv", "h": "", "e": "json"},
        )
        rows = payload.get("data", payload if isinstance(payload, list) else [])
        klines: list[list[Any]] = []
        for row in rows[:limit]:
            timestamp = _parse_stooq_timestamp(row)
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


def _parse_stooq_timestamp(row: dict[str, Any]) -> int:
    date_text = str(row.get("date", "")).strip()
    time_text = str(row.get("time", "")).strip()
    for fmt, value in (
        ("%Y-%m-%d %H:%M:%S", f"{date_text} {time_text}".strip()),
        ("%Y-%m-%d %H:%M", f"{date_text} {time_text}".strip()),
        ("%Y-%m-%d", date_text),
        ("%Y%m%d", date_text.replace("-", "")),
    ):
        if not value:
            continue
        try:
            return int(datetime.strptime(value, fmt).replace(tzinfo=UTC).timestamp() * 1000)
        except ValueError:
            continue
    return 0
