"""Normalize raw source payloads into canonical schema records."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from datetime import UTC, datetime
from typing import Any

from src.algotradeplan.core.canonical import (
    FundingRateRecord,
    MacroSnapshot,
    NewsItem,
    OHLCVRecord,
    OrderbookSnapshot,
    TradeRecord,
)
from src.algotradeplan.plugins.data.contracts import DataRecord


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _to_int(value: Any, default: int) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _exchange_name(source: str) -> str:
    if source.endswith("_spot"):
        return source.removesuffix("_spot")
    if source.endswith("_futures"):
        return source.removesuffix("_futures")
    if source.endswith("_fx"):
        return source.removesuffix("_fx")
    return source.split("_", 1)[0]


def _now_ms() -> int:
    return int(datetime.now(UTC).timestamp() * 1000)


def normalize_ohlcv(source: str, symbol: str, rows: list[Any]) -> list[OHLCVRecord]:
    exchange = _exchange_name(source)
    normalized: list[OHLCVRecord] = []
    for row in rows:
        if not isinstance(row, list) or len(row) < 5:
            continue
        timestamp_ms = _to_int(row[0], _now_ms())
        normalized.append(
            OHLCVRecord(
                symbol=symbol,
                exchange=exchange,
                timestamp_ms=timestamp_ms,
                open=_to_float(row[1]),
                high=_to_float(row[2]),
                low=_to_float(row[3]),
                close=_to_float(row[4]),
                volume=_to_float(row[5], 0.0) if len(row) > 5 else 0.0,
                source=source,
            )
        )
    return normalized


def normalize_trade(source: str, symbol: str, rows: list[Any]) -> list[TradeRecord]:
    exchange = _exchange_name(source)
    normalized: list[TradeRecord] = []
    for index, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            continue
        normalized.append(
            TradeRecord(
                symbol=symbol,
                exchange=exchange,
                trade_id=str(row.get("id") or row.get("trade_id") or row.get("i") or index),
                timestamp_ms=_to_int(row.get("time") or row.get("T") or row.get("timestamp"), _now_ms() + index),
                price=_to_float(row.get("price") or row.get("p") or row.get("lastPrice")),
                quantity=_to_float(row.get("qty") or row.get("size") or row.get("q") or 0.0),
                side=str(row.get("side") or row.get("S") or "buy").lower(),
                source=source,
                metadata={"raw": row},
            )
        )
    return normalized


def normalize_orderbook(source: str, symbol: str, rows: list[Any]) -> list[OrderbookSnapshot]:
    exchange = _exchange_name(source)
    normalized: list[OrderbookSnapshot] = []
    for index, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            continue
        bids = row.get("bids") or row.get("b") or []
        asks = row.get("asks") or row.get("a") or []
        if not bids and row.get("bid") is not None:
            bids = [[row.get("bid"), 0.0]]
        if not asks and row.get("ask") is not None:
            asks = [[row.get("ask"), 0.0]]
        normalized.append(
            OrderbookSnapshot(
                symbol=symbol,
                exchange=exchange,
                timestamp_ms=_to_int(row.get("timestamp") or row.get("ts"), _now_ms() + index),
                bids=[[ _to_float(level[0]), _to_float(level[1], 0.0)] for level in bids if isinstance(level, list) and len(level) >= 2],
                asks=[[ _to_float(level[0]), _to_float(level[1], 0.0)] for level in asks if isinstance(level, list) and len(level) >= 2],
                source=source,
            )
        )
    return normalized


def normalize_funding(source: str, symbol: str, rows: list[Any]) -> list[FundingRateRecord]:
    exchange = _exchange_name(source)
    normalized: list[FundingRateRecord] = []
    for index, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            continue
        normalized.append(
            FundingRateRecord(
                symbol=symbol,
                exchange=exchange,
                timestamp_ms=_to_int(row.get("fundingTime") or row.get("timestamp"), _now_ms() + index),
                rate=_to_float(row.get("fundingRate") or row.get("rate") or 0.0),
                next_funding_timestamp_ms=_to_int(row.get("nextFundingTime"), 0) or None,
                derived=bool(row.get("derived", False)),
                source=source,
                metadata={"raw": row},
            )
        )
    return normalized


def normalize_tick(source: str, symbol: str, rows: list[Any]) -> list[dict[str, Any]]:
    exchange = _exchange_name(source)
    normalized: list[dict[str, Any]] = []
    for index, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            continue
        normalized.append(
            {
                "symbol": str(row.get("symbol") or symbol),
                "exchange": exchange,
                "timestamp_ms": _to_int(row.get("time") or row.get("timestamp"), _now_ms() + index),
                "price": _to_float(row.get("price") or row.get("lastPrice") or row.get("c"), 0.0),
                "source": source,
                "metadata": {"raw": row},
            }
        )
    return normalized


def normalize_news(source: str, asset: str, rows: list[Any]) -> list[NewsItem]:
    normalized: list[NewsItem] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        normalized.append(
            NewsItem(
                title=str(row.get("title") or row.get("headline") or asset),
                url=str(row.get("url") or row.get("story_url") or ""),
                source=source,
                published_at=str(row.get("created_at") or row.get("published_at") or datetime.now(UTC).isoformat()),
                assets=[asset.upper()] if asset else [],
                metadata={"raw": row},
            )
        )
    return normalized


def normalize_macro(source: str, base_currency: str, payload: dict[str, Any]) -> list[MacroSnapshot]:
    if not isinstance(payload, dict):
        return []
    timestamp = str(payload.get("date") or payload.get("timestamp") or datetime.now(UTC).date().isoformat())
    rates = {str(key): _to_float(value) for key, value in payload.get("rates", {}).items()}
    return [
        MacroSnapshot(
            base_currency=str(payload.get("base") or base_currency),
            timestamp=timestamp,
            rates=rates,
            source=source,
            metadata={"raw": payload},
        )
    ]


def normalize_fundamentals(source: str, symbol: str, payload: Any) -> list[dict[str, Any]]:
    rows = payload if isinstance(payload, list) else [payload]
    normalized: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        normalized.append(
            {
                "symbol": symbol,
                "source": source,
                "timestamp_ms": _now_ms(),
                "fields": row,
            }
        )
    return normalized


def normalize_dataset(dataset: str, source: str, symbol: str, payload: Any) -> list[Any]:
    if dataset == "tick":
        rows = payload if isinstance(payload, list) else [payload]
        return normalize_tick(source, symbol, rows)
    if dataset == "kline":
        return normalize_ohlcv(source, symbol, payload if isinstance(payload, list) else [])
    if dataset == "trade":
        return normalize_trade(source, symbol, payload if isinstance(payload, list) else [])
    if dataset == "orderbook":
        rows = payload if isinstance(payload, list) else [payload]
        return normalize_orderbook(source, symbol, rows)
    if dataset == "funding":
        return normalize_funding(source, symbol, payload if isinstance(payload, list) else [])
    if dataset == "news":
        return normalize_news(source, symbol, payload if isinstance(payload, list) else [])
    if dataset == "macro":
        return normalize_macro(source, symbol, payload if isinstance(payload, dict) else {})
    if dataset == "fundamentals":
        return normalize_fundamentals(source, symbol, payload)
    return []


def to_data_records(dataset: str, source: str, asset_type: str, items: list[Any]) -> list[DataRecord]:
    records: list[DataRecord] = []
    for index, item in enumerate(items, start=1):
        payload = asdict(item) if is_dataclass(item) else dict(item)
        timestamp_ms = int(payload.get("timestamp_ms") or _now_ms() + index)
        symbol = str(payload.get("symbol") or payload.get("base_currency") or payload.get("title") or source)
        records.append(
            DataRecord(
                key=f"{source}:{dataset}:{symbol}:{timestamp_ms}:{index}",
                observed_at=datetime.fromtimestamp(timestamp_ms / 1000, tz=UTC).isoformat(),
                domain="market" if dataset in {"kline", "trade", "orderbook", "funding", "tick"} else dataset,
                source=source,
                asset_type=asset_type,
                payload=payload,
                metadata={"dataset": dataset, "join_key": symbol, "canonical": True},
            )
        )
    return records
