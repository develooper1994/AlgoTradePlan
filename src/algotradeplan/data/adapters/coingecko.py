"""CoinGecko adapter."""

from __future__ import annotations

from typing import Any, Callable

JsonGetter = Callable[[str, dict[str, Any]], Any]


class CoinGeckoAdapter:
    source = "coingecko"

    def __init__(self, json_getter: JsonGetter) -> None:
        self._json_getter = json_getter

    def discover_assets(self, limit: int = 10, **filters: Any) -> list[str]:  # noqa: ARG002
        payload = self._json_getter(
            "https://api.coingecko.com/api/v3/coins/markets",
            {"vs_currency": "usd", "order": "market_cap_desc", "per_page": max(1, limit), "page": 1},
        )
        return [str(item.get("id")) for item in payload if item.get("id")][:limit]

    def fetch_raw(
        self,
        symbol: str,
        datasets: list[str],  # noqa: ARG002
        *,
        timeframe: str = "1m",  # noqa: ARG002
        limit: int = 500,
    ) -> dict[str, Any]:
        market = self._json_getter(
            "https://api.coingecko.com/api/v3/coins/markets",
            {"vs_currency": "usd", "ids": symbol, "per_page": 1, "page": 1},
        )
        chart = self._json_getter(
            f"https://api.coingecko.com/api/v3/coins/{symbol}/market_chart",
            {"vs_currency": "usd", "days": min(90, max(1, limit // 24 or 1))},
        )
        tick = [{"symbol": symbol, "price": (market[0].get("current_price") if market else 0)}]
        prices = chart.get("prices", [])
        volumes = chart.get("total_volumes", [])
        klines: list[list[float]] = []
        for index in range(min(len(prices), len(volumes), limit)):
            ts, close = prices[index]
            _, volume = volumes[index]
            klines.append([ts, close, close, close, close, volume])
        return {"tick": tick, "kline": klines}
