"""DefiLlama adapter."""

from __future__ import annotations

from typing import Any, Callable

JsonGetter = Callable[[str, dict[str, Any]], Any]


class DefiLlamaAdapter:
    source = "defillama"

    def __init__(self, json_getter: JsonGetter) -> None:
        self._json_getter = json_getter
        self._protocol_cache: list[dict[str, Any]] | None = None

    def discover_assets(self, limit: int = 10, **filters: Any) -> list[str]:  # noqa: ARG002
        payload = self._protocols()
        names = [str(item.get("slug")) for item in payload if isinstance(item, dict) and item.get("slug")]
        return names[:limit]

    def fetch_raw(
        self,
        symbol: str,
        datasets: list[str],
        *,
        timeframe: str = "1m",  # noqa: ARG002
        limit: int = 500,
    ) -> dict[str, Any]:
        protocols = self._protocols()
        protocol = next((item for item in protocols if item.get("slug") == symbol), protocols[0] if protocols else {})
        chart_payload = self._json_getter(f"https://api.llama.fi/protocol/{symbol}", {})
        tvl_rows = chart_payload.get("chainTvls", {})
        flattened = []
        for chain_name, chain_values in tvl_rows.items():
            if isinstance(chain_values, dict):
                series = chain_values.get("tvl", [])
                flattened.extend({"chain": chain_name, **row} for row in series if isinstance(row, dict))
        flattened = flattened[:limit]
        result: dict[str, Any] = {}
        if "macro" in datasets:
            result["macro"] = {
                "base": str(protocol.get("symbol") or symbol).upper(),
                "date": "",
                "rates": {str(item.get("date")): float(item.get("totalLiquidityUSD") or 0.0) for item in flattened},
                "metadata": {"series_type": "tvl_by_chain", "protocol": symbol},
            }
        if "fundamentals" in datasets:
            result["fundamentals"] = [
                {
                    "symbol": symbol,
                    "tvl": float(protocol.get("tvl") or 0.0),
                    "mcap": float(protocol.get("mcap") or 0.0),
                    "name": protocol.get("name") or symbol,
                    "metadata": {"source": "defillama_protocols", "field_group": "protocol_snapshot"},
                }
            ]
        return result

    def _protocols(self) -> list[dict[str, Any]]:
        if self._protocol_cache is None:
            payload = self._json_getter("https://api.llama.fi/protocols", {})
            self._protocol_cache = [item for item in payload if isinstance(item, dict)]
        return list(self._protocol_cache)
