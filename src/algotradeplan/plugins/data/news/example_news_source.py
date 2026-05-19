"""Example news data source plugin."""

from __future__ import annotations

from src.algotradeplan.plugins.data.contracts import DataRecord, DataRequest


class ExampleNewsDataSource:
    plugin_id = "example_news_source"
    domain = "news"

    def fetch(self, request: DataRequest) -> list[DataRecord]:
        symbol = request.symbol or "SPY"
        return [
            DataRecord(
                key=f"{symbol}-headline-2026-01-01",
                observed_at="2026-01-01T00:00:00Z",
                domain=self.domain,
                source="demo_news_feed",
                asset_type="news",
                payload={
                    "symbol": symbol,
                    "headline": "Central bank commentary stabilizes risk sentiment",
                    "dataset": request.dataset,
                },
                metadata={"join_key": symbol, "lake_zone": "raw"},
            )
        ]
