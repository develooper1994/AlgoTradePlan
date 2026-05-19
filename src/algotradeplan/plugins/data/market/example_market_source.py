"""Example market data source plugin."""

from __future__ import annotations

from src.algotradeplan.plugins.data.contracts import DataRecord, DataRequest


class ExampleMarketDataSource:
    plugin_id = "example_market_source"
    domain = "market"

    def fetch(self, request: DataRequest) -> list[DataRecord]:
        symbol = request.symbol or "SPY"
        return [
            DataRecord(
                key=f"{symbol}-close-2026-01-01",
                observed_at="2026-01-01T00:00:00Z",
                domain=self.domain,
                source="demo_market_feed",
                asset_type="equity",
                payload={"symbol": symbol, "close": 100.0, "dataset": request.dataset},
                metadata={"join_key": symbol, "lake_zone": "raw"},
            )
        ]
