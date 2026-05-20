"""World Bank macro adapter."""

from __future__ import annotations

from typing import Any, Callable

JsonGetter = Callable[[str, dict[str, Any]], Any]


class WorldBankAdapter:
    source = "world_bank"

    def __init__(self, json_getter: JsonGetter) -> None:
        self._json_getter = json_getter

    def discover_assets(self, limit: int = 10, **filters: Any) -> list[str]:  # noqa: ARG002
        return ["NY.GDP.MKTP.CD", "FP.CPI.TOTL.ZG", "SL.UEM.TOTL.ZS"][:limit]

    def fetch_raw(
        self,
        symbol: str,
        datasets: list[str],  # noqa: ARG002
        *,
        timeframe: str = "1m",  # noqa: ARG002
        limit: int = 500,
    ) -> dict[str, Any]:
        payload = self._json_getter(
            f"https://api.worldbank.org/v2/country/WLD/indicator/{symbol}",
            {"format": "json", "per_page": min(100, max(1, limit))},
        )
        rows = payload[1] if isinstance(payload, list) and len(payload) > 1 else []
        rates = {
            str(row.get("date")): float(row.get("value") or 0.0)
            for row in rows
            if isinstance(row, dict) and row.get("date")
        }
        snapshot = {"base": symbol, "date": rows[0].get("date") if rows else "", "rates": rates}
        return {"macro": snapshot}
