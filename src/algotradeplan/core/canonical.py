"""Canonical data schema models for the trading framework.

These dataclasses define the normalized representations used throughout
the data layer (raw → normalized → feature-ready → backtest-ready).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# ---------------------------------------------------------------------------
# Asset identity
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class AssetIdentity:
    symbol: str                   # e.g. "BTC/USDT"
    base_asset: str               # e.g. "BTC"
    quote_asset: str              # e.g. "USDT"
    exchange: str                 # e.g. "binance"
    asset_class: str              # "spot" | "perpetual" | "future" | "option"
    exchange_symbol: str = ""     # exchange-native ticker, if different
    metadata: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# OHLCV / Kline
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class OHLCVRecord:
    symbol: str
    exchange: str
    timestamp_ms: int             # open-bar epoch milliseconds (UTC)
    open: float
    high: float
    low: float
    close: float
    volume: float
    source: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Trade tick
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class TradeRecord:
    symbol: str
    exchange: str
    trade_id: str
    timestamp_ms: int
    price: float
    quantity: float
    side: str                     # "buy" | "sell"
    source: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Orderbook snapshot
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class OrderbookSnapshot:
    symbol: str
    exchange: str
    timestamp_ms: int
    bids: list[list[float]]       # [[price, qty], ...]
    asks: list[list[float]]       # [[price, qty], ...]
    source: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Funding rate
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class FundingRateRecord:
    symbol: str
    exchange: str
    timestamp_ms: int
    rate: float
    next_funding_timestamp_ms: int | None = None
    derived: bool = False
    source: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# News item
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class NewsItem:
    title: str
    url: str
    source: str
    published_at: str             # ISO-8601
    assets: list[str] = field(default_factory=list)
    sentiment_score: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Macro series
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class MacroSeriesPoint:
    series_id: str                # e.g. "GDP_US", "CPI_EU"
    timestamp: str                # ISO-8601 date or datetime
    value: float
    unit: str = ""
    source: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class MacroSnapshot:
    base_currency: str
    timestamp: str
    rates: dict[str, float]       # {"EUR": 0.91, "GBP": 0.78, ...}
    source: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
