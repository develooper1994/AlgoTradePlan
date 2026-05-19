"""Data source plugin that replays a provided batch of normalized records."""

from __future__ import annotations

from src.algotradeplan.plugins.data.contracts import DataRecord, DataRequest


class StaticMarketBatchSourcePlugin:
    plugin_id = "static_market_batch_source"
    domain = "market"

    def __init__(self, records: list[DataRecord]) -> None:
        self._records = records

    def fetch(self, request: DataRequest) -> list[DataRecord]:  # noqa: ARG002
        """Return fixed records; request is required by the DataSourcePlugin protocol."""
        return list(self._records)
