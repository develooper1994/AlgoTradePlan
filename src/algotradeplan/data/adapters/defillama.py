"""DefiLlama adapter."""

from __future__ import annotations

from typing import Any, Callable

JsonGetter = Callable[[str, dict[str, Any]], Any]


class DefiLlamaAdapter:
    source = "defillama"

    def __init__(self, json_getter: JsonGetter) -> None:
        self._json_getter = json_getter

    def discover_assets(self, limit: int = 10, **filters: Any) -> list[str]:  # noqa: ARG002
        payload = self._json_getter("https://api.llama.fi/protocols", {})
        names = [str(item.get("slug")) for item in payload if isinstance(item, dict) and item.get("slug")]
        return names[:limit]

    def fetch_raw(
        self,
        symbol: str,
        datasets: list[str],  # noqa: ARG002
        *,
        timeframe: str = "1m",  # noqa: ARG002
        limit: int = 500,
    ) -> dict[str, Any]:
        protocols = self._json_getter("https://api.llama.fi/protocols", {})
        protocol = next((item for item in protocols if item.get("slug") == symbol), protocols[0] if protocols else {})
        chart_payload = self._json_getter(f"https://api.llama.fi/protocol/{symbol}", {})
        tvl_rows = chart_payload.get("chainTvls", {})
        flattened = []
        for chain_name, chain_values in tvl_rows.items():
            if isinstance(chain_values, dict):
                series = chain_values.get("tvl", [])
                flattened.extend({"chain": chain_name, **row} for row in series if isinstance(row, dict))
        flattened = flattened[:limit]
        macro = {
            "base": str(protocol.get("symbol") or symbol).upper(),
            "date": "",
            "rates": {str(item.get("date")): float(item.get("totalLiquidityUSD") or 0.0) for item in flattened},
        }
        fundamentals = [
            {
                "symbol": symbol,
                "tvl": float(protocol.get("tvl") or 0.0),
                "mcap": float(protocol.get("mcap") or 0.0),
                "name": protocol.get("name") or symbol,
            }
        ]
        return {"macro": macro, "fundamentals": fundamentals}
