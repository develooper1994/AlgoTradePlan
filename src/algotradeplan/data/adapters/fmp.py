"""Financial Modeling Prep adapter."""

from __future__ import annotations

import os
from typing import Any, Callable

JsonGetter = Callable[[str, dict[str, Any]], Any]


class FinancialModelingPrepAdapter:
    source = "financial_modeling_prep"

    def __init__(self, json_getter: JsonGetter) -> None:
        self._json_getter = json_getter

    def discover_assets(self, limit: int = 10, **filters: Any) -> list[str]:
        requested = [str(item).upper() for item in filters.get("symbols", []) if str(item).strip()]
        seeds = requested or ["AAPL", "MSFT", "SPY", "QQQ"]
        return seeds[:limit]

    def fetch_raw(
        self,
        symbol: str,
        datasets: list[str],
        *,
        timeframe: str = "1m",  # noqa: ARG002
        limit: int = 500,
    ) -> dict[str, Any]:
        api_key = os.getenv("FMP_API_KEY", "")
        result: dict[str, Any] = {}
        if "tick" in datasets:
            quote = self._json_getter(
                f"https://financialmodelingprep.com/api/v3/quote-short/{symbol.upper()}",
                {"apikey": api_key},
            )
            result["tick"] = quote if isinstance(quote, list) else []
        if "kline" in datasets:
            payload = self._json_getter(
                f"https://financialmodelingprep.com/api/v3/historical-price-full/{symbol.upper()}",
                {"timeseries": min(250, max(1, limit)), "apikey": api_key},
            )
            historical = payload.get("historical", []) if isinstance(payload, dict) else []
            result["kline"] = [
                [row.get("date", ""), row.get("open", 0), row.get("high", 0), row.get("low", 0), row.get("close", 0), row.get("volume", 0)]
                for row in reversed(historical)
                if isinstance(row, dict)
            ]
        if "fundamentals" in datasets:
            profile = self._json_getter(
                f"https://financialmodelingprep.com/api/v3/profile/{symbol.upper()}",
                {"apikey": api_key},
            )
            result["fundamentals"] = profile if isinstance(profile, list) else []
        if "news" in datasets:
            news = self._json_getter(
                "https://financialmodelingprep.com/api/v3/stock_news",
                {"tickers": symbol.upper(), "limit": min(50, max(1, limit)), "apikey": api_key},
            )
            result["news"] = news if isinstance(news, list) else []
        if "corporate_actions" in datasets:
            actions = self._json_getter(
                f"https://financialmodelingprep.com/api/v3/historical-price-full/stock_split/{symbol.upper()}",
                {"apikey": api_key},
            )
            result["corporate_actions"] = actions.get("historical", []) if isinstance(actions, dict) else []
        return result
