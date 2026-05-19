"""CCXT-backed market discovery and multi-dataset ingestion plugin."""

from __future__ import annotations

from importlib import import_module
from typing import Any


class CcxtDependencyError(RuntimeError):
    """Raised when ccxt is unavailable in the runtime environment."""


class CcxtMarketDataAgent:
    plugin_id = "ccxt_market_data_agent"
    domain = "market"
    required_datasets = ("tick", "trade", "kline", "orderbook", "funding")
    _QUOTE_ASSETS = {"USDT", "USD", "USDC"}

    def _new_exchange(self, exchange_id: str) -> Any:
        try:
            ccxt_module = import_module("ccxt")
        except ImportError as exc:
            raise CcxtDependencyError(
                "ccxt is required for live market discovery. Install with: pip install ccxt"
            ) from exc

        exchange_class = getattr(ccxt_module, exchange_id, None)
        if exchange_class is None:
            raise ValueError(f"Unsupported ccxt exchange id: {exchange_id}")
        return exchange_class({"enableRateLimit": True})

    def discover_assets(self, exchange_id: str, max_symbols: int) -> list[str]:
        exchange = self._new_exchange(exchange_id)
        try:
            markets = exchange.load_markets()
            filtered = []
            for symbol, market in markets.items():
                if not market.get("active", True):
                    continue
                quote = str(market.get("quote", "")).upper()
                if quote not in self._QUOTE_ASSETS:
                    continue
                if exchange_id == "binanceusdm" and market.get("contract") is not True:
                    continue
                filtered.append(symbol)
            return sorted(filtered)[:max(1, max_symbols)]
        except Exception as exc:
            raise RuntimeError(f"{exchange_id} discovery failed: {exc}") from exc
        finally:
            if hasattr(exchange, "close"):
                try:
                    exchange.close()
                except Exception:
                    pass

    def fetch_exchange_datasets(self, exchange_id: str, symbol: str) -> dict[str, list[Any]]:
        exchange = self._new_exchange(exchange_id)
        try:
            tick = [exchange.fetch_ticker(symbol)]
            kline = exchange.fetch_ohlcv(symbol, timeframe="1m", limit=180)
            trade = exchange.fetch_trades(symbol, limit=25)
            orderbook = [exchange.fetch_order_book(symbol, limit=10)]

            funding: list[Any] = []
            try:
                funding = exchange.fetch_funding_rate_history(symbol, limit=5)
            except Exception:
                try:
                    funding_snapshot = exchange.fetch_funding_rate(symbol)
                    funding = [funding_snapshot]
                except Exception:
                    funding = []

            return {
                "tick": list(tick),
                "kline": list(kline),
                "trade": list(trade),
                "orderbook": list(orderbook),
                "funding": list(funding),
            }
        except Exception as exc:
            raise RuntimeError(f"{exchange_id} dataset fetch failed for {symbol}: {exc}") from exc
        finally:
            if hasattr(exchange, "close"):
                try:
                    exchange.close()
                except Exception:
                    pass
