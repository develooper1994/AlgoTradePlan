"""Deterministic offline fallback adapter."""

from __future__ import annotations

from typing import Any


class OfflineFallbackAdapter:
    source = "offline_fallback"

    def discover_assets(self, limit: int = 10, **filters: Any) -> list[str]:  # noqa: ARG002
        return ["BTCUSDT"][:limit]

    def fetch_raw(
        self,
        symbol: str,
        datasets: list[str],  # noqa: ARG002
        *,
        timeframe: str = "1m",  # noqa: ARG002
        limit: int = 500,
    ) -> dict[str, Any]:
        rows = max(1, min(limit, 500))
        return {
            "tick": [{"symbol": symbol, "price": "123.45"}],
            "kline": [
                [1_700_000_000_000 + (index * 60_000), "100", "101", "99", str(100 + index * 0.2), "10"]
                for index in range(rows)
            ],
            "trade": [{"id": 1, "price": "123.45", "qty": "0.25", "time": 1_700_000_000_001}],
            "orderbook": [{"bids": [["123.40", "1"]], "asks": [["123.50", "1"]]}],
            "funding": [{"fundingRate": "0.0001", "fundingTime": 1_700_000_000_002, "derived": True}],
        }
