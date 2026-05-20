"""ECB macro and FX adapter."""

from __future__ import annotations

from typing import Any, Callable

JsonGetter = Callable[[str, dict[str, Any]], Any]


class EcbAdapter:
    source = "ecb"

    def __init__(self, json_getter: JsonGetter) -> None:
        self._json_getter = json_getter

    def discover_assets(self, limit: int = 10, **filters: Any) -> list[str]:  # noqa: ARG002
        return ["EUR", "USD", "GBP", "JPY"][:limit]

    def fetch_raw(
        self,
        symbol: str,
        datasets: list[str],  # noqa: ARG002
        *,
        timeframe: str = "1m",  # noqa: ARG002
        limit: int = 500,  # noqa: ARG002
    ) -> dict[str, Any]:
        payload = self._json_getter(
            "https://data-api.ecb.europa.eu/service/data/EXR/D.USD.EUR.SP00.A",
            {"format": "jsondata"},
        )
        observations = payload.get("dataSets", [{}])[0].get("series", {}).get("0:0:0:0:0", {}).get("observations", {})
        rates = {
            str(index): float(value[0]) if isinstance(value, list) and value else 0.0
            for index, value in observations.items()
        }
        tick = [{"symbol": symbol, "price": next(iter(rates.values()), 0.0)}]
        macro = {"base": "EUR", "date": "", "rates": rates}
        return {"tick": tick, "macro": macro}
