"""Example data source plugin."""

from __future__ import annotations


class ExampleDataPlugin:
    plugin_id = "example_data_source"

    def fetch(self, symbol: str) -> dict[str, object]:
        return {"symbol": symbol, "price": 0.0}
