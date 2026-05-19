"""Example macro data source plugin."""

from __future__ import annotations

from src.algotradeplan.plugins.data.contracts import DataRecord, DataRequest


class ExampleMacroDataSource:
    plugin_id = "example_macro_source"
    domain = "macro"

    def fetch(self, request: DataRequest) -> list[DataRecord]:
        series = request.parameters.get("series", "CPI")
        return [
            DataRecord(
                key=f"{series}-release-2026-01",
                observed_at="2026-01-01T00:00:00Z",
                domain=self.domain,
                source="demo_macro_feed",
                asset_type="macro",
                payload={"series": series, "value": 2.4, "dataset": request.dataset},
                metadata={"join_key": series, "lake_zone": "raw"},
            )
        ]
