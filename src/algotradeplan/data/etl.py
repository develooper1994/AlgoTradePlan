"""Fluent ETL facade on top of MarketData-backed :class:`DataHub`."""

from __future__ import annotations

from typing import Any

from integration.algotradeplan.hub_bridge import DataHub, IngestResult


class ETL:
    def __init__(self, hub: DataHub | None = None) -> None:
        self.hub = hub or DataHub()
        self._source: str | None = None
        self._discovered_assets: list[str] = []
        self._selected_assets: list[str] = []
        self._results: list[IngestResult] = []
        self._datasets: list[str] = []
        self._timeframe = "1m"
        self._limit = 500
        self._allow_partial = True

    def source(self, source: str) -> "ETL":
        self._source = source
        return self

    def discover_assets(self, *, limit: int = 10, **filters: Any) -> "ETL":
        if self._source is None:
            raise ValueError("source must be selected before discover_assets")
        self._discovered_assets = self.hub.discover_assets(self._source, limit=limit, **filters)
        return self

    def select_assets(self, *, limit: int = 5, prefer: list[str] | None = None) -> "ETL":
        prefer = [item.upper() for item in (prefer or [])]
        discovered = list(self._discovered_assets)
        if prefer:
            discovered.sort(key=lambda symbol: (0 if any(symbol.upper().startswith(item) for item in prefer) else 1, symbol))
        self._selected_assets = discovered[:limit]
        return self

    def fetch(
        self,
        datasets: list[str],
        *,
        timeframe: str = "1m",
        limit: int = 500,
        allow_partial: bool = True,
    ) -> "ETL":
        if self._source is None:
            raise ValueError("source must be selected before fetch")
        self._datasets = list(datasets)
        self._timeframe = timeframe
        self._limit = limit
        self._allow_partial = allow_partial
        targets = self._selected_assets or self._discovered_assets[:1]
        self._results = [
            self.hub.ingest(
                source=self._source,
                symbol=symbol,
                datasets=datasets,
                timeframe=timeframe,
                limit=limit,
                allow_partial=allow_partial,
                store=False,
            )
            for symbol in targets
        ]
        return self

    def normalize(self) -> "ETL":
        return self

    def validate(self) -> "ETL":
        return self

    def store(self) -> "ETL":
        if self._source is None:
            raise ValueError("source must be selected before store")
        refreshed: list[IngestResult] = []
        for result in self._results:
            refreshed.append(
                self.hub.ingest(
                    source=self._source,
                    symbol=result.symbol or "",
                    datasets=self._datasets,
                    timeframe=self._timeframe,
                    limit=self._limit,
                    allow_partial=self._allow_partial,
                    store=True,
                )
            )
        self._results = refreshed
        return self

    def to_feature_frame(self):
        if not self._results:
            return []
        rows = []
        for result in self._results:
            frame = result.to_feature_frame()
            if hasattr(frame, "to_dict"):
                rows.extend(frame.to_dict(orient="records"))
            else:
                rows.extend(frame)
        try:
            import pandas as pd  # type: ignore
        except Exception:
            return rows
        return pd.DataFrame(rows)

    def load_market_data(
        self,
        *,
        source: str,
        symbol: str,
        dataset: str,
        timeframe: str = "1m",
        limit: int = 500,
        allow_partial: bool = False,
    ):
        return self.hub.load_market_data(
            source=source,
            symbol=symbol,
            dataset=dataset,
            timeframe=timeframe,
            limit=limit,
            allow_partial=allow_partial,
        )
